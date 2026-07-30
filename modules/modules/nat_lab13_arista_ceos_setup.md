# Lab 13 – Build an Arista cEOS Lab in AWS

**Course:** Network Automation Tools — Day 5
**Prerequisite:** Days 1–4 complete. You have an AWS account, your `control-node` EC2 instance, and the `AutomationLab-Key.pem` from Lab 1. You also need a **free arista.com account** (used only to download the switch image).
**Objective:** Stand up a real Arista switch — `leaf1` — as a lightweight container (**cEOS-lab**) on an AWS EC2 host using **containerlab**. The same host runs your automation code. By the end you will have a switch you can reach over SSH and eAPI, ready for Labs 14 and 15.

---

> **About the environment:** cEOS-lab is Arista's containerized EOS — the full switch operating system packaged as a Docker image, so you can build and tear down real switches in seconds without dedicated hardware. `containerlab` deploys and wires them from a small topology file. In this course you run both the switch and your automation code on a single EC2 host.

> **Cost note:** cEOS needs about 2 GB of RAM, so this lab uses a `t3.medium` instance, which is **not** free-tier (~$0.04/hr). **Stop the instance when you are not using it.** Clean up at the end of Lab 15.

## Overview

In this lab you will:

1. Resize your control node (or launch a new instance) so it has enough memory for a switch container
2. Install Docker and containerlab with a single command
3. Download the Arista cEOS image and import it into Docker
4. Deploy `leaf1` from a small topology file
5. Create the `arista` login and enable eAPI on the switch
6. Verify you can reach `leaf1` over ping, SSH, and eAPI

---

## Part 1 — Prepare the Host

### Step 1. Give the host enough memory

A single cEOS switch needs ~2 GB of RAM, and a `t2.micro` (1 GB) is too small. Resize your control node to `t3.medium`:

1. In the AWS console: **EC2 → Instances → control-node → Instance state → Stop instance**.
2. Once it shows **Stopped**: **Actions → Instance settings → Change instance type → `t3.medium` → Apply**.
3. **Instance state → Start instance**.

> **New public IP:** A stopped/started instance without an Elastic IP gets a **new** public IPv4 address. Note the new one from the console for any SSH or `scp` you do from your laptop.

> **Alternative:** If you would rather leave the control node alone, launch a **new** `t3.medium` (Amazon Linux 2023) in the same VPC and subnet and use it as your lab host. Everything below is identical.

### Step 2. Connect and confirm memory

Connect with EC2 Instance Connect (the browser terminal, as in Lab 1). Confirm the memory:

```bash
free -h
```

The `Mem:` total should read about `3.8Gi` on a `t3.medium`.

> **Tip — big pastes:** The browser terminal can drop characters on very large single pastes. If a multi-line block ever gets mangled, paste it in smaller chunks or open a file with `nano` and paste there.

---

## Part 2 — Install Docker and containerlab

### Step 3. Install Docker and containerlab

Amazon Linux 2023 ships Docker in its repositories. Install and start it, then add containerlab with its package script:

```bash
sudo dnf install -y docker
sudo systemctl enable --now docker
bash -c "$(curl -sL https://get.containerlab.dev)"
```

> **Note:** The containerlab project also offers a combined `containerlab.dev/setup` installer, but it does not recognize Amazon Linux 2023. On this OS, install Docker from the `dnf` repo (above) and containerlab from its own script — that is the supported path here.

### Step 4. Enable Docker and raise the inotify limit for cEOS

Add your user to the docker group, then raise `fs.inotify.max_user_instances`. cEOS needs a high value to boot reliably — the combined installer would normally set this, so on Amazon Linux 2023 you set it yourself and make it survive reboots:

```bash
sudo usermod -aG docker $USER
newgrp docker

echo "fs.inotify.max_user_instances = 62800" | sudo tee /etc/sysctl.d/99-ceos.conf
sudo sysctl -p /etc/sysctl.d/99-ceos.conf
```

Verify the tooling and the setting:

```bash
docker --version
containerlab version
sysctl fs.inotify.max_user_instances
```

You should get version strings from both tools, and `fs.inotify.max_user_instances` should read `62800`.

---

## Part 3 — Get the cEOS Image

### Step 5. Obtain the cEOS image

Get the cEOS image file your instructor provides: the **64-bit** build, `cEOS64-lab-4.36.1F` — not the 32-bit `cEOS-lab-...` or the ARM `cEOSarm-lab-...`. Download it to your laptop, or note the link your instructor gave you.

> **Note on the filename:** The file may end in `.tar.xz` (still compressed) or `.tar`. Some browsers — including Safari on macOS — automatically decompress the `.xz` on download, leaving a `.tar`. **Use whichever name you actually have** in the commands below; `docker import` accepts either. These steps use `.tar`; if yours is `.tar.xz`, substitute that everywhere. Check with `ls` if you're unsure.

### Step 6. Copy the image to the host

If the file is on your laptop, copy it up to this EC2 host with `scp`, using the key from Lab 1.

1. Find the host's **public IPv4 address**: AWS console → **EC2 → Instances → your instance → Public IPv4 address**. If you resized the instance, the IP changed after the stop/start — use the current one.

2. From a terminal **on your laptop** (not this EC2 session), in the folder that holds the cEOS file:

   ```bash
   # Mac/Linux: make sure the key isn't world-readable, or scp refuses it
   chmod 400 /path/to/AutomationLab-Key.pem

   scp -i /path/to/AutomationLab-Key.pem cEOS64-lab-4.36.1F.tar ec2-user@<host-public-ip>:~/
   ```

   Replace the placeholders with real values: `/path/to/AutomationLab-Key.pem` is your key's actual location (often `~/Downloads/AutomationLab-Key.pem`), and `<host-public-ip>` is the address from step 1. The file is a gigabyte or two, so allow a few minutes.

   > **Windows:** `scp` works the same in PowerShell (Windows 10/11). Prefer a GUI? Use the free **WinSCP** — connect with the host's public IP, username `ec2-user`, and the `.pem` key, then drag the file across.

3. Back in this EC2 session, confirm it arrived:

   ```bash
   ls -lh ~/cEOS64-lab-4.36.1F.tar
   ```

> **Alternative — via S3:** if your instructor placed the image in an S3 bucket you can reach (this host has AWS credentials from Lab 10), pull it directly instead:
> ```bash
> aws s3 cp s3://<your-bucket>/cEOS64-lab-4.36.1F.tar .
> ```

> **If scp is refused:** use the *current* public IP, check the path to `AutomationLab-Key.pem`, and run the command from your laptop (that's where the key lives). The host accepts the key login normally — no extra SSH flags needed.

### Step 7. Import it into Docker

```bash
docker import cEOS64-lab-4.36.1F.tar ceos:4.36.1F
docker images | grep ceos
```

**Expected output:**
```
ceos   4.36.1F   <image id>   ...
```

> **Different version?** If your file is a different EOS version, use that version string as the tag here **and** in the topology file in Step 8 — the two must match.

---

## Part 4 — Deploy leaf1

### Step 8. Write the topology file

The `mgmt-ipv4` line pins `leaf1` to a fixed address so name resolution is easy. Match the `image:` tag to what you imported:

```bash
mkdir -p ~/arista-lab && cd ~/arista-lab
cat > leaf1.clab.yml << 'EOF'
name: aristalab
mgmt:
  network: clab-mgmt
  ipv4-subnet: 172.20.20.0/24
topology:
  nodes:
    leaf1:
      kind: arista_ceos
      image: ceos:4.36.1F
      mgmt-ipv4: 172.20.20.11
EOF
```

### Step 9. Deploy it

```bash
sudo containerlab deploy -t leaf1.clab.yml
```

EOS takes a minute or two to boot. When it finishes, containerlab prints a table showing the `leaf1` node running at `172.20.20.11`.

> **If `leaf1` never comes up** (the container keeps restarting, or Step 11's `docker exec ... Cli` fails to connect): confirm the inotify limit from Step 4 with `sysctl fs.inotify.max_user_instances` (it must be `62800`, not the low default), and check the boot log with `docker logs clab-aristalab-leaf1`. A too-low inotify limit is the most common cause of a cEOS node that deploys but won't finish booting.

### Step 10. Make the hostname resolve

So the lab scripts' `leaf1` hostname works:

```bash
echo "172.20.20.11 leaf1" | sudo tee -a /etc/hosts
```

---

## Part 5 — Configure the Switch

### Step 11. Create the lab login and enable eAPI

Drop into the switch CLI:

```bash
docker exec -it clab-aristalab-leaf1 Cli
```

> **Switch vs. host — watch your prompt.** Once you're in, the prompt becomes `leaf1>` or `leaf1#`. That means you are **on the switch**, where only EOS commands work. A prompt like `[ec2-user@ip-... ]$` means you are **on the host**, where Linux commands (`docker`, `curl`, `ping`) work. Running a host command on the switch gives `% Invalid input`, and vice versa. Check the prompt before every command in this part of the lab.

At the switch prompt, run the following. This creates the `arista` user with the course lab password `Arista123!` and turns on eAPI:

```
enable
configure
username arista privilege 15 role network-admin secret Arista123!
management api http-commands
   no shutdown
   protocol https
end
write memory
```

> **Lab password:** `Arista123!` is a throwaway credential for this isolated lab container only. Every script in Labs 14 and 15 uses it. Never use a password like this on a real device.

### Step 12. Confirm eAPI is running

```
show management api http-commands
```

**Expected output (abridged):**
```
Enabled:            Yes
HTTPS server:       running, set to use port 443
...
```

Then leave the switch and return to the host:

```
exit
```

Your prompt should read `[ec2-user@... ]$` again — you need to be on the host for the verification steps below.

---

## Part 6 — Verify

### Step 13. Reach the switch from the host

From the **host** prompt (`[ec2-user@... ]$`), check connectivity and log in:

```bash
ping -c 2 leaf1
ssh arista@leaf1
```

Log in with `Arista123!` and run `show version` to confirm you see `cEOSLab`. That `ssh` puts you back **on the switch** (`leaf1>`), so return to the host before the next step:

```
exit
```

Confirm your prompt reads `[ec2-user@... ]$` again — the next command is a host command and will fail on the switch.

### Step 14. Confirm eAPI answers over HTTPS

Run this **on the host** (prompt `$`). It sends a real eAPI request — a JSON-RPC `POST` — and prints the HTTP status:

```bash
curl -k -u arista:Arista123! https://leaf1/command-api \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"runCmds","params":{"version":1,"cmds":["show hostname"],"format":"json"},"id":"health"}' \
  -o /dev/null -w "%{http_code}\n"
```

**Expected output:**
```
200
```

A `200` means eAPI is reachable and your credentials work — `leaf1` is ready for Lab 14.

> **Why POST, and what about 405?** The eAPI endpoint only accepts `POST` requests carrying a JSON-RPC body. A plain `curl https://leaf1/command-api` sends a `GET` and returns `405 Method Not Allowed` — which actually confirms eAPI is listening, but the `POST` above is the real end-to-end check. A `401` would mean the username/password is wrong; a connection refused or timeout means eAPI isn't enabled or reachable (re-check Step 11).

---

## Verification Checklist

| Task | Expected Result | Pass/Fail |
|------|-----------------|-----------|
| Host resized | `free -h` shows ~3.8 Gi | |
| containerlab installed | `containerlab version` prints a version | |
| System prepared for cEOS | `sysctl fs.inotify.max_user_instances` = 62800 | |
| cEOS image imported | `docker images` lists `ceos` | |
| `leaf1` deployed | containerlab table shows it running | |
| Hostname resolves | `ping leaf1` succeeds | |
| eAPI enabled | `show management api http-commands` → Enabled: Yes | |
| eAPI reachable | `curl` to `/command-api` returns `200` | |

---

## Reflection Questions

1. Why does cEOS run as a container while the Cisco C8000V ran as a full EC2 instance? What are the trade-offs?
2. What does containerlab do for you that plain `docker run` would not?
3. eAPI listens on HTTPS 443. Which earlier lab used HTTPS 443 to a Cisco device, and what was that protocol called?
4. Why pin `leaf1` to a fixed management IP instead of letting Docker assign one?

---

## Summary

| Concept | Key Point |
|---------|-----------|
| cEOS-lab | Arista EOS packaged as a container — a real switch, no VM or hardware |
| containerlab | Deploys container-based network topologies from a small YAML file |
| `docker import` | Loads the cEOS tarball as a usable Docker image |
| `arista_ceos` kind | Tells containerlab how to run and wire a cEOS node |
| eAPI | The EOS JSON-RPC API over HTTPS — the front door for Labs 14–15 |
| Single host | Your EC2 host runs both the switch container and your automation code |

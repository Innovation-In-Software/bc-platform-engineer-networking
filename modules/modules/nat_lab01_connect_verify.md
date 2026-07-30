# Lab 1 – Connect and Verify

**Course:** Network Automation Tools — Day 1  
**Objective:** Provision your AWS lab environment, install Ansible on your control node, and verify that Ansible can reach both Cisco Catalyst 8000V targets.

---

## Overview

Before writing a single playbook you need a working lab environment. In this lab you will:

1. Accept the Catalyst 8000V Marketplace terms
2. Create a VPC and subnets
3. Launch a control node EC2 instance
4. Launch two Catalyst 8000V routers
5. Install Ansible on the control node
6. Write an inventory file
7. Run your first Ansible ad-hoc command against both routers

---

## Part 1 — Accept Marketplace Terms

You must subscribe to the Catalyst 8000V before you can launch instances. This only needs to be done once per AWS account.

1. Go to **AWS Marketplace** and search for **Cisco Catalyst 8000V SD-WAN & Router - PAYG - DNA Essentials**
2. Click the listing → **Try for free** → **Subscribe**
3. On the subscription page click **Set up your account**
4. Wait for the subscription status to show **Active** — this can take 1-2 minutes

> **Note:** This is a free trial at the account level. All IAM users on this account benefit from it. You will only be charged EC2 instance costs — there is no Cisco software charge during the trial period.

---

## Part 2 — Build the VPC

### Step 1. Create the VPC

1. Go to **VPC → Your VPCs → Create VPC**
2. Configure:
   - **Name tag:** `AutomationLab-VPC`
   - **IPv4 CIDR block:** `10.0.1.0/24`
   - Leave all other settings as default
3. Click **Create VPC**

### Step 2. Create a subnet

1. Go to **VPC → Subnets → Create Subnet**
2. Configure:
   - **VPC:** `AutomationLab-VPC`
   - **Subnet name:** `AutomationLab-Subnet`
   - **Availability Zone:** pick any — note which one you choose, all instances must be in the same AZ
   - **IPv4 VPC CIDR block:** select `10.0.1.0/24` from the dropdown (this is the parent VPC's block)
   - **IPv4 subnet CIDR block:** `10.0.1.0/24`
3. Click **Create subnet**
4. Select the subnet → **Actions → Edit subnet settings** → check **Enable auto-assign public IPv4 address** → **Save**

### Step 3. Create and attach an Internet Gateway

1. Go to **VPC → Internet Gateways → Create internet gateway**
   - **Name tag:** `AutomationLab-IGW`
2. Click **Create internet gateway**
3. Select the IGW → **Actions → Attach to VPC** → select `AutomationLab-VPC` → **Attach**

### Step 4. Update the route table

1. Go to **VPC → Route Tables**
2. Find the route table associated with `AutomationLab-VPC`
3. Select it → **Routes → Edit routes → Add route**:
   - **Destination:** `0.0.0.0/0`
   - **Target:** select **Internet Gateway** → choose `AutomationLab-IGW`
4. Click **Save changes**

---

## Part 3 — Create a Security Group

1. Go to **EC2 → Security Groups → Create security group**
2. Configure:
   - **Name:** `AutomationLab-SG`
   - **Description:** `Lab security group for automation course`
   - **VPC:** `AutomationLab-VPC`
3. Add inbound rules:

| Type | Protocol | Port | Source | Purpose |
|------|----------|------|--------|---------|
| SSH | TCP | 22 | 0.0.0.0/0 | SSH access |
| Custom TCP | TCP | 830 | 10.0.1.0/24 | NETCONF |
| Custom TCP | TCP | 443 | 10.0.1.0/24 | RESTCONF |
| All ICMP - IPv4 | ICMP | All | 10.0.1.0/24 | Ping within lab |

4. Leave outbound rules as default (allow all)
5. Click **Create security group**

> **Note:** The SSH rule (port 22 from `0.0.0.0/0`) is what allows you to reach the control node with EC2 Instance Connect in Part 7. Keep it in place.

---

## Part 4 — Create a Key Pair

1. Go to **EC2 → Key Pairs → Create key pair**
2. Configure:
   - **Name:** `AutomationLab-Key`
   - **Key pair type:** RSA
   - **Private key file format:** `.pem`
3. Click **Create key pair** — the `.pem` file downloads automatically
4. Save it somewhere safe — you will need it throughout the course

---

## Part 5 — Launch the Control Node

1. Go to **EC2 → Launch Instance**
2. Configure:
   - **Name:** `control-node`
   - **AMI:** Amazon Linux 2023 AMI (free tier eligible)
   - **Instance type:** `t2.micro`
   - **Key pair:** `AutomationLab-Key`
3. Under **Network settings → Edit**:
   - **VPC:** `AutomationLab-VPC`
   - **Subnet:** `AutomationLab-Subnet`
   - **Auto-assign public IP:** Enable
   - **Firewall:** Select existing security group → `AutomationLab-SG`
4. Leave storage as default
5. Click **Launch instance**

---

## Part 6 — Launch Two Catalyst 8000V Routers

Repeat these steps twice — once for `c8kv-1` and once for `c8kv-2`.

### Step 5. Launch c8kv-1

1. Go to **EC2 → Launch Instance**
2. Click **Browse more AMIs → AWS Marketplace AMIs**
3. Search for **Cisco Catalyst 8000V SD-WAN & Router - PAYG - DNA Essentials**
4. Select it and click **Select**
5. Configure:
   - **Name:** `c8kv-1`
   - **Instance type:** `t3.medium` — minimum required for the Catalyst 8000V
   - **Key pair:** `AutomationLab-Key`
6. Under **Network settings → Edit**:
   - **VPC:** `AutomationLab-VPC`
   - **Subnet:** `AutomationLab-Subnet`
   - **Auto-assign public IP:** Enable
   - **Firewall:** Select existing security group → `AutomationLab-SG`
7. Leave storage as default
8. Click **Launch instance**

### Step 6. Launch c8kv-2

Repeat Step 5 with the name `c8kv-2`. Everything else is identical.

> **Boot time:** The Catalyst 8000V takes 4-6 minutes to fully boot IOS-XE after the instance shows Running. Wait until both instances show **2/2 status checks passed** before continuing.

### Step 7. Note all three private IPs

Go to **EC2 → Instances** and note the **Private IPv4 address** for each:

| Instance | Private IP | Role |
|----------|------------|------|
| control-node | | Ansible control node |
| c8kv-1 | | First managed router |
| c8kv-2 | | Second managed router |

> All three instances must be in the same subnet for private IP connectivity to work.

---

## Part 7 — Install Ansible on the Control Node

### Step 8. Connect via EC2 Instance Connect

EC2 Instance Connect gives you a browser-based shell using a temporary SSH key that AWS generates for the session. It needs **no IAM role, no SSM agent setup, and no private key of your own** — it works because your control node has a public IP and `AutomationLab-SG` already allows SSH (port 22) inbound.

1. Go to **EC2 → Instances → control-node**
2. Select it → **Connect**
3. Choose the **EC2 Instance Connect** tab
4. Make sure **Connect using EC2 Instance Connect** is selected (not the *Endpoint* option, which is for private instances)
5. **Username:** `ec2-user` (this should already be filled in)
6. Click **Connect**
7. A browser-based terminal opens — you are now on your control node

> **Troubleshooting:** If **Connect** is greyed out or the session fails, confirm two things that were set up earlier in this lab: the control node has a **public IPv4 address** (Part 5, auto-assign enabled), and `AutomationLab-SG` allows inbound **SSH (TCP 22)** from `0.0.0.0/0` (Part 3). Both are prerequisites for Instance Connect.

### Step 9. Install Ansible

```bash
sudo dnf update -y
sudo dnf install -y python3 python3-pip
pip3 install ansible --user
pip3 install ansible-pylibssh --user
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
source ~/.bashrc
ansible --version
```

**Expected output:**
```
ansible [core 2.x.x]
  python version = 3.x.x
```

> **Why `ansible-pylibssh`?** Ansible's `network_cli` connection needs a Python SSH transport library to talk to the routers, and it is **not** included with Ansible or the `cisco.ios` collection. Without it, your first playbook fails with `paramiko is not installed` or `ansible-pylibssh not installed`. `ansible-pylibssh` is the transport Ansible prefers for network devices — install it now and later labs "just connect."

### Step 10. Install the cisco.ios collection

```bash
ansible-galaxy collection install cisco.ios
ansible-galaxy collection list | grep cisco
```

**Expected output:**
```
cisco.ios    x.x.x
```

### Step 11. Place your key on the control node

You need the `.pem` file on the control node to SSH to the routers. Because you are connected through EC2 Instance Connect (a browser terminal), you cannot `scp` the file up — you are already *on* the control node, so instead you'll recreate the key on it by pasting its contents into a file with `nano`.

1. On the control node, make sure the `.ssh` directory exists:

   ```bash
   mkdir -p ~/.ssh
   ```

2. On your **local machine**, open `AutomationLab-Key.pem` in a text editor and copy its entire contents — everything from `-----BEGIN RSA PRIVATE KEY-----` through `-----END RSA PRIVATE KEY-----`, inclusive.

3. Back in the Instance Connect terminal, open a new file with nano:

   ```bash
   nano ~/.ssh/AutomationLab-Key.pem
   ```

4. Paste the copied key into nano. Make sure nothing follows the `-----END RSA PRIVATE KEY-----` line.

5. Save and exit: **Ctrl-O**, then **Enter**, then **Ctrl-X**.

6. Set correct permissions:

   ```bash
   chmod 400 ~/.ssh/AutomationLab-Key.pem
   ```

7. Verify the file is intact:

   ```bash
   head -1 ~/.ssh/AutomationLab-Key.pem   # -----BEGIN RSA PRIVATE KEY-----
   tail -1 ~/.ssh/AutomationLab-Key.pem   # -----END RSA PRIVATE KEY-----
   ```

   The last line must be the `END` line — **not** a `chmod` command or any other text. If it isn't, reopen the file in nano and delete the stray trailing line.

> **Why nano and not a heredoc?** A `cat > file << 'EOF'` heredoc requires the closing `EOF` to be on its own line. If it isn't, the shell keeps reading input (you'll see a `>` prompt) and swallows your next command — including `chmod` — into the file. `nano` avoids this failure mode entirely.

> **Security note:** Your private key is a secret. Only paste it into a terminal you control (like this Instance Connect session) — never into a chat, ticket, email, or web form. When you finish the course, delete the `AutomationLab-Key` key pair in **EC2 → Key Pairs** and generate a fresh key rather than reusing this one elsewhere.

> **Alternative (local terminal):** If you are instead working from your own machine's terminal rather than Instance Connect, you can copy the key up directly with `scp -i AutomationLab-Key.pem AutomationLab-Key.pem ec2-user@<control-node-public-ip>:~/.ssh/` and then run the `chmod 400` on the control node.

### Step 11b. Enable the ssh-rsa algorithm for manual SSH (required)

You will use the `.pem` key to make an **initial** SSH connection to each router — just enough to log in and create a username/password login that Ansible will use afterward. That first connection needs a small fix.

The EC2 key is an **RSA** key, and modern OpenSSH on Amazon Linux 2023 disables the legacy `ssh-rsa` signature algorithm by default. Without enabling it, the connection fails with `sign_and_send_pubkey: no mutual signature supported`. Add a matching SSH config block on the control node so it's handled automatically:

```bash
cat >> ~/.ssh/config << 'EOF'
Host 10.0.1.*
    PubkeyAcceptedAlgorithms +ssh-rsa
    HostKeyAlgorithms +ssh-rsa
    IdentityFile ~/.ssh/AutomationLab-Key.pem
    User ec2-user
EOF
chmod 600 ~/.ssh/config
```

> **Note:** This config is only for your **manual** SSH connections in Step 12. Ansible does **not** use this file — it connects using its own libssh transport with the username/password you'll configure in Step 12, which avoids the SSH key-algorithm issues entirely. That's why the labs use password authentication for Ansible: it's the reliable path on this control-node environment.

### Step 12. Connect to each router and create an Ansible login

You'll SSH to each router with the key, then configure a **username and password** that Ansible will use. Start with c8kv-1:

```bash
ssh <c8kv-1-private-ip>
```

**Expected output** (the prompt reflects the router's hostname):
```
ip-10-0-1-183#
```

The trailing `#` confirms you are at the IOS-XE privileged-exec prompt. Run `show version` and confirm you see `Cisco IOS XE Software`.

Now create the login Ansible will use. Enter configuration mode and add an enable secret and a privilege-15 user:

```
conf t
enable secret Cisco123!
username ansible privilege 15 secret Cisco123!
line vty 0 4
 login local
 transport input ssh
end
write memory
```

Type `exit` to return to the control node. **Repeat every step above for c8kv-2** using its private IP.

> **Lab password:** `Cisco123!` is a throwaway credential for this isolated lab only. The routers sit in a private subnet and are deleted at the end of the course. Never use a password like this on a real device.

> **Verify the new login before moving on.** From the control node, log in as the new user to confirm password auth works:
> ```bash
> ssh ansible@<c8kv-1-private-ip>
> ```
> Enter `Cisco123!`. Landing on a `ip-10-0-1-183#` prompt confirms Ansible will be able to connect. Type `exit`.

> **Troubleshooting:**
> - `sign_and_send_pubkey: no mutual signature supported` on the *key* login → the `ssh-rsa` config from Step 11b isn't in place.
> - A `$` prompt instead of `#` → IOS-XE is still booting; wait 2-3 minutes.
> - The `ansible` password login is rejected → re-check the `line vty 0 4 / login local` lines were applied and saved with `write memory`.

---

## Part 8 — Configure Ansible and the Inventory

### Step 13. Create your working directory

```bash
mkdir ~/ansible-lab
cd ~/ansible-lab
```

### Step 14. Create ansible.cfg

Ansible does not automatically find an inventory in the current directory, and it prompts on unknown SSH host keys. This config file fixes both, so later labs run with a plain `ansible-playbook <file>`:

```bash
cat > ansible.cfg << 'EOF'
[defaults]
inventory = inventory.yml
host_key_checking = False

[persistent_connection]
connect_timeout = 60
EOF
```

### Step 15. Create inventory.yml

This inventory uses the **username/password** you configured on the routers (not the SSH key). The one libssh line, `ansible_libssh_hostkeys: ssh-rsa`, is required so Ansible accepts the router's host key. Replace the IPs with the actual private IPs from Step 7:

```bash
cat > inventory.yml << 'EOF'
all:
  children:
    routers:
      hosts:
        c8kv-1:
          ansible_host: 10.0.1.X
        c8kv-2:
          ansible_host: 10.0.1.Y
      vars:
        ansible_network_os: ios
        ansible_connection: network_cli
        ansible_network_cli_ssh_type: libssh
        ansible_user: ansible
        ansible_password: Cisco123!
        ansible_libssh_hostkeys: ssh-rsa
        ansible_become: yes
        ansible_become_method: enable
        ansible_become_password: Cisco123!
EOF
```

### Step 16. Verify Ansible can reach both routers

Run a quick ad-hoc command to confirm end-to-end connectivity:

```bash
ansible routers -m cisco.ios.ios_command -a "commands='show version'"
```

**Expected:** both `c8kv-1` and `c8kv-2` return `SUCCESS` with `show version` output. If you see that, your lab environment is fully working and you're ready for Lab 2.

> **Troubleshooting:**
> - `ansible-pylibssh not installed` → the transport library wasn't installed; run `pip3 install ansible-pylibssh --user` (Step 9).
> - `Failed to authenticate` → the `ansible` user/password doesn't match; recheck Step 12 and the inventory.
> - `no matching host key` → confirm the `ansible_libssh_hostkeys: ssh-rsa` line is present in the inventory.

# Lab 7 – Connect with Netmiko

**Course:** Network Automation Tools — Day 3  
**Prerequisite:** Labs 1–6 complete — both Catalyst 8000V routers reachable, the `ansible` / `Cisco123!` login working on each (created in Lab 1), and their private IPs noted  
**Objective:** Leave Ansible behind for the day and drive the routers directly from Python. Set up a virtual environment, install Netmiko, connect over SSH, run show commands, loop over both devices, and handle failures gracefully.

---

> **Remember:** Stop the `c8kv-1` and `c8kv-2` instances when you finish this lab to avoid unnecessary charges. Go to **EC2 → Instances → select both routers → Instance State → Stop**.

## Overview

Netmiko is the most common first tool for Python network automation. It wraps SSH and handles the awkward parts — prompts, paging, and timing — so you can focus on commands and output. In this lab you will:

1. Create and activate a Python virtual environment
2. Install Netmiko with `pip`
3. Connect to one router and run a show command
4. Loop over both routers, running several commands on each
5. Save the collected output to files
6. Add error handling so one bad device does not stop the run

---

## Part 1 — Set Up the Python Environment

### Step 1. Create a working directory and virtual environment

Work from the control node. Keep the Python labs separate from your Ansible labs.

```bash
mkdir ~/python-lab
cd ~/python-lab
python3 -m venv venv
source venv/bin/activate
```

Your prompt should now start with `(venv)`, showing the environment is active.

### Step 2. Install Netmiko

```bash
pip install netmiko
pip list | grep -i netmiko
```

**Expected output:**
```
netmiko    4.x.x
```

> **Note:** Installing Netmiko also installs Paramiko, the underlying SSH library. Everything installs inside `venv/`, not into the system Python.

---

## Part 2 — Connect to One Device

### Step 3. Create the connection script

The device dictionary holds everything Netmiko needs to log in. You connect with the **`ansible` username and password** you configured on both routers in Lab 1 — the same credentials the Ansible labs used. Replace `10.0.1.X` with the private IP of `c8kv-1`.

```bash
cat > connect_one.py << 'EOF'
from netmiko import ConnectHandler

device = {
    "device_type": "cisco_ios",
    "host": "10.0.1.X",
    "username": "ansible",
    "password": "Cisco123!",
}

connection = ConnectHandler(**device)
output = connection.send_command("show version")
print(output)
connection.disconnect()
EOF
```

> **Why password auth and not the SSH key?** The EC2 key is an **RSA** key, and these routers only accept the legacy `ssh-rsa` (SHA-1) signature — the same constraint you hit in Lab 1 Step 11b, where OpenSSH needed `PubkeyAcceptedAlgorithms +ssh-rsa`. Netmiko connects through **Paramiko**, not OpenSSH, so that `~/.ssh/config` fix does not apply, and modern Paramiko will not sign with `ssh-rsa` unless its own algorithm list happens to allow it — behavior that varies by Paramiko version and often fails outright with `no RSA pubkey algorithms are configured` or `Authentication (publickey) failed`. Password authentication sidesteps the whole RSA-signature negotiation, which is exactly why Labs 1–6 use the `ansible` password login for automation. It is the reliable path on this control-node environment.
>
> **Lab password reminder:** `Cisco123!` is the throwaway credential from Lab 1, used only for these isolated lab routers. Never hard-code a real password in a script — in production you would pull it from a vault or environment variable (as you saw in Lab 6).

### Step 4. Run it

```bash
python3 connect_one.py
```

**Expected output (abridged):**
```
Cisco IOS XE Software, Version 17.x
...
c8kv-1 uptime is ...
```

| Line | What it does |
|------|-------------|
| `device_type: cisco_ios` | Selects the IOS CLI driver |
| `username: ansible` | The privilege-15 login you created on the routers in Lab 1 |
| `password: Cisco123!` | That user's password — no SSH key needed |
| `send_command("show version")` | Runs one show command, returns text |
| `disconnect()` | Closes the SSH session cleanly |

> **Troubleshooting the connection:**
> - `Authentication to ... failed` → the `ansible` username/password does not match. Re-check Lab 1 Step 12 (`username ansible privilege 15 secret Cisco123!` and `line vty 0 4 / login local`), and confirm you can `ssh ansible@<router-ip>` manually.
> - The connection hangs, then times out → the router may still be booting, or you used the wrong private IP.
> - `no RSA pubkey algorithms are configured` / `Authentication (publickey) failed` → you are still using the key-based device dictionary. Switch to the `username`/`password` form shown above (see the note under Step 3 for why).

---

## Part 3 — Loop Over Both Routers

### Step 5. Create a multi-device script

Put both routers in a list and run the same commands on each. Replace both IPs with your actual private addresses.

```bash
cat > collect.py << 'EOF'
from netmiko import ConnectHandler

USER = "ansible"
PASSWORD = "Cisco123!"

devices = [
    {"device_type": "cisco_ios", "host": "10.0.1.X", "username": USER, "password": PASSWORD},
    {"device_type": "cisco_ios", "host": "10.0.1.Y", "username": USER, "password": PASSWORD},
]

commands = ["show ip interface brief", "show ip route"]

for device in devices:
    connection = ConnectHandler(**device)
    hostname = connection.find_prompt().strip("#>")
    print(f"\n===== {hostname} ({device['host']}) =====")
    for command in commands:
        print(f"\n--- {command} ---")
        print(connection.send_command(command))
    connection.disconnect()
EOF
```

### Step 6. Run it

```bash
python3 collect.py
```

You should see a labelled block of output for **each** router. This is the core pattern of Python automation: write the logic once, then loop it over a device list.

---

## Part 4 — Save Output and Handle Errors

### Step 7. Add file saving and error handling

Real networks have unreachable devices and bad credentials. Wrap each connection so one failure does not stop the whole run, and write each device's output to its own file.

```bash
cat > collect_safe.py << 'EOF'
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

USER = "ansible"
PASSWORD = "Cisco123!"

devices = [
    {"device_type": "cisco_ios", "host": "10.0.1.X", "username": USER, "password": PASSWORD},
    {"device_type": "cisco_ios", "host": "10.0.1.Y", "username": USER, "password": PASSWORD},
]

for device in devices:
    host = device["host"]
    try:
        connection = ConnectHandler(**device)
        hostname = connection.find_prompt().strip("#>")
        output = connection.send_command("show ip interface brief")
        connection.disconnect()

        with open(f"{hostname}_interfaces.txt", "w") as f:
            f.write(output)
        print(f"{host}: collected and saved as {hostname}_interfaces.txt")

    except NetmikoTimeoutException:
        print(f"{host}: TIMEOUT - is the router booted and reachable?")
    except NetmikoAuthenticationException:
        print(f"{host}: AUTH FAILED - check the username/password")
EOF
```

### Step 8. Run it and confirm the files

```bash
python3 collect_safe.py
ls *_interfaces.txt
cat c8kv-1_interfaces.txt
```

### Step 9. Test the error handling

Temporarily change one IP in `collect_safe.py` to an unused address such as `10.0.1.250` and re-run. That device should report `TIMEOUT` while the other still collects successfully — proving one bad device no longer breaks the run.

> **Note:** When you finish, deactivate the environment with `deactivate`. The `venv` stays on disk for the next lab.

---

## Verification Checklist

| Task | Expected Result | Pass/Fail |
|------|-----------------|-----------|
| Virtual environment active | Prompt shows `(venv)` | |
| Netmiko installed | `pip list` shows netmiko | |
| `connect_one.py` runs | `show version` output printed | |
| `collect.py` loops both routers | Labelled output for each device | |
| Output files created | `c8kv-1_interfaces.txt`, `c8kv-2_interfaces.txt` | |
| Error handling works | Bad IP reports TIMEOUT, others succeed | |

---

## Reflection Questions

1. Why use a virtual environment instead of installing Netmiko system-wide?
2. What does `device_type: cisco_ios` control, and why does it matter?
3. How would you extend `collect.py` to run against ten routers instead of two?
4. Why is wrapping each connection in `try`/`except` important on a real network?

---

## Summary

| Concept | Key Point |
|---------|-----------|
| `venv` | Isolates project packages from the system Python |
| `ConnectHandler(**device)` | Opens an SSH session using a device dictionary |
| `username` / `password` | Password auth with the `ansible` login from Lab 1 — the reliable path on these routers |
| Why not the SSH key | The RSA key needs the legacy `ssh-rsa` signature, which modern Paramiko often won't send; password auth avoids the issue |
| `send_command()` | Runs one show command, returns text |
| Loop over a device list | Scales one script across many devices |
| `try` / `except` | Lets one device fail without stopping the run |
| `with open()` | Saves collected output to disk safely |

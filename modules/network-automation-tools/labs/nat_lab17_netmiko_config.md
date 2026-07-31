# Lab 17 – Config Changes with Netmiko and Jinja2

**Course:** Network Automation Tools — Day 3  
**Prerequisite:** Labs 7–9 complete — `~/python-lab` with a virtual environment and Netmiko installed; both routers reachable with the `ansible` / `Cisco123!` login from Lab 1  
**Objective:** Move from reading devices to changing them. Back up the running configuration first, push a change with `send_config_set`, generate per-device configuration from a Jinja2 template, save it, and prove what changed with a diff.

---

> **Remember:** Stop the `c8kv-1` and `c8kv-2` instances when you finish this lab to avoid unnecessary charges. Go to **EC2 → Instances → select both routers → Instance State → Stop**.

> **If you stopped your instances after Lab 9:** start them again and give them 3–4 minutes to boot. **Private IPs do not change** across a stop/start, so the addresses you have been using are still correct. Only the public IP changes.

## Overview

Reading is safe; writing is where automation earns its keep — and where it can do damage. The professional pattern is always the same: back up, change, verify, diff. In this lab you will:

1. Back up the running configuration of both routers to timestamped files
2. Push a configuration change with `send_config_set`
3. Save the change to startup-config from Python
4. Generate per-device configuration from a Jinja2 template
5. Diff the running configuration against the backup to prove what changed

---

> ## ⚠ Never configure GigabitEthernet1
>
> `GigabitEthernet1` is the AWS-facing interface that carries your SSH session. Shutting it down, changing its IP, or removing it will **lock you out of the router permanently** — there is no console access on these instances and the only fix is to terminate and rebuild.
>
> Every change in this lab targets **loopback interfaces only**. Loopbacks are virtual, always safe, and cannot break connectivity.

---

## Part 1 — Back Up Before You Change

### Step 1. Activate your environment

```bash
cd ~/python-lab
source venv/bin/activate
```

Your prompt should show `(venv)`.

### Step 2. Create the backup script

This pulls `show running-config` from each router and writes it to a timestamped file under `backups/`. Replace both IPs with your private addresses.

```bash
cat > backup_configs.py << 'EOF'
from datetime import datetime
from pathlib import Path

from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

USER = "ansible"
PASSWORD = "Cisco123!"

devices = [
    {"device_type": "cisco_ios", "host": "10.0.1.X", "username": USER, "password": PASSWORD},
    {"device_type": "cisco_ios", "host": "10.0.1.Y", "username": USER, "password": PASSWORD},
]

BACKUP_DIR = Path("backups")
BACKUP_DIR.mkdir(exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

for device in devices:
    host = device["host"]
    try:
        connection = ConnectHandler(**device)
        hostname = connection.find_prompt().strip("#>")
        running = connection.send_command("show running-config", read_timeout=90)
        connection.disconnect()

        path = BACKUP_DIR / f"{hostname}-{stamp}.cfg"
        path.write_text(running)
        print(f"{host}: saved {path} ({len(running.splitlines())} lines)")

    except NetmikoTimeoutException:
        print(f"{host}: TIMEOUT - is the router booted and reachable?")
    except NetmikoAuthenticationException:
        print(f"{host}: AUTH FAILED - check the username/password")
EOF
```

### Step 3. Run it and inspect a backup

```bash
python3 backup_configs.py
ls -l backups/
head -20 backups/c8kv-1-*.cfg
```

**Expected output:**
```
10.0.1.X: saved backups/c8kv-1-20260730-141205.cfg (312 lines)
10.0.1.Y: saved backups/c8kv-2-20260730-141205.cfg (298 lines)
```

| Line | What it does |
|------|-------------|
| `read_timeout=90` | `show running-config` is long — give Netmiko time to read it all |
| `find_prompt().strip("#>")` | Uses the device's own hostname for the filename |
| `BACKUP_DIR.mkdir(exist_ok=True)` | Creates `backups/` once, silently, if it isn't there |
| `datetime.now().strftime(...)` | One timestamp for the whole run, so a set of backups sorts together |

> **Note:** Keep this backup. Part 4 diffs against it, and it is your rollback if a change goes wrong.

---

## Part 2 — Push a Change with `send_config_set`

`send_command()` runs show commands. To send configuration you use **`send_config_set()`**, which enters config mode for you, sends every line in the list, and exits when it is done.

### Step 4. Create the push script

Replace the IP with `c8kv-1`.

```bash
cat > push_loopback.py << 'EOF'
from netmiko import ConnectHandler

device = {
    "device_type": "cisco_ios",
    "host": "10.0.1.X",
    "username": "ansible",
    "password": "Cisco123!",
}

config_commands = [
    "interface Loopback1",
    " description Pushed by Netmiko",
    " ip address 172.16.10.1 255.255.255.255",
]

connection = ConnectHandler(**device)

output = connection.send_config_set(config_commands)
print(output)

connection.save_config()
print("--- saved to startup-config ---")

print(connection.send_command("show running-config interface Loopback1"))
connection.disconnect()
EOF
```

### Step 5. Run it

```bash
python3 push_loopback.py
```

**Expected output (abridged):**
```
configure terminal
c8kv-1(config)#interface Loopback1
c8kv-1(config-if)# description Pushed by Netmiko
c8kv-1(config-if)# ip address 172.16.10.1 255.255.255.255
c8kv-1(config-if)#end
c8kv-1#
--- saved to startup-config ---
Building configuration...

interface Loopback1
 description Pushed by Netmiko
 ip address 172.16.10.1 255.255.255.255
end
```

Netmiko echoes the whole config-mode session back to you. That echo is the device's own record of what it accepted — read it, don't skip it.

| Element | What it does |
|---------|-------------|
| `send_config_set(list)` | Enters config mode, sends each line, exits config mode |
| `save_config()` | Runs `write memory` so the change survives a reload or an EC2 stop/start |
| `show running-config interface Loopback1` | Verifies from the device, not from your assumptions |

> **Troubleshooting:**
> - `% Invalid input detected` in the echoed output → a typo in one of your config lines. The device rejected that line and moved on; the rest still applied. Fix and re-run.
> - `save_config()` raises a read timeout → `write memory` took longer than the default. Replace it with `connection.send_command("write memory", read_timeout=60)`.
> - `TypeError: ... unexpected keyword argument 'read_timeout'` → you are on Netmiko 3.x. Run `pip install --upgrade netmiko` inside the active `venv`.

### Step 6. Run it a second time

```bash
python3 push_loopback.py
```

It succeeds again, with the same result. IOS configuration commands are **convergent** — re-sending them sets the same values — but Netmiko itself has no idea whether anything changed. Contrast that with Ansible's `ios_config`, which reports `changed: false`, and with the RESTCONF PATCH in Lab 9, which declares desired state. With Netmiko you get control; you supply the intelligence yourself.

---

## Part 3 — Generate Config from a Jinja2 Template

Hard-coding `172.16.10.1` in the script does not scale. Separate the **template** from the **data**.

### Step 7. Install Jinja2

```bash
pip install jinja2
```

### Step 8. Create the template

```bash
cat > loopback.j2 << 'EOF'
interface Loopback1
 description {{ description }}
 ip address {{ loopback_ip }} 255.255.255.255
 no shutdown
EOF
```

### Step 9. Create the template-driven push script

Replace both IPs.

```bash
cat > push_template.py << 'EOF'
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler

USER = "ansible"
PASSWORD = "Cisco123!"

devices = [
    {"host": "10.0.1.X", "loopback_ip": "172.16.10.1", "description": "Site A loopback"},
    {"host": "10.0.1.Y", "loopback_ip": "172.16.10.2", "description": "Site B loopback"},
]

env = Environment(loader=FileSystemLoader("."), trim_blocks=True, lstrip_blocks=True)
template = env.get_template("loopback.j2")

for entry in devices:
    config = template.render(**entry)

    print(f"\n===== {entry['host']} =====")
    print(config)

    connection = ConnectHandler(
        device_type="cisco_ios",
        host=entry["host"],
        username=USER,
        password=PASSWORD,
    )

    output = connection.send_config_set(config.splitlines())

    if "Invalid input" in output or "Incomplete command" in output:
        print("!! the device rejected part of this config:")
        print(output)
    else:
        connection.save_config()
        print(connection.send_command("show running-config interface Loopback1"))

    connection.disconnect()
EOF
```

### Step 10. Run it

```bash
python3 push_template.py
```

**Expected output (abridged):**
```
===== 10.0.1.X =====
interface Loopback1
 description Site A loopback
 ip address 172.16.10.1 255.255.255.255
 no shutdown

interface Loopback1
 description Site A loopback
 ip address 172.16.10.1 255.255.255.255
end

===== 10.0.1.Y =====
interface Loopback1
 description Site B loopback
 ip address 172.16.10.2 255.255.255.255
 no shutdown
...
```

Each router got its own values from one template. Adding a third router is now one dictionary in the list — no new logic.

> **Keep these descriptions.** Lab 11 audits both routers against exactly `Site A loopback` and `Site B loopback`. If you change the wording here, change it there too.

| Element | What it does |
|---------|-------------|
| `FileSystemLoader(".")` | Looks for templates in the current directory |
| `template.render(**entry)` | Substitutes `{{ }}` variables with this device's values |
| `config.splitlines()` | Turns the rendered text block into the list `send_config_set` expects |
| Checking the output | Catches a rejected line before you report success |

---

## Part 4 — Prove What Changed

A backup you never compare against is just a file. `difflib` turns two configs into a readable change record.

### Step 11. Create the diff script

Replace the IP with `c8kv-1`.

```bash
cat > diff_config.py << 'EOF'
import difflib
from pathlib import Path

from netmiko import ConnectHandler

NOISE = (
    "Building configuration",
    "Current configuration",
    "! Last configuration change",
    "! NVRAM config last updated",
)


def clean(text):
    """Drop blank lines and the lines that change on every capture."""
    return [
        line.rstrip()
        for line in text.splitlines()
        if line.strip() and not line.startswith(NOISE)
    ]


device = {
    "device_type": "cisco_ios",
    "host": "10.0.1.X",
    "username": "ansible",
    "password": "Cisco123!",
}

connection = ConnectHandler(**device)
hostname = connection.find_prompt().strip("#>")
current = connection.send_command("show running-config", read_timeout=90)
connection.disconnect()

backups = sorted(Path("backups").glob(f"{hostname}-*.cfg"))
if not backups:
    raise SystemExit(f"No backup found for {hostname} - run backup_configs.py first")

baseline = backups[0]
print(f"Comparing {baseline} with the running config on {hostname}\n")

diff = difflib.unified_diff(
    clean(baseline.read_text()),
    clean(current),
    fromfile=str(baseline),
    tofile=f"{hostname} (now)",
    lineterm="",
)

changes = list(diff)
if changes:
    for line in changes:
        print(line)
else:
    print("No differences.")
EOF
```

### Step 12. Run it

```bash
python3 diff_config.py
```

**Expected output (abridged):**
```
Comparing backups/c8kv-1-20260730-141205.cfg with the running config on c8kv-1

--- backups/c8kv-1-20260730-141205.cfg
+++ c8kv-1 (now)
@@ -142,6 +142,10 @@
 interface Loopback0
  description Configured via RESTCONF
  ip address 172.16.1.1 255.255.255.255
+interface Loopback1
+ description Site A loopback
+ ip address 172.16.10.1 255.255.255.255
 interface GigabitEthernet1
```

Lines starting with `+` were added, `-` removed. This is the artifact you attach to a change ticket.

> **Why the `clean()` function?** Every `show running-config` includes a "Building configuration…" header, a byte count, and a "Last configuration change" timestamp. Those differ on every capture and would bury the real change in noise. Filtering them is the difference between a diff people read and a diff people ignore.

### Step 13. Take a post-change backup

```bash
python3 backup_configs.py
ls backups/
```

You now have a before and an after. That is a change record.

---

## Verification Checklist

| Task | Expected Result | Pass/Fail |
|------|-----------------|-----------|
| Backups created | Timestamped `.cfg` for each router in `backups/` | |
| `push_loopback.py` runs | Config-mode echo, no `% Invalid input` | |
| Change saved | `save_config()` reports success; survives a reload | |
| Jinja2 installed | `pip list` shows Jinja2 | |
| Template push works | Loopback1 on both routers with per-site description | |
| Diff shows the change | `+ interface Loopback1` and its lines | |
| Post-change backup taken | Two timestamps present in `backups/` | |

---

## Reflection Questions

1. Why back up before changing, when the device already has a startup-config you could reload from?
2. `send_config_set()` is not idempotent the way `ios_config` is. What does that mean in practice, and where does the responsibility land?
3. What does separating the Jinja2 template from the device data buy you at fifty routers that it does not at two?
4. The script checks the output for `Invalid input`. What else would you check for before declaring a change successful?
5. Why is `GigabitEthernet1` off limits in this environment, and how would you guard against a teammate targeting it in a script?

---

## Summary

| Concept | Key Point |
|---------|-----------|
| Back up first | A timestamped `show running-config` is your rollback and your evidence |
| `send_config_set()` | Sends a list of config lines — enters and exits config mode for you |
| `save_config()` | Writes to startup-config so the change survives a reload or stop/start |
| Read the echo | The device tells you what it accepted; check for `% Invalid input` |
| Jinja2 template | One template plus per-device data scales to any number of routers |
| `difflib.unified_diff` | Turns two configs into a readable, attachable change record |
| Filter the noise | Timestamps and byte counts differ every capture — strip them |
| Loopbacks only | Never touch the interface carrying your management session |

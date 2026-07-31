# Lab 8 – Parsing and Getters

**Course:** Network Automation Tools — Day 3  
**Prerequisite:** Lab 7 complete — `~/python-lab` with an active virtual environment and Netmiko installed  
**Objective:** Stop treating device output as text. Turn it into structured data two ways — with TextFSM through Netmiko, and with NAPALM getters — then compare the two approaches and save the result as JSON.

---

> **Remember:** Stop the `c8kv-1` and `c8kv-2` instances when you finish this lab to avoid unnecessary charges. Go to **EC2 → Instances → select both routers → Instance State → Stop**.

## Overview

Raw show output is meant for humans and is fragile to parse by hand. In this lab you will:

1. Return parsed data from Netmiko with `use_textfsm=True`
2. Loop over the resulting list of dictionaries by field name
3. Install NAPALM and open a connection to each router
4. Retrieve the same kind of data with `get_facts` and `get_interfaces`
5. Compare the two approaches
6. Save structured data to a JSON file

---

## Part 1 — Structured Output with TextFSM

### Step 1. Activate your environment

```bash
cd ~/python-lab
source venv/bin/activate
```

### Step 2. Install the TextFSM templates

Netmiko uses the `ntc-templates` library to parse standard show commands.

```bash
pip install ntc-templates
```

### Step 3. Create a parsing script

Adding `use_textfsm=True` tells Netmiko to run the matching template and return a **list of dictionaries** instead of raw text. The connection uses the `ansible` / `Cisco123!` password login from Lab 1 — the same reliable path you settled on in Lab 7. Replace the IP with `c8kv-1`.

```bash
cat > parse_textfsm.py << 'EOF'
from netmiko import ConnectHandler

device = {
    "device_type": "cisco_ios",
    "host": "10.0.1.X",
    "username": "ansible",
    "password": "Cisco123!",
}

connection = ConnectHandler(**device)
interfaces = connection.send_command("show ip interface brief", use_textfsm=True)
connection.disconnect()

print(type(interfaces))
for row in interfaces:
    print(f"{row['interface']:25} {row['ip_address']:16} {row['status']}")
EOF
```

### Step 4. Run it

```bash
python3 parse_textfsm.py
```

**Expected output:**
```
<class 'list'>
GigabitEthernet1          10.0.1.X         up
Loopback0                 10.255.0.1       up
...
```

Notice you accessed `row['interface']` and `row['status']` **by name** — no string slicing or regex. That is the whole point of structured data.

> **Note:** If `use_textfsm=True` returns raw text instead of a list, the templates are not installed. Confirm `pip install ntc-templates` completed inside the active `venv`.

---

## Part 2 — NAPALM Getters

### Step 5. Install NAPALM

```bash
pip install napalm
pip list | grep -i napalm
```

### Step 6. Create a getters script

NAPALM returns structured data directly — no parsing step at all. Its `ios` driver uses Netmiko underneath, so it authenticates the same way you just used — with the `ansible` username and password. Replace both IPs.

```bash
cat > napalm_facts.py << 'EOF'
import json
from napalm import get_network_driver

driver = get_network_driver("ios")

hosts = ["10.0.1.X", "10.0.1.Y"]

for host in hosts:
    device = driver(hostname=host, username="ansible", password="Cisco123!")
    device.open()
    facts = device.get_facts()
    device.close()

    print(f"\n===== {facts['hostname']} =====")
    print(f"  Model:   {facts['model']}")
    print(f"  Version: {facts['os_version'].split(',')[0]}")
    print(f"  Serial:  {facts['serial_number']}")
    print(f"  Uptime:  {facts['uptime']} seconds")
    print(f"  Interfaces: {facts['interface_list']}")
EOF
```

### Step 7. Run it

```bash
python3 napalm_facts.py
```

**Expected output (abridged):**
```
===== c8kv-1 =====
  Model:   C8000V
  Version: Cisco IOS XE Software
  Serial:  ...
  Uptime:  ... seconds
  Interfaces: ['GigabitEthernet1', 'Loopback0', ...]
```

> **Note:** `get_facts` returns the **same field names** no matter the vendor. On an Arista or Juniper device the identical code would work — that is NAPALM's multivendor promise.

---

## Part 3 — Compare and Save as JSON

### Step 8. Retrieve interface details and save them

```bash
cat > napalm_interfaces.py << 'EOF'
import json
from napalm import get_network_driver

driver = get_network_driver("ios")

device = driver(hostname="10.0.1.X", username="ansible", password="Cisco123!")
device.open()
interfaces = device.get_interfaces()
device.close()

# Show a structured summary
for name, data in interfaces.items():
    state = "up" if data["is_up"] else "down"
    print(f"{name:25} {state:5} {data['description']}")

# Save the full structure as JSON for reuse
with open("c8kv-1_interfaces.json", "w") as f:
    json.dump(interfaces, f, indent=2)
print("\nSaved c8kv-1_interfaces.json")
EOF
python3 napalm_interfaces.py
```

### Step 9. Inspect the JSON

```bash
head -20 c8kv-1_interfaces.json
```

The file holds clean, structured data any other tool can read — no scraping required.

---

## Verification Checklist

| Task | Expected Result | Pass/Fail |
|------|-----------------|-----------|
| `ntc-templates` installed | `use_textfsm=True` returns a list | |
| TextFSM parsing works | Fields accessed by name, not slicing | |
| NAPALM installed | `pip list` shows napalm | |
| `get_facts` runs on both routers | Hostname, model, version printed | |
| `get_interfaces` runs | Per-interface status and description | |
| JSON saved | `c8kv-1_interfaces.json` is valid JSON | |

---

## Reflection Questions

1. What is the return type of `send_command(..., use_textfsm=True)`, and why is that easier to work with than text?
2. How do NAPALM getters differ from parsing Netmiko output yourself?
3. Why would the `napalm_facts.py` code work unchanged against a different vendor?
4. When might you still reach for regex instead of a TextFSM template?

---

## Summary

| Concept | Key Point |
|---------|-----------|
| `use_textfsm=True` | Netmiko parses output into a list of dictionaries |
| `ntc-templates` | Ready-made TextFSM templates for common commands |
| NAPALM getters | Return structured data directly, no parsing |
| `get_facts` / `get_interfaces` | Normalized fields across vendors |
| `json.dump()` | Saves structured data for reuse by other tools |
| Structured data | Access fields by name — reliable and portable |

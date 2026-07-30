# Lab 14 – eAPI and pyeapi

**Course:** Network Automation Tools — Day 5
**Prerequisite:** Lab 13 complete — `leaf1` (cEOS) is deployed on your AWS host, resolves via `/etc/hosts`, has the `arista` / `Arista123!` login, and eAPI is enabled (you got `200` from `curl .../command-api`).
**Objective:** Automate an Arista switch programmatically. Call eAPI directly with the `requests` library, then use the `pyeapi` client to run show commands and push a configuration change.

---

> **Where you're working:** Everything in this lab runs on your EC2 host from Lab 13 — the same machine runs the `leaf1` switch container and the scripts you write. Your code reaches `leaf1` over the network.

## Overview

Arista EOS was built for automation, and eAPI is its programmatic front door — every CLI command becomes an API call that returns structured JSON. In this lab you will:

1. Create a Python virtual environment on the host
2. Confirm eAPI on `leaf1`
3. Call eAPI directly with `requests` and read the JSON response
4. Install `pyeapi` and connect to the switch
5. Run show commands and inspect structured output
6. Push a small configuration change with `pyeapi`

---

## Part 1 — Prepare the Environment

### Step 1. Create a working directory and virtual environment

You are already on the EC2 host. Work in the `arista-lab` directory you made in Lab 13:

```bash
cd ~/arista-lab
python3 -m venv venv
source venv/bin/activate
pip install requests
```

Your prompt should now start with `(venv)`, and `requests` (used by the raw eAPI script in Part 3) is installed.

### Step 2. Confirm you can reach the switch

```bash
ping -c 2 leaf1
ssh arista@leaf1
```

Log in with `Arista123!`, run `show version` to confirm EOS (`cEOSLab`), then `exit` back to the host.

> **Note:** `leaf1` resolves because of the `/etc/hosts` entry you added in Lab 13. If `ping` fails, re-check that entry and that the container is running (`sudo containerlab inspect -t leaf1.clab.yml`).

---

## Part 2 — Confirm eAPI

### Step 3. Verify eAPI is enabled

You enabled eAPI in Lab 13. Confirm it from the host with a quick eAPI request (a JSON-RPC `POST`):

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

A `200` confirms eAPI is up and your credentials work. (A plain `GET` to the endpoint returns `405` — eAPI only accepts `POST` with a JSON-RPC body, which is exactly what the scripts in this lab send.) If you get `401`, the username/password is wrong; if the connection is refused, re-run Lab 13 Step 11 to enable eAPI on `leaf1`.

> **Note:** In production you would restrict eAPI with an access list. Leaving a management API open to everyone is a security risk.

---

## Part 3 — Call eAPI with requests

### Step 4. Write a raw eAPI script

eAPI uses JSON-RPC: you POST a request naming the commands to run and the output format.

```bash
cat > eapi_raw.py << 'EOF'
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SWITCH = "leaf1"
AUTH = ("arista", "Arista123!")

payload = {
    "jsonrpc": "2.0",
    "method": "runCmds",
    "params": {
        "version": 1,
        "cmds": ["show version"],
        "format": "json",
    },
    "id": "lab14",
}

url = f"https://{SWITCH}/command-api"
response = requests.post(url, json=payload, auth=AUTH, verify=False)

result = response.json()["result"][0]
print("Model:  ", result["modelName"])
print("Version:", result["version"])
print("Serial: ", result["serialNumber"])
EOF
```

### Step 5. Run it

```bash
python3 eapi_raw.py
```

**Expected output:**
```
Model:   cEOSLab
Version: 4.x.x
Serial:  ...
```

You asked for `format: json`, so the switch returned structured data — you indexed straight into it by key, with no parsing.

---

## Part 4 — Use pyeapi

### Step 6. Install pyeapi and create a config file

`pyeapi` handles the JSON-RPC details and reads connection info from a config file, keeping credentials out of your script.

```bash
pip install pyeapi

cat > ~/.eapi.conf << 'EOF'
[connection:leaf1]
host: leaf1
username: arista
password: Arista123!
transport: https
EOF
```

### Step 7. Run show commands with pyeapi

```bash
cat > pyeapi_show.py << 'EOF'
import pyeapi

node = pyeapi.connect_to("leaf1")

result = node.enable("show ip interface brief")
interfaces = result[0]["result"]["interfaces"]

for name, data in interfaces.items():
    addr = data["interfaceAddress"]["ipAddr"]["address"]
    print(f"{name:20} {addr}")
EOF
python3 pyeapi_show.py
```

The output is built from structured data — `pyeapi` returned a dictionary you walked by key. On a fresh switch you will at least see `Management0` with the `172.20.20.11` address.

### Step 8. Push a configuration change

```bash
cat > pyeapi_config.py << 'EOF'
import pyeapi

node = pyeapi.connect_to("leaf1")

node.config([
    "interface Loopback14",
    "description Configured via pyeapi",
    "ip address 10.14.14.14/32",
])
print("Loopback14 configured.")

# Confirm the change
result = node.enable("show interfaces Loopback14")
desc = result[0]["result"]["interfaces"]["Loopback14"]["description"]
print("Description is now:", desc)
EOF
python3 pyeapi_config.py
```

**Expected output:**
```
Loopback14 configured.
Description is now: Configured via pyeapi
```

> **Note:** `node.enable()` runs show commands; `node.config()` applies configuration — the read and write paths, mirroring `send_command` and `send_config_set` from the Day 3 Netmiko lab.

---

## Verification Checklist

| Task | Expected Result | Pass/Fail |
|------|-----------------|-----------|
| Virtual environment active | Prompt shows `(venv)` | |
| eAPI reachable | `curl` to `/command-api` returns `200` | |
| Raw eAPI call works | Model, version, serial printed | |
| `pyeapi` installed and configured | `~/.eapi.conf` created | |
| Show command via pyeapi | Interface data printed | |
| Config change via pyeapi | Loopback14 description set | |

---

## Reflection Questions

1. What does `format: json` in the eAPI request change about the response?
2. How does calling eAPI compare to parsing Cisco output with TextFSM in Day 3?
3. How is eAPI similar to the RESTCONF calls you made to the Cisco routers in Day 3 (Lab 9)? How is it different?
4. What are the `pyeapi` equivalents of Netmiko's `send_command` and `send_config_set`?

---

## Summary

| Concept | Key Point |
|---------|-----------|
| eAPI | Presents the EOS CLI as a JSON-RPC API over HTTPS |
| `runCmds` | The eAPI method that runs a list of commands |
| `format: json` | Returns structured data instead of raw text |
| `pyeapi` | Arista's official Python client for eAPI |
| `node.enable()` | Runs show commands, returns structured data |
| `node.config()` | Applies configuration lines |
| `~/.eapi.conf` | Stores connection details outside your code |

# Lab 18 – Compliance Audit and Reporting

**Course:** Network Automation Tools — Day 3 (Capstone)  
**Prerequisite:** Lab 17 complete — `Loopback1` configured on both routers from the Jinja2 template (`Site A loopback` / `Site B loopback`), RESTCONF enabled from Lab 9, `~/python-lab` venv with Netmiko, NAPALM and `requests` installed  
**Objective:** Tie the whole day together. Describe the network's intended state in YAML, collect its actual state with NAPALM, compare the two, cross-check one fact independently over RESTCONF, and produce a report and an exit code a scheduler can act on.

---

> **Remember:** Stop the `c8kv-1` and `c8kv-2` instances when you finish this lab to avoid unnecessary charges. Go to **EC2 → Instances → select both routers → Instance State → Stop**.

> **If you stopped your instances after Lab 10:** start them again and allow 3–4 minutes to boot, plus a further **2–5 minutes before RESTCONF answers** — the yang-management processes restart from scratch every boot (Lab 9, Step 2). Private IPs are unchanged. Your configuration is intact because Lab 10 ran `save_config()`.

## Overview

Every tool so far has answered "what is the device doing right now?" A compliance audit answers a harder question: **"is the network what we said it should be?"** That needs a written definition of intent, a way to measure reality, and something that compares them without a human squinting at output. In this lab you will:

1. Write the intended state of both routers as YAML
2. Collect the actual state with NAPALM getters and store it as JSON
3. Compare intent against reality and flag every difference
4. Verify one finding independently over RESTCONF
5. Generate a CSV and a Markdown report
6. Return an exit code so a scheduler or CI job can react
7. Introduce real drift, detect it, and remediate it

---

## Part 1 — Describe the Intended State

### Step 1. Activate your environment and install PyYAML

```bash
cd ~/python-lab
source venv/bin/activate
pip install pyyaml
```

### Step 2. Write the intended state file

This is the **source of truth** — a human-readable statement of what the network should look like, kept separate from any code. Replace both IPs with your private addresses.

```bash
cat > intended_state.yaml << 'EOF'
devices:
  - host: 10.0.1.X
    hostname: c8kv-1
    interfaces:
      Loopback0:
        enabled: true
      Loopback1:
        enabled: true
        description: Site A loopback

  - host: 10.0.1.Y
    hostname: c8kv-2
    interfaces:
      Loopback0:
        enabled: true
      Loopback1:
        enabled: true
        description: Site B loopback
EOF
```

```bash
python3 -c "import yaml; print(yaml.safe_load(open('intended_state.yaml')))"
```

If that prints a dictionary, your YAML is valid. If it raises a `ScannerError`, you have an indentation problem — YAML is whitespace-sensitive and never accepts tabs.

> **Note:** `Loopback0` is only checked for existence and state. Its description differs between the routers because Lab 9's PATCH ran against `c8kv-1` only — a good reminder that intended state must describe the network you actually agreed on, not the one you assume.

---

## Part 2 — Collect the Actual State

### Step 3. Create the collection script

NAPALM getters give you normalized fields, so the audit logic never has to know it is talking to Cisco. Replace both IPs.

```bash
cat > collect_state.py << 'EOF'
import json

from napalm import get_network_driver

USER = "ansible"
PASSWORD = "Cisco123!"
HOSTS = ["10.0.1.X", "10.0.1.Y"]

driver = get_network_driver("ios")
state = {}

for host in HOSTS:
    device = driver(hostname=host, username=USER, password=PASSWORD)
    device.open()
    state[host] = {
        "facts": device.get_facts(),
        "interfaces": device.get_interfaces(),
    }
    device.close()
    print(f"{host}: collected {len(state[host]['interfaces'])} interfaces")

with open("actual_state.json", "w") as f:
    json.dump(state, f, indent=2)

print("wrote actual_state.json")
EOF
```

### Step 4. Run it

```bash
python3 collect_state.py
head -30 actual_state.json
```

**Expected output:**
```
10.0.1.X: collected 3 interfaces
10.0.1.Y: collected 3 interfaces
wrote actual_state.json
```

Collection and comparison are deliberately two separate scripts. The JSON snapshot can be re-audited, archived, or handed to another team without touching the routers again.

---

## Part 3 — Compare Intent Against Reality

### Step 5. Create the audit script

```bash
cat > audit.py << 'EOF'
import csv
import json
import sys

import yaml

with open("intended_state.yaml") as f:
    intended = yaml.safe_load(f)

with open("actual_state.json") as f:
    actual = json.load(f)

results = []


def check(device, item, expected, found):
    results.append({
        "device": device,
        "check": item,
        "expected": expected,
        "actual": found,
        "result": "PASS" if str(expected) == str(found) else "FAIL",
    })


for entry in intended["devices"]:
    host = entry["host"]
    name = entry["hostname"]
    device_state = actual.get(host)

    if device_state is None:
        check(name, "state collected", "yes", "no")
        continue

    check(name, "hostname", name, device_state["facts"]["hostname"])

    for interface, wanted in entry["interfaces"].items():
        found = device_state["interfaces"].get(interface)

        if found is None:
            check(name, f"{interface} exists", "present", "missing")
            continue

        check(name, f"{interface} exists", "present", "present")

        if "enabled" in wanted:
            check(name, f"{interface} enabled", wanted["enabled"], found["is_enabled"])

        if "description" in wanted:
            check(name, f"{interface} description", wanted["description"], found["description"])

width = max(len(r["check"]) for r in results)
for r in results:
    print(f"{r['device']:8} {r['check']:{width}}  {r['result']:4}  "
          f"expected={r['expected']!r} actual={r['actual']!r}")

with open("audit_results.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["device", "check", "expected", "actual", "result"])
    writer.writeheader()
    writer.writerows(results)

failures = [r for r in results if r["result"] == "FAIL"]
print(f"\n{len(results) - len(failures)} passed, {len(failures)} failed")

sys.exit(1 if failures else 0)
EOF
```

### Step 6. Run it

```bash
python3 audit.py
echo "exit code: $?"
```

**Expected output:**
```
c8kv-1   hostname                 PASS  expected='c8kv-1' actual='c8kv-1'
c8kv-1   Loopback0 exists         PASS  expected='present' actual='present'
c8kv-1   Loopback0 enabled        PASS  expected=True actual=True
c8kv-1   Loopback1 exists         PASS  expected='present' actual='present'
c8kv-1   Loopback1 enabled        PASS  expected=True actual=True
c8kv-1   Loopback1 description    PASS  expected='Site A loopback' actual='Site A loopback'
c8kv-2   hostname                 PASS  expected='c8kv-2' actual='c8kv-2'
...

12 passed, 0 failed
exit code: 0
```

| Element | What it does |
|---------|-------------|
| `yaml.safe_load()` | Reads intent without executing anything in the file |
| `str(expected) == str(found)` | Compares YAML booleans and NAPALM booleans on equal footing |
| One `results` list | Every check produces a row — reportable, sortable, countable |
| `sys.exit(1 if failures else 0)` | The whole audit reduced to one number a machine can act on |

> **Troubleshooting:**
> - `FileNotFoundError: actual_state.json` → run `collect_state.py` first.
> - `Loopback1 exists ... FAIL ... actual='missing'` → Lab 10's `push_template.py` did not reach that router. Re-run it.
> - A description FAIL you did not expect → the wording in `intended_state.yaml` must match Lab 10's template exactly, including capitalisation.

---

## Part 4 — Verify Independently over RESTCONF

A single source can be confidently wrong. Confirming a finding through a second, unrelated path is how you tell a real problem from a broken script.

### Step 7. Create the RESTCONF cross-check

This reads the same description through the API you enabled in Lab 9, using `apiuser`. Replace both IPs.

```bash
cat > restconf_check.py << 'EOF'
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

AUTH = ("apiuser", "L@bRestconf123")
HEADERS = {"Accept": "application/yang-data+json"}

DEVICES = {
    "c8kv-1": {"host": "10.0.1.X", "description": "Site A loopback"},
    "c8kv-2": {"host": "10.0.1.Y", "description": "Site B loopback"},
}

for name, entry in DEVICES.items():
    url = (f"https://{entry['host']}"
           "/restconf/data/ietf-interfaces:interfaces/interface=Loopback1")

    response = requests.get(url, auth=AUTH, headers=HEADERS, verify=False, timeout=30)

    if response.status_code != 200:
        print(f"{name}: HTTP {response.status_code} - see the Lab 9 troubleshooting notes")
        continue

    interface = response.json()["ietf-interfaces:interface"][0]
    found = interface.get("description", "")
    verdict = "MATCH" if found == entry["description"] else "DRIFT"
    print(f"{name}: description={found!r} -> {verdict}")
EOF
```

### Step 8. Run it

```bash
python3 restconf_check.py
```

**Expected output:**
```
c8kv-1: description='Site A loopback' -> MATCH
c8kv-2: description='Site B loopback' -> MATCH
```

> **If you get `502 Bad Gateway`:** RESTCONF's backend processes are still starting after the reboot. Wait two or three minutes and try again — this is the same behaviour you saw in Lab 9, not a fault in this script. Confirm with `show platform software yang-management process` over SSH.

Two different protocols — SSH/NAPALM and HTTPS/RESTCONF — reporting the same value is strong evidence. If they ever disagree, believe neither until you have found out why.

---

## Part 5 — Produce the Report

### Step 9. Create the report generator

```bash
cat > report.py << 'EOF'
import csv
from datetime import datetime

with open("audit_results.csv") as f:
    rows = list(csv.DictReader(f))

failures = [r for r in rows if r["result"] == "FAIL"]

lines = [
    "# Network Compliance Report",
    "",
    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    "",
    f"**{len(rows) - len(failures)} of {len(rows)} checks passed.**",
    "",
]

if failures:
    lines += ["## Failures", ""]
    for r in failures:
        lines.append(f"- **{r['device']}** — {r['check']}: "
                     f"expected `{r['expected']}`, found `{r['actual']}`")
    lines.append("")

lines += [
    "## All checks",
    "",
    "| Device | Check | Expected | Actual | Result |",
    "|--------|-------|----------|--------|--------|",
]
for r in rows:
    lines.append(f"| {r['device']} | {r['check']} | {r['expected']} | "
                 f"{r['actual']} | {r['result']} |")

with open("audit_report.md", "w") as f:
    f.write("\n".join(lines) + "\n")

print(f"wrote audit_report.md ({len(rows)} checks, {len(failures)} failures)")
EOF
```

### Step 10. Run it

```bash
python3 report.py
cat audit_report.md
```

You now have three artifacts from one collection: `actual_state.json` for machines, `audit_results.csv` for spreadsheets, and `audit_report.md` for people.

---

## Part 6 — Detect and Remediate Real Drift

An audit that has never caught anything is untested.

### Step 11. Introduce drift by hand

SSH to `c8kv-2` and change the description the way a rushed engineer would at 2 a.m.:

```bash
ssh ansible@<c8kv-2-private-ip>
```

```
configure terminal
interface Loopback1
 description temp fix - remove later
end
exit
```

Note that this change was **not** written to memory, and nobody wrote it down. That is exactly how drift happens.

### Step 12. Detect it

```bash
python3 collect_state.py
python3 audit.py
echo "exit code: $?"
```

**Expected output (abridged):**
```
c8kv-2   Loopback1 description    FAIL  expected='Site B loopback' actual='temp fix - remove later'

11 passed, 1 failed
exit code: 1
```

Confirm it independently:

```bash
python3 restconf_check.py
```

```
c8kv-1: description='Site A loopback' -> MATCH
c8kv-2: description='temp fix - remove later' -> DRIFT
```

Two protocols, one conclusion. Now generate the report of the failure:

```bash
python3 report.py
cat audit_report.md
```

### Step 13. Remediate

Push the intended configuration back with the Lab 10 template, then re-audit:

```bash
python3 push_template.py
python3 collect_state.py
python3 audit.py
echo "exit code: $?"
```

**Expected output:**
```
12 passed, 0 failed
exit code: 0
```

Detect → verify → remediate → re-verify. That closed loop is the whole discipline; every tool in this course is just a way of implementing one of those four steps.

### Step 14. Understand the exit code

```bash
python3 audit.py > /dev/null 2>&1; echo "exit code: $?"
```

`0` means compliant, `1` means drift. That single number is what lets this run unattended — a cron entry, a CI pipeline stage, or a monitoring check can act on it without reading a word of output. A daily run of these three scripts is a genuine, if small, compliance system.

---

## Verification Checklist

| Task | Expected Result | Pass/Fail |
|------|-----------------|-----------|
| PyYAML installed | `pip list` shows PyYAML | |
| `intended_state.yaml` valid | `yaml.safe_load` prints a dictionary | |
| State collected | `actual_state.json` written for both routers | |
| Audit passes cleanly | 12 passed, 0 failed, exit code `0` | |
| RESTCONF cross-check | `MATCH` for both routers | |
| Reports generated | `audit_results.csv` and `audit_report.md` exist | |
| Drift detected | Hand-made change reports `FAIL` and exit code `1` | |
| Drift remediated | Re-audit returns to 0 failures | |

---

## Reflection Questions

1. Why keep intended state in YAML rather than in the Python script that reads it?
2. Collection and comparison are separate scripts here. What does that separation make possible?
3. The RESTCONF check reads a fact NAPALM already gave you. When is that redundancy worth the extra call, and when is it waste?
4. `sys.exit(1)` looks trivial. Why does it matter more than everything printed above it?
5. This audit checks descriptions and interface state. What five checks would you add first for a production network, and where would each one's data come from?
6. Detecting drift is safe; automatically remediating it is not. What would you require before letting Step 13 run unattended?

---

## Course Wrap-Up

Across Day 3 you drove the same network four ways:

| Tool | Best at | Cost |
|------|---------|------|
| Netmiko | Any CLI command, any IOS device, total control | You parse and validate everything yourself |
| TextFSM / `ntc-templates` | Structured data from existing show commands | Template must exist for the command |
| NAPALM getters | Normalized, multivendor facts with no parsing | Only covers what the getters expose |
| RESTCONF | Declarative, idempotent, JSON in and out | Needs enabling, takes minutes to start, YANG models are strict |

None of them replaces the others. The judgement being taught is which one to reach for — and this lab shows they combine well: NAPALM for breadth, RESTCONF for confirmation, Netmiko for the fix.

---

## Optional — End-of-Course Cleanup

If you are finished with the routers, remove the lab loopbacks:

```bash
cat > cleanup.py << 'EOF'
from netmiko import ConnectHandler

USER = "ansible"
PASSWORD = "Cisco123!"
HOSTS = ["10.0.1.X", "10.0.1.Y"]

for host in HOSTS:
    connection = ConnectHandler(
        device_type="cisco_ios", host=host, username=USER, password=PASSWORD
    )
    print(connection.send_config_set(["no interface Loopback1"]))
    connection.save_config()
    connection.disconnect()
    print(f"{host}: Loopback1 removed")
EOF
python3 cleanup.py
```

`Loopback0` stays — it was part of Lab 3 and does no harm. `GigabitEthernet1` is never touched.

Then **stop or terminate both instances** in the EC2 console. Stopping preserves them for later; terminating ends all charges. Deactivate your environment with `deactivate`.

---

## Summary

| Concept | Key Point |
|---------|-----------|
| Intended state in YAML | Intent lives in data, readable by people who don't write Python |
| Collect, then compare | A JSON snapshot can be re-audited without touching the network |
| NAPALM getters | Normalized fields keep audit logic vendor-independent |
| Independent verification | A second protocol confirming the same fact turns a finding into evidence |
| CSV + Markdown output | One collection, three audiences: machines, spreadsheets, people |
| `sys.exit(1)` | The exit code is what makes an audit automatable |
| Detect → verify → remediate → re-verify | The closed loop every compliance system implements |
| Test your audit | An audit that has never caught drift has never been proven to work |

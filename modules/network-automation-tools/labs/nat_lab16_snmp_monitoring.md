# Lab 16 – Monitoring with SNMP

**Course:** Network Automation Tools — Day 5
**Prerequisite:** Lab 15 complete — `leaf1` (cEOS) reachable on your AWS host, and your Ansible `inventory.yml` (with the `become` settings) working.
**Objective:** See how a monitoring platform reads a device. Enable SNMP on `leaf1` with Ansible, then poll it from the host with the Net-SNMP tools — the exact protocol and OIDs that Zabbix, LibreNMS, PRTG, and Nagios use to watch switches and routers.

---

> **Where you're working:** The same EC2 host from Labs 13–15 runs `leaf1` and your tools. You configure the switch with Ansible, then query it over SNMP from the host — standing in for the monitoring server.

## Overview

SNMP (Simple Network Management Protocol) is the workhorse of network monitoring. A monitoring server *polls* a device over **UDP 161** to read values, and a device can *push* alerts as *traps* over **UDP 162**. Every value lives at a numbered address called an **OID** inside a **MIB**. In this lab you will:

1. Install the SNMP command-line tools on the host
2. Enable SNMP on `leaf1` with Ansible (a read-only community plus system info)
3. Confirm the config is idempotent
4. Poll system information with `snmpget` and `snmpwalk`
5. Walk the interface table — exactly what a monitor polls per interface
6. Read interface counters and see how they become bandwidth graphs

---

## Part 1 — Set Up

### Step 1. Move to your working directory and install the SNMP tools

Work in the `arista-lab` directory that holds your Lab 15 `inventory.yml`, so Ansible can find it — then install the Net-SNMP client tools on the host (the same tools a monitoring server uses under the hood):

```bash
cd ~/arista-lab
source venv/bin/activate
sudo dnf install -y net-snmp-utils
snmpget --version
```

You should get a version string. `net-snmp-utils` provides `snmpget` (read one value) and `snmpwalk` (read a whole subtree).

> **Stay in `~/arista-lab`** for the rest of this lab. That's where `inventory.yml` lives, and it's where you'll create the playbook below — if you run `ansible-playbook` from elsewhere you'll get `Could not match supplied host pattern` because the inventory isn't found.

---

## Part 2 — Enable SNMP on the Switch

### Step 2. Create the SNMP config playbook

You configure the switch with Ansible, reusing the `inventory.yml` from Lab 15. This sets a **read-only** community string (`labmonitor`) and fills in the device's contact and location — the basics every monitor reads.

```bash
cat > snmp.yml << 'EOF'
---
- name: Enable SNMP on the switch
  hosts: arista
  gather_facts: false

  tasks:

    - name: Configure SNMP community and system info
      arista.eos.eos_config:
        lines:
          - snmp-server community labmonitor ro
          - snmp-server location AWS-Lab
          - snmp-server contact netops@example.com
EOF
```

> **Why read-only (`ro`)?** A monitoring tool only needs to *read* values, never change them. A read-only community can poll everything but cannot configure the device — the right level of access for monitoring.

### Step 3. Apply it, then prove idempotency

```bash
ansible-playbook -i inventory.yml snmp.yml
```

Expect `changed=1` on the first run. Run it again:

```bash
ansible-playbook -i inventory.yml snmp.yml
```

Now expect `changed=0` — the same idempotency you saw in Lab 15. SNMP is now enabled on `leaf1`.

---

## Part 3 — Poll the Device

You query the switch from the **host**, exactly as a monitoring server would. `-v2c` selects SNMP version 2c, and `-c labmonitor` supplies the community string.

> **Numeric OIDs:** These commands use numeric OIDs (like `1.3.6.1.2.1.1.5.0`) so they work without extra MIB files installed. Each command's comment says what the OID is.

### Step 4. Read the device name and system group

```bash
# sysName.0 — the device's hostname
snmpget -v2c -c labmonitor leaf1 1.3.6.1.2.1.1.5.0
```

**Expected output:**
```
.1.3.6.1.2.1.1.5.0 = STRING: leaf1
```

Now walk the whole **system group** (`1.3.6.1.2.1.1`) — description, uptime, contact, name, and location in one shot:

```bash
snmpwalk -v2c -c labmonitor leaf1 1.3.6.1.2.1.1
```

You should see the EOS version string (sysDescr), the uptime, and the `AWS-Lab` / `netops@example.com` values you set in Step 2.

### Step 5. Walk the interface table

This is the heart of interface monitoring — the list of interfaces (IF-MIB `ifDescr`, `1.3.6.1.2.1.2.2.1.2`):

```bash
snmpwalk -v2c -c labmonitor leaf1 1.3.6.1.2.1.2.2.1.2
```

**Expected (abridged):**
```
.1.3.6.1.2.1.2.2.1.2.1  = STRING: Management0
.1.3.6.1.2.1.2.2.1.2.2  = STRING: Ethernet1
.1.3.6.1.2.1.2.2.1.2... = STRING: Loopback0
.1.3.6.1.2.1.2.2.1.2... = STRING: Loopback15
```

Each interface has an index number — that index is the key a monitor uses to pull per-interface stats.

### Step 6. Read interface counters (the basis of bandwidth graphs)

Poll the inbound byte counters (`ifInOctets`, `1.3.6.1.2.1.2.2.1.10`):

```bash
snmpwalk -v2c -c labmonitor leaf1 1.3.6.1.2.1.2.2.1.10
```

You'll get a running byte total per interface. Poll it again a few seconds later and the numbers grow.

> **This is exactly how a monitor draws a bandwidth graph.** Zabbix (and LibreNMS, PRTG, Nagios…) poll `ifInOctets`/`ifOutOctets` on a schedule, subtract consecutive readings, divide by the interval, and plot the result as bits-per-second. Everything you just ran by hand is what those tools automate.

---

## Verification Checklist

| Task | Expected Result | Pass/Fail |
|------|-----------------|-----------|
| Net-SNMP installed | `snmpget --version` prints a version | |
| SNMP configured | `snmp.yml` first run → `changed=1` | |
| Idempotent | second run → `changed=0` | |
| `sysName` poll | returns `leaf1` | |
| System group walk | shows description, contact, location | |
| Interface walk | lists Management0, Ethernet1, Loopbacks | |

---

## Reflection Questions

1. Why is a **read-only** community the right choice for a monitoring server?
2. What is the difference between **polling** (a GET on UDP 161) and a **trap** (UDP 162)? When is each better?
3. How does a tool like Zabbix turn the raw `ifInOctets` counter into a bandwidth-over-time graph?
4. SNMPv2c sends the community string in clear text. What does **SNMPv3** add, and why does it matter on a real network?

---

## Summary

| Concept | Key Point |
|---------|-----------|
| SNMP | The standard device-monitoring protocol — poll on UDP 161, traps on UDP 162 |
| Community string | SNMPv2c's shared secret; `ro` = read-only, right for monitoring |
| OID | The numeric address of a value inside a MIB |
| `snmpget` / `snmpwalk` | Read one value / walk an entire subtree |
| System group & IF-MIB | The standard MIBs every monitor reads (device info, interfaces) |
| Counters → graphs | Tools poll `ifInOctets`/`ifOutOctets` over time to compute bandwidth |

---

## Troubleshooting

- **`Timeout: No Response from leaf1`** → the switch isn't answering SNMP. Confirm the community actually applied: `ssh arista@leaf1`, `enable`, then `show running-config | include snmp-server`. Make sure you polled with the matching `-c labmonitor`, and give cEOS a few seconds after the config to start its SNMP agent. (You already `ping leaf1` successfully, so it isn't a network-path problem.)
- **`Unknown Object Identifier`** → you used a name instead of a numeric OID and MIB files aren't installed. Use the numeric OIDs shown above.
- **Some OIDs return no data** → `leaf1` is a container, so hardware/environmental OIDs (temperature, power supplies, fans) have nothing behind them. The system and interface MIBs used in this lab are what monitoring relies on and do respond.

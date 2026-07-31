# Lab 4 – Variables and Templates

**Course:** Network Automation Tools — Day 2  
**Prerequisite:** Labs 1–3 complete — Ansible installed, both Catalyst 8000V routers reachable, `inventory.yml` working, hostnames and Loopback0 configured  
**Objective:** Separate data from logic. Store per-device values in `host_vars` and `group_vars`, build a single Jinja2 template, render a unique configuration for each router, and push it with `ios_config`.

---

> **Remember:** Stop the `c8kv-1` and `c8kv-2` instances when you finish this lab to avoid unnecessary charges. Go to **EC2 → Instances → select both routers → Instance State → Stop**.

## Overview

In Lab 3 every value was hard-coded inside the playbook. That does not scale. In this lab you will:

1. Move shared values into `group_vars/routers.yml`
2. Move device-specific values into `host_vars/c8kv-1.yml` and `host_vars/c8kv-2.yml`
3. Write one Jinja2 template that uses those variables, a loop, and a conditional
4. Render the template into a per-device config file with the `template` module
5. Push the rendered config to each router with `ios_config`
6. Verify that each router received its own values

---

## Part 1 — Organize Your Variables

### Step 1. Move to your working directory

```bash
cd ~/ansible-lab
```

### Step 2. Create group variables

Values here apply to **every** host in the `routers` group. Ansible auto-loads a file named after the group from the `group_vars/` directory.

```bash
mkdir -p group_vars host_vars
cat > group_vars/routers.yml << 'EOF'
---
# Applies to every device in the routers group
snmp_enabled: true
snmp_community: LabReadOnly
login_banner: "Authorized access only - Automation Lab"
EOF
```

### Step 3. Create host variables

Values here apply to **one** device only. The filename must match the inventory hostname exactly.

```bash
cat > host_vars/c8kv-1.yml << 'EOF'
---
loopbacks:
  - id: 10
    description: Test loopback A
    ip: 10.255.10.1
    mask: 255.255.255.255
  - id: 11
    description: Test loopback B
    ip: 10.255.11.1
    mask: 255.255.255.255
EOF

cat > host_vars/c8kv-2.yml << 'EOF'
---
loopbacks:
  - id: 10
    description: Test loopback A
    ip: 10.255.10.2
    mask: 255.255.255.255
EOF
```

> **Note:** `c8kv-1` defines two loopbacks and `c8kv-2` defines one. This proves the point of templating — the same template will generate a different amount of config for each device based purely on its data.

---

## Part 2 — Write the Jinja2 Template

### Step 4. Create the template file

Template files end in `.j2`. The single-quoted heredoc (`<< 'EOF'`) is important — it stops the shell from touching the `{{ }}` and `{% %}` markers so Jinja2 sees them intact.

```bash
mkdir -p templates
cat > templates/base_config.j2 << 'EOF'
hostname {{ inventory_hostname }}
!
{% for lo in loopbacks %}
interface Loopback{{ lo.id }}
 description {{ lo.description }}
 ip address {{ lo.ip }} {{ lo.mask }}
!
{% endfor %}
{% if snmp_enabled %}
snmp-server community {{ snmp_community }} RO
{% endif %}
banner login ^C
{{ login_banner }}
^C
EOF
```

### Step 5. Understand the template

| Line | What it does |
|------|-------------|
| `hostname {{ inventory_hostname }}` | Inserts the current host's inventory name — a magic variable |
| `{% for lo in loopbacks %}` | Starts a loop over the `loopbacks` list from `host_vars` |
| `interface Loopback{{ lo.id }}` | Builds an interface block using each dictionary's fields |
| `{% endfor %}` | Ends the loop — repeats the block once per list item |
| `{% if snmp_enabled %}` | Includes the SNMP line only when the variable is true |
| `{% endif %}` | Ends the conditional |
| `{{ login_banner }}` | Inserts the shared banner text from `group_vars` |

---

## Part 3 — Render the Template

### Step 6. Create the render-and-push playbook

The `template` module renders a `.j2` file on the control node. Because network devices have no local filesystem for Ansible to write to, the render task is delegated to `localhost`.

```bash
cat > deploy_config.yml << 'EOF'
---
- name: Render and deploy per-router configuration
  hosts: routers
  gather_facts: false

  tasks:

    - name: Render base config from template
      ansible.builtin.template:
        src: templates/base_config.j2
        dest: "/tmp/{{ inventory_hostname }}.cfg"
      delegate_to: localhost

    - name: Push rendered config to the device
      cisco.ios.ios_config:
        src: "/tmp/{{ inventory_hostname }}.cfg"
EOF
```

### Step 7. Render only, and inspect the output first

Run just the render task using a tag-free dry approach — comment out the push, or run the template step and read the files. Render both configs and inspect them **before** pushing anything:

```bash
ansible-playbook deploy_config.yml --start-at-task "Render base config from template"
cat /tmp/c8kv-1.cfg
cat /tmp/c8kv-2.cfg
```

**Expected `/tmp/c8kv-1.cfg`:**
```
hostname c8kv-1
!
interface Loopback10
 description Test loopback A
 ip address 10.255.10.1 255.255.255.255
!
interface Loopback11
 description Test loopback B
 ip address 10.255.11.1 255.255.255.255
!
snmp-server community LabReadOnly RO
banner login ^C
Authorized access only - Automation Lab
^C
```

`c8kv-2.cfg` should contain **one** loopback block (Loopback10), confirming the loop rendered from that host's data.

---

## Part 4 — Push and Verify

### Step 8. Run the full playbook

```bash
ansible-playbook deploy_config.yml
```

**Expected PLAY RECAP (first run):**
```
c8kv-1  : ok=2  changed=1  unreachable=0  failed=0
c8kv-2  : ok=2  changed=1  unreachable=0  failed=0
```

### Step 9. Confirm idempotency

Run it again. Nothing has changed, so `ios_config` should report no changes:

```bash
ansible-playbook deploy_config.yml
```

**Expected PLAY RECAP (second run):**
```
c8kv-1  : ok=2  changed=0  unreachable=0  failed=0
c8kv-2  : ok=2  changed=0  unreachable=0  failed=0
```

> **Note:** The `template` task may still report `ok` rather than `changed` on the second run because the rendered file content is unchanged. `ios_config` compares against the running config and sends nothing, so `changed=0`.

### Step 10. Verify each router got its own values

```bash
ssh -i ~/.ssh/AutomationLab-Key.pem ec2-user@<c8kv-1-private-ip>
show ip interface brief | include Loopback
show running-config | include snmp-server community
exit
```

`c8kv-1` should show **Loopback10 and Loopback11**; `c8kv-2` should show **only Loopback10**. Both should show the `LabReadOnly` SNMP community.

---

## Verification Checklist

| Task | Expected Result | Pass/Fail |
|------|-----------------|-----------|
| `group_vars/routers.yml` auto-loads | SNMP and banner applied to both | |
| `host_vars/c8kv-1.yml` auto-loads | Two loopbacks on c8kv-1 | |
| `host_vars/c8kv-2.yml` auto-loads | One loopback on c8kv-2 | |
| Template renders per host | `/tmp/c8kv-1.cfg` ≠ `/tmp/c8kv-2.cfg` | |
| First push | changed=1 on both hosts | |
| Second push | changed=0 on both hosts | |
| Loopbacks present on devices | Correct count per router | |

---

## Reflection Questions

1. Where would you add a value that should apply to **all** routers, and where for a single router?
2. Why must the render task be delegated to `localhost` for a network device?
3. What happens to the rendered config if you set `snmp_enabled: false` in `group_vars`?
4. If `c8kv-2` needed a third loopback, which file would you edit — and would the template change at all?

---

## Summary

| Concept | Key Point |
|---------|-----------|
| `group_vars/` | Values shared by every host in a group, auto-loaded by name |
| `host_vars/` | Values for a single host, auto-loaded by hostname |
| `inventory_hostname` | Magic variable holding the current host's name |
| Jinja2 `{% for %}` | Repeats a config block for each list item |
| Jinja2 `{% if %}` | Includes config only when a condition is true |
| `template` module | Renders a `.j2` file; delegate to localhost for network devices |
| `ios_config: src` | Pushes a rendered config file, idempotently |

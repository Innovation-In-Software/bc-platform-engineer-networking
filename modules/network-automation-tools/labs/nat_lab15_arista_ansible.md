# Lab 15 – Arista with Ansible

**Course:** Network Automation Tools — Day 5
**Prerequisite:** Lab 14 complete — `leaf1` (cEOS) reachable on your AWS host with eAPI enabled and the `arista` / `Arista123!` login working.
**Objective:** Prove that the Ansible skills from Days 1 and 2 transfer directly to Arista. Install the `arista.eos` collection, build an inventory that connects over eAPI, gather facts, push configuration, and confirm idempotency.

---

> **Where you're working:** The same EC2 host from Labs 13–14 runs both `leaf1` and your automation code. You have one switch, so this lab targets `leaf1` only — the workflow is identical with more switches.

## Overview

Ansible is vendor-neutral: the same playbook structure works on Arista through the `arista.eos` collection. Only the modules and connection settings change. In this lab you will:

1. Install Ansible and the `arista.eos` collection
2. Write an inventory that connects to EOS over eAPI
3. Gather structured facts with `eos_facts`
4. Push configuration with `eos_config`
5. Run the playbook twice and confirm idempotency

---

## Part 1 — Install the Collection

### Step 1. Activate your environment

```bash
cd ~/arista-lab
source venv/bin/activate
```

### Step 2. Install Ansible and the arista.eos collection

```bash
pip install ansible
ansible-galaxy collection install arista.eos
ansible-galaxy collection list | grep arista
```

**Expected output:**
```
arista.eos    x.x.x
```

> **Note:** The `arista.eos` collection is the direct counterpart to the `cisco.ios` collection from Day 1 — same idea, different vendor.

---

## Part 2 — Build the Inventory

### Step 3. Create the inventory

Arista connects cleanly over eAPI using the `httpapi` connection plugin. This inventory uses the `arista` / `Arista123!` credentials you set in Lab 13.

```bash
cat > inventory.yml << 'EOF'
all:
  children:
    arista:
      hosts:
        leaf1:
      vars:
        ansible_network_os: arista.eos.eos
        ansible_connection: ansible.netcommon.httpapi
        ansible_httpapi_use_ssl: true
        ansible_httpapi_validate_certs: false
        ansible_user: arista
        ansible_password: Arista123!
        ansible_become: true
        ansible_become_method: enable
EOF
```

### Step 4. Understand the connection settings

| Setting | What it does |
|---------|-------------|
| `ansible_network_os: arista.eos.eos` | Selects the EOS platform |
| `ansible_connection: ...httpapi` | Connects over eAPI, not SSH |
| `ansible_httpapi_use_ssl: true` | Uses HTTPS |
| `ansible_httpapi_validate_certs: false` | Accepts the switch's self-signed certificate |
| `ansible_user` / `ansible_password` | eAPI credentials from Lab 13 |
| `ansible_become: true` | Enter EOS privileged (enable) mode for changes |
| `ansible_become_method: enable` | Use `enable` to escalate — no password needed here |

> **Why `become`?** Gathering facts uses show commands, which run fine unprivileged. But `eos_config` changes the running config, and EOS requires **privileged (enable) mode** to do that. Without the two `become` lines, the config task fails with `Invalid input (privileged mode required)`. cEOS has no `enable secret` set, so `become_method: enable` escalates without a password; on a switch that has one, you would also set `ansible_become_password`.

> **Note:** You have a single switch (`leaf1`). To manage more later, add them under `hosts:` — the rest of the inventory is unchanged. This is the same `httpapi` pattern regardless of switch count.

---

## Part 3 — Gather Facts

### Step 5. Create a facts playbook

```bash
cat > facts.yml << 'EOF'
---
- name: Gather EOS facts
  hosts: arista
  gather_facts: false

  tasks:

    - name: Collect device facts
      arista.eos.eos_facts:

    - name: Show model and version
      ansible.builtin.debug:
        msg: "{{ ansible_net_hostname }} is a {{ ansible_net_model }} running {{ ansible_net_version }}"
EOF
```

### Step 6. Run it

```bash
ansible-playbook -i inventory.yml facts.yml
```

**Expected output (abridged):**
```
TASK [Show model and version] **************************************************
ok: [leaf1] => {
    "msg": "leaf1 is a cEOSLab running 4.x.x"
}
```

`eos_facts` populates the same `ansible_net_*` variables you used with `ios_facts` on Day 1 — proof the workflow is vendor-neutral.

---

## Part 4 — Push Config and Verify Idempotency

### Step 7. Create a configuration playbook

`eos_config` works exactly like `ios_config` — `lines` and `parents`, idempotent by design.

```bash
cat > configure.yml << 'EOF'
---
- name: Configure a loopback on each switch
  hosts: arista
  gather_facts: false

  tasks:

    - name: Ensure Loopback15 is configured
      arista.eos.eos_config:
        parents: interface Loopback15
        lines:
          - description Configured via Ansible
          - ip address 10.15.15.15/32
EOF
```

### Step 8. First run — expect a change

```bash
ansible-playbook -i inventory.yml configure.yml
```

**Expected PLAY RECAP:**
```
leaf1  : ok=1  changed=1  unreachable=0  failed=0
```

### Step 9. Second run — expect no change

```bash
ansible-playbook -i inventory.yml configure.yml
```

**Expected PLAY RECAP:**
```
leaf1  : ok=1  changed=0  unreachable=0  failed=0
```

`changed=0` confirms the device already matches the desired state — the same idempotency you saw on Cisco in Day 1, proving the workflow is truly vendor-neutral.

### Step 10. Confirm on the switch

From the **host**, SSH into `leaf1` and enter `Arista123!` when prompted:

```bash
ssh arista@leaf1
```

You land on the switch at `leaf1>` (unprivileged). `show running-config` requires **enable** mode, so elevate first, then check the interface:

```
enable
show running-config interface Loopback15
```

**Expected (at the `leaf1#` prompt):**
```
interface Loopback15
   description Configured via Ansible
   ip address 10.15.15.15/32
```

Then leave the switch and return to the host:

```
exit
```

Your prompt should read `[ec2-user@... ]$` again. (No password is needed for `enable` — cEOS has no `enable secret` set. And enter these commands *after* you've logged in — pasting them together with the `ssh` line lets the password prompt swallow the next line.)

---

## Verification Checklist

| Task | Expected Result | Pass/Fail |
|------|-----------------|-----------|
| `arista.eos` installed | `collection list` shows arista.eos | |
| Inventory uses httpapi | eAPI connection configured | |
| `eos_facts` runs | Model and version printed | |
| First config run | changed=1 | |
| Second config run | changed=0 | |
| Loopback present | `Loopback15` visible on `leaf1` | |

---

## Reflection Questions

1. What are the only real differences between this lab and the Day 1 Cisco playbooks?
2. Why does the inventory use the `httpapi` connection instead of `network_cli`?
3. What does `changed=0` on the second run prove about `eos_config`?
4. How would you reuse a Day 2 role to configure both Cisco and Arista devices?

---

## Summary

| Concept | Key Point |
|---------|-----------|
| `arista.eos` collection | The Arista counterpart to `cisco.ios` |
| `httpapi` connection | Ansible drives EOS over eAPI |
| `eos_facts` | Gathers `ansible_net_*` facts, like `ios_facts` |
| `eos_config` | Idempotent config push, like `ios_config` |
| Vendor-neutral workflow | Same playbook structure across vendors |
| Idempotency | `changed=0` means already in the desired state |

---

## Cleanup — you're done with the course

This is the last lab. Tear down the Day 5 environment so nothing keeps running:

```bash
cd ~/arista-lab
sudo containerlab destroy -t leaf1.clab.yml
```

Then, in the AWS console, **stop the EC2 instance** (or resize the control node back to `t2.micro`) so you are not billed for `t3.medium` idle time. If you have not already, run `terraform destroy` in `~/terraform-lab` (Lab 12) to remove the Day 4 network, and stop or terminate the Cisco router instances from Days 1–3.

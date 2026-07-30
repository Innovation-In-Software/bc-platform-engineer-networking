# Lab 5 – Building a Role

**Course:** Network Automation Tools — Day 2  
**Prerequisite:** Lab 4 complete — variables, template, and `deploy_config.yml` working against both routers  
**Objective:** Refactor the working configuration from Lab 4 into a reusable Ansible **role**. Scaffold the standard directory structure, move your tasks, template, and defaults into it, call the role from a short playbook, and override a default for a single device.

---

> **Remember:** Stop the `c8kv-1` and `c8kv-2` instances when you finish this lab to avoid unnecessary charges. Go to **EC2 → Instances → select both routers → Instance State → Stop**.

## Overview

A single playbook works, but real projects package automation into roles so it can be reused and shared. In this lab you will:

1. Scaffold a role named `base_config` with `ansible-galaxy init`
2. Move the template into the role's `templates/` directory
3. Move the tasks into the role's `tasks/main.yml`
4. Move the shared values into the role's `defaults/main.yml`
5. Call the role from a short top-level playbook
6. Override a role default for one router and confirm the result

The end result behaves exactly like Lab 4 — roles change how the code is **organized**, not what it does.

> **Reminder on `changed` counts:** As in Labs 3 and 4, the `changed` numbers below assume a particular device state. If your routers already hold the config (e.g. from Lab 4), a run that the lab shows as `changed=1` may show `changed=0` on your box — that is correct idempotent behavior, not an error. The values here describe what changes *relative to the current state*.

> **Tip:** Each `cat > file << 'EOF'` block starts with `cat`. If you mistype it as `at`, the file is created empty or not at all. A quick `cat <file>` after each block confirms it wrote.

---

## Part 1 — Scaffold the Role

### Step 1. Move to your working directory

```bash
cd ~/ansible-lab
```

### Step 2. Create the role skeleton

```bash
mkdir -p roles
ansible-galaxy init roles/base_config
```

**Expected output:**
```
- Role roles/base_config was created successfully
```

### Step 3. Look at what was created

```bash
ls roles/base_config
```

**Expected output:**
```
defaults  files  handlers  meta  README.md  tasks  templates  vars
```

| Directory | Purpose |
|-----------|---------|
| `tasks/` | The main list of tasks (`main.yml`) |
| `templates/` | Jinja2 templates the role uses |
| `defaults/` | Default variable values — weakest precedence, easily overridden |
| `vars/` | Stronger variables, harder to override |
| `handlers/` | Handlers the role can notify |
| `meta/` | Role metadata and dependencies |

---

## Part 2 — Populate the Role

### Step 4. Move the template into the role

A role automatically looks in its own `templates/` directory, so the `src` no longer needs a path.

```bash
cp templates/base_config.j2 roles/base_config/templates/base_config.j2
```

### Step 5. Define the role's defaults

These are the values you expect users of the role to override. Notice `src: base_config.j2` with no directory prefix.

```bash
cat > roles/base_config/defaults/main.yml << 'EOF'
---
# Default values for the base_config role
snmp_enabled: true
snmp_community: LabReadOnly
login_banner: "Authorized access only - Automation Lab"
EOF
```

### Step 6. Write the role's tasks

```bash
cat > roles/base_config/tasks/main.yml << 'EOF'
---
- name: Render base config from template
  ansible.builtin.template:
    src: base_config.j2
    dest: "/tmp/{{ inventory_hostname }}.cfg"
  delegate_to: localhost

- name: Push rendered config to the device
  cisco.ios.ios_config:
    src: "/tmp/{{ inventory_hostname }}.cfg"
EOF
```

> **Note:** You already have `snmp_enabled`, `snmp_community`, and `login_banner` in `group_vars/routers.yml` from Lab 4. Those still work and take precedence over the role defaults — the defaults simply guarantee the role runs even without them. The per-device `loopbacks` stay in `host_vars/`.

---

## Part 3 — Use the Role in a Playbook

### Step 7. Create a short top-level playbook

The playbook becomes tiny — it just maps hosts to roles.

```bash
cat > site.yml << 'EOF'
---
- name: Configure routers with the base_config role
  hosts: routers
  gather_facts: false

  roles:
    - base_config
EOF
```

### Step 8. Run it

```bash
ansible-playbook site.yml
```

**Expected PLAY RECAP:**
```
c8kv-1  : ok=2  changed=0  unreachable=0  failed=0
c8kv-2  : ok=2  changed=0  unreachable=0  failed=0
```

> **Why changed=0?** The devices already hold this exact configuration from Lab 4, and the rendered file is unchanged, so both the template and push tasks report `ok`. The role produced the identical result — which is the proof that the refactor preserved behavior. If you were starting from a clean device, this run would show `changed=1` (push only).

---

## Part 4 — Override a Default

### Step 9. Override a role variable for one device

Give `c8kv-1` a different SNMP community without touching the role at all. Add the line to its host vars:

```bash
cat >> host_vars/c8kv-1.yml << 'EOF'
snmp_community: LabReadOnly-C1
EOF
```

### Step 10. Re-run and observe the targeted change

```bash
ansible-playbook site.yml
```

**Expected PLAY RECAP:**
```
c8kv-1  : ok=2  changed=2  unreachable=0  failed=0
c8kv-2  : ok=2  changed=0  unreachable=0  failed=0
```

Only `c8kv-1` changed; `c8kv-2` stayed at `changed=0`. That is the lesson — the `host_vars` override beat the role default for that host only.

> **Why `changed=2` on c8kv-1 (both tasks), not just 1?** The override changes the SNMP community, so **two** things change on c8kv-1:
> 1. **Render task** — the rendered `/tmp/c8kv-1.cfg` now contains `LabReadOnly-C1` instead of `LabReadOnly`, so the `template` module rewrites the file → `changed`.
> 2. **Push task** — `ios_config` sends the new community line to the router → `changed`.
>
> Whenever a variable that feeds the template changes, expect *both* the render and the push to report `changed`. `c8kv-2`'s variables were untouched, so its rendered file is identical and both its tasks report `ok` → `changed=0`.
>
> You will also see the normal `ios_config` idempotency `[WARNING]` on the push task; it does not indicate a problem.

### Step 11. Confirm on the device

Connect with the `ansible` login (password `Cisco123!`):

```bash
ssh -o PubkeyAcceptedAlgorithms=+ssh-rsa -o HostKeyAlgorithms=+ssh-rsa ansible@<c8kv-1-private-ip>
show running-config | include snmp-server community
exit
```

> **Shortcut:** If you set up `~/.ssh/config` in Lab 1 (Step 11b), `ssh <c8kv-1-private-ip>` also works (key-based, no password prompt).

**What you'll actually see on c8kv-1:**
```
snmp-server community LabReadOnly RO
snmp-server community LabReadOnly-C1 RO
```

c8kv-1 now has **both** communities, while c8kv-2 shows only the original `LabReadOnly`. This is not what you might have expected — you changed the value, so you'd think the old one would be gone. It isn't, and understanding why is an important lesson about `ios_config`.

### Step 12. Understand and fix the add-vs-replace behavior

**Why both lines exist:** `ios_config` is **additive** — it sends the lines you give it that aren't already in the running config, but it does **not** remove lines you didn't mention. Here's the sequence:

1. In Step 8, the template rendered `snmp-server community LabReadOnly RO` and `ios_config` added it to c8kv-1.
2. In Step 10, you changed the variable, so the template rendered `snmp-server community LabReadOnly-C1 RO`. `ios_config` saw that this new line was missing and added it — but it had no instruction to remove the old `LabReadOnly` line, so that line stayed.

On IOS, each unique `snmp-server community <name>` is a separate entry, so you end up with two communities instead of a replacement. **This is the single most important `ios_config` gotcha: it adds; it does not reconcile or replace.** Changing a value in your data does not automatically remove the old config it produced.

**Clean up the stale community** on c8kv-1 (this removes only the old default, leaving the overridden one):

```bash
ansible c8kv-1 -m cisco.ios.ios_config -a "lines='no snmp-server community LabReadOnly RO'"
```

Confirm it's now correct:

```bash
ssh -o PubkeyAcceptedAlgorithms=+ssh-rsa -o HostKeyAlgorithms=+ssh-rsa ansible@<c8kv-1-private-ip>
show running-config | include snmp-server community
exit
```

Now `c8kv-1` shows only `LabReadOnly-C1`, and `c8kv-2` still shows only `LabReadOnly` — the intended end state.

> **How this is handled in production:** Because `ios_config` won't remove old config on its own, real projects handle "replace" one of a few ways: (a) use a **resource module** like `cisco.ios.ios_snmp_server` that manages the full SNMP state declaratively (it removes what's not in your data); (b) explicitly render a `no snmp-server community {{ old_value }}` line; or (c) periodically reconcile against an intended full configuration. The template-plus-`ios_config` pattern in this course is great for **adding/ensuring** config, but remember it does not clean up what a changed variable leaves behind.

---

## Verification Checklist

| Task | Expected Result | Pass/Fail |
|------|-----------------|-----------|
| `ansible-galaxy init` runs | `base_config` role directory created | |
| Template copied into role | `roles/base_config/templates/base_config.j2` exists | |
| `tasks/main.yml` populated | Render + push tasks present | |
| `defaults/main.yml` populated | SNMP and banner defaults present | |
| `site.yml` calls the role | Playbook is just hosts + roles | |
| Role run | Same result as Lab 4 (changed=0 on already-configured devices) | |
| Override applied | Only c8kv-1 changes (changed=2: render + push) | |
| Observe add-vs-replace | c8kv-1 shows BOTH communities before cleanup | |
| Cleanup applied | c8kv-1 shows only LabReadOnly-C1 after removing the old line | |

---

## Reflection Questions

1. Why did the first run of `site.yml` report `changed=0` instead of `changed=1`?
2. What is the difference in precedence between `defaults/main.yml` and `vars/main.yml`?
3. When you overrode the SNMP community, why did only `c8kv-1` change — and why did it show `changed=2` rather than `changed=1`?
4. After the override, c8kv-1 had *two* SNMP communities instead of one. Why does `ios_config` leave the old line in place, and what are two ways you could make it truly replace the value instead of adding to it?
5. How would you reuse the `base_config` role in a completely different project?

---

## Summary

| Concept | Key Point |
|---------|-----------|
| `ansible-galaxy init` | Scaffolds the standard role directory structure |
| `tasks/main.yml` | The role's main task list, loaded automatically |
| `templates/` | Role templates are found by name, no path needed |
| `defaults/main.yml` | Weakest variables — meant to be overridden |
| `roles:` in a play | Runs a role's tasks; keeps the playbook short |
| Variable override | `host_vars` beats role defaults, per host |
| `ios_config` is additive | It adds/ensures lines but does not remove old config a changed variable leaves behind — clean up or use a resource module |
| Refactoring | Roles change structure, not the outcome |

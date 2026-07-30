# Lab 2 – First Playbook: Gather Facts

**Course:** Network Automation Tools — Day 1  
**Prerequisite:** Lab 1 complete — Ansible + `ansible-pylibssh` installed, the `ansible` username/password login configured on both routers, and `ansible.cfg` + `inventory.yml` present in `~/ansible-lab` with a working `ansible routers -m cisco.ios.ios_command -a "commands='show version'"`.  
**Objective:** Write and run your first Ansible playbook. Collect structured and unstructured data from both Catalyst 8000V routers and understand how Ansible processes and displays results.

---

> **Remember:** Stop the `c8kv-1` and `c8kv-2` instances when you finish this lab to avoid unnecessary charges. Go to **EC2 → Instances → select both routers → Instance State → Stop**.

## Overview

In this lab you will:

1. Write a playbook that runs show commands and prints the output
2. Use the `register` keyword to capture command output
3. Use the `debug` module to display results
4. Add a second play using `ios_facts` to collect structured device data
5. Use verbose flags to understand what Ansible is doing under the hood

> **Connection note:** All playbooks in this lab connect using the **username/password** and `ansible.cfg`/`inventory.yml` you set up in Lab 1. Because `ansible.cfg` sets `inventory = inventory.yml`, you can run `ansible-playbook <file>` from `~/ansible-lab` without an `-i` flag. If you ever see `[WARNING]: Could not match supplied host pattern... routers`, you are not in `~/ansible-lab` or `ansible.cfg` is missing — `cd ~/ansible-lab` and confirm the file exists.

---

## Part 1 — Your First Playbook

### Step 1. Create the playbook file

Make sure you are in your working directory:

```bash
cd ~/ansible-lab
```

Create the playbook:

```bash
cat > gather_info.yml << 'EOF'
---
- name: Gather IOS information from routers
  hosts: routers
  gather_facts: false

  tasks:

    - name: Get show version
      cisco.ios.ios_command:
        commands:
          - show version
      register: version_output

    - name: Print show version output
      ansible.builtin.debug:
        var: version_output.stdout_lines

    - name: Get show ip interface brief
      cisco.ios.ios_command:
        commands:
          - show ip interface brief
      register: interface_output

    - name: Print interface output
      ansible.builtin.debug:
        var: interface_output.stdout_lines
EOF
```

### Step 2. Review the playbook structure before running

Before running anything, understand each line:

| Line | What it does |
|------|-------------|
| `---` | Marks the start of a YAML document |
| `- name: Gather IOS information` | Human-readable name for this play |
| `hosts: routers` | Run against the routers group in inventory.yml |
| `gather_facts: false` | Skip the default fact gathering — network devices do not support it |
| `tasks:` | List of tasks to execute in order |
| `cisco.ios.ios_command:` | Call the ios_command module |
| `commands:` | List of IOS commands to run |
| `register: version_output` | Save the result into a variable called version_output |
| `ansible.builtin.debug:` | Print a variable to the screen |
| `var: version_output.stdout_lines` | Print the stdout_lines field from the registered variable |

### Step 3. Run the playbook

```bash
ansible-playbook gather_info.yml
```

**Expected output structure** (the router prompt/hostname will reflect the instance, e.g. `ip-10-0-1-183`):
```
PLAY [Gather IOS information from routers] *************************************

TASK [Get show version] ********************************************************
ok: [c8kv-1]
ok: [c8kv-2]

TASK [Print show version output] ***********************************************
ok: [c8kv-1] => {
    "version_output.stdout_lines": [
        [
            "Cisco IOS XE Software, Version 17.x ...",
            ...
        ]
    ]
}
ok: [c8kv-2] => {
    ...
}

TASK [Get show ip interface brief] *********************************************
ok: [c8kv-1]
ok: [c8kv-2]

TASK [Print interface output] **************************************************
ok: [c8kv-1] => {
    "interface_output.stdout_lines": [
        [
            "Interface              IP-Address      OK? Method Status Protocol",
            "GigabitEthernet1       10.0.1.x        YES DHCP   up     up",
            ...
        ]
    ]
}

PLAY RECAP *************************************************************
c8kv-1   : ok=4  changed=0  unreachable=0  failed=0  skipped=0
c8kv-2   : ok=4  changed=0  unreachable=0  failed=0  skipped=0
```

> **If this fails to connect**, the problem is in the Lab 1 setup, not this playbook. Re-run the Lab 1 Step 16 verification (`ansible routers -m cisco.ios.ios_command -a "commands='show version'"`) and fix connectivity there first. Common causes: `ansible-pylibssh` not installed, wrong `ansible`/password, or the `ansible_libssh_hostkeys: ssh-rsa` line missing from the inventory.

### Step 4. Understand the PLAY RECAP

The PLAY RECAP at the end is the most important line:

| Counter | Meaning |
|---------|---------|
| ok | Tasks that ran successfully and produced no changes |
| changed | Tasks that made a change to the device |
| unreachable | Devices Ansible could not connect to |
| failed | Tasks that ran but produced an error |
| skipped | Tasks that were skipped due to a condition |

For this playbook you expect `ok=4 changed=0` on both routers — we ran four tasks and nothing was changed.

---

## Part 2 — Using ios_facts for Structured Data

`ios_command` returns raw text output — the same thing you would see if you typed the command yourself. `ios_facts` returns structured data as Python dictionaries that Ansible can work with programmatically.

### Step 5. Add a second play to the playbook

```bash
cat >> gather_info.yml << 'EOF'

- name: Collect structured facts
  hosts: routers
  gather_facts: false

  tasks:

    - name: Gather IOS facts
      cisco.ios.ios_facts:
        gather_subset:
          - all

    - name: Print hostname
      ansible.builtin.debug:
        msg: "Device hostname is {{ ansible_net_hostname }}"

    - name: Print IOS version
      ansible.builtin.debug:
        msg: "IOS-XE version is {{ ansible_net_version }}"

    - name: Print interface list
      ansible.builtin.debug:
        msg: "Interfaces: {{ ansible_net_interfaces.keys() | list }}"
EOF
```

### Step 6. Run the updated playbook

```bash
ansible-playbook gather_info.yml
```

The second play will now run after the first. Look for the structured output from ios_facts — `ansible_net_hostname`, `ansible_net_version`, and `ansible_net_interfaces` are populated automatically by the module.

### Step 7. Explore the full facts structure

To see everything ios_facts collects, add this task to the second play:

```bash
cat >> gather_info.yml << 'EOF'

    - name: Print all facts
      ansible.builtin.debug:
        var: ansible_facts
EOF
```

Run again and observe the volume of structured data returned. This includes interfaces, neighbors, routing table entries, hardware details, and more.

---

## Part 3 — Verbose Mode

Ansible has four levels of verbosity that give you progressively more detail about what it is doing.

### Step 8. Run with -v

```bash
ansible-playbook gather_info.yml -v
```

This shows the full task output including return values.

### Step 9. Run with -vv

```bash
ansible-playbook gather_info.yml -vv
```

This shows connection details — which host Ansible is connecting to and how.

### Step 10. Run with -vvv

```bash
ansible-playbook gather_info.yml -vvv
```

This shows the full debug output including the SSH connection being established, commands being sent, and raw responses being received.

> **Note:** Do not use `-vvvv` in normal operation — it can log sensitive connection details to the screen. Use it only when actively debugging a connection failure.

---

## Part 4 — Using a Separate Facts Playbook

For real network automation you often want a standalone facts collection playbook that you run before any changes to capture the baseline state.

### Step 11. Create a standalone facts playbook

```bash
cat > collect_facts.yml << 'EOF'
---
- name: Collect and save device facts
  hosts: routers
  gather_facts: false

  tasks:

    - name: Gather IOS facts
      cisco.ios.ios_facts:
        gather_subset:
          - all

    - name: Display device summary
      ansible.builtin.debug:
        msg:
          - "Hostname:    {{ ansible_net_hostname }}"
          - "Model:       {{ ansible_net_model }}"
          - "IOS Version: {{ ansible_net_version }}"
          - "Serial:      {{ ansible_net_serialnum }}"

    - name: Save facts to file
      ansible.builtin.copy:
        content: "{{ ansible_facts | to_nice_json }}"
        dest: "/tmp/{{ inventory_hostname }}_facts.json"
      delegate_to: localhost
EOF
```

### Step 12. Run the facts playbook

```bash
ansible-playbook collect_facts.yml
```

After it runs, check the output files:

```bash
cat /tmp/c8kv-1_facts.json | head -50
cat /tmp/c8kv-2_facts.json | head -50
```

You now have a JSON snapshot of both routers that you could diff against a future run to detect configuration drift.

---

## Verification Checklist

| Task | Expected Result | Pass/Fail |
|------|----------------|-----------|
| gather_info.yml runs without errors | ok=4+ changed=0 on both hosts | |
| show version output visible | IOS-XE version string in output | |
| show ip interface brief visible | GigabitEthernet1 up/up visible | |
| ios_facts play runs | Structured data returned | |
| ansible_net_hostname populated | router hostname visible in debug | |
| ansible_net_version populated | IOS-XE version string | |
| collect_facts.yml runs | JSON files created in /tmp | |

---

## Reflection Questions

1. What is the difference between `ios_command` and `ios_facts`? When would you use each?
2. The playbook sets `gather_facts: false`. What would happen if you set it to `true` and why does it need to be false for network devices?
3. Look at the PLAY RECAP — all tasks show `ok` not `changed`. What would need to happen for a task to show `changed=1`?
4. The `register` keyword captures task output into a variable. `version_output.stdout_lines` is a list of lists — why is it nested like that?

---

## Summary

| Concept | Key Point |
|---------|-----------|
| `ios_command` | Runs show commands — returns raw text |
| `ios_facts` | Collects structured device data automatically |
| `register` | Saves task output into a named variable |
| `debug` | Prints variables or messages to screen |
| `gather_facts: false` | Must be false for network devices |
| PLAY RECAP | ok=changed=0 means tasks ran, nothing modified |
| `-v / -vv / -vvv` | Increasing verbosity levels for troubleshooting |

---

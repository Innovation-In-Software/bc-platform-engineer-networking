# Lab 3 – Configure and Verify Idempotency

**Course:** Network Automation Tools — Day 1  
**Prerequisite:** Labs 1 and 2 complete  
**Objective:** Use `ios_config` to push configuration to both Catalyst 8000V routers, understand idempotency in practice, and use `--check` and `--diff` to safely preview changes before applying them.

---

> **Remember:** Stop the `c8kv-1` and `c8kv-2` instances when you finish this lab to avoid unnecessary charges. Go to **EC2 → Instances → select both routers → Instance State → Stop**.

## Overview

In this lab you will:

1. Use `ios_config` to set hostnames and configure a loopback interface on both routers
2. Observe `changed=1` on the first run and `changed=0` on the second run — idempotency in action
3. Use `--check` mode to do a dry run without making any changes
4. Use `--diff` to see exactly what would change before committing
5. Understand why `ios_config` is idempotent but `ios_command` is not

---

## Part 1 — Configure Hostnames and Loopback Interfaces

### Step 1. Create the configuration playbook

```bash
cd ~/ansible-lab

cat > configure_routers.yml << 'EOF'
---
- name: Configure base settings on routers
  hosts: routers
  gather_facts: false

  tasks:

    - name: Set hostname
      cisco.ios.ios_config:
        lines:
          - hostname {{ inventory_hostname }}

    - name: Configure loopback interface
      cisco.ios.ios_config:
        lines:
          - ip address 172.16.1.{{ ansible_host.split('.')[-1] }} 255.255.255.255
        parents:
          - interface Loopback0

    - name: Add interface description
      cisco.ios.ios_config:
        lines:
          - description Managed by Ansible
        parents:
          - interface GigabitEthernet1

    - name: Verify hostname is set
      cisco.ios.ios_command:
        commands:
          - show running-config | include hostname
      register: hostname_check

    - name: Print hostname verification
      ansible.builtin.debug:
        var: hostname_check.stdout_lines
EOF
```

> **What `parents` does:** The `parents` keyword tells ios_config which configuration block to enter before applying the lines. `parents: interface Loopback0` is equivalent to typing `interface Loopback0` on the router first, then entering the sub-commands. Without it, the lines would be applied at the global config level.

> **Why no `no shutdown` on the loopback?** A loopback interface comes up automatically when created, and IOS-XE does **not** store `no shutdown` in the running config (it only records `shutdown` when an interface is administratively down). If you put `no shutdown` in the task, `ios_config` would look for that line in the running config, never find it, and re-apply it on *every* run — breaking idempotency and producing a permanent `changed=1` plus a warning. Omitting it keeps the task idempotent. This is the single most common idempotency trap with `ios_config`: only send lines that actually appear in `show running-config`.

### Step 2. Run the playbook — first run

```bash
ansible-playbook configure_routers.yml
```

**Expected output:**
```
TASK [Set hostname] ************************************************************
changed: [c8kv-1]
changed: [c8kv-2]

TASK [Configure loopback interface] ********************************************
changed: [c8kv-1]
changed: [c8kv-2]

TASK [Add interface description] ***********************************************
changed: [c8kv-1]
changed: [c8kv-2]

PLAY RECAP *************************************************************
c8kv-1   : ok=5  changed=3  unreachable=0  failed=0  skipped=0
c8kv-2   : ok=5  changed=3  unreachable=0  failed=0  skipped=0
```

`changed=3` means three tasks made changes to each router.

> **Note:** The `Set hostname` task changes each router's hostname from its DHCP-assigned name (e.g. `ip-10-0-1-183`) to its inventory name (`c8kv-1`). From this point on, the router's prompt and its `ansible_net_hostname` fact will read `c8kv-1` / `c8kv-2`.

### Step 3. Verify the changes on the routers

SSH into c8kv-1 to confirm the changes were applied. Thanks to the `~/.ssh/config` you set up in Lab 1 (Step 11b), the connection command is simply:

```bash
ssh <c8kv-1-private-ip>
```

> **If that fails** with `no mutual signature supported`, the `~/.ssh/config` from Lab 1 isn't in place — either re-add it, or pass the algorithm flags inline:
> ```bash
> ssh -i ~/.ssh/AutomationLab-Key.pem \
>   -o PubkeyAcceptedAlgorithms=+ssh-rsa \
>   -o HostKeyAlgorithms=+ssh-rsa \
>   ec2-user@<c8kv-1-private-ip>
> ```

On the router:
```
show running-config | section interface Loopback
show running-config | include hostname
show running-config | section GigabitEthernet1
```

You should see:
```
hostname c8kv-1
interface Loopback0
 ip address 172.16.1.x 255.255.255.255
interface GigabitEthernet1
 description Managed by Ansible
```

Type `exit` to return to the control node.

---

## Part 2 — Observe Idempotency

### Step 4. Run the playbook a second time without any changes

```bash
ansible-playbook configure_routers.yml
```

**Expected output:**
```
TASK [Set hostname] ************************************************************
ok: [c8kv-1]
ok: [c8kv-2]

TASK [Configure loopback interface] ********************************************
ok: [c8kv-1]
ok: [c8kv-2]

TASK [Add interface description] ***********************************************
ok: [c8kv-1]
ok: [c8kv-2]

PLAY RECAP *************************************************************
c8kv-1   : ok=5  changed=0  unreachable=0  failed=0  skipped=0
c8kv-2   : ok=5  changed=0  unreachable=0  failed=0  skipped=0
```

`changed=0` on both routers — Ansible checked the current configuration, found it already matched the desired state, and made no changes.

### Step 5. Understand what just happened

`ios_config` works by:
1. Connecting to the router
2. Fetching the current running configuration
3. Comparing it against the lines you specified
4. Only sending lines that are missing or different

If the configuration already matches what you specified, Ansible reports `ok` (no change needed) instead of `changed` (something was applied). This is idempotency — you can safely run the same playbook multiple times and the result is always the same.

### Step 6. Why `ios_command` should not be used for changes

There's an important subtlety here. The `cisco.ios.ios_command` module is designed for **read-only** `show` commands, and it defaults to reporting `ok` (not `changed`) — it does not assume it changed anything. You can see this yourself:

```bash
cat > idempotency_test.yml << 'EOF'
---
- name: Demonstrate ios_command reporting
  hosts: routers
  gather_facts: false

  tasks:

    - name: Run a show command
      cisco.ios.ios_command:
        commands:
          - show clock
      register: output
EOF
```

```bash
ansible-playbook idempotency_test.yml
```

You'll see `ok=1 changed=0` — the module ran a command but correctly reports no change.

So why not use `ios_command` for configuration? The problem is not the `changed` counter — it's that **`ios_command` has no idempotency logic at all.** It cannot enter config mode, it does not compare against the running config, and it will happily send the same command every run whether or not it's needed. `ios_config`, by contrast, fetches the running config, diffs it against your intent, and only sends what's missing.

To make the difference concrete, compare the two approaches to setting a description:

| | `ios_command: "conf t / interface Gi1 / description X"` | `ios_config` |
|---|---|---|
| Enters config mode | You must script it manually | Handled automatically |
| Checks current state first | No — sends blindly every run | Yes — diffs against running config |
| Idempotent | No | Yes |
| Works with `--check`/`--diff` | No | Yes |

**Rule of thumb:** `ios_command` for gathering/showing, `ios_config` for changing. Never push configuration with `ios_command`.

> **Note on the original lab claim:** Older versions of this lab stated that `ios_command` "always shows changed" without a `changed_when: false` override. That is **not** true for `cisco.ios.ios_command`, which defaults to `changed_when: false`. The real reason to avoid it for changes is the lack of idempotency logic described above, not the `changed` flag.

---

## Part 3 — Check Mode and Diff Mode

Check mode and diff mode are your safety tools. Use them before running any playbook that makes changes in production.

### Step 7. Run in check mode (dry run)

Check mode runs the playbook but makes no changes. It tells you what WOULD happen:

```bash
ansible-playbook configure_routers.yml --check
```

**Expected output:**
```
TASK [Set hostname] ************************************************************
ok: [c8kv-1]
ok: [c8kv-2]
```

Since the configuration is already correct from the previous run, check mode shows everything as `ok`. Now make a change to test it — modify the description in the playbook:

```bash
sed -i 's/Managed by Ansible/Managed by Ansible - Updated/' configure_routers.yml
```

Run check mode again:

```bash
ansible-playbook configure_routers.yml --check
```

**Expected output:**
```
TASK [Add interface description] ***********************************************
changed: [c8kv-1]
changed: [c8kv-2]
```

Check mode tells you the description task would make a change — but it has not made it yet. The router is unchanged.

### Step 8. See exactly what would change

You want to see *what* would change before applying it. With `ios_config`, run check mode with verbosity (`-v`), which surfaces the module's `updates` field — the exact configuration lines it would send:

```bash
ansible-playbook configure_routers.yml --check -v
```

**Expected output** (the `Add interface description` task):
```
TASK [Add interface description] ***********************************************
[WARNING]: To ensure idempotency and correct diff the input configuration
lines should be similar to how they appear if present in the running
configuration on device
changed: [c8kv-1] => {"changed": true, "commands": ["interface GigabitEthernet1", "description Managed by Ansible - Updated"], "updates": ["interface GigabitEthernet1", "description Managed by Ansible - Updated"]}
```

The `commands`/`updates` list is the "diff" that matters: it shows the exact lines Ansible would push to the router — here, entering `interface GigabitEthernet1` and setting the new description — **without applying them**, because `--check` is still in effect.

> **About the `[WARNING]` and the absence of a git-style diff:** `cisco.ios.ios_config` frequently prints this idempotency/diff warning even when the task is working correctly, and on many IOS-XE images it reports the pending change via the `commands`/`updates` fields rather than a `--- before / +++ after` block. The `updates` list is the reliable, honest signal of what would be sent. `--diff` may add a before/after view for some line types, but do not rely on it always rendering — trust the `updates` list. (Earlier versions of this lab showed a clean before/after diff for this step; that format is not what the module reliably produces here.)

The `--check` guarantee is what matters operationally: nothing is sent to the device, so you can preview the exact `updates` on production routers with zero risk before committing.

### Step 9. Apply the change for real

```bash
ansible-playbook configure_routers.yml
```

Verify on the router:
```
show running-config | section GigabitEthernet1
```

Should now show `description Managed by Ansible - Updated`.

### Step 10. Revert and confirm idempotency again

Change it back in the playbook:

```bash
sed -i 's/Managed by Ansible - Updated/Managed by Ansible/' configure_routers.yml
```

Run once to apply the revert:
```bash
ansible-playbook configure_routers.yml
```

Run again to confirm idempotency:
```bash
ansible-playbook configure_routers.yml
```

Second run should show `changed=0` on all tasks.

---

## Part 4 — Save the Running Configuration

Changes made by `ios_config` are in the running configuration. They will be lost if the router reloads unless you save them to startup configuration.

### Step 11. Add a save task to the playbook

```bash
cat >> configure_routers.yml << 'EOF'

    - name: Save running config to startup
      cisco.ios.ios_config:
        save_when: modified
EOF
```

> `save_when: modified` only writes the startup config if something actually changed during this playbook run. This is more efficient than always saving — writing the startup config takes time and causes unnecessary flash writes.

### Step 12. Run the updated playbook

```bash
ansible-playbook configure_routers.yml
```

On the router:
```
show startup-config | include hostname
show startup-config | section Loopback
```

The configuration should now be persisted to startup config.

---

## Part 5 — Full Verification Run

### Step 13. Create a verification playbook

A good practice is to separate configuration playbooks from verification playbooks. The configuration playbook makes changes. The verification playbook confirms they took effect.

```bash
cat > verify_config.yml << 'EOF'
---
- name: Verify router configuration
  hosts: routers
  gather_facts: false

  tasks:

    - name: Check hostname
      cisco.ios.ios_command:
        commands:
          - show running-config | include hostname
      register: hostname_result

    - name: Check Loopback0 exists and is up
      cisco.ios.ios_command:
        commands:
          - show interfaces Loopback0
      register: loopback_result

    - name: Check interface description
      cisco.ios.ios_command:
        commands:
          - show running-config | section GigabitEthernet1
      register: description_result

    - name: Print all verification results
      ansible.builtin.debug:
        msg:
          - "=== {{ inventory_hostname }} ==="
          - "Hostname: {{ hostname_result.stdout[0] }}"
          - "Loopback: {{ loopback_result.stdout_lines[0][0] }}"
          - "Description: {{ description_result.stdout[0] }}"
EOF
```

### Step 14. Run the verification playbook

```bash
ansible-playbook verify_config.yml
```

Both routers should show:
- Correct hostname matching the inventory name
- Loopback0 interface up/up
- GigabitEthernet1 with the Ansible description

---

## Verification Checklist

| Task | Expected Result | Pass/Fail |
|------|----------------|-----------|
| First run of configure_routers.yml | changed=3 on both routers | |
| Router shows hostname set | show running-config includes hostname c8kv-1/c8kv-2 | |
| Router shows Loopback0 | Interface exists with correct IP | |
| Second run of configure_routers.yml | changed=0 on both routers | |
| --check mode shows pending changes | changed shown without applying | |
| Check mode shows pending changes | `updates` list shown with `-v`, without applying | |
| save_when: modified works | startup-config updated | |
| verify_config.yml passes | All checks return expected values | |

---

## Reflection Questions

1. Run the configure playbook a third time. Does `changed=0` every time, or could it sometimes show `changed=1` even if you made no edits? What could cause that?
2. What is the difference between `save_when: always`, `save_when: modified`, and `save_when: never`? When would you use each?
3. You used `parents: interface Loopback0` to enter interface configuration mode. What would happen if you removed the `parents` line and just put `ip address 172.16.1.x 255.255.255.255` directly in `lines`?
4. A colleague says "I use ios_command for all my config changes because I can see the exact command being sent." Given that `ios_command` has no idempotency logic and cannot diff against the running config, what are the risks with this approach?
5. You ran `--check --diff` and saw a change would be made. You decided not to apply it. Did the `--check` run affect the router in any way?

---

## Summary

| Concept | Key Point |
|---------|-----------|
| `ios_config` | Idempotent — only sends lines that are missing from the running config |
| `ios_command` | Read-only; defaults to `ok`. Has no idempotency logic, so never use it to push config |
| `changed=0` | Desired state already matches — no changes made |
| `changed=1` | A change was applied to the device |
| `--check` | Dry run — shows what would change without touching the device |
| `--diff` | Adds detail on what would change; with `ios_config`, the `updates`/`commands` list (via `-v`) is the reliable signal |
| `save_when: modified` | Writes startup config only if something changed this run |
| `parents:` | Enters a config sub-mode before applying lines |

---

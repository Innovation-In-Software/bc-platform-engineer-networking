# Lab 6 – Securing Secrets with Vault

**Course:** Network Automation Tools — Day 2  
**Prerequisite:** Lab 5 complete — the `base_config` role and `site.yml` working against both routers  
**Objective:** Remove plain-text secrets from your project. Move sensitive values into an encrypted Ansible Vault file, reference them safely from your playbook, run with a vault password, and confirm the secrets never appear in output or in a repository.

---

> **Remember:** Stop the `c8kv-1` and `c8kv-2` instances when you finish this lab to avoid unnecessary charges. Go to **EC2 → Instances → select both routers → Instance State → Stop**.

## Overview

Your inventory and vars files currently hold values in clear text. Real credentials must never sit in plain text or land in Git. In this lab you will:

1. Identify the secrets in your project
2. Create a dedicated vault file and encrypt it with `ansible-vault`
3. Reference the encrypted values through a plain vars file (the indirection pattern)
4. Run your playbook by supplying the vault password
5. Confirm the secrets are protected — in the file, in output, and in version control
6. Encrypt a single value with `encrypt_string` as a bonus technique

> **One vault password throughout:** This lab uses a single vault password, stored once in `~/.vault_pass`, for **every** vault command. Encrypting with one password and then trying to decrypt with a different one is the most common Vault mistake — this lab avoids it by creating the password file first (Step 3) and using it everywhere.

> **Tip:** Each `cat > file << 'EOF'` block starts with `cat`. If you mistype it as `at`, the file is created empty. A quick `cat <file>` after each block confirms it wrote.

---

## Part 1 — Identify the Secrets

### Step 1. Move to your working directory

```bash
cd ~/ansible-lab
```

### Step 2. Decide what needs protecting

Two values in this project are sensitive:

- The device **enable / become password** (`ansible_become_password`)
- The **SNMP community** string used by the `base_config` role

Right now the SNMP community is plain text in `group_vars/routers.yml`, and the become password sits in plain text in `inventory.yml`. Both belong in a vault.

---

## Part 2 — Create and Encrypt a Vault File

### Step 3. Create the vault password file first

Create the password file **once**, now, and use it for every vault command in this lab. This guarantees encryption and decryption always use the same password.

**This lab's vault password is `L@bVaultPass`.** You will not be prompted to invent one — the command below writes it into `~/.vault_pass`, and every `ansible-vault` command in this lab reads the password from that file. Whenever a step asks for the vault password (for example `--ask-vault-pass` later), the password is `L@bVaultPass`.

```bash
echo 'L@bVaultPass' > ~/.vault_pass
chmod 600 ~/.vault_pass
```

> `chmod 600` ensures only your user can read the password file. In production this file is supplied by a secrets manager or CI system and is never committed to Git.

> **Why this matters:** The most common Ansible Vault error is encrypting a file with one password and later trying to decrypt it with a different one (`Decryption failed (no vault secrets were found that could decrypt)`). Setting the password once here, and passing `--vault-password-file ~/.vault_pass` to every vault command, makes that mismatch impossible.

### Step 4. Convert the group vars into a directory

Ansible auto-loads **every** file inside a `group_vars/<group>/` directory. This lets you keep plain values and encrypted values side by side.

```bash
mkdir -p group_vars/routers
mv group_vars/routers.yml group_vars/routers/vars.yml
```

### Step 5. Create the vault file

Put the secrets in their own file, each prefixed with `vault_` so it is obvious they come from the vault.

```bash
cat > group_vars/routers/vault.yml << 'EOF'
---
vault_become_password: "L@bEnable123"
vault_snmp_community: "S3cr3t-RO"
EOF
```

### Step 6. Encrypt the vault file using the password file

Because you pass `--vault-password-file`, `ansible-vault` uses the password from `~/.vault_pass` instead of prompting — so the encryption password matches the file you'll use to decrypt later.

```bash
ansible-vault encrypt group_vars/routers/vault.yml --vault-password-file ~/.vault_pass
```

**Expected output:**
```
Encryption successful
```

### Step 7. Confirm it is unreadable

```bash
cat group_vars/routers/vault.yml
```

**Expected output:**
```
$ANSIBLE_VAULT;1.1;AES256
39643835306...long block of hex...
```

> **Note:** This encrypted file is now safe to commit to Git. Without the vault password the contents are useless.

---

## Part 3 — Reference the Vault Variables

### Step 8. Point plain variables at the vault values

Edit `group_vars/routers/vars.yml` so the real variable names reference the `vault_` values. This indirection keeps the encrypted names separate from the names your tasks actually use.

```bash
cat >> group_vars/routers/vars.yml << 'EOF'

# Reference the encrypted values from vault.yml
snmp_community: "{{ vault_snmp_community }}"
ansible_become_password: "{{ vault_become_password }}"
EOF
```

### Step 9. Remove the old plain SNMP line

Open `group_vars/routers/vars.yml` and delete the original `snmp_community` line from Lab 4 so the vaulted value is the only one. (In Lab 5 you may have set it to `LabReadOnly`; adjust the pattern if your value differs.)

```bash
sed -i '/^snmp_community: LabReadOnly$/d' group_vars/routers/vars.yml
cat group_vars/routers/vars.yml
```

Confirm the only `snmp_community` line remaining is the Jinja2 reference to `vault_snmp_community`. If you still see a plain `snmp_community:` line with a literal value, delete it manually with `nano`.

> **Also remove the plain become password from the inventory.** In `inventory.yml`, delete the `ansible_become_password: Cisco123!` line — it is now provided by the vaulted `ansible_become_password` reference. Leaving it in inventory would keep a secret in plain text and override the vaulted value.

---

## Part 4 — Run With the Vault Password

### Step 10. Run non-interactively with the password file

```bash
ansible-playbook site.yml --vault-password-file ~/.vault_pass
```

The play decrypts the vault using `~/.vault_pass` and runs. The SNMP community changes to the vaulted value (`S3cr3t-RO`), so on the first run after this change you should see a change on the routers:

```
c8kv-1  : ok=2  changed=... unreachable=0  failed=0
c8kv-2  : ok=2  changed=... unreachable=0  failed=0
```

> **On the `changed` count:** The exact number depends on your routers' current state (as in Labs 3–5). Because the SNMP community value is changing to `S3cr3t-RO`, expect a change on this first run (the render and push tasks) and `changed=0` on a second run. And note — as you learned in Lab 5 — `ios_config` is additive, so the *old* community may remain alongside `S3cr3t-RO`; see the cleanup note below.

> **Leftover community (Lab 5 lesson applies):** If `show running-config | include snmp-server community` shows more than one community, remove the stale one, e.g.:
> ```bash
> ansible routers -m cisco.ios.ios_config -a "lines='no snmp-server community LabReadOnly RO'"
> ```

### Step 11. Run interactively by typing the password

You can also be prompted instead of using the file:

```bash
ansible-playbook site.yml --ask-vault-pass
```

**Expected:**
```
Vault password:
```

Enter `L@bVaultPass` (the same password in `~/.vault_pass`). The play runs identically.

---

## Part 5 — Confirm the Secrets Are Protected

### Step 12. View the vault safely

```bash
ansible-vault view group_vars/routers/vault.yml --vault-password-file ~/.vault_pass
```

This prints the decrypted contents to the screen without ever writing them to disk.

### Step 13. Prove it fails without the password

```bash
ansible-playbook site.yml
```

**Expected error:**
```
ERROR! Attempting to decrypt but no vault secrets found
```

This confirms the data is genuinely protected — the playbook cannot run without the password.

### Step 14. Keep secrets out of output and Git

Make sure the password file and any secret-handling output stay out of version control:

```bash
cat > .gitignore << 'EOF'
.vault_pass
*.retry
EOF
```

> **Note:** Add `no_log: true` to any *custom* task that handles a secret so it never prints in verbose mode. (The role's existing tasks don't echo the secrets, but this is the habit to build.) Never disable `no_log` on a task that touches credentials.

---

## Bonus — Encrypt a Single Value

Sometimes you only need to hide one value in an otherwise readable file. `encrypt_string` produces an inline encrypted blob you can paste directly into YAML. Use the same password file so it matches your vault:

```bash
ansible-vault encrypt_string 'AnotherSecret!' --name 'tacacs_key' --vault-password-file ~/.vault_pass
```

**Expected output:**
```
tacacs_key: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          6631633...
```

Paste that block straight into any vars file, alongside plain values, and Ansible decrypts it at runtime (as long as it's run with the same vault password).

---

## Verification Checklist

| Task | Expected Result | Pass/Fail |
|------|-----------------|-----------|
| `~/.vault_pass` created and chmod 600 | Password file readable only by you | |
| `group_vars/routers/` directory created | `vars.yml` and `vault.yml` present | |
| `ansible-vault encrypt` runs | `vault.yml` starts with `$ANSIBLE_VAULT` | |
| Plain vars reference vault values | `snmp_community` uses `{{ vault_... }}` | |
| Plain become password removed from inventory | No `ansible_become_password: Cisco123!` in inventory.yml | |
| Run with `--vault-password-file` | Playbook completes non-interactively | |
| Run with `--ask-vault-pass` | Playbook completes after typing password | |
| Run without password | Playbook fails with a decrypt error | |
| `.gitignore` created | `.vault_pass` excluded from Git | |
| `encrypt_string` | Inline `!vault` blob produced | |

---

## Reflection Questions

1. Why prefix the encrypted variables with `vault_` and reference them from a separate plain file?
2. What is the difference between `ansible-vault encrypt` and `ansible-vault encrypt_string`?
3. Why must the `--vault-password-file` itself be protected and excluded from Git?
4. When would you use `no_log: true`, and what is the risk of disabling it on a task that handles a password?
5. This lab creates the password file *before* encrypting, and uses it for every vault command. Why does that prevent the "encrypted with one password, decrypting with another" error?

---

## Summary

| Concept | Key Point |
|---------|-----------|
| Ansible Vault | Encrypts secrets at rest so they are safe in Git |
| Consistent password | Create the password file first; use it for encrypt, run, view — so passwords always match |
| `ansible-vault encrypt` | Encrypts an entire file |
| `group_vars/<group>/` | Directory that auto-loads plain and vaulted files together |
| `vault_` indirection | Keeps encrypted names separate from the names tasks use |
| `--ask-vault-pass` | Prompts for the password at runtime |
| `--vault-password-file` | Supplies the password non-interactively for automation |
| `no_log: true` | Prevents a task from printing secrets |
| `encrypt_string` | Encrypts a single value as an inline `!vault` blob |

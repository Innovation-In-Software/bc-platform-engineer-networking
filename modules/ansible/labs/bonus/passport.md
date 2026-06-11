# Ansible Host Passport - Facts and Templates Lab

## Scenario

Your team wants every managed server to have a small local “host passport” file containing basic information about the machine. This file should be generated automatically using Ansible facts and inventory group information.

You need to create a Jinja2 template and a playbook that generates a unique `/tmp/host-passport.txt` file on each managed host.

## Prerequisites

This lab assumes you have:

* The `ansible-working-[your initials]` project already created in Automation Platform
* The `First Inventory-[your initials]` configured with two managed nodes
* Linux credentials configured in Automation Platform
* VS Code with access to your `ansible-working` repository
* At least two inventory groups:

  * `web`
  * `app`

If you do not have these groups yet, create them before continuing.

## Update Inventory Groups

We need the two managed nodes to have different roles.

1. Navigate to **Automation Execution** → **Infrastructure** → **Inventories**
2. Click **First Inventory-[your initials]**
3. Click the **Groups** tab
4. Create a group named `web`
5. Add the first managed node to the `web` group
6. Go back to the **Groups** tab
7. Create a group named `app`
8. Add the second managed node to the `app` group

## Create the Template and Playbook

In VS Code, open your `ansible-working` repository.

### Create the Directory

Create a directory named:

```text
host-passport-lab
```

### Create the Jinja2 Template

Inside `host-passport-lab`, create a file named `host-passport.j2` with the following content:

```jinja2
Host Passport
=============

Inventory name: {{ inventory_hostname }}
System hostname: {{ ansible_facts['hostname'] }}
Distribution: {{ ansible_facts['distribution'] }}
Distribution version: {{ ansible_facts['distribution_version'] }}

Primary IPv4 address: {{ ansible_default_ipv4.address | default('unknown') }}

Inventory groups:
{{ group_names | join(', ') }}

{% if 'web' in group_names %}
Role: WEB NODE
{% elif 'app' in group_names %}
Role: APP NODE
{% else %}
Role: GENERIC NODE
{% endif %}

Managed by Ansible: yes
```

### Create the Playbook

Inside `host-passport-lab`, create a playbook named `passport.yml`:

```yaml
---
- name: Generate host passport files
  hosts: all
  gather_facts: true

  tasks:
    - name: Deploy host passport file
      ansible.builtin.template:
        src: host-passport.j2
        dest: /tmp/host-passport.txt
        mode: '0644'

    - name: Display completion message
      ansible.builtin.debug:
        msg: "Host passport generated for {{ inventory_hostname }}"
```

## Commit and Push Changes to GitHub

1. Save your changes
2. Open the **Source Control** pane in VS Code
3. Review the new files
4. Commit with the message:

```text
Add host passport lab
```

1. Push the changes to GitHub

## Create Job Template

In Automation Platform, create a new job template:

1. Navigate to **Automation Execution** → **Templates**

2. Click **Create template**

3. Select **Create job template**

4. Fill in the following details:

   * **Name**: `generate_host_passport-[your initials]`
   * **Description**: `Generate host passport files using facts and templates`
   * **Job Type**: `Run`
   * **Inventory**: `First Inventory-[your initials]`
   * **Project**: `ansible-working-[your initials]`
   * **Execution Environment**: `Default execution environment`
   * **Playbook**: `host-passport-lab/passport.yml`
   * **Credentials**: `Linux credentials-[your initials]`

5. Click **Create job template**

## Run the Job Template

1. Click **Launch template**
2. Monitor the job output
3. Confirm that the template task completes successfully for both hosts

## Verify the Deployment

Run an ad-hoc command in Automation Platform.

**Step 1 – Details**

* **Module**: `shell`
* **Arguments**:

```bash
cat /tmp/host-passport.txt
```

**Step 2 – Execution Environment**

* **Execution Environment**: Default execution environment

**Step 3 – Credential**

* **Credential**: `Linux credentials-[your initials]`

**Step 4 – Review**

* Click **Finish**

Expected output will be different for each host.

Example for a web host:

```text
Host Passport
=============

Inventory name: server1
System hostname: server1
Distribution: RedHat
Distribution version: 9.2

Primary IPv4 address: 192.168.1.10

Inventory groups:
web

Role: WEB NODE

Managed by Ansible: yes
```

Example for an app host:

```text
Role: APP NODE
```

## Understanding the Template

This template uses several Ansible concepts:

* `{{ inventory_hostname }}`: the host name from the inventory
* `{{ ansible_facts['hostname'] }}`: the system hostname discovered by facts
* `{{ ansible_default_ipv4.address }}`: the primary IPv4 address
* `{{ group_names }}`: the list of groups this host belongs to
* `{% if 'web' in group_names %}`: conditional Jinja2 logic
* `| default('unknown')`: a filter used when a value may be missing
* `| join(', ')`: a filter that converts a list into a readable string

## Test Idempotency

Run the job template again.

The second run should not change the file if nothing in the template or facts changed.

Look for:

```text
changed=0
```

or confirm that the template task reports `ok` instead of `changed`.

## Conclusion

Congratulations! You have successfully:

* Used Ansible facts in a Jinja2 template
* Used inventory group membership inside a template
* Generated host-specific content
* Deployed a file to all managed nodes
* Verified that each host received customized output
* Tested idempotent behavior

This lab demonstrates how Ansible templates can create consistent but host-specific configuration files.

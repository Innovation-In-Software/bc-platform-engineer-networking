# Ansible YAML Surgery - Syntax Repair Lab

## Scenario

A teammate started writing a simple Ansible playbook but pushed it before testing the YAML syntax. The playbook is supposed to create a text file on all managed servers, but it currently fails because the YAML structure is invalid.

Your task is to diagnose the problem, fix the playbook, test it locally from the controller, and then run it through Ansible Automation Platform.

## Prerequisites

This lab assumes you have:

* The `ansible-working-[your initials]` project already created in Automation Platform
* The `First Inventory-[your initials]` configured with your two managed nodes
* Linux credentials configured in Automation Platform
* VS Code with access to your `ansible-working` repository
* Terminal access on the Ansible controller

## Create the Broken Playbook

In VS Code, open your `ansible-working` repository.

1. Create a directory named `yaml-surgery-lab`
2. Inside `yaml-surgery-lab`, create a file named `broken.yml`
3. Add the following intentionally broken content:

```yaml
---
name: Broken YAML playbook
hosts: all
tasks:
- name: Create lab file
copy:
content: "This file was created after fixing YAML"
dest: /tmp/yaml-surgery.txt
```

## Test the Broken Playbook

From the terminal on the controller, run:

```bash
ansible-playbook broken.yml -i /home/ansible/inventory/inventory.yaml --syntax-check
```

You should see a YAML or playbook syntax error.

The exact error message may vary, but the playbook should not pass the syntax check.

## Fix the Playbook

Update `broken.yml` so that it contains valid Ansible YAML:

```yaml
---
- name: Fixed YAML playbook
  hosts: all

  tasks:
    - name: Create lab file
      ansible.builtin.copy:
        content: "This file was created after fixing YAML"
        dest: /tmp/yaml-surgery.txt
```

## Run Syntax Check Again

Run:

```bash
ansible-playbook broken.yml -i /home/ansible/inventory/inventory.yaml --syntax-check
```

Expected result:

```text
playbook: broken.yml
```

## Run the Playbook Locally from the Controller

Run:

```bash
ansible-playbook broken.yml -i /home/ansible/inventory/inventory.yaml --syntax-check
```

The playbook should complete successfully and create `/tmp/yaml-surgery.txt` on both managed nodes.

## Commit and Push Changes to GitHub

1. Confirm you have saved your changes
2. In VS Code, click the **Source Control** icon
3. Review the changes
4. Enter the commit message:

```text
Add YAML surgery lab
```

1. Commit the changes
2. Push the changes to GitHub

## Create Job Template

In Automation Platform, create a new job template:

1. Navigate to **Automation Execution** → **Templates**

2. Click **Create template**

3. Select **Create job template**

4. Fill in the following details:

   * **Name**: `yaml_surgery-[your initials]`
   * **Description**: `Run fixed YAML playbook`
   * **Job Type**: `Run`
   * **Inventory**: `First Inventory-[your initials]`
   * **Project**: `ansible-working-[your initials]`
   * **Execution Environment**: `Default execution environment`
   * **Playbook**: `yaml-surgery-lab/broken.yml`
   * **Credentials**: `Linux credentials-[your initials]`

5. Click **Create job template**

## Run the Job Template

1. Click **Launch template**
2. Monitor the job output
3. Confirm that the file creation task runs successfully on both hosts

## Verify the Deployment

Use an ad-hoc command in Automation Platform:

1. Navigate to **Automation Execution** → **Infrastructure** → **Inventories**
2. Open `First Inventory-[your initials]`
3. Click the **Hosts** tab
4. Select both hosts
5. Click **Run command**

**Step 1 – Details**

* **Module**: `shell`
* **Arguments**:

```bash
cat /tmp/yaml-surgery.txt
```

* Click **Next**

**Step 2 – Execution Environment**

* **Execution Environment**: Default execution environment
* Click **Next**

**Step 3 – Credential**

* **Credential**: `Linux credentials-[your initials]`
* Click **Next**

**Step 4 – Review**

* Click **Finish**

Expected output:

```text
This file was created after fixing YAML
```

## Understanding the Fix

The original playbook failed because:

* A playbook must usually start with a YAML list item: `- name:`
* `hosts` must be indented under the play
* `tasks` must be indented under the play
* Each task must be a list item under `tasks`
* Module parameters must be indented under the module name

Broken structure:

```yaml
tasks:
- name: Create lab file
copy:
content: "..."
```

Correct structure:

```yaml
tasks:
  - name: Create lab file
    ansible.builtin.copy:
      content: "..."
      dest: "..."
```

## Conclusion

Congratulations! You have successfully:

* Identified a broken YAML playbook
* Used `--syntax-check` to validate the playbook
* Fixed indentation and playbook structure
* Ran the playbook locally
* Ran the fixed playbook through Automation Platform
* Verified the result on managed nodes

This lab demonstrates why YAML formatting is critical in Ansible and why syntax checking should be part of your normal workflow.
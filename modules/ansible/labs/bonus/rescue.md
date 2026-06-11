# Ansible Blocks - Rescue and Rollback Lab

## Scenario

A deployment team is testing a new application release process. The process should create a release directory, place a version file inside it, and then perform a deployment step.

However, deployments sometimes fail. If a failure happens, the playbook must perform a controlled rollback:

* Record which task failed
* Remove the partially deployed release directory
* Always write a summary file
* Mark the job as failed so that Automation Platform clearly shows that the deployment did not succeed

---

## Prerequisites

This lab assumes you have:

* The `ansible-working-[your initials]` project already created in Automation Platform
* The `First Inventory-[your initials]` configured with your managed nodes
* Linux credentials configured in Automation Platform
* VS Code with access to your `ansible-working` repository
* At least one Linux managed node available
* Privilege escalation available if your environment requires it

This lab is designed to run on managed nodes only. If your inventory also contains the controller as a host, create a dedicated group for the target nodes before running the lab.

---

## Update Inventory Groups

We will create a group named `rollback_targets` and add only the managed nodes to it.

1. Navigate to **Automation Execution** → **Infrastructure** → **Inventories**

2. Click **First Inventory-[your initials]**

3. Click the **Groups** tab

4. Click **Create group**

5. Fill in the following details:

   * **Name**: `rollback_targets`
   * **Description**: `Hosts used for the blocks rescue rollback lab`

6. Click **Create group**

7. Open the `rollback_targets` group

8. Click the **Hosts** tab

9. Click **Add host**

10. Select **Add existing host**

11. Select your managed nodes, for example:

* `TargetNode-1-[your initials]`
* `TargetNode-2-[your initials]`

12. Click **Confirm**

Do not add the control node to this group.

---

## Create the Playbook

In VS Code, open your `ansible-working` repository.

### Create the Directory

Create a directory named:

```text
blocks-rescue-lab
```

### Create the Playbook

Inside the `blocks-rescue-lab` directory, create a playbook named `rollback.yml` with the following content:

```yaml
---
- name: Simulate deployment with rollback
  hosts: rollback_targets
  gather_facts: false

  vars:
    app_dir: /tmp/app-release
    rollback_log: /tmp/app-rollback.log
    summary_log: /tmp/app-summary.log
    app_version: "1.0.0"

  tasks:
    - name: Deploy application with rollback protection
      block:
        - name: Create application release directory
          ansible.builtin.file:
            path: "{{ app_dir }}"
            state: directory
            mode: '0755'

        - name: Create application version file
          ansible.builtin.copy:
            content: "version={{ app_version }}"
            dest: "{{ app_dir }}/version.txt"
            mode: '0644'

        - name: Simulate deployment failure
          ansible.builtin.command: /bin/false

      rescue:
        - name: Record failed task name
          ansible.builtin.copy:
            content: |
              Rollback was executed.
              Failed task: {{ ansible_failed_task.name }}
              Host: {{ inventory_hostname }}
            dest: "{{ rollback_log }}"
            mode: '0644'

        - name: Remove partially deployed release directory
          ansible.builtin.file:
            path: "{{ app_dir }}"
            state: absent

        - name: Mark deployment as failed after rollback
          ansible.builtin.fail:
            msg: "Deployment failed on {{ inventory_hostname }}. Rollback was completed."

      always:
        - name: Write deployment summary
          ansible.builtin.copy:
            content: |
              Deployment process finished.
              Host: {{ inventory_hostname }}
              Summary file created from always block.
            dest: "{{ summary_log }}"
            mode: '0644'
```

---

## Important Note About Expected Failure

This playbook is intentionally designed to fail.

The task named:

```text
Simulate deployment failure
```

runs:

```bash
/bin/false
```

That command always returns a failure exit code.

The purpose of the lab is not to make the job green. The purpose is to confirm that:

* The failure is caught by `rescue`
* The rollback runs
* The partially created release directory is removed
* The summary file is created by `always`
* The final job is marked as failed on purpose

The final failure is expected because of this task:

```yaml
- name: Mark deployment as failed after rollback
  ansible.builtin.fail:
    msg: "Deployment failed on {{ inventory_hostname }}. Rollback was completed."
```

This is a realistic pattern: cleanup can succeed, but the deployment should still be reported as failed.

---

## Commit and Push Changes to GitHub

1. Confirm you have saved your changes
2. In VS Code, click the **Source Control** icon
3. In the **Source Control** pane, review the new files
4. Enter the commit message:

```text
Add blocks rescue rollback lab
```

5. Click **Commit**
6. Click **Yes** if prompted to stage all files
7. Click the **...** menu in the Source Control pane
8. Select **Push** to push the changes to GitHub
9. If prompted, authenticate with GitHub

---

## Sync the Project in Automation Platform

Before creating or running the Job Template, make sure Automation Platform has the latest version of your repository.

1. Navigate to **Automation Execution** → **Projects**
2. Open `ansible-working-[your initials]`
3. Click **Sync project**
4. Wait until the sync completes successfully

---

## Create Job Template

In Automation Platform, create a new job template.

1. Navigate to **Automation Execution** → **Templates**

2. Click **Create template**

3. Select **Create job template**

4. Fill in the following details:

   * **Name**: `blocks_rescue_rollback-[your initials]`
   * **Description**: `Simulate deployment failure and rollback with block rescue always`
   * **Job Type**: `Run`
   * **Inventory**: `First Inventory-[your initials]`
   * **Project**: `ansible-working-[your initials]`
   * **Execution Environment**: `Default execution environment`
   * **Playbook**: `blocks-rescue-lab/rollback.yml`
   * **Credentials**: `Linux credentials-[your initials]`

5. If your environment requires privilege escalation, enable:

   * **Privilege escalation**: checked

6. Click **Create job template**

---

## Run the Job Template

1. Click the **Launch template** button on `blocks_rescue_rollback-[your initials]`
2. Monitor the job execution in real time
3. The job should eventually show a failure

This failure is expected.

The output should show:

* The release directory being created
* The version file being created
* The intentional failure
* The rescue tasks running
* The rollback log being written
* The release directory being removed
* The always task writing the summary file
* The final controlled failure message

Expected final error message will look similar to:

```text
Deployment failed on TargetNode-1. Rollback was completed.
```

---

## Verify the Rollback

Use ad-hoc commands in Automation Platform.

1. Navigate to **Automation Execution** → **Infrastructure** → **Inventories**
2. Select **First Inventory-[your initials]**
3. Click the **Hosts** tab
4. Select only the hosts that belong to the `rollback_targets` group
5. Click **Run command**

This opens a four-step wizard.

---

### Step 1 – Details

Use the `shell` module.

* **Module**: `shell`
* **Arguments**:

```bash
echo "Checking release directory:" && \
test ! -d /tmp/app-release && echo "OK: release directory was removed" || echo "ERROR: release directory still exists"; \
echo "--- rollback log ---"; \
cat /tmp/app-rollback.log; \
echo "--- summary log ---"; \
cat /tmp/app-summary.log
```

* **Privilege escalation**: leave unchecked unless your environment requires it
* Click **Next**

---

### Step 2 – Execution Environment

* **Execution Environment**: `Default execution environment`
* Click **Next**

---

### Step 3 – Credential

* **Credential**: `Linux credentials-[your initials]`
* Click **Next**

---

### Step 4 – Review

1. Confirm the values
2. Click **Finish**

---

## Expected Output

The release directory should be gone:

```text
OK: release directory was removed
```

The rollback log should contain the failed task name:

```text
--- rollback log ---
Rollback was executed.
Failed task: Simulate deployment failure
Host: TargetNode-1
```

The summary log should exist because the `always` block runs no matter what:

```text
--- summary log ---
Deployment process finished.
Host: TargetNode-1
Summary file created from always block.
```

The host names will match your actual inventory.

---

## Verify That the Release Directory Was Removed

You can also run a simpler ad-hoc command:

* **Module**: `shell`
* **Arguments**:

```bash
ls -ld /tmp/app-release /tmp/app-rollback.log /tmp/app-summary.log
```

Expected behavior:

* `/tmp/app-release` should not exist
* `/tmp/app-rollback.log` should exist
* `/tmp/app-summary.log` should exist

You may see output similar to:

```text
ls: cannot access '/tmp/app-release': No such file or directory
-rw-r--r--. 1 user user 91 /tmp/app-rollback.log
-rw-r--r--. 1 user user 95 /tmp/app-summary.log
```

---

## Understanding the Block

The `block` section contains the normal deployment steps:

```yaml
block:
  - name: Create application release directory
  - name: Create application version file
  - name: Simulate deployment failure
```

Ansible executes these tasks in order.

When the task `Simulate deployment failure` fails, Ansible stops executing the remaining tasks in the block and moves into the `rescue` section.

---

## Understanding the Rescue Section

The `rescue` section runs only when a task inside the block fails.

In this lab, `rescue` does three things:

* Writes a rollback log
* Removes the partially deployed application directory
* Uses the `fail` module to mark the deployment as failed

The variable:

```jinja2
{{ ansible_failed_task.name }}
```

contains the name of the task that caused the failure.

In this lab, it should resolve to:

```text
Simulate deployment failure
```

This is useful because rollback logs can show exactly which step failed.

---

## Understanding the Always Section

The `always` section runs whether the block succeeds or fails.

In this lab, the `always` section creates:

```text
/tmp/app-summary.log
```

This is useful for cleanup, summaries, notifications, and diagnostic files that should always be created at the end of a process.

---

## Optional Challenge 1 - Make the Failure Configurable

Currently, the playbook always fails because it always runs `/bin/false`.

Modify the playbook so that the failure is controlled by a variable named `force_failure`.

Add this variable:

```yaml
vars:
  force_failure: true
```

Then replace the failure task with:

```yaml
- name: Simulate deployment failure
  ansible.builtin.command: /bin/false
  when: force_failure | bool
```

Now you can control whether the deployment succeeds or fails.

---

## Optional Challenge 2 - Add a Survey

Add a Survey to the Job Template.

1. Open the `blocks_rescue_rollback-[your initials]` Job Template
2. Click the **Survey** tab
3. Click **Create survey question**

Create the first question:

* **Question**: `Application version`
* **Answer variable name**: `app_version`
* **Answer type**: `Text`
* **Default answer**: `1.0.0`
* **Required**: yes

Create the second question:

* **Question**: `Force deployment failure?`
* **Answer variable name**: `force_failure`
* **Answer type**: `Multiple choice single select`
* **Choices**:

```text
true
false
```

* **Default answer**: `true`
* **Required**: yes

Save and enable the survey.

Update the playbook so that `force_failure` is defined by the survey:

```yaml
vars:
  app_dir: /tmp/app-release
  rollback_log: /tmp/app-rollback.log
  summary_log: /tmp/app-summary.log
  app_version: "1.0.0"
  force_failure: true
```

And update the failure task:

```yaml
- name: Simulate deployment failure
  ansible.builtin.command: /bin/false
  when: force_failure | bool
```

Now launch the template twice:

First run:

```text
app_version: 1.0.0
force_failure: true
```

Expected result:

* Job fails
* Rollback runs
* `/tmp/app-release` is removed

Second run:

```text
app_version: 1.1.0
force_failure: false
```

Expected result:

* Job succeeds
* Rollback does not run
* `/tmp/app-release/version.txt` exists
* `/tmp/app-summary.log` exists

---

## Optional Challenge 3 - Verify Successful Deployment

If you completed Optional Challenge 2 and launched the job with:

```text
force_failure: false
```

run this ad-hoc command:

* **Module**: `shell`
* **Arguments**:

```bash
echo "--- release version ---"; \
cat /tmp/app-release/version.txt; \
echo "--- summary log ---"; \
cat /tmp/app-summary.log
```

Expected output:

```text
--- release version ---
version=1.1.0
--- summary log ---
Deployment process finished.
Host: TargetNode-1
Summary file created from always block.
```

---

## Cleanup

If you want to reset the lab environment, run an ad-hoc command:

* **Module**: `shell`
* **Arguments**:

```bash
rm -rf /tmp/app-release /tmp/app-rollback.log /tmp/app-summary.log
```

Use privilege escalation only if your environment requires it.

---

## Conclusion

Congratulations! You have successfully:

* Created a playbook using `block`, `rescue`, and `always`
* Simulated a deployment failure
* Captured the failed task name using `ansible_failed_task.name`
* Removed a partially deployed application directory
* Created a summary file that is written no matter what happens
* Marked the job as failed after rollback
* Verified rollback behavior with ad-hoc commands
* Optionally made the failure controlled by an Automation Platform Survey

This lab demonstrates a key production pattern: a rollback can succeed, but the original deployment should still be reported as failed if the intended change was not completed.

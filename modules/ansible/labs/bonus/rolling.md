# Ansible Rolling Update - Serial Deployment Lab

## Scenario

Your team needs to update two managed servers, but only one server should be updated at a time. This approach reduces risk because one server remains available while the other is being updated.

In this lab, you will simulate a rolling deployment by creating a release marker file on each host. You will use the `serial` keyword to process the hosts one at a time.

## Prerequisites

This lab assumes you have:

* The `ansible-working-[your initials]` project already created in Automation Platform
* The `First Inventory-[your initials]` configured with two managed nodes
* Linux credentials configured in Automation Platform
* VS Code with access to your `ansible-working` repository

## Create the Playbook

In VS Code, open your `ansible-working` repository.

### Create the Directory

Create a directory named:

```text
rolling-update-lab
```

### Create the Playbook

Inside `rolling-update-lab`, create a playbook named `rolling.yml`:

```yaml
---
- name: Simulated rolling update
  hosts: all
  serial: 1
  max_fail_percentage: 50

  vars:
    release_version: "1.0.0"
    break_host: ""

  tasks:
    - name: Show current host being updated
      ansible.builtin.debug:
        msg: "Starting rolling update on {{ inventory_hostname }}"

    - name: Create application directory
      ansible.builtin.file:
        path: /tmp/platform-app
        state: directory
        mode: '0755'

    - name: Deploy release version marker
      ansible.builtin.copy:
        content: "{{ release_version }}"
        dest: /tmp/platform-app/release-version.txt
        mode: '0644'
      notify: restart fake application

    - name: Simulate maintenance time
      ansible.builtin.pause:
        seconds: 5

    - name: Optional simulated failure
      ansible.builtin.fail:
        msg: "Simulated failure on {{ inventory_hostname }}"
      when: inventory_hostname == break_host

    - name: Run health check
      ansible.builtin.command: test -f /tmp/platform-app/release-version.txt
      changed_when: false

    - name: Show successful update message
      ansible.builtin.debug:
        msg: "Rolling update completed on {{ inventory_hostname }}"

  handlers:
    - name: restart fake application
      ansible.builtin.debug:
        msg: "Fake application restarted on {{ inventory_hostname }}"
```

## Commit and Push Changes to GitHub

1. Save your changes
2. Open the **Source Control** pane
3. Review the new playbook
4. Commit with the message:

```text
Add rolling update lab
```

1. Push the changes to GitHub

## Create Job Template

In Automation Platform, create a new job template:

1. Navigate to **Automation Execution** → **Templates**

2. Click **Create template**

3. Select **Create job template**

4. Fill in the following details:

   * **Name**: `rolling_update-[your initials]`
   * **Description**: `Run simulated rolling update one host at a time`
   * **Job Type**: `Run`
   * **Inventory**: `First Inventory-[your initials]`
   * **Project**: `ansible-working-[your initials]`
   * **Execution Environment**: `Default execution environment`
   * **Playbook**: `rolling-update-lab/rolling.yml`
   * **Credentials**: `Linux credentials-[your initials]`

5. Click **Create job template**

## Add a Survey

Add a survey to the job template.

1. Open the `rolling_update-[your initials]` job template
2. Click the **Survey** tab
3. Click **Create survey question**

Create the first question:

* **Question**: `Release version`
* **Answer variable name**: `release_version`
* **Answer type**: `Text`
* **Default answer**: `1.0.0`
* **Required**: yes

Create the second question:

* **Question**: `Host to break intentionally`
* **Answer variable name**: `break_host`
* **Answer type**: `Text`
* **Default answer**: leave empty
* **Required**: no

Save and enable the survey.

## Run the Job Template

1. Click **Launch template**
2. Enter:

```text
release_version: 1.0.0
break_host:
```

1. Monitor the output carefully

Because `serial: 1` is used, you should see Ansible complete the tasks for one host before moving to the next host.

## Verify the Deployment

Run an ad-hoc command.

**Step 1 – Details**

* **Module**: `shell`
* **Arguments**:

```bash
cat /tmp/platform-app/release-version.txt
```

**Step 2 – Execution Environment**

* **Execution Environment**: Default execution environment

**Step 3 – Credential**

* **Credential**: `Linux credentials-[your initials]`

**Step 4 – Review**

* Click **Finish**

Expected output:

```text
1.0.0
```

## Test a New Release

Launch the job template again.

Use:

```text
release_version: 1.1.0
break_host:
```

The release marker should be updated to `1.1.0`.

## Optional Failure Test

Launch the job template again and set:

```text
release_version: 1.2.0
break_host: <name of one managed host from your inventory>
```

Observe what happens when one host fails.

## Understanding Rolling Updates

This lab demonstrates:

* `serial: 1` limits execution to one host at a time
* Rolling updates reduce the risk of changing all hosts at once
* `max_fail_percentage` can stop a play if too many hosts fail
* Handlers still work during rolling updates
* Surveys can be used to make release versions dynamic

## Conclusion

Congratulations! You have successfully:

* Created a rolling update playbook
* Used `serial` to control batch size
* Used a survey to provide release input
* Simulated a controlled host failure
* Verified release deployment on managed nodes

This lab demonstrates how Ansible can safely orchestrate changes across multiple servers.
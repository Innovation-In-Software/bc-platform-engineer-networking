---

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
ansible-playbook -i inventory.ini yaml-surgery-lab/broken.yml --syntax-check
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
ansible-playbook -i inventory.ini yaml-surgery-lab/broken.yml --syntax-check
```

Expected result:

```text
playbook: yaml-surgery-lab/broken.yml
```

## Run the Playbook Locally from the Controller

Run:

```bash
ansible-playbook -i inventory.ini yaml-surgery-lab/broken.yml
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

5. Commit the changes
6. Push the changes to GitHub

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

---

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

5. Push the changes to GitHub

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

---

# Ansible Handler Orchestra - Notify and Handler Lab

## Scenario

Your team has a simple service configuration file that should be deployed to all managed servers. When the configuration changes, a restart action should be triggered. However, the restart should not run if the configuration file did not change.

Because this is a training environment, we will not restart a real service. Instead, the handler will write a marker line to `/tmp/demo-service-restarted.log`.

## Prerequisites

This lab assumes you have:

* The `ansible-working-[your initials]` project already created in Automation Platform
* The `First Inventory-[your initials]` configured with your managed nodes
* Linux credentials configured in Automation Platform
* VS Code with access to your `ansible-working` repository

## Create the Template and Playbook

In VS Code, open your `ansible-working` repository.

### Create the Directory

Create a directory named:

```text
handlers-lab
```

### Create the Jinja2 Template

Inside `handlers-lab`, create a file named `demo-service.conf.j2`:

```jinja2
# Demo service configuration
# Managed by Ansible

service_name={{ demo_service_name }}
service_port={{ demo_service_port }}
environment={{ demo_environment }}
```

### Create the Playbook

Inside `handlers-lab`, create a playbook named `handlers.yml`:

```yaml
---
- name: Deploy demo service configuration
  hosts: all
  gather_facts: true

  vars:
    demo_service_name: training-service
    demo_service_port: 8080
    demo_environment: lab

  tasks:
    - name: Deploy demo service configuration file
      ansible.builtin.template:
        src: demo-service.conf.j2
        dest: /tmp/demo-service.conf
        mode: '0644'
      notify: restart demo service

    - name: Display configuration deployment message
      ansible.builtin.debug:
        msg: "Demo service configuration checked on {{ inventory_hostname }}"

  handlers:
    - name: Write restart marker
      ansible.builtin.lineinfile:
        path: /tmp/demo-service-restarted.log
        line: "Restart triggered for {{ demo_service_name }} on {{ inventory_hostname }}"
        create: true
        mode: '0644'
      listen: restart demo service
```

## Commit and Push Changes to GitHub

1. Save your changes
2. Open the **Source Control** pane
3. Review the new files
4. Commit with the message:

```text
Add handlers lab
```

5. Push the changes to GitHub

## Create Job Template

In Automation Platform, create a new job template:

1. Navigate to **Automation Execution** → **Templates**

2. Click **Create template**

3. Select **Create job template**

4. Fill in the following details:

   * **Name**: `handler_orchestra-[your initials]`
   * **Description**: `Deploy config and trigger handler only on change`
   * **Job Type**: `Run`
   * **Inventory**: `First Inventory-[your initials]`
   * **Project**: `ansible-working-[your initials]`
   * **Execution Environment**: `Default execution environment`
   * **Playbook**: `handlers-lab/handlers.yml`
   * **Credentials**: `Linux credentials-[your initials]`

5. Click **Create job template**

## Run the Job Template

1. Click **Launch template**
2. Monitor the output
3. The first run should report a change for the template task
4. The handler should run because the configuration file was created

Expected handler output should show that the restart marker task ran.

## Verify the Deployment

Run an ad-hoc command.

**Step 1 – Details**

* **Module**: `shell`
* **Arguments**:

```bash
cat /tmp/demo-service.conf && echo "---" && cat /tmp/demo-service-restarted.log
```

**Step 2 – Execution Environment**

* **Execution Environment**: Default execution environment

**Step 3 – Credential**

* **Credential**: `Linux credentials-[your initials]`

**Step 4 – Review**

* Click **Finish**

Expected output:

```text
# Demo service configuration
# Managed by Ansible

service_name=training-service
service_port=8080
environment=lab
---
Restart triggered for training-service on server1
```

## Test Idempotency

Launch the same job template again without changing anything.

Expected behavior:

* The template task should report `ok`
* The handler should not run again
* The restart marker file should not receive a new line

## Force a Configuration Change

Edit `handlers.yml` and change:

```yaml
demo_service_port: 8080
```

to:

```yaml
demo_service_port: 9090
```

Commit and push the change:

```text
Change demo service port
```

Run the job template again.

The template task should report `changed`, and the handler should run again.

## Understanding Handlers

This lab demonstrates:

* A task can notify a handler using `notify`
* A handler only runs when the notifying task reports `changed`
* A handler does not run when the task reports `ok`
* The `listen` keyword allows handlers to listen for a topic name
* Handlers are useful for restarts, reloads, cache refreshes, and other actions that should happen only after a change

## Conclusion

Congratulations! You have successfully:

* Created a template-managed configuration file
* Used `notify` to trigger a handler
* Used `listen` to decouple the handler name from the notify topic
* Verified that handlers only run after changes
* Tested Ansible idempotency

This lab demonstrates why handlers are an important part of safe and efficient configuration management.

---

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

5. Push the changes to GitHub

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

3. Monitor the output carefully

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

---

# Ansible Debugger Escape Room - Interactive Troubleshooting Lab

## Scenario

A playbook was written to install a package, but it fails because the task references the wrong variable name. Instead of immediately editing the playbook and running it again, you will use the Ansible task debugger to inspect the failing task, temporarily fix it, and rerun the task.

This lab is intentionally performed from the command line because the Ansible debugger is interactive.

## Prerequisites

This lab assumes you have:

* Terminal access to the Ansible controller
* An inventory file that can reach at least one managed host
* SSH access from the controller to the managed host
* Basic familiarity with `ansible-playbook`
* VS Code with access to your `ansible-working` repository

## Create the Debugger Lab Playbook

In VS Code, open your `ansible-working` repository.

### Create the Directory

Create a directory named:

```text
debugger-lab
```

### Create the Playbook

Inside `debugger-lab`, create a file named `debugger_escape.yml`:

```yaml
---
- name: Debugger escape room
  hosts: all
  debugger: on_failed

  vars:
    package_name: curl

  tasks:
    - name: Install package
      ansible.builtin.package:
        name: "{{ pakage_name }}"
        state: present
```

Notice that the playbook contains a mistake:

```text
pakage_name
```

The correct variable is:

```text
package_name
```

Do not fix it yet.

## Run the Broken Playbook

From the controller terminal, run:

```bash
ansible-playbook -i inventory.ini debugger-lab/debugger_escape.yml
```

The task should fail because `pakage_name` is undefined.

The debugger prompt should appear and look similar to this:

```text
[host1] TASK: Install package (debug)>
```

## Inspect the Failure

At the debugger prompt, run:

```text
p result._result
```

This prints the task result and should show that the variable is undefined.

Now inspect the task arguments:

```text
p task.args
```

You should see something similar to:

```text
{'name': '{{ pakage_name }}', 'state': 'present'}
```

Inspect available task variables:

```text
p task_vars['package_name']
```

Expected output:

```text
'curl'
```

## Temporarily Fix the Task Argument

At the debugger prompt, update the module argument:

```text
task.args['name'] = '{{ package_name }}'
```

Check the updated arguments:

```text
p task.args
```

Expected output:

```text
{'name': '{{ package_name }}', 'state': 'present'}
```

Now rerun the task:

```text
redo
```

The task should now complete successfully.

Continue the playbook:

```text
continue
```

## Fix the Playbook Permanently

Now update `debugger_escape.yml` so it uses the correct variable:

```yaml
---
- name: Debugger escape room
  hosts: all
  debugger: on_failed

  vars:
    package_name: curl

  tasks:
    - name: Install package
      ansible.builtin.package:
        name: "{{ package_name }}"
        state: present
```

Save the file.

## Run the Fixed Playbook

Run:

```bash
ansible-playbook -i inventory.ini debugger-lab/debugger_escape.yml
```

This time the playbook should run without entering the debugger.

## Commit and Push Changes to GitHub

1. Save the corrected playbook
2. Open the **Source Control** pane
3. Review the changes
4. Commit with the message:

```text
Add debugger escape room lab
```

5. Push the changes to GitHub

## Optional Challenge: Fix the Variable Instead of the Argument

Create a second broken playbook named `debugger_bad_value.yml`:

```yaml
---
- name: Debugger bad value challenge
  hosts: all
  debugger: on_failed

  vars:
    package_name: package_that_does_not_exist

  tasks:
    - name: Install package
      ansible.builtin.package:
        name: "{{ package_name }}"
        state: present
```

Run it:

```bash
ansible-playbook -i inventory.ini debugger-lab/debugger_bad_value.yml
```

At the debugger prompt, inspect the variable:

```text
p task_vars['package_name']
```

Update the variable:

```text
task_vars['package_name'] = 'curl'
```

Recreate the task with the updated variable:

```text
update_task
```

Rerun the task:

```text
redo
```

## Understanding the Debugger

This lab demonstrates:

* `debugger: on_failed` starts the debugger only when a task fails
* `p result._result` prints the task failure details
* `p task.args` shows module arguments
* `p task_vars` shows variables available to the task
* `task.args['key'] = value` changes a module argument temporarily
* `task_vars['key'] = value` changes a variable temporarily
* `update_task` is required after changing task variables
* `redo` reruns the failed task

## Conclusion

Congratulations! You have successfully:

* Triggered the Ansible task debugger
* Inspected a task failure
* Found an undefined variable problem
* Temporarily fixed a task in the debugger
* Reran the failed task without restarting the whole playbook
* Fixed the playbook permanently

This lab demonstrates how the Ansible debugger can shorten the troubleshooting cycle when developing playbooks.

---

# Ansible Vault Courier - Secure Variables Lab

## Scenario

Your application needs a database configuration file on a managed host. The file must contain a database username and password, but those secrets must not be stored as plain text in your Git repository.

You will use Ansible Vault to encrypt the secrets file, deploy a configuration file from a Jinja2 template, and run the playbook through Automation Platform using a Vault credential.

## Prerequisites

This lab assumes you have:

* The `ansible-working-[your initials]` project already created in Automation Platform
* The `First Inventory-[your initials]` configured with your managed nodes
* Linux credentials configured in Automation Platform
* VS Code with access to your `ansible-working` repository
* Terminal access on the Ansible controller
* Permission to create credentials in Automation Platform

## Create the Vault Lab Files

In VS Code, open your `ansible-working` repository.

### Create the Directory

Create a directory named:

```text
vault-courier-lab
```

### Create the Plain Text Secrets File

Inside `vault-courier-lab`, create a file named `secrets.yml`:

```yaml
---
db_user: training_app
db_password: SuperSecret123
db_host: database.internal
db_port: 5432
```

### Create the Template

Inside `vault-courier-lab`, create a file named `db.conf.j2`:

```jinja2
# Database configuration
# Managed by Ansible

db_user={{ db_user }}
db_password={{ db_password }}
db_host={{ db_host }}
db_port={{ db_port }}
```

### Create the Playbook

Inside `vault-courier-lab`, create a playbook named `vault_courier.yml`:

```yaml
---
- name: Deploy database configuration from encrypted variables
  hosts: all

  vars_files:
    - secrets.yml

  tasks:
    - name: Create application config directory
      ansible.builtin.file:
        path: /tmp/vault-courier
        state: directory
        mode: '0700'

    - name: Deploy database configuration
      ansible.builtin.template:
        src: db.conf.j2
        dest: /tmp/vault-courier/db.conf
        mode: '0600'
      no_log: true

    - name: Display safe success message
      ansible.builtin.debug:
        msg: "Database configuration deployed securely on {{ inventory_hostname }}"
```

## Encrypt the Secrets File

From the controller terminal, run:

```bash
cd ansible-working-[your initials]/vault-courier-lab
ansible-vault encrypt secrets.yml
```

Enter a vault password when prompted.

Use a password you can remember for the lab, for example:

```text
VaultPass123
```

Do not use real production passwords in training labs.

## Confirm the File Is Encrypted

Run:

```bash
cat secrets.yml
```

You should see content similar to:

```text
$ANSIBLE_VAULT;1.1;AES256
663864383...
```

You should no longer see the plain text values.

## Test Locally from the Controller

Run the playbook locally from the controller:

```bash
ansible-playbook -i inventory.ini vault-courier-lab/vault_courier.yml --ask-vault-pass
```

Enter the same vault password used to encrypt `secrets.yml`.

The playbook should complete successfully.

## Commit and Push Changes to GitHub

1. Save your changes
2. Confirm that `secrets.yml` is encrypted before committing
3. Open the **Source Control** pane in VS Code
4. Review the changes
5. Commit with the message:

```text
Add vault courier lab
```

6. Push the changes to GitHub

## Create a Vault Credential in Automation Platform

1. Navigate to **Automation Execution** → **Infrastructure** → **Credentials**

2. Click **Create credential**

3. Fill in the following details:

   * **Name**: `Vault credential-[your initials]`
   * **Description**: `Vault password for encrypted lab variables`
   * **Organization**: select your organization
   * **Credential Type**: `Vault`

4. In the **Vault Password** field, enter the same password used to encrypt `secrets.yml`

5. Click **Create credential**

## Create Job Template

In Automation Platform, create a new job template:

1. Navigate to **Automation Execution** → **Templates**

2. Click **Create template**

3. Select **Create job template**

4. Fill in the following details:

   * **Name**: `vault_courier-[your initials]`
   * **Description**: `Deploy database configuration using Ansible Vault`
   * **Job Type**: `Run`
   * **Inventory**: `First Inventory-[your initials]`
   * **Project**: `ansible-working-[your initials]`
   * **Execution Environment**: `Default execution environment`
   * **Playbook**: `vault-courier-lab/vault_courier.yml`

5. In **Credentials**, add both:

   * `Linux credentials-[your initials]`
   * `Vault credential-[your initials]`

6. Click **Create job template**

## Run the Job Template

1. Click **Launch template**
2. Monitor the job output
3. Confirm that the configuration deployment task completes successfully

Because the template task uses `no_log: true`, sensitive output should be hidden.

## Verify the Deployment

Use an ad-hoc command in Automation Platform.

**Step 1 – Details**

* **Module**: `shell`
* **Arguments**:

```bash
ls -l /tmp/vault-courier/db.conf && cat /tmp/vault-courier/db.conf
```

**Step 2 – Execution Environment**

* **Execution Environment**: Default execution environment

**Step 3 – Credential**

* **Credential**: `Linux credentials-[your initials]`

**Step 4 – Review**

* Click **Finish**

Expected output:

```text
-rw------- ... /tmp/vault-courier/db.conf

# Database configuration
# Managed by Ansible

db_user=training_app
db_password=SuperSecret123
db_host=database.internal
db_port=5432
```

## Important Security Discussion

The deployed file contains the secret in plain text because the application needs to read it.

This means:

* Vault protects secrets in Git
* Vault protects secrets during Ansible execution
* `no_log: true` helps prevent secrets from appearing in job output
* File permissions on the managed host are still important
* A user with access to the managed host may still be able to read the deployed secret if permissions are too broad

## Test Failure Without Vault Credential

Optional test:

1. Remove the Vault credential from the job template
2. Launch the job again
3. Observe that Ansible cannot decrypt `secrets.yml`
4. Add the Vault credential back

## Understanding Ansible Vault

This lab demonstrates:

* `ansible-vault encrypt` encrypts sensitive files
* Encrypted files can be stored in Git more safely than plain text secrets
* `vars_files` can load encrypted variable files
* `--ask-vault-pass` provides the password locally
* Automation Platform uses a Vault credential to decrypt encrypted files during job execution
* `no_log: true` helps protect sensitive task output

## Conclusion

Congratulations! You have successfully:

* Created a secrets file
* Encrypted it with Ansible Vault
* Used encrypted variables in a playbook
* Created a Vault credential in Automation Platform
* Ran a job template that decrypts secrets at runtime
* Deployed a configuration file securely
* Verified the result on managed hosts

This lab demonstrates how Ansible Vault helps protect sensitive data while still allowing automation to use that data when needed.

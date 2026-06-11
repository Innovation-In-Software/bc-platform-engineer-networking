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

1. Push the changes to GitHub

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
## Bonus challenge

Create a survey where user can provide service port number to the template.

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
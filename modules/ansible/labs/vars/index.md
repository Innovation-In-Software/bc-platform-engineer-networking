
---

# Exploring Module Documentation with `ansible-navigator`

## Objective

Use `ansible-navigator` to inspect module documentation, compare module capabilities, and identify commonly used module parameters.

## Steps

1. Open a terminal session.

1. Install ansible-navigator, if not already installed:
```
pip3 install ansible-navigator ansible-core --user
```

2. Display all available modules:

```bash
ansible-navigator doc -l -m stdout
```

3. Search the output for the following modules:

- `file`
- `copy`
- `template`
- `service`
- `user`

4. Display documentation for the `file` module:

```bash
ansible-navigator doc ansible.builtin.file -m stdout
```

5. Identify the purpose of the following parameters:

- `path`
- `state`
- `mode`
- `owner`
- `group`

6. Display documentation for the `copy` module:

```bash
ansible-navigator doc ansible.builtin.copy -m stdout
```

7. Compare the `copy` and `template` modules by reviewing their documentation.

8. Display the documentation for the `service` module:

```bash
ansible-navigator doc ansible.builtin.service -m stdout
```

9. Identify which module parameters would:

- Start a service
- Restart a service
- Enable a service at boot

## Validation

Verify that:

- Documentation output displays successfully
- Examples and parameter descriptions are visible
- You can identify functional differences between modules

---

# Working with Lists, Dictionaries, and Nested Variables

## Objective

Define and access structured variables using lists and dictionaries inside a playbook.

## Steps

1. Create a working directory:

```bash
mkdir lab-vars
cd lab-vars
```

2. Create a playbook named `complex_vars.yml`.

3. Add the following content:

```yaml
---
- name: Manage Structured Variables
  hosts: localhost
  gather_facts: false

  vars:
    target_packages:
      - curl
      - git
      - tmux

    deployment_regions:
      - london
      - newyork
      - singapore

    user_identities:
      lead:
        username: "engineer_alpha"
        uid: 2001
        shell: "/bin/bash"

      support:
        username: "engineer_beta"
        uid: 2002
        shell: "/bin/sh"

  tasks:
    - name: Display first package
      ansible.builtin.debug:
        msg: "Primary package: {{ target_packages[0] }}"

    - name: Display second region
      ansible.builtin.debug:
        msg: "Secondary region: {{ deployment_regions[1] }}"

    - name: Display lead engineer details
      ansible.builtin.debug:
        msg: "{{ user_identities['lead']['username'] }} uses shell {{ user_identities['lead']['shell'] }}"

    - name: Display support engineer UID
      ansible.builtin.debug:
        msg: "Support UID is {{ user_identities['support']['uid'] }}"

    - name: Loop through package list
      ansible.builtin.debug:
        msg: "Installing package {{ item }}"
      loop: "{{ target_packages }}"
```

4. Run the playbook:

```bash
ansible-playbook complex_vars.yml 
```

5. Add another region and package to the variables section.

6. Add another debug task that displays all deployment regions.

## Validation

Verify that:

- List indexing works correctly
- Dictionary values display properly
- Loop output processes all packages

---

# Variable Precedence and Runtime Overrides

## Objective

Use external variable files and runtime overrides to control playbook behavior.

## Steps

1. Create a file named `environment_settings.yml`:

```yaml
---
deployment_tier: "development"
service_port: 8080
application_name: "inventory-api"
log_level: "info"
```

2. Create a playbook named `precedence_flow.yml`:

```yaml
---
- name: Demonstrate Variable Precedence
  hosts: localhost
  gather_facts: false

  vars_files:
    - environment_settings.yml

  tasks:
    - name: Display deployment settings
      ansible.builtin.debug:
        msg: "Deploying {{ application_name }} to {{ deployment_tier }} on port {{ service_port }}"

    - name: Display logging configuration
      ansible.builtin.debug:
        msg: "Current log level is {{ log_level }}"
```

3. Run the playbook normally:

```bash
ansible-playbook precedence_flow.yml 
```

4. Override the deployment tier:

```bash
ansible-playbook precedence_flow.yml -e "deployment_tier=production"
```

5. Override multiple variables:

```bash
ansible-playbook precedence_flow.yml -e "deployment_tier=staging service_port=9090 log_level=debug"
```

6. Modify the variable file and re-run the playbook.

## Validation

Verify that:

- Variables load from external files
- Runtime overrides take precedence
- Multiple variable overrides work correctly

---

# Gathering Facts and Registering Task Output

## Objective

Use Ansible facts and registered variables to collect and display system information.

## Steps

1. Create a playbook named `state_tracking.yml`.

2. Add the following content:

```yaml
---
- name: Evaluate Host Information
  hosts: localhost
  gather_facts: true

  tasks:
    - name: Display operating system
      ansible.builtin.debug:
        msg: "Operating system: {{ ansible_facts['distribution'] }}"

    - name: Display architecture
      ansible.builtin.debug:
        msg: "Architecture: {{ ansible_facts['architecture'] }}"

    - name: Display total memory
      ansible.builtin.debug:
        msg: "Memory detected: {{ ansible_facts['memtotal_mb'] }} MB"

    - name: Capture current uptime
      ansible.builtin.command: uptime
      register: uptime_output

    - name: Display uptime output
      ansible.builtin.debug:
        var: uptime_output.stdout

    - name: Display command return code
      ansible.builtin.debug:
        msg: "Return code was {{ uptime_output.rc }}"
```

3. Run the playbook:

```bash
ansible-playbook state_tracking.yml 
```

4. Review the structure of the registered variable in the output.

5. Add another task that captures disk usage using:

```bash
df -h
```

## Validation

Verify that:

- Facts are gathered successfully
- Registered variables contain command output
- Return codes and stdout values are accessible

---

# Loops, Conditions, and File Management

## Objective

Use loops and conditional statements to manage multiple files dynamically.

## Steps

1. Create a playbook named `conditional_loops.yml`.

2. Add the following content:

```yaml
---
- name: Manage Conditional File Operations
  hosts: localhost
  gather_facts: false

  vars:
    system_role: "database"

    required_files:
      - "db_schema.sql"
      - "db_indices.sql"
      - "db_backup.sh"

  tasks:
    - name: Display current role
      ansible.builtin.debug:
        msg: "Current role is {{ system_role }}"

    - name: Create database files
      ansible.builtin.file:
        path: "/tmp/{{ item }}"
        state: touch
        mode: '0644'
      loop: "{{ required_files }}"
      when: system_role == "database"

    - name: Verify files were processed
      ansible.builtin.debug:
        msg: "Processed file {{ item }}"
      loop: "{{ required_files }}"
```

3. Run the playbook:

```bash
ansible-playbook conditional_loops.yml 
```

4. Change the `system_role` variable to `webserver`.

5. Re-run the playbook and observe skipped tasks.

6. Add another file to the loop list and execute the playbook again.

## Validation

Verify that:

- Loop processing works correctly
- Conditional execution skips tasks when conditions fail
- Files are created under `/tmp`

---

# Event-Driven Automation with Handlers

## Objective

Use handlers and notifications to trigger actions only when task changes occur.

## Steps

1. Create a playbook named `event_handlers.yml`.

2. Add the following content:

```yaml
---
- name: Configure Application Services
  hosts: localhost
  gather_facts: false

  tasks:
    - name: Deploy application configuration
      ansible.builtin.copy:
        content: |
          application_port=9000
          environment=development
        dest: /tmp/app_network.conf
      notify: "restart application stack"

    - name: Deploy logging configuration
      ansible.builtin.copy:
        content: "log_level=info"
        dest: /tmp/app_logging.conf
      notify: "restart application stack"

  handlers:
    - name: Clear cache
      ansible.builtin.debug:
        msg: "Clearing application cache"
      listen: "restart application stack"

    - name: Restart worker processes
      ansible.builtin.debug:
        msg: "Restarting worker services"
      listen: "restart application stack"
```

3. Run the playbook:

```bash
ansible-playbook event_handlers.yml 
```

4. Run the playbook a second time without modifying the files.

5. Change the logging configuration content and re-run the playbook.

## Validation

Verify that:

- Handlers trigger only when changes occur
- Multiple tasks can notify the same handler topic
- Handlers do not execute when tasks report `ok`


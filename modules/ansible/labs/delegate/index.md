# Delegating Tasks and Local Actions

## Objective

Use delegation techniques to execute tasks on the control node.

## Steps

1. Create a playbook named `delegate_tasks.yml`.

2. Add the following content:

```yaml
---
- name: Execute Delegated Operations
  hosts: localhost
  gather_facts: false

  tasks:
    - name: Execute delegated command
      ansible.builtin.command: hostname
      delegate_to: 127.0.0.1
      register: delegated_hostname

    - name: Display delegated hostname
      ansible.builtin.debug:
        var: delegated_hostname.stdout

    - name: Execute local action
      local_action:
        module: ansible.builtin.debug
        msg: "Running local administrative task"

    - name: Create local status file
      ansible.builtin.copy:
        content: "delegation completed"
        dest: /tmp/delegation_status.txt
      delegate_to: localhost
```

3. Run the playbook:

```bash
ansible-playbook delegate_tasks.yml 
```

4. Replace `127.0.0.1` with `localhost` and test again.

5. Review the task output carefully to identify delegated tasks.

## Validation

Verify that:

- Delegated tasks execute successfully
- Registered output captures delegated command results
- Local actions run on the control node

---

# Managing Asynchronous Tasks

## Objective

Execute long-running tasks asynchronously and monitor their completion status.

## Steps

1. Create a playbook named `async_polling.yml`.

2. Add the following content:

```yaml
---
- name: Manage Asynchronous Operations
  hosts: localhost
  gather_facts: false

  tasks:
    - name: Start background task
      ansible.builtin.command: sleep 10
      async: 30
      poll: 0
      register: background_job

    - name: Display async job ID
      ansible.builtin.debug:
        msg: "Job ID is {{ background_job.ansible_job_id }}"

    - name: Run intermediate processing task
      ansible.builtin.debug:
        msg: "Executing additional work while background task runs"

    - name: Monitor async job status
      ansible.builtin.async_status:
        jid: "{{ background_job.ansible_job_id }}"
      register: job_result
      until: job_result.finished
      retries: 10
      delay: 2

    - name: Display final job status
      ansible.builtin.debug:
        var: job_result.finished
```

3. Run the playbook:

```bash
ansible-playbook async_polling.yml 
```

4. Increase the sleep timer and adjust retry values.

5. Observe how polling intervals affect execution timing.

## Validation

Verify that:

- Background tasks start successfully
- Intermediate tasks execute immediately
- Polling continues until completion

---

# Check Mode, Diff Mode, and Safe Execution

## Objective

Use dry-run execution techniques to validate changes before applying them.

## Steps

1. Create a playbook named `rolling_audit.yml`.

2. Add the following content:

```yaml
---
- name: Perform Safe Configuration Audit
  hosts: localhost
  gather_facts: false

  tasks:
    - name: Deploy audit configuration
      ansible.builtin.copy:
        content: |
          audit_checkpoint=beta
          validation_state=enabled
        dest: /tmp/audit_log.txt
```

3. Run the playbook in check and diff mode:

```bash
ansible-playbook rolling_audit.yml --check --diff
```

4. Review the diff output carefully.

5. Execute the playbook normally.

6. Re-run the playbook with `--check`.

7. Compare the output from all executions.

## Validation

Verify that:

- Diff output displays pending changes
- Check mode prevents modifications
- Normal execution creates the file successfully

---

# Troubleshooting with the Ansible Debugger

## Objective

Use the Ansible debugger to inspect task failures and correct values during runtime.

## Steps

1. Create a playbook named `runtime_debugging.yml`.

2. Add the following content:

```yaml
---
- name: Debug Runtime Failures
  hosts: localhost
  gather_facts: false

  vars:
    approved_path: "/tmp/working_directory"

  tasks:
    - name: Create managed directory
      ansible.builtin.file:
        path: "{{ undefined_variable_name_error }}"
        state: directory
      debugger: on_failed
```

3. Run the playbook:

```bash
ansible-playbook runtime_debugging.yml 
```

4. At the debugger prompt, inspect task arguments:

```text
p task.args
```

5. Update the incorrect value:

```text
task.args['path'] = '{{ approved_path }}'
```

6. Re-run the failed task:

```text
redo
```

7. Exit the debugger and verify the directory exists:

```bash
ls -ld /tmp/working_directory
```

## Validation

Verify that:

- The debugger launches after task failure
- Task arguments can be inspected interactively
- The task succeeds after correcting the value
- The target directory is created successfully

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
ansible-playbook vault_courier.yml -i /home/ansible/inventory/inventory.yaml --ask-vault-pass
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

1. Push the changes to GitHub

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
# AAP - Surveys

Demonstrate the use of Ansible Automation controller [survey feature](https://docs.ansible.com/automation-controller/latest/html/userguide/job_templates.html#surveys). Surveys set extra variables for the playbook similar to 'Prompt for Extra Variables' does, but in a user-friendly question and answer way. Surveys also allow for validation of user input.



## Install Apache

For this lab, we will use a playbook stored in this Git repository

[https://github.com/jruels/workshop-examples](https://github.com/jruels/workshop-examples)

A playbook to ensure Apache is installed and started. The playbook is `apache_install.yml`

```yaml
---
- name: Apache server installed
  hosts: all

  tasks:
  - name: latest Apache version installed
    yum:
      name: httpd
      state: latest

  - name: Apache enabled and running
    service:
      name: httpd
      enabled: true
      state: reloaded
```


Go to **Automation Execution → Projects**, and confirm the **Ansible Workshop Examples-[your initials]** project has the latest revision of our GitHub repository by clicking the **Sync project** icon.

After starting the sync job, go to **Automation Execution → Jobs**: there is a new job for the update of the Git repository.


## Create a new Job Template

Go to **Automation Execution → Templates**, click the **Create template** button and choose **Create job template**.

Create a new Job Template for installing Apache.

Fill in the following: 

* **Name**: Install Apache-[your initials]

* **Job Type**: Run

* **Inventory**: First Inventory-[your initials]

* **Project**: Ansible Workshop Examples-[your initials]

* **Execution Environment**: Default execution environment

* **Playbook**: `rhel/apache/apache_install.yml`

* **Credentials**: Linux credentials-[your initials]

* **Options**: The tasks need to run as `root` so check **Privilege escalation**

* Click **Create job template**



You can start the job by directly clicking the blue **Launch template** button, or by clicking on the rocket icon in the Templates list view. After launching the Job Template, you are automatically brought to the job overview where you can follow the playbook execution in real-time.



If everything is configured successfully, you should see that Apache was installed. 



## Challenge Lab: Check the Result

Time for a little challenge:

- Use an ad-hoc command on your managed hosts to make sure Apache has been installed and is running.

You have already been through all the steps needed, so try this for yourself.



### Solution

<details>
  <summary>Click here to expand</summary>

Go to **Automation Execution → Infrastructure → Inventories → First Inventory-[your initials]**



In the Hosts view select both nodes and click Run Command



Within the Details window, select the command module, in Arguments type systemctl status httpd and click Next.



Within the Execution Environment window, select Default execution environment and click Next.



Within the Machine Credential window, select Linux credentials-[your initials] and click Launch.

</details>



## Extend template with a Survey

You have installed Apache on your nodes in the job you just ran. Now we're going to extend this:

- Use a proper role that has a Jinja2 template to deploy an `index.html` file.
- Create a job **Template-[your initials]** with a survey to collect the values for the `index.html` template.
- Launch the job **Template-[your initials]**

Additionally, the role will make sure that the Apache configuration is properly set up for this exercise.



### The Apache-configuration Role

The playbook and the role with the Jinja2 template already exist in the Github repository we added previously.



Review the playbook file below, `apache_role_install.yml`: 

```yaml
---
- name: Ensure Apache installation
  hosts: web

  roles:
    - role_apache
```



This playbook calls the `apache` role which can be found in the [roles directory](https://github.com/jruels/workshop-examples/tree/master/rhel/apache/roles/role_apache)

  

- Inside the role, note the two variables in the `templates/index.html.j2` template file marked by ``.
- Notice the tasks in `tasks/main.yml` that deploy the file from the template.



What is this playbook doing? It creates a file (**dest**) on the managed hosts from the template (**src**).

The role deploys a static configuration for Apache. This is to make sure that all changes done in the previous chapters are overwritten and your examples work properly.

Because the playbook and role is located in the same GitHub repo as the `apache_install.yml` playbook you don't have to configure a new project for this exercise.



### Create a Template with a Survey 

Now you create a new Template that includes a survey.

#### Create Template

Go to **Automation Execution → Templates**, click the **Create template** button and choose **Create job template**

Fill out the following information:

* **Name**: Create index.html-[your initials]
* **Job Type**: Run
* **Inventory**: First Inventory-[your initials]
* **Project**: Ansible Workshop Examples-[your initials]
* **Execution Environment**: Default execution environment
* **Playbook**: rhel/apache/apache_role_install.yml
* **Credentials**: Linux credentials-[your initials]
* **Limit**: web
* **Options**: Privilege escalation



* Click **Create job template**

> **Warning**: Do not run the template yet!



#### Add the Survey 

In the Template, click the **Survey** tab at the top, and click the **Create survey question** button. 

Fill out the form: 

* **Question**: First Line

* **Answer variable name**: first_line

* **Answer type**: Text



* Click **Create survey question**
* Click the **Create survey question** button again



In the same fashion add a second survey question:

* **Question**: Second Line

* **Answer variable name**: second_line

* **Answer type**: Text



* Click **Create survey question**
* Click the **Survey enabled** toggle to enable the survey



### Launch the Template

Now launch **Create index.html-[your initials]** job template by clicking the **Launch template** button.

Before the actual launch, the survey will ask for **First Line** and **Second Line**. Fill in some text and click **Next**. The **Preview** window shows the values.


 If all is good run the Job by clicking **Launch**.

After the job has completed, check the Apache homepage. SSH into your nodes, execute `curl` against `localhost`:

```bash
$ curl http://localhost
<body>
<h1>Apache is running fine</h1>
<h1>This is survey field "First Line": line one</h1>
<h1>This is survey field "Second Line": line two</h1>
</body>
```

Note how the two variables were used by the playbook to create the content of the `index.html` file.



## Congrats! 



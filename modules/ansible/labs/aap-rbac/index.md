# AAP - Role-based access control

You have already learned how Ansible automation controller separates credentials from users. Another advantage of Ansible automation controller is the user and group rights management. This exercise demonstrates Role-Based Access Control (RBAC)



## Ansible Automation Controller Users

There are three types of automation controller users:

- **Normal user**: Have read and write access limited to the inventory and projects for which that user has been granted the appropriate roles and privileges.
- **Ansible Automation Platform Auditor**: Has read-only access to all resources within the environment.
- **Ansible Automation Platform Administrator**: Has full system administration privileges, including comprehensive read and write access across the entire installation.



Let's create a user:

In the automation controller menu under **Access Management** click **Users**

Click the **Create user** button

Fill in the values for the new user:

- **Username**: wweb-[your initials]
- **Password**: ansible
- **Confirm password**: ansible
- **First name**: Werner-[your initials]
- **Last name**: Web-[your initials]
- **Email**: wweb-[your initials]@example.com
- **User type**: Normal user
- **Organizations**: Default



* Click **Create user**



## Ansible Automation Controller Teams

A Team is a subdivision of an organization with associated users, projects, credentials, and permissions. Teams provide a means to implement role-based access control schemes and delegate responsibilities across organizations. For instance, permissions may be granted to a whole Team rather than each user on the Team.

Create a Team:

In the menu go to **Access Management → Teams**

Click the **Create team** button and create a team named `Web Content-[your initials]` within the `Default` Organization.

- Click **Create team**

Add a user to the team:

- Click on the team `Web Content-[your initials]` and click the **Users** tab.
- Click **Assign users**.
- Select the checkbox next to the `wweb-[your initials]` user.
- Click **Assign users**.

Permissions allow users to read, modify, and administer projects, inventories, and other automation controller elements. Permissions can be set for different resources.



## Granting permissions

To allow users or teams to actually do something, you have to set permissions. The user **wweb-[your initials]** should only be allowed to modify content of the assigned webservers.

Add the permission to use the `Create index.html-[your initials]` template:

- Go to **Automation Execution → Templates** and select `Create index.html-[your initials]`.
- Click the **User Access** tab and click **Assign users**.
- **Step 1 - Select user(s)**: Select the checkbox next to `wweb-[your initials]` and click **Next**.
- **Step 2 - Select roles to apply**: Select **JobTemplate Execute** and click **Next**.
- **Step 3 - Review**: Confirm the user and role are correct, then click **Finish**.



## Test permissions

Now log out of Automation Controller's web UI and log back in as the **wweb-[your initials]** user.

- Go to **Automation Execution → Templates**. You should notice that for **wweb** only the `Create index.html-[your initials]` template is listed. The user is allowed to view and launch, but not to edit the Template (no Edit button available).
- Run the Job Template by clicking the rocket icon. Enter the values for the survey questions and launch the job.
- Go to **Automation Execution → Jobs** to watch the job run and review the output.

Check the result by running `curl` against the web server on `Server 1`:

```bash
#> curl http://<Server 1 IP>
```

You enabled a restricted user to run an Ansible playbook

- Without having access to the credentials
- Without being able to change the playbook itself
- But with the ability to change variables you predefined

Effectively you provided the power to execute automation to another user without handing out your credentials or giving the user the ability to change the automation code. And yet, at the same time the user can still modify things based on the surveys you created.

This capability is one of the main strengths of Ansible automation controller.



## Congrats! 





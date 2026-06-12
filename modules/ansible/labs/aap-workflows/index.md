# AAP - Workflows



## Objective

The basic idea of a workflow is to link multiple Job Templates together. They may or may not share inventory, playbooks, or even permissions. The links can be conditional:

- if job template A succeeds, job template B is automatically executed afterward
- but in case of failure, job template C will be run.

And the workflows are not even limited to Job Templates, but can also include project or inventory updates.

This enables new applications for Ansible automation controller: different Job Templates can build upon each other. E.g. the networking team creates playbooks with their own content, in their own Git repository, and even targeting their own inventory, while the operations team also has their own repos, playbooks, and inventory.

In this lab, you'll learn how to set up a workflow.

## Guide

### Lab scenario

You have two departments in your organization:

- The web operations team that is developing playbooks in their own Git branch named `webops`
- The web developers team that is developing playbooks in their own Git branch named `webdev`

When there is a new Node.js server to deploy, two things need to happen:

### Web operations team

- `httpd`, `firewalld`, and `node.js` need to be installed, `SELinux` settings configured, the firewall needs to be opened, and `httpd` and `node.js` should get started.

### Web developers team

- The most recent version of the web application needs to be deployed and `node.js` needs to be restarted.

In other words, the Web operations team prepares a server for application deployment, and the Web developers team deploys the application on the server.



To make things easier for you, everything needed already exists in a GitHub repository, including playbooks, JSP files, and more. You just need to glue it together.

> **Note**
>
> In this example, we utilize two separate branches of the same repository for the content of the distinct teams. In reality, the structure of your Source Control repositories depends on several factors and may vary.

### Set up projects

First, you need to set up the Git repository as a Project, just as you normally would.

Go to **Automation Execution → Projects**, click the **Create project** button to create a project for the web operations team. Fill out the form as follows:

| Parameter                        | Value                                             |
| -------------------------------- | ------------------------------------------------- |
| Name                             | Webops Git Repo-[your initials]                   |
| Organization                     | Default                                           |
| Execution environment            | Default execution environment                     |
| Source control type              | Git                                               |
| Source control URL               | `https://github.com/jruels/workshop-examples.git` |
| Source control branch/tag/commit | `webops`                                          |
| Options                          | ✓ Clean ✓ Delete ✓ Update revision on launch      |

Click **Create project**

------

Go to **Automation Execution → Projects**, click the **Create project** button to create a project for the web developers team. Fill out the form as follows:

| Parameter                        | Value                                             |
| -------------------------------- | ------------------------------------------------- |
| Name                             | Webdev Git Repo-[your initials]                   |
| Organization                     | Default                                           |
| Execution environment            | Default execution environment                     |
| Source control type              | Git                                               |
| Source control URL               | `https://github.com/jruels/workshop-examples.git` |
| Source control branch/tag/commit | `webdev`                                          |
| Options                          | ✓ Clean ✓ Delete ✓ Update revision on launch      |

Click **Create project**

### Set up job templates

Now you have to create two Job Templates like you would for "normal" Jobs.

Go to **Automation Execution → Templates**, click the **Create template** button and choose **Create job template**:

| Parameter             | Value                                |
| --------------------- | ------------------------------------ |
| Name                  | Web App Deploy-[your initials]       |
| Job type              | Run                                  |
| Inventory             | First Inventory-[your initials]      |
| Project               | Webops Git Repo-[your initials]      |
| Execution environment | Default execution environment        |
| Playbook              | `rhel/webops/web_infrastructure.yml` |
| Credentials           | Linux credentials-[your initials]    |
| Limit                 | web                                  |
| Options               | ✓ Privilege escalation               |

Click **Create job template**

------

Go to **Automation Execution → Templates**, click the **Create template** button and choose **Create job template**:

| Parameter             | Value                              |
| --------------------- | ---------------------------------- |
| Name                  | Node.js Deploy-[your initials]     |
| Job type              | Run                                |
| Inventory             | First Inventory-[your initials]    |
| Project               | Webdev Git Repo-[your initials]    |
| Execution environment | Default execution environment      |
| Playbook              | `rhel/webdev/install_node_app.yml` |
| Credentials           | Linux credentials-[your initials]  |
| Limit                 | web                                |
| Options               | ✓ Privilege escalation             |

Click **Create job template**

> **Tip**
>
> If you want to know what the Ansible Playbooks look like, check out the Github URL and switch to the appropriate branches.



### Set up the workflow

Workflows are configured in the **Templates** view, you might have noticed you can choose between **Create job template** and **Create workflow job template** when creating a template.

Go to **Automation Execution → Templates**, click the **Create template** button and choose **Create workflow job template**:

| **Parameter** | Value                                |
| ------------- | ------------------------------------ |
| Name          | Deploy Webapp Server-[your initials] |
| Organization  | Default                              |

Click **Create workflow job template**

After saving the template, click the **View workflow visualizer** button on the template details page to open the Workflow Visualizer.

The Workflow Visualizer opens on an empty canvas that reads **There are currently no nodes in this workflow**. The toolbar at the top contains **Save**, **Add step**, and **Launch workflow** buttons.

Click **Add step** to open the node configuration panel. (A **Start** node appears on the canvas once you add your first node.)

In the **Node details** step, fill in:

- **Node type**: Job Template
- **Job template**: Select **Web App Deploy-[your initials]**

Click **Next**, review the summary, then click **Finish**.

A new node appears in the canvas connected to the **Start** node with a **Run always** edge.

To add the second node, hover over the **Web App Deploy-[your initials]** node. Click the **⋮** (three-dot) icon that appears on the node, then click **Add step and link** from the menu.

In the **Node details** step, fill in:

- **Status**: Run on success
- **Node type**: Job Template
- **Job template**: Select **Node.js Deploy-[your initials]**

Click **Next**, review the summary, then click **Finish**.

Click **Save** in the toolbar at the top of the Workflow Visualizer to save the workflow.



### Launch workflow

From within the **Deploy Webapp Server-[your initials]** details page, click **Launch template** to launch the workflow.



Note how the workflow run is shown in **Automation Execution → Jobs**. In contrast to a normal job template job execution, there is no playbook output when the job completes, but the time to complete the job is displayed. If you want to look at the actual playbook run, click on the node you wish to see the details for. To return to the workflow output view, go to **Automation Execution → Jobs** and click the workflow job **Deploy Webapp Server-[your initials]**.

## Challenge Lab: Recovery workflow
Using what you learned in this lab, create a workflow with three jobs (JobA-[your initials], JobB-[your initials], JobC-[your initials]). If JobA is successful, JobB runs; if JobA fails, JobC runs.

To create the branching workflow:
1. Add JobA using **Add step**
2. Hover over JobA, click **⋮**, then **Add step and link** — set **Status** to **Run on success** and select JobB
3. Hover over JobA again, click **⋮**, then **Add step and link** — set **Status** to **Run on fail** and select JobC


## Congrats!

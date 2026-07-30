# Lab 10 – Build a VPC

**Course:** Network Automation Tools — Day 4  
**Prerequisite:** Access to the control node with Terraform installed and an IAM role (or credentials) allowing VPC management  
**Objective:** Write your first Terraform configuration and use it to build real AWS infrastructure. Create a VPC and a subnet, then run the core Terraform workflow — `init`, `plan`, `apply` — and confirm the result in the AWS console.

---

> **Remember:** The resources in this lab (VPC, subnet, gateway, route table, security group) are free of charge, but you will run `terraform destroy` at the end of Lab 12 to leave your account clean. Keep this working directory — Labs 11 and 12 build on it.

## Overview

Today you stop configuring devices and start building the network itself as code. In this lab you will:

1. Prepare a Terraform working directory on the control node
2. Write a provider block for AWS
3. Declare a VPC resource with a 10.0.1.0/24 CIDR
4. Declare a subnet that references the VPC
5. Run `terraform init`, `plan`, and `apply`
6. Verify the VPC and subnet in the AWS console

This rebuilds, as code, the same network you created by hand in Lab 1.

---

## Part 1 — Prepare the Working Directory

### Step 1. Confirm Terraform is installed

```bash
terraform version
```

**Expected output:**
```
Terraform v1.x.x
on linux_amd64
```

### Step 2. Confirm AWS access

The AWS provider needs permission to create resources. The cleanest method is an IAM role attached to the control node — then no keys live in your code. Confirm the control node can reach AWS:

```bash
aws sts get-caller-identity
```

You should see an account ID and the role ARN.

> **Note:** If you are not using an instance role, export credentials into your shell instead: `export AWS_ACCESS_KEY_ID=...` and `export AWS_SECRET_ACCESS_KEY=...`. Never put keys in a `.tf` file — those get committed to Git.

### Step 3. Create a fresh directory

```bash
mkdir ~/terraform-lab
cd ~/terraform-lab
```

---

## Part 2 — Write the Provider and VPC

### Step 4. Create main.tf

The `terraform` block pins the AWS provider; the `provider` block sets the region.

```bash
cat > main.tf << 'EOF'
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_vpc" "lab" {
  cidr_block           = "10.0.1.0/24"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "AutomationLab-VPC"
  }
}
EOF
```

### Step 5. Understand the configuration

| Block | What it does |
|-------|-------------|
| `terraform { required_providers }` | Declares and version-pins the AWS provider |
| `provider "aws"` | Configures the region for all AWS resources |
| `resource "aws_vpc" "lab"` | Declares a VPC; `lab` is the local name you reference |
| `cidr_block` | The VPC's address range, matching the Lab 1 network |
| `tags` | A human-readable Name for the console and billing |

> **Note:** Change `region` if your account uses a different one. All resources in this project are created there.

---

## Part 3 — Add a Subnet

### Step 6. Append the subnet resource

The subnet references `aws_vpc.lab.id`, which places it inside the VPC and tells Terraform to create the VPC first.

```bash
cat >> main.tf << 'EOF'

resource "aws_subnet" "lab" {
  vpc_id                  = aws_vpc.lab.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true

  tags = {
    Name = "AutomationLab-Subnet"
  }
}
EOF
```

> **Note:** The subnet CIDR equals the VPC CIDR here, exactly as in Lab 1 — the single subnet uses the whole range. `map_public_ip_on_launch` gives instances a public IP, as the Day 1 lab required.

---

## Part 4 — Init, Plan, Apply

### Step 7. Initialize the directory

```bash
terraform init
```

**Expected output (abridged):**
```
Initializing provider plugins...
- Installing hashicorp/aws v5.x.x...
Terraform has been successfully initialized!
```

### Step 8. Preview the plan

```bash
terraform plan
```

Look for the summary line. A `+` marks each resource to be created:

```
Plan: 2 to add, 0 to change, 0 to destroy.
```

### Step 9. Apply the configuration

```bash
terraform apply
```

Terraform re-shows the plan and asks for confirmation. Type `yes`:

```
Do you want to perform these actions?
  Enter a value: yes
...
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.
```

---

## Part 5 — Verify

### Step 10. Inspect Terraform's view

```bash
terraform state list
```

**Expected output:**
```
aws_subnet.lab
aws_vpc.lab
```

### Step 11. Confirm in the AWS console

Go to **VPC → Your VPCs** and **VPC → Subnets**. You should see `AutomationLab-VPC` and `AutomationLab-Subnet` with the `10.0.1.0/24` range — the same network from Lab 1, now built from five lines of code.

> **Note:** Leave everything running. Lab 11 adds routing and a security group to this same configuration.

---

## Verification Checklist

| Task | Expected Result | Pass/Fail |
|------|-----------------|-----------|
| `terraform version` works | Version string printed | |
| AWS access confirmed | `get-caller-identity` returns an ARN | |
| `terraform init` succeeds | Provider installed, directory initialized | |
| `terraform plan` | `2 to add, 0 to change, 0 to destroy` | |
| `terraform apply` | `2 added` | |
| Resources visible | VPC and subnet in the console | |

---

## Reflection Questions

1. What does the `terraform` block's `required_providers` section do?
2. Why does the subnet reference `aws_vpc.lab.id` instead of a hard-coded VPC ID?
3. What is the difference between `terraform plan` and `terraform apply`?
4. Why should AWS credentials never appear in a `.tf` file?

---

## Summary

| Concept | Key Point |
|---------|-----------|
| `provider "aws"` | Configures the region and connection to AWS |
| `resource` block | Declares one piece of infrastructure to create |
| Resource reference | `aws_vpc.lab.id` sets an implicit dependency and order |
| `terraform init` | Downloads providers, prepares the directory |
| `terraform plan` | Previews changes without applying them |
| `terraform apply` | Creates the resources after you confirm |
| `terraform state list` | Shows what Terraform is managing |

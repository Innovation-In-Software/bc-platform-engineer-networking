# Lab 12 – Variables and Outputs

**Course:** Network Automation Tools — Day 4  
**Prerequisite:** Lab 11 complete — `~/terraform-lab` holds the full lab network (VPC, subnet, gateway, routing, security group), applied  
**Objective:** Turn your working configuration into a reusable one. Replace hard-coded values with input variables, supply them from a `tfvars` file, expose key IDs as outputs, then cleanly destroy everything you built.

---

> **Remember:** This lab ends with `terraform destroy`, which removes every resource from Labs 10–12. Run it so nothing is left in your account.

## Overview

A configuration that only builds one fixed network is not reusable. In this lab you will:

1. Add input variables for the region, CIDR, and name prefix
2. Supply their values in a `terraform.tfvars` file
3. Refactor `main.tf` to use the variables
4. Add outputs for the VPC, subnet, and security group IDs
5. Re-apply and view the outputs
6. Destroy the entire environment

---

## Part 1 — Add Input Variables

### Step 1. Move to your working directory

```bash
cd ~/terraform-lab
```

### Step 2. Create variables.tf

Terraform loads every `.tf` file in the directory, so variables can live in their own file.

```bash
cat > variables.tf << 'EOF'
variable "region" {
  description = "AWS region for the lab"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for the lab VPC and subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "name_prefix" {
  description = "Prefix for all resource names"
  type        = string
  default     = "AutomationLab"
}
EOF
```

---

## Part 2 — Supply Values with tfvars

### Step 3. Create terraform.tfvars

`terraform.tfvars` is loaded automatically and is where the actual values live, keeping the main code generic.

```bash
cat > terraform.tfvars << 'EOF'
region      = "us-east-1"
vpc_cidr    = "10.0.1.0/24"
name_prefix = "AutomationLab"
EOF
```

> **Note:** Because the variables have defaults, this file is optional here — but it is the standard place to set environment-specific values, and never a place for secrets.

> **Match what you actually deployed.** These three values must equal what Labs 10–11 built. In particular, if you changed the **region** in Lab 10 to match your Lab 1 resources, set that **same** region here (and in `variables.tf`) — not `us-east-1`. Likewise `vpc_cidr` must be the CIDR you deployed (`10.0.1.0/24` in these labs) and `name_prefix` must be `AutomationLab`. If any of them differs from the live resources, Step 6 will show changes — or try to build a second copy in another region — instead of `No changes`.

---

## Part 3 — Refactor main.tf to Use Variables

### Step 4. Update the provider and VPC

Replace the hard-coded region and CIDR with variable references, and build names from `var.name_prefix`. Open `main.tf` in an editor and change the `provider`, `aws_vpc`, and `aws_subnet` blocks to match:

```hcl
provider "aws" {
  region = var.region
}

resource "aws_vpc" "lab" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.name_prefix}-VPC"
  }
}

resource "aws_subnet" "lab" {
  vpc_id                  = aws_vpc.lab.id
  cidr_block              = var.vpc_cidr
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.name_prefix}-Subnet"
  }
}
```

### Step 5. Update the remaining names

Three resources still have hard-coded names in `main.tf`: the internet gateway, the route table, and the security group. Open `main.tf` and update each one so its name is built from `var.name_prefix`. These edits are all inside the resource blocks you wrote in Lab 11 — you are changing the `Name` tag values (and, for the security group, its `name` argument too).

**Internet gateway** (`aws_internet_gateway "lab"`) — change its tag:

```hcl
  tags = {
    Name = "${var.name_prefix}-IGW"
  }
```

**Route table** (`aws_route_table "lab"`) — same idea, with `-RT`:

```hcl
  tags = {
    Name = "${var.name_prefix}-RT"
  }
```

**Security group** (`aws_security_group "lab"`) — this block has **two** name fields (see Lab 11 Step 5): the `name` argument at the top and the `Name` tag at the bottom. Update **both**:

```hcl
resource "aws_security_group" "lab" {
  name        = "${var.name_prefix}-SG"
  description = "Lab security group for automation course"
  vpc_id      = aws_vpc.lab.id

  # ... the ingress / egress blocks stay exactly as they are ...

  tags = {
    Name = "${var.name_prefix}-SG"
  }
}
```

The `${...}` syntax inserts the variable's value into the string, so `${var.name_prefix}-SG` resolves to `AutomationLab-SG` — the same name already deployed. That is why the next step reports no changes. (Leave every other line — the CIDRs, ports, and `vpc_id` references — untouched.)

### Step 6. Confirm nothing actually changes

```bash
terraform plan
```

Because the values are identical to what is already deployed, the plan should report no changes:

```
No changes. Your infrastructure matches the configuration.
```

> **Note:** This is the proof your refactor was safe — you improved the code's structure without altering the live network. If you see changes, a variable value does not match what was originally applied.

---

## Part 4 — Add Outputs

### Step 7. Create outputs.tf

Outputs expose values after apply so other tools — or you — can use them.

```bash
cat > outputs.tf << 'EOF'
output "vpc_id" {
  description = "The ID of the lab VPC"
  value       = aws_vpc.lab.id
}

output "subnet_id" {
  description = "The ID of the lab subnet"
  value       = aws_subnet.lab.id
}

output "security_group_id" {
  description = "The ID of the lab security group"
  value       = aws_security_group.lab.id
}
EOF
```

---

## Part 5 — Apply, View Outputs, and Destroy

### Step 8. Apply to register the outputs

```bash
terraform apply
```

The plan shows no resource changes, but after you confirm, the outputs are displayed:

```
Apply complete! Resources: 0 added, 0 changed, 0 destroyed.

Outputs:
subnet_id         = "subnet-0abc123..."
security_group_id = "sg-0def456..."
vpc_id            = "vpc-0ghi789..."
```

### Step 9. Re-display outputs any time

```bash
terraform output
terraform output vpc_id
```

These IDs are exactly what you would hand to Ansible or Python to configure devices in this network — the bridge from provisioning to configuration.

### Step 10. Destroy the environment

```bash
terraform destroy
```

Review the destroy plan — every resource marked with a `-` — then type `yes`:

```
Plan: 0 to add, 0 to change, 6 to destroy.
...
Destroy complete! Resources: 6 destroyed.
```

> **Note:** Terraform destroys resources in reverse dependency order — associations and rules first, the VPC last — with no manual sequencing. Confirm in the console that the VPC is gone.

---

## Verification Checklist

| Task | Expected Result | Pass/Fail |
|------|-----------------|-----------|
| `variables.tf` created | Region, CIDR, and prefix variables defined | |
| `terraform.tfvars` created | Values supplied for the variables | |
| `main.tf` refactored | Uses `var.*` and `${var.name_prefix}` | |
| Plan after refactor | `No changes` | |
| Outputs added | VPC, subnet, and SG IDs displayed | |
| `terraform destroy` | `6 destroyed`, VPC gone from console | |

---

## Reflection Questions

1. Why did `terraform plan` report no changes after you replaced literals with variables?
2. What is the difference between `variables.tf` and `terraform.tfvars`?
3. How would you use the `vpc_id` output in a later Ansible or Python step?
4. Why is `terraform destroy` such an advantage for lab and test environments?

---

## Summary

| Concept | Key Point |
|---------|-----------|
| `variable` block | Declares an input, with a type and optional default |
| `terraform.tfvars` | Supplies values, auto-loaded, never holds secrets |
| `var.name` / `${var.name}` | References and interpolates a variable |
| `output` block | Exposes values like IDs after apply |
| `terraform output` | Re-displays outputs without re-running |
| `terraform destroy` | Removes all resources in correct order |
| Refactor safely | Same values mean `No changes` — structure improved, network unchanged |

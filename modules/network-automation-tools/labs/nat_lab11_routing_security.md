# Lab 11 – Routing and Security

**Course:** Network Automation Tools — Day 4  
**Prerequisite:** Lab 10 complete — `~/terraform-lab` holds a working VPC and subnet, already applied  
**Objective:** Finish the lab network. Add an internet gateway, a route table with a default route, the route-table association, and a security group that opens SSH, RESTCONF, and NETCONF — the exact rules from Lab 1, now as code.

---

> **Remember:** These resources are free of charge, but you will run `terraform destroy` at the end of Lab 12 to leave your account clean. Keep working in the same directory.

## Overview

A VPC and subnet alone cannot reach the internet, and nothing controls access yet. In this lab you will:

1. Add an internet gateway attached to the VPC
2. Create a route table with a default route to the gateway
3. Associate the route table with the subnet
4. Create a security group with SSH, RESTCONF, and NETCONF rules
5. Apply the additions and verify the plan

By the end you will have rebuilt the entire Day 1 lab network from Terraform.

---

## Part 1 — Internet Gateway

### Step 1. Move to your working directory

```bash
cd ~/terraform-lab
```

### Step 2. Add the internet gateway

```bash
cat >> main.tf << 'EOF'

resource "aws_internet_gateway" "lab" {
  vpc_id = aws_vpc.lab.id

  tags = {
    Name = "AutomationLab-IGW"
  }
}
EOF
```

The gateway references the VPC by id, so Terraform attaches it automatically.

---

## Part 2 — Route Table and Default Route

### Step 3. Add a route table with a default route

The `route` block sends all outbound traffic (`0.0.0.0/0`) to the internet gateway.

```bash
cat >> main.tf << 'EOF'

resource "aws_route_table" "lab" {
  vpc_id = aws_vpc.lab.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.lab.id
  }

  tags = {
    Name = "AutomationLab-RT"
  }
}
EOF
```

---

## Part 3 — Associate the Route Table

### Step 4. Link the route table to the subnet

A route table has no effect until it is associated with a subnet. This is the step most people forget.

```bash
cat >> main.tf << 'EOF'

resource "aws_route_table_association" "lab" {
  subnet_id      = aws_subnet.lab.id
  route_table_id = aws_route_table.lab.id
}
EOF
```

> **Note:** Without this association the route exists but nothing uses it, and instances in the subnet silently fail to reach the internet.

---

## Part 4 — Security Group

### Step 5. Add the security group

Each `ingress` block is one inbound rule. These mirror the Lab 1 security group exactly: SSH from anywhere, and RESTCONF, NETCONF, and ICMP from within the lab subnet.

```bash
cat >> main.tf << 'EOF'

resource "aws_security_group" "lab" {
  name        = "AutomationLab-SG"
  description = "Lab security group for automation course"
  vpc_id      = aws_vpc.lab.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "RESTCONF"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.1.0/24"]
  }

  ingress {
    description = "NETCONF"
    from_port   = 830
    to_port     = 830
    protocol    = "tcp"
    cidr_blocks = ["10.0.1.0/24"]
  }

  ingress {
    description = "ICMP within lab"
    from_port   = -1
    to_port     = -1
    protocol    = "icmp"
    cidr_blocks = ["10.0.1.0/24"]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "AutomationLab-SG"
  }
}
EOF
```

### Step 6. Understand the rules

| Rule | Port | Source | Purpose |
|------|------|--------|---------|
| SSH | 22 | 0.0.0.0/0 | Remote CLI access |
| RESTCONF | 443 | 10.0.1.0/24 | REST API within the lab |
| NETCONF | 830 | 10.0.1.0/24 | NETCONF within the lab |
| ICMP | all | 10.0.1.0/24 | Ping within the lab |
| Egress | all | 0.0.0.0/0 | Outbound to the internet |

---

## Part 5 — Apply and Verify

### Step 7. Preview the additions

```bash
terraform plan
```

Only the new resources should appear:

```
Plan: 4 to add, 0 to change, 0 to destroy.
```

> **Note:** A `0 to change, 0 to destroy` line confirms your existing VPC and subnet are untouched — Terraform is only adding.

### Step 8. Apply

```bash
terraform apply
```

Type `yes`:

```
Apply complete! Resources: 4 added, 0 changed, 0 destroyed.
```

### Step 9. Verify

```bash
terraform state list
```

**Expected output:**
```
aws_internet_gateway.lab
aws_route_table.lab
aws_route_table_association.lab
aws_security_group.lab
aws_subnet.lab
aws_vpc.lab
```

In the console, confirm the internet gateway is attached, the route table has the `0.0.0.0/0` route, and the security group shows all four inbound rules.

> **Note:** Leave everything running. Lab 12 parameterizes this configuration and then tears it all down.

---

## Verification Checklist

| Task | Expected Result | Pass/Fail |
|------|-----------------|-----------|
| Internet gateway added | Attached to the VPC | |
| Route table created | Default route to the IGW | |
| Association created | Route table linked to the subnet | |
| Security group created | SSH, RESTCONF, NETCONF, ICMP rules | |
| `terraform apply` | `4 added, 0 changed, 0 destroyed` | |
| Full network present | 6 resources in `state list` | |

---

## Reflection Questions

1. Why must a route table be associated with a subnet to take effect?
2. Why is SSH open to `0.0.0.0/0` but RESTCONF and NETCONF only to `10.0.1.0/24`?
3. How did Terraform know to create the VPC before the gateway and route table?
4. Compared to clicking these steps in the console (Lab 1), what does the Terraform version give you?

---

## Summary

| Concept | Key Point |
|---------|-----------|
| `aws_internet_gateway` | Gives the VPC a path to the internet |
| `aws_route_table` + `route` | Directs traffic; default route points at the IGW |
| `aws_route_table_association` | Links a route table to a subnet — easy to forget |
| `aws_security_group` | Stateful firewall; `ingress` blocks are inbound rules |
| Implicit dependencies | Resource references set the correct creation order |
| Idempotent apply | Re-running changes nothing already in the desired state |

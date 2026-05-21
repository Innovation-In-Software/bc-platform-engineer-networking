# Lab 01 – Building a VPC Architecture in AWS


**Objective:**  
Translate a traditional two-switch LAN into a cloud-based Virtual Private Cloud (VPC) on AWS.  
You will design public and private subnets, configure routing, attach an Internet Gateway, and deploy EC2 instances to simulate a web and database tier.

---

## Topology

### Traditional LAN
[PC1] — [Switch1] — [Router] — [Switch2] — [PC2]


### AWS Equivalent
```
             ┌──────────────────────────┐
             │         VPC              │
             │  (10.0.0.0/16)          │
             │ ┌──────────────┐ ┌──────────────┐
Internet ⇄ IGW ⇄│ Public Subnet │ │ Private Subnet│
│ (10.0.1.0/24) │ │ (10.0.2.0/24) │
│ Web Server │ │ DB Server │
└──────────────────────────┘
```

---

## Step 1 – Create a VPC

1. Go to **VPC Dashboard** in the AWS Management Console.  
2. Click **Create VPC** → Select **VPC only**.  
3. Configure:
   - **Name tag:** `TrainingVPC`
   - **IPv4 CIDR block:** `10.0.0.0/16`
   - Leave IPv6 unchecked for now.
4. Click **Create VPC**.  

**Result:** Your logical private network is created. This is equivalent to your main LAN.

---

## Step 2 – Create Subnets (Public and Private)

You will create **two subnets**, each in a **different Availability Zone (AZ)** for redundancy.

| Subnet Name | CIDR Block | AZ Example | Type |
|--------------|-------------|-------------|------|
| PublicSubnetA | 10.0.1.0/24 | us-east-1a | Public |
| PrivateSubnetB | 10.0.2.0/24 | us-east-1b | Private |

### Steps
1. In the **VPC Dashboard**, go to **Subnets → Create Subnet**.  
2. Choose `TrainingVPC`.  
3. Add **PublicSubnetA**:
   - **Subnet name:** `PublicSubnetA`
   - **Availability Zone:** `us-east-1a` (or your region's first AZ)
   - **IPv4 CIDR block:** `10.0.1.0/24`
4. Add **PrivateSubnetB**:
   - **Subnet name:** `PrivateSubnetB` 
   - **Availability Zone:** `us-east-1b` (or your region's second AZ)
   - **IPv4 CIDR block:** `10.0.2.0/24`
5. Click **Create subnet**.

### Enable Auto-Assign Public IP (IMPORTANT)
6. **Select PublicSubnetA** → **Actions → Edit subnet settings**
7. **Check the box:** "Enable auto-assign public IPv4 address"
8. Click **Save**

> **Critical Step:** Without this setting, EC2 instances launched in the public subnet won't receive public IP addresses automatically.

**Result:** Your VPC now has two isolated network zones, with the public subnet configured to auto-assign public IPs.

---

## Step 3 – Create and Attach an Internet Gateway (IGW)

1. Go to **Internet Gateways** → **Create internet gateway**.  
   - **Name:** `TrainingIGW`
2. After creation, select it → click **Actions → Attach to VPC → TrainingVPC**.  

**Result:** The VPC now has an external gateway to reach the internet (like your router's uplink).

---

## Step 4 – Configure Route Tables

You will use two route tables: one for **public** and one for **private** subnets.

### Create Public Route Table
1. Go to **Route Tables → Create Route Table**.  
   - **Name:** `PublicRT`
   - **VPC:** `TrainingVPC`
2. Open the new route table → **Routes → Edit routes → Add route**.  
   - **Destination:** `0.0.0.0/0`  
   - **Target:** `TrainingIGW`
3. Save changes.  
4. Under **Subnet associations**, select **PublicSubnetA**.

### Create Private Route Table
1. Create another route table named `PrivateRT`.  
2. No IGW route for now (local only).  
3. Associate it with **PrivateSubnetB**.

**Result:**  
- Public subnet can access the internet.  
- Private subnet remains isolated.

---

## Step 5 – Launch EC2 Instances

| Instance | Subnet | AMI | Type | Key Pair | Security Group |
|-----------|---------|-----|-------|------------|----------------|
| WebServer | PublicSubnetA | Amazon Linux 2 | t2.micro | Existing or new | Allow SSH (22), HTTP (80) |
| DBServer | PrivateSubnetB | Amazon Linux 2 | t2.micro | Existing or new | Allow SSH (22) from WebServer only |

### Detailed Launch Steps

#### Launch WebServer (Public Subnet)
1. **Go to EC2 → Launch Instance**
2. **Name:** `WebServer`
3. **AMI:** Amazon Linux 2023 (or Amazon Linux 2)
4. **Instance type:** t2.micro
5. **Key pair:** Create new or select existing
6. **Network settings → Edit:**
   - **VPC:** `TrainingVPC`
   - **Subnet:** `PublicSubnetA`
   - **Auto-assign public IP:** **Enable**
7. **Security Group:** Create new
   - **Name:** `WebServerSG`
   - **Rules:**
     - SSH (22) from My IP
     - HTTP (80) from Anywhere (0.0.0.0/0)
8. **Launch instance**

#### Launch DBServer (Private Subnet)  
1. **Go to EC2 → Launch Instance**
2. **Name:** `DBServer`
3. **AMI:** Amazon Linux 2023 (or Amazon Linux 2)
4. **Instance type:** t2.micro
5. **Key pair:** Same as WebServer
5. **Network settings → Edit:**
   - **VPC:** `TrainingVPC`
   - **Subnet:** `PrivateSubnetB`
   - **Auto-assign public IP:** **Disable**
6. **Security Group:** Create new
   - **Name:** `DBServerSG`
   - **Rules:**
     - SSH (22) from WebServerSG (select security group)
8. **Launch instance**

### Verify IP Assignment
After launch, check **EC2 → Instances:**
- **WebServer:** Should show both **Private IP** (10.0.1.x) and **Public IP**
- **DBServer:** Should show only **Private IP** (10.0.2.x), no public IP

### If WebServer Still Has No Public IP

**The auto-assign setting only applies to NEW instances launched after enabling it.**

#### Option 1: Allocate and Associate Elastic IP (Recommended)
1. **Go to EC2 → Elastic IPs → Allocate Elastic IP address**
2. **Click "Allocate"** (keep default settings)
3. **Select the new Elastic IP → Actions → Associate Elastic IP address**
4. **Configure:**
   - **Resource type:** Instance
   - **Instance:** Select your WebServer
   - **Private IP address:** Select the instance's private IP
5. **Click "Associate"**

#### Option 2: Relaunch the Instance
1. **Terminate the existing WebServer instance**
2. **Launch a new instance** following the same steps
3. **The new instance will get a public IP automatically**

#### Option 3: Manual Assignment During Instance Modification
**Note:** You cannot directly assign a public IP to a running instance without using Elastic IPs.

### Verify After Fix
**Go to EC2 → Instances and confirm:**
- **WebServer:** Now shows **Public IPv4 address** field populated
- **Status:** Both instances show "Running" state

**Result:**  
- WebServer will be publicly accessible via its public IP
- DBServer will be isolated within the private subnet

---

## Step 6 – Test and Verify Connectivity

1. **Connect to WebServer** using its **Public IP** via SSH:  
```
ssh -i yourkey.pem ec2-user@<WebServer_Public_IP>
```
2. From the WebServer, check internal connectivity:
```
ping 10.0.2.10
```

**Expected Result:**  
Ping to the DBServer **succeeds** (private connectivity within the VPC).

3. Try `curl google.com` from the **DBServer** (if no NAT configured) → should **fail**.  
This confirms that the private subnet has **no internet access**.

---

## Verification Checklist

| Check | Expected Result |
|--------|------------------|
| VPC CIDR | 10.0.0.0/16 |
| IGW attached | Yes |
| Public Subnet route | 0.0.0.0/0 → IGW |
| Private Subnet route | Local only |
| WebServer public IP | Reachable |
| DBServer | Accessible only from WebServer |

---

## � Troubleshooting Common Issues

### Issue: EC2 Instance Has No Public IP Address

**Problem:** When launching EC2 instances in the public subnet, they don't receive a public IP.

**Solution:**
1. **Check subnet settings:**
   ```
   VPC Dashboard → Subnets → Select PublicSubnetA → Actions → Edit subnet settings
   ```
   - "Enable auto-assign public IPv4 address" should be **checked**

2. **Alternative - Manually assign during launch:**
   - During EC2 launch → **Network settings** → **Auto-assign public IP** → Select **Enable**

### Issue: Cannot SSH to WebServer

**Possible Causes & Solutions:**

1. **Security Group Issue:**
   - Go to **EC2 → Security Groups**
   - Ensure SSH (port 22) is allowed from your public IP
   - Rule: `SSH | TCP | 22 | My IP`

2. **Route Table Issue:**
   - **VPC → Route Tables → PublicRT**
   - Verify route: `0.0.0.0/0 → IGW`

3. **Internet Gateway Issue:**
   - **VPC → Internet Gateways**
   - Ensure `TrainingIGW` is **attached** to `TrainingVPC`

### Issue: Private Instance Cannot Reach Public Instance

**Solution:**
- Check **Security Groups** on both instances
- Private instance SG should allow outbound traffic
- Public instance SG should allow inbound from private subnet CIDR (10.0.2.0/24)

### Verification Commands for Troubleshooting

**Check subnet configuration:**
```bash
# In AWS CLI (optional)
aws ec2 describe-subnets --subnet-ids subnet-xxxxx
```

**Test connectivity from EC2:**
```bash
# Test internet connectivity
curl -I http://google.com

# Test internal connectivity  
ping 10.0.2.10

# Check routing
ip route show
```

---

## Reflection Questions

- What AWS components replace switches and routers from your Day 2 labs?
- Why is it important to separate public and private subnets?  
- How would you enable outbound internet access for private instances (hint: NAT Gateway)?  
- How could you automate this setup using CloudFormation or Terraform?

---

## Summary

| Traditional Network | AWS Equivalent |
|----------------------|----------------|
| Switch / VLAN | Subnet |
| Router | Route Table |
| Firewall | Security Group / NACL |
| Internet Access | Internet Gateway |
| Physical Hosts | EC2 Instances |

---

**End of Lab 05 – Building a VPC Architecture in AWS**
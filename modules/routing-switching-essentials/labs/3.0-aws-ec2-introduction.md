# Lab 00 – Getting Started with AWS: EC2 Instances and AWS Console

**Objective:**  
Introduction to Amazon Web Services (AWS) for networking professionals transitioning from on-premises to cloud infrastructure. You will learn to navigate the AWS Management Console, understand basic AWS concepts, and create your first EC2 instances to prepare for advanced networking labs.

---
## Pre-requisites

Make sure to use the credentials provided by the instructor to access your aws platform.


## ⚙️ Step 1. Navigate the AWS Management Console

### Logging In
1. **Access AWS Console:**
   - Go to [console.aws.amazon.com](https://console.aws.amazon.com)
   - Enter your **email address** and **password**
   - Complete any MFA if configured

2. **Console Dashboard Overview:**
   - **Search Bar:** Find services quickly (top of screen)
   - **Recently Visited Services:** Quick access to used services
   - **All Services:** Complete list organized by category
   - **Region Selector:** Top-right corner (important!)

### Understanding AWS Regions
3. **Select Your Region:**
   - Click the **region dropdown** (top-right, next to your name)
   - Choose **US East (N. Virginia)** for this lab
   - **Why it matters:** Resources are region-specific

4. **Region Concepts:**
   - **Region:** Geographic location (e.g., us-east-1)
   - **Availability Zone (AZ):** Data center within a region (e.g., us-east-1a)
   - **Edge Location:** Content delivery network (CDN) points

---

## Step 2. Explore Key AWS Services for Networking

### Navigate to EC2 Service
1. **Open EC2 Dashboard:**
   - In the search bar, type **"EC2"**
   - Click **"EC2"** from the dropdown
   - **Alternative:** Services → Compute → EC2

2. **EC2 Dashboard Overview:**
   - **Instances:** Virtual machines currently running
   - **Images (AMIs):** Templates for creating instances
   - **Key Pairs:** SSH keys for secure access
   - **Security Groups:** Virtual firewalls
   - **Elastic IPs:** Static public IP addresses

### Navigate to VPC Service
3. **Open VPC Dashboard:**
   - Search for **"VPC"**
   - Click **"VPC"** from results
   - **Alternative:** Services → Networking & Content Delivery → VPC

4. **VPC Dashboard Overview:**
   - **Your VPCs:** Virtual private clouds you create
   - **Subnets:** Network segments within VPCs
   - **Route Tables:** Routing configuration
   - **Internet Gateways:** Connection to internet
   - **Security Groups:** Instance-level firewalls
   - **Network ACLs:** Subnet-level firewalls

---

## Step 3. Create Your First EC2 Instance

### Launch Instance Wizard
1. **Start Instance Creation:**
   - In EC2 Dashboard, click **"Launch Instance"**
   - **Instance Name:** Enter `MyFirstInstance`

2. **Choose Amazon Machine Image (AMI):**
   - Select **"Amazon Linux 2 AMI"** (Free tier eligible)
   - **What is an AMI?** Pre-configured operating system template

3. **Choose Instance Type:**
   - Select **"t2.micro"** (Free tier eligible)
   - **vCPUs:** 1, **Memory:** 1 GiB
   - Click **"Next: Configure Instance Details"**

### Configure Instance Details
4. **Network Settings:**
   - **Network (VPC):** Leave default VPC selected
   - **Subnet:** Leave default (will auto-assign to an AZ)
   - **Auto-assign Public IP:** **Enable** (important for remote access)

5. **Storage Configuration:**
   - **Root Volume:** 8 GiB GP2 (General Purpose SSD)
   - **Free tier eligible:** Up to 30 GB
   - Click **"Next: Add Tags"**

6. **Add Tags (Optional but Recommended):**
   - Click **"Add Tag"**
   - **Key:** `Name`, **Value:** `MyFirstInstance`
   - **Key:** `Purpose`, **Value:** `Learning`
   - **Key:** `Lab`, **Value:** `Day3-Lab00`

### Configure Security Group
7. **Create Security Group:**
   - **Security group name:** `MyFirstSG`
   - **Description:** `Allow SSH access for learning`
   - **Rules:**
     - **Type:** SSH, **Protocol:** TCP, **Port:** 22, **Source:** My IP
   - **What this does:** Allows SSH access only from your current IP

8. **Review and Launch:**
   - Click **"Review and Launch"**
   - Review all settings
   - Click **"Launch"**

### Key Pair Creation
9. **Create Key Pair for SSH:**
   - **Key pair name:** `MyAWSKey`
   - **Key pair type:** RSA
   - **Private key file format:** .pem (for Mac/Linux) or .ppk (for PuTTY)
   - Click **"Download Key Pair"**
   - **Important:** Store this file securely! You cannot download it again

10. **Launch Instance:**
    - Click **"Launch Instances"**
    - Click **"View Instances"** to see your instance

---

## Step 4. Monitor and Connect to Your Instance

### Instance Status Check
1. **View Instance Details:**
   - In EC2 Dashboard → **Instances**
   - Find your instance `MyFirstInstance`
   - **Instance State:** Should show "Running" (may take 2-3 minutes)
   - **Status Checks:** Should show "2/2 checks passed"

2. **Important Instance Information:**
   - **Instance ID:** Unique identifier (e.g., i-1234567890abcdef0)
   - **Public IPv4 address:** For internet access
   - **Private IPv4 address:** For internal VPC communication
   - **Key pair name:** SSH key used
   - **Security groups:** Firewall rules applied

### Connect to Your Instance
3. **SSH Connection (Mac/Linux):**
   ```bash
   # Change key permissions
   chmod 400 MyAWSKey.pem
   
   # Connect to instance
   ssh -i MyAWSKey.pem ec2-user@<PUBLIC-IP-ADDRESS>
   ```

4. **SSH Connection (Windows - PuTTY):**
   - Convert .pem to .ppk using PuTTYgen
   - Open PuTTY
   - **Host Name:** ec2-user@<PUBLIC-IP-ADDRESS>
   - **Connection → SSH → Auth:** Browse for .ppk file
   - Click **"Open"**

5. **Alternative: AWS Console Connect:**
   - Select your instance
   - Click **"Connect"**
   - Choose **"EC2 Instance Connect"**
   - Click **"Connect"** (opens browser-based terminal)

### Verify Connection
6. **Test Basic Commands:**
   ```bash
   # Check hostname
   hostname
   
   # Check IP configuration
   ip addr show
   
   # Check internet connectivity
   ping -c 4 google.com
   
   # Check AWS metadata
   curl http://169.254.169.254/latest/meta-data/instance-id
   ```

---

## Step 5. Explore AWS Networking Concepts

### Understanding Default VPC
1. **Check Current Network Configuration:**
   ```bash
   # View routing table
   route -n
   
   # Check DNS configuration
   cat /etc/resolv.conf
   
   # View network interfaces
   ifconfig
   ```

2. **From AWS Console:**
   - Go to **VPC Dashboard**
   - Click **"Your VPCs"**
   - Select the **default VPC**
   - Note the **CIDR block** (likely 172.31.0.0/16)

### Security Group Analysis
3. **Review Security Group:**
   - Go to **EC2 → Security Groups**
   - Select **MyFirstSG**
   - **Inbound Rules:** SSH (port 22) from your IP
   - **Outbound Rules:** All traffic (default)

4. **Security Group vs. Traditional Firewall:**
   - **Stateful:** Return traffic automatically allowed
   - **Instance-level:** Applied to specific EC2 instances
   - **White-list only:** Deny all by default, explicit allow rules

---

## Verification Checklist

| Component | Status | How to Verify |
|-----------|---------|---------------|
| **AWS Account** | Pass | Successfully logged into console |
| **Region Selected** | Pass | US East (N. Virginia) shown in top-right |
| **EC2 Instance** | Pass | Instance state = "Running" |
| **Public IP** | Pass | Public IP address assigned |
| **SSH Access** | Pass | Successfully connected via SSH |
| **Internet Access** | Pass | `ping google.com` succeeds |
| **Security Group** | Pass | SSH rule allows your IP only |

---

## Key Concepts Learned

### AWS Fundamentals
- **Regions and Availability Zones:** Geographic distribution for redundancy
- **EC2 Instances:** Virtual servers in the cloud
- **AMIs:** Templates for creating instances
- **Security Groups:** Instance-level firewalls

### Networking Concepts
- **Default VPC:** AWS provides a basic network automatically
- **Public/Private IPs:** Instances can have both internal and external addresses
- **SSH Key Pairs:** Secure authentication for Linux instances
- **Internet Gateway:** Provides internet access to VPC

### Cost Management
- **Free Tier Limits:** Understanding what's included
- **Instance Types:** t2.micro for learning, larger for production
- **Resource Cleanup:** Always terminate unused resources

---

## Cleanup (Important!)

### Terminate Your Instance
1. **Stop Charges:**
   - Go to **EC2 → Instances**
   - Select `MyFirstInstance`
   - **Instance State → Terminate Instance**
   - **Confirm termination**

2. **Verify Cleanup:**
   - Instance state should show "Terminated"
   - **Storage:** EBS volumes are automatically deleted
   - **Security Group:** Can be kept for future labs

> **Important:** Always terminate instances when not in use to avoid unexpected charges!

---

## What's Next?

You're now ready for advanced AWS networking labs:
- **Lab 01:** Building VPC Architecture
- **Lab 02:** Configuring Security Groups
- **Lab 03:** Network ACLs and Subnet Security

### Skills Acquired
- AWS Console navigation  
- EC2 instance creation and management  
- SSH connectivity to cloud instances  
- Basic AWS networking concepts  
- Security group configuration  
- Cost management awareness

---

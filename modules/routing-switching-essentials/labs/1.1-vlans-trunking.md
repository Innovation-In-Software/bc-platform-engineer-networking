# Lab 01 – VLANs and Trunking

**Objective:**  
In this lab, you will configure VLANs, assign access ports, and enable trunking between switches in Cisco Packet Tracer. You will also verify VLAN communication and understand how VLANs isolate broadcast domains.

---

## Topology
```
[PC1]----[SW1]----[SW2]----[PC2]
```

| Device | Interface | VLAN | IP Address |
|---------|------------|------|-------------|
| PC1 | NIC | VLAN 10 | 192.168.10.10/24 |
| PC2 | NIC | VLAN 20 | 192.168.20.10/24 |

---

## Step 1. Build the Topology in Packet Tracer

1. Add **2 switches** (2960) and **2 PCs**.  
2. Connect PC1 and PC2 to their respective switches using **Copper Straight-Through** cables.  
3. Connect SW1 to SW2 using **FastEthernet0/24** using **Copper Cross-Over** cables.  
4. Ensure all interfaces show **green links** before proceeding.
> You can use the fast forward button to accelerate the links activation
---

## Step 2. Create VLANs on Both Switches

1. Click switch0 and navigate to the CLI
```
Switch>enable
Switch#configure terminal
Switch(config)# vlan 10
Switch(config-vlan)# name HR
```

2. Do the same for your other Switch
```
Switch>enable
Switch#configure terminal
Switch(config)# vlan 20
Switch(config-vlan)# name FINANCE
```

> Note: VLANs 10 and 20 will segment the network into separate broadcast domains.

---

## Step 3. Assign Access Ports

### On SW1
```
Switch(config)# interface fa0/1
Switch(config-if)# switchport mode access
Switch(config-if)# switchport access vlan 10
```

### On SW2
```
Switch(config)# interface fa0/2
Switch(config-if)# switchport mode access
Switch(config-if)# switchport access vlan 20
```

---

## Step 4. Configure the Trunk Link Between Switches
```
Switch(config)# interface fa0/24
Switch(config-if)# switchport mode trunk
Switch(config-if)# switchport trunk allowed vlan 10,20
```

> Note: This ensures VLAN 10 and VLAN 20 traffic can travel across switches.

---

## Step 5. Configure IPs on PCs

| PC | IP Address | Subnet Mask | Gateway |
|----|-------------|-------------|----------|
| PC1 | 192.168.10.10 | 255.255.255.0 | N/A |
| PC2 | 192.168.20.10 | 255.255.255.0 | N/A |

---

## Step 6. Verify Configuration

### VLANs
```
show vlan brief
```
### Trunks
```
show interfaces trunk
```

VLAN 10 and 20 should appear as **active**, and **FastEthernet0/24** should be a trunk port.

---

## Step 7. Test Connectivity

### Test 1: Inter-VLAN Communication (Should Fail)
1. **On PC1 (VLAN 10):**
   - Open **Command Prompt** in Packet Tracer
   - Execute ping command:
   ```
   C:\> ping 192.168.20.10
   ```
   - **Expected Result:** **Request timed out** or **Destination host unreachable**
   - **Why it fails:** PC1 (VLAN 10) and PC2 (VLAN 20) are in different broadcast domains

2. **Verify VLAN isolation:**
   - Try pinging from PC2 to PC1:
   ```
   C:\> ping 192.168.10.10
   ```
   - **Expected Result:** **Should also fail** for the same reason

### Test 2: Intra-VLAN Communication (Should Succeed)
1. **Add PC3 to SW2:**
   - Add a third PC to the topology
   - Connect PC3 to SW2 interface **FastEthernet0/3**

2. **Configure SW2 interface for VLAN 10:**
   ```
   SW2(config)# interface fa0/3
   SW2(config-if)# switchport mode access
   SW2(config-if)# switchport access vlan 10
   SW2(config-if)# exit
   ```

3. **Configure PC3 network settings:**
   - **IP Address:** 192.168.10.20
   - **Subnet Mask:** 255.255.255.0
   - **Default Gateway:** (leave blank for this lab)

4. **Test connectivity within VLAN 10:**
   - **From PC1 to PC3:**
   ```
   C:\> ping 192.168.10.20
   ```
   - **Expected Result:** **Reply from 192.168.10.20** (successful pings)
   
   - **From PC3 to PC1:**
   ```
   C:\> ping 192.168.10.10
   ```
   - **Expected Result:** **Reply from 192.168.10.10** (successful pings)

5. **Verify PC3 cannot reach VLAN 20:**
   ```
   C:\> ping 192.168.20.10
   ```
   - **Expected Result:** **Request timed out** (PC3 in VLAN 10 cannot reach PC2 in VLAN 20)

### Additional Verification Commands
**On switches, verify the configuration:**
```
show vlan brief
show interfaces fa0/3 switchport
show mac address-table
```

### Expected Results Summary
| Source | Destination | VLAN | Result | Reason |
|--------|-------------|------|---------|---------|
| PC1 (VLAN 10) | PC2 (VLAN 20) | Cross-VLAN | Fail | Different broadcast domains |
| PC1 (VLAN 10) | PC3 (VLAN 10) | Same VLAN | Success | Same broadcast domain |
| PC3 (VLAN 10) | PC2 (VLAN 20) | Cross-VLAN | Fail | Different broadcast domains |
   

---

## Reflection

- What happens if a VLAN is missing on one switch?  
- Why does traffic between VLANs fail without routing?  
- What is the purpose of trunking in multi-switch environments?

---

## Summary

| Concept | Description |
|----------|--------------|
| VLANs | Separate networks at Layer 2 |
| Access Ports | Connect hosts to specific VLANs |
| Trunk Links | Carry multiple VLANs between switches |
| Verification | `show vlan brief`, `show interfaces trunk` |

---

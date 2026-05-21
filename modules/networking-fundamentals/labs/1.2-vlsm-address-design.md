# Lab 02 – IP Addressing and Subnet Planning Using VLSM

**Objective:** Design variable subnet sizes efficiently.

## Topology
**Router — Switch — PCs**

Each router interface connects to a switch, and each switch connects to a group of PCs.

---
## Step 0. Creating the topology in Packet Tracer 

1. Open **Cisco Packet Tracer**.
2. Add **Three PCs** and **one switch for each PC** (e.g., `2960`). Connect them with Straight-Through cable as usual
3. Add **One Router**
4. Connect each switch to the router on one of the gigabit interface, use Straight-Through cable
> Note the pairing of switch - gigabite interface, it will be usefull for later


## Step 1. Subnet the Network `192.168.100.0/24`

We need:
| Subnet | Hosts Required | Subnet Mask | Usable IPs | Subnet Size | Allocation |
|---------|----------------|--------------|-------------|--------------|-------------|
| A | 60 | `/26` | 62 | 255.255.255.192 | `192.168.100.0/26` |
| B | 30 | `/27` | 30 | 255.255.255.224 | `192.168.100.64/27` |
| C | 10 | `/28` | 14 | 255.255.255.240 | `192.168.100.96/28` |

### Subnet Details

1. **Subnet A (/26)**
   - Network: `192.168.100.0`
   - Usable: `192.168.100.1` – `192.168.100.62`
   - Broadcast: `192.168.100.63`

2. **Subnet B (/27)**
   - Network: `192.168.100.64`
   - Usable: `192.168.100.65` – `192.168.100.94`
   - Broadcast: `192.168.100.95`

3. **Subnet C (/28)**
   - Network: `192.168.100.96`
   - Usable: `192.168.100.97` – `192.168.100.110`
   - Broadcast: `192.168.100.111`

---

## Step 2. Configure Router Interfaces

Assume:
- `GigabitEthernet0/0` → Subnet A (60 hosts)
- `GigabitEthernet0/1` → Subnet B (30 hosts)
- `GigabitEthernet0/2` → Subnet C (10 hosts)

### Cisco IOS Commands

- Below you will find all the IOS commands to be run on each router.  
- To access the IOS CLI make sure to click on the router and navigate to the CLI page.

```bash
Router> enable
Router# configure terminal
# Subnet A - 192.168.100.0/26
Router(config)# interface gigabitEthernet0/0
Router(config-if)# ip address 192.168.100.1 255.255.255.192
Router(config-if)# no shutdown
Router(config-if)# exit
# Subnet B - 192.168.100.64/27
Router(config)# interface gigabitEthernet0/1
Router(config-if)# ip address 192.168.100.65 255.255.255.224
Router(config-if)# no shutdown
Router(config-if)# exit

# Subnet C - 192.168.100.96/28
Router(config)# interface gigabitEthernet0/2
Router(config-if)# ip address 192.168.100.97 255.255.255.240
Router(config-if)# no shutdown
Router(config-if)# exit

Router(config)# end
Router# write memory

```

---

## Step 3. Configure PCs

Assign IP addresses manually or via DHCP (if available):

| Subnet | Example PC IP | Gateway |
|---------|----------------|----------|
| A | 192.168.100.10 | 192.168.100.1 |
| B | 192.168.100.70 | 192.168.100.65 |
| C | 192.168.100.100 | 192.168.100.97 |

---

## Step 4. Verify Configuration

### On the Router
```bash
Router# show ip interface brief
Router# show ip route
```


**Expected Output:**

```
192.168.100.0/26 is directly connected, GigabitEthernet0/0
192.168.100.64/27 is directly connected, GigabitEthernet0/1
192.168.100.96/28 is directly connected, GigabitEthernet0/2
```

### Test Connectivity

- Now we will make sure our network is working properly and our components can communicate 

```
Router# ping 192.168.100.70
Router# ping 192.168.100.100
```

Successful replies indicate proper connectivity between subnets. If you CLI stays hanging, use Ctrl+C to cancel the command.

---

## Summary

| Task | Description |
|------|--------------|
| Subnetting | Divided `192.168.100.0/24` into `/26`, `/27`, and `/28` networks |
| Router Configuration | Assigned each subnet to a router interface |
| PC Configuration | Assigned IPs with correct gateways |
| Verification | Used `show ip route` and `ping` to confirm connectivity |

---

# Lab 03 – Spanning Tree Protocol and EtherChannel

**Objective:**  
Understand and verify Spanning Tree Protocol (STP) operation and configure EtherChannel (LACP) for redundancy and load balancing in Packet Tracer.

---

## Topology

```

    [SW1]
    /   \
 [SW2]  [SW3]
```

All switches are interconnected using redundant links.

---

## Step 1. Build the Topology and Verify Default STP Configuration

### Topology Setup
1. **Add 3 switches** (2960 series) to Packet Tracer
2. **Create redundant connections:**
   - SW1 to SW2: FastEthernet0/1 ↔ FastEthernet0/1
   - SW1 to SW3: FastEthernet0/2 ↔ FastEthernet0/2  
   - SW2 to SW3: FastEthernet0/3 ↔ FastEthernet0/3
3. **Add PCs** for testing:
   - PC1 connected to SW2 FastEthernet0/10
   - PC2 connected to SW3 FastEthernet0/10

### Initial STP Verification
1. **Check STP status on all switches:**
   ```
   Switch# show spanning-tree
   ```

2. **Analyze the output for SW1:**
   ```
   Switch# show spanning-tree vlan 1
   ```
   - **Expected Information:**
     - Bridge ID (Priority + MAC address)
     - Root Bridge identification
     - Port roles and states

3. **Example expected output:**
   ```
   VLAN0001
     Spanning tree enabled protocol ieee
     Root ID    Priority    32769
                Address     000C.CF8A.4A80
                This bridge is the root
                Hello Time   2 sec  Max Age 20 sec  Forward Delay 15 sec
   
     Bridge ID  Priority    32769  (priority 32768 sys-id-ext 1)
                Address     000C.CF8A.4A80
                Hello Time   2 sec  Max Age 20 sec  Forward Delay 15 sec
                Aging Time  300 sec
   
   Interface           Role Sts Cost      Prio.Nbr Type
   ------------------- ---- --- --------- -------- --------------------------------
   Fa0/1              Desg FWD 19        128.1    P2p
   Fa0/2              Desg FWD 19        128.2    P2p
   ```

4. **Check which ports are blocking:**
   ```
   Switch# show spanning-tree interface fa0/3
   ```
   - **Look for:** Port state (Forwarding/Blocking)
   - **Understand:** Why certain ports block to prevent loops

### STP Analysis Checklist
| Switch | Check | Command | Expected Result |
|--------|-------|---------|----------------|
| SW1 | Root Bridge Status | `show spanning-tree` | Should show "This bridge is the root" |
| SW2 | Port Roles | `show spanning-tree vlan 1` | Mix of Root/Designated ports |
| SW3 | Blocking Ports | `show spanning-tree` | At least one port should be blocking |
| All | Convergence | `show spanning-tree summary` | All VLANs should be forwarding |

---

## Step 2. Configure the Root Bridge
```
SW1(config)# spanning-tree vlan 1 priority 4096
```
SW1 becomes the **Root Bridge** (lower priority = higher priority for election).

---

## Step 3. Enable PortFast and BPDU Guard

Apply to all **access ports** (connected to PCs):
```
SW2(config)# interface range fa0/1 - 5
SW2(config-if-range)# spanning-tree portfast
SW2(config-if-range)# spanning-tree bpduguard enable
```
> Note: PortFast reduces convergence time, BPDU Guard prevents loops.

---

## Step 4. Configure EtherChannel Between SW2 and SW3
```
SW2(config)# interface range fa0/21 - 22
SW2(config-if-range)# channel-group 1 mode active

SW3(config)# interface range fa0/21 - 22
SW3(config-if-range)# channel-group 1 mode passive
```
This enables **LACP (Link Aggregation Control Protocol)** negotiation.

---

## Step 5. Verify EtherChannel Configuration

### Basic EtherChannel Verification
1. **Check EtherChannel summary:**
   ```
   Switch# show etherchannel summary
   ```
   - **Expected Output:**
   ```
   Number of channel-groups in use: 1
   Number of aggregators:           1
   
   Group  Port-channel  Protocol    Ports
   ------+-------------+-----------+-----------------------------------------------
   1      Po1(SU)         LACP      Fa0/21(P)   Fa0/22(P)
   ```
   - **Status Codes:**
     - `S` = Layer 2, `U` = Up
     - `P` = Port is in use and bundled

2. **Detailed interface information:**
   ```
   Switch# show interfaces port-channel 1
   ```
   - **Check for:** Interface status, protocol status, and member interfaces

3. **LACP neighbor information:**
   ```
   Switch# show lacp neighbor
   ```
   - **Expected:** Shows partner switch information and LACP state

### Advanced EtherChannel Verification
1. **Check load balancing method:**
   ```
   Switch# show etherchannel load-balance
   ```
   - **Default method:** Usually source MAC address

2. **Verify individual member interfaces:**
   ```
   Switch# show interfaces fa0/21
   Switch# show interfaces fa0/22
   ```
   - **Status:** Both should be up/up
   - **Check:** No errors or drops

3. **LACP detailed information:**
   ```
   Switch# show lacp 1 detail
   ```
   - **Verify:** System priority, port priority, and operational key

### EtherChannel Status Verification
| Component | Command | Expected Result | Status |
|-----------|---------|----------------|--------|
| Bundle Status | `show etherchannel summary` | Po1(SU) with 2 ports | Pass |
| Protocol | `show etherchannel 1 port-channel` | LACP negotiated | Pass |
| Member Ports | `show interfaces fa0/21-22` | Both up/up | Pass |
| LACP Neighbors | `show lacp neighbor` | Partner information visible | Pass |

---

## Step 6. Verify STP After EtherChannel Implementation

### STP Topology Analysis
1. **Check updated STP topology:**
   ```
   Switch# show spanning-tree vlan 1
   ```
   - **Key Change:** Port-channel1 appears as single interface to STP
   - **Benefit:** Eliminates one potential blocking port

2. **Compare before and after EtherChannel:**
   ```
   Switch# show spanning-tree interface port-channel 1
   ```
   - **Expected Output:**
   ```
   Vlan                Role Sts Cost      Prio.Nbr Type
   ------------------- ---- --- --------- -------- --------------------------------
   VLAN0001            Desg FWD 12        128.65   P2p
   ```

### Detailed STP Verification
1. **Root bridge confirmation:**
   ```
   SW1# show spanning-tree root
   ```
   - **Expected:** SW1 should be root for VLAN 1 (priority 4096)

2. **Port roles on each switch:**
   ```
   SW2# show spanning-tree vlan 1 | include Role
   SW3# show spanning-tree vlan 1 | include Role
   ```
   - **SW2:** Should have Root port toward SW1, Designated port (Po1) toward SW3
   - **SW3:** Should have Root port toward SW1, Root port (Po1) toward SW2

3. **Cost calculation verification:**
   ```
   Switch# show spanning-tree vlan 1 | include Cost
   ```
   - **EtherChannel cost:** Should be lower than individual links (typically 12 vs 19)
   - **Path selection:** Lower cost path becomes preferred

### STP Convergence Testing
1. **Monitor STP state changes:**
   ```
   Switch# debug spanning-tree events
   ```
   - **Caution:** Use carefully in production; disable after testing

2. **Check STP timers:**
   ```
   Switch# show spanning-tree detail | include Timer
   ```
   - **Forward Delay:** 15 seconds (default)
   - **Hello Timer:** 2 seconds (default)
   - **Max Age:** 20 seconds (default)

3. **Verify PortFast configuration:**
   ```
   SW2# show spanning-tree interface fa0/10 detail
   ```
   - **Expected:** PortFast should be enabled on access ports

### STP Enhancement Verification
| Feature | Command | Expected Behavior | Status |
|---------|---------|------------------|--------|
| Root Bridge | `show spanning-tree root` | SW1 is root (priority 4096) | Pass |
| EtherChannel Integration | `show spanning-tree interface po1` | Single logical link | Pass |
| PortFast | `show spanning-tree interface fa0/10` | Immediate forwarding | Pass |
| BPDU Guard | `show spanning-tree interface fa0/10` | Protection enabled | Pass |

### Topology Understanding
```
# Visual representation of final STP topology:
#
#           SW1 (Root Bridge)
#          /  |  \
#         /   |   \
#        /    |    \
#     SW2 ----+---- SW3
#      |             |
#    PC1           PC2
#
# Where SW2-SW3 connection is EtherChannel (Po1)
```

---

## Step 7. Comprehensive Testing and Failure Recovery

### Test 1: Baseline Connectivity Test
1. **Configure PC IP addresses:**
   - **PC1:** 192.168.1.10/24 (connected to SW2)
   - **PC2:** 192.168.1.20/24 (connected to SW3)

2. **Test basic connectivity:**
   ```
   PC1> ping 192.168.1.20
   ```
   - **Expected Result:** **Successful pings** (4/4 packets received)

### Test 2: EtherChannel Load Balancing Test
1. **Generate continuous traffic:**
   ```
   PC1> ping -t 192.168.1.20
   ```

2. **Monitor EtherChannel utilization:**
   ```
   SW2# show interfaces port-channel 1
   SW3# show interfaces port-channel 1
   ```
   - **Check:** Packet counters should increment on both member interfaces

### Test 3: Single Link Failure Recovery
1. **Document baseline state:**
   ```
   SW2# show etherchannel summary
   ```
   - **Expected:** Po1(SU) with Fa0/21(P) Fa0/22(P)

2. **Simulate link failure:**
   ```
   SW2(config)# interface fa0/21
   SW2(config-if)# shutdown
   ```

3. **Verify EtherChannel adapts:**
   ```
   SW2# show etherchannel summary
   ```
   - **Expected:** Po1(SU) with Fa0/22(P) only
   - **Status:** One member down, EtherChannel still operational

4. **Test connectivity during failure:**
   ```
   PC1> ping 192.168.1.20
   ```
   - **Expected Result:** **Pings still succeed** (redundancy working)

5. **Restore the failed link:**
   ```
   SW2(config)# interface fa0/21
   SW2(config-if)# no shutdown
   ```

6. **Verify recovery:**
   ```
   SW2# show etherchannel summary
   ```
   - **Expected:** Po1(SU) with both Fa0/21(P) Fa0/22(P) restored

### Test 4: STP Convergence with EtherChannel
1. **Check STP status before EtherChannel:**
   ```
   Switch# show spanning-tree vlan 1
   ```
   - **Note:** Multiple physical links visible to STP

2. **Check STP after EtherChannel:**
   ```
   Switch# show spanning-tree vlan 1
   ```
   - **Expected:** Port-channel1 appears as single logical link
   - **Benefit:** Reduced STP complexity and faster convergence

### Test 5: Complete EtherChannel Failure
1. **Shut down entire EtherChannel:**
   ```
   SW2(config)# interface port-channel 1
   SW2(config-if)# shutdown
   ```

2. **Observe STP reconvergence:**
   ```
   Switch# show spanning-tree vlan 1
   ```
   - **Expected:** STP recalculates, alternate path becomes active
   - **Convergence time:** Should be ~30-50 seconds

3. **Test connectivity:**
   ```
   PC1> ping 192.168.1.20
   ```
   - **Expected:** Temporary loss, then recovery via alternate path

4. **Restore EtherChannel:**
   ```
   SW2(config)# interface port-channel 1
   SW2(config-if)# no shutdown
   ```

### Comprehensive Test Results
| Test Scenario | Traffic Source | Expected Result | Recovery Time | Status |
|---------------|----------------|----------------|---------------|---------||
| Normal Operation | PC1→PC2 | Success | N/A | Pass |
| Single Link Down | PC1→PC2 | Success | <1 second | Pass |
| EtherChannel Down | PC1→PC2 | Success (via STP alternate) | ~30-50 sec | Pass |
| Link Restoration | PC1→PC2 | Success | <5 seconds | Pass |

### Performance Monitoring Commands
```
# Monitor interface statistics
show interfaces fa0/21 | include packets
show interfaces fa0/22 | include packets
show interfaces port-channel 1 | include packets

# Check for errors
show interfaces fa0/21 | include error
show interfaces fa0/22 | include error

# Monitor STP changes
show spanning-tree vlan 1 | include listening|learning|forwarding
```

---

## Reflection

- Why is PortFast not used on trunk or uplink ports?  
- How does LACP help redundancy?  
- What happens if STP and EtherChannel are both disabled?

---

## Summary

| Concept | Description |
|----------|--------------|
| STP | Prevents switching loops |
| Root Bridge | Central reference in STP topology |
| PortFast / BPDU Guard | Speed up access port activation and protect from loops |
| EtherChannel | Combines multiple links for redundancy and load balancing |

---

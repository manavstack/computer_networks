"""
topology_engine.py - Core Network Engine for the 4 Foundational Topologies:
1. Bus Topology (Linear Shared Trunk, Taps, 50-ohm Terminators, CSMA/CD)
2. Star Topology (Central Switch, Dedicated Links, CAM/MAC Table Learning, Microsegmentation)
3. Ring Topology (IEEE 802.5 Token Ring, Token Free/Busy, A=1/C=1 ACK bits, Repeaters)
4. Mesh Topology (Full Point-to-Point Mesh, L = N(N-1)/2, Dedicated Links, Dijkstra Routing)
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Tuple, Optional, Set, Any
import networkx as nx
import math


class TopologyType(Enum):
    BUS = "Bus Topology"
    STAR = "Star Topology"
    RING = "Ring Topology"
    MESH = "Mesh Topology"


@dataclass
class WorkflowStep:
    step_num: int
    title: str
    active_nodes: List[str]
    active_links: List[Tuple[str, str]]
    description: str
    layer_info: str  # e.g., 'Layer 1 (Physical)' or 'Layer 2 (Data Link)'
    status: str      # 'in_progress', 'delivered', 'dropped', 'filtered'


class NetworkTopology:
    def __init__(
        self,
        topo_type: TopologyType,
        num_nodes: int = 5,
        star_mode: str = "Switch",  # "Switch" or "Hub"
    ):
        self.topo_type = topo_type
        self.num_nodes = max(3, min(10, num_nodes))
        self.star_mode = star_mode  # "Switch" or "Hub"

        self.graph = nx.Graph()
        self.pos: Dict[str, Tuple[float, float]] = {}
        self.node_roles: Dict[str, str] = {}
        self.mac_addresses: Dict[str, str] = {}
        self.ip_addresses: Dict[str, str] = {}
        self.switch_cam_table: Dict[str, str] = {}  # MAC -> port_name

        # Token Ring State
        self.token_state: str = "FREE"  # "FREE" or "BUSY"
        self.token_holder: str = "Host_1"

        # Fault management
        self.failed_links: Set[Tuple[str, str]] = set()
        self.failed_nodes: Set[str] = set()
        self.bus_terminator_active: bool = True

        self._build_topology()

    def _build_topology(self):
        """Constructs geometry, roles, MACs, and physical links for the 4 topologies."""
        self.graph.clear()
        self.pos.clear()
        self.node_roles.clear()
        self.mac_addresses.clear()
        self.ip_addresses.clear()

        n = self.num_nodes

        # 1. ──────── BUS TOPOLOGY ────────
        if self.topo_type == TopologyType.BUS:
            # Trunk cable taps: Tap_1 .. Tap_n
            # Hosts: Host_1 .. Host_n
            for i in range(1, n + 1):
                h = f"Host_{i}"
                tap = f"Tap_{i}"
                self.graph.add_node(h)
                self.graph.add_node(tap)
                self.node_roles[h] = "host"
                self.node_roles[tap] = "backbone_tap"
                self.mac_addresses[h] = f"00:1B:44:11:00:{i:02X}"
                self.ip_addresses[h] = f"192.168.1.{i}"

                # Drop line from Host to Tap
                self.graph.add_edge(h, tap, cable_type="Drop Cable (Cat5e)", length_m=3.0)

                # Linear positions
                x_pos = (i - 1) * 2.2
                self.pos[tap] = (x_pos, 0.0)
                y_offset = 1.3 if (i % 2 == 1) else -1.3
                self.pos[h] = (x_pos, y_offset)

            # Central Coaxial Trunk connecting consecutive taps
            for i in range(1, n):
                self.graph.add_edge(f"Tap_{i}", f"Tap_{i+1}", cable_type="50Ω Coaxial Trunk", length_m=10.0)

        # 2. ──────── STAR TOPOLOGY ────────
        elif self.topo_type == TopologyType.STAR:
            center_name = "Central_Switch" if self.star_mode == "Switch" else "Central_Hub"
            self.graph.add_node(center_name)
            self.node_roles[center_name] = "switch" if self.star_mode == "Switch" else "hub"
            self.pos[center_name] = (0.0, 0.0)

            angle_step = 2.0 * math.pi / n
            for i in range(1, n + 1):
                h = f"Host_{i}"
                self.graph.add_node(h)
                self.node_roles[h] = "host"
                self.mac_addresses[h] = f"00:1B:44:22:00:{i:02X}"
                self.ip_addresses[h] = f"192.168.2.{i}"

                angle = (i - 1) * angle_step
                self.pos[h] = (3.0 * math.cos(angle), 3.0 * math.sin(angle))
                self.graph.add_edge(h, center_name, cable_type="UTP Cat6", length_m=15.0)

        # 3. ──────── RING TOPOLOGY ────────
        elif self.topo_type == TopologyType.RING:
            angle_step = 2.0 * math.pi / n
            hosts = [f"Host_{i}" for i in range(1, n + 1)]
            for i, h in enumerate(hosts, start=1):
                self.graph.add_node(h)
                self.node_roles[h] = "host"
                self.mac_addresses[h] = f"00:1B:44:33:00:{i:02X}"
                self.ip_addresses[h] = f"192.168.3.{i}"

                angle = (i - 1) * angle_step
                self.pos[h] = (3.0 * math.cos(angle), 3.0 * math.sin(angle))

            # Point-to-point ring links
            for i in range(n):
                u = hosts[i]
                v = hosts[(i + 1) % n]
                self.graph.add_edge(u, v, cable_type="Fiber Ring Link", length_m=25.0)

        # 4. ──────── MESH TOPOLOGY ────────
        elif self.topo_type == TopologyType.MESH:
            angle_step = 2.0 * math.pi / n
            nodes = [f"Node_{i}" for i in range(1, n + 1)]
            for i, m_name in enumerate(nodes, start=1):
                self.graph.add_node(m_name)
                self.node_roles[m_name] = "host"
                self.mac_addresses[m_name] = f"00:1B:44:44:00:{i:02X}"
                self.ip_addresses[m_name] = f"10.0.0.{i}"

                angle = (i - 1) * angle_step
                self.pos[m_name] = (3.0 * math.cos(angle), 3.0 * math.sin(angle))

            # Connect every pair: N(N-1)/2 links
            for i in range(n):
                for j in range(i + 1, n):
                    u, v = nodes[i], nodes[j]
                    self.graph.add_edge(u, v, cable_type="Dedicated Point-to-Point", length_m=20.0)

    # ──────────────────────────────────────────────────────────
    #  FAULT MANAGEMENT
    # ──────────────────────────────────────────────────────────
    def toggle_link_fault(self, u: str, v: str) -> bool:
        edge = (min(u, v), max(u, v))
        if edge in self.failed_links:
            self.failed_links.remove(edge)
            return False
        else:
            self.failed_links.add(edge)
            return True

    def toggle_node_fault(self, node: str) -> bool:
        if node in self.failed_nodes:
            self.failed_nodes.remove(node)
            return False
        else:
            self.failed_nodes.add(node)
            return True

    def is_link_operational(self, u: str, v: str) -> bool:
        edge = (min(u, v), max(u, v))
        if edge in self.failed_links:
            return False
        if u in self.failed_nodes or v in self.failed_nodes:
            return False
        return True

    def get_active_graph(self) -> nx.Graph:
        active = nx.Graph()
        for node, data in self.graph.nodes(data=True):
            if node not in self.failed_nodes:
                active.add_node(node, **data)
        for u, v, data in self.graph.edges(data=True):
            if self.is_link_operational(u, v):
                active.add_edge(u, v, **data)
        return active

    # ──────────────────────────────────────────────────────────
    #  CLEAR WORKFLOW ENGINE FOR EACH TOPOLOGY
    # ──────────────────────────────────────────────────────────
    def get_detailed_workflow(self, source: str, destination: str) -> List[WorkflowStep]:
        """
        Produces crystal-clear, step-by-step educational workflows explaining exactly
        how packets and control signals flow in the selected topology.
        """
        steps: List[WorkflowStep] = []

        if source == destination:
            steps.append(WorkflowStep(
                step_num=1,
                title="Loopback Interface",
                active_nodes=[source],
                active_links=[],
                description=f"Source and Destination are the same ({source}). Frame is handled internally via local loopback (127.0.0.1) without entering the physical medium.",
                layer_info="Layer 3 (Network Layer)",
                status="delivered"
            ))
            return steps

        if source in self.failed_nodes:
            steps.append(WorkflowStep(
                step_num=1,
                title="Source Offline",
                active_nodes=[source],
                active_links=[],
                description=f"Source host {source} is powered off or disabled. Transmission aborted.",
                layer_info="Layer 1 (Physical)",
                status="dropped"
            ))
            return steps

        # ══════════════════════════════════════════════════════
        # 1. BUS TOPOLOGY WORKFLOW
        # ══════════════════════════════════════════════════════
        if self.topo_type == TopologyType.BUS:
            src_tap = f"Tap_{source.split('_')[1]}"
            dst_tap = f"Tap_{destination.split('_')[1]}"

            # Step 1: Carrier Sense & Drop Line Transmission
            steps.append(WorkflowStep(
                step_num=1,
                title="Step 1: Carrier Sense (CSMA/CD) & Drop Line Transmission",
                active_nodes=[source, src_tap],
                active_links=[(source, src_tap)],
                description=f"{source} senses the medium for electrical carrier voltage. Channel is idle. {source} injects Manchester-encoded frame onto its drop cable to {src_tap}.",
                layer_info="Layer 1 Physical & Layer 2 MAC",
                status="in_progress"
            ))

            if not self.is_link_operational(source, src_tap):
                steps.append(WorkflowStep(
                    step_num=2,
                    title="Error: Broken Drop Cable",
                    active_nodes=[source],
                    active_links=[(source, src_tap)],
                    description=f"Physical drop cable between {source} and {src_tap} is severed! Frame fails to reach the backbone trunk.",
                    layer_info="Layer 1 Physical",
                    status="dropped"
                ))
                return steps

            # Step 2: Bidirectional Trunk Broadcast
            steps.append(WorkflowStep(
                step_num=2,
                title="Step 2: Bidirectional Signal Propagation on Coaxial Trunk",
                active_nodes=[src_tap],
                active_links=[],
                description="Electromagnetic waves propagate simultaneously in BOTH directions along the 50Ω coaxial trunk cable toward the terminators at approximately 2/3 speed of light.",
                layer_info="Layer 1 Physical",
                status="in_progress"
            ))

            # Step 3: Terminator Check
            if not self.bus_terminator_active:
                steps.append(WorkflowStep(
                    step_num=3,
                    title="CRITICAL FAULT: Missing Bus Terminator (Signal Reflection)",
                    active_nodes=[],
                    active_links=[],
                    description="Terminator is MISSING at the cable end! Signal hits the open circuit, reflects backward, and creates destructive standing wave interference (collision). All data is destroyed!",
                    layer_info="Layer 1 Physical Impairment",
                    status="dropped"
                ))
                return steps
            else:
                steps.append(WorkflowStep(
                    step_num=3,
                    title="Step 3: End Signal Absorption by 50Ω Terminators",
                    active_nodes=[],
                    active_links=[],
                    description="50-ohm BNC terminators at each cable end absorb the reaching electromagnetic waves, preventing signal reflections from bouncing back onto the bus.",
                    layer_info="Layer 1 Impedance Matching",
                    status="in_progress"
                ))

            # Check trunk connectivity
            active_g = self.get_active_graph()
            if not nx.has_path(active_g, src_tap, dst_tap):
                steps.append(WorkflowStep(
                    step_num=4,
                    title="Fault: Backbone Trunk Severed",
                    active_nodes=[src_tap],
                    active_links=[],
                    description="Central coaxial trunk cable is broken between the stations! Network is physically partitioned. Signal cannot cross the gap.",
                    layer_info="Layer 1 Physical",
                    status="dropped"
                ))
                return steps

            # Step 4: Address Filtering at All Stations
            for i in range(1, self.num_nodes + 1):
                h = f"Host_{i}"
                if h == source:
                    continue
                t = f"Tap_{i}"
                if h == destination:
                    steps.append(WorkflowStep(
                        step_num=len(steps) + 1,
                        title=f"Step 4: Destination Match on {destination}",
                        active_nodes=[t, destination],
                        active_links=[(t, destination)],
                        description=f"{destination} inspects Destination MAC ({self.mac_addresses[destination]}). It's a MATCH! NIC accepts frame, verifies CRC-32 checksum, and pushes payload up to OS network stack.",
                        layer_info="Layer 2 Data Link Layer",
                        status="delivered"
                    ))
                else:
                    steps.append(WorkflowStep(
                        step_num=len(steps) + 1,
                        title=f"Address Mismatch on {h} (Filtered)",
                        active_nodes=[t, h],
                        active_links=[(t, h)],
                        description=f"{h} reads Destination MAC. Address does NOT match its own MAC. Frame is silently discarded by hardware NIC filter.",
                        layer_info="Layer 2 MAC Filtering",
                        status="filtered"
                    ))

        # ══════════════════════════════════════════════════════
        # 2. STAR TOPOLOGY WORKFLOW
        # ══════════════════════════════════════════════════════
        elif self.topo_type == TopologyType.STAR:
            center = "Central_Switch" if self.star_mode == "Switch" else "Central_Hub"

            # Step 1: Ingress Transmission to Central Device
            steps.append(WorkflowStep(
                step_num=1,
                title="Step 1: Point-to-Point Uplink Transmission",
                active_nodes=[source, center],
                active_links=[(source, center)],
                description=f"{source} transmits packet across its dedicated full-duplex Cat6 UTP cable directly into port {source} of {center}.",
                layer_info="Layer 1 & Layer 2 Uplink",
                status="in_progress"
            ))

            if not self.is_link_operational(source, center):
                steps.append(WorkflowStep(
                    step_num=2,
                    title="Fault: Severed Cable",
                    active_nodes=[source],
                    active_links=[(source, center)],
                    description=f"Physical cable between {source} and {center} is unplugged or broken. Frame lost.",
                    layer_info="Layer 1 Physical",
                    status="dropped"
                ))
                return steps

            if center in self.failed_nodes:
                steps.append(WorkflowStep(
                    step_num=2,
                    title="CATASTROPHIC FAULT: Central Node Down (Single Point of Failure)",
                    active_nodes=[center],
                    active_links=[],
                    description=f"The central {center} has experienced hardware/power failure! Because all traffic aggregates here, the ENTIRE star network collapses.",
                    layer_info="Single Point of Failure (SPOF)",
                    status="dropped"
                ))
                return steps

            # Switch vs Hub logic
            if self.star_mode == "Switch":
                src_mac = self.mac_addresses[source]
                dst_mac = self.mac_addresses[destination]

                # Step 2: CAM Table Learning
                self.switch_cam_table[src_mac] = source
                steps.append(WorkflowStep(
                    step_num=2,
                    title="Step 2: Switch CAM Table Source Learning",
                    active_nodes=[center],
                    active_links=[],
                    description=f"Switch parses incoming Ethernet header: Learns Source MAC `{src_mac}` is on ingress Port `{source}`. Updates its hardware CAM (Content Addressable Memory) table.",
                    layer_info="Layer 2 Bridging / Switching",
                    status="in_progress"
                ))

                # Step 3: Destination Lookup
                if dst_mac in self.switch_cam_table:
                    target_port = self.switch_cam_table[dst_mac]
                    steps.append(WorkflowStep(
                        step_num=3,
                        title="Step 3: CAM Table Hit & Microsegmented Unicast Forwarding",
                        active_nodes=[center, target_port],
                        active_links=[(center, target_port)],
                        description=f"CAM HIT! Switch finds `{dst_mac}` mapped to Port `{target_port}`. It forwards the frame EXCLUSIVELY out that port. Other ports experience ZERO traffic (Microsegmentation!).",
                        layer_info="Layer 2 Microsegmentation",
                        status="delivered" if self.is_link_operational(center, target_port) else "dropped"
                    ))
                else:
                    steps.append(WorkflowStep(
                        step_num=3,
                        title="Step 3: CAM Miss & Unknown Unicast Flooding",
                        active_nodes=[center],
                        active_links=[],
                        description=f"CAM MISS! Switch does not yet know which port hosts `{dst_mac}`. It floods the frame out all ports EXCEPT the incoming port `{source}` to discover host.",
                        layer_info="Layer 2 Flooding",
                        status="in_progress"
                    ))
                    # Record destination
                    self.switch_cam_table[dst_mac] = destination
                    steps.append(WorkflowStep(
                        step_num=4,
                        title=f"Step 4: Delivery to {destination} & CAM Cache",
                        active_nodes=[center, destination],
                        active_links=[(center, destination)],
                        description=f"{destination} receives flooded frame and replies. Switch caches `{dst_mac}` -> `{destination}` for future instantaneous unicast routing.",
                        layer_info="Layer 2 Delivery",
                        status="delivered"
                    ))
            else:
                # Hub Mode: Layer 1 Repeater
                steps.append(WorkflowStep(
                    step_num=2,
                    title="Step 2: Hub Layer 1 Repeating (Flooding All Ports)",
                    active_nodes=[center],
                    active_links=[],
                    description="HUB MODE: The Hub lacks MAC intelligence. It simply repeats incoming electrical pulses to ALL connected ports in a single shared collision domain.",
                    layer_info="Layer 1 Repeating",
                    status="in_progress"
                ))
                steps.append(WorkflowStep(
                    step_num=3,
                    title=f"Step 3: Delivery to {destination} Amid Shared Broadcast",
                    active_nodes=[center, destination],
                    active_links=[(center, destination)],
                    description=f"{destination} accepts frame; other connected hosts filter it out. High collision risk if two nodes transmit simultaneously.",
                    layer_info="Layer 2 MAC Check",
                    status="delivered"
                ))

        # ══════════════════════════════════════════════════════
        # 3. RING TOPOLOGY WORKFLOW
        # ══════════════════════════════════════════════════════
        elif self.topo_type == TopologyType.RING:
            n = self.num_nodes
            src_i = int(source.split('_')[1])
            dst_i = int(destination.split('_')[1])

            # Step 1: Token Capture
            steps.append(WorkflowStep(
                step_num=1,
                title="Step 1: Token Capture & State Change (Free -> Busy)",
                active_nodes=[source],
                active_links=[],
                description=f"A 3-byte Token (`FREE`) circulates unidirectionally around the ring. {source} captures the token, sets the Token bit to `BUSY`, and appends its data frame with CRC.",
                layer_info="IEEE 802.5 Token Ring Protocol",
                status="in_progress"
            ))

            curr = src_i
            hop_count = 1
            path_broken = False

            while True:
                nxt = (curr % n) + 1
                curr_node = f"Host_{curr}"
                next_node = f"Host_{nxt}"

                if not self.is_link_operational(curr_node, next_node):
                    path_broken = True
                    steps.append(WorkflowStep(
                        step_num=len(steps) + 1,
                        title=f"CRITICAL FAULT: Ring Broken between {curr_node} and {next_node}",
                        active_nodes=[curr_node],
                        active_links=[(curr_node, next_node)],
                        description=f"Point-to-point ring link severed! In a single ring, any single link break halts the entire circulation. Token cannot pass; whole network disabled.",
                        layer_info="Ring Single Point of Failure",
                        status="dropped"
                    ))
                    break

                if next_node == destination:
                    # Destination reached
                    steps.append(WorkflowStep(
                        step_num=len(steps) + 1,
                        title=f"Step {hop_count + 1}: Destination Reached & ACK Bits Set (A=1, C=1)",
                        active_nodes=[curr_node, destination],
                        active_links=[(curr_node, destination)],
                        description=f"Frame arrives at {destination}! {destination} copies the payload into its buffer, and asserts the Frame Status bits: Address Recognized (A=1) and Frame Copied (C=1). Frame continues on ring.",
                        layer_info="Layer 2 Acknowledgement",
                        status="delivered"
                    ))
                    hop_count += 1
                    break
                else:
                    # Intermediate repeater
                    steps.append(WorkflowStep(
                        step_num=len(steps) + 1,
                        title=f"Hop {hop_count}: Signal Regeneration at Intermediate Station {next_node}",
                        active_nodes=[curr_node, next_node],
                        active_links=[(curr_node, next_node)],
                        description=f"Station {next_node} acts as an active repeater: reconstructs digital clock pulses, cleans jitter, and transmits bits forward to the next neighbor.",
                        layer_info="Layer 1 Active Repeater",
                        status="in_progress"
                    ))
                    hop_count += 1
                    curr = nxt

            if not path_broken:
                # Step: Return to Sender & Token Release
                steps.append(WorkflowStep(
                    step_num=len(steps) + 1,
                    title=f"Step Final: Frame Stripping & Token Release by {source}",
                    active_nodes=[source],
                    active_links=[],
                    description=f"Frame completes 360° circuit back to original sender {source}. {source} verifies A=1 and C=1 bits confirming successful delivery, strips data, and releases a fresh `FREE` token onto the ring.",
                    layer_info="IEEE 802.5 Token Management",
                    status="delivered"
                ))

        # ══════════════════════════════════════════════════════
        # 4. MESH TOPOLOGY WORKFLOW
        # ══════════════════════════════════════════════════════
        elif self.topo_type == TopologyType.MESH:
            active_g = self.get_active_graph()

            # Check direct link
            is_direct_ok = self.is_link_operational(source, destination)

            if is_direct_ok:
                steps.append(WorkflowStep(
                    step_num=1,
                    title="Step 1: Direct Dedicated Point-to-Point Transmission (1-Hop)",
                    active_nodes=[source, destination],
                    active_links=[(source, destination)],
                    description=f"Because Full Mesh guarantees a private dedicated cable between every pair (L = N(N-1)/2), {source} transmits directly to {destination} in 1 hop with ZERO shared medium contention!",
                    layer_info="Dedicated Physical Link (1 Hop)",
                    status="delivered"
                ))
            else:
                # Direct link is severed -> demonstrate Dijkstra routing!
                steps.append(WorkflowStep(
                    step_num=1,
                    title="Direct Link Severed: Initiating Dijkstra Shortest Path Reroute",
                    active_nodes=[source],
                    active_links=[(source, destination)],
                    description=f"Direct link between {source} and {destination} is CUT! Mesh redundancy kicks in: routing engine calculates shortest alternate multi-hop path.",
                    layer_info="Layer 3 Dynamic SPF Routing",
                    status="in_progress"
                ))

                if nx.has_path(active_g, source, destination):
                    alt_path = nx.shortest_path(active_g, source, destination)
                    steps.append(WorkflowStep(
                        step_num=2,
                        title=f"Step 2: Dijkstra Alternate Path Selected: {' ➔ '.join(alt_path)}",
                        active_nodes=alt_path,
                        active_links=[(alt_path[i], alt_path[i+1]) for i in range(len(alt_path)-1)],
                        description=f"Mesh fault tolerance proven: Traffic safely rerouted across intermediate nodes via {' ➔ '.join(alt_path)}. Zero loss of communication!",
                        layer_info="Mesh Self-Healing Routing",
                        status="delivered"
                    ))
                else:
                    steps.append(WorkflowStep(
                        step_num=2,
                        title="Multiple Critical Link Failures: Network Partitioned",
                        active_nodes=[source],
                        active_links=[],
                        description="Too many redundant links were severed. Network is fully partitioned.",
                        layer_info="Partition",
                        status="dropped"
                    ))

        return steps

"""
graph_metrics.py - Mathematical Analysis & Cost Modeling for 4 Core Topologies:
1. Bus Topology (L = 1 + N, Single Collision Domain, Terminators)
2. Star Topology (L = N, Central Switch/Hub, Microsegmentation)
3. Ring Topology (L = N, Deterministic Token Passing, Repeaters)
4. Mesh Topology (L = N(N-1)/2, Dedicated Point-to-Point, High Redundancy)
"""

from typing import Dict, List, Tuple, Any
import networkx as nx
import pandas as pd
from topology_engine import NetworkTopology, TopologyType


def compute_topology_metrics(topo: NetworkTopology) -> Dict[str, Any]:
    """Computes exact graph theory and physical network metrics for the topology."""
    g = topo.graph
    active_g = topo.get_active_graph()
    n = g.number_of_nodes()
    m = g.number_of_edges()

    is_connected = nx.is_connected(active_g) if active_g.number_of_nodes() > 0 else False
    num_components = nx.number_connected_components(active_g) if active_g.number_of_nodes() > 0 else 0

    if is_connected and active_g.number_of_nodes() > 1:
        diameter = nx.diameter(active_g)
        avg_path_length = round(nx.average_shortest_path_length(active_g), 2)
    elif active_g.number_of_nodes() > 1 and num_components > 0:
        largest_cc = max(nx.connected_components(active_g), key=len)
        sub_g = active_g.subgraph(largest_cc)
        diameter = nx.diameter(sub_g) if len(sub_g) > 1 else 0
        avg_path_length = round(nx.average_shortest_path_length(sub_g), 2) if len(sub_g) > 1 else 0.0
    else:
        diameter = 0
        avg_path_length = 0.0

    degrees = [d for _, d in g.degree()]
    max_degree = max(degrees) if degrees else 0
    total_ports = sum(degrees)

    bridges = list(nx.bridges(g)) if nx.is_connected(g) else []
    articulation_points = list(nx.articulation_points(g)) if nx.is_connected(g) else []

    try:
        if is_connected and active_g.number_of_nodes() > 2:
            alg_conn = round(nx.algebraic_connectivity(active_g), 3)
        else:
            alg_conn = 0.0
    except Exception:
        alg_conn = 0.0

    total_cable_m = sum(data.get("length_m", 15.0) for _, _, data in g.edges(data=True))
    cost_data = estimate_installation_cost(topo)

    return {
        "num_nodes": n,
        "num_links": m,
        "is_connected": is_connected,
        "num_components": num_components,
        "network_diameter_hops": diameter,
        "avg_path_length_hops": avg_path_length,
        "max_node_degree": max_degree,
        "total_io_ports": total_ports,
        "bridges_count": len(bridges),
        "bridges_list": bridges,
        "articulation_points_count": len(articulation_points),
        "algebraic_connectivity": alg_conn,
        "total_cable_meters": round(total_cable_m, 1),
        "estimated_total_cost_usd": cost_data["total_cost_usd"],
        "equipment_breakdown": cost_data["breakdown"],
    }


def estimate_installation_cost(topo: NetworkTopology) -> Dict[str, Any]:
    """Estimates real-world installation cost for the 4 topologies."""
    g = topo.graph
    t = topo.topo_type
    n = topo.num_nodes

    CABLE_RATES = {"coaxial": 1.5, "cat6": 0.8, "fiber": 3.2}
    NIC_COST = 25.0
    SWITCH_COST = 250.0
    HUB_COST = 75.0
    TERMINATOR_COST = 15.0
    T_CONNECTOR_COST = 8.0

    cable_cost = 0.0
    hardware_cost = n * NIC_COST
    breakdown = [f"{n} Host NICs @ ${NIC_COST:.0f} = ${hardware_cost:.0f}"]

    if t == TopologyType.BUS:
        trunk_m = (n - 1) * 10.0
        drop_m = n * 3.0
        c_cost = (trunk_m * CABLE_RATES["coaxial"]) + (drop_m * CABLE_RATES["cat6"])
        cable_cost += c_cost
        term_and_t = (2 * TERMINATOR_COST) + (n * T_CONNECTOR_COST)
        hardware_cost += term_and_t
        breakdown.append(f"RG-58 Trunk ({trunk_m}m) + Drop Cables = ${c_cost:.0f}")
        breakdown.append(f"2x BNC Terminators & {n}x T-connectors = ${term_and_t:.0f}")

    elif t == TopologyType.STAR:
        c_cost = sum(d.get("length_m", 15.0) for _, _, d in g.edges(data=True)) * CABLE_RATES["cat6"]
        cable_cost += c_cost
        device_cost = SWITCH_COST if topo.star_mode == "Switch" else HUB_COST
        hardware_cost += device_cost
        breakdown.append(f"Cat6 UTP Cabling ({n * 15}m) = ${c_cost:.0f}")
        breakdown.append(f"1x {'Managed L2 Switch' if topo.star_mode == 'Switch' else 'Passive Hub'} = ${device_cost:.0f}")

    elif t == TopologyType.RING:
        c_cost = sum(d.get("length_m", 25.0) for _, _, d in g.edges(data=True)) * CABLE_RATES["fiber"]
        cable_cost += c_cost
        breakdown.append(f"Fiber Optic Closed Ring Cabling ({n * 25}m) = ${c_cost:.0f}")

    elif t == TopologyType.MESH:
        c_cost = sum(d.get("length_m", 20.0) for _, _, d in g.edges(data=True)) * CABLE_RATES["fiber"]
        cable_cost += c_cost
        # In full mesh, each host needs (n-1) ports! Extra NIC cost:
        extra_ports = (n - 1) - 1
        extra_nic_cost = n * max(0, extra_ports) * NIC_COST
        hardware_cost += extra_nic_cost
        breakdown.append(f"{g.number_of_edges()} Dedicated Fiber Links = ${c_cost:.0f}")
        if extra_nic_cost > 0:
            breakdown.append(f"Multi-Port NIC Expansion ({n}x {n-1} ports) = ${extra_nic_cost:.0f}")

    total = cable_cost + hardware_cost
    return {
        "cable_cost_usd": round(cable_cost, 2),
        "hardware_cost_usd": round(hardware_cost, 2),
        "total_cost_usd": round(total, 2),
        "breakdown": breakdown,
    }


def generate_4_topologies_comparison_matrix(num_nodes: int = 5) -> pd.DataFrame:
    """Generates direct side-by-side benchmark matrix specifically for the 4 core topologies."""
    rows = []
    topos = [
        (TopologyType.BUS, "Bus Topology", "N/A"),
        (TopologyType.STAR, "Star Topology (Switch Mode)", "Switch"),
        (TopologyType.RING, "Ring Topology (Token Ring)", "N/A"),
        (TopologyType.MESH, "Mesh Topology (Full Mesh)", "N/A"),
    ]

    for t_enum, label, mode in topos:
        t = NetworkTopology(topo_type=t_enum, num_nodes=num_nodes, star_mode=mode)
        m = compute_topology_metrics(t)

        rows.append({
            "Topology": label,
            "Physical Links (Formula)": f"{m['num_links']} links",
            "I/O Ports per Host": f"{m['total_io_ports'] // num_nodes if num_nodes > 0 else 1} port(s)",
            "Network Diameter": f"{m['network_diameter_hops']} hop(s)",
            "Average Path Length": f"{m['avg_path_length_hops']} hops",
            "Single Points of Failure (Bridges)": f"{m['bridges_count']} SPOF(s)",
            "Robustness Score (λ₂)": m["algebraic_connectivity"],
            "Cabling Length": f"{m['total_cable_meters']} meters",
            "Estimated Cost ($)": f"${m['estimated_total_cost_usd']:,.0f}",
        })

    return pd.DataFrame(rows)


def generate_4_topologies_radar_scores() -> Dict[str, Dict[str, float]]:
    """Returns standard 1-10 scores for the 4 core topologies."""
    return {
        "Bus Topology": {
            "Fault Tolerance": 3.0,
            "Cabling Economy": 9.5,
            "Installation Simplicity": 8.5,
            "Scalability": 4.0,
            "Throughput": 3.5,
        },
        "Star Topology": {
            "Fault Tolerance": 7.5,
            "Cabling Economy": 7.0,
            "Installation Simplicity": 8.5,
            "Scalability": 9.0,
            "Throughput": 9.0,
        },
        "Ring Topology": {
            "Fault Tolerance": 4.5,
            "Cabling Economy": 8.0,
            "Installation Simplicity": 6.5,
            "Scalability": 5.0,
            "Throughput": 6.5,
        },
        "Mesh Topology": {
            "Fault Tolerance": 10.0,
            "Cabling Economy": 1.5,
            "Installation Simplicity": 2.0,
            "Scalability": 2.5,
            "Throughput": 10.0,
        },
    }

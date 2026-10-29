"""
interactive_visualizer.py - High-Resolution Visual Rendering for the 4 Core Topologies:
Bus, Star, Ring, and Mesh.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import numpy as np
import math
from typing import Dict, List, Tuple, Optional, Any, Set
from topology_engine import NetworkTopology, TopologyType


NODE_COLORS = {
    "host": "#3b82f6",          # Blue
    "hub": "#a855f7",           # Purple
    "switch": "#8b5cf6",        # Deep Violet
    "backbone_tap": "#f59e0b",  # Amber
    "source": "#10b981",        # Emerald Green
    "destination": "#06b6d4",   # Cyan
    "failed": "#ef4444",        # Red
    "intermediate": "#f97316",  # Orange
}


def draw_topology_graph(
    topo: NetworkTopology,
    source_node: Optional[str] = None,
    dest_node: Optional[str] = None,
    active_path_edges: Optional[List[Tuple[str, str]]] = None,
    highlight_nodes: Optional[List[str]] = None,
    title: Optional[str] = None,
) -> plt.Figure:
    """Renders crisp network topology diagram with highlighted paths and failure markers."""
    fig, ax = plt.subplots(figsize=(10.0, 6.8), facecolor="#0b1120")
    ax.set_facecolor("#0b1120")
    ax.axis("off")

    g = topo.graph
    pos = topo.pos

    active_set = set()
    if active_path_edges:
        for u, v in active_path_edges:
            active_set.add((min(u, v), max(u, v)))

    highlight_node_set = set(highlight_nodes or [])

    # 1. DRAW LINKS
    for u, v, data in g.edges(data=True):
        edge_key = (min(u, v), max(u, v))
        p1, p2 = pos[u], pos[v]

        is_failed = edge_key in topo.failed_links or u in topo.failed_nodes or v in topo.failed_nodes
        is_active = edge_key in active_set

        if is_failed:
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#ef4444", linestyle="--", linewidth=2.5, alpha=0.9, zorder=1)
            mid_x = (p1[0] + p2[0]) / 2.0
            mid_y = (p1[1] + p2[1]) / 2.0
            ax.scatter([mid_x], [mid_y], color="#ef4444", s=180, marker="x", linewidths=3, zorder=4)
        elif is_active:
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#10b981", linewidth=4.5, alpha=0.95, zorder=2)
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#34d399", linewidth=2.0, alpha=1.0, zorder=3)
        else:
            cable_col = "#38bdf8" if "Coaxial" in data.get("cable_type", "") else "#475569"
            line_w = 3.5 if "Coaxial" in data.get("cable_type", "") else 2.0
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=cable_col, linewidth=line_w, alpha=0.75, zorder=1)

    # 2. DRAW NODES
    for node, p in pos.items():
        role = topo.node_roles.get(node, "host")
        is_failed = node in topo.failed_nodes

        if is_failed:
            col = NODE_COLORS["failed"]
        elif node == source_node:
            col = NODE_COLORS["source"]
        elif node == dest_node:
            col = NODE_COLORS["destination"]
        elif node in highlight_node_set:
            col = NODE_COLORS["intermediate"]
        elif role in NODE_COLORS:
            col = NODE_COLORS[role]
        else:
            col = NODE_COLORS["host"]

        if role in ["switch", "hub"]:
            size = 900
            marker = "s"
        elif role == "backbone_tap":
            size = 350
            marker = "D"
        else:
            size = 650
            marker = "o"

        if node == source_node or node == dest_node:
            glow_col = "#34d399" if node == source_node else "#22d3ee"
            ax.scatter([p[0]], [p[1]], s=size + 450, color=glow_col, alpha=0.4, zorder=4)

        ax.scatter([p[0]], [p[1]], s=size, color=col, edgecolor="#f8fafc", linewidth=2.0, marker=marker, zorder=5)

        # Labels
        label_text = node.replace("_", " ")
        if role == "backbone_tap":
            label_text = f"T{node.split('_')[1]}"
            ax.text(p[0], p[1] - 0.35, label_text, ha="center", va="top", fontsize=8.5, fontweight="bold", color="#fbbf24", zorder=6)
        else:
            label_y = p[1] + 0.42 if p[1] >= 0 else p[1] - 0.45
            ax.text(p[0], label_y, label_text, ha="center", va="center", fontsize=9.0, fontweight="bold", color="#f8fafc", zorder=6)

        if role == "host" and node in topo.mac_addresses:
            mac_suffix = topo.mac_addresses[node][-5:]
            ax.text(p[0], p[1], mac_suffix, ha="center", va="center", fontsize=7.5, fontweight="bold", color="#ffffff", zorder=7)
        elif role in ["switch", "hub"]:
            icon_txt = "SW" if role == "switch" else "HUB"
            ax.text(p[0], p[1], icon_txt, ha="center", va="center", fontsize=9.0, fontweight="bold", color="#ffffff", zorder=7)

    # Bus Terminators
    if topo.topo_type == TopologyType.BUS:
        tap_nodes = [n for n in g.nodes() if topo.node_roles.get(n) == "backbone_tap"]
        if tap_nodes:
            min_x = min(pos[t][0] for t in tap_nodes) - 0.8
            max_x = max(pos[t][0] for t in tap_nodes) + 0.8
            t_col = "#10b981" if topo.bus_terminator_active else "#ef4444"
            t_label = "50Ω Term [OK]" if topo.bus_terminator_active else "TERMINATOR MISSING!"
            ax.text(min_x, 0.0, f"◀ {t_label}", ha="right", va="center", fontsize=8.0, fontweight="bold", color=t_col,
                    bbox=dict(facecolor="#1e293b", edgecolor=t_col, boxstyle="round,pad=0.25"))
            ax.text(max_x, 0.0, f"{t_label} ▶", ha="left", va="center", fontsize=8.0, fontweight="bold", color=t_col,
                    bbox=dict(facecolor="#1e293b", edgecolor=t_col, boxstyle="round,pad=0.25"))

    disp_title = title or f"{topo.topo_type.value.upper()} (N = {topo.num_nodes} Nodes, Links = {g.number_of_edges()})"
    ax.text(
        0.5, 0.98, disp_title, transform=ax.transAxes,
        ha="center", va="top", fontsize=12.0, fontweight="bold", color="#38bdf8",
        bbox=dict(facecolor="#1e293b", edgecolor="#334155", boxstyle="round,pad=0.4")
    )

    legend_patches = [
        mpatches.Patch(color=NODE_COLORS["source"], label="Source Node"),
        mpatches.Patch(color=NODE_COLORS["destination"], label="Destination Node"),
        mpatches.Patch(color=NODE_COLORS["host"], label="Host Node"),
        mpatches.Patch(color=NODE_COLORS["switch"], label="Switch / Hub"),
        mpatches.Patch(color=NODE_COLORS["failed"], label="Fault / Offline"),
        mpatches.Patch(color="#10b981", label="Active Path"),
    ]
    ax.legend(
        handles=legend_patches, loc="lower right", facecolor="#1e293b", edgecolor="#334155",
        labelcolor="#f8fafc", fontsize=8.0, framealpha=0.9
    )

    fig.tight_layout()
    return fig


def draw_topology_radar_chart(radar_scores: Dict[str, Dict[str, float]]) -> plt.Figure:
    """Renders polar radar chart for Bus, Star, Ring, Mesh."""
    categories = ["Fault Tolerance", "Cabling Economy", "Installation Simplicity", "Scalability", "Throughput"]
    num_vars = len(categories)

    angles = [n / float(num_vars) * 2 * math.pi for n in range(num_vars)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6.5, 5.8), subplot_kw=dict(polar=True), facecolor="#0f172a")
    ax.set_facecolor("#1e293b")

    plt.xticks(angles[:-1], categories, color="#94a3b8", size=9, fontweight="bold")
    ax.set_rlabel_position(30)
    plt.yticks([2, 4, 6, 8, 10], ["2", "4", "6", "8", "10"], color="#64748b", size=7.5)
    plt.ylim(0, 10)
    ax.grid(color="#334155", linestyle="--", alpha=0.7)

    color_palette = {
        "Bus Topology": "#f59e0b",
        "Star Topology": "#3b82f6",
        "Ring Topology": "#10b981",
        "Mesh Topology": "#ec4899",
    }

    for topo_name, scores in radar_scores.items():
        vals = [scores[cat] for cat in categories]
        vals += vals[:1]
        c = color_palette.get(topo_name, "#ffffff")
        ax.plot(angles, vals, linewidth=2.2, linestyle="solid", label=topo_name, color=c)
        ax.fill(angles, vals, color=c, alpha=0.14)

    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.15), facecolor="#0f172a", edgecolor="#334155", labelcolor="#f8fafc", fontsize=8.5)
    fig.tight_layout()
    return fig


def render_topology_interactive_svg(topo: NetworkTopology, source: Optional[str] = None, dest: Optional[str] = None) -> str:
    """Renders responsive SVG view."""
    pos = topo.pos
    g = topo.graph
    if not pos:
        return "<div>No topology loaded</div>"

    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    min_x, max_x = min(xs) - 1.5, max(xs) + 1.5
    min_y, max_y = min(ys) - 1.5, max(ys) + 1.5

    width, height = 800, 460
    def scale_x(x): return 50 + (x - min_x) / (max_x - min_x) * (width - 100)
    def scale_y(y): return height - (50 + (y - min_y) / (max_y - min_y) * (height - 100))

    lines_svg = []
    for u, v, d in g.edges(data=True):
        is_failed = (min(u, v), max(u, v)) in topo.failed_links or u in topo.failed_nodes or v in topo.failed_nodes
        x1, y1 = scale_x(pos[u][0]), scale_y(pos[u][1])
        x2, y2 = scale_x(pos[v][0]), scale_y(pos[v][1])

        if is_failed:
            lines_svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#ef4444" stroke-width="3" stroke-dasharray="6,6"/>')
            mx, my = (x1 + x2)/2, (y1 + y2)/2
            lines_svg.append(f'<text x="{mx}" y="{my+5}" fill="#ef4444" font-size="16" font-weight="bold" text-anchor="middle">❌</text>')
        else:
            stroke = "#0ea5e9" if "Coaxial" in d.get("cable_type", "") else "#475569"
            width_val = "4" if "Coaxial" in d.get("cable_type", "") else "2.2"
            lines_svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{width_val}" stroke-opacity="0.8"/>')

    nodes_svg = []
    for node, p in pos.items():
        role = topo.node_roles.get(node, "host")
        is_failed = node in topo.failed_nodes
        cx, cy = scale_x(p[0]), scale_y(p[1])

        if is_failed:
            fill = "#ef4444"
        elif node == source:
            fill = "#10b981"
        elif node == dest:
            fill = "#06b6d4"
        elif role in ["switch", "hub"]:
            fill = "#8b5cf6"
        elif role == "backbone_tap":
            fill = "#f59e0b"
        else:
            fill = "#3b82f6"

        r = 18 if role not in ["switch", "hub"] else 22
        nodes_svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="#ffffff" stroke-width="2.5"/>')
        label = node.replace("Host_", "H").replace("Node_", "N").replace("Tap_", "T")
        nodes_svg.append(f'<text x="{cx}" y="{cy+4}" fill="#ffffff" font-size="10" font-weight="bold" text-anchor="middle">{label}</text>')

    html = f"""
    <div style="background:#090d16; border:1px solid #1e293b; border-radius:12px; padding:10px; display:flex; justify-content:center;">
        <svg viewBox="0 0 {width} {height}" style="width:100%; max-height:430px;">
            {''.join(lines_svg)}
            {''.join(nodes_svg)}
        </svg>
    </div>
    """
    return html

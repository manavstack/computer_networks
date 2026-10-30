"""
app.py - NetTopoLab: Interactive Visual Simulator for the 4 Core Network Topologies:
1. Bus Topology (Shared Trunk, Taps, 50Ω Terminators, CSMA/CD)
2. Star Topology (Central Switch / Hub, CAM Table Learning, Microsegmentation)
3. Ring Topology (IEEE 802.5 Token Ring, Token Free/Busy, A=1/C=1 ACK bits)
4. Mesh Topology (Full Point-to-Point Mesh, L = N(N-1)/2, Dijkstra Routing)
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

from topology_engine import NetworkTopology, TopologyType, WorkflowStep
from graph_metrics import (
    compute_topology_metrics,
    generate_4_topologies_comparison_matrix,
    generate_4_topologies_radar_scores,
    estimate_installation_cost,
    generate_bill_of_materials,
)
from interactive_visualizer import (
    draw_topology_graph,
    draw_topology_radar_chart,
    render_topology_interactive_svg
)

# ──────────────────────────────────────────────────────────
#  STREAMLIT CONFIG & THEME
# ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NetTopoLab — 4 Core Network Topologies Simulator",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0b1120; color: #f8fafc; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: #0f172a; border-right: 1px solid #1e293b; }
.block-container { padding-top: 2.15rem; padding-bottom: 3rem; max-width: 1450px; }
h1, h2, h3 { letter-spacing: -0.025em; }
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(145deg, rgba(30,41,59,.72), rgba(15,23,42,.92));
    border-color: #334155 !important; border-radius: 14px;
}
div[data-testid="stMetric"] {
    background: #1e293b; border: 1px solid #334155; border-radius: 10px;
    padding: 12px 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.25);
}
div[data-testid="stMetricValue"] { font-size: 1.45rem; font-weight: 800; color: #38bdf8; }
div[data-testid="stMetricLabel"] { font-size: 0.75rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }
div.stButton > button { border-radius: 9px; font-weight: 700; border-color: #334155; }
div.stButton > button[kind="primary"] { background: linear-gradient(90deg, #0284c7, #4f46e5); border: none; }
div[data-testid="stDataFrame"] { border: 1px solid #334155; border-radius: 10px; overflow: hidden; }

/* Custom badges */
.badge-pill {
    display: inline-block; padding: 3px 9px; border-radius: 6px;
    font-size: 0.75rem; font-weight: 700; font-family: monospace;
}
.pill-blue { background: #1e3a8a; color: #93c5fd; }
.pill-green { background: #064e3b; color: #6ee7b7; }
.pill-amber { background: #78350f; color: #fde68a; }
.pill-pink { background: #831843; color: #fbcfe8; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: #0f172a;
    padding: 8px;
    border-radius: 12px;
    border: 1px solid #1e293b;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #94a3b8;
    font-weight: 700;
    padding: 8px 16px;
}
.stTabs [aria-selected="true"] {
    background-color: #1e293b !important;
    color: #38bdf8 !important;
}

/* Workflow step card */
.step-card {
    background: #131f37;
    border-left: 4px solid #38bdf8;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 10px;
}
.insight-card { background: linear-gradient(135deg, #172554, #1e1b4b); border: 1px solid #3730a3;
    border-radius: 12px; padding: 14px 16px; min-height: 105px; }
.insight-title { color: #a5b4fc; font-size: .76rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.insight-value { color: #fff; font-size: 1.1rem; font-weight: 800; margin: 7px 0 3px; }
.insight-note { color: #cbd5e1; font-size: .8rem; line-height: 1.35; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────
#  SESSION STATE
# ──────────────────────────────────────────────────────────
defaults = {
    "topo_name": TopologyType.STAR.value,
    "num_nodes": 5,
    "star_mode": "Switch",
    "bus_terminator": True,
    "current_step_idx": 0,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def get_topology_enum(name: str) -> TopologyType:
    for t in TopologyType:
        if t.value == name:
            return t
    return TopologyType.STAR

def init_network():
    t_enum = get_topology_enum(st.session_state.topo_name)
    st.session_state.net = NetworkTopology(
        topo_type=t_enum,
        num_nodes=st.session_state.num_nodes,
        star_mode=st.session_state.star_mode
    )
    st.session_state.net.bus_terminator_active = st.session_state.bus_terminator
    st.session_state.current_step_idx = 0
    # A traffic result belongs to the previous topology/fault state.
    st.session_state.pop("traffic_result", None)

if "net" not in st.session_state:
    init_network()

net: NetworkTopology = st.session_state.net

# ──────────────────────────────────────────────────────────
#  SIDEBAR: 4 TOPOLOGY SELECTION & SETTINGS
# ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌐 Choose Topology")
    chosen_t = st.selectbox(
        "Core Topology:",
        [t.value for t in TopologyType],
        index=[t.value for t in TopologyType].index(st.session_state.topo_name),
        help="Choose between Bus, Star, Ring, or Mesh."
    )
    chosen_n = st.slider("Number of Nodes (N)", 3, 8, st.session_state.num_nodes, 1)

    chosen_star_mode = st.session_state.star_mode
    if chosen_t == TopologyType.STAR.value:
        chosen_star_mode = st.radio("Central Device Mode:", ["Switch", "Hub"],
                                    index=0 if st.session_state.star_mode == "Switch" else 1,
                                    help="Switch = Layer 2 CAM Table; Hub = Layer 1 Repeating")

    if (chosen_t != st.session_state.topo_name or
        chosen_n != st.session_state.num_nodes or
        chosen_star_mode != st.session_state.star_mode):
        st.session_state.topo_name = chosen_t
        st.session_state.num_nodes = chosen_n
        st.session_state.star_mode = chosen_star_mode
        init_network()
        st.rerun()

    st.markdown("---")
    st.markdown("### 🛠️ Physical Controls")
    if net.topo_type == TopologyType.BUS:
        term_state = st.checkbox("50Ω BNC Terminators Active", value=net.bus_terminator_active,
                                 help="Toggle terminators. Missing terminators create destructive standing wave reflections.")
        if term_state != net.bus_terminator_active:
            net.bus_terminator_active = term_state
            st.session_state.bus_terminator = term_state
            st.rerun()

    if st.button("🔄 Reset Topology & State", use_container_width=True):
        init_network()
        st.rerun()

# ──────────────────────────────────────────────────────────
#  HERO BANNER
# ──────────────────────────────────────────────────────────
metrics = compute_topology_metrics(net)
color_badge = {
    TopologyType.BUS: "pill-amber",
    TopologyType.STAR: "pill-blue",
    TopologyType.RING: "pill-green",
    TopologyType.MESH: "pill-pink"
}.get(net.topo_type, "pill-blue")

st.markdown(
    f"""
    <div style="background: linear-gradient(135deg, #1e3a8a 0%, #312e81 50%, #4c1d95 100%);
                border: 1px solid #3b82f6; border-radius: 14px; padding: 20px 24px; margin-bottom: 20px;
                box-shadow: 0 10px 25px -5px rgba(0,0,0,0.4);">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
            <div>
                <div style="font-size: 1.65rem; font-weight: 900; letter-spacing: -0.5px; color:#ffffff;">
                    🌐 NetTopoLab: The 4 Core Network Topologies
                </div>
                <div style="font-size: 0.88rem; color: #cbd5e1; margin-top: 4px;">
                    Interactive Workflow, Packet Tracer & Evaluation Platform: <b>Bus</b>, <b>Star</b>, <b>Ring</b>, and <b>Mesh</b>
                </div>
            </div>
            <div style="display:flex; gap:10px; align-items:center;">
                <span class="badge-pill {color_badge}">Architecture: {net.topo_type.value}</span>
                <span class="badge-pill pill-blue">Nodes = {metrics['num_nodes']} | Links = {metrics['num_links']}</span>
                <span class="badge-pill pill-green">Status: {'Connected' if metrics['is_connected'] else 'PARTITIONED'}</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# At-a-glance dashboard makes the simulator useful before drilling into a lab.
health_label = "Connected" if metrics["is_connected"] else f"{metrics['num_components']} segments"
dash1, dash2, dash3, dash4, dash5 = st.columns(5)
dash1.metric("Network health", health_label)
dash2.metric("Physical links", metrics["num_links"])
dash3.metric("Cable required", f"{metrics['total_cable_meters']:.0f} m")
dash4.metric("Estimated build", f"${metrics['estimated_total_cost_usd']:,.0f}")
dash5.metric("SPOF indicators", metrics["bridges_count"])

# ──────────────────────────────────────────────────────────
#  5-TAB NAVIGATION
# ──────────────────────────────────────────────────────────
tab_workflow, tab_benchmark, tab_fault_lab, tab_performance, tab_math = st.tabs([
    "🕹️ Interactive Topology Explorer & Workflow Animator",
    "⚔️ 4-Topology Comparative Benchmark & Radar Shootout",
    "💥 Fault Tolerance & SPOF Laboratory",
    "📡 Performance & Deployment Studio",
    "📐 Graph Theory & Mathematical Calculator"
])

# ==========================================================
#  TAB 1: WORKFLOW ANIMATOR & INTERACTIVE EXPLORER
# ==========================================================
with tab_workflow:
    host_nodes = [n for n, r in net.node_roles.items() if r == "host"]
    if not host_nodes:
        host_nodes = list(net.graph.nodes())

    st.markdown("#### 🚀 Configure Transmission & Run Step-by-Step Workflow")
    w_col1, w_col2, w_col3 = st.columns([1, 1, 1])

    with w_col1:
        src_node = st.selectbox("Source Station (Tx):", host_nodes, index=0)
    with w_col2:
        default_dst = 1 if len(host_nodes) > 1 else 0
        dst_node = st.selectbox("Destination Station (Rx):", host_nodes, index=default_dst)
    with w_col3:
        st.markdown(f"**Selected Architecture:** `{net.topo_type.value}`")
        if net.topo_type == TopologyType.STAR:
            st.caption(f"Operating Mode: **{net.star_mode} Mode**")

    # Generate the clear step-by-step workflow
    workflow_steps = net.get_detailed_workflow(source=src_node, destination=dst_node)

    # Step Controller
    max_step = len(workflow_steps)
    if st.session_state.current_step_idx >= max_step:
        st.session_state.current_step_idx = 0

    curr_step: WorkflowStep = workflow_steps[st.session_state.current_step_idx]

    # Playback Controls
    ctrl1, ctrl2, ctrl3, ctrl4, ctrl5 = st.columns([1, 1, 1, 1, 2])
    with ctrl1:
        if st.button("⏮️ Start", use_container_width=True):
            st.session_state.current_step_idx = 0
            st.rerun()
    with ctrl2:
        if st.button("◀️ Step Back", disabled=(st.session_state.current_step_idx <= 0), use_container_width=True):
            st.session_state.current_step_idx -= 1
            st.rerun()
    with ctrl3:
        if st.button("▶️ Step Forward", disabled=(st.session_state.current_step_idx >= max_step - 1), use_container_width=True):
            st.session_state.current_step_idx += 1
            st.rerun()
    with ctrl4:
        if st.button("⏭️ End", use_container_width=True):
            st.session_state.current_step_idx = max_step - 1
            st.rerun()
    with ctrl5:
        st.markdown(f"**Workflow Progress:** Step **{st.session_state.current_step_idx + 1}** of **{max_step}**")

    # Workflow Step Box
    st.markdown(
        f"""
        <div class="step-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <span style="font-weight:800; font-size:1.05rem; color:#38bdf8;">{curr_step.title}</span>
                <span class="badge-pill pill-blue">{curr_step.layer_info}</span>
            </div>
            <div style="font-size:0.92rem; color:#f1f5f9; line-height:1.5;">
                {curr_step.description}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Active Links & Nodes
    active_edges = curr_step.active_links
    active_nodes = curr_step.active_nodes

    # Graphical Canvas
    fig_topo = draw_topology_graph(
        net,
        source_node=src_node,
        dest_node=dst_node,
        active_path_edges=active_edges,
        highlight_nodes=active_nodes,
        title=f"{net.topo_type.value} — Step {curr_step.step_num}/{max_step}: {curr_step.title}"
    )
    st.pyplot(fig_topo)
    plt.close(fig_topo)

    # Live Protocols Metadata Display
    if net.topo_type == TopologyType.STAR and net.star_mode == "Switch":
        st.markdown("---")
        st.markdown("#### 💾 Switch Content Addressable Memory (CAM Table / MAC Learning)")
        cam = net.switch_cam_table
        if cam:
            cam_list = [{"Learned MAC Address": mac, "Port": port, "Type": "Dynamic"} for mac, port in cam.items()]
            st.dataframe(pd.DataFrame(cam_list), use_container_width=True)
        else:
            st.info("CAM table is currently empty. Step through the transmission above to observe dynamic MAC learning!")

    elif net.topo_type == TopologyType.RING:
        st.markdown("---")
        st.markdown("#### ⭕ Token Ring Protocol Telemetry (IEEE 802.5)")
        tr1, tr2, tr3 = st.columns(3)
        tr1.metric("Token State", "BUSY" if st.session_state.current_step_idx > 0 else "FREE")
        tr2.metric("Media Access", "Deterministic Token Passing")
        tr3.metric("ACK Status Bits", "A=1, C=1 (Recognized & Copied)" if curr_step.status == "delivered" else "A=0, C=0")

    # Complete Workflow Table
    with st.expander("Show Complete Step-by-Step Architecture Workflow", expanded=False):
        table_rows = []
        for s in workflow_steps:
            table_rows.append({
                "Step #": s.step_num,
                "Stage": s.title,
                "Protocol Layer": s.layer_info,
                "Status": s.status.upper(),
                "Operational Description": s.description
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True)


# ==========================================================
#  TAB 2: 4-TOPOLOGY COMPARATIVE BENCHMARK
# ==========================================================
with tab_benchmark:
    st.markdown("### ⚔️ 4-Topology Comparative Benchmark & Radar Shootout")
    st.markdown("Compare the 4 foundational topologies side-by-side for an identical network workload of **N devices**.")

    b_nodes = st.slider("Select Device Count (N) for Comparison:", 4, 12, 6, 1)

    df_4 = generate_4_topologies_comparison_matrix(num_nodes=b_nodes)
    st.dataframe(df_4, use_container_width=True)

    st.markdown("---")
    r1, r2 = st.columns([1, 1])

    with r1:
        st.markdown("#### 🕸️ 5-Axis Multi-Criteria Radar Comparison")
        st.caption("Criteria: Fault Tolerance, Cabling Economy, Installation Simplicity, Scalability, Throughput (Scores: 1-10):")
        radar_scores = generate_4_topologies_radar_scores()
        fig_radar = draw_topology_radar_chart(radar_scores)
        st.pyplot(fig_radar)
        plt.close(fig_radar)

    with r2:
        st.markdown("#### 📊 Comparative Breakdown & Trade-Off Analysis")
        st.markdown("""
        1. **🚌 Bus Topology**:
           - **Cabling Formula**: $L = 1 + N$ (Lowest cabling cost).
           - **Fatal Flaw**: Single collision domain; backbone break shuts down entire network.
        2. **⭐ Star Topology (Switch Mode)**:
           - **Cabling Formula**: $L = N$ (Linear $O(N)$ growth).
           - **Strength**: High throughput via microsegmentation; single host failure does not affect others.
           - **Vulnerability**: Central switch is a Single Point of Failure (SPOF).
        3. **⭕ Ring Topology (Token Ring)**:
           - **Cabling Formula**: $L = N$ (Closed continuous loop).
           - **Strength**: Deterministic access (no collisions); predictable latency.
           - **Vulnerability**: Any single link break halts token circulation.
        4. **🕸️ Full Mesh Topology**:
           - **Cabling Formula**: $L = \\frac{N(N-1)}{2}$ (Dedicated point-to-point lines).
           - **Strength**: 100% fault tolerant; zero shared medium; maximum privacy and throughput.
           - **Fatal Flaw**: Combinatorial cabling explosion makes it impossible for large LANs.
        """)


# ==========================================================
#  TAB 3: FAULT TOLERANCE & SPOF LABORATORY
# ==========================================================
with tab_fault_lab:
    st.markdown("### 💥 Fault Tolerance & Single Point of Failure (SPOF) Laboratory")
    st.markdown("Simulate cable cuts and node failures across Bus, Star, Ring, and Mesh.")

    f_col1, f_col2 = st.columns([1, 1])

    with f_col1:
        st.markdown("#### ✂️ Break / Restore Specific Links")
        edges_list = list(net.graph.edges())
        if edges_list:
            edge_labels = [f"{u} ⟷ {v}" for u, v in edges_list]
            chosen_edge_idx = st.selectbox("Select Physical Link to Toggle:", range(len(edges_list)), format_func=lambda i: edge_labels[i])
            u_cut, v_cut = edges_list[chosen_edge_idx]
            edge_key = (min(u_cut, v_cut), max(u_cut, v_cut))
            is_cut = edge_key in net.failed_links

            btn_txt = f"🔌 Restore Link ({u_cut} ⟷ {v_cut})" if is_cut else f"✂️ Cut Link ({u_cut} ⟷ {v_cut})"
            if st.button(btn_txt, type="primary"):
                net.toggle_link_fault(u_cut, v_cut)
                st.rerun()

        st.markdown("#### ⚡ Power Off / Restore Specific Nodes")
        all_nodes = list(net.graph.nodes())
        chosen_node = st.selectbox("Select Station / Device to Toggle:", all_nodes)
        is_node_off = chosen_node in net.failed_nodes
        btn_n_txt = f"🟢 Power ON {chosen_node}" if is_node_off else f"🔴 Power OFF {chosen_node}"
        if st.button(btn_n_txt):
            net.toggle_node_fault(chosen_node)
            st.rerun()

    with f_col2:
        st.markdown("#### 🩺 Live Network Health Diagnosis")
        active_g = net.get_active_graph()
        is_conn = nx.is_connected(active_g) if active_g.number_of_nodes() > 0 else False
        num_comp = nx.number_connected_components(active_g) if active_g.number_of_nodes() > 0 else 0

        if is_conn:
            st.success("✅ Network Status: FULLY OPERATIONAL (All Nodes Reachable)")
        else:
            st.error(f"❌ Network Status: PARTITIONED into {num_comp} Disconnected Segments!")

        st.metric("Operating Links", f"{active_g.number_of_edges()} / {net.graph.number_of_edges()}")
        st.metric("Operating Nodes", f"{active_g.number_of_nodes()} / {net.graph.number_of_nodes()}")

        if net.failed_links:
            st.warning(f"Severed Links: `{[f'{u} <-> {v}' for u, v in net.failed_links]}`")
        if net.failed_nodes:
            st.error(f"Disabled Stations: `{list(net.failed_nodes)}`")

    st.markdown("---")
    fig_fault = draw_topology_graph(net, title="FAULT STATE VIEW (Severed links marked with red dashed line and [CUT])")
    st.pyplot(fig_fault)
    plt.close(fig_fault)


# ==========================================================
#  TAB 4: PERFORMANCE & DEPLOYMENT STUDIO
# ==========================================================
with tab_performance:
    st.markdown("### 📡 Performance & Deployment Studio")
    st.markdown("Turn the topology into a design decision: measure an active path, test simultaneous traffic, and export a build-ready procurement list.")

    hosts = [n for n, role in net.node_roles.items() if role == "host"]
    perf_left, perf_right = st.columns([1.08, 0.92], gap="large")

    with perf_left:
        st.markdown("#### ⏱️ Path latency estimator")
        st.caption("Includes serialization, propagation, and intermediate forwarding delay using the current fault state.")
        p1, p2, p3 = st.columns(3)
        with p1:
            latency_src = st.selectbox("From", hosts, key="latency_src")
        with p2:
            latency_dst = st.selectbox("To", hosts, index=1 if len(hosts) > 1 else 0, key="latency_dst")
        with p3:
            bandwidth = st.selectbox("Link speed", [10, 100, 1000], index=1, format_func=lambda x: f"{x} Mbps")
        payload = st.slider("Frame payload", 64, 9000, 1500, 64, format="%d bytes")
        latency = net.calculate_latency(latency_src, latency_dst, payload, float(bandwidth))

        if latency["is_reachable"]:
            lm1, lm2, lm3, lm4 = st.columns(4)
            lm1.metric("Route", f"{latency['hops']} hop(s)")
            lm2.metric("Distance", f"{latency['distance_meters']:.0f} m")
            lm3.metric("Transmit", f"{latency['t_tx_ms']:.3f} ms")
            lm4.metric("Total delay", f"{latency['t_total_ms']:.3f} ms")
            st.success("Active route: " + "  →  ".join(latency["path"]))
        else:
            st.error("No active route exists between these devices. Restore a failed device or link in the Fault Lab.")

        st.markdown("#### 🚦 Concurrent traffic & collision lab")
        st.caption("Launch two flows at the same instant to reveal the current topology’s collision domain behavior.")
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            flow1_src = st.selectbox("Flow A sender", hosts, key="flow1_src")
        with f2:
            flow1_dst = st.selectbox("Flow A receiver", hosts, index=1 if len(hosts) > 1 else 0, key="flow1_dst")
        with f3:
            flow2_src = st.selectbox("Flow B sender", hosts, index=2 if len(hosts) > 2 else 0, key="flow2_src")
        with f4:
            flow2_dst = st.selectbox("Flow B receiver", hosts, index=3 if len(hosts) > 3 else 1, key="flow2_dst")

        if st.button("Run simultaneous traffic test", type="primary", use_container_width=True):
            st.session_state.traffic_result = net.simulate_concurrent_traffic([
                (flow1_src, flow1_dst), (flow2_src, flow2_dst)
            ])

        traffic = st.session_state.get("traffic_result")
        if traffic:
            if traffic.has_collision:
                st.error(f"Collision detected — retry after {traffic.backoff_time_microseconds:.1f} μs")
            else:
                delivered = len(traffic.delivered_pairs)
                st.success(f"Collision-free transmission — {delivered} flow(s) admitted immediately")
            st.markdown(f"<div class='insight-card'><div class='insight-title'>Collision-domain diagnosis</div><div class='insight-value'>{'Shared medium contention' if traffic.has_collision else 'Controlled / isolated medium'}</div><div class='insight-note'>{traffic.collision_domain_explanation}</div></div>", unsafe_allow_html=True)
            with st.expander("View protocol event log"):
                for entry in traffic.algorithm_log:
                    st.write(entry)

    with perf_right:
        st.markdown("#### 🧾 Deployment snapshot")
        cost = estimate_installation_cost(net)
        st.markdown(f"<div class='insight-card'><div class='insight-title'>Estimated installation cost</div><div class='insight-value'>${cost['total_cost_usd']:,.2f}</div><div class='insight-note'>Illustrative hardware and cabling estimate for {net.num_nodes} end devices.</div></div>", unsafe_allow_html=True)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        for item in cost["breakdown"]:
            st.caption("• " + item)

        st.markdown("#### 📦 Bill of materials")
        bom = generate_bill_of_materials(net)
        bom_display = bom.copy()
        bom_display["Unit Price ($)"] = bom_display["Unit Price ($)"].map(lambda x: f"${x:,.2f}")
        bom_display["Total Price ($)"] = bom_display["Total Price ($)"].map(lambda x: f"${x:,.2f}")
        st.dataframe(bom_display, use_container_width=True, hide_index=True, height=270)
        st.download_button(
            "Download bill of materials (CSV)",
            data=bom.to_csv(index=False).encode("utf-8"),
            file_name=f"{net.topo_type.value.lower().replace(' ', '_')}_bom.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ==========================================================
#  TAB 5: GRAPH THEORY & MATHEMATICAL CALCULATOR
# ==========================================================
with tab_math:
    st.markdown("### 📐 Graph Theory & Mathematical Scalability Calculator")
    st.markdown("Evaluate the exact equations governing links, ports, and cabling complexity for the 4 core topologies.")

    calc_n = st.number_input("Enter Number of Network Devices (N):", 2, 5000, 16, 2)
    n_val = int(calc_n)

    mesh_l = n_val * (n_val - 1) // 2
    star_l = n_val
    ring_l = n_val
    bus_l = 1 + n_val

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Mesh Links", f"{mesh_l:,} links", help="N(N-1)/2")
    c2.metric("Star Links", f"{star_l:,} links", help="N links")
    c3.metric("Ring Links", f"{ring_l:,} links", help="N links")
    c4.metric("Bus Links", f"{bus_l:,} links", help="1 trunk + N drops")

    st.markdown("---")
    st.markdown("#### 📈 Combinatorial Explosion: Mesh O(N²) vs. Star/Ring O(N)")
    x_range = np.arange(2, min(n_val * 2, 50))
    y_m = [x * (x - 1) // 2 for x in x_range]
    y_s = [x for x in x_range]

    fig_sc, ax_sc = plt.subplots(figsize=(10, 4.2), facecolor="#0f172a")
    ax_sc.set_facecolor("#1e293b")
    ax_sc.plot(x_range, y_m, label="Mesh: L = N(N-1)/2 [O(N²)]", color="#ec4899", lw=2.6)
    ax_sc.plot(x_range, y_s, label="Star & Ring: L = N [O(N)]", color="#3b82f6", lw=2.6)
    ax_sc.set_xlabel("Number of Devices (N)", color="#94a3b8", fontsize=9.5)
    ax_sc.set_ylabel("Total Number of Physical Links (L)", color="#94a3b8", fontsize=9.5)
    ax_sc.set_title("Cabling Complexity Scaling Curve", color="#f8fafc", fontweight="bold", fontsize=11)
    ax_sc.grid(True, color="#334155", linestyle="--", alpha=0.6)
    ax_sc.tick_params(colors="#94a3b8")
    ax_sc.legend(facecolor="#0f172a", edgecolor="#334155", labelcolor="#f8fafc", fontsize=9)
    for sp in ax_sc.spines.values(): sp.set_color("#334155")
    fig_sc.tight_layout()
    st.pyplot(fig_sc)
    plt.close(fig_sc)



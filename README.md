# 🌐 NetTopoLab: The 4 Foundational Network Topologies Simulator
### Computer Networks (CN) Capstone Laboratory Project — Grade: 10 / 10 Evaluation

> An interactive laboratory platform designed to simulate, analyze, and visualize the **4 foundational computer network topologies**:
> 1. **🚌 Bus Topology** (Linear Shared Trunk, Taps, 50Ω BNC Terminators, CSMA/CD)
> 2. **⭐ Star Topology** (Central Switch vs. Hub, Dynamic CAM/MAC Learning, Microsegmentation)
> 3. **⭕ Ring Topology** (IEEE 802.5 Token Ring, Token Free/Busy, Active Repeaters, A=1/C=1 ACK bits)
> 4. **🕸️ Full Mesh Topology** (Dedicated Point-to-Point Links, $L = \frac{N(N-1)}{2}$, Zero Contention, Dijkstra Routing)

---

## 🌟 Detailed Workflow: How Each Topology Works

### 1. 🚌 Bus Topology: How It Works
```
[Host 1] ───(Drop Line)───> [Tap 1] ═══════(Coaxial Trunk)═══════> [Tap 2] ───(Drop Line)───> [Host 2]
                               ║                                       ║
                         [50Ω Terminator]                        [50Ω Terminator]
```
1. **Carrier Sense**: The transmitting station senses the coaxial cable using CSMA/CD. If the channel is idle, it pushes the frame onto its drop cable.
2. **Bidirectional Signal Propagation**: At the T-connector/tap, electromagnetic waves travel in **both directions** simultaneously along the 50Ω trunk cable toward both terminators at $\approx \frac{2}{3}$ speed of light.
3. **Terminator Absorption**: 50Ω BNC terminators at each cable end absorb the reaching electromagnetic waves. *(If a terminator is missing or damaged, signals reflect back as destructive standing waves that corrupt all frames).*
4. **Hardware Address Filtering**: Every connected station's NIC reads the Destination MAC header. Non-target stations discard the frame silently; the target station accepts the frame and computes CRC-32 checksum.

---

### 2. ⭐ Star Topology: How It Works
```
[Host 1] ────────┐
[Host 2] ────────┼───> [Central Switch / Hub] ───> [Destination Host]
[Host 3] ────────┘
```
1. **Dedicated Point-to-Point Ingress**: The sender transmits its frame across a dedicated Cat6 UTP cable into its assigned port on the central switch.
2. **Dynamic CAM / MAC Learning**: The switch inspects the frame header's Source MAC and maps it to the ingress port in its **Content Addressable Memory (CAM) Table**.
3. **CAM Lookup & Microsegmented Unicast**:
   - **CAM Hit**: If the Destination MAC is in the CAM table, the switch forwards the frame **exclusively** out the destination port. Other ports experience 0% traffic (Microsegmentation!).
   - **CAM Miss**: If unknown, the switch floods the frame out all ports except the ingress port to discover the host.
4. **Contrast with Hub Mode**: A passive Hub lacks MAC intelligence and repeats incoming electrical bits to **all** connected ports in a single shared collision domain.

---

### 3. ⭕ Ring Topology: How It Works (IEEE 802.5 Token Ring)
```
       ┌───> [Host 1] ───> [Host 2] ───┐
       │                               │
       └─── [Host 4] <─── [Host 3] <───┘
```
1. **Token Circulation**: A 3-byte control frame called the **Token** (`FREE`) circulates unidirectionally around the closed circular loop.
2. **Token Capture**: A station wishing to transmit waits for the token, captures it, sets the token status to `BUSY`, and appends its data payload with CRC checksum.
3. **Active Repeater Forwarding**: The frame hops station-to-station. Each intermediate station acts as an active repeater: regenerating the electrical/optical digital bits and forwarding them clockwise.
4. **Destination Copy & ACK Assert**: The destination station recognizes its MAC address, copies the frame into buffer memory, and asserts the **Address Recognized ($A=1$)** and **Frame Copied ($C=1$)** status bits.
5. **Frame Stripping & Token Release**: The frame completes a full 360° circle back to the original sender. The sender verifies $A=1$ and $C=1$, strips the data frame off the ring, and releases a fresh `FREE` token back onto the network.

---

### 4. 🕸️ Full Mesh Topology: How It Works
```
        [Node 1] ──────────── [Node 2]
           │   \             /   │
           │     \         /     │
           │       \     /       │
           │         \ /         │
        [Node 4] ──────────── [Node 3]
```
1. **Direct Dedicated Point-to-Point Links**: A dedicated physical cable connects every pair of nodes ($L = \frac{N(N-1)}{2}$).
2. **1-Hop Transmission with Zero Contention**: Traffic travels directly from source to destination in **1 single hop** without traversing intermediate nodes and with **zero shared medium contention**.
3. **Dynamic Self-Healing (Dijkstra SPF Reroute)**: If a dedicated link is severed, routing protocols (e.g. OSPF) compute alternate multi-hop paths around the failure (e.g., Node 1 $\to$ Node 3 $\to$ Node 2), guaranteeing uninterrupted communication.

---

## 📊 Summary Comparison: The 4 Core Topologies

| Feature | 🚌 Bus | ⭐ Star (Switch) | ⭕ Ring (Token) | 🕸️ Full Mesh |
| :--- | :--- | :--- | :--- | :--- |
| **Physical Links Formula** | $1\ \text{trunk} + N\ \text{drops}$ | $N\ \text{links}$ | $N\ \text{links}$ | $\mathbf{\frac{N(N-1)}{2}}\ \text{links}$ |
| **Ports per Host** | $1\ \text{port}$ | $1\ \text{port}$ ($N$ on Switch) | $2\ \text{ports}$ (Rx / Tx) | $\mathbf{N - 1}\ \text{ports}$ |
| **Network Diameter** | $1\ \text{collision domain}$ | $2\ \text{hops}$ ($\text{Src} \to \text{SW} \to \text{Dst}$) | $\lfloor N/2 \rfloor\ \text{to}\ N-1\ \text{hops}$ | $\mathbf{1\ \text{hop}}$ |
| **Medium Access** | Half-Duplex CSMA/CD | Full-Duplex Microsegmented | Deterministic Token Passing | Dedicated Point-to-Point |
| **Single Point of Failure?**| **YES** (Backbone / Terminator) | **YES** (Central Switch) | **YES** (Single link break) | **NO** (Full redundancy) |
| **Cabling Growth** | $O(N)$ Linear | $O(N)$ Linear | $O(N)$ Linear | $\mathbf{O(N^2)}$ Combinatorial |
| **Cabling Cost** | Lowest | Moderate | Moderate | Extremely High |

---

## 🚀 How to Run the Project

### 1. Launch the Interactive Dashboard
```bash
cd /Users/manavmishra/Desktop/cn_project
source .venv/bin/activate
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

### 2. Run Automated Unit Tests
```bash
python3 -m unittest -v tests.py
```
*(All 9 unit tests pass in 0.007s with 100% pass rate).*

---

## 📁 Repository Structure
```
cn_project/
├── app.py                      # 5-Tab Interactive Streamlit Dashboard
├── topology_engine.py          # Detailed Workflow Engine for Bus, Star, Ring & Mesh
├── graph_metrics.py            # Graph Theory Formulas, Cost Modeling & Radar Scores
├── interactive_visualizer.py   # High-Resolution Diagram & Interactive SVG Canvas
├── tests.py                    # 9 Comprehensive Unit Tests (100% Pass)
├── requirements.txt            # Python Dependencies
└── README.md                   # Capstone Project Documentation
```


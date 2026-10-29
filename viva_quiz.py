"""
viva_quiz.py - University Lab Viva Voce Preparation for the 4 Core Topologies:
Bus, Star, Ring, and Mesh.
"""

from typing import List, Dict

TOPOLOGY_QUIZ_QUESTIONS: List[Dict] = [
    {
        "id": 1,
        "question": "In a Full Mesh topology with N nodes, what is the exact formula for the total number of duplex links required?",
        "options": [
            "N(N - 1) / 2",
            "N(N - 1)",
            "N - 1",
            "2N"
        ],
        "correct_index": 0,
        "explanation": "Every node has a dedicated link to every other node. The total unique pairs among N nodes is C(N, 2) = N(N - 1) / 2."
    },
    {
        "id": 2,
        "question": "How many physical I/O ports (network interfaces) does EACH host require in a Full Mesh network of N nodes?",
        "options": [
            "N - 1",
            "N",
            "1",
            "N / 2"
        ],
        "correct_index": 0,
        "explanation": "Since each node maintains an independent point-to-point connection to all other (N - 1) nodes, every host requires strictly (N - 1) physical I/O ports."
    },
    {
        "id": 3,
        "question": "What is the critical role of 50-ohm BNC terminators at the ends of a linear Bus trunk cable?",
        "options": [
            "Absorb electrical signals at cable ends to prevent signal reflections that corrupt subsequent frames.",
            "Amplify digital signals to overcome cable attenuation.",
            "Provide power to network interface cards.",
            "Convert half-duplex signals into full-duplex signals."
        ],
        "correct_index": 0,
        "explanation": "When electrical signals hit an open-circuit cable end, they bounce back (signal reflection), causing destructive standing wave interference that destroys data. 50Ω terminators absorb this wave energy."
    },
    {
        "id": 4,
        "question": "In a Star topology, what is the crucial operational difference between a Central Switch and a Central Hub?",
        "options": [
            "A Switch uses a CAM/MAC table to forward packets only to the destination port (microsegmentation), whereas a Hub floods packets to all ports in a single collision domain.",
            "A Hub operates at Layer 3 while a Switch operates at Layer 1.",
            "A Hub uses fiber optic while a Switch only uses coaxial cable.",
            "A Switch cannot connect more than 4 computers."
        ],
        "correct_index": 0,
        "explanation": "A Hub is a Layer-1 repeater (Physical Star, Logical Bus) with 1 shared collision domain. A Switch is a Layer-2 bridge that learns MAC addresses and unicasts traffic directly, giving dedicated bandwidth to each port."
    },
    {
        "id": 5,
        "question": "In an IEEE 802.5 Token Ring network, how does the transmitting station verify that the destination accepted the frame?",
        "options": [
            "The destination sets the Address Recognized (A=1) and Frame Copied (C=1) bits in the Frame Status byte as it circulates back.",
            "The destination sends an out-of-band ICMP ping message.",
            "The central MAU sends an acknowledgement to the sender.",
            "The sender assumes delivery if no collision is heard within 51.2 microseconds."
        ],
        "correct_index": 0,
        "explanation": "Frames circulate in a full 360° circle. When passing the destination, the destination copies the payload and sets the trailing A=1 and C=1 bits. The sender inspects these bits before stripping the frame and releasing the token."
    },
    {
        "id": 6,
        "question": "What happens if a single physical link is severed in a standard unidirectional Ring topology?",
        "options": [
            "The entire network halts because the token cannot complete its circulation loop.",
            "Only the two adjacent nodes lose communication; the rest continue unaffected.",
            "The ring automatically reverses direction with no downtime.",
            "Packets jump across the gap wirelessly."
        ],
        "correct_index": 0,
        "explanation": "In a single unidirectional ring, every station depends on the continuous circular passing of the token. A single break halts token circulation, causing total network failure (unless a Dual-Ring self-healing loopback is deployed)."
    },
    {
        "id": 7,
        "question": "In a Bus topology, what happens if the main backbone trunk cable is cut in the middle vs. if an individual drop cable fails?",
        "options": [
            "Severing the backbone splits the network into two disconnected halves and causes signal reflection; a drop cable cut isolates only that single host.",
            "Both failures shut down the entire network completely.",
            "Severing the backbone has no effect due to dynamic rerouting.",
            "A drop cable cut causes all other hosts to reboot."
        ],
        "correct_index": 0,
        "explanation": "The backbone is a shared medium; breaking it creates open ends that destroy communication via reflections. A drop line connects just one host; if it fails, the backbone remains intact and all other hosts communicate normally."
    },
    {
        "id": 8,
        "question": "What is the Network Diameter (worst-case latency in hops) of a Full Mesh topology vs. a Star topology?",
        "options": [
            "Full Mesh is 1 hop (direct); Star is 2 hops (Host A -> Switch -> Host B).",
            "Full Mesh is N hops; Star is 1 hop.",
            "Both have a diameter of N - 1 hops.",
            "Full Mesh is 4 hops; Star is 8 hops."
        ],
        "correct_index": 0,
        "explanation": "In Full Mesh, every host connects directly to every other host, giving a diameter of 1 hop. In Star, packets travel from source to central switch, and switch to destination, giving a diameter of 2 hops."
    },
    {
        "id": 9,
        "question": "What is the primary reason Full Mesh topologies are NOT used to connect 500 office computers in a company?",
        "options": [
            "Cabling explosion: 500 nodes would require 124,750 cables and 499 network ports per computer, which is cost and hardware prohibitive.",
            "Full Mesh networks do not support the TCP/IP protocol suite.",
            "Mesh networks have higher latency than a Bus topology.",
            "Electromagnetic interference between adjacent wires causes total packet loss."
        ],
        "correct_index": 0,
        "explanation": "Combinatorial growth L = N(N-1)/2 means 500 computers need 124,750 cables. Star or Tree topologies with switches scale linearly (O(N)), making them the standard choice for LANs."
    },
    {
        "id": 10,
        "question": "What routing algorithm is standard for calculating the optimal alternate path in a Mesh topology when a link is severed?",
        "options": [
            "Dijkstra's Shortest Path First (SPF) Algorithm",
            "Binary Search Algorithm",
            "QuickSort Algorithm",
            "Round Robin Scheduling"
        ],
        "correct_index": 0,
        "explanation": "Dijkstra's SPF algorithm (used in OSPF and IS-IS routing protocols) models the network as a weighted graph and dynamically computes the shortest alternate path to bypass severed or congested links."
    }
]

VIVA_TOPOLOGY_CHEAT_SHEET = r"""
### 🎓 Comprehensive Viva Voce Cheat Sheet: 4 Foundational Topologies

| Feature | 🚌 Bus Topology | ⭐ Star Topology (Switch) | ⭕ Ring Topology (Token) | 🕸️ Full Mesh Topology |
| :--- | :--- | :--- | :--- | :--- |
| **Physical Links ($L$)** | $1\ \text{trunk} + N\ \text{drops}$ | $N\ \text{links}$ | $N\ \text{links}$ | $\mathbf{\frac{N(N-1)}{2}}\ \text{links}$ |
| **I/O Ports per Node** | $1\ \text{port}$ | $1\ \text{port}\ (N\ \text{on Switch})$ | $2\ \text{ports}\ (\text{Rx / Tx})$ | $\mathbf{N - 1}\ \text{ports}$ |
| **Network Diameter** | $1\ \text{collision domain}$ | $2\ \text{hops}\ (\text{Source} \to \text{SW} \to \text{Dest})$ | $\lfloor N/2 \rfloor\ \text{to}\ N-1\ \text{hops}$ | $\mathbf{1\ \text{hop}}\ (\text{Direct point-to-point})$ |
| **Media Access Control** | Half-Duplex CSMA/CD | Full-Duplex Microsegmentation | IEEE 802.5 Token Passing | Dedicated Point-to-Point |
| **Troubleshooting Ease** | Very Difficult (break stops bus) | Very Easy (port-level isolation) | Moderate (break stops ring) | Easy (isolated lines) |
| **Installation Cost** | Lowest (Minimal cable) | Moderate (Cat6 + Switch) | Moderate (Fiber loop) | Extremely High ($O(N^2)$ cables) |
| **Single Point of Failure?** | **YES** (Backbone / Terminator) | **YES** (Central Switch) | **YES** (Any single link break) | **NO** (Fully redundant paths) |
| **Scalability** | Poor (Signal degrades with taps) | **Excellent** (Add ports/switches) | Poor (Adding node breaks ring) | Terrible ($O(N^2)$ explosion) |

---

#### 💡 Mathematical Derivations & Lab Proofs:
1. **Full Mesh Combinatorial Derivation**:
   $$\text{Links} = \binom{N}{2} = \frac{N(N-1)}{2}$$
   - *Example*: For $N = 6$: $\frac{6 \times 5}{2} = 15$ cables. For $N = 20$: $\frac{20 \times 19}{2} = 190$ cables.
2. **Star vs. Hub Collision Domains**:
   - A Hub has **1 Collision Domain** for all $N$ ports.
   - A Switch has **$N$ separate Collision Domains** (1 per port), eliminating collisions completely.
3. **Bus Characteristic Impedance & Reflection**:
   - Reflection Coefficient: $\Gamma = \frac{Z_L - Z_0}{Z_L + Z_0}$.
   - If unterminated ($Z_L = \infty$), $\Gamma = +1$ (100% signal reflects back).
   - If terminated with $Z_L = 50\Omega = Z_0$, $\Gamma = 0$ (zero reflection, 100% absorption).
"""

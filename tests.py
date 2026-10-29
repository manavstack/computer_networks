"""
tests.py - Comprehensive Unit Test Suite for the 4 Core Topologies:
Bus, Star, Ring, and Mesh.
"""

import unittest
from topology_engine import NetworkTopology, TopologyType, WorkflowStep
from graph_metrics import (
    compute_topology_metrics,
    generate_4_topologies_comparison_matrix,
    generate_4_topologies_radar_scores,
    estimate_installation_cost
)


class Test4NetworkTopologies(unittest.TestCase):

    def test_full_mesh_formula(self):
        """Full Mesh link count must follow N(N-1)/2 and each node degree must be N-1."""
        for n in [3, 4, 5, 7]:
            topo = NetworkTopology(topo_type=TopologyType.MESH, num_nodes=n)
            expected_links = n * (n - 1) // 2
            self.assertEqual(topo.graph.number_of_edges(), expected_links)
            for _, deg in topo.graph.degree():
                self.assertEqual(deg, n - 1)

    def test_star_switch_and_hub(self):
        """Star topology must have N links and degree N at center."""
        n = 5
        topo_sw = NetworkTopology(topo_type=TopologyType.STAR, num_nodes=n, star_mode="Switch")
        self.assertEqual(topo_sw.graph.number_of_edges(), n)
        self.assertIn("Central_Switch", topo_sw.graph.nodes())
        self.assertEqual(topo_sw.graph.degree("Central_Switch"), n)

        topo_hub = NetworkTopology(topo_type=TopologyType.STAR, num_nodes=n, star_mode="Hub")
        self.assertIn("Central_Hub", topo_hub.graph.nodes())

    def test_ring_topology(self):
        """Ring topology must have N links and degree 2 at all nodes."""
        n = 6
        topo = NetworkTopology(topo_type=TopologyType.RING, num_nodes=n)
        self.assertEqual(topo.graph.number_of_edges(), n)
        for _, deg in topo.graph.degree():
            self.assertEqual(deg, 2)

    def test_bus_topology(self):
        """Bus topology must have N drop cables and N-1 trunk links."""
        n = 4
        topo = NetworkTopology(topo_type=TopologyType.BUS, num_nodes=n)
        # N drop cables + (N-1) trunk links = 2N - 1 total edges
        self.assertEqual(topo.graph.number_of_edges(), (2 * n) - 1)

    def test_bus_workflow_and_terminator_fault(self):
        """Bus workflow should deliver when terminator is active and drop when missing."""
        topo = NetworkTopology(topo_type=TopologyType.BUS, num_nodes=4)
        # 1. Normal run
        steps = topo.get_detailed_workflow("Host_1", "Host_3")
        self.assertTrue(any(s.status == "delivered" for s in steps))

        # 2. Missing terminator
        topo.bus_terminator_active = False
        steps_fail = topo.get_detailed_workflow("Host_1", "Host_3")
        self.assertTrue(any(s.status == "dropped" and "terminator" in s.title.lower() for s in steps_fail))

    def test_star_switch_workflow_cam_learning(self):
        """Star switch workflow must learn MAC and unicast to destination."""
        topo = NetworkTopology(topo_type=TopologyType.STAR, num_nodes=4, star_mode="Switch")
        steps = topo.get_detailed_workflow("Host_1", "Host_2")
        self.assertTrue(any(s.status == "delivered" for s in steps))
        # Verify MAC learned in CAM table
        src_mac = topo.mac_addresses["Host_1"]
        self.assertIn(src_mac, topo.switch_cam_table)
        self.assertEqual(topo.switch_cam_table[src_mac], "Host_1")

    def test_ring_workflow_token_passing(self):
        """Ring workflow must capture token, traverse intermediate hops, and set ACK bits."""
        topo = NetworkTopology(topo_type=TopologyType.RING, num_nodes=5)
        steps = topo.get_detailed_workflow("Host_1", "Host_4")
        self.assertTrue(any("token capture" in s.title.lower() for s in steps))
        self.assertTrue(any("ack bits set" in s.title.lower() for s in steps))
        self.assertTrue(any(s.status == "delivered" for s in steps))

    def test_mesh_workflow_direct_and_reroute(self):
        """Mesh must route directly in 1 hop, and reroute via Dijkstra when direct link cut."""
        topo = NetworkTopology(topo_type=TopologyType.MESH, num_nodes=4)
        # 1. Direct 1-hop
        steps1 = topo.get_detailed_workflow("Node_1", "Node_2")
        self.assertEqual(len(steps1), 1)
        self.assertEqual(steps1[0].status, "delivered")

        # 2. Cut direct link
        topo.toggle_link_fault("Node_1", "Node_2")
        steps2 = topo.get_detailed_workflow("Node_1", "Node_2")
        self.assertTrue(any("dijkstra" in s.title.lower() for s in steps2))
        self.assertEqual(steps2[-1].status, "delivered")

    def test_benchmark_matrix_4_topologies(self):
        """Benchmark matrix must contain exactly the 4 topologies."""
        df = generate_4_topologies_comparison_matrix(num_nodes=5)
        self.assertEqual(len(df), 4)
        topos = df["Topology"].tolist()
        self.assertTrue(any("Bus" in t for t in topos))
        self.assertTrue(any("Star" in t for t in topos))
        self.assertTrue(any("Ring" in t for t in topos))
        self.assertTrue(any("Mesh" in t for t in topos))


if __name__ == "__main__":
    unittest.main()

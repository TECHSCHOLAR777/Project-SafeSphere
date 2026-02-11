"""
SafeSphere Road Graph Examples - Heatmap Integration

Demonstrates building and analyzing a road network with integrated heatmap risks.
"""

from road_graph import RoadGraph, RoadNode, RoadEdge
from heatmap_adapter import HeatmapAdapter


def example_basic_graph():
    """Example 1: Build a basic road network."""
    print("=" * 70)
    print("EXAMPLE 1: Building a Basic Road Network")
    print("=" * 70)

    # Create road graph (undirected for now)
    road = RoadGraph(directed=False, risk_penalty_factor=50.0)

    # Add nodes (zones/locations)
    nodes_data = [
        RoadNode("Office_A", (0.0, 0.0), "Office Building A", "entrance"),
        RoadNode("Office_B", (5.0, 0.0), "Office Building B", "entrance"),
        RoadNode("Parking", (2.5, 3.0), "Parking Lot", "zone"),
        RoadNode("Security", (2.5, -2.0), "Security Station", "zone"),
        RoadNode("Exit_Main", (10.0, 0.0), "Main Emergency Exit", "exit"),
    ]

    for node in nodes_data:
        road.add_node(node)
        print(f"Added node: {node.node_id} at {node.position}")

    print(f"\nTotal nodes: {road.get_nodes_count()}")

    # Add edges (roads)
    edges_data = [
        RoadEdge("A_P", "Office_A", "Parking", distance=3.2, road_type="path"),
        RoadEdge("B_P", "Office_B", "Parking", distance=3.2, road_type="path"),
        RoadEdge("P_E", "Parking", "Exit_Main", distance=7.5, road_type="road"),
        RoadEdge("A_S", "Office_A", "Security", distance=2.0, road_type="corridor"),
        RoadEdge("S_E", "Security", "Exit_Main", distance=10.5, road_type="road"),
        RoadEdge("A_B", "Office_A", "Office_B", distance=5.0, road_type="path"),
    ]

    for edge in edges_data:
        road.add_edge(edge)
        cost = road.get_edge_cost(edge.from_node, edge.to_node)
        print(f"Added edge: {edge.from_node} → {edge.to_node} (distance: {edge.distance}, cost: {cost})")

    print(f"Total edges: {road.get_edges_count()}")

    # Graph statistics
    print("\n--- Graph Statistics (without heatmap risk) ---")
    stats = road.get_graph_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"{key}: {value:.3f}")
        else:
            print(f"{key}: {value}")

    return road


def example_heatmap_integration():
    """Example 2: Integrate heatmap risk into road graph."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Integrating Heatmap Risk into Road Graph")
    print("=" * 70)

    # Build road graph
    road = RoadGraph(directed=False, risk_penalty_factor=50.0)

    # Add nodes
    nodes = [
        RoadNode("Start", (0.0, 0.0), "Start Point", "entrance"),
        RoadNode("Route_Safe", (2.0, 0.0), "Safe Route Node", "zone"),
        RoadNode("Route_Risk", (1.0, 1.5), "Risky Route Node", "zone"),
        RoadNode("End", (4.0, 0.0), "Destination", "exit"),
    ]
    for node in nodes:
        road.add_node(node)

    # Add edges
    edges = [
        RoadEdge("E_SafeR", "Start", "Route_Safe", distance=2.0),
        RoadEdge("SafeR_End", "Route_Safe", "End", distance=2.0),
        RoadEdge("E_RiskR", "Start", "Route_Risk", distance=1.5),
        RoadEdge("RiskR_End", "Route_Risk", "End", distance=2.5),
    ]
    for edge in edges:
        road.add_edge(edge)

    print("Road graph built with 4 nodes and 4 edges\n")

    # Create heatmap with risk data
    heatmap_data = {
        "nodes": {
            "Start": {"position": {"x": 0.0, "y": 0.0}, "risk": 0.05},
            "Route_Safe": {"position": {"x": 2.0, "y": 0.0}, "risk": 0.15},
            "Route_Risk": {"position": {"x": 1.0, "y": 1.5}, "risk": 0.80},
            "End": {"position": {"x": 4.0, "y": 0.0}, "risk": 0.10},
        },
        "edges": {
            "E_SafeR": {"from_node": "Start", "to_node": "Route_Safe", "risk": 0.10},
            "SafeR_End": {"from_node": "Route_Safe", "to_node": "End", "risk": 0.12},
            "E_RiskR": {"from_node": "Start", "to_node": "Route_Risk", "risk": 0.70},
            "RiskR_End": {"from_node": "Route_Risk", "to_node": "End", "risk": 0.75},
        },
        "updated_at": "2026-02-10T14:30:00Z"
    }

    heatmap = HeatmapAdapter()
    heatmap.load_heatmap(heatmap_data)

    # Integrate heatmap into road graph
    print("--- Before Heatmap Integration ---")
    print(f"E_SafeR cost: {road.get_edge_cost('Start', 'Route_Safe'):.3f}")
    print(f"SafeR_End cost: {road.get_edge_cost('Route_Safe', 'End'):.3f}")
    print(f"E_RiskR cost: {road.get_edge_cost('Start', 'Route_Risk'):.3f}")
    print(f"RiskR_End cost: {road.get_edge_cost('Route_Risk', 'End'):.3f}")

    road.load_heatmap_risks(heatmap)

    print("\n--- After Heatmap Integration (Cost = Distance × Risk Multiplier) ---")
    breakdown_safe = road.cost_breakdown("Start", "Route_Safe")
    breakdown_risk1 = road.cost_breakdown("Start", "Route_Risk")
    breakdown_risk2 = road.cost_breakdown("Route_Risk", "End")

    print(f"\nStart → Route_Safe:")
    print(f"  Distance: {breakdown_safe['base_distance']} | Risk: {breakdown_safe['heatmap_risk']:.2f}")
    print(f"  Multiplier: {breakdown_safe['risk_multiplier']:.2f}x | Cost: {breakdown_safe['final_cost']:.3f}")

    print(f"\nStart → Route_Risk:")
    print(f"  Distance: {breakdown_risk1['base_distance']} | Risk: {breakdown_risk1['heatmap_risk']:.2f}")
    print(f"  Multiplier: {breakdown_risk1['risk_multiplier']:.2f}x | Cost: {breakdown_risk1['final_cost']:.3f}")

    print(f"\nRoute_Risk → End:")
    print(f"  Distance: {breakdown_risk2['base_distance']} | Risk: {breakdown_risk2['heatmap_risk']:.2f}")
    print(f"  Multiplier: {breakdown_risk2['risk_multiplier']:.2f}x | Cost: {breakdown_risk2['final_cost']:.3f}")

    # Statistics after integration
    print("\n--- Updated Graph Statistics (with risk) ---")
    stats = road.get_graph_stats()
    print(f"Average distance: {stats['avg_distance']:.3f}")
    print(f"Average risk: {stats['avg_risk']:.3f}")
    print(f"Average cost: {stats['avg_cost']:.3f}")
    print(f"Max cost: {stats['max_cost']:.3f}")
    print(f"Min cost: {stats['min_cost']:.3f}")

    return road, heatmap


def example_risk_analysis():
    """Example 3: Analyze edges by risk level."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Risk Analysis - Finding Problem Areas")
    print("=" * 70)

    # Build a more complex network
    road = RoadGraph(directed=False, risk_penalty_factor=50.0)

    # Create a grid-like network
    positions = {
        "Zone_00": (0.0, 0.0),
        "Zone_01": (0.0, 2.0),
        "Zone_10": (2.0, 0.0),
        "Zone_11": (2.0, 2.0),
        "Zone_20": (4.0, 0.0),
        "Zone_21": (4.0, 2.0),
    }

    for zone_id, pos in positions.items():
        road.add_node(RoadNode(zone_id, pos, f"Zone at {pos}", "zone"))

    # Add edges with varying distances
    edges_to_add = [
        RoadEdge("E00_01", "Zone_00", "Zone_01", 2.0),
        RoadEdge("E00_10", "Zone_00", "Zone_10", 2.0),
        RoadEdge("E01_11", "Zone_01", "Zone_11", 2.0),
        RoadEdge("E10_11", "Zone_10", "Zone_11", 2.0),
        RoadEdge("E10_20", "Zone_10", "Zone_20", 2.0),
        RoadEdge("E11_21", "Zone_11", "Zone_21", 2.0),
        RoadEdge("E20_21", "Zone_20", "Zone_21", 2.0),
    ]

    for edge in edges_to_add:
        road.add_edge(edge)

    # Create heatmap with mixed risk levels
    heatmap_data = {
        "nodes": {
            "Zone_00": {"position": {"x": 0.0, "y": 0.0}, "risk": 0.10},
            "Zone_01": {"position": {"x": 0.0, "y": 2.0}, "risk": 0.15},
            "Zone_10": {"position": {"x": 2.0, "y": 0.0}, "risk": 0.20},
            "Zone_11": {"position": {"x": 2.0, "y": 2.0}, "risk": 0.75},  # High risk!
            "Zone_20": {"position": {"x": 4.0, "y": 0.0}, "risk": 0.25},
            "Zone_21": {"position": {"x": 4.0, "y": 2.0}, "risk": 0.85},  # Critical!
        },
        "edges": {
            "E00_01": {"from_node": "Zone_00", "to_node": "Zone_01", "risk": 0.10},
            "E00_10": {"from_node": "Zone_00", "to_node": "Zone_10", "risk": 0.15},
            "E01_11": {"from_node": "Zone_01", "to_node": "Zone_11", "risk": 0.70},  # High!
            "E10_11": {"from_node": "Zone_10", "to_node": "Zone_11", "risk": 0.65},
            "E10_20": {"from_node": "Zone_10", "to_node": "Zone_20", "risk": 0.20},
            "E11_21": {"from_node": "Zone_11", "to_node": "Zone_21", "risk": 0.80},  # Critical!
            "E20_21": {"from_node": "Zone_20", "to_node": "Zone_21", "risk": 0.30},
        },
        "updated_at": "2026-02-10T14:30:00Z"
    }

    heatmap = HeatmapAdapter()
    heatmap.load_heatmap(heatmap_data)
    road.load_heatmap_risks(heatmap)

    print("\n--- High Risk Edges (risk > 0.60) ---")
    high_risk = road.get_high_risk_edges(threshold=0.60)
    for i, edge in enumerate(high_risk, 1):
        print(f"{i}. {edge['from']} → {edge['to']}")
        print(f"   Risk: {edge['risk']:.2f} | Distance: {edge['distance']:.2f} | Cost: {edge['cost']:.3f}")

    print("\n--- Low Risk Edges (risk < 0.20) ---")
    low_risk = road.get_low_risk_edges(threshold=0.20)
    for i, edge in enumerate(low_risk, 1):
        print(f"{i}. {edge['from']} → {edge['to']}")
        print(f"   Risk: {edge['risk']:.2f} | Distance: {edge['distance']:.2f} | Cost: {edge['cost']:.3f}")

    return road


def example_connectivity():
    """Example 4: Analyze network connectivity."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Network Connectivity Analysis")
    print("=" * 70)

    road = RoadGraph(directed=True)  # Directed graph for one-way roads

    # Create a network with multiple paths
    nodes = [
        RoadNode("A", (0.0, 0.0)),
        RoadNode("B", (1.0, 0.0)),
        RoadNode("C", (2.0, 0.0)),
        RoadNode("D", (1.0, 1.0)),
        RoadNode("E", (2.0, 1.0)),
    ]
    for node in nodes:
        road.add_node(node)

    # Create directed edges (one-way roads)
    edges = [
        RoadEdge("AB", "A", "B", 1.0),
        RoadEdge("BC", "B", "C", 1.0),
        RoadEdge("BD", "B", "D", 1.4),
        RoadEdge("DE", "D", "E", 1.4),
        RoadEdge("EC", "E", "C", 1.4),
    ]
    for edge in edges:
        road.add_edge(edge)

    print("Created directed road network (5 nodes, 5 edges)\n")

    # Get connectivity matrix
    print("--- Connectivity Matrix ---")
    matrix = road.get_connectivity_matrix()
    for node_id, neighbors in matrix.items():
        print(f"{node_id}: {neighbors}")

    # Get neighbor information for a node
    print("\n--- Neighbors of Node B with Costs ---")
    neighbors = road.get_neighbors("B")
    for neighbor_id, cost, risk in neighbors:
        print(f"  → {neighbor_id}: cost={cost:.3f}, risk={risk:.3f}")

    # Validate graph
    print("\n--- Graph Validation ---")
    is_valid, errors = road.validate_graph()
    if is_valid:
        print("✓ Graph is valid!")
    else:
        print("✗ Graph has errors:")
        for error in errors:
            print(f"  - {error}")

    return road


def example_graph_statistics():
    """Example 5: Comprehensive graph statistics."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Comprehensive Graph Statistics and Metrics")
    print("=" * 70)

    road = RoadGraph(directed=False, risk_penalty_factor=75.0)

    # Build a realistic campus network
    nodes = [
        RoadNode("Main_Gate", (0.0, 0.0), "Main Entrance"),
        RoadNode("Library", (1.0, 1.0), "Central Library"),
        RoadNode("Cafeteria", (1.0, -1.0), "Cafeteria"),
        RoadNode("Sports", (2.0, 0.0), "Sports Complex"),
        RoadNode("Emergency_Exit", (3.0, 1.5), "Emergency Exit"),
    ]
    for node in nodes:
        road.add_node(node)

    edges = [
        RoadEdge("MG_L", "Main_Gate", "Library", 1.4),
        RoadEdge("MG_C", "Main_Gate", "Cafeteria", 1.4),
        RoadEdge("L_S", "Library", "Sports", 1.4),
        RoadEdge("C_S", "Cafeteria", "Sports", 2.0),
        RoadEdge("S_E", "Sports", "Emergency_Exit", 1.8),
    ]
    for edge in edges:
        road.add_edge(edge)

    # Add heatmap risk
    heatmap_data = {
        "nodes": {
            "Main_Gate": {"position": {"x": 0.0, "y": 0.0}, "risk": 0.10},
            "Library": {"position": {"x": 1.0, "y": 1.0}, "risk": 0.20},
            "Cafeteria": {"position": {"x": 1.0, "y": -1.0}, "risk": 0.50},
            "Sports": {"position": {"x": 2.0, "y": 0.0}, "risk": 0.75},
            "Emergency_Exit": {"position": {"x": 3.0, "y": 1.5}, "risk": 0.05},
        },
        "edges": {
            "MG_L": {"from_node": "Main_Gate", "to_node": "Library", "risk": 0.15},
            "MG_C": {"from_node": "Main_Gate", "to_node": "Cafeteria", "risk": 0.45},
            "L_S": {"from_node": "Library", "to_node": "Sports", "risk": 0.65},
            "C_S": {"from_node": "Cafeteria", "to_node": "Sports", "risk": 0.60},
            "S_E": {"from_node": "Sports", "to_node": "Emergency_Exit", "risk": 0.70},
        },
        "updated_at": "2026-02-10T14:30:00Z"
    }

    heatmap = HeatmapAdapter()
    heatmap.load_heatmap(heatmap_data)
    road.load_heatmap_risks(heatmap)

    print("\n--- Overall Statistics ---")
    stats = road.get_graph_stats()
    print(f"Nodes: {stats['node_count']}")
    print(f"Edges: {stats['edge_count']}")
    print(f"Connected: {stats['is_connected']}")
    print(f"Directed: {stats['is_directed']}")
    print(f"\nRisk Penalty Factor: {stats['risk_penalty_factor']}")
    print(f"Average Distance: {stats['avg_distance']:.3f}")
    print(f"Average Risk: {stats['avg_risk']:.3f}")
    print(f"Average Cost: {stats['avg_cost']:.3f}")
    print(f"Cost Range: {stats['min_cost']:.3f} - {stats['max_cost']:.3f}")

    # Detailed edge information
    print("\n--- All Edges with Costs ---")
    print(f"{'From':<15} {'To':<15} {'Distance':<10} {'Risk':<8} {'Cost':<10}")
    print("-" * 60)
    for u, v in road.get_all_edges():
        dist = road.get_edge_distance(u, v) or 0.0
        risk = road.get_edge_risk(u, v) or 0.0
        cost = road.get_edge_cost(u, v) or 0.0
        print(f"{u:<15} {v:<15} {dist:<10.2f} {risk:<8.2f} {cost:<10.2f}")

    return road


def example_export_import():
    """Example 6: Export and import graph."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Export and Import Graph Structure")
    print("=" * 70)

    # Create original graph
    road1 = RoadGraph()
    road1.add_node(RoadNode("A", (0.0, 0.0), "Node A"))
    road1.add_node(RoadNode("B", (1.0, 0.0), "Node B"))
    road1.add_edge(RoadEdge("AB", "A", "B", 1.0))

    # Load heatmap
    heatmap_data = {
        "nodes": {
            "A": {"position": {"x": 0.0, "y": 0.0}, "risk": 0.2},
            "B": {"position": {"x": 1.0, "y": 0.0}, "risk": 0.3},
        },
        "edges": {
            "AB": {"from_node": "A", "to_node": "B", "risk": 0.25},
        },
        "updated_at": "2026-02-10T14:30:00Z"
    }
    heatmap = HeatmapAdapter()
    heatmap.load_heatmap(heatmap_data)
    road1.load_heatmap_risks(heatmap)

    print("Original graph created and loaded with heatmap risk\n")

    # Export to dictionary
    print("--- Exporting Graph ---")
    exported = road1.export_to_dict()
    print(f"Nodes in export: {list(exported['nodes'].keys())}")
    print(f"Edges in export: {list(exported['edges'].keys())}")
    print(f"Risk penalty factor: {exported['risk_penalty_factor']}")
    print(f"Graph stats:\n  {exported['stats']}")

    # Create new graph and import
    print("\n--- Importing into New Graph ---")
    road2 = RoadGraph()
    road2.import_from_dict(exported)

    print(f"Imported nodes: {road2.get_all_nodes()}")
    print(f"Imported edges: {len(road2.get_all_edges())}")
    print(f"Node A risk: {road2.node_risks['A']}")
    print(f"Edge A→B cost: {road2.get_edge_cost('A', 'B'):.3f}")

    print("\n✓ Export/import successful!")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("SAFESPHERE ROAD GRAPH - NetworkX Integration Examples")
    print("=" * 70)

    example_basic_graph()
    example_heatmap_integration()
    example_risk_analysis()
    example_connectivity()
    example_graph_statistics()
    example_export_import()

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()

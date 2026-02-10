"""
SafeSphere Safe Route Engine - Example Usage

Demonstrates practical usage of HeatmapAdapter and GraphUtils
for safe route planning with risk heatmap data from backend.
"""

from heatmap_adapter import HeatmapAdapter, Position
from graph_utils import GraphUtils


def example_basic_usage():
    """Example 1: Basic heatmap loading and queries."""
    print("=" * 70)
    print("EXAMPLE 1: Basic Heatmap Loading and Node Queries")
    print("=" * 70)

    # Create heatmap from backend data
    heatmap_data = {
        "nodes": {
            "Gate_A": {
                "position": {"x": 0.0, "y": 0.0},
                "risk": 0.15,
                "name": "Main Gate",
                "type": "entrance"
            },
            "Parking_Lot": {
                "position": {"x": 2.0, "y": 1.5},
                "risk": 0.45,
                "name": "Parking Area",
                "type": "zone"
            },
            "Building_Entrance": {
                "position": {"x": 4.0, "y": 2.0},
                "risk": 0.25,
                "name": "Office Building",
                "type": "entrance"
            },
            "Blind_Corner": {
                "position": {"x": 3.0, "y": 0.5},
                "risk": 0.75,
                "name": "Maintenance Area",
                "type": "risk_zone"
            }
        },
        "edges": {
            "Gate_to_Parking": {
                "from_node": "Gate_A",
                "to_node": "Parking_Lot",
                "risk": 0.20
            },
            "Parking_to_Building": {
                "from_node": "Parking_Lot",
                "to_node": "Building_Entrance",
                "risk": 0.30
            },
            "Gate_to_Corner": {
                "from_node": "Gate_A",
                "to_node": "Blind_Corner",
                "risk": 0.65
            },
            "Corner_to_Building": {
                "from_node": "Blind_Corner",
                "to_node": "Building_Entrance",
                "risk": 0.55
            }
        },
        "updated_at": "2026-02-10T14:30:00Z"
    }

    # Load heatmap
    heatmap = HeatmapAdapter()
    heatmap.load_heatmap(heatmap_data)

    # Query individual nodes
    print("\n--- Node Risk Queries ---")
    for node_id in ["Gate_A", "Parking_Lot", "Building_Entrance", "Blind_Corner"]:
        risk = heatmap.get_node_risk(node_id)
        metadata = heatmap.get_zone_metadata(node_id)
        print(f"{node_id}:")
        print(f"  Risk: {risk:.2f} | Name: {metadata['name']} | Type: {metadata['type']}")

    print("\n--- Statistics ---")
    stats = heatmap.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

    print("\n--- Risk Distribution ---")
    dist = heatmap.get_risk_distribution()
    for level, count in dist.items():
        print(f"  {level.upper()}: {count} zones")

    print("\n--- Safe and Danger Zones ---")
    safe = heatmap.find_safe_zones(threshold=0.3)
    danger = heatmap.find_danger_zones(threshold=0.7)
    print(f"Safe zones (<0.3): {safe}")
    print(f"Danger zones (>0.7): {danger}")


def example_interpolation():
    """Example 2: Risk interpolation at arbitrary positions."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Risk Interpolation at Arbitrary Positions")
    print("=" * 70)

    heatmap_data = {
        "nodes": {
            "North": {"position": {"x": 0.0, "y": 10.0}, "risk": 0.10},
            "South": {"position": {"x": 0.0, "y": 0.0}, "risk": 0.80},
            "East": {"position": {"x": 10.0, "y": 5.0}, "risk": 0.30},
            "West": {"position": {"x": -10.0, "y": 5.0}, "risk": 0.60},
        },
        "edges": {},
        "updated_at": "2026-02-10T14:30:00Z"
    }

    heatmap = HeatmapAdapter()
    heatmap.load_heatmap(heatmap_data)

    print("\n--- Testing IDW Interpolation ---")
    test_positions = [
        (0.0, 5.0, "Center (between North/South)"),
        (5.0, 5.0, "Between Center and East"),
        (-5.0, 5.0, "Between Center and West"),
        (0.0, 7.5, "Upper Center (toward North)"),
    ]

    for x, y, description in test_positions:
        pos = Position(x, y)
        interpolated_risk = heatmap.get_interpolated_risk(pos, k=3)
        print(f"Position ({x:5.1f}, {y:5.1f}) | {description:30s} | Risk: {interpolated_risk:.3f}")


def example_pathfinding():
    """Example 3: Safest path finding."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Safest Path Finding (Dijkstra)")
    print("=" * 70)

    heatmap_data = {
        "nodes": {
            "START": {"position": {"x": 0.0, "y": 0.0}, "risk": 0.10, "name": "Start"},
            "Safe_Route_1": {"position": {"x": 1.0, "y": 0.0}, "risk": 0.15, "name": "Safe Node 1"},
            "Safe_Route_2": {"position": {"x": 2.0, "y": 0.0}, "risk": 0.12, "name": "Safe Node 2"},
            "Danger_Route": {"position": {"x": 1.0, "y": 1.0}, "risk": 0.85, "name": "Danger Zone"},
            "END": {"position": {"x": 3.0, "y": 0.0}, "risk": 0.05, "name": "End"},
        },
        "edges": {
            "start_safe1": {"from_node": "START", "to_node": "Safe_Route_1", "risk": 0.12},
            "safe1_safe2": {"from_node": "Safe_Route_1", "to_node": "Safe_Route_2", "risk": 0.10},
            "safe2_end": {"from_node": "Safe_Route_2", "to_node": "END", "risk": 0.08},
            "start_danger": {"from_node": "START", "to_node": "Danger_Route", "risk": 0.75},
            "danger_end": {"from_node": "Danger_Route", "to_node": "END", "risk": 0.70},
        },
        "updated_at": "2026-02-10T14:30:00Z"
    }

    heatmap = HeatmapAdapter()
    heatmap.load_heatmap(heatmap_data)

    print("\n--- Finding Safest Path ---")
    result = GraphUtils.dijkstra_safest_path(heatmap, "START", "END")

    if result:
        path, total_risk, segments = result
        print(f"✓ Path found!")
        print(f"  Nodes: {' → '.join(path)}")
        print(f"  Total Risk: {total_risk:.3f}")
        print(f"\n  Segments:")
        for segment in segments:
            print(f"    {segment}")
    else:
        print("✗ No path found")

    print("\n--- Alternative Paths ---")
    alternatives = GraphUtils.find_k_safest_paths(heatmap, "START", "END", k=3)
    for i, (path, risk, segments) in enumerate(alternatives, 1):
        print(f"\n  Path {i}: {' → '.join(path)}")
        print(f"  Risk: {risk:.3f}")


def example_route_analysis():
    """Example 4: Comprehensive route analysis."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Route Safety Analysis and Comparison")
    print("=" * 70)

    heatmap_data = {
        "nodes": {
            "A": {"position": {"x": 0.0, "y": 0.0}, "risk": 0.10},
            "B": {"position": {"x": 1.0, "y": 0.0}, "risk": 0.20},
            "C": {"position": {"x": 2.0, "y": 0.0}, "risk": 0.30},
            "D": {"position": {"x": 3.0, "y": 0.0}, "risk": 0.70},
            "E": {"position": {"x": 2.0, "y": 1.0}, "risk": 0.15},
        },
        "edges": {
            "A_B": {"from_node": "A", "to_node": "B", "risk": 0.15},
            "B_C": {"from_node": "B", "to_node": "C", "risk": 0.25},
            "C_D": {"from_node": "C", "to_node": "D", "risk": 0.75},
            "B_E": {"from_node": "B", "to_node": "E", "risk": 0.10},
            "E_C": {"from_node": "E", "to_node": "C", "risk": 0.12},
        },
        "updated_at": "2026-02-10T14:30:00Z"
    }

    heatmap = HeatmapAdapter()
    heatmap.load_heatmap(heatmap_data)

    # Analyze multiple routes
    routes = [
        ["A", "B", "C", "D"],  # Direct but passes through danger zone
        ["A", "B", "E", "C", "D"],  # Longer but safer
    ]

    print("\n--- Route Comparison ---")
    comparison = GraphUtils.compare_routes(heatmap, routes, verbose=False)
    for route_info in comparison["ranked_routes"]:
        print(f"Route: {' → '.join(route_info['path'])}")
        print(f"  Risk: {route_info['total_risk']:.3f} | Safety: {route_info['safety_level']}")

    print("\n--- Detailed Analysis of Safest Route ---")
    safest_analysis = GraphUtils.analyze_route_safety(heatmap, routes[1])
    print(f"Path: {' → '.join(safest_analysis['path'])}")
    print(f"Total Risk: {safest_analysis['total_risk']:.3f}")
    print(f"Avg Risk: {safest_analysis['avg_risk']:.3f}")
    print(f"Max Risk Segment: {safest_analysis['max_risk_segment']} ({safest_analysis['max_risk_value']:.3f})")
    print(f"Safety Level: {safest_analysis['safety_level']}")
    print(f"Recommendation: {safest_analysis['recommendation']}")

    print("\n--- Segment Details ---")
    for segment in safest_analysis['segments']:
        print(f"  {segment['from']} → {segment['to']}: risk {segment['risk']:.3f}")


def example_bottlenecks_and_reachability():
    """Example 5: Finding bottlenecks and reachable zones."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Bottleneck Detection and Reachability Analysis")
    print("=" * 70)

    heatmap_data = {
        "nodes": {
            "Office": {"position": {"x": 0.0, "y": 0.0}, "risk": 0.05},
            "Safe_Zone": {"position": {"x": 2.0, "y": 0.0}, "risk": 0.20},
            "Checkpoint": {"position": {"x": 4.0, "y": 0.0}, "risk": 0.90},  # Bottleneck!
            "Beyond": {"position": {"x": 6.0, "y": 0.0}, "risk": 0.35},
        },
        "edges": {
            "E_S": {"from_node": "Office", "to_node": "Safe_Zone", "risk": 0.10},
            "S_C": {"from_node": "Safe_Zone", "to_node": "Checkpoint", "risk": 0.85},  # Bottleneck!
            "C_B": {"from_node": "Checkpoint", "to_node": "Beyond", "risk": 0.40},
        },
        "updated_at": "2026-02-10T14:30:00Z"
    }

    heatmap = HeatmapAdapter()
    heatmap.load_heatmap(heatmap_data)

    print("\n--- Finding Bottlenecks (risk > 0.80) ---")
    bottlenecks = GraphUtils.find_bottlenecks(heatmap, threshold=0.80)
    for bottleneck in bottlenecks:
        print(f"  {bottleneck['type'].upper()}: {bottleneck.get('id')}")
        print(f"    Risk: {bottleneck['risk']:.2f}")
        if bottleneck['type'] == 'edge':
            print(f"    Route: {bottleneck['from']} → {bottleneck['to']}")

    print("\n--- Reachable Zones from Office (max risk 0.50) ---")
    reachable = GraphUtils.get_reachable_nodes(heatmap, "Office", max_risk=0.50, max_hops=5)
    if reachable:
        for node_id, (risk, hops) in reachable.items():
            print(f"  {node_id}: risk {risk:.3f}, {hops} hops")
    else:
        print("  No zones reachable within constraints")


def example_time_estimation():
    """Example 6: Travel time estimation with risk-based speed adjustments."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Travel Time Estimation")
    print("=" * 70)

    heatmap_data = {
        "nodes": {
            "Start": {"position": {"x": 0.0, "y": 0.0}, "risk": 0.15},
            "Mid_Safe": {"position": {"x": 50.0, "y": 0.0}, "risk": 0.25},
            "Mid_Risk": {"position": {"x": 100.0, "y": 0.0}, "risk": 0.70},
            "End": {"position": {"x": 150.0, "y": 0.0}, "risk": 0.20},
        },
        "edges": {
            "S_M1": {"from_node": "Start", "to_node": "Mid_Safe", "risk": 0.20},
            "M1_M2": {"from_node": "Mid_Safe", "to_node": "Mid_Risk", "risk": 0.60},
            "M2_E": {"from_node": "Mid_Risk", "to_node": "End", "risk": 0.30},
        },
        "updated_at": "2026-02-10T14:30:00Z"
    }

    heatmap = HeatmapAdapter()
    heatmap.load_heatmap(heatmap_data)

    # Route through medium risk
    route = ["Start", "Mid_Safe", "Mid_Risk", "End"]

    print("\n--- Travel Time Analysis ---")
    timing = GraphUtils.estimate_travel_time(heatmap, route, base_speed_ms=20.0)
    print(f"Route: {' → '.join(timing['route'])}")
    print(f"Total Distance: {timing['total_distance']} units")
    print(f"Total Time: {timing['total_time_seconds']:.1f} seconds ({timing['total_time_minutes']:.2f} minutes)")
    print(f"Average Speed: {timing['avg_speed']:.2f} units/sec")

    print("\n--- Segment Details (risk-adjusted speeds) ---")
    for segment in timing['segments']:
        print(f"  {segment['from']} → {segment['to']}")
        print(f"    Distance: {segment['distance']} | Risk Factor: {segment['risk_factor']:.2f}")
        print(f"    Adjusted Speed: {segment['adjusted_speed']:.2f} | Time: {segment['time_seconds']:.1f}s")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("SAFESPHERE SAFE ROUTE ENGINE - HEATMAP ADAPTER EXAMPLES")
    print("=" * 70)

    example_basic_usage()
    example_interpolation()
    example_pathfinding()
    example_route_analysis()
    example_bottlenecks_and_reachability()
    example_time_estimation()

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()

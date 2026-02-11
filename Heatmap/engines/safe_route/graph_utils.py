"""
Graph Utilities for Safe Route Engine

Lightweight helper functions for heatmap graph operations:
- Pathfinding (safest routes)
- Risk analysis
- Reachability checks
- Route optimization

No external libraries - pure algorithmic implementation.
"""

from typing import List, Dict, Tuple, Optional, Set
from heapq import heappush, heappop
from dataclasses import dataclass
import math


@dataclass
class RouteSegment:
    """Represents a segment of a route."""
    from_node: str
    to_node: str
    edge_id: str
    risk: float
    
    def __repr__(self):
        return f"{self.from_node}→{self.to_node} (risk={self.risk:.2f})"


class GraphUtils:
    """Helper utilities for heatmap graph operations."""

    @staticmethod
    def dijkstra_safest_path(
        adapter,
        start_node: str,
        end_node: str,
        max_iterations: int = 1000
    ) -> Optional[Tuple[List[str], float, List[RouteSegment]]]:
        """
        Find safest path from start to end using Dijkstra's algorithm.
        
        Minimizes total risk score, not distance.
        
        Args:
            adapter: HeatmapAdapter instance
            start_node: Starting node ID
            end_node: Destination node ID
            max_iterations: Prevent infinite loops (default 1000)
            
        Returns:
            (node_path, total_risk, route_segments) or None if no path found
            
        Example:
            path, risk, segments = GraphUtils.dijkstra_safest_path(
                heatmap, "zone_A", "zone_D"
            )
            print(f"Path: {path}, Total Risk: {risk:.3f}")
        """
        if start_node == end_node:
            return ([start_node], 0.0, [])

        # Priority queue: (accumulated_risk, current_node, path, segments)
        heap = [(0.0, start_node, [start_node], [])]
        visited = set()
        iterations = 0

        while heap and iterations < max_iterations:
            iterations += 1
            current_risk, current_node, path, segments = heappop(heap)

            if current_node in visited:
                continue

            visited.add(current_node)

            # Check if we reached the destination
            if current_node == end_node:
                return (path, round(current_risk, 3), segments)

            # Explore neighbors
            neighbors = adapter.get_connected_nodes(current_node)
            for next_node, edge_risk in neighbors:
                if next_node not in visited:
                    # Node risk contributes to total
                    next_node_risk = adapter.get_node_risk(next_node) or 0.0
                    # Combined risk: edge risk + node risk (split 50/50)
                    segment_risk = (edge_risk + next_node_risk) / 2.0
                    new_total_risk = current_risk + segment_risk

                    # Find the edge_id for this connection
                    edge_id = None
                    for eid, edata in adapter.edges.items():
                        if edata.get("from_node") == current_node and edata.get("to_node") == next_node:
                            edge_id = eid
                            break

                    new_segment = RouteSegment(
                        from_node=current_node,
                        to_node=next_node,
                        edge_id=edge_id or f"{current_node}_{next_node}",
                        risk=round(segment_risk, 3)
                    )

                    new_segments = segments + [new_segment]
                    heappush(heap, (new_total_risk, next_node, path + [next_node], new_segments))

        return None  # No path found

    @staticmethod
    def find_k_safest_paths(
        adapter,
        start_node: str,
        end_node: str,
        k: int = 3
    ) -> List[Tuple[List[str], float, List[RouteSegment]]]:
        """
        Find up to k safest alternative paths.
        
        Useful for providing route alternatives to users.
        
        Args:
            adapter: HeatmapAdapter instance
            start_node: Starting node ID
            end_node: Destination node ID
            k: Number of paths to find (default 3)
            
        Returns:
            List of (node_path, total_risk, route_segments) tuples, sorted by risk
        """
        paths = []
        blocked_edges = set()

        for _ in range(k):
            # Temporarily block edges from previously found paths
            original_edges = {}
            for edge_id in blocked_edges:
                if edge_id in adapter.edges:
                    original_edges[edge_id] = adapter.edges[edge_id]
                    del adapter.edges[edge_id]

            # Find safest path in modified graph
            result = GraphUtils.dijkstra_safest_path(adapter, start_node, end_node)

            # Restore edges
            for edge_id, edge_data in original_edges.items():
                adapter.edges[edge_id] = edge_data

            if result:
                paths.append(result)
                # Block edges used in this path
                for segment in result[2]:
                    # Find the edge_id
                    for edge_id, edata in adapter.edges.items():
                        if (edata.get("from_node") == segment.from_node and
                                edata.get("to_node") == segment.to_node):
                            blocked_edges.add(edge_id)
                            break
            else:
                break

        return sorted(paths, key=lambda x: x[1])  # Sort by total risk

    @staticmethod
    def is_reachable(adapter, start_node: str, end_node: str, max_risk: float = 1.0) -> bool:
        """
        Check if destination is reachable from start within max risk.
        
        Args:
            adapter: HeatmapAdapter instance
            start_node: Starting node ID
            end_node: Destination node ID
            max_risk: Maximum acceptable path risk (default 1.0 = any path)
            
        Returns:
            True if reachable within risk threshold, False otherwise
        """
        result = GraphUtils.dijkstra_safest_path(adapter, start_node, end_node)
        if result:
            _, total_risk, _ = result
            return total_risk <= max_risk
        return False

    @staticmethod
    def get_reachable_nodes(
        adapter,
        start_node: str,
        max_risk: float = 0.7,
        max_hops: int = 10
    ) -> Dict[str, Tuple[float, int]]:
        """
        Find all nodes reachable from start within max risk.
        
        Args:
            adapter: HeatmapAdapter instance
            start_node: Starting node ID
            max_risk: Maximum path risk to consider (default 0.7)
            max_hops: Maximum number of edges to traverse (default 10)
            
        Returns:
            Dict mapping reachable_node_id -> (total_risk, hops_needed)
        """
        reachable = {}
        visited = set()
        queue = [(start_node, 0.0, 0)]  # (node, accumulated_risk, hop_count)

        while queue:
            current_node, current_risk, hops = queue.pop(0)

            if current_node in visited or hops > max_hops or current_risk > max_risk:
                continue

            visited.add(current_node)
            reachable[current_node] = (round(current_risk, 3), hops)

            # Explore neighbors
            for next_node, edge_risk in adapter.get_connected_nodes(current_node):
                if next_node not in visited:
                    next_node_risk = adapter.get_node_risk(next_node) or 0.0
                    segment_risk = (edge_risk + next_node_risk) / 2.0
                    new_risk = current_risk + segment_risk

                    if new_risk <= max_risk and hops + 1 <= max_hops:
                        queue.append((next_node, new_risk, hops + 1))

        return reachable

    @staticmethod
    def analyze_route_safety(adapter, node_path: List[str]) -> Dict:
        """
        Comprehensive safety analysis of a given route.
        
        Args:
            adapter: HeatmapAdapter instance
            node_path: List of node IDs forming the route
            
        Returns:
            Dict with safety metrics and recommendations
        """
        if not node_path or len(node_path) < 2:
            return {"error": "Invalid route"}

        segments = []
        total_risk = 0.0
        max_risk_segment = None
        max_risk_value = 0.0
        danger_count = 0

        for i in range(len(node_path) - 1):
            from_node = node_path[i]
            to_node = node_path[i + 1]

            # Find edge connecting these nodes
            edge_id = None
            edge_risk = 0.0
            for eid, edata in adapter.edges.items():
                if edata.get("from_node") == from_node and edata.get("to_node") == to_node:
                    edge_id = eid
                    edge_risk = edata.get("risk", 0.0)
                    break

            node_risk = adapter.get_node_risk(to_node) or 0.0
            segment_risk = (edge_risk + node_risk) / 2.0
            segments.append({
                "from": from_node,
                "to": to_node,
                "edge_id": edge_id,
                "risk": round(segment_risk, 3),
            })

            total_risk += segment_risk
            if segment_risk > max_risk_value:
                max_risk_value = segment_risk
                max_risk_segment = to_node
            if segment_risk > 0.7:
                danger_count += 1

        avg_risk = total_risk / len(segments)

        # Safety classification
        if avg_risk < 0.2:
            safety_level = "EXCELLENT"
        elif avg_risk < 0.4:
            safety_level = "GOOD"
        elif avg_risk < 0.6:
            safety_level = "MODERATE"
        elif avg_risk < 0.8:
            safety_level = "RISKY"
        else:
            safety_level = "DANGEROUS"

        return {
            "path": node_path,
            "segment_count": len(segments),
            "total_risk": round(total_risk, 3),
            "avg_risk": round(avg_risk, 3),
            "max_risk_segment": max_risk_segment,
            "max_risk_value": round(max_risk_value, 3),
            "danger_count": danger_count,
            "safety_level": safety_level,
            "segments": segments,
            "recommendation": GraphUtils._get_recommendation(safety_level, avg_risk),
        }

    @staticmethod
    def _get_recommendation(safety_level: str, avg_risk: float) -> str:
        """Generate textual recommendation based on safety level."""
        recommendations = {
            "EXCELLENT": "Route is very safe. Standard precautions apply.",
            "GOOD": "Route is safe. Proceed with normal awareness.",
            "MODERATE": "Route has some mid-risk areas. Maintain vigilance.",
            "RISKY": "Route passes through high-risk areas. Enhanced security recommended.",
            "DANGEROUS": "Route is highly dangerous. Consider alternatives or police escort.",
        }
        return recommendations.get(safety_level, f"Risk level: {avg_risk:.2f}")

    @staticmethod
    def compare_routes(
        adapter,
        routes: List[List[str]],
        verbose: bool = False
    ) -> Dict:
        """
        Compare multiple routes and rank by safety.
        
        Args:
            adapter: HeatmapAdapter instance
            routes: List of routes (each route is a list of node IDs)
            verbose: Include segments in output
            
        Returns:
            Dict with ranked routes and comparison stats
        """
        analyses = []
        for route in routes:
            analysis = GraphUtils.analyze_route_safety(adapter, route)
            analyses.append(analysis)

        # Sort by total risk
        ranked = sorted(analyses, key=lambda x: x.get("total_risk", float('inf')))

        return {
            "routes_compared": len(routes),
            "safest_route": ranked[0] if ranked else None,
            "ranked_routes": ranked if verbose else [
                {"path": r["path"], "total_risk": r["total_risk"], "safety_level": r["safety_level"]}
                for r in ranked
            ],
        }

    @staticmethod
    def find_bottlenecks(adapter, threshold: float = 0.8) -> List[Dict]:
        """
        Find critical high-risk edges/nodes (bottlenecks).
        
        Args:
            adapter: HeatmapAdapter instance
            threshold: Risk threshold above which edges are critical (default 0.8)
            
        Returns:
            List of bottleneck nodes and edges with high risk
        """
        bottlenecks = []

        # Check nodes
        for node_id, node_data in adapter.nodes.items():
            risk = node_data.get("risk", 0.0)
            if risk >= threshold:
                bottlenecks.append({
                    "type": "node",
                    "id": node_id,
                    "risk": round(risk, 3),
                    "name": node_data.get("name", "Unknown"),
                })

        # Check edges
        for edge_id, edge_data in adapter.edges.items():
            risk = edge_data.get("risk", 0.0)
            if risk >= threshold:
                bottlenecks.append({
                    "type": "edge",
                    "id": edge_id,
                    "from": edge_data.get("from_node"),
                    "to": edge_data.get("to_node"),
                    "risk": round(risk, 3),
                })

        return sorted(bottlenecks, key=lambda x: x["risk"], reverse=True)

    @staticmethod
    def estimate_travel_time(
        adapter,
        route: List[str],
        base_speed_ms: float = 10.0
    ) -> Dict:
        """
        Estimate travel time considering risk-based speed adjustments.
        
        Higher risk areas require slower movement (caution).
        
        Args:
            adapter: HeatmapAdapter instance
            route: List of node IDs forming the route
            base_speed_ms: Base speed in units/second (default 10.0)
            
        Returns:
            Dict with time estimates
        """
        if len(route) < 2:
            return {"error": "Invalid route"}

        total_distance = 0.0
        total_time = 0.0
        segments_time = []

        positions = {}
        for node_id in adapter.nodes:
            if "position" in adapter.nodes[node_id]:
                pos = adapter.nodes[node_id]["position"]
                positions[node_id] = pos

        for i in range(len(route) - 1):
            from_node = route[i]
            to_node = route[i + 1]

            # Calculate distance if positions are available
            if from_node in positions and to_node in positions:
                p1 = positions[from_node]
                p2 = positions[to_node]
                distance = math.sqrt((p1["x"] - p2["x"]) ** 2 + (p1["y"] - p2["y"]) ** 2)
            else:
                distance = 1.0  # Default unit distance

            # Get risk factor
            edge_risk = 0.0
            for eid, edata in adapter.edges.items():
                if edata.get("from_node") == from_node and edata.get("to_node") == to_node:
                    edge_risk = edata.get("risk", 0.0)
                    break

            node_risk = adapter.get_node_risk(to_node) or 0.0
            avg_risk = (edge_risk + node_risk) / 2.0

            # Speed multiplier (higher risk = slower)
            # At risk 0.0: speed = base_speed
            # At risk 0.5: speed = 0.5 * base_speed
            # At risk 1.0: speed = 0.25 * base_speed
            speed_multiplier = 1.0 - (avg_risk * 0.75)
            actual_speed = base_speed_ms * speed_multiplier

            segment_time = distance / actual_speed if actual_speed > 0 else float('inf')
            segments_time.append({
                "from": from_node,
                "to": to_node,
                "distance": round(distance, 2),
                "risk_factor": round(avg_risk, 3),
                "adjusted_speed": round(actual_speed, 2),
                "time_seconds": round(segment_time, 1),
            })

            total_distance += distance
            total_time += segment_time

        return {
            "route": route,
            "total_distance": round(total_distance, 2),
            "total_time_seconds": round(total_time, 1),
            "total_time_minutes": round(total_time / 60, 2),
            "avg_speed": round(total_distance / total_time, 2) if total_time > 0 else 0.0,
            "segments": segments_time,
        }

    @staticmethod
    def validate_route_safety(
        coordinates: List[Tuple[float, float]],
        threat_zone_manager,
        strict_mode: bool = True,
        buffer_km: float = 0.1
    ) -> Dict:
        """
        Validate if a route is safe by checking against threat zones.
        
        This method ensures routes do not intersect with threat circles,
        providing hard safety guarantees rather than soft scoring.
        
        Args:
            coordinates: List of (lng, lat) tuples forming the route
            threat_zone_manager: ThreatZoneManager instance with loaded threats
            strict_mode: If True, reject routes touching threat zones
            buffer_km: Safety buffer around threat zones
            
        Returns:
            Dict with:
            - is_safe: bool - True if route is safe
            - threat_intersections: List of intersected threat zones
            - closest_threat: Dict with nearest threat info
            - safety_score: float 0.0-1.0 (1.0 = completely safe)
        """
        # Check for intersections with threat zones
        intersects, first_zone = threat_zone_manager.route_intersects_any_threat(
            coordinates,
            buffer_km=buffer_km,
            threat_levels_to_avoid=["CRITICAL", "HIGH", "MEDIUM"]
        )
        
        threat_intersections = []
        if intersects:
            threat_intersections.append({
                "zone_id": first_zone.zone_id,
                "threat_level": first_zone.threat_level,
                "radius_km": first_zone.radius_km,
            })
        
        # Get closest threat
        closest = threat_zone_manager.get_closest_threat_to_route(coordinates)
        
        # Calculate safety score
        if closest:
            min_dist = closest.get("min_distance_km", 0)
            # Safety score: 1.0 if >2km away, 0.0 if inside threat zone, linear in between
            safety_score = max(0.0, min(1.0, min_dist / 2.0))
            is_inside_zone = closest.get("inside_zone", False)
            is_safe = not is_inside_zone and not intersects
        else:
            safety_score = 1.0
            is_safe = True
        
        return {
            "is_safe": is_safe,
            "threat_intersections": threat_intersections,
            "closest_threat": closest,
            "safety_score": round(safety_score, 3),
            "has_critical_threat": len([t for t in threat_intersections if t["threat_level"] == "CRITICAL"]) > 0,
        }

    @staticmethod
    def rank_routes_by_safety(
        routes: List[Dict],
        threat_zone_manager,
        keep_unsafe: bool = False
    ) -> List[Dict]:
        """
        Rank routes by safety, filtering out those that cross threat zones.
        
        Args:
            routes: List of dicts with 'geometry' containing coordinates
            threat_zone_manager: ThreatZoneManager with loaded threats
            keep_unsafe: If True, keep unsafe routes but rank them lower
            
        Returns:
            Sorted list of routes with safety metrics added
        """
        ranked_routes = []
        
        for route in routes:
            coordinates = route.get("geometry", {}).get("coordinates", [])
            if not coordinates:
                ranked_routes.append({
                    **route,
                    "safety_metrics": {
                        "is_safe": True,
                        "safety_score": 1.0,
                        "threat_intersections": [],
                    }
                })
                continue
            
            safety_metrics = GraphUtils.validate_route_safety(
                coordinates,
                threat_zone_manager,
                strict_mode=True,
                buffer_km=0.1
            )
            
            ranked_routes.append({
                **route,
                "safety_metrics": safety_metrics,
            })
        
        # Sort by safety score (higher is better), then filter
        ranked_routes.sort(key=lambda r: r["safety_metrics"]["safety_score"], reverse=True)
        
        if not keep_unsafe:
            # Keep only safe routes, or if none exist, keep all
            safe_routes = [r for r in ranked_routes if r["safety_metrics"]["is_safe"]]
            if safe_routes:
                ranked_routes = safe_routes
        
        return ranked_routes

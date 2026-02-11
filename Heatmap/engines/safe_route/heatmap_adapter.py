"""
SafeSphere HeatmapAdapter Module

Lightweight, backend-friendly heatmap adapter for Safe Route Engine.
Accepts risk data from backend and provides efficient query functions
for nodes and edges in a road/zone network.

No external map APIs or ML models - purely algorithmic logic.
"""

from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
import math


@dataclass
class Position:
    """Represents a geographic coordinate or zone identifier."""
    x: float
    y: float

    def distance_to(self, other: 'Position') -> float:
        """Euclidean distance to another position."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def __hash__(self):
        return hash((round(self.x, 6), round(self.y, 6)))

    def __eq__(self, other):
        return isinstance(other, Position) and self.x == other.x and self.y == other.y


class HeatmapAdapter:
    """
    Manages risk heatmap data for a road/zone network.
    
    Structure:
    - Nodes: Geographic points (intersections, zones) with risk scores
    - Edges: Road segments connecting nodes, also with risk scores
    - Risk scores: 0.0 (safe) to 1.0 (extremely dangerous)
    
    Example backend data format:
    {
        "nodes": {
            "(0.0, 0.0)": {"position": {...}, "risk": 0.1},
            "(1.0, 0.0)": {"position": {...}, "risk": 0.5},
        },
        "edges": {
            "((0.0,0.0), (1.0,0.0))": {"risk": 0.3},
        }
    }
    """

    def __init__(self):
        """Initialize empty heatmap."""
        self.nodes: Dict[str, Dict] = {}  # node_id -> {position, risk, metadata}
        self.edges: Dict[str, Dict] = {}  # edge_id -> {from_node, to_node, risk, metadata}
        self.position_to_node_id: Dict[Position, str] = {}  # quick lookup
        self.updated_at: str = ""

    def load_heatmap(self, heatmap_data: Dict) -> None:
        """
        Load heatmap data from backend.
        
        Args:
            heatmap_data: Dict with 'nodes' and 'edges' keys containing risk data
            
        Example:
            {
                "nodes": {
                    "zone_A": {"position": {"x": 0.0, "y": 0.0}, "risk": 0.15, "name": "Main Gate"},
                    "zone_B": {"position": {"x": 1.5, "y": 2.0}, "risk": 0.45, "name": "Parking Lot"},
                },
                "edges": {
                    "A_to_B": {"from_node": "zone_A", "to_node": "zone_B", "risk": 0.25},
                },
                "updated_at": "2026-02-10T14:30:00Z"
            }
        """
        self.nodes = heatmap_data.get("nodes", {})
        self.edges = heatmap_data.get("edges", {})
        self.updated_at = heatmap_data.get("updated_at", "")

        # Build position lookup table
        self.position_to_node_id = {}
        for node_id, node_data in self.nodes.items():
            if "position" in node_data:
                pos_dict = node_data["position"]
                pos = Position(pos_dict["x"], pos_dict["y"])
                self.position_to_node_id[pos] = node_id

    def get_node_risk(self, node_id: str) -> Optional[float]:
        """
        Get risk score for a specific node.
        
        Args:
            node_id: Identifier of the node (e.g., "zone_A")
            
        Returns:
            Risk score (0.0-1.0) or None if node not found
        """
        if node_id not in self.nodes:
            return None
        return self.nodes[node_id].get("risk", 0.0)

    def get_edge_risk(self, edge_id: str) -> Optional[float]:
        """
        Get risk score for a specific edge (road segment).
        
        Args:
            edge_id: Identifier of the edge (e.g., "A_to_B")
            
        Returns:
            Risk score (0.0-1.0) or None if edge not found
        """
        if edge_id not in self.edges:
            return None
        return self.edges[edge_id].get("risk", 0.0)

    def get_node_risk_by_position(self, position: Position, tolerance: float = 0.1) -> Optional[float]:
        """
        Find nearest node and return its risk score.
        
        Args:
            position: Geographic position to query
            tolerance: Maximum distance to consider (default 0.1 units)
            
        Returns:
            Risk score of nearest node within tolerance, or None
        """
        nearest_node_id = None
        nearest_distance = tolerance

        for pos, node_id in self.position_to_node_id.items():
            dist = position.distance_to(pos)
            if dist < nearest_distance:
                nearest_distance = dist
                nearest_node_id = node_id

        if nearest_node_id:
            return self.get_node_risk(nearest_node_id)
        return None

    def get_interpolated_risk(self, position: Position, k: int = 3) -> float:
        """
        Interpolate risk at a position using k-nearest neighbors (IDW).
        
        Uses Inverse Distance Weighting (IDW) to estimate risk at arbitrary positions
        based on nearby known nodes.
        
        Args:
            position: Geographic position to estimate risk for
            k: Number of nearest neighbors to use (default 3)
            
        Returns:
            Interpolated risk score (0.0-1.0)
        """
        if not self.position_to_node_id:
            return 0.5  # Default middle risk if no nodes

        # Find k nearest nodes
        distances_and_risks = []
        for pos, node_id in self.position_to_node_id.items():
            dist = position.distance_to(pos)
            risk = self.get_node_risk(node_id)
            if risk is not None:
                distances_and_risks.append((dist, risk))

        # Sort by distance
        distances_and_risks.sort(key=lambda x: x[0])
        nearest_k = distances_and_risks[:k]

        if not nearest_k:
            return 0.5

        # Handle case where position exactly matches a node
        if nearest_k[0][0] == 0:
            return nearest_k[0][1]

        # IDW interpolation
        total_weight = 0.0
        weighted_risk = 0.0
        for distance, risk in nearest_k:
            weight = 1.0 / (distance ** 2)  # Inverse square distance
            weighted_risk += weight * risk
            total_weight += weight

        return min(1.0, max(0.0, weighted_risk / total_weight))

    def find_safe_zones(self, threshold: float = 0.3) -> List[str]:
        """
        Find all zones below risk threshold.
        
        Args:
            threshold: Risk score below which zones are considered safe (default 0.3)
            
        Returns:
            List of safe node IDs
        """
        safe_zones = []
        for node_id, node_data in self.nodes.items():
            risk = node_data.get("risk", 0.0)
            if risk < threshold:
                safe_zones.append(node_id)
        return safe_zones

    def find_danger_zones(self, threshold: float = 0.7) -> List[str]:
        """
        Find all zones above risk threshold.
        
        Args:
            threshold: Risk score above which zones are dangerous (default 0.7)
            
        Returns:
            List of dangerous node IDs
        """
        danger_zones = []
        for node_id, node_data in self.nodes.items():
            risk = node_data.get("risk", 0.0)
            if risk >= threshold:
                danger_zones.append(node_id)
        return danger_zones

    def get_zone_metadata(self, node_id: str) -> Optional[Dict]:
        """
        Get metadata for a zone (name, type, etc).
        
        Args:
            node_id: Zone identifier
            
        Returns:
            Metadata dict or None if node not found
        """
        if node_id not in self.nodes:
            return None
        node = self.nodes[node_id]
        return {k: v for k, v in node.items() if k not in ["position", "risk"]}

    def get_route_risk(self, edge_ids: List[str]) -> Dict:
        """
        Analyze total risk of a route (sequence of edges).
        
        Args:
            edge_ids: List of edge IDs forming a route
            
        Returns:
            Dict with overall_risk, max_risk, avg_risk, danger_count
        """
        if not edge_ids:
            return {"overall_risk": 0.0, "max_risk": 0.0, "avg_risk": 0.0, "danger_count": 0}

        risks = [self.get_edge_risk(edge_id) for edge_id in edge_ids]
        risks = [r for r in risks if r is not None]

        if not risks:
            return {"overall_risk": 0.0, "max_risk": 0.0, "avg_risk": 0.0, "danger_count": 0}

        max_risk = max(risks)
        avg_risk = sum(risks) / len(risks)
        danger_count = sum(1 for r in risks if r > 0.7)

        # Overall risk is weighted average (max risk has more weight)
        overall_risk = (avg_risk * 0.4) + (max_risk * 0.6)

        return {
            "overall_risk": round(overall_risk, 3),
            "max_risk": round(max_risk, 3),
            "avg_risk": round(avg_risk, 3),
            "danger_count": danger_count,
            "total_edges": len(risks),
        }

    def get_connected_nodes(self, node_id: str) -> List[Tuple[str, float]]:
        """
        Get all nodes connected to a given node via edges, with edge risks.
        
        Args:
            node_id: Source node ID
            
        Returns:
            List of (connected_node_id, edge_risk) tuples
        """
        connected = []
        for edge_id, edge_data in self.edges.items():
            if edge_data.get("from_node") == node_id:
                to_node = edge_data.get("to_node")
                edge_risk = edge_data.get("risk", 0.0)
                connected.append((to_node, edge_risk))
        return connected

    def get_safest_neighbor(self, node_id: str) -> Optional[Tuple[str, float]]:
        """
        Find safest connected node from current node.
        
        Args:
            node_id: Source node ID
            
        Returns:
            (neighbor_node_id, combined_edge_and_node_risk) or None
        """
        neighbors = self.get_connected_nodes(node_id)
        if not neighbors:
            return None

        best_neighbor = None
        best_risk = float('inf')

        for neighbor_id, edge_risk in neighbors:
            node_risk = self.get_node_risk(neighbor_id) or 0.0
            # Combined risk: average of edge risk and destination node risk
            combined_risk = (edge_risk + node_risk) / 2.0
            if combined_risk < best_risk:
                best_risk = combined_risk
                best_neighbor = (neighbor_id, round(best_risk, 3))

        return best_neighbor

    def get_riskiest_neighbor(self, node_id: str) -> Optional[Tuple[str, float]]:
        """
        Find riskiest connected node (to avoid).
        
        Args:
            node_id: Source node ID
            
        Returns:
            (neighbor_node_id, combined_edge_and_node_risk) or None
        """
        neighbors = self.get_connected_nodes(node_id)
        if not neighbors:
            return None

        worst_neighbor = None
        worst_risk = -1.0

        for neighbor_id, edge_risk in neighbors:
            node_risk = self.get_node_risk(neighbor_id) or 0.0
            combined_risk = (edge_risk + node_risk) / 2.0
            if combined_risk > worst_risk:
                worst_risk = combined_risk
                worst_neighbor = (neighbor_id, round(worst_risk, 3))

        return worst_neighbor

    def get_stats(self) -> Dict:
        """
        Get overall heatmap statistics.
        
        Returns:
            Dict with node_count, edge_count, avg_node_risk, max_node_risk, etc.
        """
        if not self.nodes:
            return {
                "node_count": 0,
                "edge_count": 0,
                "avg_node_risk": 0.0,
                "max_node_risk": 0.0,
                "min_node_risk": 0.0,
                "safe_zones": 0,
                "danger_zones": 0,
            }

        node_risks = [n.get("risk", 0.0) for n in self.nodes.values()]
        edge_risks = [e.get("risk", 0.0) for e in self.edges.values()]

        safe_count = len(self.find_safe_zones())
        danger_count = len(self.find_danger_zones())

        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "avg_node_risk": round(sum(node_risks) / len(node_risks), 3) if node_risks else 0.0,
            "max_node_risk": round(max(node_risks), 3) if node_risks else 0.0,
            "min_node_risk": round(min(node_risks), 3) if node_risks else 0.0,
            "avg_edge_risk": round(sum(edge_risks) / len(edge_risks), 3) if edge_risks else 0.0,
            "safe_zones": safe_count,
            "danger_zones": danger_count,
            "updated_at": self.updated_at,
        }

    def get_risk_distribution(self) -> Dict[str, int]:
        """
        Get distribution of risk levels (how many zones in each risk band).
        
        Returns:
            Dict with risk band count: {safe: N, low: N, medium: N, high: N, critical: N}
        """
        distribution = {"safe": 0, "low": 0, "medium": 0, "high": 0, "critical": 0}

        for node_data in self.nodes.values():
            risk = node_data.get("risk", 0.0)
            if risk < 0.2:
                distribution["safe"] += 1
            elif risk < 0.4:
                distribution["low"] += 1
            elif risk < 0.6:
                distribution["medium"] += 1
            elif risk < 0.8:
                distribution["high"] += 1
            else:
                distribution["critical"] += 1

        return distribution

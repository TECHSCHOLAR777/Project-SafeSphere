"""
SafeSphere Road Graph Module

Builds a road network graph using NetworkX with integrated heatmap risk scoring.

Nodes: Geographic locations/zones
Edges: Road segments with distance costs
Integration: Heatmap risk multipliers for cost calculation

Cost Function:
    edge_cost = base_distance * (1 + risk_penalty_factor * heatmap_risk)

Where risk_penalty_factor controls how much risk affects routing cost.
Higher risk = higher cost = less likely to be chosen in pathfinding.
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import math
import networkx as nx
from networkx import Graph, DiGraph


@dataclass
class RoadNode:
    """Represents a node (zone/location) in the road network."""
    node_id: str
    position: Tuple[float, float]  # (x, y)
    name: str = ""
    node_type: str = "zone"  # intersection, entrance, zone, poi
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def distance_to(self, other: 'RoadNode') -> float:
        """Euclidean distance to another node."""
        x1, y1 = self.position
        x2, y2 = other.position
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


@dataclass
class RoadEdge:
    """Represents an edge (road segment) in the road network."""
    edge_id: str
    from_node: str
    to_node: str
    distance: float  # Base distance cost
    road_type: str = "road"  # road, path, corridor, emergency_exit
    speed_limit: float = 1.0  # Base speed units/second
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RoadGraph:
    """
    Road network graph with integrated heatmap risk scoring.
    
    Uses NetworkX as the underlying graph structure.
    Combines distance costs with risk penalties for intelligent routing.
    """

    def __init__(self, directed: bool = True, risk_penalty_factor: float = 50.0):
        """
        Initialize road graph.
        
        Args:
            directed: If True, creates directed graph (one-way roads possible)
            risk_penalty_factor: Multiplier for risk impact on edge cost
                                 Higher value = risk has more effect
                                 (default 50.0 means 1.0 risk adds 50x distance cost)
        """
        self.directed = directed
        self.risk_penalty_factor = risk_penalty_factor
        
        # Use directed or undirected graph
        self.graph = DiGraph() if directed else Graph()
        
        # Keep references to nodes and edges for faster lookup
        self.nodes_dict: Dict[str, RoadNode] = {}
        self.edges_dict: Dict[str, RoadEdge] = {}
        
        # Store heatmap risk scores (node_id -> risk, edge_id -> risk)
        self.node_risks: Dict[str, float] = {}
        self.edge_risks: Dict[str, float] = {}

    def add_node(self, road_node: RoadNode) -> None:
        """
        Add a node (zone/location) to the road graph.
        
        Args:
            road_node: RoadNode with id, position, name, type
        """
        self.nodes_dict[road_node.node_id] = road_node
        
        # Add to NetworkX graph with attributes
        self.graph.add_node(
            road_node.node_id,
            position=road_node.position,
            name=road_node.name,
            node_type=road_node.node_type,
            **road_node.metadata
        )

    def add_edge(self, road_edge: RoadEdge) -> None:
        """
        Add an edge (road segment) to the road graph.
        
        Args:
            road_edge: RoadEdge with from_node, to_node, distance
        """
        self.edges_dict[road_edge.edge_id] = road_edge
        
        # Calculate initial cost (distance only)
        cost = road_edge.distance
        
        # Add to NetworkX graph with attributes
        self.graph.add_edge(
            road_edge.from_node,
            road_edge.to_node,
            edge_id=road_edge.edge_id,
            distance=road_edge.distance,
            cost=cost,  # Will be updated when risks are added
            road_type=road_edge.road_type,
            speed_limit=road_edge.speed_limit,
            **road_edge.metadata
        )

    def load_heatmap_risks(self, heatmap: 'HeatmapAdapter') -> None:
        """
        Integrate heatmap risk scores into the road graph.
        
        Updates edge costs based on node and edge risks from heatmap.
        
        Args:
            heatmap: HeatmapAdapter instance with risk data
        """
        # Store heatmap reference
        self.heatmap = heatmap
        
        # Update node risks
        for node_id in self.nodes_dict:
            risk = heatmap.get_node_risk(node_id)
            if risk is not None:
                self.node_risks[node_id] = risk
        
        # Update edge costs based on combined node and edge risks
        for edge_id, edge in self.edges_dict.items():
            edge_risk = heatmap.get_edge_risk(edge_id)
            from_risk = self.node_risks.get(edge.from_node, 0.0)
            to_risk = self.node_risks.get(edge.to_node, 0.0)
            
            if edge_risk is not None:
                self.edge_risks[edge_id] = edge_risk
            else:
                # Average of node risks if edge risk not available
                self.edge_risks[edge_id] = (from_risk + to_risk) / 2.0
            
            # Calculate risk-adjusted cost
            self._update_edge_cost(edge_id)

    def _update_edge_cost(self, edge_id: str) -> None:
        """
        Update edge cost based on distance and risk.
        
        Cost = distance * (1 + risk_penalty_factor * total_risk)
        
        Args:
            edge_id: Edge identifier
        """
        edge = self.edges_dict.get(edge_id)
        if not edge:
            return
        
        base_distance = edge.distance
        heatmap_risk = self.edge_risks.get(edge_id, 0.0)
        
        # Cost function: penalize risk heavily
        # At risk 0.0: cost = distance
        # At risk 0.5: cost = distance * (1 + 25) = 26x distance
        # At risk 1.0: cost = distance * (1 + 50) = 51x distance
        risk_multiplier = 1.0 + (self.risk_penalty_factor * heatmap_risk)
        adjusted_cost = base_distance * risk_multiplier
        
        # Update in NetworkX graph
        self.graph[edge.from_node][edge.to_node]['cost'] = adjusted_cost
        self.graph[edge.from_node][edge.to_node]['risk'] = heatmap_risk
        self.graph[edge.from_node][edge.to_node]['risk_multiplier'] = risk_multiplier

    def get_node(self, node_id: str) -> Optional[RoadNode]:
        """Get node by ID."""
        return self.nodes_dict.get(node_id)

    def get_edge(self, edge_id: str) -> Optional[RoadEdge]:
        """Get edge by ID."""
        return self.edges_dict.get(edge_id)

    def get_edge_cost(self, from_node: str, to_node: str) -> Optional[float]:
        """
        Get total cost of traversing an edge (distance + risk penalty).
        
        Args:
            from_node: Source node ID
            to_node: Destination node ID
            
        Returns:
            Total cost or None if edge doesn't exist
        """
        if self.graph.has_edge(from_node, to_node):
            return self.graph[from_node][to_node].get('cost', 0.0)
        return None

    def get_edge_distance(self, from_node: str, to_node: str) -> Optional[float]:
        """Get base distance of an edge (without risk penalty)."""
        if self.graph.has_edge(from_node, to_node):
            return self.graph[from_node][to_node].get('distance', 0.0)
        return None

    def get_edge_risk(self, from_node: str, to_node: str) -> Optional[float]:
        """Get risk score of an edge."""
        if self.graph.has_edge(from_node, to_node):
            return self.graph[from_node][to_node].get('risk', 0.0)
        return None

    def get_neighbors(self, node_id: str) -> List[Tuple[str, float, float]]:
        """
        Get all neighbors of a node with their costs and risks.
        
        Args:
            node_id: Node ID
            
        Returns:
            List of (neighbor_id, cost, risk) tuples
        """
        neighbors = []
        if node_id in self.graph:
            for neighbor in self.graph.neighbors(node_id):
                cost = self.get_edge_cost(node_id, neighbor) or 0.0
                risk = self.get_edge_risk(node_id, neighbor) or 0.0
                neighbors.append((neighbor, cost, risk))
        return neighbors

    def get_nodes_count(self) -> int:
        """Get total number of nodes."""
        return self.graph.number_of_nodes()

    def get_edges_count(self) -> int:
        """Get total number of edges."""
        return self.graph.number_of_edges()

    def get_all_nodes(self) -> List[str]:
        """Get all node IDs."""
        return list(self.graph.nodes())

    def get_all_edges(self) -> List[Tuple[str, str]]:
        """Get all edges as (from_node, to_node) tuples."""
        return list(self.graph.edges())

    def get_graph_stats(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics."""
        nodes = self.get_all_nodes()
        edges = self.get_all_edges()
        
        if not edges:
            return {
                "node_count": len(nodes),
                "edge_count": 0,
                "is_connected": False,
                "avg_distance": 0.0,
                "avg_risk": 0.0,
                "avg_cost": 0.0,
                "max_cost": 0.0,
                "min_cost": 0.0,
            }
        
        # Calculate statistics
        distances = [self.get_edge_distance(u, v) for u, v in edges if self.get_edge_distance(u, v)]
        risks = [self.get_edge_risk(u, v) for u, v in edges if self.get_edge_risk(u, v) is not None]
        costs = [self.get_edge_cost(u, v) for u, v in edges if self.get_edge_cost(u, v)]
        
        # Check connectivity
        is_connected = nx.is_strongly_connected(self.graph) if self.directed else nx.is_connected(self.graph)
        
        return {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "is_directed": self.directed,
            "is_connected": is_connected,
            "avg_distance": sum(distances) / len(distances) if distances else 0.0,
            "avg_risk": sum(risks) / len(risks) if risks else 0.0,
            "avg_cost": sum(costs) / len(costs) if costs else 0.0,
            "max_cost": max(costs) if costs else 0.0,
            "min_cost": min(costs) if costs else 0.0,
            "risk_penalty_factor": self.risk_penalty_factor,
        }

    def get_high_risk_edges(self, threshold: float = 0.7) -> List[Dict]:
        """
        Find edges with risk above threshold.
        
        Args:
            threshold: Risk threshold (default 0.7)
            
        Returns:
            List of dicts with edge info and risks
        """
        high_risk = []
        for u, v in self.get_all_edges():
            risk = self.get_edge_risk(u, v)
            if risk and risk >= threshold:
                high_risk.append({
                    "from": u,
                    "to": v,
                    "risk": risk,
                    "distance": self.get_edge_distance(u, v),
                    "cost": self.get_edge_cost(u, v),
                })
        return sorted(high_risk, key=lambda x: x["risk"], reverse=True)

    def get_low_risk_edges(self, threshold: float = 0.3) -> List[Dict]:
        """
        Find edges with risk below threshold.
        
        Args:
            threshold: Risk threshold (default 0.3)
            
        Returns:
            List of dicts with edge info and risks
        """
        low_risk = []
        for u, v in self.get_all_edges():
            risk = self.get_edge_risk(u, v)
            if risk is not None and risk < threshold:
                low_risk.append({
                    "from": u,
                    "to": v,
                    "risk": risk,
                    "distance": self.get_edge_distance(u, v),
                    "cost": self.get_edge_cost(u, v),
                })
        return sorted(low_risk, key=lambda x: x["risk"])

    def cost_breakdown(self, from_node: str, to_node: str) -> Optional[Dict]:
        """
        Get detailed cost breakdown for an edge.
        
        Shows how the final cost is calculated from distance and risk.
        
        Args:
            from_node: Source node
            to_node: Destination node
            
        Returns:
            Dict with distance, risk, multiplier, and final cost
        """
        distance = self.get_edge_distance(from_node, to_node)
        risk = self.get_edge_risk(from_node, to_node)
        cost = self.get_edge_cost(from_node, to_node)
        
        if distance is None:
            return None
        
        risk = risk or 0.0
        risk_multiplier = 1.0 + (self.risk_penalty_factor * risk)
        
        return {
            "from_node": from_node,
            "to_node": to_node,
            "base_distance": round(distance, 3),
            "heatmap_risk": round(risk, 3),
            "risk_multiplier": round(risk_multiplier, 3),
            "final_cost": round(cost or distance * risk_multiplier, 3),
            "cost_formula": f"{distance:.2f} × {risk_multiplier:.2f} = {cost:.2f}",
        }

    def update_risk_penalty_factor(self, factor: float) -> None:
        """
        Update the risk penalty factor and recalculate all edge costs.
        
        Useful for adjusting how much risk affects routing.
        
        Args:
            factor: New penalty factor (e.g., 50.0)
        """
        self.risk_penalty_factor = factor
        
        # Recalculate all edge costs
        for edge_id in self.edges_dict:
            self._update_edge_cost(edge_id)

    def get_connectivity_matrix(self) -> Dict[str, List[str]]:
        """
        Get adjacency list showing which nodes are directly connected.
        
        Returns:
            Dict mapping node_id -> [list of connected node_ids]
        """
        matrix = {}
        for node_id in self.get_all_nodes():
            neighbors = [n for n, _, _ in self.get_neighbors(node_id)]
            matrix[node_id] = neighbors
        return matrix

    def validate_graph(self) -> Tuple[bool, List[str]]:
        """
        Validate graph integrity.
        
        Checks:
        - All edges reference existing nodes
        - All nodes have positions
        - No self-loops (unless explicitly allowed)
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Check edges reference valid nodes
        valid_nodes = set(self.get_all_nodes())
        for from_node, to_node in self.get_all_edges():
            if from_node not in valid_nodes:
                errors.append(f"Edge references invalid from_node: {from_node}")
            if to_node not in valid_nodes:
                errors.append(f"Edge references invalid to_node: {to_node}")
        
        # Check nodes have positions
        for node_id, node in self.nodes_dict.items():
            if node.position is None or len(node.position) != 2:
                errors.append(f"Node {node_id} has invalid position: {node.position}")
        
        # Check for self-loops
        for from_node, to_node in self.get_all_edges():
            if from_node == to_node:
                errors.append(f"Self-loop detected: {from_node}")
        
        return (len(errors) == 0, errors)

    def export_to_dict(self) -> Dict:
        """
        Export graph structure to dictionary format (serializable).
        
        Useful for saving/transferring graph state.
        
        Returns:
            Dict with nodes and edges
        """
        nodes = {}
        for node_id, node in self.nodes_dict.items():
            nodes[node_id] = {
                "position": node.position,
                "name": node.name,
                "type": node.node_type,
                "risk": self.node_risks.get(node_id, 0.0),
                "metadata": node.metadata,
            }
        
        edges = {}
        for (u, v) in self.get_all_edges():
            edge_key = f"{u}_{v}"
            edges[edge_key] = {
                "from_node": u,
                "to_node": v,
                "distance": self.get_edge_distance(u, v),
                "risk": self.get_edge_risk(u, v),
                "cost": self.get_edge_cost(u, v),
                "metadata": self.graph[u][v].get("metadata", {}),
            }
        
        return {
            "nodes": nodes,
            "edges": edges,
            "directed": self.directed,
            "risk_penalty_factor": self.risk_penalty_factor,
            "stats": self.get_graph_stats(),
        }

    def import_from_dict(self, data: Dict) -> None:
        """
        Import graph structure from dictionary.
        
        Args:
            data: Dictionary from export_to_dict()
        """
        # Clear current graph
        self.graph.clear()
        self.nodes_dict.clear()
        self.edges_dict.clear()
        self.node_risks.clear()
        self.edge_risks.clear()
        
        # Import nodes
        for node_id, node_data in data.get("nodes", {}).items():
            node = RoadNode(
                node_id=node_id,
                position=tuple(node_data["position"]),
                name=node_data.get("name", ""),
                node_type=node_data.get("type", "zone"),
                metadata=node_data.get("metadata", {})
            )
            self.add_node(node)
            self.node_risks[node_id] = node_data.get("risk", 0.0)
        
        # Import edges
        for edge_key, edge_data in data.get("edges", {}).items():
            edge = RoadEdge(
                edge_id=edge_key,
                from_node=edge_data["from_node"],
                to_node=edge_data["to_node"],
                distance=edge_data.get("distance", 0.0),
                metadata=edge_data.get("metadata", {})
            )
            self.add_edge(edge)
            risk = edge_data.get("risk", 0.0)
            self.edge_risks[edge_key] = risk
            self._update_edge_cost(edge_key)
        
        self.risk_penalty_factor = data.get("risk_penalty_factor", 50.0)

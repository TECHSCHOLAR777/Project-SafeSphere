# SafeSphere Safe Route Engine - HeatmapAdapter Module

## Overview

The **HeatmapAdapter** is a lightweight, backend-friendly module for the Safe Route Engine that manages risk heatmap data and provides efficient query functions for safe route planning.

**Key Features:**
- ✓ No external map APIs required
- ✓ No machine learning models
- ✓ Pure algorithmic implementation
- ✓ Backend integration ready
- ✓ Explainable logic

---

## Architecture

### Data Model

The heatmap represents a **graph of zones/intersections** (nodes) and **road segments** (edges), each with a risk score (0.0 = safe, 1.0 = dangerous).

```json
{
  "nodes": {
    "zone_id": {
      "position": {"x": 0.0, "y": 0.0},
      "risk": 0.25,
      "name": "Main Gate",
      "type": "entrance",
      "metadata": {}
    }
  },
  "edges": {
    "edge_id": {
      "from_node": "zone_A",
      "to_node": "zone_B",
      "risk": 0.35,
      "metadata": {}
    }
  },
  "updated_at": "2026-02-10T14:30:00Z"
}
```

---

## Core Components

### 1. **HeatmapAdapter Class**

Main interface for managing heatmap data and answering queries.

#### Key Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `load_heatmap(data)` | Load heatmap data from backend | None |
| `get_node_risk(node_id)` | Get risk for a specific node | float (0.0-1.0) |
| `get_edge_risk(edge_id)` | Get risk for a specific edge | float (0.0-1.0) |
| `get_node_risk_by_position(pos)` | Find nearest node by position | float or None |
| `get_interpolated_risk(pos, k=3)` | Estimate risk at arbitrary position using k-NN | float |
| `find_safe_zones(threshold=0.3)` | Find all zones below risk threshold | List[str] |
| `find_danger_zones(threshold=0.7)` | Find all zones above risk threshold | List[str] |
| `get_connected_nodes(node_id)` | Get neighbors of a node | List[(node_id, edge_risk)] |
| `get_safest_neighbor(node_id)` | Find safest connected node | (node_id, risk) or None |
| `get_riskiest_neighbor(node_id)` | Find most dangerous connected node | (node_id, risk) or None |
| `get_route_risk(edge_ids)` | Analyze total risk of a route | Dict with risk metrics |
| `get_stats()` | Get overall heatmap statistics | Dict |
| `get_risk_distribution()` | Classify zones into risk bands | Dict[band → count] |

---

### 2. **GraphUtils Class**

Provides advanced graph operations for pathfinding and analysis.

#### Static Methods

| Method | Purpose | Algorithm |
|--------|---------|-----------|
| `dijkstra_safest_path(adapter, start, end)` | Find safest route | Dijkstra's algorithm |
| `find_k_safest_paths(adapter, start, end, k=3)` | Find k alternative safe routes | Modified Dijkstra |
| `is_reachable(adapter, start, end, max_risk)` | Check if destination reachable | Graph traversal |
| `get_reachable_nodes(adapter, start, max_risk, max_hops)` | Find all reachable zones | BFS with constraints |
| `analyze_route_safety(adapter, path)` | Comprehensive route analysis | Segment-by-segment metrics |
| `compare_routes(adapter, routes)` | Rank multiple routes by safety | Comparative analysis |
| `find_bottlenecks(adapter, threshold)` | Find critical high-risk areas | Threshold filtering |
| `estimate_travel_time(adapter, route, base_speed)` | Estimate travel with risk-adjusted speed | Physics-based calculation |

---

## Risk Interpolation (IDW)

For positions between known nodes, SafeSphere uses **Inverse Distance Weighting (IDW)** to estimate risk:

```
risk(P) = Σ(weight_i × risk_i) / Σ(weight_i)

where:
  weight_i = 1 / distance_i²
  
k = 3 nearest neighbors (configurable)
```

**Example:**
```python
position = Position(1.5, 2.0)
interpolated_risk = heatmap.get_interpolated_risk(position, k=3)
# Returns estimated risk at (1.5, 2.0) based on 3 nearest known nodes
```

---

## Pathfinding Algorithm

SafeSphere uses **Dijkstra's algorithm** to find the safest route between two points.

**Cost Function:**
```
segment_risk = (edge_risk + destination_node_risk) / 2.0
total_path_risk = Σ segment_risk for all segments
```

The algorithm prioritizes minimizing total risk, not distance.

### Example Output:
```python
path, total_risk, segments = GraphUtils.dijkstra_safest_path(heatmap, "Gate", "Building")

# Result:
# path = ["Gate", "Parking", "Safe_Zone", "Building"]
# total_risk = 0.285
# segments = [
#     RouteSegment(Gate→Parking, risk=0.20),
#     RouteSegment(Parking→Safe_Zone, risk=0.15),
#     RouteSegment(Safe_Zone→Building, risk=0.15),
# ]
```

---

## Use Cases

### Use Case 1: Real-Time Risk Queries
```python
heatmap = HeatmapAdapter()
heatmap.load_heatmap(backend_data)

# Check if a zone is safe
risk = heatmap.get_node_risk("Main_Gate")
if risk < 0.3:
    print("Zone is safe")
```

### Use Case 2: Safe Route Planning
```python
# Find safest path for emergency evacuation
path, total_risk, segments = GraphUtils.dijkstra_safest_path(
    heatmap, "Office", "Safe_Exit"
)
print(f"Evacuate via: {' → '.join(path)}")
print(f"Expected risk level: {total_risk:.3f}")
```

### Use Case 3: Alternative Routes
```python
# Provide user with 3 safest route options
routes = GraphUtils.find_k_safest_paths(
    heatmap, "Parking", "Building", k=3
)
for i, (path, risk, segments) in enumerate(routes, 1):
    print(f"Option {i}: {' → '.join(path)} (risk: {risk:.2f})")
```

### Use Case 4: Bottleneck Identification
```python
# Find critical infrastructure requiring security attention
bottlenecks = GraphUtils.find_bottlenecks(heatmap, threshold=0.80)
for bottleneck in bottlenecks:
    print(f"High-risk {bottleneck['type']}: {bottleneck['id']}")
    # Alert security, increase patrols, etc.
```

### Use Case 5: Travel Time Estimation
```python
# Estimate safe travel time (slower in high-risk areas)
timing = GraphUtils.estimate_travel_time(
    heatmap, 
    ["Gate", "Parking", "Building"],
    base_speed_ms=10.0
)
print(f"Safe travel time: {timing['total_time_minutes']:.2f} minutes")
```

---

## Risk Bands

Zones are classified into 5 risk levels:

| Band | Score Range | Interpretation | Action |
|------|-------------|-----------------|--------|
| **SAFE** | 0.0 - 0.2 | Very safe, standard precautions | Monitor only |
| **LOW** | 0.2 - 0.4 | Good safety, normal operations | Continue with awareness |
| **MEDIUM** | 0.4 - 0.6 | Moderate risk, elevated awareness | Caution advised |
| **HIGH** | 0.6 - 0.8 | High risk, avoid if possible | Restricted access |
| **CRITICAL** | 0.8 - 1.0 | Extremely dangerous | Lockdown / Avoid |

---

## Backend Integration Pattern

### How It Works:

1. **Backend Service** (Supabase) maintains risk heatmap:
   ```json
   GET /api/heatmap/current
   Returns: heatmap_data with all nodes and edges
   ```

2. **Safe Route Engine** queries heatmap:
   ```python
   heatmap_data = requests.get("http://backend/api/heatmap/current").json()
   heatmap = HeatmapAdapter()
   heatmap.load_heatmap(heatmap_data)
   ```

3. **Route Planning**:
   ```python
   path = GraphUtils.dijkstra_safest_path(heatmap, start, end)
   return {"recommended_path": path, "risk_level": total_risk}
   ```

4. **Update Frequency**:
   - Heatmap refreshed every 5-10 minutes from backend
   - Live threat data from Threat CV engine updates risk scores
   - Routes recalculated as heatmap changes

---

## Performance Characteristics

| Operation | Complexity | Time (N=100 zones) |
|-----------|-----------|-------------------|
| Load heatmap | O(N+M) | < 10ms |
| Get node risk | O(1) | < 1ms |
| Get interpolated risk | O(k log N) | 5-15ms (k=3) |
| Dijkstra safest path | O((N+M) log N) | 50-150ms |
| Find k-safest paths | O(k×(N+M) log N) | 200-500ms (k=3) |
| Bottleneck detection | O(N+M) | 10-20ms |
| Route analysis | O(path_length) | 1-5ms |

*Where N = number of zones, M = number of edges*

**Lightweight:** No ML models, no external APIs, pure algorithmic logic.

---

## API Examples

### Example 1: Basic Query
```python
from heatmap_adapter import HeatmapAdapter

heatmap = HeatmapAdapter()
heatmap.load_heatmap(backend_data)

# Get risk at specific zone
risk = heatmap.get_node_risk("Main_Gate")
print(f"Gate risk: {risk}")  # Output: 0.15
```

### Example 2: Find Safe Zones
```python
# Find all zones safe for evacuation
safe_zones = heatmap.find_safe_zones(threshold=0.30)
print(f"Safe zones: {safe_zones}")
# Output: ['Gate_A', 'Office']
```

### Example 3: Safest Route
```python
from graph_utils import GraphUtils

path, risk, segments = GraphUtils.dijkstra_safest_path(
    heatmap, "Office", "Emergency_Exit"
)
print(f"Route: {' → '.join(path)}")
print(f"Total risk: {risk:.3f}")
```

### Example 4: Route Comparison
```python
routes = [
    ["Office", "Hallway", "Main_Door"],
    ["Office", "Back_Stairs", "Side_Exit"],
]

comparison = GraphUtils.compare_routes(heatmap, routes)
safest = comparison["safest_route"]
print(f"Safest route: {' → '.join(safest['path'])}")
```

### Example 5: Estimate Travel Time
```python
timing = GraphUtils.estimate_travel_time(
    heatmap,
    ["Gate", "Parking", "Building"],
    base_speed_ms=10.0  # 10 units/second
)
print(f"Safe travel time: {timing['total_time_minutes']:.2f} minutes")
```

---

## Configuration

No external configuration required. All settings are parameter-based:

```python
# Risk thresholds (customizable per deployment)
SAFE_THRESHOLD = 0.30
DANGER_THRESHOLD = 0.70

# Pathfinding parameters
K_NEIGHBORS = 3  # for interpolation
MAX_ITERATIONS = 1000  # Dijkstra safety limit

# Travel time settings
BASE_SPEED_MS = 10.0  # units per second
```

---

## Testing

Run the example file to test all functionality:

```bash
python example_usage.py
```

**Output includes:**
- Basic node queries and statistics
- Risk interpolation at arbitrary positions
- Safest path computation
- Route analysis and comparison
- Bottleneck detection
- Travel time estimation

---

## Integration with Threat CV Engine

The Safe Route Engine receives live risk updates from Threat CV:

```
Threat CV Engine
    ↓ (detects high-threat with weapon)
    ├─ POST /api/threat/report 
    └─→ Backend (Supabase)
            ↓ (updates heatmap risk scores)
            ├─ Increases risk for Main_Entrance to 0.95
            └─→ Safe Route Engine
                    ↓ (recalculates safe paths)
                    └─→ Recommends evacuation via back exits
```

This creates a **closed-loop safety system** where route recommendations adapt in real-time to threats.

---

## Future Enhancements (Optional)

- [ ] Machine learning for threat prediction (predictive routing)
- [ ] Multi-objective optimization (risk vs. distance)
- [ ] Real-time crowd density updates
- [ ] Mobile-first UI for route recommendations
- [ ] Integration with emergency dispatch systems
- [ ] Analytics dashboard for security teams

---

## License

SafeSphere © 2026 - All Rights Reserved

---

## Support

For questions or issues, contact the SafeSphere development team.

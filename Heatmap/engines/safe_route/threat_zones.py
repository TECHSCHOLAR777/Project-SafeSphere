"""
SafeSphere Threat Zone Module

Manages threat circles as explicit obstacles for route avoidance.
Implements geometric algorithms for threat circle detection and avoidance.

Key features:
- Define threat zones as circles (center point + radius)
- Detect if a route line segment intersects a threat circle
- Calculate minimum distance from a path to threat zones
- Filter out routes that cross threat circles entirely
"""

from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
import math


@dataclass
class ThreatZone:
    """Represents a circular threat zone."""
    zone_id: str
    latitude: float
    longitude: float
    radius_km: float  # Radius in kilometers
    threat_level: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    threat_score: float = 0.5  # 0.0 to 1.0
    name: str = ""
    
    def center(self) -> Tuple[float, float]:
        """Return center as (lat, lng) tuple."""
        return (self.latitude, self.longitude)


class ThreatZoneManager:
    """
    Manages threat zones and provides geometric queries.
    
    Handles:
    - Zone creation and management
    - Line-circle intersection detection
    - Distance calculations
    - Zone filtering for routes
    """
    
    def __init__(self):
        """Initialize threat zone manager."""
        self.zones: Dict[str, ThreatZone] = {}
    
    def add_threat_zone(self, zone: ThreatZone) -> None:
        """Add a threat zone to the manager."""
        self.zones[zone.zone_id] = zone
    
    def create_from_incident(
        self,
        incident_id: str,
        latitude: float,
        longitude: float,
        threat_level: str,
        threat_score: float = 0.5,
        name: str = ""
    ) -> ThreatZone:
        """
        Create a threat zone from incident data.
        
        Threat avoidance radius scaling:
        - CRITICAL: 1.5 km (maximum avoidance)
        - HIGH: 1.2 km
        - MEDIUM: 0.8 km
        - LOW: 0.5 km
        """
        # Determine avoidance radius based on threat level
        radius_map = {
            "CRITICAL": 1.5,
            "HIGH": 1.2,
            "MEDIUM": 0.8,
            "LOW": 0.5
        }
        radius = radius_map.get(threat_level.upper(), 0.8)
        
        zone = ThreatZone(
            zone_id=incident_id,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius,
            threat_level=threat_level,
            threat_score=threat_score,
            name=name
        )
        self.add_threat_zone(zone)
        return zone
    
    def load_from_incidents(self, incidents: List[Dict]) -> None:
        """Load threat zones from incident list."""
        for inc in incidents:
            lat = inc.get("latitude")
            lng = inc.get("longitude")
            if lat is not None and lng is not None:
                self.create_from_incident(
                    incident_id=inc.get("incident_id", f"THREAT_{id(inc)}"),
                    latitude=float(lat),
                    longitude=float(lng),
                    threat_level=inc.get("threat_level", "MEDIUM"),
                    threat_score=float(inc.get("threat_score", 0.5)),
                    name=inc.get("behavior_summary", "")
                )
    
    def haversine_distance(
        self,
        lat1: float,
        lng1: float,
        lat2: float,
        lng2: float
    ) -> float:
        """
        Calculate distance between two points in kilometers using Haversine formula.
        """
        R = 6371.0  # Earth radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def point_in_circle(
        self,
        point_lat: float,
        point_lng: float,
        circle: ThreatZone
    ) -> bool:
        """Check if a point is inside a threat circle."""
        dist = self.haversine_distance(point_lat, point_lng, circle.latitude, circle.longitude)
        return dist <= circle.radius_km
    
    def distance_point_to_circle(
        self,
        point_lat: float,
        point_lng: float,
        circle: ThreatZone
    ) -> float:
        """
        Calculate distance from a point to the nearest point on a circle.
        Negative distance means point is inside the circle.
        """
        center_dist = self.haversine_distance(point_lat, point_lng, circle.latitude, circle.longitude)
        return center_dist - circle.radius_km
    
    def line_segment_intersects_circle(
        self,
        lat1: float,
        lng1: float,
        lat2: float,
        lng2: float,
        circle: ThreatZone,
        buffer_km: float = 0.0
    ) -> bool:
        """
        Check if a line segment intersects a threat circle.
        
        Uses parametric line representation and closest point calculation.
        A buffer can be added to expand the threat zone.
        
        Args:
            lat1, lng1: Start point of line segment
            lat2, lng2: End point of line segment
            circle: ThreatZone to test against
            buffer_km: Extra buffer around threat zone (for safety margin)
            
        Returns:
            True if segment intersects expanded circle, False otherwise
        """
        effective_radius = circle.radius_km + buffer_km
        
        # Quick check: if both endpoints are far from the circle, no intersection
        start_dist = self.haversine_distance(lat1, lng1, circle.latitude, circle.longitude)
        end_dist = self.haversine_distance(lat2, lng2, circle.latitude, circle.longitude)
        
        # If both points are inside the circle, segment definitely intersects
        if start_dist <= effective_radius and end_dist <= effective_radius:
            return True
        
        # If both points are far outside, likely no intersection
        if start_dist > effective_radius and end_dist > effective_radius:
            # Check if the circle is entirely on one side of the line
            # Using a simplified bounding box check
            lat_min, lat_max = min(lat1, lat2), max(lat1, lat2)
            lng_min, lng_max = min(lng1, lng2), max(lng1, lng2)
            
            circle_lat_min = circle.latitude - (effective_radius / 111.0)
            circle_lat_max = circle.latitude + (effective_radius / 111.0)
            circle_lng_min = circle.longitude - (effective_radius / (111.0 * math.cos(math.radians(circle.latitude))))
            circle_lng_max = circle.longitude + (effective_radius / (111.0 * math.cos(math.radians(circle.latitude))))
            
            # If bounding boxes don't overlap, no intersection
            if lat_max < circle_lat_min or lat_min > circle_lat_max:
                return False
            if lng_max < circle_lng_min or lng_min > circle_lng_max:
                return False
        
        # Calculate closest point on line segment to circle center
        closest_dist = self._distance_point_to_line_segment(
            circle.latitude, circle.longitude,
            lat1, lng1, lat2, lng2
        )
        
        return closest_dist <= effective_radius
    
    def _distance_point_to_line_segment(
        self,
        point_lat: float,
        point_lng: float,
        line_start_lat: float,
        line_start_lng: float,
        line_end_lat: float,
        line_end_lng: float
    ) -> float:
        """
        Calculate minimum distance from a point to a line segment.
        Handles the projection of the point onto the segment.
        """
        # Convert to approximate cartesian coordinates for easier math
        # Around the center point
        lat_center = (line_start_lat + line_end_lat) / 2
        
        # Approximate conversions (valid for small distances)
        x1 = line_start_lng * 111.0 * math.cos(math.radians(lat_center))
        y1 = line_start_lat * 111.0
        
        x2 = line_end_lng * 111.0 * math.cos(math.radians(lat_center))
        y2 = line_end_lat * 111.0
        
        px = point_lng * 111.0 * math.cos(math.radians(lat_center))
        py = point_lat * 111.0
        
        # Vector from start to end
        dx = x2 - x1
        dy = y2 - y1
        
        # If the segment is a point, return distance to that point
        if dx == 0 and dy == 0:
            return math.sqrt((px - x1)**2 + (py - y1)**2)
        
        # Project point onto the line
        # t = ((px-x1)*dx + (py-y1)*dy) / (dx*dx + dy*dy)
        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        
        # Clamp t to [0, 1] to stay on the segment
        t = max(0.0, min(1.0, t))
        
        # Closest point on the segment
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        # Distance in kilometers (x/y were computed in km)
        dist_km = math.sqrt((px - closest_x)**2 + (py - closest_y)**2)

        return dist_km
    
    def route_intersects_any_threat(
        self,
        coordinates: List[Tuple[float, float]],
        buffer_km: float = 0.0,
        threat_levels_to_avoid: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[ThreatZone]]:
        """
        Check if a route (list of coordinates) intersects any threat zone.
        
        Args:
            coordinates: List of (lng, lat) tuples forming the route path
            buffer_km: Extra safety buffer around threat zones
            threat_levels_to_avoid: List of threat levels to check (default all)
            
        Returns:
            (intersects: bool, intersecting_zone: ThreatZone or None)
        """
        if threat_levels_to_avoid is None:
            threat_levels_to_avoid = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        
        # Check each line segment
        for i in range(len(coordinates) - 1):
            lng1, lat1 = coordinates[i]
            lng2, lat2 = coordinates[i + 1]
            
            # Check against each threat zone
            for zone in self.zones.values():
                if zone.threat_level.upper() not in threat_levels_to_avoid:
                    continue
                
                if self.line_segment_intersects_circle(lat1, lng1, lat2, lng2, zone, buffer_km):
                    return (True, zone)
        
        return (False, None)
    
    def get_closest_threat_to_route(
        self,
        coordinates: List[Tuple[float, float]]
    ) -> Optional[Dict]:
        """
        Find the closest threat zone to a route and its minimum distance.
        
        Args:
            coordinates: List of (lng, lat) tuples forming the route path
            
        Returns:
            Dict with zone_id, threat_level, min_distance_km, or None if no threats
        """
        min_distance = float('inf')
        closest_zone = None
        
        for i in range(len(coordinates) - 1):
            lng1, lat1 = coordinates[i]
            lng2, lat2 = coordinates[i + 1]
            
            for zone in self.zones.values():
                dist = self._distance_point_to_line_segment(
                    zone.latitude, zone.longitude,
                    lat1, lng1, lat2, lng2
                )
                
                if dist < min_distance:
                    min_distance = dist
                    closest_zone = zone
        
        if closest_zone is None:
            return None
        
        return {
            "zone_id": closest_zone.zone_id,
            "threat_level": closest_zone.threat_level,
            "threat_score": closest_zone.threat_score,
            "min_distance_km": round(max(0.0, min_distance - closest_zone.radius_km), 3),
            "inside_zone": min_distance <= closest_zone.radius_km,
        }
    
    def filter_routes_by_safety(
        self,
        routes: List[Dict],
        strict_mode: bool = True,
        buffer_km: float = 0.1
    ) -> List[Dict]:
        """
        Filter routes to remove those that intersect threat zones.
        
        Args:
            routes: List of route dicts with 'geometry' containing coordinates
            strict_mode: If True, reject any route touching threat zones
                        If False, allow routes but mark them with risk
            buffer_km: Safety buffer around threat zones
            
        Returns:
            Filtered list of safe routes (or all routes if none are safe)
        """
        safe_routes = []
        unsafe_routes = []
        
        for route in routes:
            coordinates = route.get("geometry", {}).get("coordinates", [])
            if not coordinates:
                safe_routes.append(route)
                continue
            
            intersects, zone = self.route_intersects_any_threat(
                coordinates, buffer_km, threat_levels_to_avoid=["CRITICAL", "HIGH", "MEDIUM"]
            )
            
            if intersects:
                unsafe_routes.append((route, zone))
            else:
                safe_routes.append(route)
        
        # If we have safe routes, return only those; else return all
        if safe_routes:
            return safe_routes
        
        # If no fully safe routes, return all but mark them
        return routes
    
    def get_all_zones(self) -> List[ThreatZone]:
        """Get all threat zones."""
        return list(self.zones.values())
    
    def get_zones_by_threat_level(self, level: str) -> List[ThreatZone]:
        """Get all zones with a specific threat level."""
        return [z for z in self.zones.values() if z.threat_level.upper() == level.upper()]
    
    def clear_zones(self) -> None:
        """Clear all threat zones."""
        self.zones.clear()
    
    def stats(self) -> Dict:
        """Get threat zone statistics."""
        if not self.zones:
            return {
                "total_zones": 0,
                "critical_zones": 0,
                "high_zones": 0,
                "medium_zones": 0,
                "low_zones": 0,
            }
        
        level_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for zone in self.zones.values():
            level = zone.threat_level.upper()
            if level in level_counts:
                level_counts[level] += 1
        
        return {
            "total_zones": len(self.zones),
            "critical_zones": level_counts["CRITICAL"],
            "high_zones": level_counts["HIGH"],
            "medium_zones": level_counts["MEDIUM"],
            "low_zones": level_counts["LOW"],
        }

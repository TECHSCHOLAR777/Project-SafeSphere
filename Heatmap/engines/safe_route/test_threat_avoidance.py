"""
Test Suite for SafeSphere Threat Avoidance System

Demonstrates how the threat zone manager detects and prevents routes
from crossing threat circles.
"""

import math
from threat_zones import ThreatZoneManager, ThreatZone
from graph_utils import GraphUtils


def test_threat_zone_creation():
    """Test creating threat zones from incidents."""
    print("\n" + "="*70)
    print("TEST 1: Creating Threat Zones from Incidents")
    print("="*70)
    
    manager = ThreatZoneManager()
    
    # Create some incident data
    incidents = [
        {
            "incident_id": "INC_001",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "threat_level": "CRITICAL",
            "threat_score": 0.95,
            "behavior_summary": "Armed suspect with weapon"
        },
        {
            "incident_id": "INC_002",
            "latitude": 40.7200,
            "longitude": -74.0150,
            "threat_level": "HIGH",
            "threat_score": 0.75,
            "behavior_summary": "Suspicious activity"
        },
        {
            "incident_id": "INC_003",
            "latitude": 40.7300,
            "longitude": -73.9950,
            "threat_level": "MEDIUM",
            "threat_score": 0.50,
            "behavior_summary": "Minor incident"
        }
    ]
    
    # Load incidents as threat zones
    manager.load_from_incidents(incidents)
    
    # Display zone information
    print("\n✓ Threat zones created:")
    for zone in manager.get_all_zones():
        print(f"  - {zone.zone_id}: {zone.threat_level} threat")
        print(f"    Location: ({zone.latitude:.4f}, {zone.longitude:.4f})")
        print(f"    Avoidance radius: {zone.radius_km} km")
    
    # Show statistics
    stats = manager.stats()
    print(f"\n✓ Zone statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


def test_point_in_circle():
    """Test point-in-circle detection."""
    print("\n" + "="*70)
    print("TEST 2: Point-in-Circle Detection")
    print("="*70)
    
    manager = ThreatZoneManager()
    
    # Create a threat zone
    zone = ThreatZone(
        zone_id="TEST_ZONE",
        latitude=40.7128,
        longitude=-74.0060,
        radius_km=1.0,
        threat_level="HIGH"
    )
    manager.add_threat_zone(zone)
    
    # Test points
    test_points = [
        (40.7128, -74.0060, "At center"),
        (40.7228, -74.0060, "1 km North (boundary)"),
        (40.7228, -74.0060, "1 km North (on boundary)"),
        (40.7228, -74.0060, "1 km North (just outside)"),
        (40.6200, -74.0060, "10 km away"),
    ]
    
    print("\n✓ Testing point locations relative to threat zone:")
    print(f"  Zone: ({zone.latitude:.4f}, {zone.longitude:.4f}), radius={zone.radius_km}km")
    
    for lat, lng, description in test_points:
        dist = manager.haversine_distance(lat, lng, zone.latitude, zone.longitude)
        inside = manager.point_in_circle(lat, lng, zone)
        status = "INSIDE" if inside else "OUTSIDE"
        print(f"  - {description:30s} | Distance: {dist:.3f}km | Status: {status}")


def test_line_circle_intersection():
    """Test line segment to circle intersection."""
    print("\n" + "="*70)
    print("TEST 3: Line Segment to Circle Intersection")
    print("="*70)
    
    manager = ThreatZoneManager()
    
    # Create a threat zone
    zone = ThreatZone(
        zone_id="THREAT_ZONE",
        latitude=40.7150,
        longitude=-74.0100,
        radius_km=0.8,
        threat_level="HIGH"
    )
    manager.add_threat_zone(zone)
    
    # Test routes (line segments)
    test_routes = [
        {
            "name": "Direct through threat",
            "p1": (40.7000, -74.0200),  # Southwest
            "p2": (40.7300, -74.0000),  # Northeast (crosses zone)
        },
        {
            "name": "North of threat",
            "p1": (40.7300, -74.0100),  # North
            "p2": (40.7400, -74.0100),  # Further North
        },
        {
            "name": "Close but avoids threat",
            "p1": (40.6900, -74.0100),
            "p2": (40.7000, -74.0100),  # Stays outside radius
        },
        {
            "name": "Grazes threat boundary",
            "p1": (40.7150, -73.9300),  # West
            "p2": (40.7150, -73.9400),  # Further West (tangent to circle)
        }
    ]
    
    print(f"\n✓ Threat zone: ({zone.latitude:.4f}, {zone.longitude:.4f}), radius={zone.radius_km}km")
    print("\nTesting route segments:")
    
    for route in test_routes:
        lat1, lng1 = route["p1"]
        lat2, lng2 = route["p2"]
        
        intersects = manager.line_segment_intersects_circle(lat1, lng1, lat2, lng2, zone, buffer_km=0.0)
        intersects_buffered = manager.line_segment_intersects_circle(lat1, lng1, lat2, lng2, zone, buffer_km=0.1)
        
        status = "CROSSES" if intersects else "SAFE"
        status_buffered = "CROSSES" if intersects_buffered else "SAFE"
        
        print(f"\n  {route['name']:30s}")
        print(f"    From: ({lat1:.4f}, {lng1:.4f})")
        print(f"    To:   ({lat2:.4f}, {lng2:.4f})")
        print(f"    Without buffer: {status}")
        print(f"    With 100m buffer: {status_buffered}")


def test_route_validation():
    """Test full route validation."""
    print("\n" + "="*70)
    print("TEST 4: Full Route Validation")
    print("="*70)
    
    manager = ThreatZoneManager()
    
    # Create threat zones
    zones = [
        ThreatZone("THREAT_1", 40.7150, -74.0100, 0.8, "HIGH", 0.8),
        ThreatZone("THREAT_2", 40.7300, -73.9900, 1.0, "CRITICAL", 0.95),
    ]
    for zone in zones:
        manager.add_threat_zone(zone)
    
    # Test routes
    test_routes = [
        {
            "name": "Safe northern route",
            "coordinates": [
                (-74.0200, 40.7400),  # Start NW
                (-74.0100, 40.7500),  # Through North
                (-73.9900, 40.7600),  # End NE
            ]
        },
        {
            "name": "Direct through threats",
            "coordinates": [
                (-74.0200, 40.7000),  # Start SW
                (-74.0100, 40.7150),  # Through THREAT_1
                (-73.9900, 40.7300),  # Through THREAT_2
                (-73.9800, 40.7400),  # End E
            ]
        },
        {
            "name": "Southern detour (safe)",
            "coordinates": [
                (-74.0200, 40.7000),  # Start SW
                (-74.0100, 40.7000),  # South loop
                (-73.9900, 40.7000),  # Loop around
                (-73.9800, 40.7400),  # End E
            ]
        }
    ]
    
    print(f"\n✓ Testing {len(test_routes)} routes against {len(zones)} threat zones")
    
    for route in test_routes:
        intersects, zone = manager.route_intersects_any_threat(route["coordinates"])
        closest = manager.get_closest_threat_to_route(route["coordinates"])
        
        print(f"\n  {route['name']:30s}")
        print(f"    Intersects threats: {intersects}")
        if intersects:
            print(f"    Intersected zone: {zone.zone_id} ({zone.threat_level})")
        if closest:
            print(f"    Closest threat: {closest['zone_id']} at {closest['min_distance_km']}km")
        else:
            print(f"    Closest threat: None (very far)")


def test_route_ranking():
    """Test ranking routes by safety."""
    print("\n" + "="*70)
    print("TEST 5: Route Ranking by Safety")
    print("="*70)
    
    manager = ThreatZoneManager()
    
    # Create a threat zone
    manager.create_from_incident(
        "INC_001", 40.7150, -74.0100, "CRITICAL", 0.95
    )
    
    # Simulate OSRM routes (with geometry)
    routes = [
        {
            "geometry": {
                "coordinates": [
                    (-74.0200, 40.7150),  # Through threat
                    (-74.0100, 40.7150),  # Center of circle
                    (-73.9900, 40.7150),  # Exit threat
                ]
            },
            "duration": 300,
            "distance": 5000,
        },
        {
            "geometry": {
                "coordinates": [
                    (-74.0200, 40.7000),  # North
                    (-74.0100, 40.7300),  # North loop
                    (-73.9900, 40.7200),  # Return
                ]
            },
            "duration": 400,
            "distance": 7000,
        },
        {
            "geometry": {
                "coordinates": [
                    (-74.0200, 40.6900),  # South (safe)
                    (-74.0100, 40.6900),  # South route
                    (-73.9900, 40.6900),  # South exit
                ]
            },
            "duration": 500,
            "distance": 8000,
        }
    ]
    
    # Rank routes
    if GraphUtils:
        ranked = GraphUtils.rank_routes_by_safety(routes, manager)
        
        print(f"\n✓ Ranked {len(ranked)} routes by safety:\n")
        for i, route in enumerate(ranked, 1):
            safety = route.get("safety_metrics", {})
            print(f"  Route {i}:")
            print(f"    Distance: {route['distance']}m | Duration: {route['duration']}s")
            print(f"    Safety: {safety.get('is_safe')} | Score: {safety.get('safety_score')}")
            if safety.get('threat_intersections'):
                print(f"    ⚠️ Intersects: {safety['threat_intersections']}")
            if safety.get('closest_threat'):
                closest = safety['closest_threat']
                print(f"    📍 Closest threat: {closest['min_distance_km']}km away")


def run_all_tests():
    """Run all tests."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  SafeSphere Threat Avoidance System - Test Suite".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    try:
        test_threat_zone_creation()
        test_point_in_circle()
        test_line_circle_intersection()
        test_route_validation()
        test_route_ranking()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()

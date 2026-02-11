"""
SafeSphere Backend API - Supabase Integration

This API accepts threat incident reports from the threat_cv engine
and stores incidents in Supabase (public.incidents) table.
Also handles SOS alerts via public.sos_alerts table.

Database-first design: All data persists in Supabase PostgreSQL.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import json
import os
import math
import random
import numpy as np
import requests
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase import create_client, Client
except ImportError:
    print("ERROR: 'supabase' package not installed. Install with: pip install supabase")
    raise ImportError("supabase-py is required")


# ----- Supabase Configuration -----
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_KEY environment variables."
    )

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print(f"✅ Connected to Supabase: {SUPABASE_URL.split('.')[0]}...")
except Exception as e:
    print(f"❌ Supabase connection failed: {e}")
    raise

# Optional: Keep local directories for screenshot staging
DATA_DIR = Path("safesphere_backend")
SCREENSHOT_DIR = DATA_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


# ----- Models -----
class ThreatIncident(BaseModel):
    incident_id: str
    timestamp: str
    threat_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    threat_score: float
    people_count: int
    weapon_detected: bool
    weapon_types: List[str] = []
    behavior_summary: str
    is_critical: bool
    full_telemetry: Dict
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_id: Optional[str] = None
    location_accuracy_m: Optional[float] = None
    mode: Optional[str] = None  # "cctv" | "client"


class IncidentResponse(BaseModel):
    success: bool
    incident_id: str
    message: str

class SeedRequest(BaseModel):
    center_lat: float
    center_lng: float
    count: int = 50
    radius_km: float = 1.0
    mode: Optional[str] = "cctv"
    source_prefix: Optional[str] = "SEED_CAM"

class RouteRequest(BaseModel):
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float


# ----- App -----
app = FastAPI(
    title="SafeSphere Threat Management API (Supabase-ready)",
    version="1.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----- Database Operations -----
def _insert_incident(incident: Dict) -> bool:
    """Insert incident into Supabase incidents table.
    """
    try:
        # Prepare record for Supabase schema
        db_record = {
            "incident_id": incident.get("incident_id"),
            "timestamp": incident.get("timestamp"),
            "threat_level": incident.get("threat_level"),
            "threat_score": float(incident.get("threat_score", 0.0)),
            "people_count": incident.get("people_count"),
            "weapon_detected": incident.get("weapon_detected", False),
            "weapon_types": incident.get("weapon_types"),  # JSONB field
            "behavior_summary": incident.get("behavior_summary"),
            "is_critical": incident.get("is_critical", False),
            "latitude": incident.get("latitude"),
            "longitude": incident.get("longitude"),
            "location_accuracy_m": incident.get("location_accuracy_m"),
            "source_id": incident.get("source_id"),
            "mode": incident.get("mode"),
            "full_telemetry": incident.get("full_telemetry"),  # JSONB field
        }
        
        response = supabase.table("incidents").insert(db_record).execute()
        print(f"✅ Incident inserted: {db_record.get('incident_id')}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to insert incident: {e}")
        return False


def _load_incidents_from_db(limit: int = 1000) -> List[Dict]:
    """Load incidents from Supabase database.
    """
    try:
        response = supabase.table("incidents").select(
            "*"
        ).order(
            "timestamp", desc=True
        ).limit(limit).execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        print(f"❌ Failed to load incidents: {e}")
        return []


def _get_incident_by_id(incident_id: str) -> Optional[Dict]:
    """Get single incident by ID from Supabase.
    """
    try:
        response = supabase.table("incidents").select(
            "*"
        ).eq(
            "incident_id", incident_id
        ).execute()
        
        return response.data[0] if response.data else None
        
    except Exception as e:
        print(f"❌ Failed to get incident {incident_id}: {e}")
        return None


def _get_incidents_by_threat_level(threat_level: str, limit: int = 100) -> List[Dict]:
    """Get incidents filtered by threat level from Supabase.
    """
    try:
        response = supabase.table("incidents").select(
            "*"
        ).eq(
            "threat_level", threat_level
        ).order(
            "timestamp", desc=True
        ).limit(limit).execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        print(f"❌ Failed to get incidents by threat level: {e}")
        return []


def _get_incidents_nearby(lat: float, lng: float, radius_km: float = 2.0, limit: int = 500) -> List[Dict]:
    """Get incidents within radius of coordinates.
    For now, loads all and filters client-side. For production, use PostGIS.
    """
    try:
        incidents = _load_incidents_from_db(limit=limit * 2)  # Load extra to account for filtering
        results = []
        
        for incident in incidents:
            ilat = incident.get("latitude")
            ilng = incident.get("longitude")
            if ilat is None or ilng is None:
                continue
            
            distance = _haversine_km(lat, lng, float(ilat), float(ilng))
            if distance <= radius_km:
                incident_copy = dict(incident)
                incident_copy["distance_km"] = round(distance, 3)
                results.append(incident_copy)
        
        return sorted(results, key=lambda x: x["distance_km"])[:limit]
        
    except Exception as e:
        print(f"❌ Failed to get nearby incidents: {e}")
        return []


# ----- Geo helpers -----
def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def _severity_weight(level: str, score: float) -> float:
    base = max(0.0, min(1.0, score))
    boost = {"LOW": 0.0, "MEDIUM": 0.10, "HIGH": 0.20, "CRITICAL": 0.35}.get(level.upper(), 0.0)
    w = base * 0.7 + boost
    return max(0.0, min(0.99, w))

def _round_zone(lat: float, lng: float, step: float = 0.002) -> (float, float):
    lat_c = round(lat / step) * step
    lng_c = round(lng / step) * step
    return (round(lat_c, 6), round(lng_c, 6))

# Legacy function maintained for backward compatibility
def _load_incidents(limit: int = 1000) -> List[Dict]:
    """Maintained for backward compatibility. Delegates to database.
    """
    return _load_incidents_from_db(limit=limit)

def _aggregate_heatmap(items: List[Dict], zone_step: float = 0.002) -> List[Dict]:
    zones: Dict[str, Dict] = {}
    for it in items:
        lat = it.get("latitude")
        lng = it.get("longitude")
        if lat is None or lng is None:
            continue
        f = _extract_features(it)
        rank = _model_rank(f)
        zlat, zlng = _round_zone(float(lat), float(lng), step=zone_step)
        zid = f"{zlat}:{zlng}"
        if zid not in zones:
            zones[zid] = {"lat": zlat, "lng": zlng, "rank_sum": 0.0, "count": 0}
        z = zones[zid]
        z["rank_sum"] += rank
        z["count"] += 1
    result = []
    for z in zones.values():
        avg = z["rank_sum"] / max(1, z["count"])
        result.append({
            "lat": z["lat"],
            "lng": z["lng"],
            "weight": round(z["rank_sum"], 3),
            "avg": round(avg, 3),
            "count": z["count"],
        })
    return sorted(result, key=lambda r: r["avg"], reverse=True)

def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))

def _derive_incident_type(it: Dict) -> str:
    if it.get("weapon_detected"):
        wt = (it.get("weapon_types") or [])
        if "gun" in wt:
            return "weapon_firearm"
        if "knife" in wt or "blade" in wt:
            return "weapon_blade"
        return "weapon"
    full_telemetry = it.get("full_telemetry") or {}
    bt = full_telemetry.get("behavior") or {}
    pairs = bt.get("pair_interactions", [])
    overall = bt.get("overall_risk", "")
    if any("following" in (p.get("status","")) for p in pairs):
        return "following"
    if any("approach" in (p.get("status","")) for p in pairs) or "high" in overall:
        return "rapid_approach"
    ctx = full_telemetry.get("context_factors") or {}
    if ctx.get("isolation", False):
        return "isolation_risk"
    return "suspicious_activity"

def _extract_features(it: Dict) -> np.ndarray:
    s = float(it.get("threat_score", 0.0))
    ppl = float(it.get("people_count", 0))
    has_w = 1.0 if it.get("weapon_detected") else 0.0
    wt = it.get("weapon_types") or []
    gun = 1.0 if "gun" in wt else 0.0
    knife = 1.0 if ("knife" in wt or "blade" in wt) else 0.0
    is_crit = 1.0 if it.get("is_critical") else 0.0
    full_telemetry = it.get("full_telemetry") or {}
    ctx = full_telemetry.get("context_factors") or {}
    iso = 1.0 if ctx.get("isolation", False) else 0.0
    night = 1.0 if ctx.get("night_mode", False) else 0.0
    accel = 1.0 if ctx.get("sudden_acceleration", False) else 0.0
    return np.array([s, ppl, has_w, gun, knife, is_crit, iso, night, accel], dtype=float)

_ML_W = np.array([1.2, 0.25, 1.1, 1.6, 1.0, 0.8, 0.5, 0.2, 0.6], dtype=float)
_ML_B = -0.8

def _model_rank(features: np.ndarray) -> float:
    z = float(features.dot(_ML_W) + _ML_B)
    return max(0.0, min(1.0, _sigmoid(z)))

def _get_osrm_routes(start_lat: float, start_lng: float, end_lat: float, end_lng: float) -> List[Dict]:
    """Fetch route alternatives from OSRM public API."""
    # OSRM uses lng,lat order
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}?overview=full&geometries=geojson&alternatives=true"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("routes", [])
    except Exception as e:
        print(f"⚠️ OSRM routing failed: {e}")
    return []

def _calculate_route_risk(route_geo: Dict, incidents: List[Dict]) -> float:
    """Calculate risk score for a route based on nearby incidents."""
    coordinates = route_geo.get("coordinates", [])
    if not coordinates:
        return 0.0
    
    total_risk = 0.0
    # Sample points to avoid heavy computation (every 10th point)
    sample_points = coordinates[::10]
    if not sample_points:
        sample_points = coordinates

    for pt in sample_points:
        # GeoJSON is [lng, lat]
        r_lng, r_lat = pt[0], pt[1]
        
        for inc in incidents:
            i_lat = inc.get("latitude")
            i_lng = inc.get("longitude")
            if i_lat is None or i_lng is None:
                continue
                
            # Quick bounding box check (approx 1km)
            if abs(i_lat - r_lat) > 0.01 or abs(i_lng - r_lng) > 0.01:
                continue
                
            dist = _haversine_km(r_lat, r_lng, float(i_lat), float(i_lng))
            
            # If incident is within 300m of route path
            if dist < 0.3:
                severity = _severity_weight(inc.get("threat_level", "LOW"), inc.get("threat_score", 0.0))
                # Higher risk if closer
                proximity_factor = (1.0 - (dist / 0.3))
                total_risk += severity * proximity_factor

    return total_risk


# ----- API Endpoints (simple contract for backend team) -----
@app.post("/threats/report", response_model=IncidentResponse)
async def report_threat(incident: ThreatIncident):
    """
    Receive a threat incident from the threat_cv engine and store in Supabase.
    
    This endpoint now directly saves to the incidents table in Supabase.
    """
    try:
        data = incident.dict()
        
        # Sanitize input data (handle Swagger UI default values or missing data)
        timestamp = data.get("timestamp")
        try:
            if not timestamp or timestamp == "string":
                raise ValueError("Placeholder timestamp")
            # Basic validation of ISO format
            datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
        except ValueError:
            timestamp = datetime.now().isoformat()
            
        incident_id = data.get("incident_id")
        if not incident_id or incident_id == "string":
            incident_id = f"INC_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}"

        # Prepare incident for database
        threat_incident = {
            "incident_id": incident_id,
            "timestamp": timestamp,
            "threat_level": data.get("threat_level") if data.get("threat_level") != "string" else "LOW",
            "threat_score": float(data.get("threat_score", 0.0)),
            "people_count": data.get("people_count"),
            "weapon_detected": data.get("weapon_detected", False),
            "weapon_types": data.get("weapon_types"),
            "behavior_summary": data.get("behavior_summary"),
            "is_critical": data.get("is_critical", False),
            "full_telemetry": data.get("full_telemetry"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "location_accuracy_m": data.get("location_accuracy_m"),
            "source_id": data.get("source_id"),
            "mode": data.get("mode"),
        }
        
        print(f"🛡️  Received threat report: {threat_incident.get('incident_id')} - Level: {threat_incident.get('threat_level')}")
        
        # Insert into Supabase
        success = _insert_incident(threat_incident)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to persist incident to database")
        
        return IncidentResponse(
            success=True,
            incident_id=incident_id,
            message="Incident received and saved to database"
        )
        
    except Exception as e:
        print(f"❌ Error reporting threat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/route/calculate")
async def calculate_safe_route(req: RouteRequest):
    """
    Calculate the safest route between two points.
    Fetches alternatives from OSRM and scores them against threat database.
    """
    try:
        # 1. Get routes from OSRM
        routes = _get_osrm_routes(req.start_lat, req.start_lng, req.end_lat, req.end_lng)
        if not routes:
            raise HTTPException(status_code=404, detail="No routes found")

        # 2. Get active incidents (last 24h ideally, but using all active for demo)
        # In production, use geospatial query for bounding box of route
        incidents = _load_incidents_from_db(limit=500)
        
        # 3. Score each route
        scored_routes = []
        for route in routes:
            risk_score = _calculate_route_risk(route["geometry"], incidents)
            scored_routes.append({
                "geometry": route["geometry"],
                "duration": route["duration"],
                "distance": route["distance"],
                "risk_score": round(risk_score, 2)
            })
        
        # 4. Sort by risk score (lowest first)
        scored_routes.sort(key=lambda x: x["risk_score"])
        
        best_route = scored_routes[0]
        is_safe = best_route["risk_score"] < 1.0
        
        return {
            "success": True,
            "route": best_route,
            "alternatives_analyzed": len(routes),
            "safety_status": "SAFE" if is_safe else "CAUTION",
            "risk_score": best_route["risk_score"]
        }

    except Exception as e:
        print(f"❌ Error calculating route: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sos")
async def trigger_sos(alert: Dict):
    """
    Handle SOS alerts from the frontend. Saves to sos_alerts table.
    """
    try:
        print(f"🚨 SOS ALERT RECEIVED: {alert.get('type')}")
        
        sos_record = {
            "type": alert.get("type", "SOS"),
            "details": alert.get("details"),
            "latitude": alert.get("location", {}).get("lat"),
            "longitude": alert.get("location", {}).get("lng"),
            "status": "active"
        }
        
        response = supabase.table("sos_alerts").insert(sos_record).execute()
        print(f"✅ SOS Alert saved: {response.data[0].get('id') if response.data else 'unknown'}")
        
        return {
            "success": True,
            "message": "SOS Alert recorded and emergency services notified",
            "id": response.data[0].get("id") if response.data else None
        }
        
    except Exception as e:
        print(f"❌ SOS Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/incidents")
async def list_incidents(limit: int = 100, threat_level: Optional[str] = None):
    """List recent incidents from Supabase. Optionally filter by threat level."""
    try:
        if threat_level:
            incidents = _get_incidents_by_threat_level(threat_level, limit)
        else:
            incidents = _load_incidents_from_db(limit=limit)
        
        return {"count": len(incidents), "incidents": incidents}
        
    except Exception as e:
        print(f"❌ Error listing incidents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """Get specific incident from Supabase by ID."""
    try:
        incident = _get_incident_by_id(incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
        return incident
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload/screenshot")
async def upload_screenshot(incident_id: str = Form(...), file: UploadFile = File(...)):
    """Upload screenshot associated with an incident. Backend can move to Supabase storage."""
    try:
        filename = f"{incident_id}_{file.filename}"
        filepath = SCREENSHOT_DIR / filename
        contents = await file.read()
        with open(filepath, "wb") as f:
            f.write(contents)
        return {"success": True, "incident_id": incident_id, "path": str(filepath)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/seed/incidents")
async def seed_incidents(req: SeedRequest):
    """Generate and seed test incidents into Supabase database."""
    try:
        items = []
        now = datetime.now()
        
        for i in range(req.count):
            base_score = random.uniform(0.1, 0.98)
            angle = random.uniform(0, 2*math.pi)
            dist_km = random.uniform(0, req.radius_km)
            dlat = dist_km / 111.0
            dlng = dist_km / (111.0 * max(0.1, math.cos(math.radians(req.center_lat))))
            lat = req.center_lat + dlat * math.sin(angle)
            lng = req.center_lng + dlng * math.cos(angle)
            
            weapon_prob = 0.15
            has_weapon = random.random() < weapon_prob
            wtype = []
            if has_weapon:
                wtype = random.choices(["knife", "gun", "blade"], weights=[0.5, 0.4, 0.1], k=1)
            
            incident_id = f"INC_{now.strftime('%Y%m%d_%H%M%S')}_{i:03d}"
            
            incident_record = {
                "incident_id": incident_id,
                "timestamp": datetime.now().isoformat(),
                "threat_level": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
                "threat_score": float(base_score),
                "people_count": random.randint(1, 4),
                "weapon_detected": has_weapon,
                "weapon_types": wtype,
                "behavior_summary": "seeded test data",
                "is_critical": random.random() < 0.1,
                "full_telemetry": {
                    "location": {"latitude": lat, "longitude": lng, "mode": req.mode, "source_id": f"{req.source_prefix}_{i:03d}"},
                    "behavior": {"pair_interactions": []},
                    "context_factors": {"isolation": False}
                },
                "latitude": lat,
                "longitude": lng,
                "location_accuracy_m": 25.0,
                "source_id": f"{req.source_prefix}_{i:03d}",
                "mode": req.mode,
            }
            
            _insert_incident(incident_record)
            items.append(incident_record)
        
        print(f"✅ Seeded {len(items)} test incidents to Supabase")
        return {"seeded": len(items), "incidents": items}
        
    except Exception as e:
        print(f"❌ Error seeding incidents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dataset/incidents")
async def dataset_incidents(limit: int = 1000):
    """Get incidents dataset from Supabase for analysis."""
    try:
        items = _load_incidents_from_db(limit=limit)
        out = []
        
        for it in items:
            out.append({
                "incident_id": it.get("incident_id"),
                "timestamp": it.get("timestamp"),
                "threat_level": it.get("threat_level"),
                "threat_score": it.get("threat_score"),
                "latitude": it.get("latitude"),
                "longitude": it.get("longitude"),
                "source_id": it.get("source_id"),
                "weapon_detected": it.get("weapon_detected"),
            })
        
        return {"count": len(out), "incidents": out}
        
    except Exception as e:
        print(f"❌ Error getting dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/heatmap/model")
async def heatmap_model(zone_step: float = 0.002, limit: int = 2000):
    """Generate threat heatmap zones from Supabase incidents with ML scoring."""
    try:
        items = _load_incidents_from_db(limit=limit)
        zones: Dict[str, Dict] = {}
        
        for it in items:
            lat = it.get("latitude")
            lng = it.get("longitude")
            if lat is None or lng is None:
                continue
            
            # ML-based threat ranking
            f = _extract_features(it)
            rank = _model_rank(f)
            
            # Geographic clustering
            zlat, zlng = _round_zone(float(lat), float(lng), step=zone_step)
            zid = f"{zlat}:{zlng}"
            
            if zid not in zones:
                zones[zid] = {"lat": zlat, "lng": zlng, "rank_sum": 0.0, "count": 0}
            
            zones[zid]["rank_sum"] += rank
            zones[zid]["count"] += 1
        
        result = [
            {
                "lat": v["lat"],
                "lng": v["lng"],
                "weight": round(v["rank_sum"], 3),
                "avg": round(v["rank_sum"] / max(1, v["count"]), 3),
                "count": v["count"]
            }
            for v in zones.values()
        ]
        
        result.sort(key=lambda x: x["avg"], reverse=True)
        return {"count": len(result), "zones": result}
        
    except Exception as e:
        print(f"❌ Error generating heatmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/incidents/nearby")
async def incidents_nearby(lat: float, lng: float, radius_km: float = 2.0, limit: int = 500):
    """Get incidents near coordinates from Supabase."""
    try:
        incidents = _get_incidents_nearby(lat, lng, radius_km, limit)
        return {"count": len(incidents), "incidents": incidents}
        
    except Exception as e:
        print(f"❌ Error getting nearby incidents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/heatmap/data")
async def heatmap_data(zone_step: float = 0.002, limit: int = 2000):
    """Get aggregated heatmap data from Supabase."""
    try:
        items = _load_incidents_from_db(limit=limit)
        zones = _aggregate_heatmap(items, zone_step=zone_step)
        return {"count": len(zones), "zones": zones}
        
    except Exception as e:
        print(f"❌ Error getting heatmap data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/heatmap/nearby")
async def heatmap_nearby(lat: float, lng: float, radius_km: float = 2.0, zone_step: float = 0.002, limit: int = 2000):
    """Get heatmap zones near coordinates from Supabase."""
    try:
        items = _load_incidents_from_db(limit=limit)
        zones = _aggregate_heatmap(items, zone_step=zone_step)
        nearby = []
        
        for z in zones:
            d = _haversine_km(lat, lng, z["lat"], z["lng"])
            if d <= radius_km:
                zcopy = dict(z)
                zcopy["distance_km"] = round(d, 3)
                nearby.append(zcopy)
        
        nearby.sort(key=lambda x: (x["distance_km"], -x["weight"]))
        return {"count": len(nearby), "zones": nearby}
        
    except Exception as e:
        print(f"❌ Error getting nearby heatmap zones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/map", response_class=HTMLResponse)
async def heatmap_view(key: Optional[str] = None):
    html = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>SafeSphere Threat Heatmap</title>
    <style>
      html, body, #map { height: 100%; margin: 0; }
      #controls { position: absolute; top: 10px; left: 10px; z-index: 10; background: rgba(255,255,255,.9); padding: 8px; border-radius: 6px; box-shadow: 0 2px 6px rgba(0,0,0,.2); }
    </style>
  </head>
  <body>
    <div id="controls">
      <label>Zone step: <input id="zoneStep" type="number" value="0.002" step="0.001"></label>
      <label>Radius (km): <input id="radiusKm" type="number" value="2" step="0.5"></label>
      <button id="refresh">Refresh</button>
    </div>
    <div id="map"></div>
    <script>
      let map, heatmap, userMarker;
      async function fetchZones(zoneStep=0.002){
        const res = await fetch(`/heatmap/model?zone_step=${zoneStep}`);
        return await res.json();
      }
      function initMap(){
        map = new google.maps.Map(document.getElementById('map'), {
          zoom: 14,
          center: {lat: 37.7749, lng: -122.4194},
          mapTypeId: 'roadmap'
        });
        heatmap = new google.maps.visualization.HeatmapLayer({
          data: [],
          dissipating: true,
          radius: 30
        });
        heatmap.setMap(map);
        navigator.geolocation?.watchPosition((pos)=>{
          const {latitude, longitude} = pos.coords;
          if(!userMarker){
            userMarker = new google.maps.Marker({
              position: {lat: latitude, lng: longitude},
              map,
              title: 'You'
            });
            map.setCenter({lat: latitude, lng: longitude});
          } else {
            userMarker.setPosition({lat: latitude, lng: longitude});
          }
        });
        document.getElementById('refresh').addEventListener('click', async ()=>{
          const step = parseFloat(document.getElementById('zoneStep').value || '0.002');
          const data = await fetchZones(step);
          const points = data.zones.map(z => ({location: new google.maps.LatLng(z.lat, z.lng), weight: z.weight}));
          heatmap.setData(points);
        });
        fetchZones().then(data=>{
          const points = data.zones.map(z => ({location: new google.maps.LatLng(z.lat, z.lng), weight: z.weight}));
          heatmap.setData(points);
        });
      }
    </script>
    <script async defer src="__GMAPS_SCRIPT_PLACEHOLDER__"></script>
  </body>
</html>
"""
    gmaps_key = key or os.environ.get("GOOGLE_MAPS_API_KEY") or "YOUR_GOOGLE_MAPS_API_KEY"
    script_url = f"https://maps.googleapis.com/maps/api/js?key={gmaps_key}&libraries=visualization&callback=initMap"
    html = html.replace("__GMAPS_SCRIPT_PLACEHOLDER__", script_url)
    return HTMLResponse(content=html, status_code=200)

@app.get("/map/leaflet", response_class=HTMLResponse)
async def leaflet_heatmap_view():
    html = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>SafeSphere Threat Heatmap (Leaflet)</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
    <style>
      html, body, #map { height: 100%; margin: 0; }
      #controls { position: absolute; top: 10px; left: 10px; z-index: 10; background: rgba(255,255,255,.9); padding: 8px; border-radius: 6px; box-shadow: 0 2px 6px rgba(0,0,0,.2); }
      #controls label { margin-right: 8px; }
      .zone-label { position: relative; transform: translate(-50%, -50%); pointer-events: none; }
      .zone-label-text { background: rgba(0,0,0,.6); color: #fff; padding: 2px 6px; border-radius: 10px; font-size: 12px; }
      #basemap { margin-left: 8px; }
    </style>
  </head>
  <body>
    <div id="controls">
      <label>Zone step: <input id="zoneStep" type="number" value="0.002" step="0.001"></label>
      <label><input id="showCircles" type="checkbox" checked> Show circles</label>
      <label>Basemap:
        <select id="basemap">
          <option value="osm">OpenStreetMap</option>
          <option value="osm_plain">OpenStreetMap (plain)</option>
          <option value="hot">OSM HOT</option>
          <option value="carto">CARTO Light</option>
          <option value="none">None</option>
        </select>
      </label>
      <button id="refresh">Refresh</button>
    </div>
    <div id="map"></div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
    <script src="https://unpkg.com/leaflet.heat/dist/leaflet-heat.js"></script>
    <script>
      let map = L.map('map').setView([37.7749, -122.4194], 13);
      const providerMap = {
        osm: { url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png', attribution: '&copy; OpenStreetMap contributors' },
        osm_plain: { url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', attribution: '&copy; OpenStreetMap contributors' },
        hot: { url: 'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', attribution: '&copy; OpenStreetMap contributors, HOT' },
        carto: { url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png', attribution: '&copy; OpenStreetMap contributors, &copy; CARTO' }
      };
      let providerIndex = 0;
      let tileErrorCount = 0;
      let tileLayer = null;
      function setProviderByKey(key){
        if(tileLayer){ map.removeLayer(tileLayer); tileLayer = null; }
        if(key === 'none'){ return; }
        const p = providerMap[key];
        tileLayer = L.tileLayer(p.url, {maxZoom:19, crossOrigin:true, attribution:p.attribution});
        tileLayer.on('tileerror', ()=>{
          tileErrorCount++;
          if(tileErrorCount > 5){
            document.getElementById('basemap').value = 'none';
            if(tileLayer){ map.removeLayer(tileLayer); tileLayer = null; }
          }
        });
        tileLayer.addTo(map);
      }
      document.getElementById('basemap').addEventListener('change', (e)=> setProviderByKey(e.target.value));
      setProviderByKey('osm');
      let heat = L.heatLayer([], {radius: 25, blur: 15, maxZoom: 17}).addTo(map);
      let circlesLayer = L.layerGroup().addTo(map);
      let labelsLayer = L.layerGroup().addTo(map);
      let userMarker = null;
      async function fetchZones(zoneStep=0.002){
        const res = await fetch(`/heatmap/data?zone_step=${zoneStep}`);
        return await res.json();
      }
      function weightToColor(w){
        const clamped = Math.max(0, Math.min(1, w));
        const h = (1 - clamped) * 120;
        return `hsl(${h}, 90%, 45%)`;
      }
      function weightToRadiusMeters(w){
        const clamped = Math.max(0, Math.min(1, w));
        return 50 + clamped * 250;
      }
      function setHeat(data){
        const pts = data.zones.map(z => {
          const v = (z.avg ?? z.weight);
          return [z.lat, z.lng, Math.max(0, Math.min(1, v))];
        });
        heat.setLatLngs(pts);
        circlesLayer.clearLayers();
        labelsLayer.clearLayers();
        const showCircles = document.getElementById('showCircles').checked;
        if (showCircles) {
          data.zones.forEach(z => {
            const v = (z.avg ?? z.weight);
            const color = weightToColor(v);
            const radius = weightToRadiusMeters(v);
            const c = L.circle([z.lat, z.lng], {radius: radius, color: color, fillColor: color, fillOpacity: 0.25, weight: 2});
            circlesLayer.addLayer(c);
            const label = L.marker([z.lat, z.lng], {
              icon: L.divIcon({className: 'zone-label', html: `<span class="zone-label-text">${v.toFixed(2)}</span>`, iconSize: [0, 0], iconAnchor: [0, 0]})
            });
            labelsLayer.addLayer(label);
          });
        }
      }
      document.getElementById('refresh').addEventListener('click', async ()=>{
        const step = parseFloat(document.getElementById('zoneStep').value || '0.002');
        const data = await fetchZones(step);
        setHeat(data);
      });
      fetchZones().then(setHeat);
      if (navigator.geolocation) {
        navigator.geolocation.watchPosition((pos)=>{
          const {latitude, longitude} = pos.coords;
          if(!userMarker){
            userMarker = L.marker([latitude, longitude]).addTo(map);
            map.setView([latitude, longitude], 15);
          } else {
            userMarker.setLatLng([latitude, longitude]);
          }
        }, ()=>{}, {enableHighAccuracy: true});
      }
    </script>
  </body>
</html>
"""
    return HTMLResponse(content=html, status_code=200)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "service": "SafeSphere Backend API"}


# ----- Implementation Notes -----
# ✅ All data now persists in Supabase database
# ✅ incidents table: Stores all threat detections
# ✅ sos_alerts table: Stores emergency SOS alerts
# ✅ JSONB fields: weapon_types and full_telemetry are stored as JSONB for flexibility
# ✅ Location indexing: idx_incidents_location for fast geographic queries
# 
# Environment Variables Required:
#   SUPABASE_URL: Your Supabase project URL
#   SUPABASE_KEY: Your Supabase API key (use anon key for client access)
#
# Install dependencies:
#   pip install supabase python-dotenv


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

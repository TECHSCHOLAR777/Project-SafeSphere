"""
SafeSphere Backend API (Supabase-ready placeholder)

This lightweight API accepts threat incident reports from the threat_cv engine
and stores each incident as a JSON file under `safesphere_backend/pending_incidents/`.

Backend team: replace the file-storage hooks with Supabase (or other DB) writes.
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


# ----- Config -----
DATA_DIR = Path("safesphere_backend")
PENDING_DIR = DATA_DIR / "pending_incidents"
SCREENSHOT_DIR = DATA_DIR / "screenshots"
PENDING_DIR.mkdir(parents=True, exist_ok=True)
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


# ----- App -----
app = FastAPI(
    title="SafeSphere Threat Management API (Supabase-ready)",
    version="1.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----- Helper: File storage (for backend team) -----
def save_incident_file(incident: Dict) -> bool:
    """Save incident JSON to pending folder for backend ingestion.
    Backend team can replace this with direct Supabase writes.
    """
    try:
        incident_id = incident.get("incident_id") or f"INC_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        path = PENDING_DIR / f"{incident_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(incident, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Failed to save incident file: {e}")
        return False


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

def _load_incidents(limit: int = 1000) -> List[Dict]:
    files = sorted(PENDING_DIR.glob("*.json"), key=os.path.getmtime, reverse=True)[:limit]
    items: List[Dict] = []
    for p in files:
        try:
            with open(p, "r", encoding="utf-8") as f:
                items.append(json.load(f))
        except Exception:
            continue
    return items

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
    bt = it.get("full_telemetry", {}).get("behavior", {})
    pairs = bt.get("pair_interactions", [])
    overall = bt.get("overall_risk", "")
    if any("following" in (p.get("status","")) for p in pairs):
        return "following"
    if any("approach" in (p.get("status","")) for p in pairs) or "high" in overall:
        return "rapid_approach"
    ctx = it.get("full_telemetry", {}).get("context_factors", {})
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
    ctx = it.get("full_telemetry", {}).get("context_factors", {})
    iso = 1.0 if ctx.get("isolation", False) else 0.0
    night = 1.0 if ctx.get("night_mode", False) else 0.0
    accel = 1.0 if ctx.get("sudden_acceleration", False) else 0.0
    return np.array([s, ppl, has_w, gun, knife, is_crit, iso, night, accel], dtype=float)

_ML_W = np.array([1.2, 0.25, 1.1, 1.6, 1.0, 0.8, 0.5, 0.2, 0.6], dtype=float)
_ML_B = -0.8

def _model_rank(features: np.ndarray) -> float:
    z = float(features.dot(_ML_W) + _ML_B)
    return max(0.0, min(1.0, _sigmoid(z)))


# ----- API Endpoints (simple contract for backend team) -----
@app.post("/threats/report", response_model=IncidentResponse)
async def report_threat(incident: ThreatIncident):
    """
    Receive a threat incident from the threat_cv engine.

    NOTE FOR BACKEND DEV: Replace `save_incident_file` internals with Supabase
    insert logic (or call Supabase HTTP REST endpoint). Keep the endpoint
    contract identical so the engine can POST directly.
    """
    data = incident.dict()
    curated = {
        "incident_id": data.get("incident_id"),
        "timestamp": data.get("timestamp"),
        "type": _derive_incident_type(data),
        "model_rank": round(_model_rank(_extract_features(data)), 3),
        "people_count": data.get("people_count"),
        "weapon_detected": data.get("weapon_detected"),
        "weapon_types": data.get("weapon_types"),
        "behavior_summary": data.get("behavior_summary"),
        "is_critical": data.get("is_critical"),
        "full_telemetry": data.get("full_telemetry"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "source_id": data.get("source_id"),
        "mode": data.get("mode"),
        "location_accuracy_m": data.get("location_accuracy_m"),
    }
    print(f"Received threat report: {curated.get('incident_id')}")
    saved = save_incident_file(curated)
    if not saved:
        raise HTTPException(status_code=500, detail="Failed to persist incident")

    # Response: backend team will implement further actions (dispatch, alerts)
    return IncidentResponse(success=True, incident_id=data.get("incident_id"), message="Incident received and saved")

@app.post("/api/sos")
async def trigger_sos(alert: Dict):
    """
    Handle SOS alerts from the frontend.
    """
    # In a real app, save to 'sos_alerts' table here
    print(f"🚨 SOS RECEIVED: {alert}")
    return {"success": True, "message": "SOS Alert Processed"}


@app.get("/incidents")
async def list_incidents(limit: int = 100):
    """List recent pending incident files (for backend ingestion)."""
    files = sorted(PENDING_DIR.glob("*.json"), key=os.path.getmtime, reverse=True)[:limit]
    items = []
    for p in files:
        try:
            with open(p, "r", encoding="utf-8") as f:
                items.append(json.load(f))
        except Exception:
            continue
    return {"count": len(items), "incidents": items}


@app.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """Return saved incident JSON (placeholder storage)."""
    path = PENDING_DIR / f"{incident_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Incident not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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
            wtype = random.choices(["knife","gun","blade"], weights=[0.5,0.4,0.1], k=1)
        itype = random.choices(["suspicious_activity","following","rapid_approach","isolation_risk","weapon","weapon_firearm","weapon_blade"], weights=[0.4,0.2,0.15,0.1,0.05,0.06,0.04], k=1)[0]
        incident_id = f"INC_{now.strftime('%Y%m%d_%H%M%S')}_{i:03d}"
        raw = {
            "incident_id": incident_id,
            "timestamp": datetime.now().isoformat(),
            "people_count": random.randint(1,4),
            "weapon_detected": has_weapon,
            "weapon_types": wtype,
            "behavior_summary": "seeded",
            "is_critical": random.random() < 0.1,
            "full_telemetry": {
                "location": {"latitude": lat, "longitude": lng, "mode": req.mode, "source_id": f"{req.source_prefix}_{i:03d}"},
                "behavior": {"pair_interactions": [{"status": "following"}] if itype=="following" else [{"status":"approach"}] if itype=="rapid_approach" else []},
                "context_factors": {"isolation": itype=="isolation_risk"}
            },
            "latitude": lat,
            "longitude": lng,
            "source_id": f"{req.source_prefix}_{i:03d}",
            "mode": req.mode,
            "location_accuracy_m": 25.0
        }
        raw["threat_score"] = float(base_score)
        curated = {
            "incident_id": raw["incident_id"],
            "timestamp": raw["timestamp"],
            "type": itype,
            "model_rank": round(_model_rank(_extract_features(raw)), 3),
            "people_count": raw["people_count"],
            "weapon_detected": raw["weapon_detected"],
            "weapon_types": raw["weapon_types"],
            "behavior_summary": raw["behavior_summary"],
            "is_critical": raw["is_critical"],
            "full_telemetry": raw["full_telemetry"],
            "latitude": raw["latitude"],
            "longitude": raw["longitude"],
            "source_id": raw["source_id"],
            "mode": raw["mode"],
            "location_accuracy_m": raw["location_accuracy_m"]
        }
        save_incident_file(curated)
        items.append(curated)
    return {"seeded": len(items)}

@app.get("/dataset/incidents")
async def dataset_incidents(limit: int = 1000):
    items = _load_incidents(limit=limit)
    out = []
    for it in items:
        f = _extract_features(it)
        rank = _model_rank(f)
        itype = _derive_incident_type(it)
        out.append({
            "incident_id": it.get("incident_id"),
            "timestamp": it.get("timestamp"),
            "type": itype,
            "model_rank": round(rank, 3),
            "latitude": it.get("latitude"),
            "longitude": it.get("longitude"),
            "source_id": it.get("source_id"),
        })
    return {"count": len(out), "incidents": out}

@app.get("/heatmap/model")
async def heatmap_model(zone_step: float = 0.002, limit: int = 2000):
    items = _load_incidents(limit=limit)
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
        zones[zid]["rank_sum"] += rank
        zones[zid]["count"] += 1
    result = [{"lat": v["lat"], "lng": v["lng"], "weight": round(v["rank_sum"],3), "avg": round(v["rank_sum"]/max(1,v["count"]),3), "count": v["count"]} for v in zones.values()]
    result.sort(key=lambda x: x["avg"], reverse=True)
    return {"count": len(result), "zones": result}

@app.get("/incidents/nearby")
async def incidents_nearby(lat: float, lng: float, radius_km: float = 2.0, limit: int = 500):
    items = _load_incidents(limit=limit)
    results = []
    for it in items:
        ilat = it.get("latitude")
        ilng = it.get("longitude")
        if ilat is None or ilng is None:
            continue
        d = _haversine_km(lat, lng, float(ilat), float(ilng))
        if d <= radius_km:
            it_copy = dict(it)
            it_copy["distance_km"] = round(d, 3)
            results.append(it_copy)
    results.sort(key=lambda x: x["distance_km"])
    return {"count": len(results), "incidents": results}


@app.get("/heatmap/data")
async def heatmap_data(zone_step: float = 0.002, limit: int = 2000):
    items = _load_incidents(limit=limit)
    zones = _aggregate_heatmap(items, zone_step=zone_step)
    return {"count": len(zones), "zones": zones}


@app.get("/heatmap/nearby")
async def heatmap_nearby(lat: float, lng: float, radius_km: float = 2.0, zone_step: float = 0.002, limit: int = 2000):
    items = _load_incidents(limit=limit)
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


# ----- Notes for Backend Team -----
# - Replace `save_incident_file` with Supabase client code to insert into a table.
# - Recommended Supabase table columns:
#   incident_id, timestamp, threat_level, threat_score, people_count,
#   weapon_detected, weapon_types (JSON), behavior_summary, is_critical, full_telemetry (JSON), created_at
# - For screenshots/videos: either upload to Supabase storage bucket or provide endpoints to receive files and then store.


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

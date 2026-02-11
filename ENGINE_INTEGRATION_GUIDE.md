# SafeSphere Engine Integration Guide

## Available Engines & API Endpoints

### 1. **Threat CV Engine** (Computer Vision)
**Status:** ✅ Ready  
**Location:** `/Heatmap/engines/threat_cv/main.py`  
**Purpose:** Real-time threat detection from video feeds

#### API Endpoint:
```
POST /threats/report
Body: {
  incident_id: string
  timestamp: string (ISO format)
  threat_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
  threat_score: float (0.0-1.0)
  people_count: int
  weapon_detected: bool
  weapon_types: string[]
  behavior_summary: string
  is_critical: bool
  latitude: float
  longitude: float
  source_id: string
  location_accuracy_m: float
  mode: "cctv" | "client"
  full_telemetry: object
}
Response: { success: bool, incident_id: string, message: string }
```

#### Detection Capabilities:
- Person detection & tracking
- Weapon recognition
- Behavioral anomaly detection
- Motion analysis
- Crowd density assessment
- Threat scoring & classification

---

### 2. **Voice AI Engine** (Speech Recognition)
**Status:** ✅ Ready  
**Location:** `/Heatmap/engines/voice_ai/main.py`  
**Purpose:** Voice command recognition & SOS activation

#### Capabilities:
- Real-time speech-to-text
- Command parsing (SOS, Help, Alert, etc.)
- Voice authentication (optional)
- Noise filtering & enhancement

#### Usage in Frontend:
```javascript
// Pseudo-code for Voice SOS integration
const voiceAI = new VoiceAIEngine();
voiceAI.startListening();
voiceAI.on('command', (cmd) => {
  if (cmd === 'SOS') triggerSOS();
  if (cmd === 'HELP') openEmergencyContacts();
});
```

---

### 3. **Safe Route Engine** (Path Optimization)
**Status:** 🔲 Placeholder (Empty)  
**Location:** `/Heatmap/engines/safe_route/main.py`  
**Purpose:** AI-powered safest route calculation

#### Recommended API Structure:
```
POST /route/calculate
Body: {
  start: { lat: float, lng: float }
  end: { lat: float, lng: float }
  avoid_zones: [{ lat: float, lng: float, radius_km: float }]
  preferences: {
    well_lit: bool
    crowded: bool
    near_police: bool
    avoid_isolated: bool
  }
}
Response: {
  route: [{ lat: float, lng: float }],
  safety_score: float,
  estimated_time: int,
  threats_on_path: int
}
```

---

### 4. **LLM Engine** (Large Language Model)
**Status:** 🔲 Placeholder (Empty)  
**Location:** `/Heatmap/engines/llm_engine/main.py`  
**Purpose:** Intelligence analysis, recommendations, chatbot

#### Recommended API Structure:
```
POST /ai/analyze
Body: {
  incident: { threat_level, threat_score, behavior_summary, weapon_types }
  context: { location, time, crowd_density }
  user_query: string (optional)
}
Response: {
  risk_assessment: string
  recommended_actions: string[]
  emergency_priority: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
  detailed_report: string
}
```

---

## Integration Points in Frontend

### **Integration Point 1: User Dashboard - Safe Route Button**
**File:** `script.js` (UserPage object)  
**Current Feature:** Feature card for "Safe Route"  
**Integration:** Click handler → API call to `/route/calculate`

```javascript
// In UserPage.init() - Replace feature card click handler
document.querySelector('[data-feature="safe-route"]')?.addEventListener('click', async () => {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(async (pos) => {
      const route = await fetch('http://localhost:8000/route/calculate', {
        method: 'POST',
        body: JSON.stringify({
          start: { lat: pos.coords.latitude, lng: pos.coords.longitude },
          end: getUserDestination(),
          preferences: { well_lit: true, crowded: true, avoid_isolated: true }
        })
      }).then(r => r.json());
      showRouteOnMap(route);
    });
  }
});
```

---

### **Integration Point 2: User Dashboard - Threat Map**
**File:** `script.js` (UserPage object) + `index.html`  
**Current Feature:** Feature card for "Threat Map"  
**Integration:** Click handler → Fetch `/heatmap/nearby` or `/incidents/nearby`

```javascript
// Show threats near user location
document.querySelector('[data-feature="threat-map"]')?.addEventListener('click', async () => {
  const threats = await fetch(`http://localhost:8000/heatmap/nearby?lat=${userLat}&lng=${userLng}&radius_km=5`).then(r => r.json());
  displayThreatHeatmap(threats.zones);
  updateThreatAlertCount(threats.count);
});
```

---

### **Integration Point 3: SOS Button - Voice Activation**
**File:** `script.js` (Line ~500, SOS button handler)  
**Current Feature:** Click to activate SOS  
**Integration:** Add voice command detection

```javascript
// Add voice SOS alongside click SOS
const startVoiceSOS = async () => {
  const voiceResult = await fetch('http://localhost:8000/voice/detect', {
    method: 'POST',
    body: JSON.stringify({ listen_duration_sec: 10 })
  }).then(r => r.json());
  
  if (voiceResult.command === 'SOS') {
    triggerSOSAlert();
  }
};

// SOS button long-press → voice activation
sosButton.addEventListener('touchstart', () => {
  sosLongPressTimer = setTimeout(startVoiceSOS, 1000);
});
```

---

### **Integration Point 4: Police Dashboard - Live Threat Feed**
**File:** `script.js` (PolicePage object, line ~730)  
**Current Feature:** Static alert list  
**Integration:** WebSocket connection to real-time threat stream

```javascript
// In PolicePage.init() - Replace static alerts with live feed
const threatSocket = new WebSocket('ws://localhost:8000/threats/stream');
threatSocket.onmessage = (event) => {
  const threat = JSON.parse(event.data);
  addThreatAlertCard(threat);
  updateHeatmap(threat.latitude, threat.longitude);
};
```

---

### **Integration Point 5: Guardian Dashboard - Activity Timeline**
**File:** `script.js` (GuardianPage object, line ~630)  
**Current Feature:** Static timeline  
**Integration:** Real-time location & activity updates from protégé

```javascript
// Fetch live activity for loved one
const liveActivity = setInterval(async () => {
  const updates = await fetch(`http://localhost:8000/user/${userId}/activity?since=${lastUpdate}`).then(r => r.json());
  updates.forEach(update => addTimelineEvent(update));
}, 5000); // Poll every 5 seconds
```

---

### **Integration Point 6: Emergency Actions - Voice Command**
**File:** `index.html` (Line ~87, Voice SOS action card)  
**Current Feature:** Placeholder icon  
**Integration:** Trigger voice listening & command parsing

```html
<!-- index.html Emergency Actions section -->
<div class="action-card" data-action="voice">
  <div class="action-icon accent-orange">🎤</div>
  <p class="action-title">Voice SOS</p>
  <!-- Add audio visualizer when active -->
  <div class="voice-visualizer hidden" id="voiceVisualizer">
    <div class="voice-bar"></div>
  </div>
</div>
```

```javascript
// Event handler
document.querySelector('[data-action="voice"]')?.addEventListener('click', () => {
  startVoiceListening();
  showVoiceVisualizer();
});
```

---

### **Integration Point 7: Threat Detection Dashboard View**
**File:** Add new page option OR extend Guardian dashboard  
**Current Status:** No real-time threat visualization  
**Integration:** `/map/leaflet` endpoint or custom heatmap display

```javascript
// New ThreatVisualizationPage object
const ThreatPage = {
  init() {
    // Load heatmap data
    const heatmapData = fetch('http://localhost:8000/heatmap/data').then(r => r.json());
    // Display on Leaflet map
    displayHeatmapOnMap(heatmapData.zones);
    // Real-time threat feed
    subscribeToLiveThreatStream();
  }
};
```

---

### **Integration Point 8: Chat Widget - AI Assistance**
**File:** `script.js` (ChatWidget class, line ~40)  
**Current Feature:** Chat interface (backend not connected)  
**Integration:** Send messages to LLM engine for intelligent responses

```javascript
// In ChatWidget.handleSendMessage()
const response = await fetch('http://localhost:8000/ai/chat', {
  method: 'POST',
  body: JSON.stringify({
    message: userMessage,
    context: {
      user_location: { lat, lng },
      nearby_threats: threatCount,
      time_of_day: currentHour
    }
  })
}).then(r => r.json());

this.addMessage(response.reply, 'bot');
```

---

### **Integration Point 9: Incident Reporting Form**
**File:** Add modal/form to User Dashboard  
**Current Feature:** Only feature cards  
**Integration:** POST to `/threats/report` endpoint

```javascript
// New incident report handler
const reportThreat = async (incident) => {
  const response = await fetch('http://localhost:8000/threats/report', {
    method: 'POST',
    body: JSON.stringify({
      incident_id: generateIncidentID(),
      timestamp: new Date().toISOString(),
      threat_level: incident.level,
      threat_score: incident.score,
      people_count: incident.peopleCount,
      weapon_detected: incident.hasWeapon,
      behavior_summary: incident.description,
      is_critical: incident.level === 'CRITICAL',
      latitude: userLocation.lat,
      longitude: userLocation.lng,
      mode: 'client'
    })
  }).then(r => r.json());
  
  Toast.show(`Incident ${response.incident_id} reported`, 'success');
};
```

---

### **Integration Point 10: SOS Alert Endpoint**
**File:** `script.js` (SOS button handler, line ~500)  
**Current Feature:** Local state update only  
**Integration:** POST to `/api/sos` to notify emergency services

```javascript
// Enhance SOS button click handler
const triggerSOSAlert = async () => {
  const sos = await fetch('http://localhost:8000/api/sos', {
    method: 'POST',
    body: JSON.stringify({
      type: 'SOS',
      details: {
        user_id: currentUser.id,
        reason: 'Emergency assistance needed',
        threat_detected: threatDetected,
        is_false_alarm: false
      },
      location: {
        lat: userLocation.latitude,
        lng: userLocation.longitude,
        accuracy: userLocation.accuracy
      }
    })
  }).then(r => r.json());
  
  Toast.show('Emergency services notified ✅', 'success');
};
```

---

## API Summary Table

| Engine | Endpoint | Method | Purpose | Priority |
|--------|----------|--------|---------|----------|
| **Threat CV** | `/threats/report` | POST | Report detected threats | 🔴 HIGH |
| **Threat CV** | `/incidents` | GET | Fetch all incidents | 🟠 MEDIUM |
| **Threat CV** | `/incidents/nearby` | GET | Get nearby threats | 🟠 MEDIUM |
| **Threat CV** | `/heatmap/data` | GET | Threat heatmap data | 🟠 MEDIUM |
| **Threat CV** | `/heatmap/nearby` | GET | Nearby heatmap zones | 🟠 MEDIUM |
| **SOS** | `/api/sos` | POST | SOS alert notification | 🔴 HIGH |
| **Safe Route** | `/route/calculate` | POST | Optimal safe path | 🟡 LOW |
| **Voice AI** | `/voice/detect` | POST | Voice command detection | 🟡 LOW |
| **LLM Engine** | `/ai/analyze` | POST | Threat analysis & recommendations | 🟡 LOW |
| **LLM Engine** | `/ai/chat` | POST | Conversational AI | 🟡 LOW |

---

## Implementation Roadmap

### Phase 1: Core Safety (HIGH Priority)
- [ ] Connect `/threats/report` endpoint to police dashboard
- [ ] Connect `/api/sos` to SOS button
- [ ] Display `/heatmap/nearby` on user dashboard
- [ ] Add real-time threat feed to police dashboard

### Phase 2: User Experience (MEDIUM Priority)
- [ ] Implement safe route calculator
- [ ] Add threat map visualization
- [ ] Connect chat widget to LLM engine
- [ ] Guardian real-time activity tracking

### Phase 3: Advanced Features (LOW Priority)
- [ ] Voice SOS activation
- [ ] Voice command interface
- [ ] Advanced threat analysis & recommendations
- [ ] Incident reporting form

---

## Testing the APIs

### 1. Test Threat Report Endpoint
```bash
curl -X POST http://localhost:8000/threats/report \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "TEST_001",
    "timestamp": "2026-02-11T12:00:00Z",
    "threat_level": "HIGH",
    "threat_score": 0.85,
    "people_count": 3,
    "weapon_detected": true,
    "behavior_summary": "Aggressive group",
    "is_critical": true,
    "latitude": 40.7128,
    "longitude": -74.0060,
    "mode": "client"
  }'
```

### 2. Test SOS Alert
```bash
curl -X POST http://localhost:8000/api/sos \
  -H "Content-Type: application/json" \
  -d '{
    "type": "SOS",
    "details": {"user_id": "user_123", "reason": "Emergency"},
    "location": {"lat": 40.7128, "lng": -74.0060}
  }'
```

### 3. Fetch Incidents
```bash
curl http://localhost:8000/incidents?limit=10
```

### 4. Get Nearby Threats
```bash
curl "http://localhost:8000/heatmap/nearby?lat=40.7128&lng=-74.0060&radius_km=2"
```

---

## Next Steps

1. **Verify backend is running:** `uvicorn backend_api:app --reload` in `/Heatmap` directory
2. **Test each endpoint** using the curl commands above
3. **Implement Phase 1 integrations** starting with SOS and threat reporting
4. **Add WebSocket support** for real-time threat feeds
5. **Build safe route calculator** (requires map API like Google Maps or Mapbox)
6. **Develop voice command interface** using Web Audio API

---

**Last Updated:** 2026-02-11  
**Backend Status:** ✅ Ready to serve  
**Frontend Integration:** 🔄 In Progress

# SafeSphere Threat Detection Engine v1.0

## 🛡️ Overview

The SafeSphere Threat Detection Engine is a comprehensive computer vision system for **universal real-time threat detection**. Designed to protect **everyone** - regardless of gender - from potential danger by analyzing video feeds for threats in real-time.

## 🎯 Mission

**Everyone deserves to feel safe.** This engine provides intelligent threat assessment using computer vision and AI to detect:
- Aggressive behavior patterns
- Weapon presence
- Suspicious movements
- Dangerous situations

## 📊 Features Implemented

### 1. **Motion Detection** (`motion_detector.py`)
- Detects movement in video
- Classifies as: `LOW` | `MEDIUM` | `HIGH`
- Baseline for threat assessment

### 2. **Person Detection & Tracking** (`person_detector.py` + `tracker.py`)
- Detects people in frames using HOG descriptor
- Assigns unique IDs to each person
- Tracks velocity and position
- Handles occlusions and missed frames

### 3. **Behavior Analysis** (`behavior_analyzer.py`)
- Analyzes proximity between people
- Detects following behavior
- Measures approach velocity
- Assesses alignment of movement
- Persistence scoring (how long threat lasts)

### 4. **Weapon Detection** (`weapon_detector.py`) ⭐ NEW
- Uses YOLO deep learning model
- Detects: guns, knives, blades, explosive devices
- Provides confidence scores
- Automatically escalates threat level

### 5. **Enhanced Context Analysis** (`enhanced_context.py`) ⭐ NEW
- **Environmental factors**: Night time, lighting, location
- **Social factors**: Isolation vs crowds, group safety
- **Physical environment**: Escape routes, corners, exits
- **Threat patterns**: Multiple attackers, clustering
- **Spatial analysis**: Person location relative to boundaries

### 6. **Threat Classification** (`threat_classifier.py`) ⭐ NEW
- **4-Level System**: `LOW` | `MEDIUM` | `HIGH` | `CRITICAL`
- Intelligent thresholding based on context
- Automatic escalation for weapons
- Detailed reasoning for each classification
- Specific recommendations for each threat level

### 7. **Incident Logging & Recording** (`incident_logger.py`) ⭐ NEW
- Automatic incident logging to JSON
- Screenshot capture on threat detection
- Video recording for high-threat situations
- Full telemetry storage for analysis
- Evidence preservation for law enforcement

### 8. **Intelligent Alerting System** (`main.py`) ⭐ NEW
- Only alerts on real threats (not noise)
- Prevents alert spam with deduplication
- Context-aware threshold adjustment
- Detailed alert messages with recommendations
- Multi-level response protocols

## 🔴 Threat Levels & Actions

### **LOW (0.0-0.3)**
```
Status: MONITOR
Action: Continue normal monitoring
Recording: No
Alert: No
```

### **MEDIUM (0.3-0.6)**
```
Status: ALERT_USER
Action: User notified of suspicious activity
Recording: ✅ YES (for evidence)
Alert: No (to backend only)
Recommendations:
  - Stay alert
  - Move to safe area if needed
```

### **HIGH (0.6-0.8)**
```
Status: ALERT_POLICE
Action: Police/Security notified immediately
Recording: ✅ YES
Alert: ✅ YES (to backend + emergency contacts)
Recommendations:
  - 🆘 Activate SOS
  - 📍 Share live location
  - 🚶 Move to populated area
  - 📞 Contact 911/Emergency
```

### **CRITICAL (0.8+)**
```
Status: EMERGENCY_PROTOCOL
Action: Full emergency response
Recording: ✅ YES (continuous)
Alert: ✅ YES (auto-dispatch)
Recommendations:
  - 🆘 SOS ACTIVATED - Emergency dispatched
  - 📍 LOCATION SHARED with police + contacts
  - 🎥 RECORDING + STREAMING in progress
  - 🗣️ VOICE ALERT activated
  - 🏃 SAFE ROUTE generated to nearest police station
  - 💡 Lights ON + Device locked
```

## 🚀 Running the Engine

### Basic Usage
```bash
python -m engines.threat_cv.main
```

### With Custom Video Source
```python
from engines.threat_cv.main import SafeSphereThreatsCV

engine = SafeSphereThreatsCV(enable_recording=True)
# Modify video source before running
engine.video = VideoSource(source="path/to/video.mp4")
engine.run()
```

## 📁 Output Files

### Logs Directory: `safespherevenv/logs/incidents/`

```
incidents/
├── incidents.jsonl          # All threat events (JSON lines format)
├── screenshots/             # Frame captures of threats
│   ├── INC_20260210_143045_001_frame_0000.jpg
│   ├── INC_20260210_143045_001_frame_0001.jpg
│   └── ...
└── videos/                  # Full recordings of critical threats
    ├── INC_20260210_143045_001.mp4
    └── ...
```

### Example Incident Entry

```json
{
  "incident_id": "INC_20260210_143045_001",
  "is_critical": true,
  "incident": {
    "timestamp": "2026-02-10T14:30:45.123",
    "threat_level": "CRITICAL",
    "threat_score": 0.87,
    "weapon_detected": true,
    "weapon_types": ["gun"],
    "people_count": 2,
    "threat_reason": "Risk: HIGH, Score: 0.87"
  },
  "full_telemetry": { ... }
}
```

## 🔧 Configuration

All modules have configurable parameters:

```python
# Behavior Analysis
from engines.threat_cv.inference.behavior_analyzer import BehaviorConfig
config = BehaviorConfig(
    proximity_threshold=120.0,        # pixels
    approach_velocity_threshold=-4.0, # pixels/frame
    persistence_frames=15             # frames before "following"
)

# Threat Classification
from engines.threat_cv.inference.threat_classifier import ThreatClassifierConfig
config = ThreatClassifierConfig(
    low_threshold=0.3,
    medium_threshold=0.5,
    high_threshold=0.7,
    critical_threshold=0.85
)

# Enhanced Context
from engines.threat_cv.inference.enhanced_context import EnhancedContextConfig
config = EnhancedContextConfig(
    night_boost=0.15,                # +15% in darkness
    isolation_boost=0.10,            # +10% when alone
    multiple_threats_boost=0.30,     # +30% for multiple attackers
    weapon_visible_boost=0.40        # +40% for weapons
)
```

## 📊 Telemetry Data

Full telemetry is sent for each threat detection:

```json
{
  "timestamp": "2026-02-10T14:30:45.123",
  "motion": { "level": "high" },
  "detection": { "people_count": 2 },
  "tracking": {
    "tracked_people": 2,
    "individuals": [ ... ]
  },
  "behavior": {
    "overall_risk": "high",
    "pair_interactions": [ ... ]
  },
  "weapon_detection": {
    "has_weapon": true,
    "weapons_detected": [ ... ],
    "weapon_types": ["gun"]
  },
  "threat_assessment": {
    "visual_threat_probability": 0.87,
    "threat_level": "CRITICAL"
  }
}
```

## 🔄 Integration with Backend

### Send to Backend API

```python
import requests

# When threat detected
try:
    response = requests.post(
        "http://your-backend.com/threat-alert",
        json=telemetry,
        timeout=5
    )
    print(f"✅ Police notified: {response.status_code}")
except Exception as e:
    print(f"⚠️ Backend error: {e}")
```

### WebSocket for Real-Time Updates

```python
import asyncio
from websockets import connect

async def send_alert(telemetry):
    async with connect("ws://your-backend.com/threats") as websocket:
        await websocket.send(json.dumps(telemetry))
```

## 🎓 How It Works

### Processing Pipeline

```
Video Frame Input
       ↓
Motion Detection ──────┐
       ↓               │
Person Detection       │
       ↓               │
Person Tracking        │
       ↓               │
Behavior Analysis      │
       ↓               │
Weapon Detection       │
       ↓               │
Context Analysis       │
       ↓               │
Threat Scoring ◄───────┘
       ↓
Threat Classification
       ↓
Alert Generation (if needed)
       ↓
Logging & Recording (if critical)
       ↓
Telemetry to Backend
```

### Threat Score Calculation

```
Base Score = (Motion × 0.4) + (Behavior × 0.6)
Adjusted Score = Base Score × (1 + context_boost)

If Weapon Detected:
    Adjusted Score += 0.30
    Threat Level = At Least HIGH

Final Score = Clamp(0.0, Adjusted Score, 1.0)
```

## 🛠️ Robustness Features

✅ **Error Handling**
- Graceful degradation if YOLO unavailable
- Fallback to rule-based detection
- Try-catch blocks for video processing

✅ **Performance**
- Frame buffering for context
- Efficient tracking algorithm
- Minimal CPU usage

✅ **Privacy**
- No personal data storage
- Privacy-first design
- Evidence only when threat detected

✅ **Reliability**
- Alert deduplication
- Frame validation
- Safe cleanup on shutdown

## 📈 Accuracy Improvements (Roadmap)

- [ ] ML model training with real incident data
- [ ] Pose estimation for aggressive stances
- [ ] Activity recognition (running, fighting)
- [ ] Audio analysis (screams, threats)
- [ ] Ensemble models for higher confidence

## 🤝 Contributing

This engine is part of the SafeSphere initiative to provide universal safety. Contributions welcome!

## 📞 Support

For issues or questions, please submit to the main SafeSphere repository.

---

**Version:** 1.0  
**Last Updated:** February 10, 2026  
**Status:** Production Ready for Prototype  
🌍 **For Everyone's Safety**

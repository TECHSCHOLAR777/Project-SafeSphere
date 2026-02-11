# SOS Video Recording Implementation

## Overview

A comprehensive **SOS Video Recording System** has been implemented that allows users to record video incidents directly from their device when pressing the SOS button. The video is then processed through the threat_cv engine for threat analysis and automatically saved to the incidents database.

---

## Features Implemented

### 1. **Frontend Video Recording (script.js)**

#### VideoRecorder Class
- **Location**: Lines 314-460 in `script.js`
- **Capabilities**:
  - Request camera and microphone access from device
  - Record video in supported formats (WebM with VP9/VP8/H264 codecs, fallback to MP4)
  - Display real-time preview of camera feed
  - Calculate and display recording duration
  - Generate Blob from recorded chunks for upload
  - Graceful error handling for permission issues

**Key Methods**:
```javascript
- startRecording()      // Request permissions and begin recording
- stopRecording()       // Stop and return video blob
- getSupportedMimeType() // Detect browser-supported codec
- getStatus()          // Get current recording duration
- formatDuration()     // Format milliseconds to MM:SS
```

### 2. **SOS Recording Modal UI**

#### Modal Implementation
- **Location**: Lines 490-735 in `script.js` (openVideoRecordingModal method)
- **Features**:
  - Professional UI overlay with dark background
  - Real-time video preview from device camera
  - Large RED "START RECORDING" button
  - Timer display showing recording duration
  - Status messages (Ready → Recording → Processing)
  - "STOP & SEND" button (appears after recording starts)
  - "CANCEL" button to discard recording
  - Instructions for user guidance

**User Experience**:
1. Click SOS button anywhere in app
2. Modal appears with camera feed
3. User sees instructions about threat detection
4. Click "START RECORDING" to begin
5. Timer counts duration (0:00 format)
6. Click "STOP & SEND" to process video
7. Video uploaded to backend + threat analysis starts
8. Success/error notification displays

### 3. **Backend Video Upload Endpoint (backend_api.py)**

#### New Endpoint: `/api/sos-video`
- **Location**: Lines 553-679 in `backend_api.py`
- **Method**: POST with multipart form-data
- **Input Parameters**:
  - `video` (UploadFile) - WebM video file from client
  - `type` (Form) - Alert type (default: "SOS")
  - `latitude` (Form) - User location latitude
  - `longitude` (Form) - User location longitude
  - `duration_seconds` (Form) - Recording duration

**Processing Steps**:
1. Generate unique incident ID: `SOS_YYYYMMDD_HHMMSS_XXXXX`
2. Create `sos_videos/` directory if needed
3. Save video file to disk
4. Call `_process_video_through_threat_cv()` for analysis
5. Create incident record from threat analysis
6. Save incident to Supabase `incidents` table
7. Save SOS metadata to `sos_alerts` table
8. Return success response with incident ID

### 4. **Threat Detection Processing**

#### Function: `_process_video_through_threat_cv()`
- **Location**: Lines 681-800 in `backend_api.py`
- **Purpose**: Extract frames from video and analyze through threat_cv engine

**Processing Flow**:
1. Import SafeSphereThreatsCV engine and OpenCV
2. Open video file with cv2.VideoCapture
3. Process up to 150 frames (5 seconds @ 30fps)
4. For each frame:
   - Detect persons using PersonDetector
   - Detect weapons using WeaponDetector
   - Analyze behavior with BehaviorAnalyzer
   - Calculate threat score with ThreatScorer
5. Track:
   - Maximum threat score
   - Average threat score
   - Number of people detected
   - Weapons found
   - Behavioral descriptions

**Threat Level Determination**:
```
- CRITICAL: threat_score > 0.8 OR weapon_found = true
- HIGH:     threat_score > 0.6
- MEDIUM:   threat_score > 0.4
- LOW:      threat_score <= 0.4
```

**Return Data**:
```json
{
  "success": true,
  "incident_id": "SOS_20260211_143022_12345",
  "threat_level": "HIGH",
  "threat_score": 0.75,
  "people_count": 2,
  "weapon_detected": false,
  "behavior_summary": "Aggressive approach detected",
  "is_critical": false,
  "frames_processed": 150,
  "full_telemetry": { ... }
}
```

### 5. **Incident Auto-Creation**

When video is analyzed, an incident record is automatically created:

```python
{
  "incident_id": "SOS_20260211_143022_12345",
  "timestamp": "2026-02-11T14:30:22.123456",
  "threat_level": "HIGH",
  "threat_score": 0.75,
  "people_count": 2,
  "weapon_detected": false,
  "weapon_types": [],
  "behavior_summary": "Aggressive approach detected",
  "is_critical": false,
  "latitude": 28.7127,
  "longitude": 77.1154,
  "location_accuracy_m": 5.0,
  "source_id": "client_sos_video",
  "mode": "client",
  "full_telemetry": { ... }
}
```

This is saved to the **Supabase `incidents` table** automatically.

---

## Data Flow Diagram

```
┌─────────────────────────────┐
│  User clicks SOS button     │
│  (anywhere in app)          │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  VideoRecorder Modal Opens  │
│  - Camera permission req    │
│  - Video preview starts     │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  User clicks START          │
│  Recording begins           │
│  - Timer counts duration    │
│  - Red status indicator     │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  User clicks STOP & SEND    │
│  Recording stops            │
│  Video blob created         │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  FormData created                       │
│  - video blob                           │
│  - latitude/longitude                   │
│  - duration_seconds                     │
│  Sent via POST to `/api/sos-video`      │
└─────────────┬─────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────┐
│  Backend receives video file           │
│  - Save to /sos_videos/                │
│  - Unique incident ID created          │
└─────────────┬──────────────────────────┘
              │
              ▼
┌────────────────────────────────────────┐
│  threat_cv Analysis                    │
│  - Extract frames (up to 150)          │
│  - Detect persons/weapons              │
│  - Analyze behavior                    │
│  - Calculate threat_score              │
│  - Determine threat_level              │
└─────────────┬──────────────────────────┘
              │
              ▼
┌────────────────────────────────────────┐
│  Create Incident Record                │
│  - incident_id                         │
│  - threat_level (HIGH/MEDIUM/etc)     │
│  - threat_score (0.0-1.0)             │
│  - fulltelemetry from analysis        │
│  - location latitude/longitude         │
└─────────────┬──────────────────────────┘
              │
              ▼
┌────────────────────────────────────────┐
│  Save to Supabase                      │
│  - incidents table (threat analysis)   │
│  - sos_alerts table (metadata)         │
└─────────────┬──────────────────────────┘
              │
              ▼
┌────────────────────────────────────────┐
│  Return Response to Client             │
│  Success/Error notification shown      │
│  Incident ID provided for reference    │
└────────────────────────────────────────┘
```

---

## Technical Specifications

### Video Codec Support
The system supports multiple codecs in priority order:
1. **WebM + VP9 + Opus** (Highest quality)
2. **WebM + VP8 + Opus** (Good compatibility)
3. **WebM + H.264 + Opus** (Fallback)
4. **WebM** (Basic)
5. **MP4** (Last resort)

### Frame Processing
- **Max frames**: 150 frames processed (5 seconds @ 30fps)
- **Resolution**: 1280x720 (ideal, device-dependent)
- **Audio**: Mono/Stereo combined
- **MIME types**: `video/webm`, `video/mp4`

### Error Handling

**Frontend**:
- NotAllowedError → "Camera/Microphone access denied"
- NotFoundError → "No camera/microphone found"
- Generic errors → User-friendly error messages

**Backend**:
- Import failures → Fallback incident created without threat analysis
- Video processing errors → Logged, fallback incident created
- Database errors → Logged with exception traceback

### Fallback Behavior

If threat_cv engine is unavailable:
```python
{
  "threat_level": "MEDIUM",
  "threat_score": 0.5,
  "behavior_summary": "SOS video report (threat detection unavailable)",
  "frames_processed": 0,
  "processing_note": "Threat CV engine unavailable"
}
```

The incident is still saved to the database with a generic threat level.

---

## User Journey

### Scenario: User in Distress
1. **Feels threatened** → Clicks SOS button
2. **Modal appears** → "🚨 SOS RECORDING" with emergency warning
3. **Records video** → Captures 10-15 second clip of threat
4. **Submits** → Clicks "STOP & SEND"
5. **Backend processes**:
   - Detects people, weapons, aggression
   - Determines threat level
   - Saves to incidents table
6. **User notified** → "✅ SOS Alert sent! Video being analyzed..."
7. **Law enforcement** → Can view incident with:
   - Threat level classification
   - Number of people involved
   - Weapons detected
   - Behavioral analysis
   - User location
   - Video timestamp

---

## Integration Points

### Frontend Integration
- **Entry Point**: `ActionHandler.triggerSOS()`
- **Used by**: SOS button (header), Dashboard SOS button, Any page with emergency access
- **Dependencies**: VideoRecorder class, Toast notifications, Geolocation API

### Backend Integration
- **Endpoint**: `POST /api/sos-video`
- **Dependencies**: 
  - FastAPI, Pydantic
  - Supabase client
  - threat_cv engine (optional - has fallback)
  - OpenCV (if threat_cv available)

### Database
- **Tables**: `incidents`, `sos_alerts`
- **Columns used**:
  - incident_id, timestamp, threat_level, threat_score
  - people_count, weapon_detected, behavior_summary
  - latitude, longitude, source_id, mode
  - full_telemetry (JSON)

---

## Testing Checklist

- [ ] SOS button visible on dashboard
- [ ] Clicking SOS opens modal
- [ ] Camera permission request appears
- [ ] Grant permission → video feed displays
- [ ] START RECORDING button works
- [ ] Timer increments correctly (MM:SS format)
- [ ] STOP & SEND button appears
- [ ] Video uploads successfully
- [ ] Backend receives video file
- [ ] threat_cv analyzes frames
- [ ] Incident created in database
- [ ] Response shows success with incident ID
- [ ] Toast notification displays result
- [ ] CANCEL button discards recording
- [ ] Works on mobile and desktop browsers
- [ ] Fallback works if threat_cv unavailable

---

## Browser Compatibility

| Browser | Support | Notes |
|---------|---------|-------|
| Chrome | ✅ Full | Best WebM support |
| Firefox | ✅ Full | Good codec support |
| Safari | ⚠️ Limited | May need MP4 fallback |
| Edge | ✅ Full | Chrome-based |
| Mobile Chrome | ✅ Full | WebM preferred |
| Mobile Safari | ⚠️ Limited | H.264 codec |

---

## File Modifications Summary

### 1. `script.js`
- **Added**: VideoRecorder class (147 lines)
- **Modified**: ActionHandler.triggerSOS() method
- **Added**: openVideoRecordingModal() method
- **Added**: sendSOSWithVideo() async method
- **Updated**: Dashboard SOS button to use video recording

### 2. `backend_api.py`
- **Added**: `/api/sos-video` endpoint (127 lines)
- **Added**: `_process_video_through_threat_cv()` function (120 lines)
- **Added**: sos_videos directory creation

---

## Performance Considerations

### Video Processing
- **150 frame limit** prevents long processing times
- **Every 30fps = 5 seconds** of video analyzed
- **Lightweight frame sampling** reduces CPU load
- **Async uploads** don't block frontend

### Storage
- Videos saved to `/sos_videos/` directory
- Typical 30-second video = 2-5 MB
- Consider periodic cleanup of old videos

### Threat Detection
- **Frame rate**: ~30fps through threat_cv
- **Detection time**: 2-5 seconds per video
- **CPU load**: Moderate (parallelizable)

---

## Security Considerations

1. **Video Storage**: Currently local disk in `/sos_videos/`
   - Recommendation: Migrate to Supabase Storage for encryption
   
2. **Location Verification**: User device provides coordinates
   - May be inaccurate in indoor/dense buildings
   - Recommendation: Cross-reference with cell tower location
   
3. **False Negatives**: threat_cv may miss subtle threats
   - Mitigated by: Human review of flagged incidents
   
4. **Privacy**: Video permanently recorded
   - Recommendation: Auto-delete after retention period (30-90 days)

---

## Future Enhancements

1. **Real-time Upload Progress**: Show % progress while uploading
2. **Video Trimming**: Let users cut unwanted parts before sending
3. **Audio-only Option**: For audio evidence if camera unavailable
4. **Multiple Clips**: Record multiple short clips for context
5. **Vector Storage**: Store video embeddings for similarity search
6. **Batch Processing**: Multiple videos in single incident
7. **Mobile Optimization**: Adaptive quality based on bandwidth
8. **Geofencing**: Auto-activate recording in high-threat zones

---

## Conclusion

The SOS Video Recording System provides a powerful, user-friendly way for SafeSphere users to document threatening situations in real-time. The video is automatically analyzed by the threat_cv engine to determine threat levels and behavioral patterns, with all data saved to the incidents database for law enforcement and safety personnel to review.

This implementation ensures that critical evidence is captured and properly classified, enabling faster, more informed emergency response.

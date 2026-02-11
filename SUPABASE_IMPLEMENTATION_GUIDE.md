# SafeSphere Supabase Backend Implementation Guide

## Overview

The `backend_api.py` has been fully refactored to use **Supabase PostgreSQL** as the primary data store instead of JSON files. All threat incidents and SOS alerts now persist directly to Supabase tables.

### Key Changes
✅ `POST /threats/report` → Stores ThreatIncident objects in `public.incidents` table  
✅ `POST /api/sos` → Stores SOS alerts in `public.sos_alerts` table  
✅ `GET /incidents` → Queries from Supabase instead of JSON files  
✅ `GET /heatmap/*` → All heatmap data sourced from Supabase  
✅ Environment-driven configuration via `SUPABASE_URL` and `SUPABASE_KEY`  

---

## Prerequisites

### Required
- Python 3.9+
- Pip package manager
- Active Supabase project

### Optional
- `.env` file for local development

---

## Step 1: Create Supabase Project

1. **Sign Up**
   - Go to https://supabase.com
   - Create a new account or sign in
   - Click "New Project"

2. **Configure Project**
   - Enter a project name (e.g., "SafeSphere-Threats")
   - Choose a region (select closest to your location)
   - Set a strong database password
   - Click "Create new project" and wait 2-3 minutes for provisioning

3. **Note Your Credentials**
   In the Supabase dashboard:
   - Go to **Settings** → **API**
   - Copy your **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - Copy your **Anon Key** (public key for client access)
   - ⚠️ **DO NOT use the Service Role key in client applications**

---

## Step 2: Create Database Tables

Navigate to the **SQL Editor** in your Supabase project and run this script:

```sql
-- Create incidents table
CREATE TABLE IF NOT EXISTS public.incidents (
    incident_id VARCHAR(100) PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    threat_level VARCHAR(20) NOT NULL, -- LOW, MEDIUM, HIGH, CRITICAL
    threat_score DECIMAL(5,2) NOT NULL,
    people_count INTEGER,
    weapon_detected BOOLEAN DEFAULT FALSE,
    weapon_types JSONB, -- Array of weapon type strings
    behavior_summary TEXT,
    is_critical BOOLEAN DEFAULT FALSE,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    location_accuracy_m DECIMAL(8,2),
    source_id VARCHAR(100),
    mode VARCHAR(20), -- 'cctv' or 'client'
    full_telemetry JSONB, -- Complete telemetry data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for geographic queries
CREATE INDEX IF NOT EXISTS idx_incidents_location 
ON public.incidents(latitude, longitude);

-- Create index for threat level queries
CREATE INDEX IF NOT EXISTS idx_incidents_threat_level 
ON public.incidents(threat_level);

-- Create index for timestamp queries (recent incidents first)
CREATE INDEX IF NOT EXISTS idx_incidents_timestamp 
ON public.incidents(timestamp DESC);

-- Create SOS alerts table
CREATE TABLE IF NOT EXISTS public.sos_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) DEFAULT 'SOS', -- SOS, EMERGENCY, etc.
    details TEXT,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    status VARCHAR(20) DEFAULT 'active', -- active, resolved, canceled
    video_path TEXT, -- Path to the SOS video file, if applicable
    incident_id VARCHAR(100), -- Link to the incident created from video analysis
    severity VARCHAR(20) DEFAULT 'CRITICAL', -- LOW, MEDIUM, HIGH, CRITICAL
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Foreign key to link to the incidents table
    CONSTRAINT fk_incident
        FOREIGN KEY(incident_id) 
        REFERENCES incidents(incident_id)
        ON DELETE SET NULL
);

-- Create index for SOS status queries
CREATE INDEX IF NOT EXISTS idx_sos_alerts_status 
ON public.sos_alerts(status);

-- Create index for SOS location queries
CREATE INDEX IF NOT EXISTS idx_sos_alerts_location 
ON public.sos_alerts(latitude, longitude);

-- Create index for linking SOS alerts to incidents
CREATE INDEX IF NOT EXISTS idx_sos_alerts_incident_id
ON public.sos_alerts(incident_id);

-- Enable real-time subscriptions (optional)
ALTER TABLE public.incidents REPLICA IDENTITY FULL;
ALTER TABLE public.sos_alerts REPLICA IDENTITY FULL;
```

---

## Step 3: Install Dependencies

Run this in the Heatmap directory:

```bash
pip install supabase python-dotenv fastapi uvicorn
```

Check your `requirements.txt` includes supabase:
```bash
pip freeze | grep supabase
```

If not present, add to requirements.txt:
```
supabase>=0.8.0
python-dotenv>=1.0.0
```

---

## Step 4: Configure Environment Variables

### Option A: Local Development (.env file)

Create a `.env` file in `/workspaces/Project-SafeSphere/Heatmap/`:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here

# Optional: Debug mode
DEBUG=true
```

⚠️ **Never commit .env to version control!**

Load in Python:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Option B: Environment Variables (Production)

Set variables in your deployment environment:

#### Docker
```dockerfile
ENV SUPABASE_URL="https://your-project.supabase.co"
ENV SUPABASE_KEY="your-anon-key-here"
```

#### Heroku
```bash
heroku config:set SUPABASE_URL="https://your-project.supabase.co"
heroku config:set SUPABASE_KEY="your-anon-key-here"
```

#### Docker Compose
```yaml
services:
  safesphere-backend:
    environment:
      - SUPABASE_URL=https://your-project.supabase.co
      - SUPABASE_KEY=your-anon-key-here
```

---

## Step 5: Test Supabase Connection

Create a test script `test_supabase.py`:

```python
import os
from supabase import create_client

# Load environment
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY")

# Test connection
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase connection successful!")
    
    # Test table access
    response = supabase.table("incidents").select("COUNT").execute()
    print(f"✅ Can access incidents table")
    
    response = supabase.table("sos_alerts").select("COUNT").execute()
    print(f"✅ Can access sos_alerts table")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

Run it:
```bash
python test_supabase.py
```

---

## Step 6: Run the Backend API

### Using Uvicorn directly
```bash
cd Heatmap
python -m uvicorn backend_api:app --reload --host 0.0.0.0 --port 8000
```

### Using a startup script
Create `start_backend.sh`:
```bash
#!/bin/bash
source .env
cd Heatmap
python -m uvicorn backend_api:app --reload --host 0.0.0.0 --port 8000
```

Make it executable:
```bash
chmod +x start_backend.sh
./start_backend.sh
```

### Expected Output
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✅ Connected to Supabase: xxxxx...
INFO:     Application startup complete
```

---

## API Usage Examples

### 1. Report a Threat Incident

**Endpoint:** `POST /threats/report`

```bash
curl -X POST http://localhost:8000/threats/report \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC_20260211_120000_001",
    "timestamp": "2026-02-11T12:00:00Z",
    "threat_level": "HIGH",
    "threat_score": 0.85,
    "people_count": 3,
    "weapon_detected": true,
    "weapon_types": ["knife"],
    "behavior_summary": "Rapid approach, aggressive behavior",
    "is_critical": true,
    "latitude": 40.7128,
    "longitude": -74.0060,
    "location_accuracy_m": 15.0,
    "source_id": "CAM_001",
    "mode": "cctv",
    "full_telemetry": {
      "motion": "high",
      "tracked_persons": 3,
      "confidence": 0.94
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "incident_id": "INC_20260211_120000_001",
  "message": "Incident received and saved to database"
}
```

### 2. List Recent Incidents

**Endpoint:** `GET /incidents`

```bash
curl http://localhost:8000/incidents?limit=50
```

**Response:**
```json
{
  "count": 50,
  "incidents": [
    {
      "incident_id": "INC_20260211_120000_001",
      "timestamp": "2026-02-11T12:00:00Z",
      "threat_level": "HIGH",
      "threat_score": 0.85,
      "people_count": 3,
      "weapon_detected": true,
      "latitude": 40.7128,
      "longitude": -74.0060,
      ...
    }
  ]
}
```

### 3. Get Incident by ID

**Endpoint:** `GET /incidents/{incident_id}`

```bash
curl http://localhost:8000/incidents/INC_20260211_120000_001
```

### 4. Find Nearby Incidents

**Endpoint:** `GET /incidents/nearby`

```bash
curl "http://localhost:8000/incidents/nearby?lat=40.7128&lng=-74.0060&radius_km=2.0&limit=100"
```

### 5. Get Heatmap Data

**Endpoint:** `GET /heatmap/data`

```bash
curl "http://localhost:8000/heatmap/data?zone_step=0.002&limit=2000"
```

**Response:**
```json
{
  "count": 15,
  "zones": [
    {
      "lat": 40.712,
      "lng": -74.006,
      "weight": 8.5,
      "avg": 0.85,
      "count": 10
    }
  ]
}
```

### 6. Trigger SOS Alert

**Endpoint:** `POST /api/sos`

```bash
curl -X POST http://localhost:8000/api/sos \
  -H "Content-Type: application/json" \
  -d '{
    "type": "SOS",
    "details": "Person in distress at location",
    "location": {
      "lat": 40.7128,
      "lng": -74.0060
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "SOS Alert recorded and emergency services notified",
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 7. Seed Test Data

**Endpoint:** `POST /seed/incidents`

```bash
curl -X POST http://localhost:8000/seed/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "center_lat": 40.7128,
    "center_lng": -74.0060,
    "count": 100,
    "radius_km": 1.5,
    "mode": "cctv",
    "source_prefix": "TEST_CAM"
  }'
```

---

## Field Mapping Reference

### ThreatIncident → incidents table

| ThreatIncident Field | Database Column | Type | Notes |
|---|---|---|---|
| `incident_id` | `incident_id` | VARCHAR(100) PK | Unique identifier |
| `timestamp` | `timestamp` | TIMESTAMP | ISO 8601 format |
| `threat_level` | `threat_level` | VARCHAR(20) | LOW/MEDIUM/HIGH/CRITICAL |
| `threat_score` | `threat_score` | DECIMAL(5,2) | 0.0-1.0 range |
| `people_count` | `people_count` | INTEGER | Number of people detected |
| `weapon_detected` | `weapon_detected` | BOOLEAN | True if weapon detected |
| `weapon_types` | `weapon_types` | JSONB | Array: ["knife", "gun", "blade"] |
| `behavior_summary` | `behavior_summary` | TEXT | Textual description |
| `is_critical` | `is_critical` | BOOLEAN | Requires immediate attention |
| `latitude` | `latitude` | DECIMAL(10,8) | Geolocation |
| `longitude` | `longitude` | DECIMAL(11,8) | Geolocation |
| `location_accuracy_m` | `location_accuracy_m` | DECIMAL(8,2) | Accuracy radius in meters |
| `source_id` | `source_id` | VARCHAR(100) | Camera ID or client ID |
| `mode` | `mode` | VARCHAR(20) | 'cctv' or 'client' |
| `full_telemetry` | `full_telemetry` | JSONB | Complete detection data |

---

## Troubleshooting

### Connection Errors

```
❌ Supabase connection failed: [Errno -2] Name or service not known
```

**Solution:**
- Check SUPABASE_URL is correct (starts with https://)
- Verify no typos in URL
- Test internet connectivity

### Authentication Errors

```
❌ 401 Unauthorized: Invalid API key
```

**Solution:**
- Use **Anon Key**, not Service Role Key
- Verify key is copied completely
- Check for extra whitespace

### Table Not Found

```
❌ PostgreSQL error: relation "incidents" does not exist
```

**Solution:**
- Run SQL script to create tables (Step 2)
- Verify tables exist in Supabase SQL Editor
- Check schema is `public`

### Missing Environment Variables

```
ValueError: Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_KEY
```

**Solution:**
- Create `.env` file with variables
- Or set OS environment variables
- Run `python -c "import os; print(os.environ.get('SUPABASE_URL'))"`

---

## Database Queries (for Analytics)

### Count Incidents by Threat Level

```sql
SELECT threat_level, COUNT(*) as count
FROM incidents
GROUP BY threat_level
ORDER BY count DESC;
```

### Find Critical Incidents (Last 24 Hours)

```sql
SELECT incident_id, timestamp, threat_score, weapon_detected
FROM incidents
WHERE is_critical = true
  AND timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;
```

### Geographic Heatmap (SQL PostGIS)

```sql
SELECT 
  ROUND(latitude::numeric, 3) as lat,
  ROUND(longitude::numeric, 3) as lng,
  COUNT(*) as count,
  AVG(threat_score) as avg_threat
FROM incidents
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY ROUND(latitude::numeric, 3), ROUND(longitude::numeric, 3)
ORDER BY count DESC;
```

---

## Performance Optimization

### Enable Row Level Security (RLS) - Optional

For production, add authentication:

```sql
ALTER TABLE incidents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable read access for all users" ON incidents
  FOR SELECT USING (true);

CREATE POLICY "Enable insert for authenticated users" ON incidents
  FOR INSERT WITH CHECK (auth.role() = 'authenticated');
```

### Add Database Triggers - Optional

Auto-update `updated_at`:

```sql
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_incidents_timestamp
  BEFORE UPDATE ON incidents
  FOR EACH ROW
  EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_sos_alerts_timestamp
  BEFORE UPDATE ON sos_alerts
  FOR EACH ROW
  EXECUTE FUNCTION update_timestamp();
```

---

## Monitoring & Logs

### View API Logs in Terminal

```bash
# With detailed logging
python -m uvicorn backend_api:app --reload --log-level debug
```

### Check Supabase Logs

In Supabase dashboard:
- **Logs** → **Database** (for SQL errors)
- **Logs** → **API** (for HTTP requests)
- **Logs** → **Auth** (for authentication issues)

---

## Next Steps

1. ✅ Test incident insertion with `/seed/incidents`
2. ✅ Verify data in Supabase dashboard
3. ✅ Query `/heatmap/data` to see visualization
4. ✅ Integrate with threat_cv engine (POST to `/threats/report`)
5. ✅ Set up frontend to consume `/incidents` and `/heatmap/data` endpoints

---

## Support & Resources

- **Supabase Docs**: https://supabase.com/docs
- **Python Client**: https://github.com/supabase-community/supabase-py
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **PostGIS Queries**: https://postgis.net/docs

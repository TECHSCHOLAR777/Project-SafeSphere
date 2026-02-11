# SafeSphere Supabase Quick Start

Get the backend running in 5 minutes.

## 1. Get Supabase Credentials (2 min)

1. Go to https://supabase.com → Sign in/create account
2. Create a new project (wait 2-3 min for provisioning)
3. Go to **Settings → API**
4. Copy **Project URL** and **Anon Key**

## 2. Create Database Tables (1 min)

Go to **SQL Editor** in Supabase and run:

```sql
CREATE TABLE IF NOT EXISTS public.incidents (
    incident_id VARCHAR(100) PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    threat_level VARCHAR(20) NOT NULL,
    threat_score DECIMAL(5,2) NOT NULL,
    people_count INTEGER,
    weapon_detected BOOLEAN DEFAULT FALSE,
    weapon_types JSONB,
    behavior_summary TEXT,
    is_critical BOOLEAN DEFAULT FALSE,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    location_accuracy_m DECIMAL(8,2),
    source_id VARCHAR(100),
    mode VARCHAR(20),
    full_telemetry JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.sos_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) DEFAULT 'SOS',
    details TEXT,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_incidents_location ON public.incidents(latitude, longitude);
CREATE INDEX idx_incidents_threat_level ON public.incidents(threat_level);
CREATE INDEX idx_incidents_timestamp ON public.incidents(timestamp DESC);
CREATE INDEX idx_sos_alerts_status ON public.sos_alerts(status);
```

## 3. Install Dependencies (1 min)

```bash
cd Heatmap
pip install supabase python-dotenv
```

## 4. Set Environment Variables (30 sec)

Create `.env` file in `Heatmap/` directory:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
```

Replace with your actual credentials from step 1.

## 5. Start Backend (30 sec)

```bash
cd Heatmap
python -m uvicorn backend_api:app --reload --port 8000
```

You should see:
```
✅ Connected to Supabase: xxxxx...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 6. Test It (1 min)

### Insert a test incident:
```bash
curl -X POST http://localhost:8000/threats/report \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "TEST_001",
    "timestamp": "2026-02-11T12:00:00Z",
    "threat_level": "HIGH",
    "threat_score": 0.85,
    "people_count": 2,
    "weapon_detected": true,
    "weapon_types": ["knife"],
    "behavior_summary": "Test incident",
    "is_critical": false,
    "full_telemetry": {},
    "latitude": 40.7128,
    "longitude": -74.0060,
    "location_accuracy_m": 15,
    "source_id": "TEST",
    "mode": "test"
  }'
```

### List incidents:
```bash
curl http://localhost:8000/incidents?limit=10
```

### Get heatmap:
```bash
curl "http://localhost:8000/heatmap/data?limit=100"
```

### Seed 50 test incidents:
```bash
curl -X POST http://localhost:8000/seed/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "center_lat": 40.7128,
    "center_lng": -74.0060,
    "count": 50,
    "radius_km": 1.0,
    "mode": "cctv",
    "source_prefix": "CAM"
  }'
```

## Verify Data

Go to Supabase dashboard → **Table Editor**:
1. Click `incidents` table
2. Should see your test data rows
3. Click `sos_alerts` to see empty table

## Done! 🎉

Your backend is now connected to Supabase. 

### Next Steps:
1. Start threat_cv engine and POST incidents to `http://localhost:8000/threats/report`
2. Verify data appears in Supabase
3. Query endpoints as needed
4. Deploy with your cloud provider

### Documentation:
- Full setup: [SUPABASE_IMPLEMENTATION_GUIDE.md](../SUPABASE_IMPLEMENTATION_GUIDE.md)
- Changes made: [BACKEND_REDESIGN_SUMMARY.md](../BACKEND_REDESIGN_SUMMARY.md)

### Troubleshooting:

**Connection error?**
```
ValueError: Missing Supabase credentials
```
→ Check .env file exists and has correct SUPABASE_URL and SUPABASE_KEY

**Table not found?**
```
PostgreSQL error: relation "incidents" does not exist
```
→ Run SQL scripts in Supabase SQL Editor (step 2)

**Can't insert data?**
```
401 Unauthorized
```
→ Use Anon Key, not Service Role Key. Check key is complete.

---

**Get more help:** See [SUPABASE_IMPLEMENTATION_GUIDE.md](../SUPABASE_IMPLEMENTATION_GUIDE.md#troubleshooting) for detailed troubleshooting.

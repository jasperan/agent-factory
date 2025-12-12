# Field Eye Deployment Guide

## Quick Deployment (5 minutes)

### 1. Deploy Database Schema to Supabase

**Step 1:** Open Supabase SQL Editor
- Go to: https://mggqgrxwumnnujojndub.supabase.co/project/_/sql/new
- Or: Dashboard → SQL Editor → New Query

**Step 2:** Copy and run the schema
```bash
# Copy the schema file
cat agent_factory/field_eye/config/field_eye_schema.sql
```

**Step 3:** Paste into SQL Editor and click "Run"

**Expected Output:**
```
Success. No rows returned
```

**What Gets Created:**
- ✅ 5 tables: `field_eye_sessions`, `field_eye_frames`, `field_eye_defects`, `field_eye_kits`, `field_eye_models`
- ✅ Vector extension enabled (pgvector)
- ✅ Indexes for fast queries
- ✅ RLS policies (Row Level Security)
- ✅ Helper functions (e.g., `get_field_eye_stats()`)

---

### 2. Verify Deployment

**Test from Python:**
```bash
poetry run python -c "
from agent_factory.memory.storage import SupabaseMemoryStorage
storage = SupabaseMemoryStorage()
result = storage.client.table('field_eye_sessions').select('id').limit(1).execute()
print('✅ Field Eye tables deployed successfully')
"
```

**Test from Telegram:**
```
/fieldeye_stats
```

**Expected Response:**
```
📊 Field Eye Statistics

Sessions: 0
Frames: 0
Defects: 0
```

---

### 3. Bot Status Check

**Current Status:**
- ✅ Field Eye handlers registered in bot.py
- ✅ 4 commands available: `/fieldeye_upload`, `/fieldeye_stats`, `/fieldeye_defects`, `/fieldeye_sessions`
- ⚠️ Video upload temporarily disabled (NumPy dependency conflict)
- ✅ Stats/defects/sessions work (database queries only)

**Bot Not Running:**
The bot is NOT currently running in the background. To start it:

```bash
# Option 1: Foreground (for testing)
cd "C:/Users/hharp/OneDrive/Desktop/Agent Factory"
poetry run python -m agent_factory.integrations.telegram

# Option 2: Background (production)
# Windows: Use Windows Task Scheduler
# Or create a startup script
```

---

### 4. Resolve NumPy Dependency Conflict (Optional)

**Problem:** Field Eye requires NumPy 2.x + OpenCV, but LangChain 0.2.x requires NumPy 1.x

**Solutions:**

**Option A: Wait for LangChain Update (Recommended)**
- LangChain team is working on NumPy 2.x support
- Monitor: https://github.com/langchain-ai/langchain/issues

**Option B: Use opencv-python-headless**
```bash
# Try headless version (may be compatible with NumPy 1.x)
poetry add opencv-python-headless
```

**Option C: Separate Environment**
```bash
# Create separate Python env for Field Eye video processing
# Then call via subprocess from main bot
```

**Current Workaround:**
Field Eye handlers check `FIELD_EYE_AVAILABLE` flag and show clear error message if dependencies unavailable.

---

### 5. Enable Video Upload (After NumPy Resolution)

Once dependencies are resolved:

1. **Test import:**
```bash
poetry run python -c "
from agent_factory.field_eye.utils.video_processor import VideoProcessor
from agent_factory.field_eye.utils.pause_detector import PauseDetector
print('✅ Field Eye dependencies OK')
"
```

2. **Test video upload via Telegram:**
- Send video file to bot
- Add caption: `/fieldeye_upload`
- Should extract frames, detect pauses, save to DB

---

## Troubleshooting

### Schema Deployment Fails

**Error:** `relation "field_eye_sessions" already exists`
- **Solution:** Schema already deployed, skip this step

**Error:** `extension "vector" does not exist`
- **Solution:** Enable pgvector in Supabase:
  - Dashboard → Database → Extensions
  - Search "vector"
  - Click "Enable"
  - Re-run schema

### Bot Won't Start

**Error:** `Conflict: terminated by other getUpdates request`
- **Solution:** Another bot instance is running. Kill it:
```bash
tasklist | grep python
# Find the PID, then:
taskkill /PID <pid> /F
```

**Error:** `UnicodeEncodeError: 'charmap' codec`
- **Solution:** Already fixed in latest commit (8d30911)
- All emoji print statements replaced with ASCII

### Field Eye Commands Don't Work

**Error:** `Field Eye Not Available`
- **Cause:** NumPy dependency conflict
- **Solution:** See "Resolve NumPy Dependency Conflict" above

---

## Production Deployment Checklist

- [ ] Deploy Field Eye schema to Supabase
- [ ] Verify schema with test query
- [ ] Test `/fieldeye_stats` command
- [ ] Test `/fieldeye_defects` command
- [ ] Test `/fieldeye_sessions` command
- [ ] Resolve NumPy conflict (optional, for video upload)
- [ ] Set up bot auto-start (Task Scheduler)
- [ ] Configure health monitoring (http://localhost:9876/health)
- [ ] Set up log rotation
- [ ] Test with real inspection video

---

## Next Steps

1. **Deploy schema now** (2 minutes)
2. **Start bot** (to test stats commands)
3. **Resolve NumPy conflict** (for video upload feature)
4. **Test with real video** (when dependencies ready)

**Revenue Timeline:**
- **Month 3-4:** Hardware kits available ($99-$149)
- **Month 6:** SaaS launch ($29-$99/mo)
- **Month 9-12:** Robot dataset licensing outreach
- **Year 3:** $1M+ ARR target

---

**Last Updated:** 2025-12-11
**Schema Version:** 1.0
**Bot Version:** With Field Eye handlers (commit fc47189)

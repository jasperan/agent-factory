# Phase 5 Deployment Guide

**RIVET Pro Research Pipeline - Database Schema Deployment**

---

## Overview

Phase 5 enables autonomous knowledge base growth by automatically discovering and ingesting forum content when the bot encounters questions it can't answer (Route C).

**Time Required:** 10 minutes
**Prerequisites:** Supabase project with credentials in `.env`

---

## What Gets Deployed

### Database Table
- **`source_fingerprints`** - Tracks discovered sources for deduplication and ingestion monitoring

### Features
- ✅ SHA-256 URL fingerprinting for deduplication
- ✅ Source type tracking (Stack Overflow, Reddit, YouTube, PDFs)
- ✅ Ingestion lifecycle tracking (queued → completed)
- ✅ 4 performance indexes for fast lookups

---

## Step-by-Step Deployment

### Step 1: Open Supabase SQL Editor (2 minutes)

1. Navigate to your Supabase project: https://app.supabase.com
2. Select your project (e.g., `rivet-pro-kb`)
3. Click **SQL Editor** in the left sidebar
4. Click **New Query**

### Step 2: Deploy Schema (3 minutes)

1. Open this file on your local machine:
   ```
   docs/database/phase5_research_pipeline_migration.sql
   ```

2. Copy the ENTIRE contents (Ctrl+A, Ctrl+C)

3. Paste into Supabase SQL Editor

4. Click **Run** (or press F5)

5. Wait for confirmation:
   ```
   Success. No rows returned
   ```

### Step 3: Verify Deployment - SQL Method (2 minutes)

**Option A: Quick SQL Verification**

Run this query in SQL Editor:
```sql
SELECT COUNT(*) FROM source_fingerprints;
```

**Expected:** `0` (table empty)
**If error:** Table doesn't exist - re-run migration SQL

Check indexes:
```sql
SELECT indexname FROM pg_indexes WHERE tablename = 'source_fingerprints';
```

**Expected:** 5 indexes
- `source_fingerprints_pkey`
- `idx_source_fingerprints_hash`
- `idx_source_fingerprints_queued`
- `idx_source_fingerprints_created`
- `idx_source_fingerprints_source_type`

### Step 4: Verify Deployment - Python Method (3 minutes)

**Option B: Automated Verification Script**

1. Open terminal/PowerShell
2. Navigate to Agent Factory directory:
   ```bash
   cd C:\Users\hharp\OneDrive\Desktop\Agent Factory
   ```

3. Run verification script:
   ```bash
   poetry run python scripts/deployment/verify_phase5_schema.py
   ```

4. Review output:
   ```
   ============================================================
   VERIFYING RIVET PRO PHASE 5 SCHEMA
   Research Pipeline - Source Fingerprints Table
   ============================================================

   [OK] Connected to Supabase
   [OK] Table exists
   [OK] Insert succeeded
   [OK] Query succeeded
   [OK] Cleanup succeeded

   ============================================================
   VERIFICATION COMPLETE - PHASE 5 SCHEMA OPERATIONAL
   ============================================================
   ```

**If all tests pass:** ✅ Schema deployed successfully!

**If tests fail:** See Troubleshooting section below

---

## Post-Deployment Testing

### Test 1: Trigger Research Pipeline (5 minutes)

1. Send Telegram query to RIVET Pro bot:
   ```
   Mitsubishi iQ-R PLC ethernet connection not working
   ```

2. Bot should respond with:
   ```
   🔍 Researching Similar Issues
   I'm searching forums and documentation for additional information.
   Check back in 3-5 minutes for updated results!
   ```

3. Check fingerprints table:
   ```sql
   SELECT * FROM source_fingerprints ORDER BY created_at DESC LIMIT 5;
   ```

**Expected:** 5-10 rows with Stack Overflow/Reddit URLs

### Test 2: Monitor Ingestion (3-5 minutes)

Wait 3-5 minutes, then check ingestion completion:

```sql
SELECT
  url,
  source_type,
  created_at,
  ingestion_completed_at,
  EXTRACT(EPOCH FROM (ingestion_completed_at - created_at)) / 60 as minutes_to_complete
FROM source_fingerprints
WHERE ingestion_completed_at IS NOT NULL
ORDER BY ingestion_completed_at DESC
LIMIT 5;
```

**Expected:** Some rows should have `ingestion_completed_at` timestamps

### Test 3: Verify KB Growth

Check if new atoms were created:

```sql
SELECT COUNT(*) FROM knowledge_atoms
WHERE created_at > NOW() - INTERVAL '10 minutes';
```

**Expected:** 1-5 new atoms (from forum ingestion)

---

## Troubleshooting

### Issue: "Table source_fingerprints does not exist"

**Cause:** Migration SQL didn't execute

**Fix:**
1. Re-copy migration SQL
2. Ensure you copied ENTIRE file (all 112 lines)
3. Re-run in SQL Editor
4. Verify with: `\dt source_fingerprints`

### Issue: "Only 4 indexes found (expected 5)"

**Cause:** Index creation failed

**Fix:**
1. Check Supabase logs for errors
2. Manually run index creation:
   ```sql
   CREATE INDEX IF NOT EXISTS idx_source_fingerprints_hash
     ON source_fingerprints(url_hash);
   ```
3. Repeat for other 3 indexes (see migration SQL)

### Issue: "Duplicate key value violates unique constraint"

**Status:** ✅ This is CORRECT behavior!

**Explanation:** Deduplication is working - same URL can't be inserted twice

### Issue: Python verification script fails to connect

**Fix:**
1. Verify `.env` has correct credentials:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your-key-here
   ```
2. Test connection:
   ```bash
   poetry run python -c "from supabase import create_client; import os; from dotenv import load_dotenv; load_dotenv(); print('OK')"
   ```

---

## Success Metrics

After 24 hours of operation, you should see:

```sql
-- Total sources discovered
SELECT COUNT(*) FROM source_fingerprints;
-- Expected: 50-100

-- Sources by type
SELECT source_type, COUNT(*) FROM source_fingerprints GROUP BY source_type;
-- Expected: stackoverflow (30-50), reddit (20-40)

-- Completion rate
SELECT
  COUNT(*) as total,
  COUNT(ingestion_completed_at) as completed,
  ROUND(100.0 * COUNT(ingestion_completed_at) / COUNT(*), 2) as completion_rate
FROM source_fingerprints;
-- Expected: 60-80% completion rate
```

---

## Rollback (If Needed)

To remove Phase 5 schema:

```sql
DROP TABLE IF EXISTS source_fingerprints CASCADE;
```

**Warning:** This deletes all source tracking data!

---

## Next Steps

✅ **Schema Deployed**
✅ **Verification Complete**
✅ **Research Pipeline Operational**

**Now:**
1. Monitor Telegram bot logs for Route C triggers
2. Watch fingerprints table populate
3. Verify KB atom count increases over time
4. Move to next task in backlog

---

## Support Files

| File | Purpose |
|------|---------|
| `docs/database/phase5_research_pipeline_migration.sql` | Schema migration SQL (deploy this) |
| `docs/database/verify_phase5_deployment.sql` | Manual verification queries |
| `scripts/deployment/verify_phase5_schema.py` | Automated verification script |
| `PHASE5_COMPLETE.md` | Complete implementation summary |

---

**Deployment Complete!** Research pipeline is now autonomous. 🚀

# Railway PostgreSQL Setup - Quick Start (5 Minutes)

**Purpose:** Set up Railway as second database for RIVET (dual database operation)
**Status:** Neon already deployed ✅ | Railway setup needed
**Time:** 5-10 minutes

---

## Step 1: Create Railway PostgreSQL Database (2 min)

1. **Go to Railway:** https://railway.app/
2. **Login** with GitHub (if not already logged in)
3. **Create New Project:**
   - Click "New Project" button
   - Select "Provision PostgreSQL"
   - Wait 30-60 seconds for provisioning

4. **Database will show as "Active"** when ready

---

## Step 2: Get Connection Credentials (2 min)

1. **Click on your PostgreSQL service** (the purple database icon)
2. **Go to "Connect" tab** (or "Variables" tab)
3. **Copy these values:**

   You'll see variables like:
   ```
   PGHOST=containers-us-west-123.railway.app
   PGPORT=5432
   PGDATABASE=railway
   PGUSER=postgres
   PGPASSWORD=abc123xyz789
   DATABASE_URL=postgresql://postgres:abc123xyz789@containers-us-west-123.railway.app:5432/railway
   ```

4. **Copy the DATABASE_URL** (this has everything in one string)

---

## Step 3: Update .env File (1 min)

1. **Open:** `C:\Users\hharp\OneDrive\Desktop\Agent Factory\.env`

2. **Find the Railway section** (around line 60):
   ```
   # TODO: Fill these values from Railway dashboard
   RAILWAY_DB_HOST=containers-us-west-xxx.railway.app
   RAILWAY_DB_PORT=5432
   RAILWAY_DB_NAME=railway
   RAILWAY_DB_USER=postgres
   RAILWAY_DB_PASSWORD=your_railway_password_here
   RAILWAY_DB_URL=postgresql://postgres:your_railway_password_here@containers-us-west-xxx.railway.app:5432/railway
   ```

3. **Replace with your actual values:**
   ```
   RAILWAY_DB_HOST=containers-us-west-123.railway.app
   RAILWAY_DB_PORT=5432
   RAILWAY_DB_NAME=railway
   RAILWAY_DB_USER=postgres
   RAILWAY_DB_PASSWORD=abc123xyz789
   RAILWAY_DB_URL=postgresql://postgres:abc123xyz789@containers-us-west-123.railway.app:5432/railway
   ```

4. **Save the file**

---

## Step 4: I'll Deploy the Schema (Automated)

Once you've updated .env, I'll run:
```bash
poetry run python scripts/deploy_multi_provider_schema.py --rivet --provider railway
```

This will:
- ✅ Create 4 tables (manuals, manual_chunks, conversations, user_feedback)
- ✅ Enable pgvector extension
- ✅ Create 12+ indexes (including HNSW vector index)
- ✅ Create search functions

---

## Step 5: Verify Both Databases (Automated)

Then I'll test both databases are working:
```bash
cd agent-factory-rivet-launch
poetry run python rivet/config/multi_provider_db.py
```

Expected output:
```
Testing neon...     [PASS]
Testing railway...  [PASS]
Testing supabase... [FAIL] (expected, hostname issue)
```

---

## What You'll Have After This

✅ **Dual Database Setup:**
- **Neon** (primary) - 1536-dimension vectors, already deployed
- **Railway** (backup) - Ready for deployment

✅ **Automatic Failover:**
- If Neon fails → Railway takes over
- If Railway fails → Neon takes over
- Zero downtime for RIVET agents

✅ **Production-Ready:**
- Both databases have identical schemas
- RIVET agents work with either database
- Switch providers by changing one .env variable

---

## Railway Dashboard Tips

**Monitor Usage:**
- Go to your Railway project
- Click PostgreSQL service
- "Metrics" tab shows CPU, memory, disk usage

**Free Tier Limits:**
- $5/month credit (renews monthly)
- ~500 hours of usage
- Perfect for development + backup database

**Upgrade if Needed:**
- Hobby Plan: $5/month (no sleep, more resources)
- Pro Plan: $20/month (production features)

---

## Ready?

**When you've completed Steps 1-3 above, let me know!**

I'll run the deployment commands and verify both databases are working together.

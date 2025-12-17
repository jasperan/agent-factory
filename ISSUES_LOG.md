# Issues Log

Known issues, bugs, and blockers.

---

## [2025-12-17 08:00] STATUS: [INFO] - Autonomous System Ready for Testing

**Status:** INFO (Not a blocker)

**Description:**
Autonomous Claude system complete but not yet tested in production.

**Affected Components:**
- Issue queue builder (needs real GitHub issues)
- Safety monitor (needs real execution for cost/time tracking)
- Claude executor (needs GitHub Actions environment)
- PR creator (needs real issues to create PRs)

**Impact:**
- **Severity:** NONE
- All components include test modes (dry run, mock data)
- Can test locally before GitHub Actions deployment
- No blocking issues

**Testing Required:**
1. **Local component tests** (15 min)
   ```bash
   python scripts/autonomous/issue_queue_builder.py
   python scripts/autonomous/safety_monitor.py
   python scripts/autonomous/telegram_notifier.py
   ```

2. **Full dry run** (30 min)
   ```bash
   DRY_RUN=true python scripts/autonomous/autonomous_claude_runner.py
   ```

3. **GitHub Actions test** (1 hour)
   - Configure secrets: ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN
   - Manual workflow dispatch with dry_run=true
   - Monitor logs and Telegram notifications

4. **First real run** (supervised)
   - Manual dispatch with max_issues=1-2, dry_run=false
   - Review created draft PRs
   - Verify safety limits

**Next Steps:**
1. User configures GitHub secrets
2. User runs local tests
3. User triggers manual GitHub Actions run (dry run)
4. User reviews and approves
5. Enable nightly automation

**Status:** Ready for testing, comprehensive documentation provided

---

## [2025-12-17 03:30] STATUS: [INFO] - Telegram Admin Panel Using Placeholder Data

**Status:** INFO (Not a blocker)

**Description:**
Telegram admin panel is fully functional but displays placeholder data until integrated with real sources.

**Affected Features:**
- Agent status (shows 3 placeholder agents)
- Content queue (shows 2 placeholder items)
- KB statistics (shows placeholder atom counts)
- Analytics dashboard (shows placeholder metrics)
- System health (shows placeholder service status)

**Impact:**
- **Severity:** LOW
- UI and logic are complete and working
- Commands execute without errors
- Navigation and permissions functional
- Real data integration is Phase 8+ work

**Root Cause:**
- Phase 1-7 focused on building UI/logic
- Real data sources require:
  - LangFuse API queries
  - Database table creation (content_queue, admin_actions)
  - VPS SSH commands
  - Stripe API integration

**Proposed Solution:**
Phase 8+ integration tasks:
1. Create database tables (SQL provided in TELEGRAM_ADMIN_COMPLETE.md)
2. Query LangFuse for agent traces
3. Query database for content queue
4. SSH to VPS for KB and service stats
5. Query Stripe for revenue metrics

**Workaround:**
Use admin panel to test UI and navigation. Placeholder data demonstrates functionality.

**Status:** Documented, not blocking testing

## [2025-12-17 00:15] STATUS: [OPEN] - pgvector Extension Not Available for PostgreSQL 18

**Problem:**
Cannot install pgvector extension on PostgreSQL 18 for Windows

**Root Cause:**
- PostgreSQL 18 is too new (released 2024)
- pgvector project doesn't provide pre-built Windows binaries for PostgreSQL 18 yet
- Latest available: pgvector for PostgreSQL 13-17
- Requires compiling from source (complex on Windows, requires Visual Studio)

**Impact:**
- **Severity:** HIGH
- Blocks schema deployment (schema requires `embedding vector(1536)`)
- Blocks semantic search functionality
- Blocks knowledge base operations requiring embeddings
- Cannot use Agent Factory's hybrid search (semantic + keyword)

**Error Message:**
```
psycopg.errors.FeatureNotSupported: extension "vector" is not available
HINT:  The extension must first be installed on the system where PostgreSQL is running.
```

**Workarounds Attempted:**
1. ❌ Download pgvector v0.7.4 for PG13 - GitHub 404 error
2. ❌ Download pgvector v0.7.0 for PG13 - GitHub 404 error
3. ❌ Deploy modified schema without pgvector - Script ran but created 0 tables

**Proposed Solutions:**

**Option A: Deploy Schema Without pgvector (Temporary)**
- Modify schema: `embedding vector(1536)` → `embedding TEXT`
- Skip vector similarity index
- Enables basic database operations
- Can store knowledge atoms (without semantic search)
- Migrate to Railway later when semantic search needed

**Option B: Use Railway ($5/month)**
- pgvector pre-installed and working
- PostgreSQL 16 with pgvector 0.7.x
- Production-ready immediately
- No Windows compilation issues
- 3-minute setup

**Option C: Downgrade to PostgreSQL 13**
- PostgreSQL 13 already installed on same machine
- pgvector binaries available for PG13
- Risk: Port conflict, need to stop PostgreSQL 18
- More complex than other options

**Recommended:** Option A (deploy without pgvector) + Option B later (Railway when needed)

**Status:** OPEN - Awaiting decision on which solution to implement

---

## [2025-12-16 22:45] STATUS: [PARTIALLY RESOLVED] - All Database Providers Failing Connectivity

**Problem:**
All three configured database providers (Neon, Supabase, Railway) failing connectivity tests

**Root Causes:**
1. **Neon:** Brand new project may still be provisioning, or IP restrictions enabled, or `channel_binding=require` incompatible
2. **Supabase:** DNS resolution failing - project likely doesn't exist or was deleted
3. **Railway:** Connection timeout - never properly configured (placeholder credentials in .env)

**Impact:**
- **Severity:** CRITICAL
- Blocks ingestion chain migration deployment
- Blocks KB ingestion testing and growth
- Blocks script quality improvement (stuck at 70/100)
- Blocks RIVET Pro Phase 2 RAG layer development
- User frustrated with Supabase setup complexity

**Error Messages:**
```bash
[FAIL] Neon - connection to server failed: server closed the connection unexpectedly
[FAIL] Supabase - failed to resolve host 'db.mggqgrxwumnnujojndub.supabase.co': [Errno 11001] getaddrinfo failed
[FAIL] Railway - connection timeout expired
```

**Proposed Solutions (User Must Choose):**
1. **Railway Hobby Plan ($5/month)** - Most reliable, 24/7 uptime, no auto-pause, 3-min setup
2. **Local PostgreSQL (FREE)** - 100% reliable offline, ~800 MB storage, 10-min setup
3. **Both Railway + Local** - Best of both worlds (cloud + offline failover)
4. **Wait for Neon** - May need 5-10 minutes to finish provisioning (uncertain)

**User Actions Completed:**
- Provided fresh Neon connection string (still failing)
- Updated `.env` with new NEON_DB_URL
- Tested with and without `channel_binding=require` parameter

**Files Created:**
- `test_all_databases.py` - Automated connectivity testing
- `NEON_QUICK_SETUP.md` - Complete Neon setup guide
- `SUPABASE_MCP_SETUP.md` - MCP + Railway + Local alternatives

**Status:** OPEN - Awaiting user decision on database provider
**Next Step:** User creates Railway project OR installs local PostgreSQL OR waits for Neon

---

## [2025-12-16 22:00] STATUS: [OPEN] - Ingestion Chain Migration Not Deployed

**Problem:**
Ingestion chain SQL migration file exists but not executed in any database

**Root Cause:**
Blocked by database connectivity issue (Issue #1 above)

**Impact:**
- **Severity:** HIGH
- Cannot test ingestion chain workflows
- Script quality improvement blocked
- KB growth limited to manual VPS ingestion

**Missing Tables:**
1. `source_fingerprints` - URL deduplication
2. `ingestion_logs` - Processing history
3. `failed_ingestions` - Error tracking
4. `human_review_queue` - Quality review
5. `atom_relations` - Prerequisite chains

**File Ready:** `docs/database/ingestion_chain_migration.sql`

**Proposed Solution (After Database Working):**
```bash
# Option 1: Deploy to Railway/Local
poetry run python -c "from dotenv import load_dotenv; load_dotenv(); import psycopg; import os; from pathlib import Path; sql = Path('docs/database/ingestion_chain_migration.sql').read_text(); conn = psycopg.connect(os.getenv('RAILWAY_DB_URL')); conn.execute(sql); conn.commit(); print('✅ Migration complete'); conn.close()"

# Option 2: Deploy via Supabase MCP (if user chooses this)
# Claude Code MCP server will execute migration SQL directly
```

**Status:** OPEN - Blocked by database connectivity
**Depends On:** Issue #1 (database connectivity)

---

## [2025-12-16 21:00] STATUS: [FIXED] - Ollama Embeddings Too Slow

**Problem:**
Ollama embeddings taking 20-55 seconds per chunk with 50% timeout rate

**Root Cause:**
1. Worker using wrong endpoint (`/api/generate` instead of `/api/embeddings`)
2. Even with correct endpoint, Ollama too slow for massive scale (20-55s per embedding)

**Impact:**
- **Severity:** Critical (resolved)
- 45 hours per PDF (vs target: <5 minutes)
- Only 4 atoms created after 15 hours of runtime
- Blocked massive-scale ingestion (target: 50K+ atoms)

**Solution Implemented:**
Switched to OpenAI embeddings (text-embedding-3-small)
- Speed: ~1 second per embedding (20-55x faster)
- Reliability: 100% success rate (vs 50% with Ollama)
- Cost: ~$0.04 per PDF (~$20 for 500 PDFs)
- Result: 193 atoms in 3 minutes (first PDF complete)

**Files Modified:**
- `scripts/vps/fast_worker.py` - Added OpenAI integration
- `scripts/vps/requirements_fast.txt` - Added openai==1.59.5
- PostgreSQL schema altered: vector(768) → vector(1536)

**Status:** FIXED - Production deployment successful

---

## [2025-12-16 18:00] STATUS: [FIXED] - PostgreSQL Schema Mismatch

**Problem:**
Worker code expected different schema than actual PostgreSQL table

**Root Cause:**
1. Worker expected `id` column (string) → Schema has `atom_id` (int, auto-increment)
2. Worker tried to insert unused fields (`source_document`, `source_type`)
3. Embedding dimensions mismatch (worker: auto-detect, schema: 768 fixed)

**Impact:**
- **Severity:** High (resolved)
- Worker crashed on first atom save attempt
- Error: "column 'id' does not exist"

**Solution Implemented:**
1. Updated worker to use `atom_id` (auto-increment)
2. Removed unused INSERT fields
3. Updated schema to 1536 dims for OpenAI embeddings
4. Changed deduplication to MD5(content) hash check

**Files Modified:**
- `scripts/vps/fast_worker.py` - Lines 240-375 (atom creation/saving)

**Status:** FIXED - Worker successfully creating atoms

---

## [2025-12-16 17:00] STATUS: [FIXED] - Wrong Ollama API Endpoint

**Problem:**
Old LangGraph worker using `/api/generate` endpoint instead of `/api/embeddings`

**Root Cause:**
Worker code originally designed for LLM-based parsing, not simple embedding generation

**Impact:**
- **Severity:** Critical (resolved)
- 4-5 minutes per chunk vs ~1 second with embeddings endpoint
- 45 hours per PDF vs 15 minutes
- Zero atoms created after 15 hours of runtime

**Evidence:**
```
Ollama logs: POST "/api/generate" | 500 | 5m0s
Worker logs: Processing chunk 156/538
```

**Solution Implemented:**
Created new fast_worker.py using embeddings-only approach
- No LLM parsing (just PDF → chunks → embeddings → save)
- Simple semantic chunking (800 chars, 100 overlap)
- Direct embedding generation

**Status:** FIXED - Replaced with optimized worker

---

## [2025-12-16 14:30] STATUS: [OPEN] - Supabase Connection Not Resolving

**Problem:**
Database pooler endpoint not resolving when connecting to Supabase

**Root Cause:**
Connection string may be outdated or incorrect in `.env`

**Impact:**
- **Severity:** Low (non-critical)
- Multi-provider setup allows using Neon as primary
- Supabase features still accessible via REST API
- No blocking impact on development

**Workaround:**
Using Neon as primary PostgreSQL provider

**Proposed Solution:**
1. Open Supabase dashboard
2. Copy fresh connection string (pooler mode)
3. Update `SUPABASE_DB_URL` in `.env`
4. Test connection

**Status:** Open but non-critical

---

## [2025-12-16 14:30] STATUS: [OPEN] - Database Migration Pending (BLOCKER for KB Ingestion)

**Problem:**
Ingestion chain tables not created in database yet

**Root Cause:**
SQL migration file exists but not executed: `docs/database/ingestion_chain_migration.sql`

**Impact:**
- **Severity:** High (blocks KB ingestion)
- Cannot run ingestion chain workflows
- Script quality improvement blocked (stuck at 70/100, target 75/100)
- KB growth limited to 1,965 atoms

**Required Tables:**
1. `ingestion_jobs`
2. `ingestion_results`
3. `validation_queue`
4. `enrichment_queue`
5. `publish_queue`

**Proposed Solution:**
**USER TASK (5 minutes):**
1. Open Supabase SQL Editor
2. Run `docs/database/ingestion_chain_migration.sql`
3. Verify 5 tables created: `SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%queue%';`
4. Test: `poetry run python -c "from agent_factory.workflows.ingestion_chain import ingest_source; print('OK')"`

**Status:** Open - waiting for user to deploy migration

---

## [2025-12-15 22:00] STATUS: [OPEN] - Context Capacity Exceeded (RESOLVED via Clear)

**Problem:**
Context reached 221k/200k tokens (111% capacity)

**Root Cause:**
Long session with extensive documentation reading

**Impact:**
- **Severity:** Critical (resolved)
- Blocked further work until context cleared
- Required session handoff creation

**Solution Implemented:**
Created comprehensive handoff documents:
- `SESSION_HANDOFF_DEC16.md`
- `README_START_HERE.md`
- `RIVET_PRO_STATUS.md`

**Prevention:**
- More frequent context clears
- Memory system files (these 5 files)
- Concise handoff documents

**Status:** Resolved via context clear

---

**Last Updated:** [2025-12-16 14:30]

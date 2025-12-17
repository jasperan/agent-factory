# Next Actions

Priority-ordered tasks for Agent Factory.

---

## CRITICAL

### ✅ COMPLETED: Autonomous Claude System
**Status:** COMPLETE - Ready for testing
**Completed:** 2025-12-17 08:00

**What Was Built:**
1. ✅ Issue queue builder with hybrid scoring (450 lines)
2. ✅ Safety monitor with cost/time/failure tracking (400 lines)
3. ✅ Autonomous runner orchestrator (400 lines)
4. ✅ Claude executor + PR creator (600 lines combined)
5. ✅ Telegram notifier (300 lines)
6. ✅ GitHub Actions cron workflow
7. ✅ Complete documentation (300+ lines)
8. ✅ All 8 phases complete - 2,500+ lines total

**How to Test:**
```bash
# Step 1: Test components individually
python scripts/autonomous/issue_queue_builder.py
python scripts/autonomous/safety_monitor.py
python scripts/autonomous/telegram_notifier.py

# Step 2: Full dry run
DRY_RUN=true python scripts/autonomous/autonomous_claude_runner.py

# Step 3: Configure GitHub secrets
# Go to repo → Settings → Secrets → Add ANTHROPIC_API_KEY

# Step 4: Test in GitHub Actions
# Actions → Autonomous Claude → Run workflow (dry run = true)
```

**Next Steps:**
- Configure GitHub secrets (ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN)
- Test manually with 1-2 issues
- Enable nightly automation at 2am UTC
- Monitor first few runs

---

## CRITICAL

### ✅ COMPLETED: Telegram Admin Panel
**Status:** COMPLETE - Ready for testing
**Completed:** 2025-12-17 03:30

**What Was Built:**
1. ✅ 7 specialized managers (3,400 lines)
2. ✅ 24 new commands registered
3. ✅ Main dashboard with inline keyboards
4. ✅ Agent monitoring and control
5. ✅ Content approval workflow
6. ✅ GitHub Actions integration
7. ✅ KB management interface
8. ✅ Analytics dashboard
9. ✅ System health checks
10. ✅ Complete documentation

**How to Use:**
1. Start bot: `python telegram_bot.py`
2. In Telegram, send: `/admin`
3. Navigate using inline keyboard buttons
4. Direct commands: `/deploy`, `/kb`, `/health`, `/agents_admin`

**Configuration Needed:**
```env
GITHUB_TOKEN=<your_github_personal_access_token>
```

**Next Steps:**
- Test admin panel in Telegram
- Configure GitHub token
- Create database tables (SQL in TELEGRAM_ADMIN_COMPLETE.md)
- Integrate real data sources (Phase 8+)

### ✅ COMPLETED: Local PostgreSQL Deployment
**Status:** OPERATIONAL - 13 tables deployed
**Completed:** 2025-12-17 00:45

**What Was Done:**
1. ✅ PostgreSQL 18 installed via winget (automatic)
2. ✅ `agent_factory` database created
3. ✅ Schema deployed without pgvector (8 Agent Factory + 5 Ingestion Chain tables)
4. ✅ Ingestion test passed (3 knowledge atoms created from Wikipedia)
5. ✅ Keyword search verified working

**Database Ready:**
- Connection: `LOCAL_DB_URL=postgresql://postgres:Bo1ws2er%4012@localhost:5432/agent_factory`
- 13 tables operational
- Basic CRUD working
- Ingestion chain functional
- Keyword/text search operational

**Current Limitation:**
- Vector embeddings stored as TEXT (no semantic search until Railway/Supabase)

**Next Step:**
- Use Railway when semantic search needed ($5/month, pgvector included)
1. Create account at https://railway.app
2. New Project → Add Service → PostgreSQL
3. Copy connection string
4. Update `.env`: `RAILWAY_DB_URL=<connection_string>`
5. Test: `poetry run python test_all_databases.py`
**Time:** 3 minutes | **Reliability:** 24/7, no auto-pause

**Option B: Local PostgreSQL (FREE)**
1. Download PostgreSQL 16 from https://www.postgresql.org/download/windows/
2. Install with default settings (port 5432)
3. Update `.env`: `LOCAL_DB_URL=postgresql://postgres:your_password@localhost:5432/agent_factory`
4. Create database: `createdb agent_factory`
5. Test: `poetry run python test_all_databases.py`
**Time:** 10 minutes | **Storage:** ~800 MB total | **Reliability:** 100% offline

**Option C: Both Railway + Local (BEST)**
- Cloud database for production (Railway)
- Local database for development (offline reliable)
- Automatic failover between both

**After Database Working:**
- Deploy: `poetry run python scripts/deploy_multi_provider_schema.py`
- Deploy: Ingestion chain migration SQL
- Test: Ingestion chain with Wikipedia PLC article

---

## HIGH

### Monitor VPS KB Ingestion Progress
**Time:** 5 min check-ins
**Status:** Worker processing 34 URLs autonomously
**Commands:**
```bash
ssh root@72.60.175.144
docker logs fast-rivet-worker --tail 20
docker exec infra_postgres_1 psql -U rivet -d rivet -c "SELECT COUNT(*) FROM knowledge_atoms;"
```

### Expand URL Lists to 500+ Sources
**Time:** 2-3 hours
**Priority:** High (unlocks massive-scale ingestion)
**Tasks:**
1. Research manufacturer documentation sites (Allen-Bradley, Siemens, Mitsubishi, Omron, Schneider, ABB, Yaskawa)
2. Find YouTube playlists (PLC tutorials, troubleshooting videos)
3. Identify forums (PLCTalk, Reddit r/PLC, controls.com)
4. Create categorized URL lists (manuals, videos, forums)
5. Test batch URL push to VPS queue

**Expected Output:** 500+ URLs ready for ingestion

### Create Monitoring Dashboard
**Time:** 1 hour
**File:** `scripts/vps/dashboard.py`
**Features:**
- Atom count growth over time
- Processing rate (atoms/hour)
- Queue depth
- Failed URLs
- Cost tracking (OpenAI API usage)
- Estimated completion time

---

## MEDIUM

### Deploy Database Migration (5 min - USER TASK)
**File:** `docs/database/ingestion_chain_migration.sql`
**Action:**
1. Open Supabase SQL Editor
2. Run migration SQL
3. Verify 5 tables created
4. Test: `poetry run python -c "from agent_factory.workflows.ingestion_chain import ingest_source; print('OK')"`
**Impact:** Unlocks KB ingestion chain + script quality improvement

---

## HIGH

### Complete RIVET Pro Phase 2 (RAG Layer) - IN PROGRESS
**Time:** 45 min
**Files to create:**
- `agent_factory/rivet_pro/rag/config.py` (150 lines) - Collection definitions
- `agent_factory/rivet_pro/rag/filters.py` (100 lines) - Intent → Supabase filters
- `agent_factory/rivet_pro/rag/retriever.py` (300 lines) - search_docs(), estimate_coverage()
- `tests/rivet_pro/rag/test_retriever.py` (150 lines)

**Key Functions:**
```python
def search_docs(intent: RivetIntent, agent_id: str, top_k: int = 8) -> List[RetrievedDoc]
def estimate_coverage(intent: RivetIntent) -> KBCoverage  # "strong"|"thin"|"none"
```

### Start RIVET Pro Phase 3 (SME Agents) - PARALLEL READY
**Time:** 2 hours (4 agents in parallel)
**Agents:**
1. Siemens agent (SINAMICS/MICROMASTER)
2. Rockwell agent (ControlLogix/CompactLogix)
3. Generic PLC agent (fallback)
4. Safety agent (SIL/safety relays)

**Each agent ~250 lines**
**Can run in parallel using git worktrees**

---

## MEDIUM

### Fix Supabase Connection (Non-Critical)
**Issue:** Database pooler endpoint not resolving
**Workaround:** Using Neon as primary
**Fix:** Update connection string from Supabase dashboard

### Continue ISH Content Pipeline
**Options:**
1. Batch ingest 50+ sources (KB growth)
2. Enhance video quality (script improvement)

**Status:** Week 2 complete, agents functional

---

## BACKLOG

### RIVET Pro Phase 4: Orchestrator (1.5 hours)
**Depends on:** Phases 1-3 complete
**What:** 4-route routing logic (Strong KB, Thin KB, No KB, Clarification)

### RIVET Pro Phase 5: Research Pipeline (2 hours)
**Can run in parallel:** Yes (depends only on Phase 1)
**What:** Web scraping + KB enrichment for Route C

### RIVET Pro Phase 6: Logging (1 hour)
**Can run in parallel:** Yes (depends only on Phase 1)
**What:** AgentTrace persistence to Supabase

### RIVET Pro Phase 7: API/Webhooks (1.5 hours)
**Depends on:** Phases 1-6 complete
**What:** Telegram/WhatsApp integration endpoints

### RIVET Pro Phase 8: Vision/OCR (2 hours)
**Can run in parallel:** Yes (optional, depends on Phase 4)
**What:** Image nameplates, diagrams, error codes

---

**Last Updated:** [2025-12-16 14:30]

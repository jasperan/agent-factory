# Next Actions

Priority-ordered tasks for Agent Factory.

---

## CRITICAL

### TELEGRAM BOT - TWO-MESSAGE PATTERN DEPLOYMENT (IMMEDIATE)
- [x] Implement two-message pattern (clean user + admin debug) ✓
- [x] Remove route/confidence footer from user messages ✓
- [x] Add _send_admin_debug_message() helper function ✓
- [ ] Push changes to GitHub - NEXT
- [ ] Deploy to VPS: `ssh vps "cd /root/Agent-Factory && git pull origin main && systemctl restart orchestrator-bot"`
- [ ] Test admin debug messages (send query, verify admin chat 8445149012 receives trace)
- [ ] Verify clean user messages (no route/confidence footer)

### CI/CD INFRASTRUCTURE - DECISION REQUIRED (HIGH PRIORITY)
- [x] Audit VPS infrastructure and GitHub Actions workflows ✓
- [x] Document findings in SYSTEM_MANIFEST.md ✓
- [ ] **DECISION NEEDED:** Fix GitHub Actions OR disable automated deploys?
  - Option A: Update deploy-vps.yml to deploy orchestrator_bot.py (not telegram_bot.py)
  - Option B: Delete/disable deploy-vps.yml (continue manual deploys)
- [ ] **DECISION NEEDED:** Delete legacy files?
  - Remove: telegram_bot.py, rivet-pro.service, deploy_rivet_pro.sh
  - All unused, confuse GitHub Actions workflow
- [ ] Check autonomous Claude workflow status: Review GitHub Actions logs for 2am UTC runs
- [ ] Verify all GitHub Actions secrets are configured (VPS_SSH_KEY, VPS_ENV_FILE, etc.)

### TELEGRAM BOT - GROQ FALLBACK TESTING & MONITORING
- [x] Create standalone RivetCEO bot (orchestrator_bot.py) ✓
- [x] Fix Markdown parsing errors (ResponseFormatter escaping) ✓
- [x] Fix search_docs() function signature (RivetIntent creation) ✓
- [x] Fix EquipmentType.GENERIC enum error (changed to UNKNOWN) ✓
- [x] Configure passwordless SSH to VPS ✓
- [x] Deploy to VPS 72.60.175.144 ✓
- [x] Start 24/7 bot service with systemd ✓
- [x] Add Groq LLM fallback for Routes C & D ✓
- [x] Deploy Groq integration to VPS ✓
- [ ] User testing with no-KB-coverage queries (Routes C/D) - NEXT
  - Test: "My hydraulic pump makes grinding noises"
  - Test: "Troubleshoot conveyor belt slipping"
  - Test: "Help?" (unclear intent)
- [ ] Monitor Groq response quality: `ssh vps "journalctl -u orchestrator-bot -f | grep 'LLM response'"`
- [ ] Verify 3-tier fallback chain (Groq → GPT-3.5 → hardcoded)
- [ ] Monitor Groq rate limits (30 req/min, 6K req/day)
- [ ] Document Groq deployment checklist

### WEEK 1 DOCUMENTATION TASKS (5 remaining)
- [ ] Update PROJECT_STRUCTURE.md with "Strategic Priority" column (15 min)
- [ ] Add "Revenue Architecture" section to docs/architecture/00_architecture_platform.md (30 min)
- [ ] Create docs/monetization/ directory with pricing/GTM/revenue docs (45 min)
- [ ] Create scripts/monetization/ directory with revenue calculators (30 min)
- [ ] Create agent_factory/knowledge/ module structure (30 min)

### KNOWLEDGE ATOM COMPLETION
- [ ] Generate embeddings for 52 atoms (task-86.7 acceptance criteria #3) (1 hour)
- [ ] Upload atoms to database (acceptance criteria #4) (30 min)
- [ ] Test semantic search (acceptance criteria #5-6) (30 min)

## HIGH

### EXTERNAL REPO EXTRACTION (Week 2-4 Strategic Plan)
- [ ] Create EPIC: Knowledge Extraction from Anthropic Archon (Week 2)
- [ ] Create EPIC: Knowledge Extraction from LangChain (Week 3)
- [ ] Create EPIC: Knowledge Extraction from LangGraph (Week 3)
- [ ] Create EPIC: Knowledge Extraction from AutoGPT (Week 4)

### SCAFFOLD VALIDATION TASKS
- [ ] task-scaffold-validate-knowledge-base (blog post validation - blocked by knowledge base)
- [ ] task-scaffold-validate-scraper-clips (video extraction)
- [ ] task-scaffold-validate-scraper-metadata (metadata extraction)
- [ ] task-scaffold-validate-youtube-api (YouTube API integration)

## COMPLETED TODAY (2025-12-22)

### SCAFFOLD VALIDATION
- [x] task-scaffold-validate-parser-scale - Parser Scale Validation (2 hours)
  - Status: DONE ✓
  - Results: 140 tasks parsed, 2.137s, 0.34 MB, 5/5 criteria passed
  - Files: scripts/validate_parser_scale.py, scripts/validate_parser_scale_direct.py

### KNOWLEDGE ATOM GENERATION
- [x] task-86.7 - Generate 50-70 Knowledge Atoms (Phase 2.1-2.3 complete) (4 hours)
  - Status: 52/50-70 atoms complete (acceptance criteria #1 ✓)
  - Files: data/atoms-core-repos.json (52 atoms, 100% validated)
  - Next: Generate embeddings (criteria #3)

### DOCUMENTATION
- [x] PRODUCTS.md creation (30 min)
  - Status: COMPLETE ✓
  - Content: 274 lines, revenue strategy, pricing, targets

- [x] CLAUDE.md priority markers (30 min)
  - Status: COMPLETE ✓
  - Changes: SCAFFOLD #1, Infrastructure Foundation, RIVET/PLC deferred

---

## CRITICAL (Previous Work)

### ✅ COMPLETE: User Actions Feature (All 4 Phases)
**Status:** COMPLETE
**Priority:** HIGH (Core feature implemented)
**Completed:** 2025-12-17 19:40

**What Was Built:**

**Phase 1 (commit 3bf6a9b):**
1. ✅ Installed Backlog CLI v1.28.0 via npm
2. ✅ Extended sync script with User Actions section (390 lines)
3. ✅ Added USER_ACTIONS sync zone to TASK.md
4. ✅ Created task-24 EPIC + 4 subtasks
5. ✅ Tested sync script (dry-run + full sync successful)

**Phase 2 (commit 172d695):**
6. ✅ Added "Special Labels → user-action" subsection to backlog/README.md
7. ✅ Updated CLAUDE.md Rule 0 to reference User Actions section
8. ✅ Documented when to use user-action label with examples

**Phase 3 (commit 172d695):**
9. ✅ Created tests/test_user_actions_sync.py with 5 unit tests
10. ✅ All tests passing (pytest + standalone execution)

**Phase 4 (commit 172d695):**
11. ✅ Created scripts/backlog/migrate_user_actions.py
12. ✅ Migration script supports --dry-run and interactive confirmation
13. ✅ Identified 7 candidate tasks for user-action label

**Final Stats:**
- Total: 725 lines added across 7 files
- All 4 subtasks completed (task-24.1 through task-24.4)
- task-24 EPIC marked Done
- Zero schema changes (backward compatible)
- ASCII-only output (Windows compatible)

**All Acceptance Criteria Met:**
- ✅ backlog/README.md documents user-action label
- ✅ CLAUDE.md Rule 0 mentions User Actions section
- ✅ 5 unit tests passing
- ✅ Migration script created and tested
- ✅ All task-24 subtasks marked Done
- ✅ task-24 EPIC marked Done

---

### ✅ COMPLETE: Backlog Setup Implementation - Phase 3 (TASK.md Sync)
**Status:** COMPLETE (needs CLI to test)
**Priority:** HIGH (Core automation)
**Time Estimate:** 2-3 hours

**What to Build:**
1. `scripts/backlog/sync_tasks.py` - Core sync engine (~300 lines)
   - Reads all Backlog tasks (uses Backlog.md MCP tools)
   - Identifies "Current Task" (first task with status "In Progress")
   - Generates "Backlog" section (all "To Do" tasks, prioritized)
   - Preserves TASK.md structure (intro text, manual sections)
   - Updates only sync zones (marked with comments)
   - Supports flags: `--dry-run`, `--force`, `--section=current|backlog`

2. Add sync zone comments to TASK.md:
   ```markdown
   <!-- BACKLOG_SYNC:CURRENT:BEGIN -->
   ## Current Task
   [Auto-generated content]
   <!-- BACKLOG_SYNC:CURRENT:END -->

   <!-- BACKLOG_SYNC:BACKLOG:BEGIN -->
   ## Backlog
   [Auto-generated content]
   <!-- BACKLOG_SYNC:BACKLOG:END -->
   ```

**Acceptance Criteria:**
- [ ] Sync script reads Backlog tasks correctly via MCP
- [ ] TASK.md "Current Task" updated from "In Progress" tasks
- [ ] TASK.md "Backlog" updated from "To Do" tasks (prioritized)
- [ ] Manual sections preserved (intro text, notes)
- [ ] --dry-run flag shows preview without writing
- [ ] Script uses PyYAML for parsing

**Commands:**
```bash
# Dry run
poetry run python scripts/backlog/sync_tasks.py --dry-run

# Full sync
poetry run python scripts/backlog/sync_tasks.py

# Sync only current task section
poetry run python scripts/backlog/sync_tasks.py --section current
```

---

## HIGH

### Phase 6: Integration & Git Hooks
**Status:** PENDING (depends on Phase 3)
**Priority:** HIGH
**Time Estimate:** 1 hour

**What to Build:**
1. `scripts/backlog/install_git_hooks.py` - Git hook installer
2. Update memory system integration (link Backlog tasks to PROJECT_CONTEXT.md)
3. Add CLI usage examples to backlog/README.md

---

## MEDIUM

### Phase 2: Task Templates
**Status:** PENDING (optional, can skip for now)
**Priority:** MEDIUM
**Time Estimate:** 1 hour

**What to Build:**
1. 5 task templates in `backlog/templates/` (BUILD, FIX, TEST, CLEANUP, AUDIT)
2. `scripts/backlog/create_task_from_template.py` - Interactive CLI wizard

---

## CRITICAL

### ✅ COMPLETED: Backlog Setup Implementation - Phase 1
**Status:** COMPLETE
**Completed:** 2025-12-17 20:30

**What Was Built:**
1. ✅ `backlog/README.md` - Complete workflow guide (600+ lines)
2. ✅ `backlog/decisions/TEMPLATE.md` - Decision documentation template
3. ✅ `CLAUDE.md` Rule 0 updated - Backlog.md integration

**Documentation Delivered:**
- When to use Backlog.md vs TASK.md
- Task lifecycle (To Do → In Progress → Done → Archived)
- YAML frontmatter reference
- Task creation methods (MCP, CLI, manual)
- Parent-child relationships
- Labels, priorities, dependencies
- MCP tool usage examples
- Best practices and FAQ

**Next Phase:** Phase 3 - TASK.md Sync (core automation)

---

## CRITICAL

### ✅ COMPLETED: RIVET Pro Phase 3 - SME Agents
**Status:** COMPLETE
**Completed:** 2025-12-17 17:45

**What Was Built:**
1. ✅ BaseSMEAgent abstract class (240 lines) - Shared RAG integration
2. ✅ GenericPLCAgent (120 lines) - IEC 61131-3 fallback
3. ✅ SiemensAgent (165 lines) - SIMATIC PLCs, SINAMICS drives, TIA Portal
4. ✅ RockwellAgent (165 lines) - ControlLogix/CompactLogix, PowerFlex, Studio 5000
5. ✅ SafetyAgent (190 lines) - IEC 61508/61511, SIL ratings, E-stop circuits
6. ✅ AgentRouter (157 lines) - Priority-based routing (Safety → Vendor → Generic)
7. ✅ ResponseFormatter (175 lines) - Citations, safety warnings, action lists
8. ✅ Package exports and documentation

**Total:** 1,325 lines across 8 files

**Git Workflow:**
- Created worktree: `../agent-factory-rivet-phase3` on branch `rivet-pro/phase3-sme-agents`
- Committed with detailed message
- Created PR #61: https://github.com/Mikecranesync/Agent-Factory/pull/61
- Cleaned up worktree and branch

**Backlog Tasks Completed:**
- task-3.1: Siemens Agent (DONE)
- task-3.2: Rockwell Agent (DONE)
- task-3.3: Generic PLC Agent (DONE)
- task-3.4: Safety Agent (DONE)
- task-3.5: RAG Integration (DONE)
- task-3.6: Testing & Validation (DONE)
- task-3: EPIC - RIVET Pro Phase 3 (DONE)

**Next Phase:** Phase 4 - Orchestrator (1.5 hours)

---

## CRITICAL

### ✅ COMPLETED: Backlog Task Creation from STATUS.md Audit
**Status:** COMPLETE
**Completed:** 2025-12-17 15:30

**What Was Done:**
1. ✅ Comprehensive repository audit (STATUS.md - 500+ lines)
2. ✅ Detailed implementation plan created
3. ✅ 21 Backlog tasks created with acceptance criteria
4. ✅ All tasks organized by type (BUILD/FIX/CLEANUP/TEST)
5. ✅ Priority assignments completed
6. ✅ Source line references added

**Tasks Created:**
- BUILD: 11 tasks (RIVET Pro Phases 3-8, PLC Tutor, YouTube automation)
- FIX: 3 tasks (pgvector, Telegram admin data, pytest)
- CLEANUP: 2 tasks (documentation updates)
- TEST: 5 tasks (comprehensive test coverage)

**Total Estimated Effort:** 70-90 hours

**All Tasks Available:**
- View in `backlog/tasks/` directory
- Use `backlog task list` to see all tasks
- Use `backlog task view <id>` for details

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

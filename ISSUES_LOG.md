# Issues Log

Known issues, bugs, and blockers.

---

## [2025-12-23 22:00] STATUS: [RESOLVED] - Route C always shows 54% confidence

**Problem:**
All Route C queries showed exactly 54% confidence regardless of content.

**Root Cause:**
- Missing GROQ_API_KEY in VPS .env file
- LLMRouter attempted Groq → failed with 401 Unauthorized
- Fell back to OpenAI GPT-3.5-turbo
- Confidence calculation: 0.6 (OpenAI base) × 0.9 (fallback penalty) = 0.54

**Impact:**
- **Severity:** LOW (functional but misleading)
- Route C still worked (OpenAI fallback successful)
- User responses correct, but confidence misleading
- Higher LLM costs (~$0.002/query vs free Groq)
- Logs showed 401 errors from Groq API

**Fix Applied:**
1. Found GROQ_API_KEY in local .env: `gsk_***` (redacted)
2. Added to VPS .env: `echo 'GROQ_API_KEY=...' >> /root/Agent-Factory/.env`
3. Restarted bot service: `systemctl restart orchestrator-bot.service`
4. Verified initialization successful

**Verification:**
- Test query: "AS-i troubleshooting"
- Route: C (no KB coverage) ✅
- Confidence: 50% (Groq base, no fallback penalty) ✅
- Groq logs: No 401 errors ✅
- Response quality: Good ✅

**Status:** RESOLVED (2025-12-23 22:00)

---

## [2025-12-23 22:00] STATUS: [RESOLVED] - Decimal type error in kb_evaluator.py

**Problem:**
TypeError when calculating KB coverage confidence: `unsupported operand type(s) for *: 'decimal.Decimal' and 'float'`

**Trigger:**
Query: "How to troubleshoot the Siemens PLC"

**Root Cause:**
- PostgreSQL returns NUMERIC columns as Python `Decimal` objects
- Line 81: `relevance_scores = [doc.similarity for doc in docs]` returned list of Decimals
- Line 82: Sum/division kept Decimal type for avg_relevance
- Line 154: `avg_relevance * 0.3` attempted Decimal × float → TypeError
- Python Decimal doesn't support mixed-type arithmetic

**Impact:**
- **Severity:** CRITICAL (crashes all KB coverage evaluations)
- All queries with KB search crashed (Routes A, B, C with any atoms)
- Bot returned ERROR response to user
- Confidence calculation impossible
- Affected ALL vendor queries that found atoms

**Fix Applied:**
Line 81 changed to:
```python
relevance_scores = [float(doc.similarity) for doc in docs]
```

**Deployment:**
- Committed: cee50ff "fix: Convert Decimal similarity to float in kb_evaluator"
- Pushed to GitHub
- Pulled on VPS: `git pull`
- Discovered ORCHESTRATOR_BOT_TOKEN and GROQ_API_KEY also missing
- Re-added both tokens to VPS .env
- Restarted service successfully

**Verification:**
- Test query: "How to troubleshoot the Siemens PLC"
- No TypeError ✅
- Confidence calculated correctly ✅
- Route selected appropriately ✅

**Status:** RESOLVED (2025-12-23 22:00)

---

## [2025-12-23 22:00] STATUS: [KNOWN ISSUE] - Limited VFD KB coverage (4 atoms, config-only)

**Problem:**
Query "Diagnose VFD overheating" hits Route C (no KB coverage) instead of Route A/B.

**Root Cause:**
- Database has 1,964 total atoms
- Only 4 VFD-related atoms found
- All 4 atoms about VFD configuration/setup (parameter settings, commissioning)
- None about troubleshooting, faults, or diagnostics
- Similarity scores for those 4 atoms all <0.55 (below threshold)

**Impact:**
- **Severity:** MEDIUM (expected behavior, not a bug)
- VFD troubleshooting queries hit Route C (Groq LLM fallback)
- Responses still helpful (Groq generates good generic advice)
- Missing opportunity to use KB-backed SME agents
- Users don't get manufacturer-specific troubleshooting steps

**Analysis:**
- This is EXPECTED behavior, not a bug
- KB genuinely lacks VFD troubleshooting content
- Route C fallback working correctly
- Similarity threshold (0.55) appropriate - atoms were about config, not troubleshooting

**Fix Required:**
- Ingest VFD troubleshooting manuals (Siemens, Rockwell, ABB)
- Target content: fault codes, overheating causes, diagnostic procedures
- Estimated: 50-100 new atoms needed for VFD troubleshooting coverage

**Workaround:**
Route C Groq fallback provides reasonable generic answers until KB coverage improves.

**Status:** KNOWN ISSUE - KB enrichment task

---

## [2025-12-23 22:00] STATUS: [PENDING] - Phase 3 SME agents untested for Route A/B

**Problem:**
Phase 3 agents deployed but never validated working because all test queries hit Route C (no KB coverage).

**Root Cause:**
- Test queries: "Diagnose VFD overheating", "AS-i troubleshooting", etc.
- All hit Route C due to no KB coverage or low similarity
- Route A/B require KB atoms with similarity ≥0.55
- Haven't sent query with strong KB coverage yet

**Impact:**
- **Severity:** MEDIUM (deployment risk)
- Unknown if real agents generate responses correctly
- Unknown if [MOCK] prefix removed
- Unknown if KB citations working
- Unknown if vendor-specific agents selected properly

**Validation Needed:**
1. Send query with KB coverage: "What is a PLC?" or "Explain Siemens S7-1200"
2. Verify Route A or B selected (not C)
3. Verify response contains NO [MOCK] prefix
4. Verify response includes real technical content
5. Verify KB citations present ([Source 1], [Source 2], etc.)
6. Verify confidence 0.80-0.95 (Route A) or 0.70-0.85 (Route B)

**Expected Behavior:**
- Route A/B triggered
- GenericAgent or vendor-specific agent selected
- LLM generates response using KB atoms as context
- Citations to KB sources included
- Professional technical content with proper terminology

**Status:** PENDING - awaiting test query with KB coverage

---

## [2025-12-23 00:20] STATUS: [FIXED] - Photo handler crashes with "column vendor does not exist"

**Problem:**
Photo OCR worked (extracted manufacturer/model/fault), but KB search crashed with SQL error: "column vendor does not exist".

**Root Cause:**
- `agent_factory/rivet_pro/rag/retriever.py` lines 166-167
- SELECT statement used `vendor` and `equipment_type` columns
- Database schema has `manufacturer` (not `vendor`) and no `equipment_type` column
- Schema evolved over time, code didn't update
- Silent failure: no admin notification, generic error to user

**Impact:**
- **Severity:** HIGH (photo handler completely broken)
- All photo messages failed after OCR extraction
- User saw: "Error processing photo: column vendor does not exist"
- No visibility into production failures (no tracing)
- KB gap logging also affected (depends on retriever)

**Fix Applied:**
1. Updated SELECT: `vendor` → `manufacturer` (line 166)
2. Removed `equipment_type` from SELECT (line 167)
3. Updated tuple unpacking to match new column count (line 193)
4. Hardcoded `equipment_type="unknown"` in RetrievedDoc construction (line 194)

**Prevention Measures:**
1. Created `scripts/validate_schema.py` - runs before deploy, exits 1 on mismatch
2. Added RequestTrace class - logs all requests to JSONL + admin messages
3. Updated SYSTEM_MANIFEST.md - pre-deployment validation checklist
4. Production tracing - all failures now send admin notification (chat ID 8445149012)

**Deployment:**
- Deployed to VPS: 2025-12-23 00:19 UTC
- Service restarted successfully
- Trace logs initialized: `/root/Agent-Factory/logs/traces.jsonl`
- No errors in journalctl logs

**Status:** FIXED - deployed to production

---

## [2025-12-23 14:45] STATUS: [FIXED] - Schema mismatch: page_number vs source_pages

**Problem:**
Schema validation script found mismatch: retriever.py uses `page_number`, database has `source_pages`.

**Root Cause:**
- Same as photo handler bug: schema drift over time
- retriever.py wasn't using `source_pages` column (TEXT[] array)
- Database schema: `source_pages TEXT[]` column exists
- RetrievedDoc.page_number always None
- Affects source citation accuracy

**Impact:**
- **Severity:** MEDIUM (query worked, but column unused)
- page_number returned NULL for all rows
- RetrievedDoc.page_number always None
- No visible errors (SQL query didn't fail)
- Citations lacked page numbers

**Fix Applied:**
1. Added `source_pages` to SELECT query (line 168)
2. Extract first page number from array: `source_pages[0] if source_pages and len(source_pages) > 0 else None`
3. Updated tuple unpacking to use correct row indices (lines 186-204)
4. Schema validation passes: `poetry run python scripts/validate_schema.py`

**Commit:** a021a2f - "fix: Use source_pages column for citation accuracy in retriever"

**Status:** FIXED - Citations now include page numbers when available

---

## [2025-12-22 19:30] STATUS: [OPEN] - GitHub Actions deploy workflow deploys outdated bot

**Problem:**
GitHub Actions workflow `.github/workflows/deploy-vps.yml` is failing because it deploys the OLD bot setup (telegram_bot.py) instead of the current production bot (orchestrator_bot.py).

**Root Cause:**
- Workflow references outdated files:
  - Bot: `telegram_bot.py` (old, exists but unused)
  - Service: `rivet-pro.service` (old service file, not active)
  - Script: `deploy_rivet_pro.sh` (old deployment script)
- Production actually uses:
  - Bot: `agent_factory/integrations/telegram/orchestrator_bot.py`
  - Service: `/etc/systemd/system/orchestrator-bot.service` (active)
  - Deployment: Manual git pull + systemctl restart
- Verification steps fail:
  - Workflow checks for `telegram_bot.py` process (doesn't run)
  - Workflow verifies `rivet-pro.service` status (not enabled/active)

**Impact:**
- **Severity:** MEDIUM (production not affected, but CI/CD broken)
- GitHub Actions deployments fail on every push to main
- Manual deployments work fine (bot is stable)
- No impact on production bot (@RivetCeo_bot runs independently via systemd)
- Confusing failure notifications sent to admin

**Evidence:**
- VPS investigation (2025-12-22): Only `orchestrator-bot.service` is active
- Recent commits (last 5): All focus on `orchestrator_bot.py` improvements
- Service status: `orchestrator-bot.service` loaded/active/running
- Legacy files exist but are unused (telegram_bot.py, rivet-pro.service)

**Options:**

Option A: Update GitHub Actions workflow
- Edit `.github/workflows/deploy-vps.yml`
- Change bot verification: `telegram_bot.py` → `orchestrator_bot.py`
- Change service check: `rivet-pro.service` → `orchestrator-bot.service`
- Update or remove reference to `deploy_rivet_pro.sh`
- Pros: Automated deploys work again
- Cons: Requires workflow YAML edits, testing

Option B: Disable automated deploys (simpler)
- Delete or disable `.github/workflows/deploy-vps.yml`
- Continue using manual `git pull + systemctl restart`
- Add comment: "Manual deployment only - GitHub Actions disabled"
- Pros: Simple, manual deployment already works
- Cons: No automation, no deployment notifications

Option C: Clean up legacy files first, then update workflow
- Delete: `telegram_bot.py`, `rivet-pro.service`, `deploy_rivet_pro.sh`
- Update workflow to reference only new files
- Pros: Clean repo, no confusion
- Cons: Requires coordination (delete + workflow update)

**Workaround:**
Continue using manual deployment (current approach):
```bash
git push origin main
ssh vps "cd /root/Agent-Factory && git pull origin main && systemctl restart orchestrator-bot"
```

**Related Files:**
- `.github/workflows/deploy-vps.yml` (outdated workflow)
- `telegram_bot.py` (legacy bot, unused)
- `rivet-pro.service` (legacy service file, unused)
- `deploy_rivet_pro.sh` (legacy deploy script)
- `agent_factory/integrations/telegram/orchestrator_bot.py` (current bot)
- `/etc/systemd/system/orchestrator-bot.service` (current service)

**Documentation:**
See `SYSTEM_MANIFEST.md` for complete CI/CD infrastructure audit

**Status:** OPEN - decision needed on Option A, B, or C

---

## [2025-12-22 17:45] STATUS: [OPEN] - ORCHESTRATOR_BOT_TOKEN persistence issue on VPS

**Problem:**
ORCHESTRATOR_BOT_TOKEN environment variable not persisting in VPS .env file after git pull operations.

**Root Cause:**
- .env file is .gitignored (correctly for security)
- git pull doesn't overwrite .env
- However, ORCHESTRATOR_BOT_TOKEN line sometimes missing after deployments
- Possible cause: Multiple echo commands creating duplicates or line position issues

**Impact:**
- **Severity:** LOW (workaround available)
- Bot fails to start until token manually re-added
- Requires manual SSH to fix: `echo 'ORCHESTRATOR_BOT_TOKEN=...' >> .env`
- Delays deployment by 1-2 minutes

**Workaround:**
```bash
# Always verify token exists after git pull
ssh vps "cd /root/Agent-Factory && grep -q ORCHESTRATOR_BOT_TOKEN .env || echo 'ORCHESTRATOR_BOT_TOKEN=7910254197:AAGeEqMI_rvJExOsZVrTLc_0fb26CQKqlHQ' >> .env"
```

**Proposed Solution:**
- Create deployment script that checks/adds required .env variables
- Or: Use systemd EnvironmentFile directive to load from separate config
- Or: Add pre-deployment validation to check for required env vars

**Status:** OPEN - workaround documented, not critical

---

## [2025-12-22 13:30] STATUS: [FIXED] - EquipmentType.GENERIC enum attribute error

**Problem:**
Bot crashing with error: "type object 'EquipmentType' has no attribute 'GENERIC'"

**Root Cause:**
- kb_evaluator.py line 50 used `EquipmentType.GENERIC`
- EquipmentType enum only has: VFD, PLC, HMI, SENSOR, CONTACTOR, BREAKER, MCC, SAFETY_RELAY, SERVO, MOTOR, ENCODER, UNKNOWN
- GENERIC attribute doesn't exist, should use UNKNOWN as fallback

**Impact:**
- **Severity:** HIGH (fixed)
- Bot unable to process any queries
- All requests failed at knowledge base evaluation stage

**Solution Implemented:**
Changed line 50 in agent_factory/routers/kb_evaluator.py:
```python
# Before:
equipment_type=EquipmentType.GENERIC,

# After:
equipment_type=EquipmentType.UNKNOWN,
```

**Commit:** c1a0927
**Status:** FIXED - Bot now processes queries without enum errors

---

## [2025-12-22 13:30] STATUS: [FIXED] - search_docs() unexpected keyword argument

**Problem:**
Bot returning error: "search_docs() got an unexpected keyword argument 'query'"

**Root Cause:**
- kb_evaluator.py calling search_docs() with wrong parameters
- Was calling: `search_docs(query="text", vendor="...", top_k=10)`
- Expected signature: `search_docs(intent: RivetIntent, config: RAGConfig, db: DatabaseManager)`
- Function signature mismatch from Phase 2 RAG implementation

**Impact:**
- **Severity:** CRITICAL (fixed)
- Bot unable to query knowledge base
- All queries failed after RAG layer initialization
- Users received error messages instead of answers

**Solution Implemented:**
1. Import RivetIntent, EquipmentType, RAGConfig
2. Create RivetIntent object from request:
   ```python
   intent = RivetIntent(
       vendor=vendor,
       equipment_type=EquipmentType.UNKNOWN,
       symptom=request.text or "",
       raw_summary=request.text or "",
       context_source="text_only",
       confidence=0.8
   )
   ```
3. Pass correct parameters to search_docs():
   ```python
   config = RAGConfig(top_k=10)
   docs = search_docs(intent=intent, config=config, db=self.rag)
   ```
4. Extract similarity scores from RetrievedDoc objects

**Files Modified:**
- agent_factory/routers/kb_evaluator.py (lines 13, 44-64)

**Commit:** 39f78a4
**Status:** FIXED - Knowledge base queries working correctly

---

## [2025-12-22 13:30] STATUS: [FIXED] - Telegram bot returning "no information" for all queries

**Problem:**
Bot always responding with "Our knowledge base doesn't have enough information... check back in 24-48 hours" for every query. Route C with 0% confidence.

**Root Cause:**
- Orchestrator initialized without RAG layer: `RivetOrchestrator()`
- KB evaluator checking `if self.rag is None` → using mock evaluator
- Mock evaluator uses query length heuristics, returns CoverageLevel.NONE
- Router sees NONE coverage → defaults to Route C (research pipeline)

**Impact:**
- **Severity:** CRITICAL (fixed)
- Bot unable to answer any questions from knowledge base
- 1,964 knowledge atoms in database unused
- Poor user experience (bot appears broken)

**Solution Implemented:**
Initialize orchestrator with DatabaseManager in post_init():
```python
from agent_factory.core.database_manager import DatabaseManager
db = DatabaseManager()

# Verify database has atoms
result = db.execute_query("SELECT COUNT(*) FROM knowledge_atoms")
atom_count = result[0][0] if result else 0
logger.info(f"Database initialized with {atom_count} knowledge atoms")

# Pass RAG layer to orchestrator
orchestrator = RivetOrchestrator(rag_layer=db)
logger.info("Orchestrator initialized successfully with RAG layer")
```

**Files Modified:**
- agent_factory/integrations/telegram/orchestrator_bot.py (lines 138-153)

**Commit:** 63385b3
**Status:** FIXED - Bot now queries knowledge base with 1,964 atoms

---

## [2025-12-22 13:30] STATUS: [FIXED] - Telegram Markdown parse entity errors

**Problem:**
Bot responses causing error: "Can't parse entities: can't find end of the entity starting at byte offset 492"

**Root Cause:**
- Orchestrator responses contain special characters (`_`, `|`, `%`, etc.)
- Telegram Markdown requires escaping these characters
- Line 105: `f"\n\n_Route: {route} | Confidence: {conf:.0%}_"` has unescaped special chars
- ResponseFormatter utility exists but wasn't imported/used

**Impact:**
- **Severity:** HIGH (fixed)
- Users receive error messages instead of bot responses
- All formatted responses failed to send
- Plain text fallback existed but proper solution needed

**Solution Implemented:**
1. Import ResponseFormatter: `from agent_factory.integrations.telegram.formatters import ResponseFormatter`
2. Escape response before sending: `escaped_response = ResponseFormatter.escape_markdown(response)`
3. Send escaped response: `await update.message.reply_text(escaped_response, parse_mode="Markdown")`

**Files Modified:**
- agent_factory/integrations/telegram/orchestrator_bot.py (lines 27, 109)

**Commit:** 63385b3
**Status:** FIXED - All Markdown properly escaped, no parse errors

---

## [2025-12-22 07:10] STATUS: [FIXED] - Multiple Telegram bot instances causing conflicts

**Problem:**
Multiple bot processes running simultaneously causing Telegram API "Conflict: terminated by other getUpdates request" error.

**Root Cause:**
- Previous bot instances not properly killed when restarting
- Multiple Python processes polling same bot token
- Telegram API rejects concurrent getUpdates requests

**Impact:**
- **Severity:** HIGH (fixed)
- Bot unable to poll for messages
- 409 Conflict errors every 5-10 seconds
- Bot appeared offline to users

**Error Message:**
```
telegram.error.Conflict: Conflict: terminated by other getUpdates request;
make sure that only one bot instance is running
```

**Solution Implemented:**
1. Killed all Python processes: `taskkill //F //IM python.exe`
2. Waited 10 seconds for Telegram to clear webhook state
3. Started single clean bot instance
4. Verified 200 OK responses on polling

**Files Modified:**
- None (process management fix)

**Status:** FIXED - Bot now running cleanly without conflicts

---

## [2025-12-22 07:10] STATUS: [FIXED] - Telegram Markdown parsing errors

**Problem:**
Bot responses causing Markdown parsing errors in Telegram: "Can't parse entities: can't find end of the entity starting at byte offset 492"

**Root Cause:**
- RivetOrchestrator responses contain characters that conflict with Telegram's Markdown parser
- Telegram Markdown v2 has strict entity parsing requirements
- Certain special characters or formatting cause parser to fail

**Impact:**
- **Severity:** HIGH (fixed)
- Users received error messages instead of bot responses
- All queries resulted in parse failures
- Bot appeared broken

**Solution Implemented:**
Added BadRequest exception handling with plain text fallback:
```python
try:
    await update.message.reply_text(response, parse_mode="Markdown")
except BadRequest as parse_error:
    logger.warning(f"Markdown parse error, sending as plain text: {parse_error}")
    await update.message.reply_text(response)  # No parse_mode = plain text
```

**Files Modified:**
- agent_factory/integrations/telegram/orchestrator_bot.py (lines 108-121)

**Status:** FIXED - Bot now falls back to plain text when Markdown fails

---

## [2025-12-22 04:40] STATUS: INFO - MCP tools unavailable in standalone Python scripts

**Issue**: BacklogParser relies on MCP tools which aren't available when running standalone Python scripts (only work inside Claude Code CLI sessions).

**Impact**: Cannot use BacklogParser for validation scripts run via `poetry run python`.

**Solution Implemented**: Created direct file-reading validation script (validate_parser_scale_direct.py) that parses YAML frontmatter from backlog/tasks/*.md files directly.

**Result**: Validation successful - 140 tasks parsed in 2.137s without MCP dependency.

**Learning**: For standalone scripts, bypass MCP and read files directly from filesystem.

---

## [2025-12-22 04:40] STATUS: FIXED - Unicode emoji encoding in Windows console

**Issue**: Windows console (cp1252 encoding) cannot display Unicode emojis (✅, ❌, ⚠️, 🎉) used in Python script output.

**Error**: `UnicodeEncodeError: 'charmap' codec can't encode character '\u2705'`

**Solution**: Replaced all Unicode emojis with ASCII equivalents ([OK], [FAIL], [WARN], [SUCCESS]).

**Files Fixed**: scripts/validate_parser_scale.py, scripts/validate_parser_scale_direct.py

**Result**: Scripts run successfully on Windows with readable ASCII output.

---

## [2025-12-22 04:40] STATUS: INFO - Blog post validation blocked by empty knowledge base

**Issue**: task-scaffold-validate-knowledge-base shows only 851 words/post average (need 2000+).

**Root Cause**: Knowledge base not yet populated with sufficient atoms (only 52 CORE atoms currently).

**Blocker**: Blog post generation needs rich knowledge base for 2000+ word content.

**Solution Path**:
1. Generate embeddings for 52 atoms
2. Upload to database
3. OR extract more atoms from external repos (Archon, LangChain) for richer content
4. Re-run blog post generation with populated knowledge base

**Status**: Deferred until knowledge base has 100+ atoms with diverse content.

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

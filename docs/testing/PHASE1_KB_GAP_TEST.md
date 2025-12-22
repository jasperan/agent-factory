# Phase 1: KB Gap Logging - Test Guide

## Status
✅ **Deployed to VPS** (2025-12-22 23:16 UTC)
✅ **Database table created** (kb_gaps count: 0)
⏳ **Ready for testing**

---

## Test Objective
Verify that when the bot receives a query with **no KB matches** (Route C), it:
1. Logs the query to the `kb_gaps` table
2. Increments frequency for duplicate queries within 7 days
3. Captures intent metadata (vendor, equipment, symptom)

---

## Test 1: First Query (New Gap)

### Step 1: Send Test Query to Bot
Open Telegram and send this message to **@RivetCeo_bot**:

```
Siemens G120 F0003 fault
```

**Expected Bot Response:**
- Should show "🤖 AI Generated (no KB match)" label
- Should provide Groq-generated answer about the fault
- Trace should show: `Route: ROUTE_C, KB Atoms: 0`

### Step 2: Verify Gap Logged in Database

Run this command from your Windows terminal:

```powershell
ssh vps "cd /root/Agent-Factory && /root/.local/bin/poetry run python -c \"
from agent_factory.core.database_manager import DatabaseManager
db = DatabaseManager()
result = db.execute_query('SELECT id, query, intent_vendor, intent_equipment, frequency, triggered_at FROM kb_gaps ORDER BY id DESC LIMIT 1')
if result:
    row = result[0]
    print(f'✅ Gap logged successfully!')
    print(f'   ID: {row[0]}')
    print(f'   Query: {row[1]}')
    print(f'   Vendor: {row[2]}')
    print(f'   Equipment: {row[3]}')
    print(f'   Frequency: {row[4]}')
    print(f'   Triggered: {row[5]}')
else:
    print('❌ No gaps logged')
\""
```

**Expected Output:**
```
✅ Gap logged successfully!
   ID: 1
   Query: Siemens G120 F0003 fault
   Vendor: siemens
   Equipment: vfd
   Frequency: 1
   Triggered: 2025-12-22 23:XX:XX
```

---

## Test 2: Duplicate Query (Frequency Increment)

### Step 1: Send Same Query Again
Send the **exact same message** to @RivetCeo_bot again:

```
Siemens G120 F0003 fault
```

### Step 2: Verify Frequency Incremented

Run the same database query as Test 1.

**Expected Output:**
```
✅ Gap logged successfully!
   ID: 1  ← Same ID (not a new record)
   Query: Siemens G120 F0003 fault
   Vendor: siemens
   Equipment: vfd
   Frequency: 2  ← Incremented from 1 to 2
   Triggered: 2025-12-22 23:XX:XX  ← Original trigger time
```

**Key Check:** The `id` should be the same (not a new record), and `frequency` should increment from 1 to 2.

---

## Test 3: Different Query (New Gap)

### Step 1: Send Different Query
Send a **different** query that will also trigger Route C:

```
Allen-Bradley CompactLogix E0412 error
```

### Step 2: Verify Second Gap Logged

Run this command to see **all gaps**:

```powershell
ssh vps "cd /root/Agent-Factory && /root/.local/bin/poetry run python -c \"
from agent_factory.core.database_manager import DatabaseManager
db = DatabaseManager()
result = db.execute_query('SELECT id, query, intent_vendor, frequency FROM kb_gaps ORDER BY id')
for row in result:
    print(f'ID: {row[0]}, Query: {row[1]}, Vendor: {row[2]}, Freq: {row[3]}')
\""
```

**Expected Output:**
```
ID: 1, Query: Siemens G120 F0003 fault, Vendor: siemens, Freq: 2
ID: 2, Query: Allen-Bradley CompactLogix E0412 error, Vendor: allen_bradley, Freq: 1
```

---

## Test 4: Gap Statistics

### Check Overall Stats

Run this command to see gap statistics:

```powershell
ssh vps "cd /root/Agent-Factory && /root/.local/bin/poetry run python -c \"
from agent_factory.core.database_manager import DatabaseManager
from agent_factory.core.kb_gap_logger import KBGapLogger
db = DatabaseManager()
logger = KBGapLogger(db)
stats = logger.get_gap_stats()
print(f'📊 KB Gap Statistics:')
print(f'   Total gaps: {stats[\"total_gaps\"]}')
print(f'   Resolved: {stats[\"resolved_count\"]}')
print(f'   Unresolved: {stats[\"unresolved_count\"]}')
print(f'   Resolution rate: {stats[\"resolution_rate\"]:.1f}%')
print(f'   Avg frequency: {stats[\"avg_frequency\"]:.1f}')
\""
```

**Expected Output (after Tests 1-3):**
```
📊 KB Gap Statistics:
   Total gaps: 2
   Resolved: 0
   Unresolved: 2
   Resolution rate: 0.0%
   Avg frequency: 1.5  ← (2 + 1) / 2
```

---

## Test 5: Top Gaps

### Get Most Frequent Unresolved Gaps

```powershell
ssh vps "cd /root/Agent-Factory && /root/.local/bin/poetry run python -c \"
from agent_factory.core.database_manager import DatabaseManager
from agent_factory.core.kb_gap_logger import KBGapLogger
db = DatabaseManager()
logger = KBGapLogger(db)
gaps = logger.get_top_gaps(limit=10)
print(f'🔝 Top Unresolved Gaps:')
for gap in gaps:
    print(f'   [{gap[\"frequency\"]}x] {gap[\"query\"][:50]} (ID: {gap[\"id\"]})')
\""
```

**Expected Output:**
```
🔝 Top Unresolved Gaps:
   [2x] Siemens G120 F0003 fault (ID: 1)
   [1x] Allen-Bradley CompactLogix E0412 error (ID: 2)
```

---

## Success Criteria

Phase 1 passes if:
- ✅ New queries create new kb_gaps records
- ✅ Duplicate queries (within 7 days) increment `frequency` instead of creating duplicates
- ✅ Intent metadata captured correctly (vendor, equipment, symptom)
- ✅ Timestamp fields populated (`triggered_at`, `last_asked_at`)
- ✅ Statistics methods return correct aggregates
- ✅ Top gaps sorted by frequency (descending)

---

## Next Steps After Testing

Once Phase 1 tests pass:

1. **Mark Phase 1 complete** in NEXT_ACTIONS.md
2. **Begin Phase 2**: Auto-trigger research pipeline
   - Update `orchestrator.py` to call `ResearchPipeline.run()` from Route C
   - Update `research_pipeline.py` to accept `gap_id` parameter
   - Update `ingestion_chain.py` to mark gaps resolved after atoms created

**Estimated Time for Phase 2**: 2-3 hours

---

## Troubleshooting

### No gaps logged after sending query

**Check bot logs:**
```bash
ssh vps "journalctl -u orchestrator-bot -n 50 --no-pager | grep -i 'kb gap'"
```

**Look for:**
- `INFO:agent_factory.core.orchestrator:KB gap logger initialized`
- `INFO:agent_factory.core.orchestrator:Logged KB gap: gap_id=X, query='...'`

**If missing:** KB gap logger may not be initializing correctly.

### Frequency not incrementing

**Check 7-day window:**
- Gap deduplication only works within 7 days
- If previous query > 7 days old, a new record will be created

**Check query exact match:**
- Queries must match **exactly** (case-sensitive)
- `"Siemens G120 F0003 fault"` ≠ `"siemens g120 f0003 fault"`

### Database connection errors

**Check database health:**
```bash
ssh vps "cd /root/Agent-Factory && /root/.local/bin/poetry run python -c \"
from agent_factory.core.database_manager import DatabaseManager
db = DatabaseManager()
print(db.health_check_all())
\""
```

**Expected:** At least one provider (neon or supabase) should be healthy.

---

## VPS Access

**SSH:** `ssh vps` (aliased in ~/.ssh/config)
**Bot Service:** `systemctl status orchestrator-bot`
**Bot Logs:** `journalctl -u orchestrator-bot -f`
**Database:** Neon PostgreSQL (primary), Supabase (failover)

---

## Files Involved

- `agent_factory/core/kb_gap_logger.py` - KBGapLogger class (200 lines)
- `agent_factory/core/orchestrator.py` - Integration (lines 63-70, 324-338)
- `docs/database/migrations/001_kb_gaps_table.sql` - Schema
- `C:\Users\hharp\.claude\plans\federated-sniffing-meteor.md` - Full integration plan

---

**Last Updated:** 2025-12-22 23:30 UTC
**Status:** Ready for testing

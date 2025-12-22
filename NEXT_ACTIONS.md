# Next Actions (2025-12-22)

## Immediate Next Step

**Test Phase 1 KB Search Fix**
- Send photo of equipment nameplate via Telegram
- Verify KB search returns > 0 atoms
- Check if Route A/B responses now work (instead of always Route C)

**If test succeeds → Phase 2: Expand Vendor Detection**
**If test fails → Debug why manufacturer filter isn't finding atoms**

## Blocked By

**None** - Phase 1 is complete and deployed

## In Progress

**Phase 1: KB Search Fix** ✅ COMPLETE
- Changed retriever to use `manufacturer` column
- Deployed to production VPS
- Bot running with 1,964 atoms loaded

## Backlog (Prioritized)

### 1. Phase 2: Expand Vendor Detection (HIGH)
**Why:** Only 4 vendors recognized, missing 10+ major manufacturers

**Tasks:**
1. Add to VendorType enum: FUJI, MITSUBISHI, OMRON, SCHNEIDER, ABB, YASKAWA, DELTA, DANFOSS, WEG, EATON
2. Update vendor_detector.py with keyword patterns
3. Expand VENDOR_TO_MANUFACTURER mapping in filters.py
4. Test: "Fuji Electric FRN troubleshooting" should detect vendor=FUJI

**Files:**
- `agent_factory/schemas/routing.py` (VendorType enum)
- `agent_factory/routers/vendor_detector.py` (patterns)
- `agent_factory/rivet_pro/rag/filters.py` (mapping)

**Estimate:** 2-3 hours

### 2. Phase 3: Integrate Research Pipeline (MEDIUM)
**Why:** Routes C/D fallback to single LLM, no actual research happens

**Tasks:**
1. Create `agent_factory/rivet_pro/parsing/intent_parser.py`
2. Modify orchestrator `_route_c_no_kb()` to call ResearchPipeline
3. Append research sources to response text
4. Test: KB miss should trigger Stack Overflow + Reddit scraping

**Files:**
- `agent_factory/core/orchestrator.py` (_route_c_no_kb method)
- `agent_factory/rivet_pro/parsing/intent_parser.py` (new file)

**Estimate:** 4-6 hours

### 3. Test Semantic Search with pgvector (LOW)
**Why:** Keyword matching may miss relevant atoms

**Tasks:**
1. Verify embeddings exist in knowledge_atoms table
2. Enable pgvector cosine similarity in retriever.py
3. Test hybrid search (keywords + semantic)

**Estimate:** 2-3 hours

### 4. Replace Mock SME Agents (FUTURE)
**Why:** All agents are mocks, no vendor-specific logic

**Tasks:**
1. Implement SiemensAgent with Siemens fault code database
2. Implement RockwellAgent with Allen-Bradley patterns
3. etc. for each vendor

**Estimate:** 1-2 weeks

## Decisions Needed

**None** - Clear path forward with Phases 2 and 3

## Notes

- Phase 1 deployed without database migration (used existing `manufacturer` column)
- Backward compatible (GENERIC vendor still works)
- No breaking changes to API response format
- Research is async (won't block user responses)

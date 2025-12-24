# Next Actions (2025-12-24)

## CRITICAL

**Deploy Performance Fixes to VPS** (HIGH PRIORITY)
- Two major fixes merged to main, ready for deployment
- Fix #1: Route C latency (36s → <5s)
- Fix #2: KB population (0 → 21 atoms, dynamic count)
- Deployment command: `ssh vps "cd /root/Agent-Factory && git pull && systemctl restart orchestrator-bot"`
- Expected impact: 85% latency reduction for Route C queries

## Immediate Next Step

**Option 1: Deploy Merged Fixes** (RECOMMENDED)
- Deploy Fix #1 + #2 to VPS
- Test Route C latency with real queries
- Verify dynamic atom count displays correctly
- Monitor performance with timing instrumentation logs

**Option 2: Complete Fix #3 (OCR Wiring)**
- Finish remaining 4 tasks in `fix/ocr-metadata-wiring` worktree
- Then deploy all 3 fixes together
- Estimate: 2-3 hours additional work

## Blocked By

**None** - All fixes complete and merged to main

## In Progress

**Fix #3 & #4: OCR Metadata Wiring** (worktree: `fix/ocr-metadata-wiring`)
- Status: Worktree created, not yet started
- Remaining tasks:
  1. Update `create_text_request()` to accept OCR results parameter
  2. Wire OCR through photo handler (pass to request)
  3. Parse equipment from OCR in orchestrator (use metadata not regex)
  4. Update gap detector to prefer OCR over text extraction

**Files:**
- `agent_factory/rivet_pro/models.py` - Add ocr_results parameter
- `agent_factory/integrations/telegram/orchestrator_bot.py` - Pass OCR to request
- `agent_factory/core/orchestrator.py` - Parse OCR metadata for intent
- `agent_factory/core/gap_detector.py` - Prefer OCR equipment over regex

**Estimate:** 2-3 hours

## Backlog (Prioritized)

### 1. Clean Up Git Worktrees (MEDIUM)
**Why:** 3 worktrees active, 2 merged to main

**Tasks:**
1. Remove latency fix worktree: `git worktree remove ../agent-factory-latency-fix`
2. Remove KB fix worktree: `git worktree remove ../agent-factory-kb-fix`
3. Keep OCR fix worktree active for Fix #3
4. Push main branch to GitHub: `git push origin main`

**Estimate:** 5 minutes

### 2. Phase 2: Expand Vendor Detection (HIGH)
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

### 3. Performance Monitoring & Validation (MEDIUM)
**Why:** Verify latency improvements in production

**Tasks:**
1. Run performance tests: `poetry run pytest tests/test_route_c_performance.py -v`
2. Monitor VPS logs for timing markers: `ssh vps "journalctl -u orchestrator-bot -f | grep PERF"`
3. Test LLM cache hit rate with repeated queries
4. Validate parallel execution actually reduces latency
5. Check gap logging doesn't block user responses

**Estimate:** 1-2 hours

### 4. Phase 3: Integrate Research Pipeline (MEDIUM)
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

## Decisions Needed

**Deployment Strategy**
- Deploy now (Fix #1 + #2) or wait for Fix #3 (OCR wiring)?
- User preference needed

## Notes

- All performance optimizations use async/await patterns
- LLM cache saves ~$0.002 per cached query
- Fire-and-forget pattern prevents blocking user responses
- Performance tests validate <5s latency target
- Git worktree pattern successful for parallel development

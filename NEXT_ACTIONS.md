# Next Actions (2025-12-24)

## Recently Completed

**✅ OCR Enhancement Project - All 5 Phases Deployed** (Commit: 80f4be2)
- Phase 1: Dual OCR providers (GPT-4o primary, Gemini fallback)
- Phase 2: KB model number filtering for precision matching
- Phase 3: Auto-fill library from OCR (with "Save to Library" button)
- Phase 4: Quality validation, normalization, confidence scoring
- Phase 5: LangSmith tracing integration
- **Status**: Deployed to VPS, bot running successfully
- **Next**: User testing with photo upload to verify button appears

## Immediate Next Step

**User Testing Required** (HIGH PRIORITY)
1. Send nameplate photo to Telegram bot
2. Verify "Save to Library" button appears after OCR response
3. Tap button → confirm auto-fill with manufacturer/model/serial
4. Enter nickname → save → check `/library` command
5. Report any issues or proceed to next feature

## Blocked By

**None** - All code deployed and operational

## Ready to Start (When User Tested OCR)

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

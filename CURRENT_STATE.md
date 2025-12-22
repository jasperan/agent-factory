# Current State (2025-12-22)

## ✅ Working (Production)

### Photo OCR Handler
- GPT-4o Vision API extracts manufacturer, model, serial number
- JSON parsing handles markdown code fences
- Route C orchestrator fixed (no more decision.intent crash)
- Two-message pattern (user response + admin debug trace)
- Temp file cleanup working
- Deployed to VPS, bot running

### KB Search (FIXED - Phase 1 Complete)
- Retriever uses correct `manufacturer` column
- VENDOR_TO_MANUFACTURER mapping for 9 vendors
- 1,964 knowledge atoms loaded in database
- No more SQL errors on filtered searches

### LLM Routing
- 73% cost reduction vs baseline
- Model capability detection working
- Groq fallback for Routes C/D
- OpenAI fallback if Groq fails

## ⚠️ Partially Working

### Vendor Detection
- Only 4 vendors recognized: SIEMENS, ROCKWELL, GENERIC, SAFETY
- Missing: Fuji, Mitsubishi, Omron, Schneider, ABB, Yaskawa, Delta, Danfoss, WEG, Eaton
- **Next:** Phase 2 will add 10+ vendors

### Research Pipeline
- Code exists but not integrated into Routes C/D
- ResearchPipeline can scrape Stack Overflow + Reddit
- NOT triggered automatically on KB miss
- **Next:** Phase 3 will integrate research

## ❌ Broken / TODO

### KB Coverage
- Some queries still return 0 atoms (vendor not recognized)
- Need to test if filtering by manufacturer actually finds atoms
- Need semantic search (pgvector) for better matching

### Multi-Agent Research
- Flag `research_triggered=True` set but no actual research runs
- PAI research skill exists but not called
- Intent parser missing (can't extract equipment/symptom from query)

## Recent Changes (2025-12-22)

**Phase 1: KB Search Fix**
- Changed retriever.py: `vendor` → `manufacturer`
- Updated filters.py: Added VENDOR_TO_MANUFACTURER map
- Deployed to VPS at 23:36 UTC
- Commit: c3cb093

**Photo Handler Fixes (2025-12-22)**
- Fixed JSON markdown fence stripping
- Fixed Route C AttributeError (decision.intent)
- Deployed to VPS
- Commits: 8ccaeda, 9df09ff

## Next Actions

**Immediate (Phase 2):**
- Expand vendor detection (add 10 manufacturers)
- Test photo handler finds KB atoms for Fuji equipment

**Short-term (Phase 3):**
- Integrate ResearchPipeline into Route C
- Implement intent_parser.py

**Future:**
- Replace mock SME agents with real implementations
- Add pgvector semantic search
- Enable PAI multi-agent research for deep queries

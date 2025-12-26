# 🎯 Dynamic Few-Shot RAG Enhancement Specification

**Version:** 2.0
**Created:** 2025-12-26
**Updated:** 2025-12-26
**Status:** 📋 SPECIFICATION (Not Started)
**Integration Target:** RivetCEO Bot Orchestrator

---

## 📋 CLAUDE CODE CONSTRAINTS (READ THIS FIRST)

> ⚠️ **MANDATORY RULES FOR CLAUDE CODE CLI**
> 
> 1. **DO NOT** implement any phase without explicit user approval
> 2. **DO NOT** modify existing orchestrator routes until Phase 3
> 3. **DO NOT** scrape any websites without user providing credentials/permission
> 4. **ALWAYS** read the phase-specific task file before starting work
> 5. **ALWAYS** update PROJECT_TRACKER.md after completing any task
> 6. **STOP** at each checkpoint and wait for user validation
> 7. **RUN TESTS** before declaring any phase complete

### Claude Code CLI Best Practices (from Anthropic Engineering)

**Session Management:**
- Use `/init` to have Claude understand project structure
- Use `/clear` between phases to reset context window
- For complex tasks: have Claude dump progress to `.md`, `/clear`, then continue

**Prompt Specificity:**
- Claude Code success rate improves with specific instructions
- Reference specific files: `@./examples/store.py`
- Include test commands in prompts

**Task File Usage:**
```bash
# Start each phase by reading the task file
cat .claude/tasks/phase1-infrastructure.md

# Then tell Claude:
"Implement phase 1 following .claude/tasks/phase1-infrastructure.md exactly"
```

**CLAUDE.md Integration:**
- This spec is referenced in main CLAUDE.md
- Task files are in `.claude/tasks/` for slash command access
- Project constraints cascade: CLAUDE.md → This Spec → Phase Task Files

---

## 🎬 VIDEO TUTORIALS (Watch Before Implementation)

| Resource | Link | Duration | Focus |
|----------|------|----------|-------|
| LangChain RAG from Scratch (FreeCodeCamp) | https://www.youtube.com/watch?v=sVcwVQRHIc8 | 2.5 hours | Complete RAG fundamentals |
| pixegami RAG Tutorial | https://www.youtube.com/watch?v=tcqEUSNCn8I | 30 min | Simple RAG with LangChain |
| LangChain Few-Shot Prompting | https://www.youtube.com/watch?v=Y0ml8r9GE00 | 15 min | Few-shot example selectors |
| Building Production RAG | https://www.youtube.com/watch?v=jENqvjpkwmw | 45 min | Production patterns |

---

## 📚 GITHUB REFERENCE REPOS

### Primary References (Study These First)

| Repository | Link | Study Files | Why |
|------------|------|-------------|-----|
| `langchain-ai/rag-from-scratch` | https://github.com/langchain-ai/rag-from-scratch | All notebooks in order | Official LangChain RAG curriculum |
| `NirDiamant/RAG_Techniques` | https://github.com/NirDiamant/RAG_Techniques | Full repo - 20+ techniques | Most comprehensive RAG patterns |
| `pixegami/rag-tutorial-v2` | https://github.com/pixegami/rag-tutorial-v2 | `query_data.py`, `test_rag.py` | Testing patterns + local LLM |
| `pguso/rag-from-scratch` | https://github.com/pguso/rag-from-scratch | `src/retrievers/` | Retriever implementations from ground up |
| `mddunlap924/LangChain-SynData-RAG-Eval` | https://github.com/mddunlap924/LangChain-SynData-RAG-Eval | `gen-question-answer-query.ipynb` | Few-shot + synthetic data |

### Industrial Datasets & Domain References

| Repository | Link | Why |
|------------|------|-----|
| `jonathanwvd/awesome-industrial-datasets` | https://github.com/jonathanwvd/awesome-industrial-datasets | Predictive maintenance datasets |
| `harvard-hbs/rag-example` | https://github.com/harvard-hbs/rag-example | Production RAG patterns |
| `infiniflow/ragflow` | https://github.com/infiniflow/ragflow | Enterprise RAG engine reference |

### LangChain Documentation (Required Reading)

| Topic | URL |
|-------|-----|
| Few-shot chat examples | https://python.langchain.com/docs/how_to/few_shot_examples_chat/ |
| SemanticSimilarityExampleSelector | https://python.langchain.com/docs/how_to/example_selectors_similarity/ |
| Dynamic few-shot with LangSmith | https://blog.langchain.dev/few-shot-prompting-with-dynamic-examples/ |
| FewShotChatMessagePromptTemplate | https://api.python.langchain.com/en/latest/prompts/langchain_core.prompts.few_shot.FewShotChatMessagePromptTemplate.html |

### Code Patterns to Copy

**SemanticSimilarityExampleSelector (from LangChain source):**
```
https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/example_selectors/semantic_similarity.py
```

**FewShotChatMessagePromptTemplate example:**
```
https://github.com/langchain-ai/langchain/discussions/23850
```

**pixegami test patterns:**
```
https://github.com/pixegami/rag-tutorial-v2/blob/main/test_rag.py
```

---

## 🎯 Business Objective

Build a self-improving industrial maintenance RAG system where:
1. Real maintenance cases (starting with roller coaster PLC troubleshooting) become training examples
2. Similar past cases are dynamically retrieved to improve Claude's parsing of messy technician input
3. Every resolved case automatically enriches the knowledge base
4. System gets smarter with every interaction

---

## 🏗️ Architecture Decision

### Why RAG Over Fine-Tuning

| Factor | Fine-Tuning | Dynamic Few-Shot RAG |
|--------|-------------|---------------------|
| **Setup Cost** | $500+/month, 3 weeks | $50/month, 1 day |
| **Update Speed** | Retrain (hours/days) | Instant (add to DB) |
| **Data Required** | 1000+ examples | Works with 10+ examples |
| **Maintenance** | Model drift over time | Self-improving |
| **Your Use Case** | ❌ Overkill | ✅ Perfect fit |

### Integration Point

```
Current RivetCEO Flow:
┌─────────────────┐
│ Telegram Input  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4-Route Orchestr│ ◄── INSERT FEW-SHOT RETRIEVAL HERE
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│Route A│ │Route C│
│ OCR   │ │ SME   │
└───────┘ └───────┘
```

**Injection Point:** Before SME agent prompting, retrieve 2-3 similar solved cases and inject as few-shot examples.

---

## 📂 DIRECTORY STRUCTURE

```
chucky_project/
├── DYNAMIC_FEWSHOT_RAG_SPEC.md          # This file (master spec)
├── .claude/
│   ├── tasks/                            # Phase task files for Claude Code
│   │   ├── phase0-case-collection.md     # Manual user task
│   │   ├── phase1-infrastructure.md      # Claude Code task
│   │   ├── phase2-retrieval.md           # Claude Code task
│   │   ├── phase3-integration.md         # Claude Code task
│   │   ├── phase4-feedback.md            # Claude Code task
│   │   └── phase5-backfill.md            # Claude Code task
│   └── agents/
│       └── fewshot-rag-builder.md        # Sub-agent definition
├── examples/                              # NEW: Few-shot RAG module
│   ├── __init__.py
│   ├── schemas.py                        # Pydantic schemas
│   ├── store.py                          # Vector store wrapper
│   ├── embedder.py                       # Embedding pipeline
│   ├── retriever.py                      # Case retrieval
│   ├── formatter.py                      # Few-shot formatter
│   └── tests/
│       ├── test_store.py
│       ├── test_retriever.py
│       └── fixtures/
│           └── sample_cases.json
└── cases/                                 # Roller coaster cases (user collects)
    ├── RC-001.json
    ├── RC-002.json
    └── ...
```

---

## 📦 PHASES

### Phase 0: Roller Coaster Case Collection
**Duration:** Ongoing (parallel with other phases)
**Owner:** Mike (USER DOES THIS - NOT CLAUDE)
**Task File:** `.claude/tasks/phase0-case-collection.md`

**Objective:** Collect real maintenance cases from your roller coaster work

**Case Format (JSON Schema):**
```json
{
  "case_id": "RC-001",
  "timestamp": "2025-12-26T10:30:00Z",
  "equipment": {
    "type": "PLC",
    "manufacturer": "Allen-Bradley",
    "model": "ControlLogix 5580",
    "location": "Lift Hill Controller"
  },
  "input": {
    "raw_text": "lift not moving fault light on panel",
    "photo_url": "optional-telegram-photo-id"
  },
  "diagnosis": {
    "root_cause": "Safety circuit E-stop chain broken at station 3",
    "fault_codes": ["F001", "E-STOP"],
    "symptoms": ["Lift motor not energizing", "Fault LED active"]
  },
  "resolution": {
    "steps": [
      "Checked E-stop chain continuity",
      "Found broken contact at station 3 E-stop",
      "Replaced E-stop switch",
      "Reset safety circuit"
    ],
    "parts_used": ["E-stop switch P/N 800T-FXP16"],
    "time_to_fix": "45 minutes"
  },
  "keywords": ["lift", "e-stop", "safety circuit", "controllogix"],
  "category": "electrical"
}
```

**Storage Location:** `cases/` directory

**Acceptance Criteria:**
- [ ] Minimum 5 real cases documented
- [ ] Each case has raw input + structured resolution
- [ ] Cases cover different equipment types (PLC, VFD, sensors)

---

### Phase 1: Example Store Infrastructure
**Duration:** 2-4 hours
**Dependencies:** None
**Task File:** `.claude/tasks/phase1-infrastructure.md`
**Claude Code Allowed:** ✅ Yes (with constraints)

**Before Starting - Study These Files:**
```
# From pixegami/rag-tutorial-v2
https://github.com/pixegami/rag-tutorial-v2/blob/main/get_embedding_function.py
https://github.com/pixegami/rag-tutorial-v2/blob/main/populate_database.py

# From langchain-ai/rag-from-scratch
https://github.com/langchain-ai/rag-from-scratch/blob/main/rag_from_scratch_1_to_4.ipynb
```

**Constraints:**
```
ALLOWED:
- Create new Python files in examples/ directory
- Create Pydantic schemas for case validation
- Create vector store initialization scripts
- Create embedding pipeline
- Create unit tests

NOT ALLOWED:
- Modify existing orchestrator code
- Connect to production databases without explicit approval
- Make external API calls (use mocks for testing)
```

**Deliverables:**

1. **Case Schema** (`examples/schemas.py`) - See task file for implementation

2. **Vector Store Setup** (`examples/store.py`)
   - Reuse existing Pinecone/Supabase pgvector from RivetCEO
   - DO NOT create new infrastructure

3. **Embedding Pipeline** (`examples/embedder.py`)
   - Use same embeddings as existing knowledge base

**Test Command:**
```bash
cd examples && python -m pytest tests/test_store.py -v
```

**Acceptance Criteria:**
- [ ] Schema validates sample case JSON
- [ ] Vector store connection works (test mode)
- [ ] Can embed a sample case successfully
- [ ] No modifications to existing code
- [ ] All tests pass

**CHECKPOINT:** ⛔ Stop here. User must validate infrastructure before Phase 2.

---

### Phase 2: Example Retrieval System
**Duration:** 2-4 hours
**Dependencies:** Phase 1 complete, minimum 3 cases in store
**Task File:** `.claude/tasks/phase2-retrieval.md`
**Claude Code Allowed:** ✅ Yes (with constraints)

**Before Starting - Study These Files:**
```
# LangChain SemanticSimilarityExampleSelector
https://api.python.langchain.com/en/latest/example_selectors/langchain_core.example_selectors.semantic_similarity.SemanticSimilarityExampleSelector.html

# Few-shot chat examples
https://python.langchain.com/docs/how_to/few_shot_examples_chat/

# Discussion with working code
https://github.com/langchain-ai/langchain/discussions/23850
```

**Constraints:**
```
ALLOWED:
- Create retrieval module in examples/
- Create similarity scoring logic
- Create few-shot prompt formatter
- Unit tests for retrieval

NOT ALLOWED:
- Modify orchestrator routes
- Change SME agent prompts
- Deploy anything to production
```

**Deliverables:**

1. **Retriever** (`examples/retriever.py`) - Based on `SemanticSimilarityExampleSelector`

2. **Few-Shot Formatter** (`examples/formatter.py`)

**Test Command:**
```bash
cd examples && python -m pytest tests/test_retriever.py -v --query "motor won't start"
```

**Acceptance Criteria:**
- [ ] Retrieves top-3 similar cases for test query
- [ ] Similarity scores > 0.7 for good matches
- [ ] Few-shot format is clear and parseable
- [ ] Latency < 500ms for retrieval
- [ ] All tests pass

**CHECKPOINT:** ⛔ Stop here. User must test retrieval quality before Phase 3.

---

### Phase 3: Orchestrator Integration
**Duration:** 3-5 hours
**Dependencies:** Phase 2 complete, retrieval quality validated
**Task File:** `.claude/tasks/phase3-integration.md`
**Claude Code Allowed:** ⚠️ RESTRICTED

**Before Starting - Study:**
```
# LangChain FewShotChatMessagePromptTemplate
https://python.langchain.com/docs/how_to/few_shot_examples_chat/

# pixegami query pattern
https://github.com/pixegami/rag-tutorial-v2/blob/main/query_data.py
```

**Constraints:**
```
ALLOWED:
- Modify SME agent prompt templates ONLY
- Add retrieval call before SME invocation
- Add latency monitoring for retrieval step

REQUIRES USER APPROVAL FOR EACH CHANGE:
- Any change to orchestrator routing logic
- Any change to existing route handlers
- Any modification to Telegram handlers

NOT ALLOWED:
- Remove or disable existing functionality
- Change database schemas
- Modify authentication/security code
```

**Integration Pattern:**
```python
# BEFORE (current flow):
async def route_c_sme_handler(input_data):
    prompt = SME_SYSTEM_PROMPT
    response = await call_sme_agent(prompt, input_data)
    return response

# AFTER (with few-shot enhancement):
async def route_c_sme_handler(input_data):
    # NEW: Retrieve similar cases
    similar_cases = await case_retriever.get_similar_cases(input_data.text)
    few_shot_context = format_maintenance_examples(similar_cases)
    
    # Inject into prompt
    enhanced_prompt = f"""
{SME_SYSTEM_PROMPT}

## Similar Past Cases (for reference):
{few_shot_context}

## Current Case:
{input_data.text}
"""
    response = await call_sme_agent(enhanced_prompt, input_data)
    return response
```

**Latency Budget:**
- Current routing latency: ~36 seconds (known issue)
- Retrieval overhead budget: < 2 seconds
- Target total latency: < 40 seconds

**LangSmith Traces to Add:**
- `fewshot.retrieval.latency_ms`
- `fewshot.cases_found`
- `fewshot.avg_similarity_score`

**Acceptance Criteria:**
- [ ] SME agent receives few-shot context
- [ ] Latency increase < 2 seconds
- [ ] LangSmith shows retrieval traces
- [ ] No regression in existing functionality
- [ ] Fallback works when no similar cases found

**CHECKPOINT:** ⛔ Stop here. User must validate in staging before Phase 4.

---

### Phase 4: Feedback Loop (Auto-Learning)
**Duration:** 4-6 hours
**Dependencies:** Phase 3 deployed and stable
**Task File:** `.claude/tasks/phase4-feedback.md`
**Claude Code Allowed:** ⚠️ RESTRICTED

**Objective:** Automatically add resolved cases to knowledge base

**Trigger:** When technician marks case as "resolved" in Telegram

**Flow:**
```
Technician sends: ✅ Fixed it
         │
         ▼
┌────────────────────────┐
│ Detect resolution      │
└────────────────────────┘
         │
         ▼
┌────────────────────────┐
│ Ask follow-up:         │
│ - Root cause?          │
│ - Fix steps?           │
│ - Time to fix?         │
└────────────────────────┘
         │
         ▼
┌────────────────────────┐
│ Parse into Case schema │
└────────────────────────┘
         │
         ▼
┌────────────────────────┐
│ Embed + store in DB    │
└────────────────────────┘
         │
         ▼
┌────────────────────────┐
│ Available for future   │
│ few-shot retrieval     │
└────────────────────────┘
```

**Acceptance Criteria:**
- [ ] Resolution trigger works in Telegram
- [ ] Follow-up questions are asked
- [ ] Messy input is parsed into structured case
- [ ] Case is embedded and stored
- [ ] New case appears in retrieval results

**CHECKPOINT:** ⛔ Stop here. User must validate learning loop before Phase 5.

---

### Phase 5: Industrial Forum Backfill (Optional)
**Duration:** 8-16 hours
**Dependencies:** Phases 1-4 complete
**Task File:** `.claude/tasks/phase5-backfill.md`
**Claude Code Allowed:** ⚠️ MANUAL SUPERVISION REQUIRED

**Objective:** Backfill with curated industrial forum cases

**Data Sources (Priority Order - NOT Reddit):**

| Source | Type | Quality | URL |
|--------|------|---------|-----|
| PLCTalk.net | Forum threads | ⭐⭐⭐⭐⭐ | https://plctalk.net |
| Control.com | Forum threads | ⭐⭐⭐⭐ | https://control.com |
| MrPLC.com | Forum threads | ⭐⭐⭐⭐ | https://mrplc.com |
| Your Roller Coaster Cases | Real cases | ⭐⭐⭐⭐⭐ | Local |

**Scraping Constraints:**
```
MANDATORY:
- Respect robots.txt
- Rate limit: 1 request per 5 seconds minimum
- User-Agent: "RivetCEO-KnowledgeBot/1.0"
- Store raw HTML for audit trail
- Human review before ingestion

DO NOT SCRAPE:
- Private/authenticated content
- User personal information
- Content explicitly marked as copyrighted
```

**Quality Filters:**
- Thread must have accepted/marked solution
- At least 3 replies
- Contains specific equipment references
- Published within last 5 years

**Acceptance Criteria:**
- [ ] Scraper respects rate limits
- [ ] 50+ curated cases from forums
- [ ] Each case passes human review
- [ ] Cases improve retrieval diversity

---

## 📊 Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Parse accuracy | (establish) | +20% | Manual review |
| Technician satisfaction | (establish) | +30% | Telegram feedback |
| Time to resolution | (establish) | -15% | Case timestamps |
| Knowledge base size | 2,000 atoms | 50,000 atoms | Vector store count |
| Retrieval hit rate | N/A | >80% | Cases with similar matches |

---

## ⚠️ Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Low-quality forum data | Medium | High | Human review gate |
| Latency regression | Medium | High | Strict 2s budget |
| Irrelevant retrievals | Medium | Medium | Similarity threshold 0.7+ |
| Over-reliance on examples | Low | Medium | Blend with general knowledge |

---

## 🔗 Related Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Main project instructions |
| `PROJECT_TRACKER.md` | Sprint tracking |
| `.claude/agents/fewshot-rag-builder.md` | Sub-agent definition |
| `.claude/agents/industrial-knowledge-curator.md` | Knowledge ingestion agent |
| `.claude/tasks/phase*.md` | Phase-specific task files |

---

## 🚀 QUICK START FOR CLAUDE CODE

To start implementation:

```bash
# Step 1: Read this spec
cat DYNAMIC_FEWSHOT_RAG_SPEC.md

# Step 2: Read the phase task file
cat .claude/tasks/phase1-infrastructure.md

# Step 3: Study the reference repos (links in task file)

# Step 4: Implement following task file instructions

# Step 5: Run tests
cd examples && python -m pytest tests/ -v

# Step 6: Update PROJECT_TRACKER.md

# Step 7: STOP and wait for user checkpoint approval
```

---

## 📝 Session Log

| Date | Phase | Status | Notes |
|------|-------|--------|-------|
| 2025-12-26 | Spec v1.0 | 📋 Created | Initial specification |
| 2025-12-26 | Spec v2.0 | 📋 Enhanced | Added GitHub/YouTube refs, task files |
| 2025-12-26 | Spec v2.1 | 📋 Enhanced | Added NirDiamant/RAG_Techniques, industrial datasets, Phase 4-5 task files, slash command |

---

## 🎯 QUICK START (Copy-Paste Ready)

### Option 1: Use Slash Command in Claude Code CLI
```
/project:start-rag-phase 1
```

### Option 2: Manual Start
```bash
# Step 1: Read master spec
cat DYNAMIC_FEWSHOT_RAG_SPEC.md

# Step 2: Read phase task file
cat .claude/tasks/phase1-infrastructure.md

# Step 3: Study the reference repos (CRITICAL - don't skip)
# Open in browser and READ the code patterns

# Step 4: Tell Claude Code:
"Implement phase 1 following .claude/tasks/phase1-infrastructure.md"

# Step 5: After implementation, run tests
cd examples && python -m pytest tests/ -v

# Step 6: Update tracker
# Claude will do this automatically if CLAUDE.md is followed
```

---

**Next Action:** User collects 5 roller coaster cases (Phase 0), then use `/project:start-rag-phase 1` or `cat .claude/tasks/phase1-infrastructure.md` to start Phase 1.

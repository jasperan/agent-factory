# Dynamic Few-Shot RAG Setup Complete ✓

**Date:** 2025-12-26
**Status:** Files copied, ready for implementation

---

## What Was Done

### 1. Files Copied from Chucky Project

**Specification:**
- ✓ `specs/DYNAMIC_FEWSHOT_RAG_SPEC.md` (21 KB)

**Phase Task Files:**
- ✓ `.claude/tasks/phase0-case-collection.md` (3.1 KB)
- ✓ `.claude/tasks/phase1-infrastructure.md` (17 KB)
- ✓ `.claude/tasks/phase2-retrieval.md` (19 KB)
- ✓ `.claude/tasks/phase3-integration.md` (13 KB)
- ✓ `.claude/tasks/phase4-feedback.md` (5.8 KB)
- ✓ `.claude/tasks/phase5-backfill.md` (7.4 KB)

**Slash Command:**
- ✓ `.claude/commands/start-rag-phase.md` (1.3 KB)

---

## What This System Does

The Dynamic Few-Shot RAG system enhances Agent Factory's knowledge retrieval:

1. **Stores Real Cases** - Captures actual troubleshooting interactions as examples
2. **Smart Retrieval** - Finds similar past cases when answering questions
3. **Better Answers** - Uses past cases as few-shot examples to improve responses
4. **Auto-Learning** - Continuously improves from successful interactions

**Target:** RivetCEO Bot (industrial maintenance troubleshooting)

---

## How to Use

### Start a Phase
```bash
# In Claude Code CLI
/start-rag-phase 1
```

This will:
1. Read the master spec (`DYNAMIC_FEWSHOT_RAG_SPEC.md`)
2. Read the phase-specific task file
3. Guide you through implementation
4. Run tests and checkpoints

### Phase Overview

| Phase | Name | User Action Required |
|-------|------|---------------------|
| **0** | Case Collection | ✅ YES - Manual data collection |
| **1** | Infrastructure | ❌ NO - Claude can implement |
| **2** | Retrieval | ❌ NO - Claude can implement |
| **3** | Integration | ⚠️ RESTRICTED - Modify orchestrator carefully |
| **4** | Feedback Loop | ❌ NO - Claude can implement |
| **5** | Forum Backfill | ⚠️ SUPERVISED - Scraping requires permissions |

---

## Reference Resources

### Key GitHub Repos (Study Before Implementation)
- [`langchain-ai/rag-from-scratch`](https://github.com/langchain-ai/rag-from-scratch) - Official curriculum
- [`NirDiamant/RAG_Techniques`](https://github.com/NirDiamant/RAG_Techniques) - 20+ techniques
- [`pixegami/rag-tutorial-v2`](https://github.com/pixegami/rag-tutorial-v2) - Testing patterns

### Video Tutorials
- [LangChain RAG from Scratch](https://www.youtube.com/watch?v=sVcwVQRHIc8) (2.5 hours)
- [pixegami RAG Tutorial](https://www.youtube.com/watch?v=tcqEUSNCn8I) (30 min)

---

## Integration with Agent Factory

This RAG system will integrate with:
- **RivetCEO Bot** - Main industrial maintenance troubleshooting agent
- **Knowledge Atoms** - Existing knowledge base infrastructure
- **PostgreSQL + pgvector** - Already configured for embeddings
- **LangGraph Pipeline** - Existing ingestion system

---

## Next Steps

1. **Read the spec:**
   ```bash
   cat specs/DYNAMIC_FEWSHOT_RAG_SPEC.md
   ```

2. **Start with Phase 1:**
   ```bash
   /start-rag-phase 1
   ```

3. **Follow checkpoints** - Each phase has validation steps

---

## Important Constraints

⚠️ **DO NOT:**
- Skip ahead to other phases
- Modify orchestrator routes before Phase 3
- Scrape websites without permission
- Declare phase complete without running tests

✅ **ALWAYS:**
- Read phase task file before starting
- Run tests after each deliverable
- Update PROJECT_TRACKER.md after tasks
- Stop at checkpoints for user approval

---

## File Locations

```
Agent Factory/
├── specs/
│   └── DYNAMIC_FEWSHOT_RAG_SPEC.md     # Master specification
├── .claude/
│   ├── tasks/
│   │   ├── phase0-case-collection.md
│   │   ├── phase1-infrastructure.md
│   │   ├── phase2-retrieval.md
│   │   ├── phase3-integration.md
│   │   ├── phase4-feedback.md
│   │   └── phase5-backfill.md
│   └── commands/
│       └── start-rag-phase.md          # Slash command
```

---

## Questions?

See the full spec or individual phase task files for detailed instructions.

# Strangler Pattern Migration Rules

This document defines the rules for consolidating 19 scattered repositories into 2 focused products.

**Status**: User Approved - December 21, 2025

---

## The Strangler Pattern

The [Strangler Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html) gradually replaces a legacy system by incrementally building a new system around the old one, then "strangling" the old system until it can be retired.

**Our approach**:
1. Identify winning products (Agent-Factory, Friday-Unified)
2. Extract useful code from scattered repos into products
3. Stop developing the old repos (they become "code mines")
4. Archive old repos once extraction is complete

---

## Rule 1: STOP Adding Code to EXPERIMENT Repos

### Affected Repos
- `CodeBang`
- `jarvis-android-voice-proto`
- `Chucky`
- `claudegen-coach`

### What This Means
- These repos are now **read-only "code mines"**
- You can EXTRACT useful patterns, but DON'T develop new features
- No new commits to these repos
- No bug fixes (unless critical for extraction)

### Why
These repos have minimal working code and lack focus. Development effort should go to Agent-Factory and Friday-Unified instead.

---

## Rule 2: ARCHIVE Empty Repos Immediately

### Affected Repos (DELETE or mark as archived)
- `your-assistant-app` - 1 file (blank README), no code
- `Nexus1` - 1 file (blank README), no code
- `VibeBuddy` - 1 file (blank README), no code
- `TechMeterAI` - Completely empty (0 commits)

### What This Means
- Delete these repos OR mark as archived on GitHub
- They add no value and clutter the portfolio

### Affected Repos (KEEP as reference, don't modify)
- `langchain-crash-course` - Educational fork, useful reference
- `Archon` - Knowledge management fork, mine patterns but don't modify

### Why
Empty repos waste mental energy and make the portfolio look unprofessional.

---

## Rule 3: ABSORB jarvis-core into Agent-Factory

### What This Means
1. Review `jarvis-core` for useful orchestration concepts:
   - Cross-app orchestration patterns
   - Single sign-on authentication approaches
   - Data synchronization strategies
2. If useful, add to `Agent-Factory/core/orchestrator.py` or related modules
3. Document in Agent-Factory architecture docs
4. **THEN**: Archive `jarvis-core` repo

### Why
`jarvis-core` and `Agent-Factory` overlap (both are "orchestration hubs"). Consolidate to avoid duplication and confusion.

### Timeline
Weeks 3-4

---

## Rule 4: CONSOLIDATE Friday Variants

**Priority 2** (after SCAFFOLD focus)

### What This Means
1. Create unified `Friday-Unified` repo (or rename `Friday` as primary)
2. Merge code from all three variants:
   - `Friday` (React Native voice assistant - **PRIMARY BASE**)
   - `FRIDAYNEW` (Google AI Studio integration - extract patterns)
   - `Friday-2` (AI Studio variant - evaluate for useful code)
3. Extract shared voice/audio utilities into **Library 2: Voice & Audio Processing**
4. Archive `FRIDAYNEW` and `Friday-2` after merge

### Why
Three Friday variants create confusion and duplicate effort. One unified codebase is easier to maintain and develop.

### Timeline
Weeks 5-6

---

## Rule 5: NEW Work Goes Here

### Agent-Factory (PRIMARY FOCUS)
All SCAFFOLD platform work:
- AI orchestration
- ClaudeExecutor and PRCreator
- Task execution and tracking
- LLM routing and cost optimization
- Memory and knowledge base systems

### Friday-Unified (SECONDARY FOCUS)
All voice assistant work:
- Mobile voice AI (React Native)
- Web voice AI (AI Studio)
- Voice & Audio Processing library

### Industrial Platform (DEFERRED)
DO NOT START until Agent-Factory + Friday-Unified are mature:
- `nexus-cmms-recovery-point-2` - equipment tracking
- `chucky_project` - n8n automation + bots

---

## Rule 6: Libraries Are SHARED

### Library 1: AI Infrastructure Core
- **Lives in**: `Agent-Factory/core` and `Agent-Factory/llm`
- **Used by**: All products (Agent-Factory, Friday, Industrial Platform)
- **Contains**: Orchestration, LLM routing, memory systems, SCAFFOLD execution

### Library 2: Voice & Audio Processing
- **Create new library**: Extract from Friday variants
- **Used by**: Friday-Unified (mobile + web)
- **Contains**: Audio recording, transcription, TTS, waveform UI

### Library 3: Bot Integration Framework
- **Status**: DEFERRED until Industrial Platform starts
- **Used by**: Industrial Platform, potential Agent-Factory integrations

---

## Rule 7: Migration Order

### Week 1-2: Focus on Agent-Factory
- Continue SCAFFOLD platform development
- Improve orchestration, LLM routing, memory
- Integrate Backlog.md task management
- **DO NOT** work on Friday consolidation yet
- **DO NOT** work on Industrial Platform
- **DO NOT** add features to EXPERIMENT repos

### Week 3-4: Continue SCAFFOLD + Begin jarvis-core Extraction
- Keep building Agent-Factory
- Review `jarvis-core` for useful patterns
- Extract patterns into Agent-Factory if valuable
- Document extraction in architecture docs

### Week 5-6: Consolidate Friday Variants
- Create `Friday-Unified` repo (or rename `Friday`)
- Merge code from `Friday`, `FRIDAYNEW`, `Friday-2`
- Extract Voice & Audio Processing library
- Archive `FRIDAYNEW` and `Friday-2`

### Week 7-8: Finalize Voice Library
- Polish Voice & Audio Processing library
- Ensure both mobile and web use shared library
- Documentation and examples

### Week 9+: Archive Old Repos
- Add deprecation notices to EXPERIMENT repos
- Archive `jarvis-core` (after extraction)
- Archive old Friday variants
- Delete empty repos (`your-assistant-app`, `Nexus1`, `VibeBuddy`, `TechMeterAI`)

---

## Deprecation Notice Template

Add to README of deprecated repos:

```markdown
⚠️ **This repository is deprecated.**

Active development has moved to:
- [Agent-Factory](https://github.com/mikecranesync/Agent-Factory) - AI orchestration platform
- [Friday-Unified](https://github.com/mikecranesync/Friday-Unified) - Voice AI assistant

See [STRANGLER_RULES.md](https://github.com/mikecranesync/Agent-Factory/blob/main/STRANGLER_RULES.md) for the migration plan.

This repo is kept for reference only. No new features or bug fixes will be implemented.
```

---

## Success Metrics

### By End of Week 2
- ✅ All 4 portfolio docs created in Agent-Factory
- ✅ Deprecation notices added to EXPERIMENT repos
- ✅ Empty repos archived/deleted

### By End of Week 6
- ✅ Friday-Unified repo created and functional
- ✅ Voice & Audio Processing library extracted
- ✅ jarvis-core patterns absorbed into Agent-Factory

### By End of Week 9
- ✅ All old Friday variants archived
- ✅ jarvis-core archived
- ✅ Portfolio fully consolidated into 2 active products + shared libraries

---

## Key Principle

**"Code mines, not active projects."**

Old repos are useful for extracting patterns, but active development must focus on Agent-Factory and Friday-Unified. Don't spread effort across 19 repos—consolidate into 2 winning products.

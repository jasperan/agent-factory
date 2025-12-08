# Lessons Learned Database

**Purpose:** Capture debugging insights, architectural decisions, and "gotchas" discovered during development.

**Why This Exists:** To prevent repeating the same mistakes and speed up debugging by learning from past issues.

---

## Quick Search

### By Category
- [LangChain Integration](#langchain-integration)
- [Memory Systems](#memory-systems)
- [Telegram Integration](#telegram-integration)
- [Agent Architecture](#agent-architecture)
- [Testing & Debugging](#testing--debugging)

### By Severity
- **High:** LL-001, LL-002 (3+ hours debugging time)
- **Medium:** LL-003, LL-004 (1-2 hours)
- **Low:** LL-005 (preventative)

---

## All Lessons

| ID | Title | Category | Status | Date |
|----|-------|----------|--------|------|
| LL-001 | LangChain Memory Systems Are Opaque | LangChain, Memory | ✅ Resolved | 2025-12-08 |
| LL-002 | Agent Caching Requires Memory Persistence | Agent Architecture | ✅ Resolved | 2025-12-08 |
| LL-003 | System Prompts Don't Enforce Behavior | Prompt Engineering | ✅ Resolved | 2025-12-08 |
| LL-004 | Test at Integration Points | Testing | ✅ Resolved | 2025-12-08 |
| LL-005 | Simpler is More Reliable | Architecture | ✅ Resolved | 2025-12-08 |

---

## How to Use

### Searching for Lessons

**By Keyword:**
```bash
grep -r "memory" docs/lessons_learned/LESSONS_DATABASE.md
```

**By Tag:**
```bash
grep "#langchain" docs/lessons_learned/LESSONS_DATABASE.md
```

**By File:**
```bash
grep "bot.py" docs/lessons_learned/LESSONS_DATABASE.md
```

### Adding a New Lesson

1. Assign next ID (LL-006, LL-007, etc.)
2. Use the template below
3. Add to `LESSONS_DATABASE.md`
4. Add entry to `lessons_database.json`
5. Update this README index

---

## Lesson Template

```markdown
## [LL-XXX] Title of Lesson

**Category:** Primary, Secondary
**Severity:** High/Medium/Low
**Date Discovered:** YYYY-MM-DD
**Status:** Resolved/Open/Workaround

### Problem Statement
What went wrong? (1-2 sentences)

### Symptoms
- Observable behavior #1
- Observable behavior #2

### Root Cause
Why did it happen? (technical explanation)

### Failed Attempts
1. ❌ What we tried first (why it failed)
2. ❌ What we tried second (why it failed)

### Solution
✅ What actually worked

```python
# Code example if applicable
```

### Code References
- **Fixed:** path/to/file.py:line
- **Related:** path/to/other/file.py

### Principle
**Core learning:** Abstract principle to apply elsewhere

### Related Lessons
- LL-XXX (similar issue)
- LL-YYY (related pattern)

### Tags
#tag1 #tag2 #tag3
```

---

## Integration

### CLAUDE.md Reference
This database is referenced in `CLAUDE.md` - Claude CLI should check here before implementing similar patterns.

### Future: Vector Database
`lessons_database.json` is machine-readable and ready for vector embedding and semantic search.

**Future CLI Command:**
```bash
agentcli lessons --search "context retention"
# Returns: LL-001, LL-002 with relevance scores
```

---

## Categories

### LangChain Integration
Lessons about working with LangChain framework, agents, and memory systems.

### Memory Systems
Patterns for managing conversation state, context, and history.

### Telegram Integration
Telegram bot-specific issues, handlers, session management.

### Agent Architecture
Core patterns for agent design, orchestration, and lifecycle.

### Testing & Debugging
Strategies for finding and fixing bugs efficiently.

---

## Principles Extracted

These universal principles emerged from specific lessons:

1. **Explicit > Implicit** - Visible state is debuggable state (LL-001)
2. **State Synchronization** - Cached objects need state initialization (LL-002)
3. **Data Before Instructions** - Prompts need both (LL-003)
4. **Integration Testing** - Test the glue, not just components (LL-004)
5. **Minimize State Systems** - Fewer moving parts = fewer bugs (LL-005)

---

## Contributing

When you discover a new lesson:
1. Create a branch: `git checkout -b lesson/short-description`
2. Add lesson to `LESSONS_DATABASE.md`
3. Add JSON entry to `lessons_database.json`
4. Update this README index
5. Submit PR with label `lesson-learned`

---

**Last Updated:** 2025-12-08
**Total Lessons:** 5
**Next ID:** LL-006

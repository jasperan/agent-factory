# Decision Template

Use this template to document major Backlog-related decisions.

**For project-wide decisions:** Add to `DECISIONS_LOG.md` in the root directory.
**For Backlog-specific decisions:** Create a file here (`backlog/decisions/`) and link from main `DECISIONS_LOG.md`.

---

## [YYYY-MM-DD] Decision: [Short Title]

**Context:**
[Describe the situation that requires a decision. What problem are you solving? What constraints exist?]

**Decision:**
[State the decision clearly and concisely in 1-2 sentences]

**Rationale:**
1. [First reason this decision makes sense]
2. [Second reason]
3. [Third reason - data, constraints, trade-offs]

**Alternatives Considered:**
- **Option A:** [Describe alternative]
  - Pros: [Benefits]
  - Cons: [Drawbacks]
  - Rejected: [Why not chosen]

- **Option B:** [Describe alternative]
  - Pros: [Benefits]
  - Cons: [Drawbacks]
  - Rejected: [Why not chosen]

**Implementation:**
[How will this decision be implemented? What changes are needed?]

**Impact:**
[What is affected by this decision? Files, workflows, dependencies?]

**Status:**
[Accepted | Rejected | Superseded | Deprecated]

**Related Decisions:**
- [Link to DECISIONS_LOG.md entry if this is a refinement]
- [Link to other related decisions]

---

## Example Decision

## [2025-12-17] Decision: One-Way Sync (Backlog → TASK.md)

**Context:**
Need to sync Backlog task statuses with TASK.md for Claude Code integration. Two options: bidirectional sync or one-way sync. Bidirectional sync risks conflicts (user edits TASK.md manually while Backlog updates task status programmatically).

**Decision:**
Implement one-way sync from Backlog.md → TASK.md. Backlog.md is the source of truth.

**Rationale:**
1. **Conflict Resolution Simplified:** No conflicts possible when Backlog is source of truth
2. **Clear Ownership:** Backlog tasks own all metadata (status, priority, labels)
3. **TASK.md as View Layer:** TASK.md becomes a read-only generated view
4. **User Discipline:** Users edit Backlog tasks, not TASK.md directly

**Alternatives Considered:**
- **Bidirectional Sync:** Sync changes in both directions
  - Pros: User can edit TASK.md and have changes propagate
  - Cons: Conflict resolution complex, race conditions possible, unclear source of truth
  - Rejected: Too complex, defeats purpose of structured Backlog

- **Manual Sync Only:** No automation, user runs sync manually
  - Pros: User controls when sync happens
  - Cons: Requires discipline, easy to forget, TASK.md becomes stale
  - Rejected: Automation reduces friction

**Implementation:**
1. Create `scripts/backlog/sync_tasks.py` that reads Backlog tasks via MCP
2. Add sync zone comments to TASK.md (`<!-- BACKLOG_SYNC:CURRENT:BEGIN -->`)
3. Preserve TASK.md content outside sync zones
4. Optional: Install git pre-commit hook to auto-sync

**Impact:**
- TASK.md becomes auto-generated (sync zones only)
- Users edit Backlog task files (via MCP or file edit)
- Sync script must run after any Backlog changes
- Git hook can automate sync on commit

**Status:**
Accepted

**Related Decisions:**
- See `DECISIONS_LOG.md` entry: [2025-12-17] Backlog Setup Implementation
- Related to CLAUDE.md Rule 0 (Task Tracking)

---

## Template Fields Guide

### Context
- What situation requires a decision?
- What are the constraints?
- What data informed this decision?

### Decision
- Clear, actionable statement
- One-two sentences max
- No ambiguity

### Rationale
- Why this decision makes sense
- Data-driven reasoning
- Trade-offs considered

### Alternatives
- What other options existed?
- Why were they rejected?
- Document for future reference

### Implementation
- How will this be executed?
- What changes are needed?
- Who is responsible?

### Impact
- What is affected?
- Files, workflows, dependencies
- Future considerations

### Status
- **Accepted:** Decision approved and implemented
- **Rejected:** Decision not accepted
- **Superseded:** Replaced by later decision
- **Deprecated:** No longer recommended

---

**Last Updated:** 2025-12-17

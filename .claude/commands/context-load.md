# context-load

Loads all memory system files to resume work after context clear.

## Prompt

You are resuming work after a context clear. Read and summarize all 5 memory files to restore session context:

### Files to Read (in order)

1. **PROJECT_CONTEXT.md**
   - Read ONLY the newest entry (first entry after file header)
   - Extract: Project name, current phase, status, recent changes, blockers, next steps

2. **NEXT_ACTIONS.md**
   - Read CRITICAL and HIGH priority sections only
   - Extract: Top 3 immediate actions with their status

3. **DEVELOPMENT_LOG.md**
   - Read ONLY the most recent date section
   - Extract: What was built, what was changed, testing results

4. **ISSUES_LOG.md**
   - Read entries with status [OPEN] only
   - Extract: Active issues that need attention

5. **DECISIONS_LOG.md**
   - Read the 3 most recent decisions
   - Extract: What was decided and why

## Output Format

Provide a concise resume in this exact format:

```
# Session Resume [YYYY-MM-DD]

## Current Status
[From PROJECT_CONTEXT: phase, status, what's working]

## Immediate Tasks
1. [From NEXT_ACTIONS: highest priority task]
2. [From NEXT_ACTIONS: second priority task]
3. [From NEXT_ACTIONS: third priority task]

## Last Session Summary
[From DEVELOPMENT_LOG: brief summary of last activities]

## Open Issues
[From ISSUES_LOG: list of OPEN issues or "None"]

## Recent Decisions
[From DECISIONS_LOG: 1-2 most impactful recent decisions]

## Ready to Continue
[Yes/No - are there blockers?]
```

## Instructions

1. Read the 5 memory files in order (PROJECT_CONTEXT, NEXT_ACTIONS, DEVELOPMENT_LOG, ISSUES_LOG, DECISIONS_LOG)
2. Extract ONLY the most recent/relevant information from each
3. Use the exact output format specified above
4. Be concise - focus on actionable information
5. Identify any blockers that would prevent continuing work
6. Provide clear understanding of what to do next

## Success Criteria

After running this command:
- [ ] All 5 memory files read
- [ ] Context restored without reading entire files
- [ ] Only most recent/relevant information surfaced
- [ ] Clear understanding of what to do next
- [ ] User can immediately continue work

## Usage Notes

- Run this command at the start of a new session after `/context-clear`
- Expected completion time: 30-60 seconds
- Provides complete context to resume work
- Pairs with `/context-clear` for complete session management

## Example Output

```
# Session Resume 2025-12-05

## Current Status
**Project:** Agent Factory
**Phase:** Constitutional Code Generation Framework
**Status:** Phase 1 Foundation Complete - Ready for Demo

**What's Working:**
- factory.py: Spec parser extracting 53 requirements
- callbacks.py & orchestrator.py: Hybrid docs applied
- All core modules tested and importing
- Git checkpoint: 26276ca

## Immediate Tasks
1. [CRITICAL] Create orchestrator_demo.py - Validate implementation (30 min)
2. [HIGH] Write basic tests for callbacks/orchestrator (1 hour)
3. [MEDIUM] Run full integration demo

## Last Session Summary
Built constitutional code generation system with factory.py, applied hybrid documentation to core modules, created Jinja2 templates. All modules tested successfully.

## Open Issues
- Dependency conflict (LangChain vs LangGraph) - deferred

## Recent Decisions
- Hybrid documentation over full PLC-style (readable + traceable)
- Constitutional code generation approach (specs as source of truth)

## Ready to Continue
Yes - No blockers, ready to create demo
```

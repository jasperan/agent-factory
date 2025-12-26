# Start Few-Shot RAG Phase

Start implementing phase $ARGUMENTS of the Dynamic Few-Shot RAG system.

## Before Starting:

1. Read the master spec:
```bash
cat DYNAMIC_FEWSHOT_RAG_SPEC.md
```

2. Read the specific phase task file:
```bash
cat .claude/tasks/phase$ARGUMENTS-*.md
```

3. Study the GitHub repos listed in the task file BEFORE writing any code

4. Check PROJECT_TRACKER.md for any dependencies or blockers

## Constraints:

- Follow the task file instructions EXACTLY
- DO NOT skip ahead to other phases
- DO NOT modify files outside the allowed scope
- RUN TESTS after each deliverable
- UPDATE PROJECT_TRACKER.md after completing tasks
- STOP at checkpoints and wait for user approval

## Output Format:

After completing each task, report:
```
✅ Task X.Y: [task name]
   - Files created/modified: [list]
   - Tests: [pass/fail]
   - Notes: [any observations]
   
Next: Task X.Z or CHECKPOINT (awaiting approval)
```

## Phase Quick Reference:

- Phase 0: Case Collection (USER task - not Claude)
- Phase 1: Infrastructure - schemas, store, embedder
- Phase 2: Retrieval - retriever, formatter
- Phase 3: Integration - orchestrator modification (RESTRICTED)
- Phase 4: Feedback Loop - auto-capture system
- Phase 5: Forum Backfill - industrial data (SUPERVISED)

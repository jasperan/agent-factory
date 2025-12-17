---
id: task-23.2
title: 'BUILD: Headless Claude runner (AI Dev Loop 3/6)'
status: To Do
assignee: []
created_date: '2025-12-17 22:14'
labels:
  - build
  - ai-loop
  - orchestrator
  - claude
  - automation
dependencies:
  - task-23.2
parent_task_id: task-23
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement headless runner script that takes Backlog task ID, runs Claude to implement it, and updates status.

**Part of EPIC:** task-23 (AI Dev Control Loop Dashboard)  
**Dependencies:** task-23.2 (architecture document must exist first)

**Goal:** Core automation that executes tasks autonomously.

**Plan:**
1. Create scripts/autonomous/headless_runner.py that:
   - Accepts Backlog task ID via CLI arg or BACKLOG_TASK_ID env var
   - Calls 'backlog task <id> --plain' to read full task context
   - Builds Claude prompt from task (title, description, plan, AC) and repo context
   - Runs Claude headless (CLI or API) to:
     * Create git worktree/branch for task
     * Implement code/tests/docs according to task
     * Run tests/linters
     * Prepare commits and draft PR
   - Writes logs to logs/ai-dev-loop/
2. On start: Mark task In Progress via Backlog CLI
3. On completion:
   - Success: mark Done and attach PR link in task body
   - Failure: mark Blocked and store short reason
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Running 'BACKLOG_TASK_ID=<id> python scripts/autonomous/headless_runner.py' executes loop without manual intervention
- [ ] #2 On success: branch/worktree created, code/tests/docs changed, tests pass, draft PR exists, task status=Done
- [ ] #3 On failure: no changes reach main, task status=Blocked with explanation
<!-- AC:END -->

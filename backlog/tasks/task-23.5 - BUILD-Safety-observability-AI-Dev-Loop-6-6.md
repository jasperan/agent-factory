---
id: task-23.5
title: 'BUILD: Safety & observability (AI Dev Loop 6/6)'
status: To Do
assignee: []
created_date: '2025-12-17 22:17'
labels:
  - build
  - ai-loop
  - safety
  - observability
  - logging
dependencies: []
parent_task_id: task-23
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Prevent runaway loops and make debugging failures easy.

**Part of EPIC:** task-23 (AI Dev Control Loop Dashboard)

**Goal:** Add safety controls and logging to prevent runaway loops and enable debugging.

**Plan:**
1. Add safety controls to headless_runner.py:
   - Max runtime per task (e.g., 30 minutes)
   - Max token/cost per run (if supported by Claude API)
   - Allowed directories (no touching infra scripts, secrets)
2. Logging:
   - Log prompts, outputs (summarized), exit codes, timing to logs/ai-dev-loop/
   - Record short human-readable summary in Backlog task on completion
3. Optionally: Add last N runs view to UI for quick diagnosis
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Runs stop cleanly when limits are hit
- [ ] #2 Logs exist for successes and failures in logs/ai-dev-loop/
- [ ] #3 A human (or another agent) can read logs and understand why run failed
<!-- AC:END -->

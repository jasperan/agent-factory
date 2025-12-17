---
id: task-23.4
title: 'BUILD: Simple dashboard (React/Telegram) (AI Dev Loop 5/6)'
status: To Do
assignee: []
created_date: '2025-12-17 22:17'
labels:
  - build
  - ai-loop
  - ui
  - react
  - telegram
  - dashboard
dependencies: []
parent_task_id: task-23
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Provide minimal control UI to view tasks and trigger runs without opening CLI manually.

**Part of EPIC:** task-23 (AI Dev Control Loop Dashboard)

**Goal:** Build simple UI for viewing/triggering runs.

**Plan:**
1. Implement small service (Node/Express or Python/FastAPI) that:
   - Wraps Backlog commands (task list, task <id>, board export) into HTTP endpoints
   - Exposes endpoint to trigger headless_runner.py for given task ID
2. React UI:
   - Fetches task list and statuses
   - Shows simple Kanban or table
   - Has Run with Claude button per task
3. Telegram bot:
   - /board → sends Markdown version of board  
   - /run_task <id> → triggers headless_runner.py and returns status
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 React UI can list tasks and trigger at least one successful headless run
- [ ] #2 Telegram bot can show board snapshot and trigger run via /run_task <id>
- [ ] #3 Both UIs stay in sync with Backlog statuses
<!-- AC:END -->

---
id: task-24.4
title: 'BUILD: Create migration script for existing tasks'
status: To Do
assignee: []
created_date: '2025-12-18 00:07'
labels:
  - build
  - backlog
  - migration
dependencies:
  - task-24.1
parent_task_id: task-24
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create script to tag existing manual tasks with user-action label. Estimated Time: 15 minutes
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 scripts/backlog/migrate_user_actions.py created
- [ ] #2 Scans for manual task keywords
- [ ] #3 Supports --dry-run preview
- [ ] #4 Confirms before applying changes
<!-- AC:END -->

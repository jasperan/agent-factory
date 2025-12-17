---
id: task-23
title: 'BUILD: AI Dev Control Loop Dashboard'
status: To Do
assignee: []
created_date: '2025-12-17 22:13'
labels:
  - build
  - ai-loop
  - dashboard
  - orchestrator
  - claude
  - backlog
  - epic
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Build an AI-first development control loop that uses Backlog.md tasks as the source of truth, and headless Claude/agents as the execution engine, to automatically implement features, tests, and docs from a Kanban board.

This loop should let a user:
- Capture ideas and specs as structured Backlog tasks
- See those tasks on a Kanban board (Backlog.md + optional React/Telegram UI)
- Trigger headless Claude runs that take a task, create a git worktree/branch, implement the changes, run tests, and open a draft PR
- Update Backlog task status (To Do → In Progress → Done / Blocked) automatically based on the run result
- Be resilient against upstream changes by forking/vendoring Backlog.md into the user's own GitHub account

The goal is to make the control loop reliable enough that it can be reused across projects and eventually productized as a sellable "AI Dev Control Room."

**EPIC:** This task has 6 child subtasks (task-24.1 through task-24.6) covering:
1. Fork and vendor Backlog.md (safety)
2. Define AI Dev Loop architecture (documentation)
3. Headless Claude runner implementation (core automation)
4. Backlog status + Kanban sync (integration)
5. Simple dashboard UI (React/Telegram)
6. Safety & observability (limits, logging)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A Backlog task can be run end-to-end by the loop to produce a draft PR
- [ ] #2 Task statuses correctly transition To Do → In Progress → Done/Blocked
- [ ] #3 The architecture and behavior are documented and understandable
- [ ] #4 The pattern is reusable on another repo with minimal changes
- [ ] #5 All 6 child tasks completed (task-24.1 through task-24.6)
<!-- AC:END -->

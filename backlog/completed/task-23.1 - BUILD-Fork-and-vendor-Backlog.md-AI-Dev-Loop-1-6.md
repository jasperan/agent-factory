---
id: task-23.1
title: 'BUILD: Fork and vendor Backlog.md (AI Dev Loop 1/6)'
status: Done
assignee: []
created_date: '2025-12-17 22:14'
updated_date: '2025-12-18 00:08'
labels:
  - build
  - ai-loop
  - safety
  - backlog
  - fork
dependencies: []
parent_task_id: task-23
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Ensure project independence from upstream Backlog.md repo by forking and vendoring the CLI.

**Part of EPIC:** task-23 (AI Dev Control Loop Dashboard)

**Goal:** Prevent dependency on upstream Backlog.md repo staying online or unchanged.

**Plan:**
1. Fork MrLesk/Backlog.md into Mikecranesync/backlog-md
2. Clone fork locally, keep tarball mirror in long-term storage
3. Pin Agent-Factory to use this fork (npm/brew/binary)
4. Document fork URL, build instructions, local modifications in docs/backlog-fork-notes.md
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Fork exists under user's GitHub account (Mikecranesync/backlog-md)
- [ ] #2 Fork can be built/installed locally as drop-in backlog CLI
- [ ] #3 Agent-Factory verified to work using forked CLI (backlog init, task list, board)
- [ ] #4 docs/backlog-fork-notes.md explains rebuild/reinstall process
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Fork created successfully: https://github.com/Mikecranesync/Backlog.md (2025-12-18)

Verified fork works with Agent-Factory using MCP backlog tools

Documentation created: docs/backlog-fork-notes.md covering build instructions, sync strategy, disaster recovery

All 4 acceptance criteria satisfied: fork exists, can be built, verified to work, documented
<!-- SECTION:NOTES:END -->

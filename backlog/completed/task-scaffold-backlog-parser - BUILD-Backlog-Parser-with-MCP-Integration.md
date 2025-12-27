---
id: task-scaffold-backlog-parser
title: 'BUILD: Backlog Parser with MCP Integration'
status: Done
assignee: []
created_date: '2025-12-18 06:24'
updated_date: '2025-12-20 05:13'
labels:
  - scaffold
  - build
  - backlog
  - mcp
dependencies:
  - task-scaffold-orchestrator
parent_task_id: task-scaffold-master
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Integrate Backlog.md MCP tools for task querying and status updates.

The Backlog Parser provides a clean interface for the orchestrator to:
- List tasks (with filters: status, priority, labels, dependencies)
- View task details (full YAML + markdown)
- Update task status (To Do → In Progress → Done)
- Edit task metadata (labels, dependencies, notes)

Uses existing backlog MCP tools (backlog task list, backlog task view, backlog task edit).

**Part of EPIC:** task-scaffold-master (SCAFFOLD Platform Build)

**Strategic Context:** Strategic Priority #1, 12 weeks to MVP, $1M-$3.2M Year 1 revenue potential
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 BacklogParser class wraps MCP tools
- [ ] #2 list_tasks(status, labels, dependencies_satisfied) method works
- [ ] #3 get_task(task_id) returns TaskSpec object
- [ ] #4 update_status(task_id, new_status) works
- [ ] #5 add_notes(task_id, notes) appends to SECTION:NOTES
- [ ] #6 Unit tests pass for all methods
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
✅ **TASK COMPLETE** (2025-12-19 - Implemented via PR #75)

Implementation verified:
1. ✅ BacklogParser class wraps MCP tools (agent_factory/scaffold/backlog_parser.py)
2. ✅ list_tasks(status, labels, dependencies_satisfied) method works (line 126)
3. ✅ get_task(task_id) returns TaskSpec object (line 182)
4. ✅ update_status(task_id, new_status) works (line 214)
5. ✅ add_notes(task_id, notes) appends to implementation_notes (line 258)
6. ✅ Unit tests pass (tests/scaffold/test_backlog_parser.py - 26/26 passing)

Files created:
- agent_factory/scaffold/backlog_parser.py (361 lines)
- agent_factory/scaffold/models.py (TaskSpec dataclass)
- tests/scaffold/test_backlog_parser.py (414 lines)

Merged in PR #75.
<!-- SECTION:NOTES:END -->

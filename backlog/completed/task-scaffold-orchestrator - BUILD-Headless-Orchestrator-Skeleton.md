---
id: task-scaffold-orchestrator
title: 'BUILD: Headless Orchestrator Skeleton'
status: Done
assignee: []
created_date: '2025-12-18 06:24'
updated_date: '2025-12-20 05:55'
labels:
  - scaffold
  - build
  - orchestration
  - autonomous
dependencies: []
parent_task_id: task-scaffold-master
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Build the main orchestration loop for autonomous task execution.

The orchestrator reads tasks from Backlog.md via MCP, routes to appropriate agents (Claude Code CLI or custom), manages execution in isolated git worktrees, and updates task status after completion.

Key components:
- TaskFetcher: Query Backlog.md for eligible tasks (status=To Do, dependencies satisfied)
- AgentRouter: Match task to agent (explicit label, title prefix, domain, default)
- SessionManager: Track active sessions, enforce concurrency limits
- ResultProcessor: Create PRs on success, update Backlog.md, log failures

This is the foundation for the entire SCAFFOLD platform.

**Part of EPIC:** task-scaffold-master (SCAFFOLD Platform Build)

**Strategic Context:** Strategic Priority #1, 12 weeks to MVP, $1M-$3.2M Year 1 revenue potential
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Orchestrator class exists with main() entry point
- [ ] #2 TaskFetcher queries Backlog.md via MCP (backlog task list)
- [ ] #3 AgentRouter routes tasks based on labels/title/domain
- [ ] #4 SessionManager tracks active worktrees and budgets
- [ ] #5 ResultProcessor updates Backlog.md after task completion
- [ ] #6 Command: poetry run python scripts/autonomous/scaffold_orchestrator.py works
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Generated from SCAFFOLD Master Orchestration Prompt (2025-12-18)

This task was auto-imported using semantic ID mapping to avoid conflicts with existing tasks.

✅ **TASK COMPLETE** (2025-12-20 - Already implemented via PR #75)

Implementation verified:
1. ✅ Orchestrator class exists with main() entry point (agent_factory/scaffold/orchestrator.py:33)
2. ✅ TaskFetcher queries Backlog.md via MCP (agent_factory/scaffold/task_fetcher.py)
3. ✅ AgentRouter routes tasks based on labels/title/domain (agent_factory/scaffold/task_router.py)
4. ✅ SessionManager tracks active worktrees and budgets (agent_factory/scaffold/session_manager.py)
5. ✅ ResultProcessor updates Backlog.md after task completion (agent_factory/scaffold/result_processor.py)
6. ✅ Command works: poetry run python scripts/autonomous/scaffold_orchestrator.py --dry-run

Files created:
- agent_factory/scaffold/orchestrator.py (396 lines)
- agent_factory/scaffold/task_fetcher.py (167 lines)
- agent_factory/scaffold/task_router.py (269 lines)
- agent_factory/scaffold/session_manager.py (352 lines)
- agent_factory/scaffold/result_processor.py (245 lines)
- scripts/autonomous/scaffold_orchestrator.py (229 lines - CLI entry point)

Features:
- Main orchestration loop with run() method
- Dry-run mode for testing
- Safety limits: max_tasks, max_concurrent, max_cost, max_time_hours
- Component integration: TaskFetcher → TaskRouter → SessionManager → ResultProcessor
- CLI with argparse (--dry-run, --max-tasks, --labels)

Tested successfully with: poetry run python scripts/autonomous/scaffold_orchestrator.py --dry-run --max-tasks 3
<!-- SECTION:NOTES:END -->

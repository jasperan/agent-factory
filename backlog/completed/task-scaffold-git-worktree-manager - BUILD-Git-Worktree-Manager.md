---
id: task-scaffold-git-worktree-manager
title: 'BUILD: Git Worktree Manager'
status: Done
assignee: []
created_date: '2025-12-18 06:24'
updated_date: '2025-12-20 05:56'
labels:
  - scaffold
  - build
  - git
  - worktree
dependencies:
  - task-scaffold-orchestrator
parent_task_id: task-scaffold-master
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Manage isolated git worktrees for parallel task execution.

The Worktree Manager creates and cleans up dedicated worktrees for each task:
- Creates worktree in ../agent-factory-{task-id}/ on branch autonomous/{task-id}
- Tracks active worktrees (prevents duplicates, enforces limits)
- Cleans up after PR creation (removes worktree, deletes branch if merged)
- Handles errors (removes corrupted worktrees)

This enables parallel execution of multiple tasks without conflicts.

**Part of EPIC:** task-scaffold-master (SCAFFOLD Platform Build)

**Strategic Context:** Strategic Priority #1, 12 weeks to MVP, $1M-$3.2M Year 1 revenue potential
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 WorktreeManager class with create_worktree(task_id) method
- [ ] #2 Creates worktree: git worktree add ../agent-factory-{id} -b autonomous/{id}
- [ ] #3 Tracks active worktrees in memory (dict or database)
- [ ] #4 Prevents duplicate worktrees for same task
- [ ] #5 Enforces max_concurrent_worktrees limit (default: 3)
- [ ] #6 cleanup_worktree(task_id) removes worktree and deletes branch
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Generated from SCAFFOLD Master Orchestration Prompt (2025-12-18)

This task was auto-imported using semantic ID mapping to avoid conflicts with existing tasks.

✅ **TASK COMPLETE** (2025-12-20 - Already implemented via PR #75)

Implementation verified:
1. ✅ WorktreeManager class with create_worktree(task_id) method (agent_factory/scaffold/worktree_manager.py:77)
2. ✅ Creates worktree at ../agent-factory-{id} on branch autonomous/{id} (line 82)
3. ✅ Tracks active worktrees in .scaffold/worktrees.json (line 75, uses WorktreeMetadata)
4. ✅ Prevents duplicate worktrees for same task (lines 104-108, raises WorktreeExistsError)
5. ✅ Enforces max_concurrent_worktrees limit (default: 3) (lines 111-119, raises WorktreeLimitError)
6. ✅ cleanup_worktree(task_id) removes worktree and deletes branch (line 172)

Files created:
- agent_factory/scaffold/worktree_manager.py (267 lines)
- agent_factory/scaffold/models.py (includes WorktreeMetadata dataclass)

Features:
- Isolated worktree creation at ../agent-factory-{task-id}/
- Branch naming: autonomous/{task-id}
- Metadata persistence to .scaffold/worktrees.json
- Duplicate prevention (WorktreeExistsError)
- Concurrency limit enforcement (WorktreeLimitError)
- Cleanup with force option for error handling
- Integration with SessionManager for session-level tracking

Used by SessionManager (agent_factory/scaffold/session_manager.py:80) for worktree lifecycle management.
<!-- SECTION:NOTES:END -->

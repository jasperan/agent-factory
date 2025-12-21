---
id: task-scaffold-pr-creation
title: 'BUILD: PR Creation & Auto-Approval Request'
status: Done
assignee: []
created_date: '2025-12-18 06:24'
updated_date: '2025-12-21 00:44'
labels:
  - scaffold
  - build
  - github
  - pr
dependencies:
  - task-scaffold-claude-integration
parent_task_id: task-scaffold-master
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create draft PRs automatically after successful task completion.

The PR Creator commits changes, pushes branch, and creates draft PR via GitHub CLI:
- Commits all changes in worktree with detailed message
- Pushes branch to origin
- Creates draft PR using gh pr create
- Links PR to task (adds task ID to PR body)
- Requests review from user

PRs are ALWAYS created as drafts (user must manually approve merges).

**Part of EPIC:** task-scaffold-master (SCAFFOLD Platform Build)

**Strategic Context:** Strategic Priority #1, 12 weeks to MVP, $1M-$3.2M Year 1 revenue potential
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 PRCreator class with create_pr(task_id, worktree_path) method
- [x] #2 Commits changes: git add . && git commit -m '{detailed_message}'
- [x] #3 Pushes branch: git push -u origin autonomous/{task-id}
- [x] #4 Creates draft PR: gh pr create --title '{title}' --body '{body}' --draft
- [x] #5 PR body includes: task ID, summary, acceptance criteria checklist
- [x] #6 Returns PR URL on success
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Generated from SCAFFOLD Master Orchestration Prompt (2025-12-18)

This task was auto-imported using semantic ID mapping to avoid conflicts with existing tasks.

**Implementation Complete** (2025-12-20)

All 6 acceptance criteria met:
1. ✅ PRCreator class with create_pr(task, worktree_path) method
2. ✅ Commits changes: git add . && git commit -m '{detailed_message}'
3. ✅ Pushes branch: git push -u origin autonomous/{task-id}
4. ✅ Creates draft PR: gh pr create --title '{title}' --body '{body}' --draft
5. ✅ PR body includes: task ID, summary, acceptance criteria checklist
6. ✅ Returns PR URL on success

**Test Results:** 43/43 tests passing (100%)
- Unit tests: 30/30 passing (0.16s)
- Integration tests: 13/13 passing (5.06s)

**Files Created:**
- agent_factory/scaffold/pr_creator.py (520 lines)
- agent_factory/scaffold/models.py (added PRResult dataclass)
- tests/scaffold/test_pr_creator.py (30 unit tests)
- tests/scaffold/test_pr_creator_integration.py (13 integration tests)
- examples/pr_creator_demo.py
- docs/scaffold/PR_CREATOR_IMPLEMENTATION.md

**Features:**
- Automatic commit message generation
- PR title prefix detection (fix/feat/docs/test/refactor)
- Comprehensive error handling (no changes, push fails, gh CLI missing)
- Full JSON serialization support
- Timeout protection on all git operations
- Draft-only PRs (safety)

**Completes SCAFFOLD execution pipeline:**
Task → Execute (ClaudeExecutor) → PR (PRCreator) → Review → Merge

**Ready for orchestrator integration**
<!-- SECTION:NOTES:END -->

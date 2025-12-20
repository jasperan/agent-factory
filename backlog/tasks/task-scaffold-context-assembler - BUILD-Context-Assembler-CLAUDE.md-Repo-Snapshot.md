---
id: task-scaffold-context-assembler
title: 'BUILD: Context Assembler (CLAUDE.md + Repo Snapshot)'
status: Done
assignee: []
created_date: '2025-12-18 06:24'
updated_date: '2025-12-20 05:28'
labels:
  - scaffold
  - build
  - context
  - claude
dependencies:
  - task-scaffold-backlog-parser
parent_task_id: task-scaffold-master
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Assemble context for Claude Code CLI execution.

The Context Assembler prepares the execution environment for each task:
- Reads CLAUDE.md system prompts
- Generates repo snapshot (file tree, recent commits, key files)
- Formats task specification (title, description, acceptance criteria)
- Creates execution prompt template
- Packages context for Claude Code CLI invocation

This ensures Claude has full context for autonomous task execution.

**Part of EPIC:** task-scaffold-master (SCAFFOLD Platform Build)

**Strategic Context:** Strategic Priority #1, 12 weeks to MVP, $1M-$3.2M Year 1 revenue potential
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 ContextAssembler class with assemble_context(task_id) method
- [ ] #2 Reads CLAUDE.md and extracts system prompts
- [ ] #3 Generates file tree snapshot (max depth 3, excludes node_modules)
- [ ] #4 Extracts last 10 commits from git log
- [ ] #5 Formats task spec as markdown
- [ ] #6 Returns complete context string ready for Claude Code CLI
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Generated from SCAFFOLD Master Orchestration Prompt (2025-12-18)

This task was auto-imported using semantic ID mapping to avoid conflicts with existing tasks.

✅ **TASK COMPLETE** (2025-12-20)

Implementation verified:
1. ✅ ContextAssembler class with assemble_context(task, worktree_path) method (agent_factory/scaffold/context_assembler.py:27)
2. ✅ Reads CLAUDE.md and extracts system prompts (_read_claude_md method, lines 124-160)
3. ✅ Generates file tree snapshot with max depth 3, excludes node_modules (_generate_file_tree, lines 162-186)
4. ✅ Extracts last 10 commits from git log (_extract_git_commits, lines 219-242)
5. ✅ Formats task spec as markdown (_format_task_spec, lines 244-276)
6. ✅ Returns complete context string ready for Claude Code CLI (assemble_context, lines 65-122)

Files created:
- agent_factory/scaffold/context_assembler.py (302 lines)
- tests/scaffold/test_context_assembler.py (365 lines, 22/22 tests passing)

Features:
- CLAUDE.md reader with 200-line truncation
- File tree generator with tree command + fallback to os.walk
- Git commit history extraction (last 10 commits)
- Task spec formatter with acceptance criteria
- Complete context template for Claude Code CLI

Next task: task-scaffold-orchestrator (Orchestrator Main Loop)
<!-- SECTION:NOTES:END -->

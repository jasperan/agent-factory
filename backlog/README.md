# Backlog.md Workflow Guide

Complete guide to task management with Backlog.md in Agent Factory.

---

## Table of Contents

1. [Overview](#overview)
2. [When to Use Backlog.md vs TASK.md](#when-to-use-backlogmd-vs-taskmd)
3. [Task Lifecycle](#task-lifecycle)
4. [YAML Frontmatter Reference](#yaml-frontmatter-reference)
5. [Creating Tasks](#creating-tasks)
6. [Task Organization](#task-organization)
7. [Parent-Child Relationships](#parent-child-relationships)
8. [Labels, Priorities, and Dependencies](#labels-priorities-and-dependencies)
9. [MCP Tool Usage](#mcp-tool-usage)
10. [Integration with CLAUDE.md](#integration-with-claudemd)
11. [Automation Scripts](#automation-scripts)
12. [Best Practices](#best-practices)
13. [FAQ](#faq)

---

## Overview

**Backlog.md** is a task management system designed for Agent Factory development. It provides:
- **Structured task tracking** with YAML frontmatter + Markdown
- **MCP integration** for programmatic task access
- **Parent-child relationships** for breaking down large features
- **Automatic syncing** to TASK.md for Claude Code integration
- **Task templates** for consistent task creation

**Key Principle:** Backlog.md is the **source of truth** for all tasks. TASK.md is auto-generated from Backlog data.

---

## When to Use Backlog.md vs TASK.md

### Use Backlog.md When:
- ✅ **Creating new tasks** - Use MCP tools or CLI wizard
- ✅ **Breaking down features** - Create parent task + subtasks
- ✅ **Tracking multiple workstreams** - Organize by labels/priorities
- ✅ **Planning sprints** - Filter by priority/labels
- ✅ **Documenting acceptance criteria** - Detailed checklists
- ✅ **Managing long-term backlog** - 20+ tasks

### Use TASK.md When:
- 📋 **Quick reference** - See current task at a glance
- 📋 **Claude Code context** - Auto-loaded by CLAUDE.md Rule 0
- 📋 **High-level status** - What's in progress vs backlog

**TL;DR:** Create/edit tasks in **Backlog.md**. Read current status from **TASK.md** (auto-synced).

---

## Task Lifecycle

Tasks flow through these states:

```
To Do → In Progress → Done → Archived/Completed
```

### States Explained

1. **To Do** (default)
   - Task created but not started
   - Appears in TASK.md "Backlog" section
   - Sorted by priority (high → medium → low)

2. **In Progress**
   - Task currently being worked on
   - Appears in TASK.md "Current Task" section
   - **Important:** Only 1-2 tasks should be "In Progress" at a time

3. **Done**
   - Task completed, acceptance criteria met
   - Ready to archive
   - Run: `python scripts/backlog/archive_task.py task-X` to move to `backlog/completed/`

4. **Archived/Completed**
   - Moved from `backlog/tasks/` to `backlog/completed/`
   - Preserved for history, no longer in active backlog
   - Can still be queried via MCP tools

### Transitioning States

**Manual (MCP Tools):**
```python
# Via Backlog.md MCP
backlog task edit task-4 --status "In Progress"
backlog task edit task-4 --status "Done"
```

**Manual (File Edit):**
Edit task file YAML frontmatter:
```yaml
status: "In Progress"  # or "Done"
updated_date: '2025-12-17 18:30'  # Update timestamp
```

**Automated (Sync Script):**
```bash
# After updating task status, sync to TASK.md
poetry run python scripts/backlog/sync_tasks.py
```

---

## YAML Frontmatter Reference

Every task file starts with YAML frontmatter enclosed in `---` markers:

```yaml
---
id: task-4
title: 'BUILD: RIVET Pro Phase 4 - Orchestrator'
status: To Do
assignee: []
created_date: '2025-12-17 15:30'
updated_date: '2025-12-17 16:45'
labels:
  - build
  - rivet-pro
  - orchestrator
dependencies: []
parent_task_id: null
priority: high
---
```

### Field Descriptions

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `id` | string | ✅ Yes | Unique task identifier | `task-4` or `task-3.2` |
| `title` | string | ✅ Yes | Task title with ACTION prefix | `BUILD: RIVET Pro Phase 4` |
| `status` | string | ✅ Yes | Current state | `To Do`, `In Progress`, `Done` |
| `assignee` | list | No | Assigned users (empty for solo projects) | `[]` or `['claude']` |
| `created_date` | string | ✅ Yes | ISO timestamp when created | `'2025-12-17 15:30'` |
| `updated_date` | string | No | ISO timestamp when last edited | `'2025-12-17 16:45'` |
| `labels` | list | No | Categorization tags | `['build', 'rivet-pro']` |
| `dependencies` | list | No | Tasks that must complete first | `['task-3']` |
| `parent_task_id` | string | No | Parent task (for subtasks only) | `task-3` or `null` |
| `priority` | string | ✅ Yes | Urgency level | `high`, `medium`, `low` |

### Valid Status Values
- `To Do` - Default, not started
- `In Progress` - Currently working
- `Done` - Completed

**Note:** Status values are case-sensitive and must match exactly.

### Valid Priority Values
- `high` - Critical path, blocking other work
- `medium` - Important but not urgent
- `low` - Nice-to-have, backlog

---

## Creating Tasks

### Method 1: Using MCP Tools (Recommended)

```python
# Via Backlog.md MCP
backlog task create \
  --title "BUILD: New Feature Name" \
  --priority high \
  --labels build,rivet-pro \
  --description "Detailed task description..." \
  --acceptance-criteria "[ ] Criterion 1" "[ ] Criterion 2"
```

### Method 2: Using CLI Wizard (Coming Soon)

```bash
poetry run python scripts/backlog/create_task_from_template.py

# Interactive prompts:
# 1. Select action type: BUILD/FIX/TEST/CLEANUP/AUDIT
# 2. Enter title: RIVET Pro Phase 5
# 3. Select priority: high/medium/low
# 4. Add labels (comma-separated): build,rivet-pro,research
# 5. Task created as task-24.md
```

### Method 3: Manual File Creation

1. **Create file:** `backlog/tasks/task-24 - BUILD-New-Feature.md`

2. **Add YAML frontmatter:**
```yaml
---
id: task-24
title: 'BUILD: New Feature Name'
status: To Do
assignee: []
created_date: '2025-12-17 18:00'
labels:
  - build
  - rivet-pro
dependencies: []
parent_task_id: null
priority: high
---
```

3. **Add description:**
```markdown
## Description

[Detailed explanation of what needs to be built...]

## Context

[Why this task is needed, background information...]

## Acceptance Criteria

<!-- AC:BEGIN -->
- [ ] #1 First criterion - specific, measurable
- [ ] #2 Second criterion - testable
- [ ] #3 Third criterion - clear definition of done
<!-- AC:END -->

## Notes

[Additional implementation notes, references, links...]
```

4. **Save and validate:**
```bash
poetry run python scripts/backlog/validate_tasks.py task-24
```

### File Naming Convention

**Format:** `task-{number} - {ACTION}-{Short-Description}.md`

**Examples:**
- `task-4 - BUILD-RIVET-Pro-Phase4-Orchestrator.md`
- `task-14 - FIX-pgvector-Extension-PostgreSQL-18.md`
- `task-19 - TEST-Memory-Storage-Backend-Tests.md`
- `task-17 - CLEANUP-Update-PROJECT_STRUCTURE-md.md`

**ACTION Prefixes:**
- `BUILD` - New features, implementations
- `FIX` - Bug fixes, issues
- `TEST` - Test coverage, validation
- `CLEANUP` - Documentation, refactoring
- `AUDIT` - Inventory, analysis

---

## Task Organization

### By Action Type

Tasks are categorized by action prefix in the title:

- **BUILD (11 tasks):** RIVET Pro Phases 3-8, PLC Tutor, YouTube automation, Voice clone, Curriculum, Hybrid search
- **FIX (3 tasks):** pgvector extension, Telegram admin panel, pytest slow execution
- **CLEANUP (2 tasks):** PROJECT_STRUCTURE.md, architecture docs accuracy
- **TEST (5 tasks):** Memory backends, Telegram handlers, autonomous system, ingestion chain, agent integration

### By Priority

**High Priority (Critical Path):**
- RIVET Pro Phases 3-8
- PLC Tutor Multi-Agent Orchestration
- YouTube Automation Pipeline
- Telegram Admin Real Data Integration

**Medium Priority:**
- Hybrid Search Implementation
- Voice Clone Setup
- Testing Infrastructure

**Low Priority:**
- Documentation updates
- Architecture audits

### By Labels

Common label combinations:

- `build` + `rivet-pro` - RIVET Pro development
- `build` + `plc-tutor` - PLC Tutor features
- `test` + `coverage` - Test infrastructure
- `cleanup` + `documentation` - Documentation work
- `fix` + `database` - Database issues

### Directory Structure

```
backlog/
├── tasks/                    # Active tasks (To Do, In Progress)
│   ├── task-1.md
│   ├── task-2.md
│   ├── task-3.md            # Parent task (EPIC)
│   ├── task-3.1.md          # Child task
│   ├── task-3.2.md          # Child task
│   └── ...
├── completed/               # Archived completed tasks (Done)
│   └── (moved here after archiving)
├── drafts/                  # Work-in-progress task ideas
├── decisions/               # Links to DECISIONS_LOG.md entries
└── docs/                    # Testing checklists, guides
```

---

## Parent-Child Relationships

Use parent-child relationships to break down large features (EPICs) into smaller tasks.

### Example: RIVET Pro Phase 3 (SME Agents)

**Parent Task:** `task-3` - RIVET Pro Phase 3 - SME Agents (EPIC)
```yaml
---
id: task-3
title: 'BUILD: RIVET Pro Phase 3 - SME Agents (EPIC)'
status: Done
parent_task_id: null
priority: high
---
```

**Child Tasks:**
- `task-3.1` - Siemens Agent (parent: task-3)
- `task-3.2` - Rockwell Agent (parent: task-3)
- `task-3.3` - Generic PLC Agent (parent: task-3)
- `task-3.4` - Safety Agent (parent: task-3)
- `task-3.5` - RAG Integration Layer (parent: task-3)
- `task-3.6` - SME Agents Testing (parent: task-3)

**Child Task YAML:**
```yaml
---
id: task-3.1
title: 'BUILD: RIVET Pro Phase 3.1 - Siemens Agent'
status: Done
parent_task_id: task-3  # Links to parent EPIC
priority: high
---
```

### Creating Child Tasks

**Via MCP:**
```python
backlog task create \
  --title "BUILD: Subtask Name" \
  --parent-task-id task-3 \
  --priority high
```

**Manual File Creation:**
1. Create file: `task-3.7 - BUILD-New-Subtask.md`
2. Set `parent_task_id: task-3` in YAML
3. Use same priority as parent (usually)

### Archiving Parent Tasks

When archiving a parent task with children:

```bash
# Archive parent + all children
poetry run python scripts/backlog/archive_task.py task-3 --include-children

# Archive parent only (leaves children active)
poetry run python scripts/backlog/archive_task.py task-3
```

---

## Labels, Priorities, and Dependencies

### Labels

Labels categorize tasks for filtering and organization.

**Common Label Patterns:**

**By Action:**
- `build`, `fix`, `test`, `cleanup`, `audit`

**By Feature Area:**
- `rivet-pro`, `plc-tutor`, `youtube`, `telegram`, `orchestrator`

**By Domain:**
- `agents`, `siemens`, `rockwell`, `safety`, `database`

**By Scope:**
- `coverage`, `ingestion`, `documentation`, `integration`

**Example:**
```yaml
labels:
  - build          # Action type
  - rivet-pro      # Feature area
  - orchestrator   # Specific component
```

### Priorities

Set priority based on:
- **high:** Critical path, blocks other work, must complete soon
- **medium:** Important but not urgent, can be scheduled
- **low:** Nice-to-have, backlog, low impact

**Example Decision Flow:**
1. Does this block other work? → **high**
2. Is this on the critical path to production? → **high**
3. Is this a quick win (low effort, high impact)? → **medium**
4. Is this documentation or cleanup? → **low**

### Dependencies

Use dependencies to express task ordering constraints.

**Example:**
```yaml
# task-4 depends on task-3 completing first
dependencies:
  - task-3
```

**Validation:**
The validation script checks that:
- Dependency task IDs exist
- No circular dependencies (task-4 → task-5 → task-4)
- Dependencies are marked "Done" before dependent task marked "In Progress"

**Usage:**
```bash
# Check dependencies before starting task
poetry run python scripts/backlog/validate_tasks.py task-4
```

---

## MCP Tool Usage

Backlog.md integrates with the **Backlog.md MCP server** for programmatic task access.

### Available MCP Tools

**Create Task:**
```python
mcp__backlog__task_create(
    title="BUILD: New Feature",
    description="Detailed description...",
    priority="high",
    labels=["build", "rivet-pro"],
    acceptance_criteria=["Criterion 1", "Criterion 2"],
    parent_task_id=None
)
```

**List Tasks:**
```python
# All tasks
mcp__backlog__task_list()

# Filter by status
mcp__backlog__task_list(status="In Progress")

# Filter by labels
mcp__backlog__task_list(labels=["build", "rivet-pro"])

# Limit results
mcp__backlog__task_list(limit=10)
```

**View Task:**
```python
mcp__backlog__task_view(id="task-4")
```

**Edit Task:**
```python
mcp__backlog__task_edit(
    id="task-4",
    status="In Progress",
    labels=["build", "rivet-pro", "in-review"]
)
```

**Search Tasks:**
```python
mcp__backlog__task_search(
    query="RIVET Pro",
    status="To Do",
    priority="high"
)
```

**Archive Task:**
```python
mcp__backlog__task_archive(id="task-3")
```

### MCP Resources

The Backlog.md MCP server also provides resources:

**Workflow Overview:**
```
backlog://workflow/overview
```

**Task Creation Guide:**
```
backlog://guides/task-creation
```

**Task Execution Guide:**
```
backlog://guides/task-execution
```

**Task Completion Guide:**
```
backlog://guides/task-completion
```

---

## Integration with CLAUDE.md

The project's `CLAUDE.md` file (Rule 0: Task Tracking) defines the workflow integration:

### Rule 0: Task Tracking

**Before starting ANY task:**
1. ✅ **Check TASK.md** - See what's in progress and backlog
2. ✅ **Update status** - Mark task as "In Progress" when you start
3. ✅ **Mark complete** - Update status to "Done" immediately after finishing
4. ✅ **Add discovered work** - New tasks found during implementation go to "Discovered During Work" section

### Workflow Pattern

**1. Session Start:**
```bash
# Read current status
cat TASK.md

# Or use MCP
backlog task list --status "In Progress"
```

**2. Start Task:**
```python
# Update task status
backlog task edit task-4 --status "In Progress"

# Sync to TASK.md
poetry run python scripts/backlog/sync_tasks.py
```

**3. During Work:**
- Add notes to task file under "## Notes" section
- Update acceptance criteria checkboxes
- Create new tasks for discovered work

**4. Complete Task:**
```python
# Mark task done
backlog task edit task-4 --status "Done"

# Update acceptance criteria (all checked)
backlog task edit task-4 \
  --acceptance-criteria-check 1 \
  --acceptance-criteria-check 2 \
  --acceptance-criteria-check 3

# Sync to TASK.md
poetry run python scripts/backlog/sync_tasks.py
```

**5. Archive Task:**
```bash
# Move to completed/
poetry run python scripts/backlog/archive_task.py task-4
```

### Auto-Sync with Git Hooks (Optional)

Install pre-commit hook to auto-sync TASK.md:

```bash
poetry run python scripts/backlog/install_git_hooks.py

# Hook runs on every commit:
# 1. Syncs Backlog → TASK.md
# 2. Warns if TASK.md out of sync
# 3. User can commit anyway or cancel to fix
```

---

## Automation Scripts

All automation scripts located in `scripts/backlog/`:

### 1. Sync Tasks (Backlog → TASK.md)

**Purpose:** Generate TASK.md from Backlog tasks (one-way sync)

```bash
# Dry run (preview changes)
poetry run python scripts/backlog/sync_tasks.py --dry-run

# Sync both sections
poetry run python scripts/backlog/sync_tasks.py

# Sync only "Current Task" section
poetry run python scripts/backlog/sync_tasks.py --section current

# Force sync (ignore warnings)
poetry run python scripts/backlog/sync_tasks.py --force
```

### 2. Create Task from Template

**Purpose:** Interactive CLI wizard for task creation

```bash
poetry run python scripts/backlog/create_task_from_template.py

# Prompts:
# 1. Select action type: [BUILD, FIX, TEST, CLEANUP, AUDIT]
# 2. Enter title: "RIVET Pro Phase 5"
# 3. Select priority: [high, medium, low]
# 4. Add labels (comma-separated): "build,rivet-pro,research"
# 5. Add description: "..."
# 6. Task created as task-24.md
```

### 3. Archive Task

**Purpose:** Move completed tasks to `backlog/completed/`

```bash
# Archive single task
poetry run python scripts/backlog/archive_task.py task-4

# Archive task + all child tasks
poetry run python scripts/backlog/archive_task.py task-3 --include-children

# Dry run (preview what would be archived)
poetry run python scripts/backlog/archive_task.py task-4 --dry-run
```

### 4. Validate Tasks

**Purpose:** Check task consistency (YAML valid, dependencies exist, etc.)

```bash
# Validate all tasks
poetry run python scripts/backlog/validate_tasks.py

# Validate specific task
poetry run python scripts/backlog/validate_tasks.py task-4

# Validate with detailed output
poetry run python scripts/backlog/validate_tasks.py --verbose
```

### 5. Bulk Operations

**Purpose:** Batch update multiple tasks

```bash
# Update statuses
poetry run python scripts/backlog/bulk_operations.py \
  --status "In Progress" task-4 task-5 task-6

# Add labels
poetry run python scripts/backlog/bulk_operations.py \
  --add-labels in-review task-4 task-5

# Remove labels
poetry run python scripts/backlog/bulk_operations.py \
  --remove-labels blocked task-7

# Change priorities
poetry run python scripts/backlog/bulk_operations.py \
  --priority medium task-8 task-9
```

### 6. Install Git Hooks

**Purpose:** Setup optional pre-commit hook for auto-sync

```bash
# Install hook
poetry run python scripts/backlog/install_git_hooks.py

# Uninstall hook
poetry run python scripts/backlog/install_git_hooks.py --uninstall

# Hook behavior on commit:
# - Runs sync_tasks.py --dry-run
# - Warns if TASK.md out of sync
# - User can continue commit or cancel to sync first
```

---

## Best Practices

### 1. Keep One Task "In Progress"
- Focus on completing tasks before starting new ones
- Avoid work-in-progress sprawl
- Use TASK.md "Current Task" section as your north star

### 2. Write Clear Acceptance Criteria
- Specific, measurable, testable
- Use checkboxes for tracking progress
- Each criterion should define "done"

**Good:**
```markdown
- [ ] #1 Sync script reads all Backlog tasks using MCP tools
- [ ] #2 TASK.md "Current Task" section updated from "In Progress" tasks
- [ ] #3 Unit tests pass with 90%+ coverage
```

**Bad:**
```markdown
- [ ] Make it work
- [ ] Test stuff
- [ ] Documentation
```

### 3. Use Parent-Child for Large Features
- Create EPIC parent task for multi-step features
- Break into 3-6 child tasks
- Mark parent "Done" only when all children complete

### 4. Archive Completed Tasks Regularly
- Keeps active backlog focused
- Preserves history in `backlog/completed/`
- Run weekly: `poetry run python scripts/backlog/archive_task.py --all-done`

### 5. Validate Before Committing
```bash
# Check task validity
poetry run python scripts/backlog/validate_tasks.py

# Sync to TASK.md
poetry run python scripts/backlog/sync_tasks.py

# Commit
git add . && git commit -m "feat: Complete task-4"
```

### 6. Use Labels for Filtering
- Apply consistent labels
- Use labels for sprint planning (filter by label + priority)
- Combine labels for powerful queries

### 7. Keep TASK.md Auto-Generated
- Don't manually edit TASK.md sync zones
- Make changes in Backlog task files
- Run sync script to propagate changes

---

## FAQ

### Q: Can I edit TASK.md directly?
**A:** Yes, but only outside sync zones (marked with `<!-- BACKLOG_SYNC:... -->` comments). Changes inside sync zones will be overwritten by the next sync.

### Q: How do I see all tasks?
**A:** `backlog task list` (MCP) or `ls backlog/tasks/` (filesystem)

### Q: What happens if I delete a task file?
**A:** Task disappears from Backlog and TASK.md (after sync). If you need to recover, check git history.

### Q: Can I have multiple "In Progress" tasks?
**A:** Technically yes, but **not recommended**. Focus on 1-2 tasks max for better throughput.

### Q: How do I change task priority?
**A:** Edit task file YAML (`priority: high`) or use MCP (`backlog task edit task-4 --priority high`)

### Q: What if dependency task isn't done yet?
**A:** Validation script warns you. Finish dependency first or remove the dependency constraint.

### Q: How do I create a subtask?
**A:** Set `parent_task_id: task-X` in child task YAML frontmatter

### Q: Can I use Backlog.md without MCP?
**A:** Yes, all operations work via file editing. MCP tools are a convenience layer.

### Q: How do I search tasks?
**A:** `backlog task search --query "RIVET"` (MCP) or `grep -r "RIVET" backlog/tasks/` (shell)

### Q: What if sync script fails?
**A:** Run with `--dry-run` first to preview changes. Check validation output. Report errors as GitHub issues.

### Q: Can I customize templates?
**A:** Yes, edit files in `backlog/templates/`. CLI wizard uses these as starting points.

### Q: How do I bulk update tasks?
**A:** `poetry run python scripts/backlog/bulk_operations.py --status "Done" task-4 task-5 task-6`

---

## Quick Reference

### Common Commands

```bash
# View current tasks
backlog task list --status "In Progress"

# Create task
backlog task create --title "BUILD: Feature" --priority high

# Update status
backlog task edit task-4 --status "In Progress"

# Sync to TASK.md
poetry run python scripts/backlog/sync_tasks.py

# Validate tasks
poetry run python scripts/backlog/validate_tasks.py

# Archive completed
poetry run python scripts/backlog/archive_task.py task-4
```

### File Locations

- **Active tasks:** `backlog/tasks/`
- **Completed tasks:** `backlog/completed/`
- **Templates:** `backlog/templates/`
- **Scripts:** `scripts/backlog/`
- **Configuration:** `backlog/config.yml`
- **Auto-generated:** `TASK.md` (root)

### Key Files

- `CLAUDE.md` - Rule 0 defines task workflow
- `TASK.md` - Auto-generated from Backlog (read-only sync zones)
- `backlog/config.yml` - Project settings
- `backlog/README.md` - This guide

---

## Support

For issues, questions, or suggestions:
- **GitHub Issues:** https://github.com/Mikecranesync/Agent-Factory/issues
- **Documentation:** This file (backlog/README.md)
- **MCP Guides:** `backlog://workflow/overview` (via MCP resources)

---

**Last Updated:** 2025-12-17
**Version:** 1.0.0
**Maintained by:** Agent Factory Team

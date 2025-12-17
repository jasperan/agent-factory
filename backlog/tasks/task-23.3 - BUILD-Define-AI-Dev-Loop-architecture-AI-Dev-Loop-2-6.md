---
id: task-23.3
title: 'BUILD: Define AI Dev Loop architecture (AI Dev Loop 2/6)'
status: To Do
assignee: []
created_date: '2025-12-17 22:17'
labels:
  - build
  - ai-loop
  - architecture
  - documentation
dependencies: []
parent_task_id: task-23
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create comprehensive architecture document describing all control loop components.

**Part of EPIC:** task-23 (AI Dev Control Loop Dashboard)

**Goal:** Produce a clear architecture document so humans and agents can reason about the system.

**Plan:**
1. Write docs/ai-dev-loop-architecture.md covering:
   - Backlog.md: task format, Kanban, instructions files (CLAUDE.md, AGENTS.md)
   - Headless orchestrator: task consumption and Claude/agent invocation
   - Claude/agents: prompts, roles, safety limits, tool access
   - Git worktree/branch strategy and PR flow
   - Optional UI layers: React dashboard, Telegram bot
2. Include sequence diagrams (text or Mermaid) showing:
   - Task → Orchestrator → Claude → PR → Backlog update
   - User clicks Run in UI → Headless loop executes task
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 docs/ai-dev-loop-architecture.md exists with all major components described
- [ ] #2 Diagrams (text or Mermaid) cover main E2E loop
- [ ] #3 Another developer/agent can read doc and understand adding new task type/repo
<!-- AC:END -->

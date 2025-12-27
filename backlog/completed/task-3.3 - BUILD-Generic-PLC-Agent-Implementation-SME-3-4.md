---
id: task-3.3
title: 'BUILD: Generic PLC Agent Implementation (SME 3/4)'
status: Done
assignee: []
created_date: '2025-12-17 07:50'
updated_date: '2025-12-17 13:11'
labels:
  - build
  - rivet-pro
  - agents
  - generic
dependencies: []
parent_task_id: task-3
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement Generic PLC Subject Matter Expert agent for RIVET Pro. This agent serves as fallback when vendor is unknown or for vendor-agnostic PLC questions. Covers universal PLC concepts (I/O, ladder logic, timers, counters, troubleshooting fundamentals).

**File to create:** `agent_factory/rivet_pro/agents/generic_agent.py`

**Part of EPIC:** task-3 (RIVET Pro Phase 3 - SME Agents)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 GenericPLCAgent class created inheriting from base SME agent structure
- [ ] #2 System prompt covers universal PLC concepts (digital/analog I/O, ladder logic, function blocks, timers, counters)
- [ ] #3 Handles vendor-agnostic queries (basic troubleshooting, general programming concepts)
- [ ] #4 Response includes disclaimer when vendor-specific features are mentioned
- [ ] #5 Unit tests pass for generic PLC scenarios (minimum 5 test cases)
- [ ] #6 Gracefully routes to 'need clarification' when vendor context is critical
<!-- AC:END -->

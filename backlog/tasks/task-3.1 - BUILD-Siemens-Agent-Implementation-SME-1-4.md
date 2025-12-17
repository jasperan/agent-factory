---
id: task-3.1
title: 'BUILD: Siemens Agent Implementation (SME 1/4)'
status: Done
assignee: []
created_date: '2025-12-17 07:50'
updated_date: '2025-12-17 13:11'
labels:
  - build
  - rivet-pro
  - agents
  - siemens
dependencies: []
parent_task_id: task-3
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement Siemens Subject Matter Expert agent for RIVET Pro. This agent handles queries about Siemens PLCs (SINAMICS drives, MICROMASTER frequency converters, TIA Portal software). Provides vendor-specific troubleshooting and configuration guidance.

**File to create:** `agent_factory/rivet_pro/agents/siemens_agent.py`

**Part of EPIC:** task-3 (RIVET Pro Phase 3 - SME Agents)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 SiemensAgent class created inheriting from base SME agent structure
- [ ] #2 System prompt includes Siemens-specific terminology (SINAMICS, MICROMASTER, TIA Portal, S7-1200, S7-1500)
- [ ] #3 Handles Siemens-specific queries (drive fault codes, parameter P0xxxx settings, communication protocols)
- [ ] #4 Response format matches RivetResponse schema from Phase 1
- [ ] #5 Unit tests pass for Siemens-specific scenarios (minimum 5 test cases)
- [ ] #6 Agent documentation includes 3+ example queries and expected responses
<!-- AC:END -->

---
id: task-3.4
title: 'BUILD: Safety Agent Implementation (SME 4/4)'
status: Done
assignee: []
created_date: '2025-12-17 07:50'
updated_date: '2025-12-17 13:11'
labels:
  - build
  - rivet-pro
  - agents
  - safety
dependencies: []
parent_task_id: task-3
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement Safety Subject Matter Expert agent for RIVET Pro. This agent validates safety PLC configurations against IEC 61508/61511 standards. Checks SIL ratings, safety relay configurations, and critical safety violations.

**File to create:** `agent_factory/rivet_pro/agents/safety_agent.py`

**Part of EPIC:** task-3 (RIVET Pro Phase 3 - SME Agents)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 SafetyAgent class created inheriting from base SME agent structure
- [ ] #2 System prompt includes IEC 61508/61511 safety standards and SIL rating definitions
- [ ] #3 Validates SIL ratings (SIL1, SIL2, SIL3) based on application requirements
- [ ] #4 Checks safety relay configurations for compliance
- [ ] #5 Provides clear warnings for critical safety violations or non-compliant configurations
- [ ] #6 Unit tests pass for safety compliance scenarios (minimum 5 test cases including edge cases)
<!-- AC:END -->

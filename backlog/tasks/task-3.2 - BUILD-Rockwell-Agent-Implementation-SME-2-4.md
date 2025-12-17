---
id: task-3.2
title: 'BUILD: Rockwell Agent Implementation (SME 2/4)'
status: Done
assignee: []
created_date: '2025-12-17 07:50'
updated_date: '2025-12-17 13:11'
labels:
  - build
  - rivet-pro
  - agents
  - rockwell
dependencies: []
parent_task_id: task-3
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement Rockwell Automation Subject Matter Expert agent for RIVET Pro. This agent specializes in Allen-Bradley PLCs (ControlLogix, CompactLogix, Studio 5000/RSLogix 5000). Provides guidance on tag-based programming, AOIs, and ladder logic troubleshooting.

**File to create:** `agent_factory/rivet_pro/agents/rockwell_agent.py`

**Part of EPIC:** task-3 (RIVET Pro Phase 3 - SME Agents)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 RockwellAgent class created inheriting from base SME agent structure
- [ ] #2 System prompt includes Rockwell terminology (ControlLogix, CompactLogix, Studio 5000, RSLogix, tag addressing)
- [ ] #3 Handles Rockwell-specific queries (AOI development, tag structures, FactoryTalk integration, fault codes)
- [ ] #4 Response format matches RivetResponse schema from Phase 1
- [ ] #5 Unit tests pass for Rockwell-specific scenarios (minimum 5 test cases)
- [ ] #6 Agent documentation includes 3+ example queries and expected responses
<!-- AC:END -->

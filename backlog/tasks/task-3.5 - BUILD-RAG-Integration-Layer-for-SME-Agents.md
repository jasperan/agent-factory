---
id: task-3.5
title: 'BUILD: RAG Integration Layer for SME Agents'
status: Done
assignee: []
created_date: '2025-12-17 07:50'
updated_date: '2025-12-17 13:11'
labels:
  - build
  - rivet-pro
  - agents
  - rag-integration
dependencies:
  - task-3.1
  - task-3.2
  - task-3.3
  - task-3.4
parent_task_id: task-3
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Integrate all 4 SME agents with Phase 2 RAG layer for vendor-specific knowledge retrieval. Implements vendor filtering, KB coverage estimation, and fallback logic when knowledge is insufficient.

**Files to create/modify:**
- `agent_factory/rivet_pro/agents/base_sme_agent.py` (base class for all SME agents)
- Integration code in each agent file

**Part of EPIC:** task-3 (RIVET Pro Phase 3 - SME Agents)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Each agent queries RAG layer using search_docs() from Phase 2
- [ ] #2 Vendor filters applied correctly (Siemens → vendor=siemens, Rockwell → vendor=rockwell_automation)
- [ ] #3 KB coverage estimation integrated via estimate_coverage() function
- [ ] #4 Agents fallback to GenericPLCAgent or 'need clarification' when coverage is 'none'
- [ ] #5 Integration tests pass for RAG queries across all 4 agents
- [ ] #6 Response citations include KB source references with proper attribution
<!-- AC:END -->

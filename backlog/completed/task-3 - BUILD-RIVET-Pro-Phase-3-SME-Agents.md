---
id: task-3
title: 'BUILD: RIVET Pro Phase 3 - SME Agents'
status: Done
assignee: []
created_date: '2025-12-17 07:31'
updated_date: '2025-12-17 13:11'
labels:
  - build
  - rivet-pro
  - agents
  - epic
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**EPIC: RIVET Pro Phase 3 - SME Agents**

This is an EPIC task that has been split into 6 child tasks for parallel development:

- **task-3.1:** Siemens Agent Implementation (SME 1/4)
- **task-3.2:** Rockwell Agent Implementation (SME 2/4)
- **task-3.3:** Generic PLC Agent Implementation (SME 3/4)
- **task-3.4:** Safety Agent Implementation (SME 4/4)
- **task-3.5:** RAG Integration Layer for SME Agents
- **task-3.6:** SME Agents Testing & Validation

---

## EPIC Completion Criteria

✅ **This EPIC is complete when ALL 6 child tasks are marked as "Done".**

---

## Original Description

Implement 4 Subject Matter Expert agents for RIVET Pro industrial maintenance assistant. Includes:

1. **Siemens agent** (SINAMICS/MICROMASTER drives, TIA Portal)
2. **Rockwell agent** (ControlLogix/CompactLogix, Studio 5000)
3. **Generic PLC agent** (fallback for unknown vendors)
4. **Safety agent** (SIL/safety relays, IEC 61508/61511)

The agents integrate with the existing RAG layer (Phase 2) for vendor-specific knowledge retrieval.

---

## Dependencies

**Phase 2 RAG layer must be complete** before child tasks can begin.

---

## Development Approach

- **Tasks 3.1-3.4** can be developed in parallel (4 independent agents)
- **Task 3.5** integrates all agents with RAG layer (depends on 3.1-3.4)
- **Task 3.6** validates the complete system (depends on 3.1-3.5)

**Estimated Timeline:** 4.5-5.5 hours (sequential) or 3-4 hours (parallel development)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Siemens agent implemented with vendor-specific knowledge retrieval
- [ ] #2 Rockwell agent implemented with ControlLogix/CompactLogix support
- [ ] #3 Generic PLC fallback agent handles unknown vendors
- [ ] #4 Safety agent validates SIL compliance and safety relay configurations
- [ ] #5 All 4 agents integrate with existing RAG layer (Phase 2)
- [ ] #6 Tests pass for each agent (mock responses, KB queries)
<!-- AC:END -->

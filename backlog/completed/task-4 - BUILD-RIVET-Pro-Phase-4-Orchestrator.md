---
id: task-4
title: 'BUILD: RIVET Pro Phase 4 - Orchestrator'
status: Done
assignee: []
created_date: '2025-12-17 07:31'
updated_date: '2025-12-17 23:06'
labels:
  - build
  - rivet-pro
  - orchestrator
dependencies: []
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Build 4-route orchestrator for RIVET Pro that routes queries based on KB coverage. Routes: A (Strong KB → Direct SME), B (Thin KB → SME + enrichment), C (No KB → Research), D (Unclear → Clarification). Routes to correct SME agent based on vendor detection.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Orchestrator routes to correct SME agent based on vendor detection
- [ ] #2 Route A (Strong KB) returns direct answers with citations
- [ ] #3 Route B (Thin KB) triggers enrichment pipeline
- [ ] #4 Route C (No KB) triggers research pipeline (Phase 5)
- [ ] #5 Route D (Unclear) requests user clarification
- [ ] #6 Integration tests cover all 4 routes with realistic queries
<!-- AC:END -->

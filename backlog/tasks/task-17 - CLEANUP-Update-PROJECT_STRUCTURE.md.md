---
id: task-17
title: 'CLEANUP: Update PROJECT_STRUCTURE.md'
status: To Do
assignee: []
created_date: '2025-12-17 07:34'
labels:
  - cleanup
  - documentation
dependencies: []
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
PROJECT_STRUCTURE.md outdated - shows /agents/ (259 files) but core framework is /agent_factory/ (128 files). Structure changed during development. Update to reflect current organization.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Distinguish /agent_factory/ (128 core framework files) from /agents/ (259 agent implementations)
- [ ] #2 Update file counts in all sections
- [ ] #3 Add /agent_factory/ section with subdirectories (core, memory, integrations, workflows, observability, rivet_pro)
- [ ] #4 Clarify /agents/ is separate from /agent_factory/
- [ ] #5 Update Last Updated timestamp
- [ ] #6 Verify directory structure matches actual repo (ls -R comparison)
<!-- AC:END -->

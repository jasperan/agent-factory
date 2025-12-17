---
id: task-16
title: 'FIX: pytest Slow Execution Investigation'
status: To Do
assignee: []
created_date: '2025-12-17 07:34'
labels:
  - fix
  - testing
  - performance
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
pytest appears to hang or run very slowly (timeout after 5 seconds). Possible causes: database connection timeouts, LLM API calls in tests, missing test configuration.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Identify tests causing slowdowns (run with -v -s flags)
- [ ] #2 Mock database connections in tests (use pytest fixtures)
- [ ] #3 Mock LLM API calls (use responses or vcr.py)
- [ ] #4 Add pytest.ini configuration (timeouts, markers)
- [ ] #5 Document test execution best practices
- [ ] #6 All tests run in <10 seconds total
<!-- AC:END -->

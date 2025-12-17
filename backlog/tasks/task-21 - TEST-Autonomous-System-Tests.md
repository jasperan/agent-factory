---
id: task-21
title: 'TEST: Autonomous System Tests'
status: To Do
assignee: []
created_date: '2025-12-17 07:34'
labels:
  - test
  - coverage
  - autonomous
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add tests for autonomous nighttime issue solver components. Test issue_queue_builder, safety_monitor, telegram_notifier with mock data.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Test IssueQueueBuilder with mock GitHub issues (hybrid scoring)
- [ ] #2 Test SafetyMonitor limits (cost, time, failure thresholds)
- [ ] #3 Test TelegramNotifier with mock Telegram API
- [ ] #4 Test autonomous_claude_runner orchestration flow
- [ ] #5 Test ClaudeExecutor with mock GitHub Actions API
- [ ] #6 Test PRCreator with mock GitHub API
- [ ] #7 All autonomous components covered with 85%+ coverage
<!-- AC:END -->

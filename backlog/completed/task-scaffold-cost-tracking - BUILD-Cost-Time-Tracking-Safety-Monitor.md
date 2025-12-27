---
id: task-scaffold-cost-tracking
title: 'BUILD: Cost & Time Tracking (Safety Monitor)'
status: Done
assignee: []
created_date: '2025-12-18 06:24'
updated_date: '2025-12-20 06:37'
labels:
  - scaffold
  - build
  - safety
  - monitoring
dependencies:
  - task-scaffold-orchestrator
parent_task_id: task-scaffold-master
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Track API costs and execution time with circuit breakers.

The Safety Monitor enforces hard limits to prevent runaway costs:
- Tracks total cost (API calls to Claude)
- Tracks elapsed time (session duration)
- Tracks consecutive failures (circuit breaker)
- Checks limits before each task execution
- Aborts session if limits exceeded

Safety limits (configurable):
- max_cost: $5 (default)
- max_time_hours: 4 (default)
- max_consecutive_failures: 3 (default)

**Part of EPIC:** task-scaffold-master (SCAFFOLD Platform Build)

**Strategic Context:** Strategic Priority #1, 12 weeks to MVP, $1M-$3.2M Year 1 revenue potential
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 SafetyMonitor class with check_limits() method
- [ ] #2 Tracks total_cost, elapsed_time, consecutive_failures
- [ ] #3 check_limits() returns (allowed, reason) tuple
- [ ] #4 Aborts if total_cost >= max_cost
- [ ] #5 Aborts if elapsed_time >= max_time_hours
- [ ] #6 Aborts if consecutive_failures >= max_consecutive_failures
- [ ] #7 Resets consecutive_failures on task success
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Complete (2025-12-20)

All 7 acceptance criteria met:

1. ✅ **SafetyMonitor class with check_limits() method** - SafetyMonitor class in agent_factory/scaffold/safety_monitor.py
2. ✅ **Tracks total_cost, elapsed_time, consecutive_failures** - SafetyState dataclass with tracking
3. ✅ **check_limits() returns (allowed, reason) tuple** - Returns True/False with reason string
4. ✅ **Aborts if total_cost >= max_cost** - Cost limit enforcement ($5 default)
5. ✅ **Aborts if elapsed_time >= max_time_hours** - Time limit enforcement (4h default)
6. ✅ **Aborts if consecutive_failures >= max_consecutive_failures** - Circuit breaker (3 failures default)
7. ✅ **Resets consecutive_failures on task success** - record_success() resets counter

## Files Created

- `agent_factory/scaffold/safety_monitor.py` (160 lines)
  - SafetyMonitor class with check_limits() method
  - SafetyLimits and SafetyState dataclasses
  - Methods: check_limits(), record_cost(), record_success(), record_failure()
  - Helper methods: get_state_summary(), get_limits_summary(), get_remaining_budget()
  - Circuit breaker behavior with automatic reset on success

- `tests/scaffold/test_safety_monitor.py` (390 lines)
  - 36 comprehensive tests covering all functionality
  - Test categories: SafetyLimits, SafetyState, initialization, check_limits, cost tracking, success/failure recording, circuit breaker, integration
  - All tests passing (36/36)

## Implementation Details

**Safety Limits (Configurable):**
- `max_cost`: Maximum total cost in USD (default: $5.00)
- `max_time_hours`: Maximum session duration in hours (default: 4.0)
- `max_consecutive_failures`: Maximum consecutive task failures before circuit breaker trips (default: 3)

**Tracking:**
- `total_cost`: Accumulates costs from all tasks
- `elapsed_time`: Calculated from session start_time
- `consecutive_failures`: Increments on failure, resets to 0 on success

**Circuit Breaker:**
- Trips after N consecutive failures (default: 3)
- Prevents infinite loops when tasks consistently fail
- Resets automatically on first successful task execution
- Separate from total failures count

**Usage Example:**
```python
monitor = SafetyMonitor(max_cost=5.0, max_time_hours=4.0, max_consecutive_failures=3)

# Before each task
allowed, reason = monitor.check_limits()
if not allowed:
    print(f"Session aborted: {reason}")
    break

# After task execution
if task_succeeded:
    monitor.record_success(cost=0.25)
else:
    monitor.record_failure()

# Check remaining budget
budget = monitor.get_remaining_budget()
print(f"Remaining: ${budget['remaining_cost']:.2f}, {budget['remaining_hours']:.2f}h")
```
<!-- SECTION:NOTES:END -->

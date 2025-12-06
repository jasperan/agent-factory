# NEXT ACTIONS

**Last Updated:** 2025-12-06
**Current Phase:** Phase 2 Complete
**Next Phase:** Phase 3 - Spec → Agent Generation Pipeline

## Immediate Actions (Today)

1. ✅ Update PROGRESS.md with Phase 2 completion
2. ✅ Update memory files (PROJECT_CONTEXT, NEXT_ACTIONS, DEVELOPMENT_LOG)
3. 🔄 Commit memory file updates
4. 🔄 Push all changes to GitHub

## Phase 3 Planning (Dec 13-15, 2025)

### Goals
Build the `factory.py` command-line tool that generates agents from spec files.

### Tasks
1. Create `factory.py` CLI with commands:
   - `factory.py build <agent-name>` - Generate from spec
   - `factory.py validate <spec-file>` - Validate spec format
   - `factory.py eval <agent-name>` - Run evaluation tests

2. Implement spec parser:
   - Read markdown spec files
   - Extract structured sections (Purpose, Scope, Invariants, etc.)
   - Validate completeness against Article II requirements

3. Implement code generator:
   - Generate LangGraph workflow from spec
   - Assign tools based on "Tools Required"
   - Create Pydantic schemas from "Data Models"

4. Implement eval generator:
   - Generate test cases from "Behavior Examples"
   - Create anti-sycophancy tests
   - Generate performance benchmarks

5. Testing:
   - Create sample spec file
   - Generate agent from spec
   - Verify generated agent passes all evals

## Future Phases

- **Phase 4 (Dec 16-18):** Claude SDK Workers
- **Phase 5 (Dec 19-22):** Evaluation System
- **Phase 6 (Dec 23-Jan 5):** Google ADK Integration
- **Phase 7 (Jan 6-15):** Computer Use Integration
- **Phase 8 (Jan 16-30):** Niche Dominator Swarm

## Blocked/Waiting

None currently.

## Notes

- All 162 tests passing - no regressions
- Phase 0-2 completed ahead of schedule (2 phases in 3 hours vs 5 days budgeted)
- OpenHands integration working before Dec 15 deadline
- 40% comment density achieved per Article IV

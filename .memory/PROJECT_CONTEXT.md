# PROJECT CONTEXT

**Project:** Agent Factory
**Status:** Active Development
**Current Phase:** Phase 2 Complete - PLC-Style Heavy Commenting
**Next Phase:** Phase 3 - Spec → Agent Generation Pipeline
**Last Updated:** 2025-12-06

## Overview

Agent Factory creates reliable, repeatable, production-ready AI agents through **specification-first development**. Following "The New Code" philosophy from Sean Grove's AI Engineer World's Fair 2025 talk.

**Core Principle:** Specifications are eternal, code is ephemeral.

## Architecture

```
AGENTS.md (Constitution - Source of Truth)
    ↓
Spec Files (specs/*.md) - Versioned, debated
    ↓
Generated Code (agent_factory/) - Regenerable
    ↓
Tests (from specs) - Auto-generated
    ↓
Deployments (ephemeral)
```

## Technology Stack

- **Python 3.11+** with Poetry for dependency management
- **LangChain** for agent framework
- **Pydantic** for data validation
- **Pytest** for testing (162 tests passing)
- **LangGraph** for orchestration (planned)
- **Google ADK** for production deployment (planned)
- **OpenHands** for autonomous coding (integrated)

## Key Files

- `AGENTS.md` - Constitution (655 lines, 10 Articles)
- `specs/template.md` - Spec template (450+ lines)
- `agent_factory/core/orchestrator.py` - Multi-agent routing (924 lines)
- `agent_factory/core/callbacks.py` - Event system (642 lines)
- `agent_factory/workers/openhands_worker.py` - Autonomous coding (580 lines)
- `agent_factory/refs/project_twin.py` - Digital codebase mirror

## Current Statistics

- **162 tests** passing (all green)
- **40% comment density** achieved (Article IV requirement)
- **$200/month saved** (OpenHands integration vs Claude Code)
- **82 files** tracked by Digital Twin
- **107 classes, 413 functions** analyzed

## Recent Achievements

1. **Phase 0 (Dec 6):** OpenHands integration - avoided $200/mo fee
2. **Phase 1 (Dec 6):** AGENTS.md constitution created
3. **Phase 2 (Dec 6):** PLC-style heavy commenting (40% density)
4. **Phase 5 (Dec 5):** Project Twin digital mirror complete
5. **Phases 1-4 (Dec 5):** Orchestration, schemas, observability, tools

## Git Status

- **Current branch:** main
- **Latest commit:** f3bbb8d (Phase 2 complete)
- **Ahead of origin:** 7 commits

## Next Steps

See NEXT_ACTIONS.md for immediate tasks.

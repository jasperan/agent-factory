# Changelog

All notable changes to Agent Factory will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Week 1 - Foundation (In Progress)
- Infrastructure setup (voice training, Supabase, API keys)
- First 10 knowledge atoms (manual creation)
- Week 1 complete checklist tracking (Issue #49)

### Week 2 - Agent Development (Planned)
- Research Agent implementation (Issue #47)
- Scriptwriter Agent implementation (Issue #48)
- Atom Builder Agent integration

### Week 3 - Video Production (Planned)
- Voice Production Agent (ElevenLabs)
- Video Assembly Agent (MoviePy + FFmpeg)
- Thumbnail Agent (DALLE/Canva)
- YouTube Uploader Agent

---

## [0.2.0] - 2025-12-10 - Triune Moonshot Integration

### Added
- **Complete Strategy Suite** (142KB documentation)
  - `TRIUNE_STRATEGY.md` (32KB) - Master integration document
  - `YOUTUBE_WIKI_STRATEGY.md` (17KB) - YouTube-first content approach
  - `AGENT_ORGANIZATION.md` (26KB) - 18 autonomous agents with specs
  - `IMPLEMENTATION_ROADMAP.md` (22KB) - Week-by-week plan (12 weeks)
  - `CONTENT_ROADMAP_AtoZ.md` (24KB) - 100+ video topics sequenced
  - `ATOM_SPEC_UNIVERSAL.md` (21KB) - Universal knowledge atom schema

- **Production Pydantic Models** (`core/models.py`, 600+ lines)
  - `LearningObject` - IEEE LOM base class
  - `PLCAtom` - PLC/automation knowledge atoms
  - `RIVETAtom` - Industrial maintenance atoms
  - `Module` & `Course` - Curriculum organization
  - `VideoScript` & `UploadJob` - Content production
  - `AgentMessage` & `AgentStatus` - Inter-agent communication
  - All models with Pydantic v2 validation + examples

- **Validation Test Suite** (`test_models.py`)
  - Tests for all 6 model types
  - Sample data fixtures
  - 100% pass rate

- **GitHub Issues for Week 1**
  - Issue #44: Infrastructure setup & voice training (CRITICAL)
  - Issue #45: Create first 10 knowledge atoms (HIGH)
  - Issue #46: Implement Pydantic models (COMPLETED)
  - Issue #47: Build Research Agent (Week 2)
  - Issue #48: Build Scriptwriter Agent (Week 2)
  - Issue #49: Week 1 Complete Checklist (TRACKING)

- **Documentation Updates**
  - `README.md` - Complete overhaul for triune vision
  - `CLAUDE.md` - YouTube-Wiki strategy integration
  - `TASK.md` - Week 1 priorities and tracking
  - `CONTRIBUTING.md` - Comprehensive contribution guidelines

### Changed
- Project scope expanded from simple agent framework to **autonomous content production engine**
- Repository now clearly communicates:
  - PLC Tutor / Industrial Skills Hub (education vertical)
  - RIVET (industrial maintenance vertical)
  - 18-agent autonomous system
  - YouTube-wiki approach (teach to build knowledge base)
  - Voice clone for 24/7 production
  - Multi-stream monetization ($5M ARR Year 3 target)

### Technical Details
- Pydantic v2 with full validation
- IEEE LOM-compliant knowledge atoms
- JSON-LD 1.1 + Schema.org compatibility
- Supabase + pgvector schema defined
- Security-first architecture (enterprise-grade)

### Metrics
- 7 strategy documents (142KB)
- 600+ lines of production models
- 100+ planned video topics
- 18 planned autonomous agents
- 12-week implementation timeline

---

## [0.1.0] - 2025-12-09 - Production Patterns Integration

### Added
- **Settings Service** (database-backed configuration)
  - Runtime config changes without code deployment
  - Environment variable fallback (works without database)
  - Type-safe helpers (get_int, get_bool, get_float)
  - Category organization (llm, memory, orchestration)
  - 5-minute cache with auto-reload
  - Pattern from Archon (13.4k⭐) by Cole Medin

- **Supabase Memory Storage**
  - Fast persistent storage (60-120x faster than file-based)
  - PostgreSQL + pgvector for vector search
  - HNSW indexes (< 100ms search)
  - 3 storage backends: InMemory, SQLite, Supabase
  - Unified API across all backends

- **Research Documentation**
  - `cole_medin_patterns.md` (6,000+ words) - 9 production patterns
  - `archon_architecture_analysis.md` (7,000+ words) - Microservices deep dive
  - `integration_recommendations.md` (8,000+ words) - Prioritized roadmap

- **Validation Commands**
  - `poetry run python -c "from agent_factory.core.settings_service import settings; print(settings)"`
  - `poetry run python examples/settings_demo.py`
  - `poetry run python test_memory_consolidated.py`

### Fixed
- Memory system consolidation (resolved import conflicts)
- SupabaseMemoryStorage upsert constraint issue (delete-then-insert pattern)
- ContextManager test assertions
- 6/6 memory tests passing

### Changed
- Memory API now has clear, working interface
- Settings-driven features enable A/B testing
- Hybrid search ready (SQL migration included)

### Documentation
- Added examples: `settings_demo.py`, `memory_demo.py`
- Updated CLAUDE.md with Settings Service section
- Created TASK.md for active task tracking

---

## [0.0.1] - 2025-12-03 - Initial Release

### Added
- **Core Agent Factory**
  - `AgentFactory` class for dynamic agent creation
  - Support for OpenAI, Anthropic (Claude), Google (Gemini) LLMs
  - Pluggable tool system
  - Tool registry for centralized management
  - LCEL-based composition

- **Pre-configured Agents**
  - Research Agent (Wikipedia, DuckDuckGo, Tavily search)
  - Coding Agent (file operations, Git integration)

- **Tools**
  - Research Tools: Wikipedia, DuckDuckGo, Tavily, CurrentTime
  - Coding Tools: ReadFile, WriteFile, ListDirectory, FileSearch, GitStatus

- **Memory Management**
  - Conversation memory for multi-turn interactions
  - In-memory storage backend

- **Examples & Documentation**
  - `agent_factory/examples/demo.py` - Demonstration scripts
  - `README.md` - Installation and usage guide
  - `POETRY_GUIDE.md` - Poetry 2.x migration guide
  - `.env.example` - Environment template

### Technical Details
- Python 3.10+ support
- Poetry for dependency management
- LangChain framework integration
- Type hints throughout codebase

---

## Version History Summary

| Version | Date | Key Features | Status |
|---------|------|--------------|--------|
| **0.2.0** | 2025-12-10 | Triune moonshot integration, 18-agent system, production models | **CURRENT** |
| **0.1.0** | 2025-12-09 | Settings service, Supabase memory, Cole Medin patterns | Released |
| **0.0.1** | 2025-12-03 | Initial agent factory, research/coding agents, tools | Released |

---

## Upcoming Releases

### [0.3.0] - Week 4 (Public Launch) - Target: 2025-12-31
- Voice clone validated (ElevenLabs Pro)
- First 3 videos published to YouTube
- Research Agent + Atom Builder operational
- Scriptwriter Agent generating scripts
- CTR > 2%, AVD > 40%, 100+ subscribers

### [0.4.0] - Week 8 (All Agents Operational) - Target: 2026-01-28
- All 18 agents implemented and tested
- End-to-end video production pipeline
- Human-in-loop approval UI
- Agent communication + monitoring
- 10+ videos published

### [0.5.0] - Week 12 (Autonomous Operations) - Target: 2026-02-25
- 30 videos published
- 1,000+ subscribers
- $500+ revenue (courses + ads)
- Agents 80% autonomous
- YouTube Partner Program applied

### [1.0.0] - Month 12 (Scale Achieved) - Target: 2026-12-10
- 100+ videos published
- 20,000+ subscribers
- $5,000/month revenue
- 100+ validated knowledge atoms
- Agents fully autonomous (99%)
- Multi-platform presence (TikTok, Instagram)

### [2.0.0] - Year 2 (RIVET Launch) - Target: 2027-12-10
- Industrial maintenance vertical operational
- Reddit monitoring + validation pipeline
- B2B integrations (CMMS platforms)
- $80K ARR (RIVET) + $35K ARR (PLC Tutor)

### [3.0.0] - Year 3 (DAAS) - Target: 2028-12-10
- Data-as-a-Service revenue stream
- Knowledge base licensing to enterprises
- $2.5M ARR (PLC Tutor) + $2.5M ARR (RIVET)
- Sustainable business achieved

---

## Release Guidelines

### Semantic Versioning

- **MAJOR** (X.0.0): Breaking changes, new verticals (RIVET launch)
- **MINOR** (0.X.0): New features, agents, milestones (Week 4, 8, 12)
- **PATCH** (0.0.X): Bug fixes, documentation updates, minor improvements

### Release Checklist

- [ ] Update version in `pyproject.toml`
- [ ] Update CHANGELOG.md with release notes
- [ ] Run full test suite (`poetry run pytest`)
- [ ] Validate models (`poetry run python test_models.py`)
- [ ] Update README.md if needed
- [ ] Create git tag (`git tag -a vX.Y.Z -m "Release vX.Y.Z"`)
- [ ] Push tag (`git push origin vX.Y.Z`)
- [ ] Create GitHub release with notes
- [ ] Update documentation site (if applicable)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Development workflow (git worktrees)
- Code standards (Python, Pydantic, testing)
- Pull request process
- Security requirements
- Bug reports and feature requests

---

## Links

- **Repository:** https://github.com/your-username/agent-factory
- **Documentation:** [README.md](README.md), [docs/](docs/)
- **Issues:** https://github.com/your-username/agent-factory/issues
- **Discussions:** https://github.com/your-username/agent-factory/discussions
- **Releases:** https://github.com/your-username/agent-factory/releases

---

**"The best way to predict the future is to build it autonomously."**

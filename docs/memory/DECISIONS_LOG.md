# DECISIONS_LOG.md

## Latest Decisions

### 2025-12-06

**Decision:** Use NetworkX for knowledge graph implementation
**Reasoning:**
- Mature, well-tested library for graph operations
- Built-in algorithms (PageRank, shortest path, cycle detection)
- Already specified in Phase 5 spec
- Better than reinventing graph algorithms
**Alternatives Considered:** Custom graph implementation
**Impact:** Robust dependency tracking with minimal code
**Status:** Implemented successfully

**Decision:** Separate CodeAnalyzer from ProjectTwin
**Reasoning:**
- Single responsibility: CodeAnalyzer handles AST parsing
- ProjectTwin orchestrates overall syncing
- Easier to test independently
- Follows Phase 5 spec architecture
**Alternatives Considered:** Combining into single class
**Impact:** Clean separation of concerns, better testability
**Status:** Working well

**Decision:** Include both LLM and non-LLM modes in TwinAgent
**Reasoning:**
- Basic queries work without LLM (faster, cheaper)
- Complex queries benefit from LLM reasoning
- Graceful degradation when API key missing
- Flexibility for different use cases
**Alternatives Considered:** LLM-only or query-only
**Impact:** Better user experience, works in more scenarios
**Status:** Validated in demo

**Decision:** Use sys.path.insert for demo/test imports
**Reasoning:**
- Poetry package-mode=false (application, not library)
- Simplest solution for running demos/tests
- Consistent with existing test files
- No need for complex package installation
**Alternatives Considered:** Proper package installation, conftest.py
**Impact:** Demos and tests work immediately
**Status:** Working across all test files

**Decision:** Create memory system files
**Reasoning:**
- User requested memory system updates
- Helps track project state across sessions
- Provides context for future work
- Follows memory system pattern
**Alternatives Considered:** None (explicit user request)
**Impact:** Better session continuity
**Status:** Files created and populated

---

### 2025-12-05

**Decision:** Phase 4 before Phase 5
**Reasoning:**
- Deterministic tools needed for reliable file operations
- Phase 5 (Project Twin) depends on safe file reading
- Builds foundation for code analysis
**Impact:** Solid foundation for Phase 5 implementation

**Decision:** Comprehensive factory testing
**Reasoning:**
- AgentFactory is core entry point
- Needs thorough testing before building on top
- 22 tests cover all major use cases
**Impact:** Confidence in core functionality

**Decision:** Production observability in Phase 3
**Reasoning:**
- Essential for production deployments
- Tracing, metrics, cost tracking needed early
- Enables debugging and optimization
**Impact:** Production-ready observability from day 1

**Decision:** Structured outputs in Phase 2
**Reasoning:**
- Type safety for agent responses
- Pydantic validation
- Better than unstructured dicts
**Impact:** Reliable, validated agent outputs

**Decision:** Multi-agent orchestration in Phase 1
**Reasoning:**
- Core pattern for specialist agents
- Enables routing to appropriate handlers
- Foundation for all subsequent phases
**Impact:** Flexible agent architecture

---

## Architectural Decisions

**Decision:** Google ADK patterns as foundation
**Reasoning:**
- Proven patterns from Google's Agent Development Kit
- Industry best practices
- Documented in docs/PATTERNS.md
**Status:** Applied throughout project

**Decision:** LangChain as agent framework
**Reasoning:**
- Rich ecosystem of tools and integrations
- Active development and community
- Good documentation
**Status:** Core dependency

**Decision:** Pydantic for data validation
**Reasoning:**
- Type safety with runtime validation
- Excellent error messages
- Integrates well with LangChain
**Status:** Used for all schemas

**Decision:** Poetry for dependency management
**Reasoning:**
- Modern Python packaging
- Lock file for reproducible builds
- Better than pip requirements.txt
**Status:** Working well

---

## Testing Decisions

**Decision:** pytest as testing framework
**Reasoning:**
- Industry standard
- Rich plugin ecosystem
- Clean syntax
**Status:** 162 tests passing

**Decision:** Test coverage by component
**Reasoning:**
- Each phase gets comprehensive tests
- Unit tests + integration tests
- Validates behavior, not just coverage percentage
**Status:** High-quality tests across all phases

---

## Documentation Decisions

**Decision:** Memory system files for session continuity
**Reasoning:**
- Large project needs context tracking
- Helps after context clears
- User-readable format
**Status:** Implemented today (2025-12-06)

**Decision:** CLAUDE.md as meta documentation
**Reasoning:**
- Single source of truth for AI assistant
- References other docs
- Clear execution rules
**Status:** Working well as guide

**Decision:** Phase-specific spec docs
**Reasoning:**
- Detailed implementation guidance
- Separate from progress tracking
- Easy to reference during implementation
**Status:** PHASE1-5_SPEC.md created

# Agent Factory - Current State Overview

> **Generated:** 2025-12-07 (Phase 0 - Repo Mapping)
> **Purpose:** Complete documentation of current codebase architecture, capabilities, and limitations

---

## Executive Summary

**Agent Factory** is a **spec-first AI agent creation framework** currently functioning as a CLI tool. It enables developers to build production-grade AI agents from markdown specifications using LangChain, LangGraph, and Google ADK patterns.

**Current Status:** Post-Phase 4 (Deterministic Tools + Caching Complete)
**Test Coverage:** 205 passing tests
**Architecture:** CLI-based, single-user, local execution
**Primary Use Case:** Developer tool for rapid agent prototyping

---

## Project Statistics

| Metric | Value |
|--------|-------|
| **Total Python Files** | 156 files |
| **Core Modules** | 4 files (agent_factory/core/) |
| **Tools** | 7 categories (research, file ops, coding, cache, validators) |
| **CLI Modules** | 9 files (wizard, editor, chat, presets) |
| **Tests** | 205 passing (97% pass rate) |
| **Documentation** | 17 wiki pages + 5 memory files |
| **Generated Agents** | 1 (Bob - Market Research Specialist) |
| **Lines of Code** | ~15,000 lines (estimated) |

---

## Directory Structure

```
Agent-Factory/
├── agent_factory/              # Core package
│   ├── core/                   # Agent engine
│   │   ├── agent_factory.py    # Main factory class (420 lines)
│   │   ├── orchestrator.py     # Multi-agent routing (Phase 1)
│   │   ├── callbacks.py        # Event bus system
│   │   └── __init__.py
│   ├── tools/                  # Agent tools
│   │   ├── research_tools.py   # Wikipedia, DuckDuckGo, Tavily, time
│   │   ├── file_tools.py       # Read, Write, List, Search
│   │   ├── coding_tools.py     # Git status, file search
│   │   ├── validators.py       # Path validation, size limits
│   │   ├── cache.py            # TTL caching with LRU eviction
│   │   └── tool_registry.py    # Tool catalog
│   ├── cli/                    # CLI interface
│   │   ├── app.py              # Typer CLI (chat interface)
│   │   ├── interactive_creator.py  # 8-step wizard (1500+ lines)
│   │   ├── agent_editor.py     # Tool/invariant editing
│   │   ├── chat_session.py     # REPL with history
│   │   ├── agent_presets.py    # bob, research, coding
│   │   ├── templates.py        # Pre-built templates
│   │   ├── wizard_state.py     # State management
│   │   └── tool_registry.py    # CLI tool catalog
│   ├── codegen/                # Spec → Code generation
│   │   ├── spec_parser.py      # Markdown → AgentSpec
│   │   ├── code_generator.py   # AgentSpec → Python
│   │   └── eval_generator.py   # Generate pytest tests
│   ├── schemas/                # Pydantic models
│   │   └── agent_spec.py       # AgentSpec, BehaviorExample, etc.
│   └── workers/                # Autonomous agents
│       └── openhands_worker.py # OpenHands integration
├── agents/                     # Generated agent code
│   └── unnamedagent_v1_0.py    # Bob (Market Research)
├── specs/                      # Agent specifications
│   ├── template.md             # Spec template
│   └── [user-created specs]
├── tests/                      # Test suite (205 tests)
│   ├── test_agent_factory.py
│   ├── test_file_tools.py
│   ├── test_cache.py
│   └── [more tests]
├── docs/                       # Documentation (Phase 0)
│   └── [this file]
├── agentcli.py                 # Argparse CLI (spec workflow)
├── pyproject.toml              # Poetry dependencies
└── [memory files, docs, etc.]
```

---

## Core Architecture

### 1. Agent Factory (`agent_factory/core/agent_factory.py`)

**Purpose:** Central factory for creating LangChain AgentExecutors with custom configurations.

**Capabilities:**
- **Multi-LLM Support:** OpenAI, Anthropic Claude, Google Gemini
- **Agent Types:** ReAct, Structured Chat
- **Memory:** ConversationBufferMemory (built-in)
- **Tools:** Dynamic tool assignment from tool registry
- **Structured Output:** Pydantic schema binding (OpenAI/Anthropic)

**Key Methods:**
```python
# Create generic agent
agent = factory.create_agent(
    role="Research Agent",
    tools_list=[wikipedia, duckduckgo],
    system_prompt="You are a research assistant...",
    agent_type="react",
    response_schema=ResearchResponse  # Optional Pydantic model
)

# Create preset agents
research_agent = factory.create_research_agent(tools_list)
coding_agent = factory.create_coding_agent(tools_list)

# Create orchestrator (multi-agent routing)
orchestrator = factory.create_orchestrator()

# Create OpenHands worker (autonomous coding)
openhands = factory.create_openhands_agent(model="claude-3-5-sonnet")
```

**Current Limitations:**
- ❌ No LLM abstraction layer (calls OpenAI/Anthropic directly)
- ❌ No multi-LLM routing (can't use Llama → Perplexity → Claude cascade)
- ❌ No cost tracking per agent call
- ❌ No rate limiting
- ❌ Hard-coded prompt hub names (`hwchase17/react`)

---

### 2. Multi-Agent Orchestrator (`agent_factory/core/orchestrator.py`)

**Purpose:** Route queries to specialized agents based on keywords/capabilities.

**Status:** ✅ Already implemented (Phase 1 complete!)

**Capabilities:**
- Register multiple agents with routing keywords
- Intelligent query routing via LLM classification
- Event bus integration for monitoring
- Verbose logging of routing decisions

**Example:**
```python
orchestrator = factory.create_orchestrator()

# Register specialized agents
orchestrator.register("research", research_agent, keywords=["search", "find", "lookup"])
orchestrator.register("coding", coding_agent, keywords=["code", "file", "write"])

# Route query to appropriate agent
response = orchestrator.route("Search for Python best practices")
# → Routes to research_agent
```

**Gap:** Not used in current CLI - all routing is manual (user selects agent)

---

### 3. Two Separate CLI Tools

#### A. `agentcli.py` (Argparse) - **Spec-to-Agent Workflow**

**Purpose:** Build agents from markdown specifications.

**Commands:**
```bash
poetry run python agentcli.py build <spec-name>     # Generate agent + tests
poetry run python agentcli.py validate <spec-file>  # Check spec syntax
poetry run python agentcli.py eval <agent-name>     # Run pytest
poetry run python agentcli.py list                  # Show available specs
poetry run python agentcli.py status                # System info
poetry run python agentcli.py create                # Interactive wizard
poetry run python agentcli.py edit <agent-name>     # Modify existing agent
```

**Flow:**
```
specs/template.md
    ↓ (validate)
Parse → AgentSpec object
    ↓ (build)
Generate agents/agent_v1_0.py + tests/test_agent_v1_0.py
    ↓ (eval)
Run pytest tests
```

#### B. `agent_factory/cli/app.py` (Typer) - **Chat Interface**

**Purpose:** Interactive chat with preset agents.

**Commands:**
```bash
poetry run agentcli chat --agent bob       # Market research
poetry run agentcli chat --agent research  # Web research
poetry run agentcli chat --agent coding    # File operations
poetry run agentcli list-agents            # Show presets
```

**Features:**
- REPL with command history (prompt-toolkit)
- Rich markdown output
- Multi-turn conversation memory
- Slash commands (/help, /exit, /clear, /history, /save)
- Session save/resume

**User Confusion Point:**
- Users try `agentcli chat --agent bob-1` (fails)
- Correct syntax: `--agent bob` (no version suffix for presets)
- Documentation inconsistency between spec names (bob-1) and preset names (bob)

---

## Tool System

### Available Tools (10 total)

#### Research Tools (`research_tools.py`)
1. **WikipediaSearchTool** - Search Wikipedia articles (3-sentence summaries)
2. **DuckDuckGoSearchTool** - Web search (5 results, no API key)
3. **TavilySearchTool** - AI-optimized search (requires TAVILY_API_KEY)
4. **CurrentTimeTool** - Get current date/time

#### File Operation Tools (`file_tools.py`)
5. **ReadFileTool** - Read text files (max 10MB, encoding detection)
6. **WriteFileTool** - Write files (atomic, with backups)
7. **ListDirectoryTool** - List directory contents
8. **FileSearchTool** - Search file contents with regex

#### Coding Tools (`coding_tools.py`)
9. **GitStatusTool** - Show git repository status
10. **CodeSearchTool** - Search code files

**Safety Features:**
- Path validation (prevent directory traversal)
- File size limits (10MB max)
- Binary file detection
- Encoding auto-detection
- Atomic writes with backups
- Idempotent operations

**Caching System:** (`cache.py`)
- TTL-based caching (time-to-live expiration)
- LRU eviction (least recently used)
- Decorator-based (@cached)
- Thread-safe

---

## Agent Presets

### 1. Bob - Market Research Specialist

**Spec:** `specs/bob-1.md` (414 lines)
**Code:** `agents/unnamedagent_v1_0.py` (210 lines)
**Model:** gpt-4o-mini (default), configurable
**Iteration Limit:** 25 (higher than default 15)
**Timeout:** 5 minutes

**Tools (10):**
- Research: Wikipedia, DuckDuckGo, Tavily, CurrentTime
- File ops: Read, Write, List, Search

**Invariants (8):**
1. Evidence-Based (sources required)
2. Ethical Research (no dark patterns)
3. Transparency (disclose uncertainty)
4. User Focus (solve real problems)
5. Timeliness (data < 6 months old)
6. Actionability (next steps included)
7. Cost Awareness (< $0.50 per query)
8. Response Speed (< 60 seconds)

**Use Case:** Find underserved market niches, validate product ideas

---

### 2. Research Agent (Preset)

**Config:** `agent_factory/cli/agent_presets.py`
**Tools:** Wikipedia, DuckDuckGo, Tavily (optional), CurrentTime
**Agent Type:** Structured Chat
**System Prompt:** "You are an AI research assistant..."

---

### 3. Coding Agent (Preset)

**Config:** `agent_factory/cli/agent_presets.py`
**Tools:** ReadFile, WriteFile, ListDirectory, FileSearch
**Agent Type:** ReAct
**System Prompt:** "You are an AI coding assistant..."

---

## Code Generation Pipeline

### Spec → Agent Flow

```
1. User creates spec: specs/my-agent-v1.0.md
   ↓
2. Validate: agentcli validate specs/my-agent-v1.0.md
   - Check required sections (Purpose, Scope, Invariants, etc.)
   - Validate behavior examples (correct/wrong)
   - Ensure tools are defined
   ↓
3. Build: agentcli build my-agent-v1.0
   - Parse spec → AgentSpec Pydantic model
   - Generate agents/myagent_v1_0.py
     * Import statements
     * create_agent() function
     * Tool configuration
     * System prompt from spec
   - Generate tests/test_myagent_v1_0.py
     * Smoke test
     * Tool availability tests
     * Behavior example tests
   ↓
4. Test: agentcli eval my-agent-v1.0
   - Run pytest -v
   - Verify agent creates successfully
   - Test tool invocations
   ↓
5. Use: import from agents.myagent_v1_0 import create_agent
```

**Code Generator Features:**
- PLC-style heavy commenting (40% comment density)
- Type hints on all functions
- Pydantic schema validation
- Error handling
- Metadata tracking

---

## Current Capabilities vs Limitations

### ✅ What Works Well

**Developer Experience:**
- Interactive wizard (8 steps, template support)
- Spec validation with detailed feedback
- Auto-generated code + tests
- Chat interface with history
- Agent editing (tools/invariants)

**Agent Quality:**
- Type-safe (Pydantic schemas)
- Well-documented (PLC comments)
- Tested (pytest generated automatically)
- Memory-enabled (conversation buffer)
- Tool-rich (10 tools available)

**Safety & Reliability:**
- Path validation (no directory traversal)
- File size limits (prevent memory overflow)
- Atomic file writes (no corruption)
- Idempotent operations (safe retries)
- Caching (performance optimization)

---

### ❌ Current Limitations

**1. No LLM Abstraction Layer**
- Direct calls to OpenAI/Anthropic/Google
- Can't implement cost-optimized routing
- No centralized token/cost tracking
- Hard to switch providers dynamically

**2. No Multi-LLM Routing**
- Can't cascade: Llama (local, free) → Perplexity (cheap) → Claude (expensive)
- Single provider per agent
- No purpose-based routing ("simple" → Llama, "search" → Perplexity)

**3. No Cost Monitoring**
- No tracking of API costs per run
- No budget limits or alerts
- No usage analytics
- Can't estimate costs before running

**4. CLI-Only (No Web UI)**
- Requires command-line knowledge
- No visual agent builder
- No dashboard for analytics
- Not accessible to non-developers

**5. Single-User (No Multi-Tenancy)**
- All agents belong to one user
- No teams/organizations
- No sharing/permissions
- No row-level security

**6. No API for External Access**
- Can't call agents via HTTP
- No webhooks
- No Zapier/Make integration
- Not embeddable in other apps

**7. Limited Tool Set**
- Only 10 tools currently
- No Slack/Discord/Email integration
- No database tools
- No scheduling/cron tools

**8. No Marketplace**
- Can't share agents with community
- No template discovery
- No rating/review system
- No revenue sharing for creators

---

## Technical Debt

### Code Quality Issues

1. **Inconsistent Error Handling**
   - Some tools return error strings
   - Some raise exceptions
   - No unified error response format

2. **Hard-Coded Values**
   - Prompt hub names (`hwchase17/react`)
   - File size limits (10MB)
   - Temperature defaults vary by provider

3. **Limited Type Coverage**
   - Some older modules lack type hints
   - Optional typing in some functions

4. **Documentation Gaps**
   - Some functions missing docstrings
   - API-level docs incomplete
   - No architecture diagrams

### Scalability Issues

1. **Synchronous Execution**
   - Agent runs block CLI
   - No background job queue (Celery/RQ)
   - Can't run multiple agents concurrently

2. **No Caching Strategy for LLM Calls**
   - Cache exists for tools, not for LLM
   - Same query = same API cost
   - No semantic caching

3. **Memory Management**
   - ConversationBufferMemory grows unbounded
   - No memory summarization
   - No memory persistence to DB

### Security Issues

1. **No Authentication**
   - Anyone with CLI access can run agents
   - No API keys for agent usage
   - No audit logging

2. **No Rate Limiting**
   - Can exhaust API quotas
   - No protection against runaway agents
   - No per-user limits

3. **Limited Input Validation**
   - Spec parser trusts markdown input
   - No SQL injection prevention (future DB)
   - No XSS prevention (future web UI)

---

## Dependencies

**Core:**
- `langchain` 0.2.1 - Agent framework
- `langchain-openai` - OpenAI integration
- `langchain-anthropic` - Claude integration
- `langchain-google-genai` - Gemini integration
- `pydantic` 2.x - Data validation

**Tools:**
- `wikipedia` - Wikipedia API
- `duckduckgo-search` - Web search
- `tavily-python` - AI search (optional)

**CLI:**
- `typer` - Modern CLI framework
- `rich` - Terminal formatting
- `prompt-toolkit` - REPL with history

**Dev:**
- `pytest` - Testing (205 tests)
- `poetry` - Dependency management

**Future Needs (Platform):**
- `fastapi` - REST API
- `uvicorn` - ASGI server
- `psycopg2` - PostgreSQL driver
- `redis` - Caching/queuing
- `stripe` - Billing
- `litellm` - Multi-LLM routing

---

## Testing Strategy

**Current Coverage:**
- **Unit Tests:** Tools, cache, validators (well-covered)
- **Integration Tests:** Agent creation (smoke tests)
- **E2E Tests:** CLI commands (manual testing)

**Test Structure:**
```
tests/
├── test_agent_factory.py      # Factory creation, LLM providers
├── test_file_tools.py         # File operations (27 tests)
├── test_cache.py              # Caching system (19 tests)
├── test_orchestrator.py       # Multi-agent routing
├── test_codegen.py            # Spec parsing, code gen
└── [generated test files]     # Per-agent behavior tests
```

**Testing Gaps:**
- No load testing (performance under scale)
- No security testing (penetration tests)
- No cross-platform testing (Windows focus)
- No browser testing (future web UI)

---

## Performance Characteristics

**Agent Creation:**
- Time: < 100ms (in-memory)
- Memory: ~50MB per agent instance
- Concurrent limit: N/A (single-threaded)

**Agent Execution:**
- Time: 5-60 seconds (depends on LLM + tools)
- Tokens: 500-5000 per query (varies widely)
- Cost: $0.01-$0.50 per query (OpenAI gpt-4o-mini)

**Tool Operations:**
- File read: < 100ms (10MB limit)
- Web search: 1-3 seconds (DuckDuckGo)
- Wikipedia: 0.5-1 second
- File write: < 200ms (atomic)

---

## Deployment Model

**Current:** Local development only
- Run via `poetry run` commands
- All state in local filesystem
- No server component
- No multi-user support

**Future (Platform):**
- Cloud Run (agent execution)
- Supabase (database + auth)
- Vercel (web UI)
- Redis (caching/queuing)
- S3 (spec/log storage)

---

## Key Design Patterns

1. **Factory Pattern** - AgentFactory creates agents
2. **Builder Pattern** - Interactive wizard builds specs
3. **Strategy Pattern** - Multiple LLM providers
4. **Observer Pattern** - Event bus for orchestrator
5. **Decorator Pattern** - @cached for tool results
6. **Command Pattern** - CLI command routing

---

## Next Steps (From User's 6-Phase Plan)

### Immediate (Phases 1-3, Weeks 1-2)
1. ✅ Phase 0: This documentation (complete)
2. ⏳ Phase 1: LLM abstraction layer (`llm_client.py`)
3. ⏳ Phase 2: Multi-LLM routing (LiteLLM integration)
4. ⏳ Phase 3: Modern tooling (expand tool catalog)

### Short-term (Phase 4, Week 3)
5. ⏳ Phase 4: Brain Fart Checker (niche validator)
   - **CRITICAL:** First product launch ($99/mo)
   - Build `idea_validator.py` module
   - Implement novelty/MRR/competitor scoring
   - Add `agentcli evaluate-idea "my idea"` command

### Medium-term (Phases 5-6, Week 4)
6. ⏳ Phase 5: OpenHands integration (already 80% done!)
7. ⏳ Phase 6: Cost monitoring (`agentcli cost-report`)

### Platform (Months 2-3)
8. ⏳ Phase 7: Multi-agent orchestration (teams of agents)
9. ⏳ Phase 8: Web UI (React + Next.js)
10. ⏳ Phase 9: Multi-tenancy (PostgreSQL + RLS)
11. ⏳ Phase 10: Billing (Stripe)
12. ⏳ Phase 11: Marketplace (template library)
13. ⏳ Phase 12: REST API (FastAPI)

---

## Summary

Agent Factory is a **production-quality CLI tool** for building AI agents from specifications. It successfully implements the "spec-first" philosophy with comprehensive tooling, safety features, and code generation.

**Strengths:**
- Robust spec validation
- Safe file operations
- Multi-LLM provider support
- Interactive wizard UX
- Comprehensive testing

**Ready for Platform Evolution:**
- Orchestrator already built (Phase 1 ✅)
- OpenHands integration exists (Phase 5 ✅)
- Clean architecture for API layer
- Separation of concerns (tools, core, CLI)

**Critical Gap to Address First:**
- LLM abstraction layer (Phase 1)
- Enables cost optimization, routing, monitoring
- Foundation for all platform features

---

**Document Version:** 1.0
**Last Updated:** 2025-12-07
**Next Update:** After Phase 1 completion

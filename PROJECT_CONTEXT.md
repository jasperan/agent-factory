# Project Context
> Quick reference for what this project is and its current state
> **Format:** Newest updates at top, timestamped entries

---

## [2025-12-05 21:15] Constitutional System Implementation Complete

**Project Name:** Agent Factory
**Current Phase:** Constitutional Code Generation Framework
**Status:** ✅ **Phase 1 Foundation Complete - Ready for Demo**

**Recent Major Changes:**
- Constitutional system fully implemented per AGENTS.md
- Hybrid documentation standard applied (readable + spec-linked)
- factory.py code generator with CLI (validate, generate, info commands)
- callbacks.py and orchestrator.py updated with REQ-* traceability
- All core modules tested and working

**What's Working:**
- SpecParser: Extracts requirements from markdown specs (53 total across 3 specs)
- EventBus: Pub/sub system with 1000-event history
- AgentOrchestrator: Multi-agent routing (keyword → LLM → fallback)
- AgentFactory.create_orchestrator(): Integration complete
- CLI commands: All functional

**Current Commit:** `26276ca` - Constitutional system with hybrid documentation
- 24 files changed, 7354 insertions
- 3 specs created (callbacks, orchestrator, factory)
- Jinja2 templates for automated generation

**Blockers:** None

**Next Steps:**
1. Create orchestrator_demo.py example
2. Write basic tests for callbacks/orchestrator
3. Run full integration demo
4. (Optional) Complete automated code generation in factory.py

---

## [2025-12-04 18:30] Phase 1 Development Ready

**Project Name:** Agent Factory
**Current Phase:** Phase 1 - Orchestration (Ready to Start)
**Status:** ✅ **Planning Complete - Ready for Implementation**

**Recent Additions:**
- Interactive CLI tool (agentcli) - Fully functional
- Comprehensive documentation (CLAUDE_CODEBASE.md, CLI_USAGE.md)
- Execution framework (CLAUDE.md, PROGRESS.md)
- Memory system with `/context-clear` command
- All API keys validated and working

**Current Work:**
- PHASE1_SPEC.md does not exist (user indicated it should)
- Proceeding with PROGRESS.md as specification
- First task: Create `agent_factory/core/orchestrator.py`

**Blockers:** None - ready to begin Phase 1 implementation

**Next Steps:**
1. Begin Phase 1 orchestration implementation
2. Follow PROGRESS.md checklist (checkbox by checkbox)
3. Run checkpoint tests after each section
4. Create orchestrator_demo.py when complete

---

## [2025-12-04 16:50] Current Status

**Project Name:** Agent Factory
**Type:** Python Framework (Application, not library)
**Purpose:** Dynamic AI agent creation with pluggable tool system
**GitHub:** https://github.com/Mikecranesync/Agent-Factory
**Local Path:** `C:\Users\hharp\OneDrive\Desktop\Agent Factory`

**Status:** ⚠️ **Dependency Issue - Installation Blocked**

---

## [2025-12-04 15:30] Repository Published

Agent Factory successfully published to GitHub:
- Repository created as public
- Initial commit with 22 files
- Topics added: langchain, ai-agents, llm, python, poetry, openai, agent-framework
- Comprehensive documentation included
- All API keys safely excluded from git

---

## [2025-12-04 14:00] Project Created

### What Is Agent Factory?

A scalable framework for creating specialized AI agents with dynamic tool assignment. Instead of hardcoding tools into agents, users can mix and match capabilities on demand.

### Core Features

1. **Dynamic Agent Creation**
   - `create_agent(role, system_prompt, tools_list)` - Main factory method
   - Pre-built agents: Research Agent, Coding Agent
   - Custom agent configurations

2. **Pluggable Tool System**
   - Research Tools: Wikipedia, DuckDuckGo, Tavily
   - Coding Tools: File operations, Git, directory listing
   - Tool Registry for centralized management

3. **Multiple LLM Providers**
   - OpenAI (GPT-4o) - Primary
   - Anthropic (Claude 3)
   - Google (Gemini)

4. **Built-in Memory**
   - Conversation history tracking
   - Multi-turn interactions
   - Context preservation

### Technology Stack

```
Python 3.10-3.11
Poetry 2.x (dependency management)
LangChain 0.2.1 (core framework)
OpenAI, Anthropic, Google APIs
```

### Project Structure

```
agent_factory/
├── core/              # AgentFactory main class
├── tools/             # Research & coding tools
│   ├── research_tools.py
│   ├── coding_tools.py
│   └── tool_registry.py
├── agents/            # Pre-configured agents
├── examples/          # Demo scripts
└── memory/            # Memory management
```

### API Keys Configured

✅ OpenAI (GPT-4o) - Primary provider
✅ Anthropic (Claude 3) - Alternative
✅ Google (Gemini) - Alternative
✅ Firecrawl - Web scraping (optional)
✅ Tavily - AI search (optional)

All keys stored in `.env` (gitignored)

---

## Documentation Files

- `README.md` - Comprehensive documentation
- `QUICKSTART.md` - 5-minute setup guide
- `POETRY_GUIDE.md` - Poetry 2.x changes explained
- `HOW_TO_BUILD_AGENTS.md` - Step-by-step agent creation guide
- `claude.md` - API key analysis and security report
- `LICENSE` - MIT License

---

## Key Design Decisions

1. **Poetry 2.x Configuration**
   - `package-mode = false` - Application, not a library
   - No `--no-root` flag needed

2. **Tool Architecture**
   - BaseTool class pattern for maximum flexibility
   - Tool registry for centralized management
   - Category-based organization

3. **Agent Types**
   - ReAct: For sequential reasoning (coding tasks)
   - Structured Chat: For conversations (research tasks)

4. **No Hardcoded Tools**
   - Tools are variables passed to factory
   - Easy to add/remove capabilities
   - Scalable for multiple agent instances

---

## Original Inspiration

Based on patterns from: https://github.com/Mikecranesync/langchain-crash-course
Licensed under MIT (same as this project)

---

**Last Updated:** 2025-12-04 16:50
**Maintainer:** Mike Crane (Mikecranesync)

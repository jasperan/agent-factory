# Decisions Log
> Record of key technical and design decisions
> **Format:** Newest decisions at top, with rationale and alternatives considered

---

## [2025-12-05 20:00] Hybrid Documentation Over Full PLC Style

**Decision:** Use hybrid documentation (module headers + Google docstrings + REQ-* links) instead of line-by-line PLC-style comments

**Rationale:**
- User asked if line-by-line PLC comments would "break anything"
- Answer: No, but they make code hard to read and maintain
- Hybrid approach provides full spec traceability without verbosity
- Python community standards favor docstrings over excessive comments
- Tool compatibility (Sphinx, IDEs, type checkers) requires docstrings
- Code remains readable for developers

**Implementation:**
```python
# Module level: Header with spec SHA256 + regeneration command
# Class/Function level: Google-style docstrings with REQ-* identifiers
# Inline: Strategic comments only where logic is non-obvious
```

**Alternatives Considered:**
1. **Full PLC-style (every line documented)**
   - Pro: Maximum traceability
   - Con: 3:1 comment-to-code ratio
   - Con: Hard to read and maintain
   - Con: No tool support
   - **Rejected:** Too verbose

2. **Minimal documentation**
   - Pro: Very readable
   - Con: Lost spec traceability
   - Con: Hard to regenerate from specs
   - **Rejected:** Defeats constitutional purpose

3. **Hybrid approach (CHOSEN)**
   - Pro: Readable code
   - Pro: Full spec traceability via REQ-*
   - Pro: Tool compatible
   - Pro: Maintainable
   - **Selected:** Best balance

**Examples:**
- callbacks.py: 296 lines, 15 requirements documented
- orchestrator.py: 335 lines, 13 requirements documented
- All docstrings link to spec sections
- Troubleshooting sections in complex methods

---

## [2025-12-05 18:30] Constitutional Code Generation Approach

**Decision:** Build factory.py as spec parser + code generator instead of manual coding

**Rationale:**
- User provided AGENTS.md constitutional manifest
- 3 markdown specs already created (callbacks, orchestrator, factory)
- Constitutional principle: "Code is disposable. Specs are eternal."
- factory.py should read markdown and generate Python
- Enables regeneration if specs change
- Ultimate test: factory.py regenerates itself

**Implementation Strategy:**
1. SpecParser: Extract requirements, data structures, examples
2. SpecValidator: Check format compliance
3. CodeGenerator: Jinja2 templates → Python modules
4. TestGenerator: Generate pytest tests from REQ-* statements
5. CLI: Typer-based commands (validate, generate, info)

**Phased Approach:**
- **Phase 1 (This session):** Parser, validator, CLI, Jinja2 templates
- **Phase 2 (Future):** Automated code generation from templates
- **Phase 3 (Future):** Self-regeneration (factory.py → factory.py)

**Current Status:**
- ✅ SpecParser: Extracting 53 requirements across 3 specs
- ✅ SpecValidator: Checking format
- ✅ CLI: All commands functional
- ✅ Templates: Created but not yet fully integrated
- ⏳ CodeGenerator: Manual generation done, automation pending

**Alternative:**
- Manual coding per PROGRESS.md checkboxes
- **Rejected:** User wants constitutional approach

---

## [2025-12-05 18:00] Jinja2 for Code Generation Templates

**Decision:** Use Jinja2 templating engine for code generation

**Rationale:**
- Industry standard for Python code generation
- Excellent documentation and community support
- Supports complex logic (loops, conditionals)
- Clean separation of template and data
- Already familiar to Python developers

**Template Structure:**
- `module.py.j2`: Generate full Python modules
- `test.py.j2`: Generate pytest test files
- Variables: spec metadata, requirements, dataclasses, functions

**Alternatives Considered:**
1. **String concatenation**
   - Pro: No dependencies
   - Con: Unmaintainable for complex templates
   - **Rejected:** Too brittle

2. **Mako templates**
   - Pro: More powerful than Jinja2
   - Con: Less popular, steeper learning curve
   - **Rejected:** Jinja2 sufficient

3. **AST manipulation (ast module)**
   - Pro: Generates actual Python AST
   - Con: Very complex, hard to maintain
   - **Rejected:** Overkill for this use case

---

## [2025-12-04 18:30] Slash Command: Context Clear Implementation

**Decision:** Create `/context-clear` slash command for memory system updates

**Rationale:**
- User requested "skill call" for context preservation
- Automates tedious manual memory file updates
- Ensures consistent formatting and timestamps
- Single command updates all 5 memory files at once
- Reduces human error in documentation

**Implementation:**
- File: `.claude/commands/context-clear.md`
- Updates: PROJECT_CONTEXT, NEXT_ACTIONS, DEVELOPMENT_LOG, ISSUES_LOG, DECISIONS_LOG
- Format: Reverse chronological with `[YYYY-MM-DD HH:MM]` timestamps
- Preserves existing content, adds new entries at top

**Current Status:** Command file created but not yet recognized by SlashCommand tool (investigating)

**Alternatives Considered:**
1. Manual updates each time
   - Pro: Full control
   - Con: Time-consuming, error-prone
   - **Rejected:** User wants automation

2. Python script
   - Pro: More control over logic
   - Con: Harder to maintain, less integrated
   - **Rejected:** Slash command more convenient

---

## [2025-12-04 17:30] CLI Tool: Typer + Prompt-Toolkit Stack

**Decision:** Use Typer for CLI framework and prompt-toolkit for interactive REPL

**Rationale:**
- Typer: Modern, type-safe CLI framework with excellent docs
- prompt-toolkit: Industry standard for REPL features
- Rich: Beautiful terminal formatting (already in dependencies)
- All three libraries work well together
- Windows-compatible with proper encoding handling

**Implementation:**
```python
app = typer.Typer()  # CLI framework
session = PromptSession()  # Interactive REPL
console = Console()  # Rich formatting
```

**Version Choices:**
- Typer 0.12.0 (latest stable, fixed compatibility issues)
- prompt-toolkit 3.0.43 (latest stable)
- Rich 13.7.0 (already installed)

**Issues Resolved:**
- Typer 0.9.x had `TyperArgument.make_metavar()` errors → upgraded to 0.12.0
- Windows Unicode issues → replaced all Unicode with ASCII
- Module imports → added sys.path modification

---

## [2025-12-04 16:00] Documentation Strategy: Separate Technical from User Docs

**Decision:** Create CLAUDE_CODEBASE.md for technical docs, keep CLAUDE.md for execution rules

**Rationale:**
- User replaced original CLAUDE.md (API analysis) with execution rules
- Technical documentation still needed for development reference
- Separation of concerns: execution rules vs technical details
- CLAUDE_CODEBASE.md = comprehensive technical reference
- CLAUDE.md = how I should work (execution workflow)

**Audience:**
- CLAUDE_CODEBASE.md → Developers and AI assistants
- CLAUDE.md → AI assistant execution rules
- CLI_USAGE.md → End users of the CLI tool
- README.md → General project overview

---

## [2025-12-04 15:45] Phase 1 Execution: PROGRESS.md as Specification

**Decision:** Begin Phase 1 implementation using PROGRESS.md as the specification

**Rationale:**
- PHASE1_SPEC.md does not exist (user indicated it should but file not found)
- PROGRESS.md provides sufficient detail for implementation
- Each checkbox is a specific, testable task
- Embedded checkpoint tests verify correctness
- Follows CLAUDE.md execution rules (one checkbox at a time)

**Execution Approach:**
1. Read first unchecked item in PROGRESS.md
2. Implement the feature
3. Run embedded checkpoint test
4. If pass → check box, move to next
5. If fail → fix (max 3 tries per three-strike rule)

**Grade:** B+ (sufficient but would benefit from formal API specs)

**Alternatives Considered:**
1. Create PHASE1_SPEC.md first
   - Pro: More complete design documentation
   - Con: Delays implementation
   - **Rejected:** PROGRESS.md sufficient to start

2. Skip Phase 1 and work on other tasks
   - Pro: Address dependency conflict
   - Con: User wants Phase 1 orchestration
   - **Rejected:** User priority is Phase 1

---

## [2025-12-04 16:50] Memory System: Markdown Files Over MCP

**Decision:** Use markdown files with timestamps instead of MCP memory integration

**Rationale:**
- User explicitly concerned about token usage with MCP
- User wants chronological order with clear timestamps
- User wants no information mixing between files
- Markdown files are portable and human-readable
- Can be versioned in git for historical tracking

**Alternatives Considered:**
1. MCP Memory Integration
   - Pro: Native integration with Claude
   - Con: Token usage concerns
   - Con: Less transparent to user
   - **Rejected:** User explicit preference against

2. Single MEMORY.md File
   - Pro: Everything in one place
   - Con: Would become massive and mixed
   - Con: User explicitly wants separation
   - **Rejected:** User wants distinct files

**Files Created:**
- PROJECT_CONTEXT.md - Project state and overview
- ISSUES_LOG.md - Problems and solutions
- DEVELOPMENT_LOG.md - Activity timeline
- DECISIONS_LOG.md - Key choices (this file)
- NEXT_ACTIONS.md - Immediate tasks

**Format Standard:**
- `[YYYY-MM-DD HH:MM]` timestamp on every entry
- Newest entries at top (reverse chronological)
- Clear section separators (`---`)
- No mixing of different types of information

---

## [2025-12-04 15:30] Repository Visibility: Public

**Decision:** Created Agent Factory as a public GitHub repository

**Rationale:**
- Educational framework meant for community use
- MIT license encourages open sharing
- No proprietary code or secrets
- Facilitates collaboration and feedback
- Builds portfolio for creator

**Security Measures:**
- .env file properly gitignored
- .env.example provided as template
- No actual API keys committed
- Documentation warns about secret management

**Repository URL:** https://github.com/Mikecranesync/Agent-Factory

---

## [2025-12-04 14:30] API Key Storage: .env File

**Decision:** Use .env file for API key management

**Rationale:**
- Industry standard for local development
- python-dotenv library well-supported
- Easy to gitignore (security)
- Simple for users to configure
- Matches langchain-crash-course pattern

**Alternatives Considered:**
1. Environment Variables Only
   - Pro: More secure (no file)
   - Con: Harder for beginners to configure
   - Con: Not persistent across sessions on Windows
   - **Rejected:** Less user-friendly

2. Config File (JSON/YAML)
   - Pro: More structured
   - Con: Overkill for simple key storage
   - Con: Still needs gitignore
   - **Rejected:** Unnecessary complexity

**Implementation:**
```python
from dotenv import load_dotenv
load_dotenv()  # Loads .env automatically
```

**Security Documentation:** Created claude.md with API key security checklist

---

## [2025-12-04 14:00] Poetry Configuration: package-mode = false

**Decision:** Set `package-mode = false` in pyproject.toml

**Rationale:**
- Agent Factory is an application/framework, not a library package
- Won't be published to PyPI
- Poetry 2.x requires explicit declaration
- Eliminates need for `--no-root` flag
- Prevents confusion about package vs application

**Poetry 2.x Change:**
```toml
[tool.poetry]
name = "agent-factory"
version = "0.1.0"
package-mode = false  # New in Poetry 2.x
```

**Impact:**
- `poetry sync` installs dependencies only (no local package)
- `poetry run` works correctly
- No need for `poetry install --no-root`

**Documentation:** Created POETRY_GUIDE.md explaining this change

---

## [2025-12-04 13:45] LangGraph Inclusion (Currently Causing Issues)

**Decision:** Added langgraph ^0.0.26 to dependencies for future multi-agent orchestration

**Rationale:**
- Enables advanced agent coordination patterns
- Part of LangChain ecosystem
- Future-proofing for multi-agent workflows
- Seen in langchain-crash-course repository

**Current Status:** ⚠️ **CAUSING CRITICAL DEPENDENCY CONFLICT**

**Problem:**
```
langgraph (0.0.26) requires langchain-core (>=0.1.25,<0.2.0)
langchain (0.2.1) requires langchain-core (>=0.2.0,<0.3.0)
```

**Proposed Resolution:** Remove langgraph temporarily
- Not currently used in any code
- Can be added back when versions align
- Unblocks user installation

**Status:** Awaiting implementation of fix

---

## [2025-12-04 13:30] Tool Pattern: BaseTool Class

**Decision:** Use BaseTool class pattern for all tools

**Rationale:**
- Most flexible for factory pattern
- Type-safe input validation with Pydantic
- Consistent interface across all tools
- Easy to extend and customize
- Supports complex tool logic

**Pattern:**
```python
from langchain_core.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field

class ToolInput(BaseModel):
    param: str = Field(description="Parameter description")

class CustomTool(BaseTool):
    name = "tool_name"
    description = "Tool description for LLM"
    args_schema: Type[BaseModel] = ToolInput

    def _run(self, param: str) -> str:
        # Tool logic here
        return result
```

**Alternatives Considered:**
1. Tool Constructor Pattern
   ```python
   Tool(name="tool_name", func=function, description="desc")
   ```
   - Pro: Simpler for basic tools
   - Con: Less type safety
   - Con: Harder to add configuration
   - **Rejected:** Less scalable

2. @tool() Decorator Pattern
   ```python
   @tool
   def my_tool(input: str) -> str:
       return result
   ```
   - Pro: Very concise
   - Con: Limited customization
   - Con: No instance variables
   - **Rejected:** Not flexible enough for factory

**Implementation:** All 10 tools use BaseTool class

---

## [2025-12-04 13:15] Agent Types: ReAct vs Structured Chat

**Decision:** Support both ReAct and Structured Chat agent types

**Rationale:**
- Different tasks need different patterns
- ReAct: Better for sequential reasoning (coding tasks)
- Structured Chat: Better for conversations (research tasks)
- User can choose based on use case

**Implementation:**
```python
AgentFactory.AGENT_TYPE_REACT = "react"
AgentFactory.AGENT_TYPE_STRUCTURED_CHAT = "structured_chat"
```

**Prompts:**
- ReAct: `hub.pull("hwchase17/react")`
- Structured Chat: `hub.pull("hwchase17/structured-chat-agent")`

**Pre-configured Agents:**
- Research Agent: Uses Structured Chat (conversations)
- Coding Agent: Uses ReAct (sequential file operations)

**Why Not OpenAI Functions?**
- Not provider-agnostic (OpenAI-specific)
- ReAct and Structured Chat work with all LLM providers
- More flexibility for future expansion

---

## [2025-12-04 13:00] LLM Provider Abstraction

**Decision:** Support multiple LLM providers (OpenAI, Anthropic, Google) with unified interface

**Rationale:**
- Provider-agnostic design
- Users can choose based on cost/features
- Fallback options if one provider is down
- Educational: Shows how to work with multiple LLMs

**Implementation:**
```python
def _create_llm(self, provider, model, temperature):
    if provider == "openai":
        return ChatOpenAI(model=model, temperature=temperature)
    elif provider == "anthropic":
        return ChatAnthropic(model=model, temperature=temperature)
    elif provider == "google":
        return ChatGoogleGenerativeAI(model=model, temperature=temperature)
```

**Default:** OpenAI GPT-4o
- Most accessible (widely available)
- Best documented
- Used in langchain-crash-course examples
- Good balance of cost/performance

**API Keys Required:** All 3 providers configured in .env

---

## [2025-12-04 12:30] Memory Management: Optional with Default Enabled

**Decision:** Make memory optional but enable by default

**Rationale:**
- Most use cases benefit from conversation history
- Users can disable for stateless agents
- Explicit control via `enable_memory` parameter
- System prompt stored in memory for context

**Implementation:**
```python
if enable_memory:
    memory = ConversationBufferMemory(
        memory_key=memory_key,
        return_messages=True
    )
    if system_prompt:
        memory.chat_memory.add_message(
            SystemMessage(content=f"{system_prompt}\n\nRole: {role}")
        )
```

**Memory Type:** ConversationBufferMemory
- Simplest to understand
- Stores full conversation
- Good for demos and learning

**Future Expansion:** Could add ConversationSummaryMemory, ConversationBufferWindowMemory

---

## [2025-12-04 12:00] Tool Organization: Category-Based Registry

**Decision:** Implement ToolRegistry with category-based organization

**Rationale:**
- Centralized tool management
- Easy to query tools by category
- Supports dynamic tool discovery
- Scalable for large tool collections
- Clear separation of concerns

**Categories Implemented:**
- "research": Wikipedia, DuckDuckGo, Tavily, CurrentTime
- "coding": ReadFile, WriteFile, ListDirectory, GitStatus, FileSearch

**Helper Functions:**
```python
get_research_tools(include_wikipedia=True, include_duckduckgo=True, include_tavily=False)
get_coding_tools(base_dir=".")
```

**Why Not Flat List?**
- Harder to manage as tools grow
- No logical grouping
- Difficult to enable/disable sets of tools
- **Rejected:** Not scalable

---

## [2025-12-04 11:30] Project Structure: Package-Based Architecture

**Decision:** Organize as Python package with clear module separation

**Structure:**
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

**Rationale:**
- Clear separation of concerns
- Easy to navigate for beginners
- Matches langchain-crash-course structure
- Scalable for future additions
- Standard Python package layout

**Alternatives Considered:**
1. Flat Structure (all files in root)
   - Pro: Simpler for tiny projects
   - Con: Becomes messy quickly
   - **Rejected:** Not scalable

2. Feature-Based (by agent type)
   - Pro: Groups related code
   - Con: Duplicates common components
   - **Rejected:** Less reusable

---

## [2025-12-04 11:00] Core Design: Factory Pattern

**Decision:** Use Factory Pattern for agent creation

**Rationale:**
- User explicitly requested "AgentFactory" class
- Factory pattern perfect for dynamic object creation
- Encapsulates complex initialization logic
- Single point of configuration
- Easy to extend with new agent types

**Signature:**
```python
def create_agent(
    role: str,
    tools_list: List[Union[BaseTool, Any]],
    system_prompt: Optional[str] = None,
    agent_type: str = AGENT_TYPE_REACT,
    enable_memory: bool = True,
    llm_provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    **kwargs
) -> AgentExecutor:
```

**Key Features:**
- Tools as parameters (not hardcoded)
- Flexible configuration
- Sensible defaults
- Type hints for clarity

**Alternatives Considered:**
1. Builder Pattern
   - Pro: More explicit configuration
   - Con: More verbose
   - **Rejected:** Overkill for this use case

2. Direct Construction
   - Pro: No abstraction
   - Con: Repeats boilerplate
   - Con: Harder for beginners
   - **Rejected:** User requested factory

---

## Design Principles Established

### 1. Abstraction Over Hardcoding
**Principle:** Tools are variables, not hardcoded into agents
**Benefit:** Maximum flexibility, easy to reconfigure

### 2. Scalability First
**Principle:** Design for multiple agents and tools from day one
**Benefit:** Can loop through agent definitions, grow without refactoring

### 3. Provider Agnostic
**Principle:** Work with any LLM provider
**Benefit:** No vendor lock-in, cost optimization

### 4. Educational Focus
**Principle:** Code should be readable and well-documented
**Benefit:** Users learn patterns, not just use library

### 5. Sensible Defaults
**Principle:** Works out of the box, configurable when needed
**Benefit:** Beginner-friendly, expert-capable

---

**Last Updated:** 2025-12-04 16:50
**Next Entry:** Will be added above this line


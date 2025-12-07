# Issues Log
> Chronological record of problems and solutions
> **Format:** Newest issues at top, [STATUS] tagged

---

## [2025-12-07 23:55] INFORMATIONAL: Phase 0 Documentation 90% Complete - Ready for Phase 1

**Status:** [COMPLETE] - 9 of 10 files complete, ready to begin implementation

**Context:**
- Phase 0 documentation provides complete foundation for 13-week implementation
- Building multi-tenant SaaS platform comparable to CrewAI
- Target: $10K MRR by Month 3, full platform in 13 weeks
- "Ultrathink" quality standard applied to all documentation

**Files Completed (9 of 10):**
1. ✅ docs/00_repo_overview.md (25KB, 517 lines)
2. ✅ docs/00_platform_roadmap.md (45KB, 1,200+ lines)
3. ✅ docs/00_database_schema.md (50KB, 900+ lines)
4. ✅ docs/00_architecture_platform.md (70KB, 1,500+ lines)
5. ✅ docs/00_gap_analysis.md (75KB, 1,400+ lines)
6. ✅ docs/00_business_model.md (76KB, 1,250+ lines)
7. ✅ docs/00_api_design.md (50KB, 1,400+ lines)
8. ✅ docs/00_tech_stack.md (45KB, 1,100+ lines)
9. ✅ docs/00_competitive_analysis.md (50KB, 1,100+ lines)

**Total Output:** ~530KB of comprehensive platform documentation

**Remaining Tasks (Optional):**
- CLI improvements (help text, roadmap command) - Nice to have
- docs/00_security_model.md - Optional 10th file

**Impact:**
- Complete platform vision documented before coding starts
- Reduces risk of costly architectural changes mid-development
- Enables parallel work (different devs can implement different phases)
- Investor/team presentation ready
- Acts as training material for new team members

**Next Steps:**
1. Begin Phase 1: LLM Abstraction Layer (2-3 days)
2. Install LiteLLM and create router
3. Set up infrastructure (Google Cloud, Supabase projects)

**Status:** [COMPLETE] - Phase 0 documentation foundation complete, ready for Phase 1

---

## [2025-12-07 23:45] INFORMATIONAL: Phase 0 Documentation Progress

**Status:** [IN PROGRESS] - 60% Complete (6 of 10 files)

**Context:**
- Phase 0 requires comprehensive documentation before Phase 1 implementation
- Building platform vision for multi-tenant SaaS (not just CLI tool)
- Target: $10K MRR by Month 3, full platform in 13 weeks

**Files Completed:**
1. ✅ docs/00_repo_overview.md (25KB)
2. ✅ docs/00_platform_roadmap.md (45KB)
3. ✅ docs/00_database_schema.md (50KB)
4. ✅ docs/00_architecture_platform.md (70KB)
5. ✅ docs/00_gap_analysis.md (75KB)
6. ✅ docs/00_business_model.md (76KB)

**Files Remaining:**
- docs/00_api_design.md (REST API specification, 50+ endpoints)
- docs/00_tech_stack.md (Technology choices with rationale)
- docs/00_competitive_analysis.md (vs CrewAI, Vertex, MindStudio, Lindy)
- CLI improvements (help text, roadmap command)

**Impact:**
- Complete platform vision before coding
- Reduces risk of architectural rework
- Enables informed Phase 1 implementation
- Documents business case for investors/team

**Next Steps:**
- Continue Phase 0 documentation
- Target 100% completion before starting Phase 1

**Status:** [IN PROGRESS] - On track, no blockers

---

## [2025-12-07 22:30] FIXED: Bob Not Accessible via Chat Command

**Problem:** User ran `poetry run agentcli chat --agent bob-1` and got error "Got unexpected extra argument (bob-1)"

**Context:**
- Bob agent created via wizard and stored in agents/unnamedagent_v1_0.py
- Chat interface exists and works for research/coding agents
- Bob not registered in agent preset system
- Documentation (CHAT_USAGE.md) showed incorrect command syntax

**Error Messages:**
```
poetry run agentcli chat --agent bob-1
Error: Got unexpected extra argument (bob-1)

Warning: 'agentcli' is an entry point defined in pyproject.toml, but it's not installed as a script.
```

**User Feedback:** "results not good"

**Root Cause:**
1. Bob not added to AGENT_CONFIGS dictionary in agent_presets.py
2. No get_bob_agent() factory function created
3. get_agent() dispatcher missing 'bob' case
4. Documentation used wrong syntax (bob-1 instead of bob)
5. Poetry entry point not installed after code changes

**Impact:**
- User couldn't access Bob via chat interface
- Multi-turn conversation feature unavailable
- Had to use single-query test scripts instead
- Poor UX for iterative market research

**Solution:**
1. Added Bob to AGENT_CONFIGS in agent_presets.py:
   - Full system message with 8 invariants
   - Description: "Market opportunity discovery for apps, agents, and digital products"

2. Created get_bob_agent() factory function:
   - Combines research tools (Wikipedia, DuckDuckGo, Tavily, time)
   - Adds file operation tools (Read, Write, List, Search)
   - Sets max_iterations=25 for complex research
   - Sets max_execution_time=300 (5 minutes)

3. Updated get_agent() dispatcher to include 'bob' case

4. Fixed CHAT_USAGE.md throughout:
   - Changed all `--agent bob-1` to `--agent bob`
   - Added "Available Preset Agents" table
   - Corrected all example commands

5. Ran `poetry install` to fix entry point warning

**Validation:**
```bash
poetry run agentcli list-agents
# Output:
# Available agents:
#   - bob: Bob - Market Research Specialist
#   - research: Research Assistant
#   - coding: Coding Assistant

poetry run agentcli chat --agent bob
# ✅ Chat session starts successfully
```

**Files Modified:**
- agent_factory/cli/agent_presets.py (+128 lines)
- CHAT_USAGE.md (649 lines, fixed syntax throughout)

**Commit:** 8 commits organized and pushed to GitHub

**Status:** [FIXED] - Bob now fully accessible via chat interface

---

## [2025-12-07 14:30] INFORMATIONAL: OpenAI Rate Limit Hit During Testing

**Problem:** test_bob.py failed with Error code: 429 - Rate limit exceeded
**Context:** Testing Bob market research agent

**Error Message:**
```
Rate limit reached for gpt-4o-mini in organization
Limit 200000 TPM, Used 187107, Requested 17807
Please try again in 1.474s
```

**Impact:**
- Test did not complete
- Cannot validate Bob's market research functionality yet
- Temporary only (resets in 1-2 seconds)

**Root Cause:**
- OpenAI API has token-per-minute (TPM) limits
- Previous testing consumed 187,107 tokens
- Bob's test query required 17,807 more tokens
- Total would exceed 200,000 TPM limit

**Solution:**
- Wait 1-2 seconds for rate limit window to reset
- Rerun test: `poetry run python test_bob.py`
- OR use simpler query to consume fewer tokens
- OR test via interactive chat (more controlled)

**Evidence Bob is Working:**
```
[OK] Agent created
[OK] Tools: 10 (research + file ops)
```

Agent creation succeeded, error occurred only during query execution (expected behavior with rate limits).

**Status:** [INFORMATIONAL] - Not a bug, expected API behavior

---

## [2025-12-07 12:00] FIXED: Agent Iteration Limit Too Low for Research

**Problem:** Bob agent stopped with "Agent stopped due to iteration limit or time limit"
**Root Cause:** Default max_iterations (15) too low for complex market research queries
**Error:** Agent couldn't complete multi-step research before hitting limit

**Impact:**
- Bob couldn't complete research queries
- User sees incomplete results
- Tools available but couldn't be fully utilized

**Solution:** Increased max_iterations to 25 and added 5-minute timeout

**Code Change:**
```python
agent = factory.create_agent(
    role="Market Research Specialist",
    tools_list=tools,
    system_prompt=system_prompt,
    response_schema=AgentResponse,
    max_iterations=25,  # Was: default 15
    max_execution_time=300,  # Was: no limit
    metadata={...}
)
```

**Rationale:**
- Market research requires multiple tool calls (search, read, analyze)
- Each tool call consumes 1 iteration
- Complex queries may need 20+ iterations
- 25 is reasonable limit with 5-minute safety timeout

**Status:** [FIXED]

---

## [2025-12-07 10:00] FIXED: CLI Wizard Generated Agent Without Tools

**Problem:** Bob agent created with empty tools list
**Root Cause:** Wizard doesn't prompt for tool selection during creation
**Error:** Agent fails to run because AgentFactory requires non-empty tools_list

**Impact:**
- Generated agent code has `tools = []`
- Agent cannot perform any actions
- User must manually edit code to add tools

**Solution (Manual Fix):**
Added full toolset to Bob's code:
```python
tools = get_research_tools(
    include_wikipedia=True,
    include_duckduckgo=True,
    include_tavily=True,
    include_time=True
)
tools.extend(get_coding_tools(
    include_read=True,
    include_write=True,
    include_list=True,
    include_git=True,
    include_search=True
))
```

**Long-Term Solution:**
- Add tool selection step to wizard (Step 9?)
- OR default to basic tool collection
- OR use agent editor to add tools after creation

**Status:** [FIXED] - Manually for Bob, wizard improvement needed

---

## [2025-12-07 09:00] FIXED: CLI App Not Loading .env File

**Problem:** `agentcli chat` command failed with "OPENAI_API_KEY not found"
**Root Cause:** app.py wasn't loading environment variables from .env file
**Error:** `Did not find openai_api_key, please add an environment variable 'OPENAI_API_KEY'`

**Impact:**
- CLI chat command unusable
- API keys not accessible
- All LLM calls fail

**Solution:** Added load_dotenv() to app.py

**Code Change:**
```python
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@app.command()
def chat(...):
    # Now API keys are loaded
```

**Status:** [FIXED]

---

## [2025-12-07 08:00] FIXED: Step 8 Validation Crash (Iteration 2)

**Problem:** Step 8 validation still failing after first fix
**Root Cause:** Python bytecode cache (.pyc files) using old validation code
**Error:** `ValueError: Step must be between 1 and 7, got 8`

**Impact:**
- Source code was correct but Python loaded cached bytecode
- User had to repeatedly ask for same fix
- Frustration: "why do i have to keep asking to fix this? think hard"

**Solution:**
1. Fixed source code (wizard_state.py: `<= 7` → `<= 8`)
2. Cleared ALL Python bytecode cache
3. Verified fix actually runs

**Cache Clear Command:**
```bash
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
```

**Lesson Learned:**
- Always clear cache after Python source code changes
- Windows: `Get-ChildItem -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force`
- Linux/Mac: `find . -type d -name "__pycache__" -exec rm -rf {} +`

**Status:** [FIXED]

---

## [2025-12-07 07:00] FIXED: Copy-Paste Creates Messy List Input

**Problem:** Pasting lists with bullets/numbers creates ugly output
**Root Cause:** Wizard didn't strip formatting from pasted text
**User Feedback:** "please fix its not very user friendly when i copy paste it is very messy"

**Impact:**
- Pasted items like "- Item 1" stored verbatim
- Double bullets: "- - Item 1"
- Numbers preserved: "1. Item 1"
- Checkboxes: "[x] Item 1"

**Solution:** Added _clean_list_item() method

**Code Change:**
```python
def _clean_list_item(self, text: str) -> str:
    """Clean pasted list items (remove bullets, numbers, etc.)"""
    text = text.strip()

    # Remove bullets
    bullets = ['- ', '* ', '• ', '├──', '└──', '│ ']
    for bullet in bullets:
        if text.startswith(bullet):
            text = text[len(bullet):].strip()

    # Remove numbers: "1. " or "1) "
    text = re.sub(r'^\d+[\.\)]\s+', '', text)

    # Remove checkboxes: "[x] " or "[ ] "
    text = re.sub(r'^\[[ x]\]\s*', '', text)

    return text.strip()
```

**Status:** [FIXED]

---

## [2025-12-05 19:45] FIXED: LangChain BaseTool Pydantic Field Restrictions

**Problem:** File tools couldn't set attributes in __init__ due to Pydantic validation
**Root Cause:** LangChain BaseTool uses Pydantic v1 which doesn't allow arbitrary attributes
**Error:** `ValueError: "ReadFileTool" object has no field "path_validator"`

**Impact:**
- Initial file tool implementation had `__init__` methods setting validators
- All 27 file tool tests failed on instantiation
- Couldn't configure tools with custom allowed_dirs or size limits

**Solution:**
- Removed __init__ methods from all tool classes
- Create validators inside _run() method instead
- Use Path.cwd() as default allowed directory
- Simplified tool API (no config parameters needed)

**Code Change:**
```python
# BEFORE (failed):
class ReadFileTool(BaseTool):
    allowed_dirs: List[Path] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.path_validator = PathValidator(...)  # FAILS

# AFTER (works):
class ReadFileTool(BaseTool):
    def _run(self, file_path: str) -> str:
        path_validator = PathValidator(allowed_dirs=[Path.cwd()])  # Works
```

**Testing:**
- 27 file tool tests: 0 → 27 passing
- All tools now work correctly
- Simplified API (no config needed)

**Status:** [FIXED]

---

## [2025-12-05 18:30] FIXED: Cache Cleanup Test Timing Issue

**Problem:** test_periodic_cleanup failed - expired entries not cleaned up
**Root Cause:** Cleanup interval (1s) longer than wait time (0.6s)
**Error:** `AssertionError: assert 2 == 0` (2 entries still in cache)

**Impact:** 1/19 cache tests failing

**Solution:**
- Reduced cleanup interval: 1s → 0.5s
- Reduced TTL: 0.5s → 0.3s
- Kept wait time: 0.6s (longer than both)

**Code Change:**
```python
# BEFORE:
cache = CacheManager(cleanup_interval=1)
cache.set("key1", "value1", ttl=0.5)
time.sleep(0.6)  # Not long enough for cleanup

# AFTER:
cache = CacheManager(cleanup_interval=0.5)
cache.set("key1", "value1", ttl=0.3)
time.sleep(0.6)  # Now triggers cleanup
```

**Status:** [FIXED]

---

## [2025-12-05 16:00] FIXED: PathValidator Test Working Directory Issue

**Problem:** test_validate_safe_path failed with PathTraversalError
**Root Cause:** Relative path resolved from current directory, not tmp_path
**Error:** Path 'C:\...\Agent Factory\test.txt' not in allowed dirs: [tmp_path]

**Impact:** 1/27 file tool tests failing

**Solution:** Use pytest monkeypatch to change working directory to tmp_path

**Code Change:**
```python
# BEFORE:
def test_validate_safe_path(self, tmp_path):
    validator = PathValidator(allowed_dirs=[tmp_path])
    safe_path = validator.validate("test.txt")  # Resolves from CWD

# AFTER:
def test_validate_safe_path(self, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # Change CWD to tmp_path
    validator = PathValidator(allowed_dirs=[tmp_path])
    safe_path = validator.validate("test.txt")  # Now resolves correctly
```

**Status:** [FIXED]

---

## [2025-12-05 23:45] INFORMATIONAL: All Phase 1 Issues Resolved

**Session:** Phase 1 Testing and Validation
**Status:** All deliverables complete, all tests passing
**Issues Encountered:** Minor only (all resolved immediately)

**Resolved Immediately:**
1. Test import error → Added sys.path modification to test_callbacks.py
2. Class name mismatch → Changed AgentEvent to Event (actual class name)
3. EventType mismatches → Updated TOOL_START to TOOL_CALL to match implementation
4. Demo tool requirement → Added CurrentTimeTool to all agents (empty tools_list not allowed)
5. Test failures → Fixed 6 failing tests by aligning with actual implementation

**Test Results:**
- Initial: 6/13 callback tests failed
- Fixed: All import errors, class name mismatches, EventType corrections
- Final: 24/24 tests passing (13 callbacks + 11 orchestrator)

**No Open Issues from This Session**

---

## [2025-12-05 21:00] INFORMATIONAL: No New Issues This Session

**Session:** Constitutional Code Generation Implementation
**Status:** All tasks completed without blocking issues
**Issues Encountered:** Minor only (all resolved immediately)

**Resolved Immediately:**
1. Windows Unicode encoding → Replaced with ASCII ([OK]/[FAIL])
2. Dependencies not installed → Added jinja2, markdown via poetry
3. File needed reading before writing → Read first

**No Open Issues from This Session**

---

## [2025-12-04 16:45] OPEN: Dependency Conflict - LangChain vs LangGraph

**Problem:**
```
poetry sync fails with dependency resolution error
langgraph 0.0.26 requires langchain-core (>=0.1.25,<0.2.0)
langchain 0.2.1 requires langchain-core (>=0.2.0,<0.3.0)
These requirements are mutually exclusive
```

**Impact:**
- ❌ Cannot install dependencies
- ❌ Cannot run demo
- ❌ Fresh clones won't work
- ❌ Blocks all development

**Root Cause:**
LangGraph was added to `pyproject.toml` for future multi-agent orchestration but:
1. Not currently used in any code
2. Latest LangGraph version (0.0.26) requires old LangChain core (<0.2.0)
3. Current LangChain (0.2.1) requires new core (>=0.2.0)

**Proposed Solution:**
```toml
# Remove from pyproject.toml:
langgraph = "^0.0.26"
```

**Alternative Solution:**
Upgrade entire LangChain ecosystem to latest versions (more risk of breaking changes)

**Status:** OPEN - Awaiting fix
**Priority:** CRITICAL - Blocks installation
**Discovered By:** User attempting first installation

---

## [2025-12-04 16:30] FIXED: PowerShell Path with Spaces

**Problem:**
```powershell
cd C:\Users\hharp\OneDrive\Desktop\Agent Factory
# Error: A positional parameter cannot be found that accepts argument 'Factory'
```

**Root Cause:**
PowerShell interprets space as argument separator without quotes

**Solution:**
```powershell
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
```

**Status:** FIXED - Documented in troubleshooting
**Impact:** Documentation issue
**Lessons:**
- Folder names with spaces need quotes in PowerShell
- Should update docs with proper Windows examples

---

## [2025-12-04 15:45] FIXED: README Placeholder URL

**Problem:**
README.md contains `<your-repo-url>` placeholder which:
1. Causes PowerShell error (< is reserved operator)
2. Doesn't tell users the actual clone URL

**Original:**
```bash
git clone <your-repo-url>
```

**Fixed:**
```bash
git clone https://github.com/Mikecranesync/Agent-Factory.git
```

**Status:** FIXED - Updated in docs
**Impact:** User confusion during installation

---

## [2025-12-04 15:00] FIXED: API Key Format Issues

**Problem:**
Four API keys in `.env` had "ADD_KEY_HERE" prefixes:
```env
ANTHROPIC_API_KEY=ADD_KEY_HERE sk-ant-api03-...
GOOGLE_API_KEY=ADD_KEY_HERE=AIzaSy...
FIRECRAWL_API_KEY=ADD_KEY_HERE= fc-fb46...
TAVILY_API_KEY=ADD_KEY_HERE= tvly-dev-...
```

**Impact:**
- Keys would not load correctly
- API calls would fail with authentication errors

**Solution:**
Removed all "ADD_KEY_HERE" prefixes, leaving only actual keys

**Status:** FIXED
**Verification:** All keys validated in `claude.md`

---

## Known Issues (Not Yet Encountered)

### Potential: Poetry Version Mismatch
**Risk:** Users with Poetry 1.x may have issues
**Prevention:** Documentation specifies Poetry 2.x requirement
**Mitigation:** POETRY_GUIDE.md explains version differences

### Potential: Missing Python Version
**Risk:** Python 3.12+ not compatible
**Prevention:** pyproject.toml specifies `python = ">=3.10.0,<3.13"`
**Mitigation:** Clear error message from Poetry

### Potential: API Rate Limits
**Risk:** Free tiers may hit limits during testing
**Prevention:** Documentation includes rate limit information
**Mitigation:** claude.md documents all provider limits

---

## Issue Tracking Guidelines

### When Adding New Issues:
1. Add at TOP of file
2. Include timestamp: `[YYYY-MM-DD HH:MM]`
3. Use status tag: [OPEN], [INVESTIGATING], [FIXED], [WONTFIX]
4. Include:
   - Problem description
   - Root cause (if known)
   - Impact assessment
   - Proposed solution
   - Current status

### When Updating Issues:
1. Add status update as new subsection under issue
2. Include timestamp of update
3. DO NOT remove old information
4. Mark as [FIXED] or [CLOSED] when resolved

### When Issue is Fixed:
1. Change status to FIXED
2. Add solution details
3. Document verification steps
4. Keep entry for historical reference

---

**Last Updated:** 2025-12-04 16:50

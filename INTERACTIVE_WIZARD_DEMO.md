# Interactive Agent Creation Wizard - Demo

## What This Is

The `agentcli create` command launches an interactive wizard that guides you through creating a custom agent step-by-step.

## Commands

### List Available Templates
```bash
poetry run python agentcli.py create --list-templates
```

**Output:**
```
========================================================================
AVAILABLE TEMPLATES
========================================================================

researcher:
  Research assistant for finding accurate technical information

coder:
  Code analysis and file manipulation assistant

analyst:
  Data analysis and reporting assistant

file_manager:
  File organization and management assistant
```

### Create Agent from Scratch
```bash
poetry run python agentcli.py create
```

### Create Agent from Template
```bash
poetry run python agentcli.py create --template researcher
```

## Interactive Wizard Flow

The wizard guides you through 7 steps:

### Step 1: Agent Basics
- **Agent name**: Unique identifier (e.g., "ResearchAgent")
- **Version**: Semantic version (default: v1.0)
- **Owner**: Your name or team
- **Purpose**: One-line description of what the agent does

### Step 2: Scope - What CAN this agent do?
- Shows pre-filled capabilities (if using template)
- Add additional capabilities one at a time
- Press Enter on blank line when done

### Step 3: Scope - What should agent NEVER do?
- Shows pre-filled restrictions (if using template)
- Add additional restrictions one at a time
- Press Enter on blank line when done

### Step 4: Invariants (Rules that MUST NEVER be violated)
- Shows pre-filled invariants (if using template)
- Add additional invariants in format: `Name: Description`
- Press Enter on blank line when done

### Step 5: Tool Selection
- Shows currently selected tools (from template)
- Displays available tools organized by category:
  - Research (Wikipedia, DuckDuckGo, Tavily, CurrentTime)
  - File Operations (Read, Write, List, Search)
  - Code Tools (GitStatus)
- Select tools by entering comma-separated numbers (e.g., `1,2,5`)
- Press Enter to keep current selection

### Step 6: Behavior Examples
- Optionally provide examples of CORRECT behavior
  - User query + Expected agent response
- Optionally provide examples of WRONG behavior
  - User query + What agent should NOT say
- Template already includes examples
- Press Enter to skip adding more

### Step 7: Success Criteria
- **Latency target** (seconds): Max response time (default: 30)
- **Cost per query** (USD): Max API cost (default: 0.10)
- **Accuracy requirement** (%): Expected accuracy (default: 95)

### Review and Confirm
- Shows complete agent specification summary
- Confirms to proceed with generation (y/n)

### Generation
If confirmed:
1. Creates spec markdown file in `specs/`
2. Generates Python agent code in `agents/`
3. Generates pytest test file in `tests/`
4. Shows next steps

## Example Session

```bash
poetry run python agentcli.py create --template researcher

========================================================================
AGENT FACTORY - INTERACTIVE AGENT CREATOR
========================================================================

Starting with template: Research assistant for finding accurate technical information

[1/7] Agent Basics
------------------------------------------------------------------------
Agent name: MyResearchAgent
Version [v1.0]:
Owner/Author: john-doe

[2/7] Scope - What CAN this agent do?
------------------------------------------------------------------------
Current capabilities:
  - Search web sources (Wikipedia, documentation, Stack Overflow)
  - Synthesize information from multiple sources
  - Provide citations for all claims
  - Ask clarifying questions when query is ambiguous
  - Admit when information is not found or uncertain

Add capabilities (press Enter when done):
  + Compare multiple viewpoints
  +

[3/7] Scope - What should this agent NEVER do?
------------------------------------------------------------------------
Current restrictions:
  - Make up information when sources are unavailable
  - Access private/internal company data
  - Perform actions that modify external systems
  - Provide medical, legal, or financial advice
  - Execute code or commands

Add restrictions (press Enter when done):
  -

[4/7] Invariants (Rules that MUST NEVER be violated)
------------------------------------------------------------------------
Current invariants:
  - Accuracy First: Never fabricate sources or citations
  - User Safety: Refuse requests that could cause harm
  - Data Privacy: Never log or store sensitive user data
  - Cost Limit: Each query must cost < $0.10 in API usage
  - Latency: Response time must be < 30 seconds for 95% of queries

Add invariants (press Enter when done):
Format: Name: Description
  >

[5/7] Tool Selection
------------------------------------------------------------------------
Currently selected tools:
  - WikipediaSearchTool
  - DuckDuckGoSearchTool
  - CurrentTimeTool

Available tools by category:

Research:
  [1] WikipediaSearchTool - Search Wikipedia
  [2] DuckDuckGoSearchTool - Web search
  [3] TavilySearchTool - Advanced web search
  [4] CurrentTimeTool - Get current time/date

File Operations:
  [5] ReadFileTool - Read file contents
  [6] WriteFileTool - Write to files
  [7] ListDirectoryTool - List directory
  [8] FileSearchTool - Search in files

Code Tools:
  [9] GitStatusTool - Check git status

Select tools (comma-separated numbers, or press Enter to skip): 1,2,3,4

[6/7] Behavior Examples
------------------------------------------------------------------------
Existing examples: 3

Provide an example of CORRECT agent behavior (or press Enter to skip):
  User query:

Provide an example of WRONG agent behavior (or press Enter to skip):
  User query:

[7/7] Success Criteria
------------------------------------------------------------------------
Latency target (seconds) [30]:
Cost per query (USD) [0.10]: 0.05
Accuracy requirement (%) [95]: 98

========================================================================
REVIEW YOUR AGENT SPECIFICATION
========================================================================

Name: MyResearchAgent v1.0
Owner: john-doe
Purpose: Helps users find accurate technical information quickly from reliable sources without manual searching

Scope (5 in / 5 out):
  IN:
    - Search web sources (Wikipedia, documentation, Stack Overflow)
    - Synthesize information from multiple sources
    - Provide citations for all claims
    - Ask clarifying questions when query is ambiguous
    - Admit when information is not found or uncertain
  OUT:
    - Make up information when sources are unavailable
    - Access private/internal company data
    - Perform actions that modify external systems
    - Provide medical, legal, or financial advice
    - Execute code or commands

Invariants: 5
Tools: 4
Behavior Examples: 3
Success Criteria: latency=30s, cost=$0.05, accuracy=98%

Generate agent? (y/n): y

========================================================================
GENERATING AGENT FILES
========================================================================

[1/3] Creating spec file...
  [OK] specs/MyResearchAgent-v1.0.md

[2/3] Generating agent code...
  [OK] agents/myresearchagent_v1_0.py

[3/3] Generating test suite...
  [OK] tests/test_myresearchagent_v1_0.py

========================================================================
SUCCESS - Agent Created!
========================================================================

Files created:
  - specs/MyResearchAgent-v1.0.md
  - agents/myresearchagent_v1_0.py
  - tests/test_myresearchagent_v1_0.py

Next steps:
  1. Review spec: specs/MyResearchAgent-v1.0.md
  2. Review agent code: agents/myresearchagent_v1_0.py
  3. Run tests: poetry run pytest tests/test_myresearchagent_v1_0.py -v
  4. Refine and iterate!
```

## Benefits

1. **Template-based**: Start with proven patterns (researcher, coder, analyst, file_manager)
2. **Guided**: Step-by-step prompts ensure no required fields are missed
3. **Validated**: Input validation ensures correct data types
4. **Complete**: Generates spec + agent code + tests in one flow
5. **Iterative**: Can review and regenerate as needed

## Files Generated

1. **Spec file** (`specs/<name>-<version>.md`):
   - Complete AGENTS.md-compliant specification
   - All sections properly formatted
   - Ready for version control

2. **Agent code** (`agents/<name>_<version>.py`):
   - Imports and dependencies
   - Data models (if defined)
   - `create_agent()` function
   - Runnable demo in `if __name__ == "__main__"`

3. **Test suite** (`tests/test_<name>_<version>.py`):
   - Tests for each behavior example
   - Performance validation
   - Anti-sycophancy tests
   - Ready to run with pytest

## Validation

After creation, validate the agent:

```bash
# Validate spec format
poetry run python agentcli.py validate specs/MyResearchAgent-v1.0.md

# Run tests
poetry run pytest tests/test_myresearchagent_v1_0.py -v

# Try the agent
poetry run python agents/myresearchagent_v1_0.py
```

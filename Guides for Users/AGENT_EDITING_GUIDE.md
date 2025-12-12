# Agent Editing Guide

## 🎉 NEW FEATURE: Interactive Agent Editing

You can now edit existing agents without manual file editing!

---

## Quick Start

### List All Editable Agents
```bash
poetry run python agentcli.py edit --list
```

**Output:**
```
EDITABLE AGENTS
========================================================================

  - bob-1
  - callbacks-v1.0
  - factory-v1.0
  - orchestrator-v1.0

Edit with: agentcli edit <agent-name>
```

### Edit an Agent
```bash
poetry run python agentcli.py edit bob-1
```

---

## What You Can Edit

### 1. Tools (Add/Remove)
**Current Implementation:** ✅ Fully functional

Add or remove tools from your agent's toolset.

**Example Session:**
```
========================================================================
EDIT TOOLS
========================================================================

Current Tools:
  [X] WikipediaSearchTool - Search Wikipedia for factual information
  [X] DuckDuckGoSearchTool - Web search via DuckDuckGo
  [X] TavilySearchTool - AI-optimized search
  ... (6 more)

Available Tools by Category:

RESEARCH:
  [X] WikipediaSearchTool - Search Wikipedia
  [X] DuckDuckGoSearchTool - Web search
  [X] TavilySearchTool - AI-optimized search
  [ ] CurrentTimeTool - Get current date/time

FILE:
  [X] ReadFileTool - Read file contents
  [X] WriteFileTool - Write to files
  [ ] ListDirectoryTool - List directory contents
  [ ] FileSearchTool - Search for text patterns

Commands:
  add <tool-name>     Add a tool
  remove <tool-name>  Remove a tool
  collection <name>   Load tool collection
  done                Finish editing

> add WebBrowserTool

[+] Added WebBrowserTool

> collection full_power

[✓] Loaded collection: full_power (9 tools)

> done

Tools updated! (9 -> 10 tools)
```

**Available Tool Collections:**
- `research_basic` - Wikipedia, DuckDuckGo, Time (3 tools)
- `research_advanced` - + Tavily AI search (4 tools)
- `file_operations` - Read, Write, List, Search files (4 tools)
- `code_analysis` - Read, Search, List, Git (4 tools)
- `full_power` - All research + file tools (9 tools)

---

### 2. Invariants (Rules)
**Current Implementation:** ✅ Fully functional

Edit the rules your agent must never violate.

**Example Session:**
```
========================================================================
EDIT INVARIANTS
========================================================================

Current Invariants:

  1. Evidence-Based: All claims backed by verifiable sources
  2. Ethical Research: Never recommend exploitative practices
  3. Transparency: Always disclose uncertainty
  ... (5 more)

Commands:
  add                 Add new invariant
  remove <number>     Remove invariant
  edit <number>       Edit invariant
  done                Finish editing

> add

Invariant (format: Name: Description): Fast Response: Deliver results in < 60 seconds

[+] Added invariant

> edit 3

Editing: Transparency: Always disclose uncertainty
New invariant: Transparency: Always disclose when information is uncertain or based on limited data

[✓] Updated

> remove 5

[-] Removed: Old Rule: Description here

> done

Invariants updated! (8 -> 8)
```

---

### 3. Behavior Examples
**Status:** 🚧 Coming soon

Will allow adding/editing example conversations showing correct/incorrect behavior.

---

### 4. Purpose & Scope
**Status:** 🚧 Coming soon

Will allow editing the agent's purpose statement and in/out of scope items.

---

### 5. System Prompt
**Status:** 🚧 Coming soon

Will allow editing the system prompt template.

---

### 6. LLM Settings
**Status:** 🚧 Coming soon

Will allow changing:
- Model (gpt-4, gpt-4o-mini, claude-3-sonnet, etc.)
- Temperature (0.0 - 1.0)
- Provider (openai, anthropic, google)

---

### 7. Success Criteria
**Status:** 🚧 Coming soon

Will allow editing latency, cost, and accuracy targets.

---

## Review & Save

After making changes, select option **[8] Review & Save**:

```
========================================================================
REVIEW CHANGES
========================================================================

  tools: 9 -> 10
  invariants: 8 -> 9

Files to update:
  - specs/bob-1.md (spec)
  - agents/unnamedagent_v1_0.py (regenerate)
  - tests/test_unnamedagent_v1_0.py (regenerate)

Save changes? [y/N]: y

[1/3] Updating spec... ✓
[2/3] Regenerating agent... ✓
[3/3] Regenerating tests... ✓

Agent updated successfully!
```

---

## Complete Workflow Example

**Goal:** Add WebBrowserTool to Bob for web scraping

```bash
# 1. Edit Bob
poetry run python agentcli.py edit bob-1

# 2. Select [1] Tools
> 1

# 3. Add WebBrowserTool
> add WebBrowserTool

# 4. Done editing tools
> done

# 5. Back to main menu, select [8] Review & Save
> 8

# 6. Confirm save
Save changes? [y/N]: y

# 7. Test the updated agent
poetry run python agents/unnamedagent_v1_0.py
```

---

## Tips & Tricks

### Tool Selection Shortcuts

**Load entire collection instead of adding one-by-one:**
```
> collection full_power
```

**Add multiple tools quickly:**
```
> add WikipediaSearchTool
> add DuckDuckGoSearchTool
> add TavilySearchTool
> done
```

### Invariant Formatting

Use consistent format for clarity:
```
Name: Description (brief, actionable)

Examples:
✓ Good: "Evidence-Based: All claims backed by sources"
✗ Bad: "Try to be accurate when possible"
```

### Canceling Without Saving

Select option **[9] Cancel** to discard all changes.

---

## Current Limitations

**What's Not Yet Implemented:**
- Behavior example editing
- Purpose/scope editing
- System prompt editing
- LLM settings editing
- Success criteria editing

**These features are coming soon!** For now, edit those sections manually in the spec file.

---

## Troubleshooting

### Error: "Spec file not found"
```bash
# List available agents
poetry run python agentcli.py edit --list

# Use exact name from list
poetry run python agentcli.py edit bob-1
```

### Changes Not Showing Up
Make sure you selected **[8] Review & Save** and confirmed with **y**.

### Tool Not Found
Check available tools:
```
> help
```

Or browse the tool registry in the edit menu.

---

## Advanced: Manual Editing

If you need to edit features not yet in the UI:

### 1. Edit the Spec
```bash
# Edit spec file directly
nano specs/bob-1.md
```

### 2. Regenerate Agent
```bash
# Rebuild from updated spec
poetry run python agentcli.py build bob-1
```

### 3. Test
```bash
# Run the updated agent
poetry run python agents/unnamedagent_v1_0.py
```

---

## Future Features

Coming soon to the agent editor:
- 📝 Behavior example library (pre-built examples)
- 🎨 Visual tool picker (GUI-style selection)
- 🔄 A/B testing (compare tool configurations)
- 📊 Performance tracking (latency/cost after edits)
- 🔍 Smart suggestions (recommended tools based on purpose)
- 💾 Version history (rollback to previous configs)
- 🚀 One-click deploy (edit + test + deploy workflow)

---

## Summary

**What Works Now:**
- ✅ Add/remove tools interactively
- ✅ Use pre-configured tool collections
- ✅ Edit invariants
- ✅ Auto-regenerate spec + code + tests

**What's Coming:**
- 🚧 Edit all other agent sections
- 🚧 Visual tool selection
- 🚧 Smart recommendations

**How to Use:**
```bash
poetry run python agentcli.py edit bob-1
```

---

**Happy Editing!** 🎉

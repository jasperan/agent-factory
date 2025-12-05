# Next Actions
> Prioritized list of immediate tasks and future enhancements
> **Format:** Priority-ordered sections, timestamped updates

---

## [2025-12-05 21:15] Current Priorities - Post Constitutional Implementation

### 🔴 CRITICAL - Immediate Action Required

#### 1. Create Orchestrator Demo
**Priority:** HIGHEST - Validate constitutional implementation
**Task:** Create `agent_factory/examples/orchestrator_demo.py`
**Estimated Time:** 30 minutes

**Requirements:**
- Register 2+ agents (research, coding)
- Test keyword routing with 3+ queries
- Demonstrate event logging
- Show direct routing capability

**Test Command:**
```bash
poetry run python agent_factory/examples/orchestrator_demo.py
```

**Status:** Ready to implement

---

#### 2. Write Basic Tests
**Priority:** HIGH - Validate spec compliance
**Task:** Create tests for callbacks and orchestrator
**Estimated Time:** 1 hour

**Tests Needed:**
- `tests/test_callbacks.py`: EventBus, Event, EventType
- `tests/test_orchestrator.py`: Registration, routing, events

**Status:** Pending

---

### 🟢 COMPLETED IN THIS SESSION

✅ Constitutional system foundation (factory.py)
✅ Hybrid documentation applied (callbacks.py, orchestrator.py)
✅ SpecParser and SpecValidator working
✅ Jinja2 templates created
✅ All core modules tested and importing
✅ Git checkpoint committed (26276ca)

---

## [2025-12-04 18:30] Previous Priorities

### 🔴 CRITICAL - Immediate Action Required

#### 1. Begin Phase 1 Implementation
**Status:** ✅ COMPLETE - Constitutional approach implemented instead

---

### 🟡 HIGH - After Phase 1 Complete

#### 2. Fix Dependency Conflict
**Priority:** HIGH - Blocks fresh installations
**Issue:** langgraph 0.0.26 incompatible with langchain 0.2.1
**Solution:** Remove langgraph from pyproject.toml
**Impact:** Unblocks installation for all users
**Estimated Time:** 5 minutes

**Steps:**
1. Edit pyproject.toml
2. Remove line: `langgraph = "^0.0.26"`
3. Test: `poetry sync` should succeed
4. Commit fix with message: "fix: remove langgraph dependency causing conflict"
5. Push to GitHub

**Status:** Deferred until after Phase 1

---

### 🟡 HIGH - Should Complete Soon

#### 2. Test Installation After Fix
**Priority:** HIGH - Verify fix works
**Depends On:** Action #1 (dependency fix)
**Estimated Time:** 10 minutes

**Steps:**
1. Run `poetry sync` - should succeed
2. Run demo: `poetry run python agent_factory/examples/demo.py`
3. Verify research agent works
4. Verify coding agent works
5. Check no errors in output

**Success Criteria:**
- poetry sync completes without errors
- Demo runs and produces agent responses
- No import errors or missing dependencies

---

#### 3. Update Documentation with Actual URLs
**Priority:** HIGH - Improves user experience
**Estimated Time:** 5 minutes

**Files to Update:**
- README.md - Ensure all `<your-repo-url>` replaced
- QUICKSTART.md - Verify clone URL is correct
- HOW_TO_BUILD_AGENTS.md - Check for any placeholders

**Search and replace:**
```bash
# Find any remaining placeholders
<your-repo-url> → https://github.com/Mikecranesync/Agent-Factory.git
```

---

#### 4. Add Windows-Specific Setup Notes
**Priority:** MEDIUM-HIGH - User encountered Windows issues
**Estimated Time:** 15 minutes

**Add to QUICKSTART.md:**
```markdown
## Windows Users

### PowerShell Path with Spaces
If your path contains spaces, use quotes:
```powershell
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
```

### Poetry on Windows
Make sure Poetry is in your PATH. To verify:
```powershell
poetry --version
```

If not found, add to PATH or reinstall Poetry.
```

**Issues to Document:**
- Path quoting for spaces
- PowerShell vs CMD differences
- Poetry PATH configuration

---

### 🟢 MEDIUM - Complete When Time Allows

#### 5. Commit Memory Files to GitHub
**Priority:** MEDIUM - Preserve context
**Estimated Time:** 5 minutes

**Files to Add:**
- PROJECT_CONTEXT.md
- ISSUES_LOG.md
- DEVELOPMENT_LOG.md
- DECISIONS_LOG.md
- NEXT_ACTIONS.md (this file)

**Commit Message:**
```
docs: add memory system for context preservation

- PROJECT_CONTEXT.md: project state and overview
- ISSUES_LOG.md: chronological problem tracking
- DEVELOPMENT_LOG.md: activity timeline
- DECISIONS_LOG.md: technical decisions with rationale
- NEXT_ACTIONS.md: prioritized task list

All files use reverse chronological order with timestamps
for easy context loading in future sessions.
```

---

#### 6. Add Issue Tracking to GitHub
**Priority:** MEDIUM - Professional project management
**Estimated Time:** 10 minutes

**Create GitHub Issues:**
1. ✅ "Dependency conflict between langgraph and langchain" (can close after #1)
2. "Add Windows-specific setup documentation"
3. "Create comprehensive test suite"
4. "Add example agents for more use cases"

**Labels to Create:**
- bug (red)
- documentation (blue)
- enhancement (green)
- help wanted (purple)

---

#### 7. Create CONTRIBUTING.md
**Priority:** MEDIUM - Encourage contributions
**Estimated Time:** 20 minutes

**Contents:**
- How to report bugs
- How to suggest features
- Code style guidelines
- Pull request process
- Development setup guide
- Testing requirements

---

#### 8. Add Example Agents
**Priority:** MEDIUM - Showcase capabilities
**Estimated Time:** 30 minutes each

**Suggested Examples:**
1. **Data Analyst Agent**
   - Tools: File reading, web search, current time
   - Use case: Analyze data files and research context

2. **Documentation Agent**
   - Tools: File reading, writing, directory listing
   - Use case: Generate docs from code

3. **Debugging Assistant**
   - Tools: File reading, git status, web search
   - Use case: Analyze error logs and suggest fixes

**Location:** `agent_factory/examples/`

---

## Future Enhancements

### Phase 2 - Core Framework

#### Multi-Agent Orchestration
**Description:** Add support for multiple agents working together
**Requirements:**
- Fix langgraph dependency conflict first
- Study langgraph patterns
- Implement agent coordination
- Add examples of agent teams

**Estimated Effort:** 2-3 days

---

#### Advanced Memory Systems
**Description:** Beyond simple ConversationBufferMemory
**Options:**
- ConversationSummaryMemory (compress long conversations)
- ConversationBufferWindowMemory (sliding window)
- VectorStore memory (semantic similarity)
- Redis memory (persistent storage)

**Estimated Effort:** 1-2 days

---

#### Tool Categories Expansion
**Description:** Add more specialized tool categories
**Suggested Categories:**
- "data": CSV, JSON, Excel reading/writing
- "web": HTTP requests, web scraping, API calls
- "analysis": Data analysis, statistics, visualization
- "communication": Email, Slack, Discord integration

**Estimated Effort:** 1 week

---

#### Streaming Support
**Description:** Stream agent responses token-by-token
**Benefits:**
- Better UX for long responses
- Real-time feedback
- Reduced perceived latency

**Requirements:**
- LangChain streaming callbacks
- Update examples for streaming
- Document streaming patterns

**Estimated Effort:** 2-3 days

---

### Phase 3 - Production Features

#### Error Handling & Retries
**Description:** Robust error handling with exponential backoff
**Features:**
- Automatic retry on rate limits
- Graceful degradation
- Detailed error logging
- Fallback LLM providers

**Estimated Effort:** 1 week

---

#### Performance Monitoring
**Description:** Track agent performance metrics
**Metrics:**
- Response time
- Token usage
- Tool invocation counts
- Error rates
- Cost tracking

**Tools:**
- LangSmith integration
- Custom analytics dashboard
- Export to CSV/JSON

**Estimated Effort:** 1 week

---

#### Configuration Management
**Description:** Beyond .env files
**Features:**
- YAML/JSON config files
- Environment-specific configs (dev, prod)
- Config validation
- Secrets management integration (AWS Secrets, Azure Key Vault)

**Estimated Effort:** 3-4 days

---

#### Testing Suite
**Description:** Comprehensive automated testing
**Coverage:**
- Unit tests for all tools
- Integration tests for agents
- Mock LLM for faster tests
- CI/CD pipeline (GitHub Actions)

**Estimated Effort:** 1 week

---

### Phase 4 - Advanced Features

#### Web UI
**Description:** Browser-based interface for Agent Factory
**Tech Stack:**
- Backend: FastAPI
- Frontend: React or Streamlit
- WebSocket for streaming

**Features:**
- Visual agent builder
- Interactive chat interface
- Tool library browser
- Configuration editor

**Estimated Effort:** 2-3 weeks

---

#### Agent Templates Library
**Description:** Pre-built agent templates for common tasks
**Templates:**
- Customer Service Bot
- Code Review Assistant
- Content Writer
- Data Analysis Helper
- Project Manager
- Learning Tutor

**Estimated Effort:** 1 week

---

#### Plugin System
**Description:** Allow third-party tool plugins
**Features:**
- Plugin discovery
- Plugin installation (pip)
- Plugin validation
- Plugin marketplace

**Estimated Effort:** 2 weeks

---

## Quick Wins (Can Do Anytime)

### Documentation Improvements
- [ ] Add architecture diagram
- [ ] Create video tutorial
- [ ] Add FAQ section
- [ ] Create troubleshooting flowchart

### Code Quality
- [ ] Add type hints to all functions
- [ ] Add docstrings to all classes
- [ ] Run linter (black, flake8)
- [ ] Add pre-commit hooks

### Examples
- [ ] Add Jupyter notebook examples
- [ ] Create interactive Colab notebook
- [ ] Add CLI tool example
- [ ] Create Discord bot example

---

## Known Technical Debt

### 1. Hard-coded Prompt Hub Names
**Location:** agent_factory/core/agent_factory.py:143, 148
**Issue:** "hwchase17/react" and "hwchase17/structured-chat-agent" hardcoded
**Better Solution:** Make prompts configurable or allow custom prompts
**Priority:** LOW - Works fine, just inflexible

---

### 2. Limited Error Messages
**Location:** Various tool _run() methods
**Issue:** Generic error handling with str(e)
**Better Solution:** Custom exceptions with helpful messages
**Priority:** MEDIUM - Impacts debugging

---

### 3. No Input Validation
**Location:** Tool inputs
**Issue:** Relies on Pydantic but no custom validators
**Better Solution:** Add validators for file paths, URLs, etc.
**Priority:** MEDIUM - Security concern

---

### 4. Temperature Defaults
**Location:** agent_factory/core/agent_factory.py
**Issue:** Different providers have different default temperatures
**Better Solution:** Document provider-specific defaults
**Priority:** LOW - Minor inconsistency

---

## Maintenance Tasks

### Regular Updates
- [ ] Check for LangChain updates monthly
- [ ] Update dependencies quarterly
- [ ] Review security advisories weekly
- [ ] Update documentation with community feedback

### Community Management
- [ ] Respond to GitHub issues within 48 hours
- [ ] Review pull requests within 1 week
- [ ] Update changelog with releases
- [ ] Post updates on social media

---

## Success Metrics

### Short Term (1 month)
- ✅ Repository published
- ⏳ Dependency conflict resolved
- ⏳ 10+ GitHub stars
- ⏳ 3+ external users successfully installed
- ⏳ All examples tested and working

### Medium Term (3 months)
- [ ] 50+ GitHub stars
- [ ] 5+ community contributions
- [ ] 10+ custom agents shared by users
- [ ] Featured in LangChain showcase
- [ ] Complete test coverage

### Long Term (6 months)
- [ ] 200+ GitHub stars
- [ ] Active community Discord/Slack
- [ ] 20+ third-party tool plugins
- [ ] Used in production by 5+ companies
- [ ] Documentation site with tutorials

---

**Last Updated:** 2025-12-04 16:50
**Next Review:** After completing CRITICAL actions


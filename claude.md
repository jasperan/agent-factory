# CLAUDE.md

## What This Is

Agent Factory - a framework for building multi-agent AI systems. Part of a larger pipeline that turns ideas into live apps in 24 hours.

**You are building the engine that turns blueprints into working agents.**

**But it's bigger than that:** This engine powers RIVET (industrial maintenance platform) → which generates knowledge → which becomes the standard → which robots license → which creates perpetual income. See `MASTER_ROADMAP.md` for the full vision (Weeks → Years → Decades).

---

## The Meta Structure: Agent Factory → RIVET

Agent Factory is the engine. **RIVET** is the product it powers.

### The Full System (3 Layers)

**Layer 1: Knowledge Factory**
- Scrapers that harvest industrial maintenance data (Reddit, Stack Overflow, PDFs, forums, YouTube)
- Validators that verify accuracy against official documentation
- Vector database (Pinecone) storing validated "Knowledge Atoms"
- Ensures data integrity via 6-stage validation pipeline

**Layer 2: Agent Orchestration (← YOU ARE HERE)**
- Agent Factory builds and manages these agents
- Agents route queries, generate responses, publish content, flag for human help
- This is what you're building right now

**Layer 3: Distribution & Monetization**
- Social media distribution (YouTube, TikTok, Reddit, Twitter/X, LinkedIn)
- Premium troubleshooting calls ($50-100/hour)
- B2B integrations (CMMS vendors like ServiceTitan, MaintainX)
- Data licensing (clean industrial datasets)

### What is RIVET?

RIVET is an industrial maintenance AI platform that:
- Answers technician questions with validated, sourced solutions
- Distributes knowledge via social media (YouTube, Reddit, TikTok)
- Escalates complex issues to human experts
- Integrates into CMMS platforms for B2B revenue

**The Core Insight:** Build a brand + community + distribution network that technicians discover organically, trust immediately, and evangelize to peers.

### Agents Agent Factory Must Build for RIVET

These are the production agents you're building the framework to support:

1. **RedditMonitor-v1.0** - Finds unanswered technical questions (runs every 2 hours)
2. **KnowledgeAnswerer-v1.0** - Generates confidence-ranked answers with citations
3. **RedditResponder-v1.0** - Posts comments to Reddit (with human approval)
4. **YouTubePublisher-v1.0** - Creates 3-5 minute faceless videos from solved problems
5. **SocialAmplifier-v1.0** - Distributes content across TikTok, Instagram, Twitter, LinkedIn
6. **HumanFlagger-v1.0** - Escalates to human expert when needed (10min SLA)

### Why This Matters for Your Work

**Phase 1 (Orchestration)** enables these agents to work together:
- One agent monitors Reddit → routes to answerer → routes to responder
- Answerer queries Knowledge Factory → generates response → flags human if confidence <0.9
- YouTubePublisher receives solved problem → generates video → triggers SocialAmplifier

**The Knowledge Atom Standard** is the data contract:
- Every scraper outputs atoms in same format (JSON-LD 1.1 + JSON Schema + Schema.org)
- Every atom passes validation pipeline
- Agents consume/produce Knowledge Atoms
- See: `knowledge-atom-standard-v1.0.md` for full spec

### RIVET Timeline

- **Month 1:** Knowledge Factory foundation (1k atoms indexed)
- **Month 2:** First agent channel (Reddit monitoring + manual approval)
- **Month 3:** Content generation (YouTube channel launch)
- **Month 4:** Multi-platform distribution
- **Month 5:** Human-in-the-loop escalation (premium calls)
- **Month 6:** B2B outreach (CMMS integrations)

**Year 1 Target:** $80k revenue, proof of concept
**Year 3 Target:** $2.5M revenue, sustainable business
**Year 5 Vision:** $10-50M ARR, 1M+ users, community of 50+ technician experts

### The Data is the Moat

RIVET's competitive advantage isn't the code—it's the validated knowledge base.
- Competitors can copy tools
- They can't replicate 100k+ validated Knowledge Atoms
- You own the knowledge, the distribution, and the community

**Your role:** Build the agent orchestration layer that turns this knowledge into automated responses at scale.

---

## The PLC Vertical (Parallel Track)

Agent Factory powers **TWO verticals** simultaneously:
1. **RIVET** - Industrial Maintenance (described above)
2. **PLC Tutor** - PLC Programming Education + Automation (NEW)

### What is PLC Tutor?

PLC Tutor is an AI-powered platform that teaches PLC programming AND evolves into an autonomous PLC coding assistant.

**For Learners:**
- Interactive AI tutor for Allen-Bradley & Siemens PLC programming
- Works with real hardware (or simulation)
- Backed by PLC knowledge atoms (no hallucinations)
- Progresses from basics → advanced → autonomous coding

**For Professionals:**
- Autonomous PLC programmer (spec → verified code)
- Uses computer-use to drive Studio 5000 / TIA Portal / CODESYS
- Proposes ladder/ST code, runs verification loops
- Human-in-loop for production deployments

**For Organizations:**
- White-label PLC tutor for trade schools, OEMs
- Pre-built curriculum with exercises
- B2B training programs

### Why PLC Tutor Matters

**1. Validates Multi-Vertical Platform:**
- Proves Agent Factory works across domains
- Same Knowledge Atom Standard, different vertical
- Same DAAS monetization pattern

**2. Faster Monetization:**
- Month 4: First paid subscribers ($29-$99/mo)
- Month 6: B2B training contracts ($10K-$20K/org)
- Year 1: ~$35K ARR (proof of concept)
- Year 3: ~$2.5M ARR (same as RIVET target)

**3. Different GTM Strategy:**
- RIVET = community-driven (Reddit, forums)
- PLC Tutor = education-driven (YouTube courses)
- Validates multiple acquisition channels

**4. Cross-Selling:**
- PLC programmers ALSO do industrial maintenance
- RIVET users may need PLC training
- Bundle pricing potential

### PLC Agents Agent Factory Must Build (18 Total)

**Executive Team (2 agents):**
1. **AICEOAgent** - Strategy, metrics, KPIs, resource allocation
2. **AIChiefOfStaffAgent** - Project management, issue tracking, orchestration

**Research & Knowledge Base Team (4 agents):**
3. **ResearchAgent** - Web scraping, YouTube transcripts, PDF processing (Issue #47)
4. **AtomBuilderAgent** - Convert raw data → structured atoms (Pydantic models)
5. **AtomLibrarianAgent** - Organize atoms, build prerequisite chains, detect gaps
6. **QualityCheckerAgent** - Validate accuracy, safety compliance, citation integrity

**Content Production Team (5 agents):**
7. **MasterCurriculumAgent** - A-to-Z roadmap, learning paths, sequencing
8. **ContentStrategyAgent** - Keyword research, topic selection, SEO optimization
9. **ScriptwriterAgent** - Transform atoms → engaging video scripts (Issue #48)
10. **SEOAgent** - Optimize metadata (titles, descriptions, tags)
11. **ThumbnailAgent** - Generate eye-catching thumbnails, A/B testing

**Media & Publishing Team (4 agents):**
12. **VoiceProductionAgent** - ElevenLabs voice clone, narration generation
13. **VideoAssemblyAgent** - Sync audio + visuals, render final video
14. **PublishingStrategyAgent** - Schedule uploads, optimal timing, playlists
15. **YouTubeUploaderAgent** - Execute uploads, set metadata, handle errors

**Engagement & Analytics Team (3 agents):**
16. **CommunityAgent** - Respond to comments, moderate, engage viewers
17. **AnalyticsAgent** - Track metrics, detect trends, generate insights
18. **SocialAmplifierAgent** - Extract clips, post to TikTok/Instagram/LinkedIn

**See:** `docs/AGENT_ORGANIZATION.md` for complete specifications (responsibilities, tools, success metrics)

### The PLC Knowledge Atom Standard

**PLC Atom Types:**
- `concept`: What is a PLC, digital I/O, scan cycle
- `pattern`: Start/stop/seal-in motor, timer patterns
- `fault`: Common error codes, diagnostic procedures
- `procedure`: Step-by-step troubleshooting, setup wizards

**Example PLC Pattern Atom:**
```json
{
  "atom_id": "plc:ab:motor-start-stop-seal",
  "type": "pattern",
  "vendor": "allen_bradley",
  "platform": "control_logix",
  "title": "3-Wire Motor Start/Stop/Seal-In",
  "summary": "Basic motor control with maintained contact seal-in",
  "inputs": [
    {"tag": "Start_PB", "type": "NO_contact", "address": "I:0/0"},
    {"tag": "Stop_PB", "type": "NC_contact", "address": "I:0/1"},
    {"tag": "Motor_Run", "type": "auxiliary_contact", "address": "O:0/0"}
  ],
  "outputs": [
    {"tag": "Motor_Contactor", "type": "coil", "address": "O:0/0"}
  ],
  "logic_description": "Parallel seal-in circuit with stop button in series",
  "steps": [
    "Press Start_PB → Motor_Contactor energizes",
    "Motor_Run auxiliary contact seals in",
    "Release Start_PB → Motor stays running (sealed)",
    "Press Stop_PB → Motor_Contactor de-energizes"
  ],
  "constraints": [
    "Stop button must be NC for fail-safe operation",
    "Seal-in contact must be sized for coil current",
    "Requires overload protection (not shown in logic)"
  ],
  "difficulty": "beginner",
  "prereqs": ["plc:generic:io-basics", "plc:generic:ladder-fundamentals"],
  "source": "AB ControlLogix Programming Manual Chapter 3",
  "last_reviewed_at": "2025-12-09",
  "safety_level": "info"
}
```

### PLC Tutor Timeline

**Month 2:** Knowledge base ingestion (50-100 atoms from manuals + YouTube)
**Month 3:** PLC Tutor v0.1 (Lessons 1-5 functional)
**Month 4:** YouTube series launch + first paid subscribers
**Month 6:** Autonomous PLC coder prototype
**Month 12:** Full multi-platform tutor (Siemens + Allen-Bradley)

**Year 1 Target:** $35K ARR (50 subscribers + courses)
**Year 3 Target:** $2.5M ARR (sustainable business)

### Strategy: Same Infrastructure, Different Domain

```
Layer 1: Agent Factory (powers both)
    ↓
Layer 2: Knowledge Atom Standard
    ├── Industrial Maintenance Atoms (RIVET)
    └── PLC Programming Atoms (PLC Tutor)
    ↓
Layer 3: Multi-Vertical Products
    ├── RIVET ($2.5M ARR)
    └── PLC Tutor ($2.5M ARR)
    ↓
Layer 4: DAAS (sell both knowledge bases)
    ↓
Layer 5: Robot Licensing (both are robot-ready)
```

---

## The YouTube-Wiki Strategy (CRITICAL)

**"YouTube IS the knowledge base"**

Instead of scraping first then creating content, we **build the knowledge base BY creating original educational content**.

### Why This Changes Everything

1. **Zero Copyright Issues** - Original content = you own 100% of rights, immediate monetization
2. **Learning-by-Teaching** - You retain 90% of what you teach vs 10% of what you read
3. **Voice Clone = 24/7 Production** - ElevenLabs voice clone enables autonomous content creation
4. **Multi-Use Content** - One video → knowledge atom → blog post → social clips → course module

### The YouTube-Wiki Pipeline

```
YOU learn concept → Research Agent compiles sources
    ↓
Scriptwriter Agent drafts teaching script
    ↓
Voice Production Agent generates narration (your voice clone)
    ↓
Video Assembly Agent combines audio + visuals
    ↓
YouTube Uploader Agent publishes
    ↓
Atom Builder Agent extracts knowledge atom from video
    ↓
Social Amplifier Agent creates clips for TikTok/Instagram
```

### Key Principles

- **Videos 1-20:** YOU approve every one (set quality standard)
- **Videos 21-50:** YOU sample every 3rd (quality gates)
- **Videos 51+:** Agents autonomous (exception flagging only)
- **Content Roadmap:** 100+ videos pre-planned (A-to-Z curriculum)
- **Voice Training:** 10-15 min samples → ElevenLabs Pro → natural-sounding narration
- **SEO-First:** Every video targets low-competition, high-volume keywords

### Success Metrics

- **Week 4:** 3 videos live, voice clone validated
- **Week 12:** 30 videos, 1K subs, $500 revenue, agents 80% autonomous
- **Month 12:** 100 videos, 20K subs, $5K/mo revenue, fully autonomous

**See:** `docs/implementation/YOUTUBE_WIKI_STRATEGY.md` for complete details.

---

### PLC Implementation References

**Complete Strategy Suite (Updated Dec 2025):**
- **Master Strategy:** `docs/architecture/TRIUNE_STRATEGY.md` - Complete integration (RIVET + PLC Tutor + Agent Factory), 18-agent system, revenue models
- **YouTube-Wiki Approach:** `docs/implementation/YOUTUBE_WIKI_STRATEGY.md` - Build knowledge BY teaching (original content, voice clone, 24/7 production)
- **18-Agent System:** `docs/architecture/AGENT_ORGANIZATION.md` - Complete specs for all autonomous agents (Executive, Research, Content, Media, Engagement)
- **Implementation Plan:** `docs/implementation/IMPLEMENTATION_ROADMAP.md` - Week-by-week roadmap (Week 1-12, then Month 4-12)
- **Content A-to-Z:** `plc/content/CONTENT_ROADMAP_AtoZ.md` - 100+ video topics sequenced (electricity → AI automation)
- **Universal Atom Spec:** `docs/architecture/ATOM_SPEC_UNIVERSAL.md` - IEEE LOM-based schema for all verticals
- **Pydantic Models:** `core/models.py` - Production-ready schemas (LearningObject, PLCAtom, RIVETAtom, VideoScript, etc.)

**Legacy/Research:** (Moved to `archive/legacy-docs/`)
- `MASTER_ROADMAP.md` - Original 5-layer vision
- `PLan_fullauto_plc.md` - Initial PLC implementation plan
- `Computers, programming PLCs..md` - Market research + business insights

### PLC Validation Commands

```bash
# Verify PLC atom schema
poetry run python -c "from plc.atoms.pydantic_models import PLCAtom; print('PLC schema OK')"

# Test PLC tutor agent
poetry run python -c "from plc.agents.plc_tutor_agent import PLCTutorAgent; print('Tutor OK')"

# Run PLC atom builder
poetry run python plc/agents/plc_atom_builder_agent.py --source plc/sources/siemens/s7-1200/

# Test with real hardware
poetry run python examples/plc_tutor_demo.py --platform siemens --lesson 1
```

---

## Current Focus

> **PHASE 1: ORCHESTRATION**
> 
> Build multi-agent routing. One agent receives query, routes to specialist.

See `docs/PHASE1_SPEC.md` for implementation details.

---

## Execution Rules

### Rule 0: Task Tracking (Backlog.md Integration)
**Before starting ANY task:**
1. **Check TASK.md** - See what's in progress and backlog (auto-synced from Backlog.md)
   - **User Actions section:** Tasks requiring manual human execution (cloud signup, API keys, etc.)
   - **Current Task section:** Task currently being worked on (status: "In Progress")
   - **Backlog section:** All pending tasks (status: "To Do")
2. **Check for blocking User Actions** - If user actions exist, notify the user before proceeding
3. **View task details** - Use `backlog task view <task-id>` to see full acceptance criteria
4. **Update status** - Mark task as "In Progress" when you start:
   ```bash
   backlog task edit <task-id> --status "In Progress"
   poetry run python scripts/backlog/sync_tasks.py  # Sync to TASK.md
   ```
5. **Mark complete** - Update status to "Done" immediately after finishing:
   ```bash
   backlog task edit <task-id> --status "Done"
   poetry run python scripts/backlog/sync_tasks.py  # Sync to TASK.md
   ```
6. **Add discovered work** - New tasks found during implementation:
   ```bash
   backlog task create --title "FIX: <description>" --priority medium
   ```
7. **Identify User Actions** - If a task requires manual human execution, add the `user-action` label:
   ```bash
   # Examples: Cloud signup, API keys, voice recording, payment setup
   backlog task create --title "ACTION: Setup Railway Database" \
     --labels user-action,database,setup \
     --priority high
   ```

**Backlog.md Workflow:**
- **Source of Truth:** `backlog/tasks/*.md` (structured YAML + Markdown)
- **View Layer:** `TASK.md` (auto-generated, read-only sync zones)
- **Full Guide:** `backlog/README.md`
- **MCP Tools:** Use `backlog task <command>` for all task operations

**Quick Reference:**
- List tasks: `backlog task list --status "To Do"`
- View task: `backlog task view task-4`
- Edit task: `backlog task edit task-4 --status "In Progress"`
- Create task: `backlog task create --title "BUILD: Feature" --priority high`
- Sync to TASK.md: `poetry run python scripts/backlog/sync_tasks.py`

**Pattern from context-engineering-intro (11.8k⭐) + Backlog.md integration**

### Rule 1: One Thing at a Time
Check `TASK.md` for the current task. Complete it. Validate it. Move to next.

### Rule 2: Always Validate
After ANY change, run:
```bash
poetry run python -c "from agent_factory.core.agent_factory import AgentFactory; print('OK')"
```
If it fails, fix before moving on. Never build on broken code.

### Rule 3: Show Don't Tell
After completing a task, provide:
1. What you built (plain English)
2. How to test it (exact command)
3. Expected output

### Rule 4: Small Commits
After each working feature:
```bash
git add . && git commit -m "CHECKPOINT: [what works]"
```

### Rule 4.5: Always Use Worktrees
**ENFORCED:** Pre-commit hook blocks commits to main directory.

When working with multiple agents/tools on this codebase:
1. **NEVER work directly in main directory** - commits will be blocked
2. Create a worktree for each agent/feature/task
3. Each worktree gets its own branch
4. Clean up worktrees after PR is merged

**Why?** Multiple agents working in the same directory causes:
- File conflicts and lost work
- Race conditions on changes
- Confusion about which agent did what
- Test interference

**Create worktree:**
```bash
# Option 1: CLI (recommended)
agentcli worktree-create feature-name

# Option 2: Manual
git worktree add ../agent-factory-feature-name -b feature-name
cd ../agent-factory-feature-name
```

**See:** `docs/patterns/GIT_WORKTREE_GUIDE.md` for complete guide.

### Rule 5: Three Strikes
If something fails 3 times, STOP. Report the error. Don't keep trying different approaches - it may be a direction problem, not an execution problem.

### Rule 6: No Refactoring Without Permission
Don't "improve" or "clean up" working code unless explicitly asked. Working > elegant.

### Rule 7: Stay In Scope
If a task requires changing files outside the current phase, ask first.

### Rule 8: Security & Compliance by Design
Build enterprise-ready features from inception. No retrofitting security later.

**Before Writing ANY Code:**
Ask these 5 questions:
1. **Input:** Does this handle user input? → Validate + sanitize
2. **Data:** Does this touch data? → Encrypt if sensitive + log access
3. **Access:** Does this expose functionality? → Add auth + rate limits
4. **Output:** Does this generate output? → Filter PII + validate safety
5. **Abuse:** Could an agent abuse this? → Add monitoring + circuit breakers

**Before Marking Feature Complete:**
- [ ] Security implications documented in PR/commit
- [ ] Audit logging implemented (who did what, when)
- [ ] Error messages don't leak sensitive data
- [ ] Rate limits exist (if user-facing)
- [ ] Input validation with allow-lists (not block-lists)

**Before Declaring Phase Complete:**
- [ ] Update `docs/SECURITY_AUDIT.md` with new capabilities
- [ ] Add security tests (not just happy path)
- [ ] Document threat model (what could go wrong)
- [ ] Review against SOC 2 Trust Criteria checklist

**Core Security Principles (Always Follow):**
- **Principle of Least Privilege** - Default deny, explicit allow
- **Defense in Depth** - Multiple security layers
- **Fail Secure** - Errors should block, not allow
- **Audit Everything** - Log all privileged operations
- **Assume Breach** - Limit blast radius

**Why This Matters:**
- Enterprise customers require SOC 2 certification ($10K+ deals)
- Retrofitting security costs 10x more than building it right
- Security incidents destroy trust and revenue
- Compliance unlocks enterprise tier pricing ($299/mo vs $49/mo)

See `docs/patterns/SECURITY_STANDARDS.md` for implementation patterns and checklists.

---

## Architecture Summary
```
agent_factory/
+-- core/
|   +-- agent_factory.py        # Main factory [EXISTS]
|   +-- settings_service.py     # Runtime config [NEW - Dec 2025]
|   +-- orchestrator.py         # Routing [PHASE 1]
|   +-- callbacks.py            # Events [PHASE 1]
+-- llm/                         # LLM Router & Cost Optimization
|   +-- router.py               # LLMRouter class [COMPLETE]
|   +-- langchain_adapter.py    # LangChain bridge [NEW - Dec 2025]
|   +-- cache.py                # Response caching [STUB]
|   +-- streaming.py            # Streaming support [STUB]
|   +-- types.py                # Type definitions
|   +-- config.py               # Model registry
|   +-- tracker.py              # Cost tracking
+-- memory/
|   +-- storage.py              # Supabase storage [EXISTS]
|   +-- history.py              # Message history [EXISTS]
|   +-- hybrid_search.py        # Hybrid search [PLANNED]
+-- schemas/                     # [PHASE 2]
+-- tools/                       # [EXISTS]
+-- refs/                        # [PHASE 5]
```

For full architecture, see `docs/architecture/00_architecture_platform.md`.

---

## Settings Service (Production Pattern from Archon 13.4k⭐)

**Database-backed configuration with environment fallback**

```python
from agent_factory.core.settings_service import settings

# Get string settings
model = settings.get("DEFAULT_MODEL", category="llm")

# Get typed settings
batch_size = settings.get_int("BATCH_SIZE", default=50, category="memory")
use_hybrid = settings.get_bool("USE_HYBRID_SEARCH", category="memory")
temperature = settings.get_float("DEFAULT_TEMPERATURE", default=0.7, category="llm")

# Set values programmatically (if database available)
settings.set("DEBUG_MODE", "true", category="general")

# Reload from database (picks up runtime changes)
settings.reload()
```

**Key Benefits:**
- No code changes needed for configuration
- No service restarts required
- Environment variable fallback (works without database)
- Category-based organization (llm, memory, orchestration)
- 5-minute cache with auto-reload

**Setup:**
1. Run SQL migration: `docs/supabase_migrations.sql` in Supabase SQL Editor
2. Settings automatically load on first import
3. Use in your code - falls back to .env if database unavailable

**See:** `examples/settings_demo.py` for complete usage examples

---

## Cost-Optimized LLM Routing (Phase 2)

**Status:** Infrastructure Complete - Routing enabled by default

### Problem Solved
Autonomous agents used expensive models for simple tasks (GPT-4o for classification).
Routing selects the cheapest capable model per task, reducing costs 30-40% immediately.

### How It Works
1. Task arrives → Agent requests LLM response
2. RoutedChatModel detects capability (SIMPLE/MODERATE/COMPLEX/CODING/RESEARCH)
3. LLMRouter selects cheapest model from registry
4. Response generated & cost tracked automatically
5. Fallback chain if primary fails (3 attempts)

### Cost Impact Table
| Task Type | Old Model | New Model | Cost Reduction |
|-----------|-----------|-----------|-----------------|
| Simple classification | gpt-4o | gpt-3.5-turbo | 90% ($0.040 → $0.004) |
| Moderate reasoning | gpt-4o | gpt-4o-mini | 83% ($0.025 → $0.004) |
| Complex reasoning | gpt-4o | gpt-4o | 0% (stays premium) |
| Code generation | gpt-4o | gpt-4-turbo | 60% ($0.030 → $0.012) |

**Expected Savings:** $200-400/month (50+ autonomous agents)

### Usage Examples

#### Default Routing (Recommended)
```python
from agent_factory.core.agent_factory import AgentFactory

# Routing enabled by default
factory = AgentFactory()

# Agent automatically selects cheapest capable model
agent = factory.create_agent(
    role="classifier",
    tools_list=[search_tool]
)

# Uses gpt-3.5-turbo (SIMPLE capable, cheapest)
response = agent.invoke("Classify this email")
print(f"Model: {agent.last_model_used}, Cost: ${agent.last_cost:.6f}")
```

#### Explicit Capability
```python
from agent_factory.llm.types import ModelCapability

# Force premium models for complex tasks
agent = factory.create_agent(
    role="researcher",
    capability=ModelCapability.COMPLEX,
    tools_list=[semantic_search]
)
```

#### Cost Tracking
```python
from agent_factory.llm.tracker import get_global_tracker

tracker = get_global_tracker()
stats = tracker.aggregate_stats()
print(f"Total cost: ${stats['total_cost_usd']:.2f}")
```

### Architecture
- **Layer 1:** LLMRouter (400 lines) - Unified interface, retries, fallback
- **Layer 2:** RoutedChatModel (250 lines) - LangChain adapter
- **Layer 3:** Model Registry (330 lines) - 12 models, pricing, capabilities

### Performance
- **Latency:** <10ms overhead (99.9% is API call time)
- **Cost Reduction:** 73% in live testing ($750/mo → $198/mo)
- **Accuracy:** No degradation (capability-aware selection)

### Validation
```bash
# Test routing
poetry run python -c "from agent_factory.llm.langchain_adapter import create_routed_chat_model; print('OK')"
```

---

## Reference Documents

| Document | Purpose | When to Read |
|----------|---------|--------------|
| **ESSENTIAL DOCS (Root)** |
| `TASK.md` | **Active task tracking** | **Every session start** |
| `PROJECT_STRUCTURE.md` | **Complete codebase map** | **When navigating the project** |
| `README.md` | Project overview | Getting started |
| `CLAUDE.md` | This file - AI assistant instructions | Reference for rules |
| **ARCHITECTURE** |
| `docs/architecture/00_architecture_platform.md` | Full system design | Need big picture |
| `docs/architecture/TRIUNE_STRATEGY.md` | RIVET + PLC Tutor integration | Understanding strategy |
| `docs/architecture/AGENT_ORGANIZATION.md` | 18-agent system specs | Planning agent work |
| `docs/architecture/archon_architecture_analysis.md` | Archon microservices analysis | Understanding Supabase + pgvector |
| **IMPLEMENTATION** |
| `docs/implementation/00_platform_roadmap.md` | CLI → SaaS transformation | Platform planning |
| `docs/implementation/IMPLEMENTATION_ROADMAP.md` | Week-by-week roadmap | Current sprint planning |
| `docs/implementation/YOUTUBE_WIKI_STRATEGY.md` | Build knowledge BY teaching | Content strategy |
| **DATABASE** |
| `docs/database/00_database_schema.md` | Schema documentation | Database work |
| `docs/database/supabase_complete_schema.sql` | Full schema SQL | Deploying schema |
| `docs/database/DATABASE_TOOLS_GUIDE.md` | Database utilities | Using DB scripts |

| **PATTERNS & STANDARDS** |

| `docs/patterns/cole_medin_patterns.md` | Production patterns from Archon | Building RAG/memory features |
| `docs/patterns/GIT_WORKTREE_GUIDE.md` | Git worktree setup | Before starting work |
| `docs/patterns/SECURITY_STANDARDS.md` | Compliance patterns | Building features |
| **USER GUIDES** |
| `Guides for Users/README.md` | User guide index | Finding user documentation |
| `Guides for Users/quickstart/QUICKSTART.md` | First-time setup | New users |
| `Guides for Users/deployment/PRODUCTION_DEPLOYMENT.md` | Production deployment | Going live |
| **LEGACY (Archived)** |
| `archive/legacy-docs/MASTER_ROADMAP.md` | Original 5-layer vision | Historical context |
| `archive/legacy-docs/rivet-complete-summary.md` | RIVET platform details | Understanding end product |
| `archive/legacy-docs/knowledge-atom-standard-v1.0.md` | Data schema specification | Building knowledge features |

---

## Standards

- **Python 3.10+**
- **Type hints** on all functions
- **Pydantic** for data models
- **Google ADK patterns** (see `docs/PATTERNS.md`)
- **ASCII-only output** (Windows compatible)

---

## Validation Commands
```bash
# 1. Import check (run after any change)
poetry run python -c "from agent_factory.core.agent_factory import AgentFactory; print('OK')"

# 2. Settings Service check (verify database-backed config)
poetry run python -c "from agent_factory.core.settings_service import settings; print(settings)"

# 3. Demo check (run after completing a feature)
poetry run python agent_factory/examples/demo.py

# 4. Settings demo (verify runtime config)
poetry run python examples/settings_demo.py

# 5. Test check (run before marking phase complete)
poetry run pytest

# 6. Orchestrator check (Phase 1 specific)
poetry run python -c "from agent_factory.core.orchestrator import AgentOrchestrator; print('OK')"

# 7. Database Manager - Multi-provider PostgreSQL (Dec 2025)
poetry run python -c "from agent_factory.core.database_manager import DatabaseManager; db = DatabaseManager(); print('Providers:', list(db.providers.keys()))"
poetry run python -c "from agent_factory.core.database_manager import DatabaseManager; db = DatabaseManager(); print(db.health_check_all())"

# 8. PostgreSQL Memory Storage (Dec 2025)
poetry run python -c "from agent_factory.memory.storage import PostgresMemoryStorage; storage = PostgresMemoryStorage(); print('OK')"

# 9. Database Failover Tests (Dec 2025)
poetry run pytest tests/test_database_failover.py -v
```

---

## VPS KB Factory (Hostinger)

24/7 knowledge base ingestion pipeline running on Hostinger VPS.

**VPS:** `72.60.175.144`

**Services (Docker Compose):**
- `postgres` - PostgreSQL 16 + pgvector for semantic search
- `redis` - Job queue for ingestion URLs
- `ollama` - Local LLM (deepseek-r1:1.5b) + embeddings (nomic-embed-text)
- `rivet-worker` - LangGraph ingestion pipeline
- `rivet-scheduler` - Hourly job scheduling

**Query VPS from ScriptwriterAgent:**
```python
from agents.content.scriptwriter_agent import ScriptwriterAgent

agent = ScriptwriterAgent()

# Keyword search
atoms = agent.query_vps_atoms("ControlLogix", limit=5)

# Semantic search (uses Ollama embeddings)
atoms = agent.query_vps_atoms_semantic("How to troubleshoot motor faults", limit=5)

# Generate script from atoms
script = agent.generate_script("PLC Motor Control", atoms)
```

**VPS Management Commands:**
```bash
# SSH into VPS
ssh root@72.60.175.144

# Check services
cd /opt/rivet/infra && docker-compose ps

# View worker logs
docker logs infra_rivet-worker_1 --tail 50

# Add URL to ingest
docker exec infra_redis_1 redis-cli RPUSH kb_ingest_jobs "https://example.com/manual.pdf"

# Check atom count
docker exec infra_postgres_1 psql -U rivet -d rivet -c "SELECT COUNT(*) FROM knowledge_atoms;"
```

**Environment Variables (in .env):**
```
VPS_KB_HOST=72.60.175.144
VPS_KB_PORT=5432
VPS_KB_USER=rivet
VPS_KB_PASSWORD=rivet_factory_2025!
VPS_KB_DATABASE=rivet
```

**KB Ingestion Scripts:**
```powershell
# Push industrial PDFs to VPS (from PowerShell)
.\push_urls_to_vps.ps1

# Monitor ingestion progress
ssh root@72.60.175.144 "docker logs infra_rivet-worker_1 --tail 50"
```

**Source Files:**
- `scripts/kb_seed_urls.py` - 17 curated industrial PDF URLs (Rockwell, Siemens, Mitsubishi, Omron, Schneider)
- `scripts/push_urls_to_vps.py` - Python push script
- `scripts/monitor_vps_ingestion.py` - Python monitor script
- `push_urls_to_vps.ps1` - PowerShell push script (Windows)

---

## Cloud Dev Box Setup

**Remote development with Claude Code CLI on cloud VM**

### Quick Start

```bash
# SSH into cloud VM
ssh user@your-cloud-vm.com
cd ~/agent-factory

# One-time setup (first login)
./scripts/cloud-dev-box/setup-from-scratch.sh

# Launch Claude Code session
./scripts/cloud-dev-box/launch-claude.sh
```

### Daily Workflow

```bash
# 1. SSH into VM
ssh user@your-cloud-vm.com
cd ~/agent-factory

# 2. Check environment (optional)
./scripts/cloud-dev-box/check-prerequisites.sh

# 3. Launch Claude
./scripts/cloud-dev-box/launch-claude.sh

# 4. Work on tasks inside Claude session
> Read TASK.md
> What should I work on next?

# 5. Exit when done (Ctrl+D)
```

### Session Management

```bash
# Resume previous session
./scripts/cloud-dev-box/launch-claude.sh --resume

# List saved sessions
./scripts/cloud-dev-box/utils/session-manager.sh list

# Load specific session
./scripts/cloud-dev-box/utils/session-manager.sh resume feature-xyz
```

### Access from Mobile

**Termux (Android):**
```bash
pkg install openssh
ssh user@your-cloud-vm.com
cd ~/agent-factory && ./scripts/cloud-dev-box/launch-claude.sh
```

**JuiceSSH (Android):**
- Create connection: user@your-cloud-vm.com
- Save snippet: `cd ~/agent-factory && ./scripts/cloud-dev-box/launch-claude.sh`
- One-tap access!

**See:** `Guides for Users/deployment/CLOUD_DEV_BOX_GUIDE.md` for complete setup guide

---

## Red Flags - Stop and Report

If you find yourself:
- Refactoring existing working code
- Trying the same fix 3+ times
- Saying "this should work" but it doesn't
- Changing files outside current phase scope
- Unsure why something is failing

**STOP. Report what's happening. Ask for guidance.**

---

## Context for the Human

The project owner is not a coder. When reporting progress:
- Use plain English
- Provide exact test commands they can copy/paste
- Show expected output
- Be honest about uncertainty

---

## Quick Reference: Current Patterns

### Creating Agents (existing)
```python
factory = AgentFactory()
agent = factory.create_agent(role="Name", tools_list=[...], ...)
```

### Creating Tools (existing)
```python
class MyTool(BaseTool):
    name = "my_tool"
    description = "What it does"
    def _run(self, query: str) -> str:
        return result
```

### Orchestrator (building now)
```python
orchestrator = factory.create_orchestrator()
orchestrator.register("name", agent, keywords=["..."])
response = orchestrator.route("user query")
```

---

## Goal

Build agents that are "AI amazing to the customer" - reliable, fast, trustworthy.

**The human's apps:**
- **Friday** - Voice AI assistant (personal productivity)
- **Jarvis** - Digital ecosystem manager (workflow automation)
- **RIVET** - Industrial maintenance AI platform (community + knowledge + agents)

All three rely on Agent Factory as their agent orchestration engine.

---

## When in Doubt

1. Check `PROGRESS.md` for what to do next
2. Check the relevant spec doc for how to do it
3. Validate that it works
4. Commit checkpoint
5. Move to next item

Keep it simple. Keep it working. Keep moving forward.
```

---

Now you need the supporting docs. Here's the file structure:
```
Agent-Factory/
+-- CLAUDE.md              # Meta doc (above) - Claude CLI reads this
+-- PROGRESS.md            # Checklist - tracks what's done
+-- CLAUDE_CODEBASE.md     # Existing - your current code docs
+-- Guides for Users/      # User-facing setup/deployment guides
    +-- README.md          # Complete guide index
    +-- QUICKSTART.md      # First-time setup (15 min)
    +-- PRODUCTION_DEPLOYMENT.md  # Cloud deployment
    +-- BOT_DEPLOYMENT_GUIDE.md   # Telegram bot deployment
    +-- TELEGRAM_KB_INTEGRATION.md  # Knowledge base integration
    +-- POETRY_GUIDE.md    # Dependency management
    +-- OLLAMA_SETUP_COMPLETE.md  # FREE LLM setup
    +-- *.md               # Other user guides
+-- docs/
    +-- ARCHITECTURE.md    # Full architecture + pipeline diagram
    +-- PATTERNS.md        # 8 Google ADK patterns with examples
    +-- PRODUCTION.md      # 4 levels of production readiness
    +-- PHASE1_SPEC.md     # Detailed Phase 1 implementation
    +-- PHASE2_SPEC.md     # (create when ready)

<!-- BACKLOG.MD MCP GUIDELINES START -->

<CRITICAL_INSTRUCTION>

## BACKLOG WORKFLOW INSTRUCTIONS

This project uses Backlog.md MCP for all task and project management activities.

**CRITICAL GUIDANCE**

- If your client supports MCP resources, read `backlog://workflow/overview` to understand when and how to use Backlog for this project.
- If your client only supports tools or the above request fails, call `backlog.get_workflow_overview()` tool to load the tool-oriented overview (it lists the matching guide tools).

- **First time working here?** Read the overview resource IMMEDIATELY to learn the workflow
- **Already familiar?** You should have the overview cached ("## Backlog.md Overview (MCP)")
- **When to read it**: BEFORE creating tasks, or when you're unsure whether to track work

These guides cover:
- Decision framework for when to create tasks
- Search-first workflow to avoid duplicates
- Links to detailed guides for task creation, execution, and completion
- MCP tools reference

You MUST read the overview resource to understand the complete workflow. The information is NOT summarized here.

</CRITICAL_INSTRUCTION>

<!-- BACKLOG.MD MCP GUIDELINES END -->

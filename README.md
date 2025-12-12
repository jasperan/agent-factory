# Agent Factory 🏭🤖

> **Building the engine that turns knowledge into autonomous content at scale**

Agent Factory is not just a framework—it's the **orchestration engine** powering two ambitious platforms:
1. **PLC Tutor / Industrial Skills Hub** - AI-powered PLC programming education with autonomous YouTube content production
2. **RIVET** - Industrial maintenance knowledge platform with validated troubleshooting solutions

**Vision:** Build autonomous agent systems that create, distribute, and monetize educational content 24/7, while building the largest validated knowledge base in industrial automation.

**Status:** 🚀 Week 2 - Parallel ISH Swarm Development (6/9 agents complete, 3 in progress)

---

## 📊 Current Development Status (Week 2, Day 2)

### ISH Swarm Progress: 6/9 Agents Complete (67%)

| Agent | Status | Worktree | Lines | Function |
|-------|--------|----------|-------|----------|
| ResearchAgent | ✅ Complete | main | 450 | Find trending PLC topics from Reddit |
| ScriptwriterAgent | ✅ Tested | ish-scriptwriter | existing | Generate video scripts from atoms |
| VideoQualityReviewerAgent | ✅ Complete | ish-reviewer | 664 | Score scripts 0-10, approve/flag/reject |
| VoiceProductionAgent | ✅ Ready | main | existing | Generate narration (ElevenLabs/edge-tts) |
| VideoAssemblyAgent | ✅ Complete | ish-assembly | 546 | Render 1080p MP4 videos (FFmpeg) |
| MasterOrchestratorAgent | ✅ Complete | ish-orchestrator | 920 | Coordinate all 9 agents + approval gates |
| ThumbnailAgent | 🚧 Building | ish-thumbnail | TBD | Generate eye-catching thumbnails |
| SEOAgent | 🚧 Building | ish-seo | TBD | Optimize titles, descriptions, tags |
| YouTubeUploaderAgent | 🚧 Building | ish-youtube | TBD | Publish videos to YouTube Data API |

### Parallel Development Approach

**Why Git Worktrees?** Multiple AI agents developing simultaneously without conflicts.

**4 Worktrees Active:**
- `agent-factory-ish-scriptwriter` → Testing with 1,964 real Supabase atoms
- `agent-factory-ish-reviewer` → Quality gates (5-dimension scoring)
- `agent-factory-ish-assembly` → Video rendering (test video: 467 KB, 1080p)
- `agent-factory-ish-orchestrator` → 9-agent coordination + dashboard

**See:** `PARALLEL_DEV_REPORT.md` for complete details

### Knowledge Base Status

- **1,964 atoms** in Supabase (Allen-Bradley + Siemens)
- **Vector search** ready (<100ms semantic queries)
- **5 test scripts** generated from real atoms
- **1 test video** rendered (20s, 1080p @ 30fps)

### Week 2 Timeline

- ✅ **Day 1:** ResearchAgent (Reddit topic discovery)
- ✅ **Day 2:** ScriptwriterAgent testing + VideoQualityReviewerAgent + VideoAssemblyAgent + MasterOrchestratorAgent (parallel)
- 🚧 **Day 3:** ThumbnailAgent + SEOAgent + YouTubeUploaderAgent (parallel, in progress)
- ⏳ **Day 4-5:** End-to-end pipeline testing
- ⏳ **Day 6-7:** Week 3 prep (video production)

**Next Milestone:** Week 4 - Launch ISH swarm (3 videos/week autonomous)

---

## 🎯 What We're Building

### The Triune Vision

```
┌─────────────────────────────────────────────────────┐
│          Agent Factory (Orchestration Engine)        │
│  Multi-agent coordination • Knowledge management     │
│  Content production • Distribution automation        │
└─────────────────────────────────────────────────────┘
                         ↓
         ┌───────────────┴───────────────┐
         ↓                               ↓
┌──────────────────────┐      ┌──────────────────────┐
│  PLC Tutor           │      │  RIVET               │
│  (Education-driven)  │      │  (Community-driven)  │
├──────────────────────┤      ├──────────────────────┤
│ • YouTube A-to-Z     │      │ • Reddit monitoring  │
│ • Voice clone 24/7   │      │ • Validated answers  │
│ • 100+ video series  │      │ • B2B integrations   │
│ • Courses + certs    │      │ • Premium calls      │
│ • B2B training       │      │ • CMMS platforms     │
├──────────────────────┤      ├──────────────────────┤
│ Year 1: $35K ARR     │      │ Year 1: $80K ARR     │
│ Year 3: $2.5M ARR    │      │ Year 3: $2.5M ARR    │
└──────────────────────┘      └──────────────────────┘
         ↓                               ↓
         └───────────────┬───────────────┘
                         ↓
           ┌─────────────────────────┐
           │  Data-as-a-Service       │
           │  (License knowledge)     │
           └─────────────────────────┘
                         ↓
           ┌─────────────────────────┐
           │  Robot Licensing         │
           │  (Humanoid robots)       │
           └─────────────────────────┘
```

---

## 🚀 Current Focus: PLC Tutor Launch (Week 1-12)

### ✅ Infrastructure Complete (Dec 9-10)

**Recently Built:**
- **Supabase Memory System** - <1 second session loading (60-120x faster than files)
- **FREE LLM Integration** - $0/month costs via Ollama (DeepSeek Coder 6.7B)
- **Settings Service** - Runtime configuration without code deployments
- **Core Pydantic Models** - 600+ lines production schemas
- **GitHub Automation** - Webhooks, auto-sync, orchestrator integration
- **Complete Documentation** - 7 strategy docs (142KB), implementation roadmap

**Cost Savings:** $200-500/month in LLM costs → $0/month
**Performance:** Session loading 30-60s → <1 second

### ✅ Voice System: Generic TTS Active (Blocker Removed!)
- **Hybrid Voice System** - Edge-TTS (FREE), OpenAI TTS (PAID), ElevenLabs (custom)
- **Current Mode:** Edge-TTS (Microsoft neural voices, $0/month)
- **Upgrade Path:** Switch to custom voice Saturday (one env variable change)
- **Status:** Can produce professional narration NOW

### 🔴 Remaining User Tasks (Non-blocking for agents)
1. **First 10 Atoms** - Create electrical + PLC basics knowledge atoms
2. **Supabase Schema** - Deploy `docs/supabase_migrations.sql`
3. **Voice Training (Saturday)** - Record samples, upload to ElevenLabs (optional upgrade)

### 📅 Next: Week 2 Agent Development

Once user tasks complete, build:
- Research Agent (web scraping, YouTube transcripts)
- Scriptwriter Agent (atoms → video scripts)
- Atom Builder Agent (raw data → structured atoms)

---

## 🚀 The YouTube-Wiki Strategy (Week 1-12 Roadmap)

### The YouTube-Wiki Strategy

**Core Insight:** "YouTube IS the knowledge base"

Instead of scraping content then making videos, we **build the knowledge base BY creating original educational content**.

**The Pipeline:**
```
YOU learn concept → Research Agent compiles sources
    ↓
Scriptwriter Agent drafts teaching script (atom-backed, no hallucination)
    ↓
Voice Production Agent generates narration (ElevenLabs voice clone)
    ↓
Video Assembly Agent combines audio + visuals + captions
    ↓
YouTube Uploader Agent publishes (SEO-optimized)
    ↓
Atom Builder Agent extracts knowledge atom from video
    ↓
Social Amplifier Agent creates clips for TikTok/Instagram/LinkedIn
```

### 18 Autonomous Agents

**Executive Team (2):**
- AI CEO Agent - Strategy, metrics, resource allocation
- AI Chief of Staff Agent - Project management, issue tracking

**Research & Knowledge Base Team (4):**
- Research Agent - Web scraping, YouTube transcripts, PDFs
- Atom Builder Agent - Convert raw data → structured atoms
- Atom Librarian Agent - Organize atoms, build prerequisite chains
- Quality Checker Agent - Validate accuracy, safety, citations

**Content Production Team (5):**
- Master Curriculum Agent - 100+ video roadmap, sequencing
- Content Strategy Agent - Keyword research, SEO
- Scriptwriter Agent - Transform atoms → engaging scripts
- SEO Agent - Optimize titles, descriptions, tags
- Thumbnail Agent - Generate thumbnails, A/B testing

**Media & Publishing Team (4):**
- Voice Production Agent - ElevenLabs narration
- Video Assembly Agent - MoviePy + FFmpeg rendering
- Publishing Strategy Agent - Optimal timing, scheduling
- YouTube Uploader Agent - Execute uploads, handle errors

**Engagement & Analytics Team (3):**
- Community Agent - Respond to comments, moderate
- Analytics Agent - Track metrics, detect trends
- Social Amplifier Agent - TikTok/Instagram clips

**See:** [`docs/AGENT_ORGANIZATION.md`](docs/AGENT_ORGANIZATION.md) for complete specifications

---

## 📊 Milestones & Success Metrics

### Week 4 (Public Launch)
- ✅ 3 videos live on YouTube
- ✅ Voice clone validated (< 10% robotic artifacts)
- ✅ CTR > 2%, AVD > 40%
- ✅ 100+ subscribers

### Week 12 (Autonomous Operations)
- ✅ 30 videos published
- ✅ 1,000+ subscribers
- ✅ $500+ revenue (courses + ads)
- ✅ Agents 80% autonomous (you review exceptions only)
- ✅ YouTube Partner Program applied

### Month 12 (Scale Achieved)
- ✅ 100+ videos published
- ✅ 20,000+ subscribers
- ✅ $5,000+/month revenue
- ✅ 100+ validated knowledge atoms
- ✅ Agents fully autonomous (99% without human intervention)

**See:** [`docs/IMPLEMENTATION_ROADMAP.md`](docs/IMPLEMENTATION_ROADMAP.md) for week-by-week plan

---

## 📚 Documentation (Strategy Suite)

### Essential Reading (Start Here)

| Document | Purpose | Size |
|----------|---------|------|
| **[TRIUNE_STRATEGY.md](docs/TRIUNE_STRATEGY.md)** | Master integration document (RIVET + PLC + Agent Factory) | 32KB |
| **[YOUTUBE_WIKI_STRATEGY.md](docs/YOUTUBE_WIKI_STRATEGY.md)** | YouTube-first approach, voice clone, monetization | 17KB |
| **[AGENT_ORGANIZATION.md](docs/AGENT_ORGANIZATION.md)** | All 18 agents with complete specs | 26KB |
| **[IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md)** | Week-by-week implementation plan (12 weeks) | 22KB |
| **[CONTENT_ROADMAP_AtoZ.md](plc/content/CONTENT_ROADMAP_AtoZ.md)** | 100+ video topics sequenced (electricity → AI) | 24KB |
| **[ATOM_SPEC_UNIVERSAL.md](docs/ATOM_SPEC_UNIVERSAL.md)** | Universal knowledge atom schema (IEEE LOM) | 21KB |
| **[CLAUDE.md](CLAUDE.md)** | AI agent context (how to work with this project) | - |
| **[TASK.md](TASK.md)** | Current tasks, priorities, progress tracking | - |

### Technical Documentation

| Document | Purpose |
|----------|---------|
| [cole_medin_patterns.md](docs/cole_medin_patterns.md) | Production patterns from Archon (13.4k⭐) |
| [archon_architecture_analysis.md](docs/archon_architecture_analysis.md) | Microservices architecture deep dive |
| [integration_recommendations.md](docs/integration_recommendations.md) | Prioritized roadmap for Agent Factory |
| [GIT_WORKTREE_GUIDE.md](docs/GIT_WORKTREE_GUIDE.md) | Multi-agent development workflow |
| [SECURITY_STANDARDS.md](docs/SECURITY_STANDARDS.md) | Compliance patterns & checklists |

### GitHub Issues

| Issue | Title | Status |
|-------|-------|--------|
| [#44](https://github.com/your-username/agent-factory/issues/44) | Week 1 Foundation - System Setup & Voice Training | 🔴 CRITICAL |
| [#45](https://github.com/your-username/agent-factory/issues/45) | Create First 10 Knowledge Atoms | 🟡 HIGH |
| [#46](https://github.com/your-username/agent-factory/issues/46) | Implement Core Pydantic Models | ✅ COMPLETED |
| [#47](https://github.com/your-username/agent-factory/issues/47) | Build Research Agent | 📅 Week 2 |
| [#48](https://github.com/your-username/agent-factory/issues/48) | Build Scriptwriter Agent | 📅 Week 2 |
| [#49](https://github.com/your-username/agent-factory/issues/49) | Week 1 Complete Checklist (Master) | 🔴 TRACKING |

---

## 🤖 GitHub Issue Automation (NEW!)

**Automatically solve GitHub issues with FREE local LLMs**

### Quick Start
```bash
# Solve a single issue
poetry run python solve_github_issues.py --issue 52

# Solve all "agent-task" labeled issues
poetry run python solve_github_issues.py --label "agent-task"

# See what would be solved (dry run)
poetry run python solve_github_issues.py --label "agent-task" --dry-run
```

### How It Works
1. **Fetch issue from GitHub** (via `gh` CLI)
2. **Generate solution** with OpenHands + FREE Ollama (DeepSeek Coder)
3. **Review code** - you approve before committing
4. **Auto-commit** with message: `feat: <title> (closes #N)`
5. **Push to GitHub** - issue auto-closes!

### Cost Savings
- **Manual coding:** 2-4 hours, $100-600 per issue
- **Claude API:** 5 mins, $0.15-0.50 per issue
- **Ollama (this):** 5 mins, **$0.00 per issue**

**Annual savings:** $780-2,600 for 10 issues/week

### Features
- ✅ **$0.00 cost** - Uses FREE Ollama (DeepSeek Coder 6.7B)
- ✅ **5-15 min per issue** - vs 2-4 hours manual
- ✅ **80% GPT-4 quality** - Production-ready code
- ✅ **Safe by default** - Requires approval before committing
- ✅ **Batch processing** - Solve multiple issues at once
- ✅ **Auto-closes issues** - Via commit message

### Requirements
1. **Ollama installed** with model:
   ```bash
   winget install Ollama.Ollama
   ollama pull deepseek-coder:6.7b
   ```

2. **GitHub CLI authenticated:**
   ```bash
   gh auth login
   ```

3. **Environment configured:**
   ```bash
   # In .env
   USE_OLLAMA=true
   OLLAMA_MODEL=deepseek-coder:6.7b
   ```

### Documentation
- **Complete Guide:** [`docs/GITHUB_ISSUE_AUTOMATION.md`](docs/GITHUB_ISSUE_AUTOMATION.md)
- **Demo Script:** [`examples/solve_issue_demo.py`](examples/solve_issue_demo.py)
- **Ollama Setup:** [`docs/OPENHANDS_FREE_LLM_GUIDE.md`](docs/OPENHANDS_FREE_LLM_GUIDE.md)

### Example Output
```
[1/7] Fetching issue #52...
  Title: Implement webhook handler
  Labels: agent-task, enhancement

[2/7] Creating OpenHands task...
  Task created (450 characters)

[3/7] Solving with OpenHands (FREE Ollama)...
  SUCCESS in 12.3s

[4/7] Validating...
  [OK] Syntax valid
  [OK] No security issues

[5/7] Generated solution:
  (Shows code preview)

[6/7] Apply? yes

[7/7] Committed and pushed
  Issue #52 will auto-close!

Cost: $0.00 | Time: 12.3s | Savings vs Claude: $0.25
```

**See full guide:** [`docs/GITHUB_ISSUE_AUTOMATION.md`](docs/GITHUB_ISSUE_AUTOMATION.md)

---

## 🛠️ Technology Stack

### Core Infrastructure
- **Python 3.10+** - Primary language
- **Pydantic v2** - Data validation & schemas
- **Supabase + pgvector** - Database with vector search
- **LangChain** - Agent orchestration framework
- **APScheduler** - Task scheduling (cron-like)

### AI & ML
- **Claude API (Anthropic)** - Agent intelligence, scripting
- **OpenAI API** - Embeddings, GPT-4 for specialized tasks
- **ElevenLabs Pro** - Voice cloning & TTS ($30/mo)

### Media Production
- **FFmpeg** - Video rendering, clip extraction
- **MoviePy** - Video assembly, timeline sync
- **Pydub** - Audio processing
- **Pillow** - Image processing, thumbnails
- **OpenAI Whisper** - Caption generation

### Platforms & APIs
- **YouTube Data API** - Upload, metadata, analytics
- **TikTok API** - Post videos
- **Instagram Graph API** - Post reels
- **Reddit API** - Community engagement
- **Twitter/X API** - Social distribution

### Development Tools
- **Poetry** - Dependency management
- **Pytest** - Testing
- **Git Worktrees** - Multi-agent development

---

## 📦 Installation & Setup

### Prerequisites

- **Python 3.10 or 3.11** (required)
- **Poetry** (recommended) or pip
- **Git** (for version control)

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-username/agent-factory.git
cd agent-factory

# 2. Install dependencies (Poetry 2.x)
poetry install

# 3. Copy environment template
cp .env.example .env

# 4. Add API keys to .env
# - OPENAI_API_KEY
# - ANTHROPIC_API_KEY
# - SUPABASE_URL
# - SUPABASE_KEY
# - ELEVENLABS_API_KEY (for voice clone)

# 5. Test installation
poetry run python -c "from core.models import PLCAtom; print('✓ Installation successful')"
poetry run python test_models.py  # All 6 tests should pass
```

### Week 1 Setup (Human Tasks)

**See:** [Issue #44](https://github.com/your-username/agent-factory/issues/44) for complete checklist

**Monday-Tuesday (3-4 hours):**
- [ ] Record 10-15 min voice samples (teaching mode, varied emotion)
- [ ] Upload to ElevenLabs Professional Voice Cloning
- [ ] Create Supabase project (enable pgvector extension)
- [ ] Run schema migrations (`docs/supabase_migrations.sql`)
- [ ] Test voice clone (generate 30s sample, verify quality < 10% robotic)

**Wednesday-Thursday (4-6 hours):**
- [ ] Manually create 10 knowledge atoms (5 electrical, 5 PLC basics)
- [ ] Insert into Supabase `knowledge_atoms` table
- [ ] Generate embeddings (OpenAI `text-embedding-3-small`)
- [ ] Test vector search (query "what is voltage" → correct atom returned)

**Friday (2-3 hours):**
- [x] Implement Core Pydantic Models (`core/models.py`) ✅ COMPLETED
- [x] Validate all models with test suite ✅ COMPLETED

---

## 🏗️ Project Structure

```
agent-factory/
├── core/                          # Core data models
│   ├── models.py                  # Pydantic schemas (600+ lines) ✅
│   ├── agent_factory.py           # Main factory class
│   └── settings_service.py        # Runtime configuration
├── docs/                          # Strategy & technical docs
│   ├── TRIUNE_STRATEGY.md         # Master vision (32KB) ✅
│   ├── YOUTUBE_WIKI_STRATEGY.md   # Content strategy (17KB) ✅
│   ├── AGENT_ORGANIZATION.md      # 18 agents specs (26KB) ✅
│   ├── IMPLEMENTATION_ROADMAP.md  # Week-by-week plan (22KB) ✅
│   ├── ATOM_SPEC_UNIVERSAL.md     # Knowledge atom schema (21KB) ✅
│   └── *.md                       # Technical documentation
├── plc/                           # PLC Tutor vertical
│   ├── content/
│   │   └── CONTENT_ROADMAP_AtoZ.md  # 100+ videos (24KB) ✅
│   ├── agents/                    # PLC-specific agents (Week 2+)
│   └── atoms/                     # Knowledge atoms (Week 1)
├── agents/                        # Agent implementations (Week 2+)
│   ├── research/                  # Research & KB agents
│   ├── content/                   # Content production agents
│   ├── media/                     # Media & publishing agents
│   ├── engagement/                # Community & analytics agents
│   └── executive/                 # AI CEO & Chief of Staff
├── tests/                         # Test suites
│   └── test_models.py             # Pydantic model tests ✅
├── examples/                      # Demo scripts
├── CLAUDE.md                      # AI agent context ✅
├── TASK.md                        # Current tasks ✅
└── README.md                      # This file ✅
```

**Legend:**
- ✅ Completed (Week 0)
- 📅 Upcoming (Week 1-2)
- 🔜 Planned (Week 3+)

---

## 🤖 Core Data Models (Pydantic v2)

All data types are defined in [`core/models.py`](core/models.py) using Pydantic v2 with full validation.

### Knowledge Atoms

```python
from core.models import PLCAtom, RIVETAtom, EducationalLevel

# PLC programming knowledge atom
plc_atom = PLCAtom(
    id="plc:ab:timer-on-delay",
    title="Timer On-Delay (TON) - Allen-Bradley",
    description="TON timer delays output by preset time when input goes true",
    domain="plc",
    vendor="allen_bradley",
    plc_language="ladder",
    educational_level=EducationalLevel.INTRO,
    typical_learning_time_minutes=15,
    code_snippet="...",  # Ladder logic example
    prerequisites=["plc:generic:io-basics", "plc:generic:ladder-fundamentals"]
)

# Industrial maintenance troubleshooting atom
rivet_atom = RIVETAtom(
    id="rivet:motor:won-t-start",
    title="3-Phase Motor Won't Start",
    equipment_class="ac_induction_motor",
    symptoms=["Motor hums but doesn't rotate"],
    root_causes=[...],
    diagnostic_steps=[...],
    corrective_actions=[...],
    safety_level="danger",
    lockout_tagout_required=True
)
```

### Content Production

```python
from core.models import VideoScript, UploadJob

# Video script generated by Scriptwriter Agent
script = VideoScript(
    id="script:ohms-law-video",
    title="Ohm's Law - The Foundation of Electrical Engineering (#3)",
    outline=["Hook", "Explanation", "Example", "Recap"],
    script_text="[enthusiastic] This one equation...",
    atom_ids=["plc:generic:ohms-law"],
    duration_minutes=8,
    keywords=["ohms law", "V=IR", "electrical calculations"]
)

# YouTube upload job
upload = UploadJob(
    channel="industrial_skills_hub",
    video_script_id="script:ohms-law-video",
    audio_path="/media/ohms-law-audio.mp3",
    video_path="/media/ohms-law-video.mp4",
    thumbnail_path="/media/ohms-law-thumb.jpg",
    youtube_title="Ohm's Law - Tutorial (#3)",
    visibility="public",
    scheduled_time=None  # Publish immediately
)
```

### Curriculum Organization

```python
from core.models import Module, Course

# Module: Collection of related atoms
module = Module(
    id="module:electrical-fundamentals",
    title="Electrical Fundamentals",
    atom_ids=["plc:generic:voltage", "plc:generic:current", ...],
    estimated_hours=2.5
)

# Course: Collection of modules
course = Course(
    id="course:intro-to-plc",
    title="Introduction to PLC Programming",
    module_ids=["module:electrical-fundamentals", "module:plc-basics"],
    estimated_hours=10.0,
    price_usd=49.99
)
```

**See:** [`docs/ATOM_SPEC_UNIVERSAL.md`](docs/ATOM_SPEC_UNIVERSAL.md) for complete specification

---

## 🎓 Content Roadmap: 100+ Videos

Complete A-to-Z curriculum from electricity basics to AI-augmented automation.

### Track A: Electrical Fundamentals (Videos 1-20)
- What is Electricity?
- Voltage, Current, Resistance
- Ohm's Law (V=I×R)
- Electrical Power & Safety
- Sensors, Actuators, Motors

### Track B: PLC Fundamentals (Videos 21-40)
- What is a PLC?
- PLC Scan Cycle
- Ladder Logic Basics
- Timers & Counters
- Your First PLC Program

### Track C: Structured Text & Advanced (Videos 41-60)
- Introduction to Structured Text
- HMI Integration
- Data Logging & Trending
- Industrial Networks

### Track D: Vendor-Specific (Videos 61-80)
- Allen-Bradley ControlLogix
- Siemens S7-1200/1500
- Studio 5000 & TIA Portal

### Track E: AI & Automation (Videos 81-100)
- AI for PLC Programming
- Autonomous PLC Code Generation
- Predictive Maintenance
- The Future of Automation

**See:** [`plc/content/CONTENT_ROADMAP_AtoZ.md`](plc/content/CONTENT_ROADMAP_AtoZ.md) for all 100+ topics with keywords, hooks, examples, and quizzes

---

## 💰 Business Model & Monetization

### Multi-Stream Revenue (PLC Tutor)

**Free Tier:**
- YouTube channel (ads, organic growth)
- Core lessons (electricity basics, PLC fundamentals)
- Community engagement

**Paid Tier:**
- Structured courses ($49-$299): "Electricity Fundamentals to PLC Expert"
- Premium membership ($29/mo): Interactive AI tutor, personalized exercises
- Lab kits: Factory I/O project templates, simulation scenarios

**B2B (Later):**
- Corporate training licenses ($10K-$20K/org)
- White-label tutor for trade schools, OEMs
- API access to knowledge base + agents

### Revenue Targets

| Milestone | Subscribers | Revenue/Month | Key Metrics |
|-----------|-------------|---------------|-------------|
| Week 12 | 1,000 | $500 | First course sales, YPP application |
| Month 6 | 5,000 | $2,000 | YouTube Partner active, course bundles |
| Month 12 | 20,000 | $5,000 | Premium tier, B2B inquiries |
| Year 3 | 100,000+ | $200,000+ ($2.5M ARR) | Sustainable business, multiple revenue streams |

**See:** [`docs/TRIUNE_STRATEGY.md`](docs/TRIUNE_STRATEGY.md) for complete financial model

---

## 🔐 Security & Compliance

Agent Factory is built with **enterprise-grade security** from inception.

### Security by Design

**Before Writing Code:**
1. **Input:** Validate + sanitize all user input
2. **Data:** Encrypt sensitive data + log access
3. **Access:** Add auth + rate limits
4. **Output:** Filter PII + validate safety
5. **Abuse:** Add monitoring + circuit breakers

**Before Marking Complete:**
- [ ] Security implications documented
- [ ] Audit logging implemented (who, what, when)
- [ ] Error messages don't leak sensitive data
- [ ] Rate limits exist (if user-facing)
- [ ] Input validation with allow-lists

**Core Principles:**
- Principle of Least Privilege (default deny, explicit allow)
- Defense in Depth (multiple security layers)
- Fail Secure (errors block, not allow)
- Audit Everything (log all privileged operations)
- Assume Breach (limit blast radius)

**See:** [`docs/SECURITY_STANDARDS.md`](docs/SECURITY_STANDARDS.md) for complete guidelines

---

## 🤝 Contributing

We welcome contributions! Here's how:

### For Contributors

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Work in a git worktree** (see [`docs/GIT_WORKTREE_GUIDE.md`](docs/GIT_WORKTREE_GUIDE.md))
4. **Follow security standards** (see [`docs/SECURITY_STANDARDS.md`](docs/SECURITY_STANDARDS.md))
5. **Write tests** for new features
6. **Commit with conventional commits** (`feat:`, `fix:`, `docs:`, etc.)
7. **Push to your branch** (`git push origin feature/amazing-feature`)
8. **Open a Pull Request**

### Development Setup

```bash
# Install dev dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Validate models
poetry run python test_models.py

# Format code (if configured)
poetry run black .
poetry run isort .
```

### For AI Agents

If you're an AI agent working on this project:
- **Read [`CLAUDE.md`](CLAUDE.md)** for complete context
- **Check [`TASK.md`](TASK.md)** before starting work
- **Use git worktrees** for isolation (required by pre-commit hook)
- **Follow security checklist** before marking features complete
- **Update documentation** as you build

---

## 📞 Support & Community

- **Issues:** [GitHub Issues](https://github.com/your-username/agent-factory/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-username/agent-factory/discussions)
- **Email:** your-email@example.com

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

This project incorporates patterns from:
- [LangChain Crash Course](https://github.com/Mikecranesync/langchain-crash-course) (MIT License)
- [Archon](https://github.com/coleam00/archon) by Cole Medin (13.4k⭐)
- [context-engineering-intro](https://github.com/coleam00/context-engineering-intro) (11.8k⭐)

---

## 🙏 Acknowledgments

- **LangChain** - Agent orchestration framework
- **Cole Medin** - Production patterns (Archon, context engineering, settings service)
- **Anthropic** - Claude API for agent intelligence
- **OpenAI** - Embeddings & GPT-4
- **ElevenLabs** - Voice cloning technology
- **Supabase** - Database & vector search infrastructure

---

## 🗺️ Roadmap

### Phase 1: Foundation (Weeks 1-4) - **INFRASTRUCTURE COMPLETE**
- [x] Complete strategy documentation (TRIUNE, YOUTUBE_WIKI, AGENT_ORG, ROADMAP, CONTENT)
- [x] Implement Pydantic models (LearningObject, PLCAtom, RIVETAtom, VideoScript, etc.)
- [x] Supabase memory system (<1s session loading)
- [x] FREE LLM integration (Ollama, $0/month costs)
- [x] Settings service (runtime configuration)
- [x] GitHub automation (webhooks, auto-sync)
- [ ] Voice training & ElevenLabs setup (Issue #44) - USER TASK
- [ ] Create first 10 knowledge atoms (Issue #45) - USER TASK
- [ ] Public launch: 3 videos live (Week 4)

### Phase 2: Agent Implementation (Weeks 5-8)
- [ ] Research Agent + Atom Builder (Week 2)
- [ ] Scriptwriter Agent (Week 2)
- [ ] Video Production Pipeline (Voice, Assembly, Thumbnail) (Week 3)
- [ ] Publishing Pipeline (Strategy, Uploader) (Week 3)
- [ ] Community & Analytics Agents (Week 6)
- [ ] Executive Agents (AI CEO, Chief of Staff) (Week 7)
- [ ] Quality Checker + Atom Librarian (Week 7)
- [ ] All 18 agents operational (Week 8)

### Phase 3: Autonomous Operations (Weeks 9-12)
- [ ] Agents produce 80% autonomously (Week 9)
- [ ] 30 videos published, 1K subs, $500 revenue (Week 12)
- [ ] YouTube Partner Program approved
- [ ] First B2B inquiry

### Phase 4: Scale (Months 4-12)
- [ ] 100 videos published
- [ ] 20K subscribers, $5K/mo revenue
- [ ] Multi-platform presence (TikTok, Instagram)
- [ ] Agents fully autonomous (99% without human intervention)

### Phase 5: RIVET Launch (Year 1-2)
- [ ] Industrial maintenance vertical
- [ ] Reddit monitoring + validation pipeline
- [ ] B2B integrations (CMMS platforms)

### Phase 6: DAAS & Robot Licensing (Year 3-5)
- [ ] License knowledge bases to enterprises
- [ ] Humanoid robot training datasets
- [ ] $10-50M ARR target

**See:** [`docs/IMPLEMENTATION_ROADMAP.md`](docs/IMPLEMENTATION_ROADMAP.md) for detailed timeline

---

## ⭐ Star History

If you find this project useful, please consider giving it a star! ⭐

This helps others discover the project and shows your support for autonomous AI systems.

---

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| **Strategy Docs** | 7 documents (142KB total) |
| **Code Models** | 600+ lines (Pydantic v2) |
| **Infrastructure Status** | ✅ COMPLETE (memory, FREE LLMs, settings) |
| **Session Load Time** | <1 second (Supabase) |
| **LLM Costs** | $0/month (Ollama integration) |
| **Planned Videos** | 100+ (sequenced A-to-Z) |
| **Planned Agents** | 18 (5 teams) |
| **Implementation Timeline** | 12 weeks to autonomous operations |
| **Revenue Target (Year 3)** | $5M ARR (both verticals) |
| **Cost Savings** | $2,400-6,000/year (FREE LLMs) |

---

Made with ❤️ and 🤖 by humans and AI agents working together

**"The best way to predict the future is to build it autonomously."**

# Agent Factory - Project Structure

**Complete directory tree and file organization guide**

**Last Updated:** 2025-12-12

---

## 📂 Root Directory

**Philosophy:** Clean root with only essential files

```
Agent-Factory/
├── README.md                    # Project overview
├── CLAUDE.md                    # Instructions for Claude Code assistant
├── CONTRIBUTING.md              # Contribution guidelines
├── CHANGELOG.md                 # Version history
├── TASK.md                      # Current active tasks
├── CLAUDEUPDATE.md              # Latest updates and improvements
├── CLAUDEUPDATE_APPLIED.md      # Applied improvements summary
├── LICENSE                      # MIT License
├── .gitignore                   # Git ignore patterns
├── .env.example                 # Environment variable template
├── pyproject.toml               # Poetry dependencies
└── poetry.lock                  # Locked dependencies
```

**What's in root:**
- ✅ Core documentation (README, CLAUDE, CONTRIBUTING)
- ✅ Project configuration (pyproject.toml, .env.example)
- ✅ Active task tracking (TASK.md)
- ✅ Version control (CHANGELOG, LICENSE)

**What's NOT in root:**
- ❌ Status reports (moved to `archive/status-reports/`)
- ❌ Old deployment logs (moved to `archive/deployment-logs/`)
- ❌ Telegram bot fixes (moved to `archive/telegram-fixes/`)
- ❌ Legacy documentation (moved to `archive/legacy-docs/`)

---

## 🗂️ Main Directories

### `/agents/` - All AI Agents (259 Python files)

**Organized by function:**

```
agents/
├── __init__.py
├── executive/                   # C-Suite agents
│   ├── ai_ceo_agent.py
│   └── ai_chief_of_staff_agent.py
├── research/                    # Research & discovery
│   ├── research_agent.py
│   ├── oem_pdf_scraper_agent.py
│   └── trend_scout_agent.py
├── knowledge/                   # Knowledge management
│   ├── atom_builder_from_pdf.py
│   ├── atom_librarian_agent.py
│   ├── quality_checker_agent.py
│   └── citation_validator_agent.py
├── content/                     # Content creation
│   ├── master_curriculum_agent.py
│   ├── scriptwriter_agent.py
│   ├── seo_agent.py
│   └── thumbnail_agent.py
├── media/                       # Media production
│   ├── voice_production_agent.py
│   ├── video_assembly_agent.py
│   └── youtube_uploader_agent.py
├── engagement/                  # Community & analytics
│   ├── analytics_agent.py
│   ├── community_agent.py
│   └── social_amplifier_agent.py
├── orchestration/               # Coordination
│   └── master_orchestrator_agent.py
└── database/                    # Database utilities
    └── supabase_diagnostic_agent.py
```

---

### `/Guides for Users/` - User Documentation (11 guides)

**Organized by use case:**

```
Guides for Users/
├── README.md                    # Master index
├── quickstart/                  # Getting started
│   ├── QUICKSTART.md
│   ├── POETRY_GUIDE.md
│   └── OLLAMA_SETUP_COMPLETE.md
├── deployment/                  # Production deployment
│   ├── PRODUCTION_DEPLOYMENT.md
│   ├── BOT_DEPLOYMENT_GUIDE.md
│   ├── TELEGRAM_AUTO_START_GUIDE.md
│   └── TELEGRAM_BOT_100_PERCENT_RELIABLE.md
├── integration/                 # System integrations
│   ├── TELEGRAM_KB_INTEGRATION.md
│   └── CLAUDEUPDATE_APPLIED.md
└── development/                 # Developer guides
    ├── AGENT_EDITING_GUIDE.md
    └── QUICK_START_24_7.md
```

**Who uses this:**
- New users (quickstart/)
- DevOps engineers (deployment/)
- Developers (development/)
- Integration specialists (integration/)

---

### `/docs/` - Technical Documentation (50+ files)

**Organized by topic:**

```
docs/
├── README.md                    # Technical docs index
├── architecture/                # System architecture
│   ├── 00_architecture_platform.md
│   ├── 00_repo_overview.md
│   └── archon_architecture_analysis.md
├── implementation/              # Implementation guides
│   ├── 00_platform_roadmap.md
│   ├── 00_business_model.md
│   └── 00_competitive_analysis.md
├── database/                    # Database schemas & guides
│   ├── supabase_complete_schema.sql       # Main 7-table schema
│   ├── supabase_knowledge_schema.sql      # Knowledge atoms table
│   ├── supabase_memory_schema.sql         # Session memories table
│   ├── supabase_migrations.sql            # Database migrations
│   ├── supabase_agent_migrations.sql      # Agent-specific migrations
│   ├── setup_vector_search.sql            # Vector search setup
│   ├── 00_database_schema.md              # Schema documentation
│   └── DATABASE_TOOLS_GUIDE.md            # Database utilities guide
├── patterns/                    # Design patterns & best practices
│   ├── cole_medin_patterns.md
│   └── 00_gap_analysis.md
└── api/                        # API reference (future)
    └── API_REFERENCE.md
```

**Who uses this:**
- System architects (architecture/)
- Database administrators (database/)
- Technical leads (patterns/)
- API consumers (api/)

---

### `/scripts/` - Utility Scripts (30+ scripts)

**Organized by purpose:**

```
scripts/
├── README.md                    # Script documentation
├── deployment/                  # Deployment utilities
│   ├── deploy_supabase_schema.py
│   ├── verify_supabase_schema.py
│   └── verify_citations_column.py
├── knowledge/                   # Knowledge base operations
│   ├── upload_atoms_to_supabase.py
│   ├── query_knowledge_base.py
│   └── check_uploaded_atoms.py
├── automation/                  # Background automation
│   ├── scheduler_kb_daily.py
│   ├── health_monitor.py
│   └── bot_manager.py
├── testing/                     # Testing utilities
│   ├── test_telegram_kb.py
│   └── verify_kb_live.py
└── utilities/                   # Miscellaneous tools
    └── save_session_memory.py
```

**Usage:**
```bash
# Deployment
poetry run python scripts/deployment/deploy_supabase_schema.py

# Knowledge base
poetry run python scripts/knowledge/upload_atoms_to_supabase.py

# Automation
poetry run python scripts/automation/health_monitor.py
```

---

### `/core/` - Core Data Models

```
core/
├── models.py                    # Pydantic schemas (600+ lines)
├── agent_factory.py             # Main factory class
└── settings_service.py          # Runtime configuration
```

---

### `/examples/` - Demo Scripts

```
examples/
├── atom_builder_demo.py
├── perplexity_citation_demo.py
├── scriptwriter_demo.py
└── *.py
```

---

### `/data/` - Generated Data (Git-ignored)

```
data/
├── atoms/                       # Generated knowledge atoms
├── cache/                       # Temporary cache
├── extracted/                   # PDF extraction results
└── videos/                      # Generated videos
```

**Note:** All subdirectories git-ignored to keep repo clean

---

### `/archive/` - Old/Outdated Files (Git-ignored)

```
archive/
├── legacy-docs/                 # Old documentation (40+ files)
├── status-reports/              # Historical status reports
├── telegram-fixes/              # Telegram bot debugging logs
└── deployment-logs/             # Old deployment files
```

**Why archived:**
- Historical reference
- Not needed for active development
- Keeps root directory clean

---

## 🔍 Finding What You Need

### "I want to get started"
→ `Guides for Users/quickstart/QUICKSTART.md`

### "I want to deploy to production"
→ `Guides for Users/deployment/PRODUCTION_DEPLOYMENT.md`

### "I want to understand the architecture"
→ `docs/architecture/00_architecture_platform.md`

### "I want to create a new agent"
→ `Guides for Users/development/AGENT_EDITING_GUIDE.md`

### "I want to deploy the database schema"
→ `scripts/deployment/deploy_supabase_schema.py`

### "I want to understand the business model"
→ `docs/implementation/00_business_model.md`

### "I want to see what tasks are active"
→ `TASK.md` (root directory)

---

## 📊 File Count Summary

| Directory | Files | Purpose |
|-----------|-------|---------|
| `/` (root) | 12 | Essential docs & config |
| `/agents/` | 259 | AI agent implementations |
| `/Guides for Users/` | 11 | User documentation |
| `/docs/` | 50+ | Technical documentation |
| `/scripts/` | 30+ | Utility scripts |
| `/core/` | 3 | Core models |
| `/examples/` | 10+ | Demo scripts |
| `/archive/` | 70+ | Old files (git-ignored) |

**Total:** ~445 files (organized, clean, maintainable)

---

## 🎯 Design Philosophy

### Clean Root
- Only essential files
- Everything else categorized
- Easy to navigate

### Logical Organization
- User guides separate from technical docs
- Scripts organized by purpose
- Agents organized by function

### Git-Friendly
- Build artifacts ignored
- Generated data ignored
- Archive ignored

### Newcomer-Friendly
- README.md leads to everything
- Clear directory names
- Master indexes in each folder

---

## 🔄 Maintenance

### Adding New Files

**New user guide:**
→ Add to `Guides for Users/{category}/`
→ Update `Guides for Users/README.md`

**New technical doc:**
→ Add to `docs/{category}/`
→ Update `docs/README.md`

**New script:**
→ Add to `scripts/{purpose}/`
→ Update `scripts/README.md`

**New agent:**
→ Add to `agents/{function}/`
→ Update `agents/__init__.py`

### Archiving Old Files

**When to archive:**
- Documentation superseded by newer version
- Status reports >30 days old
- Deployment logs no longer relevant

**How to archive:**
```bash
mv old-file.md archive/legacy-docs/
```

---

## 📚 Related Documentation

- [README.md](README.md) - Project overview
- [CLAUDE.md](CLAUDE.md) - AI assistant instructions
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [Guides for Users/README.md](Guides%20for%20Users/README.md) - User guide index
- [docs/README.md](docs/README.md) - Technical docs index

---

**Maintained by:** Agent Factory Team
**Last Reorganization:** 2025-12-12
**Structure Version:** 2.0 (Major Cleanup)

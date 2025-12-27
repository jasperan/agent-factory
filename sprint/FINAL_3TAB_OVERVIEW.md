# RIVET COMPLETE BUILD - 3 TAB SPRINT
## MVP Sprint + Atlas CMMS Vision

---

## 🎯 THE VISION: Intelligent Equipment Knowledge System

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│                         RIVET: THE FULL VISION                                   │
│                                                                                  │
│   "Every piece of equipment has a brain. Every technician has an expert."       │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   PHASE 1 (This Sprint - Week 1)                                                │
│   ───────────────────────────────                                               │
│   ✅ Telegram bot with voice/text/photo                                         │
│   ✅ Context extraction (identify equipment + issue)                            │
│   ✅ Print upload + RAG query                                                   │
│   ✅ Manual library + search                                                    │
│   ✅ Response synthesis with safety warnings                                    │
│   ✅ Landing page + Stripe                                                      │
│                                                                                  │
│   PHASE 2 (Weeks 2-4)                                                           │
│   ────────────────────                                                          │
│   ⬜ Equipment hierarchy (subsystems, components)                               │
│   ⬜ Knowledge atoms (granular facts extracted from guides)                     │
│   ⬜ AI research logging (track what agent found/generated)                     │
│   ⬜ Expert review workflow (approve AI-generated content)                      │
│   ⬜ Feedback loop (tech ratings improve rankings)                              │
│                                                                                  │
│   PHASE 3 (Weeks 5-12)                                                          │
│   ─────────────────────                                                         │
│   ⬜ Full Atlas CMMS integration (work orders, assets, PM)                      │
│   ⬜ Equipment library UI (organize manuals/prints by machine)                  │
│   ⬜ Predictive maintenance (flag overdue based on hours)                       │
│   ⬜ Parts integration (recommend part numbers, check inventory)                │
│   ⬜ Analytics dashboard (failure patterns, resource effectiveness)             │
│   ⬜ Mobile app (native iOS/Android)                                            │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture: Current Sprint → Full Vision

```
                              PHASE 1 (NOW)                    PHASE 2-3 (FUTURE)
                              ────────────                     ─────────────────

                                   │
    ┌──────────────────────────────┼──────────────────────────────┐
    │                              │                              │
    ▼                              ▼                              ▼
┌─────────┐                  ┌─────────┐                   ┌─────────────┐
│  VOICE  │                  │  TEXT   │                   │ PHOTO/PDF   │
└────┬────┘                  └────┬────┘                   └──────┬──────┘
     │                            │                               │
     ▼                            │                               ▼
┌─────────┐                       │                        ┌───────────┐
│ WHISPER │                       │                        │ OCR/INDEX │
└────┬────┘                       │                        └─────┬─────┘
     │                            │                              │
     └────────────────────────────┼──────────────────────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │    CONTEXT EXTRACTOR      │◄─── Phase 1: Basic extraction
                    │                           │◄─── Phase 2: + KB atom matching
                    │  • Equipment identified   │◄─── Phase 3: + Predictive alerts
                    │  • Manufacturer detected  │
                    │  • Fault code parsed      │
                    │  • Issue type classified  │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
            ┌───────────┐ ┌───────────┐ ┌───────────────┐
            │   USER    │ │    OEM    │ │  KNOWLEDGE    │◄─── Phase 2: KB atoms
            │  PRINTS   │ │  MANUALS  │ │    ATOMS      │◄─── Phase 3: Verified facts
            │ (ChromaDB)│ │ (ChromaDB)│ │  (Postgres)   │
            └─────┬─────┘ └─────┬─────┘ └───────┬───────┘
                  │             │               │
                  └─────────────┼───────────────┘
                                │
                                ▼
                    ┌───────────────────────────┐
                    │   RESPONSE SYNTHESIZER    │◄─── Phase 1: Generate + cite
                    │                           │◄─── Phase 2: + Extract atoms
                    │  • Manual excerpts        │◄─── Phase 3: + Expert review
                    │  • Troubleshooting steps  │
                    │  • Safety warnings        │
                    │  • Source citations       │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │    AI RESEARCH LOG        │◄─── Phase 2: Track decisions
                    │                           │◄─── Phase 3: Analytics
                    │  • What was searched      │
                    │  • What was found         │
                    │  • Was fallback triggered │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │     TELEGRAM RESPONSE     │
                    │                           │
                    │  📖 Manual excerpt        │
                    │  🔧 Troubleshooting steps │
                    │  ⚠️ Safety warnings       │
                    │  📄 Source citations      │
                    └───────────────────────────┘
                                  │
                                  │ (Phase 2)
                                  ▼
                    ┌───────────────────────────┐
                    │     FEEDBACK LOOP         │◄─── Phase 2: Ratings
                    │                           │◄─── Phase 3: Auto-improvement
                    │  👍 Helpful               │
                    │  👎 Not helpful           │
                    │  → Improves rankings      │
                    └───────────────────────────┘
```

---

## 📊 Database Schema: MVP + Future Tables

```sql
-- ═══════════════════════════════════════════════════════════════════════════
-- PHASE 1: THIS SPRINT (Build these now)
-- ═══════════════════════════════════════════════════════════════════════════

-- Users (exists)
-- rivet_users: id, email, telegram_id, tier, stripe_customer_id

-- Machines (user's equipment)
CREATE TABLE machines (...);

-- User-uploaded electrical prints
CREATE TABLE prints (...);

-- OEM manual library  
CREATE TABLE equipment_manuals (...);

-- Print Q&A history
CREATE TABLE print_chat_history (...);

-- Context extraction log
CREATE TABLE context_extractions (...);

-- Missing manual tracker
CREATE TABLE manual_gaps (...);

-- ═══════════════════════════════════════════════════════════════════════════
-- PHASE 2: ADD AFTER MVP (Week 2-4)
-- ═══════════════════════════════════════════════════════════════════════════

-- Equipment hierarchy (subsystems of machines)
-- CREATE TABLE equipment_subsystems (...);

-- Granular components within subsystems
-- CREATE TABLE equipment_components (...);

-- Atomic knowledge facts (extracted from guides)
-- CREATE TABLE knowledge_atoms (...);

-- AI research job logging
-- CREATE TABLE ai_research_jobs (...);

-- AI-generated content awaiting review
-- CREATE TABLE ai_generated_resources (...);

-- Resource feedback from technicians
-- CREATE TABLE resource_feedback (...);

-- ═══════════════════════════════════════════════════════════════════════════
-- PHASE 3: FULL ATLAS INTEGRATION (Week 5+)
-- ═══════════════════════════════════════════════════════════════════════════

-- Work orders (from Atlas CMMS)
-- CREATE TABLE work_orders (...);

-- Assets (from Atlas CMMS)
-- CREATE TABLE assets (...);

-- Preventive maintenance schedules
-- CREATE TABLE preventive_maintenance (...);

-- Parts inventory
-- CREATE TABLE parts_inventory (...);
```

---

## 🚀 3-Tab Sprint Structure

| Tab | Branch | Phase 1 (Now) | Phase 2 Prep |
|-----|--------|---------------|--------------|
| **1** | `backend-complete` | DB + ChromaDB + Manual indexer | Schema ready for atoms/subsystems |
| **2** | `frontend-complete` | Landing + Stripe + Vercel | - |
| **3** | `bot-complete` | Voice + Context + Prints + Response | Logging ready for research jobs |

---

## 📋 Quick Start Commands

### Tab 1 - Backend
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
git checkout -b backend-complete
claude
# Paste: sprint/FINAL_TAB1_BACKEND.md
```

### Tab 2 - Frontend
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
git checkout -b frontend-complete
claude
# Paste: sprint/FINAL_TAB2_FRONTEND.md
```

### Tab 3 - Bot
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
git checkout -b bot-complete
claude
# Paste: sprint/FINAL_TAB3_BOT.md
```

---

## 🎯 Success Metrics

### Phase 1 (This Sprint)
| Metric | Target |
|--------|--------|
| Context extraction accuracy | >80% |
| Manual search relevance | >70% |
| Response includes safety warning | 100% for electrical |
| Voice transcription accuracy | >90% |
| Stripe checkout works | ✅ |

### Phase 2 (Weeks 2-4)
| Metric | Target |
|--------|--------|
| KB atoms extracted per guide | 3-5 |
| Expert approval rate | >70% |
| Research job logging | 100% |
| Feedback collection rate | >30% |

### Phase 3 (Weeks 5+)
| Metric | Target |
|--------|--------|
| Manual found (no generation needed) | >50% |
| Tech satisfaction rating | >4/5 stars |
| KB growth (atoms/month) | 50+ |
| Predictive alerts accuracy | >80% |

---

## 📁 File Links

| File | Purpose |
|------|---------|
| `sprint/FINAL_TAB1_BACKEND.md` | Tab 1 prompt (DB + Knowledge) |
| `sprint/FINAL_TAB2_FRONTEND.md` | Tab 2 prompt (Landing + Stripe) |
| `sprint/FINAL_TAB3_BOT.md` | Tab 3 prompt (Bot + AI) |
| `docs/SYSTEM_MAP_CURRENT.md` | Current architecture |
| `docs/SYSTEM_MAP_PROPOSED.md` | Full vision architecture |
| `ATLAS_SCHEMA_AND_AGENTIC_ENHANCEMENT.md` | Complete Atlas plan |

---

## 🔄 Post-Sprint: Phase 2 Quick Adds

After Day 5, add these with minimal effort:

```bash
# 1. Run Phase 2 migration
psql "$NEON_DB_URL" -f migrations/004_phase2_tables.sql

# 2. Add atom extraction to response synthesizer
# (already stubbed in Tab 3)

# 3. Add research logging
# (already stubbed in Tab 3)
```

---

## 💡 The Core Insight

> **Every troubleshooting session makes the system smarter.**
>
> Tech asks about brake pads → System generates guide → Expert approves →
> Atoms extracted → Next tech gets instant answer (no generation needed)
>
> This is your moat. Competitors have manuals. You have a learning system.

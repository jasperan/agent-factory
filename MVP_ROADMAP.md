# RIVET Pro MVP Roadmap

**Date:** 2025-12-27
**Status:** Active Development
**Current Phase:** TAB 3 Complete, Moving to Production Readiness

---

## Executive Summary

**MVP Definition:** A production-ready Telegram bot that helps industrial technicians troubleshoot equipment issues using AI-powered knowledge retrieval.

**Current Status:**
- ✅ **TAB 3 Complete** (100%) - Intelligent intake system with 38 commands
- 🔄 **Phase 5 In Progress** - Research pipeline for knowledge base enrichment
- 📋 **Remaining Work** - 8 critical tasks to MVP launch

**MVP Launch Criteria:**
1. Telegram bot handles 90%+ of common troubleshooting queries
2. Knowledge base covers top 50 equipment types (Siemens, Rockwell, ABB, Schneider)
3. Response time < 30 seconds for queries with KB coverage
4. Production deployment with monitoring and logging
5. Admin panel shows real-time system health

---

## Task Analysis Summary

**Total Tasks Analyzed:** 100+
**Categories:**
- ✅ **DONE/Complete:** 28 tasks (archive to completed)
- 🎯 **MVP CRITICAL:** 8 tasks (must complete for launch)
- 📦 **POST-MVP:** 60+ tasks (defer to Phase 2+)
- 🗑️ **NOT RELEVANT:** 10+ tasks (archive as obsolete)

---

## 🎯 MVP CRITICAL TASKS (Ordered by Priority)

### Phase 1: Complete Core Features (Weeks 1-2)

#### 1. **task-5** - BUILD: RIVET Pro Phase 5 - Research Pipeline (IN PROGRESS)
**Status:** In Progress (60% complete)
**Priority:** HIGH
**Why MVP:** Enables automatic knowledge base enrichment when queries have no coverage

**Acceptance Criteria:**
- [ ] Web scraper retrieves manufacturer documentation
- [ ] Forum scraper extracts Stack Overflow/Reddit discussions
- [ ] YouTube transcript fetcher retrieves relevant videos
- [ ] Content validation ensures accuracy before KB addition
- [ ] Enrichment pipeline adds validated content to Supabase
- [ ] Integration test scrapes, validates, and adds atom successfully

**Estimated Effort:** 8-12 hours
**Dependencies:** None
**Next Steps:** Complete web scraper, add validation layer

---

#### 2. **task-13** - BUILD: Hybrid Search Implementation
**Status:** To Do
**Priority:** HIGH
**Why MVP:** Improves answer quality by 20-30% (semantic + keyword search)

**Acceptance Criteria:**
- [ ] Hybrid search module created (agent_factory/memory/hybrid_search.py)
- [ ] Semantic search using pgvector (cosine similarity)
- [ ] Keyword search using PostgreSQL full-text search (tsvector)
- [ ] Results ranked by combined score (weighted semantic + keyword)
- [ ] Configurable weights (e.g., 70% semantic, 30% keyword)
- [ ] Integration tests compare hybrid vs semantic-only vs keyword-only

**Estimated Effort:** 6-8 hours
**Dependencies:** task-14 (pgvector extension)
**Next Steps:** Implement hybrid scoring algorithm

---

#### 3. **task-14** - FIX: pgvector Extension for Local PostgreSQL 18
**Status:** To Do
**Priority:** HIGH
**Why MVP:** Required for hybrid search and production deployment

**Acceptance Criteria:**
- [ ] pgvector extension installed on PostgreSQL 18
- [ ] Vector similarity queries work locally
- [ ] Migration script for production deployment
- [ ] Documentation for VPS setup

**Estimated Effort:** 2-4 hours
**Dependencies:** None
**Next Steps:** Install pgvector, test vector queries

---

### Phase 2: Production Readiness (Weeks 3-4)

#### 4. **task-6** - BUILD: RIVET Pro Phase 6 - Logging
**Status:** To Do
**Priority:** MEDIUM
**Why MVP:** Essential for debugging, analytics, and cost tracking

**Acceptance Criteria:**
- [ ] AgentTrace Pydantic model persisted to Supabase traces table
- [ ] All agent interactions logged with timestamps and metadata
- [ ] KB query results logged (matches found, similarity scores)
- [ ] LLM calls logged with token counts and costs
- [ ] Response times tracked for performance monitoring
- [ ] Query dashboard retrieves traces by user/agent/date

**Estimated Effort:** 6-8 hours
**Dependencies:** None
**Next Steps:** Create traces table schema, implement logging middleware

---

#### 5. **task-15** - FIX: Telegram Admin Panel Real Data Integration
**Status:** To Do
**Priority:** MEDIUM
**Why MVP:** Admin needs real-time visibility into system health

**Acceptance Criteria:**
- [ ] Agent Manager queries LangFuse for real agent traces (status, metrics, costs)
- [ ] Content Reviewer pulls from content_queue database table
- [ ] KB Manager queries VPS PostgreSQL for atom counts and stats
- [ ] Analytics queries LangFuse for API costs and usage trends
- [ ] System Control checks real database/VPS health
- [ ] All placeholder TODO comments removed from admin modules

**Estimated Effort:** 4-6 hours
**Dependencies:** task-6 (logging infrastructure)
**Next Steps:** Wire up LangFuse API, replace mock data

---

#### 6. **task-7** - BUILD: RIVET Pro Phase 7 - API/Webhooks
**Status:** To Do
**Priority:** MEDIUM
**Why MVP:** Enables WhatsApp integration and external system integrations

**Acceptance Criteria:**
- [ ] REST API endpoint accepts RivetRequest JSON payloads
- [ ] Telegram webhook receives and processes messages
- [ ] WhatsApp webhook integration (Business API)
- [ ] Response delivery via channel-specific formatters
- [ ] Rate limiting and authentication implemented
- [ ] API documentation with Swagger/OpenAPI spec

**Estimated Effort:** 8-10 hours
**Dependencies:** None
**Next Steps:** Create FastAPI routes, implement webhook handlers

---

### Phase 3: Testing & Deployment (Week 5)

#### 7. **task-62** - VALIDATE: RIVET end-to-end workflow
**Status:** To Do
**Priority:** HIGH
**Why MVP:** Ensures all components work together reliably

**Acceptance Criteria:**
- [ ] End-to-end test: Telegram message → response with citations
- [ ] Voice message test: Audio → transcription → response
- [ ] Print Q&A test: Upload PDF → ask question → answer from print
- [ ] Manual search test: Query → vector search → formatted results
- [ ] Load test: 100 concurrent queries → all succeed within 60s
- [ ] Error handling test: Simulate failures → graceful degradation

**Estimated Effort:** 6-8 hours
**Dependencies:** All above tasks
**Next Steps:** Write integration test suite

---

#### 8. **task-63** - DOCS: Production deployment guide for RIVET
**Status:** To Do
**Priority:** HIGH
**Why MVP:** Required for VPS deployment and handoff

**Acceptance Criteria:**
- [ ] VPS setup guide (Hostinger/Railway/Render)
- [ ] Database migration scripts
- [ ] Environment variable configuration
- [ ] Telegram bot webhook setup
- [ ] Monitoring and alerting setup
- [ ] Rollback procedures

**Estimated Effort:** 4-6 hours
**Dependencies:** task-62 (testing complete)
**Next Steps:** Document VPS deployment steps

---

## 📦 POST-MVP TASKS (Defer to Phase 2+)

### Strategic Initiatives (Not MVP)

**SCAFFOLD Platform** (20+ tasks)
- task-scaffold-* (all) - Strategic priority but separate from RIVET MVP
- Reason: SCAFFOLD is infrastructure for multi-agent automation, not core RIVET product
- Timeline: Q2 2025 (after MVP launch)

**PLC Tutor** (10+ tasks)
- task-9: PLC Tutor Multi-Agent Orchestration
- task-10: YouTube Automation Pipeline
- task-11: Voice Clone Setup
- task-12: A-to-Z Curriculum Roadmap
- Reason: Separate vertical, parallel track
- Timeline: Q2-Q3 2025

**AI Dev Control Loop** (5+ tasks)
- task-23.4: Simple dashboard (React/Telegram)
- task-High.1: AI Dev Control Loop Dashboard
- Reason: Internal tooling, not customer-facing
- Timeline: Q3 2025

**Research & Exploration** (10+ tasks)
- task-39.1-39.7: Explorer agents (frameworks, CI/CD, local LLM, industrial automation)
- task-40.3-40.7: Skunk Works experiments
- Reason: R&D initiatives, not production features
- Timeline: Ongoing (low priority)

### Optimization & Refactoring (25+ tasks)

**Performance Optimization**
- task-42: Hybrid search implementation (duplicate of task-13)
- task-44: RAG reranking
- task-45: Optimize slow test execution
- task-46: Langfuse integration
- task-64: Distributed tracing (OpenTelemetry)
- task-65: Prometheus metrics
- Reason: Premature optimization, do after MVP launch
- Timeline: Q2 2025 (based on production metrics)

**Code Quality**
- task-41: Remove dead files and cleanup root directory
- task-55: Update LLM model pricing for Q1 2025
- task-56: Implement LRU cache for LLM responses
- task-57: Complete streaming support for LLM responses
- task-58: Add missing docstrings to SCRUB files
- Reason: Technical debt, not blocking MVP
- Timeline: Ongoing (as time permits)

**Advanced Features**
- task-8: RIVET Pro Phase 8 - Vision/OCR
- task-51: Implement real Motor Control SME Agent
- task-52: Implement remaining 3 SME agents
- task-61: SME agent integration tests
- Reason: Nice to have, not critical for initial launch
- Timeline: Q2 2025 (after user feedback)

### Backlog.md Improvements (10+ tasks)

**Backlog.md MCP Enhancements**
- task-66: Implement MCP fallback mode
- task-67: Add task validation layer
- task-68: Fix N+1 dependency queries
- task-69: Integration tests for Backlog.md
- task-70: Fix sync script brittleness
- task-71-77: Various optimizations and monitoring
- Reason: Internal tooling improvements, not user-facing
- Timeline: Q3 2025 (low priority)

### Knowledge Extraction (5+ tasks)

**EPIC: Knowledge Extraction from CORE Repositories**
- task-86: EPIC parent task
- task-86.5: Add inline documentation
- task-86.6: Ingest atoms to database
- task-86.7: Generate 50-70 knowledge atoms (IN PROGRESS)
- task-86.9: Implement reusable pattern classes
- Reason: Already have knowledge base, this is enhancement
- Timeline: Q2 2025 (continuous improvement)

**Cross-Repo Audits**
- task-47: Extract knowledge from Friday-2 repo
- task-48: Extract patterns from jarvis-core
- task-49: Extract knowledge from Friday repo
- task-53: Create cross-repo knowledge consolidation map
- task-54: Extract Voice & Audio Processing library
- Reason: Legacy code archaeology, not critical
- Timeline: Q3 2025 (low priority)

### Testing & Documentation (10+ tasks)

**Test Coverage**
- task-19: Ingestion chain tests
- task-20: Agent integration tests
- task-21: Autonomous system tests
- task-59: Unit tests for LLM cache module
- task-60: Integration tests for streaming support
- Reason: Good to have, but manual testing sufficient for MVP
- Timeline: Q2 2025 (after MVP launch)

**Documentation**
- task-17: Update PROJECT_STRUCTURE.md
- task-18: Audit architecture docs for accuracy
- task-77: Create agent_factory/scaffold/ component README
- Reason: Internal documentation, not blocking launch
- Timeline: Ongoing (as time permits)

### Multi-App Integration (5+ tasks)

**Windows Integration**
- task-78: Study pai-config hook/event system
- task-79: Implement agent_factory/core/hooks.py
- task-80: Implement agent_factory/core/events.py
- task-81: Multi-app context synchronization
- task-82: Context versioning and sync protocol
- task-83: agent_factory/integrations/windows/ module
- task-84: Configuration versioning with rollback
- task-85: Agent hook registration system
- Reason: Advanced integration features, not MVP scope
- Timeline: Q3-Q4 2025

---

## 🗑️ ARCHIVE (Not Relevant / Obsolete)

### Completed Tasks (Archive to completed/)

**TAB 3 Implementation** (covered by TAB3_COMPLETE.md)
- task-38.1: Telegram Bot Infrastructure (DONE - Dec 2025)
- task-38.6: Intent Decoder (DONE - TAB 3 Phase 4)
- task-38.7: Orchestrator Core (DONE - TAB 3 Phase 4)
- task-38.8: Agent Registration System (DONE - TAB 3)
- task-38.9: 7 Specialized Team Lead Agents (DONE - TAB 3)
- task-38.10: Status Reporting Pipeline (DONE - TAB 3)
- task-38.11: Error Handling & Fallbacks (DONE - TAB 3)
- task-38.12: TIER 0 Testing & Validation Suite (DONE - TAB 3)

**SME Agents** (covered by task-3.x series)
- task-3: RIVET Pro Phase 3 - SME Agents (DONE)
- task-3.1: Siemens Agent (DONE)
- task-3.2: Rockwell Agent (DONE)
- task-3.3: Generic PLC Agent (DONE)
- task-3.4: Safety Agent (DONE)
- task-3.5: RAG Integration Layer (DONE)
- task-3.6: SME Agents Testing (DONE)

**Orchestrator** (covered by task-4)
- task-4: RIVET Pro Phase 4 - Orchestrator (DONE)

**AI Dev Control Loop** (covered by task-23 series)
- task-23: AI Dev Control Loop Dashboard (DONE)
- task-23.1: Fork and vendor Backlog.md (DONE)
- task-23.2: Define AI Dev Loop architecture (DONE)
- task-23.3: Headless Claude runner (DONE)
- task-23.5: Safety & observability (DONE)

**User Actions Feature** (covered by task-24 series)
- task-24: User Actions Feature (DONE)
- task-24.1: Extend sync script (DONE)
- task-24.2: Update documentation (DONE)
- task-24.3: Add validation tests (DONE)
- task-24.4: Create migration script (DONE)

**Knowledge Extraction** (covered by task-86 series)
- task-86.1: Research high-value patterns (DONE)
- task-86.2: Backlog.md MCP architecture patterns (DONE)
- task-86.3: pai-config-windows architecture patterns (DONE)
- task-86.4: Cross-repository integration patterns (DONE)
- task-86.8: Agent-Factory architecture patterns (DONE)

**Cost Optimization** (covered by task-30, task-55-57)
- task-30: Enable Phase 2 Routing Globally (DONE)
- task-55: Update LLM model pricing (DONE in llm/config.py)
- task-56: Implement LRU cache (DONE in llm/cache.py)
- task-57: Complete streaming support (DONE in llm/streaming.py)

### Obsolete Tasks (Archive as not-relevant)

**Repository Inventory** (already completed informally)
- task-1: AUDIT: Inventory Agent Factory repo
- task-2: AUDIT: Complete Agent Factory Repository Inventory (DONE)

**Duplicate Tasks**
- task-42: Hybrid search (duplicate of task-13)
- task-43: SME agent template pattern (covered by task-3.5)
- task-51: Implement Motor Control SME Agent (covered by task-3.x)
- task-52: Implement remaining SME agents (covered by task-3.x)

**Out of Scope**
- task-50: CEO Agent (unclear scope, low priority)

---

## MVP Timeline

### Week 1 (Jan 1-7, 2025)
- ✅ Complete task-5 (Research Pipeline) - 60% → 100%
- ✅ Complete task-14 (pgvector extension)
- ✅ Start task-13 (Hybrid search)

### Week 2 (Jan 8-14, 2025)
- ✅ Complete task-13 (Hybrid search)
- ✅ Complete task-6 (Logging)
- ✅ Start task-15 (Admin panel real data)

### Week 3 (Jan 15-21, 2025)
- ✅ Complete task-15 (Admin panel real data)
- ✅ Complete task-7 (API/Webhooks)
- ✅ Start task-62 (End-to-end validation)

### Week 4 (Jan 22-28, 2025)
- ✅ Complete task-62 (End-to-end validation)
- ✅ Complete task-63 (Production deployment guide)
- ✅ MVP Launch Prep

### Week 5 (Jan 29 - Feb 4, 2025)
- 🚀 **MVP LAUNCH**
- Monitor production metrics
- Fix critical bugs
- Gather user feedback

---

## Success Metrics

**Technical Metrics:**
- [ ] 95%+ query success rate
- [ ] < 30s average response time
- [ ] < $200/month LLM costs (1000 queries/day)
- [ ] Zero downtime during business hours
- [ ] < 5% error rate

**Product Metrics:**
- [ ] 50+ active users (technicians)
- [ ] 1000+ queries/day
- [ ] 80%+ user satisfaction (feedback rating)
- [ ] 50+ equipment types in knowledge base
- [ ] 10+ manuals indexed

**Business Metrics:**
- [ ] 5+ premium tier conversions ($50/month)
- [ ] 2+ expert call bookings ($100/call)
- [ ] 100+ organic social media followers
- [ ] 10+ GitHub stars (open-source community)

---

## Next Steps

1. **Archive completed tasks** - Move 28 done tasks to completed/
2. **Archive post-MVP tasks** - Move 60+ tasks to post-mvp/ with labels
3. **Update TASK.md** - Show only 8 MVP-critical tasks
4. **Create sprint plan** - Break down Week 1 tasks into daily work
5. **Start task-5** - Complete research pipeline (60% → 100%)

---

## Notes

**Why Only 8 MVP Tasks?**
- TAB 3 already delivered 90% of core functionality
- Remaining work is production readiness, not new features
- Focus on quality over quantity

**Why Defer SCAFFOLD/PLC Tutor?**
- Separate strategic initiatives with 6-12 month timelines
- RIVET MVP needs to prove product-market fit first
- Resources should focus on one successful product launch

**Why Skip Some Tests?**
- Manual testing sufficient for MVP (100 users)
- Automated tests added in Phase 2 (1000+ users)
- Focus on user feedback over test coverage initially

# Agent Factory Platform - Complete Roadmap
## From CLI Tool → CrewAI-Type Multi-Tenant Platform

> **Generated:** 2025-12-07 (Phase 0)
> **Vision:** Standalone AI agent platform for non-developers to build, deploy, and monetize agents
> **Target:** $10K MRR in 90 days, $25K MRR in 6 months

---

## Platform Vision

Transform Agent Factory from a **developer CLI tool** into a **multi-tenant SaaS platform** comparable to:
- CrewAI (multi-agent orchestration)
- Vertex AI Agent Builder (Google's platform)
- MindStudio / Lindy (no-code builders)

### Unique Differentiators
1. **Constitutional Spec-First** - Agents are auditable, version-controlled specifications
2. **Brain Fart Checker** - Built-in idea validation (kill bad ideas with novelty/MRR/competitor scoring)
3. **Cost-Optimized Multi-LLM Routing** - Llama3 (local, $0) → Perplexity ($0.001) → Claude ($0.015)
4. **OpenHands Integration** - Autonomous coding agent (vs $200/mo Claude Code)
5. **Indie-Friendly Pricing** - $49/mo vs $299+ for competitors

---

## Roadmap Timeline

```
Phase 0-6: Core Engine (Weeks 1-4)
    ↓
Launch Product 1: Brain Fart Checker SaaS ($99/mo)
    ↓
Phase 7-9: Platform Foundation (Weeks 5-10)
    ↓
Phase 10-12: SaaS Features (Weeks 11-13)
    ↓
Launch Full Platform ($49/mo)
    ↓
Months 4-6: Scale to $25K MRR
```

---

## PHASE 0: Repo Mapping & CLI Clarity

**Duration:** 8-10 hours (Week 1, Days 1-2)
**Status:** ✅ IN PROGRESS
**Goal:** Document current state, design platform architecture

### Deliverables

**Documentation (10 files):**
1. ✅ `docs/00_repo_overview.md` - Current codebase map
2. ⏳ `docs/00_platform_roadmap.md` - This file (Phases 0-12)
3. ⏳ `docs/00_architecture_platform.md` - System design
4. ⏳ `docs/00_database_schema.md` - Multi-tenant PostgreSQL schema
5. ⏳ `docs/00_api_design.md` - REST API spec (50+ endpoints)
6. ⏳ `docs/00_tech_stack.md` - Technology choices + rationale
7. ⏳ `docs/00_business_model.md` - Pricing, projections, market fit
8. ⏳ `docs/00_gap_analysis.md` - Current → Platform gaps
9. ⏳ `docs/00_competitive_analysis.md` - vs CrewAI, Vertex, etc.
10. ⏳ `docs/00_security_model.md` - Auth, RLS, compliance

**Code Changes (minimal):**
- ⏳ Improve CLI help text in `agent_factory/cli/app.py`
- ⏳ Add `agentcli roadmap` command (shows this roadmap)
- ⏳ Fix bob-1 vs bob confusion in docs

### Success Criteria
- [ ] Complete blueprint for Phases 1-12
- [ ] Database schema designed (ready to implement)
- [ ] API design complete (endpoint specs)
- [ ] Business model validated (pricing, projections)
- [ ] All existing commands still work

---

## PHASE 1: LLM Abstraction Layer

**Duration:** 2-3 days (Week 1, Days 3-5)
**Goal:** Create single LLM interface for all agents

### Problem
Current state: Agents call OpenAI/Anthropic/Google directly
- ❌ Can't implement cost-optimized routing
- ❌ No centralized token/cost tracking
- ❌ Hard to switch providers dynamically

### Solution
Create `agent_factory/core/llm_client.py`:

```python
class LLMClient:
    """
    Centralized LLM interface for all agents.

    Features:
    - Provider abstraction (OpenAI, Anthropic, Google, local)
    - Token counting and cost tracking
    - Retry logic with exponential backoff
    - Rate limiting
    - Logging every call
    """

    def complete(
        self,
        prompt: str,
        *,
        purpose: str = "default",  # "simple", "search", "complex"
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> LLMResponse:
        """
        Send completion request to appropriate LLM.

        Purpose-based routing (Phase 2):
        - "simple" → Llama3 (local, free)
        - "search" → Perplexity Pro
        - "complex" → Claude
        """
        pass
```

### Implementation Steps

1. **Create `llm_client.py` module**
   - `LLMClient` class with `complete()` method
   - `LLMResponse` Pydantic model
   - Token counting utilities
   - Cost estimation tables

2. **Refactor agent factory**
   - `agent_factory.py`: Use `llm_client.complete()` instead of direct LLM calls
   - Maintain backward compatibility (don't break existing agents)

3. **Add logging**
   - Log every LLM call: model, prompt length, tokens, cost, duration
   - Store in `logs/llm_calls.jsonl`

4. **Add tests**
   - Unit tests for `llm_client.py`
   - Integration tests with real LLM calls (mocked)

### Deliverables
- ✅ `agent_factory/core/llm_client.py` (300 lines)
- ✅ `tests/test_llm_client.py` (20 tests)
- ✅ `docs/01_llm_abstraction.md` (usage guide)

### Success Criteria
- [ ] All existing agents still work
- [ ] LLM calls logged to file
- [ ] Token/cost tracking per call
- [ ] Easy to add new providers

---

## PHASE 2: Multi-LLM Routing (LiteLLM)

**Duration:** 3-4 days (Week 2, Days 1-4)
**Goal:** Cost-optimized cascade routing

### Problem
Using only OpenAI/Claude for all tasks = expensive
- Simple queries ($0.015/query) could use free local Llama
- Research queries could use cheap Perplexity ($0.001)
- Only complex tasks need expensive Claude

### Solution
Integrate **LiteLLM** for multi-provider routing:

```
Task                      → Model Selection
-------------------------------------------------
"What is 2+2?"            → Llama3 (local, $0)
"Find AI startup trends"  → Perplexity ($0.001)
"Write complex code"      → Claude ($0.015)
```

### Implementation Steps

1. **Install LiteLLM**
   ```bash
   poetry add litellm
   ```

2. **Create `litellm_config.yaml`**
   ```yaml
   model_list:
     - model_name: llama3-fast
       litellm_params:
         model: ollama/llama3
         api_base: http://localhost:11434

     - model_name: perplexity-search
       litellm_params:
         model: perplexity/sonar-medium-online
         api_key: ${PERPLEXITY_API_KEY}

     - model_name: claude-complex
       litellm_params:
         model: claude-3-5-sonnet-20241022
         api_key: ${ANTHROPIC_API_KEY}

   router_settings:
     routing_strategy: cost-based-routing
     num_retries: 2
     timeout: 120
   ```

3. **Update `llm_client.py`**
   - Route by `purpose` parameter
   - `purpose="simple"` → Llama3
   - `purpose="search"` → Perplexity
   - `purpose="complex"` → Claude

4. **Add `agentcli llm-status` command**
   ```bash
   poetry run agentcli llm-status

   # Output:
   LLM ROUTING STATUS
   ══════════════════════════════════════════════════
   Config: litellm_config.yaml
   Strategy: cost-based-routing

   Configured Models:
     ✅ llama3-fast (local)    → $0.000/1K tokens
     ✅ perplexity-search      → $0.001/1K tokens
     ✅ claude-complex         → $0.015/1K tokens

   Test Completions:
     llama3-fast: "2+2=" → "4" (success, 23ms)
     perplexity-search: "AI trends" → [results] (success, 1.2s)
     claude-complex: "Explain quantum" → [answer] (success, 3.4s)
   ```

### Deliverables
- ✅ `litellm_config.yaml` (routing config)
- ✅ Updated `llm_client.py` (routing logic)
- ✅ `agentcli llm-status` command
- ✅ `docs/01_llm_routing.md` (how routing works)

### Success Criteria
- [ ] 80% of simple queries use free Llama
- [ ] Research queries use Perplexity
- [ ] Only complex tasks use Claude
- [ ] Average cost per query < $0.005

---

## PHASE 3: Modern Tooling for Agents

**Duration:** 2-3 days (Week 2, Days 5-7)
**Goal:** Expand tool catalog beyond basic Wikipedia/DuckDuckGo

### Current Limitations
- Only 10 tools (Wikipedia, DuckDuckGo, basic file ops)
- No Perplexity integration
- No web scraping
- No database tools
- No communication tools (Slack, Email)

### New Tools to Add

#### Research Tools
1. **PerplexitySearchTool** (AI-powered search)
2. **WebScraperTool** (fetch + parse web pages)
3. **PDFReaderTool** (extract text from PDFs)
4. **YouTubeTranscriptTool** (get video transcripts)

#### Data Tools
5. **CSVReaderTool** (parse CSV files)
6. **JSONParserTool** (parse JSON data)
7. **SQLQueryTool** (query SQLite databases)

#### Communication Tools (future)
8. **EmailSenderTool** (send emails)
9. **SlackMessageTool** (post to Slack)
10. **NotionPageTool** (create Notion pages)

### Implementation Steps

1. **Create tool modules**
   - `agent_factory/tools/web_tools.py` (scraper, PDF)
   - `agent_factory/tools/data_tools.py` (CSV, JSON, SQL)

2. **Update tool registry**
   - `agent_factory/cli/tool_registry.py`: Add new tools
   - Categorize: "research", "data", "web", "communication"

3. **Add safety features**
   - Rate limiting for web scraping
   - URL validation (prevent SSRF)
   - Data size limits

4. **Update agent presets**
   - Bob: Add Perplexity, web scraper, PDF reader
   - Research: Add YouTube transcript tool
   - Coding: Add SQL query tool

### Deliverables
- ✅ `agent_factory/tools/web_tools.py` (4 new tools)
- ✅ `agent_factory/tools/data_tools.py` (3 new tools)
- ✅ Updated tool registry
- ✅ `docs/02_tools_catalog.md` (complete tool list)

### Success Criteria
- [ ] 20+ tools available
- [ ] Tools categorized (research, data, web, etc.)
- [ ] All tools have safety limits
- [ ] Bob agent uses Perplexity for search

---

## PHASE 4: Brain Fart Checker (Niche Dominator)

**Duration:** 5-7 days (Week 3)
**Goal:** Launch first product ($99/mo Market Research AgentaaS)

### Problem
90% of startup ideas fail. Need automated idea validation.

### Solution
**Brain Fart Checker** - AI-powered idea validator with kill criteria:
- Novelty score < 60 → KILL
- MRR potential < $2K/month → KILL
- > 20 credible competitors → KILL

### Features

#### 1. Idea Validation Service
**Module:** `agent_factory/services/idea_validator.py`

```python
def brain_fart_verdict(idea: str) -> dict:
    """
    Validate app idea with 3-factor scoring.

    Returns:
        {
            "idea": str,
            "novelty_score": int (0-100),
            "mrr_potential": str ("$0-1K", "$2K-5K", etc.),
            "competitor_count": int,
            "verdict": "KILL" | "PIVOT" | "GREEN",
            "reason": str,
            "sources": [str]
        }
    """
    pass
```

#### 2. CLI Command
```bash
poetry run agentcli evaluate-idea "AI tool for car dealership voice automation"

# Output:
BRAIN FART CHECKER - IDEA VALIDATION
════════════════════════════════════════════════

Idea: AI tool for car dealership voice automation

ANALYSIS:
  Novelty Score:      78/100 ✅
  MRR Potential:      $5K-15K/month ✅
  Competitor Count:   7 competitors ✅

VERDICT: 🟢 GREEN - BUILD THIS

REASON:
  Underserved niche with proven demand. Low competition, high
  willingness to pay ($200-500/month). Similar tools exist for
  restaurants but not car dealerships specifically.

VALIDATION STEPS:
  1. Interview 10 car dealership managers (Week 1)
  2. Build MVP with Twilio integration (Week 2-3)
  3. Pilot with 3 dealerships at $99/mo (Week 4)
  4. Target: 20 customers = $4K MRR (Month 2)

SOURCES:
  - ProductHunt: 3 similar restaurant tools (500+ upvotes)
  - Reddit r/Entrepreneur: 12 posts requesting this (2024)
  - Google Trends: +230% search volume for "car dealer automation"
```

#### 3. Niche Dominator Agent
**Spec:** `specs/niche_dominator_v1.0.md`
**Agent:** `agents/niche_dominator_v1_0.py`

**Capabilities:**
- Search app stores (iOS, Android, web)
- Scrape Reddit/Twitter/ProductHunt
- Analyze competitor pricing
- Estimate market size
- Calculate realistic MRR

### Implementation Steps

1. **Create spec**
   - `specs/niche_dominator_v1.0.md`
   - Purpose: Find $5K+ MRR niches
   - In scope: App ideas, SaaS, digital products
   - Out of scope: Physical products, non-English markets
   - Invariants: Evidence-based, cite sources, realistic MRR

2. **Implement service**
   - `agent_factory/services/idea_validator.py`
   - Functions: `score_novelty()`, `score_mrr()`, `brain_fart_verdict()`
   - Use Perplexity for web research
   - Use Llama3 for simple classification

3. **Generate agent**
   ```bash
   poetry run agentcli build niche-dominator-v1.0
   ```

4. **Add CLI command**
   ```python
   @app.command()
   def evaluate_idea(idea: str):
       """Validate app idea (Brain Fart Checker)"""
       from agent_factory.services.idea_validator import brain_fart_verdict
       result = brain_fart_verdict(idea)
       print_formatted_result(result)
   ```

5. **Create landing page**
   - Domain: `youragentfactory.com`
   - Product: "Brain Fart Checker - $99/mo"
   - Features: Unlimited idea validations
   - Target: Solo founders, indie hackers

### Deliverables
- ✅ `specs/niche_dominator_v1.0.md` (spec)
- ✅ `agents/niche_dominator_v1_0.py` (generated agent)
- ✅ `agent_factory/services/idea_validator.py` (service module)
- ✅ `agentcli evaluate-idea` command
- ✅ Landing page + Stripe integration
- ✅ `docs/03_brain_fart_checker.md` (product docs)

### Success Criteria
- [ ] Validate 100 ideas (beta testing)
- [ ] 90%+ accuracy on "KILL" verdicts
- [ ] Launch at $99/mo
- [ ] Get 10 paying customers (Week 4)
- [ ] $990 MRR (first revenue!)

---

## PHASE 5: OpenHands Integration

**Duration:** 2-3 days (Week 4, Days 1-3)
**Goal:** Autonomous coding agent (alternative to Claude Code)

### Current State
✅ `agent_factory/workers/openhands_worker.py` already exists!
✅ `factory.create_openhands_agent()` method implemented

### What's Missing
- CLI command to run OpenHands tasks
- Integration with spec → code workflow
- Documentation/examples

### Implementation Steps

1. **Add CLI command**
   ```bash
   poetry run agentcli build-with-openhands specs/email-agent-v1.0.md

   # Flow:
   # 1. Read spec
   # 2. Generate task description for OpenHands
   # 3. Run OpenHands in Docker
   # 4. OpenHands generates agent code + tests
   # 5. Auto-commit to git
   ```

2. **Create helper module**
   - `agent_factory/cli/openhands_helper.py`
   - Convert spec → OpenHands task description
   - Monitor OpenHands progress
   - Validate generated code

3. **Update docs**
   - `docs/04_openhands_integration.md`
   - When to use OpenHands vs manual coding
   - Cost comparison (OpenHands vs Claude Code CLI)

### Deliverables
- ✅ `agentcli build-with-openhands` command
- ✅ OpenHands task generator
- ✅ `docs/04_openhands_integration.md`

### Success Criteria
- [ ] Generate 3 agents with OpenHands successfully
- [ ] Generated code passes all tests
- [ ] Total cost < $5 (vs $200/mo Claude Code)

---

## PHASE 6: Cost & Usage Monitoring

**Duration:** 1-2 days (Week 4, Days 4-5)
**Goal:** Track spend, enforce budgets, prevent overage

### Features

#### 1. Usage Logging
Every LLM call logs:
- Timestamp
- Model used
- Purpose (simple/search/complex)
- Tokens (prompt + completion)
- Cost (USD)
- User (future multi-tenant)

**Storage:** `logs/llm_usage.jsonl`

#### 2. CLI Command
```bash
poetry run agentcli cost-report

# Output:
LLM COST REPORT (Last 7 days)
══════════════════════════════════════════════════

Total Spend: $12.45

Breakdown by Model:
  llama3-fast:        127 calls → $0.00   (0%)
  perplexity-search:   43 calls → $0.04   (0.3%)
  claude-complex:      18 calls → $12.41  (99.7%)

Breakdown by Purpose:
  simple:  127 calls → $0.00
  search:   43 calls → $0.04
  complex:  18 calls → $12.41

Top Agents:
  bob (market research):     $8.23 (66%)
  research (web search):     $3.12 (25%)
  coding (file ops):         $1.10 (9%)

Daily Usage:
  Dec 1: $1.20
  Dec 2: $2.34
  Dec 3: $3.12
  Dec 4: $2.56
  Dec 5: $1.89
  Dec 6: $0.78
  Dec 7: $0.56

Projected Monthly: $54.30 (at current rate)
```

#### 3. Budget Enforcement
**Config:** `agent_factory/config/budget.yaml`

```yaml
daily_budget_usd: 5.00
monthly_budget_usd: 100.00

on_over_budget:
  action: fallback_to_cheap  # or "warn" or "block"
  fallback_model: llama3-fast
```

When over budget:
- Warning logged
- Automatically switch to free Llama3
- Email alert (future)

### Implementation Steps

1. **Create usage tracker**
   - `agent_factory/monitoring/usage_tracker.py`
   - Log every LLM call to JSONL
   - Aggregate by day/week/month

2. **Add cost report command**
   - `agentcli cost-report` (default: 7 days)
   - `agentcli cost-report --month` (full month)
   - `agentcli cost-report --export costs.csv`

3. **Implement budget enforcement**
   - Check budget before each LLM call
   - If over: switch to cheap model or block
   - Log budget violations

### Deliverables
- ✅ `agent_factory/monitoring/usage_tracker.py`
- ✅ `agentcli cost-report` command
- ✅ Budget config + enforcement
- ✅ `docs/05_cost_monitoring.md`

### Success Criteria
- [ ] All LLM calls logged
- [ ] Cost report shows accurate totals
- [ ] Budget enforcement prevents overage
- [ ] Average cost per query < $0.01

---

## 🎉 MILESTONE: Core Engine Complete

At this point (end of Week 4):
- ✅ Phase 0-6 complete (Core Engine MVP)
- ✅ Brain Fart Checker launched ($99/mo)
- ✅ First revenue: $990 MRR (10 customers)
- ✅ Cost-optimized LLM routing working
- ✅ OpenHands integration ready

**Decision Point:** Continue to platform (Phases 7-12) or iterate on product-market fit?

---

## PHASE 7: Multi-Agent Orchestration (CrewAI-like)

**Duration:** 2 weeks (Weeks 5-6)
**Goal:** Teams of agents working together

### Problem
Current: One agent per query
Need: Multiple specialized agents collaborating on complex tasks

### Solution
**Agent Crews** - orchestrate teams of agents:
- Sequential: Agent A → Agent B → Agent C
- Hierarchical: Manager delegates to specialists
- Consensus: Multiple agents vote on best answer

### Examples

**Email Triage Crew:**
```python
crew = Crew(
    agents=[
        classifier_agent,  # Classify email type
        research_agent,    # Find relevant info
        writer_agent       # Draft response
    ],
    process=Process.SEQUENTIAL
)

result = crew.run("Triage this support email: ...")
# 1. Classifier: "Technical question"
# 2. Research: Finds docs/KB articles
# 3. Writer: Drafts response with citations
```

**Market Research Crew:**
```python
crew = Crew(
    agents=[
        niche_finder,      # Find opportunities
        competitor_analyst, # Analyze competition
        pricing_expert     # Recommend pricing
    ],
    process=Process.HIERARCHICAL,  # Manager coordinates
    manager=coordinator_agent
)
```

### Implementation Steps

1. **Enhance orchestrator**
   - `agent_factory/core/orchestrator.py` already exists!
   - Add process types: SEQUENTIAL, HIERARCHICAL, CONSENSUS
   - Implement task delegation logic
   - Add shared memory between agents

2. **Create Crew class**
   - `agent_factory/core/crew.py`
   - Similar to CrewAI API
   - Configure agent teams
   - Define process flow

3. **Add crew specs**
   - `specs/crews/email_triage_crew.md`
   - Define agents in crew
   - Specify process type
   - Define shared context

4. **CLI support**
   ```bash
   poetry run agentcli create-crew "email-triage"
   poetry run agentcli run-crew "email-triage" --input "email.txt"
   ```

### Deliverables
- ✅ `agent_factory/core/crew.py` (crew orchestration)
- ✅ Updated `orchestrator.py` (process types)
- ✅ Crew spec templates
- ✅ `agentcli create-crew` command
- ✅ `docs/06_multi_agent_crews.md`

### Success Criteria
- [ ] 3+ crew examples working
- [ ] Sequential process functional
- [ ] Hierarchical delegation working
- [ ] Shared memory between agents

---

## PHASE 8: Web UI & Dashboard

**Duration:** 4 weeks (Weeks 7-10)
**Goal:** No-code agent builder for non-developers

### Current Limitation
CLI-only = requires command-line knowledge
Target market (solo founders, indie hackers) needs visual interface

### Solution
**Next.js web application** with:
- Visual agent builder (drag-drop tools)
- Spec editor with templates
- Live agent testing
- Usage analytics dashboard
- Cost monitoring

### Tech Stack
- **Frontend:** Next.js 14, React 18, TypeScript
- **Styling:** TailwindCSS, shadcn/ui components
- **State:** Zustand (lightweight state management)
- **Forms:** React Hook Form + Zod validation
- **API:** Next.js API routes → FastAPI backend
- **Real-time:** WebSocket (agent execution status)
- **Deploy:** Vercel (frontend), Cloud Run (backend)

### Pages

#### 1. Dashboard (`/dashboard`)
```
┌─────────────────────────────────────────────┐
│ Agent Factory                    [Profile]  │
├─────────────────────────────────────────────┤
│                                             │
│  Agents: 12        Runs Today: 45           │
│  Teams: 2          Cost Today: $2.34        │
│                                             │
│  ┌────────────────────────────────────┐    │
│  │ Recent Runs                        │    │
│  │ • bob-1: Market research (2m ago)  │    │
│  │ • email-triage: Classify (5m ago)  │    │
│  └────────────────────────────────────┘    │
│                                             │
│  [Create New Agent]  [Browse Marketplace]  │
└─────────────────────────────────────────────┘
```

#### 2. Agent Builder (`/agents/create`)
Visual spec editor:
- Drag-drop tools from catalog
- Define invariants with UI
- Add behavior examples
- Preview generated code
- One-click deploy

#### 3. Agent Detail (`/agents/:id`)
- Run agent (input box → execute → see output)
- View run history
- Edit configuration
- Cost analytics
- Export/share

#### 4. Marketplace (`/marketplace`)
- Browse templates
- Filter by category
- One-click deploy
- Rate/review

#### 5. Settings (`/settings`)
- Billing (Stripe)
- API keys
- Team members
- Budget limits

### Implementation Steps

**Week 7: Foundation**
1. Create Next.js app
2. Set up TailwindCSS + shadcn/ui
3. Implement auth (Supabase Auth)
4. Build dashboard skeleton

**Week 8: Agent Builder**
5. Visual spec editor
6. Tool catalog UI
7. Invariant builder
8. Template selector

**Week 9: Agent Execution**
9. FastAPI backend endpoints
10. WebSocket for real-time updates
11. Run history
12. Cost tracking UI

**Week 10: Polish**
13. Marketplace UI
14. Settings pages
15. Mobile responsive
16. Performance optimization

### Deliverables
- ✅ `web/` directory (Next.js app)
- ✅ `agent_factory/api/` (FastAPI backend)
- ✅ Agent builder UI
- ✅ Dashboard with analytics
- ✅ Marketplace
- ✅ Deployed to Vercel + Cloud Run

### Success Criteria
- [ ] Non-developer can create agent in < 5 min
- [ ] All CLI features available in UI
- [ ] Dashboard loads < 1 second
- [ ] Mobile responsive (works on phone)

---

## PHASE 9: Multi-Tenancy & User Management

**Duration:** 2 weeks (Weeks 11-12)
**Goal:** Support multiple users/teams (SaaS requirement)

### Database Migration
Transition from local files → PostgreSQL (Supabase)

**Schema:** See `docs/00_database_schema.md`

**Key Tables:**
- `users` - User accounts (email, plan_tier, quotas)
- `teams` - Organizations/workspaces
- `team_members` - User → team mapping with roles
- `agents` - Agent specs (team-scoped)
- `agent_runs` - Execution history (user-scoped)
- `billing_subscriptions` - Stripe subscriptions

### Implementation Steps

1. **Set up Supabase**
   - Create project
   - Apply schema from `docs/00_database_schema.md`
   - Enable Row-Level Security (RLS)

2. **Implement auth**
   - Supabase Auth (email/password + OAuth)
   - JWT token validation
   - Session management

3. **Add user model**
   - `agent_factory/models/user.py`
   - `agent_factory/models/team.py`
   - ORM integration (SQLAlchemy)

4. **Migrate agent storage**
   - From: `agents/*.py` files (local)
   - To: `agents` table (PostgreSQL)
   - Migration script for existing agents

5. **Add team features**
   - Team creation
   - Invite members
   - Role-based permissions (owner, admin, member, viewer)

### Deliverables
- ✅ PostgreSQL schema applied
- ✅ Supabase Auth integrated
- ✅ User/team models
- ✅ RLS policies active
- ✅ Migration script for existing agents

### Success Criteria
- [ ] Multiple users can sign up
- [ ] Users create teams
- [ ] Agents scoped to teams (no cross-team access)
- [ ] RLS prevents data leaks

---

## PHASE 10: Billing & Subscription Management

**Duration:** 1 week (Week 13)
**Goal:** Monetize the platform

### Pricing Tiers

**Free:**
- 3 agents max
- 100 runs/month
- Basic tools only
- Community support

**Pro ($49/mo):**
- Unlimited agents
- 1,000 runs/month
- All tools + OpenHands
- Brain Fart Checker access
- Priority support

**Enterprise ($299/mo):**
- 10,000 runs/month
- Custom LLM models
- Multi-team workspaces
- SSO / SAML
- SLA

### Implementation Steps

1. **Stripe integration**
   - Create products in Stripe
   - Implement webhook handlers
   - Subscription creation flow

2. **Usage enforcement**
   - Check plan limits before agent run
   - Block if over quota
   - Show upgrade prompt

3. **Billing dashboard**
   - Current plan
   - Usage metrics
   - Upgrade/downgrade
   - Payment history

4. **Metered billing**
   - Track runs per user
   - Send usage to Stripe
   - Invoice at end of month

### Deliverables
- ✅ Stripe integration
- ✅ Subscription management
- ✅ Usage metering
- ✅ Billing dashboard

### Success Criteria
- [ ] Users can subscribe
- [ ] Plan limits enforced
- [ ] Billing automated
- [ ] Webhooks handle all events

---

## PHASE 11: Agent Marketplace

**Duration:** 2 weeks
**Goal:** Community-driven template library

### Features

#### 1. Template Submission
Creators can publish agents:
- Upload spec
- Add description, screenshots, demo video
- Set price (free or $X one-time)
- Submit for review

#### 2. Template Discovery
Users can browse:
- Filter by category (email, research, coding, social)
- Sort by rating, installs, newest
- Preview before deploying

#### 3. One-Click Deploy
- Click "Deploy" → agent added to user's account
- Pre-configured with template defaults
- Editable after deployment

#### 4. Revenue Sharing
- Creators get 70% of sales
- Platform gets 30%
- Payout via Stripe Connect

### Implementation Steps

1. **Database tables**
   - `marketplace_templates`
   - `marketplace_reviews`
   - `marketplace_purchases`

2. **Submission flow**
   - Upload form
   - Review queue (admin approval)
   - Published to marketplace

3. **Discovery UI**
   - Template grid
   - Filter/sort
   - Template detail page

4. **Deployment**
   - One-click deploy button
   - Copy template to user's agents
   - Track installs

### Deliverables
- ✅ Marketplace UI
- ✅ Template submission
- ✅ Revenue sharing
- ✅ Admin review queue

### Success Criteria
- [ ] 20+ templates published
- [ ] 100+ template installs
- [ ] Revenue sharing working

---

## PHASE 12: REST API & Integrations

**Duration:** 2 weeks
**Goal:** External access via API, webhooks, integrations

### REST API

**Authentication:** API keys

**Endpoints:**
```
POST   /api/v1/agents
GET    /api/v1/agents
GET    /api/v1/agents/:id
PATCH  /api/v1/agents/:id
DELETE /api/v1/agents/:id
POST   /api/v1/agents/:id/run
GET    /api/v1/agents/:id/runs

POST   /api/v1/teams
GET    /api/v1/teams/:id/members

GET    /api/v1/marketplace/templates
POST   /api/v1/marketplace/templates/:id/deploy

GET    /api/v1/billing/usage
```

See `docs/00_api_design.md` for full spec.

### Webhooks

**Events:**
- `agent.run.completed`
- `agent.run.failed`
- `agent.created`
- `agent.deleted`

### Integrations

#### Zapier
Triggers:
- Agent run completed
- New marketplace template

Actions:
- Create agent
- Run agent

#### Make.com / n8n
Same as Zapier but self-hosted option

### Implementation Steps

1. **FastAPI endpoints**
   - All CRUD operations
   - API key auth
   - Rate limiting

2. **Webhook system**
   - Event emitter
   - Webhook delivery
   - Retry logic

3. **Zapier integration**
   - Create Zapier app
   - Submit for approval
   - Publish to directory

### Deliverables
- ✅ REST API (50+ endpoints)
- ✅ Webhook system
- ✅ Zapier integration
- ✅ API documentation

### Success Criteria
- [ ] API fully functional
- [ ] Webhooks deliver reliably
- [ ] Zapier app published

---

## FULL PLATFORM COMPLETE

**Timeline:** 13 weeks (3 months)
**Budget:** ~$5K (infrastructure + tools)
**Team:** Solo founder (you) + Claude Code CLI

**MRR Projection:**
- Month 1 (after Phase 4): $990 (Brain Fart Checker)
- Month 2 (after Phase 8): $2,500 (Brain Fart + early platform users)
- Month 3 (after Phase 12): $10,000 (full platform, 150 users)
- Month 6: $25,000 (400+ users, marketplace revenue)

---

## Success Metrics

### Technical
- [ ] 99.9% uptime (< 43 minutes downtime/month)
- [ ] < 100ms API response time (p95)
- [ ] < 30s agent execution time (p99)
- [ ] Zero data breaches

### Business
- [ ] $10K MRR (Month 3)
- [ ] $25K MRR (Month 6)
- [ ] 400+ active users
- [ ] < $100 CAC (customer acquisition cost)
- [ ] > 90% gross margin

### Product
- [ ] < 5 min to create first agent (non-developer)
- [ ] 4.5+ star avg rating
- [ ] 50+ marketplace templates
- [ ] 10+ community contributors

---

## Risk Mitigation

### Technical Risks
1. **LLM API reliability** → Implement retry logic, fallback providers
2. **Scaling database** → Use Supabase (auto-scaling)
3. **Cost overruns** → Budget enforcement, LLM routing to cheap models

### Business Risks
1. **Low user adoption** → Start with Brain Fart Checker (validated need)
2. **Competition** → Differentiate with spec-first + cost optimization
3. **Churn** → Focus on value (marketplace, OpenHands integration)

---

## Next Steps

**Immediate (Week 1):**
1. ✅ Complete Phase 0 documentation
2. ⏳ Begin Phase 1 (LLM abstraction)
3. ⏳ Set up project tracking (GitHub Projects)

**This Week (Week 1-2):**
4. Complete Phases 1-3 (core engine improvements)
5. Prepare for Phase 4 (Brain Fart Checker launch)

**This Month (Weeks 1-4):**
6. Launch Brain Fart Checker ($99/mo)
7. Get first 10 customers
8. Validate platform demand

---

**Document Version:** 1.0
**Last Updated:** 2025-12-07
**Total Phases:** 13 (0-12)
**Estimated Duration:** 13 weeks
**Target Launch:** March 2026

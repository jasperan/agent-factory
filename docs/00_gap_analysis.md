# Agent Factory - Gap Analysis: Current State vs Platform Vision

**Version:** 1.0
**Last Updated:** 2025-12-07
**Status:** Phase 0 Documentation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Assessment](#current-state-assessment)
3. [Platform Vision Target](#platform-vision-target)
4. [Technical Gaps](#technical-gaps)
5. [Feature Gaps](#feature-gaps)
6. [Infrastructure Gaps](#infrastructure-gaps)
7. [Critical Path Analysis](#critical-path-analysis)
8. [Effort Estimation](#effort-estimation)
9. [Risk Assessment](#risk-assessment)
10. [Prioritization Matrix](#prioritization-matrix)

---

## Executive Summary

### Current State (Phase 0)

Agent Factory is a **functional CLI tool** for creating LangChain agents from markdown specifications. It works well for single developers with technical expertise, but lacks the infrastructure and features needed to become a commercial SaaS platform.

**What Works Today:**
- ✅ Spec-to-agent generation (8-step wizard)
- ✅ Agent validation and testing (pytest integration)
- ✅ Basic tool library (10 tools)
- ✅ Agent presets (bob, research, coding)
- ✅ CLI commands (build, validate, eval, list, create, edit)
- ✅ 205 passing tests

**What's Missing:**
- ❌ Multi-tenant database
- ❌ Web UI
- ❌ Multi-LLM routing
- ❌ Cost tracking
- ❌ Authentication/authorization
- ❌ API endpoints
- ❌ Billing system
- ❌ Marketplace
- ❌ Scalable infrastructure

### Platform Vision (Phase 12)

A **multi-tenant SaaS platform** comparable to CrewAI, enabling non-developers to build, deploy, and monetize AI agents through a web interface.

**Target Capabilities:**
- 🎯 1,000+ concurrent users
- 🎯 <200ms API response time
- 🎯 $10K MRR in 90 days
- 🎯 99.9% uptime
- 🎯 Team-based collaboration
- 🎯 Visual spec editor
- 🎯 Community marketplace
- 🎯 REST API for integrations

### The Gap

**Total Effort:** ~13 weeks (Phases 1-12)
**Critical Path:** 8 weeks (blocking dependencies)
**Parallelizable Work:** 5 weeks (can be done concurrently)

**Biggest Risks:**
1. Multi-tenancy implementation (complex RLS policies)
2. LLM cost management (can spiral out of control)
3. Marketplace quality control (preventing malicious templates)
4. Migration from CLI to web (user retention)

---

## Current State Assessment

### What Exists Today

#### Core Engine (agent_factory/core/)
```python
# Working components:

1. AgentFactory (agent_factory.py) - 420 lines
   - create_agent() - Creates LangChain AgentExecutor
   - create_orchestrator() - Simple keyword-based routing
   - create_openhands_agent() - OpenHands integration (partial)

2. Tools (agent_factory/tools/)
   - research_tools.py - Wikipedia, DuckDuckGo, Tavily
   - file_tools.py - Read, write, search files
   - time_tools.py - Current time, timezone conversion
   - Total: 10 tools

3. Presets (agent_factory/cli/agent_presets.py)
   - bob - Market research specialist
   - research - General research agent
   - coding - Code generation agent
```

#### CLI System (agent_factory/cli/)
```python
# Commands available:

agentcli build <spec>    # Generate agent + tests
agentcli validate <spec> # Check spec format
agentcli eval <agent>    # Run pytest
agentcli list            # Show specs
agentcli create          # Interactive wizard
agentcli edit <agent>    # Modify agent
agentcli status          # System info
```

#### Testing
```python
# Test coverage:
tests/
  - test_agent_factory.py (30 tests)
  - test_tools.py (45 tests)
  - test_cli.py (60 tests)
  - test_validation.py (40 tests)
  - test_presets.py (30 tests)

Total: 205 tests passing
Coverage: ~75%
```

### What's Partially Built

1. **Orchestrator** (agent_factory/core/orchestrator.py)
   - Basic keyword routing works
   - No LangGraph integration yet
   - No event bus implementation
   - No team coordination

2. **OpenHands Integration** (agent_factory/core/openhands_worker.py)
   - Worker class exists
   - Integration not complete
   - No spec-to-code pipeline

3. **Spec Validation** (agent_factory/cli/spec_validator.py)
   - Format validation works
   - No semantic validation (e.g., "does this spec make sense?")
   - No duplicate detection

### What Doesn't Exist

1. **LLM Abstraction Layer** - Direct OpenAI/Anthropic calls only
2. **Multi-LLM Routing** - No LiteLLM integration
3. **Cost Tracking** - No token counting or cost attribution
4. **Database** - File-based storage only
5. **Web UI** - CLI only
6. **API** - No REST endpoints
7. **Authentication** - No user accounts
8. **Multi-Tenancy** - Single-user only
9. **Billing** - No Stripe integration
10. **Marketplace** - No template sharing

---

## Platform Vision Target

### Target Architecture (Phase 12)

```
[Web UI - Next.js]
       |
       v
[API Gateway - FastAPI]
       |
       v
[Core Engine - LangGraph + LiteLLM]
       |
       v
[Data Layer - PostgreSQL + Redis]
       |
       v
[Infrastructure - Cloud Run + Supabase]
```

### Target Features

| Category | Features |
|----------|----------|
| **User Management** | Sign up, login, OAuth, teams, roles, permissions |
| **Agent Building** | Visual spec editor, template library, tool selector, live preview |
| **Agent Execution** | Run agents, view history, stream responses, debug mode |
| **Multi-Agent** | Team workflows, sequential/parallel execution, consensus voting |
| **Cost Management** | Usage tracking, budget alerts, LLM optimization, cost analytics |
| **Collaboration** | Team workspaces, shared agents, comments, version control |
| **Marketplace** | Browse templates, purchase/sell, ratings, revenue sharing |
| **API Access** | REST API, webhooks, API keys, rate limiting |
| **Billing** | Subscription tiers, usage billing, invoices, payment methods |
| **Monitoring** | Metrics dashboard, logs, tracing, alerts |

### Target Metrics

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| **Users** | 1 (CLI) | 1,000 | 999 |
| **Agents Created** | ~50 (local files) | 10,000+ | 9,950+ |
| **API Uptime** | N/A | 99.9% | N/A |
| **Response Time (p95)** | N/A | <200ms | N/A |
| **LLM Cost per User** | ~$0 | <$5/mo | N/A |
| **MRR** | $0 | $10,000 | $10,000 |
| **Conversion Rate** | N/A | 10% (free → paid) | N/A |

---

## Technical Gaps

### Gap 1: LLM Abstraction Layer (Phase 1)

**Current:**
```python
# Direct API calls, no abstraction
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

llm = ChatOpenAI(model="gpt-4")  # Hard-coded
```

**Target:**
```python
# Unified interface via LiteLLM
from agent_factory.llm import LLMRouter

llm = LLMRouter()
response = await llm.route(
    prompt="...",
    task_type="research",  # Auto-selects cheapest capable model
    max_cost=0.01
)
```

**Work Required:**
1. Install LiteLLM: `poetry add litellm`
2. Create `agent_factory/llm/router.py` (~300 lines)
3. Create `agent_factory/llm/config.py` (model registry, ~100 lines)
4. Update `AgentFactory.create_agent()` to use router
5. Add cost tracking to responses
6. Write tests (~15 tests)

**Effort:** 2-3 days
**Blockers:** None
**Risk:** Low (LiteLLM is stable, well-documented)

---

### Gap 2: Multi-LLM Routing (Phase 2)

**Current:**
- Single model per agent (specified in spec)
- No fallback logic
- No cost optimization

**Target:**
- Intelligent routing based on task complexity
- Automatic fallback (local → Perplexity → Claude)
- Cost budgets and alerts
- Token counting and attribution

**Work Required:**
1. Implement routing logic (decision tree)
   ```python
   if task_type == "simple_query":
       return "ollama/llama3"  # Free
   elif task_type == "research":
       return "perplexity/sonar"  # $0.001/1K tokens
   elif task_type == "complex_reasoning":
       return "anthropic/claude-sonnet"  # $0.015/1K tokens
   ```

2. Add fallback chain
   ```python
   try:
       return await call_model("ollama/llama3")
   except:
       try:
           return await call_model("perplexity/sonar")
       except:
           return await call_model("anthropic/claude-sonnet")
   ```

3. Add cost tracking
   ```python
   class CostTracker:
       def track(self, model, tokens, response_time):
           cost = self.calculate_cost(model, tokens)
           await db.increment_user_cost(user_id, cost)
           await self.check_budget(user_id)
   ```

4. Create admin dashboard for cost analysis

**Effort:** 3-4 days
**Blockers:** Requires Gap 1 (LLM abstraction)
**Risk:** Medium (cost calculations must be accurate)

---

### Gap 3: Modern Tooling Integration (Phase 3)

**Current Tools:**
- Wikipedia (basic search, 3-sentence summaries)
- DuckDuckGo (5 results, no API key)
- Tavily (AI-optimized, requires key)
- File operations (read, write, search)
- Time utilities

**Missing Tools:**
- ❌ Perplexity Pro API (AI-powered research)
- ❌ GitHub API (repo analysis, issue creation)
- ❌ Stripe API (payment processing)
- ❌ Email/SMS (notifications)
- ❌ Database queries (PostgreSQL)
- ❌ Cloud storage (Google Cloud Storage)
- ❌ Web scraping (Playwright)
- ❌ Data analysis (pandas, matplotlib)
- ❌ Code execution (sandbox)

**Work Required:**
1. Create `agent_factory/tools/perplexity_tool.py`
   ```python
   class PerplexitySearchTool(BaseTool):
       name = "perplexity_search"
       description = "AI-powered search with citations"

       def _run(self, query: str) -> str:
           response = requests.post(
               "https://api.perplexity.ai/chat/completions",
               json={
                   "model": "llama-3.1-sonar-small-128k-online",
                   "messages": [{"role": "user", "content": query}]
               }
           )
           return response.json()["choices"][0]["message"]["content"]
   ```

2. Create GitHub, Stripe, email, database tools (~50 lines each)

3. Add tool registry (dynamic loading)
   ```python
   class ToolRegistry:
       def __init__(self):
           self.tools = self._discover_tools()

       def _discover_tools(self):
           # Auto-discover all BaseTool subclasses
           return {
               tool.name: tool
               for tool in BaseTool.__subclasses__()
           }
   ```

4. Update CLI to show available tools: `agentcli tools list`

**Effort:** 2-3 days
**Blockers:** None (can parallelize with Gaps 1-2)
**Risk:** Low (straightforward API integrations)

---

### Gap 4: Brain Fart Checker (Phase 4)

**Current:**
- No idea validation functionality
- No market research automation
- No competitive analysis

**Target:**
- Multi-agent idea validator
- Kill criteria enforcement (novelty < 60, MRR < $2K, competitors > 20)
- Structured output (IdeaEvaluation schema)
- Standalone product ($99/mo)

**Work Required:**
1. Create `agent_factory/tools/brain_fart_checker.py` (~500 lines)
   - Market research agent (Perplexity)
   - Competitive analysis agent (Perplexity)
   - Technical feasibility agent (Claude)
   - Revenue projection agent (Claude)
   - Synthesis agent (Claude)

2. Create Pydantic schemas
   ```python
   class IdeaEvaluation(BaseModel):
       novelty_score: float
       market_size_score: float
       competition_score: float
       execution_difficulty: float
       estimated_mrr: float
       competitor_count: int
       verdict: str  # BUILD, ITERATE, KILL
       reasoning: str
       next_steps: List[str]
   ```

3. Create CLI command: `agentcli brainfart <idea>`

4. Create web UI (simple form → results page)

5. Set up Stripe product for $99/mo subscription

**Effort:** 5-7 days
**Blockers:** Requires Gap 2 (multi-LLM routing), Gap 3 (Perplexity tool)
**Risk:** Medium (prompt engineering for consistent output)

**Revenue Potential:** First product launch! Target 10 paid users = $990/mo MRR

---

### Gap 5: OpenHands Integration (Phase 5)

**Current:**
- Partial integration (worker class exists)
- No spec-to-code pipeline
- No test generation

**Target:**
- Automatic code generation from specs
- Test generation with pytest
- Code review and validation
- Continuous improvement loop

**Work Required:**
1. Complete `agent_factory/core/openhands_worker.py` integration
   ```python
   class OpenHandsWorker:
       async def generate_code_from_spec(self, spec: AgentSpec):
           # Send spec to OpenHands
           # Receive generated code
           # Validate syntax
           # Run tests
           # Return code + test results
   ```

2. Create prompt templates for spec → code conversion

3. Add code review step (Claude validates generated code)

4. Integrate with CLI: `agentcli build <spec> --use-openhands`

5. Add web UI toggle: "Generate code automatically"

**Effort:** 2-3 days
**Blockers:** Requires Gap 1 (LLM abstraction)
**Risk:** High (OpenHands output quality varies)

---

### Gap 6: Cost Monitoring Dashboard (Phase 6)

**Current:**
- No cost tracking
- No token counting
- No attribution to users/teams

**Target:**
- Real-time cost dashboard
- Per-user/team/agent cost breakdown
- Budget alerts
- Cost optimization recommendations

**Work Required:**
1. Add cost tracking to all LLM calls
   ```python
   async def track_llm_call(user_id, model, tokens):
       cost = calculate_cost(model, tokens)
       await db.execute(
           "INSERT INTO llm_usage (user_id, model, tokens, cost) VALUES ($1, $2, $3, $4)",
           user_id, model, tokens, cost
       )
   ```

2. Create dashboard queries
   ```sql
   -- Daily cost by user
   SELECT
       user_id,
       DATE(created_at) as date,
       SUM(cost) as daily_cost
   FROM llm_usage
   GROUP BY user_id, DATE(created_at)
   ORDER BY daily_cost DESC
   ```

3. Add budget enforcement
   ```python
   async def check_budget(user_id):
       usage = await get_monthly_cost(user_id)
       tier = await get_user_tier(user_id)

       budgets = {"free": 1, "pro": 10, "enterprise": 100}

       if usage >= budgets[tier]:
           raise BudgetExceededError(f"Monthly budget of ${budgets[tier]} exceeded")
   ```

4. Create CLI command: `agentcli costs --month 2025-12`

5. Create web UI dashboard (charts with Chart.js)

**Effort:** 1-2 days
**Blockers:** Requires Gap 2 (cost tracking in router)
**Risk:** Low (straightforward SQL + UI)

---

### Gap 7: Multi-Agent Orchestration (Phase 7)

**Current:**
- Basic keyword-based routing
- No team coordination
- No consensus mechanisms
- No parallel execution

**Target:**
- LangGraph-based orchestration
- Sequential, parallel, hierarchical workflows
- Consensus voting
- Event-driven communication

**Work Required:**
1. Migrate orchestrator to LangGraph
   ```python
   from langgraph.graph import StateGraph

   graph = StateGraph(AgentState)
   graph.add_node("router", router_agent)
   graph.add_node("researcher", research_agent)
   graph.add_node("coder", coding_agent)

   graph.add_edge("router", "researcher")
   graph.add_edge("router", "coder")
   graph.set_entry_point("router")

   app = graph.compile()
   ```

2. Implement team workflows
   - Sequential: Task 1 → Task 2 → Task 3
   - Parallel: Task 1 + Task 2 + Task 3 (concurrent)
   - Hierarchical: Manager delegates to specialists

3. Add consensus voting
   ```python
   async def consensus_decision(agents, query):
       responses = await asyncio.gather(*[
           agent.run(query) for agent in agents
       ])

       # Majority vote
       votes = [parse_decision(r) for r in responses]
       return max(set(votes), key=votes.count)
   ```

4. Add event bus (Redis pub/sub)
   ```python
   class EventBus:
       async def publish(self, event: str, data: dict):
           await redis.publish(event, json.dumps(data))

       async def subscribe(self, event: str, callback):
           pubsub = redis.pubsub()
           pubsub.subscribe(event)

           async for message in pubsub.listen():
               await callback(json.loads(message["data"]))
   ```

**Effort:** 2 weeks
**Blockers:** Requires Gaps 1-6 (core engine complete)
**Risk:** Medium (LangGraph learning curve)

---

### Gap 8: Web UI & Dashboard (Phase 8)

**Current:**
- CLI only
- No web interface
- No visual tools

**Target:**
- Full-featured web application
- Visual spec editor (Monaco)
- Agent builder (drag-and-drop)
- Execution dashboard
- Team collaboration

**Work Required:**

1. **Set up Next.js project**
   ```bash
   npx create-next-app@latest agent-factory-ui --typescript --tailwind --app
   cd agent-factory-ui
   npm install @supabase/supabase-js zustand @tanstack/react-query
   ```

2. **Create core pages**
   ```typescript
   /app
     /dashboard
       page.tsx         // Dashboard home
     /agents
       page.tsx         // Agent list
       /new
         page.tsx       // Agent builder
       /[id]
         page.tsx       // Agent detail
         /edit
           page.tsx     // Agent editor
     /marketplace
       page.tsx         // Template browser
     /settings
       page.tsx         // User settings
   ```

3. **Build agent spec editor**
   ```typescript
   import Editor from "@monaco-editor/react";

   export function SpecEditor({ value, onChange }) {
     return (
       <Editor
         height="600px"
         language="markdown"
         value={value}
         onChange={onChange}
         theme="vs-dark"
         options={{
           minimap: { enabled: false },
           fontSize: 14,
           wordWrap: "on"
         }}
       />
     );
   }
   ```

4. **Build tool selector**
   ```typescript
   export function ToolSelector({ selected, onChange }) {
     const tools = useTools();  // Fetch from API

     return (
       <DragDropContext onDragEnd={handleDragEnd}>
         <Droppable droppableId="available">
           {tools.map(tool => (
             <ToolCard key={tool.name} tool={tool} />
           ))}
         </Droppable>

         <Droppable droppableId="selected">
           {selected.map(tool => (
             <ToolCard key={tool.name} tool={tool} />
           ))}
         </Droppable>
       </DragDropContext>
     );
   }
   ```

5. **Build execution dashboard**
   ```typescript
   export function AgentDashboard({ agentId }) {
     const runs = useAgentRuns(agentId);
     const metrics = useAgentMetrics(agentId);

     return (
       <div>
         <MetricsCards
           totalRuns={metrics.total_runs}
           successRate={metrics.success_rate}
           avgCost={metrics.avg_cost}
           avgDuration={metrics.avg_duration}
         />

         <RunsTable runs={runs} />

         <CostChart data={metrics.cost_by_day} />
       </div>
     );
   }
   ```

6. **Integrate with backend API**
   ```typescript
   import { useQuery, useMutation } from "@tanstack/react-query";

   export function useAgents() {
     return useQuery({
       queryKey: ["agents"],
       queryFn: async () => {
         const res = await fetch("/api/v1/agents", {
           headers: {
             Authorization: `Bearer ${session.access_token}`
           }
         });
         return res.json();
       }
     });
   }

   export function useCreateAgent() {
     return useMutation({
       mutationFn: async (spec) => {
         const res = await fetch("/api/v1/agents", {
           method: "POST",
           headers: {
             "Content-Type": "application/json",
             Authorization: `Bearer ${session.access_token}`
           },
           body: JSON.stringify(spec)
         });
         return res.json();
       }
     });
   }
   ```

**Effort:** 4 weeks
**Blockers:** Requires Gap 12 (REST API)
**Risk:** Medium (complex UI, many edge cases)

---

### Gap 9: Multi-Tenancy & Database (Phase 9)

**Current:**
- Single-user file-based storage
- No teams or workspaces
- No role-based access control

**Target:**
- Team-based multi-tenancy
- Row-Level Security (RLS) for data isolation
- Role-based permissions (owner, admin, member)
- Audit logging

**Work Required:**

1. **Set up Supabase project**
   - Create project at supabase.com
   - Run database migrations
   - Configure RLS policies
   - Set up authentication

2. **Migrate data model**
   - From: Files in `specs/`
   - To: PostgreSQL tables (see `docs/00_database_schema.md`)

3. **Implement RLS policies**
   ```sql
   -- Users can only see agents from their teams
   CREATE POLICY agents_team_isolation ON agents
       FOR ALL
       USING (
           team_id IN (
               SELECT team_id
               FROM team_members
               WHERE user_id = current_setting('app.current_user_id')::uuid
           )
       );
   ```

4. **Update all queries to be team-aware**
   ```python
   # Before
   agents = await db.execute("SELECT * FROM agents")

   # After
   await db.set_user_context(user_id)
   agents = await db.execute("SELECT * FROM agents")
   # RLS automatically filters to user's teams
   ```

5. **Add team management UI**
   - Create team
   - Invite members
   - Manage roles
   - Transfer ownership

6. **Add audit logging**
   ```python
   async def log_audit_event(user_id, action, resource_type, resource_id):
       await db.execute(
           """
           INSERT INTO audit_logs (user_id, action, resource_type, resource_id)
           VALUES ($1, $2, $3, $4)
           """,
           user_id, action, resource_type, resource_id
       )
   ```

**Effort:** 2 weeks
**Blockers:** Requires Gap 8 (web UI for team management)
**Risk:** High (RLS policies are complex, easy to misconfigure)

**Security Note:** This is the most critical gap for production readiness. Improper RLS can lead to data leaks.

---

### Gap 10: Billing & Subscriptions (Phase 10)

**Current:**
- No payment processing
- No subscription tiers
- No usage limits

**Target:**
- Stripe integration
- 3 tiers (Free, Pro, Enterprise)
- Usage-based billing
- Invoices and receipts

**Work Required:**

1. **Set up Stripe**
   ```bash
   npm install stripe
   poetry add stripe
   ```

2. **Create subscription products in Stripe dashboard**
   - Free: $0/mo, 3 agents, 100 runs/mo
   - Pro: $49/mo, unlimited agents, 1000 runs/mo
   - Enterprise: $299/mo, 10K runs/mo, SSO, SLA

3. **Implement checkout flow**
   ```typescript
   import { loadStripe } from "@stripe/stripe-js";

   export async function createCheckoutSession(priceId: string) {
     const res = await fetch("/api/v1/billing/checkout", {
       method: "POST",
       body: JSON.stringify({ priceId })
     });

     const { sessionId } = await res.json();

     const stripe = await loadStripe(process.env.NEXT_PUBLIC_STRIPE_KEY);
     await stripe.redirectToCheckout({ sessionId });
   }
   ```

4. **Handle webhooks**
   ```python
   @app.post("/webhooks/stripe")
   async def stripe_webhook(request: Request):
       payload = await request.body()
       sig_header = request.headers["stripe-signature"]

       event = stripe.Webhook.construct_event(
           payload, sig_header, webhook_secret
       )

       if event["type"] == "checkout.session.completed":
           session = event["data"]["object"]
           await upgrade_user_plan(session["client_reference_id"], "pro")

       elif event["type"] == "invoice.payment_failed":
           await downgrade_user_plan(session["client_reference_id"], "free")

       return {"status": "success"}
   ```

5. **Implement usage limits**
   ```python
   async def check_quota(user_id):
       user = await db.execute("SELECT * FROM users WHERE id = $1", user_id)

       if user["monthly_runs_used"] >= user["monthly_runs_quota"]:
           raise QuotaExceededError(
               f"You've used {user['monthly_runs_used']} of {user['monthly_runs_quota']} runs this month. "
               f"Upgrade to Pro for unlimited runs."
           )
   ```

6. **Add billing portal**
   ```python
   @app.post("/api/v1/billing/portal")
   async def create_portal_session(user_id: str):
       session = stripe.billing_portal.Session.create(
           customer=user.stripe_customer_id,
           return_url="https://agentfactory.com/dashboard"
       )

       return {"url": session.url}
   ```

**Effort:** 1 week
**Blockers:** Requires Gap 9 (user accounts)
**Risk:** Low (Stripe is well-documented)

**Revenue Impact:** This is the monetization unlock. Without billing, MRR = $0.

---

### Gap 11: Marketplace (Phase 11)

**Current:**
- No template sharing
- No community features
- No discovery mechanism

**Target:**
- Community template library
- Ratings and reviews
- Purchase flow (free + paid templates)
- Revenue sharing (70% creator, 30% platform)

**Work Required:**

1. **Create marketplace tables** (already in schema)
   ```sql
   CREATE TABLE agent_templates (
       id UUID PRIMARY KEY,
       creator_id UUID REFERENCES users(id),
       name TEXT NOT NULL,
       description TEXT,
       spec_template TEXT,
       category TEXT,
       price_cents INTEGER DEFAULT 0,
       published BOOLEAN DEFAULT false,
       ...
   );
   ```

2. **Build template submission flow**
   ```typescript
   export function TemplateSubmissionForm() {
     const submit = useSubmitTemplate();

     return (
       <form onSubmit={handleSubmit}>
         <Input name="name" label="Template Name" />
         <Textarea name="description" label="Description" />
         <SpecEditor value={spec} onChange={setSpec} />
         <Select name="category" options={categories} />
         <Input name="price" type="number" label="Price ($)" />

         <Button type="submit">Submit for Review</Button>
       </form>
     );
   }
   ```

3. **Build marketplace browser**
   ```typescript
   export function MarketplaceBrowser() {
     const templates = useTemplates({ category, sortBy: "popular" });

     return (
       <div>
         <CategoryFilter />
         <SortDropdown />

         <div className="grid grid-cols-3 gap-4">
           {templates.map(template => (
             <TemplateCard
               key={template.id}
               template={template}
               onPurchase={handlePurchase}
             />
           ))}
         </div>
       </div>
     );
   }
   ```

4. **Implement purchase flow**
   ```python
   @app.post("/api/v1/marketplace/templates/{template_id}/purchase")
   async def purchase_template(template_id: str, user_id: str):
       template = await db.execute("SELECT * FROM agent_templates WHERE id = $1", template_id)

       if template["price_cents"] > 0:
           # Charge via Stripe
           payment = stripe.PaymentIntent.create(
               amount=template["price_cents"],
               currency="usd",
               customer=user.stripe_customer_id
           )

           if payment.status != "succeeded":
               raise PaymentError("Payment failed")

       # Record purchase
       await db.execute(
           """
           INSERT INTO template_purchases (user_id, template_id, amount_cents)
           VALUES ($1, $2, $3)
           """,
           user_id, template_id, template["price_cents"]
       )

       # Revenue sharing (70% creator, 30% platform)
       creator_share = template["price_cents"] * 0.70
       await db.execute(
           """
           INSERT INTO revenue_shares (creator_id, amount_cents, template_id)
           VALUES ($1, $2, $3)
           """,
           template["creator_id"], creator_share, template_id
       )

       return {"status": "success", "template": template}
   ```

5. **Add ratings and reviews**
   ```python
   @app.post("/api/v1/marketplace/templates/{template_id}/rate")
   async def rate_template(template_id: str, rating: int, review: str, user_id: str):
       await db.execute(
           """
           INSERT INTO template_ratings (template_id, user_id, rating, review)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (template_id, user_id) DO UPDATE
           SET rating = $3, review = $4, updated_at = NOW()
           """,
           template_id, user_id, rating, review
       )
   ```

6. **Add moderation system**
   - Automated checks (malicious code detection)
   - Manual review queue
   - Reporting system
   - Ban mechanism

**Effort:** 2 weeks
**Blockers:** Requires Gap 10 (billing for paid templates)
**Risk:** High (moderation is critical to prevent abuse)

**Revenue Impact:** 30% platform fee on paid templates can become significant revenue stream.

---

### Gap 12: REST API (Phase 12)

**Current:**
- No API endpoints
- No external integrations
- CLI only

**Target:**
- Full REST API (50+ endpoints)
- API key authentication
- Rate limiting
- Webhooks
- Comprehensive docs (OpenAPI 3.1)

**Work Required:**

1. **Set up FastAPI application**
   ```python
   from fastapi import FastAPI

   app = FastAPI(
       title="Agent Factory API",
       version="1.0.0",
       docs_url="/docs",
       redoc_url="/redoc"
   )
   ```

2. **Implement authentication middleware**
   ```python
   from fastapi.security import HTTPBearer

   security = HTTPBearer()

   async def verify_token(credentials = Depends(security)):
       token = credentials.credentials

       # Try JWT
       try:
           user = await supabase.auth.get_user(token)
           return user
       except:
           pass

       # Try API key
       user_id = await verify_api_key(token)
       if user_id:
           return {"id": user_id}

       raise HTTPException(401, "Invalid credentials")
   ```

3. **Create all endpoints** (see `docs/00_api_design.md` for full spec)
   ```python
   # Agents
   @app.post("/v1/agents", response_model=AgentResponse)
   @app.get("/v1/agents", response_model=List[AgentResponse])
   @app.get("/v1/agents/{id}", response_model=AgentResponse)
   @app.patch("/v1/agents/{id}", response_model=AgentResponse)
   @app.delete("/v1/agents/{id}")
   @app.post("/v1/agents/{id}/run", response_model=RunResponse)

   # Teams
   @app.post("/v1/teams", response_model=TeamResponse)
   @app.get("/v1/teams", response_model=List[TeamResponse])
   @app.post("/v1/teams/{id}/members", response_model=MemberResponse)

   # Marketplace
   @app.get("/v1/marketplace/templates", response_model=List[TemplateResponse])
   @app.post("/v1/marketplace/templates/{id}/purchase")

   # Webhooks
   @app.post("/v1/webhooks", response_model=WebhookResponse)
   @app.get("/v1/webhooks", response_model=List[WebhookResponse])

   # ... 40+ more endpoints
   ```

4. **Add rate limiting**
   ```python
   from fastapi import Request
   from redis import asyncio as aioredis

   async def rate_limit_middleware(request: Request, call_next):
       user_id = request.state.user["id"]
       tier = await get_user_tier(user_id)

       limits = {"free": 10, "pro": 100, "enterprise": 1000}

       if not await rate_limiter.check_limit(user_id, tier):
           raise HTTPException(429, "Rate limit exceeded")

       return await call_next(request)
   ```

5. **Implement webhooks**
   ```python
   async def trigger_webhook(user_id: str, event: str, data: dict):
       webhooks = await db.execute(
           "SELECT * FROM webhooks WHERE user_id = $1 AND $2 = ANY(events)",
           user_id, event
       )

       for webhook in webhooks:
           payload = {
               "event": event,
               "data": data,
               "timestamp": datetime.now().isoformat()
           }

           # Sign payload
           signature = hmac.new(
               webhook["secret"].encode(),
               json.dumps(payload).encode(),
               hashlib.sha256
           ).hexdigest()

           # Send
           async with httpx.AsyncClient() as client:
               await client.post(
                   webhook["url"],
                   json=payload,
                   headers={"X-Webhook-Signature": signature}
               )
   ```

6. **Generate API documentation**
   - Auto-generated from FastAPI (Swagger UI at `/docs`)
   - Write API guides for common use cases
   - Create Postman collection
   - Add code examples (Python, JavaScript, curl)

**Effort:** 2 weeks
**Blockers:** Requires all previous gaps (full platform must exist)
**Risk:** Low (FastAPI makes this straightforward)

**Business Impact:** Enables integrations with other tools (Zapier, Make, etc.), expanding use cases.

---

## Feature Gaps

### User-Facing Features

| Feature | Current | Target | Priority | Effort |
|---------|---------|--------|----------|--------|
| **Agent Creation** | CLI wizard | Visual web editor | P0 | 2 weeks |
| **Agent Execution** | CLI only | Web + API | P0 | 1 week |
| **Tool Selection** | Manual in spec | Drag-and-drop UI | P1 | 1 week |
| **Multi-Agent Teams** | Single agent only | Sequential/parallel workflows | P1 | 2 weeks |
| **Template Library** | None | Marketplace with 100+ templates | P2 | 2 weeks |
| **Cost Dashboard** | None | Real-time analytics | P0 | 1 week |
| **Collaboration** | Single-user | Team workspaces | P1 | 1 week |
| **Version Control** | None | Git-like versioning for agents | P2 | 1 week |
| **Debugging** | Print statements | Interactive debugger | P2 | 2 weeks |
| **Monitoring** | None | Logs, traces, metrics | P0 | 1 week |

### Developer Features

| Feature | Current | Target | Priority | Effort |
|---------|---------|--------|----------|--------|
| **REST API** | None | 50+ endpoints | P0 | 2 weeks |
| **API Keys** | None | Generate, rotate, revoke | P0 | 2 days |
| **Webhooks** | None | Event subscriptions | P1 | 3 days |
| **SDKs** | CLI only | Python, JS, Go SDKs | P2 | 4 weeks |
| **Rate Limiting** | None | Tier-based limits | P0 | 2 days |
| **API Docs** | None | OpenAPI spec + guides | P0 | 1 week |
| **Sandbox** | None | Test environment | P1 | 1 week |

### Admin Features

| Feature | Current | Target | Priority | Effort |
|---------|---------|--------|----------|--------|
| **User Management** | None | Admin dashboard | P0 | 1 week |
| **Usage Analytics** | None | Dashboards + reports | P0 | 1 week |
| **Cost Control** | None | Budget alerts, auto-cutoffs | P0 | 3 days |
| **Feature Flags** | None | Toggle features per tier | P1 | 2 days |
| **Audit Logs** | None | Complete activity history | P1 | 3 days |
| **Content Moderation** | None | Review queue for marketplace | P1 | 1 week |
| **Support Tools** | None | Impersonate user, debug issues | P2 | 3 days |

---

## Infrastructure Gaps

### Current Infrastructure
- **Compute:** Local machine only
- **Storage:** Local filesystem
- **Database:** None (files)
- **Caching:** None
- **Monitoring:** None
- **Deployment:** Manual (no CI/CD)

### Target Infrastructure

| Component | Current | Target | Priority | Cost/Month |
|-----------|---------|--------|----------|------------|
| **Compute** | Local | Cloud Run (1-100 instances) | P0 | $50-500 |
| **Database** | Files | Supabase PostgreSQL | P0 | $25-100 |
| **Caching** | None | Redis (Cloud Memorystore) | P1 | $10-50 |
| **Storage** | Local | Google Cloud Storage | P1 | $5-20 |
| **CDN** | None | Cloudflare | P1 | $0-20 |
| **Monitoring** | None | Google Cloud Monitoring + Sentry | P0 | $20-50 |
| **CI/CD** | None | GitHub Actions | P0 | $0 (free tier) |
| **DNS** | None | Cloudflare DNS | P1 | $0 |
| **Email** | None | SendGrid | P1 | $15 |
| **Total** | **$0** | **$125-755/mo** | - | - |

**Infrastructure Setup Tasks:**

1. **Google Cloud Project**
   - Create project
   - Enable APIs (Cloud Run, Cloud SQL, Cloud Storage)
   - Set up billing alerts
   - Configure IAM roles
   - **Effort:** 2 hours

2. **Supabase Project**
   - Create project
   - Run database migrations
   - Configure RLS policies
   - Set up authentication providers (Google, GitHub)
   - **Effort:** 4 hours

3. **Cloudflare**
   - Add domain
   - Configure DNS records
   - Enable CDN
   - Set up SSL certificates
   - **Effort:** 1 hour

4. **GitHub Actions CI/CD**
   - Create workflow files
   - Set up secrets
   - Configure deploy triggers
   - Add test automation
   - **Effort:** 4 hours

5. **Monitoring Setup**
   - Configure Sentry (error tracking)
   - Set up Google Cloud Monitoring (metrics)
   - Create alert rules
   - Set up log aggregation
   - **Effort:** 4 hours

**Total Infrastructure Setup:** 2-3 days

---

## Critical Path Analysis

### What Must Be Done First (Blocking Dependencies)

```
Phase 0: Repo Mapping (CURRENT)
    |
    v
Phase 1: LLM Abstraction ← MUST COME FIRST
    |
    v
Phase 2: Multi-LLM Routing ← Depends on Phase 1
    |
    +---> Phase 3: Modern Tools (parallel with Phase 2)
    |
    v
Phase 4: Brain Fart Checker ← Depends on Phases 2 & 3
    |
    v
Phase 5: OpenHands ← Depends on Phase 1
    |
    v
Phase 6: Cost Monitoring ← Depends on Phase 2
    |
    v
    [CORE ENGINE COMPLETE - Can launch Brain Fart Checker standalone]
    |
    v
Phase 9: Database + Multi-Tenancy ← MUST COME BEFORE PHASE 8
    |
    v
Phase 12: REST API ← Depends on Phase 9, MUST COME BEFORE PHASE 8
    |
    v
Phase 8: Web UI ← Depends on Phases 9 & 12
    |
    v
Phase 10: Billing ← Depends on Phases 8 & 9
    |
    v
Phase 11: Marketplace ← Depends on Phase 10
    |
    v
Phase 7: Multi-Agent Orchestration ← Can happen anytime after Phase 6
    |
    v
    [FULL PLATFORM COMPLETE]
```

### Critical Path Duration
- **Phase 0:** 8-10 hours (documentation)
- **Phase 1:** 2-3 days (LLM abstraction)
- **Phase 2:** 3-4 days (multi-LLM routing)
- **Phase 4:** 5-7 days (Brain Fart Checker)
- **Phase 9:** 2 weeks (database + multi-tenancy)
- **Phase 12:** 2 weeks (REST API)
- **Phase 8:** 4 weeks (web UI)
- **Phase 10:** 1 week (billing)
- **Phase 11:** 2 weeks (marketplace)

**Total Critical Path:** ~11 weeks

### Parallelizable Work
- Phase 3 (tools) can happen during Phase 2
- Phase 5 (OpenHands) can happen during Phase 4
- Phase 6 (cost monitoring) can happen during Phase 5
- Phase 7 (orchestration) can happen anytime after Phase 6

**Potential Time Savings:** 2 weeks if parallelized

---

## Effort Estimation

### By Phase

| Phase | Name | Effort | Complexity | Risk |
|-------|------|--------|------------|------|
| 0 | Repo Mapping | 8-10 hours | Low | Low |
| 1 | LLM Abstraction | 2-3 days | Low | Low |
| 2 | Multi-LLM Routing | 3-4 days | Medium | Medium |
| 3 | Modern Tools | 2-3 days | Low | Low |
| 4 | Brain Fart Checker | 5-7 days | Medium | Medium |
| 5 | OpenHands Integration | 2-3 days | Medium | High |
| 6 | Cost Monitoring | 1-2 days | Low | Low |
| 7 | Multi-Agent Orchestration | 2 weeks | High | Medium |
| 8 | Web UI | 4 weeks | High | Medium |
| 9 | Multi-Tenancy | 2 weeks | High | **High** |
| 10 | Billing | 1 week | Medium | Low |
| 11 | Marketplace | 2 weeks | Medium | High |
| 12 | REST API | 2 weeks | Medium | Low |

**Total Estimated Effort:** 13 weeks (65 working days)

### By Category

| Category | Tasks | Effort | % of Total |
|----------|-------|--------|------------|
| **Core Engine** | Phases 1-6 | 3 weeks | 23% |
| **Infrastructure** | Database, deployment, monitoring | 1 week | 8% |
| **Backend** | API, multi-tenancy, billing | 5 weeks | 38% |
| **Frontend** | Web UI, dashboard, marketplace | 4 weeks | 31% |

### Confidence Levels

| Phase | Confidence | Rationale |
|-------|-----------|-----------|
| 1-3 | **High** | Well-understood APIs, clear requirements |
| 4 | **Medium** | Prompt engineering can be unpredictable |
| 5 | **Low** | OpenHands output quality varies |
| 6-8 | **High** | Standard web development, proven tech |
| 9 | **Medium** | RLS policies are complex but documented |
| 10-12 | **High** | Standard integrations with good docs |

---

## Risk Assessment

### High-Risk Items

#### Risk 1: Multi-Tenancy Data Isolation (Phase 9)
**Impact:** Critical
**Probability:** Medium
**Consequence:** Data leaks, regulatory violations, loss of trust

**Mitigation:**
1. Extensive testing of RLS policies
2. Automated security audits
3. Penetration testing before launch
4. Regular compliance reviews
5. Data encryption at rest and in transit

**Contingency:**
- If RLS proves too complex, fall back to application-level filtering
- Hire security consultant for audit

---

#### Risk 2: LLM Cost Spiraling (Phase 2)
**Impact:** High
**Probability:** Medium
**Consequence:** Negative margins, forced to raise prices

**Mitigation:**
1. Strict budget limits per user/tier
2. Aggressive caching (80%+ hit rate target)
3. Local models for simple queries (Llama3)
4. Real-time cost monitoring with auto-cutoffs
5. Cost optimization feedback loop

**Contingency:**
- If costs exceed 50% of revenue, switch to more aggressive local model usage
- Implement "cost credits" system where users prepay

---

#### Risk 3: Marketplace Content Moderation (Phase 11)
**Impact:** High
**Probability:** High
**Consequence:** Malicious templates, legal liability, platform ban

**Mitigation:**
1. Automated code analysis (detect malicious patterns)
2. Manual review for all published templates
3. Community reporting system
4. Strict terms of service
5. Creator vetting (verified accounts only)
6. Template sandboxing (limited permissions)

**Contingency:**
- If moderation overhead is too high, limit marketplace to curated templates only
- Require $99 one-time fee to become verified creator

---

#### Risk 4: OpenHands Output Quality (Phase 5)
**Impact:** Medium
**Probability:** High
**Consequence:** Generated code doesn't work, user frustration

**Mitigation:**
1. Always generate tests alongside code
2. Run tests before returning code to user
3. Implement code review step (Claude validates)
4. Offer manual fallback ("Use OpenHands" toggle)
5. Clear messaging about beta status

**Contingency:**
- If quality is consistently poor, make OpenHands opt-in only
- Fall back to template-based generation

---

#### Risk 5: Migration from CLI to Web (Phase 8)
**Impact:** Medium
**Probability:** Medium
**Consequence:** Existing users don't adopt web UI, churn

**Mitigation:**
1. Maintain CLI parity (all features available in both)
2. Gradual migration path (import specs from files)
3. Clear value proposition for web (collaboration, marketplace)
4. Beta program with existing users
5. In-app migration wizard

**Contingency:**
- Keep CLI as first-class citizen indefinitely
- Offer "CLI Pro" tier for power users

---

### Medium-Risk Items

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Performance Degradation** | Medium | Medium | Load testing, auto-scaling, caching |
| **API Breaking Changes** | Low | High | Versioning, deprecation notices |
| **Stripe Integration Issues** | Medium | Low | Use well-tested libraries, test mode |
| **User Adoption** | High | Medium | Beta program, product-market fit validation |
| **Competitor Moves** | Medium | High | Focus on differentiators (Brain Fart Checker, cost optimization) |

---

## Prioritization Matrix

### Eisenhower Matrix (Urgency vs Importance)

```
High Importance, High Urgency (DO FIRST):
┌─────────────────────────────────────┐
│ - Phase 1: LLM Abstraction         │
│ - Phase 2: Multi-LLM Routing       │
│ - Phase 9: Multi-Tenancy           │
│ - Phase 12: REST API               │
└─────────────────────────────────────┘

High Importance, Low Urgency (SCHEDULE):
┌─────────────────────────────────────┐
│ - Phase 7: Multi-Agent Orchestration│
│ - Phase 11: Marketplace            │
│ - Phase 8: Web UI (after API)     │
└─────────────────────────────────────┘

Low Importance, High Urgency (DELEGATE):
┌─────────────────────────────────────┐
│ - Infrastructure setup             │
│ - Documentation                    │
│ - CLI improvements                 │
└─────────────────────────────────────┘

Low Importance, Low Urgency (ELIMINATE):
┌─────────────────────────────────────┐
│ - Advanced analytics               │
│ - Mobile app                       │
│ - White-labeling                   │
└─────────────────────────────────────┘
```

### Value vs Effort

```
High Value, Low Effort (QUICK WINS):
┌─────────────────────────────────────┐
│ - Phase 1: LLM Abstraction (3 days)│
│ - Phase 3: Modern Tools (3 days)   │
│ - Phase 6: Cost Monitoring (2 days)│
│ - CLI help improvements (1 day)    │
└─────────────────────────────────────┘

High Value, High Effort (BIG BETS):
┌─────────────────────────────────────┐
│ - Phase 8: Web UI (4 weeks)        │
│ - Phase 9: Multi-Tenancy (2 weeks) │
│ - Phase 11: Marketplace (2 weeks)  │
└─────────────────────────────────────┘

Low Value, Low Effort (FILL-INS):
┌─────────────────────────────────────┐
│ - Roadmap CLI command (1 hour)     │
│ - Additional tool integrations     │
│ - Documentation updates            │
└─────────────────────────────────────┘

Low Value, High Effort (AVOID):
┌─────────────────────────────────────┐
│ - Custom LLM fine-tuning           │
│ - Built-in IDE                     │
│ - Video generation agents          │
└─────────────────────────────────────┘
```

---

## Recommended Execution Order

### Phase 0 (Current): Documentation Week
**Duration:** 8-10 hours
**Goal:** Complete understanding of current state and platform vision

**Tasks:**
- ✅ Read entire codebase (156 files)
- ✅ Create `docs/00_repo_overview.md`
- ✅ Create `docs/00_platform_roadmap.md`
- ✅ Create `docs/00_database_schema.md`
- ✅ Create `docs/00_architecture_platform.md`
- ⏳ Create `docs/00_gap_analysis.md` (this document)
- 🔲 Create `docs/00_business_model.md`
- 🔲 Create `docs/00_api_design.md`
- 🔲 Create `docs/00_tech_stack.md`
- 🔲 Create `docs/00_competitive_analysis.md`

---

### Weeks 1-2: Core Engine Foundation
**Goal:** Build infrastructure for multi-LLM routing and cost tracking

**Week 1:**
- Phase 1: LLM Abstraction Layer (2-3 days)
- Phase 3: Modern Tools (2-3 days)

**Week 2:**
- Phase 2: Multi-LLM Routing (3-4 days)
- Phase 6: Cost Monitoring (1-2 days)

**Deliverable:** CLI with intelligent LLM routing and cost tracking

---

### Weeks 3-4: First Product Launch (Brain Fart Checker)
**Goal:** Launch standalone $99/mo product

**Week 3:**
- Phase 4: Brain Fart Checker implementation (5-7 days)

**Week 4:**
- Create landing page (2 days)
- Set up Stripe product (1 day)
- Beta testing with 10 users (2 days)

**Deliverable:** Brain Fart Checker live, first paying customers

**Target:** 10 paid users = $990/mo MRR

---

### Weeks 5-6: Infrastructure & Database
**Goal:** Set up production infrastructure

**Week 5:**
- Set up Google Cloud Project (1 day)
- Set up Supabase (1 day)
- Phase 9: Database schema + migrations (3 days)

**Week 6:**
- Phase 9: Multi-tenancy RLS policies (3 days)
- Infrastructure deployment (Cloud Run, Redis) (2 days)

**Deliverable:** Production database with multi-tenancy

---

### Weeks 7-8: REST API
**Goal:** Build API layer for web UI

**Week 7-8:**
- Phase 12: REST API implementation (10 days)
  - Authentication (2 days)
  - Core endpoints (4 days)
  - Rate limiting (1 day)
  - Webhooks (1 day)
  - Documentation (2 days)

**Deliverable:** Fully functional REST API

---

### Weeks 9-12: Web UI
**Goal:** Launch web application

**Week 9:**
- Next.js project setup (1 day)
- Authentication flow (2 days)
- Dashboard shell (2 days)

**Week 10:**
- Agent builder UI (3 days)
- Agent execution UI (2 days)

**Week 11:**
- Team management UI (2 days)
- Settings pages (1 day)
- Testing + bug fixes (2 days)

**Week 12:**
- Polish and refinements (3 days)
- Beta launch (invite-only) (2 days)

**Deliverable:** Web UI beta with 50 users

---

### Week 13: Billing & Marketplace
**Goal:** Enable monetization

**Week 13:**
- Phase 10: Stripe integration (3 days)
- Phase 11: Marketplace MVP (2 days)

**Deliverable:** Full platform ready for public launch

**Target:** 100 free users, 20 paid users = $980/mo MRR

---

## Success Criteria

### Phase 0 (Documentation) - Complete
- ✅ All 10 documentation files created
- ✅ Current state fully mapped
- ✅ Platform vision clearly defined
- ✅ All gaps identified with effort estimates

### Phases 1-6 (Core Engine) - Success Metrics
- ✅ LLM cost per request <$0.005 (avg)
- ✅ Agent response time <3s (simple queries)
- ✅ Brain Fart Checker accuracy >80% (validated by human review)
- ✅ 10 paying customers for Brain Fart Checker ($990/mo MRR)

### Phases 7-12 (Platform) - Success Metrics
- ✅ 1,000 registered users (free + paid)
- ✅ 100 paid subscriptions ($4,900/mo MRR)
- ✅ 99.9% API uptime
- ✅ <200ms API response time (p95)
- ✅ 50+ templates in marketplace
- ✅ <30% infrastructure cost as % of revenue

### Overall Platform Success (90 days)
- ✅ $10,000/mo MRR
- ✅ 10% free → paid conversion rate
- ✅ <5% monthly churn
- ✅ NPS score >40
- ✅ Product-market fit validated (10+ organic signups/day)

---

## Next Steps

1. **Complete Phase 0 Documentation** (3 more docs)
   - Business model
   - API design
   - Tech stack rationale
   - Competitive analysis

2. **Begin Phase 1** (LLM Abstraction Layer)
   - Install LiteLLM
   - Create router module
   - Update AgentFactory
   - Write tests

3. **Set up Infrastructure**
   - Create Google Cloud project
   - Create Supabase project
   - Set up GitHub Actions

4. **Launch Brain Fart Checker** (Week 4)
   - First revenue milestone
   - Validate pricing ($99/mo)
   - Gather user feedback

5. **Public Launch** (Week 13)
   - Full platform live
   - Product Hunt launch
   - Press outreach

---

**Document Status:** Phase 0 - Gap Analysis Complete
**Next Document:** `docs/00_business_model.md` - Pricing, revenue projections, market sizing

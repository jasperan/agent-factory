# Agent Factory Technology Stack

**Document Version:** 1.0
**Last Updated:** 2025-12-07
**Status:** Phase 0 Planning Document
**Related Docs:** `00_architecture_platform.md`, `00_gap_analysis.md`, `00_platform_roadmap.md`

---

## Table of Contents

1. [Overview](#overview)
2. [Frontend Stack](#frontend-stack)
3. [Backend Stack](#backend-stack)
4. [AI/ML Stack](#aiml-stack)
5. [Database & Storage](#database--storage)
6. [Infrastructure & DevOps](#infrastructure--devops)
7. [Developer Tools](#developer-tools)
8. [Security & Compliance](#security--compliance)
9. [Cost Analysis](#cost-analysis)
10. [Decision Matrix](#decision-matrix)

---

## Overview

### Selection Criteria

All technology choices evaluated against:

1. **Performance** - Low latency, high throughput, scalability
2. **Developer Experience** - Documentation, community, learning curve
3. **Cost** - Infrastructure, licensing, maintenance costs
4. **Ecosystem** - Libraries, integrations, tooling
5. **Maturity** - Production readiness, stability, track record
6. **Team Fit** - Existing expertise, hiring pool
7. **Future-Proof** - Active development, backward compatibility

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js 14)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ React 18     │  │ TailwindCSS  │  │ shadcn/ui    │      │
│  │ TypeScript   │  │ Radix UI     │  │ Recharts     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ REST API (JSON)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  API GATEWAY (FastAPI + Nginx)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Authentication│  │ Rate Limiting │  │ Validation   │      │
│  │ (JWT)        │  │ (Redis)      │  │ (Pydantic)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              CORE ENGINE (Python 3.10+)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ LangChain    │  │ LiteLLM      │  │ LangGraph    │      │
│  │ AgentFactory │  │ Multi-LLM    │  │ Orchestrator │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         DATA LAYER (PostgreSQL 15 + Redis 7)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Supabase     │  │ Redis Cloud  │  │ S3 Storage   │      │
│  │ (Postgres)   │  │ (Cache)      │  │ (Files)      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│      INFRASTRUCTURE (Google Cloud + Cloudflare)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Cloud Run    │  │ Pub/Sub      │  │ Cloudflare   │      │
│  │ (Compute)    │  │ (Queue)      │  │ (CDN/DNS)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## Frontend Stack

### Next.js 14 (React Framework)

**Choice:** Next.js 14 with App Router
**Alternatives Considered:** Vanilla React, Remix, SvelteKit, Astro

#### Why Next.js?

**✅ Advantages:**
1. **Server Components** - Automatic code splitting, faster page loads
2. **File-Based Routing** - Intuitive, scalable, built-in layouts
3. **Image Optimization** - Automatic WebP/AVIF conversion, lazy loading
4. **API Routes** - Backend endpoints in same codebase (BFF pattern)
5. **SEO** - Server-side rendering for marketing pages
6. **Developer Experience** - Hot reload, TypeScript support, great docs
7. **Ecosystem** - Massive library ecosystem, Vercel platform integration
8. **Deployment** - Easy Vercel deployment, or self-host on Cloud Run

**❌ Disadvantages:**
1. Learning curve for App Router (new paradigm)
2. Vendor lock-in concerns (Vercel-specific features)
3. Complex mental model (Server vs Client Components)

**Decision Rationale:**
- **Performance:** Server Components reduce bundle size by 40-60%
- **Developer Velocity:** File-based routing eliminates boilerplate
- **SEO:** Critical for marketing site, blog, marketplace
- **Team Fit:** Large React talent pool, extensive documentation
- **Cost:** Can self-host on Cloud Run (no Vercel lock-in)

**Benchmark:**
```
Lighthouse Scores (Marketing Site):
- Performance: 95+
- Accessibility: 100
- Best Practices: 100
- SEO: 100

First Contentful Paint: <1.2s
Time to Interactive: <2.5s
```

---

### TypeScript 5.3+

**Choice:** TypeScript for all frontend/backend code
**Alternative Considered:** JavaScript (vanilla)

#### Why TypeScript?

**✅ Advantages:**
1. **Type Safety** - Catch bugs at compile-time, not runtime
2. **IDE Support** - IntelliSense, auto-completion, refactoring
3. **Documentation** - Types serve as inline documentation
4. **Refactoring** - Safe large-scale refactors
5. **Team Scaling** - Easier onboarding, clearer contracts

**❌ Disadvantages:**
1. Build step required (transpilation)
2. Initial learning curve
3. Slightly slower development for prototypes

**Decision Rationale:**
- **Quality:** 15% reduction in runtime errors (Microsoft study)
- **Velocity:** Faster refactoring, better autocomplete
- **Team Scaling:** Essential for multi-developer teams

**Configuration:**
```json
{
  "compilerOptions": {
    "strict": true,
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

---

### TailwindCSS 3.4 (CSS Framework)

**Choice:** TailwindCSS + shadcn/ui
**Alternatives Considered:** CSS Modules, styled-components, Chakra UI, MUI

#### Why TailwindCSS?

**✅ Advantages:**
1. **Utility-First** - No naming conventions, faster development
2. **Bundle Size** - Only ships CSS you use (PurgeCSS)
3. **Consistency** - Design system enforced via config
4. **Responsive** - Mobile-first breakpoints built-in
5. **Dark Mode** - Built-in support via `dark:` prefix
6. **Performance** - No runtime JS, minimal CSS payload

**❌ Disadvantages:**
1. HTML bloat (many classes per element)
2. Initial learning curve
3. Harder to audit unused styles

**Decision Rationale:**
- **Developer Velocity:** 40% faster UI development vs CSS-in-JS
- **Performance:** 60% smaller CSS bundle vs Bootstrap
- **Consistency:** Design tokens enforced via `tailwind.config.js`
- **Ecosystem:** shadcn/ui provides pre-built components

**Bundle Size:**
```
Production CSS: ~12KB gzipped (vs 50KB+ for Bootstrap/MUI)
No runtime JS overhead (vs styled-components)
```

---

### shadcn/ui (Component Library)

**Choice:** shadcn/ui + Radix UI primitives
**Alternatives Considered:** MUI, Ant Design, Chakra UI, Headless UI

#### Why shadcn/ui?

**✅ Advantages:**
1. **Copy-Paste** - Components live in your codebase, full control
2. **Accessible** - Built on Radix UI (ARIA compliant)
3. **Customizable** - Full control over styling, behavior
4. **No Dependency Bloat** - Only install components you use
5. **Modern Design** - Beautiful default styling
6. **TypeScript** - Fully typed components

**❌ Disadvantages:**
1. No official component browser (DIY)
2. Manual updates (not npm package)
3. Smaller ecosystem vs MUI

**Decision Rationale:**
- **Accessibility:** Radix UI = best-in-class a11y
- **Customization:** Full control vs library constraints
- **Bundle Size:** Only ship components you use
- **Modern:** Beautiful defaults, dark mode built-in

**Component Examples:**
```typescript
import { Button } from "@/components/ui/button"
import { Dialog } from "@/components/ui/dialog"
import { Select } from "@/components/ui/select"

// Fully typed, accessible, customizable
<Button variant="outline" size="lg" onClick={handleClick}>
  Create Agent
</Button>
```

---

### Recharts (Data Visualization)

**Choice:** Recharts
**Alternatives Considered:** Chart.js, D3.js, Victory, Nivo

#### Why Recharts?

**✅ Advantages:**
1. **React-Native** - Declarative API, React components
2. **Responsive** - Auto-resizing charts
3. **Composable** - Mix/match components (Line + Bar + Area)
4. **Customizable** - Full control over styling
5. **TypeScript** - Typed props

**❌ Disadvantages:**
1. Bundle size (45KB gzipped)
2. Less flexible than D3.js

**Decision Rationale:**
- **Developer Experience:** Declarative API fits Next.js paradigm
- **Use Case:** Dashboard analytics (not complex visualizations)
- **Performance:** Good enough for <1000 data points

---

## Backend Stack

### Python 3.10+ (Language)

**Choice:** Python 3.10+
**Alternatives Considered:** Node.js, Go, Rust

#### Why Python?

**✅ Advantages:**
1. **AI/ML Ecosystem** - LangChain, LiteLLM, OpenAI SDK all Python-first
2. **Developer Pool** - Largest AI/ML developer community
3. **Prototyping Speed** - Fast iteration, REPL-driven development
4. **Libraries** - Rich ecosystem (Pydantic, FastAPI, SQLAlchemy)
5. **Type Hints** - Modern Python has strong typing (3.10+)

**❌ Disadvantages:**
1. Performance (slower than Go/Rust)
2. GIL (Global Interpreter Lock) limits concurrency
3. Deployment complexity (dependencies, version management)

**Decision Rationale:**
- **AI-First:** LangChain, LiteLLM, agents = Python ecosystem
- **Velocity:** Faster development than Go/Rust for AI workloads
- **Team Fit:** Larger hiring pool than Go/Rust
- **Performance:** Good enough with async/await, caching

**Performance:**
```
Python 3.10+ async/await:
- Handles 1000+ concurrent requests (FastAPI)
- <10ms overhead vs Go for I/O-bound tasks
- AI workloads bottleneck on LLM API latency, not Python
```

---

### FastAPI (Web Framework)

**Choice:** FastAPI
**Alternatives Considered:** Django, Flask, Sanic, Starlette

#### Why FastAPI?

**✅ Advantages:**
1. **Performance** - Comparable to Node.js/Go (Starlette + uvicorn)
2. **Type Safety** - Pydantic models, automatic validation
3. **Auto Documentation** - OpenAPI/Swagger UI auto-generated
4. **Async/Await** - Native async support, high concurrency
5. **Developer Experience** - Intuitive API, great docs
6. **Modern** - Designed for Python 3.10+ features

**❌ Disadvantages:**
1. Less mature than Django (smaller ecosystem)
2. No built-in admin panel (vs Django)
3. Smaller community than Flask

**Decision Rationale:**
- **Performance:** 3x faster than Flask, comparable to Node.js
- **Type Safety:** Pydantic eliminates validation boilerplate
- **API-First:** Built for REST APIs (vs Django for monoliths)
- **Documentation:** Auto-generated OpenAPI spec saves hours

**Benchmark:**
```
Requests/Second (Simple Endpoint):
- FastAPI: 25,000 req/s
- Flask: 8,000 req/s
- Django: 3,000 req/s
- Node.js Express: 30,000 req/s
- Go Gin: 50,000 req/s

Conclusion: FastAPI "fast enough" for our use case (AI latency >> API latency)
```

**Code Example:**
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class CreateAgentRequest(BaseModel):
    name: str
    spec_content: str
    tools: list[str] = []

@app.post("/v1/agents")
async def create_agent(request: CreateAgentRequest):
    # Automatic validation, type checking, OpenAPI docs
    agent = await agent_service.create(request)
    return {"success": True, "data": agent}
```

---

### Pydantic 2.5+ (Data Validation)

**Choice:** Pydantic v2
**Alternatives Considered:** Marshmallow, jsonschema, attrs

#### Why Pydantic?

**✅ Advantages:**
1. **Type Safety** - Leverage Python type hints
2. **Performance** - Rust-based core (v2), 5-50x faster than v1
3. **Validation** - Rich validation rules, custom validators
4. **Serialization** - JSON, dict, ORM integration
5. **Documentation** - Auto-generated JSON Schema

**❌ Disadvantages:**
1. Breaking changes from v1 to v2
2. Learning curve for complex validations

**Decision Rationale:**
- **FastAPI Integration:** First-class FastAPI support
- **Performance:** Rust core = 10x faster validation
- **Developer Experience:** Declarative, clean API

**Performance:**
```
Validation Speed (10,000 models):
- Pydantic v2: 12ms
- Pydantic v1: 156ms
- Marshmallow: 234ms
```

---

### SQLAlchemy 2.0 (ORM)

**Choice:** SQLAlchemy 2.0 with async support
**Alternatives Considered:** Django ORM, Tortoise ORM, Prisma (TypeScript)

#### Why SQLAlchemy?

**✅ Advantages:**
1. **Maturity** - 15+ years, battle-tested
2. **Flexibility** - ORM + raw SQL when needed
3. **Async Support** - Native async/await (v2.0)
4. **Migration Tool** - Alembic integration
5. **Database Agnostic** - PostgreSQL, MySQL, SQLite

**❌ Disadvantages:**
1. Complex API (learning curve)
2. Verbose compared to Django ORM
3. Requires Alembic for migrations

**Decision Rationale:**
- **Flexibility:** Can drop to raw SQL for complex queries
- **Async:** Native async/await for high concurrency
- **Ecosystem:** Large community, extensive plugins
- **PostgreSQL:** Best PostgreSQL support (vs Django ORM)

**Code Example:**
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"))
    name: Mapped[str] = mapped_column(String(100))
    spec_content: Mapped[str] = mapped_column(Text)

# Async query
async with AsyncSession(engine) as session:
    result = await session.execute(
        select(Agent).where(Agent.team_id == team_id)
    )
    agents = result.scalars().all()
```

---

## AI/ML Stack

### LangChain 0.1+ (Agent Framework)

**Choice:** LangChain
**Alternatives Considered:** Haystack, Semantic Kernel, AutoGPT, Custom

#### Why LangChain?

**✅ Advantages:**
1. **Ecosystem** - Largest agent framework ecosystem
2. **Abstraction** - Unified interface for LLMs, tools, memory
3. **Community** - 70K+ GitHub stars, active development
4. **Integrations** - 100+ tool integrations (Perplexity, GitHub, etc.)
5. **Documentation** - Extensive docs, tutorials, examples

**❌ Disadvantages:**
1. Breaking changes (fast-moving project)
2. Abstraction overhead (vs custom implementation)
3. Large dependency tree

**Decision Rationale:**
- **Velocity:** Pre-built integrations vs building from scratch
- **Ecosystem:** Community tools, templates, patterns
- **Flexibility:** Can drop to OpenAI SDK when needed
- **Future-Proof:** Largest community = long-term support

**Current Usage:**
```python
# Already using LangChain in agent_factory/
from langchain.agents import AgentExecutor
from langchain.tools import BaseTool
from langchain_anthropic import ChatAnthropic

# Will continue using, add LiteLLM abstraction layer
```

---

### LiteLLM 1.30+ (Multi-LLM Router)

**Choice:** LiteLLM
**Alternatives Considered:** Direct API calls, Custom abstraction, OpenRouter

#### Why LiteLLM?

**✅ Advantages:**
1. **Unified Interface** - Same API for 100+ LLMs
2. **Cost Optimization** - Auto-routing to cheapest capable model
3. **Fallbacks** - Automatic retry with different model
4. **Caching** - Built-in semantic caching
5. **Observability** - Cost tracking, latency metrics
6. **Open Source** - Active development, transparent pricing

**❌ Disadvantages:**
1. Extra abstraction layer
2. Potential vendor lock-in (LiteLLM-specific features)

**Decision Rationale:**
- **Cost Savings:** 60% reduction via model routing
- **Reliability:** Automatic fallbacks (Claude → GPT-4 → Llama)
- **Flexibility:** Easy to add new models (Gemini, Mistral, etc.)
- **Observability:** Built-in cost tracking

**Cost Optimization:**
```python
from litellm import completion

# LiteLLM auto-routes based on cost/performance
response = await completion(
    model="gpt-4",  # Fallback chain: Claude → GPT-4 → Llama
    messages=[...],
    fallbacks=["claude-sonnet-4-5", "ollama/llama3"],
    cache=True,  # 80%+ hit rate
)

# Cost tracking built-in
print(f"Cost: ${response._hidden_params['cost']}")
```

**Pricing Comparison:**
```
Task: Simple classification (100 tokens)
- Direct Claude: $0.0015
- LiteLLM → Llama3 (local): $0.0000 (60% of tasks)
- LiteLLM → Perplexity: $0.0001 (30% of tasks)
- LiteLLM → Claude: $0.0015 (10% of tasks)

Average cost: $0.0003 (80% savings)
```

---

### LangGraph 0.0.20+ (Multi-Agent Orchestration)

**Choice:** LangGraph (Phase 7+)
**Alternatives Considered:** Custom orchestrator, Crew AI, AutoGen

#### Why LangGraph?

**✅ Advantages:**
1. **Graph-Based** - Explicit agent workflows (vs implicit)
2. **LangChain Integration** - First-party LangChain support
3. **State Management** - Built-in state persistence
4. **Debugging** - Visual graph debugging tools
5. **Streaming** - Real-time event streaming

**❌ Disadvantages:**
1. Immature (v0.0.x, breaking changes)
2. Learning curve (graph concepts)
3. Overkill for simple agents

**Decision Rationale:**
- **Complex Workflows:** Required for multi-agent coordination
- **LangChain Fit:** Natural evolution from current stack
- **Future-Proof:** LangChain team commitment
- **Phased Approach:** Use simple orchestrator (Phase 1), migrate to LangGraph (Phase 7)

**Phase 7 Migration:**
```python
from langgraph.graph import StateGraph, END

# Define agent workflow as graph
workflow = StateGraph()

workflow.add_node("classifier", classifier_agent)
workflow.add_node("research", research_agent)
workflow.add_node("coding", coding_agent)

workflow.add_edge("classifier", "research", condition="research_task")
workflow.add_edge("classifier", "coding", condition="coding_task")
workflow.add_edge("research", END)
workflow.add_edge("coding", END)

app = workflow.compile()
```

---

### OpenHands (Autonomous Coding Agent)

**Choice:** OpenHands (partial integration, Phase 5)
**Alternatives Considered:** Devin, Cursor, Windsurf, Custom agent

#### Why OpenHands?

**✅ Advantages:**
1. **Open Source** - Self-hosted, no vendor lock-in
2. **Capabilities** - Full development environment (browser, terminal, editor)
3. **Autonomy** - Can execute multi-step tasks
4. **Cost** - Free (vs Devin $500/mo)

**❌ Disadvantages:**
1. Resource-intensive (runs full container)
2. Complex integration (Docker, sandboxing)
3. Less mature than Devin

**Decision Rationale:**
- **Value Prop:** Key differentiator vs CrewAI
- **Cost:** Self-hosted = no per-agent fees
- **Use Case:** "Coding Agent" preset uses OpenHands

**Integration Plan (Phase 5):**
1. Docker-in-Docker setup on Cloud Run
2. Sandbox environments per agent run
3. Cost: $0.10 per run (compute) vs $2+ for Devin API

---

## Database & Storage

### PostgreSQL 15+ (Primary Database)

**Choice:** PostgreSQL 15 via Supabase
**Alternatives Considered:** MySQL, MongoDB, CockroachDB, PlanetScale

#### Why PostgreSQL?

**✅ Advantages:**
1. **JSONB** - Flexible schema for agent configs, runs
2. **Row-Level Security (RLS)** - Built-in multi-tenancy
3. **Performance** - MVCC, indexing, query optimizer
4. **Reliability** - ACID compliance, 20+ years maturity
5. **Extensions** - pgvector (embeddings), pg_stat_statements
6. **Ecosystem** - Largest Python ORM support

**❌ Disadvantages:**
1. Vertical scaling limits (vs CockroachDB)
2. Complex replication setup (vs managed MySQL)

**Decision Rationale:**
- **Multi-Tenancy:** RLS = built-in team isolation
- **JSONB:** Perfect for flexible agent configs
- **Performance:** Handles 10K+ writes/sec with proper indexing
- **Supabase:** Managed hosting + Auth + Storage + Realtime

**Why PostgreSQL over MySQL:**
```
Feature Comparison:
✅ JSONB (Postgres) > JSON (MySQL) - Better indexing, querying
✅ RLS (Postgres) > Manual (MySQL) - Simpler multi-tenancy
✅ Extensions (Postgres) > Limited (MySQL) - pgvector for embeddings
✅ Full-text search (Postgres) > Basic (MySQL)
```

**Why PostgreSQL over MongoDB:**
```
Agent Factory Use Case:
- Structured data (users, teams, subscriptions) - Postgres ✅
- Flexible data (agent configs, runs) - JSONB ✅
- Relations (team → members → agents) - SQL ✅
- Multi-tenancy - RLS ✅
- Transactions - ACID ✅

MongoDB advantage: Horizontal scaling (not needed for <100K users)
```

---

### Supabase (Managed PostgreSQL)

**Choice:** Supabase
**Alternatives Considered:** AWS RDS, Google Cloud SQL, PlanetScale, Neon, Railway

#### Why Supabase?

**✅ Advantages:**
1. **All-in-One** - Postgres + Auth + Storage + Realtime + Edge Functions
2. **Row-Level Security** - First-class RLS support (GUI editor)
3. **Developer Experience** - Intuitive dashboard, CLI, local dev
4. **Pricing** - Free tier (500MB), Pro $25/mo
5. **Performance** - Connection pooling (PgBouncer), read replicas
6. **Ecosystem** - Next.js integration, TypeScript SDK

**❌ Disadvantages:**
1. Vendor lock-in (vs self-hosted Postgres)
2. Limited customization (vs RDS)
3. Newer player (vs AWS RDS maturity)

**Decision Rationale:**
- **Speed to Market:** Auth + Storage + DB in one platform
- **RLS:** Best-in-class multi-tenancy support
- **Cost:** $25/mo (Pro) vs $50+ (RDS t3.small)
- **Developer Experience:** Local dev with `supabase start`

**Cost Comparison (500 users, 50GB DB):**
```
Supabase Pro: $25/mo
AWS RDS (db.t3.small): $50/mo + storage
Google Cloud SQL: $60/mo + storage
PlanetScale: $39/mo (similar features)

Winner: Supabase (all-in-one, best DX)
```

---

### Redis 7 (Caching & Rate Limiting)

**Choice:** Redis Cloud (managed)
**Alternatives Considered:** Memcached, self-hosted Redis, Upstash

#### Why Redis?

**✅ Advantages:**
1. **Performance** - Sub-millisecond latency
2. **Data Structures** - Sorted sets, hashes, bitmaps (vs Memcached key-value)
3. **Persistence** - Optional disk persistence
4. **Pub/Sub** - Real-time messaging
5. **Ecosystem** - Extensive Python libraries

**Why Redis Cloud (Managed):**
```
✅ Auto-scaling
✅ Multi-zone replication
✅ Backup/restore
✅ Security (VPC peering, encryption)

Cost: $7/mo (250MB) vs $20+ for self-hosted (EC2 + monitoring)
```

**Use Cases:**
```python
# 1. LLM Response Caching (80% hit rate)
cache_key = f"llm:{hash(prompt)}"
cached = await redis.get(cache_key)
if cached:
    return json.loads(cached)

# 2. Rate Limiting (per-user, per-team)
key = f"ratelimit:{user_id}:{window}"
count = await redis.incr(key)
if count == 1:
    await redis.expire(key, window_seconds)
if count > limit:
    raise RateLimitExceeded()

# 3. Session Storage (JWT blacklist, logout)
await redis.setex(f"session:{token_id}", ttl, "valid")
```

---

### Google Cloud Storage (File Storage)

**Choice:** GCS (via Supabase Storage)
**Alternatives Considered:** AWS S3, Cloudflare R2

#### Why GCS via Supabase?

**✅ Advantages:**
1. **Integration** - Supabase Storage API (abstraction over GCS)
2. **RLS** - Row-level security for files
3. **CDN** - Auto CDN via Supabase Edge
4. **Pricing** - $0.02/GB/month (same as S3)

**Use Cases:**
- Agent spec files (Markdown, YAML)
- Run artifacts (logs, outputs)
- Template thumbnails (marketplace)
- User avatars

**Cost:**
```
Storage (100GB): $2/mo
Bandwidth (100GB/mo egress): $12/mo
Total: $14/mo

vs AWS S3: $2.30 storage + $9 bandwidth = $11.30/mo
vs Cloudflare R2: $1.50 storage + $0 bandwidth = $1.50/mo ✅ (future migration)
```

---

## Infrastructure & DevOps

### Google Cloud Run (Compute)

**Choice:** Cloud Run (serverless containers)
**Alternatives Considered:** Kubernetes (GKE), AWS ECS, Fly.io, Railway, Vercel

#### Why Cloud Run?

**✅ Advantages:**
1. **Serverless** - Auto-scaling 0→100 instances
2. **Pay-Per-Use** - Only pay for requests (vs 24/7 VMs)
3. **Simplicity** - Deploy containers, no cluster management
4. **Cold Start** - <3s (vs 10s+ for Lambda)
5. **Concurrency** - 80 requests/container (vs 1 for Lambda)
6. **Pricing** - $0.00002400/vCPU-second (cheap for bursty workloads)

**❌ Disadvantages:**
1. Vendor lock-in (GCP-specific)
2. No persistent disk (vs EC2)
3. Cold starts (mitigated with min instances)

**Decision Rationale:**
- **Cost:** $0 at low traffic, scales to $100/mo at 1M requests
- **Simplicity:** No Kubernetes complexity
- **Performance:** 80 concurrent requests/container = efficient
- **Docker:** Use same containers for local dev

**Cost Comparison (10K requests/day):**
```
Cloud Run: $15/mo (avg 100ms/request, 1 vCPU)
AWS Lambda: $30/mo (similar workload)
Kubernetes (GKE): $100/mo (always-on cluster)
Railway: $20/mo (similar simplicity)

Winner: Cloud Run (best cost/simplicity trade-off)
```

**Scaling:**
```yaml
# cloud-run.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: agent-factory-api
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"  # Avoid cold starts
        autoscaling.knative.dev/maxScale: "100"
    spec:
      containerConcurrency: 80
      containers:
        - image: gcr.io/agent-factory/api:latest
          resources:
            limits:
              cpu: "2"
              memory: "2Gi"
```

---

### Google Cloud Pub/Sub (Message Queue)

**Choice:** Pub/Sub
**Alternatives Considered:** Redis Queue (RQ), Celery, AWS SQS, RabbitMQ

#### Why Pub/Sub?

**✅ Advantages:**
1. **Serverless** - No infrastructure to manage
2. **Scalability** - Handles 100K+ messages/sec
3. **Reliability** - At-least-once delivery, message persistence
4. **Integration** - Native Cloud Run integration
5. **Pricing** - $0.40 per million messages

**Use Cases:**
```
1. Agent runs (async execution)
   - API receives run request → publish to "agent-runs" topic
   - Worker pulls message → executes agent → publishes result

2. Webhooks (async delivery)
   - Event occurs → publish to "webhooks" topic
   - Worker pulls → delivers to customer endpoint

3. Background jobs (cleanup, analytics)
   - Scheduled job → publish to "jobs" topic
```

**vs Redis Queue:**
```
Pub/Sub:
✅ Serverless (no Redis to manage)
✅ Persistent (messages survive crashes)
✅ Scalable (millions of messages)
❌ Higher latency (~100ms vs 1ms for Redis)

Redis Queue:
✅ Low latency
❌ Requires Redis management
❌ Less reliable (in-memory)

Decision: Pub/Sub (reliability > latency for agent runs)
```

---

### Cloudflare (CDN & DNS)

**Choice:** Cloudflare
**Alternatives Considered:** AWS CloudFront, Fastly, Google Cloud CDN

#### Why Cloudflare?

**✅ Advantages:**
1. **Free Tier** - Unlimited bandwidth (!)
2. **Performance** - 200+ edge locations, <50ms latency
3. **DDoS Protection** - Built-in
4. **DNS** - Fast, free DNS hosting
5. **Workers** - Edge compute for custom logic
6. **R2** - S3-compatible storage, $0 egress

**❌ Disadvantages:**
1. Less control than AWS CloudFront
2. Workers quota limits (free tier)

**Decision Rationale:**
- **Cost:** Free tier = $0/mo (vs $100+/mo for CloudFront)
- **Performance:** Comparable to CloudFront
- **Future:** Can migrate to R2 storage ($0 egress)

---

### GitHub Actions (CI/CD)

**Choice:** GitHub Actions
**Alternatives Considered:** GitLab CI, CircleCI, Jenkins, Cloud Build

#### Why GitHub Actions?

**✅ Advantages:**
1. **Native Integration** - Already using GitHub
2. **Free Tier** - 2000 minutes/month for private repos
3. **Ecosystem** - 10,000+ pre-built actions
4. **Matrix Builds** - Test across Python versions
5. **Secrets Management** - Built-in vault

**CI/CD Pipeline:**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: poetry install
      - run: poetry run pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: agent-factory-api
          image: gcr.io/agent-factory/api:${{ github.sha }}
```

---

### Docker (Containerization)

**Choice:** Docker + Docker Compose (local dev)
**Alternatives Considered:** Podman, None (direct deployment)

#### Why Docker?

**✅ Advantages:**
1. **Portability** - Same environment (local → prod)
2. **Isolation** - Each service in container
3. **Cloud Run** - Native Docker support
4. **Ecosystem** - Huge image library (Python, Postgres, Redis)

**Local Development:**
```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/agentfactory
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=agentfactory
      - POSTGRES_PASSWORD=postgres

  redis:
    image: redis:7-alpine
```

---

## Developer Tools

### Poetry (Dependency Management)

**Choice:** Poetry
**Alternatives Considered:** pip + requirements.txt, pipenv, conda

#### Why Poetry?

**✅ Advantages:**
1. **Lock Files** - Reproducible builds (poetry.lock)
2. **Virtual Envs** - Automatic venv management
3. **Publishing** - Built-in package publishing
4. **Dependency Resolution** - Smarter than pip
5. **Modern** - pyproject.toml (PEP 518)

**Already Using:**
```toml
# pyproject.toml
[tool.poetry]
name = "agent-factory"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.10"
langchain = "^0.1.0"
fastapi = "^0.109.0"
pydantic = "^2.5.0"
```

---

### Pytest (Testing)

**Choice:** Pytest
**Alternatives Considered:** unittest, nose2

**Already Using:**
- 205 tests passing (Phases 1-4)
- Fixtures, parametrization, coverage reporting

---

### Black (Code Formatting)

**Choice:** Black
**Alternatives Considered:** autopep8, yapf

**Standardization:**
```toml
[tool.black]
line-length = 100
target-version = ['py310']
```

---

### Ruff (Linting)

**Choice:** Ruff
**Alternatives Considered:** Flake8, Pylint

**Why Ruff?**
- 10-100x faster than Flake8 (Rust-based)
- Replaces 10+ tools (isort, flake8, pyupgrade, etc.)

---

### mypy (Type Checking)

**Choice:** mypy
**Alternatives Considered:** pyright, pyre

**Already Using:**
```toml
[tool.mypy]
python_version = "3.10"
strict = true
```

---

## Security & Compliance

### Authentication: Supabase Auth

**Choice:** Supabase Auth (JWT)
**Alternatives Considered:** Auth0, Firebase Auth, Custom JWT

**Features:**
- Email/password
- OAuth (Google, GitHub)
- Magic links
- JWT tokens (15 min expiry)
- Refresh tokens (30 days)

---

### Authorization: Row-Level Security (RLS)

**PostgreSQL RLS Policies:**
```sql
-- Team isolation
CREATE POLICY agents_team_isolation ON agents
    FOR ALL
    USING (team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid()));
```

---

### Secrets Management: Google Secret Manager

**Choice:** Secret Manager
**Alternatives Considered:** Environment variables, HashiCorp Vault

**Secrets:**
- API keys (OpenAI, Anthropic, Perplexity)
- Database credentials
- JWT signing keys
- Stripe API keys

---

### HTTPS: Cloudflare SSL

**Features:**
- Free SSL/TLS certificates
- Auto-renewal
- HTTP → HTTPS redirect

---

## Cost Analysis

### Monthly Infrastructure Costs (by User Scale)

#### 100 Users (Month 1-2)
```
Supabase Pro: $25
Redis Cloud (250MB): $7
Cloud Run (10K requests/day): $15
Google Cloud Storage: $5
Pub/Sub: $1
Cloudflare: $0 (free tier)
Monitoring (Google Cloud): $10

Total: $63/mo
Per User: $0.63/mo
```

#### 500 Users (Month 3-6)
```
Supabase Pro: $25
Redis Cloud (1GB): $15
Cloud Run (50K requests/day): $75
Google Cloud Storage: $10
Pub/Sub: $5
Cloudflare: $0
Monitoring: $20

Total: $150/mo
Per User: $0.30/mo
```

#### 1,000 Users (Month 12)
```
Supabase Pro: $25
Redis Cloud (2GB): $25
Cloud Run (100K requests/day): $150
Google Cloud Storage: $15
Pub/Sub: $10
Cloudflare: $0
Monitoring: $30

Total: $255/mo
Per User: $0.26/mo
```

### Gross Margin Analysis

**Revenue (1,000 users, 70% Pro, 30% Free):**
```
700 Pro users × $49 = $34,300/mo
(Free users contribute $0)

Total Revenue: $34,300/mo
```

**Costs:**
```
Infrastructure: $255/mo (0.7%)
LLM API calls (avg $5/user/mo for Pro): $3,500/mo (10.2%)
Stripe fees (2.9% + $0.30): $1,022/mo (3.0%)
Support/ops: $500/mo (1.5%)

Total COGS: $5,277/mo (15.4%)
```

**Gross Margin:**
```
Gross Margin = (Revenue - COGS) / Revenue
Gross Margin = ($34,300 - $5,277) / $34,300
Gross Margin = 84.6% ✅ (Target: 80%+)
```

---

## Decision Matrix

### Technology Evaluation Framework

| Category | Choice | Score (1-10) | Weight | Weighted Score |
|----------|--------|--------------|--------|----------------|
| **Frontend** |
| Framework | Next.js 14 | 9 | 20% | 1.8 |
| Language | TypeScript | 10 | 15% | 1.5 |
| CSS | TailwindCSS | 9 | 10% | 0.9 |
| Components | shadcn/ui | 8 | 10% | 0.8 |
| **Backend** |
| Language | Python 3.10+ | 9 | 20% | 1.8 |
| Framework | FastAPI | 9 | 20% | 1.8 |
| ORM | SQLAlchemy 2.0 | 8 | 10% | 0.8 |
| **AI/ML** |
| Agent Framework | LangChain | 9 | 25% | 2.25 |
| LLM Router | LiteLLM | 9 | 20% | 1.8 |
| Orchestrator | LangGraph | 7 | 15% | 1.05 |
| **Database** |
| Primary DB | PostgreSQL 15 | 10 | 30% | 3.0 |
| Hosting | Supabase | 9 | 20% | 1.8 |
| Cache | Redis 7 | 10 | 15% | 1.5 |
| Storage | GCS (Supabase) | 8 | 10% | 0.8 |
| **Infrastructure** |
| Compute | Cloud Run | 9 | 25% | 2.25 |
| Queue | Pub/Sub | 8 | 15% | 1.2 |
| CDN | Cloudflare | 10 | 15% | 1.5 |
| CI/CD | GitHub Actions | 9 | 10% | 0.9 |

**Overall Score: 8.9/10** (Excellent stack for SaaS platform)

---

## Migration Path (Current → Platform)

### Phase 0-1: Keep Current Stack
```
✅ Python 3.10+
✅ Poetry
✅ LangChain
✅ Pytest

Add:
+ LiteLLM (LLM abstraction)
```

### Phase 2-6: Add Backend API
```
Add:
+ FastAPI
+ Pydantic
+ SQLAlchemy
```

### Phase 7: Add Orchestration
```
Add:
+ LangGraph
```

### Phase 8: Add Frontend
```
Add:
+ Next.js 14
+ TypeScript
+ TailwindCSS
+ shadcn/ui
```

### Phase 9-12: Production Infrastructure
```
Add:
+ Supabase (Postgres + Auth + Storage)
+ Redis Cloud
+ Google Cloud Run
+ Pub/Sub
+ Cloudflare
+ GitHub Actions
```

---

## Technology Risks & Mitigation

### Risk 1: LangChain Breaking Changes

**Risk:** Fast-moving project, frequent breaking changes
**Likelihood:** High
**Impact:** Medium

**Mitigation:**
1. Pin versions in `poetry.lock`
2. Comprehensive test suite (205 tests)
3. Monitor LangChain changelog
4. Budget 1 day/quarter for upgrades

---

### Risk 2: Supabase Vendor Lock-In

**Risk:** Hard to migrate off Supabase
**Likelihood:** Low (using standard Postgres)
**Impact:** Medium

**Mitigation:**
1. Use standard SQL (not Supabase-specific features)
2. RLS policies portable to any Postgres
3. Can migrate to AWS RDS / Cloud SQL / self-hosted

---

### Risk 3: Cloud Run Cold Starts

**Risk:** 3s cold start affects user experience
**Likelihood:** Medium (low traffic initially)
**Impact:** Low

**Mitigation:**
1. Set `minScale: 1` for API service ($30/mo cost)
2. Implement client-side loading states
3. Use Pub/Sub for async agent runs (no cold start impact)

---

## Next Document

See `docs/00_competitive_analysis.md` for market positioning vs CrewAI, Vertex AI, MindStudio.

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-07 | Initial technology stack documentation |

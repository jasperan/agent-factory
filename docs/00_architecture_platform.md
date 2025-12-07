# Agent Factory Platform - System Architecture

**Version:** 1.0
**Last Updated:** 2025-12-07
**Status:** Phase 0 Documentation

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Layers](#architecture-layers)
3. [Component Details](#component-details)
4. [Data Flow Examples](#data-flow-examples)
5. [Security Model](#security-model)
6. [Scalability Design](#scalability-design)
7. [Monitoring & Observability](#monitoring--observability)
8. [Deployment Architecture](#deployment-architecture)
9. [Migration Path](#migration-path)

---

## Overview

### Platform Vision

Agent Factory is a **multi-tenant SaaS platform** that enables users to build, deploy, and monetize AI agents through declarative specifications. The platform transforms from a CLI-only tool for developers into a full-stack web application accessible to non-technical users.

### Core Differentiators

1. **Constitutional Programming** - Spec-first approach where specifications are eternal, code is ephemeral
2. **Multi-LLM Routing** - Cost-optimized routing (Llama3 → Perplexity → Claude)
3. **Brain Fart Checker** - AI-powered idea validator with kill criteria
4. **OpenHands Integration** - Autonomous coding agent for spec-to-code generation
5. **Team-Based Multi-Tenancy** - Enterprise-ready with RLS isolation
6. **Community Marketplace** - Template sharing with revenue splits

### Target Users

- **Tier 1:** Solo founders, indie hackers (Free/Pro tiers)
- **Tier 2:** Small dev teams (Pro tier)
- **Tier 3:** Enterprise organizations (Enterprise tier)

### Success Metrics

- **MRR Target:** $10K in 90 days, $25K in 6 months
- **User Growth:** 1K free users, 100 paid users by Month 3
- **Performance:** <200ms API response time (p95), 99.9% uptime
- **Cost Efficiency:** LLM cost <30% of revenue per user

---

## Architecture Layers

The platform follows a **5-layer architecture** designed for scalability, maintainability, and cost efficiency.

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: Frontend (Next.js 14, React 18, TailwindCSS)    │
│  - Web UI, Visual Spec Editor, Dashboard                   │
└─────────────────────────────────────────────────────────────┘
                           ↓ HTTPS (TLS 1.3)
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: API Gateway (FastAPI, Nginx, Rate Limiting)     │
│  - Auth Middleware, API Keys, Rate Limits, Webhooks        │
└─────────────────────────────────────────────────────────────┘
                           ↓ Internal HTTP
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: Core Engine (LangGraph, LiteLLM, Orchestrator)  │
│  - Agent Runtime, Multi-LLM Routing, Tool Execution        │
└─────────────────────────────────────────────────────────────┘
                           ↓ PostgreSQL Protocol
┌─────────────────────────────────────────────────────────────┐
│  LAYER 4: Data Layer (PostgreSQL 15, Redis 7, Supabase)   │
│  - Multi-Tenant DB, Caching, Session Store                 │
└─────────────────────────────────────────────────────────────┘
                           ↓ Cloud APIs
┌─────────────────────────────────────────────────────────────┐
│  LAYER 5: Infrastructure (GCP Cloud Run, Storage, CDN)    │
│  - Containerization, Auto-Scaling, Object Storage          │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Details

### Layer 1: Frontend (Phase 8)

**Technology Stack:**
- **Framework:** Next.js 14 (App Router, Server Components)
- **UI Library:** React 18 with TypeScript
- **Styling:** TailwindCSS 3.4 + shadcn/ui components
- **State Management:** Zustand (lightweight, <1KB)
- **Form Handling:** React Hook Form + Zod validation
- **API Client:** TanStack Query (React Query v5)
- **Deployment:** Vercel Edge Functions

**Key Components:**

1. **Agent Builder UI** (`/app/agents/new`)
   ```typescript
   // Visual spec editor with live preview
   interface AgentBuilderProps {
     onSpecChange: (spec: AgentSpec) => void;
     initialSpec?: AgentSpec;
   }

   // Features:
   // - Monaco editor for spec editing
   // - Live validation with error highlighting
   // - Tool selector (drag-and-drop interface)
   // - Invariant builder (visual rule creator)
   // - Template gallery integration
   ```

2. **Dashboard** (`/app/dashboard`)
   ```typescript
   // Real-time agent monitoring
   interface DashboardProps {
     teamId: string;
     dateRange: DateRange;
   }

   // Metrics displayed:
   // - Total runs (last 30 days)
   // - Cost breakdown by LLM
   // - Success/failure rates
   // - Average response time
   // - Quota usage (runs, tokens)
   ```

3. **Marketplace** (`/app/marketplace`)
   ```typescript
   // Community template browsing
   interface MarketplaceProps {
     category?: string;
     sortBy: 'popular' | 'recent' | 'rating';
   }

   // Features:
   // - Template preview
   // - One-click deploy
   // - Rating and reviews
   // - Purchase flow (for paid templates)
   ```

**Authentication Flow:**
```typescript
// Supabase Auth integration
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

// Server-side auth check
export async function getSession() {
  const { data: { session } } = await supabase.auth.getSession();
  return session;
}

// Protected route wrapper
export async function withAuth(handler: Function) {
  const session = await getSession();
  if (!session) {
    return redirect('/login');
  }
  return handler(session);
}
```

**Performance Targets:**
- First Contentful Paint (FCP): <1.2s
- Time to Interactive (TTI): <2.5s
- Lighthouse Score: >90
- Bundle Size: <200KB (gzip)

---

### Layer 2: API Gateway (Phase 12)

**Technology Stack:**
- **Framework:** FastAPI 0.104+ (async/await)
- **Reverse Proxy:** Nginx (load balancing, SSL termination)
- **Rate Limiting:** Redis-based (sliding window algorithm)
- **Auth:** Supabase JWT validation + API keys
- **Documentation:** OpenAPI 3.1 (auto-generated)

**Core Endpoints:**

```python
# agent_factory/api/main.py

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from typing import List, Optional

app = FastAPI(
    title="Agent Factory API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://agentfactory.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth middleware
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify Supabase JWT or API key"""
    token = credentials.credentials

    # Try JWT first
    try:
        user = await supabase.auth.get_user(token)
        return user
    except:
        pass

    # Fallback to API key
    api_key = await db.execute(
        "SELECT user_id FROM api_keys WHERE key = $1 AND active = true",
        token
    )
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"id": api_key["user_id"]}

# Agent endpoints
@app.post("/v1/agents", response_model=AgentResponse)
async def create_agent(
    spec: AgentSpec,
    user = Depends(verify_token)
):
    """Create new agent from specification"""

    # Validate spec
    validation_result = await spec_validator.validate(spec)
    if not validation_result.valid:
        raise HTTPException(
            status_code=400,
            detail={"errors": validation_result.errors}
        )

    # Create agent
    agent = await agent_factory.create_from_spec(
        spec=spec,
        user_id=user["id"]
    )

    return agent

@app.post("/v1/agents/{agent_id}/run", response_model=RunResponse)
async def run_agent(
    agent_id: str,
    input: AgentInput,
    user = Depends(verify_token)
):
    """Execute agent with input"""

    # Check quota
    quota = await check_user_quota(user["id"])
    if quota.exceeded:
        raise HTTPException(
            status_code=429,
            detail="Monthly run quota exceeded"
        )

    # Run agent
    result = await agent_executor.run(
        agent_id=agent_id,
        input=input.query,
        stream=input.stream
    )

    return result

@app.get("/v1/agents", response_model=List[AgentResponse])
async def list_agents(
    team_id: Optional[str] = None,
    user = Depends(verify_token)
):
    """List user's agents"""

    agents = await db.execute(
        """
        SELECT * FROM agents
        WHERE team_id IN (
            SELECT team_id FROM team_members
            WHERE user_id = $1
        )
        ORDER BY created_at DESC
        """,
        user["id"]
    )

    return agents

# Marketplace endpoints
@app.get("/v1/marketplace/templates", response_model=List[TemplateResponse])
async def list_templates(
    category: Optional[str] = None,
    sort_by: str = "popular"
):
    """Browse marketplace templates"""

    query = """
        SELECT
            t.*,
            AVG(r.rating) as avg_rating,
            COUNT(DISTINCT d.id) as download_count
        FROM agent_templates t
        LEFT JOIN template_ratings r ON r.template_id = t.id
        LEFT JOIN agent_deployments d ON d.template_id = t.id
        WHERE t.published = true
    """

    if category:
        query += f" AND t.category = '{category}'"

    query += f" GROUP BY t.id ORDER BY {sort_by} DESC"

    templates = await db.execute(query)
    return templates

# Webhooks
@app.post("/v1/webhooks")
async def create_webhook(
    webhook: WebhookCreate,
    user = Depends(verify_token)
):
    """Register webhook endpoint"""

    # Validate URL is reachable
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook.url,
                json={"type": "webhook.test"}
            )
            if response.status_code != 200:
                raise HTTPException(400, "Webhook URL validation failed")
    except:
        raise HTTPException(400, "Webhook URL unreachable")

    # Store webhook
    result = await db.execute(
        """
        INSERT INTO webhooks (user_id, url, events, secret)
        VALUES ($1, $2, $3, $4)
        RETURNING *
        """,
        user["id"], webhook.url, webhook.events, generate_secret()
    )

    return result
```

**Rate Limiting Strategy:**

```python
# agent_factory/api/middleware/rate_limit.py

from fastapi import Request, HTTPException
from redis import asyncio as aioredis
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

        # Tier-based limits (requests per minute)
        self.limits = {
            "free": 10,
            "pro": 100,
            "enterprise": 1000
        }

    async def check_limit(self, user_id: str, tier: str) -> bool:
        """Sliding window rate limit"""

        now = datetime.now()
        window_start = now - timedelta(minutes=1)

        # Redis sorted set: score = timestamp, value = request_id
        key = f"rate_limit:{user_id}"

        # Remove old requests
        await self.redis.zremrangebyscore(
            key,
            0,
            window_start.timestamp()
        )

        # Count requests in window
        count = await self.redis.zcard(key)

        if count >= self.limits[tier]:
            return False

        # Add current request
        await self.redis.zadd(
            key,
            {str(now.timestamp()): now.timestamp()}
        )

        # Set expiry
        await self.redis.expire(key, 60)

        return True

# Middleware
async def rate_limit_middleware(request: Request, call_next):
    user = request.state.user
    tier = await get_user_tier(user["id"])

    if not await rate_limiter.check_limit(user["id"], tier):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": "60"}
        )

    response = await call_next(request)
    return response
```

**Performance Targets:**
- API Response Time (p95): <200ms
- API Response Time (p99): <500ms
- Throughput: 1000 req/sec (horizontal scaling)
- Error Rate: <0.1%

---

### Layer 3: Core Engine (Phases 1-7)

**Technology Stack:**
- **Orchestration:** LangGraph (multi-agent workflows)
- **LLM Abstraction:** LiteLLM (unified interface)
- **Agent Runtime:** LangChain 0.1+ (agent executors)
- **Tools:** Custom + LangChain Community Tools
- **Validation:** Pydantic 2.5+ (response schemas)

**Architecture:**

```python
# agent_factory/core/llm_router.py

from litellm import completion
from typing import Optional, Dict, Any
import logging

class LLMRouter:
    """Cost-optimized multi-LLM routing"""

    def __init__(self):
        self.models = {
            "local": {
                "model": "ollama/llama3",
                "cost_per_1k": 0.0,
                "speed": "fast",
                "use_for": ["simple_queries", "classification"]
            },
            "perplexity": {
                "model": "perplexity/llama-3.1-sonar-small-128k-online",
                "cost_per_1k": 0.001,
                "speed": "medium",
                "use_for": ["research", "fact_checking"]
            },
            "claude": {
                "model": "anthropic/claude-sonnet-4-5",
                "cost_per_1k": 0.015,
                "speed": "slow",
                "use_for": ["complex_reasoning", "code_generation"]
            }
        }

        self.fallback_chain = ["local", "perplexity", "claude"]

    async def route(
        self,
        prompt: str,
        task_type: str,
        max_cost: Optional[float] = None
    ) -> Dict[str, Any]:
        """Route to cheapest capable model"""

        # Determine preferred model
        preferred = self._select_model(task_type, max_cost)

        # Try preferred model
        try:
            response = await completion(
                model=self.models[preferred]["model"],
                messages=[{"role": "user", "content": prompt}],
                timeout=30
            )

            return {
                "response": response.choices[0].message.content,
                "model": preferred,
                "cost": self._calculate_cost(response, preferred),
                "tokens": response.usage.total_tokens
            }

        except Exception as e:
            logging.warning(f"Model {preferred} failed: {e}")

            # Fallback to next model
            return await self._fallback(prompt, preferred)

    def _select_model(self, task_type: str, max_cost: Optional[float]) -> str:
        """Select best model for task"""

        # Filter by task type
        candidates = [
            name for name, config in self.models.items()
            if task_type in config["use_for"]
        ]

        # Filter by cost
        if max_cost:
            candidates = [
                name for name in candidates
                if self.models[name]["cost_per_1k"] <= max_cost
            ]

        # Return cheapest
        return min(
            candidates,
            key=lambda x: self.models[x]["cost_per_1k"]
        )

    async def _fallback(self, prompt: str, failed_model: str):
        """Try fallback models"""

        # Get next model in chain
        idx = self.fallback_chain.index(failed_model)

        for model_name in self.fallback_chain[idx + 1:]:
            try:
                return await self.route(
                    prompt,
                    task_type="complex_reasoning",  # Use safest
                    max_cost=None  # No cost limit on fallback
                )
            except:
                continue

        raise Exception("All LLM models failed")
```

**Multi-Agent Orchestration:**

```python
# agent_factory/core/orchestrator_v2.py

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
import operator

class AgentState(TypedDict):
    """State shared across agents"""
    messages: Annotated[Sequence[str], operator.add]
    next: str
    context: Dict[str, Any]

class AgentOrchestrator:
    """LangGraph-based multi-agent orchestration"""

    def __init__(self):
        self.graph = StateGraph(AgentState)
        self.agents = {}

    def register_agent(self, name: str, agent: AgentExecutor, routing_keywords: List[str]):
        """Register agent with routing keywords"""

        self.agents[name] = {
            "executor": agent,
            "keywords": routing_keywords
        }

        # Add node to graph
        self.graph.add_node(name, self._create_agent_node(agent))

    def _create_agent_node(self, agent: AgentExecutor):
        """Create LangGraph node for agent"""

        async def node_function(state: AgentState):
            """Execute agent and update state"""

            # Get latest message
            user_input = state["messages"][-1]

            # Run agent
            result = await agent.ainvoke({"input": user_input})

            # Update state
            return {
                "messages": [result["output"]],
                "context": {
                    **state["context"],
                    "last_agent": agent.name,
                    "cost": result.get("cost", 0)
                }
            }

        return node_function

    def build(self, routing_logic: str = "keyword"):
        """Build orchestration graph"""

        # Add routing node
        self.graph.add_node("router", self._router_node)

        # Set entry point
        self.graph.set_entry_point("router")

        # Add edges from router to agents
        for agent_name in self.agents.keys():
            self.graph.add_edge("router", agent_name)
            self.graph.add_edge(agent_name, END)

        # Compile graph
        self.app = self.graph.compile()

    async def _router_node(self, state: AgentState):
        """Route to appropriate agent"""

        user_input = state["messages"][-1].lower()

        # Keyword matching
        for agent_name, config in self.agents.items():
            if any(kw in user_input for kw in config["keywords"]):
                return {"next": agent_name}

        # Default to first agent
        return {"next": list(self.agents.keys())[0]}

    async def run(self, user_input: str) -> Dict[str, Any]:
        """Execute orchestration"""

        result = await self.app.ainvoke({
            "messages": [user_input],
            "context": {}
        })

        return {
            "output": result["messages"][-1],
            "agent_used": result["context"]["last_agent"],
            "total_cost": result["context"]["cost"]
        }
```

**Brain Fart Checker (Phase 4):**

```python
# agent_factory/tools/brain_fart_checker.py

from pydantic import BaseModel, Field
from typing import List, Dict
import asyncio

class IdeaEvaluation(BaseModel):
    """Structured output from Brain Fart Checker"""

    novelty_score: float = Field(ge=0, le=100, description="Uniqueness (0-100)")
    market_size_score: float = Field(ge=0, le=100, description="TAM potential")
    competition_score: float = Field(ge=0, le=100, description="Competitive intensity (lower is better)")
    execution_difficulty: float = Field(ge=0, le=100, description="Build complexity")
    estimated_mrr: float = Field(ge=0, description="Realistic MRR at 6 months")
    competitor_count: int = Field(ge=0, description="Direct competitors")

    verdict: str = Field(description="BUILD, ITERATE, or KILL")
    reasoning: str = Field(description="Explanation of verdict")
    next_steps: List[str] = Field(description="Actionable next steps")

class BrainFartChecker:
    """AI-powered idea validator"""

    KILL_CRITERIA = {
        "novelty_score": 60,      # Must be >60
        "estimated_mrr": 2000,    # Must be >$2K
        "competitor_count": 20    # Must be <20
    }

    async def evaluate(self, idea: str) -> IdeaEvaluation:
        """Multi-agent idea evaluation"""

        # Agent 1: Market research (Perplexity)
        market_data = await self._research_market(idea)

        # Agent 2: Competitive analysis (Perplexity)
        competitors = await self._analyze_competitors(idea)

        # Agent 3: Technical feasibility (Claude)
        feasibility = await self._assess_feasibility(idea)

        # Agent 4: Revenue projection (Claude)
        revenue = await self._project_revenue(idea, market_data)

        # Synthesize results
        evaluation = await self._synthesize(
            idea, market_data, competitors, feasibility, revenue
        )

        # Apply kill criteria
        if evaluation.novelty_score < self.KILL_CRITERIA["novelty_score"]:
            evaluation.verdict = "KILL"
            evaluation.reasoning = f"Novelty too low ({evaluation.novelty_score}). Market is saturated."

        elif evaluation.estimated_mrr < self.KILL_CRITERIA["estimated_mrr"]:
            evaluation.verdict = "KILL"
            evaluation.reasoning = f"MRR potential too low (${evaluation.estimated_mrr}). Not viable business."

        elif evaluation.competitor_count > self.KILL_CRITERIA["competitor_count"]:
            evaluation.verdict = "KILL"
            evaluation.reasoning = f"Too many competitors ({evaluation.competitor_count}). Hard to differentiate."

        return evaluation

    async def _research_market(self, idea: str) -> Dict:
        """Research market using Perplexity"""

        prompt = f"""
        Research the market for this idea: {idea}

        Provide:
        1. Total addressable market (TAM) size
        2. Current market trends
        3. Customer pain points
        4. Pricing benchmarks
        """

        response = await llm_router.route(
            prompt,
            task_type="research"
        )

        return self._parse_market_data(response["response"])

    async def _synthesize(self, idea, market, competitors, feasibility, revenue):
        """Synthesize all data into final evaluation"""

        prompt = f"""
        Evaluate this startup idea and provide structured output:

        Idea: {idea}
        Market Data: {market}
        Competitors: {competitors}
        Feasibility: {feasibility}
        Revenue Projection: {revenue}

        Return JSON matching IdeaEvaluation schema.
        """

        response = await llm_router.route(
            prompt,
            task_type="complex_reasoning"
        )

        return IdeaEvaluation.parse_raw(response["response"])
```

**Performance Targets:**
- Agent Response Time (simple): <2s
- Agent Response Time (complex): <10s
- Tool Execution: <500ms per tool
- LLM Router Overhead: <50ms

---

### Layer 4: Data Layer (Phase 9)

**Technology Stack:**
- **Primary Database:** PostgreSQL 15+ (Supabase managed)
- **Caching:** Redis 7+ (Cloud Memorystore)
- **Session Store:** Redis (with TTL)
- **Object Storage:** Google Cloud Storage (agent specs, logs)
- **Search:** PostgreSQL Full-Text Search (pg_trgm extension)

**Connection Pooling:**

```python
# agent_factory/db/pool.py

from asyncpg import create_pool
from typing import Optional
import os

class DatabasePool:
    """Async PostgreSQL connection pool"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Initialize connection pool"""

        self.pool = await create_pool(
            host=os.getenv("DB_HOST"),
            port=5432,
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),

            # Pool configuration
            min_size=10,
            max_size=100,
            command_timeout=60,

            # SSL for production
            ssl="require" if os.getenv("ENV") == "production" else None
        )

    async def execute(self, query: str, *args):
        """Execute query"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def set_user_context(self, user_id: str):
        """Set RLS context"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "SET app.current_user_id = $1",
                user_id
            )

db = DatabasePool()
```

**Caching Strategy:**

```python
# agent_factory/db/cache.py

from redis import asyncio as aioredis
from typing import Optional, Any
import json
import hashlib

class CacheManager:
    """Redis-based caching for expensive operations"""

    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

        # Cache TTLs (seconds)
        self.ttls = {
            "agent_spec": 3600,        # 1 hour
            "llm_response": 1800,       # 30 minutes
            "marketplace_templates": 600, # 10 minutes
            "user_quota": 60            # 1 minute
        }

    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """Get cached value"""

        full_key = f"{namespace}:{key}"
        value = await self.redis.get(full_key)

        if value:
            return json.loads(value)

        return None

    async def set(
        self,
        key: str,
        value: Any,
        namespace: str = "default",
        ttl: Optional[int] = None
    ):
        """Set cached value"""

        full_key = f"{namespace}:{key}"
        ttl = ttl or self.ttls.get(namespace, 300)

        await self.redis.setex(
            full_key,
            ttl,
            json.dumps(value)
        )

    async def invalidate(self, pattern: str):
        """Invalidate cache by pattern"""

        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

    def cache_key(self, *args) -> str:
        """Generate cache key from arguments"""

        content = ":".join(str(arg) for arg in args)
        return hashlib.md5(content.encode()).hexdigest()

# Usage example
async def get_agent_spec(agent_id: str) -> Dict:
    """Get agent spec with caching"""

    # Check cache
    cache_key = cache.cache_key("agent_spec", agent_id)
    cached = await cache.get(cache_key, namespace="agent_spec")

    if cached:
        return cached

    # Query database
    spec = await db.execute(
        "SELECT * FROM agents WHERE id = $1",
        agent_id
    )

    # Cache result
    await cache.set(cache_key, spec, namespace="agent_spec")

    return spec
```

**Database Migrations:**

```python
# migrations/001_initial_schema.sql

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    plan_tier plan_tier DEFAULT 'free',
    monthly_runs_quota INTEGER DEFAULT 100,
    monthly_runs_used INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for full-text search
CREATE INDEX users_email_trgm_idx ON users USING gin (email gin_trgm_ops);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
```

**Performance Targets:**
- Query Response Time (indexed): <10ms
- Query Response Time (complex joins): <50ms
- Cache Hit Rate: >80%
- Connection Pool Utilization: <70%

---

### Layer 5: Infrastructure (All Phases)

**Technology Stack:**
- **Container Orchestration:** Google Cloud Run (serverless containers)
- **CI/CD:** GitHub Actions
- **Monitoring:** Google Cloud Monitoring + Sentry
- **CDN:** Cloudflare (for static assets)
- **DNS:** Cloudflare DNS
- **SSL:** Let's Encrypt (auto-renewal via Cloudflare)

**Deployment Architecture:**

```yaml
# cloudrun.yaml

apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: agent-factory-api
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "100"
        autoscaling.knative.dev/target: "80"
    spec:
      containers:
      - image: gcr.io/agent-factory/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: url
        resources:
          limits:
            memory: 2Gi
            cpu: "2"
          requests:
            memory: 512Mi
            cpu: "0.5"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

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
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install

      - name: Run tests
        run: poetry run pytest --cov

      - name: Type check
        run: poetry run mypy agent_factory/

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: |
          docker build -t gcr.io/agent-factory/api:${{ github.sha }} .
          docker tag gcr.io/agent-factory/api:${{ github.sha }} gcr.io/agent-factory/api:latest

      - name: Push to GCR
        run: |
          echo ${{ secrets.GCP_SA_KEY }} | docker login -u _json_key --password-stdin https://gcr.io
          docker push gcr.io/agent-factory/api:${{ github.sha }}
          docker push gcr.io/agent-factory/api:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy agent-factory-api \
            --image gcr.io/agent-factory/api:${{ github.sha }} \
            --platform managed \
            --region us-central1 \
            --allow-unauthenticated \
            --set-env-vars "ENV=production"
```

**Dockerfile:**

```dockerfile
# Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application
COPY agent_factory/ ./agent_factory/

# Create non-root user
RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "agent_factory.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Performance Targets:**
- Cold Start Time: <3s
- Deployment Time: <5 minutes
- Auto-scaling: 0-100 instances
- Cost per Request: <$0.001

---

## Data Flow Examples

### Example 1: Create and Run Agent (End-to-End)

```
USER (Web UI)
    |
    | POST /v1/agents
    | {
    |   "name": "Market Research Agent",
    |   "spec": "...",
    |   "tools": ["perplexity_search", "wikipedia"]
    | }
    |
    v
API GATEWAY (FastAPI)
    |
    | 1. Verify JWT token (Supabase)
    | 2. Check rate limit (Redis)
    | 3. Validate request schema (Pydantic)
    |
    v
CORE ENGINE (Agent Factory)
    |
    | 4. Validate spec format
    | 5. Create AgentExecutor
    | 6. Store in database (PostgreSQL)
    |
    v
DATABASE (PostgreSQL)
    |
    | INSERT INTO agents (team_id, spec, tools, ...)
    | VALUES (...) RETURNING id
    |
    v
RESPONSE
    |
    | {
    |   "id": "agent_abc123",
    |   "status": "ready",
    |   "created_at": "2025-12-07T10:00:00Z"
    | }
    |
    v
USER (Web UI)
    |
    | POST /v1/agents/agent_abc123/run
    | {
    |   "query": "What are the top 3 AI trends in 2025?"
    | }
    |
    v
API GATEWAY
    |
    | 1. Verify token
    | 2. Check quota (Redis cache)
    |
    v
CORE ENGINE
    |
    | 3. Load agent from DB (with cache)
    | 4. Route to LLM (LiteLLM)
    |    - Try local Llama3 first ($0)
    |    - Fallback to Perplexity ($0.001)
    | 5. Execute tools (Perplexity search)
    | 6. Track cost and tokens
    |
    v
DATABASE
    |
    | INSERT INTO agent_runs (agent_id, input, output, cost, tokens)
    | VALUES (...)
    |
    | UPDATE users
    | SET monthly_runs_used = monthly_runs_used + 1
    | WHERE id = ...
    |
    v
RESPONSE (Streaming)
    |
    | {
    |   "output": "Based on recent research...",
    |   "cost": 0.0015,
    |   "tokens": 450,
    |   "execution_time": 3.2
    | }
```

### Example 2: Marketplace Template Purchase

```
USER (Marketplace UI)
    |
    | POST /v1/marketplace/templates/tmpl_xyz/purchase
    |
    v
API GATEWAY
    |
    | 1. Verify token
    | 2. Check if already purchased
    |
    v
BILLING (Stripe)
    |
    | 3. Create payment intent
    | 4. Charge customer ($19)
    |
    v
DATABASE
    |
    | BEGIN TRANSACTION;
    |
    | INSERT INTO template_purchases (user_id, template_id, amount)
    | VALUES (...);
    |
    | UPDATE agent_templates
    | SET purchase_count = purchase_count + 1
    | WHERE id = 'tmpl_xyz';
    |
    | -- Revenue sharing (70% creator, 30% platform)
    | INSERT INTO revenue_shares (creator_id, amount, template_id)
    | VALUES (creator_id, 13.30, 'tmpl_xyz');
    |
    | COMMIT;
    |
    v
CACHE
    |
    | INVALIDATE marketplace_templates:*
    |
    v
WEBHOOK (Creator Notification)
    |
    | POST https://creator.com/webhook
    | {
    |   "type": "template.purchased",
    |   "template_id": "tmpl_xyz",
    |   "revenue": 13.30
    | }
    |
    v
RESPONSE
    |
    | {
    |   "template": {...},
    |   "purchase_id": "purch_123",
    |   "receipt_url": "https://..."
    | }
```

---

## Security Model

### Authentication

**Supabase Auth Integration:**

```typescript
// Frontend (Next.js)
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

// Sign up
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'secure_password_123'
});

// Sign in
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'secure_password_123'
});

// OAuth (Google, GitHub)
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'google'
});
```

**API Key Management:**

```python
# agent_factory/api/auth.py

import secrets
import hashlib

def generate_api_key() -> tuple[str, str]:
    """Generate API key and hash"""

    # Generate random key (32 bytes = 256 bits)
    key = secrets.token_urlsafe(32)

    # Hash for storage (SHA-256)
    key_hash = hashlib.sha256(key.encode()).hexdigest()

    return f"agf_{key}", key_hash

async def create_api_key(user_id: str, name: str) -> str:
    """Create new API key for user"""

    key, key_hash = generate_api_key()

    await db.execute(
        """
        INSERT INTO api_keys (user_id, name, key_hash, active)
        VALUES ($1, $2, $3, true)
        """,
        user_id, name, key_hash
    )

    # Return key ONCE (never stored in plaintext)
    return key

async def verify_api_key(key: str) -> Optional[str]:
    """Verify API key and return user_id"""

    key_hash = hashlib.sha256(key.encode()).hexdigest()

    result = await db.execute(
        """
        SELECT user_id FROM api_keys
        WHERE key_hash = $1 AND active = true
        """,
        key_hash
    )

    if result:
        # Update last_used
        await db.execute(
            "UPDATE api_keys SET last_used = NOW() WHERE key_hash = $1",
            key_hash
        )

        return result[0]["user_id"]

    return None
```

### Authorization (Row-Level Security)

**RLS Policies:**

```sql
-- Enable RLS on all tables
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;

-- Helper function: Get current user's teams
CREATE OR REPLACE FUNCTION current_user_teams()
RETURNS SETOF UUID
LANGUAGE SQL STABLE
AS $$
    SELECT team_id
    FROM team_members
    WHERE user_id = current_setting('app.current_user_id')::uuid;
$$;

-- Policy: Users can only see agents from their teams
CREATE POLICY agents_team_isolation ON agents
    FOR ALL
    USING (team_id IN (SELECT current_user_teams()));

-- Policy: Users can only see runs from their agents
CREATE POLICY agent_runs_isolation ON agent_runs
    FOR ALL
    USING (
        agent_id IN (
            SELECT id FROM agents
            WHERE team_id IN (SELECT current_user_teams())
        )
    );

-- Policy: Team owners can manage team members
CREATE POLICY team_members_owner_only ON team_members
    FOR ALL
    USING (
        team_id IN (
            SELECT id FROM teams
            WHERE owner_id = current_setting('app.current_user_id')::uuid
        )
    );
```

**Usage in Application:**

```python
# Set user context before queries
await db.set_user_context(user_id)

# All subsequent queries automatically filtered by RLS
agents = await db.execute("SELECT * FROM agents")
# Returns only agents from user's teams
```

### Secrets Management

**Environment Variables:**

```bash
# .env.production (never committed)

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...  # Server-side only

# LLM Providers
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
PERPLEXITY_API_KEY=pplx-...

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Sentry
SENTRY_DSN=https://xxx@sentry.io/xxx
```

**Google Secret Manager:**

```python
# agent_factory/config/secrets.py

from google.cloud import secretmanager

class SecretManager:
    """Fetch secrets from Google Secret Manager"""

    def __init__(self, project_id: str):
        self.client = secretmanager.SecretManagerServiceClient()
        self.project_id = project_id

    def get_secret(self, secret_name: str) -> str:
        """Get latest version of secret"""

        name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
        response = self.client.access_secret_version(request={"name": name})

        return response.payload.data.decode("UTF-8")

# Usage
secrets = SecretManager(project_id="agent-factory-prod")
db_password = secrets.get_secret("database-password")
```

### Compliance

**GDPR Compliance:**

```python
# agent_factory/api/gdpr.py

async def export_user_data(user_id: str) -> Dict:
    """Export all user data (GDPR right to access)"""

    data = {
        "user": await db.execute("SELECT * FROM users WHERE id = $1", user_id),
        "agents": await db.execute("SELECT * FROM agents WHERE team_id IN (SELECT current_user_teams())"),
        "runs": await db.execute("SELECT * FROM agent_runs WHERE ..."),
        "api_keys": await db.execute("SELECT name, created_at FROM api_keys WHERE user_id = $1", user_id)
    }

    return data

async def delete_user_data(user_id: str):
    """Delete all user data (GDPR right to erasure)"""

    # Soft delete (retain for legal compliance)
    await db.execute(
        """
        UPDATE users
        SET
            email = 'deleted@example.com',
            deleted_at = NOW(),
            data_retention_until = NOW() + INTERVAL '30 days'
        WHERE id = $1
        """,
        user_id
    )

    # Hard delete after 30 days (cron job)
```

---

## Scalability Design

### Horizontal Scaling

**Auto-Scaling Configuration:**

```yaml
# cloudrun.yaml (continued)

autoscaling:
  minReplicas: 1
  maxReplicas: 100
  targetCPUUtilizationPercentage: 80
  targetMemoryUtilizationPercentage: 70

  # Scale based on request rate
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
```

**Load Balancing:**

```
                    [Cloudflare CDN]
                           |
                     [Cloud Load Balancer]
                           |
        +------------------+------------------+
        |                  |                  |
   [Instance 1]      [Instance 2]      [Instance N]
   us-central1       us-central1       us-central1
        |                  |                  |
        +------------------+------------------+
                           |
                   [PostgreSQL Primary]
                           |
                   [Read Replicas x3]
```

### Database Scaling

**Read Replicas:**

```python
# agent_factory/db/router.py

class DatabaseRouter:
    """Route queries to primary or replicas"""

    def __init__(self):
        self.primary = create_pool(os.getenv("DB_PRIMARY_URL"))
        self.replicas = [
            create_pool(url)
            for url in os.getenv("DB_REPLICA_URLS").split(",")
        ]
        self.replica_index = 0

    async def execute(self, query: str, *args, readonly: bool = True):
        """Route to appropriate database"""

        if readonly:
            # Round-robin across replicas
            pool = self.replicas[self.replica_index]
            self.replica_index = (self.replica_index + 1) % len(self.replicas)
        else:
            # Write to primary
            pool = self.primary

        async with pool.acquire() as conn:
            return await conn.fetch(query, *args)

# Usage
agents = await db.execute(
    "SELECT * FROM agents WHERE team_id = $1",
    team_id,
    readonly=True  # Route to replica
)
```

**Connection Pooling:**

- **Primary:** 100 max connections
- **Per Replica:** 50 max connections
- **Total Capacity:** 100 + (50 × 3) = 250 concurrent connections

### Caching Strategy

**Multi-Level Cache:**

```
[Application Memory]  (100MB, 1s TTL)
        |
        v (miss)
    [Redis]  (10GB, 60s-3600s TTL)
        |
        v (miss)
  [PostgreSQL]
```

**Cache Warming:**

```python
# agent_factory/cache/warmer.py

async def warm_cache():
    """Pre-populate frequently accessed data"""

    # Popular marketplace templates
    templates = await db.execute(
        """
        SELECT * FROM agent_templates
        WHERE published = true
        ORDER BY download_count DESC
        LIMIT 100
        """
    )

    for template in templates:
        await cache.set(
            f"template:{template['id']}",
            template,
            namespace="marketplace_templates"
        )

    # Active user quotas
    active_users = await db.execute(
        """
        SELECT id, monthly_runs_used, monthly_runs_quota
        FROM users
        WHERE last_active > NOW() - INTERVAL '1 day'
        """
    )

    for user in active_users:
        await cache.set(
            f"quota:{user['id']}",
            {"used": user["monthly_runs_used"], "quota": user["monthly_runs_quota"]},
            namespace="user_quota"
        )
```

### Cost Optimization

**LLM Cost Targets:**

```python
# Tier-based LLM routing

ROUTING_RULES = {
    "free": {
        "max_cost_per_request": 0.001,  # Prefer local/Perplexity
        "models": ["ollama/llama3", "perplexity/sonar"]
    },
    "pro": {
        "max_cost_per_request": 0.01,   # Allow Claude for complex queries
        "models": ["ollama/llama3", "perplexity/sonar", "anthropic/claude-sonnet"]
    },
    "enterprise": {
        "max_cost_per_request": None,   # No limit
        "models": ["ollama/llama3", "perplexity/sonar", "anthropic/claude-sonnet", "anthropic/claude-opus"]
    }
}
```

**Infrastructure Cost Projections:**

| Component | Free Tier (100 users) | Pro Tier (1000 users) | Enterprise Tier |
|-----------|----------------------|----------------------|----------------|
| Cloud Run | $50/mo | $500/mo | $2000/mo |
| PostgreSQL | $25/mo | $100/mo | $400/mo |
| Redis | $10/mo | $50/mo | $200/mo |
| Storage | $5/mo | $20/mo | $100/mo |
| **Total** | **$90/mo** | **$670/mo** | **$2700/mo** |

**Target Margins:**
- Infrastructure: 20% of revenue
- LLM Costs: 30% of revenue
- **Gross Margin Target:** 50%

---

## Monitoring & Observability

### Metrics Collection

**Custom Metrics:**

```python
# agent_factory/monitoring/metrics.py

from prometheus_client import Counter, Histogram, Gauge
import time

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# Agent metrics
agent_runs_total = Counter(
    'agent_runs_total',
    'Total agent runs',
    ['agent_id', 'status']
)

agent_run_duration = Histogram(
    'agent_run_duration_seconds',
    'Agent run duration',
    ['agent_id']
)

agent_run_cost = Histogram(
    'agent_run_cost_usd',
    'Agent run cost',
    ['agent_id', 'llm_provider']
)

# System metrics
active_users = Gauge(
    'active_users',
    'Currently active users'
)

database_connections = Gauge(
    'database_connections',
    'Active database connections'
)

# Middleware
async def metrics_middleware(request: Request, call_next):
    """Collect request metrics"""

    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    http_request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response
```

### Logging

**Structured Logging:**

```python
# agent_factory/logging/logger.py

import logging
import json
from datetime import datetime

class StructuredLogger:
    """JSON structured logging for Google Cloud Logging"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        handler.setFormatter(self.JsonFormatter())
        self.logger.addHandler(handler)

    class JsonFormatter(logging.Formatter):
        """Format logs as JSON"""

        def format(self, record):
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "severity": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }

            # Add extra fields
            if hasattr(record, "user_id"):
                log_data["user_id"] = record.user_id
            if hasattr(record, "agent_id"):
                log_data["agent_id"] = record.agent_id
            if hasattr(record, "request_id"):
                log_data["request_id"] = record.request_id

            return json.dumps(log_data)

    def info(self, message: str, **kwargs):
        """Log info with extra fields"""
        self.logger.info(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        """Log error with extra fields"""
        self.logger.error(message, extra=kwargs)

# Usage
logger = StructuredLogger(__name__)

logger.info(
    "Agent run completed",
    user_id="user_123",
    agent_id="agent_abc",
    duration=3.2,
    cost=0.0015
)
```

### Alerting

**Alert Rules:**

```yaml
# alerts.yaml

groups:
- name: agent_factory_alerts
  interval: 60s
  rules:

  # Error rate alert
  - alert: HighErrorRate
    expr: |
      rate(http_requests_total{status=~"5.."}[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value | humanizePercentage }}"

  # Response time alert
  - alert: SlowResponseTime
    expr: |
      histogram_quantile(0.95,
        rate(http_request_duration_seconds_bucket[5m])
      ) > 1.0
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "API response time degraded"
      description: "p95 latency is {{ $value }}s"

  # Database alert
  - alert: HighDatabaseConnections
    expr: |
      database_connections > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Database connection pool near capacity"

  # Cost alert
  - alert: HighLLMCost
    expr: |
      sum(rate(agent_run_cost_usd[1h])) > 10
    for: 30m
    labels:
      severity: critical
    annotations:
      summary: "LLM costs exceeding budget"
      description: "Hourly cost is ${{ $value }}"
```

### Tracing

**OpenTelemetry Integration:**

```python
# agent_factory/tracing/tracer.py

from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Initialize tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Add Cloud Trace exporter
cloud_trace_exporter = CloudTraceSpanExporter()
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(cloud_trace_exporter)
)

# Usage
async def run_agent(agent_id: str, input: str):
    """Run agent with tracing"""

    with tracer.start_as_current_span("run_agent") as span:
        span.set_attribute("agent_id", agent_id)
        span.set_attribute("input_length", len(input))

        # Load agent
        with tracer.start_as_current_span("load_agent"):
            agent = await load_agent(agent_id)

        # Route to LLM
        with tracer.start_as_current_span("llm_routing") as llm_span:
            response = await llm_router.route(input, "research")
            llm_span.set_attribute("model", response["model"])
            llm_span.set_attribute("cost", response["cost"])

        # Execute tools
        with tracer.start_as_current_span("tool_execution"):
            result = await agent.execute_tools(response)

        span.set_attribute("output_length", len(result))

        return result
```

---

## Deployment Architecture

### Production Environment

```
┌─────────────────────────────────────────────────────────────┐
│                         CLOUDFLARE                          │
│  - CDN (static assets)                                      │
│  - DDoS protection                                          │
│  - SSL/TLS termination                                      │
└─────────────────────────────────────────────────────────────┘
                           |
                           v
┌─────────────────────────────────────────────────────────────┐
│                  GOOGLE CLOUD LOAD BALANCER                 │
│  - Health checks                                            │
│  - SSL certificates                                         │
│  - URL routing                                              │
└─────────────────────────────────────────────────────────────┘
                           |
        +------------------+------------------+
        |                                     |
        v                                     v
┌──────────────────┐              ┌──────────────────┐
│   CLOUD RUN      │              │   CLOUD RUN      │
│   (Frontend)     │              │   (API)          │
│                  │              │                  │
│   Next.js 14    │              │   FastAPI        │
│   us-central1   │              │   us-central1    │
│   Min: 1        │              │   Min: 1         │
│   Max: 50       │              │   Max: 100       │
└──────────────────┘              └──────────────────┘
                                           |
                                           v
                              ┌──────────────────────┐
                              │   SUPABASE           │
                              │                      │
                              │   PostgreSQL 15      │
                              │   + Auth             │
                              │   + Storage          │
                              │   us-central1        │
                              └──────────────────────┘
                                           |
                                           v
                              ┌──────────────────────┐
                              │   REDIS              │
                              │                      │
                              │   Cloud Memorystore  │
                              │   10GB               │
                              │   us-central1        │
                              └──────────────────────┘
```

### Staging Environment

```
┌─────────────────────────────────────────────────────────────┐
│                    staging.agentfactory.com                 │
└─────────────────────────────────────────────────────────────┘
                           |
                           v
                  [Cloud Run - Staging]
                           |
                           v
               [Supabase - Staging Project]
                           |
                           v
                  [Redis - Staging Instance]
```

**Environment Separation:**
- Separate GCP projects (prod vs staging)
- Separate Supabase projects
- Separate Stripe accounts (test mode vs live)
- Same codebase, different configs

---

## Migration Path

### Phase-by-Phase Migration

**Current State (Phase 0):**
- CLI-only tool
- Local Python execution
- Single-user
- No database (file-based specs)

**Phase 1-6 (Core Engine):**
- Add LLM abstraction layer
- Add multi-LLM routing
- Add modern tools (Perplexity, OpenHands)
- Launch Brain Fart Checker ($99/mo standalone product)
- Still CLI-based, but with cloud LLM APIs

**Phase 7-9 (Platform Foundation):**
- Deploy PostgreSQL database
- Implement RLS for multi-tenancy
- Build REST API (FastAPI)
- Deploy to Cloud Run
- **First web users (invite-only beta)**

**Phase 10-12 (Full Platform):**
- Launch web UI (Next.js)
- Add billing (Stripe)
- Launch marketplace
- **Public launch**

### Database Migration Strategy

**Step 1: Dual-Write (Phase 9)**
```python
# Write to both file and database
async def create_agent(spec):
    # Old: Write to file
    with open(f"specs/{spec.name}.md", "w") as f:
        f.write(spec.content)

    # New: Write to database
    await db.execute(
        "INSERT INTO agents (name, spec_content) VALUES ($1, $2)",
        spec.name, spec.content
    )
```

**Step 2: Backfill Existing Data**
```python
# One-time migration script
async def migrate_specs_to_db():
    for file in glob.glob("specs/*.md"):
        with open(file) as f:
            content = f.read()

        name = Path(file).stem

        await db.execute(
            "INSERT INTO agents (name, spec_content, migrated_from_file) VALUES ($1, $2, true)",
            name, content
        )
```

**Step 3: Read from Database (Phase 10)**
```python
# Switch to database-first
async def get_agent(name):
    return await db.execute(
        "SELECT * FROM agents WHERE name = $1",
        name
    )
```

**Step 4: Deprecate File-Based Storage (Phase 12)**
- Remove file I/O code
- Keep files as backup only

### API Versioning Strategy

```python
# v1: Initial launch
@app.get("/v1/agents")
async def list_agents_v1():
    return await db.execute("SELECT id, name, created_at FROM agents")

# v2: Add filtering (backward compatible)
@app.get("/v2/agents")
async def list_agents_v2(category: Optional[str] = None):
    query = "SELECT id, name, created_at, category FROM agents"
    if category:
        query += f" WHERE category = '{category}'"
    return await db.execute(query)

# Maintain both versions for 6 months
```

---

## Summary

This architecture transforms Agent Factory from a **CLI developer tool** into a **production-ready SaaS platform** capable of serving thousands of users.

### Key Design Principles

1. **Scalability First** - Horizontal scaling via Cloud Run, read replicas, caching
2. **Security by Default** - RLS, encrypted secrets, API keys, rate limiting
3. **Cost Optimization** - Multi-LLM routing, caching, connection pooling
4. **Observability** - Structured logging, metrics, tracing, alerting
5. **Developer Experience** - Clean APIs, comprehensive docs, versioning

### Technology Decisions Rationale

| Technology | Why Chosen | Alternatives Considered |
|------------|-----------|------------------------|
| **Next.js 14** | Best-in-class React framework, Vercel deployment | Remix, SvelteKit |
| **FastAPI** | Modern async Python, auto-docs, fast | Django, Flask |
| **Supabase** | Managed PostgreSQL + Auth + Storage | AWS RDS, PlanetScale |
| **PostgreSQL 15** | JSONB support, RLS, proven scale | MongoDB, MySQL |
| **Redis** | Battle-tested caching, sub-ms latency | Memcached, Valkey |
| **Cloud Run** | Serverless containers, zero to scale | GKE, ECS |
| **LiteLLM** | Unified LLM API, cost tracking | Direct APIs |

### Performance Targets Summary

| Metric | Target | Current (CLI) |
|--------|--------|---------------|
| API Response Time (p95) | <200ms | N/A |
| Agent Run Time (simple) | <2s | ~3s |
| Frontend FCP | <1.2s | N/A |
| Database Query (indexed) | <10ms | N/A |
| Uptime | 99.9% | N/A |
| Cost per User (Pro tier) | <$5/mo | ~$0 |

### Next Steps

1. **Complete Phase 0 Documentation** (this file + 6 more docs)
2. **Begin Phase 1** - LLM Abstraction Layer implementation
3. **Deploy Staging Environment** - Set up GCP project, Supabase
4. **Implement CI/CD** - GitHub Actions pipeline
5. **Launch Beta** - Invite-only testing (target: 50 users)

---

**Document Status:** Phase 0 - Architecture Design Complete
**Next Document:** `docs/00_gap_analysis.md` - Map current state to platform vision

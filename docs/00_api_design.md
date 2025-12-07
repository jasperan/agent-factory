# Agent Factory REST API Design

**Document Version:** 1.0
**Last Updated:** 2025-12-07
**Status:** Phase 0 Planning Document
**Related Docs:** `00_architecture_platform.md`, `00_database_schema.md`, `00_business_model.md`

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [API Conventions](#api-conventions)
4. [Core Endpoints](#core-endpoints)
5. [Marketplace Endpoints](#marketplace-endpoints)
6. [Billing Endpoints](#billing-endpoints)
7. [Admin Endpoints](#admin-endpoints)
8. [Webhook Endpoints](#webhook-endpoints)
9. [Rate Limiting](#rate-limiting)
10. [Error Handling](#error-handling)
11. [OpenAPI Specification](#openapi-specification)

---

## Overview

### API Base URL

```
Production:  https://api.agentfactory.dev/v1
Staging:     https://api-staging.agentfactory.dev/v1
Development: http://localhost:8000/v1
```

### Design Principles

1. **RESTful** - Standard HTTP methods (GET, POST, PUT, PATCH, DELETE)
2. **JSON-first** - All requests/responses use `application/json`
3. **Versioned** - `/v1` prefix, breaking changes = new version
4. **Predictable** - Consistent naming, error formats, response structure
5. **Developer-friendly** - Clear error messages, comprehensive docs
6. **Secure** - JWT authentication, API key support, rate limiting
7. **Observable** - Request IDs, detailed logging, metrics

### Response Format (Standard)

All successful responses follow this structure:

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2025-12-07T10:30:00Z",
    "version": "v1"
  }
}
```

All error responses follow this structure:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {
      "field": "agent.name",
      "issue": "Name must be between 3 and 50 characters"
    }
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2025-12-07T10:30:00Z",
    "version": "v1"
  }
}
```

---

## Authentication & Authorization

### Authentication Methods

#### 1. JWT Token (Web App, Mobile)

**Flow:**
1. User logs in via `/auth/login` → receives JWT access token (15 min) + refresh token (30 days)
2. Include token in all requests: `Authorization: Bearer <access_token>`
3. Refresh token via `/auth/refresh` when expired

**Example:**
```bash
# Login
curl -X POST https://api.agentfactory.dev/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'

# Response
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 900,
    "token_type": "Bearer",
    "user": {
      "id": "usr_abc123",
      "email": "user@example.com",
      "plan_tier": "pro"
    }
  }
}

# Use token
curl -X GET https://api.agentfactory.dev/v1/agents \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### 2. API Key (CLI, Server-to-Server)

**Flow:**
1. Generate API key via web dashboard → `/settings/api-keys`
2. Include in header: `X-API-Key: <api_key>`
3. Scoped to team, can be revoked anytime

**Example:**
```bash
curl -X GET https://api.agentfactory.dev/v1/agents \
  -H "X-API-Key: ak_live_abc123def456..."
```

**API Key Prefixes:**
- `ak_live_...` - Production keys
- `ak_test_...` - Test mode keys (sandbox, no billing)

#### 3. OAuth 2.0 (Third-Party Integrations)

**Supported Flows:**
- Authorization Code (web apps)
- Client Credentials (server-to-server)

**Scopes:**
```
agents:read          - Read agent configurations
agents:write         - Create/update/delete agents
agents:run           - Execute agent runs
templates:read       - Browse marketplace templates
templates:publish    - Publish templates to marketplace
billing:read         - View subscription/usage data
team:read            - View team members
team:write           - Manage team members
webhooks:write       - Configure webhooks
```

### Authorization Model

**Row-Level Security (RLS):**
- All resources scoped to `team_id`
- User must be member of team to access resources
- Team owner has full permissions, members have restricted access

**Permission Levels:**
```
Owner:      Full control (billing, team management, all resources)
Admin:      Manage agents, runs, templates (no billing/team management)
Member:     Read-only access to agents, can execute runs
Billing:    Read-only access + billing management
```

---

## API Conventions

### Naming Conventions

**Resources:** Plural nouns (`/agents`, `/runs`, `/templates`)
**Actions:** Verbs in path (`/agents/{id}/run`, `/templates/{id}/fork`)
**Fields:** `snake_case` for JSON keys (`team_id`, `created_at`)
**IDs:** Prefixed with resource type (`agt_abc123`, `run_xyz789`, `tpl_def456`)

### Pagination

All list endpoints support pagination via `limit` and `offset` query parameters.

**Request:**
```bash
GET /v1/agents?limit=20&offset=40
```

**Response:**
```json
{
  "success": true,
  "data": [
    { "id": "agt_abc123", ... },
    { "id": "agt_def456", ... }
  ],
  "meta": {
    "pagination": {
      "total": 156,
      "limit": 20,
      "offset": 40,
      "has_more": true
    }
  }
}
```

**Defaults:**
- `limit`: 20 (max 100)
- `offset`: 0

### Filtering & Sorting

**Filtering:**
```bash
GET /v1/agents?status=active&tools=perplexity
GET /v1/runs?status=completed&created_after=2025-12-01
```

**Sorting:**
```bash
GET /v1/agents?sort=created_at:desc
GET /v1/templates?sort=rating:desc,downloads:desc
```

### Timestamps

All timestamps use **ISO 8601 format with UTC timezone**:
```json
{
  "created_at": "2025-12-07T10:30:00Z",
  "updated_at": "2025-12-07T14:22:15Z"
}
```

### Idempotency

POST/PUT/PATCH requests support idempotency via `Idempotency-Key` header:

```bash
curl -X POST https://api.agentfactory.dev/v1/agents \
  -H "Authorization: Bearer ..." \
  -H "Idempotency-Key: unique-key-12345" \
  -d '{ ... }'
```

Same key within 24 hours = same response (prevents duplicate resources).

---

## Core Endpoints

### Agents

#### `POST /v1/agents` - Create Agent

**Description:** Create a new agent from spec

**Request:**
```json
{
  "name": "Research Assistant",
  "description": "AI agent for web research and fact-checking",
  "spec_content": "# Agent Spec\n\n## Role\nYou are a research assistant...",
  "tools": ["perplexity", "wikipedia", "arxiv"],
  "invariants": {
    "cite_sources": true,
    "max_search_depth": 3
  },
  "llm_config": {
    "model": "claude-sonnet-4-5",
    "temperature": 0.3,
    "max_tokens": 4000
  }
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "agt_abc123",
    "team_id": "team_xyz789",
    "name": "Research Assistant",
    "description": "AI agent for web research and fact-checking",
    "status": "draft",
    "spec_content": "# Agent Spec...",
    "tools": ["perplexity", "wikipedia", "arxiv"],
    "invariants": {
      "cite_sources": true,
      "max_search_depth": 3
    },
    "llm_config": {
      "model": "claude-sonnet-4-5",
      "temperature": 0.3,
      "max_tokens": 4000
    },
    "created_at": "2025-12-07T10:30:00Z",
    "updated_at": "2025-12-07T10:30:00Z",
    "created_by": "usr_def456"
  }
}
```

#### `GET /v1/agents` - List Agents

**Query Parameters:**
- `status` - Filter by status (`draft`, `active`, `archived`)
- `tools` - Filter by tool name (comma-separated)
- `limit` - Pagination limit (default: 20, max: 100)
- `offset` - Pagination offset (default: 0)
- `sort` - Sort order (`created_at:desc`, `name:asc`, `updated_at:desc`)

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "agt_abc123",
      "name": "Research Assistant",
      "status": "active",
      "tools": ["perplexity", "wikipedia"],
      "created_at": "2025-12-07T10:30:00Z",
      "run_count": 47,
      "avg_runtime": 3.2
    },
    {
      "id": "agt_def456",
      "name": "Code Reviewer",
      "status": "active",
      "tools": ["github", "gitlab"],
      "created_at": "2025-12-06T14:22:00Z",
      "run_count": 23,
      "avg_runtime": 5.8
    }
  ],
  "meta": {
    "pagination": {
      "total": 12,
      "limit": 20,
      "offset": 0,
      "has_more": false
    }
  }
}
```

#### `GET /v1/agents/{agent_id}` - Get Agent Details

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "agt_abc123",
    "team_id": "team_xyz789",
    "name": "Research Assistant",
    "description": "AI agent for web research and fact-checking",
    "status": "active",
    "spec_content": "# Agent Spec\n\n## Role\nYou are a research assistant...",
    "tools": ["perplexity", "wikipedia", "arxiv"],
    "invariants": {
      "cite_sources": true,
      "max_search_depth": 3
    },
    "llm_config": {
      "model": "claude-sonnet-4-5",
      "temperature": 0.3,
      "max_tokens": 4000
    },
    "stats": {
      "total_runs": 47,
      "successful_runs": 45,
      "failed_runs": 2,
      "avg_runtime": 3.2,
      "avg_cost": 0.024,
      "total_cost": 1.13
    },
    "created_at": "2025-12-07T10:30:00Z",
    "updated_at": "2025-12-07T10:30:00Z",
    "created_by": "usr_def456"
  }
}
```

#### `PATCH /v1/agents/{agent_id}` - Update Agent

**Request:**
```json
{
  "name": "Advanced Research Assistant",
  "tools": ["perplexity", "wikipedia", "arxiv", "pubmed"],
  "status": "active"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "agt_abc123",
    "name": "Advanced Research Assistant",
    "tools": ["perplexity", "wikipedia", "arxiv", "pubmed"],
    "status": "active",
    "updated_at": "2025-12-07T11:15:00Z"
  }
}
```

#### `DELETE /v1/agents/{agent_id}` - Delete Agent

**Response (204 No Content):**
```
(Empty body)
```

**Note:** Soft delete - sets `deleted_at` timestamp, agent still accessible via API for 30 days

#### `POST /v1/agents/{agent_id}/run` - Execute Agent Run

**Request:**
```json
{
  "input": "Research the latest developments in quantum computing error correction",
  "context": {
    "max_sources": 5,
    "date_range": "2024-01-01:2025-12-07"
  },
  "stream": false
}
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "run_id": "run_xyz789",
    "agent_id": "agt_abc123",
    "status": "running",
    "input": "Research the latest developments...",
    "created_at": "2025-12-07T11:20:00Z",
    "estimated_completion": "2025-12-07T11:20:15Z"
  }
}
```

**Streaming Response (if `stream: true`):**
```
Server-Sent Events (SSE) format:

event: start
data: {"run_id":"run_xyz789","status":"running"}

event: tool_call
data: {"tool":"perplexity","query":"quantum computing error correction 2024"}

event: tool_result
data: {"tool":"perplexity","sources":[...]}

event: thinking
data: {"content":"Based on the search results..."}

event: complete
data: {"status":"completed","output":"...","cost":0.024}
```

#### `POST /v1/agents/{agent_id}/fork` - Fork Agent to New Team

**Request:**
```json
{
  "name": "My Forked Research Assistant",
  "include_runs": false
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "agt_ghi789",
    "name": "My Forked Research Assistant",
    "forked_from": "agt_abc123",
    "created_at": "2025-12-07T11:25:00Z"
  }
}
```

---

### Runs

#### `GET /v1/runs` - List Runs (All Agents)

**Query Parameters:**
- `agent_id` - Filter by agent
- `status` - Filter by status (`pending`, `running`, `completed`, `failed`)
- `created_after` - ISO 8601 timestamp
- `created_before` - ISO 8601 timestamp
- `limit` / `offset` - Pagination

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "run_abc123",
      "agent_id": "agt_xyz789",
      "agent_name": "Research Assistant",
      "status": "completed",
      "input": "Research quantum computing...",
      "output": "Based on recent research...",
      "runtime": 3.4,
      "cost": 0.024,
      "tokens_used": 1847,
      "created_at": "2025-12-07T10:30:00Z",
      "completed_at": "2025-12-07T10:30:03Z"
    }
  ],
  "meta": {
    "pagination": { ... },
    "aggregates": {
      "total_runs": 156,
      "total_cost": 4.32,
      "total_tokens": 187456,
      "avg_runtime": 4.2
    }
  }
}
```

#### `GET /v1/runs/{run_id}` - Get Run Details

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "run_abc123",
    "agent_id": "agt_xyz789",
    "agent_name": "Research Assistant",
    "status": "completed",
    "input": "Research the latest developments in quantum computing error correction",
    "output": "Based on recent research from Nature Physics (2024) and arXiv preprints...",
    "context": {
      "max_sources": 5,
      "date_range": "2024-01-01:2025-12-07"
    },
    "execution_log": [
      {
        "timestamp": "2025-12-07T10:30:00Z",
        "event": "start",
        "data": {}
      },
      {
        "timestamp": "2025-12-07T10:30:01Z",
        "event": "tool_call",
        "data": {
          "tool": "perplexity",
          "query": "quantum computing error correction 2024"
        }
      },
      {
        "timestamp": "2025-12-07T10:30:02Z",
        "event": "tool_result",
        "data": {
          "tool": "perplexity",
          "sources": [...]
        }
      },
      {
        "timestamp": "2025-12-07T10:30:03Z",
        "event": "complete",
        "data": {}
      }
    ],
    "llm_calls": [
      {
        "model": "claude-sonnet-4-5",
        "tokens_input": 847,
        "tokens_output": 1000,
        "cost": 0.024,
        "latency": 1.8
      }
    ],
    "tool_calls": [
      {
        "tool": "perplexity",
        "query": "quantum computing error correction 2024",
        "results_count": 5,
        "latency": 0.9
      }
    ],
    "runtime": 3.4,
    "cost": 0.024,
    "tokens_used": 1847,
    "created_at": "2025-12-07T10:30:00Z",
    "completed_at": "2025-12-07T10:30:03Z"
  }
}
```

#### `POST /v1/runs/{run_id}/cancel` - Cancel Running Job

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "run_abc123",
    "status": "cancelled",
    "cancelled_at": "2025-12-07T10:35:00Z"
  }
}
```

#### `GET /v1/runs/{run_id}/logs` - Stream Run Logs (SSE)

**Response (200 OK):**
```
Content-Type: text/event-stream

event: log
data: {"timestamp":"2025-12-07T10:30:00Z","level":"info","message":"Run started"}

event: log
data: {"timestamp":"2025-12-07T10:30:01Z","level":"info","message":"Calling Perplexity API..."}

event: log
data: {"timestamp":"2025-12-07T10:30:02Z","level":"info","message":"Received 5 sources"}
```

---

### Teams

#### `POST /v1/teams` - Create Team

**Request:**
```json
{
  "name": "Acme AI Labs",
  "slug": "acme-ai-labs",
  "billing_email": "billing@acme.com"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "team_abc123",
    "name": "Acme AI Labs",
    "slug": "acme-ai-labs",
    "owner_id": "usr_def456",
    "billing_email": "billing@acme.com",
    "created_at": "2025-12-07T10:30:00Z"
  }
}
```

#### `GET /v1/teams` - List User's Teams

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "team_abc123",
      "name": "Acme AI Labs",
      "slug": "acme-ai-labs",
      "role": "owner",
      "member_count": 5,
      "agent_count": 12,
      "created_at": "2025-12-07T10:30:00Z"
    }
  ]
}
```

#### `GET /v1/teams/{team_id}` - Get Team Details

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "team_abc123",
    "name": "Acme AI Labs",
    "slug": "acme-ai-labs",
    "owner_id": "usr_def456",
    "billing_email": "billing@acme.com",
    "plan_tier": "enterprise",
    "usage": {
      "runs_this_month": 1247,
      "runs_quota": 10000,
      "quota_reset_at": "2025-01-01T00:00:00Z"
    },
    "members": [
      {
        "user_id": "usr_def456",
        "email": "owner@acme.com",
        "role": "owner",
        "joined_at": "2025-12-07T10:30:00Z"
      },
      {
        "user_id": "usr_ghi789",
        "email": "member@acme.com",
        "role": "member",
        "joined_at": "2025-12-07T11:00:00Z"
      }
    ],
    "created_at": "2025-12-07T10:30:00Z"
  }
}
```

#### `PATCH /v1/teams/{team_id}` - Update Team

**Request:**
```json
{
  "name": "Acme AI Research Labs",
  "billing_email": "finance@acme.com"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "team_abc123",
    "name": "Acme AI Research Labs",
    "billing_email": "finance@acme.com",
    "updated_at": "2025-12-07T11:30:00Z"
  }
}
```

#### `POST /v1/teams/{team_id}/members` - Invite Team Member

**Request:**
```json
{
  "email": "newmember@acme.com",
  "role": "member"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "invitation_id": "inv_abc123",
    "email": "newmember@acme.com",
    "role": "member",
    "status": "pending",
    "expires_at": "2025-12-14T10:30:00Z",
    "created_at": "2025-12-07T10:30:00Z"
  }
}
```

#### `DELETE /v1/teams/{team_id}/members/{user_id}` - Remove Team Member

**Response (204 No Content):**
```
(Empty body)
```

#### `PATCH /v1/teams/{team_id}/members/{user_id}` - Update Member Role

**Request:**
```json
{
  "role": "admin"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "user_id": "usr_ghi789",
    "role": "admin",
    "updated_at": "2025-12-07T11:30:00Z"
  }
}
```

---

### Tools

#### `GET /v1/tools` - List Available Tools

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "perplexity",
      "name": "Perplexity Search",
      "description": "AI-powered web search with citations",
      "category": "research",
      "required_plan": "pro",
      "cost_per_call": 0.001,
      "parameters": {
        "query": {
          "type": "string",
          "required": true,
          "description": "Search query"
        },
        "max_results": {
          "type": "integer",
          "required": false,
          "default": 5
        }
      }
    },
    {
      "id": "github",
      "name": "GitHub Integration",
      "description": "Access GitHub repos, issues, PRs",
      "category": "development",
      "required_plan": "pro",
      "cost_per_call": 0,
      "requires_oauth": true
    }
  ]
}
```

#### `GET /v1/tools/{tool_id}` - Get Tool Details

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "perplexity",
    "name": "Perplexity Search",
    "description": "AI-powered web search with citations",
    "category": "research",
    "required_plan": "pro",
    "cost_per_call": 0.001,
    "parameters": {
      "query": {
        "type": "string",
        "required": true,
        "description": "Search query"
      },
      "max_results": {
        "type": "integer",
        "required": false,
        "default": 5,
        "min": 1,
        "max": 20
      }
    },
    "documentation_url": "https://docs.agentfactory.dev/tools/perplexity",
    "example": {
      "query": "latest quantum computing breakthroughs",
      "max_results": 5
    }
  }
}
```

---

## Marketplace Endpoints

### Templates

#### `GET /v1/marketplace/templates` - Browse Templates

**Query Parameters:**
- `category` - Filter by category (`research`, `coding`, `content`, `business`)
- `sort` - Sort order (`rating:desc`, `downloads:desc`, `created_at:desc`)
- `featured` - Show featured templates only (`true` / `false`)
- `search` - Full-text search query

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "tpl_abc123",
      "name": "SEO Content Writer",
      "description": "AI agent for writing SEO-optimized blog posts",
      "author": {
        "id": "usr_def456",
        "name": "John Doe",
        "avatar_url": "https://cdn.agentfactory.dev/avatars/usr_def456.jpg"
      },
      "category": "content",
      "rating": 4.8,
      "downloads": 1247,
      "price": 0,
      "featured": true,
      "thumbnail_url": "https://cdn.agentfactory.dev/templates/tpl_abc123/thumb.jpg",
      "created_at": "2025-11-15T10:00:00Z",
      "updated_at": "2025-12-01T14:30:00Z"
    }
  ],
  "meta": {
    "pagination": { ... }
  }
}
```

#### `GET /v1/marketplace/templates/{template_id}` - Get Template Details

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "tpl_abc123",
    "name": "SEO Content Writer",
    "description": "AI agent for writing SEO-optimized blog posts with keyword research",
    "long_description": "This template creates an AI agent specialized in...",
    "author": {
      "id": "usr_def456",
      "name": "John Doe",
      "avatar_url": "https://cdn.agentfactory.dev/avatars/usr_def456.jpg",
      "verified": true
    },
    "category": "content",
    "tags": ["seo", "content", "blog", "marketing"],
    "rating": 4.8,
    "rating_count": 156,
    "downloads": 1247,
    "price": 0,
    "featured": true,
    "spec_preview": "# SEO Content Writer Agent\n\n## Role\nYou are an expert SEO content writer...",
    "tools_used": ["perplexity", "ahrefs"],
    "screenshots": [
      "https://cdn.agentfactory.dev/templates/tpl_abc123/screen1.jpg",
      "https://cdn.agentfactory.dev/templates/tpl_abc123/screen2.jpg"
    ],
    "changelog": [
      {
        "version": "1.2",
        "date": "2025-12-01",
        "changes": "Added keyword density optimization"
      }
    ],
    "created_at": "2025-11-15T10:00:00Z",
    "updated_at": "2025-12-01T14:30:00Z"
  }
}
```

#### `POST /v1/marketplace/templates/{template_id}/install` - Install Template

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "agent_id": "agt_xyz789",
    "template_id": "tpl_abc123",
    "name": "SEO Content Writer (Installed)",
    "installed_at": "2025-12-07T11:00:00Z"
  }
}
```

#### `POST /v1/marketplace/templates` - Publish Template

**Request:**
```json
{
  "agent_id": "agt_abc123",
  "name": "Customer Support Bot",
  "description": "AI agent for automated customer support",
  "long_description": "This template helps you build...",
  "category": "business",
  "tags": ["support", "automation", "chatbot"],
  "price": 29,
  "thumbnail": "data:image/png;base64,..."
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "tpl_def456",
    "name": "Customer Support Bot",
    "status": "pending_review",
    "submitted_at": "2025-12-07T11:00:00Z",
    "review_eta": "2025-12-09T11:00:00Z"
  }
}
```

#### `POST /v1/marketplace/templates/{template_id}/rate` - Rate Template

**Request:**
```json
{
  "rating": 5,
  "review": "Amazing template! Saved me hours of work."
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "rating_id": "rat_abc123",
    "template_id": "tpl_def456",
    "rating": 5,
    "review": "Amazing template! Saved me hours of work.",
    "created_at": "2025-12-07T11:00:00Z"
  }
}
```

---

## Billing Endpoints

### Subscriptions

#### `GET /v1/billing/subscription` - Get Current Subscription

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "sub_abc123",
    "team_id": "team_xyz789",
    "plan_tier": "pro",
    "status": "active",
    "billing_period": "monthly",
    "current_period_start": "2025-12-01T00:00:00Z",
    "current_period_end": "2025-12-31T23:59:59Z",
    "cancel_at_period_end": false,
    "price": 49,
    "currency": "usd",
    "payment_method": {
      "type": "card",
      "last4": "4242",
      "brand": "visa",
      "exp_month": 12,
      "exp_year": 2027
    },
    "next_invoice": {
      "amount": 49,
      "date": "2025-12-31T00:00:00Z"
    }
  }
}
```

#### `POST /v1/billing/subscription` - Create/Update Subscription

**Request (Upgrade to Pro):**
```json
{
  "plan_tier": "pro",
  "billing_period": "annual"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "sub_abc123",
    "plan_tier": "pro",
    "billing_period": "annual",
    "status": "active",
    "price": 470,
    "discount": 118,
    "next_invoice": {
      "amount": 470,
      "date": "2026-12-07T00:00:00Z"
    },
    "updated_at": "2025-12-07T11:00:00Z"
  }
}
```

#### `DELETE /v1/billing/subscription` - Cancel Subscription

**Query Parameters:**
- `immediately` - Cancel now vs end of period (`true` / `false`, default: `false`)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "sub_abc123",
    "status": "cancelled",
    "cancel_at_period_end": true,
    "cancelled_at": "2025-12-07T11:00:00Z",
    "access_until": "2025-12-31T23:59:59Z"
  }
}
```

### Usage

#### `GET /v1/billing/usage` - Get Current Usage

**Query Parameters:**
- `start_date` - ISO 8601 date (default: start of current month)
- `end_date` - ISO 8601 date (default: now)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "period": {
      "start": "2025-12-01T00:00:00Z",
      "end": "2025-12-07T11:00:00Z"
    },
    "quota": {
      "runs_included": 1000,
      "runs_used": 247,
      "runs_remaining": 753,
      "overage_cost": 0
    },
    "costs": {
      "llm_calls": 12.34,
      "tool_calls": 3.21,
      "total": 15.55
    },
    "breakdown_by_agent": [
      {
        "agent_id": "agt_abc123",
        "agent_name": "Research Assistant",
        "runs": 156,
        "cost": 8.92
      },
      {
        "agent_id": "agt_def456",
        "agent_name": "Code Reviewer",
        "runs": 91,
        "cost": 6.63
      }
    ],
    "breakdown_by_model": [
      {
        "model": "claude-sonnet-4-5",
        "calls": 189,
        "tokens": 187456,
        "cost": 11.24
      },
      {
        "model": "perplexity/llama-3.1",
        "calls": 58,
        "tokens": 34567,
        "cost": 0.35
      }
    ]
  }
}
```

### Invoices

#### `GET /v1/billing/invoices` - List Invoices

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "inv_abc123",
      "invoice_number": "AF-2025-001234",
      "status": "paid",
      "amount": 49,
      "currency": "usd",
      "period_start": "2025-11-01T00:00:00Z",
      "period_end": "2025-11-30T23:59:59Z",
      "paid_at": "2025-11-01T00:05:23Z",
      "pdf_url": "https://invoices.agentfactory.dev/inv_abc123.pdf",
      "created_at": "2025-11-01T00:00:00Z"
    }
  ],
  "meta": {
    "pagination": { ... }
  }
}
```

#### `GET /v1/billing/invoices/{invoice_id}` - Get Invoice Details

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "inv_abc123",
    "invoice_number": "AF-2025-001234",
    "status": "paid",
    "amount": 49,
    "tax": 0,
    "total": 49,
    "currency": "usd",
    "line_items": [
      {
        "description": "Agent Factory Pro - December 2025",
        "quantity": 1,
        "unit_price": 49,
        "total": 49
      }
    ],
    "period_start": "2025-12-01T00:00:00Z",
    "period_end": "2025-12-31T23:59:59Z",
    "paid_at": "2025-12-01T00:05:23Z",
    "payment_method": {
      "type": "card",
      "last4": "4242"
    },
    "pdf_url": "https://invoices.agentfactory.dev/inv_abc123.pdf",
    "created_at": "2025-12-01T00:00:00Z"
  }
}
```

---

## Admin Endpoints

**Note:** Require `admin` role, not accessible by regular users.

### `GET /v1/admin/stats` - Platform Statistics

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "users": {
      "total": 5432,
      "active_30d": 2341,
      "new_30d": 456
    },
    "teams": {
      "total": 1234,
      "active_30d": 789
    },
    "agents": {
      "total": 12456,
      "active_30d": 4567
    },
    "runs": {
      "total": 187456,
      "last_24h": 3456,
      "last_7d": 23456,
      "last_30d": 89123
    },
    "revenue": {
      "mrr": 66000,
      "arr": 792000,
      "growth_30d": 0.12
    },
    "templates": {
      "total": 234,
      "pending_review": 12,
      "downloads_30d": 1234
    }
  }
}
```

### `GET /v1/admin/users` - List All Users

**Query Parameters:**
- `plan_tier` - Filter by plan
- `status` - Filter by status (`active`, `suspended`, `deleted`)
- `sort` - Sort order

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "usr_abc123",
      "email": "user@example.com",
      "plan_tier": "pro",
      "status": "active",
      "teams_count": 2,
      "agents_count": 12,
      "runs_30d": 247,
      "ltv": 588,
      "created_at": "2025-10-15T10:00:00Z",
      "last_active_at": "2025-12-07T10:30:00Z"
    }
  ],
  "meta": {
    "pagination": { ... }
  }
}
```

### `POST /v1/admin/users/{user_id}/suspend` - Suspend User

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "usr_abc123",
    "status": "suspended",
    "suspended_at": "2025-12-07T11:00:00Z"
  }
}
```

---

## Webhook Endpoints

### `GET /v1/webhooks` - List Webhooks

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "wh_abc123",
      "url": "https://myapp.com/webhooks/agentfactory",
      "events": ["agent.run.completed", "agent.run.failed"],
      "status": "active",
      "secret": "whsec_abc123...",
      "created_at": "2025-12-01T10:00:00Z"
    }
  ]
}
```

### `POST /v1/webhooks` - Create Webhook

**Request:**
```json
{
  "url": "https://myapp.com/webhooks/agentfactory",
  "events": ["agent.run.completed", "agent.run.failed", "billing.subscription.updated"],
  "secret": "my-webhook-secret-key"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "wh_abc123",
    "url": "https://myapp.com/webhooks/agentfactory",
    "events": ["agent.run.completed", "agent.run.failed", "billing.subscription.updated"],
    "status": "active",
    "secret": "whsec_abc123...",
    "created_at": "2025-12-07T11:00:00Z"
  }
}
```

### `DELETE /v1/webhooks/{webhook_id}` - Delete Webhook

**Response (204 No Content):**
```
(Empty body)
```

### Webhook Events

**Available Events:**
```
agent.created
agent.updated
agent.deleted
agent.run.started
agent.run.completed
agent.run.failed
team.member.added
team.member.removed
billing.subscription.created
billing.subscription.updated
billing.subscription.cancelled
billing.invoice.paid
billing.invoice.payment_failed
template.published
template.purchased
```

**Webhook Payload Format:**
```json
{
  "id": "evt_abc123",
  "type": "agent.run.completed",
  "created_at": "2025-12-07T11:00:00Z",
  "data": {
    "run_id": "run_xyz789",
    "agent_id": "agt_abc123",
    "status": "completed",
    "runtime": 3.4,
    "cost": 0.024
  }
}
```

**Webhook Signature Verification:**
```python
import hmac
import hashlib

def verify_webhook(payload: str, signature: str, secret: str) -> bool:
    """Verify webhook signature"""
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f"sha256={expected}", signature)

# Usage
signature = request.headers.get("X-AgentFactory-Signature")
is_valid = verify_webhook(request.body, signature, webhook_secret)
```

---

## Rate Limiting

### Rate Limit Tiers

| Plan Tier | Requests/Minute | Burst | Agent Runs/Day |
|-----------|----------------|-------|----------------|
| Free | 10 | 20 | 100 |
| Pro | 60 | 100 | 1000 |
| Enterprise | 300 | 500 | 10000 |

### Rate Limit Headers

All responses include rate limit headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1701950400
X-RateLimit-Retry-After: 23
```

### Rate Limit Error Response (429 Too Many Requests)

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please retry after 23 seconds.",
    "details": {
      "limit": 60,
      "remaining": 0,
      "reset_at": "2025-12-07T11:01:00Z",
      "retry_after": 23
    }
  }
}
```

### Upgrading Rate Limits

Users can request temporary rate limit increases:

```bash
POST /v1/billing/rate-limit-increase
{
  "duration": "24h",
  "multiplier": 2
}
```

**Cost:** $10 per 24 hours for 2x rate limit

---

## Error Handling

### Error Response Format

All errors follow this structure:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "specific_field",
      "issue": "detailed explanation"
    }
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2025-12-07T11:00:00Z",
    "version": "v1"
  }
}
```

### Error Codes

#### 4xx Client Errors

| Code | HTTP Status | Description | Solution |
|------|-------------|-------------|----------|
| `INVALID_REQUEST` | 400 | Malformed request body | Check request format |
| `VALIDATION_ERROR` | 400 | Invalid input parameters | Review error.details |
| `AUTHENTICATION_REQUIRED` | 401 | Missing or invalid auth | Provide valid token/API key |
| `INSUFFICIENT_PERMISSIONS` | 403 | User lacks permission | Check team role |
| `RESOURCE_NOT_FOUND` | 404 | Resource doesn't exist | Verify resource ID |
| `QUOTA_EXCEEDED` | 429 | Monthly quota reached | Upgrade plan or wait for reset |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests | Wait for rate limit reset |

#### 5xx Server Errors

| Code | HTTP Status | Description | Solution |
|------|-------------|-------------|----------|
| `INTERNAL_ERROR` | 500 | Unexpected server error | Retry or contact support |
| `SERVICE_UNAVAILABLE` | 503 | Temporary outage | Retry with exponential backoff |
| `GATEWAY_TIMEOUT` | 504 | Upstream timeout | Retry request |

### Example Error Responses

**Validation Error (400):**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid agent configuration",
    "details": {
      "field": "tools",
      "issue": "Tool 'perplexity' requires Pro plan or higher"
    }
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2025-12-07T11:00:00Z"
  }
}
```

**Authentication Error (401):**
```json
{
  "success": false,
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Invalid or expired access token",
    "details": {
      "hint": "Token expired at 2025-12-07T10:00:00Z. Use /auth/refresh to get new token."
    }
  }
}
```

**Quota Exceeded (429):**
```json
{
  "success": false,
  "error": {
    "code": "QUOTA_EXCEEDED",
    "message": "Monthly agent run quota exceeded",
    "details": {
      "quota": 1000,
      "used": 1000,
      "reset_at": "2026-01-01T00:00:00Z",
      "upgrade_url": "https://app.agentfactory.dev/billing/upgrade"
    }
  }
}
```

**Resource Not Found (404):**
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Agent not found",
    "details": {
      "resource_type": "agent",
      "resource_id": "agt_invalid123"
    }
  }
}
```

### Retry Strategy

**Recommended exponential backoff for 5xx errors:**

```python
import time
import random

def retry_with_backoff(func, max_retries=3):
    """Retry function with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise

            # Exponential backoff: 1s, 2s, 4s
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
```

---

## OpenAPI Specification

### Full OpenAPI 3.1 Schema

**Download:** https://api.agentfactory.dev/v1/openapi.json

**Snippet:**
```yaml
openapi: 3.1.0
info:
  title: Agent Factory API
  version: 1.0.0
  description: REST API for Agent Factory multi-agent platform
  contact:
    name: Agent Factory Support
    url: https://agentfactory.dev/support
    email: support@agentfactory.dev

servers:
  - url: https://api.agentfactory.dev/v1
    description: Production
  - url: https://api-staging.agentfactory.dev/v1
    description: Staging
  - url: http://localhost:8000/v1
    description: Local development

security:
  - BearerAuth: []
  - ApiKeyAuth: []

paths:
  /agents:
    get:
      summary: List agents
      operationId: listAgents
      tags: [Agents]
      parameters:
        - name: status
          in: query
          schema:
            type: string
            enum: [draft, active, archived]
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
        - name: offset
          in: query
          schema:
            type: integer
            minimum: 0
            default: 0
      responses:
        '200':
          description: List of agents
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AgentList'

    post:
      summary: Create agent
      operationId: createAgent
      tags: [Agents]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateAgentRequest'
      responses:
        '201':
          description: Agent created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Agent'

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key

  schemas:
    Agent:
      type: object
      properties:
        id:
          type: string
          example: agt_abc123
        team_id:
          type: string
          example: team_xyz789
        name:
          type: string
          example: Research Assistant
        description:
          type: string
        status:
          type: string
          enum: [draft, active, archived]
        spec_content:
          type: string
        tools:
          type: array
          items:
            type: string
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    CreateAgentRequest:
      type: object
      required:
        - name
        - spec_content
      properties:
        name:
          type: string
          minLength: 3
          maxLength: 50
        description:
          type: string
          maxLength: 500
        spec_content:
          type: string
        tools:
          type: array
          items:
            type: string
        invariants:
          type: object
        llm_config:
          type: object

    Error:
      type: object
      properties:
        success:
          type: boolean
          example: false
        error:
          type: object
          properties:
            code:
              type: string
            message:
              type: string
            details:
              type: object
```

### Generate Client SDKs

**Using OpenAPI Generator:**
```bash
# Python SDK
openapi-generator generate \
  -i https://api.agentfactory.dev/v1/openapi.json \
  -g python \
  -o ./sdk/python

# TypeScript SDK
openapi-generator generate \
  -i https://api.agentfactory.dev/v1/openapi.json \
  -g typescript-axios \
  -o ./sdk/typescript

# Go SDK
openapi-generator generate \
  -i https://api.agentfactory.dev/v1/openapi.json \
  -g go \
  -o ./sdk/go
```

---

## API Client Examples

### Python (requests)

```python
import requests

class AgentFactoryClient:
    def __init__(self, api_key: str, base_url: str = "https://api.agentfactory.dev/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}

    def list_agents(self, status: str = None, limit: int = 20):
        """List agents"""
        params = {"limit": limit}
        if status:
            params["status"] = status

        response = requests.get(
            f"{self.base_url}/agents",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()["data"]

    def create_agent(self, name: str, spec_content: str, tools: list = None):
        """Create new agent"""
        payload = {
            "name": name,
            "spec_content": spec_content,
            "tools": tools or []
        }

        response = requests.post(
            f"{self.base_url}/agents",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()["data"]

    def run_agent(self, agent_id: str, input_text: str, stream: bool = False):
        """Execute agent run"""
        payload = {
            "input": input_text,
            "stream": stream
        }

        response = requests.post(
            f"{self.base_url}/agents/{agent_id}/run",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()["data"]

# Usage
client = AgentFactoryClient(api_key="ak_live_abc123...")

# List agents
agents = client.list_agents(status="active")
print(f"Found {len(agents)} active agents")

# Create agent
agent = client.create_agent(
    name="Research Assistant",
    spec_content="# Agent Spec\n...",
    tools=["perplexity", "wikipedia"]
)
print(f"Created agent: {agent['id']}")

# Run agent
run = client.run_agent(
    agent_id=agent["id"],
    input_text="Research quantum computing"
)
print(f"Run started: {run['run_id']}")
```

### TypeScript (axios)

```typescript
import axios, { AxiosInstance } from 'axios';

interface Agent {
  id: string;
  name: string;
  status: 'draft' | 'active' | 'archived';
  tools: string[];
  created_at: string;
}

interface CreateAgentRequest {
  name: string;
  spec_content: string;
  tools?: string[];
  description?: string;
}

class AgentFactoryClient {
  private client: AxiosInstance;

  constructor(apiKey: string, baseUrl = 'https://api.agentfactory.dev/v1') {
    this.client = axios.create({
      baseURL: baseUrl,
      headers: {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json',
      },
    });
  }

  async listAgents(status?: string, limit = 20): Promise<Agent[]> {
    const response = await this.client.get('/agents', {
      params: { status, limit },
    });
    return response.data.data;
  }

  async createAgent(request: CreateAgentRequest): Promise<Agent> {
    const response = await this.client.post('/agents', request);
    return response.data.data;
  }

  async runAgent(agentId: string, input: string): Promise<any> {
    const response = await this.client.post(`/agents/${agentId}/run`, {
      input,
      stream: false,
    });
    return response.data.data;
  }
}

// Usage
const client = new AgentFactoryClient('ak_live_abc123...');

// List agents
const agents = await client.listAgents('active');
console.log(`Found ${agents.length} active agents`);

// Create agent
const agent = await client.createAgent({
  name: 'Research Assistant',
  spec_content: '# Agent Spec\n...',
  tools: ['perplexity', 'wikipedia'],
});
console.log(`Created agent: ${agent.id}`);

// Run agent
const run = await client.runAgent(agent.id, 'Research quantum computing');
console.log(`Run started: ${run.run_id}`);
```

### cURL Examples

**List Agents:**
```bash
curl -X GET "https://api.agentfactory.dev/v1/agents?status=active&limit=10" \
  -H "X-API-Key: ak_live_abc123..."
```

**Create Agent:**
```bash
curl -X POST "https://api.agentfactory.dev/v1/agents" \
  -H "X-API-Key: ak_live_abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Research Assistant",
    "spec_content": "# Agent Spec\n\n## Role\nYou are a research assistant...",
    "tools": ["perplexity", "wikipedia"]
  }'
```

**Run Agent:**
```bash
curl -X POST "https://api.agentfactory.dev/v1/agents/agt_abc123/run" \
  -H "X-API-Key: ak_live_abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Research the latest developments in quantum computing",
    "stream": false
  }'
```

**Get Run Status:**
```bash
curl -X GET "https://api.agentfactory.dev/v1/runs/run_xyz789" \
  -H "X-API-Key: ak_live_abc123..."
```

---

## API Performance Targets

| Endpoint Category | P50 | P95 | P99 | Timeout |
|-------------------|-----|-----|-----|---------|
| Auth (JWT) | <50ms | <100ms | <200ms | 5s |
| List endpoints | <100ms | <200ms | <500ms | 10s |
| CRUD operations | <150ms | <300ms | <600ms | 10s |
| Agent runs (simple) | <2s | <5s | <10s | 60s |
| Agent runs (complex) | <5s | <15s | <30s | 120s |
| Webhooks | <100ms | <200ms | <500ms | 5s |

---

## API Versioning Policy

### Current Version: v1

**Breaking Changes:**
- New major version (`/v2`)
- Minimum 6 months notice before deprecation
- Simultaneous support for old + new version (12 months overlap)

**Non-Breaking Changes:**
- New optional fields
- New endpoints
- New query parameters
- Patch updates within same version

### Deprecation Schedule

When deprecating endpoints:
1. **T-6 months:** Announcement via email, blog, changelog
2. **T-3 months:** `Deprecation` header added to responses
3. **T-1 month:** Warning emails to users still using deprecated endpoint
4. **T-0:** Endpoint returns `410 Gone`

**Example Deprecation Header:**
```
Deprecation: true
Sunset: Sat, 01 Jun 2026 00:00:00 GMT
Link: <https://docs.agentfactory.dev/api/migration/v1-to-v2>; rel="deprecation"
```

---

## Next Document

See `docs/00_tech_stack.md` for technology choices and rationale.

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-07 | Initial API design document |

# Agent Factory Platform - Database Schema
## Multi-Tenant PostgreSQL Schema with Row-Level Security

> **Generated:** 2025-12-07 (Phase 0)
> **Database:** PostgreSQL 15+ (Supabase)
> **Purpose:** Complete schema for multi-tenant SaaS platform
> **Security:** Row-Level Security (RLS) for data isolation

---

## Schema Overview

**Database Name:** `agent_factory_production`
**Total Tables:** 15 core tables + 5 junction tables
**Security Model:** Team-based isolation with RLS
**Hosting:** Supabase (managed PostgreSQL + Auth)

### Table Categories

1. **Users & Authentication** (3 tables)
   - users, api_keys, sessions

2. **Multi-Tenancy** (2 tables)
   - teams, team_members

3. **Agents** (3 tables)
   - agents, agent_versions, agent_runs

4. **Marketplace** (3 tables)
   - marketplace_templates, marketplace_reviews, marketplace_purchases

5. **Billing** (3 tables)
   - billing_subscriptions, billing_usage, billing_invoices

6. **Webhooks & Integrations** (2 tables)
   - webhooks, webhook_deliveries

7. **Monitoring** (2 tables)
   - llm_calls, error_logs

---

## Complete SQL Schema

```sql
-- ============================================================================
-- AGENT FACTORY PLATFORM - PRODUCTION DATABASE SCHEMA
-- PostgreSQL 15+ with Row-Level Security (RLS)
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Set timezone
SET timezone = 'UTC';

-- ============================================================================
-- DOMAIN TYPES & ENUMS
-- ============================================================================

CREATE TYPE plan_tier AS ENUM ('free', 'pro', 'enterprise');
CREATE TYPE user_role AS ENUM ('owner', 'admin', 'member', 'viewer');
CREATE TYPE agent_status AS ENUM ('draft', 'active', 'archived');
CREATE TYPE run_status AS ENUM ('queued', 'running', 'completed', 'failed', 'cancelled');
CREATE TYPE marketplace_status AS ENUM ('pending', 'approved', 'rejected', 'archived');
CREATE TYPE webhook_status AS ENUM ('pending', 'delivered', 'failed');

-- ============================================================================
-- USERS & AUTHENTICATION
-- ============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Identity
    email TEXT UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    full_name TEXT,
    avatar_url TEXT,

    -- Subscription
    plan_tier plan_tier DEFAULT 'free',
    stripe_customer_id TEXT UNIQUE,
    stripe_subscription_id TEXT,

    -- Quotas (enforced at application level)
    monthly_runs_quota INTEGER DEFAULT 100, -- Free: 100, Pro: 1000, Enterprise: 10000
    monthly_runs_used INTEGER DEFAULT 0,
    quota_reset_date DATE DEFAULT (CURRENT_DATE + INTERVAL '1 month'),

    -- Settings
    default_llm_provider TEXT DEFAULT 'openai',
    daily_budget_usd DECIMAL(10,2) DEFAULT 10.00,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    onboarding_completed BOOLEAN DEFAULT FALSE,

    -- Soft delete
    deleted_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'),
    CONSTRAINT valid_quota CHECK (monthly_runs_quota >= 0),
    CONSTRAINT valid_budget CHECK (daily_budget_usd >= 0)
);

-- Indexes
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_stripe_customer ON users(stripe_customer_id) WHERE stripe_customer_id IS NOT NULL;
CREATE INDEX idx_users_plan_tier ON users(plan_tier) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- Comments
COMMENT ON TABLE users IS 'User accounts with subscription and quota management';
COMMENT ON COLUMN users.monthly_runs_quota IS 'Total agent runs allowed per month based on plan';
COMMENT ON COLUMN users.monthly_runs_used IS 'Agent runs consumed this billing period';
COMMENT ON COLUMN users.quota_reset_date IS 'Date when monthly_runs_used resets to 0';

-- ============================================================================
-- API KEYS (for API access)
-- ============================================================================

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_id UUID,  -- Set after teams table is created

    -- Key details
    name TEXT NOT NULL,  -- User-friendly name: "Production API Key"
    key_hash TEXT UNIQUE NOT NULL,  -- Bcrypt hash of actual key
    key_prefix TEXT NOT NULL,  -- First 8 chars: "sk_live_abc12345"

    -- Permissions
    scopes TEXT[] DEFAULT ARRAY['agents:read', 'agents:write', 'runs:read', 'runs:write'],

    -- Rate limiting (per minute)
    rate_limit_per_minute INTEGER DEFAULT 60,
    last_used_at TIMESTAMPTZ,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_rate_limit CHECK (rate_limit_per_minute > 0)
);

-- Indexes
CREATE INDEX idx_api_keys_user ON api_keys(user_id) WHERE is_active = TRUE;
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_team ON api_keys(team_id) WHERE team_id IS NOT NULL;

COMMENT ON TABLE api_keys IS 'API keys for programmatic access to platform';

-- ============================================================================
-- TEAMS & MULTI-TENANCY
-- ============================================================================

CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Identity
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,  -- URL-friendly: "acme-corp"
    description TEXT,
    logo_url TEXT,

    -- Owner
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Settings
    default_llm_provider TEXT DEFAULT 'openai',
    daily_budget_usd DECIMAL(10,2) DEFAULT 10.00,

    -- Limits (enterprise-specific)
    max_agents INTEGER,
    max_members INTEGER,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT slug_format CHECK (slug ~* '^[a-z0-9-]+$'),
    CONSTRAINT valid_budget CHECK (daily_budget_usd >= 0)
);

-- Indexes
CREATE INDEX idx_teams_owner ON teams(owner_id);
CREATE INDEX idx_teams_slug ON teams(slug) WHERE deleted_at IS NULL;
CREATE INDEX idx_teams_created_at ON teams(created_at DESC);

COMMENT ON TABLE teams IS 'Organizations/workspaces for multi-user collaboration';
COMMENT ON COLUMN teams.slug IS 'URL-safe identifier for team (used in URLs)';

-- ============================================================================
-- TEAM MEMBERS (many-to-many: users ↔ teams)
-- ============================================================================

CREATE TABLE team_members (
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Role & permissions
    role user_role DEFAULT 'member',

    -- Metadata
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    invited_by UUID REFERENCES users(id),

    PRIMARY KEY (team_id, user_id)
);

-- Indexes
CREATE INDEX idx_team_members_user ON team_members(user_id);
CREATE INDEX idx_team_members_role ON team_members(role);

COMMENT ON TABLE team_members IS 'User membership in teams with role-based access';

-- Add foreign key to api_keys now that teams table exists
ALTER TABLE api_keys ADD CONSTRAINT fk_api_keys_team FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;

-- ============================================================================
-- AGENTS
-- ============================================================================

CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,

    -- Identity
    name TEXT NOT NULL,
    slug TEXT NOT NULL,  -- URL-friendly, unique within team
    description TEXT,
    icon_url TEXT,

    -- Specification (stored as JSONB for queryability)
    spec_content TEXT NOT NULL,  -- Full markdown spec
    spec_version INTEGER DEFAULT 1,
    spec_metadata JSONB,  -- Parsed spec sections

    -- Configuration
    tools JSONB DEFAULT '[]'::jsonb,  -- ["wikipedia_search", "read_file", ...]
    invariants JSONB DEFAULT '[]'::jsonb,  -- [{name: "...", description: "..."}]
    behavior_examples JSONB DEFAULT '[]'::jsonb,

    -- LLM Settings
    llm_provider TEXT DEFAULT 'openai',  -- openai, anthropic, google
    model_name TEXT DEFAULT 'gpt-4o-mini',
    temperature DECIMAL(3,2) DEFAULT 0.7 CHECK (temperature BETWEEN 0 AND 2),
    max_iterations INTEGER DEFAULT 15 CHECK (max_iterations > 0),
    max_execution_time INTEGER DEFAULT 120,  -- seconds

    -- Generated Code (optional storage)
    generated_code TEXT,  -- Python code
    generated_tests TEXT,  -- Pytest code

    -- Metadata
    status agent_status DEFAULT 'draft',
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_run_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,

    -- Marketplace (Phase 11)
    is_public BOOLEAN DEFAULT FALSE,  -- Listed in marketplace?
    marketplace_price DECIMAL(10,2),  -- One-time purchase price
    marketplace_installs INTEGER DEFAULT 0,

    -- Uniqueness within team
    UNIQUE (team_id, slug)
);

-- Indexes
CREATE INDEX idx_agents_team ON agents(team_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_agents_status ON agents(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_agents_created_by ON agents(created_by);
CREATE INDEX idx_agents_public ON agents(is_public) WHERE is_public = TRUE AND deleted_at IS NULL;
CREATE INDEX idx_agents_tools ON agents USING GIN (tools);  -- For tool search
CREATE INDEX idx_agents_last_run ON agents(last_run_at DESC NULLS LAST);

COMMENT ON TABLE agents IS 'AI agents with specs, configs, and generated code';
COMMENT ON COLUMN agents.spec_metadata IS 'Parsed sections of spec for fast querying';

-- ============================================================================
-- AGENT VERSIONS (version history)
-- ============================================================================

CREATE TABLE agent_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,

    version INTEGER NOT NULL,
    spec_content TEXT NOT NULL,
    generated_code TEXT,

    -- Change tracking
    changed_by UUID NOT NULL REFERENCES users(id),
    change_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (agent_id, version)
);

-- Indexes
CREATE INDEX idx_agent_versions_agent ON agent_versions(agent_id, version DESC);

COMMENT ON TABLE agent_versions IS 'Version history for agent specs';

-- ============================================================================
-- AGENT RUNS (execution history)
-- ============================================================================

CREATE TABLE agent_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,

    -- Input/Output
    input TEXT NOT NULL,
    output TEXT,
    error TEXT,  -- If failed

    -- Execution tracking
    status run_status DEFAULT 'queued',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,  -- Total execution time

    -- Cost Tracking
    model_used TEXT,
    tokens_prompt INTEGER,
    tokens_completion INTEGER,
    tokens_total INTEGER,
    cost_usd DECIMAL(10,4),  -- Per-run cost

    -- Performance metrics
    llm_calls INTEGER DEFAULT 0,
    tool_calls JSONB,  -- [{tool: "wikipedia_search", duration_ms: 234}]

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_duration CHECK (duration_ms >= 0),
    CONSTRAINT valid_cost CHECK (cost_usd >= 0)
);

-- Indexes
CREATE INDEX idx_agent_runs_agent ON agent_runs(agent_id, created_at DESC);
CREATE INDEX idx_agent_runs_user ON agent_runs(user_id, created_at DESC);
CREATE INDEX idx_agent_runs_team ON agent_runs(team_id, created_at DESC);
CREATE INDEX idx_agent_runs_status ON agent_runs(status);
CREATE INDEX idx_agent_runs_created ON agent_runs(created_at DESC);
CREATE INDEX idx_agent_runs_cost ON agent_runs(cost_usd DESC);  -- For cost analysis

COMMENT ON TABLE agent_runs IS 'Execution history with cost and performance metrics';

-- ============================================================================
-- MARKETPLACE
-- ============================================================================

CREATE TABLE marketplace_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    creator_id UUID NOT NULL REFERENCES users(id),

    -- Listing details
    title TEXT NOT NULL,
    description TEXT,
    long_description TEXT,  -- Markdown
    category TEXT,  -- "email", "research", "coding", "social", etc.
    tags TEXT[] DEFAULT '{}',

    -- Media
    icon_url TEXT,
    screenshots TEXT[] DEFAULT '{}',
    demo_video_url TEXT,

    -- Pricing
    is_free BOOLEAN DEFAULT TRUE,
    price_usd DECIMAL(10,2),

    -- Stats
    installs INTEGER DEFAULT 0,
    rating_avg DECIMAL(3,2) DEFAULT 0 CHECK (rating_avg BETWEEN 0 AND 5),
    rating_count INTEGER DEFAULT 0,

    -- Status
    status marketplace_status DEFAULT 'pending',
    featured BOOLEAN DEFAULT FALSE,
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMPTZ,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_price CHECK (price_usd >= 0)
);

-- Indexes
CREATE INDEX idx_marketplace_status ON marketplace_templates(status);
CREATE INDEX idx_marketplace_featured ON marketplace_templates(featured, rating_avg DESC) WHERE featured = TRUE;
CREATE INDEX idx_marketplace_category ON marketplace_templates(category);
CREATE INDEX idx_marketplace_creator ON marketplace_templates(creator_id);
CREATE INDEX idx_marketplace_installs ON marketplace_templates(installs DESC);
CREATE INDEX idx_marketplace_rating ON marketplace_templates(rating_avg DESC, rating_count DESC);

COMMENT ON TABLE marketplace_templates IS 'Public agent templates for discovery and purchase';

CREATE TABLE marketplace_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID NOT NULL REFERENCES marketplace_templates(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),

    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_text TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (template_id, user_id)  -- One review per user
);

-- Indexes
CREATE INDEX idx_marketplace_reviews_template ON marketplace_reviews(template_id, created_at DESC);
CREATE INDEX idx_marketplace_reviews_user ON marketplace_reviews(user_id);

COMMENT ON TABLE marketplace_reviews IS 'User reviews and ratings for marketplace templates';

CREATE TABLE marketplace_purchases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID NOT NULL REFERENCES marketplace_templates(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,

    -- Payment
    price_paid_usd DECIMAL(10,2) NOT NULL,
    stripe_payment_intent_id TEXT,

    -- Deployed agent
    deployed_agent_id UUID REFERENCES agents(id),  -- Agent created from template

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (template_id, user_id, team_id)  -- One purchase per team
);

-- Indexes
CREATE INDEX idx_marketplace_purchases_template ON marketplace_purchases(template_id);
CREATE INDEX idx_marketplace_purchases_user ON marketplace_purchases(user_id);
CREATE INDEX idx_marketplace_purchases_team ON marketplace_purchases(team_id);

COMMENT ON TABLE marketplace_purchases IS 'Purchase history for marketplace templates';

-- ============================================================================
-- BILLING
-- ============================================================================

CREATE TABLE billing_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Stripe details
    stripe_subscription_id TEXT UNIQUE NOT NULL,
    stripe_price_id TEXT NOT NULL,
    plan_tier plan_tier NOT NULL,

    -- Status
    status TEXT NOT NULL,  -- active, canceled, past_due, etc. (from Stripe)
    current_period_start TIMESTAMPTZ NOT NULL,
    current_period_end TIMESTAMPTZ NOT NULL,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at TIMESTAMPTZ,

    -- Pricing
    amount_usd DECIMAL(10,2) NOT NULL,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_billing_subscriptions_user ON billing_subscriptions(user_id);
CREATE INDEX idx_billing_subscriptions_stripe ON billing_subscriptions(stripe_subscription_id);
CREATE INDEX idx_billing_subscriptions_status ON billing_subscriptions(status);

COMMENT ON TABLE billing_subscriptions IS 'Stripe subscription management';

CREATE TABLE billing_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),

    -- Period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- Aggregates
    total_runs INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10,2) DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,

    -- Breakdown by model (JSONB for flexibility)
    cost_breakdown JSONB DEFAULT '{}'::jsonb,  -- {llama3: 0, perplexity: 2.50, claude: 5.00}

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (user_id, period_start)
);

-- Indexes
CREATE INDEX idx_billing_usage_user_period ON billing_usage(user_id, period_start DESC);

COMMENT ON TABLE billing_usage IS 'Aggregated usage metrics for billing purposes';

CREATE TABLE billing_invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),

    -- Stripe details
    stripe_invoice_id TEXT UNIQUE NOT NULL,
    stripe_invoice_url TEXT,

    -- Amount
    amount_usd DECIMAL(10,2) NOT NULL,
    amount_paid_usd DECIMAL(10,2) DEFAULT 0,

    -- Status
    status TEXT NOT NULL,  -- draft, open, paid, uncollectible
    paid BOOLEAN DEFAULT FALSE,

    -- Dates
    due_date DATE,
    paid_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_billing_invoices_user ON billing_invoices(user_id, created_at DESC);
CREATE INDEX idx_billing_invoices_stripe ON billing_invoices(stripe_invoice_id);
CREATE INDEX idx_billing_invoices_status ON billing_invoices(status);

COMMENT ON TABLE billing_invoices IS 'Invoice records synced from Stripe';

-- ============================================================================
-- WEBHOOKS & INTEGRATIONS
-- ============================================================================

CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,

    -- Configuration
    url TEXT NOT NULL,
    events TEXT[] NOT NULL,  -- ['agent.run.completed', 'agent.run.failed']
    secret TEXT NOT NULL,  -- For signing payloads (HMAC)

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_url CHECK (url ~* '^https?://.*')
);

-- Indexes
CREATE INDEX idx_webhooks_team ON webhooks(team_id) WHERE is_active = TRUE;

COMMENT ON TABLE webhooks IS 'Webhook endpoints for event notifications';

CREATE TABLE webhook_deliveries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    webhook_id UUID NOT NULL REFERENCES webhooks(id) ON DELETE CASCADE,

    -- Event details
    event_type TEXT NOT NULL,  -- "agent.run.completed"
    payload JSONB NOT NULL,

    -- Delivery tracking
    status webhook_status DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    response_code INTEGER,
    response_body TEXT,
    delivered_at TIMESTAMPTZ,
    next_retry_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_webhook_deliveries_webhook ON webhook_deliveries(webhook_id, created_at DESC);
CREATE INDEX idx_webhook_deliveries_status ON webhook_deliveries(status);
CREATE INDEX idx_webhook_deliveries_retry ON webhook_deliveries(next_retry_at) WHERE status = 'failed';

COMMENT ON TABLE webhook_deliveries IS 'Webhook delivery attempts with retry logic';

-- ============================================================================
-- MONITORING & LOGS
-- ============================================================================

CREATE TABLE llm_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_run_id UUID REFERENCES agent_runs(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),

    -- LLM details
    provider TEXT NOT NULL,  -- "openai", "anthropic", "perplexity"
    model TEXT NOT NULL,
    purpose TEXT,  -- "simple", "search", "complex"

    -- Tokens & cost
    tokens_prompt INTEGER,
    tokens_completion INTEGER,
    tokens_total INTEGER,
    cost_usd DECIMAL(10,4),

    -- Performance
    duration_ms INTEGER,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes (partitioned by date for performance)
CREATE INDEX idx_llm_calls_user_date ON llm_calls(user_id, created_at DESC);
CREATE INDEX idx_llm_calls_provider ON llm_calls(provider, created_at DESC);
CREATE INDEX idx_llm_calls_cost ON llm_calls(cost_usd DESC);

COMMENT ON TABLE llm_calls IS 'Detailed logging of all LLM API calls for cost analysis';

-- Partition by month for scalability
CREATE TABLE llm_calls_y2025m12 PARTITION OF llm_calls
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

CREATE TABLE error_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Error details
    error_type TEXT NOT NULL,
    error_message TEXT,
    stack_trace TEXT,

    -- Context
    user_id UUID REFERENCES users(id),
    agent_id UUID REFERENCES agents(id),
    agent_run_id UUID REFERENCES agent_runs(id),
    request_path TEXT,
    request_method TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_error_logs_type ON error_logs(error_type, created_at DESC);
CREATE INDEX idx_error_logs_user ON error_logs(user_id, created_at DESC);
CREATE INDEX idx_error_logs_created ON error_logs(created_at DESC);

COMMENT ON TABLE error_logs IS 'Application error tracking for debugging';

-- ============================================================================
-- ROW-LEVEL SECURITY (RLS)
-- ============================================================================

-- Helper function: Get teams user belongs to
CREATE OR REPLACE FUNCTION current_user_teams()
RETURNS SETOF UUID
LANGUAGE SQL STABLE
AS $$
    SELECT team_id
    FROM team_members
    WHERE user_id = current_setting('app.current_user_id')::uuid;
$$;

COMMENT ON FUNCTION current_user_teams() IS 'Returns team IDs for current user (used in RLS policies)';

-- Enable RLS on all tables with team_id
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE marketplace_purchases ENABLE ROW LEVEL SECURITY;

-- Teams: Users can only see their teams
CREATE POLICY teams_member_access ON teams
    FOR ALL
    USING (id IN (SELECT current_user_teams()));

-- Agents: Users can only see agents from their teams
CREATE POLICY agents_team_isolation ON agents
    FOR ALL
    USING (team_id IN (SELECT current_user_teams()));

-- Agent runs: Users can only see runs from their teams' agents
CREATE POLICY agent_runs_team_isolation ON agent_runs
    FOR ALL
    USING (team_id IN (SELECT current_user_teams()));

-- Marketplace purchases: Users can only see their own purchases
CREATE POLICY marketplace_purchases_team_isolation ON marketplace_purchases
    FOR ALL
    USING (team_id IN (SELECT current_user_teams()));

COMMENT ON POLICY teams_member_access ON teams IS 'Users can only access teams they belong to';
COMMENT ON POLICY agents_team_isolation ON agents IS 'Agents are isolated by team membership';
COMMENT ON POLICY agent_runs_team_isolation ON agent_runs IS 'Runs are isolated by team membership';

-- ============================================================================
-- TRIGGERS & FUNCTIONS
-- ============================================================================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

-- Apply to all tables with updated_at column
CREATE TRIGGER users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER teams_updated_at BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER marketplace_templates_updated_at BEFORE UPDATE ON marketplace_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Increment user monthly runs on agent run completion
CREATE OR REPLACE FUNCTION increment_user_runs()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status = 'completed' THEN
        UPDATE users
        SET monthly_runs_used = monthly_runs_used + 1
        WHERE id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER agent_runs_increment_usage AFTER INSERT ON agent_runs
    FOR EACH ROW EXECUTE FUNCTION increment_user_runs();

-- Update marketplace template rating when review added
CREATE OR REPLACE FUNCTION update_template_rating()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE marketplace_templates
    SET
        rating_count = (SELECT COUNT(*) FROM marketplace_reviews WHERE template_id = NEW.template_id),
        rating_avg = (SELECT AVG(rating) FROM marketplace_reviews WHERE template_id = NEW.template_id)
    WHERE id = NEW.template_id;
    RETURN NEW;
END;
$$;

CREATE TRIGGER marketplace_reviews_update_rating AFTER INSERT OR UPDATE ON marketplace_reviews
    FOR EACH ROW EXECUTE FUNCTION update_template_rating();

-- Reset monthly quotas (run daily via cron)
CREATE OR REPLACE FUNCTION reset_monthly_quotas()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE users
    SET
        monthly_runs_used = 0,
        quota_reset_date = quota_reset_date + INTERVAL '1 month'
    WHERE quota_reset_date <= CURRENT_DATE;
END;
$$;

COMMENT ON FUNCTION reset_monthly_quotas() IS 'Reset user quotas monthly (run via cron)';

-- ============================================================================
-- VIEWS (for common queries)
-- ============================================================================

-- Agent summary with run stats
CREATE VIEW agent_stats AS
SELECT
    a.id,
    a.name,
    a.team_id,
    a.status,
    COUNT(ar.id) AS total_runs,
    COUNT(ar.id) FILTER (WHERE ar.status = 'completed') AS successful_runs,
    COUNT(ar.id) FILTER (WHERE ar.status = 'failed') AS failed_runs,
    AVG(ar.duration_ms) FILTER (WHERE ar.status = 'completed') AS avg_duration_ms,
    SUM(ar.cost_usd) AS total_cost_usd,
    MAX(ar.created_at) AS last_run_at
FROM agents a
LEFT JOIN agent_runs ar ON a.id = ar.agent_id
GROUP BY a.id;

COMMENT ON VIEW agent_stats IS 'Agent performance summary with run statistics';

-- User usage summary
CREATE VIEW user_usage_summary AS
SELECT
    u.id,
    u.email,
    u.plan_tier,
    u.monthly_runs_quota,
    u.monthly_runs_used,
    COUNT(DISTINCT a.id) AS agent_count,
    COUNT(ar.id) AS total_runs_lifetime,
    SUM(ar.cost_usd) AS total_cost_lifetime
FROM users u
LEFT JOIN team_members tm ON u.id = tm.user_id
LEFT JOIN agents a ON tm.team_id = a.team_id
LEFT JOIN agent_runs ar ON u.id = ar.user_id
GROUP BY u.id;

COMMENT ON VIEW user_usage_summary IS 'User subscription and usage overview';

-- ============================================================================
-- SEED DATA (for development)
-- ============================================================================

-- Insert default admin user (development only)
INSERT INTO users (id, email, full_name, plan_tier, email_verified)
VALUES
    ('00000000-0000-0000-0000-000000000001', 'admin@agentfactory.com', 'Admin User', 'enterprise', TRUE)
ON CONFLICT (email) DO NOTHING;

-- ============================================================================
-- GRANTS & PERMISSIONS
-- ============================================================================

-- Grant read/write to application role
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Grant read-only to analytics role (future)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_readonly;

-- ============================================================================
-- MAINTENANCE SCRIPTS
-- ============================================================================

-- Vacuum and analyze (run weekly)
COMMENT ON DATABASE agent_factory_production IS 'Run VACUUM ANALYZE weekly for performance';

-- Monitor table sizes
CREATE VIEW table_sizes AS
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
```

---

## Schema Statistics

| Category | Tables | Indexes | Triggers | Views |
|----------|--------|---------|----------|-------|
| Users & Auth | 2 | 5 | 1 | 1 |
| Multi-Tenancy | 2 | 4 | 1 | 0 |
| Agents | 3 | 12 | 2 | 1 |
| Marketplace | 3 | 8 | 1 | 0 |
| Billing | 3 | 6 | 0 | 0 |
| Webhooks | 2 | 3 | 0 | 0 |
| Monitoring | 2 | 5 | 0 | 0 |
| **TOTAL** | **17** | **43** | **5** | **2** |

---

## Next Steps

1. **Phase 9 Implementation:**
   - Apply schema to Supabase project
   - Test all RLS policies
   - Migrate existing agents from files → database

2. **Phase 10 Integration:**
   - Connect Stripe webhooks to billing tables
   - Implement quota enforcement

3. **Phase 11 Setup:**
   - Seed marketplace with initial templates

---

**Document Version:** 1.0
**Last Updated:** 2025-12-07
**Database:** PostgreSQL 15+ (Supabase compatible)
**Total Lines:** 800+ SQL

-- Rivet Users & Subscriptions Database Schema
-- Purpose: Support Stripe integration, user provisioning, and subscription management
-- Created: 2025-12-27

-- =============================================================================
-- USERS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS rivet_users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  telegram_id BIGINT UNIQUE,
  subscription_tier VARCHAR(50) DEFAULT 'beta', -- 'beta', 'pro', 'team'
  stripe_customer_id VARCHAR(255) UNIQUE,
  monthly_print_limit INT DEFAULT 5, -- 5 for beta, -1 for unlimited
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- =============================================================================
-- SUBSCRIPTIONS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS rivet_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES rivet_users(id) ON DELETE CASCADE,
  stripe_subscription_id VARCHAR(255) UNIQUE NOT NULL,
  stripe_customer_id VARCHAR(255) NOT NULL,
  tier VARCHAR(50) NOT NULL, -- 'pro', 'team' (beta doesn't have subscriptions)
  status VARCHAR(50) NOT NULL, -- 'active', 'canceled', 'past_due', 'trialing'
  current_period_start TIMESTAMP,
  current_period_end TIMESTAMP,
  cancel_at_period_end BOOLEAN DEFAULT FALSE,
  canceled_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- =============================================================================
-- PAYMENTS TABLE (Optional - for auditing)
-- =============================================================================
CREATE TABLE IF NOT EXISTS rivet_payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES rivet_users(id) ON DELETE CASCADE,
  stripe_invoice_id VARCHAR(255) UNIQUE NOT NULL,
  amount_cents INT NOT NULL,
  status VARCHAR(50) NOT NULL, -- 'succeeded', 'failed', 'pending'
  payment_date TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================
CREATE INDEX idx_users_email ON rivet_users(email);
CREATE INDEX idx_users_telegram_id ON rivet_users(telegram_id);
CREATE INDEX idx_users_stripe_customer ON rivet_users(stripe_customer_id);
CREATE INDEX idx_subscriptions_user_id ON rivet_subscriptions(user_id);
CREATE INDEX idx_subscriptions_stripe_sub ON rivet_subscriptions(stripe_subscription_id);
CREATE INDEX idx_payments_user_id ON rivet_payments(user_id);

-- =============================================================================
-- EXAMPLE QUERIES FOR TESTING
-- =============================================================================
-- Verify tables created
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'rivet_%';

-- Insert test user
-- INSERT INTO rivet_users (email, subscription_tier) VALUES ('test@example.com', 'beta');

-- Query user with subscription
-- SELECT u.*, s.tier, s.status, s.current_period_end
-- FROM rivet_users u
-- LEFT JOIN rivet_subscriptions s ON u.id = s.user_id
-- WHERE u.email = 'test@example.com';

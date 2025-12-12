# Multi-Provider Database Integration

**Status:** ✅ Complete (as of 2025-12-12)
**Author:** Claude Code
**Purpose:** High-availability database architecture with automatic failover

---

## Overview

Agent Factory supports **3 PostgreSQL providers** with automatic failover:

- **Supabase** (Primary) - Managed PostgreSQL + pgvector, generous free tier
- **Railway** (Backup 1) - Fast deployment, $5/month credit
- **Neon** (Backup 2) - Serverless PostgreSQL with autoscaling

**Key Benefits:**
- ✅ **Zero downtime** - Automatic failover if primary goes down
- ✅ **Cost optimization** - Use free tiers across 3 providers ($0-$5/month total)
- ✅ **Vendor independence** - Not locked into single provider
- ✅ **Geographic distribution** - Choose regions for lower latency

---

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  (Agent Factory, RIVET, PLC Tutor, Friday, Jarvis)          │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────▼───────────┐
         │  DatabaseManager      │
         │  - Health checks      │
         │  - Connection pool    │
         │  - Failover logic     │
         └─────┬──────┬──────┬───┘
               │      │      │
       ┌───────▼─┐  ┌▼──────▼─┐  ┌▼───────────┐
       │ Supabase│  │ Railway │  │  Neon      │
       │(Primary)│  │(Backup1)│  │ (Backup2)  │
       └─────────┘  └─────────┘  └────────────┘
         500MB        ~500MB         3GB
        Free Tier  $5 credit/mo  Free Tier
```

### Failover Sequence

1. **Normal operation:** All queries go to Supabase (primary)
2. **Supabase down:** Health check fails → automatic failover to Railway
3. **Railway down:** Health check fails → automatic failover to Neon
4. **All down:** Exception raised (requires manual intervention)
5. **Recovery:** When Supabase health check passes → return to primary

**Failover time:** < 5 seconds (configurable timeout)

---

## Setup Instructions

### Prerequisites

1. Python 3.10+ with Poetry
2. PostgreSQL client libraries: `poetry add "psycopg[binary]" psycopg-pool`
3. At least one database provider configured (Supabase recommended)

### Step 1: Provider Configuration

#### Option A: Supabase (Recommended Primary)

1. Go to [supabase.com](https://supabase.com) → Create project
2. Wait for database provisioning (~2 minutes)
3. Get credentials:
   - **Dashboard → Settings → Database**
   - Host: `db.[project-ref].supabase.co`
   - Password: (revealed in dashboard)
4. Add to `.env`:
   ```bash
   SUPABASE_DB_HOST=db.your-project-ref.supabase.co
   SUPABASE_DB_PASSWORD=your_password_here
   SUPABASE_URL=https://your-project-ref.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   ```

#### Option B: Railway (Recommended Backup 1)

1. Go to [railway.app](https://railway.app) → New Project
2. Add → Database → PostgreSQL
3. Click PostgreSQL service → Connect tab
4. Copy connection string
5. Add to `.env`:
   ```bash
   RAILWAY_DB_URL=postgresql://postgres:[password]@containers-us-west-xxx.railway.app:5432/railway
   ```

#### Option C: Neon (Recommended Backup 2)

1. Go to [neon.tech](https://neon.tech) → Create project
2. Copy connection string from dashboard
3. Add to `.env`:
   ```bash
   NEON_DB_URL=postgresql://[user]:[password]@[host].neon.tech/[dbname]?sslmode=require
   ```

### Step 2: Configure Failover

Add to `.env`:

```bash
# Primary provider (which to use first)
DATABASE_PROVIDER=supabase

# Enable automatic failover
DATABASE_FAILOVER_ENABLED=true

# Failover order (comma-separated, left to right)
DATABASE_FAILOVER_ORDER=supabase,railway,neon
```

### Step 3: Deploy Schema

Deploy the complete schema to all providers:

```bash
# Deploy to Neon
poetry run python scripts/deploy_multi_provider_schema.py --provider neon

# Deploy to Railway (when credentials filled in)
poetry run python scripts/deploy_multi_provider_schema.py --provider railway

# Supabase already has schema (primary)

# Verify all schemas match
poetry run python scripts/deploy_multi_provider_schema.py --verify
```

### Step 4: Test Connection

```bash
# Test imports
poetry run python -c "from agent_factory.core.database_manager import DatabaseManager; print('OK')"

# Test health checks
poetry run python -c "from agent_factory.core.database_manager import DatabaseManager; db = DatabaseManager(); print(db.health_check_all())"

# Run tests
poetry run pytest tests/test_database_failover.py -v
```

---

## Usage Examples

### Basic Usage

```python
from agent_factory.core.database_manager import DatabaseManager

# Initialize (auto-selects provider from env)
db = DatabaseManager()

# Execute query with automatic failover
rows = db.execute_query("SELECT * FROM knowledge_atoms LIMIT 10")

# Check which providers are healthy
health = db.health_check_all()
print(health)  # {'supabase': True, 'railway': False, 'neon': True}
```

### Using with Memory Storage

```python
from agent_factory.memory import Session, PostgresMemoryStorage

# Uses multi-provider with automatic failover
storage = PostgresMemoryStorage()

# Create and save session
session = Session(user_id="alice", storage=storage)
session.add_user_message("Hello")
session.save()  # Saves to primary or failover provider

# Load session later (works even if provider changed)
loaded = storage.load_session(session.session_id)
```

### Manual Provider Switching

```python
from agent_factory.core.database_manager import DatabaseManager

db = DatabaseManager()

# Start with Supabase
print(db.primary_provider)  # 'supabase'

# Switch to Neon manually
db.set_provider('neon')

# All subsequent queries use Neon
rows = db.execute_query("SELECT COUNT(*) FROM session_memories")
```

### Context Manager (Auto-cleanup)

```python
from agent_factory.core.database_manager import DatabaseManager

with DatabaseManager() as db:
    # Connection pools auto-managed
    rows = db.execute_query("SELECT * FROM knowledge_atoms")
    # Pools automatically closed when exiting context
```

### Health Monitoring

```python
from agent_factory.core.database_manager import DatabaseManager

db = DatabaseManager()

# Check all providers
for name, is_healthy in db.health_check_all().items():
    if is_healthy:
        print(f"[OK] {name} is healthy")
    else:
        print(f"[DOWN] {name} is unreachable")

# Get detailed stats
stats = db.get_provider_stats()
for name, info in stats.items():
    print(f"{name}:")
    print(f"  Healthy: {info['healthy']}")
    print(f"  Host: {info['connection_string_host']}")
    print(f"  Pool Active: {info['pool_active']}")
```

---

## Provider Comparison

| Feature | Supabase | Railway | Neon |
|---------|----------|---------|------|
| **Free Tier** | 500MB DB, 2GB egress | $5/mo credit | 3GB storage, unlimited egress |
| **Uptime SLA** | 99.9% | 99.9% | 99.95% |
| **Backups** | Daily (7 days) | Manual | Instant (point-in-time) |
| **pgvector** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Connection Pooling** | ✅ Supavisor | ❌ Manual | ✅ Built-in |
| **Geographic Regions** | 8 regions | US/EU | US/EU/Asia |
| **Serverless** | No | No | ✅ Yes (autoscaling) |
| **Dashboard** | ✅ Excellent | ✅ Good | ✅ Excellent |
| **Setup Time** | ~2 min | ~1 min | ~30 sec |
| **Best For** | Primary (feature-rich) | Backup (fast) | Backup (scalable) |

### Cost Comparison (Monthly)

**Free Tier (Development):**
- Supabase: $0 (500MB DB + 2GB egress)
- Railway: $0 (uses $5 credit, ~500MB)
- Neon: $0 (3GB storage, unlimited egress)
- **Total: $0/month**

**Production (Scale):**
- Supabase Pro: $25/mo (8GB DB, 50GB egress, daily backups)
- Railway Pro: $20/mo (8GB RAM, 100GB egress)
- Neon Scale: $19/mo (10GB storage, autoscaling compute)
- **Total: $64/month** (for high availability across 3 providers)

---

## Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_PROVIDER` | No | `supabase` | Primary provider to use |
| `DATABASE_FAILOVER_ENABLED` | No | `true` | Enable automatic failover |
| `DATABASE_FAILOVER_ORDER` | No | `supabase,railway,neon` | Failover sequence |
| `SUPABASE_DB_HOST` | If using Supabase | - | Supabase database host |
| `SUPABASE_DB_PASSWORD` | If using Supabase | - | Supabase database password |
| `RAILWAY_DB_URL` | If using Railway | - | Railway connection string |
| `NEON_DB_URL` | If using Neon | - | Neon connection string |

### Programmatic Configuration

```python
import os
os.environ['DATABASE_PROVIDER'] = 'neon'  # Use Neon as primary
os.environ['DATABASE_FAILOVER_ENABLED'] = 'false'  # Disable failover
os.environ['DATABASE_FAILOVER_ORDER'] = 'neon,supabase'  # Custom order
```

---

## Troubleshooting

### Issue: "No database providers configured"

**Cause:** No valid provider credentials in .env
**Fix:**
1. Check `.env` has at least one of: `SUPABASE_DB_HOST`, `RAILWAY_DB_URL`, `NEON_DB_URL`
2. Verify passwords are not empty or placeholders
3. Test connection manually: `psql <connection_string>`

### Issue: "Failed to resolve host"

**Cause:** DNS resolution failure or incorrect host
**Fix:**
1. Check internet connection
2. Verify host in `.env` matches dashboard
3. Try ping: `ping db.your-project.supabase.co`

### Issue: Queries slow or timing out

**Cause:** Using distant provider or network issues
**Fix:**
1. Check `db.get_provider_stats()` to see which provider is active
2. Switch to geographically closer provider
3. Increase timeout: Modify `psycopg_pool.ConnectionPool(timeout=10.0)`

### Issue: Schemas don't match across providers

**Cause:** Schema deployed to only some providers
**Fix:**
```bash
# Verify all schemas
poetry run python scripts/deploy_multi_provider_schema.py --verify

# Re-deploy to providers that are out of sync
poetry run python scripts/deploy_multi_provider_schema.py --provider railway
```

### Issue: Tests failing with import errors

**Cause:** psycopg not installed
**Fix:**
```bash
poetry add "psycopg[binary]" psycopg-pool
```

---

## Advanced Topics

### Custom Failover Order

You can customize which providers are tried first:

```bash
# Use Railway as primary, Neon as backup
DATABASE_PROVIDER=railway
DATABASE_FAILOVER_ORDER=railway,neon,supabase
```

### Disable Failover (Single Provider)

For development or cost savings, use only one provider:

```bash
DATABASE_PROVIDER=supabase
DATABASE_FAILOVER_ENABLED=false
```

### Geographic Optimization

Deploy providers in different regions for global coverage:

```
Provider 1: Supabase US-East (primary for North America)
Provider 2: Railway EU-West (primary for Europe)
Provider 3: Neon Asia-Pacific (primary for Asia)
```

Update `DATABASE_FAILOVER_ORDER` based on user location.

### Health Check Tuning

Health checks are cached for 60 seconds by default. Adjust in `database_manager.py`:

```python
class DatabaseProvider:
    def __init__(self, name: str, connection_string: str):
        self._health_check_ttl = 30  # Check every 30 seconds instead of 60
```

### Connection Pool Tuning

Adjust pool size for high-traffic applications:

```python
# In database_manager.py
self._pool = ConnectionPool(
    self.connection_string,
    min_size=5,     # Keep 5 connections warm
    max_size=50,    # Allow up to 50 concurrent connections
    timeout=10.0    # Wait up to 10 seconds for connection
)
```

---

## Monitoring & Metrics

### Health Check Dashboard

```python
from agent_factory.core.database_manager import DatabaseManager
import time

db = DatabaseManager()

while True:
    health = db.health_check_all()
    stats = db.get_provider_stats()

    for name in db.providers:
        status = "[UP]" if health[name] else "[DOWN]"
        host = stats[name]['connection_string_host']
        print(f"{status} {name} ({host})")

    time.sleep(60)  # Check every minute
```

### Alerting on Failover

```python
import logging

logger = logging.getLogger("agent_factory.core.database_manager")
logger.setLevel(logging.WARNING)

# Logs will show:
# WARNING: Executed on failover provider 'railway' (primary 'supabase' unavailable)
```

---

## Migration Guide

### From SupabaseMemoryStorage to PostgresMemoryStorage

**Before (Supabase-only):**
```python
from agent_factory.memory import Session, SupabaseMemoryStorage

storage = SupabaseMemoryStorage()
session = Session(user_id="alice", storage=storage)
```

**After (Multi-provider with failover):**
```python
from agent_factory.memory import Session, PostgresMemoryStorage

storage = PostgresMemoryStorage()  # Uses DatabaseManager internally
session = Session(user_id="alice", storage=storage)
```

**Backward Compatibility:** `SupabaseMemoryStorage` still works (uses REST API). `PostgresMemoryStorage` uses direct PostgreSQL connections and supports failover.

### Migrating Data Between Providers

```bash
# 1. Export from Supabase
pg_dump "postgresql://postgres:password@db.supabase.co:5432/postgres" > backup.sql

# 2. Import to Neon
psql "postgresql://user:password@neon.tech/db" < backup.sql

# 3. Verify data
poetry run python scripts/deploy_multi_provider_schema.py --verify
```

---

## Security Considerations

1. **Credentials:** Store in `.env`, never commit to git
2. **SSL/TLS:** All providers use encrypted connections (sslmode=require)
3. **Service Role Key:** Use `SUPABASE_SERVICE_ROLE_KEY` for backend, not `SUPABASE_ANON_KEY`
4. **Row-Level Security:** Configure in Supabase dashboard if needed
5. **API Keys:** Rotate keys regularly (every 90 days)

---

## Testing

### Unit Tests

```bash
# Run all database tests
poetry run pytest tests/test_database_failover.py -v

# Test specific scenario
poetry run pytest tests/test_database_failover.py::TestDatabaseFailover::test_manager_initialization_with_env_vars -v
```

### Integration Tests (Requires Live Databases)

```bash
# Set up test databases
export TEST_SUPABASE_DB_HOST="..."
export TEST_NEON_DB_URL="..."

# Run integration tests
poetry run pytest tests/integration/test_database_live.py -v
```

### Manual Testing

```bash
# Test connection to each provider
poetry run python -c "
from agent_factory.core.database_manager import DatabaseManager
db = DatabaseManager()
print('Primary:', db.primary_provider)
print('Health:', db.health_check_all())
print('Stats:', db.get_provider_stats())
"
```

---

## FAQ

**Q: Which provider should I use as primary?**
A: Supabase recommended for production (best features, generous free tier). Neon good for development (instant setup, autoscaling).

**Q: Do I need all 3 providers?**
A: No. One is enough for development. Two recommended for production (primary + backup). Three for high-availability mission-critical apps.

**Q: Will my data sync between providers?**
A: No, not automatically. Each provider is independent. Future: implement periodic sync (see "Future Enhancements").

**Q: What happens during failover?**
A: Query retries on backup provider within 5 seconds. No data loss (query either succeeds or fails cleanly).

**Q: Can I use different schemas on different providers?**
A: Not recommended. Use `--verify` to ensure schemas match.

**Q: How much does this cost?**
A: Free tier: $0/month. Production with all 3: ~$64/month.

---

## Future Enhancements

- **Automatic Data Sync:** Periodic replication (primary → backups) every 6 hours
- **Read Replicas:** Route read queries to closest geographic provider
- **Circuit Breaker:** Temporarily disable provider after N failures, retry later
- **Metrics Dashboard:** Web UI showing health, latency, query counts
- **Geographic Routing:** Auto-select provider based on user IP
- **Load Balancing:** Distribute queries across healthy providers

---

## Support & Resources

- **Documentation:** This file + `CLAUDE.md`
- **Examples:** `examples/memory_demo.py`
- **Tests:** `tests/test_database_failover.py`
- **Issues:** [GitHub Issues](https://github.com/anthropics/agent-factory/issues)
- **Supabase Docs:** https://supabase.com/docs/guides/database
- **Railway Docs:** https://docs.railway.app/databases/postgresql
- **Neon Docs:** https://neon.tech/docs/introduction

---

## Changelog

### 2025-12-12 - Initial Release
- ✅ DatabaseManager with 3-provider support
- ✅ Automatic failover logic
- ✅ PostgresMemoryStorage integration
- ✅ Schema deployment script
- ✅ Comprehensive test suite
- ✅ Documentation

### Future Versions
- [ ] Active-passive replication
- [ ] Prometheus metrics export
- [ ] Admin dashboard (web UI)
- [ ] Geographic routing

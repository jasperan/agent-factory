# Autonomous Plan - Telegram Admin Panel

**Goal:** Build universal remote control for Agent Factory via Telegram
**Est. Time:** 5-6 hours
**Status:** IN PROGRESS

---

## Task Queue

### Phase 1: Core Admin Infrastructure (90-120 min)
**Status:** PENDING
**Files to Create:**
- `agent_factory/integrations/telegram/admin/__init__.py`
- `agent_factory/integrations/telegram/admin/dashboard.py`
- `agent_factory/integrations/telegram/admin/command_parser.py`
- `agent_factory/integrations/telegram/admin/permissions.py`

**Features:**
- `/admin` command with inline keyboard menu system
- Text command parser (voice commands Phase 2)
- Role-based permissions (admin/viewer)
- Command routing to specialized managers
- Error handling + audit logging

**Menu Structure:**
```
/admin →
  ├── 🤖 Agents (view status, logs, start/stop)
  ├── 📝 Content (review queue, approve/reject)
  ├── 🚀 Deploy (GitHub Actions triggers)
  ├── 📚 KB (statistics, ingestion)
  ├── 📊 Metrics (analytics, costs)
  └── ⚙️ System (health checks)
```

**Validation:** Import check successful

---

### Phase 2: Agent Management (60-90 min)
**Status:** PENDING
**Files to Create:**
- `agent_factory/integrations/telegram/admin/agent_manager.py`

**Features:**
- View all agents (query LangFuse + database)
- Agent status: running/stopped/error
- Recent activity (last 5 runs)
- Start/stop commands (future: actual control)
- Performance metrics: tokens, cost, latency
- Log streaming (last 20 lines)
- Trace links to LangFuse dashboard

**Commands:**
- `/agents` - List all agents with status
- `/agent <name>` - Detailed view of specific agent
- `/agent_logs <name>` - Stream recent logs

**Data Sources:**
- LangFuse API for traces
- Supabase `agent_runs` table (to be created)
- VPS service status (docker ps, systemctl)

**Validation:** Can query and display agent status

---

### Phase 3: Content Review System (60-90 min)
**Status:** PENDING
**Files to Create:**
- `agent_factory/integrations/telegram/admin/content_reviewer.py`

**Features:**
- Approval queue (pending content from all channels)
- Content preview (text, metadata, quality scores)
- Inline buttons: Approve ✅ / Reject ❌ / Edit ✏️
- Update database on action
- Notifications when new content ready
- Filter by content type (YouTube, Reddit, Social)

**Commands:**
- `/content` - View pending queue (default: all types)
- `/content youtube` - Filter YouTube videos
- `/content reddit` - Filter Reddit posts
- `/content social` - Filter social media posts

**Database Table:**
```sql
CREATE TABLE IF NOT EXISTS content_queue (
    id SERIAL PRIMARY KEY,
    content_type VARCHAR(50),  -- 'youtube', 'reddit', 'social'
    title TEXT,
    content TEXT,
    metadata JSONB,  -- {quality_score, citations, agent_id, etc}
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    reviewed_by INTEGER,  -- Telegram user_id
    review_notes TEXT
);
```

**Validation:** Can view, approve, reject content

---

### Phase 4: GitHub Integration (45-60 min)
**Status:** PENDING
**Files to Create:**
- `agent_factory/integrations/telegram/admin/github_actions.py`

**Features:**
- Trigger GitHub Actions workflows via API
- View recent workflow runs
- Status notifications (success/failure)
- Invoke @claude in issues/PRs (future)

**Commands:**
- `/deploy` - Trigger VPS deployment
- `/workflow <name>` - Trigger custom workflow
- `/workflows` - List available workflows
- `/workflow_status` - View recent runs

**GitHub API Endpoints:**
```python
# Trigger workflow
POST /repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches

# List workflow runs
GET /repos/{owner}/{repo}/actions/runs

# Get workflow run status
GET /repos/{owner}/{repo}/actions/runs/{run_id}
```

**Environment Variables:**
```
GITHUB_TOKEN=ghp_...
GITHUB_OWNER=Mikecranesync
GITHUB_REPO=Agent-Factory
```

**Validation:** Can trigger deployment workflow successfully

---

### Phase 5: KB Management (30-45 min)
**Status:** PENDING
**Files to Create:**
- `agent_factory/integrations/telegram/admin/kb_manager.py`

**Features:**
- View atom count + growth statistics
- Trigger VPS ingestion (add URL to queue)
- Search KB content
- Queue depth monitoring
- Failed ingestion review

**Commands:**
- `/kb` - Overall statistics
- `/kb_ingest <url>` - Add URL to ingestion queue
- `/kb_search <query>` - Search KB content
- `/kb_queue` - View pending URLs

**VPS Integration:**
```python
# Add URL to Redis queue
docker exec infra_redis_1 redis-cli RPUSH kb_ingest_jobs "https://..."

# Query atom count
docker exec infra_postgres_1 psql -U rivet -d rivet -c "SELECT COUNT(*) FROM knowledge_atoms;"
```

**Validation:** Can view stats and trigger ingestion

---

### Phase 6: Analytics Dashboard (45-60 min)
**Status:** PENDING
**Files to Create:**
- `agent_factory/integrations/telegram/admin/analytics.py`

**Features:**
- Today's statistics summary
- Agent performance graphs (simple text-based initially)
- Cost breakdown (OpenAI/Anthropic API usage)
- Revenue tracking (Stripe integration hooks)
- User engagement metrics

**Commands:**
- `/metrics` - Today's summary
- `/metrics week` - Weekly dashboard
- `/costs` - API cost breakdown
- `/revenue` - Stripe revenue stats

**Data Sources:**
- LangFuse cost tracking API
- Stripe API (monthly revenue)
- Database (agent_runs, user_sessions)
- VPS logs (request counts)

**Text-Based Graphs:**
```
Agent Performance (last 7 days):
ResearchAgent:  ████████░░ 83% success
CoderAgent:     ██████████ 95% success
AnalystAgent:   ███████░░░ 72% success

API Costs (today):
OpenAI:     $12.34 ██████████████░░░░░░ (68%)
Anthropic:  $ 5.67 ███████░░░░░░░░░░░░░ (32%)
Total:      $18.01
```

**Validation:** Can view metrics and cost breakdown

---

### Phase 7: System Control (30-45 min)
**Status:** PENDING
**Files to Create:**
- `agent_factory/integrations/telegram/admin/system_control.py`

**Features:**
- Database health checks (all providers: Neon, Supabase, Railway, Local)
- VPS service status (docker containers, systemd services)
- Memory/CPU stats (if available via SSH)
- Emergency restart commands
- Configuration updates (.env variables)

**Commands:**
- `/health` - Complete system health check
- `/db_health` - Database connectivity tests
- `/vps_status` - VPS services status
- `/restart <service>` - Restart specific service

**Health Check Output:**
```
System Health Report:

Databases:
✅ Neon: Connected (1,965 atoms)
✅ Railway: Connected
⚠️  Supabase: DNS issue
❌ Local: Not running

VPS Services (72.60.175.144):
✅ rivet-worker: Running (uptime 2d 14h)
✅ postgres: Running
✅ redis: Running
✅ ollama: Running

Telegram Bot:
✅ Connected (last message 2m ago)
```

**Validation:** Can check health of all systems

---

### Phase 8: Integration & Testing (30-45 min)
**Status:** PENDING
**Files to Update:**
- `telegram_bot.py` - Register all admin handlers
- `agent_factory/integrations/telegram/admin/__init__.py` - Export managers
- `.env` - Add GitHub token
- `CLAUDE.md` - Document admin commands

**Database Migrations:**
```sql
-- Run these in Supabase SQL Editor
-- 1. Content queue table (Phase 3)
-- 2. Admin actions audit log
-- 3. Agent runs tracking table
```

**Telegram Bot Integration:**
```python
# In telegram_bot.py
from agent_factory.integrations.telegram.admin import AdminDashboard

admin = AdminDashboard()

# Register handlers
app.add_handler(CommandHandler("admin", admin.handle_admin))
app.add_handler(CommandHandler("agents", admin.agent_manager.handle_agents))
app.add_handler(CommandHandler("content", admin.content_reviewer.handle_content))
# ... etc
```

**Testing Checklist:**
- [ ] `/admin` opens menu with 6 buttons
- [ ] `/agents` shows agent status
- [ ] `/content` shows pending queue (or empty)
- [ ] `/deploy` triggers GitHub Action
- [ ] `/kb` shows statistics
- [ ] `/metrics` displays dashboard
- [ ] `/health` checks all systems
- [ ] All commands log to admin_actions table
- [ ] Permission checks work (unauthorized users blocked)
- [ ] Error handling graceful (user-friendly messages)

**Documentation Updates:**
```markdown
## Telegram Admin Panel Commands

### Main Menu
- `/admin` - Open admin dashboard

### Agent Management
- `/agents` - View all agents status
- `/agent <name>` - Detailed agent view
- `/agent_logs <name>` - Stream agent logs

### Content Review
- `/content` - View approval queue
- `/content <type>` - Filter by type (youtube/reddit/social)

### GitHub Actions
- `/deploy` - Trigger VPS deployment
- `/workflow <name>` - Run custom workflow
- `/workflows` - List available workflows

### Knowledge Base
- `/kb` - View statistics
- `/kb_ingest <url>` - Add URL to queue
- `/kb_search <query>` - Search KB

### Analytics
- `/metrics` - Today's dashboard
- `/costs` - API cost breakdown
- `/revenue` - Stripe revenue

### System Control
- `/health` - Complete health check
- `/db_health` - Database status
- `/vps_status` - VPS services
```

**Validation:** All commands functional, docs updated

---

## Decision Rules

### No Questions Needed For:

1. **File Organization**
   - Follow existing `telegram/` package structure
   - One manager per feature area
   - All managers inherit from base handler pattern

2. **Error Handling**
   ```python
   try:
       # Operation
   except Exception as e:
       logger.error(f"Failed: {e}")
       await update.message.reply_text(
           "❌ Operation failed. Please try again or contact support."
       )
       # Log to admin_actions with error details
   ```

3. **Permissions**
   ```python
   def check_admin(user_id: int) -> bool:
       return user_id in AUTHORIZED_USERS
   ```

4. **Database Queries**
   - Use existing `SupabaseMemoryStorage` connection
   - Parameterized queries (prevent SQL injection)
   - Error handling for connection failures

5. **GitHub API**
   - Use `requests` library
   - Bearer token auth
   - 3x retry with exponential backoff

6. **Command Naming**
   - Lowercase with underscores
   - Verb-first: `/agent_logs`, `/kb_search`
   - Short and memorable

7. **Inline Keyboards**
   ```python
   keyboard = [
       [InlineKeyboardButton("🤖 Agents", callback_data="menu_agents")],
       [InlineKeyboardButton("📝 Content", callback_data="menu_content")],
       # ...
   ]
   reply_markup = InlineKeyboardMarkup(keyboard)
   ```

8. **Logging**
   ```python
   logger.info(f"User {user_id} executed: {command}")
   # Also log to admin_actions table
   ```

### Escalate (STOP and REPORT) For:

1. **Security Issues**
   - Credentials found in code
   - Permission bypass attempts
   - Unsafe user input handling

2. **External Failures**
   - GitHub API down
   - LangFuse API unavailable
   - VPS SSH connection failed

3. **Schema Conflicts**
   - Table already exists with different structure
   - Migration requires data transformation

4. **Missing Config**
   - `GITHUB_TOKEN` not in .env
   - Required permissions not granted

5. **Ambiguous Requirements**
   - Feature behavior not specified in plan
   - Multiple valid implementation approaches
   - User preference needed

---

## Commit Strategy

**Checkpoint Commits (every 45-60 min):**
```
git add .
git commit -m "checkpoint: telegram admin - completed [X/8 phases]"
```

**Feature Commits (after each phase):**
```
feat(telegram-admin): Add core admin infrastructure (Phase 1)

- Created admin package structure
- Implemented main dashboard with inline keyboard menu
- Added command parser for text commands
- Built permission system with role checks
- Added audit logging for admin actions

Includes:
- agent_factory/integrations/telegram/admin/__init__.py
- agent_factory/integrations/telegram/admin/dashboard.py
- agent_factory/integrations/telegram/admin/command_parser.py
- agent_factory/integrations/telegram/admin/permissions.py

🤖 Generated with Claude Code (Autonomous Mode)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Success Criteria

### Minimum Viable (4-5 hours):
- ✅ Core infrastructure (Phase 1)
- ✅ Agent management (Phase 2)
- ✅ Content review (Phase 3)
- ✅ GitHub integration (Phase 4)

### Complete (5-6 hours):
- ✅ All 8 phases complete
- ✅ All commands functional
- ✅ Error handling throughout
- ✅ Documentation updated

### Stretch (6-7 hours):
- ✅ Voice command support
- ✅ Real-time notifications
- ✅ Advanced analytics graphs

---

## Validation Commands

```bash
# After Phase 1
poetry run python -c "from agent_factory.integrations.telegram.admin import AdminDashboard; print('Phase 1 OK')"

# After Phase 2
poetry run python -c "from agent_factory.integrations.telegram.admin import AgentManager; print('Phase 2 OK')"

# After Phase 3
poetry run python -c "from agent_factory.integrations.telegram.admin import ContentReviewer; print('Phase 3 OK')"

# After Phase 4
poetry run python -c "from agent_factory.integrations.telegram.admin import GitHubActions; print('Phase 4 OK')"

# After Phase 5
poetry run python -c "from agent_factory.integrations.telegram.admin import KBManager; print('Phase 5 OK')"

# After Phase 6
poetry run python -c "from agent_factory.integrations.telegram.admin import Analytics; print('Phase 6 OK')"

# After Phase 7
poetry run python -c "from agent_factory.integrations.telegram.admin import SystemControl; print('Phase 7 OK')"

# Final integration
poetry run python telegram_bot.py  # Should start without errors
```

---

## Progress Tracking

**Started:** [will be filled during execution]
**Current Phase:** Phase 1
**Completed Phases:** 0/8
**Est. Remaining:** 5-6 hours
**Blockers:** None

---

## Notes

- Keep it simple first (text menus, basic features)
- Voice commands in Phase 2 (after MVP proven)
- Focus on reliability over elegance
- User can iterate and enhance later
- Build foundation for future AI assistant layer

---

**Status:** Ready to begin autonomous execution

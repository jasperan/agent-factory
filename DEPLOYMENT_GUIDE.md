# RIVET Telegram Bot - Deployment Guide

**Date**: 2025-12-27
**Status**: Ready for production deployment

---

## What's New

✅ **Onboarding system fully integrated** into Telegram bot with:
- Tier-aware welcome messages (Beta/Pro/Enterprise)
- 5-step interactive tutorial
- API key authentication from landing page
- Feature tours with inline buttons
- Quick reference commands

---

## Prerequisites

### 1. Database Migration

Run the onboarding schema migration on your production database:

```bash
# Option 1: PostgreSQL CLI
psql -U rivet -d rivet -f docs/database/migrations/003_add_onboarding_fields.sql

# Option 2: Supabase SQL Editor
# 1. Login to Supabase Dashboard
# 2. Go to SQL Editor
# 3. Paste contents of docs/database/migrations/003_add_onboarding_fields.sql
# 4. Run query
```

**Verify migration:**
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'rivet_users'
  AND column_name LIKE 'onboarding%';
```

Expected result:
```
column_name              | data_type
-------------------------|----------
onboarding_completed     | boolean
onboarding_step          | integer
onboarding_skipped       | boolean
onboarding_completed_at  | timestamp
feature_tour_completed   | jsonb
```

---

## Deployment Steps

### Step 1: Pull Latest Code

```bash
cd /path/to/Agent-Factory
git pull origin rivet-bot
```

### Step 2: Install Dependencies

```bash
poetry install
```

### Step 3: Environment Variables

Ensure your `.env` has:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
AUTHORIZED_TELEGRAM_USERS=your_telegram_user_id

# Database (choose one)
DATABASE_PROVIDER=neon  # or supabase, railway, local

# Neon (recommended)
NEON_DATABASE_URL=postgresql://user:password@host/database

# OR Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_service_role_key

# Backend API (for API key validation)
BACKEND_API_URL=http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: OpenAI for voice transcription
OPENAI_API_KEY=your_openai_key

# Optional: Anthropic for context extraction
ANTHROPIC_API_KEY=your_anthropic_key
```

### Step 4: Test Locally (Optional)

```bash
# Test imports
poetry run python -c "from agent_factory.integrations.telegram.rivet_pro_handlers import rivet_pro_handlers; print('OK')"

# Run bot locally
poetry run python telegram_bot.py
```

**Test commands in Telegram:**
1. Send `/start` to your bot
2. Should see tier-aware welcome message with inline buttons
3. Click "Start Tutorial" to test onboarding flow
4. Try `/tour`, `/quickstart`, `/about` commands

### Step 5: Deploy to Production

#### Option A: Systemd Service (Linux)

Create `/etc/systemd/system/rivet-bot.service`:

```ini
[Unit]
Description=RIVET Telegram Bot
After=network.target

[Service]
Type=simple
User=rivet
WorkingDirectory=/opt/rivet/Agent-Factory
Environment="PATH=/opt/rivet/.local/bin:/usr/bin"
ExecStart=/opt/rivet/.local/bin/poetry run python telegram_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable rivet-bot
sudo systemctl start rivet-bot
sudo systemctl status rivet-bot
```

**View logs:**
```bash
sudo journalctl -u rivet-bot -f
```

#### Option B: tmux (Quick)

```bash
tmux new -s rivet-bot
cd /path/to/Agent-Factory
poetry run python telegram_bot.py

# Detach: Ctrl+B, then D
# Reattach: tmux attach -t rivet-bot
```

#### Option C: Docker (Coming Soon)

```bash
# TODO: Add Dockerfile and docker-compose.yml
docker-compose up -d rivet-bot
```

---

## Verification

### 1. Bot is Running

Check Telegram bot responds:
```
/start
```

Expected: Tier-aware welcome message with "Start Tutorial" button

### 2. Onboarding Flow Works

Test full flow:
1. `/start` → Shows welcome + buttons
2. Click "Start Tutorial" → Shows Step 2 (Feature Tour)
3. Click "Next Step" → Progresses through tutorial
4. Click "Finish Onboarding" → Completion message

### 3. Commands Work

Test each command:
```
/tutorial   → Replays onboarding
/tour       → Shows feature tour menu
/quickstart → Quick reference card
/about      → About RIVET
/pricing    → Tier comparison
```

### 4. API Key Authentication

Test from landing page:
1. Get API key from https://landing-zeta-plum.vercel.app/pricing
2. Send to bot: `/start sk_rivet_abc123`
3. Should authenticate and link Telegram ID to user account

### 5. Database State

Check onboarding progress is saved:
```sql
SELECT
  telegram_id,
  subscription_tier,
  onboarding_step,
  onboarding_completed,
  onboarding_completed_at
FROM rivet_users
WHERE telegram_id IS NOT NULL
LIMIT 5;
```

---

## Troubleshooting

### Bot Not Responding

**Check bot is running:**
```bash
# Systemd
sudo systemctl status rivet-bot

# tmux
tmux list-sessions
tmux attach -t rivet-bot
```

**Check logs for errors:**
```bash
# Systemd
sudo journalctl -u rivet-bot -n 50

# tmux
# Just read the terminal output
```

### Database Connection Errors

**Test database connection:**
```bash
poetry run python -c "
from agent_factory.core.database_manager import DatabaseManager
db = DatabaseManager()
print('Health check:', db.health_check_all())
"
```

**Common fixes:**
- Check `DATABASE_PROVIDER` in .env matches configured provider
- Verify database credentials are correct
- Test database URL with psql: `psql $NEON_DATABASE_URL`

### Import Errors

**Validate all modules import:**
```bash
poetry run python -c "
from agent_factory.integrations.telegram.onboarding_manager import OnboardingManager
from agent_factory.integrations.telegram.feature_tour import FeatureTour
from agent_factory.integrations.telegram.quick_reference import get_quickstart_message
print('All imports OK')
"
```

**Common fixes:**
- Run `poetry install` to ensure dependencies are current
- Check Python version: `python --version` (should be 3.10+)

### Callback Query Not Working

**Symptoms**: Clicking inline buttons does nothing

**Fix**: Check callback query handler is registered:
```python
# In telegram_bot.py, should see:
application.add_handler(CallbackQueryHandler(
    rivet_handlers.handle_onboarding_callback,
    pattern="^(onboard_|tour_)"
))
```

**Test**: Look for "CallbackQuery" in logs when clicking buttons

---

## Monitoring

### Key Metrics to Track

1. **Onboarding Completion Rate**
   ```sql
   SELECT
     subscription_tier,
     COUNT(*) as total,
     SUM(CASE WHEN onboarding_completed THEN 1 ELSE 0 END) as completed,
     ROUND(100.0 * SUM(CASE WHEN onboarding_completed THEN 1 ELSE 0 END) / COUNT(*), 2) as pct
   FROM rivet_users
   GROUP BY subscription_tier;
   ```

2. **Average Time to Complete**
   ```sql
   SELECT
     AVG(EXTRACT(EPOCH FROM (onboarding_completed_at - created_at))) / 60 as avg_minutes
   FROM rivet_users
   WHERE onboarding_completed = TRUE;
   ```

3. **Step Drop-off**
   ```sql
   SELECT
     onboarding_step,
     COUNT(*) as stuck_users
   FROM rivet_users
   WHERE onboarding_completed = FALSE AND onboarding_step > 0
   GROUP BY onboarding_step
   ORDER BY onboarding_step;
   ```

### Dashboard Queries

Add these to your monitoring dashboard:

```sql
-- Today's onboarding stats
SELECT
  COUNT(*) as new_users_today,
  SUM(CASE WHEN onboarding_completed THEN 1 ELSE 0 END) as completed_today
FROM rivet_users
WHERE created_at::date = CURRENT_DATE;

-- Active onboarding sessions
SELECT COUNT(*) as in_progress
FROM rivet_users
WHERE onboarding_step BETWEEN 1 AND 4
  AND onboarding_completed = FALSE;

-- Skip rate
SELECT
  COUNT(*) as total_new_users,
  SUM(CASE WHEN onboarding_skipped THEN 1 ELSE 0 END) as skipped,
  ROUND(100.0 * SUM(CASE WHEN onboarding_skipped THEN 1 ELSE 0 END) / COUNT(*), 2) as skip_pct
FROM rivet_users
WHERE created_at > NOW() - INTERVAL '7 days';
```

---

## Rollback Plan

If issues arise, rollback to previous version:

### 1. Stop Bot
```bash
sudo systemctl stop rivet-bot
# OR
tmux kill-session -t rivet-bot
```

### 2. Revert Code
```bash
git checkout <previous-commit-hash>
poetry install
```

### 3. Revert Database Migration (if needed)
```sql
-- Remove onboarding columns
ALTER TABLE rivet_users
DROP COLUMN IF EXISTS onboarding_completed,
DROP COLUMN IF EXISTS onboarding_step,
DROP COLUMN IF EXISTS onboarding_skipped,
DROP COLUMN IF EXISTS onboarding_completed_at,
DROP COLUMN IF EXISTS feature_tour_completed;

DROP INDEX IF EXISTS idx_users_onboarding_completed;
DROP INDEX IF EXISTS idx_users_onboarding_step;
```

### 4. Restart Bot
```bash
sudo systemctl start rivet-bot
# OR
tmux new -s rivet-bot
poetry run python telegram_bot.py
```

---

## Post-Deployment Checklist

- [ ] Database migration ran successfully
- [ ] Bot starts without errors
- [ ] `/start` shows onboarding flow
- [ ] Inline buttons work (click "Start Tutorial")
- [ ] `/tutorial`, `/tour`, `/quickstart` commands work
- [ ] API key authentication tested: `/start <api_key>`
- [ ] Database saves onboarding progress
- [ ] Logs show no errors
- [ ] Monitoring dashboard updated with new queries
- [ ] Team notified of new commands

---

## Support

**Issues or questions?**
- GitHub Issues: https://github.com/anthropics/claude-code/issues
- Email: support@rivet.com
- Docs: See `ONBOARDING_IMPLEMENTATION_SUMMARY.md`

---

## Next Steps (Future Enhancements)

1. **Analytics Dashboard**
   - Track onboarding metrics in real-time
   - A/B test message variations
   - Identify drop-off points

2. **Personalization**
   - Industry-specific onboarding paths
   - Job role-based tutorials
   - Recommended features based on usage

3. **Gamification**
   - Badges for completing tutorials
   - Achievement system
   - Progress leaderboard

---

**Deployed**: 2025-12-27
**Version**: RIVET Telegram Bot v2.0 (with Onboarding)
**Status**: ✅ Production Ready

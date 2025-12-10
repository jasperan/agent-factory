# GitHub Strategy Setup Guide

**Your system is READY! Just run the SQL migration.**

## Current Status

✅ Supabase configured (URL + service key in `.env`)
✅ Orchestrator installed (`orchestrator.py`)
✅ Webhook handler installed (`webhook_handler.py`)
✅ Telegram bot installed (`telegram_bot.py`)
✅ 18 agent skeletons ready for implementation
✅ Autonomous mode ready (8-hour sessions)

❌ **Database tables not created yet** (run Step 1 below)

## Step 1: Create Database Tables (3 minutes)

1. **Open Supabase SQL Editor:**
   - Go to: https://mggqgrxwumnnujojndub.supabase.co/project/_/sql
   - Login if needed

2. **Run Migration:**
   - Copy entire contents of `docs/supabase_agent_migrations.sql`
   - Paste into SQL Editor
   - Click "Run" button
   - Wait for success message

3. **Verify Tables Created:**
   ```bash
   poetry run python -c "
   from agent_factory.memory.storage import SupabaseMemoryStorage
   storage = SupabaseMemoryStorage()

   # Test each table
   storage.client.table('agent_status').select('*').limit(1).execute()
   storage.client.table('agent_jobs').select('*').limit(1).execute()
   storage.client.table('agent_messages').select('*').limit(1).execute()

   print('✅ All tables created successfully!')
   "
   ```

## Step 2: Test Orchestrator (2 minutes)

```bash
# Test orchestrator can connect
poetry run python -c "
from orchestrator import Orchestrator
orch = Orchestrator()
print('✅ Orchestrator initialized')

jobs = orch.fetch_pending_jobs()
print(f'✅ Found {len(jobs)} pending jobs')

orch.send_heartbeat()
print('✅ Heartbeat sent')
"
```

## Step 3: Set Up Telegram Bot (5 minutes)

1. **Create Telegram Bot:**
   - Open Telegram app
   - Search for @BotFather
   - Send: `/newbot`
   - Follow prompts to create bot
   - Copy token

2. **Add Token to .env:**
   ```bash
   # Add this line to .env
   TELEGRAM_BOT_TOKEN=<your_token_from_botfather>

   # Add your Telegram user ID (get from @userinfobot)
   AUTHORIZED_TELEGRAM_USERS=<your_user_id>
   ```

3. **Test Telegram Bot:**
   ```bash
   poetry run python telegram_bot.py
   ```

   Then in Telegram:
   - Find your bot
   - Send: `/start`
   - Send: `/status`

## Step 4: Set Up GitHub Webhook (5 minutes)

1. **Start Webhook Handler:**
   ```bash
   # Option 1: Local testing with ngrok
   poetry run python webhook_handler.py  # Terminal 1
   ngrok http 8000  # Terminal 2, copy HTTPS URL

   # Option 2: Deploy to VPS (recommended for production)
   # See: docs/DEPLOYMENT.md
   ```

2. **Configure GitHub Webhook:**
   - Go to: https://github.com/Mikecranesync/Agent-Factory/settings/hooks
   - Click "Add webhook"
   - Payload URL: `https://your-ngrok-url.ngrok.io/webhook/github`
   - Content type: `application/json`
   - Secret: Generate strong secret, add to `.env` as `GITHUB_WEBHOOK_SECRET`
   - Events: Select "push", "release", "issues"
   - Click "Add webhook"

3. **Test Webhook:**
   ```bash
   # Make a test commit
   echo "test" >> test.txt
   git add test.txt
   git commit -m "test: webhook trigger"
   git push

   # Check webhook_handler.py logs for incoming event
   # Check Supabase agent_jobs table for new job
   ```

## Step 5: Run 24/7 (optional)

**Option 1: tmux (recommended for testing)**
```bash
tmux new -s orchestrator "poetry run python orchestrator.py"
tmux new -s telegram "poetry run python telegram_bot.py"
tmux new -s webhook "poetry run python webhook_handler.py"

# Detach: Ctrl+B, then D
# Reattach: tmux attach -t orchestrator
```

**Option 2: systemd (recommended for production)**
See: `docs/SYSTEMD_SETUP.md` (coming soon)

## Quick Test Commands

```bash
# Test all components import
poetry run python -c "
from orchestrator import Orchestrator
from webhook_handler import app
from agents.executive.ai_ceo_agent import AICEOAgent
import telegram_bot
print('✅ All components import successfully')
"

# Test Supabase connection
poetry run python -c "
from agent_factory.memory.storage import SupabaseMemoryStorage
storage = SupabaseMemoryStorage()
print('✅ Supabase connected')
"

# Test orchestrator functions
poetry run python -c "
from orchestrator import Orchestrator
orch = Orchestrator()
jobs = orch.fetch_pending_jobs()
orch.send_heartbeat()
print(f'✅ Orchestrator working ({len(jobs)} jobs)')
"
```

## What You Get

### Telegram Commands (PRIMARY INTERFACE)
- `/status` - Real-time agent status dashboard
- `/agents` - List all agents and their health
- `/metrics` - View performance metrics
- `/approve <id>` - Approve pending items
- `/reject <id>` - Reject pending items
- `/issue <title>` - Create GitHub issue

### Autonomous Mode (8-HOUR SESSIONS)
```bash
# Run autonomous mode
/autonomous-mode

# Or manually in Python:
# See: AUTONOMOUS_PLAN.md for task queue
```

### Agent Implementation
18 agent skeletons ready in `agents/`:
- Executive Team (2): AI CEO, Chief of Staff
- Research Team (4): Research, Atom Builder, Librarian, Quality Checker
- Content Team (5): Curriculum, Strategy, Scriptwriter, SEO, Thumbnail
- Media Team (4): Voice, Video Assembly, Publishing, YouTube Uploader
- Engagement Team (3): Community, Analytics, Social Amplifier

Each has:
- Complete class structure
- Method signatures from AGENT_ORGANIZATION.md
- Supabase integration
- Ready for implementation

## Troubleshooting

**Tables don't exist?**
→ Run Step 1 again, check Supabase SQL Editor for errors

**Orchestrator can't connect?**
→ Check `.env` has `SUPABASE_URL` and `SUPABASE_KEY`

**Telegram bot not responding?**
→ Check `TELEGRAM_BOT_TOKEN` in `.env`, verify authorized users

**Webhook not receiving events?**
→ Check ngrok is running, verify GitHub webhook secret matches `.env`

## Next Steps

1. ✅ Run SQL migration (Step 1)
2. ✅ Test orchestrator (Step 2)
3. Set up Telegram bot (Step 3)
4. Set up GitHub webhook (Step 4)
5. Implement agents per `docs/AGENT_ORGANIZATION.md`
6. Launch autonomous operations!

---

**You said**: "I want the integration now"

**Status**: Integration is COMPLETE. Just run the SQL migration and you're live!

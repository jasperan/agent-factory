# KB Observability Platform - Telegram Implementation Guide

**Complete guide to implementing real-time knowledge base monitoring via Telegram**

---

## Table of Contents

1. [Overview](#overview)
2. [What You Get](#what-you-get)
3. [Prerequisites](#prerequisites)
4. [Quick Start (5 Minutes)](#quick-start-5-minutes)
5. [Configuration Options](#configuration-options)
6. [Implementation Patterns](#implementation-patterns)
7. [Notification Modes](#notification-modes)
8. [Production Deployment](#production-deployment)
9. [Troubleshooting](#troubleshooting)
10. [Optional Enhancements](#optional-enhancements)

---

## Overview

The KB Observability Platform monitors your 7-stage knowledge base ingestion pipeline and sends real-time notifications to Telegram whenever sources are processed. You'll know immediately when:

- PDFs are ingested and converted to knowledge atoms
- Forum posts are scraped and validated
- YouTube videos are transcribed and processed
- Any ingestion fails or encounters errors

**Architecture:**
```
Your Ingestion Pipeline
    ↓
IngestionMonitor (tracks 7 stages)
    ├─→ PostgreSQL Database (metrics storage)
    │   └─→ Failover Log (if database down)
    └─→ TelegramNotifier (real-time alerts)
        ├─→ VERBOSE mode: notify every source
        └─→ BATCH mode: 5-min summaries
```

---

## What You Get

### Real-Time Notifications

**Success Notification (VERBOSE mode):**
```
✅ KB Ingestion Complete

Source: example.com/manual.pdf
Atoms: 5 created, 0 failed
Duration: 760ms
Vendor: Siemens
Quality: 85%
Status: success

#ingestion #success
```

**Batch Summary (BATCH mode):**
```
📊 KB Ingestion Summary (Last 5 min)

Sources: 12 processed
✅ Success: 10 (83%)
⚠️ Partial: 2 (17%)

Atoms: 58 created, 3 failed
Avg Duration: 820ms
Avg Quality: 87%

Top Vendors:
  • Siemens (5 sources)
  • Rockwell (4 sources)
  • Mitsubishi (3 sources)

#kb_summary #batch
```

**Error Alert:**
```
❌ KB Ingestion Failed

Source: example.com/broken.pdf
Error: Connection timeout at stage 1 (acquisition)
Duration: 5,200ms

#ingestion #error
```

### Metrics Dashboard (Database)

- Real-time metrics stored in PostgreSQL
- Track success rates, durations, quality scores
- Vendor breakdown and trending
- Stage-by-stage performance analysis

---

## Prerequisites

### 1. Telegram Bot Setup

**Create Bot (2 minutes):**
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow prompts to name your bot
4. Copy the bot token (looks like `7910254197:AAGeEqMI_rvJExOsZVrTLc_0fb26CQKqlHQ`)

**Get Your Chat ID (1 minute):**
1. Start a chat with your new bot
2. Send any message to the bot
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find `"chat":{"id":1234567890}` in the JSON response
5. Copy the chat ID number

### 2. Environment Variables

Add to your `.env` file:
```bash
# Telegram Bot Configuration
ORCHESTRATOR_BOT_TOKEN=7910254197:AAGeEqMI_rvJExOsZVrTLc_0fb26CQKqlHQ
TELEGRAM_ADMIN_CHAT_ID=8445149012

# Notification Settings (Optional)
KB_NOTIFICATION_MODE=BATCH       # or VERBOSE
NOTIFICATION_QUIET_START=23      # 11pm
NOTIFICATION_QUIET_END=7         # 7am
```

### 3. Database Setup (Already Done)

The database schema is already deployed to your VPS PostgreSQL:
- Host: 72.60.175.144
- Database: rivet
- Tables: `ingestion_metrics_realtime`, `ingestion_metrics_hourly`, `ingestion_metrics_daily`

---

## Quick Start (5 Minutes)

### Step 1: Test Your Bot (2 minutes)

```bash
# Test if bot is responding
poetry run python test_telegram_live.py
```

**Expected Output:**
```
Testing TelegramNotifier with live bot...

Sending VERBOSE notification...
✅ Notification sent successfully!

Check Telegram @YourBot for the test message
```

### Step 2: Test Integration (3 minutes)

```bash
# Test full integration (IngestionMonitor + TelegramNotifier)
poetry run python test_monitor_with_notifier.py
```

**Expected Output:**
```
Testing IngestionMonitor with TelegramNotifier integration...

✅ VERBOSE mode test passed
✅ BATCH mode test passed
✅ Database failover working
✅ Telegram notifications sent

Check Telegram for 2 test notifications!
```

### Step 3: Verify Telegram Received Messages

Open Telegram and check your bot chat. You should see:
1. A test notification from Step 1
2. A VERBOSE notification from Step 2
3. A BATCH summary from Step 2

**If you see all 3 messages, you're ready for production!**

---

## Configuration Options

### Notification Modes

**VERBOSE Mode** - Best for development/testing
- Sends notification immediately after each source is processed
- 10-50 messages per hour (depending on ingestion rate)
- Good for debugging and seeing exactly what's happening
- Set: `KB_NOTIFICATION_MODE=VERBOSE`

**BATCH Mode** - Best for production
- Queues notifications and sends 5-minute summaries
- 12 messages per hour (predictable volume)
- Reduces notification fatigue
- Set: `KB_NOTIFICATION_MODE=BATCH`

### Quiet Hours

Prevent notifications during sleep:
```bash
NOTIFICATION_QUIET_START=23  # Start quiet at 11pm
NOTIFICATION_QUIET_END=7     # End quiet at 7am
```

During quiet hours:
- VERBOSE: Notifications queued, sent next morning
- BATCH: Summaries queued, sent next morning

### Rate Limiting

Built-in rate limiting prevents Telegram API throttling:
- Max 20 messages per minute (token bucket algorithm)
- Automatic exponential backoff on 429 errors
- Queue overflow protection (max 1000 queued messages)

---

## Implementation Patterns

### Pattern 1: Basic Integration (Recommended)

**Use Case:** Add monitoring to existing ingestion pipeline

**File:** `agent_factory/workflows/ingestion_chain.py`

```python
import os
from agent_factory.core.database_manager import DatabaseManager
from agent_factory.observability import IngestionMonitor, TelegramNotifier

# Initialize once at module level
notifier = TelegramNotifier(
    bot_token=os.getenv("ORCHESTRATOR_BOT_TOKEN"),
    chat_id=int(os.getenv("TELEGRAM_ADMIN_CHAT_ID", "8445149012")),
    mode=os.getenv("KB_NOTIFICATION_MODE", "BATCH")
)

db = DatabaseManager()
monitor = IngestionMonitor(db, telegram_notifier=notifier)

# Use in your ingestion function
async def ingest_pdf(url: str):
    """Ingest PDF and track with monitoring."""
    async with monitor.track_ingestion(url, "pdf") as session:
        # Stage 1: Acquisition
        content = await download_pdf(url)
        session.record_stage("acquisition", duration_ms=120, success=True)

        # Stage 2: Extraction
        text = await extract_text(content)
        session.record_stage("extraction", duration_ms=80, success=True,
                           metadata={"vendor": "Siemens"})

        # Stage 3: Chunking
        chunks = await chunk_text(text)
        session.record_stage("chunking", duration_ms=40, success=True)

        # Stage 4: Embedding
        embeddings = await generate_embeddings(chunks)
        session.record_stage("embedding", duration_ms=200, success=True)

        # Stage 5: Validation
        atoms = await validate_chunks(chunks)
        session.record_stage("validation", duration_ms=100, success=True,
                           metadata={"avg_quality_score": 0.85})

        # Stage 6: Storage
        stored = await store_atoms(atoms)
        session.record_stage("storage", duration_ms=150, success=True)

        # Stage 7: Indexing
        await index_atoms(stored)
        session.record_stage("indexing", duration_ms=70, success=True)

        # Mark complete
        session.finish(atoms_created=len(atoms), atoms_failed=0)

    # ← Automatic notification sent here (VERBOSE or queued for BATCH)
    return atoms
```

**What Happens:**
1. Monitor tracks each stage timing and metadata
2. On `async with` exit, metrics are queued for database write
3. Notification sent automatically (VERBOSE) or queued (BATCH)
4. If database fails, metrics written to `data/observability/failed_metrics.jsonl`
5. If Telegram fails, pipeline continues (never crashes)

---

### Pattern 2: BATCH Mode with Background Timer

**Use Case:** Production deployment with 5-minute summaries

**File:** `agent_factory/workflows/ingestion_chain.py` or bot startup

```python
import asyncio
import os
from agent_factory.core.database_manager import DatabaseManager
from agent_factory.observability import IngestionMonitor, TelegramNotifier

# Initialize notifier in BATCH mode
notifier = TelegramNotifier(
    bot_token=os.getenv("ORCHESTRATOR_BOT_TOKEN"),
    chat_id=int(os.getenv("TELEGRAM_ADMIN_CHAT_ID")),
    mode="BATCH"
)

db = DatabaseManager()
monitor = IngestionMonitor(db, telegram_notifier=notifier)

# Background task to send batch summaries every 5 minutes
async def batch_notification_timer():
    """Send batch summaries every 5 minutes."""
    while True:
        await asyncio.sleep(300)  # 5 minutes
        try:
            await notifier.send_batch_summary()
        except Exception as e:
            logger.error(f"Batch summary failed: {e}")
            # Continue - don't crash the timer

# Start background task (add to your app startup)
asyncio.create_task(batch_notification_timer())
```

**What Happens:**
1. Ingestion sessions queue data in `notifier._batch_queue`
2. Every 5 minutes, timer calls `send_batch_summary()`
3. Aggregated summary sent to Telegram
4. Queue cleared for next batch

---

### Pattern 3: Error-Only Notifications

**Use Case:** Only notify on failures, silence successes

```python
from agent_factory.observability import TelegramNotifier

class ErrorOnlyNotifier(TelegramNotifier):
    """Custom notifier that only sends error notifications."""

    async def notify_ingestion_complete(self, source_url, atoms_created,
                                       atoms_failed, duration_ms,
                                       vendor=None, quality_score=None,
                                       status="success"):
        """Only notify on errors or partial failures."""
        if status in ["failed", "partial"]:
            await super().notify_ingestion_complete(
                source_url, atoms_created, atoms_failed, duration_ms,
                vendor, quality_score, status
            )
        # Silently ignore success notifications

# Use error-only notifier
notifier = ErrorOnlyNotifier(
    bot_token=os.getenv("ORCHESTRATOR_BOT_TOKEN"),
    chat_id=int(os.getenv("TELEGRAM_ADMIN_CHAT_ID")),
    mode="VERBOSE"  # Still immediate, but only errors
)
```

---

### Pattern 4: Multiple Chat IDs (Team Notifications)

**Use Case:** Send notifications to multiple team members

```python
from agent_factory.observability import TelegramNotifier

class MultiChatNotifier(TelegramNotifier):
    """Send notifications to multiple chat IDs."""

    def __init__(self, bot_token, chat_ids, mode="BATCH", **kwargs):
        super().__init__(bot_token, chat_ids[0], mode, **kwargs)
        self.chat_ids = chat_ids  # List of chat IDs

    async def _send_message(self, text, parse_mode="Markdown"):
        """Send to all chat IDs."""
        for chat_id in self.chat_ids:
            self.chat_id = chat_id
            await super()._send_message(text, parse_mode)

# Use multi-chat notifier
notifier = MultiChatNotifier(
    bot_token=os.getenv("ORCHESTRATOR_BOT_TOKEN"),
    chat_ids=[8445149012, 1234567890, 9876543210],  # Team members
    mode="BATCH"
)
```

---

## Notification Modes

### VERBOSE Mode

**When to Use:**
- Development/testing environments
- Debugging ingestion issues
- Low ingestion volume (< 10 sources/hour)
- Need immediate feedback

**Characteristics:**
- Notification sent immediately after each source
- ~10-50 messages per hour
- Full details for each source
- Good for watching pipeline in real-time

**Enable:**
```bash
KB_NOTIFICATION_MODE=VERBOSE
```

---

### BATCH Mode

**When to Use:**
- Production environments
- High ingestion volume (> 10 sources/hour)
- Reduce notification fatigue
- Overview more important than individual sources

**Characteristics:**
- Queues sessions, sends summary every 5 minutes
- Exactly 12 messages per hour
- Aggregated statistics
- Vendor breakdown and trends

**Enable:**
```bash
KB_NOTIFICATION_MODE=BATCH
```

**Add Background Timer:**
```python
# In bot startup or ingestion_chain.py
import asyncio

async def batch_timer():
    while True:
        await asyncio.sleep(300)
        try:
            await notifier.send_batch_summary()
        except Exception as e:
            logger.error(f"Batch summary failed: {e}")

asyncio.create_task(batch_timer())
```

---

## Production Deployment

### Step 1: Deploy to VPS

**File:** `deploy/vps/kb_monitor.service`

```ini
[Unit]
Description=KB Observability Monitor
After=network.target postgresql.service

[Service]
Type=simple
User=rivet
WorkingDirectory=/opt/agent-factory
Environment="PATH=/opt/agent-factory/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/opt/agent-factory/.venv/bin/python -m agent_factory.workflows.ingestion_chain
Restart=always
RestartSec=10

# Memory limit
MemoryLimit=512M

# CPU limit
CPUQuota=50%

[Install]
WantedBy=multi-user.target
```

**Deploy:**
```bash
# Copy to VPS
scp deploy/vps/kb_monitor.service vps:/etc/systemd/system/

# SSH into VPS
ssh vps

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable kb_monitor
sudo systemctl start kb_monitor

# Check status
sudo systemctl status kb_monitor
```

---

### Step 2: Monitor Logs

```bash
# Real-time logs
ssh vps "journalctl -u kb_monitor -f"

# Check for Telegram errors
ssh vps "journalctl -u kb_monitor -f | grep -i telegram"

# Check for database errors
ssh vps "journalctl -u kb_monitor -f | grep -i database"
```

---

### Step 3: Verify Production

**1. Check Telegram notifications are arriving:**
- VERBOSE: Should see notification within seconds of ingestion
- BATCH: Should see summary every 5 minutes

**2. Check database metrics:**
```bash
# SSH into VPS
ssh vps

# Connect to PostgreSQL
psql -U rivet -d rivet

# Check recent ingestions
SELECT
    source_url,
    atoms_created,
    total_duration_ms,
    status,
    created_at
FROM ingestion_metrics_realtime
ORDER BY created_at DESC
LIMIT 10;
```

**3. Check failover log:**
```bash
# If database was unavailable, check failover log
ssh vps "cat /opt/agent-factory/data/observability/failed_metrics.jsonl | tail -n 5"
```

---

## Troubleshooting

### Problem: No Telegram Notifications

**Diagnosis:**
```bash
# Test bot token
poetry run python test_telegram_live.py
```

**Common Causes:**
1. **Wrong bot token** - Check `.env` file has correct `ORCHESTRATOR_BOT_TOKEN`
2. **Wrong chat ID** - Verify `TELEGRAM_ADMIN_CHAT_ID` is correct
3. **Bot not started** - Send `/start` to your bot in Telegram
4. **Network issues** - Check VPS can reach `api.telegram.org`

**Fix:**
```bash
# Test bot manually
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"

# Should return: {"ok":true,"result":{"id":...}}
```

---

### Problem: Notifications Stop During Quiet Hours

**Expected Behavior:**
- Notifications queued during quiet hours (11pm-7am default)
- Sent as morning summary when quiet period ends

**Verify Configuration:**
```bash
# Check .env
cat .env | grep NOTIFICATION_QUIET
```

**Disable Quiet Hours:**
```bash
# Set quiet hours to never trigger
NOTIFICATION_QUIET_START=25  # Invalid hour = disabled
NOTIFICATION_QUIET_END=25
```

---

### Problem: Database Connection Errors

**Diagnosis:**
```bash
# Check database connection
poetry run python -c "
from agent_factory.core.database_manager import DatabaseManager
db = DatabaseManager()
print(db.health_check_all())
"
```

**Expected Behavior:**
- If database unavailable, metrics written to `data/observability/failed_metrics.jsonl`
- Pipeline continues without crashing
- Telegram notifications still sent

**Verify Failover Log:**
```bash
# Check if failover log exists
ls -lah data/observability/failed_metrics.jsonl

# View recent failures
tail -n 5 data/observability/failed_metrics.jsonl
```

---

### Problem: Rate Limiting Errors

**Symptoms:**
- Error: `429 Too Many Requests`
- Telegram stops responding temporarily

**Cause:**
- Sending > 20 messages per minute
- Usually happens in VERBOSE mode with high ingestion rate

**Fix:**
```bash
# Switch to BATCH mode
KB_NOTIFICATION_MODE=BATCH

# Or reduce notification frequency with error-only pattern
```

**Rate Limit Details:**
- Built-in token bucket: 20 messages/minute
- Automatic exponential backoff on 429 errors
- Will retry after cooldown period

---

### Problem: BATCH Mode Not Sending Summaries

**Diagnosis:**
```bash
# Check if background timer is running
poetry run python -c "
import asyncio
from agent_factory.observability import TelegramNotifier

async def test():
    notifier = TelegramNotifier(
        bot_token='YOUR_TOKEN',
        chat_id=8445149012,
        mode='BATCH'
    )
    # Queue test data
    await notifier.queue_for_batch({
        'source_url': 'test.com/manual.pdf',
        'atoms_created': 5,
        'atoms_failed': 0,
        'duration_ms': 760,
        'status': 'success'
    })
    # Send immediately (don't wait 5 min)
    await notifier.send_batch_summary()
    print('✅ Batch summary sent')

asyncio.run(test())
"
```

**Common Causes:**
1. **Background timer not started** - Add `batch_notification_timer()` to startup
2. **No ingestions in last 5 min** - Queue is empty, no summary sent
3. **Timer crashed** - Check logs for exceptions

**Fix:**
```python
# Add to bot startup or ingestion_chain.py
import asyncio

async def batch_notification_timer():
    while True:
        await asyncio.sleep(300)
        try:
            await notifier.send_batch_summary()
        except Exception as e:
            logger.error(f"Batch summary failed: {e}")
            # Don't crash - continue timer

# Start background task
asyncio.create_task(batch_notification_timer())
```

---

## Optional Enhancements

### Phase 2.4: Telegram Commands

Add interactive commands to query metrics from Telegram:

**Commands to Implement:**
- `/stats` - Show ingestion statistics (last 24h)
- `/kb_status` - Show KB health (atom count, success rate)
- `/ingestion_live` - Show last 10 ingestions

**File:** `agent_factory/integrations/telegram/orchestrator_bot.py`

```python
from telegram import Update
from telegram.ext import ContextTypes
from agent_factory.core.database_manager import DatabaseManager
from agent_factory.observability import IngestionMonitor

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show KB ingestion statistics."""
    db = DatabaseManager()
    monitor = IngestionMonitor(db)

    # Get 24-hour stats
    stats = monitor.get_stats_summary(hours=24)

    message = f"""
📊 *KB Ingestion Stats (Last 24h)*

Sources: {stats['total_sources']:,}
Success Rate: {stats['success_rate']:.0%}
Atoms Created: {stats['atoms_created']:,}
Avg Duration: {stats['avg_duration_ms']}ms

Top Vendors:
{format_vendor_list(stats['active_vendors'])}

_Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_
"""
    await update.message.reply_text(message, parse_mode="Markdown")

# Register command
application.add_handler(CommandHandler("stats", stats_command))
```

**Usage:**
```
User: /stats
Bot: 📊 KB Ingestion Stats (Last 24h)
     Sources: 142
     Success Rate: 94%
     Atoms Created: 687
     ...
```

---

### Custom Notification Formats

**HTML Formatting:**
```python
class HTMLNotifier(TelegramNotifier):
    """Use HTML instead of Markdown."""

    async def notify_ingestion_complete(self, source_url, atoms_created,
                                       atoms_failed, duration_ms,
                                       vendor=None, quality_score=None,
                                       status="success"):
        """Send HTML-formatted notification."""
        if status == "success":
            icon = "✅"
        elif status == "partial":
            icon = "⚠️"
        else:
            icon = "❌"

        message = f"""
<b>{icon} KB Ingestion {status.title()}</b>

<b>Source:</b> <code>{source_url}</code>
<b>Atoms:</b> {atoms_created} created, {atoms_failed} failed
<b>Duration:</b> {self._format_duration(duration_ms)}
"""
        if vendor:
            message += f"<b>Vendor:</b> {vendor}\n"
        if quality_score:
            message += f"<b>Quality:</b> {quality_score:.0%}\n"

        await self._send_message(message, parse_mode="HTML")
```

---

### Metrics Dashboard (Gradio)

**Future Enhancement:** Web UI for real-time metrics visualization

```python
import gradio as gr
from agent_factory.core.database_manager import DatabaseManager
from agent_factory.observability import IngestionMonitor

def get_metrics_dashboard():
    """Generate metrics dashboard."""
    db = DatabaseManager()
    monitor = IngestionMonitor(db)

    # Get stats
    stats_24h = monitor.get_stats_summary(hours=24)
    stats_7d = monitor.get_stats_summary(hours=168)

    return {
        "24h_sources": stats_24h['total_sources'],
        "24h_success_rate": f"{stats_24h['success_rate']:.0%}",
        "7d_atoms_created": stats_7d['atoms_created'],
        # ... more metrics
    }

# Create Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# KB Observability Dashboard")

    with gr.Row():
        sources_24h = gr.Number(label="Sources (24h)")
        success_rate = gr.Textbox(label="Success Rate")
        atoms_created = gr.Number(label="Atoms Created (7d)")

    refresh_btn = gr.Button("Refresh")
    refresh_btn.click(get_metrics_dashboard, outputs=[sources_24h, success_rate, atoms_created])

demo.launch(server_name="0.0.0.0", server_port=7860)
```

**Access:** `http://your-vps:7860`

---

## Reference

### Key Files

**Implementation:**
- `agent_factory/observability/ingestion_monitor.py` - Monitor class (470 lines)
- `agent_factory/observability/telegram_notifier.py` - Notifier class (424 lines)
- `agent_factory/observability/__init__.py` - Package exports

**Testing:**
- `test_ingestion_monitor.py` - Monitor integration test
- `test_telegram_notifier.py` - Notifier test suite
- `test_telegram_live.py` - Live bot test
- `test_monitor_with_notifier.py` - Full integration test

**Documentation:**
- `docs/SYSTEM_MAP_OBSERVABILITY.md` - Complete architecture
- `.claude/memory/CONTINUE_HERE_OBSERVABILITY.md` - Resume guide
- `.claude/memory/PHASE_2.3_COMPLETE_SESSION.md` - Implementation log

**Failover:**
- `data/observability/failed_metrics.jsonl` - Database write failures
- `data/observability/failed_telegram_sends.jsonl` - Telegram send failures (if logging enabled)

### Environment Variables

```bash
# Required
ORCHESTRATOR_BOT_TOKEN=7910254197:AAGeEqMI_rvJExOsZVrTLc_0fb26CQKqlHQ
TELEGRAM_ADMIN_CHAT_ID=8445149012

# Optional
KB_NOTIFICATION_MODE=BATCH              # VERBOSE or BATCH
NOTIFICATION_QUIET_START=23             # Quiet start (24h format)
NOTIFICATION_QUIET_END=7                # Quiet end (24h format)

# Database (already configured)
VPS_KB_HOST=72.60.175.144
VPS_KB_PORT=5432
VPS_KB_USER=rivet
VPS_KB_PASSWORD=rivet_factory_2025!
VPS_KB_DATABASE=rivet
```

### Validation Commands

```bash
# Test imports
poetry run python -c "from agent_factory.observability import IngestionMonitor, TelegramNotifier; print('OK')"

# Test live bot
poetry run python test_telegram_live.py

# Test integration
poetry run python test_monitor_with_notifier.py

# Check database
poetry run python -c "from agent_factory.core.database_manager import DatabaseManager; db = DatabaseManager(); print(db.health_check_all())"

# Check failover log
ls -lah data/observability/failed_metrics.jsonl
```

---

## Next Steps

1. **Test Your Bot** - Run `poetry run python test_telegram_live.py`
2. **Test Integration** - Run `poetry run python test_monitor_with_notifier.py`
3. **Choose Mode** - Set `KB_NOTIFICATION_MODE=BATCH` or `VERBOSE` in `.env`
4. **Integrate Pipeline** - Add monitoring to your ingestion functions (Pattern 1)
5. **Deploy to VPS** - Use systemd service for production
6. **Monitor Logs** - Watch Telegram for notifications
7. **Optional: Add Commands** - Implement `/stats`, `/kb_status` commands (Phase 2.4)

---

## Support

**Documentation:**
- `docs/SYSTEM_MAP_OBSERVABILITY.md` - Complete architecture
- `.claude/memory/CONTINUE_HERE_OBSERVABILITY.md` - Implementation status

**Troubleshooting:**
- Check `.env` file has correct tokens
- Verify bot is started in Telegram (`/start`)
- Check VPS can reach `api.telegram.org`
- Review logs: `journalctl -u kb_monitor -f`

**Status:** ✅ PRODUCTION READY

---

**Last Updated:** 2025-12-25
**Version:** Phase 2.3 Complete
**Status:** Production Ready

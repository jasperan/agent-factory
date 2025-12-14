# Agent Factory - Quick Start Deployment Guide

**GOAL:** Deploy to Render.com in 2 hours (by 6 AM)
**TIME NOW:** Check clock
**DEADLINE:** 6:00 AM

---

## CRITICAL: What You Need RIGHT NOW

### 1. Open Your `.env` File

Location: `C:\Users\hharp\OneDrive\Desktop\Agent Factory\.env`

**COPY THESE VALUES** (you'll need them in Render dashboard):

```bash
# From your .env file:
TELEGRAM_BOT_TOKEN=<COPY_THIS>
TELEGRAM_ADMIN_CHAT_ID=<COPY_THIS>
AUTHORIZED_TELEGRAM_USERS=<COPY_THIS>

# Database
SUPABASE_URL=<COPY_THIS>
SUPABASE_KEY=<COPY_THIS>
NEON_DB_URL=<COPY_THIS>

# LLM (at least ONE)
OPENAI_API_KEY=<COPY_THIS>
ANTHROPIC_API_KEY=<COPY_THIS>
```

---

## STEP 1: Render.com Account Setup (5 minutes)

1. **Go to:** https://dashboard.render.com/register
2. **Sign up** with GitHub account (fastest)
3. **Connect GitHub** repository: `Agent-Factory`
4. **Authorize Render** to access repository

---

## STEP 2: Deploy Telegram Bot Web Service (30 minutes)

### 2.1 Create Service

1. **Render Dashboard** → Click **"New +"** button (top right)
2. Select **"Web Service"**
3. Find **"Agent-Factory"** repository → Click **"Connect"**

### 2.2 Configure Service

Fill in these fields:

| Field | Value |
|-------|-------|
| **Name** | `agent-factory-telegram-bot` |
| **Region** | Oregon (us-west) |
| **Branch** | `main` |
| **Root Directory** | (leave blank) |
| **Runtime** | Docker |
| **Instance Type** | Free |
| **Docker Build Context** | (leave blank) |
| **Dockerfile Path** | (leave blank - auto-detect) |

### 2.3 Advanced Settings

Expand **"Advanced"** section:

| Field | Value |
|-------|-------|
| **Health Check Path** | `/health` |
| **Auto-Deploy** | Yes (recommended) |

### 2.4 Environment Variables

Click **"Environment"** tab → **"Add Environment Variable"**

**Paste each line ONE AT A TIME:**

```bash
TELEGRAM_BOT_TOKEN=<YOUR_VALUE_FROM_ENV>
TELEGRAM_ADMIN_CHAT_ID=<YOUR_VALUE_FROM_ENV>
AUTHORIZED_TELEGRAM_USERS=<YOUR_VALUE_FROM_ENV>
SUPABASE_URL=<YOUR_VALUE_FROM_ENV>
SUPABASE_KEY=<YOUR_VALUE_FROM_ENV>
NEON_DB_URL=<YOUR_VALUE_FROM_ENV>
DATABASE_PROVIDER=neon
OPENAI_API_KEY=<YOUR_VALUE_FROM_ENV>
ANTHROPIC_API_KEY=<YOUR_VALUE_FROM_ENV>
VOICE_MODE=edge
EDGE_VOICE=en-US-GuyNeural
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4o
PYTHONUNBUFFERED=1
LOG_LEVEL=INFO
```

**OR Bulk Import:**
- Click **"Add from .env"**
- Paste ALL variables at once
- Click **"Save"**

### 2.5 Deploy!

1. Click **"Create Web Service"** button (bottom)
2. **WAIT 3-5 MINUTES** for build to complete
3. **Watch logs** in real-time (automatic)

**Look for these SUCCESS messages:**
```
✅ Bot lock acquired
✅ Health check endpoint: http://localhost:9876/health
✅ Bot is running (polling mode)
```

### 2.6 Get Your Service URL

After deployment completes:
- **Service URL:** https://agent-factory-telegram-bot.onrender.com
- **Copy this URL** (you'll need it in Step 3)

### 2.7 Test Health Endpoint

Open in browser OR use curl:
```
https://agent-factory-telegram-bot.onrender.com/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "pid": 7,
  "uptime_seconds": 42,
  "timestamp": "2025-12-13T..."
}
```

**If you see this, STEP 2 is COMPLETE! ✅**

---

## STEP 3: Set Telegram Webhook (5 minutes)

### 3.1 Open Command Prompt / Terminal

```bash
# Windows PowerShell or cmd
# Mac/Linux: Terminal
```

### 3.2 Set Webhook

**Replace `<YOUR_BOT_TOKEN>` with your actual token from .env:**

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" -H "Content-Type: application/json" -d "{\"url\": \"https://agent-factory-telegram-bot.onrender.com/telegram-webhook\", \"max_connections\": 40, \"allowed_updates\": [\"message\", \"callback_query\"]}"
```

**Expected Response:**
```json
{"ok": true, "result": true, "description": "Webhook was set"}
```

### 3.3 Verify Webhook

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

**Expected Response:**
```json
{
  "ok": true,
  "result": {
    "url": "https://agent-factory-telegram-bot.onrender.com/telegram-webhook",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "max_connections": 40
  }
}
```

### 3.4 Test Bot in Telegram

**Open Telegram app → Find your bot → Send:**
```
/start
```

**Expected:** Bot responds within 1-2 seconds

**If bot responds, STEP 3 is COMPLETE! ✅**

---

## STEP 4: Deploy Knowledge Base Cron Job (30 minutes)

### 4.1 Create Cron Job

1. **Render Dashboard** → **"New +"** → **"Cron Job"**
2. Select **"Agent-Factory"** repository again
3. Click **"Connect"**

### 4.2 Configure Cron Job

| Field | Value |
|-------|-------|
| **Name** | `agent-factory-kb-builder` |
| **Region** | Oregon (us-west) |
| **Branch** | `main` |
| **Runtime** | Docker |
| **Docker Command** | `poetry run python scripts/automation/scheduler_kb_daily.py` |
| **Schedule** | `0 2 * * *` (2 AM UTC daily) |
| **Instance Type** | Free |

### 4.3 Environment Variables

**COPY ALL variables from Step 2** (same exact list)

**Fastest way:**
- Go to your Web Service settings
- Copy all environment variables
- Paste into Cron Job environment variables

### 4.4 Test Manually (IMPORTANT!)

**DO NOT wait for 2 AM tomorrow!**

1. After creating cron job, click **"Trigger Run"** button
2. Watch logs (will take 15-30 minutes)
3. Look for SUCCESS messages:
   ```
   PHASE 1 COMPLETE: PDFs scraped
   PHASE 2 COMPLETE: Atoms generated
   PHASE 3 COMPLETE: Uploaded to database
   PHASE 4 COMPLETE: Validation passed
   PHASE 6 COMPLETE: Quality checked
   Telegram notification sent
   ```

4. **Check Telegram:** You should receive notification with full report

5. **Check Database (Supabase):**
   - Go to: https://supabase.com/dashboard/project/<YOUR_PROJECT>/editor
   - Run query:
     ```sql
     SELECT COUNT(*) FROM knowledge_atoms WHERE created_at > NOW() - INTERVAL '1 day';
     ```
   - **Expected:** Shows new atoms added (10-200 depending on PDF sources)

**If manual trigger succeeds, STEP 4 is COMPLETE! ✅**

---

## STEP 5: Set Up UptimeRobot Monitoring (20 minutes)

### 5.1 Automated Setup (Recommended)

**Run the setup helper script:**

```bash
python scripts/deployment/setup_uptimerobot.py --service-url https://agent-factory-telegram-bot.onrender.com
```

This script will guide you through:
- Account creation
- Monitor configuration
- Alert setup
- Verification

**Optional: If you have UptimeRobot API key:**

```bash
python scripts/deployment/setup_uptimerobot.py --service-url <URL> --api-key <YOUR_API_KEY>
```

### 5.2 Manual Setup (Alternative)

If you prefer manual configuration:

#### A. Create Account

1. Go to: https://uptimerobot.com/signUp
2. **Sign up** (free - no credit card)
3. **Verify email**
4. **Log in** to dashboard

#### B. Add Bot Health Monitor

1. Click **"Add New Monitor"**
2. Fill in:

| Field | Value |
|-------|-------|
| **Monitor Type** | HTTP(s) |
| **Friendly Name** | Agent Factory Bot |
| **URL (or IP)** | `https://agent-factory-telegram-bot.onrender.com/health` |
| **Monitoring Interval** | 5 minutes |
| **Monitor Timeout** | 30 seconds |

3. Click **"Create Monitor"**

#### C. Add Telegram Alert

1. Go to **"My Settings"** → **"Alert Contacts"**
2. Click **"Add Alert Contact"**
3. Select **"Webhook"**
4. Fill in:

| Field | Value |
|-------|-------|
| **Friendly Name** | Telegram Notifications |
| **Webhook URL** | `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage?chat_id=<YOUR_CHAT_ID>&text=ALERT:%20Bot%20is%20down` |

5. Click **"Create Alert Contact"**

#### D. Test Alert

1. **Pause** monitor temporarily
2. Wait 10 minutes
3. Check Telegram - should receive alert
4. **Unpause** monitor
5. Should receive "bot is up" notification

### 5.3 Verify Monitoring

**Run verification script:**

```bash
python scripts/deployment/verify_monitoring.py --service-url https://agent-factory-telegram-bot.onrender.com
```

**Expected output:**
```
PASS: All 5 health checks passed
PASS: Monitor is active and reporting 'Up'
PASS: 1 alert contact(s) configured
PASS: Optimal interval (5 min)

SUCCESS: All monitoring checks passed
```

**If all checks pass, STEP 5 is COMPLETE! ✅**

---

## STEP 6: Run Full Validation (15 minutes)

### 6.1 Automated Validation Suite

**Run comprehensive validation:**

```bash
python scripts/deployment/run_full_validation.py --service-url https://agent-factory-telegram-bot.onrender.com
```

This validates:
- Environment variables
- Health endpoint stability (10 consecutive checks)
- Webhook configuration
- Database connection and knowledge base
- Monitoring status (if UptimeRobot API key provided)

**Expected output:**
```
VALIDATION SUMMARY
==========================================
Total Checks:    15
Passed:          15
Failed:          0
Warnings:        0
Readiness Score: 100.0%

STATUS: DEPLOYMENT READY

All critical systems validated successfully!
The deployment is production-ready.
```

### 6.2 Generate Deployment Report

**Create documentation:**

```bash
python scripts/deployment/generate_deployment_report.py --service-url https://agent-factory-telegram-bot.onrender.com
```

**Output:** `DEPLOYMENT_REPORT.md` with complete deployment details

**If validation passes, STEP 6 is COMPLETE! ✅**

---

## VERIFICATION CHECKLIST

Before calling it complete, verify ALL of these:

### Bot Service
- [ ] Render web service status: LIVE
- [ ] Health endpoint returns 200 OK
- [ ] Bot responds to `/start` command in Telegram
- [ ] Response time < 2 seconds

### Cron Job
- [ ] Manual trigger completed successfully
- [ ] Telegram notification received
- [ ] New atoms in database (Supabase query shows increase)
- [ ] Logs show all 6 phases complete

### Monitoring
- [ ] UptimeRobot monitor shows "Up" status
- [ ] Alert test successful (Telegram notification received)
- [ ] Dashboard accessible: https://uptimerobot.com/dashboard

### Webhook
- [ ] Webhook URL set correctly
- [ ] `getWebhookInfo` shows correct URL
- [ ] `pending_update_count` is 0

---

## TROUBLESHOOTING

### Bot Not Responding

**Check:**
1. Render logs for errors
2. Health endpoint returns 200 OK
3. Webhook set correctly (`getWebhookInfo`)
4. TELEGRAM_BOT_TOKEN is correct

**Fix:**
- Re-deploy service in Render dashboard
- Re-set webhook (Step 3)

### Cron Job Fails

**Check:**
1. Render cron job logs
2. Environment variables set correctly
3. Database connection working

**Fix:**
- Verify all environment variables match web service
- Check Supabase/Neon database is accessible

### Free Tier Bot Sleeps

**Check:**
- UptimeRobot pinging every 5 minutes?
- Monitor status: Active?

**Fix:**
- Verify monitor interval is 5 minutes (NOT 15+)
- Add second monitor as backup (cron-job.org)

---

## FINAL STATUS

**When ALL steps are complete:**

✅ **Telegram Bot:** https://agent-factory-telegram-bot.onrender.com
✅ **Cron Job:** Runs daily at 2 AM UTC
✅ **Monitoring:** UptimeRobot active (5-min checks)
✅ **Bot Commands:** Responding in <2 seconds
✅ **Knowledge Base:** Growing automatically daily

**DEPLOYMENT TIME:** ~2 hours
**MONTHLY COST:** $1 (Render cron job)
**UPTIME TARGET:** 99.9%

---

## NEXT STEPS (After Deployment)

**Tomorrow (24 hours after deployment):**
- Check UptimeRobot dashboard → Should show 100% uptime
- Check Render cron job logs → Should have run at 2 AM UTC
- Check Supabase → Knowledge base should have grown (+50-200 atoms)

**Next Week:**
- Review Render costs (should be $0-1)
- Review knowledge base growth (target: +700 atoms/week)
- Review bot usage logs
- Consider upgrading to paid tier if needed

---

**QUESTIONS? ISSUES?**

- Render Docs: https://render.com/docs
- Telegram Bot API: https://core.telegram.org/bots/api
- UptimeRobot Help: https://uptimerobot.com/help

---

**DEADLINE CHECK:** Look at clock. If before 6 AM, you're on track! ✅

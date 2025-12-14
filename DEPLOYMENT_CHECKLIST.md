# Agent Factory - Deployment Checklist

**Target Deadline:** 6:00 AM
**Deployment Platform:** Render.com (24/7 Production)
**Start Time:** <TIMESTAMP_START>

---

## Pre-Deployment (Phase 1)

- [ ] **All 5 worktrees created**
  - [ ] deployment-cron
  - [ ] deployment-monitoring
  - [ ] deployment-docs
  - [ ] deployment-backup
  - [ ] main (existing)

- [ ] **Environment variables prepared**
  - [ ] render-env-vars.txt created (from .env)
  - [ ] render-env-vars.txt added to .gitignore
  - [ ] All CRITICAL vars validated:
    - [ ] TELEGRAM_BOT_TOKEN
    - [ ] TELEGRAM_ADMIN_CHAT_ID
    - [ ] AUTHORIZED_TELEGRAM_USERS
    - [ ] SUPABASE_URL
    - [ ] SUPABASE_KEY
    - [ ] NEON_DB_URL
    - [ ] OPENAI_API_KEY or ANTHROPIC_API_KEY

- [ ] **Pre-flight validation**
  - [ ] `python scripts/deployment_check.py` passes
  - [ ] Docker build successful
  - [ ] Local docker-compose test passes
  - [ ] Health endpoint responds: http://localhost:9876/health

---

## Render.com Deployment (Phase 2)

### Web Service: Telegram Bot

- [ ] **Service created**
  - [ ] Repository connected (Agent-Factory)
  - [ ] Branch: main
  - [ ] Runtime: Docker
  - [ ] Instance type: Free

- [ ] **Configuration**
  - [ ] Name: agent-factory-telegram-bot
  - [ ] Region: Oregon (us-west)
  - [ ] Health check path: /health
  - [ ] Environment variables: All from render-env-vars.txt

- [ ] **Deployment successful**
  - [ ] Build logs show success
  - [ ] "Bot lock acquired" in logs
  - [ ] "Bot is running" in logs
  - [ ] Health endpoint accessible
  - [ ] Service URL: https://agent-factory-telegram-bot.onrender.com

- [ ] **Health check passing**
  - [ ] `curl https://agent-factory-telegram-bot.onrender.com/health`
  - [ ] Returns: `{"status": "healthy", "pid": ..., "uptime_seconds": ...}`

### Cron Job: Knowledge Base Builder

- [ ] **Job created**
  - [ ] Repository: Agent-Factory
  - [ ] Branch: main
  - [ ] Runtime: Docker
  - [ ] Command: `poetry run python scripts/automation/scheduler_kb_daily.py`

- [ ] **Configuration**
  - [ ] Name: agent-factory-kb-builder
  - [ ] Region: Oregon (us-west)
  - [ ] Schedule: `0 2 * * *` (2 AM UTC daily)
  - [ ] Environment variables: Same as web service

- [ ] **Manual test trigger**
  - [ ] Clicked "Trigger Run"
  - [ ] Logs show all 6 phases complete:
    - [ ] PHASE 1: PDF Scraping
    - [ ] PHASE 2: Atom Building
    - [ ] PHASE 3: Supabase Upload
    - [ ] PHASE 4: Validation
    - [ ] PHASE 6: Quality Check
    - [ ] Telegram notification sent
  - [ ] Telegram notification received
  - [ ] New atoms in database (Supabase query)

---

## Telegram Webhook (Phase 3)

- [ ] **Webhook set**
  - [ ] `curl` command executed successfully
  - [ ] Response: `{"ok": true, "result": true}`

- [ ] **Webhook verified**
  - [ ] `getWebhookInfo` shows correct URL
  - [ ] `pending_update_count`: 0
  - [ ] `max_connections`: 40

- [ ] **Bot responding**
  - [ ] Sent `/start` → received response
  - [ ] Sent `/help` → received response
  - [ ] Sent `/status` → received response
  - [ ] Sent `/kb_stats` → received response
  - [ ] Response time < 2 seconds

---

## Monitoring Setup (Phase 4)

### Automated Setup (Recommended)

- [ ] **Run setup script**
  - [ ] `python scripts/deployment/setup_uptimerobot.py --service-url <URL>`
  - [ ] Followed interactive prompts
  - [ ] Account created (if new)
  - [ ] Monitor configured
  - [ ] Alert contact added

- [ ] **Run verification script**
  - [ ] `python scripts/deployment/verify_monitoring.py --service-url <URL>`
  - [ ] All checks passed:
    - [ ] Health endpoint reachability (5 checks)
    - [ ] UptimeRobot monitor status: Up
    - [ ] Alert contacts configured
    - [ ] Monitoring interval: 5 minutes

### Manual Setup (Alternative)

- [ ] **Account created**
  - [ ] https://uptimerobot.com

- [ ] **Bot health monitor**
  - [ ] Monitor type: HTTP(s)
  - [ ] Name: Agent Factory Bot
  - [ ] URL: https://agent-factory-telegram-bot.onrender.com/health
  - [ ] Interval: 5 minutes
  - [ ] Timeout: 30 seconds
  - [ ] Status: Up

- [ ] **Telegram alert channel**
  - [ ] Webhook configured
  - [ ] Test alert sent and received

- [ ] **Heartbeat monitor** (Optional)
  - [ ] Monitor type: Heartbeat
  - [ ] Name: KB Builder Cron
  - [ ] Interval: 1440 minutes (24 hours)
  - [ ] Alert threshold: 30 hours
  - [ ] Heartbeat URL copied

- [ ] **Heartbeat integrated** (Optional)
  - [ ] Added to `scripts/automation/scheduler_kb_daily.py`
  - [ ] Committed and pushed
  - [ ] Redeployed to Render

---

## Validation & Testing (Phase 5)

### Bot Functionality

- [ ] **10 test commands sent**
  - [ ] `/start` - response received
  - [ ] `/help` - response received
  - [ ] `/status` - response received
  - [ ] `/agents` - response received
  - [ ] `/metrics` - response received
  - [ ] `/kb_stats` - response received
  - [ ] `/ask What is a PLC?` - response received
  - [ ] `/health` - response received
  - [ ] Random message 1 - response received
  - [ ] Random message 2 - response received

- [ ] **All responses < 2 seconds**
- [ ] **No errors in Render logs**

### Health Endpoint

- [ ] **5-minute continuous test**
  - [ ] Checked every 30 seconds (10 checks)
  - [ ] All checks returned 200 OK
  - [ ] All checks showed `status: healthy`
  - [ ] PID consistent (no restarts)

### Cron Job

- [ ] **Supabase verification**
  - [ ] Total atoms increased
  - [ ] New atoms added today (SQL query)
  - [ ] 100% embedding coverage
  - [ ] No failed uploads

### UptimeRobot

- [ ] **Dashboard shows "Up"**
- [ ] **Alert test completed**
  - [ ] Paused monitor
  - [ ] Received alert in Telegram
  - [ ] Unpaused monitor
  - [ ] Received "up" notification

---

## Documentation (Phase 6)

- [ ] **DEPLOYMENT_REPORT.md created**
  - [ ] Service URLs documented
  - [ ] Monitoring links added
  - [ ] Credentials location noted
  - [ ] Validation results recorded
  - [ ] Next steps outlined
  - [ ] Rollback procedure documented

- [ ] **README.md updated**
  - [ ] Production deployment badge added
  - [ ] Service status section added
  - [ ] Links to deployment docs

- [ ] **Committed and pushed**
  - [ ] Branch: deployment-docs
  - [ ] Commit message: "docs: Add production deployment report"

---

## Backup & Failover (Phase 7)

### Railway.app Backup

- [ ] **Account created**
- [ ] **Project deployed**
  - [ ] Repository: Agent-Factory
  - [ ] Branch: main
  - [ ] Service: agent-factory-backup-bot
  - [ ] Environment: Copied from Render
  - [ ] Status: STANDBY (not active)

### Database Failover

- [ ] **Test script created**
  - [ ] `scripts/test_database_failover.py`
- [ ] **Failover tested**
  - [ ] Neon (primary) health check: PASS
  - [ ] Supabase (backup) health check: PASS
  - [ ] Railway (tertiary) health check: PASS

---

## Final Checklist & Go-Live (Phase 8)

### All Checks Complete

- [ ] Pre-flight check: PASSED
- [ ] Render Web Service: OPERATIONAL
- [ ] Render Cron Job: OPERATIONAL
- [ ] Telegram webhook: VERIFIED
- [ ] UptimeRobot monitors: ACTIVE
- [ ] Bot commands: RESPONDING
- [ ] Cron job test: SUCCESSFUL
- [ ] Telegram notifications: WORKING
- [ ] Health endpoint: ACCESSIBLE (5 consecutive checks)
- [ ] Railway backup: DEPLOYED (standby)
- [ ] Database failover: TESTED
- [ ] Documentation: UPDATED

### Go-Live Notification Sent

- [ ] **Telegram message sent to admin**
  - [ ] Deployment status: OPERATIONAL
  - [ ] Service URLs included
  - [ ] Next actions outlined
  - [ ] Monitoring links provided

### Post-Deployment Tasks

- [ ] **24-hour stability monitoring** (next day)
  - [ ] Check UptimeRobot dashboard at 24 hours
  - [ ] Verify cron job runs successfully at 2 AM UTC tomorrow
  - [ ] Check Supabase for knowledge base growth (+100 atoms expected)
  - [ ] Review Render logs for errors

- [ ] **First week monitoring**
  - [ ] Daily check of UptimeRobot (target: 99.9% uptime)
  - [ ] Daily verification of cron job success
  - [ ] Weekly review of knowledge base growth
  - [ ] Weekly review of Render costs (target: $1/month)

---

## Deployment Status

**Current Phase:** <CURRENT_PHASE>
**Progress:** <X>/9 phases complete
**Estimated Completion:** <TIME>
**Blockers:** <NONE or LIST>

---

## Emergency Contacts

- **Render Support:** https://render.com/support
- **Telegram Bot API:** https://core.telegram.org/bots/api
- **UptimeRobot Support:** https://uptimerobot.com/help
- **Database (Neon):** https://neon.tech/docs
- **Database (Supabase):** https://supabase.com/docs

---

**Last Updated:** <TIMESTAMP>
**Updated By:** <NAME>

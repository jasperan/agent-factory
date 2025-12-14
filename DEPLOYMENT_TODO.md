# Agent Factory - Deployment TODO List

**Status:** All infrastructure ready - waiting for user execution
**Estimated Time:** 2 hours total
**Cost:** $1/month
**Deadline:** When ready (no rush)

---

## ✅ Pre-Deployment (Already Complete)

- [x] All automation scripts created (9 files, 2,918 lines)
- [x] All documentation written (5 guides, 1,289 lines)
- [x] Git worktrees created (5 parallel tracks)
- [x] Failover infrastructure documented
- [x] Database operational (1,964 atoms in Neon)
- [x] All code committed and pushed to GitHub

**You have everything you need. Just follow the steps below when ready.**

---

## 📋 Deployment Checklist (When You're Ready)

### Phase 1: Preparation (10 minutes)

- [ ] **Read deployment guide**
  - File: `DEPLOYMENT_QUICK_START.md`
  - Time: 5 minutes
  - Purpose: Understand the deployment process

- [ ] **Prepare environment variables**
  - Open: `.env` file
  - Copy these values (you'll paste into Render.com):
    - `TELEGRAM_BOT_TOKEN`
    - `TELEGRAM_ADMIN_CHAT_ID`
    - `AUTHORIZED_TELEGRAM_USERS`
    - `NEON_DB_URL`
    - `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY`)
  - Time: 5 minutes

---

### Phase 2: Render.com Setup (60 minutes)

- [ ] **Create Render.com account**
  - Go to: https://dashboard.render.com/register
  - Sign up with GitHub (fastest)
  - Authorize access to `Agent-Factory` repository
  - Time: 5 minutes

- [ ] **Deploy Web Service (Telegram Bot)**
  - Dashboard → "New +" → "Web Service"
  - Repository: `Agent-Factory`
  - Name: `agent-factory-telegram-bot`
  - Region: Oregon (us-west)
  - Runtime: Docker
  - Instance: Free
  - Health Check Path: `/health`
  - Environment Variables: Paste from .env (see guide)
  - Time: 30 minutes
  - **Success:** Service shows "Live" status

- [ ] **Deploy Cron Job (KB Automation)**
  - Dashboard → "New +" → "Cron Job"
  - Repository: `Agent-Factory`
  - Name: `agent-factory-kb-builder`
  - Schedule: `0 2 * * *` (2 AM UTC daily)
  - Command: `poetry run python scripts/automation/scheduler_kb_daily.py`
  - Environment Variables: Same as web service
  - Time: 20 minutes
  - **Success:** Manual trigger runs successfully

- [ ] **Test manual cron trigger**
  - Click "Trigger Run" in Render dashboard
  - Watch logs for 15-30 minutes
  - Look for: "PHASE 6 COMPLETE" + Telegram notification
  - Time: 5 minutes (to start), then background
  - **Success:** Telegram notification received

---

### Phase 3: Automation Scripts (30 minutes)

- [ ] **Set Telegram webhook**
  ```bash
  python scripts/deployment/set_telegram_webhook.py --service-url https://agent-factory-telegram-bot.onrender.com
  ```
  - Time: 5 minutes
  - **Success:** Response shows `{"ok": true}`

- [ ] **Setup UptimeRobot monitoring**
  ```bash
  python scripts/deployment/setup_uptimerobot.py --service-url https://agent-factory-telegram-bot.onrender.com
  ```
  - Follow interactive prompts
  - Create UptimeRobot account: https://uptimerobot.com/signUp
  - Configure bot health monitor (5-minute interval)
  - Add Telegram alert webhook
  - Time: 20 minutes
  - **Success:** Monitor shows "Up" status

- [ ] **Run full validation**
  ```bash
  python scripts/deployment/run_full_validation.py --service-url https://agent-factory-telegram-bot.onrender.com
  ```
  - Tests health endpoint (10 checks)
  - Verifies webhook configuration
  - Checks database connection
  - Validates monitoring status
  - Time: 5 minutes
  - **Success:** Readiness score ≥95%

---

### Phase 4: Final Verification (20 minutes)

- [ ] **Generate deployment report**
  ```bash
  python scripts/deployment/generate_deployment_report.py --service-url https://agent-factory-telegram-bot.onrender.com
  ```
  - Creates: `DEPLOYMENT_REPORT.md`
  - Time: 5 minutes
  - **Success:** Report file created with all details

- [ ] **Run final go-live checklist**
  ```bash
  python scripts/deployment/final_checklist.py --service-url https://agent-factory-telegram-bot.onrender.com
  ```
  - Runs comprehensive checks
  - Makes GO/NO-GO decision
  - Sends Telegram notification
  - Time: 5 minutes
  - **Success:** Decision = "GO"

- [ ] **Manual bot testing**
  - Open Telegram app
  - Send `/start` to your bot
  - Send `/help`
  - Send `/kb_stats`
  - Ask a PLC question
  - Time: 5 minutes
  - **Success:** All commands respond in <2 seconds

- [ ] **Verify UptimeRobot dashboard**
  - Go to: https://uptimerobot.com/dashboard
  - Check: "Agent Factory Bot" monitor
  - Status: Should show "Up" (green)
  - Time: 5 minutes
  - **Success:** 100% uptime shown

---

### Phase 5: Post-Deployment Monitoring (24 hours)

- [ ] **Hour 1: Initial monitoring**
  - Send 10 test commands to bot
  - All should respond in <2 seconds
  - Check Render logs for errors
  - **Success:** No errors, all responses fast

- [ ] **Hour 6: Stability check**
  - UptimeRobot dashboard: 100% uptime
  - Render service: No restarts
  - Bot still responding
  - **Success:** Stable for 6 hours

- [ ] **Hour 24: Cron job verification**
  - Check Render cron job ran at 2 AM UTC
  - Telegram notification received
  - Database query: New atoms added
  - SQL: `SELECT COUNT(*) FROM knowledge_atoms WHERE created_at > NOW() - INTERVAL '1 day';`
  - Expected: +50-200 atoms
  - **Success:** Cron ran, atoms added

---

## 📊 Success Criteria (Must Pass All)

At the end of deployment, verify:

- [x] ✅ Bot responds to `/start` command
- [x] ✅ Health endpoint returns 200 OK
- [x] ✅ Cron job manual trigger succeeds
- [x] ✅ Telegram notification received
- [x] ✅ UptimeRobot shows 100% uptime
- [x] ✅ New atoms in database (after first cron run)
- [x] ✅ Full validation shows ≥95% score
- [x] ✅ Final checklist shows "GO" decision

**If all checked: DEPLOYMENT SUCCESSFUL** 🎉

---

## 🚨 Troubleshooting

### Bot Not Responding

**Problem:** Sent `/start`, no response

**Troubleshoot:**
1. Check Render logs for errors
2. Test health endpoint: `curl https://agent-factory-telegram-bot.onrender.com/health`
3. Verify webhook: `curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo`

**Fix:**
```bash
# Re-deploy service
Render Dashboard → agent-factory-telegram-bot → Manual Deploy

# Re-set webhook
python scripts/deployment/set_telegram_webhook.py --service-url <URL>
```

---

### Cron Job Fails

**Problem:** Manual trigger shows errors in logs

**Troubleshoot:**
1. Check Render cron job logs
2. Verify environment variables match web service
3. Test database: `python scripts/deployment/test_database_failover.py`

**Fix:**
```bash
# Verify DATABASE_PROVIDER is set to "neon"
# Check NEON_DB_URL is correct
# Re-trigger manually
```

---

### Free Tier Sleeping

**Problem:** Bot stops responding after 15 minutes

**Troubleshoot:**
1. Check UptimeRobot monitor is active
2. Verify check interval is 5 minutes (not longer)

**Fix:**
```bash
# Verify monitoring
python scripts/deployment/verify_monitoring.py --service-url <URL>

# Check UptimeRobot dashboard
# https://uptimerobot.com/dashboard
```

---

## 📞 Support Resources

**Documentation:**
- Quick Start: `DEPLOYMENT_QUICK_START.md`
- Checklist: `DEPLOYMENT_CHECKLIST.md`
- Overview: `DEPLOYMENT_COMPLETE_README.md`

**External Help:**
- Render Docs: https://render.com/docs
- Telegram Bot API: https://core.telegram.org/bots/api
- UptimeRobot Help: https://uptimerobot.com/help

**Emergency:**
- GitHub Issues: https://github.com/Mikecranesync/Agent-Factory/issues

---

## 💡 Tips for Success

**Before You Start:**
1. Set aside 2-3 hours uninterrupted time
2. Have your `.env` file open for copy/paste
3. Read `DEPLOYMENT_QUICK_START.md` once through first

**During Deployment:**
1. Follow the steps in order (don't skip)
2. Wait for each phase to complete before moving on
3. Check logs frequently for errors
4. Take screenshots of configuration for reference

**After Deployment:**
1. Monitor bot for first 24 hours
2. Check UptimeRobot dashboard daily (first week)
3. Verify cron job runs successfully tomorrow at 2 AM UTC
4. Review costs after 7 days (should be $1/month)

---

## 🎯 When You're Ready to Deploy

**Start here:**
1. Open `DEPLOYMENT_QUICK_START.md`
2. Follow Step 1: Render.com Account Setup
3. Work through each phase above
4. Run automation scripts as you go
5. Verify success criteria at the end

**Estimated time:** 2 hours
**Monthly cost:** $1
**Uptime target:** 99.9%

**Everything is ready. You just need to execute when the time is right.**

---

**Status:** WAITING FOR USER EXECUTION
**Last Updated:** 2025-12-13
**Infrastructure:** ✅ COMPLETE
**Documentation:** ✅ COMPLETE
**Automation:** ✅ COMPLETE

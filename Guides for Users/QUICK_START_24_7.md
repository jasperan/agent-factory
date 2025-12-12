# 24/7 Production Schedule - Quick Start

## 🚀 3-Step Setup (15 Minutes Total)

### STEP 1: Fix Supabase Schema (5 min - YOU)

```sql
-- Open Supabase SQL Editor → Paste this file → RUN
docs/supabase_complete_schema.sql
```

**Verify:** Query `knowledge_atoms` table should have `content` column

---

### STEP 2: Upload 2045 Atoms (5 min - AUTOMATED)

```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
poetry run python scripts/FULL_AUTO_KB_BUILD.py
```

**Expected:** "Uploaded: 2045, Failed: 0"

---

### STEP 3: Start 24/7 Automation (10 sec - AUTOMATED)

```powershell
# Run as Administrator
PowerShell -ExecutionPolicy Bypass -File scripts\setup_windows_scheduler.ps1
```

**Creates 3 tasks:**
- Daily KB Building (2:00 AM)
- Weekly Maintenance (Sunday 12:00 AM)
- Health Monitor (every 15 min)

---

## ✅ Verify Setup

```powershell
# Check tasks exist
schtasks /query /tn "AgentFactory_KB_Daily"
schtasks /query /tn "AgentFactory_KB_Weekly"
schtasks /query /tn "AgentFactory_HealthMonitor"

# Run health check
poetry run python scripts/health_monitor.py
```

---

## 📊 What Happens Now

**Every Day (2:00 AM):**
1. Scrape new PDFs from OEM sources
2. Build knowledge atoms with embeddings
3. Upload to Supabase
4. Send Telegram report

**Every Week (Sunday 12:00 AM):**
1. Reindex database
2. Find duplicate atoms
3. Quality audit
4. Growth report

**Every 15 Minutes:**
1. Health checks
2. Alert if critical issues

---

## 📈 Expected Growth

- **Week 1:** 2,545 atoms (+500)
- **Week 4:** 3,545 atoms (+1,500)
- **Month 3:** 6,545 atoms (+4,500)

**Cost:** ~$0.30/month (OpenAI embeddings)

---

## 🔧 Quick Commands

**View Logs:**
```bash
type data\logs\kb_daily_20251211.log
type data\logs\health_monitor.log
```

**Manual Test:**
```bash
poetry run python scripts/scheduler_kb_daily.py
poetry run python scripts/health_monitor.py
```

**Disable/Enable:**
```powershell
schtasks /change /tn "AgentFactory_KB_Daily" /disable
schtasks /change /tn "AgentFactory_KB_Daily" /enable
```

---

## 🆘 Troubleshooting

**Issue:** Upload failing
- **Fix:** Deploy Supabase schema (Step 1)

**Issue:** Task not running
- **Check:** `schtasks /query /tn "AgentFactory_KB_Daily" /v`
- **Logs:** `data/logs/kb_daily_*.log`

**Issue:** No Telegram notifications
- **Add to .env:**
  ```
  TELEGRAM_BOT_TOKEN=your_token
  TELEGRAM_ADMIN_CHAT_ID=your_chat_id
  ```

---

## 📖 Full Documentation

See `docs/24_7_AUTOMATION_GUIDE.md` for complete guide.

---

## 🎯 Success Checklist

After 1 week, you should have:
- [ ] 3 scheduled tasks running
- [ ] Daily logs being generated
- [ ] Health checks passing (green)
- [ ] ~500 new atoms added
- [ ] Telegram notifications working

**If all green → Your 24/7 automation is working!** 🎉

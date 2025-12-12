# Telegram Bot Auto-Start Setup (Windows)

## Problem
Having to manually run `poetry run python -m agent_factory.integrations.telegram` every time is stupid. The bot should run 24/7 automatically.

## Solution
Install as Windows Service that:
- ✅ Starts automatically on Windows boot
- ✅ Runs in background (no terminal window)
- ✅ Restarts automatically if it crashes
- ✅ Logs to file (not console)
- ✅ Manageable via Windows Services GUI

---

## Installation (One-Time Setup)

### Step 1: Run PowerShell as Administrator

Right-click PowerShell → "Run as Administrator"

### Step 2: Install Service

```powershell
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
powershell -ExecutionPolicy Bypass -File scripts\install_telegram_service.ps1
```

**What it does:**
1. Downloads NSSM (service manager) automatically
2. Creates Windows service "AgentFactoryTelegramBot"
3. Sets to auto-start on boot
4. Starts the service immediately
5. Creates log files in `logs/`

**Expected Output:**
```
Downloading NSSM (service manager)...
[OK] NSSM installed to C:\Users\hharp\...\bin\nssm.exe
Installing service: Agent Factory Telegram Bot
Starting service...

==========================================
Service Status: SERVICE_RUNNING
==========================================

[OK] Telegram bot is now running 24/7!

Service Details:
  Name: AgentFactoryTelegramBot
  Display: Agent Factory Telegram Bot
  Auto-start: Yes (starts on Windows boot)
  Logs: C:\Users\hharp\...\logs
```

---

## Service Management

### Check Status
```powershell
bin\nssm.exe status AgentFactoryTelegramBot
```

### Start/Stop/Restart
```powershell
# Start
bin\nssm.exe start AgentFactoryTelegramBot

# Stop
bin\nssm.exe stop AgentFactoryTelegramBot

# Restart (after code changes)
bin\nssm.exe restart AgentFactoryTelegramBot
```

### View Logs
```powershell
# Real-time log tail
Get-Content logs\telegram_bot.log -Wait -Tail 50

# Error log
Get-Content logs\telegram_bot_error.log -Tail 50
```

### Windows Services GUI
```powershell
services.msc
```
Search for "Agent Factory Telegram Bot" → Right-click → Start/Stop/Restart

### Remove Service (if needed)
```powershell
bin\nssm.exe stop AgentFactoryTelegramBot
bin\nssm.exe remove AgentFactoryTelegramBot confirm
```

---

## Verification

### Test 1: Check Service Running
```powershell
bin\nssm.exe status AgentFactoryTelegramBot
# Should show: SERVICE_RUNNING
```

### Test 2: Send Telegram Message
Open Telegram → Send `/kb_stats` to bot

Should respond immediately (even though no terminal window is open)

### Test 3: Reboot Test
```powershell
# Restart computer
shutdown /r /t 0

# After reboot, check service started automatically
bin\nssm.exe status AgentFactoryTelegramBot
# Should show: SERVICE_RUNNING
```

---

## Troubleshooting

### Service Won't Start
**Check logs:**
```powershell
Get-Content logs\telegram_bot_error.log -Tail 50
```

**Common Issues:**
1. **TELEGRAM_BOT_TOKEN missing** → Add to `.env` file
2. **Supabase credentials missing** → Add to `.env` file
3. **Poetry env not found** → Run `poetry install` first

**Fix and restart:**
```powershell
bin\nssm.exe restart AgentFactoryTelegramBot
```

### Service Crashes Repeatedly
**View crash logs:**
```powershell
Get-EventLog -LogName Application -Source "AgentFactoryTelegramBot" -Newest 10
```

**Increase restart delay:**
```powershell
bin\nssm.exe set AgentFactoryTelegramBot AppThrottle 15000  # 15 seconds
bin\nssm.exe restart AgentFactoryTelegramBot
```

### Bot Not Responding in Telegram
**Check service is running:**
```powershell
bin\nssm.exe status AgentFactoryTelegramBot
```

**Check logs for errors:**
```powershell
Get-Content logs\telegram_bot.log -Tail 100
```

**Test bot token:**
```powershell
# In PowerShell
$env:TELEGRAM_BOT_TOKEN = "your_token_here"
poetry run python -c "from agent_factory.integrations.telegram.config import TelegramConfig; print(TelegramConfig.from_env())"
```

---

## Updates After Code Changes

When you modify bot code, restart the service:

```powershell
bin\nssm.exe restart AgentFactoryTelegramBot
```

No need to reinstall - just restart.

---

## Configuration Files

### `.env` (Required)
```bash
# Telegram Bot (from @BotFather)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Supabase (for KB access)
SUPABASE_URL=https://mggqgrxwumnnujojndub.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_key_here

# Optional: Restrict access
AUTHORIZED_TELEGRAM_USERS=123456789,987654321
```

### Service Configuration
All handled by NSSM automatically:
- Auto-restart on crash: ✅ Yes
- Start on boot: ✅ Yes
- Log rotation: ✅ Yes (1MB max)
- Run as: ✅ Local System account

---

## Architecture

**Before (Manual Start):**
```
You → Open terminal → poetry run python ...
    ↓
Terminal window must stay open
    ↓
Close terminal → Bot dies
    ↓
Reboot → Bot doesn't restart
```

**After (Windows Service):**
```
Windows boots → Service Manager starts bot
    ↓
Bot runs in background (no window)
    ↓
Crash → Auto-restarts (5-second delay)
    ↓
Reboot → Auto-starts on boot
    ↓
You → Access via Telegram 24/7
```

---

## Success Metrics

✅ **Service running:** `nssm status AgentFactoryTelegramBot` shows `SERVICE_RUNNING`
✅ **Bot responds:** Send `/kb_stats` in Telegram → Instant response
✅ **Survives reboot:** Restart PC → Service auto-starts
✅ **No terminal needed:** Close all windows → Bot still works
✅ **Logs working:** `logs\telegram_bot.log` has timestamps

---

## Next Steps

After installation:
1. ✅ Verify service running
2. ✅ Test `/kb_stats` in Telegram
3. ✅ Reboot to confirm auto-start
4. ✅ Close this guide - you're done!

**You'll never need to manually start the bot again.**

---

## Alternative: Task Scheduler (Simpler but Less Robust)

If NSSM installation fails, use Windows Task Scheduler:

```powershell
# Create scheduled task (runs on boot)
$action = New-ScheduledTaskAction -Execute "poetry" -Argument "run python -m agent_factory.integrations.telegram" -WorkingDirectory "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName "AgentFactoryTelegramBot" -Action $action -Trigger $trigger -Principal $principal -Settings $settings
```

**Start manually:**
```powershell
Start-ScheduledTask -TaskName "AgentFactoryTelegramBot"
```

**Pros:** Built into Windows, no downloads
**Cons:** No auto-restart on crash, harder to manage logs

**Recommendation:** Use NSSM (primary method) if possible.

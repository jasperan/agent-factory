# Quick Deploy - 2-Step Automated VPS Deployment

Get your Telegram bot running 24/7 on Hostinger VPS in **10 minutes** with just 2 pieces of information.

---

## What You Need (Only 2 Things!)

1. **Hostinger VPS IP address**
   - Go to your Hostinger dashboard
   - Click on your VPS
   - Copy the IP address (format: `123.456.789.012`)

2. **SSH password**
   - Same dashboard, look for "SSH Access" or "Root Password"
   - Or you already set this up when you created the VPS

**That's it!** Everything else is automated from your existing `.env` file.

---

## Step 1: Run the Deployment Script

### Option A: Windows (PowerShell) - RECOMMENDED

```powershell
# Open PowerShell in Agent Factory directory
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"

# Run deployment script
.\deploy_to_vps.ps1
```

**You'll be asked:**
1. `Enter your Hostinger VPS IP address:` → Type your VPS IP
2. `SSH username (default: root):` → Press Enter (uses root)
3. SSH password will be prompted when connecting

**Then the script does everything automatically:**
- ✓ Installs Docker
- ✓ Clones your GitHub repo
- ✓ Creates .env from your existing credentials
- ✓ Builds and starts bot
- ✓ Sets up auto-restart
- ✓ Sets up monitoring

**Time:** ~10 minutes

### Option B: Linux/Mac (Bash)

```bash
# Make script executable
chmod +x deploy_to_vps.sh

# Run deployment
./deploy_to_vps.sh
```

Same questions, same automation.

---

## Step 2: Test Your Bot

1. **Open Telegram** on your phone
2. **Search for your bot** (the name you gave @BotFather)
3. **Send:** `/start`
4. **Bot should respond** with welcome message

**If bot responds → ✅ You're done! Bot is live 24/7**

---

## What the Script Used From Your .env

The deployment script automatically pulled these values from your existing `.env` file:

```
✓ TELEGRAM_BOT_TOKEN (your bot token)
✓ NEON_DB_URL (your database)
✓ OPENAI_API_KEY (for AI responses)
✓ TELEGRAM_ADMIN_CHAT_ID (your user ID: 8445149012)
✓ AUTHORIZED_TELEGRAM_USERS (who can use bot: 8445149012)
```

No manual copy-pasting needed!

---

## Troubleshooting

### Bot doesn't respond in Telegram

```powershell
# Check bot status (from Windows PowerShell)
ssh root@YOUR_VPS_IP "cd /opt/agent-factory && docker-compose ps"

# View logs
ssh root@YOUR_VPS_IP "cd /opt/agent-factory && docker-compose logs --tail 50"
```

**Common issues:**
- "Bot starting..." → Wait 30 seconds, try again
- "Connection error" → Check NEON_DB_URL is correct
- "Bot offline" → Run: `ssh root@YOUR_VPS_IP "cd /opt/agent-factory && docker-compose restart"`

### Script fails during deployment

1. **SSH connection fails:**
   - Check VPS IP is correct
   - Check SSH password is correct
   - Try pinging VPS: `ping YOUR_VPS_IP`

2. **Docker build fails:**
   - VPS may be too small (need 2GB+ RAM)
   - Run script again (it will resume from where it stopped)

3. **Permission denied:**
   - Make sure you're using `root` user
   - Or use `sudo` if you're using a different user

---

## What's Running on Your VPS Now

**Services:**
- ✓ Docker container running Telegram bot
- ✓ Health check server on port 9876 (localhost only)
- ✓ Systemd service (auto-restart on VPS reboot)
- ✓ Cron job monitoring bot every 5 minutes

**Security:**
- ✓ Firewall enabled (only SSH port 22 open)
- ✓ Bot port NOT exposed to internet (secure)
- ✓ .env file has 600 permissions (owner only)

---

## Useful Commands

**From your Windows machine:**

```powershell
# View live logs
ssh root@YOUR_VPS_IP "cd /opt/agent-factory && docker-compose logs -f"

# Restart bot
ssh root@YOUR_VPS_IP "cd /opt/agent-factory && docker-compose restart"

# Check health
ssh root@YOUR_VPS_IP "curl http://localhost:9876/health"

# Stop bot
ssh root@YOUR_VPS_IP "cd /opt/agent-factory && docker-compose down"

# Start bot
ssh root@YOUR_VPS_IP "cd /opt/agent-factory && docker-compose up -d"
```

---

## Next Steps After Bot is Live

### Week 1: Get First User

1. **Post in Reddit:**
   - r/HVAC
   - r/industrial
   - r/MaintenanceTech

**Example post:**
```
Title: Free AI bot for HVAC troubleshooting (testing beta)

I built a Telegram bot that helps diagnose HVAC problems.
Currently testing with real technicians.

Free during beta. Message me for bot link.
Goal: Make troubleshooting faster.

Might charge $10/mo later. Thoughts?
```

2. **Track usage:**
```powershell
# See who's using bot
ssh root@YOUR_VPS_IP "cd /opt/agent-factory && docker-compose logs | grep 'Received message'"
```

3. **Ask for feedback:**
   - Did it help?
   - Would you pay $10/mo?
   - What else do you need?

### Week 2: Get Paying User

If someone says "yes, I'd pay $10/mo":

1. Create Stripe payment link: https://stripe.com
2. Send them link
3. **You now have revenue!**

If they say "no":
- Ask why not
- Ask what price they'd pay
- Ask what features they need
- Build that

---

## Cost Breakdown

**Monthly cost to run:**
- Hostinger VPS: ~$5-10/mo (you already have)
- Neon database: $0 (free tier)
- OpenAI API: ~$1-5/mo (gpt-4o-mini is cheap)
- **Total: ~$6-15/mo**

**Breakeven:** 2 paying users @ $10/mo

**At 10 users:**
- Revenue: $100/mo
- Cost: $15/mo
- **Profit: $85/mo**

---

## Success Checklist

**Day 1 (Today):**
- [x] Run deployment script
- [x] Bot responds to /start
- [ ] You message bot and it works

**Week 1:**
- [ ] Posted in 1-2 Reddit groups
- [ ] 1 person tested bot
- [ ] Asked if they'd pay

**Week 2:**
- [ ] 5 people tested bot
- [ ] At least 1 said "I'd pay for this"
- [ ] You know what users want

**Month 1:**
- [ ] 1 paying customer ($10/mo)
- [ ] $10 MRR
- [ ] **You're making money from AI**

---

## Support

**If deployment fails:**
1. Check this guide's Troubleshooting section
2. Check `HOSTINGER_VPS_DEPLOYMENT.md` for detailed manual steps
3. Run deployment script again (it's safe to re-run)

**If bot doesn't work:**
1. Check logs: `ssh root@YOUR_VPS_IP "cd /opt/agent-factory && docker-compose logs"`
2. Check .env values are correct
3. Restart bot: `ssh root@YOUR_VPS_IP "cd /opt/agent-factory && docker-compose restart"`

---

**Ready? Run the script:**

```powershell
.\deploy_to_vps.ps1
```

**Time to live bot:** 10 minutes
**Cost:** $0 (uses infrastructure you already have)
**Difficulty:** Easy (just answer 2 questions)

Good luck! 🚀

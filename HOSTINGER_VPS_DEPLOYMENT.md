# Hostinger VPS Deployment - Telegram Bot 24/7

Complete step-by-step guide to deploy Agent Factory Telegram bot on Hostinger VPS.

**Time:** 30-45 minutes
**Cost:** $0 (using Hostinger VPS you already have)
**Result:** Bot running 24/7, accessible worldwide via Telegram

---

## Prerequisites

Before starting, collect these:

1. **Hostinger VPS Access**
   - VPS IP address (from Hostinger dashboard)
   - SSH password or private key
   - Recommended: 2GB RAM, 2 vCPU (KVM 2 plan or higher)

2. **Telegram Bot Token**
   - Open Telegram, message @BotFather
   - Send: `/newbot`
   - Follow prompts to create bot
   - Copy token (format: `123456789:ABCdefGHI...`)

3. **Neon Database URL**
   - Go to https://console.neon.tech
   - Select your project
   - Click "Connection Details"
   - Copy "Pooled Connection" string
   - Format: `postgresql://user:pass@host/dbname?sslmode=require`

4. **OpenAI API Key** (Optional but recommended)
   - Go to https://platform.openai.com/api-keys
   - Create new key
   - Copy key (starts with `sk-...`)

5. **Your Telegram User ID** (for testing)
   - Message @userinfobot on Telegram
   - Copy your numeric user ID

---

## Phase 1: VPS Setup (15 minutes)

### Step 1.1: SSH into VPS

```bash
# From your local machine (Windows PowerShell, macOS Terminal, or Linux shell)
ssh root@YOUR_VPS_IP

# If using password:
# Enter password when prompted

# If using private key:
ssh -i path/to/private_key root@YOUR_VPS_IP
```

### Step 1.2: Update System

```bash
# Update package lists
apt update

# Upgrade installed packages
apt upgrade -y

# Install essential tools
apt install -y git curl wget nano ufw
```

### Step 1.3: Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Start Docker service
systemctl start docker
systemctl enable docker

# Verify Docker installation
docker --version
# Should show: Docker version 24.x.x or higher

# Test Docker
docker run hello-world
# Should download and run test container
```

### Step 1.4: Install Docker Compose

```bash
# Install Docker Compose
apt install -y docker-compose

# Verify installation
docker-compose --version
# Should show: docker-compose version 1.29.x or higher
```

### Step 1.5: Configure Firewall (IMPORTANT - Security)

```bash
# Allow SSH (don't lock yourself out!)
ufw allow 22/tcp

# Enable firewall
ufw enable

# Verify firewall status
ufw status
# Should show: Status: active, with port 22 allowed

# NOTE: We do NOT expose port 9876 (health check)
# Bot communicates outbound to Telegram servers only
# No inbound ports needed except SSH
```

---

## Phase 2: Deploy Bot (20 minutes)

### Step 2.1: Clone Repository

```bash
# Create app directory
mkdir -p /opt/agent-factory
cd /opt/agent-factory

# Clone repository
git clone https://github.com/Mikecranesync/Agent-Factory.git .

# Verify files
ls -la
# Should see: Dockerfile, pyproject.toml, agent_factory/, etc.
```

### Step 2.2: Create Production Environment File

```bash
# Create .env file
nano .env

# Paste this template and fill in YOUR values:
```

```bash
# =============================================================================
# REQUIRED - Bot Will Not Start Without These
# =============================================================================

# Telegram Bot Token (from @BotFather)
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE

# Database (Neon PostgreSQL)
DATABASE_PROVIDER=neon
NEON_DB_URL=YOUR_NEON_CONNECTION_STRING_HERE

# LLM Provider (for agent responses)
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4o-mini
OPENAI_API_KEY=YOUR_OPENAI_KEY_HERE

# =============================================================================
# OPTIONAL - Recommended for Production
# =============================================================================

# Python Configuration
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
LOG_LEVEL=INFO

# Voice Mode (use free Edge-TTS)
VOICE_MODE=edge
EDGE_VOICE=en-US-GuyNeural

# Security - Limit to your Telegram user ID
TELEGRAM_ALLOWED_USERS=YOUR_TELEGRAM_USER_ID_HERE

# Rate Limiting
TELEGRAM_RATE_LIMIT=10

# =============================================================================
# DO NOT SET THESE (Docker handles them)
# =============================================================================
# PORT - Auto-set by Docker
# SUPABASE_URL - Using Neon instead
```

**After pasting:**
1. Replace `YOUR_BOT_TOKEN_HERE` with actual token from @BotFather
2. Replace `YOUR_NEON_CONNECTION_STRING_HERE` with Neon database URL
3. Replace `YOUR_OPENAI_KEY_HERE` with OpenAI API key
4. Replace `YOUR_TELEGRAM_USER_ID_HERE` with your numeric Telegram user ID
5. Press `Ctrl+O` to save
6. Press `Enter` to confirm filename
7. Press `Ctrl+X` to exit nano

### Step 2.3: Create Docker Compose Configuration

```bash
nano docker-compose.yml
```

Paste this:

```yaml
version: '3.8'

services:
  telegram-bot:
    build: .
    container_name: agent-factory-bot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    ports:
      - "127.0.0.1:9876:9876"  # Health check (localhost only)
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9876/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**Save and exit:**
- Press `Ctrl+O`, `Enter`, `Ctrl+X`

### Step 2.4: Build Docker Image

```bash
# Build image (takes 5-10 minutes first time)
docker-compose build

# Check for errors
# Should end with: Successfully built <image_id>
```

### Step 2.5: Start Bot

```bash
# Start bot in background
docker-compose up -d

# Check bot is running
docker-compose ps
# Should show: agent-factory-bot running (healthy)

# View logs
docker-compose logs -f telegram-bot

# Look for these lines:
# [OK] Health check endpoint: http://0.0.0.0:9876/health
# Telegram Bot started successfully

# Press Ctrl+C to stop viewing logs (bot keeps running)
```

### Step 2.6: Test Bot

**Option A: Test Health Endpoint (from VPS)**
```bash
curl http://localhost:9876/health

# Expected response:
# {"status":"ok","uptime":123.45}
```

**Option B: Test Telegram Bot (from your phone)**
1. Open Telegram app
2. Search for your bot name (from @BotFather)
3. Start conversation
4. Send: `/start`
5. **Expected:** Bot responds with welcome message

**If bot doesn't respond:**
```bash
# Check logs for errors
docker-compose logs telegram-bot | tail -50

# Common issues:
# - "TELEGRAM_BOT_TOKEN not set" → check .env file
# - "Database connection failed" → check NEON_DB_URL
# - "OpenAI authentication failed" → check OPENAI_API_KEY
```

---

## Phase 3: Production Configuration (10 minutes)

### Step 3.1: Create Systemd Service (Auto-Start on Boot)

```bash
nano /etc/systemd/system/agent-factory.service
```

Paste this:

```ini
[Unit]
Description=Agent Factory Telegram Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/agent-factory
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Save and enable:

```bash
# Reload systemd
systemctl daemon-reload

# Enable service
systemctl enable agent-factory

# Test service
systemctl start agent-factory
systemctl status agent-factory

# Should show: active (exited)
```

### Step 3.2: Create Monitoring Script

```bash
nano /opt/agent-factory/monitor.sh
```

Paste this:

```bash
#!/bin/bash
# Agent Factory Health Monitor
# Run via cron every 5 minutes

HEALTH_URL="http://localhost:9876/health"
LOG_FILE="/opt/agent-factory/monitor.log"

timestamp=$(date '+%Y-%m-%d %H:%M:%S')

# Check health endpoint
if curl -sf "$HEALTH_URL" > /dev/null; then
    echo "[$timestamp] OK - Bot healthy" >> "$LOG_FILE"
else
    echo "[$timestamp] ERROR - Bot unhealthy, restarting..." >> "$LOG_FILE"
    cd /opt/agent-factory
    docker-compose restart
    echo "[$timestamp] Restart complete" >> "$LOG_FILE"
fi

# Keep only last 1000 lines
tail -1000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
```

Make executable and test:

```bash
# Make executable
chmod +x /opt/agent-factory/monitor.sh

# Test run
/opt/agent-factory/monitor.sh

# Check log
cat /opt/agent-factory/monitor.log
# Should show: [timestamp] OK - Bot healthy
```

### Step 3.3: Setup Cron Job (Auto-Monitor)

```bash
# Edit crontab
crontab -e

# If prompted, choose nano (option 1)

# Add this line at the end:
*/5 * * * * /opt/agent-factory/monitor.sh
```

Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`)

Verify cron is running:

```bash
systemctl status cron
# Should show: active (running)
```

---

## Phase 4: Ongoing Management

### Useful Commands

**Check bot status:**
```bash
docker-compose ps
docker-compose logs telegram-bot --tail 50
```

**Restart bot:**
```bash
cd /opt/agent-factory
docker-compose restart
```

**Stop bot:**
```bash
docker-compose down
```

**Start bot:**
```bash
docker-compose up -d
```

**Update bot code:**
```bash
cd /opt/agent-factory
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

**View logs:**
```bash
# Last 50 lines
docker-compose logs telegram-bot --tail 50

# Follow live logs
docker-compose logs -f telegram-bot

# Search logs for errors
docker-compose logs telegram-bot | grep -i error
```

**Check disk space:**
```bash
df -h
docker system df
```

**Clean up old Docker images:**
```bash
docker system prune -a
```

---

## Phase 5: Get Your First User

### Step 5.1: Test Bot Yourself

```bash
# Get your bot username from logs
docker-compose logs telegram-bot | grep "Bot username"

# Or from @BotFather (send /mybots)
```

Send these commands:
- `/start` - Welcome message
- `/help` - Available commands
- `/status` - System status
- `/agents` - List available agents

### Step 5.2: Create Simple Pitch

**Example Reddit post:**

```
Title: Free AI assistant for HVAC troubleshooting (testing beta)

Body:
Hey r/HVAC,

I built an AI bot that helps diagnose HVAC issues using verified repair manuals and technical docs.

Currently testing it with real technicians. If you're interested:
1. Message me for bot link
2. Try it with a real problem you're facing
3. Let me know if it's helpful

Goal: Make troubleshooting faster. 100% free during beta.

If it saves you time, I might charge $10/mo later. Thoughts?
```

**Post in:**
- r/HVAC
- r/HVAC_Tech (if exists)
- Facebook HVAC tech groups
- LinkedIn (tag #HVACTech)

### Step 5.3: Track First User

When someone messages your bot:

```bash
# Watch logs for their messages
docker-compose logs -f telegram-bot | grep "Received message"

# See what they're asking
# See if bot responds correctly
# Note: what worked, what didn't
```

### Step 5.4: Collect Feedback

After they use it, message them:
1. "Did this save you time?"
2. "Would you pay $10/mo for this?"
3. "What else would you need?"

**If yes to #2:**
- Create Stripe payment link
- Send them link
- **You now have revenue**

**If no to #2:**
- Ask why not
- Ask what price they WOULD pay
- Ask what features they need
- Build that

---

## Troubleshooting

### Bot doesn't start

```bash
# Check logs
docker-compose logs telegram-bot

# Common errors:
# "TELEGRAM_BOT_TOKEN not set" → Check .env file exists and has token
# "Database connection failed" → Check NEON_DB_URL is correct
# "Permission denied" → Run: chmod +x /opt/agent-factory/monitor.sh
```

### Bot responds slowly

```bash
# Check resources
htop  # Press q to exit

# If RAM > 90%:
# Upgrade VPS plan OR reduce Docker memory:
docker-compose down
nano docker-compose.yml
# Add under telegram-bot service:
#   mem_limit: 1g
docker-compose up -d
```

### Bot stops randomly

```bash
# Check monitor log
cat /opt/agent-factory/monitor.log | tail -20

# Check Docker logs
docker-compose logs telegram-bot | tail -100

# Most common: Out of memory
# Solution: Upgrade VPS to 2GB+ RAM
```

### Health check fails

```bash
# Test manually
curl http://localhost:9876/health

# If no response:
docker-compose restart

# If still fails:
docker-compose logs telegram-bot | grep -i health
# Check for port conflicts or firewall issues
```

---

## Security Checklist

- [x] Firewall enabled (ufw)
- [x] Only port 22 (SSH) exposed
- [x] Bot port 9876 localhost-only
- [x] TELEGRAM_ALLOWED_USERS set (limits who can use bot)
- [x] .env file has secure permissions (600)
- [x] SSH key-based auth (recommended over password)
- [ ] Fail2ban installed (optional, prevents SSH brute-force)
- [ ] Automatic security updates enabled

**Optional security hardening:**
```bash
# Install fail2ban (SSH protection)
apt install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# Enable automatic security updates
apt install -y unattended-upgrades
dpkg-reconfigure --priority=low unattended-upgrades
```

---

## Success Metrics

**Week 1:**
- [x] Bot deployed and running 24/7
- [x] Health checks passing
- [x] You can message bot and get responses
- [ ] 1 other person tested bot

**Week 2:**
- [ ] 5 people tested bot
- [ ] At least 1 person asked "how much?"
- [ ] You have pricing figured out

**Month 1:**
- [ ] 1 paying customer ($10/mo)
- [ ] You know what users actually want
- [ ] Bot uptime > 99%

---

## Next Steps After First User

1. **Add Stripe payment** (stripe.com/billing)
2. **Create landing page** (simple HTML or Carrd.co)
3. **Setup analytics** (count messages, track popular commands)
4. **Build user dashboard** (show usage stats)
5. **Add more features** based on user requests

---

## Cost Breakdown

**Current monthly cost:**
- Hostinger VPS: ~$5-10/mo (you already have)
- Neon database: $0 (free tier, 3GB)
- OpenAI API: ~$1-5/mo (gpt-4o-mini is cheap)
- **Total: ~$6-15/mo**

**Revenue at 10 users @ $10/mo:**
- Revenue: $100/mo
- Cost: $15/mo
- **Profit: $85/mo**

**Breakeven: 2 paying users**

---

## Support

**If you get stuck:**
1. Check logs: `docker-compose logs telegram-bot`
2. Check this guide's Troubleshooting section
3. Google the specific error message
4. Ask in Agent Factory Discord/GitHub issues

**Emergency commands:**
```bash
# Full reset (if everything breaks)
cd /opt/agent-factory
docker-compose down
docker system prune -a -f
git pull
docker-compose build --no-cache
docker-compose up -d
```

---

**Status:** Ready to deploy
**ETA:** 30-45 minutes from start to working bot
**Difficulty:** Intermediate (copy-paste commands, basic Linux knowledge)

Good luck! 🚀

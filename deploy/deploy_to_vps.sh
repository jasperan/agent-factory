#!/bin/bash
#
# Agent Factory - Automated VPS Deployment Script
#
# This script automates the ENTIRE deployment process to Hostinger VPS.
# You only need to provide: VPS IP and SSH password
#
# Usage:
#   chmod +x deploy_to_vps.sh
#   ./deploy_to_vps.sh
#
# What it does:
#   1. Connects to your VPS via SSH
#   2. Installs Docker + Docker Compose
#   3. Clones GitHub repo
#   4. Creates .env file from your local credentials
#   5. Builds and starts bot
#   6. Sets up systemd auto-restart
#   7. Sets up health monitoring
#   8. Tests bot is running
#
# Time: ~10 minutes total
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Agent Factory - Automated VPS Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Collect VPS info from user
echo -e "${YELLOW}Step 1: VPS Information${NC}"
echo ""

read -p "Enter your Hostinger VPS IP address: " VPS_IP
if [ -z "$VPS_IP" ]; then
    echo -e "${RED}Error: VPS IP is required${NC}"
    exit 1
fi

read -p "SSH username (default: root): " SSH_USER
SSH_USER=${SSH_USER:-root}

read -p "Use SSH key authentication? (y/n, default: n): " USE_KEY
USE_KEY=${USE_KEY:-n}

if [ "$USE_KEY" = "y" ] || [ "$USE_KEY" = "Y" ]; then
    read -p "Path to SSH private key: " SSH_KEY
    SSH_CMD="ssh -i $SSH_KEY $SSH_USER@$VPS_IP"
    SCP_CMD="scp -i $SSH_KEY"
else
    SSH_CMD="ssh $SSH_USER@$VPS_IP"
    SCP_CMD="scp"
    echo -e "${YELLOW}You'll be prompted for SSH password multiple times${NC}"
fi

echo ""
echo -e "${GREEN}✓ VPS Info collected${NC}"
echo ""

# Step 2: Test SSH connection
echo -e "${YELLOW}Step 2: Testing SSH connection...${NC}"
if $SSH_CMD "echo 'SSH connection successful'" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ SSH connection working${NC}"
else
    echo -e "${RED}✗ SSH connection failed${NC}"
    echo "Please check:"
    echo "  - VPS IP is correct"
    echo "  - SSH password is correct"
    echo "  - VPS is running"
    exit 1
fi
echo ""

# Step 3: Read local .env file
echo -e "${YELLOW}Step 3: Reading local credentials from .env file...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found in current directory${NC}"
    echo "Run this script from the Agent Factory root directory"
    exit 1
fi

# Extract values from .env
TELEGRAM_BOT_TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" .env | cut -d= -f2)
NEON_DB_URL=$(grep "^NEON_DB_URL=" .env | cut -d= -f2)
OPENAI_API_KEY=$(grep "^OPENAI_API_KEY=" .env | cut -d= -f2)
TELEGRAM_ADMIN_CHAT_ID=$(grep "^TELEGRAM_ADMIN_CHAT_ID=" .env | cut -d= -f2)
AUTHORIZED_TELEGRAM_USERS=$(grep "^AUTHORIZED_TELEGRAM_USERS=" .env | cut -d= -f2)

# Validate required values
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo -e "${RED}Error: TELEGRAM_BOT_TOKEN not found in .env${NC}"
    exit 1
fi

if [ -z "$NEON_DB_URL" ]; then
    echo -e "${RED}Error: NEON_DB_URL not found in .env${NC}"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}Warning: OPENAI_API_KEY not found in .env${NC}"
    echo "Bot will work with limited functionality"
fi

echo -e "${GREEN}✓ Credentials loaded from .env${NC}"
echo ""

# Step 4: Install Docker on VPS
echo -e "${YELLOW}Step 4: Installing Docker on VPS...${NC}"

$SSH_CMD << 'ENDSSH'
set -e

# Check if Docker is already installed
if command -v docker &> /dev/null; then
    echo "Docker already installed"
else
    echo "Installing Docker..."
    apt update
    apt install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
    echo "Docker installed successfully"
fi

# Check if Docker Compose is already installed
if command -v docker-compose &> /dev/null; then
    echo "Docker Compose already installed"
else
    echo "Installing Docker Compose..."
    apt install -y docker-compose
    echo "Docker Compose installed successfully"
fi
ENDSSH

echo -e "${GREEN}✓ Docker installed${NC}"
echo ""

# Step 5: Setup firewall
echo -e "${YELLOW}Step 5: Configuring firewall...${NC}"

$SSH_CMD << 'ENDSSH'
set -e

# Install and configure UFW
if ! command -v ufw &> /dev/null; then
    apt install -y ufw
fi

# Allow SSH (don't lock ourselves out!)
ufw allow 22/tcp

# Enable firewall
echo "y" | ufw enable

echo "Firewall configured (only SSH allowed)"
ENDSSH

echo -e "${GREEN}✓ Firewall configured${NC}"
echo ""

# Step 6: Clone repository
echo -e "${YELLOW}Step 6: Cloning Agent Factory repository...${NC}"

$SSH_CMD << 'ENDSSH'
set -e

# Create app directory
mkdir -p /opt/agent-factory
cd /opt/agent-factory

# Clone or update repository
if [ -d ".git" ]; then
    echo "Repository exists, pulling latest changes..."
    git pull origin main
else
    echo "Cloning repository..."
    git clone https://github.com/Mikecranesync/Agent-Factory.git .
fi

echo "Repository ready"
ENDSSH

echo -e "${GREEN}✓ Repository cloned${NC}"
echo ""

# Step 7: Create .env file on VPS
echo -e "${YELLOW}Step 7: Creating .env file on VPS...${NC}"

$SSH_CMD bash << ENDSSH
set -e
cd /opt/agent-factory

# Create .env file with production values
cat > .env << 'ENVEOF'
# =============================================================================
# Agent Factory - Production Environment (Auto-Generated)
# Generated: $(date)
# =============================================================================

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
TELEGRAM_ADMIN_CHAT_ID=$TELEGRAM_ADMIN_CHAT_ID
AUTHORIZED_TELEGRAM_USERS=$AUTHORIZED_TELEGRAM_USERS
TELEGRAM_RATE_LIMIT=10

# Database Configuration
DATABASE_PROVIDER=neon
NEON_DB_URL=$NEON_DB_URL

# LLM Provider
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4o-mini
OPENAI_API_KEY=$OPENAI_API_KEY

# Voice Production (FREE Edge-TTS)
VOICE_MODE=edge
EDGE_VOICE=en-US-GuyNeural

# Python Configuration
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
LOG_LEVEL=INFO
ENVEOF

# Set secure permissions
chmod 600 .env

echo ".env file created successfully"
ENDSSH

echo -e "${GREEN}✓ .env file created${NC}"
echo ""

# Step 8: Build and start bot
echo -e "${YELLOW}Step 8: Building Docker image and starting bot...${NC}"

$SSH_CMD << 'ENDSSH'
set -e
cd /opt/agent-factory

# Build Docker image
echo "Building Docker image (this may take 5-10 minutes)..."
docker-compose build

# Start bot
echo "Starting bot..."
docker-compose up -d

# Wait for startup
sleep 10

echo "Bot started successfully"
ENDSSH

echo -e "${GREEN}✓ Bot started${NC}"
echo ""

# Step 9: Setup systemd service
echo -e "${YELLOW}Step 9: Setting up systemd auto-restart service...${NC}"

$SSH_CMD << 'ENDSSH'
set -e

# Create systemd service file
cat > /etc/systemd/system/agent-factory.service << 'SERVICEEOF'
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
SERVICEEOF

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable agent-factory

echo "Systemd service configured"
ENDSSH

echo -e "${GREEN}✓ Auto-restart configured${NC}"
echo ""

# Step 10: Setup monitoring
echo -e "${YELLOW}Step 10: Setting up health monitoring...${NC}"

$SSH_CMD << 'ENDSSH'
set -e
cd /opt/agent-factory

# Create monitoring script
cat > monitor.sh << 'MONITOREOF'
#!/bin/bash
HEALTH_URL="http://localhost:9876/health"
LOG_FILE="/opt/agent-factory/monitor.log"
timestamp=$(date '+%Y-%m-%d %H:%M:%S')

if curl -sf "$HEALTH_URL" > /dev/null; then
    echo "[$timestamp] OK - Bot healthy" >> "$LOG_FILE"
else
    echo "[$timestamp] ERROR - Bot unhealthy, restarting..." >> "$LOG_FILE"
    cd /opt/agent-factory
    docker-compose restart
    echo "[$timestamp] Restart complete" >> "$LOG_FILE"
fi

tail -1000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
MONITOREOF

chmod +x monitor.sh

# Add to crontab (run every 5 minutes)
(crontab -l 2>/dev/null | grep -v "monitor.sh"; echo "*/5 * * * * /opt/agent-factory/monitor.sh") | crontab -

echo "Monitoring configured (runs every 5 minutes)"
ENDSSH

echo -e "${GREEN}✓ Monitoring configured${NC}"
echo ""

# Step 11: Test deployment
echo -e "${YELLOW}Step 11: Testing deployment...${NC}"

HEALTH_STATUS=$($SSH_CMD "curl -sf http://localhost:9876/health" || echo "FAILED")

if [ "$HEALTH_STATUS" = "FAILED" ]; then
    echo -e "${YELLOW}⚠ Health check not responding yet (may still be starting up)${NC}"
    echo "Check logs with: ssh $SSH_USER@$VPS_IP 'cd /opt/agent-factory && docker-compose logs'"
else
    echo -e "${GREEN}✓ Health check passing${NC}"
    echo "Response: $HEALTH_STATUS"
fi

# Get bot status
BOT_STATUS=$($SSH_CMD "cd /opt/agent-factory && docker-compose ps | grep telegram-bot | awk '{print \$4}'")
echo "Bot status: $BOT_STATUS"

echo ""

# Step 12: Final summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Bot Details:${NC}"
echo "  VPS IP: $VPS_IP"
echo "  SSH User: $SSH_USER"
echo "  Bot Status: $BOT_STATUS"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Open Telegram and search for your bot"
echo "2. Send /start to test the bot"
echo "3. Bot should respond with welcome message"
echo ""
echo -e "${YELLOW}Useful Commands:${NC}"
echo "  View logs:    ssh $SSH_USER@$VPS_IP 'cd /opt/agent-factory && docker-compose logs -f'"
echo "  Restart bot:  ssh $SSH_USER@$VPS_IP 'cd /opt/agent-factory && docker-compose restart'"
echo "  Stop bot:     ssh $SSH_USER@$VPS_IP 'cd /opt/agent-factory && docker-compose down'"
echo "  Check health: ssh $SSH_USER@$VPS_IP 'curl http://localhost:9876/health'"
echo ""
echo -e "${GREEN}✓ Bot is now running 24/7 on your VPS!${NC}"
echo ""

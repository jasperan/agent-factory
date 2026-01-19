# Agent Factory - Automated VPS Deployment (Windows PowerShell)
#
# Usage: .\deploy_to_vps.ps1
#
# This script automates deployment to Hostinger VPS from Windows.
# You only need to provide: VPS IP and SSH password
#

Write-Host "========================================"  -ForegroundColor Blue
Write-Host "Agent Factory - Automated VPS Deployment" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

# Step 1: Collect VPS info
Write-Host "Step 1: VPS Information" -ForegroundColor Yellow
Write-Host ""

$VPS_IP = Read-Host "Enter your Hostinger VPS IP address"
if ([string]::IsNullOrEmpty($VPS_IP)) {
    Write-Host "Error: VPS IP is required" -ForegroundColor Red
    exit 1
}

$SSH_USER = Read-Host "SSH username (default: root)"
if ([string]::IsNullOrEmpty($SSH_USER)) {
    $SSH_USER = "root"
}

Write-Host ""
Write-Host "✓ VPS Info collected" -ForegroundColor Green
Write-Host ""

# Step 2: Test SSH connection
Write-Host "Step 2: Testing SSH connection..." -ForegroundColor Yellow

try {
    $testResult = ssh "$SSH_USER@$VPS_IP" "echo 'SSH connection successful'" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ SSH connection working" -ForegroundColor Green
    } else {
        throw "SSH connection failed"
    }
} catch {
    Write-Host "✗ SSH connection failed" -ForegroundColor Red
    Write-Host "Please check:"
    Write-Host "  - VPS IP is correct"
    Write-Host "  - SSH password is correct"
    Write-Host "  - VPS is running"
    Write-Host "  - OpenSSH client is installed (run: winget install Microsoft.OpenSSH.Beta)"
    exit 1
}

Write-Host ""

# Step 3: Read local .env file
Write-Host "Step 3: Reading local credentials from .env file..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    Write-Host "Error: .env file not found in current directory" -ForegroundColor Red
    Write-Host "Run this script from the Agent Factory root directory"
    exit 1
}

# Read .env and extract values
$envContent = Get-Content ".env"
$TELEGRAM_BOT_TOKEN = ($envContent | Select-String "^TELEGRAM_BOT_TOKEN=" | ForEach-Object { $_ -replace "^TELEGRAM_BOT_TOKEN=", "" })
$NEON_DB_URL = ($envContent | Select-String "^NEON_DB_URL=" | ForEach-Object { $_ -replace "^NEON_DB_URL=", "" })
$OPENAI_API_KEY = ($envContent | Select-String "^OPENAI_API_KEY=" | ForEach-Object { $_ -replace "^OPENAI_API_KEY=", "" })
$TELEGRAM_ADMIN_CHAT_ID = ($envContent | Select-String "^TELEGRAM_ADMIN_CHAT_ID=" | ForEach-Object { $_ -replace "^TELEGRAM_ADMIN_CHAT_ID=", "" })
$AUTHORIZED_TELEGRAM_USERS = ($envContent | Select-String "^AUTHORIZED_TELEGRAM_USERS=" | ForEach-Object { $_ -replace "^AUTHORIZED_TELEGRAM_USERS=", "" })

# Validate
if ([string]::IsNullOrEmpty($TELEGRAM_BOT_TOKEN)) {
    Write-Host "Error: TELEGRAM_BOT_TOKEN not found in .env" -ForegroundColor Red
    exit 1
}

if ([string]::IsNullOrEmpty($NEON_DB_URL)) {
    Write-Host "Error: NEON_DB_URL not found in .env" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Credentials loaded from .env" -ForegroundColor Green
Write-Host ""

# Create deployment script content
$deployScript = @"
#!/bin/bash
set -e

echo "Installing Docker..."
if ! command -v docker &> /dev/null; then
    apt update
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
fi

if ! command -v docker-compose &> /dev/null; then
    apt install -y docker-compose
fi

echo "Configuring firewall..."
if ! command -v ufw &> /dev/null; then
    apt install -y ufw
fi
ufw allow 22/tcp
echo 'y' | ufw enable

echo "Cloning repository..."
mkdir -p /opt/agent-factory
cd /opt/agent-factory
if [ -d ".git" ]; then
    git pull origin main
else
    git clone https://github.com/Mikecranesync/Agent-Factory.git .
fi

echo "Creating .env file..."
cat > .env << 'ENVEOF'
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
TELEGRAM_ADMIN_CHAT_ID=$TELEGRAM_ADMIN_CHAT_ID
AUTHORIZED_TELEGRAM_USERS=$AUTHORIZED_TELEGRAM_USERS
TELEGRAM_RATE_LIMIT=10
DATABASE_PROVIDER=neon
NEON_DB_URL=$NEON_DB_URL
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4o-mini
OPENAI_API_KEY=$OPENAI_API_KEY
VOICE_MODE=edge
EDGE_VOICE=en-US-GuyNeural
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
LOG_LEVEL=INFO
ENVEOF
chmod 600 .env

echo "Building and starting bot..."
docker-compose build
docker-compose up -d

echo "Setting up systemd service..."
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

systemctl daemon-reload
systemctl enable agent-factory

echo "Setting up monitoring..."
cat > /opt/agent-factory/monitor.sh << 'MONITOREOF'
#!/bin/bash
HEALTH_URL="http://localhost:9876/health"
LOG_FILE="/opt/agent-factory/monitor.log"
timestamp=\$(date '+%Y-%m-%d %H:%M:%S')

if curl -sf "\$HEALTH_URL" > /dev/null; then
    echo "[\$timestamp] OK - Bot healthy" >> "\$LOG_FILE"
else
    echo "[\$timestamp] ERROR - Bot unhealthy, restarting..." >> "\$LOG_FILE"
    cd /opt/agent-factory
    docker-compose restart
    echo "[\$timestamp] Restart complete" >> "\$LOG_FILE"
fi
tail -1000 "\$LOG_FILE" > "\$LOG_FILE.tmp" && mv "\$LOG_FILE.tmp" "\$LOG_FILE"
MONITOREOF
chmod +x /opt/agent-factory/monitor.sh
(crontab -l 2>/dev/null | grep -v "monitor.sh"; echo "*/5 * * * * /opt/agent-factory/monitor.sh") | crontab -

echo "Deployment complete!"
docker-compose ps
"@

# Save to temp file
$tempScript = [System.IO.Path]::GetTempFileName() + ".sh"
$deployScript | Out-File -FilePath $tempScript -Encoding ASCII

Write-Host "Step 4-11: Running automated deployment on VPS..." -ForegroundColor Yellow
Write-Host "(This may take 5-10 minutes)" -ForegroundColor Yellow
Write-Host ""

# Execute on VPS
try {
    $result = Get-Content $tempScript | ssh "$SSH_USER@$VPS_IP" "bash"
    Write-Host $result
    Write-Host ""
    Write-Host "✓ Deployment completed successfully" -ForegroundColor Green
} catch {
    Write-Host "✗ Deployment failed" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
} finally {
    Remove-Item $tempScript -ErrorAction SilentlyContinue
}

# Test deployment
Write-Host ""
Write-Host "Step 12: Testing deployment..." -ForegroundColor Yellow

try {
    $healthStatus = ssh "$SSH_USER@$VPS_IP" "curl -sf http://localhost:9876/health" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Health check passing" -ForegroundColor Green
        Write-Host "Response: $healthStatus"
    } else {
        Write-Host "⚠ Health check not responding yet (may still be starting up)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Health check test failed (bot may still be starting up)" -ForegroundColor Yellow
}

# Final summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Blue
Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""
Write-Host "Bot Details:" -ForegroundColor Yellow
Write-Host "  VPS IP: $VPS_IP"
Write-Host "  SSH User: $SSH_USER"
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Open Telegram and search for your bot"
Write-Host "2. Send /start to test the bot"
Write-Host "3. Bot should respond with welcome message"
Write-Host ""
Write-Host "Useful Commands:" -ForegroundColor Yellow
Write-Host "  View logs:    ssh $SSH_USER@$VPS_IP 'cd /opt/agent-factory && docker-compose logs -f'"
Write-Host "  Restart bot:  ssh $SSH_USER@$VPS_IP 'cd /opt/agent-factory && docker-compose restart'"
Write-Host "  Stop bot:     ssh $SSH_USER@$VPS_IP 'cd /opt/agent-factory && docker-compose down'"
Write-Host "  Check health: ssh $SSH_USER@$VPS_IP 'curl http://localhost:9876/health'"
Write-Host ""
Write-Host "✓ Bot is now running 24/7 on your VPS!" -ForegroundColor Green
Write-Host ""

#!/bin/bash
# Agent Factory - Quick Deployment Script
# Automates deployment steps for Render.com

set -e  # Exit on error

echo "=========================================="
echo "AGENT FACTORY - DEPLOYMENT HELPER"
echo "=========================================="
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "   Please create .env file with required variables"
    exit 1
fi

echo "✅ .env file found"
echo ""

# Load environment variables
source .env

# Validate critical environment variables
REQUIRED_VARS=(
    "TELEGRAM_BOT_TOKEN"
    "TELEGRAM_ADMIN_CHAT_ID"
    "AUTHORIZED_TELEGRAM_USERS"
    "SUPABASE_URL"
    "SUPABASE_KEY"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "❌ Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please set these variables in your .env file"
    exit 1
fi

echo "✅ All required environment variables present"
echo ""

# Ask for Render service URL
echo "Enter your Render.com service URL:"
echo "(e.g., https://agent-factory-telegram-bot.onrender.com)"
read -p "> " SERVICE_URL

if [ -z "$SERVICE_URL" ]; then
    echo "❌ Service URL is required"
    exit 1
fi

echo ""
echo "=========================================="
echo "DEPLOYMENT STEPS"
echo "=========================================="
echo ""

# Step 1: Set Telegram webhook
echo "[1/3] Setting Telegram webhook..."
python scripts/deployment/set_telegram_webhook.py --service-url "$SERVICE_URL"

if [ $? -ne 0 ]; then
    echo "❌ Webhook setup failed"
    exit 1
fi

echo ""

# Step 2: Validate deployment
echo "[2/3] Validating deployment..."
python scripts/deployment/validate_deployment.py --service-url "$SERVICE_URL"

if [ $? -ne 0 ]; then
    echo "⚠️  Validation had issues, but continuing..."
fi

echo ""

# Step 3: Test bot
echo "[3/3] Testing bot..."
echo "Please send /start to your bot in Telegram"
echo "Press Enter when you've sent the message..."
read

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "Your bot is now running at:"
echo "  Service: $SERVICE_URL"
echo "  Health: $SERVICE_URL/health"
echo ""
echo "Next steps:"
echo "1. Set up UptimeRobot monitoring (see DEPLOYMENT_QUICK_START.md Step 5)"
echo "2. Monitor logs at: https://dashboard.render.com"
echo "3. Check bot is responding to commands"
echo ""

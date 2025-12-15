#!/bin/bash
#
# Production Bot Startup Script for Render
#
# This script:
# 1. Deploys database schema if needed
# 2. Starts the Telegram bot
#
# Exit codes:
#   0 - Normal exit (Ctrl+C)
#   1 - Database deployment failed
#   2 - Bot startup failed

set -e  # Exit on error

echo "============================================================"
echo "Agent Factory - Production Startup"
echo "============================================================"

# Step 1: Deploy database schema
echo ""
echo "[1/2] Deploying database schema..."
echo ""

if python scripts/automation/deploy_database_schema.py; then
    echo "✅ Database schema ready"
else
    echo "❌ Database schema deployment failed"
    exit 1
fi

# Step 2: Start bot
echo ""
echo "[2/2] Starting Telegram bot..."
echo ""

if poetry run python -m agent_factory.integrations.telegram; then
    echo "✅ Bot exited normally"
    exit 0
else
    echo "❌ Bot crashed"
    exit 2
fi

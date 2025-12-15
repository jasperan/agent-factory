#!/bin/bash
#
# RIVET Pro Telegram Bot - Production Deployment Script
# VPS: Hostinger Ubuntu (72.60.175.144)
# Location: /root/Agent-Factory/deploy_rivet_pro.sh
#
# Usage:
#   ./deploy_rivet_pro.sh          # Deploy/update bot
#   ./deploy_rivet_pro.sh --check  # Check status only
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
BOT_LOG="$LOG_DIR/bot.log"
ERROR_LOG="$LOG_DIR/bot-error.log"
HEALTH_URL="http://localhost:9876/health"
LOCK_FILE="$SCRIPT_DIR/.telegram_bot.lock"

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}  RIVET Pro Telegram Bot - Deployment Script${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# ============================================================================
# Validation Functions
# ============================================================================

check_env_file() {
    print_info "Checking .env file..."

    if [ ! -f "$SCRIPT_DIR/.env" ]; then
        print_error ".env file not found!"
        echo ""
        echo "Please create .env with required variables:"
        echo "  - TELEGRAM_BOT_TOKEN"
        echo "  - SUPABASE_URL"
        echo "  - SUPABASE_SERVICE_ROLE_KEY"
        echo "  - OPENAI_API_KEY (or USE_OLLAMA=true)"
        echo ""
        echo "Copy from .env.vps template:"
        echo "  cp .env.vps .env"
        echo "  nano .env"
        exit 1
    fi

    # Check for required variables
    local required_vars=(
        "TELEGRAM_BOT_TOKEN"
        "SUPABASE_URL"
    )

    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$SCRIPT_DIR/.env"; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        exit 1
    fi

    print_success ".env file validated"
}

check_poetry() {
    print_info "Checking Poetry installation..."

    if ! command -v poetry &> /dev/null; then
        print_error "Poetry not installed!"
        echo ""
        echo "Install Poetry:"
        echo "  curl -sSL https://install.python-poetry.org | python3 -"
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
        exit 1
    fi

    print_success "Poetry installed: $(poetry --version)"
}

check_python() {
    print_info "Checking Python version..."

    local python_version=$(python3 --version 2>&1 | awk '{print $2}')
    local major=$(echo $python_version | cut -d. -f1)
    local minor=$(echo $python_version | cut -d. -f2)

    if [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 11 ]); then
        print_error "Python 3.11+ required, found $python_version"
        echo ""
        echo "Install Python 3.11:"
        echo "  sudo apt update"
        echo "  sudo apt install -y python3.11 python3.11-venv"
        exit 1
    fi

    print_success "Python $python_version (OK)"
}

check_bot_status() {
    print_info "Checking bot status..."

    # Check lock file
    if [ -f "$LOCK_FILE" ]; then
        print_warning "Lock file exists: $LOCK_FILE"
    fi

    # Check health endpoint
    if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
        local health_response=$(curl -s "$HEALTH_URL")
        local pid=$(echo "$health_response" | grep -o '"pid":[0-9]*' | cut -d: -f2)
        print_warning "Bot is already running (PID: $pid)"
        echo ""
        echo "Health response:"
        echo "$health_response" | python3 -m json.tool 2>/dev/null || echo "$health_response"
        echo ""
        return 0
    else
        print_info "Bot is not running"
        return 1
    fi
}

# ============================================================================
# Installation Functions
# ============================================================================

install_dependencies() {
    print_info "Installing Python dependencies..."

    cd "$SCRIPT_DIR"

    # Install dependencies without dev packages
    if poetry install --only main --no-interaction --no-ansi; then
        print_success "Dependencies installed"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi

    # Verify bot imports
    print_info "Verifying bot installation..."
    if poetry run python -c "from agent_factory.integrations.telegram.bot import TelegramBot; print('OK')" 2>&1 | grep -q "OK"; then
        print_success "Bot modules verified"
    else
        print_error "Bot modules failed to import"
        exit 1
    fi
}

create_log_directory() {
    print_info "Creating log directory..."
    mkdir -p "$LOG_DIR"
    print_success "Log directory ready: $LOG_DIR"
}

# ============================================================================
# Bot Management Functions
# ============================================================================

stop_bot() {
    print_info "Stopping bot..."

    # Try health endpoint to get PID
    if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
        local health_response=$(curl -s "$HEALTH_URL")
        local pid=$(echo "$health_response" | grep -o '"pid":[0-9]*' | cut -d: -f2)

        if [ -n "$pid" ]; then
            print_info "Found bot process (PID: $pid)"
            print_info "Sending SIGTERM..."
            kill -TERM "$pid" 2>/dev/null || true

            # Wait for graceful shutdown (max 10 seconds)
            local count=0
            while [ $count -lt 10 ] && kill -0 "$pid" 2>/dev/null; do
                sleep 1
                count=$((count + 1))
            done

            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                print_warning "Graceful shutdown failed, forcing..."
                kill -9 "$pid" 2>/dev/null || true
            fi

            print_success "Bot stopped"
            sleep 2  # Wait for port release
            return 0
        fi
    fi

    # Fallback: kill by process name
    if pgrep -f "telegram_bot.py" > /dev/null; then
        print_warning "Killing bot by process name..."
        pkill -f "telegram_bot.py" || true
        sleep 2
        print_success "Bot stopped"
        return 0
    fi

    print_info "Bot was not running"

    # Remove stale lock file
    if [ -f "$LOCK_FILE" ]; then
        print_info "Removing stale lock file..."
        rm -f "$LOCK_FILE"
    fi

    return 0
}

start_bot() {
    print_info "Starting bot..."

    cd "$SCRIPT_DIR"

    # Start bot in background
    nohup poetry run python telegram_bot.py > "$BOT_LOG" 2> "$ERROR_LOG" &
    local bot_pid=$!

    print_info "Bot started (PID: $bot_pid)"
    print_info "Waiting for initialization..."

    # Wait for health endpoint (max 15 seconds)
    local count=0
    while [ $count -lt 15 ]; do
        if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
            local health_response=$(curl -s "$HEALTH_URL")
            print_success "Bot is running!"
            echo ""
            echo "Health response:"
            echo "$health_response" | python3 -m json.tool 2>/dev/null || echo "$health_response"
            echo ""
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done

    print_error "Bot failed to start (health endpoint unreachable)"
    echo ""
    echo "Check logs:"
    echo "  tail -n 50 $ERROR_LOG"
    exit 1
}

# ============================================================================
# Main Deployment Flow
# ============================================================================

deploy() {
    print_header
    echo ""

    # Validations
    check_python
    check_poetry
    check_env_file
    echo ""

    # Check current status
    local bot_running=false
    if check_bot_status; then
        bot_running=true
        echo ""
        read -p "Bot is running. Restart? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Deployment cancelled"
            exit 0
        fi
    fi
    echo ""

    # Installation
    create_log_directory
    install_dependencies
    echo ""

    # Stop if running
    if [ "$bot_running" = true ]; then
        stop_bot
        echo ""
    fi

    # Start bot
    start_bot

    # Final status
    echo ""
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}  ✅ Deployment Complete!${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo ""
    echo "📊 Status:"
    echo "  - Bot PID: $(pgrep -f telegram_bot.py)"
    echo "  - Health: $HEALTH_URL"
    echo "  - Logs: $BOT_LOG"
    echo ""
    echo "🔧 Management:"
    echo "  - View logs: tail -f $BOT_LOG"
    echo "  - Check health: curl $HEALTH_URL"
    echo "  - Restart: ./deploy_rivet_pro.sh"
    echo ""
    echo "🤖 Telegram:"
    echo "  - Bot: @Agent_Factory_Bot (or your bot username)"
    echo "  - Test: Send /start to the bot"
    echo ""
    echo "⚙️  systemd (optional):"
    echo "  - Enable: sudo systemctl enable rivet-pro"
    echo "  - Start: sudo systemctl start rivet-pro"
    echo "  - Status: sudo systemctl status rivet-pro"
    echo ""
}

status_only() {
    print_header
    echo ""
    check_bot_status
    echo ""

    if [ -f "$BOT_LOG" ]; then
        echo "Recent logs:"
        echo "----------------------------------------"
        tail -n 20 "$BOT_LOG"
        echo "----------------------------------------"
    fi
    echo ""
}

# ============================================================================
# Entry Point
# ============================================================================

case "${1:-}" in
    --check|--status|-s)
        status_only
        ;;
    --help|-h)
        echo "RIVET Pro Deployment Script"
        echo ""
        echo "Usage:"
        echo "  ./deploy_rivet_pro.sh           Deploy/restart bot"
        echo "  ./deploy_rivet_pro.sh --check   Check bot status"
        echo "  ./deploy_rivet_pro.sh --help    Show this help"
        echo ""
        ;;
    *)
        deploy
        ;;
esac

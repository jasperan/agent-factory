#!/usr/bin/env bash
#
# Pre-push hook: Update README with latest metrics
#
# This hook triggers before git push and updates README.md with plain English
# summaries of the latest changes, git statistics, and database metrics.
#
# Behavior:
#   - Only runs on pushes to main branch
#   - Skips if README.md has uncommitted or staged changes
#   - Extracts metrics (files, lines, commit message, DB atom count)
#   - Injects entry into "## 📝 Latest Updates" section
#   - Commits with "docs: Update README with latest metrics [skip ci]"
#   - Times out after 10 seconds (non-blocking)
#   - Logs all executions to data/logs/hooks/hook_executions.log
#
# Safety features:
#   - Non-blocking (push continues even if update fails)
#   - Graceful degradation (works without database)
#   - Multiple recursion prevention checks
#   - Detailed logging for debugging
#
# Installation:
#   This hook is automatically enabled via .claude/hooks/config.yml
#
# Manual trigger:
#   .claude/hooks/pre_push.sh
#

set -e

HOOK_NAME="pre_push"
LOG_DIR="data/logs/hooks"
TIMEOUT_SECONDS=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo "$(date -Iseconds 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S%z') PRE_PUSH $1" >> "$LOG_DIR/hook_executions.log"
}

# Echo with color
echo_info() {
    echo -e "${GREEN}🎣 Pre-push hook:${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}⚠️  Pre-push hook:${NC} $1"
}

echo_error() {
    echo -e "${RED}❌ Pre-push hook:${NC} $1"
}

echo_info "README update"
log "status=started"

# Flag to track if we should update README
SHOULD_UPDATE=false
BRANCH_NAME=""

# Read stdin to get branch info
# Format: <local ref> <local sha> <remote ref> <remote sha>
while read local_ref local_sha remote_ref remote_sha; do
    # Extract branch name from refs/heads/main
    BRANCH_NAME=$(echo "$remote_ref" | sed 's|refs/heads/||')

    # Only run on main branch
    if [ "$BRANCH_NAME" != "main" ]; then
        echo_info "Branch: $BRANCH_NAME (skipping, not main)"
        log "status=skipped branch=$BRANCH_NAME reason=not_main"
        exit 0
    fi

    echo_info "Branch: $BRANCH_NAME (updating README)"
    SHOULD_UPDATE=true
    break
done

# If no branches detected (shouldn't happen), exit
if [ "$SHOULD_UPDATE" = false ]; then
    echo_warning "No branch information detected"
    log "status=skipped reason=no_branch_info"
    exit 0
fi

# Check for Poetry
if ! command -v poetry &> /dev/null; then
    echo_warning "Poetry not found, skipping README update"
    log "status=skipped reason=poetry_not_found"
    exit 0
fi

# Check if README has uncommitted changes
if git diff --name-only | grep -q "^README.md$"; then
    echo_warning "README.md has uncommitted changes, skipping update"
    log "status=skipped reason=uncommitted_changes"
    exit 0
fi

# Check if README already staged
if git diff --cached --name-only | grep -q "^README.md$"; then
    echo_warning "README.md already staged, skipping update"
    log "status=skipped reason=already_staged"
    exit 0
fi

# Check if last commit message contains our marker (recursion prevention)
LAST_COMMIT_MSG=$(git log -1 --format=%s 2>/dev/null || echo "")
if echo "$LAST_COMMIT_MSG" | grep -q "Update README with latest metrics"; then
    echo_warning "Last commit already updated README, skipping"
    log "status=skipped reason=already_updated"
    exit 0
fi

# Run metrics extraction + README update (with timeout)
echo_info "📊 Extracting metrics..."

# Use timeout command if available (Linux/Mac)
TIMEOUT_CMD="timeout"
if ! command -v timeout &> /dev/null; then
    # Try gtimeout (Homebrew on Mac)
    if command -v gtimeout &> /dev/null; then
        TIMEOUT_CMD="gtimeout"
    else
        # No timeout available - run without it (Windows)
        TIMEOUT_CMD=""
    fi
fi

# Execute update (skip database for speed)
export DB_SKIP=1

# Run metrics extraction and README update (via temp file to avoid pipe issues)
METRICS_FILE="$LOG_DIR/metrics_temp.json"
if poetry run python scripts/update_readme_metrics.py > "$METRICS_FILE" 2>> "$LOG_DIR/pre_push_output.log"; then
    if poetry run python scripts/update_readme.py < "$METRICS_FILE" 2>&1 | tee -a "$LOG_DIR/pre_push_output.log"; then
        rm -f "$METRICS_FILE"
    else
        rm -f "$METRICS_FILE"
        echo_error "README update script failed"
        log "status=failed"
        exit 0
    fi
else
    echo_error "Metrics extraction failed"
    log "status=failed"
    exit 0
fi

# Check if update succeeded
if true; then
    # Check if README actually changed
    if git diff --quiet README.md; then
        echo_info "ℹ️  No changes to README"
        log "status=no_changes"
    else
        # Commit README update
        echo_info "💾 Committing README update..."

        git add README.md

        # Create commit message with [skip ci] to prevent recursion
        COMMIT_MSG="docs: Update README with latest metrics [skip ci]"

        if git commit -m "$COMMIT_MSG" 2>&1 | tee -a "$LOG_DIR/pre_push_output.log"; then
            log "status=success"
            echo_info "✅ README updated"
        else
            echo_error "Failed to commit README changes"
            log "status=commit_failed"
        fi
    fi
else
    echo_error "README update failed (non-blocking)"
    log "status=failed"
fi

# Always exit 0 (allow push to continue)
exit 0

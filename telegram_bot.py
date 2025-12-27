#!/usr/bin/env python3
"""
Telegram Bot for Agent Factory - Primary User Interface

User's Goal: "Control everything from phone/desktop without terminal interaction"

This bot is the PRIMARY interface for monitoring and controlling the Agent Factory
system. Commands allow you to:
- Check agent status (/status)
- Approve/reject items (/approve, /reject)
- View metrics (/metrics)
- Create issues (/issue)
- Monitor agents (/agents)

Based on Complete GitHub Strategy + Telegram-first interface requirement.

Deployment:
- Run continuously (systemd/supervisor/tmux)
- Receives notifications from agents
- Sends daily standups (8 AM user timezone)
- Handles approvals for human-in-loop workflow

Usage:
    python telegram_bot.py                  # Run foreground
    tmux new -s telegram "python telegram_bot.py"  # Background
    systemctl start telegram-bot            # With systemd

"""

import os
import sys
import logging
import asyncio
from datetime import datetime, time as dt_time
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment first
load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from telegram.constants import ParseMode

from agent_factory.memory.storage import SupabaseMemoryStorage
from agent_factory.integrations.telegram.rivet_pro_handlers import RIVETProHandlers
from agent_factory.integrations.telegram.langgraph_handlers import LangGraphHandlers
from agent_factory.integrations.telegram.admin import (
    AdminDashboard,
    AgentManager,
    ContentReviewer,
    GitHubActions,
    KBManager,
    Analytics,
    SystemControl,
)
from agent_factory.integrations.telegram.scaffold_handlers import ScaffoldHandlers
from agent_factory.integrations.telegram.tier0_handlers import TIER0Handlers

# ============================================================================
# Configuration
# ============================================================================

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
if not TELEGRAM_BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not set in .env")
    print("Get token from @BotFather on Telegram")
    exit(1)

# Authorized Users (comma-separated Telegram user IDs)
AUTHORIZED_USERS = os.getenv("AUTHORIZED_TELEGRAM_USERS", "").split(",")
AUTHORIZED_USERS = [int(user_id.strip()) for user_id in AUTHORIZED_USERS if user_id.strip()]

# Daily Standup Time (24-hour format)
STANDUP_HOUR = int(os.getenv("STANDUP_HOUR", "8"))  # 8 AM default
STANDUP_MINUTE = int(os.getenv("STANDUP_MINUTE", "0"))

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("telegram_bot")

# Supabase storage
storage = SupabaseMemoryStorage()


# ============================================================================
# Authorization Middleware
# ============================================================================

def authorized_only(func):
    """Decorator to restrict commands to authorized users"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id

        # If no authorized users configured, allow all (dev mode)
        if not AUTHORIZED_USERS:
            logger.warning("No AUTHORIZED_TELEGRAM_USERS set, allowing all users (dev mode)")
            return await func(update, context)

        if user_id not in AUTHORIZED_USERS:
            logger.warning(f"Unauthorized access attempt from user {user_id}")
            await update.message.reply_text(
                "❌ *Unauthorized*\n\n"
                "You are not authorized to use this bot.\n"
                f"Your user ID: `{user_id}`\n\n"
                "Contact the bot owner to get access.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        return await func(update, context)

    return wrapper


# ============================================================================
# Command Handlers
# ============================================================================

@authorized_only
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message with command list"""
    await update.message.reply_text(
        "🤖 *Agent Factory Bot*\n\n"
        "Control your autonomous agent system from Telegram.\n\n"
        "*Agent Workflows:*\n"
        "/research <query> - Multi-agent research pipeline\n"
        "/consensus <query> - 3 agents vote on best answer\n"
        "/analyze <task> - Supervisor routes to specialists\n\n"
        "*System Commands:*\n"
        "/status - Agent health dashboard\n"
        "/agents - List all agents + uptime\n"
        "/metrics - KPIs (subs, revenue, atoms)\n"
        "/approve <id> - Approve pending item\n"
        "/reject <id> <reason> - Reject with feedback\n"
        "/issue <title> - Create GitHub issue\n\n"
        "*Daily Standup:* Delivered at 8 AM\n"
        "*Notifications:* Approval requests, alerts\n\n"
        "Use /help for detailed command docs.",
        parse_mode=ParseMode.MARKDOWN
    )


@authorized_only
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detailed help for all commands"""
    await update.message.reply_text(
        "📖 *Command Reference*\n\n"

        "*Agent Workflows (LangGraph):*\n\n"

        "*/research <query>*\n"
        "Run multi-agent research workflow with quality gates. "
        "Planner → Researcher → Analyzer → Writer. "
        "Retries if quality < 70%. Includes LangFuse trace link.\n"
        "Example: `/research What is a PLC?`\n\n"

        "*/consensus <query>*\n"
        "Get consensus from 3 specialist agents. Technical expert, practical expert, "
        "and teaching expert generate answers. Judge picks best one.\n"
        "Example: `/consensus Best PLC for beginners?`\n\n"

        "*/analyze <task>*\n"
        "Supervisor analyzes task and delegates to specialist teams "
        "(research, analysis, coding). Combines results.\n"
        "Example: `/analyze Create PLC troubleshooting guide`\n\n"

        "*System Commands:*\n\n"

        "*/status*\n"
        "Get real-time agent status dashboard. Shows running agents, pending jobs, "
        "approval queue.\n\n"

        "*/agents*\n"
        "List all 18 agents with uptime, tasks completed, current status.\n\n"

        "*/metrics*\n"
        "View KPIs: YouTube subscribers, revenue, knowledge atoms, video count.\n\n"

        "*/approve <id>*\n"
        "Approve pending item (video script, final video, knowledge atom). "
        "Example: `/approve abc-123`\n\n"

        "*/reject <id> <reason>*\n"
        "Reject item with feedback for agent to fix. "
        "Example: `/reject abc-123 Voice pacing too fast`\n\n"

        "*/issue <title>*\n"
        "Create GitHub issue. Multi-line titles supported. "
        "Example: `/issue Fix Research Agent timeout`\n\n"

        "*Notifications:*\n"
        "- Daily standup (8 AM)\n"
        "- Approval requests (real-time)\n"
        "- Agent failures (within 10 min)\n"
        "- Negative trends (>20% metric drop)\n\n"

        "*Privacy:*\n"
        "Only authorized Telegram user IDs can use this bot. "
        f"Your ID: `{update.effective_user.id}`",
        parse_mode=ParseMode.MARKDOWN
    )


@authorized_only
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get real-time agent status dashboard"""
    try:
        # Fetch agent status
        response = storage.client.table("agent_status") \
            .select("*") \
            .execute()

        agents = response.data

        if not agents:
            await update.message.reply_text(
                "⚠️ No agents registered yet.\n\n"
                "Start the orchestrator to register agents:\n"
                "`python orchestrator.py`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Count by status
        running = sum(1 for a in agents if a["status"] == "running")
        idle = sum(1 for a in agents if a["status"] == "idle")
        error = sum(1 for a in agents if a["status"] == "error")
        stopped = sum(1 for a in agents if a["status"] == "stopped")

        # Fetch pending jobs
        jobs_response = storage.client.table("agent_jobs") \
            .select("*") \
            .eq("status", "pending") \
            .execute()

        pending_jobs = len(jobs_response.data)

        # Fetch approval queue
        approvals_response = storage.client.table("approval_requests") \
            .select("*") \
            .eq("status", "pending") \
            .execute()

        pending_approvals = len(approvals_response.data)

        # Build status message
        status_emoji = "🟢" if error == 0 else "🔴"

        message = (
            f"{status_emoji} *Agent Factory Status*\n\n"
            f"*Agents:*\n"
            f"  🟢 Running: {running}\n"
            f"  ⚪️ Idle: {idle}\n"
            f"  🔴 Error: {error}\n"
            f"  ⚫️ Stopped: {stopped}\n\n"
            f"*Work Queue:*\n"
            f"  📋 Pending Jobs: {pending_jobs}\n"
            f"  ⏳ Awaiting Approval: {pending_approvals}\n\n"
        )

        # Show agents with errors
        if error > 0:
            error_agents = [a for a in agents if a["status"] == "error"]
            message += "*⚠️ Errors:*\n"
            for agent in error_agents:
                agent_name = agent["agent_name"]
                error_msg = agent.get("error_message", "Unknown error")[:50]
                message += f"  • {agent_name}: {error_msg}\n"

        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Failed to fetch status: {e}")
        await update.message.reply_text(
            f"❌ *Error fetching status*\n\n`{str(e)}`",
            parse_mode=ParseMode.MARKDOWN
        )


@authorized_only
async def cmd_agents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all agents with details"""
    try:
        response = storage.client.table("agent_status") \
            .select("*") \
            .execute()

        agents = response.data

        if not agents:
            await update.message.reply_text(
                "No agents registered yet.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Sort by name
        agents.sort(key=lambda a: a["agent_name"])

        message = "🤖 *All Agents*\n\n"

        for agent in agents:
            name = agent["agent_name"]
            status = agent["status"]
            completed = agent.get("tasks_completed_today", 0)
            failed = agent.get("tasks_failed_today", 0)
            current_task = agent.get("current_task", "Idle")

            # Emoji by status
            emoji = {
                "running": "🟢",
                "idle": "⚪️",
                "error": "🔴",
                "stopped": "⚫️"
            }.get(status, "❓")

            message += (
                f"{emoji} *{name}*\n"
                f"  Status: {status.upper()}\n"
                f"  Today: {completed} ✅  {failed} ❌\n"
                f"  Current: {current_task}\n\n"
            )

        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Failed to fetch agents: {e}")
        await update.message.reply_text(
            f"❌ Error: `{str(e)}`",
            parse_mode=ParseMode.MARKDOWN
        )


@authorized_only
async def cmd_metrics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View KPIs: subs, revenue, atoms, videos"""
    try:
        # Fetch knowledge atoms count
        atoms_response = storage.client.table("knowledge_atoms") \
            .select("id", count="exact") \
            .execute()

        atom_count = atoms_response.count or 0

        # Fetch published videos count
        videos_response = storage.client.table("published_videos") \
            .select("id", count="exact") \
            .execute()

        video_count = videos_response.count or 0

        # Fetch latest video analytics (placeholder until YouTube API integrated)
        # TODO: Implement YouTube Analytics API integration
        subscribers = "N/A (YouTube API pending)"
        revenue = "N/A (YouTube API pending)"

        message = (
            "📊 *Key Metrics*\n\n"
            f"*YouTube:*\n"
            f"  Subscribers: {subscribers}\n"
            f"  Revenue: {revenue}\n\n"
            f"*Knowledge Base:*\n"
            f"  Atoms: {atom_count}\n"
            f"  Videos: {video_count}\n\n"
            "*Note:* YouTube metrics available after Week 4 launch + API integration."
        )

        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Failed to fetch metrics: {e}")
        await update.message.reply_text(
            f"❌ Error: `{str(e)}`",
            parse_mode=ParseMode.MARKDOWN
        )


@authorized_only
async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve pending item"""
    # Parse arguments
    args = context.args

    if not args:
        await update.message.reply_text(
            "Usage: `/approve <id>`\n\n"
            "Example: `/approve abc-123`\n\n"
            "Get pending IDs with /status",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    item_id = args[0]

    try:
        # Find approval request
        response = storage.client.table("approval_requests") \
            .select("*") \
            .eq("id", item_id) \
            .eq("status", "pending") \
            .execute()

        if not response.data:
            await update.message.reply_text(
                f"❌ Approval request `{item_id}` not found or already processed.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        approval = response.data[0]
        approval_type = approval["approval_type"]

        # Update status
        storage.client.table("approval_requests") \
            .update({
                "status": "approved",
                "reviewed_by": f"telegram_user_{update.effective_user.id}",
                "reviewed_at": datetime.now().isoformat(),
                "feedback": "Approved via Telegram"
            }) \
            .eq("id", item_id) \
            .execute()

        await update.message.reply_text(
            f"✅ *Approved*\n\n"
            f"Type: {approval_type}\n"
            f"ID: `{item_id}`\n\n"
            "Agent will proceed with next steps.",
            parse_mode=ParseMode.MARKDOWN
        )

        logger.info(f"Approved {approval_type} {item_id} via Telegram")

    except Exception as e:
        logger.error(f"Failed to approve {item_id}: {e}")
        await update.message.reply_text(
            f"❌ Error: `{str(e)}`",
            parse_mode=ParseMode.MARKDOWN
        )


@authorized_only
async def cmd_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reject pending item with feedback"""
    args = context.args

    if len(args) < 2:
        await update.message.reply_text(
            "Usage: `/reject <id> <reason>`\n\n"
            "Example: `/reject abc-123 Voice pacing too fast`\n\n"
            "Get pending IDs with /status",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    item_id = args[0]
    reason = " ".join(args[1:])

    try:
        # Find approval request
        response = storage.client.table("approval_requests") \
            .select("*") \
            .eq("id", item_id) \
            .eq("status", "pending") \
            .execute()

        if not response.data:
            await update.message.reply_text(
                f"❌ Approval request `{item_id}` not found or already processed.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        approval = response.data[0]
        approval_type = approval["approval_type"]

        # Update status
        storage.client.table("approval_requests") \
            .update({
                "status": "rejected",
                "reviewed_by": f"telegram_user_{update.effective_user.id}",
                "reviewed_at": datetime.now().isoformat(),
                "feedback": reason
            }) \
            .eq("id", item_id) \
            .execute()

        await update.message.reply_text(
            f"❌ *Rejected*\n\n"
            f"Type: {approval_type}\n"
            f"ID: `{item_id}`\n"
            f"Feedback: {reason}\n\n"
            "Agent will revise and resubmit.",
            parse_mode=ParseMode.MARKDOWN
        )

        logger.info(f"Rejected {approval_type} {item_id} via Telegram: {reason}")

    except Exception as e:
        logger.error(f"Failed to reject {item_id}: {e}")
        await update.message.reply_text(
            f"❌ Error: `{str(e)}`",
            parse_mode=ParseMode.MARKDOWN
        )


@authorized_only
async def cmd_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create GitHub issue"""
    args = context.args

    if not args:
        await update.message.reply_text(
            "Usage: `/issue <title>`\n\n"
            "Example: `/issue Fix Research Agent timeout`\n\n"
            "Multi-line titles supported:\n"
            "/issue This is the title\\n"
            "This is the description",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    title = " ".join(args)

    # TODO: Implement GitHub API integration
    # For now, just log and acknowledge

    logger.info(f"GitHub issue requested via Telegram: {title}")

    await update.message.reply_text(
        f"📝 *Issue Created*\n\n"
        f"Title: {title}\n\n"
        "*(Note: GitHub API integration pending. Issue logged for AI Chief of Staff.)*",
        parse_mode=ParseMode.MARKDOWN
    )


# ============================================================================
# Daily Standup
# ============================================================================

async def send_daily_standup(context: ContextTypes.DEFAULT_TYPE):
    """Send daily standup to all authorized users"""
    try:
        logger.info("Sending daily standup...")

        # Fetch agent status
        agents_response = storage.client.table("agent_status") \
            .select("*") \
            .execute()

        agents = agents_response.data

        # Count by status
        running = sum(1 for a in agents if a["status"] == "running")
        error = sum(1 for a in agents if a["status"] == "error")

        # Fetch tasks completed/failed yesterday
        # (Reset daily counters at midnight, so "today" = yesterday)
        total_completed = sum(a.get("tasks_completed_today", 0) for a in agents)
        total_failed = sum(a.get("tasks_failed_today", 0) for a in agents)

        # Fetch pending work
        jobs_response = storage.client.table("agent_jobs") \
            .select("*") \
            .eq("status", "pending") \
            .execute()

        pending_jobs = len(jobs_response.data)

        # Build standup message
        status_emoji = "🟢" if error == 0 else "🔴"

        message = (
            f"☀️ *Daily Standup - {datetime.now().strftime('%Y-%m-%d')}*\n\n"
            f"{status_emoji} *System Status:* {'Healthy' if error == 0 else f'{error} agents with errors'}\n\n"
            f"*Yesterday:*\n"
            f"  ✅ Tasks Completed: {total_completed}\n"
            f"  ❌ Tasks Failed: {total_failed}\n\n"
            f"*Today:*\n"
            f"  📋 Pending Jobs: {pending_jobs}\n"
            f"  🤖 Active Agents: {running}\n\n"
            "Use /status for real-time dashboard."
        )

        # Send to all authorized users
        for user_id in AUTHORIZED_USERS:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Failed to send standup to user {user_id}: {e}")

        logger.info("Daily standup sent successfully")

    except Exception as e:
        logger.error(f"Failed to send daily standup: {e}")


# ============================================================================
# Main Application
# ============================================================================

def main():
    """Main entry point"""
    # Check environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        logger.error("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        exit(1)

    if not AUTHORIZED_USERS:
        logger.warning("No AUTHORIZED_TELEGRAM_USERS set in .env (dev mode, all users allowed)")

    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Initialize RIVET Pro handlers
    rivet_handlers = RIVETProHandlers()

    # Initialize LangGraph handlers
    langgraph_handlers = LangGraphHandlers()

    # Initialize Admin Panel
    admin_dashboard = AdminDashboard()
    agent_manager = AgentManager()
    content_reviewer = ContentReviewer()
    github_actions = GitHubActions()
    kb_manager = KBManager()
    analytics = Analytics()
    system_control = SystemControl()

    # Initialize SCAFFOLD handlers
    scaffold_handlers = ScaffoldHandlers(
        repo_root=project_root,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_cost=float(os.getenv("SCAFFOLD_MAX_COST", "5.0")),
        max_time_hours=float(os.getenv("SCAFFOLD_MAX_TIME_HOURS", "2.0")),
        dry_run=os.getenv("SCAFFOLD_DRY_RUN", "false").lower() == "true"
    )

    # Initialize TIER 0.1 handlers (CEO Command & Control)
    # WS-3 Integration: Pass rivet_handlers for voice → RIVET Pro routing
    tier0_handlers = TIER0Handlers(
        storage=storage,
        rivet_handlers=rivet_handlers,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # Register command handlers
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("agents", cmd_agents))
    application.add_handler(CommandHandler("metrics", cmd_metrics))
    application.add_handler(CommandHandler("approve", cmd_approve))
    application.add_handler(CommandHandler("reject", cmd_reject))
    application.add_handler(CommandHandler("issue", cmd_issue))

    # Register RIVET Pro handlers
    application.add_handler(CommandHandler("troubleshoot", rivet_handlers.handle_troubleshoot))
    application.add_handler(CommandHandler("upgrade", rivet_handlers.handle_upgrade))
    application.add_handler(CommandHandler("book_expert", rivet_handlers.handle_book_expert))
    application.add_handler(CommandHandler("my_sessions", rivet_handlers.handle_my_sessions))
    application.add_handler(CommandHandler("pro_stats", rivet_handlers.handle_pro_stats))
    application.add_handler(CommandHandler("vps_status", rivet_handlers.handle_vps_status))

    # Register LangGraph workflow handlers
    application.add_handler(CommandHandler("research", langgraph_handlers.handle_research))
    application.add_handler(CommandHandler("consensus", langgraph_handlers.handle_consensus))
    application.add_handler(CommandHandler("analyze", langgraph_handlers.handle_analyze))

    # Register SCAFFOLD handlers
    application.add_handler(CommandHandler("scaffold", scaffold_handlers.handle_scaffold_create))
    application.add_handler(CommandHandler("scaffold_status", scaffold_handlers.handle_scaffold_status))
    application.add_handler(CommandHandler("scaffold_history", scaffold_handlers.handle_scaffold_history))

    # Register Admin Panel handlers
    application.add_handler(CommandHandler("admin", admin_dashboard.handle_admin))
    application.add_handler(CallbackQueryHandler(admin_dashboard.handle_callback, pattern="^menu_"))

    # Agent management
    application.add_handler(CommandHandler("agents_admin", agent_manager.handle_agents))
    application.add_handler(CommandHandler("agent", agent_manager.handle_agent_detail))
    application.add_handler(CommandHandler("agent_logs", agent_manager.handle_agent_logs))

    # Content review
    application.add_handler(CommandHandler("content", content_reviewer.handle_content))

    # GitHub Actions
    application.add_handler(CommandHandler("deploy", github_actions.handle_deploy))
    application.add_handler(CommandHandler("workflow", github_actions.handle_workflow))
    application.add_handler(CommandHandler("workflows", github_actions.handle_workflows))
    application.add_handler(CommandHandler("workflow_status", github_actions.handle_workflow_status))
    application.add_handler(CallbackQueryHandler(github_actions.handle_deploy_confirm, pattern="^deploy_confirm$"))

    # KB management
    application.add_handler(CommandHandler("kb", kb_manager.handle_kb))
    application.add_handler(CommandHandler("kb_ingest", kb_manager.handle_kb_ingest))
    application.add_handler(CommandHandler("kb_search", kb_manager.handle_kb_search))
    application.add_handler(CommandHandler("kb_queue", kb_manager.handle_kb_queue))

    # Analytics
    application.add_handler(CommandHandler("metrics_admin", analytics.handle_metrics))
    application.add_handler(CommandHandler("costs", analytics.handle_costs))
    application.add_handler(CommandHandler("revenue", analytics.handle_revenue))

    # System control
    application.add_handler(CommandHandler("health", system_control.handle_health))
    application.add_handler(CommandHandler("db_health", system_control.handle_db_health))
    application.add_handler(CommandHandler("vps_status_admin", system_control.handle_vps_status))
    application.add_handler(CommandHandler("restart", system_control.handle_restart))

    # TIER 0.1: Voice and image message handlers (high priority)
    application.add_handler(
        MessageHandler(
            filters.VOICE,
            tier0_handlers.handle_voice_message
        ),
        group=0  # High priority
    )
    application.add_handler(
        MessageHandler(
            filters.PHOTO,
            tier0_handlers.handle_image_message
        ),
        group=0  # High priority
    )

    # Add message handler for natural language troubleshooting (lower priority)
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            rivet_handlers.handle_troubleshoot
        ),
        group=1  # Lower priority than command handlers
    )

    # Schedule daily standup (optional - requires job-queue extra)
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_daily(
            send_daily_standup,
            time=dt_time(hour=STANDUP_HOUR, minute=STANDUP_MINUTE)
        )
        logger.info("Daily standup scheduled")
    else:
        logger.warning("JobQueue not available - daily standup disabled")

    # Run bot
    logger.info("=" * 70)
    logger.info("Agent Factory Telegram Bot Started")
    logger.info("=" * 70)
    logger.info(f"Authorized Users: {len(AUTHORIZED_USERS)}")
    logger.info(f"Daily Standup: {STANDUP_HOUR:02d}:{STANDUP_MINUTE:02d}")
    logger.info("System Commands: /start, /help, /status, /agents, /metrics, /approve, /reject, /issue")
    logger.info("RIVET Pro: /troubleshoot, /upgrade, /book_expert, /my_sessions, /pro_stats")
    logger.info("SCAFFOLD: /scaffold, /scaffold_status, /scaffold_history")
    logger.info("Admin Panel: /admin, /agents_admin, /content, /deploy, /kb, /metrics_admin, /health")
    logger.info("TIER 0.1 (CEO Command & Control): Voice messages, Image OCR, Session management")
    logger.info("=" * 70)

    # Run polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

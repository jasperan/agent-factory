#!/usr/bin/env python3
"""
Rivet CMMS - Public Telegram Bot

This is the PUBLIC version of the Telegram bot for multi-tenant deployment.
All users access the same @RivetCMMS_bot, with data isolated by user_id.

Changes from personal RivetCEO bot:
- Removed AUTHORIZED_USERS gate (anyone can use)
- Admin commands protected by admin_users table
- Rate limiting on free tier
- Usage analytics for billing

Bot Commands (Public):
- /start - Onboarding + auto-provision
- /troubleshoot - AI troubleshooting
- /add_machine, /list_machines - Equipment management
- /upload_print, /chat_print - Electrical print Q&A
- /upload_manual, /manual_search - Manual library
- /upgrade - View pricing / upgrade tier
- /help - Command reference

Admin Commands (admin_users table only):
- /admin - Admin dashboard
- /deploy - Trigger deployments
- /metrics_admin - Revenue/usage analytics
- /health - System health check
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

# NEW: Public auth middleware
from agent_factory.integrations.telegram.public_auth import (
    auth, admin_only, super_admin_only, rate_limited, public_command
)

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
from agent_factory.integrations.telegram.print_handlers import (
    add_machine_command,
    list_machines_command,
    upload_print_command,
    list_prints_command,
    chat_print_command,
    end_chat_command,
    cancel_command,
    handle_print_document
)
from agent_factory.integrations.telegram.manual_handlers import (
    upload_manual_command,
    manual_search_command,
    manual_list_command,
    manual_gaps_command,
    handle_manual_document
)

# ============================================================================
# Configuration
# ============================================================================

# Bot Token - use PUBLIC_TELEGRAM_BOT_TOKEN for public bot
TELEGRAM_BOT_TOKEN = os.getenv("PUBLIC_TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN", "")
if not TELEGRAM_BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not set in .env")
    print("Get token from @BotFather on Telegram")
    exit(1)

# Beta Mode Configuration
BETA_MODE = os.getenv("BETA_MODE", "true").lower() == "true"
BETA_FULL_ACCESS = os.getenv("BETA_FULL_ACCESS", "true").lower() == "true"

if BETA_MODE:
    logger.info("=" * 70)
    logger.info("🚀 BETA MODE ENABLED - Full access for all users")
    logger.info("=" * 70)
    if BETA_FULL_ACCESS:
        logger.info("✨ BETA FULL ACCESS: No rate limits, unlimited features")

# Daily Standup Time (24-hour format) - admin only
STANDUP_HOUR = int(os.getenv("STANDUP_HOUR", "8"))
STANDUP_MINUTE = int(os.getenv("STANDUP_MINUTE", "0"))

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("rivet_public_bot")

# Supabase storage
storage = SupabaseMemoryStorage()


# ============================================================================
# Public Command Handlers
# ============================================================================

@public_command
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome + onboarding for new users"""
    # Delegate to RIVET Pro handlers (has full onboarding flow)
    pass  # Handled by rivet_handlers.handle_start


@public_command
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Public help command"""
    is_admin = auth.is_admin(update.effective_user.id)
    
    help_text = (
        "🔧 *Rivet CMMS - Command Reference*\n\n"
        
        "*Getting Started:*\n"
        "/start - Set up your account\n"
        "/tutorial - Interactive walkthrough\n"
        "/quickstart - Quick command overview\n\n"
        
        "*Troubleshooting:*\n"
        "Just type your question! Or use:\n"
        "/troubleshoot - Start a troubleshooting session\n"
        "🎤 Send voice message - Hands-free questions\n"
        "📷 Send photo - OCR equipment nameplates\n\n"
        
        "*Equipment Management:*\n"
        "/add_machine <name> - Add a machine\n"
        "/list_machines - View your machines\n\n"
        
        "*Electrical Prints:*\n"
        "/upload_print <machine> - Upload print PDF\n"
        "/list_prints <machine> - View prints\n"
        "/chat_print <machine> - Q&A with prints\n"
        "/end_chat - End print session\n\n"
        
        "*Manual Library:*\n"
        "/upload_manual - Add OEM manual\n"
        "/manual_search <query> - Search manuals\n"
        "/manual_list - Browse all manuals\n\n"
        
        "*Account:*\n"
        "/upgrade - View plans & pricing\n"
        "/my_sessions - Troubleshooting history\n"
        "/pro_stats - Your usage stats\n\n"
    )
    
    if is_admin:
        help_text += (
            "*━━━ Admin Commands ━━━*\n"
            "/admin - Admin dashboard\n"
            "/agents_admin - Manage agents\n"
            "/metrics_admin - Analytics\n"
            "/health - System status\n"
            "/deploy - Trigger deployment\n"
        )
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


# ============================================================================
# Admin Command Handlers (Protected)
# ============================================================================

@admin_only
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Get real-time system status"""
    try:
        response = storage.client.table("agent_status").select("*").execute()
        agents = response.data

        if not agents:
            await update.message.reply_text(
                "⚠️ No agents registered yet.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        running = sum(1 for a in agents if a["status"] == "running")
        error = sum(1 for a in agents if a["status"] == "error")

        jobs_response = storage.client.table("agent_jobs") \
            .select("*").eq("status", "pending").execute()
        pending_jobs = len(jobs_response.data)

        status_emoji = "🟢" if error == 0 else "🔴"

        # Get user count
        users_response = storage.client.table("rivet_users") \
            .select("id", count="exact").execute()
        user_count = users_response.count or 0

        message = (
            f"{status_emoji} *Rivet CMMS Status*\n\n"
            f"*Users:* {user_count}\n"
            f"*Agents:* {running} running, {error} errors\n"
            f"*Pending Jobs:* {pending_jobs}\n"
        )

        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Failed to fetch status: {e}")
        await update.message.reply_text(f"❌ Error: `{str(e)}`", parse_mode=ParseMode.MARKDOWN)


@admin_only
async def cmd_agents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: List all agents"""
    try:
        response = storage.client.table("agent_status").select("*").execute()
        agents = response.data

        if not agents:
            await update.message.reply_text("No agents registered.", parse_mode=ParseMode.MARKDOWN)
            return

        agents.sort(key=lambda a: a["agent_name"])
        message = "🤖 *All Agents*\n\n"

        for agent in agents:
            emoji = {"running": "🟢", "idle": "⚪️", "error": "🔴", "stopped": "⚫️"}.get(agent["status"], "❓")
            message += f"{emoji} *{agent['agent_name']}* - {agent['status']}\n"

        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: `{str(e)}`", parse_mode=ParseMode.MARKDOWN)


@admin_only  
async def cmd_metrics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: View business metrics"""
    try:
        # User counts by tier
        users = storage.client.table("rivet_users").select("tier").execute()
        tier_counts = {}
        for u in users.data:
            tier = u.get("tier", "free")
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        # Knowledge stats
        atoms = storage.client.table("knowledge_atoms").select("id", count="exact").execute()
        manuals = storage.client.table("equipment_manuals").select("id", count="exact").execute()

        message = (
            "📊 *Business Metrics*\n\n"
            f"*Users by Tier:*\n"
        )
        for tier, count in tier_counts.items():
            message += f"  {tier}: {count}\n"
        
        message += (
            f"\n*Knowledge Base:*\n"
            f"  Atoms: {atoms.count or 0}\n"
            f"  Manuals: {manuals.count or 0}\n"
        )

        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: `{str(e)}`", parse_mode=ParseMode.MARKDOWN)


@admin_only
async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Approve pending item"""
    args = context.args
    if not args:
        await update.message.reply_text("Usage: `/approve <id>`", parse_mode=ParseMode.MARKDOWN)
        return

    item_id = args[0]
    try:
        storage.client.table("approval_requests") \
            .update({
                "status": "approved",
                "reviewed_by": f"admin_{update.effective_user.id}",
                "reviewed_at": datetime.now().isoformat(),
            }) \
            .eq("id", item_id).execute()

        await update.message.reply_text(f"✅ Approved `{item_id}`", parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: `{str(e)}`", parse_mode=ParseMode.MARKDOWN)


@admin_only
async def cmd_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Reject pending item"""
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: `/reject <id> <reason>`", parse_mode=ParseMode.MARKDOWN)
        return

    item_id = args[0]
    reason = " ".join(args[1:])

    try:
        storage.client.table("approval_requests") \
            .update({
                "status": "rejected",
                "reviewed_by": f"admin_{update.effective_user.id}",
                "reviewed_at": datetime.now().isoformat(),
                "feedback": reason
            }) \
            .eq("id", item_id).execute()

        await update.message.reply_text(f"❌ Rejected `{item_id}`\nReason: {reason}", parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: `{str(e)}`", parse_mode=ParseMode.MARKDOWN)


# ============================================================================
# Daily Standup (Admin Only)
# ============================================================================

async def send_daily_standup(context: ContextTypes.DEFAULT_TYPE):
    """Send daily standup to all admins"""
    try:
        # Get all admins
        import psycopg2
        conn = psycopg2.connect(os.getenv("NEON_DB_URL"))
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id FROM admin_users")
        admin_ids = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        # Get stats
        users = storage.client.table("rivet_users").select("id", count="exact").execute()
        
        message = (
            f"☀️ *Daily Standup - {datetime.now().strftime('%Y-%m-%d')}*\n\n"
            f"*Total Users:* {users.count or 0}\n"
            "Use /metrics_admin for detailed stats."
        )

        for admin_id in admin_ids:
            try:
                await context.bot.send_message(chat_id=admin_id, text=message, parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                logger.error(f"Failed to send standup to {admin_id}: {e}")

    except Exception as e:
        logger.error(f"Failed to send daily standup: {e}")


# ============================================================================
# Main Application
# ============================================================================

def main():
    """Main entry point"""
    # Validate environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    neon_url = os.getenv("NEON_DB_URL")

    if not neon_url:
        logger.error("NEON_DB_URL must be set for public deployment")
        exit(1)

    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Initialize handlers
    rivet_handlers = RIVETProHandlers()
    langgraph_handlers = LangGraphHandlers()

    # Admin panel handlers
    admin_dashboard = AdminDashboard()
    agent_manager = AgentManager()
    content_reviewer = ContentReviewer()
    github_actions = GitHubActions()
    kb_manager = KBManager()
    analytics = Analytics()
    system_control = SystemControl()

    # SCAFFOLD handlers
    scaffold_handlers = ScaffoldHandlers(
        repo_root=project_root,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_cost=float(os.getenv("SCAFFOLD_MAX_COST", "5.0")),
        max_time_hours=float(os.getenv("SCAFFOLD_MAX_TIME_HOURS", "2.0")),
        dry_run=os.getenv("SCAFFOLD_DRY_RUN", "false").lower() == "true"
    )

    # TIER 0.1 handlers
    tier0_handlers = TIER0Handlers(
        storage=storage,
        rivet_handlers=rivet_handlers,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC COMMANDS (anyone can use)
    # ─────────────────────────────────────────────────────────────────────────
    
    application.add_handler(CommandHandler("help", cmd_help))
    
    # RIVET Pro (public)
    application.add_handler(CommandHandler("start", rivet_handlers.handle_start))
    application.add_handler(CommandHandler("troubleshoot", rivet_handlers.handle_troubleshoot))
    application.add_handler(CommandHandler("upgrade", rivet_handlers.handle_upgrade))
    application.add_handler(CommandHandler("book_expert", rivet_handlers.handle_book_expert))
    application.add_handler(CommandHandler("my_sessions", rivet_handlers.handle_my_sessions))
    application.add_handler(CommandHandler("pro_stats", rivet_handlers.handle_pro_stats))

    # Onboarding (public)
    application.add_handler(CommandHandler("tutorial", rivet_handlers.handle_tutorial))
    application.add_handler(CommandHandler("tour", rivet_handlers.handle_tour))
    application.add_handler(CommandHandler("quickstart", rivet_handlers.handle_quickstart))
    application.add_handler(CommandHandler("about", rivet_handlers.handle_about))
    application.add_handler(CommandHandler("pricing", rivet_handlers.handle_pricing))
    application.add_handler(CallbackQueryHandler(rivet_handlers.handle_onboarding_callback, pattern="^(onboard_|tour_)"))

    # Machine/Print handlers (public)
    application.add_handler(CommandHandler("add_machine", add_machine_command))
    application.add_handler(CommandHandler("list_machines", list_machines_command))
    application.add_handler(CommandHandler("upload_print", upload_print_command))
    application.add_handler(CommandHandler("list_prints", list_prints_command))
    application.add_handler(CommandHandler("chat_print", chat_print_command))
    application.add_handler(CommandHandler("end_chat", end_chat_command))
    application.add_handler(CommandHandler("cancel", cancel_command))

    # Manual Library (public)
    application.add_handler(CommandHandler("upload_manual", upload_manual_command))
    application.add_handler(CommandHandler("manual_search", manual_search_command))
    application.add_handler(CommandHandler("manual_list", manual_list_command))
    application.add_handler(CommandHandler("manual_gaps", manual_gaps_command))

    # LangGraph workflows (public - rate limited in handlers)
    application.add_handler(CommandHandler("research", langgraph_handlers.handle_research))
    application.add_handler(CommandHandler("consensus", langgraph_handlers.handle_consensus))
    application.add_handler(CommandHandler("analyze", langgraph_handlers.handle_analyze))

    # ─────────────────────────────────────────────────────────────────────────
    # ADMIN COMMANDS (admin_users table only)
    # ─────────────────────────────────────────────────────────────────────────
    
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("agents", cmd_agents))
    application.add_handler(CommandHandler("metrics", cmd_metrics))
    application.add_handler(CommandHandler("approve", cmd_approve))
    application.add_handler(CommandHandler("reject", cmd_reject))

    # Admin panel
    application.add_handler(CommandHandler("admin", admin_dashboard.handle_admin))
    application.add_handler(CallbackQueryHandler(admin_dashboard.handle_callback, pattern="^menu_"))
    application.add_handler(CommandHandler("agents_admin", agent_manager.handle_agents))
    application.add_handler(CommandHandler("agent", agent_manager.handle_agent_detail))
    application.add_handler(CommandHandler("agent_logs", agent_manager.handle_agent_logs))
    application.add_handler(CommandHandler("content", content_reviewer.handle_content))
    application.add_handler(CommandHandler("deploy", github_actions.handle_deploy))
    application.add_handler(CommandHandler("workflow", github_actions.handle_workflow))
    application.add_handler(CommandHandler("workflows", github_actions.handle_workflows))
    application.add_handler(CommandHandler("workflow_status", github_actions.handle_workflow_status))
    application.add_handler(CallbackQueryHandler(github_actions.handle_deploy_confirm, pattern="^deploy_confirm$"))
    application.add_handler(CommandHandler("kb", kb_manager.handle_kb))
    application.add_handler(CommandHandler("kb_ingest", kb_manager.handle_kb_ingest))
    application.add_handler(CommandHandler("kb_search", kb_manager.handle_kb_search))
    application.add_handler(CommandHandler("kb_queue", kb_manager.handle_kb_queue))
    application.add_handler(CommandHandler("metrics_admin", analytics.handle_metrics))
    application.add_handler(CommandHandler("costs", analytics.handle_costs))
    application.add_handler(CommandHandler("revenue", analytics.handle_revenue))
    application.add_handler(CommandHandler("health", system_control.handle_health))
    application.add_handler(CommandHandler("db_health", system_control.handle_db_health))
    application.add_handler(CommandHandler("vps_status", system_control.handle_vps_status))
    application.add_handler(CommandHandler("vps_status_admin", system_control.handle_vps_status))
    application.add_handler(CommandHandler("restart", system_control.handle_restart))
    
    # SCAFFOLD (admin only)
    application.add_handler(CommandHandler("scaffold", scaffold_handlers.handle_scaffold_create))
    application.add_handler(CommandHandler("scaffold_status", scaffold_handlers.handle_scaffold_status))
    application.add_handler(CommandHandler("scaffold_history", scaffold_handlers.handle_scaffold_history))

    # ─────────────────────────────────────────────────────────────────────────
    # MESSAGE HANDLERS
    # ─────────────────────────────────────────────────────────────────────────

    # PDF upload router
    async def handle_pdf_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if context.user_data.get("awaiting_manual"):
            await handle_manual_document(update, context)
            return
        if context.user_data.get("awaiting_print"):
            await handle_print_document(update, context)
            return
        await update.message.reply_text(
            "📄 *PDF Received!*\n\n"
            "• `/upload_print <machine>` - Add as electrical print\n"
            "• `/upload_manual` - Add to manual library",
            parse_mode=ParseMode.MARKDOWN
        )

    application.add_handler(MessageHandler(filters.Document.PDF, handle_pdf_upload), group=0)

    # Voice/Image handlers (TIER 0.1)
    application.add_handler(MessageHandler(filters.VOICE, tier0_handlers.handle_voice_message), group=0)
    application.add_handler(MessageHandler(filters.PHOTO, tier0_handlers.handle_image_message), group=0)

    # Natural language fallback
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, rivet_handlers.handle_troubleshoot),
        group=1
    )

    # Daily standup scheduler
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_daily(send_daily_standup, time=dt_time(hour=STANDUP_HOUR, minute=STANDUP_MINUTE))
        logger.info("Daily standup scheduled for admins")

    # ─────────────────────────────────────────────────────────────────────────
    # LAUNCH
    # ─────────────────────────────────────────────────────────────────────────
    
    logger.info("═" * 70)
    logger.info("RIVET CMMS - PUBLIC BOT STARTED")
    logger.info("═" * 70)
    logger.info("Mode: PUBLIC (multi-tenant)")
    logger.info("Auth: admin_users table for admin commands")
    logger.info("Rate Limiting: Enabled for free tier")
    logger.info("═" * 70)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

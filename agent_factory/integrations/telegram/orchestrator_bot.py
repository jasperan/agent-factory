"""
RivetCEO Bot - Standalone Orchestrator Interface
t.me/RivetCeo_bot
Run: poetry run python -m agent_factory.integrations.telegram.orchestrator_bot
"""
import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("ORCHESTRATOR_BOT_TOKEN")

# Import orchestrator
from agent_factory.core.orchestrator import RivetOrchestrator
from agent_factory.rivet_pro.models import create_text_request, ChannelType, RouteType
from agent_factory.integrations.telegram.formatters import ResponseFormatter

orchestrator = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "**RivetCEO - Industrial AI Assistant**\n\n"
        "I'm your direct line to 96 specialized agents and 1,057 knowledge atoms.\n\n"
        "Just ask me anything about:\n"
        "- PLC troubleshooting\n"
        "- VFD fault codes\n"
        "- Motor control\n"
        "- Industrial automation\n"
        "- Equipment manuals\n\n"
        "No commands needed. Just type your question.",
        parse_mode="Markdown"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global orchestrator
    online = "Online" if orchestrator else "Offline"
    await update.message.reply_text(
        f"**RivetCEO Status**\n\n"
        f"Orchestrator: {online}\n"
        f"Agents: 96 available\n"
        f"Knowledge Base: 1,057 atoms\n"
        f"Routes: A/B/C/D active",
        parse_mode="Markdown"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global orchestrator

    user_id = update.effective_user.id
    query = update.message.text.strip()

    if not query:
        return

    logger.info(f"[{user_id}] Query: {query[:50]}...")

    if not orchestrator:
        await update.message.reply_text("Orchestrator offline. Try /status")
        return

    await update.message.chat.send_action("typing")

    try:
        request = create_text_request(
            user_id=f"telegram_{user_id}",
            text=query,
            channel=ChannelType.TELEGRAM
        )

        result = await orchestrator.route_query(request)

        if result and result.text:
            response = result.text

            if result.safety_warnings:
                response += "\n\n**Safety:**\n"
                for w in result.safety_warnings:
                    response += f"- {w}\n"

            if result.suggested_actions:
                response += "\n\n**Steps:**\n"
                for i, action in enumerate(result.suggested_actions, 1):
                    response += f"{i}. {action}\n"

            # Build sources section
            response += "\n\n📚 **Sources:**\n"

            # Check if KB atoms were used (cited_documents or Route A/B)
            has_kb_sources = bool(result.cited_documents) or result.route_taken in [RouteType.A_DIRECT_SME, RouteType.B_SME_ENRICH]

            if has_kb_sources:
                # Show KB atom count and titles
                if result.cited_documents:
                    kb_count = len(result.cited_documents)
                    response += f"Knowledge Base ({kb_count} matches):\n"
                    for doc in result.cited_documents[:3]:  # Top 3 atoms
                        title = doc.get("title", "Document")
                        response += f"  • {title}\n"
                else:
                    response += "Knowledge Base (match found)\n"

                # Also show manual links if available
                if result.links:
                    response += "Referenced Manuals:\n"
                    for link in result.links[:2]:  # Limit to 2
                        response += f"  • {link}\n"

            elif result.route_taken in [RouteType.C_RESEARCH, RouteType.D_CLARIFICATION]:
                # LLM-generated (no KB match)
                response += "AI Generated (no KB match)\n"
                if result.research_triggered:
                    response += "  • Research pipeline used\n"
            else:
                # Fallback: show what we have
                if result.links:
                    for link in result.links[:3]:
                        response += f"  • {link}\n"
                else:
                    response += "AI Generated\n"

            # Add route and confidence for transparency
            route = result.route_taken.value if result.route_taken else "unknown"
            conf = result.confidence or 0
            response += f"\n\n_Route: {route} | Confidence: {conf:.0%}_"

            # Debug info now sent to admin only (see _send_admin_debug_message)

            # Escape Markdown special characters before sending
            escaped_response = ResponseFormatter.escape_markdown(response)

            # Send response (try Markdown, fall back to plain text if parsing fails)
            try:
                if len(escaped_response) > 4000:
                    for i in range(0, len(escaped_response), 4000):
                        await update.message.reply_text(escaped_response[i:i+4000], parse_mode="Markdown")
                else:
                    await update.message.reply_text(escaped_response, parse_mode="Markdown")
            except BadRequest as parse_error:
                logger.warning(f"Markdown parse error, sending as plain text: {parse_error}")
                # Retry without Markdown
                if len(response) > 4000:
                    for i in range(0, len(response), 4000):
                        await update.message.reply_text(response[i:i+4000])
                else:
                    await update.message.reply_text(response)

            # Send debug trace to admin
            await _send_admin_debug_message(context, user_id, query, result)
        else:
            await update.message.reply_text("No response. Try rephrasing your question.")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await update.message.reply_text(f"Error: {str(e)[:200]}")


async def post_init(app: Application):
    global orchestrator
    try:
        # Initialize database connection
        from agent_factory.core.database_manager import DatabaseManager
        db = DatabaseManager()

        # Verify database has atoms
        result = db.execute_query("SELECT COUNT(*) FROM knowledge_atoms")
        atom_count = result[0][0] if result else 0
        logger.info(f"Database initialized with {atom_count} knowledge atoms")

        # Pass RAG layer to orchestrator
        orchestrator = RivetOrchestrator(rag_layer=db)
        logger.info("Orchestrator initialized successfully with RAG layer")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator with RAG: {e}")
        # Fallback to no RAG (current behavior)
        orchestrator = RivetOrchestrator()
        logger.warning("Orchestrator initialized WITHOUT RAG layer (fallback mode)")


def main():
    if not BOT_TOKEN:
        print("ERROR: ORCHESTRATOR_BOT_TOKEN not set in .env")
        return

    print("=" * 50)
    print("RivetCEO Bot Starting...")
    print(f"Bot: t.me/RivetCeo_bot")
    print("=" * 50)

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running. Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


async def _send_admin_debug_message(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    query: str,
    result
) -> None:
    """Send debug trace to admin chat ID."""
    admin_chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")

    if not admin_chat_id:
        return  # Admin notifications disabled

    try:
        # Build trace message
        route = result.route_taken.value if result.route_taken else "unknown"
        agent = result.agent_id.value if hasattr(result, 'agent_id') and result.agent_id else "unknown"
        conf = result.confidence or 0.0

        # Extract KB info
        kb_count = len(result.cited_documents) if result.cited_documents else 0
        kb_coverage = result.trace.get('kb_coverage', 'unknown') if result.trace else 'unknown'
        vendor = result.trace.get('vendor', 'unknown') if result.trace else 'unknown'

        # Build trace text
        trace_text = (
            f"```\n"
            f"TRACE\n"
            f"Route: {route}\n"
            f"Agent: {agent}\n"
            f"Confidence: {conf:.0%}\n"
            f"KB Coverage: {kb_coverage}\n"
            f"KB Atoms: {kb_count}\n"
            f"Vendor: {vendor}\n"
            f"User: {user_id}\n"
            f"Query: {query[:100]}{'...' if len(query) > 100 else ''}\n"
            f"```"
        )

        # Send to admin
        await context.bot.send_message(
            chat_id=admin_chat_id,
            text=trace_text,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Failed to send admin trace: {e}")
        # Don't let admin notification failures break user experience


if __name__ == "__main__":
    main()

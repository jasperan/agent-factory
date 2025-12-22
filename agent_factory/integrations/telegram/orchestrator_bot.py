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
from agent_factory.rivet_pro.models import create_text_request, ChannelType
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

            if result.links:
                response += "\n\n**Sources:**\n"
                for link in result.links[:3]:
                    response += f"- {link}\n"

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
            await _send_admin_debug_message(context, result)
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
    result
) -> None:
    """Send debug trace to admin chat."""
    admin_chat_id = 8445149012

    # Extract route and confidence
    route = result.route_taken.value if result.route_taken else "unknown"
    confidence = result.confidence or 0.0

    # Simple code block format
    debug_message = f"""```
TRACE
Route: {route}
Confidence: {confidence:.0%}
```"""

    try:
        await context.bot.send_message(
            chat_id=admin_chat_id,
            text=debug_message,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to send admin debug message: {e}")


if __name__ == "__main__":
    main()

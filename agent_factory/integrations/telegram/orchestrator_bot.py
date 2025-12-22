"""
RivetCEO Bot - Standalone Orchestrator Interface
t.me/RivetCeo_bot
Run: poetry run python -m agent_factory.integrations.telegram.orchestrator_bot
"""
import os
import asyncio
import logging
import tempfile
import base64
import json
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("ORCHESTRATOR_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Import orchestrator
from agent_factory.core.orchestrator import RivetOrchestrator
from agent_factory.rivet_pro.models import create_text_request, ChannelType, RouteType
from agent_factory.integrations.telegram.formatters import ResponseFormatter

orchestrator = None
openai_client = None


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
            has_kb_sources = bool(result.cited_documents) or result.route_taken in [RouteType.ROUTE_A, RouteType.ROUTE_B]

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

            elif result.route_taken in [RouteType.ROUTE_C, RouteType.ROUTE_D]:
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


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle equipment nameplate photos.

    Workflow:
    1. Download photo from Telegram
    2. Send to GPT-4o Vision for equipment info extraction
    3. Build search query from extracted data
    4. Feed into orchestrator.route_query()
    5. Return troubleshooting response
    """
    global orchestrator, openai_client

    user_id = update.effective_user.id

    # Check if OpenAI Vision available
    if not openai_client:
        await update.message.reply_text(
            "❌ Photo OCR unavailable (OpenAI API key not configured)"
        )
        return

    # Check if orchestrator available
    if not orchestrator:
        await update.message.reply_text("Orchestrator offline. Try /status")
        return

    logger.info(f"[{user_id}] Photo received")

    await update.message.chat.send_action("typing")

    try:
        # Step 1: Download photo (highest resolution)
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()

        # Create temp file
        temp_image_path = None
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_image:
            await photo_file.download_to_drive(temp_image.name)
            temp_image_path = temp_image.name

        try:
            # Step 2: Encode as base64
            with open(temp_image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode("utf-8")

            # Step 3: Send to GPT-4o Vision
            vision_response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """This is an industrial equipment nameplate/label. Extract and return as JSON:
{
  "manufacturer": "",
  "model_number": "",
  "serial_number": "",
  "fault_code": "" (if visible on display),
  "other_text": "" (any other relevant text)
}
If you cannot read the image clearly, explain why."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )

            ocr_result = vision_response.choices[0].message.content
            logger.info(f"[{user_id}] OCR result: {ocr_result[:200]}")

            # Step 4: Parse JSON (or use raw text if JSON parsing fails)
            try:
                equipment_data = json.loads(ocr_result)
                manufacturer = equipment_data.get("manufacturer", "").strip()
                model = equipment_data.get("model_number", "").strip()
                fault_code = equipment_data.get("fault_code", "").strip()
                other_text = equipment_data.get("other_text", "").strip()

                # Build search query
                query_parts = []
                if manufacturer:
                    query_parts.append(manufacturer)
                if model:
                    query_parts.append(model)
                if fault_code:
                    query_parts.append(f"fault code {fault_code}")
                else:
                    query_parts.append("troubleshooting")

                search_query = " ".join(query_parts)

                # Build display string
                detected_info = []
                if manufacturer:
                    detected_info.append(f"Manufacturer: {manufacturer}")
                if model:
                    detected_info.append(f"Model: {model}")
                if fault_code:
                    detected_info.append(f"Fault Code: {fault_code}")

                detected_str = "\n".join(detected_info) if detected_info else "Equipment detected"

            except json.JSONDecodeError:
                # Fallback: use raw OCR text as query
                search_query = ocr_result
                detected_str = "Equipment nameplate read"
                manufacturer = ""
                model = ""
                fault_code = ""

            logger.info(f"[{user_id}] Search query: {search_query}")

            # Step 5: Feed into orchestrator
            request = create_text_request(
                user_id=f"telegram_{user_id}",
                text=search_query,
                channel=ChannelType.TELEGRAM
            )

            result = await orchestrator.route_query(request)

            # Step 6: Build response (same format as text handler)
            if result and result.text:
                # Photo detection header
                response = f"📷 **Detected:**\n{detected_str}\n\n"

                # Main response
                response += result.text

                # Safety warnings
                if result.safety_warnings:
                    response += "\n\n**Safety:**\n"
                    for w in result.safety_warnings:
                        response += f"- {w}\n"

                # Suggested actions
                if result.suggested_actions:
                    response += "\n\n**Steps:**\n"
                    for i, action in enumerate(result.suggested_actions, 1):
                        response += f"{i}. {action}\n"

                # Sources
                response += "\n\n📚 **Sources:**\n"
                has_kb_sources = bool(result.cited_documents) or result.route_taken in [RouteType.ROUTE_A, RouteType.ROUTE_B]

                if has_kb_sources:
                    if result.cited_documents:
                        kb_count = len(result.cited_documents)
                        response += f"Knowledge Base ({kb_count} matches):\n"
                        for doc in result.cited_documents[:3]:
                            title = doc.get("title", "Document")
                            response += f"  • {title}\n"
                    else:
                        response += "Knowledge Base (match found)\n"

                    if result.links:
                        response += "Referenced Manuals:\n"
                        for link in result.links[:2]:
                            response += f"  • {link}\n"

                elif result.route_taken in [RouteType.ROUTE_C, RouteType.ROUTE_D]:
                    response += "AI Generated (no KB match)\n"
                    if result.research_triggered:
                        response += "  • Research pipeline used\n"
                else:
                    if result.links:
                        for link in result.links[:3]:
                            response += f"  • {link}\n"
                    else:
                        response += "AI Generated\n"

                # Route + confidence
                route = result.route_taken.value if result.route_taken else "unknown"
                conf = result.confidence or 0
                response += f"\n\n_Route: {route} | Confidence: {conf:.0%}_"

                # Escape Markdown
                escaped_response = ResponseFormatter.escape_markdown(response)

                # Send to user
                try:
                    if len(escaped_response) > 4000:
                        for i in range(0, len(escaped_response), 4000):
                            await update.message.reply_text(escaped_response[i:i+4000], parse_mode="Markdown")
                    else:
                        await update.message.reply_text(escaped_response, parse_mode="Markdown")
                except BadRequest as parse_error:
                    logger.warning(f"Markdown parse error, sending as plain text: {parse_error}")
                    if len(response) > 4000:
                        for i in range(0, len(response), 4000):
                            await update.message.reply_text(response[i:i+4000])
                    else:
                        await update.message.reply_text(response)

                # Send admin debug trace
                await _send_admin_debug_message_photo(
                    context=context,
                    user_id=user_id,
                    ocr_result=ocr_result,
                    search_query=search_query,
                    manufacturer=manufacturer,
                    model=model,
                    fault_code=fault_code,
                    result=result
                )

            else:
                await update.message.reply_text("No response. Photo may not contain readable equipment nameplate.")

        finally:
            # Cleanup temp file
            if temp_image_path:
                try:
                    Path(temp_image_path).unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")

    except Exception as e:
        logger.error(f"Error handling photo: {e}", exc_info=True)
        await update.message.reply_text(f"Error processing photo: {str(e)[:200]}")


async def post_init(app: Application):
    global orchestrator, openai_client
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

    # Initialize OpenAI client for Vision API
    if OPENAI_API_KEY:
        openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI Vision API client initialized")
    else:
        logger.warning("OpenAI API key not set - photo OCR disabled")


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
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))  # Photo handler (BEFORE text)
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


async def _send_admin_debug_message_photo(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    ocr_result: str,
    search_query: str,
    manufacturer: str,
    model: str,
    fault_code: str,
    result
) -> None:
    """Send debug trace for photo OCR to admin chat ID."""
    admin_chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")

    if not admin_chat_id:
        return  # Admin notifications disabled

    try:
        route = result.route_taken.value if result.route_taken else "unknown"
        agent = result.agent_id.value if hasattr(result, 'agent_id') and result.agent_id else "unknown"
        conf = result.confidence or 0.0

        kb_count = len(result.cited_documents) if result.cited_documents else 0
        kb_coverage = result.trace.get('kb_coverage', 'unknown') if result.trace else 'unknown'

        # Build trace with OCR details
        trace_text = (
            f"```\n"
            f"PHOTO TRACE\n"
            f"OCR Manufacturer: {manufacturer or 'N/A'}\n"
            f"OCR Model: {model or 'N/A'}\n"
            f"OCR Fault Code: {fault_code or 'N/A'}\n"
            f"Search Query: {search_query[:80]}{'...' if len(search_query) > 80 else ''}\n"
            f"---\n"
            f"Route: {route}\n"
            f"Agent: {agent}\n"
            f"Confidence: {conf:.0%}\n"
            f"KB Coverage: {kb_coverage}\n"
            f"KB Atoms: {kb_count}\n"
            f"User: {user_id}\n"
            f"```"
        )

        # Send to admin
        await context.bot.send_message(
            chat_id=admin_chat_id,
            text=trace_text,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Failed to send admin photo trace: {e}")
        # Don't let admin notification failures break user experience


if __name__ == "__main__":
    main()

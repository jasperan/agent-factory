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
import time
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import BadRequest
from dotenv import load_dotenv
from openai import AsyncOpenAI
from langsmith import traceable
from agent_factory.integrations.telegram.ocr.pipeline import OCRPipeline

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
from agent_factory.core.trace_logger import RequestTrace
from agent_factory.rivet_pro.models import create_text_request, ChannelType, RouteType
from agent_factory.integrations.telegram.formatters import ResponseFormatter
from agent_factory.integrations.telegram import library
from agent_factory.integrations.telegram.admin.kb_manager import KBManager

# Import admin modules
from agent_factory.integrations.telegram.admin import (
    AdminDashboard,
    AgentManager,
    ContentReviewer,
    GitHubActions,
    Analytics,
    SystemControl,
)
from agent_factory.integrations.telegram.scaffold_handlers import ScaffoldHandlers
from agent_factory.integrations.telegram.langgraph_handlers import LangGraphHandlers

orchestrator = None
kb_manager = None
openai_client = None
ocr_pipeline = None


async def get_atom_count() -> int:
    """Query actual atom count from database."""
    try:
        from agent_factory.core.database_manager import DatabaseManager
        db = DatabaseManager()
        query = "SELECT COUNT(*) FROM knowledge_atoms"
        result = db.execute_query(query)
        return result[0][0] if result else 0
    except Exception as e:
        logger.error(f"Failed to query atom count: {e}")
        return 0


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    atom_count = await get_atom_count()
    await update.message.reply_text(
        "**RivetCEO - Industrial AI Assistant**\n\n"
        f"I'm your direct line to 96 specialized agents and {atom_count} knowledge atoms.\n\n"
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
    atom_count = await get_atom_count()
    await update.message.reply_text(
        f"**RivetCEO Status**\n\n"
        f"Orchestrator: {online}\n"
        f"Agents: 96 available\n"
        f"Knowledge Base: {atom_count} atoms\n"
        f"Routes: A/B/C/D active",
        parse_mode="Markdown"
    )


async def cmd_trace(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle trace verbosity level (Step 6/6 enhancement)."""
    import os

    args = context.args

    if not args:
        # Show current setting
        level = os.getenv("TRACE_LEVEL", "normal")
        await update.message.reply_text(f"Current trace level: {level}")
        return

    level = args[0].lower()
    if level not in ["minimal", "normal", "verbose", "debug"]:
        await update.message.reply_text(
            "Usage: /trace [minimal|normal|verbose|debug]\n\n"
            "Levels:\n"
            "  minimal - Only errors and route taken\n"
            "  normal - Basic routing decisions (default)\n"
            "  verbose - Include KB retrieval and agent reasoning\n"
            "  debug - Full trace with all decision points"
        )
        return

    # Update environment variable (persists for session)
    os.environ["TRACE_LEVEL"] = level
    await update.message.reply_text(f"✓ Trace level set to: {level}")


# BATCH 1: Extracted functions with @traceable decorators

@traceable(run_type="tool", project_name="rivet-ceo-bot", name="format_user_response")
async def format_user_response(result, trace: RequestTrace) -> str:
    """Format orchestrator result into user-facing message."""
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
            response += "\n🔍 **Researching Similar Issues**\n"
            response += "I'm searching forums and documentation for additional information.\n"
            response += "Check back in 3-5 minutes for updated results!\n"
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

    return response


@traceable(run_type="tool", project_name="rivet-ceo-bot", name="send_to_user")
async def send_to_user(update: Update, response: str, trace: RequestTrace):
    """Send formatted response to user via Telegram."""
    # Escape Markdown special characters before sending
    escaped_response = ResponseFormatter.escape_markdown(response)

    # Send response (try Markdown, fall back to plain text if parsing fails)
    try:
        if len(escaped_response) > 4000:
            for i in range(0, len(escaped_response), 4000):
                await update.message.reply_text(escaped_response[i:i+4000], parse_mode="Markdown")
        else:
            await update.message.reply_text(escaped_response, parse_mode="Markdown")

        trace.event("RESPONSE_SENT", length=len(response))

    except BadRequest as parse_error:
        logger.warning(f"Markdown parse error, sending as plain text: {parse_error}")
        # Retry without Markdown
        if len(response) > 4000:
            for i in range(0, len(response), 4000):
                await update.message.reply_text(response[i:i+4000])
        else:
            await update.message.reply_text(response)

        trace.event("RESPONSE_SENT", length=len(response))


@traceable(run_type="tool", project_name="rivet-ceo-bot", name="send_admin_trace")
async def send_admin_trace(context: ContextTypes.DEFAULT_TYPE, trace: RequestTrace, result):
    """Send comprehensive debug trace to admin (Step 5/6 enhancement)."""
    sections = []

    # Section 1: Request Info
    sections.extend([
        "=" * 50,
        f"TRACE [{trace.trace_id[:8]}]",
        "=" * 50,
        "",
        "📥 REQUEST",
        f"  Type: {trace.message_type}",
        f"  User: {trace.username} ({trace.user_id})",
        f"  Time: {trace.start_time}",
        f"  Query: {trace.content[:100]}{'...' if len(trace.content) > 100 else ''}",
        ""
    ])

    # Section 2: Routing Decision
    sections.extend([
        "🔀 ROUTING DECISION",
        f"  Route: {result.route_taken.value if result.route_taken else 'unknown'}",
        f"  Confidence: {result.confidence:.2%}" if result.confidence else "  Confidence: 0%",
        ""
    ])

    # Add decision trace details
    decisions = trace.get_decisions()
    if decisions:
        for decision in decisions:
            sections.extend([
                f"  Decision Point: {decision.get('decision_point')}",
                f"    → Outcome: {decision.get('outcome')}",
                f"    → Reasoning: {decision.get('reasoning')}",
            ])
            if decision.get('alternatives'):
                sections.append("    → Alternatives:")
                for alt_name, alt_reason in decision.get('alternatives', {}).items():
                    sections.append(f"        • {alt_name}: {alt_reason}")
            sections.append("")

    # Section 3: KB Coverage Details
    kb_retrieval = trace.get_kb_retrieval_info()
    if kb_retrieval:
        sections.extend([
            "📚 KNOWLEDGE BASE",
            f"  Coverage: {kb_retrieval.get('coverage', 0):.2%}",
            f"  Atoms Found: {kb_retrieval.get('atoms_found', 0)}",
        ])
        if kb_retrieval.get('top_matches'):
            sections.append("  Top Matches:")
            for atom_id, score in kb_retrieval['top_matches'][:5]:
                sections.append(f"    - {atom_id}: {score:.2%}")
        sections.append("")

    # Section 4: Agent Reasoning
    agent_reasoning = trace.get_agent_reasoning()
    if agent_reasoning:
        sections.extend([
            f"🤖 AGENT: {agent_reasoning.get('agent', 'Unknown')}",
            f"  Atoms Used: {len(agent_reasoning.get('kb_atoms_used', []))}",
        ])
        if agent_reasoning.get('reasoning_steps'):
            sections.append("  Reasoning Steps:")
            for step in agent_reasoning['reasoning_steps']:
                sections.append(f"    {step}")
        sections.append("")

    # Section 5: Research Pipeline
    if result.research_triggered:
        research_status = trace.get_research_pipeline_status()
        if research_status:
            sections.extend([
                "🔍 RESEARCH PIPELINE",
                f"  Triggered: YES",
                f"  Sources Found: {len(research_status.get('sources_found', []))}",
                f"  Sources Queued: {research_status.get('sources_queued', 0)}",
                f"  Estimated Completion: {research_status.get('estimated_completion', 'unknown')}",
            ])
            if research_status.get('sources_found'):
                sections.append("  URLs:")
                for url in research_status['sources_found'][:5]:
                    sections.append(f"    - {url}")
            sections.append("")

    # Section 6: LangGraph Execution
    langgraph_trace = trace.get_langgraph_trace()
    if langgraph_trace:
        sections.extend([
            "🔗 LANGGRAPH WORKFLOW",
            f"  Workflow: {langgraph_trace.get('workflow', 'unknown')}",
            f"  Nodes: {' → '.join(langgraph_trace.get('nodes_executed', []))}",
            f"  Duration: {langgraph_trace.get('total_duration_ms', 0)}ms",
            f"  Retries: {langgraph_trace.get('retry_count', 0)}",
            ""
        ])

    # Section 7: Performance Timing
    timings = trace.get_all_timings()
    if timings:
        sections.append("⏱️ PERFORMANCE")
        for operation, duration_ms in timings.items():
            sections.append(f"  {operation}: {duration_ms}ms")
        sections.extend(["", f"  TOTAL: {trace.total_duration_ms}ms", ""])

    # Section 8: VPS Logs
    try:
        from agent_factory.integrations.telegram.log_monitor import VPSLogMonitor
        log_monitor = VPSLogMonitor()
        recent_errors = log_monitor.tail_recent_errors(last_n_lines=5)
        if recent_errors and any(e.strip() for e in recent_errors):
            sections.append("⚠️ VPS RECENT ERRORS")
            for error_line in recent_errors:
                if error_line.strip():
                    sections.append(f"  {error_line}")
            sections.append("")
    except Exception as e:
        logger.warning(f"VPS log check failed: {e}")
        sections.extend([f"⚠️ VPS log check failed: {e}", ""])

    # Section 9: Errors
    errors = trace.get_errors()
    if errors:
        sections.append("❌ ERRORS")
        for error in errors:
            sections.extend([
                f"  Type: {error.get('error_type', 'unknown')}",
                f"  Message: {error.get('message', 'N/A')}",
                f"  Location: {error.get('location', 'N/A')}",
                ""
            ])

    sections.append("=" * 50)

    # Send to admin chat
    message = "\n".join(sections)

    try:
        await context.bot.send_message(
            chat_id=8445149012,  # Admin chat ID
            text=f"```\n{message}\n```",
            parse_mode="Markdown"
        )
    except Exception as admin_error:
        logger.warning(f"Failed to send admin trace: {admin_error}")


@traceable(run_type="tool", project_name="rivet-ceo-bot", name="send_admin_error")
async def send_admin_error(context: ContextTypes.DEFAULT_TYPE, trace: RequestTrace, error: str):
    """Send error trace to admin."""
    error_message = trace.format_admin_message(
        route="ERROR",
        confidence=0,
        kb_atoms=0,
        error=error[:200]
    )
    try:
        await context.bot.send_message(chat_id=8445149012, text=error_message)
    except:
        pass


async def _handle_machine_troubleshooting(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    machine: dict,
    user_query: str
):
    """
    Handle troubleshooting query with machine context enrichment.

    When a user is in troubleshooting mode for a specific machine, their queries
    are enriched with machine metadata before being sent to the orchestrator.
    """
    global orchestrator
    from agent_factory.integrations.telegram.library_db import MachineLibraryDB

    user_id = str(update.effective_user.id)

    # Check for /done exit command
    if user_query.lower().strip() == "/done":
        context.user_data.pop('active_machine', None)
        await update.message.reply_text(
            "✅ **Exited troubleshooting mode**\n\n"
            "Use /library to return to your machines.",
            parse_mode="Markdown"
        )
        return

    # Enrich query with machine context
    enriched_query = f"""Equipment Information:
Manufacturer: {machine.get('manufacturer') or 'Not specified'}
Model Number: {machine.get('model_number') or 'Not specified'}
Serial Number: {machine.get('serial_number') or 'Not specified'}
Location: {machine.get('location') or 'Not specified'}
Notes: {machine.get('notes') or 'None'}

User Issue: {user_query}"""

    # Update last_queried timestamp
    db = MachineLibraryDB()
    try:
        db.update_machine_last_queried(machine['id'])
    except Exception as e:
        logger.warning(f"Failed to update last_queried: {e}")

    if not orchestrator:
        await update.message.reply_text("Orchestrator offline. Try /status")
        return

    await update.message.chat.send_action("typing")

    try:
        # Send enriched query to orchestrator
        request = create_text_request(
            user_id=f"telegram_{user_id}",
            text=enriched_query,
            channel=ChannelType.TELEGRAM
        )

        result = await orchestrator.route_query(request)

        # Log to machine history
        try:
            route_taken = result.route_taken.value if result.route_taken else "unknown"
            db.add_query_history(
                machine_id=machine['id'],
                query_text=user_query,
                response_summary=result.text[:500] if result.text else "",
                route_taken=route_taken,
                atoms_used=[doc.get('id', '') for doc in (result.cited_documents or [])]
            )
        except Exception as e:
            logger.warning(f"Failed to log query history: {e}")

        # Format and send response
        if result and result.route_taken:
            formatted_text = await format_user_response(result, None)

            # Add machine context header
            header = f"🔧 **{machine['nickname']}** | Route {result.route_taken.value}\n\n"

            await update.message.reply_text(
                header + formatted_text,
                parse_mode="Markdown"
            )

            logger.info(f"[{user_id}] Machine troubleshooting: {machine['nickname']} | Route {result.route_taken.value}")
        else:
            await update.message.reply_text("No response from orchestrator.")

    except Exception as e:
        logger.error(f"Error in machine troubleshooting: {e}", exc_info=True)
        await update.message.reply_text(
            f"Error processing query: {str(e)[:100]}\n\n"
            "Type /done to exit troubleshooting mode.",
            parse_mode="Markdown"
        )


@traceable(run_type="chain", project_name="rivet-ceo-bot", metadata={"component": "telegram_bot", "handler": "text"})
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main text message handler - PARENT TRACE"""
    global orchestrator

    user_id = update.effective_user.id
    query = update.message.text.strip()

    if not query:
        return

    # CHECK FOR ACTIVE MACHINE CONTEXT (Machine Library troubleshooting mode)
    active_machine = context.user_data.get('active_machine')
    if active_machine:
        await _handle_machine_troubleshooting(update, context, active_machine, query)
        return

    # Start RequestTrace (existing system - runs in parallel with LangSmith)
    trace = RequestTrace(
        message_type="text",
        user_id=str(user_id),
        username=update.effective_user.username,
        content=query
    )
    trace.event("INPUT_RECEIVED")

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

        # Time the routing
        route_start = time.time()
        result = await orchestrator.route_query(request)
        trace.timing("routing", int((time.time() - route_start) * 1000))

        if result and result.route_taken:
            trace.event("ROUTE_DECISION", route=result.route_taken.value, confidence=result.confidence)

        if result and result.text:
            # Use extracted functions (all traced)
            response = await format_user_response(result, trace)
            await send_to_user(update, response, trace)
            await send_admin_trace(context, trace, result)
        else:
            await update.message.reply_text("No response. Try rephrasing your question.")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        trace.error(type(e).__name__, str(e), "handle_message")

        # Send error trace to admin
        await send_admin_error(context, trace, str(e))
        await update.message.reply_text(f"Error: {str(e)[:200]}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle equipment nameplate photos.

    Workflow:
    1. Download photo from Telegram
    2. Use OCR Pipeline (GPT-4o + Gemini fallback) for equipment info extraction
    3. Build search query from extracted data
    4. Feed into orchestrator.route_query()
    5. Return troubleshooting response
    """
    global orchestrator, ocr_pipeline

    user_id = update.effective_user.id

    # Start trace
    trace = RequestTrace(
        message_type="photo",
        user_id=str(user_id),
        username=update.effective_user.username,
        content=f"photo:{update.message.photo[-1].file_id[:20]}"
    )
    trace.event("PHOTO_RECEIVED")

    # Check if OCR Pipeline available
    if not ocr_pipeline:
        await update.message.reply_text(
            "❌ Photo OCR unavailable (OCR pipeline not initialized)"
        )
        return

    # Check if orchestrator available
    if not orchestrator:
        await update.message.reply_text("Orchestrator offline. Try /status")
        return

    logger.info(f"[{user_id}] Photo received")

    await update.message.chat.send_action("typing")

    manufacturer = None
    model = None
    fault_code = None

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
            # Step 2: Read image bytes
            with open(temp_image_path, "rb") as image_file:
                image_bytes = image_file.read()

            # Step 3: Use OCR Pipeline (GPT-4o primary, Gemini fallback)
            ocr_start = time.time()
            ocr_result = await ocr_pipeline.analyze_photo(image_bytes, user_id=str(user_id))
            trace.timing("ocr", int((time.time() - ocr_start) * 1000))

            logger.info(
                f"[{user_id}] OCR result: manufacturer={ocr_result.manufacturer}, "
                f"model={ocr_result.model_number}, confidence={ocr_result.confidence:.2f}, "
                f"provider={ocr_result.provider}"
            )

            # Step 4: Extract data from OCRResult
            manufacturer = ocr_result.manufacturer or ""
            model = ocr_result.model_number or ""
            fault_code = ocr_result.fault_code or ""

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

            detected_str = "\n".join(detected_info) if detected_info else "Equipment nameplate read"

            logger.info(f"[{user_id}] Search query: {search_query}")
            trace.event("OCR_COMPLETE", manufacturer=manufacturer, model=model, fault_code=fault_code)

            # Step 5: Feed into orchestrator
            request = create_text_request(
                user_id=f"telegram_{user_id}",
                text=search_query,
                channel=ChannelType.TELEGRAM
            )

            route_start = time.time()
            result = await orchestrator.route_query(request)
            trace.timing("routing", int((time.time() - route_start) * 1000))

            if result and result.route_taken:
                trace.event("ROUTE_DECISION", route=result.route_taken.value, confidence=result.confidence)

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

                    trace.event("RESPONSE_SENT", length=len(response))

                except BadRequest as parse_error:
                    logger.warning(f"Markdown parse error, sending as plain text: {parse_error}")
                    if len(response) > 4000:
                        for i in range(0, len(response), 4000):
                            await update.message.reply_text(response[i:i+4000])
                    else:
                        await update.message.reply_text(response)

                    trace.event("RESPONSE_SENT", length=len(response))

                # Show "Save to Library" button if OCR extracted equipment data
                if ocr_result and ocr_result.confidence >= 0.5 and (ocr_result.manufacturer or ocr_result.model_number):
                    # Store OCR result for library module
                    context.user_data['ocr_result'] = ocr_result
                    context.user_data['photo_file_id'] = photo.file_id

                    # Create button
                    save_button = InlineKeyboardMarkup([[
                        InlineKeyboardButton("💾 Save to My Library", callback_data="lib_save_ocr")
                    ]])

                    # Show different message based on confidence
                    if ocr_result.confidence >= 0.7:
                        save_message = "📸 **Equipment detected!** Save this to your library for quick reference?"
                    else:
                        save_message = f"📸 **Equipment detected** (confidence: {ocr_result.confidence:.0%})\n⚠️ _Low confidence - please verify details_\n\nSave to your library?"

                    try:
                        await update.message.reply_text(
                            save_message,
                            reply_markup=save_button,
                            parse_mode="Markdown"
                        )
                        logger.info(f"[{user_id}] Save to Library button shown (confidence: {ocr_result.confidence:.2f})")
                    except Exception as button_error:
                        logger.warning(f"Failed to show Save to Library button: {button_error}")

                # Send trace to admin (Message 2)
                admin_message = trace.format_admin_message(
                    route=result.route_taken.value if result.route_taken else "unknown",
                    confidence=result.confidence or 0.0,
                    kb_atoms=len(result.cited_documents) if result.cited_documents else 0,
                    llm_model=result.trace.get("llm_model") if result.trace else None,
                    ocr_result={"manufacturer": manufacturer, "model": model, "fault_code": fault_code},
                    kb_coverage="high" if result.confidence and result.confidence > 0.8 else "low"
                )
                try:
                    await context.bot.send_message(
                        chat_id=8445149012,  # Admin chat ID
                        text=admin_message,
                        parse_mode="Markdown"
                    )
                except Exception as admin_error:
                    logger.warning(f"Failed to send admin trace: {admin_error}")

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
        trace.error(type(e).__name__, str(e), "handle_photo")

        # Send error trace to admin
        error_message = trace.format_admin_message(
            route="ERROR",
            confidence=0,
            kb_atoms=0,
            ocr_result={"manufacturer": manufacturer or "N/A", "model": model or "N/A", "fault_code": fault_code or "N/A"},
            error=str(e)[:200]
        )
        try:
            await context.bot.send_message(chat_id=8445149012, text=error_message)
        except:
            pass

        await update.message.reply_text(f"Error processing photo: {str(e)[:200]}")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle voice messages - Transcribe with Whisper and route through orchestrator.

    Same routing as text messages (A/B/C/D routes).
    """
    global orchestrator, openai_client

    # Check dependencies
    if openai_client is None:
        await update.message.reply_text(
            "⚠️ Voice transcription is not available. Please use text messages."
        )
        return

    if orchestrator is None:
        await update.message.reply_text(
            "⚠️ Orchestrator is not available. Please contact support."
        )
        return

    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    voice = update.message.voice

    logger.info(f"[{user_id}] Voice message received, duration: {voice.duration}s")

    processing_msg = await update.message.reply_text("🎤 Processing voice...")

    try:
        # Download voice file
        file = await context.bot.get_file(voice.file_id)

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            await file.download_to_drive(tmp.name)
            audio_path = Path(tmp.name)

        # Transcribe with Whisper
        await processing_msg.edit_text("🎤 Transcribing...")

        with open(audio_path, 'rb') as audio_file:
            transcription = await openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )

        transcribed_text = transcription.text.strip()
        logger.info(f"[{user_id}] Transcribed: {transcribed_text[:100]}...")

        # Cleanup
        audio_path.unlink()

        # Acknowledge transcription
        await processing_msg.edit_text(
            f"🎤 **I heard:** \"{transcribed_text}\"\n\n_Analyzing..._",
            parse_mode="Markdown"
        )

        # Route through orchestrator (same as text messages)
        request = create_text_request(
            user_id=f"telegram_{user_id}",
            text=transcribed_text,
            channel=ChannelType.TELEGRAM,
            username=username
        )

        response = await orchestrator.route_query(request)

        # Format response (same as handle_message)
        trace = RequestTrace(
            message_type="voice",
            user_id=str(user_id),
            username=username,
            content=transcribed_text
        )
        formatted_text = await format_user_response(response, trace)

        # Send final response
        await update.message.reply_text(formatted_text, parse_mode="Markdown")

        logger.info(
            f"[{user_id}] Voice processed. "
            f"Route: {response.route_taken.value}, Confidence: {response.confidence:.2f}"
        )

    except Exception as e:
        logger.error(f"[{user_id}] Voice error: {e}", exc_info=True)
        await processing_msg.edit_text(
            f"❌ **Error processing voice**\n\n{str(e)[:200]}",
            parse_mode="Markdown"
        )


async def post_init(app: Application):
    global orchestrator, openai_client, kb_manager
    try:
        # Initialize database connection
        from agent_factory.core.database_manager import DatabaseManager
        db = DatabaseManager()

        # Verify database has atoms
        result = db.execute_query("SELECT COUNT(*) FROM knowledge_atoms")
        atom_count = result[0][0] if result else 0

        if atom_count == 0:
            logger.warning("⚠️  CRITICAL: Knowledge Base is empty! Bot will run with limited capabilities.")
            logger.warning("   Run: poetry run python upload_atoms_to_neon.py")
        else:
            logger.info(f"✅ Knowledge Base: {atom_count} atoms loaded")

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

    # Initialize OCR Pipeline (dual provider: GPT-4o + Gemini)
    global ocr_pipeline
    try:
        ocr_pipeline = OCRPipeline()
        logger.info("OCR Pipeline initialized (GPT-4o + Gemini fallback)")
    except Exception as e:
        logger.error(f"Failed to initialize OCR Pipeline: {e}")
        ocr_pipeline = None

    # Initialize KB Observability Batch Timer
    try:
        from agent_factory.observability import TelegramNotifier
        from agent_factory.core.database_manager import DatabaseManager

        # Get DB manager and create notifier
        db_manager = DatabaseManager()
        notifier = TelegramNotifier(
            bot_token=os.getenv("ORCHESTRATOR_BOT_TOKEN"),
            chat_id=int(os.getenv("TELEGRAM_ADMIN_CHAT_ID", "8445149012")),
            mode=os.getenv("KB_NOTIFICATION_MODE", "BATCH"),
            quiet_hours_start=int(os.getenv("NOTIFICATION_QUIET_START", "23")),
            quiet_hours_end=int(os.getenv("NOTIFICATION_QUIET_END", "7")),
            db_manager=db_manager
        )

        # Start batch notification timer (runs every 5 minutes)
        async def batch_notification_timer():
            """Background task to send batch summaries every 5 minutes."""
            while True:
                await asyncio.sleep(300)  # 5 minutes
                try:
                    await notifier.send_batch_summary()
                    logger.info("KB observability batch summary sent")
                except Exception as e:
                    logger.error(f"Batch summary failed: {e}")

        # Create background task in bot's event loop
        app.create_task(batch_notification_timer())
        logger.info("✅ KB Observability batch timer started (5-minute intervals)")

    except Exception as e:
        logger.error(f"Failed to initialize KB observability timer: {e}")
        logger.warning("KB ingestion notifications disabled")


def main():
    global kb_manager

    if not BOT_TOKEN:
        print("ERROR: ORCHESTRATOR_BOT_TOKEN not set in .env")
        return

    print("=" * 50)
    print("RivetCEO Bot Starting...")
    print(f"Bot: t.me/RivetCeo_bot")
    print("=" * 50)

    # Initialize KB Manager before registering handlers
    kb_manager = KBManager()
    print("KB Manager initialized")

    # Initialize Admin Panel handlers
    admin_dashboard = AdminDashboard()
    agent_manager = AgentManager()
    content_reviewer = ContentReviewer()
    github_actions = GitHubActions()
    analytics = Analytics()
    system_control = SystemControl()
    print("Admin Panel initialized")

    # Initialize SCAFFOLD handlers
    project_root = Path(__file__).parent.parent.parent.parent  # agent_factory root
    scaffold_handlers = ScaffoldHandlers(
        repo_root=project_root,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_cost=float(os.getenv("SCAFFOLD_MAX_COST", "5.0")),
        max_time_hours=float(os.getenv("SCAFFOLD_MAX_TIME_HOURS", "2.0")),
        dry_run=os.getenv("SCAFFOLD_DRY_RUN", "false").lower() == "true"
    )
    print("SCAFFOLD handlers initialized")

    # Initialize LangGraph handlers
    langgraph_handlers = LangGraphHandlers()
    print("LangGraph handlers initialized")

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("trace", cmd_trace))  # Trace verbosity control (Step 6/6)

    # Machine Library - Personal equipment library for technicians
    app.add_handler(CommandHandler("library", library.library_command))
    app.add_handler(library.add_machine_handler)  # ConversationHandler for add flow
    app.add_handler(CallbackQueryHandler(library.library_callback_router, pattern="^lib_"))

    # Knowledge Base Management - Admin commands for KB ingestion
    app.add_handler(CommandHandler("kb", kb_manager.handle_kb))
    app.add_handler(CommandHandler("kb_ingest", kb_manager.handle_kb_ingest))
    app.add_handler(CommandHandler("kb_search", kb_manager.handle_kb_search))
    app.add_handler(CommandHandler("kb_queue", kb_manager.handle_kb_queue))
    app.add_handler(CommandHandler("kb_enrichment", kb_manager.handle_kb_enrichment))

    # Admin Panel Commands
    app.add_handler(CommandHandler("admin", admin_dashboard.handle_admin))
    app.add_handler(CallbackQueryHandler(admin_dashboard.handle_callback, pattern="^menu_"))

    # Agent Management
    app.add_handler(CommandHandler("agents_admin", agent_manager.handle_agents))
    app.add_handler(CommandHandler("agent", agent_manager.handle_agent_detail))
    app.add_handler(CommandHandler("agent_logs", agent_manager.handle_agent_logs))

    # Content Review
    app.add_handler(CommandHandler("content", content_reviewer.handle_content))

    # GitHub Actions
    app.add_handler(CommandHandler("deploy", github_actions.handle_deploy))
    app.add_handler(CommandHandler("workflow", github_actions.handle_workflow))
    app.add_handler(CommandHandler("workflows", github_actions.handle_workflows))
    app.add_handler(CommandHandler("workflow_status", github_actions.handle_workflow_status))
    app.add_handler(CallbackQueryHandler(github_actions.handle_deploy_confirm, pattern="^deploy_confirm$"))

    # Analytics
    app.add_handler(CommandHandler("metrics_admin", analytics.handle_metrics))
    app.add_handler(CommandHandler("costs", analytics.handle_costs))
    app.add_handler(CommandHandler("revenue", analytics.handle_revenue))

    # System Control
    app.add_handler(CommandHandler("health", system_control.handle_health))
    app.add_handler(CommandHandler("db_health", system_control.handle_db_health))
    app.add_handler(CommandHandler("vps_status_admin", system_control.handle_vps_status))
    app.add_handler(CommandHandler("restart", system_control.handle_restart))

    # SCAFFOLD Commands
    app.add_handler(CommandHandler("scaffold", scaffold_handlers.handle_scaffold_create))
    app.add_handler(CommandHandler("scaffold_status", scaffold_handlers.handle_scaffold_status))
    app.add_handler(CommandHandler("scaffold_history", scaffold_handlers.handle_scaffold_history))

    # LangGraph Workflow Commands
    app.add_handler(CommandHandler("research", langgraph_handlers.handle_research))
    app.add_handler(CommandHandler("consensus", langgraph_handlers.handle_consensus))
    app.add_handler(CommandHandler("analyze", langgraph_handlers.handle_analyze))

    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))  # Photo handler (BEFORE text)

    # Voice message handler - Transcribe + Route through RivetOrchestrator
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Startup summary
    print("\n" + "=" * 70)
    print("RivetCEO Bot - Admin Commands Available:")
    print("=" * 70)
    print("\nCore:")
    print("  /start, /status, /trace, /library")
    print("\nKnowledge Base:")
    print("  /kb, /kb_ingest, /kb_search, /kb_queue, /kb_enrichment")
    print("\nAdmin Panel:")
    print("  /admin (dashboard)")
    print("\nAgent Management:")
    print("  /agents_admin, /agent, /agent_logs")
    print("\nContent Review:")
    print("  /content")
    print("\nGitHub & Deployment:")
    print("  /deploy, /workflow, /workflows, /workflow_status")
    print("\nAnalytics:")
    print("  /metrics_admin, /costs, /revenue")
    print("\nSystem Control:")
    print("  /health, /db_health, /vps_status_admin, /restart")
    print("\nSCAFFOLD:")
    print("  /scaffold, /scaffold_status, /scaffold_history")
    print("\nLangGraph Workflows:")
    print("  /research, /consensus, /analyze")
    print("\n" + "=" * 70)
    print("Authorization: Telegram ID 8445149012 only")
    print("=" * 70)
    print("\nBot running. Ctrl+C to stop.\n")
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

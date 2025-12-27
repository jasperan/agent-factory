"""Photo handler for technical schematics and prints."""

import tempfile
from pathlib import Path
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction, ParseMode

from agent_factory.rivet_pro.print_analyzer import PrintAnalyzer


async def handle_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle uploaded photo (schematic/print).

    Flow:
    1. Download photo (highest resolution)
    2. Analyze with Claude Vision
    3. Send analysis to user
    4. Store photo path in session for follow-up questions

    Args:
        update: Telegram update with photo
        context: Telegram context
    """
    user_id = update.effective_user.id
    photo = update.message.photo[-1]  # Highest resolution

    # Show typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    photo_path: Optional[Path] = None

    try:
        # Download photo
        file = await context.bot.get_file(photo.file_id)

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            await file.download_to_drive(tmp.name)
            photo_path = Path(tmp.name)

        # Analyze with Claude Vision
        analyzer = PrintAnalyzer()
        analysis = await analyzer.analyze(photo_path)

        # Send analysis
        response_text = (
            "📊 **Schematic Analysis:**\n\n"
            f"{analysis}\n\n"
            "💬 **Ask me anything about this print!**\n"
            "_Send a text or voice message with your question._"
        )

        await update.message.reply_text(
            response_text,
            parse_mode=ParseMode.MARKDOWN
        )

        # Store photo path in session for follow-up questions
        context.user_data["current_print"] = str(photo_path)
        context.user_data["current_print_analysis"] = analysis

    except Exception as e:
        print(f"Photo handler error: {str(e)}")
        await update.message.reply_text(
            "❌ Sorry, I couldn't analyze this image. "
            "Please make sure it's a clear photo of a schematic or wiring diagram."
        )

        # Cleanup on error
        if photo_path and photo_path.exists():
            photo_path.unlink(missing_ok=True)


async def handle_photo_question_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    question: str
) -> bool:
    """
    Handle text question about previously uploaded photo.

    Args:
        update: Telegram update
        context: Telegram context
        question: User's question

    Returns:
        True if question was answered, False if no photo in context
    """
    print_path = context.user_data.get("current_print")

    if not print_path:
        return False  # No photo in context

    # Show typing
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    try:
        # Answer question about the print
        analyzer = PrintAnalyzer()
        answer = await analyzer.answer_question(Path(print_path), question)

        await update.message.reply_text(
            f"🎯 **Question:** {question}\n\n"
            f"📊 **Answer:**\n{answer}",
            parse_mode=ParseMode.MARKDOWN
        )

        return True

    except Exception as e:
        print(f"Photo question error: {str(e)}")
        await update.message.reply_text(
            "❌ Error answering your question about the schematic. Please try rephrasing."
        )

        return True  # Still handled, just errored


async def handle_photo_troubleshooting(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    fault_description: str
) -> None:
    """
    Handle troubleshooting query with photo context.

    Args:
        update: Telegram update
        context: Telegram context
        fault_description: Description of the fault/symptom
    """
    print_path = context.user_data.get("current_print")

    if not print_path:
        await update.message.reply_text(
            "⚠️ Please upload a schematic first, then describe the fault."
        )
        return

    # Show typing
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    try:
        # Identify fault location
        analyzer = PrintAnalyzer()
        analysis = await analyzer.identify_fault_location(
            Path(print_path),
            fault_description
        )

        await update.message.reply_text(
            f"🔧 **Troubleshooting Analysis:**\n\n"
            f"{analysis}",
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        print(f"Troubleshooting error: {str(e)}")
        await update.message.reply_text(
            "❌ Error analyzing fault location. Please try again."
        )


async def handle_photo_safety_check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Generate safety warnings for current schematic.

    Args:
        update: Telegram update
        context: Telegram context
    """
    print_path = context.user_data.get("current_print")

    if not print_path:
        await update.message.reply_text(
            "⚠️ Please upload a schematic first."
        )
        return

    # Show typing
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )

    try:
        # Get safety warnings
        analyzer = PrintAnalyzer()
        warnings = await analyzer.get_safety_warnings(Path(print_path))

        await update.message.reply_text(
            f"⚠️ **Safety Analysis:**\n\n"
            f"{warnings}",
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        print(f"Safety check error: {str(e)}")
        await update.message.reply_text(
            "❌ Error generating safety analysis."
        )

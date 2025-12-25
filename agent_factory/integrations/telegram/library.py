"""
Telegram Machine Library Handlers.

Personal machine library for RivetCEO Bot - lets technicians save equipment
for quick reference and context-aware troubleshooting.

Features:
- Save machines with details (nickname, manufacturer, model, serial, etc.)
- View library in 2-column grid layout
- Troubleshoot machines with context-enriched queries
- Track query history per machine
- Delete machines
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from .library_db import MachineLibraryDB
from .conversation_state import get_state_manager

logger = logging.getLogger(__name__)

# Initialize database and state manager
db = MachineLibraryDB()
state_manager = get_state_manager()

# Conversation states for add machine flow
NICKNAME, MANUFACTURER, MODEL, SERIAL, LOCATION, NOTES, PHOTO = range(7)

# Callback data prefixes (must stay under 64 bytes total)
CB_VIEW = "lib_view_"          # lib_view_{short_id}
CB_TROUBLESHOOT = "lib_ts_"    # lib_ts_{short_id}
CB_HISTORY = "lib_hist_"       # lib_hist_{short_id}
CB_DELETE = "lib_del_"         # lib_del_{short_id}
CB_CONFIRM_DEL = "lib_cdel_"   # lib_cdel_{short_id}
CB_ADD = "lib_add"
CB_SAVE_OCR = "lib_save_ocr"   # Save from OCR extraction
CB_BACK = "lib_back"
CB_SKIP = "lib_skip"


# ============================================================================
# /library Command - Entry Point
# ============================================================================

async def library_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Entry point: /library command.

    Shows user's saved machines in a 2-column grid layout,
    or empty state if no machines saved yet.
    """
    user_id = str(update.effective_user.id)

    try:
        machines = db.get_user_machines(user_id)
    except Exception as e:
        logger.error(f"Failed to load machines for user {user_id}: {e}")
        await update.message.reply_text(
            "❌ Error loading machines. Please try again.",
            parse_mode="Markdown"
        )
        return

    # Build 2-column grid keyboard
    keyboard = []
    row = []
    for machine in machines:
        short_id = machine['id'][:8]  # First 8 chars of UUID
        btn = InlineKeyboardButton(
            text=machine['nickname'][:14],  # Truncate for button width
            callback_data=f"{CB_VIEW}{short_id}"
        )
        row.append(btn)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:  # Add remaining button if odd number
        keyboard.append(row)

    # Add "Add New Machine" button
    keyboard.append([InlineKeyboardButton("➕ Add New Machine", callback_data=CB_ADD)])

    # Build message text
    text = "📚 **My Machine Library**\n\n"
    if not machines:
        text += "_No machines saved yet. Tap 'Add New' to get started!_"
    else:
        text += f"_{len(machines)} machine(s) saved_\n\nTap a machine to view details."

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# ============================================================================
# Callback Router - Routes lib_* callbacks to appropriate handlers
# ============================================================================

async def library_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Route lib_* callbacks to specific handlers.

    Handles: view, troubleshoot, history, delete, confirm delete, back
    Note: CB_SAVE_OCR is handled by ConversationHandler entry point, not here
    """
    query = update.callback_query
    data = query.data

    try:
        if data.startswith(CB_VIEW):
            await _handle_view_machine(update, context)
        elif data.startswith(CB_TROUBLESHOOT):
            await _handle_troubleshoot_machine(update, context)
        elif data.startswith(CB_HISTORY):
            await _handle_view_history(update, context)
        elif data.startswith(CB_DELETE):
            await _handle_delete_confirm(update, context)
        elif data.startswith(CB_CONFIRM_DEL):
            await _handle_delete_machine(update, context)
        elif data == CB_BACK:
            await _handle_back_to_library(update, context)
        elif data == CB_SAVE_OCR:
            # Handled by ConversationHandler, not here
            pass
        else:
            await query.answer("Unknown action", show_alert=True)

    except Exception as e:
        logger.error(f"Error in library callback router: {e}", exc_info=True)
        await query.answer("Error processing request", show_alert=True)


# ============================================================================
# View Machine Detail
# ============================================================================

async def _handle_view_machine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show machine detail view with action buttons."""
    query = update.callback_query
    await query.answer()

    short_id = query.data.replace(CB_VIEW, "")
    user_id = str(update.effective_user.id)

    # Find machine by short_id (first 8 chars of UUID)
    try:
        machines = db.get_user_machines(user_id)
        machine = next((m for m in machines if m['id'].startswith(short_id)), None)

        if not machine:
            await query.edit_message_text(
                "⚠️ Machine not found. It may have been deleted.",
                parse_mode="Markdown"
            )
            return

    except Exception as e:
        logger.error(f"Error loading machine: {e}")
        await query.edit_message_text("❌ Error loading machine.")
        return

    # Format machine details
    text = f"""🔧 **{machine['nickname']}**
━━━━━━━━━━━━━━━
**Manufacturer:** {machine['manufacturer'] or '_Not set_'}
**Model:** {machine['model_number'] or '_Not set_'}
**Serial:** {machine['serial_number'] or '_Not set_'}
**Location:** {machine['location'] or '_Not set_'}
**Notes:** {machine['notes'] or '_None_'}
"""

    # Add query count if available
    try:
        query_count = db.get_query_count(machine['id'])
        if query_count > 0:
            text += f"\n📊 **Queries:** {query_count}"
    except Exception:
        pass  # Non-critical, skip if fails

    # Build action buttons
    keyboard = [
        [
            InlineKeyboardButton("🔍 Troubleshoot", callback_data=f"{CB_TROUBLESHOOT}{short_id}"),
            InlineKeyboardButton("📜 History", callback_data=f"{CB_HISTORY}{short_id}")
        ],
        [
            InlineKeyboardButton("🗑️ Delete", callback_data=f"{CB_DELETE}{short_id}")
        ],
        [InlineKeyboardButton("⬅️ Back to Library", callback_data=CB_BACK)]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# ============================================================================
# Troubleshoot Machine - Sets active machine context
# ============================================================================

async def _handle_troubleshoot_machine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Set active machine context for troubleshooting.

    Stores machine in context.user_data['active_machine'] so that subsequent
    text messages are enriched with machine context before routing to orchestrator.
    """
    query = update.callback_query
    await query.answer()

    short_id = query.data.replace(CB_TROUBLESHOOT, "")
    user_id = str(update.effective_user.id)

    try:
        machines = db.get_user_machines(user_id)
        machine = next((m for m in machines if m['id'].startswith(short_id)), None)

        if not machine:
            await query.edit_message_text("⚠️ Machine not found.")
            return

    except Exception as e:
        logger.error(f"Error loading machine for troubleshooting: {e}")
        await query.edit_message_text("❌ Error loading machine.")
        return

    # Store in user context (ephemeral, lives until /done or session end)
    context.user_data['active_machine'] = machine

    logger.info(f"User {user_id} started troubleshooting {machine['nickname']} ({machine['id'][:8]})")

    await query.edit_message_text(
        f"🔧 **Troubleshooting: {machine['nickname']}**\n\n"
        f"_{machine['manufacturer'] or 'Unknown'} {machine['model_number'] or ''}_\n\n"
        "Describe the issue you're experiencing. "
        "I'll include the machine details in my analysis.\n\n"
        "_Type /done to exit troubleshooting mode._",
        parse_mode="Markdown"
    )


# ============================================================================
# View Query History
# ============================================================================

async def _handle_view_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show last 10 queries for this machine."""
    query = update.callback_query
    await query.answer()

    short_id = query.data.replace(CB_HISTORY, "")
    user_id = str(update.effective_user.id)

    try:
        machines = db.get_user_machines(user_id)
        machine = next((m for m in machines if m['id'].startswith(short_id)), None)

        if not machine:
            await query.edit_message_text("⚠️ Machine not found.")
            return

        history = db.get_machine_history(machine['id'], limit=10)

    except Exception as e:
        logger.error(f"Error loading history: {e}")
        await query.edit_message_text("❌ Error loading history.")
        return

    # Format history
    text = f"📜 **Query History: {machine['nickname']}**\n\n"

    if not history:
        text += "_No queries yet. Start troubleshooting to build history!_"
    else:
        for idx, entry in enumerate(history[:10], 1):
            timestamp = entry['timestamp'].strftime("%m/%d %H:%M") if entry['timestamp'] else "Unknown"
            query_text = entry['query'][:50] + "..." if len(entry['query']) > 50 else entry['query']
            route = entry['route'] or "?"
            text += f"{idx}. **{timestamp}** (Route {route})\n   _{query_text}_\n\n"

    # Back button
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data=f"{CB_VIEW}{short_id}")]]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# ============================================================================
# Delete Machine - Confirmation
# ============================================================================

async def _handle_delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show delete confirmation dialog."""
    query = update.callback_query
    await query.answer()

    short_id = query.data.replace(CB_DELETE, "")
    user_id = str(update.effective_user.id)

    try:
        machines = db.get_user_machines(user_id)
        machine = next((m for m in machines if m['id'].startswith(short_id)), None)

        if not machine:
            await query.edit_message_text("⚠️ Machine not found.")
            return

    except Exception as e:
        logger.error(f"Error loading machine for delete: {e}")
        await query.edit_message_text("❌ Error.")
        return

    text = f"🗑️ **Delete {machine['nickname']}?**\n\n"
    text += "This will permanently delete:\n"
    text += "• Machine details\n"
    text += "• Query history\n\n"
    text += "This cannot be undone."

    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, Delete", callback_data=f"{CB_CONFIRM_DEL}{short_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"{CB_VIEW}{short_id}")
        ]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def _handle_delete_machine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute machine deletion."""
    query = update.callback_query
    await query.answer()

    short_id = query.data.replace(CB_CONFIRM_DEL, "")
    user_id = str(update.effective_user.id)

    try:
        machines = db.get_user_machines(user_id)
        machine = next((m for m in machines if m['id'].startswith(short_id)), None)

        if not machine:
            await query.edit_message_text("⚠️ Machine not found.")
            return

        # Delete machine (cascades to history)
        db.delete_machine(machine['id'], user_id)

        logger.info(f"User {user_id} deleted machine {machine['nickname']} ({machine['id'][:8]})")

        await query.edit_message_text(
            f"✅ **{machine['nickname']}** deleted.\n\n"
            "Use /library to view your remaining machines.",
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error deleting machine: {e}")
        await query.edit_message_text("❌ Error deleting machine.")


# ============================================================================
# Back to Library
# ============================================================================

async def _handle_back_to_library(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to library grid view."""
    query = update.callback_query
    await query.answer()

    user_id = str(update.effective_user.id)

    try:
        machines = db.get_user_machines(user_id)
    except Exception as e:
        logger.error(f"Error loading machines: {e}")
        await query.edit_message_text("❌ Error loading machines.")
        return

    # Rebuild grid keyboard (same as library_command)
    keyboard = []
    row = []
    for machine in machines:
        short_id = machine['id'][:8]
        btn = InlineKeyboardButton(
            text=machine['nickname'][:14],
            callback_data=f"{CB_VIEW}{short_id}"
        )
        row.append(btn)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("➕ Add New Machine", callback_data=CB_ADD)])

    text = "📚 **My Machine Library**\n\n"
    text += f"_{len(machines)} machine(s) saved_" if machines else "_No machines saved yet._"

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# ============================================================================
# ConversationHandler: Add Machine Flow
# ============================================================================

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start add machine conversation."""
    query = update.callback_query
    await query.answer()

    user_id = str(update.effective_user.id)

    # Check for existing state (resume capability)
    existing_state = await state_manager.load_state(user_id, "add_machine")

    if existing_state:
        # Resume from saved state
        context.user_data['new_machine'] = existing_state['data']
        logger.info(f"Resuming add_machine for user {user_id} from state {existing_state['current_state']}")

        # Map state name to conversation state constant
        state_map = {
            'NICKNAME': NICKNAME,
            'MANUFACTURER': MANUFACTURER,
            'MODEL': MODEL,
            'SERIAL': SERIAL,
            'LOCATION': LOCATION,
            'NOTES': NOTES,
            'PHOTO': PHOTO
        }

        resume_text = "🔄 **Resuming...**\n\n"
        resume_text += f"Last state: {existing_state['current_state']}\n\n"
        resume_text += "Continuing where you left off..."

        await query.edit_message_text(resume_text, parse_mode="Markdown")

        return state_map.get(existing_state['current_state'], NICKNAME)

    # Fresh start - initialize empty machine data
    context.user_data['new_machine'] = {}

    await query.edit_message_text(
        "➕ **Add New Machine**\n\n"
        "What do you want to call this machine?\n"
        "_(e.g., 'Line 3 Robot', 'Basement Compressor')_\n\n"
        "/cancel to abort",
        parse_mode="Markdown"
    )
    return NICKNAME


async def add_from_ocr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start add machine with OCR pre-fill."""
    query = update.callback_query
    await query.answer()

    user_id = str(update.effective_user.id)

    # Check for existing state first (resume capability)
    existing_state = await state_manager.load_state(user_id, "add_machine")

    if existing_state:
        # Resume from saved state
        context.user_data['new_machine'] = existing_state['data']
        logger.info(f"Resuming add_machine (OCR) for user {user_id} from state {existing_state['current_state']}")

        state_map = {
            'NICKNAME': NICKNAME,
            'MANUFACTURER': MANUFACTURER,
            'MODEL': MODEL,
            'SERIAL': SERIAL,
            'LOCATION': LOCATION,
            'NOTES': NOTES,
            'PHOTO': PHOTO
        }

        resume_text = "🔄 **Resuming...**\n\n"
        resume_text += f"Last state: {existing_state['current_state']}\n\n"
        resume_text += "Continuing where you left off..."

        await query.edit_message_text(resume_text, parse_mode="Markdown")

        return state_map.get(existing_state['current_state'], NICKNAME)

    # No existing state - try OCR pre-fill
    ocr_result = context.user_data.get('ocr_result')
    if not ocr_result:
        await query.edit_message_text("⏰ Session expired. Please send the photo again.")
        return ConversationHandler.END

    # Pre-fill from OCR (convert OCRResult object to dict)
    context.user_data['new_machine'] = {
        'manufacturer': ocr_result.manufacturer or '',
        'model_number': ocr_result.model_number or '',
        'serial_number': ocr_result.serial_number or '',
        'photo_file_id': context.user_data.get('photo_file_id')
    }

    # Show preview
    preview = "📸 **Equipment Detected:**\n\n"
    if ocr_result.manufacturer:
        preview += f"• Manufacturer: {ocr_result.manufacturer}\n"
    if ocr_result.model_number:
        preview += f"• Model: {ocr_result.model_number}\n"
    if ocr_result.serial_number:
        preview += f"• Serial: {ocr_result.serial_number}\n"

    if not (ocr_result.manufacturer or ocr_result.model_number):
        preview += "• _(No equipment data detected)_\n"

    preview += "\n"

    # Confidence warning
    confidence = getattr(ocr_result, 'confidence', 0.0)
    if confidence < 0.7:
        preview += f"⚠️ Low OCR confidence ({confidence:.0%}). Please verify.\n\n"

    preview += "**What nickname do you want to give this machine?**\n_(e.g., 'Line 3 Robot')_\n\n/cancel to abort"

    await query.edit_message_text(preview, parse_mode="Markdown")

    return NICKNAME


async def add_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save nickname, ask for manufacturer."""
    user_id = str(update.effective_user.id)

    # Save nickname to context
    context.user_data['new_machine']['nickname'] = update.message.text.strip()

    # Persist state to database (CRITICAL: prevents data loss)
    await state_manager.save_state(
        user_id=user_id,
        conversation_type="add_machine",
        current_state="MANUFACTURER",
        data=context.user_data['new_machine']
    )

    keyboard = [[InlineKeyboardButton("Skip ⏭️", callback_data=CB_SKIP)]]
    await update.message.reply_text(
        "What's the **manufacturer**?\n_(e.g., Fanuc, Siemens, Allen-Bradley)_",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return MANUFACTURER


async def add_manufacturer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save manufacturer, ask for model."""
    user_id = str(update.effective_user.id)

    if update.callback_query:  # Skip pressed
        await update.callback_query.answer()
        context.user_data['new_machine']['manufacturer'] = None
        msg = update.callback_query.message
    else:
        context.user_data['new_machine']['manufacturer'] = update.message.text.strip()
        msg = update.message

    # Persist state to database
    await state_manager.save_state(
        user_id=user_id,
        conversation_type="add_machine",
        current_state="MODEL",
        data=context.user_data['new_machine']
    )

    keyboard = [[InlineKeyboardButton("Skip ⏭️", callback_data=CB_SKIP)]]
    await msg.reply_text(
        "What's the **model number**?\n_(e.g., M-20iA, S7-1200, G120C)_",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return MODEL


async def add_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save model, ask for serial."""
    user_id = str(update.effective_user.id)

    if update.callback_query:
        await update.callback_query.answer()
        context.user_data['new_machine']['model_number'] = None
        msg = update.callback_query.message
    else:
        context.user_data['new_machine']['model_number'] = update.message.text.strip()
        msg = update.message

    # Persist state to database
    await state_manager.save_state(
        user_id=user_id,
        conversation_type="add_machine",
        current_state="SERIAL",
        data=context.user_data['new_machine']
    )

    keyboard = [[InlineKeyboardButton("Skip ⏭️", callback_data=CB_SKIP)]]
    await msg.reply_text(
        "What's the **serial number**?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return SERIAL


async def add_serial(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save serial, ask for location."""
    user_id = str(update.effective_user.id)

    if update.callback_query:
        await update.callback_query.answer()
        context.user_data['new_machine']['serial_number'] = None
        msg = update.callback_query.message
    else:
        context.user_data['new_machine']['serial_number'] = update.message.text.strip()
        msg = update.message

    # Persist state to database
    await state_manager.save_state(
        user_id=user_id,
        conversation_type="add_machine",
        current_state="LOCATION",
        data=context.user_data['new_machine']
    )

    keyboard = [[InlineKeyboardButton("Skip ⏭️", callback_data=CB_SKIP)]]
    await msg.reply_text(
        "Where is this machine located?\n_(e.g., Building A, Line 3)_",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return LOCATION


async def add_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save location, ask for notes."""
    user_id = str(update.effective_user.id)

    if update.callback_query:
        await update.callback_query.answer()
        context.user_data['new_machine']['location'] = None
        msg = update.callback_query.message
    else:
        context.user_data['new_machine']['location'] = update.message.text.strip()
        msg = update.message

    # Persist state to database
    await state_manager.save_state(
        user_id=user_id,
        conversation_type="add_machine",
        current_state="NOTES",
        data=context.user_data['new_machine']
    )

    keyboard = [[InlineKeyboardButton("Skip ⏭️", callback_data=CB_SKIP)]]
    await msg.reply_text(
        "Any **notes** about this machine?\n_(e.g., 'Replaced servo amp 2024-03')_",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return NOTES


async def add_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save notes, ask for photo."""
    user_id = str(update.effective_user.id)

    if update.callback_query:
        await update.callback_query.answer()
        context.user_data['new_machine']['notes'] = None
        msg = update.callback_query.message
    else:
        context.user_data['new_machine']['notes'] = update.message.text.strip()
        msg = update.message

    # Persist state to database
    await state_manager.save_state(
        user_id=user_id,
        conversation_type="add_machine",
        current_state="PHOTO",
        data=context.user_data['new_machine']
    )

    keyboard = [[InlineKeyboardButton("Skip ⏭️", callback_data=CB_SKIP)]]
    await msg.reply_text(
        "Send a **photo** of this machine (optional).\n"
        "This helps with identification.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return PHOTO


async def add_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save photo, show confirmation and save."""
    if update.callback_query:  # Skip pressed
        await update.callback_query.answer()
        context.user_data['new_machine']['photo_file_id'] = None
        return await add_confirm(update, context)
    else:
        # Save photo file_id
        photo = update.message.photo[-1]  # Largest size
        context.user_data['new_machine']['photo_file_id'] = photo.file_id
        return await add_confirm(update, context)


async def add_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show confirmation and save machine to database."""
    machine_data = context.user_data.get('new_machine', {})
    user_id = str(update.effective_user.id)

    # Build confirmation message
    text = "✅ **Machine Saved!**\n\n"
    text += f"**{machine_data['nickname']}**\n"
    if machine_data.get('manufacturer'):
        text += f"Manufacturer: {machine_data['manufacturer']}\n"
    if machine_data.get('model_number'):
        text += f"Model: {machine_data['model_number']}\n"

    try:
        machine_id = db.create_machine(user_id, machine_data)
        logger.info(f"User {user_id} created machine {machine_data['nickname']} ({machine_id[:8]})")

        # Clear persistent state on successful save
        await state_manager.clear_state(user_id, "add_machine")

        text += "\nUse /library to view your machines."

        msg = update.callback_query.message if update.callback_query else update.message
        await msg.reply_text(text, parse_mode="Markdown")

    except ValueError as e:
        # Duplicate nickname
        msg = update.callback_query.message if update.callback_query else update.message
        await msg.reply_text(
            f"❌ Error: {str(e)}\n\nPlease use a different nickname.",
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error creating machine: {e}", exc_info=True)
        msg = update.callback_query.message if update.callback_query else update.message
        await msg.reply_text(
            "❌ Error saving machine. Please try again.",
            parse_mode="Markdown"
        )

    # Clean up context
    context.user_data.pop('new_machine', None)
    return ConversationHandler.END


async def add_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel add machine flow."""
    user_id = str(update.effective_user.id)

    # Clear persistent state on cancel
    await state_manager.clear_state(user_id, "add_machine")

    context.user_data.pop('new_machine', None)
    await update.message.reply_text(
        "❌ Cancelled. Use /library to view your machines.",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


# ============================================================================
# Build ConversationHandler
# ============================================================================

add_machine_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(add_start, pattern=f"^{CB_ADD}$"),
        CallbackQueryHandler(add_from_ocr, pattern=f"^{CB_SAVE_OCR}$")
    ],
    states={
        NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_nickname)],
        MANUFACTURER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_manufacturer),
            CallbackQueryHandler(add_manufacturer, pattern=f"^{CB_SKIP}$")
        ],
        MODEL: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_model),
            CallbackQueryHandler(add_model, pattern=f"^{CB_SKIP}$")
        ],
        SERIAL: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_serial),
            CallbackQueryHandler(add_serial, pattern=f"^{CB_SKIP}$")
        ],
        LOCATION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_location),
            CallbackQueryHandler(add_location, pattern=f"^{CB_SKIP}$")
        ],
        NOTES: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_notes),
            CallbackQueryHandler(add_notes, pattern=f"^{CB_SKIP}$")
        ],
        PHOTO: [
            MessageHandler(filters.PHOTO, add_photo),
            CallbackQueryHandler(add_photo, pattern=f"^{CB_SKIP}$")
        ],
    },
    fallbacks=[CommandHandler("cancel", add_cancel)],
    name="add_machine",
    persistent=False  # Don't persist state across restarts
)

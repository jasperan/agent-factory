"""
Telegram bot handlers for commands, messages, and callbacks.

Handlers:
- Command handlers: /start, /help, /agent, /reset
- Message handler: Process user messages with agent
- Callback handlers: Inline button presses (agent selection, approvals)
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from .formatters import ResponseFormatter
from .intent_detector import IntentDetector
from . import kb_handlers
from . import github_handlers


# =============================================================================
# Command Handlers
# =============================================================================


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command.

    Shows welcome message with agent selection keyboard.

    Example:
        User: /start
        Bot: Welcome! Choose an agent: [Research] [Coding] [Bob]
    """
    chat_id = update.effective_chat.id

    # Access bot instance from context
    bot_instance = context.bot_data.get("bot_instance")
    if not bot_instance:
        await update.message.reply_text("Error: Bot not initialized")
        return

    # Check user whitelist
    if not bot_instance._is_user_allowed(chat_id):
        await update.message.reply_text(
            "Sorry, this bot is currently in private mode. "
            "Contact the bot owner for access."
        )
        return

    # Create agent selection keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                "[Research] Research Assistant",
                callback_data="agent_research"
            )
        ],
        [
            InlineKeyboardButton(
                "[Code] Coding Assistant",
                callback_data="agent_coding"
            )
        ],
        [
            InlineKeyboardButton(
                "[Bob] Market Research Specialist",
                callback_data="agent_bob"
            )
        ]
    ]

    welcome_text = (
        "*Welcome to Agent Factory!* 🤖\n\n"
        "Your AI assistant for industrial maintenance and troubleshooting.\n\n"
        "💡 *What I can help with:*\n"
        "• HVAC troubleshooting\n"
        "• Equipment diagnostics\n"
        "• Repair procedures\n"
        "• Technical documentation\n\n"
        "🎯 *Beta Testing - FREE Access*\n"
        "Help me improve! Use the bot, tell me what works (or doesn't).\n"
        "Your feedback shapes the product.\n\n"
        "*Choose an agent to get started:*"
    )

    await update.message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /help command.

    Shows available commands and usage instructions.

    Example:
        User: /help
        Bot: [Command reference]
    """
    help_text = """*Agent Factory Commands*

*Basic Commands:*
/start - Show agent selection menu
/menu - Interactive help menu
/help - Show this help message
/agent - Switch to different agent
/reset - Clear conversation history

*GitHub Automation:*
/listissues - List all open issues
/listissues <label> - List issues by label
/solveissue <number> - Auto-solve issue with FREE Ollama

*How to Use:*
1. Choose an agent with /start or /agent
2. Send your question or task
3. The agent will respond using its tools

*Available Agents:*
- *Research* - Web search, Wikipedia, research tasks
- *Coding* - File operations, code analysis
- *Bob* - Market research and opportunity discovery

*GitHub Example:*
/listissues bug
/solveissue 52
[Bot solves, you approve via buttons]
Issue auto-closes!

*Tips:*
- Be specific in your questions
- Sessions persist - your history is remembered
- Use /reset to start fresh
- Rate limit: 10 messages per minute
- GitHub solving costs $0.00 (FREE Ollama)

*Need more help?*
Visit: github.com/Mikecranesync/Agent-Factory
"""

    await update.message.reply_text(help_text, parse_mode="Markdown")


async def agent_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /agent command.

    Shows agent selection keyboard (same as /start but without welcome).

    Example:
        User: /agent
        Bot: [Agent selection keyboard]
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "[Research] Research Assistant",
                callback_data="agent_research"
            )
        ],
        [
            InlineKeyboardButton(
                "[Code] Coding Assistant",
                callback_data="agent_coding"
            )
        ],
        [
            InlineKeyboardButton(
                "[Bob] Market Research Specialist",
                callback_data="agent_bob"
            )
        ]
    ]

    await update.message.reply_text(
        "*Choose an agent:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def reset_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /reset command.

    Clears conversation history for current chat.

    Example:
        User: /reset
        Bot: Session cleared! Starting fresh.
    """
    chat_id = update.effective_chat.id

    bot_instance = context.bot_data.get("bot_instance")
    if bot_instance:
        bot_instance.session_manager.reset_session(chat_id)

    await update.message.reply_text(
        "*Session cleared!*\n\n"
        "Your conversation history has been reset.\n"
        "Use /agent to choose an agent and start fresh.",
        parse_mode="Markdown"
    )


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /menu command.

    Shows interactive help menu with categories.

    Example:
        User: /menu
        Bot: [Interactive menu with buttons]
    """
    keyboard = [
        [
            InlineKeyboardButton("Commands", callback_data="help_commands"),
            InlineKeyboardButton("Agents", callback_data="help_agents")
        ],
        [
            InlineKeyboardButton("GitHub", callback_data="help_github"),
            InlineKeyboardButton("Tips", callback_data="help_tips")
        ],
        [
            InlineKeyboardButton("Status", callback_data="help_status"),
            InlineKeyboardButton("Quick Start", callback_data="help_quickstart")
        ]
    ]

    menu_text = (
        "*Agent Factory Help Menu*\n\n"
        "Choose a topic to learn more:\n\n"
        "- *Commands* - All available commands\n"
        "- *Agents* - Agent capabilities\n"
        "- *GitHub* - Auto-solve issues\n"
        "- *Tips* - Best practices\n"
        "- *Status* - System metrics\n"
        "- *Quick Start* - Get started in 30 seconds"
    )

    await update.message.reply_text(
        menu_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# =============================================================================
# Message Handler
# =============================================================================


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle user text messages.

    Processes message with selected agent and returns response.

    Flow:
    1. Get chat session
    2. Check rate limit
    3. Validate message
    4. Show typing indicator
    5. Execute agent
    6. Format and send response

    Example:
        User: "What's the weather in Paris?"
        Bot: [typing...] [agent response]
    """
    chat_id = update.effective_chat.id
    message_text = update.message.text

    bot_instance = context.bot_data.get("bot_instance")
    if not bot_instance:
        await update.message.reply_text("Error: Bot not initialized")
        return

    # Check user whitelist
    if not bot_instance._is_user_allowed(chat_id):
        await update.message.reply_text(
            "Sorry, you don't have access to this bot."
        )
        return

    # Check rate limit
    allowed, wait_time = bot_instance.session_manager.check_rate_limit(
        chat_id,
        limit=bot_instance.config.rate_limit
    )

    if not allowed:
        await update.message.reply_text(
            f"Rate limit exceeded. Please wait {wait_time} seconds."
        )
        return

    # Validate message length
    if len(message_text) > bot_instance.config.max_message_length:
        await update.message.reply_text(
            f"Message too long (max {bot_instance.config.max_message_length} chars). "
            "Please shorten your message."
        )
        return

    # Show typing indicator
    if bot_instance.config.typing_indicator:
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)

    # Detect intent from natural language BEFORE routing to agent
    intent_type, parameter = IntentDetector.classify(message_text)

    # Route based on detected intent
    if intent_type == "kb_search":
        # User wants to search knowledge base
        await kb_handlers.kb_search_natural(update, context, parameter)
        return

    elif intent_type == "script_gen":
        # User wants to generate a script
        await kb_handlers.generate_script_natural(update, context, parameter)
        return

    elif intent_type == "github_issue":
        # User wants to solve a GitHub issue
        issue_number = int(parameter)
        await github_handlers.solve_issue_natural(update, context, issue_number)
        return

    # Otherwise, proceed with general chat (existing behavior)
    # Get agent type (auto-select research if not set for conversational mode)
    agent_type = bot_instance.session_manager.get_agent_type(chat_id)
    if not agent_type:
        agent_type = "research"  # Default to research agent for immediate chat
        bot_instance.session_manager.set_agent_type(chat_id, agent_type)

    # Execute agent
    try:
        response = await bot_instance.execute_agent_message(
            chat_id,
            message_text,
            agent_type
        )

        # Format and send response
        chunks = ResponseFormatter.chunk_message(
            response,
            max_chunks=bot_instance.config.max_response_chunks
        )

        for i, chunk in enumerate(chunks):
            if i > 0 and bot_instance.config.typing_indicator:
                # Show typing for subsequent chunks
                await context.bot.send_chat_action(chat_id, ChatAction.TYPING)

            await update.message.reply_text(chunk)

    except Exception as e:
        error_msg = ResponseFormatter.format_error(e)
        await update.message.reply_text(
            f"{error_msg}\n\nPlease try rephrasing your question."
        )


# =============================================================================
# Callback Handlers (Inline Buttons)
# =============================================================================


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle inline button callbacks.

    Handles:
    - Agent selection buttons (agent_research, agent_coding, agent_bob)
    - Approval buttons (approve_*, reject_*)

    Example:
        User clicks: [Research Assistant]
        Callback data: "agent_research"
        Bot: Agent switched to Research
    """
    query = update.callback_query
    await query.answer()  # Acknowledge button press

    chat_id = update.effective_chat.id
    callback_data = query.data

    bot_instance = context.bot_data.get("bot_instance")
    if not bot_instance:
        await query.edit_message_text("Error: Bot not initialized")
        return

    # Handle agent selection
    if callback_data.startswith("agent_"):
        agent_type = callback_data.replace("agent_", "")

        # Set agent type
        bot_instance.session_manager.set_agent_type(chat_id, agent_type)

        # Get agent info
        agent_info = ResponseFormatter.format_agent_info(agent_type, True)

        await query.edit_message_text(
            f"*Agent Selected:* {agent_type.title()}\n\n"
            f"{agent_info}\n\n"
            "Send me a message to get started!",
            parse_mode="Markdown"
        )

    # Handle approval callbacks (Factor 7)
    elif callback_data.startswith("approve_") or callback_data.startswith("reject_"):
        action = "approved" if callback_data.startswith("approve_") else "rejected"

        # Get pending approval
        approval = bot_instance.session_manager.get_pending_approval(chat_id)

        if not approval:
            await query.edit_message_text("No pending approval found.")
            return

        # Clear pending approval
        bot_instance.session_manager.clear_pending_approval(chat_id)

        # Notify user
        await query.edit_message_text(
            f"*Action {action}:* {approval['action']}\n\n"
            "Processing your decision...",
            parse_mode="Markdown"
        )

        # TODO: Resume agent execution with approval result
        # This will be connected to Factor 6 (async task system)
        # For now, just acknowledge

    # Handle help menu callbacks
    elif callback_data.startswith("help_"):
        await _handle_help_callback(query, callback_data)

    else:
        await query.edit_message_text(f"Unknown action: {callback_data}")


async def _handle_help_callback(query, callback_data: str):
    """Handle help menu button callbacks."""
    back_button = [[InlineKeyboardButton("Back to Menu", callback_data="help_back")]]

    if callback_data == "help_commands":
        text = """*All Commands*

*Basic:*
/start - Agent selection
/menu - Interactive help
/help - Full command list
/agent - Switch agent
/reset - Clear history

*GitHub:*
/listissues [label] - List issues
/solveissue <number> - Auto-solve

Use /menu to return."""

    elif callback_data == "help_agents":
        text = """*Available Agents*

*Research:* Web search, Wikipedia
*Coding:* File ops, code analysis
*Bob:* Market research

Choose: /start or /agent"""

    elif callback_data == "help_github":
        text = """*GitHub Automation*

/listissues - All issues
/solveissue 52 - Auto-solve

*Flow:*
1. Bot analyzes issue
2. Generates solution (FREE)
3. You approve
4. Auto-commits & closes

Cost: $0.00 (Ollama)"""

    elif callback_data == "help_tips":
        text = """*Tips & Tricks*

- Be specific
- Sessions persist
- Use /reset for fresh start
- 10 msg/min limit
- 4000 char max
- GitHub: FREE Ollama"""

    elif callback_data == "help_status":
        text = """*System Status*

*GitHub:*
- FREE Ollama
- Auto-solve enabled
- Human approval required

*Bot:*
- 3 agents active
- Sessions persist
- Rate limiting: ON"""

    elif callback_data == "help_quickstart":
        text = """*Quick Start*

1. /start
2. Pick agent
3. Ask question
4. Get answer

Examples:
/listissues bug
/solveissue 52"""

    elif callback_data == "help_back":
        keyboard = [
            [
                InlineKeyboardButton("Commands", callback_data="help_commands"),
                InlineKeyboardButton("Agents", callback_data="help_agents")
            ],
            [
                InlineKeyboardButton("GitHub", callback_data="help_github"),
                InlineKeyboardButton("Tips", callback_data="help_tips")
            ],
            [
                InlineKeyboardButton("Status", callback_data="help_status"),
                InlineKeyboardButton("Quick Start", callback_data="help_quickstart")
            ]
        ]
        await query.edit_message_text(
            "*Agent Factory Help Menu*\n\n"
            "Choose a topic to learn more:\n\n"
            "- *Commands* - All commands\n"
            "- *Agents* - Capabilities\n"
            "- *GitHub* - Auto-solve\n"
            "- *Tips* - Best practices\n"
            "- *Status* - Metrics\n"
            "- *Quick Start* - 30 sec start",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    else:
        text = "Unknown help topic."

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(back_button),
        parse_mode="Markdown"
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle errors in handlers.

    Logs error and sends user-friendly message.

    Example:
        Error occurs in handler
        Bot: Something went wrong. Please try again.
    """
    # Log error (in production, use proper logging)
    print(f"Error: {context.error}")

    # Try to notify user
    if update and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    "Something went wrong processing your request.\n"
                    "Please try again or use /reset to start fresh."
                )
            )
        except Exception:
            pass  # Can't send message, ignore

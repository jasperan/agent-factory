"""
Main Telegram bot for Agent Factory.

Orchestrates all components:
- Configuration
- Session management
- Agent execution
- Handler registration
- Bot lifecycle
- Health check HTTP server
- Graceful shutdown
"""

import asyncio
import os
import signal
from typing import Optional
from aiohttp import web
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from agent_factory.core.agent_factory import AgentFactory
from agent_factory.cli.agent_presets import get_agent

from .config import TelegramConfig
from .session_manager import TelegramSessionManager
from .formatters import ResponseFormatter
from . import handlers
from . import github_handlers
from . import kb_handlers
from . import fieldeye_handlers


class TelegramBot:
    """
    Main Telegram bot for Agent Factory.

    Integrates:
    - Telegram bot API (python-telegram-bot)
    - Agent Factory (agent execution)
    - Session management (per-user state)
    - Security (rate limiting, validation, PII filtering)

    Example:
        >>> config = TelegramConfig.from_env()
        >>> bot = TelegramBot(config)
        >>> await bot.run()
    """

    def __init__(self, config: TelegramConfig):
        """
        Initialize Telegram bot.

        Args:
            config: Bot configuration with security settings

        Example:
            >>> config = TelegramConfig(bot_token="123:ABC")
            >>> bot = TelegramBot(config)
        """
        self.config = config
        self.session_manager = TelegramSessionManager()
        self.factory = AgentFactory(verbose=False)

        # Build application
        self.app = Application.builder().token(config.bot_token).build()

        # Store bot instance in context for handlers
        self.app.bot_data["bot_instance"] = self

        # Register handlers
        self._setup_handlers()

        # Health check server
        self.health_app = None
        self.health_runner = None
        self.start_time = None

        # Shutdown flag
        self._shutdown = False

    def _setup_handlers(self):
        """
        Register all command, message, and callback handlers.

        Handlers are processed in order:
        1. Command handlers (/start, /help, /agent, /reset, /solve-issue, /list-issues, /kb_*, /fieldeye_*)
        2. Callback handlers (button presses)
        3. Message handler (text messages)
        4. Error handler (global error handling)
        """
        # Command handlers
        self.app.add_handler(CommandHandler("start", handlers.start_handler))
        self.app.add_handler(CommandHandler("menu", handlers.menu_handler))
        self.app.add_handler(CommandHandler("help", handlers.help_handler))
        self.app.add_handler(CommandHandler("agent", handlers.agent_handler))
        self.app.add_handler(CommandHandler("reset", handlers.reset_handler))

        # GitHub automation commands
        self.app.add_handler(CommandHandler("solveissue", github_handlers.solve_issue_handler))
        self.app.add_handler(CommandHandler("listissues", github_handlers.list_issues_handler))

        # Knowledge Base commands
        self.app.add_handler(CommandHandler("kb_stats", kb_handlers.kb_stats_handler))
        self.app.add_handler(CommandHandler("kb_search", kb_handlers.kb_search_handler))
        self.app.add_handler(CommandHandler("kb_get", kb_handlers.kb_get_handler))
        self.app.add_handler(CommandHandler("generate_script", kb_handlers.generate_script_handler))

        # Field Eye commands
        self.app.add_handler(CommandHandler("fieldeye_upload", fieldeye_handlers.fieldeye_upload_handler))
        self.app.add_handler(CommandHandler("fieldeye_stats", fieldeye_handlers.fieldeye_stats_handler))
        self.app.add_handler(CommandHandler("fieldeye_defects", fieldeye_handlers.fieldeye_defects_handler))
        self.app.add_handler(CommandHandler("fieldeye_sessions", fieldeye_handlers.fieldeye_sessions_handler))

        # Callback handler (inline buttons)
        self.app.add_handler(CallbackQueryHandler(self._unified_callback_handler))

        # Message handler (text messages, NOT commands)
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                handlers.message_handler
            )
        )

        # Error handler
        self.app.add_error_handler(handlers.error_handler)

    async def _unified_callback_handler(self, update, context):
        """
        Unified callback handler that routes to appropriate handler.

        Routes callbacks based on prefix:
        - gh_* → GitHub handlers (approve/reject issue solutions)
        - agent_* → Agent selection handlers
        - approve_*/reject_* → General approval handlers
        """
        query = update.callback_query
        callback_data = query.data

        if callback_data.startswith("gh_"):
            # GitHub callback
            await github_handlers.github_approval_callback(update, context)
        else:
            # Regular callback (agent selection, etc.)
            await handlers.callback_handler(update, context)

    def _is_user_allowed(self, chat_id: int) -> bool:
        """
        Check if user is allowed to use bot.

        Args:
            chat_id: Telegram chat ID

        Returns:
            True if user is allowed, False otherwise

        Example:
            >>> bot._is_user_allowed(12345)
            True
        """
        if self.config.allowed_users is None:
            return True  # No whitelist, all users allowed

        return chat_id in self.config.allowed_users

    def _format_chat_history(self, session) -> str:
        """
        Convert Session history to LangChain chat_history format.

        Args:
            session: Session object with conversation history

        Returns:
            Formatted chat history string

        Example:
            >>> history = bot._format_chat_history(session)
            'user: What is Python?\nassistant: Python is a programming language.'
        """
        messages = session.history.get_messages()
        if len(messages) <= 1:
            return ""

        formatted = []
        # Exclude the current message (last one) as it's being processed
        for msg in messages[:-1]:
            formatted.append(f"{msg.role}: {msg.content}")

        return "\n".join(formatted)

    async def execute_agent_message(
        self,
        chat_id: int,
        message: str,
        agent_type: str
    ) -> str:
        """
        Execute agent with user message.

        Flow:
        1. Get or create session
        2. Add user message to session
        3. Get agent executor
        4. Execute agent with timeout
        5. Add response to session
        6. Filter PII if enabled
        7. Return response

        Args:
            chat_id: Telegram chat ID
            message: User message
            agent_type: Agent type (research, coding, bob)

        Returns:
            Agent response

        Raises:
            TimeoutError: If agent execution exceeds max time
            Exception: If agent execution fails

        Example:
            >>> response = await bot.execute_agent_message(
            ...     12345,
            ...     "What's the capital of France?",
            ...     "research"
            ... )
        """
        # Get or create session
        session = self.session_manager.get_or_create(chat_id, agent_type)

        # Add user message to history
        session.add_user_message(message)

        # Get or create agent executor (reuse for context retention)
        agent_executor = session.get_agent_executor(agent_type)
        if agent_executor is None:
            try:
                agent_executor = get_agent(agent_type, self.factory)
                session.set_agent_executor(agent_type, agent_executor)
            except ValueError as e:
                return f"Error: Invalid agent type '{agent_type}'. Use /agent to choose a valid agent."

        # Execute agent with timeout
        try:
            # Format chat history for context
            chat_history = self._format_chat_history(session)

            # Inject history into the input prompt for context
            if chat_history:
                input_with_context = f"""PREVIOUS CONVERSATION:
{chat_history}

CURRENT MESSAGE:
{message}

Please respond to the current message, referencing the previous conversation when relevant."""
            else:
                input_with_context = message

            response = await asyncio.wait_for(
                asyncio.to_thread(
                    agent_executor.invoke,
                    {"input": input_with_context}
                ),
                timeout=self.config.max_agent_execution_time
            )

            # Extract response text
            if isinstance(response, dict):
                response_text = response.get("output", str(response))
            else:
                response_text = str(response)

        except asyncio.TimeoutError:
            response_text = (
                f"Agent execution timed out after {self.config.max_agent_execution_time}s. "
                "Please try a simpler query or use /reset to start fresh."
            )

        except Exception as e:
            response_text = ResponseFormatter.format_error(e)

        # Add response to session history
        session.add_assistant_message(response_text)

        # Save session
        session.save()

        # LOG QUERY FOR STREAM 2 (Query Intelligence)
        # This captures what equipment users ask about to prioritize scraping
        self._log_query_intelligence(user_id, message)

        # Filter PII if enabled
        if self.config.enable_pii_filtering:
            response_text = self._filter_pii(response_text)

        return response_text

    def _filter_pii(self, text: str) -> str:
        """
        Filter PII from response text.

        Uses existing PII detector from Agent Factory.

        Args:
            text: Response text

        Returns:
            Text with PII filtered

        Example:
            >>> bot._filter_pii("My email is john@example.com")
            'My email is [EMAIL]'
        """
        # TODO: Integrate with agent_factory/security/pii_detector.py
        # For now, basic implementation
        import re

        # Filter emails
        text = re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[EMAIL]',
            text
        )

        # Filter phone numbers (simple patterns)
        text = re.sub(
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            '[PHONE]',
            text
        )

        # Filter credit cards
        text = re.sub(
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            '[CREDIT_CARD]',
            text
        )

        return text

    def _log_query_intelligence(self, user_id: str, query: str):
        """
        Log query for Stream 2 intelligence (DaaS business model).

        Captures what equipment users ask about to prioritize manual scraping.
        This is the "secret weapon" - user queries tell us what's valuable.

        Args:
            user_id: Telegram user ID (will be hashed for privacy)
            query: User's query text

        Example queries to capture:
            - "ABB ACS880 error 2210"
            - "Siemens S7-1200 PLC troubleshooting"
            - "Carrier 30XA chiller maintenance"
        """
        import re
        import hashlib
        import json
        from datetime import datetime

        # Hash user ID for privacy (GDPR/CCPA compliance)
        user_hash = hashlib.sha256(str(user_id).encode()).hexdigest()[:16]

        # Extract equipment models using common patterns
        equipment_patterns = [
            r'\b(ACS\d+|ACH\d+|ACS[A-Z]\d+)\b',  # ABB drives
            r'\b(S7-\d+)\b',  # Siemens PLCs
            r'\b(\d+XA|\d+HX)\b',  # Carrier chillers
            r'\b(PowerFlex \d+|ControlLogix)\b',  # Rockwell
        ]

        equipment_model = None
        for pattern in equipment_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                equipment_model = match.group(1).upper()
                break

        # Extract error codes (e.g., "error 2210", "fault E123")
        error_code = None
        error_match = re.search(r'\b(?:error|fault|code)\s*([A-Z]?\d+)\b', query, re.IGNORECASE)
        if error_match:
            error_code = error_match.group(1).upper()

        # Only log if query mentions equipment or errors (not general chat)
        if equipment_model or error_code or any(word in query.lower() for word in
            ['manual', 'troubleshoot', 'repair', 'service', 'maintenance', 'diagnostic', 'wiring']):

            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'user_hash': user_hash,
                'equipment_model': equipment_model,
                'error_code': error_code,
                'query_length': len(query),
                'has_error_keyword': bool(error_code),
                'query_preview': query[:100]  # First 100 chars only for privacy
            }

            # TODO: Write to database (query_intelligence table)
            # For now, log to file for manual review
            try:
                with open('query_intelligence.log', 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
            except Exception:
                pass  # Silent fail - don't break bot if logging fails

    async def _health_check_handler(self, request):
        """
        HTTP health check endpoint.

        Returns JSON with bot status, PID, uptime.

        Response:
            {'status': 'running', 'pid': 12345, 'uptime_seconds': 3600}
        """
        import time
        uptime = time.time() - self.start_time if self.start_time else 0

        return web.json_response({
            'status': 'running',
            'pid': os.getpid(),
            'uptime_seconds': uptime,
            'version': '1.0.0'
        })

    async def _start_health_server(self):
        """Start health check HTTP server on localhost:9876."""
        self.health_app = web.Application()
        self.health_app.router.add_get('/health', self._health_check_handler)

        self.health_runner = web.AppRunner(self.health_app)
        await self.health_runner.setup()

        site = web.TCPSite(self.health_runner, 'localhost', 9876)
        await site.start()

        print("[OK] Health check endpoint: http://localhost:9876/health")

    async def _stop_health_server(self):
        """Stop health check HTTP server."""
        if self.health_runner:
            await self.health_runner.cleanup()

    def _setup_signal_handlers(self):
        """
        Setup graceful shutdown on SIGTERM/SIGINT.

        Ensures bot stops cleanly and releases lock file.
        """
        def signal_handler(signum, frame):
            print(f"\n\n[WARNING] Received signal {signum}")
            self._shutdown = True

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def run(self):
        """
        Start bot in polling mode with health check and graceful shutdown.

        Polls Telegram servers for updates.
        Runs until interrupted (Ctrl+C) or SIGTERM.

        Example:
            >>> await bot.run()
            Starting Telegram bot...
            Bot is running (polling mode)
            Press Ctrl+C to stop
        """
        import time
        self.start_time = time.time()

        print("=" * 60)
        print("Starting Agent Factory Telegram Bot")
        print("=" * 60)
        print(f"Config:")
        print(f"  - Rate limit: {self.config.rate_limit} msg/min")
        print(f"  - Max message length: {self.config.max_message_length} chars")
        print(f"  - Session TTL: {self.config.session_ttl_hours} hours")
        print(f"  - PII filtering: {self.config.enable_pii_filtering}")
        print(f"  - User whitelist: {len(self.config.allowed_users) if self.config.allowed_users else 'None (all users)'}")
        print(f"  - PID: {os.getpid()}")
        print("=" * 60)

        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()

        # Start health check server
        await self._start_health_server()

        print("Bot is running (polling mode)")
        print("Press Ctrl+C to stop")
        print("=" * 60)

        # Start polling
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

        # Run forever until interrupted
        try:
            # Keep alive
            while not self._shutdown:
                await asyncio.sleep(1)

                # Periodic cleanup of expired sessions
                if asyncio.get_event_loop().time() % 3600 < 1:  # Every hour
                    cleaned = self.session_manager.cleanup_expired(
                        self.config.session_ttl_hours
                    )
                    if cleaned > 0:
                        print(f"Cleaned {cleaned} expired sessions")

        except KeyboardInterrupt:
            print("\n\n[WARNING] Keyboard interrupt")

        finally:
            print("\nShutting down bot...")

            # Stop health server
            await self._stop_health_server()

            # Cleanup Telegram bot
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()

            print("[OK] Bot stopped cleanly")

    def get_stats(self) -> dict:
        """
        Get bot statistics.

        Returns:
            Dictionary with stats:
            - sessions: Session statistics
            - config: Bot configuration summary

        Example:
            >>> stats = bot.get_stats()
            >>> print(stats['sessions']['active_sessions'])
            5
        """
        return {
            "sessions": self.session_manager.get_stats(),
            "config": {
                "rate_limit": self.config.rate_limit,
                "session_ttl_hours": self.config.session_ttl_hours,
                "pii_filtering": self.config.enable_pii_filtering,
                "user_whitelist_enabled": self.config.allowed_users is not None
            }
        }

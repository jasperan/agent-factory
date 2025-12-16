"""
Agent Management for Telegram Admin Panel

Monitor and control agents:
- View agent status (running/stopped/error)
- Stream agent logs
- Performance metrics (tokens, cost, latency)
- Start/stop agents (future: actual control)
- Trace links to LangFuse dashboard

Commands:
    /agents - List all agents with status
    /agent <name> - Detailed view of specific agent
    /agent_logs <name> - Stream recent logs

Usage:
    from agent_factory.integrations.telegram.admin import AgentManager

    manager = AgentManager()
    app.add_handler(CommandHandler("agents", manager.handle_agents))
"""

import logging
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from .permissions import require_access

logger = logging.getLogger(__name__)


@dataclass
class AgentStatus:
    """Agent status information"""
    name: str
    status: str  # 'running', 'stopped', 'error'
    last_run: Optional[datetime]
    total_runs: int
    success_rate: float
    avg_tokens: int
    avg_cost: float
    avg_latency: float
    trace_url: Optional[str]


class AgentManager:
    """
    Manages agent monitoring and control.

    Provides:
    - Real-time agent status
    - Performance metrics
    - Log streaming
    - LangFuse trace links
    """

    def __init__(self):
        """Initialize agent manager"""
        self.langfuse_base_url = os.getenv("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com")
        logger.info("AgentManager initialized")

    @require_access
    async def handle_agents(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /agents command - show all agents status.

        Args:
            update: Telegram update
            context: Callback context
        """
        await update.message.reply_text("🔄 Fetching agent status...")

        try:
            # Get agent status
            agents = await self._get_all_agents()

            if not agents:
                await update.message.reply_text(
                    "⚠️ No agents found.\n\n"
                    "Agents will appear here after their first run.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            # Format status message
            message = await self._format_agents_list(agents)

            # Build keyboard for detailed views
            keyboard = []
            for agent in agents[:5]:  # Top 5 agents
                keyboard.append([
                    InlineKeyboardButton(
                        f"📊 {agent.name}",
                        callback_data=f"agent_detail_{agent.name}"
                    )
                ])

            keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="agents_refresh")])
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )

        except Exception as e:
            logger.error(f"Failed to fetch agents: {e}")
            await update.message.reply_text(
                f"❌ Failed to fetch agent status: {str(e)}\n\n"
                "Please try again or check system logs.",
                parse_mode=ParseMode.MARKDOWN
            )

    @require_access
    async def handle_agent_detail(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /agent <name> command - show detailed agent view.

        Args:
            update: Telegram update
            context: Callback context
        """
        if not context.args:
            await update.message.reply_text(
                "❌ Usage: `/agent <agent_name>`\n\n"
                "Example: `/agent research_agent`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        agent_name = context.args[0]

        await update.message.reply_text(f"🔄 Fetching details for {agent_name}...")

        try:
            agent = await self._get_agent_status(agent_name)

            if not agent:
                await update.message.reply_text(
                    f"❌ Agent not found: {agent_name}\n\n"
                    "Use /agents to see all available agents.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            # Format detailed message
            message = await self._format_agent_detail(agent)

            # Build action keyboard
            keyboard = [
                [
                    InlineKeyboardButton("📜 View Logs", callback_data=f"agent_logs_{agent_name}"),
                    InlineKeyboardButton("📊 Metrics", callback_data=f"agent_metrics_{agent_name}"),
                ],
                [
                    InlineKeyboardButton("🔗 LangFuse", url=agent.trace_url) if agent.trace_url else None,
                    InlineKeyboardButton("🔄 Refresh", callback_data=f"agent_refresh_{agent_name}"),
                ],
                [InlineKeyboardButton("◀️ Back to List", callback_data="agents_list")],
            ]
            # Filter out None buttons
            keyboard = [[btn for btn in row if btn] for row in keyboard]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )

        except Exception as e:
            logger.error(f"Failed to fetch agent details: {e}")
            await update.message.reply_text(
                f"❌ Failed to fetch agent details: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )

    @require_access
    async def handle_agent_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /agent_logs <name> command - stream recent logs.

        Args:
            update: Telegram update
            context: Callback context
        """
        if not context.args:
            await update.message.reply_text(
                "❌ Usage: `/agent_logs <agent_name>`\n\n"
                "Example: `/agent_logs research_agent`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        agent_name = context.args[0]

        await update.message.reply_text(f"🔄 Fetching logs for {agent_name}...")

        try:
            logs = await self._get_agent_logs(agent_name, limit=20)

            if not logs:
                await update.message.reply_text(
                    f"⚠️ No logs found for {agent_name}",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            # Format logs
            message = f"📜 *Recent Logs: {agent_name}*\n\n```\n"
            for log in logs:
                message += f"{log['timestamp']} [{log['level']}] {log['message']}\n"
            message += "```"

            # Truncate if too long (Telegram 4096 char limit)
            if len(message) > 4000:
                message = message[:3900] + "\n...\n(truncated)\n```"

            keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data=f"agent_logs_{agent_name}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )

        except Exception as e:
            logger.error(f"Failed to fetch logs: {e}")
            await update.message.reply_text(
                f"❌ Failed to fetch logs: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )

    async def _get_all_agents(self) -> List[AgentStatus]:
        """
        Get status for all agents.

        Returns:
            List of agent status objects

        TODO: Query actual data sources:
        - LangFuse API for traces
        - Supabase agent_runs table
        - VPS service status
        """
        # Placeholder data for now
        # Will be replaced with real queries in integration phase
        return [
            AgentStatus(
                name="research_agent",
                status="running",
                last_run=datetime.now() - timedelta(minutes=5),
                total_runs=127,
                success_rate=0.95,
                avg_tokens=1234,
                avg_cost=0.05,
                avg_latency=2.3,
                trace_url=f"{self.langfuse_base_url}/traces"
            ),
            AgentStatus(
                name="content_agent",
                status="running",
                last_run=datetime.now() - timedelta(minutes=15),
                total_runs=89,
                success_rate=0.92,
                avg_tokens=2345,
                avg_cost=0.08,
                avg_latency=3.1,
                trace_url=f"{self.langfuse_base_url}/traces"
            ),
            AgentStatus(
                name="analyst_agent",
                status="stopped",
                last_run=datetime.now() - timedelta(hours=2),
                total_runs=45,
                success_rate=0.88,
                avg_tokens=987,
                avg_cost=0.03,
                avg_latency=1.8,
                trace_url=f"{self.langfuse_base_url}/traces"
            ),
        ]

    async def _get_agent_status(self, agent_name: str) -> Optional[AgentStatus]:
        """
        Get status for specific agent.

        Args:
            agent_name: Agent name

        Returns:
            Agent status or None if not found
        """
        agents = await self._get_all_agents()
        for agent in agents:
            if agent.name == agent_name:
                return agent
        return None

    async def _get_agent_logs(self, agent_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent logs for agent.

        Args:
            agent_name: Agent name
            limit: Maximum number of logs

        Returns:
            List of log entries

        TODO: Query actual log sources:
        - Database logs table
        - VPS docker logs
        - CloudWatch/Datadog
        """
        # Placeholder data
        return [
            {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "level": "INFO",
                "message": f"[{agent_name}] Processing request"
            },
            {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "level": "INFO",
                "message": f"[{agent_name}] Generated response in 2.1s"
            },
            {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "level": "DEBUG",
                "message": f"[{agent_name}] Tokens used: 1234"
            },
        ]

    async def _format_agents_list(self, agents: List[AgentStatus]) -> str:
        """Format agents list for display"""
        message = "🤖 *Agent Status Overview*\n\n"

        # Summary stats
        total = len(agents)
        running = sum(1 for a in agents if a.status == "running")
        stopped = sum(1 for a in agents if a.status == "stopped")
        errors = sum(1 for a in agents if a.status == "error")

        message += f"*Total:* {total} agents\n"
        message += f"✅ Running: {running}\n"
        message += f"⏸️ Stopped: {stopped}\n"
        if errors > 0:
            message += f"❌ Errors: {errors}\n"
        message += "\n"

        # Individual agents
        for agent in agents:
            status_icon = {
                "running": "✅",
                "stopped": "⏸️",
                "error": "❌"
            }.get(agent.status, "❓")

            message += f"{status_icon} *{agent.name}*\n"
            message += f"  • Runs: {agent.total_runs} ({agent.success_rate:.0%} success)\n"
            message += f"  • Avg Cost: ${agent.avg_cost:.4f}\n"
            message += f"  • Avg Latency: {agent.avg_latency:.1f}s\n"

            if agent.last_run:
                time_ago = self._time_ago(agent.last_run)
                message += f"  • Last Run: {time_ago}\n"

            message += "\n"

        return message

    async def _format_agent_detail(self, agent: AgentStatus) -> str:
        """Format detailed agent view"""
        status_icon = {
            "running": "✅",
            "stopped": "⏸️",
            "error": "❌"
        }.get(agent.status, "❓")

        message = f"{status_icon} *{agent.name}*\n\n"

        message += "*Status Information:*\n"
        message += f"• State: `{agent.status}`\n"
        if agent.last_run:
            message += f"• Last Run: {agent.last_run.strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += f"• Time Ago: {self._time_ago(agent.last_run)}\n"
        message += "\n"

        message += "*Performance Metrics:*\n"
        message += f"• Total Runs: {agent.total_runs}\n"
        message += f"• Success Rate: {agent.success_rate:.1%}\n"
        message += f"• Avg Tokens: {agent.avg_tokens:,}\n"
        message += f"• Avg Cost: ${agent.avg_cost:.4f}\n"
        message += f"• Avg Latency: {agent.avg_latency:.2f}s\n"
        message += "\n"

        message += "*Quick Actions:*\n"
        message += "• View logs (📜)\n"
        message += "• View metrics (📊)\n"
        if agent.trace_url:
            message += "• View in LangFuse (🔗)\n"

        return message

    def _time_ago(self, dt: datetime) -> str:
        """Format time ago string"""
        delta = datetime.now() - dt
        seconds = delta.total_seconds()

        if seconds < 60:
            return f"{int(seconds)}s ago"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m ago"
        elif seconds < 86400:
            return f"{int(seconds / 3600)}h ago"
        else:
            return f"{int(seconds / 86400)}d ago"

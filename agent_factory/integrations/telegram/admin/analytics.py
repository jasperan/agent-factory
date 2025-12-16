"""
Analytics Dashboard for Telegram Admin Panel

Monitor performance and costs:
- Today's statistics summary
- Agent performance graphs (text-based)
- API cost breakdown (OpenAI/Anthropic)
- Revenue tracking (Stripe integration)
- User engagement metrics

Commands:
    /metrics - Today's summary
    /metrics week - Weekly dashboard
    /costs - API cost breakdown
    /revenue - Stripe revenue stats

Usage:
    from agent_factory.integrations.telegram.admin import Analytics

    analytics = Analytics()
    app.add_handler(CommandHandler("metrics", analytics.handle_metrics))
"""

import logging
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from .permissions import require_access

logger = logging.getLogger(__name__)


class TimeRange(str, Enum):
    """Time range for metrics"""
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"


@dataclass
class DailyMetrics:
    """Daily metrics summary"""
    date: datetime
    total_requests: int
    successful: int
    failed: int
    avg_latency: float
    total_tokens: int
    total_cost: float
    agents_active: int


@dataclass
class CostBreakdown:
    """API cost breakdown"""
    openai_cost: float
    anthropic_cost: float
    total_cost: float
    openai_tokens: int
    anthropic_tokens: int
    requests_by_model: Dict[str, int]


@dataclass
class RevenueMetrics:
    """Revenue metrics"""
    total_revenue: float
    subscriptions: int
    one_time: float
    mrr: float  # Monthly recurring revenue
    churn_rate: float


class Analytics:
    """
    Manages analytics dashboard and metrics.

    Provides:
    - Daily/weekly/monthly metrics
    - Cost tracking by provider
    - Revenue analytics
    - Agent performance graphs
    """

    def __init__(self):
        """Initialize analytics"""
        self.langfuse_url = os.getenv("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com")
        logger.info("Analytics initialized")

    @require_access
    async def handle_metrics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /metrics command - show dashboard.

        Args:
            update: Telegram update
            context: Callback context
        """
        # Parse time range argument
        time_range = TimeRange.TODAY
        if context.args and len(context.args) > 0:
            arg = context.args[0].lower()
            if arg in ["week", "w"]:
                time_range = TimeRange.WEEK
            elif arg in ["month", "m"]:
                time_range = TimeRange.MONTH

        await update.message.reply_text(f"📊 Fetching {time_range.value} metrics...")

        try:
            metrics = await self._get_metrics(time_range)

            # Format metrics message
            message = await self._format_metrics(metrics, time_range)

            # Build action keyboard
            keyboard = [
                [
                    InlineKeyboardButton("Today", callback_data="metrics_today"),
                    InlineKeyboardButton("Week", callback_data="metrics_week"),
                    InlineKeyboardButton("Month", callback_data="metrics_month"),
                ],
                [
                    InlineKeyboardButton("💰 Costs", callback_data="metrics_costs"),
                    InlineKeyboardButton("💵 Revenue", callback_data="metrics_revenue"),
                ],
                [InlineKeyboardButton("🔄 Refresh", callback_data="metrics_refresh")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )

        except Exception as e:
            logger.error(f"Failed to fetch metrics: {e}")
            await update.message.reply_text(
                f"❌ Failed to fetch metrics: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )

    @require_access
    async def handle_costs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /costs command - show API cost breakdown.

        Args:
            update: Telegram update
            context: Callback context
        """
        await update.message.reply_text("💰 Fetching cost breakdown...")

        try:
            costs = await self._get_cost_breakdown()

            # Format cost message
            message = await self._format_costs(costs)

            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Failed to fetch costs: {e}")
            await update.message.reply_text(
                f"❌ Failed to fetch costs: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )

    @require_access
    async def handle_revenue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /revenue command - show Stripe revenue stats.

        Args:
            update: Telegram update
            context: Callback context
        """
        await update.message.reply_text("💵 Fetching revenue stats...")

        try:
            revenue = await self._get_revenue_metrics()

            # Format revenue message
            message = await self._format_revenue(revenue)

            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Failed to fetch revenue: {e}")
            await update.message.reply_text(
                f"❌ Failed to fetch revenue: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )

    async def _get_metrics(self, time_range: TimeRange) -> List[DailyMetrics]:
        """
        Get metrics for time range.

        Args:
            time_range: Time range to query

        Returns:
            List of daily metrics

        TODO: Query LangFuse API and database
        """
        # Placeholder data for now
        days = {"today": 1, "week": 7, "month": 30}[time_range.value]

        metrics = []
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            metrics.append(
                DailyMetrics(
                    date=date,
                    total_requests=120 - i * 10,
                    successful=110 - i * 9,
                    failed=10 - i,
                    avg_latency=2.3 + i * 0.1,
                    total_tokens=15000 - i * 1000,
                    total_cost=7.50 - i * 0.5,
                    agents_active=5
                )
            )

        return metrics

    async def _get_cost_breakdown(self) -> CostBreakdown:
        """
        Get API cost breakdown.

        Returns:
            Cost breakdown by provider

        TODO: Query LangFuse cost tracking API
        """
        # Placeholder data
        return CostBreakdown(
            openai_cost=12.34,
            anthropic_cost=5.67,
            total_cost=18.01,
            openai_tokens=25000,
            anthropic_tokens=12000,
            requests_by_model={
                "gpt-4o": 45,
                "gpt-4o-mini": 78,
                "claude-3-5-sonnet-20241022": 23,
            }
        )

    async def _get_revenue_metrics(self) -> RevenueMetrics:
        """
        Get revenue metrics from Stripe.

        Returns:
            Revenue metrics

        TODO: Query Stripe API
        """
        # Placeholder data
        return RevenueMetrics(
            total_revenue=2450.00,
            subscriptions=12,
            one_time=890.00,
            mrr=1560.00,
            churn_rate=0.08
        )

    async def _format_metrics(self, metrics: List[DailyMetrics], time_range: TimeRange) -> str:
        """Format metrics for display"""
        if not metrics:
            return "⚠️ No metrics available"

        message = f"📊 *Metrics Dashboard ({time_range.value.title()})*\n\n"

        # Summary stats
        total_requests = sum(m.total_requests for m in metrics)
        total_successful = sum(m.successful for m in metrics)
        total_failed = sum(m.failed for m in metrics)
        total_cost = sum(m.total_cost for m in metrics)
        avg_latency = sum(m.avg_latency for m in metrics) / len(metrics)
        success_rate = total_successful / total_requests if total_requests > 0 else 0

        message += "*Summary:*\n"
        message += f"• Total Requests: {total_requests:,}\n"
        message += f"• Success Rate: {success_rate:.1%}\n"
        message += f"• Avg Latency: {avg_latency:.2f}s\n"
        message += f"• Total Cost: ${total_cost:.2f}\n"
        message += f"• Active Agents: {metrics[0].agents_active}\n\n"

        # Today's details (if showing week/month)
        if time_range != TimeRange.TODAY and metrics:
            today = metrics[0]
            message += "*Today:*\n"
            message += f"• Requests: {today.total_requests}\n"
            message += f"• Cost: ${today.total_cost:.2f}\n"
            message += f"• Tokens: {today.total_tokens:,}\n\n"

        # Simple text-based graph for week/month
        if len(metrics) > 1:
            message += "*Request Volume:*\n"
            message += self._draw_bar_chart(
                [m.total_requests for m in reversed(metrics[-7:])],
                max_width=20
            )
            message += "\n"

        # Failed requests breakdown (if any)
        if total_failed > 0:
            message += f"\n⚠️ Failed Requests: {total_failed} ({total_failed/total_requests:.1%})\n"

        return message

    async def _format_costs(self, costs: CostBreakdown) -> str:
        """Format cost breakdown"""
        message = "💰 *API Cost Breakdown (Today)*\n\n"

        message += "*Total Cost:* "
        message += f"${costs.total_cost:.2f}\n\n"

        # Provider breakdown
        message += "*By Provider:*\n"
        openai_pct = costs.openai_cost / costs.total_cost if costs.total_cost > 0 else 0
        anthropic_pct = costs.anthropic_cost / costs.total_cost if costs.total_cost > 0 else 0

        message += f"• OpenAI: ${costs.openai_cost:.2f} ({openai_pct:.0%})\n"
        message += "  " + self._draw_progress_bar(openai_pct, width=20) + "\n"

        message += f"• Anthropic: ${costs.anthropic_cost:.2f} ({anthropic_pct:.0%})\n"
        message += "  " + self._draw_progress_bar(anthropic_pct, width=20) + "\n\n"

        # Token usage
        message += "*Token Usage:*\n"
        message += f"• OpenAI: {costs.openai_tokens:,} tokens\n"
        message += f"• Anthropic: {costs.anthropic_tokens:,} tokens\n\n"

        # Model breakdown
        message += "*By Model:*\n"
        for model, count in sorted(costs.requests_by_model.items(), key=lambda x: x[1], reverse=True):
            message += f"• {model}: {count} requests\n"

        return message

    async def _format_revenue(self, revenue: RevenueMetrics) -> str:
        """Format revenue metrics"""
        message = "💵 *Revenue Dashboard*\n\n"

        message += "*Total Revenue:* "
        message += f"${revenue.total_revenue:.2f}\n\n"

        message += "*Breakdown:*\n"
        message += f"• Subscriptions: ${revenue.mrr:.2f}/mo ({revenue.subscriptions} active)\n"
        message += f"• One-time: ${revenue.one_time:.2f}\n\n"

        message += "*Metrics:*\n"
        message += f"• MRR: ${revenue.mrr:.2f}\n"
        message += f"• Churn Rate: {revenue.churn_rate:.1%}\n"

        # Simple projection
        annual_projection = revenue.mrr * 12
        message += f"• Annual Projection: ${annual_projection:.2f}\n\n"

        if revenue.churn_rate > 0.1:
            message += "⚠️ High churn rate - review customer satisfaction\n"

        return message

    def _draw_bar_chart(self, values: List[int], max_width: int = 20) -> str:
        """Draw simple ASCII bar chart"""
        if not values:
            return ""

        max_val = max(values)
        if max_val == 0:
            return "\n".join([f"Day {i+1}: " for i in range(len(values))])

        chart = ""
        for i, val in enumerate(values):
            bar_len = int((val / max_val) * max_width)
            bar = "█" * bar_len
            chart += f"Day {i+1}: {bar} {val}\n"

        return chart

    def _draw_progress_bar(self, percentage: float, width: int = 20) -> str:
        """Draw progress bar"""
        filled = int(percentage * width)
        empty = width - filled
        return "█" * filled + "░" * empty

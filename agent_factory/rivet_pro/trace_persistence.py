"""
RIVET Pro Phase 6: Trace Persistence Layer

Persists AgentTrace data to Supabase for analytics and debugging.
Supports batch inserts, query dashboard, and cost tracking.

Usage:
    from agent_factory.rivet_pro.trace_persistence import TracePersistence

    persistence = TracePersistence()

    # Save trace
    trace = AgentTrace(...)
    persistence.save_trace(trace)

    # Query traces
    traces = persistence.get_user_traces(user_id="telegram_123", limit=10)

    # Get analytics
    stats = persistence.get_analytics(days=7)
"""

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from supabase import create_client, Client
from agent_factory.rivet_pro.models import AgentTrace

logger = logging.getLogger(__name__)


class TracePersistence:
    """Supabase persistence layer for AgentTrace data."""

    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """Initialize Supabase client.

        Args:
            supabase_url: Supabase project URL (defaults to SUPABASE_URL env var)
            supabase_key: Supabase service role key (defaults to SUPABASE_SERVICE_ROLE_KEY env var)
        """
        self.url = supabase_url or os.getenv("SUPABASE_URL")
        self.key = supabase_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not self.url or not self.key:
            logger.warning("Supabase credentials not found. Trace persistence disabled.")
            self.client = None
            return

        try:
            self.client: Client = create_client(self.url, self.key)
            logger.info("TracePersistence initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None

    def save_trace(self, trace: AgentTrace, tokens_used: int = 0, estimated_cost_usd: float = 0.0) -> bool:
        """Save a single trace to Supabase.

        Args:
            trace: AgentTrace object to persist
            tokens_used: Total tokens used (for cost tracking)
            estimated_cost_usd: Estimated API cost in USD

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.debug("Supabase client not initialized. Skipping trace save.")
            return False

        try:
            # Convert AgentTrace to database format
            trace_data = {
                "request_id": trace.request_id,
                "user_id": trace.user_id,
                "channel": trace.channel if isinstance(trace.channel, str) else trace.channel.value,
                "message_type": trace.message_type if isinstance(trace.message_type, str) else trace.message_type.value,
                "intent": trace.intent.model_dump(),  # Convert Pydantic model to dict
                "route": trace.route if isinstance(trace.route, str) else trace.route.value,
                "agent_id": trace.agent_id if isinstance(trace.agent_id, str) else trace.agent_id.value,
                "response_text": trace.response_text,
                "docs_retrieved": trace.docs_retrieved,
                "doc_sources": trace.doc_sources,
                "processing_time_ms": trace.processing_time_ms,
                "llm_calls": trace.llm_calls,
                "tokens_used": tokens_used,
                "estimated_cost_usd": estimated_cost_usd,
                "research_triggered": trace.research_triggered,
                "kb_enrichment_triggered": trace.kb_enrichment_triggered,
                "error": trace.error,
                "timestamp": trace.timestamp.isoformat(),
            }

            # Insert into Supabase
            result = self.client.table("agent_traces").insert(trace_data).execute()

            route_str = trace.route if isinstance(trace.route, str) else trace.route.value
            agent_str = trace.agent_id if isinstance(trace.agent_id, str) else trace.agent_id.value
            logger.info(f"Trace saved: {trace.request_id} (route={route_str}, agent={agent_str})")
            return True

        except Exception as e:
            logger.error(f"Failed to save trace {trace.request_id}: {e}")
            return False

    def save_traces_batch(self, traces: List[Dict[str, Any]]) -> int:
        """Save multiple traces in a batch (faster for bulk inserts).

        Args:
            traces: List of trace dictionaries (already formatted)

        Returns:
            Number of traces successfully saved
        """
        if not self.client:
            return 0

        try:
            result = self.client.table("agent_traces").insert(traces).execute()
            count = len(result.data) if result.data else 0
            logger.info(f"Batch saved {count} traces")
            return count
        except Exception as e:
            logger.error(f"Failed to save batch traces: {e}")
            return 0

    def get_user_traces(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get traces for a specific user.

        Args:
            user_id: User identifier
            limit: Maximum number of traces to return
            offset: Pagination offset
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)

        Returns:
            List of trace dictionaries
        """
        if not self.client:
            return []

        try:
            query = self.client.table("agent_traces").select("*").eq("user_id", user_id)

            if start_date:
                query = query.gte("timestamp", start_date.isoformat())
            if end_date:
                query = query.lte("timestamp", end_date.isoformat())

            result = query.order("timestamp", desc=True).range(offset, offset + limit - 1).execute()

            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to get user traces: {e}")
            return []

    def get_traces_by_route(
        self,
        route: str,
        limit: int = 10,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get traces by routing decision.

        Args:
            route: Route type (A_direct_sme, B_sme_enrich, C_research, D_clarification)
            limit: Maximum number of traces
            days: Look back N days

        Returns:
            List of trace dictionaries
        """
        if not self.client:
            return []

        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            result = (
                self.client.table("agent_traces")
                .select("*")
                .eq("route", route)
                .gte("timestamp", start_date.isoformat())
                .order("timestamp", desc=True)
                .limit(limit)
                .execute()
            )

            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to get traces by route: {e}")
            return []

    def get_traces_by_agent(
        self,
        agent_id: str,
        limit: int = 10,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get traces by agent.

        Args:
            agent_id: Agent identifier (siemens_agent, rockwell_agent, etc.)
            limit: Maximum number of traces
            days: Look back N days

        Returns:
            List of trace dictionaries
        """
        if not self.client:
            return []

        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            result = (
                self.client.table("agent_traces")
                .select("*")
                .eq("agent_id", agent_id)
                .gte("timestamp", start_date.isoformat())
                .order("timestamp", desc=True)
                .limit(limit)
                .execute()
            )

            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to get traces by agent: {e}")
            return []

    def get_error_traces(
        self,
        limit: int = 10,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get traces with errors for debugging.

        Args:
            limit: Maximum number of traces
            days: Look back N days

        Returns:
            List of error trace dictionaries
        """
        if not self.client:
            return []

        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            result = (
                self.client.table("agent_traces")
                .select("*")
                .not_.is_("error", "null")
                .gte("timestamp", start_date.isoformat())
                .order("timestamp", desc=True)
                .limit(limit)
                .execute()
            )

            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to get error traces: {e}")
            return []

    def get_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get analytics from the agent_traces_analytics view.

        Args:
            days: Look back N days (view is pre-filtered to 7 days)

        Returns:
            Analytics dictionary with aggregated stats
        """
        if not self.client:
            return {}

        try:
            result = self.client.table("agent_traces_analytics").select("*").execute()

            if not result.data:
                return {}

            # Aggregate stats
            total_requests = sum(row["request_count"] for row in result.data)
            total_cost = sum(row["total_cost_usd"] or 0 for row in result.data)
            total_errors = sum(row["error_count"] for row in result.data)

            return {
                "total_requests": total_requests,
                "total_cost_usd": round(total_cost, 4),
                "total_errors": total_errors,
                "by_agent": result.data,
                "period_days": days
            }
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {}

    def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get analytics for a specific user.

        Args:
            user_id: User identifier

        Returns:
            User analytics dictionary
        """
        if not self.client:
            return {}

        try:
            result = (
                self.client.table("user_request_analytics")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )

            if not result.data or len(result.data) == 0:
                return {}

            return result.data[0]
        except Exception as e:
            logger.error(f"Failed to get user analytics: {e}")
            return {}

    def get_slow_queries(
        self,
        threshold_ms: int = 5000,
        limit: int = 10,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get traces with slow processing times (> threshold).

        Args:
            threshold_ms: Minimum processing time in ms
            limit: Maximum number of traces
            days: Look back N days

        Returns:
            List of slow trace dictionaries
        """
        if not self.client:
            return []

        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            result = (
                self.client.table("agent_traces")
                .select("*")
                .gte("processing_time_ms", threshold_ms)
                .gte("timestamp", start_date.isoformat())
                .order("processing_time_ms", desc=True)
                .limit(limit)
                .execute()
            )

            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to get slow queries: {e}")
            return []

    def get_research_triggers(
        self,
        limit: int = 10,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get traces where research was triggered (Route C).

        Args:
            limit: Maximum number of traces
            days: Look back N days

        Returns:
            List of research trigger trace dictionaries
        """
        if not self.client:
            return []

        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            result = (
                self.client.table("agent_traces")
                .select("*")
                .eq("research_triggered", True)
                .gte("timestamp", start_date.isoformat())
                .order("timestamp", desc=True)
                .limit(limit)
                .execute()
            )

            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to get research triggers: {e}")
            return []

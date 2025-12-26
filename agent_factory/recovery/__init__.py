"""
Unified Automatic Recovery Framework for Agent Factory.

Consolidates all 7 recovery mechanisms into a single, easy-to-use interface:
1. HTTP Retry (exponential backoff with jitter)
2. Database Failover (4-tier: Neon → Supabase → Railway → Local)
3. LLM Fallback (capability-aware routing with cost optimization)
4. Error Tracking (14 categories with alerting)
5. Safety Monitor (circuit breaker for cost/time/failures)
6. Health Monitoring (multi-provider health checks)
7. Ingestion Monitoring (pipeline tracking)

Example:
    >>> from agent_factory.recovery import RecoveryCoordinator
    >>> recovery = RecoveryCoordinator()
    >>>
    >>> # HTTP retry (automatic)
    >>> @recovery.http_retry()
    >>> def fetch_data():
    >>>     return requests.get("https://api.example.com/data")
    >>>
    >>> # Database with failover (automatic)
    >>> atoms = recovery.db_query("SELECT * FROM knowledge_atoms LIMIT 10")
    >>>
    >>> # LLM with fallback (automatic)
    >>> response = recovery.llm_complete("Explain PLC programming")

For complete documentation, see: docs/recovery/README.md
"""

from .config import RecoveryConfig
from .coordinator import RecoveryCoordinator

__version__ = "1.0.0"
__all__ = ["RecoveryCoordinator", "RecoveryConfig"]

"""
Knowledge Base Observability Platform.

Provides real-time monitoring and visibility for the 7-stage ingestion pipeline.

Components:
- IngestionMonitor: Tracks pipeline metrics (stage timings, success/failure, quality)
- TelegramNotifier: Real-time Telegram notifications (VERBOSE or BATCH mode)
- MetricsAggregator: Hourly/daily rollups for trend analysis
- Dashboard: Web UI (Gradio) + Telegram commands (/stats, /kb_status, /ingestion_live)

Database Tables:
- ingestion_metrics_realtime: Per-source ingestion results
- ingestion_metrics_hourly: Hourly aggregations
- ingestion_metrics_daily: Daily rollups

See: docs/database/observability_migration.sql for schema
See: .claude/plans/memoized-hugging-ullman.md for implementation plan
"""

from .ingestion_monitor import IngestionMonitor
from .telegram_notifier import TelegramNotifier

__all__ = ["IngestionMonitor", "TelegramNotifier"]

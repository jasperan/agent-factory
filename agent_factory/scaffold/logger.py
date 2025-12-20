"""
Structured logging for SCAFFOLD orchestrator sessions.

Logs all orchestrator actions to JSONL files for observability and debugging.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import logging


@dataclass
class LogEntry:
    """Single log entry with timestamp and event data."""
    timestamp: str
    event_type: str
    task_id: Optional[str]
    data: Dict[str, Any]

    def to_json(self) -> str:
        """Convert to JSON string for JSONL format."""
        return json.dumps(asdict(self), ensure_ascii=True)


@dataclass
class SessionSummary:
    """Summary statistics for a SCAFFOLD session."""
    session_id: str
    start_time: str
    end_time: str
    total_tasks: int
    successful: int
    failed: int
    total_cost: float
    elapsed_time: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for logging."""
        return asdict(self)


class ScaffoldLogger:
    """
    Structured logger for SCAFFOLD orchestrator sessions.

    Logs all events to JSONL files in logs/scaffold_sessions/{session_id}.jsonl
    Each log entry is a JSON object with timestamp, event_type, task_id, and data.
    """

    def __init__(self, session_id: str, log_dir: Optional[Path] = None):
        """
        Initialize logger for a session.

        Args:
            session_id: Unique session identifier
            log_dir: Directory for log files (default: logs/scaffold_sessions)
        """
        self.session_id = session_id
        self.log_dir = log_dir or Path("logs/scaffold_sessions")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.log_file = self.log_dir / f"{session_id}.jsonl"

        # Session tracking
        self.start_time = datetime.utcnow().isoformat()
        self.task_results: Dict[str, str] = {}  # task_id -> status (success/failure)
        self.task_costs: Dict[str, float] = {}  # task_id -> cost

        # Python logging for debugging
        self.logger = logging.getLogger(f"scaffold.{session_id}")

    def log_event(self, event_type: str, data: Dict[str, Any], task_id: Optional[str] = None):
        """
        Log an event to the JSONL file.

        Args:
            event_type: Type of event (session_start, task_start, task_success, task_failure, session_end)
            data: Event data dictionary
            task_id: Optional task ID for task-specific events
        """
        timestamp = datetime.utcnow().isoformat()
        entry = LogEntry(
            timestamp=timestamp,
            event_type=event_type,
            task_id=task_id,
            data=data
        )

        # Write to JSONL file (one JSON object per line)
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(entry.to_json() + "\n")

        # Also log to Python logger for debugging
        self.logger.info(f"[{event_type}] {task_id or 'session'}: {data}")

        # Track task results
        if event_type == "task_success":
            self.task_results[task_id] = "success"
            if "cost" in data:
                self.task_costs[task_id] = data["cost"]
        elif event_type == "task_failure":
            self.task_results[task_id] = "failure"

    def session_start(self, data: Optional[Dict[str, Any]] = None):
        """Log session start event."""
        self.log_event("session_start", data or {})

    def task_start(self, task_id: str, data: Optional[Dict[str, Any]] = None):
        """Log task start event."""
        self.log_event("task_start", data or {}, task_id=task_id)

    def task_success(self, task_id: str, cost: float = 0.0, data: Optional[Dict[str, Any]] = None):
        """Log task success event."""
        event_data = {"cost": cost}
        if data:
            event_data.update(data)
        self.log_event("task_success", event_data, task_id=task_id)

    def task_failure(self, task_id: str, error: str, data: Optional[Dict[str, Any]] = None):
        """Log task failure event."""
        event_data = {"error": error}
        if data:
            event_data.update(data)
        self.log_event("task_failure", event_data, task_id=task_id)

    def session_end(self, data: Optional[Dict[str, Any]] = None) -> SessionSummary:
        """
        Log session end event and return summary.

        Args:
            data: Optional additional data to log

        Returns:
            SessionSummary with statistics
        """
        end_time = datetime.utcnow().isoformat()

        # Calculate summary statistics
        total_tasks = len(self.task_results)
        successful = sum(1 for status in self.task_results.values() if status == "success")
        failed = sum(1 for status in self.task_results.values() if status == "failure")
        total_cost = sum(self.task_costs.values())

        # Calculate elapsed time
        start_dt = datetime.fromisoformat(self.start_time)
        end_dt = datetime.fromisoformat(end_time)
        elapsed_time = (end_dt - start_dt).total_seconds()

        summary = SessionSummary(
            session_id=self.session_id,
            start_time=self.start_time,
            end_time=end_time,
            total_tasks=total_tasks,
            successful=successful,
            failed=failed,
            total_cost=total_cost,
            elapsed_time=elapsed_time
        )

        # Log session end with summary
        event_data = summary.to_dict()
        if data:
            event_data.update(data)
        self.log_event("session_end", event_data)

        return summary

    def read_logs(self) -> List[LogEntry]:
        """
        Read all log entries from the JSONL file.

        Returns:
            List of LogEntry objects
        """
        if not self.log_file.exists():
            return []

        entries = []
        with self.log_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    entries.append(LogEntry(**data))

        return entries

    @staticmethod
    def get_session_summary(session_id: str, log_dir: Optional[Path] = None) -> Optional[SessionSummary]:
        """
        Get session summary from a completed session.

        Args:
            session_id: Session identifier
            log_dir: Directory for log files (default: logs/scaffold_sessions)

        Returns:
            SessionSummary if session_end event found, None otherwise
        """
        log_dir = log_dir or Path("logs/scaffold_sessions")
        log_file = log_dir / f"{session_id}.jsonl"

        if not log_file.exists():
            return None

        # Read last line (should be session_end)
        with log_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        if not lines:
            return None

        # Find session_end event
        for line in reversed(lines):
            line = line.strip()
            if line:
                data = json.loads(line)
                if data.get("event_type") == "session_end":
                    summary_data = data["data"]
                    return SessionSummary(**summary_data)

        return None

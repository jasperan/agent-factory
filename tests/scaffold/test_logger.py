"""
Tests for SCAFFOLD Logger.

Comprehensive test suite covering all logging functionality.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from agent_factory.scaffold.logger import (
    ScaffoldLogger,
    LogEntry,
    SessionSummary
)


@pytest.fixture
def temp_log_dir(tmp_path):
    """Temporary directory for log files."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir


@pytest.fixture
def logger(temp_log_dir):
    """ScaffoldLogger instance with temporary directory."""
    return ScaffoldLogger(session_id="test-session-001", log_dir=temp_log_dir)


class TestLogEntry:
    """Test LogEntry dataclass."""

    def test_log_entry_creation(self):
        """Test creating a log entry."""
        entry = LogEntry(
            timestamp="2025-12-20T06:00:00",
            event_type="task_start",
            task_id="task-1",
            data={"description": "Test task"}
        )

        assert entry.timestamp == "2025-12-20T06:00:00"
        assert entry.event_type == "task_start"
        assert entry.task_id == "task-1"
        assert entry.data == {"description": "Test task"}

    def test_log_entry_to_json(self):
        """Test converting log entry to JSON."""
        entry = LogEntry(
            timestamp="2025-12-20T06:00:00",
            event_type="task_success",
            task_id="task-1",
            data={"cost": 0.05}
        )

        json_str = entry.to_json()
        parsed = json.loads(json_str)

        assert parsed["timestamp"] == "2025-12-20T06:00:00"
        assert parsed["event_type"] == "task_success"
        assert parsed["task_id"] == "task-1"
        assert parsed["data"]["cost"] == 0.05

    def test_log_entry_no_task_id(self):
        """Test log entry without task ID (session events)."""
        entry = LogEntry(
            timestamp="2025-12-20T06:00:00",
            event_type="session_start",
            task_id=None,
            data={"max_tasks": 10}
        )

        json_str = entry.to_json()
        parsed = json.loads(json_str)

        assert parsed["task_id"] is None
        assert parsed["event_type"] == "session_start"


class TestSessionSummary:
    """Test SessionSummary dataclass."""

    def test_session_summary_creation(self):
        """Test creating a session summary."""
        summary = SessionSummary(
            session_id="test-session-001",
            start_time="2025-12-20T06:00:00",
            end_time="2025-12-20T07:00:00",
            total_tasks=5,
            successful=4,
            failed=1,
            total_cost=0.25,
            elapsed_time=3600.0
        )

        assert summary.session_id == "test-session-001"
        assert summary.total_tasks == 5
        assert summary.successful == 4
        assert summary.failed == 1
        assert summary.total_cost == 0.25
        assert summary.elapsed_time == 3600.0

    def test_session_summary_to_dict(self):
        """Test converting summary to dict."""
        summary = SessionSummary(
            session_id="test-session-001",
            start_time="2025-12-20T06:00:00",
            end_time="2025-12-20T07:00:00",
            total_tasks=3,
            successful=3,
            failed=0,
            total_cost=0.15,
            elapsed_time=1800.0
        )

        data = summary.to_dict()

        assert isinstance(data, dict)
        assert data["session_id"] == "test-session-001"
        assert data["total_tasks"] == 3
        assert data["successful"] == 3


class TestScaffoldLoggerInitialization:
    """Test logger initialization."""

    def test_logger_initialization(self, temp_log_dir):
        """Test creating a logger instance."""
        logger = ScaffoldLogger(session_id="session-001", log_dir=temp_log_dir)

        assert logger.session_id == "session-001"
        assert logger.log_dir == temp_log_dir
        assert logger.log_file == temp_log_dir / "session-001.jsonl"
        assert logger.task_results == {}
        assert logger.task_costs == {}

    def test_logger_creates_log_directory(self, tmp_path):
        """Test logger creates log directory if it doesn't exist."""
        log_dir = tmp_path / "logs" / "nested" / "scaffold_sessions"
        assert not log_dir.exists()

        logger = ScaffoldLogger(session_id="session-002", log_dir=log_dir)

        assert log_dir.exists()
        assert logger.log_file.parent == log_dir

    def test_logger_default_log_dir(self, tmp_path, monkeypatch):
        """Test logger uses default log directory."""
        monkeypatch.chdir(tmp_path)
        logger = ScaffoldLogger(session_id="session-003")

        expected_dir = Path("logs/scaffold_sessions")
        assert logger.log_dir == expected_dir
        assert logger.log_file == expected_dir / "session-003.jsonl"


class TestLoggingEvents:
    """Test logging individual events."""

    def test_log_event_basic(self, logger):
        """Test logging a basic event."""
        logger.log_event("session_start", {"max_tasks": 10})

        # Read log file
        logs = logger.read_logs()
        assert len(logs) == 1
        assert logs[0].event_type == "session_start"
        assert logs[0].data["max_tasks"] == 10

    def test_log_event_with_task_id(self, logger):
        """Test logging event with task ID."""
        logger.log_event("task_start", {"title": "Test task"}, task_id="task-1")

        logs = logger.read_logs()
        assert len(logs) == 1
        assert logs[0].event_type == "task_start"
        assert logs[0].task_id == "task-1"
        assert logs[0].data["title"] == "Test task"

    def test_log_event_multiple(self, logger):
        """Test logging multiple events."""
        logger.log_event("session_start", {})
        logger.log_event("task_start", {"title": "Task 1"}, task_id="task-1")
        logger.log_event("task_success", {"cost": 0.05}, task_id="task-1")

        logs = logger.read_logs()
        assert len(logs) == 3
        assert logs[0].event_type == "session_start"
        assert logs[1].event_type == "task_start"
        assert logs[2].event_type == "task_success"


class TestEventHelpers:
    """Test helper methods for common events."""

    def test_session_start(self, logger):
        """Test session_start helper."""
        logger.session_start({"max_tasks": 5})

        logs = logger.read_logs()
        assert len(logs) == 1
        assert logs[0].event_type == "session_start"
        assert logs[0].data["max_tasks"] == 5

    def test_task_start(self, logger):
        """Test task_start helper."""
        logger.task_start("task-1", {"title": "Test task"})

        logs = logger.read_logs()
        assert len(logs) == 1
        assert logs[0].event_type == "task_start"
        assert logs[0].task_id == "task-1"
        assert logs[0].data["title"] == "Test task"

    def test_task_success(self, logger):
        """Test task_success helper."""
        logger.task_success("task-1", cost=0.05, data={"duration": 120})

        logs = logger.read_logs()
        assert len(logs) == 1
        assert logs[0].event_type == "task_success"
        assert logs[0].task_id == "task-1"
        assert logs[0].data["cost"] == 0.05
        assert logs[0].data["duration"] == 120

        # Verify tracking
        assert logger.task_results["task-1"] == "success"
        assert logger.task_costs["task-1"] == 0.05

    def test_task_failure(self, logger):
        """Test task_failure helper."""
        logger.task_failure("task-1", error="Import failed", data={"exit_code": 1})

        logs = logger.read_logs()
        assert len(logs) == 1
        assert logs[0].event_type == "task_failure"
        assert logs[0].task_id == "task-1"
        assert logs[0].data["error"] == "Import failed"
        assert logs[0].data["exit_code"] == 1

        # Verify tracking
        assert logger.task_results["task-1"] == "failure"


class TestSessionSummaryGeneration:
    """Test session summary generation."""

    def test_session_end_summary(self, logger):
        """Test session_end generates correct summary."""
        logger.session_start()
        logger.task_start("task-1")
        logger.task_success("task-1", cost=0.05)
        logger.task_start("task-2")
        logger.task_success("task-2", cost=0.03)
        logger.task_start("task-3")
        logger.task_failure("task-3", error="Failed")

        summary = logger.session_end()

        assert summary.session_id == logger.session_id
        assert summary.total_tasks == 3
        assert summary.successful == 2
        assert summary.failed == 1
        assert summary.total_cost == 0.08

    def test_session_end_empty(self, logger):
        """Test session_end with no tasks."""
        logger.session_start()
        summary = logger.session_end()

        assert summary.total_tasks == 0
        assert summary.successful == 0
        assert summary.failed == 0
        assert summary.total_cost == 0.0

    def test_session_end_logs_summary(self, logger):
        """Test session_end writes summary to log."""
        logger.session_start()
        logger.task_success("task-1", cost=0.10)
        summary = logger.session_end()

        logs = logger.read_logs()
        session_end_log = logs[-1]

        assert session_end_log.event_type == "session_end"
        assert session_end_log.data["total_tasks"] == 1
        assert session_end_log.data["successful"] == 1
        assert session_end_log.data["total_cost"] == 0.10


class TestJSONLFormat:
    """Test JSONL file format compliance."""

    def test_jsonl_one_object_per_line(self, logger):
        """Test each log entry is on its own line."""
        logger.session_start()
        logger.task_start("task-1")
        logger.task_success("task-1", cost=0.05)

        # Read raw file
        with logger.log_file.open("r") as f:
            lines = f.readlines()

        assert len(lines) == 3
        for line in lines:
            # Each line should be valid JSON
            data = json.loads(line.strip())
            assert "timestamp" in data
            assert "event_type" in data

    def test_jsonl_valid_json_objects(self, logger):
        """Test all lines are valid JSON objects."""
        logger.session_start()
        logger.task_start("task-1")
        logger.task_success("task-1", cost=0.05)
        logger.session_end()

        with logger.log_file.open("r") as f:
            for line in f:
                line = line.strip()
                if line:
                    # Should not raise JSONDecodeError
                    data = json.loads(line)
                    assert isinstance(data, dict)


class TestReadLogs:
    """Test reading logs from JSONL file."""

    def test_read_logs_empty_file(self, logger):
        """Test reading logs from empty file."""
        logs = logger.read_logs()
        assert logs == []

    def test_read_logs_multiple_entries(self, logger):
        """Test reading multiple log entries."""
        logger.session_start()
        logger.task_start("task-1")
        logger.task_success("task-1", cost=0.05)
        logger.task_start("task-2")
        logger.task_failure("task-2", error="Failed")
        logger.session_end()

        logs = logger.read_logs()
        assert len(logs) == 6

        event_types = [log.event_type for log in logs]
        assert event_types == [
            "session_start",
            "task_start",
            "task_success",
            "task_start",
            "task_failure",
            "session_end"
        ]


class TestGetSessionSummary:
    """Test static method to retrieve session summary."""

    def test_get_session_summary(self, temp_log_dir):
        """Test retrieving session summary from completed session."""
        logger = ScaffoldLogger(session_id="session-001", log_dir=temp_log_dir)
        logger.session_start()
        logger.task_success("task-1", cost=0.05)
        logger.task_success("task-2", cost=0.03)
        logger.session_end()

        # Retrieve summary
        summary = ScaffoldLogger.get_session_summary("session-001", log_dir=temp_log_dir)

        assert summary is not None
        assert summary.session_id == "session-001"
        assert summary.total_tasks == 2
        assert summary.successful == 2
        assert summary.total_cost == 0.08

    def test_get_session_summary_no_file(self, temp_log_dir):
        """Test retrieving summary when log file doesn't exist."""
        summary = ScaffoldLogger.get_session_summary("nonexistent", log_dir=temp_log_dir)
        assert summary is None

    def test_get_session_summary_no_session_end(self, temp_log_dir):
        """Test retrieving summary when session_end event not found."""
        logger = ScaffoldLogger(session_id="incomplete", log_dir=temp_log_dir)
        logger.session_start()
        logger.task_start("task-1")
        # No session_end

        summary = ScaffoldLogger.get_session_summary("incomplete", log_dir=temp_log_dir)
        assert summary is None


class TestIntegration:
    """Integration tests for full session workflow."""

    def test_full_session_workflow(self, temp_log_dir):
        """Test complete session from start to end."""
        logger = ScaffoldLogger(session_id="full-session", log_dir=temp_log_dir)

        # Start session
        logger.session_start({"max_tasks": 5, "max_cost": 1.0})

        # Execute tasks
        logger.task_start("task-1", {"title": "First task"})
        logger.task_success("task-1", cost=0.10, data={"duration": 60})

        logger.task_start("task-2", {"title": "Second task"})
        logger.task_success("task-2", cost=0.08, data={"duration": 45})

        logger.task_start("task-3", {"title": "Third task"})
        logger.task_failure("task-3", error="Dependency missing", data={"exit_code": 1})

        # End session
        summary = logger.session_end({"reason": "max_tasks_reached"})

        # Verify summary
        assert summary.total_tasks == 3
        assert summary.successful == 2
        assert summary.failed == 1
        assert summary.total_cost == 0.18

        # Verify log file
        logs = logger.read_logs()
        # session_start + 3*(task_start+result) + session_end
        # Note: task_success/failure also trigger log_event, so we get 8 total
        assert len(logs) == 8

        # Verify session_end includes summary
        session_end_log = logs[-1]
        assert session_end_log.event_type == "session_end"
        assert session_end_log.data["total_tasks"] == 3
        assert session_end_log.data["reason"] == "max_tasks_reached"

    def test_multiple_sessions_same_directory(self, temp_log_dir):
        """Test multiple sessions in same directory."""
        logger1 = ScaffoldLogger(session_id="session-001", log_dir=temp_log_dir)
        logger1.session_start()
        logger1.task_success("task-1", cost=0.05)
        logger1.session_end()

        logger2 = ScaffoldLogger(session_id="session-002", log_dir=temp_log_dir)
        logger2.session_start()
        logger2.task_success("task-1", cost=0.10)
        logger2.task_success("task-2", cost=0.15)
        logger2.session_end()

        # Verify separate log files
        assert (temp_log_dir / "session-001.jsonl").exists()
        assert (temp_log_dir / "session-002.jsonl").exists()

        # Verify summaries
        summary1 = ScaffoldLogger.get_session_summary("session-001", log_dir=temp_log_dir)
        summary2 = ScaffoldLogger.get_session_summary("session-002", log_dir=temp_log_dir)

        assert summary1.total_tasks == 1
        assert summary2.total_tasks == 2
        assert summary1.total_cost == 0.05
        assert summary2.total_cost == 0.25

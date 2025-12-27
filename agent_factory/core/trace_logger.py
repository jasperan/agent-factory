"""
Production-grade tracing with file logging + admin message output.

Provides RequestTrace class for tracking full request lifecycle:
- JSONL file logging (traces.jsonl, errors.jsonl)
- Admin Telegram messages with formatted trace
- Timing tracking for performance monitoring
- Error isolation for quick triage
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from logging.handlers import RotatingFileHandler
import uuid
import time
import os
import sys

# Paths - environment-aware (VPS uses /root/Agent-Factory, local uses project root)
if os.name == 'posix' and Path("/root/Agent-Factory").exists():
    # VPS production environment
    LOG_DIR = Path("/root/Agent-Factory/logs")
else:
    # Local development (Windows or other)
    # Find project root (where pyproject.toml is located)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent  # Go up to Agent Factory root
    LOG_DIR = project_root / "logs"

TRACE_FILE = LOG_DIR / "traces.jsonl"
ERROR_FILE = LOG_DIR / "errors.jsonl"
METRICS_FILE = LOG_DIR / "metrics.jsonl"

LOG_DIR.mkdir(exist_ok=True, parents=True)

# Rotating file handlers (10MB max, 5 backups)
trace_handler = RotatingFileHandler(TRACE_FILE, maxBytes=10_000_000, backupCount=5)
error_handler = RotatingFileHandler(ERROR_FILE, maxBytes=10_000_000, backupCount=5)


class RequestTrace:
    """Context manager for tracing a full request lifecycle."""

    def __init__(self, message_type: str, user_id: str, username: str = None, content: str = ""):
        self.request_id = str(uuid.uuid4())[:8]
        self.trace_id = self.request_id  # Alias for compatibility
        self.message_type = message_type
        self.user_id = user_id
        self.username = username
        self.content = content[:500]  # Truncate to 500 chars
        self.start_time = time.time()
        self.events = []
        self.timings = {}

        # Enhanced trace data (Phase 5.5 - Dec 2025)
        self.decisions = []  # Routing decision points
        self.agent_reasoning_data = None  # Agent thought process
        self.research_pipeline_data = None  # Research pipeline status
        self.langgraph_trace_data = None  # LangGraph workflow execution
        self.kb_retrieval_data = None  # KB atom retrieval details

    def event(self, event_type: str, **data):
        """Log an event in this request's lifecycle."""
        elapsed_ms = int((time.time() - self.start_time) * 1000)
        entry = {
            "request_id": self.request_id,
            "elapsed_ms": elapsed_ms,
            "event": event_type,
            **data
        }
        self.events.append(entry)
        self._write_log(entry)

    def timing(self, step: str, ms: int):
        """Record timing for a step."""
        self.timings[step] = ms

    def error(self, error_type: str, message: str, location: str):
        """Log an error."""
        entry = {
            "request_id": self.request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_type": error_type,
            "message": message,
            "location": location,
            "user_id": self.user_id,
            "content": self.content
        }
        self._write_error(entry)
        self.events.append({"event": "ERROR", **entry})

    def _write_log(self, entry: dict):
        """Write trace log entry to JSONL file."""
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(TRACE_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _write_error(self, entry: dict):
        """Write error log entry to JSONL file."""
        with open(ERROR_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def decision(self, decision_point: str, outcome: str, reasoning: str,
                 alternatives: dict = None, confidence: float = None, **extra_data):
        """
        Capture a routing decision point with alternatives considered.

        Args:
            decision_point: Name of decision (e.g., "kb_coverage_evaluation")
            outcome: Selected outcome (e.g., "route_a")
            reasoning: Why this outcome was chosen
            alternatives: Dict of alternative outcomes with reasons
            confidence: Decision confidence score (0.0-1.0)
            **extra_data: Additional data (kb_atoms_found, top_atom_scores, etc.)
        """
        decision = {
            "decision_point": decision_point,
            "outcome": outcome,
            "reasoning": reasoning,
            "alternatives": alternatives or {},
            "confidence": confidence,
            **extra_data
        }
        self.decisions.append(decision)
        self.event(f"DECISION_{decision_point.upper()}", **decision)

    def agent_reasoning(self, agent: str, query: str, kb_atoms_used: list,
                       kb_retrieval_scores: list = None, reasoning_steps: list = None,
                       confidence: float = None, **extra_data):
        """
        Capture agent's internal reasoning process.

        Args:
            agent: Agent name (e.g., "SiemensAgent")
            query: User query being processed
            kb_atoms_used: List of atom IDs used
            kb_retrieval_scores: List of (atom_id, score) tuples
            reasoning_steps: List of reasoning step descriptions
            confidence: Agent's confidence in response
            **extra_data: Additional agent-specific data
        """
        self.agent_reasoning_data = {
            "agent": agent,
            "query": query,
            "kb_atoms_used": kb_atoms_used,
            "kb_retrieval_scores": kb_retrieval_scores or [],
            "reasoning_steps": reasoning_steps or [],
            "confidence": confidence,
            **extra_data
        }
        self.event("AGENT_REASONING", agent=agent, atoms_used=len(kb_atoms_used))

    def research_pipeline_status(self, triggered: bool, sources_found: list = None,
                                 sources_queued: int = 0, estimated_completion: str = "N/A",
                                 **extra_data):
        """
        Capture research pipeline execution status.

        Args:
            triggered: Whether research pipeline was triggered
            sources_found: List of URLs discovered
            sources_queued: Number of sources queued for ingestion
            estimated_completion: Time estimate (e.g., "3-5 minutes")
            **extra_data: Additional pipeline data
        """
        self.research_pipeline_data = {
            "triggered": triggered,
            "sources_found": sources_found or [],
            "sources_queued": sources_queued,
            "estimated_completion": estimated_completion,
            **extra_data
        }
        self.event("RESEARCH_PIPELINE", triggered=triggered, sources=sources_queued)

    def langgraph_execution(self, workflow_trace: dict):
        """
        Capture LangGraph workflow execution trace.

        Args:
            workflow_trace: Dict with workflow, nodes_executed, state_transitions,
                          retry_count, quality_gate_results, total_duration_ms
        """
        self.langgraph_trace_data = workflow_trace
        self.event("LANGGRAPH_WORKFLOW",
                  workflow=workflow_trace.get("workflow"),
                  nodes=len(workflow_trace.get("nodes_executed", [])),
                  duration_ms=workflow_trace.get("total_duration_ms"))

    def kb_retrieval(self, coverage: float, atoms_found: int, top_matches: list):
        """
        Capture KB atom retrieval details.

        Args:
            coverage: KB coverage score (0.0-1.0)
            atoms_found: Total number of atoms found
            top_matches: List of (atom_id, score) tuples for top matches
        """
        self.kb_retrieval_data = {
            "coverage": coverage,
            "atoms_found": atoms_found,
            "top_matches": top_matches
        }
        self.event("KB_RETRIEVAL", coverage=coverage, atoms=atoms_found)

    # Getter methods for trace data
    def get_decisions(self) -> list:
        """Get all decision points captured."""
        return self.decisions

    def get_agent_reasoning(self) -> dict:
        """Get agent reasoning data."""
        return self.agent_reasoning_data

    def get_research_pipeline_status(self) -> dict:
        """Get research pipeline status."""
        return self.research_pipeline_data or {}

    def get_langgraph_trace(self) -> dict:
        """Get LangGraph workflow trace."""
        return self.langgraph_trace_data

    def get_kb_retrieval_info(self) -> dict:
        """Get KB retrieval details."""
        return self.kb_retrieval_data

    def get_all_timings(self) -> dict:
        """Get all performance timings."""
        return self.timings

    def get_errors(self) -> list:
        """Get all errors logged in this trace."""
        return [e for e in self.events if e.get("event") == "ERROR"]

    @property
    def total_duration_ms(self) -> int:
        """Get total duration in milliseconds."""
        return int((time.time() - self.start_time) * 1000)

    def summary(self) -> dict:
        """Return summary for admin message."""
        total_ms = int((time.time() - self.start_time) * 1000)
        return {
            "request_id": self.request_id,
            "message_type": self.message_type,
            "user_id": self.user_id,
            "total_ms": total_ms,
            "timings": self.timings,
            "events": [e["event"] for e in self.events]
        }

    def format_admin_message(
        self,
        route: str,
        confidence: float,
        kb_atoms: int,
        llm_model: str = None,
        ocr_result: dict = None,
        kb_coverage: str = "none",
        error: str = None
    ) -> str:
        """Format the second message for admin."""
        total_ms = int((time.time() - self.start_time) * 1000)

        lines = ["```"]
        lines.append(f"TRACE [{self.request_id}]")
        lines.append("=" * 30)

        # Input section
        if self.message_type == "photo" and ocr_result:
            lines.append("PHOTO OCR")
            lines.append(f"  Manufacturer: {ocr_result.get('manufacturer', 'N/A')}")
            lines.append(f"  Model: {ocr_result.get('model', 'N/A')}")
            lines.append(f"  Fault Code: {ocr_result.get('fault_code', 'N/A')}")
            lines.append("")

        # Routing section
        lines.append("ROUTING")
        lines.append(f"  Route: {route}")
        lines.append(f"  Confidence: {confidence:.0%}")
        lines.append(f"  KB Coverage: {kb_coverage}")
        lines.append(f"  KB Atoms: {kb_atoms}")
        lines.append("")

        # LLM section
        if llm_model:
            lines.append("LLM")
            lines.append(f"  Model: {llm_model}")
            lines.append(f"  Cost: ${self.timings.get('llm_cost', 0):.4f}")
            lines.append("")

        # Timing section
        lines.append("TIMING")
        for step, ms in self.timings.items():
            if step != "llm_cost":
                lines.append(f"  {step}: {ms}ms")
        lines.append(f"  TOTAL: {total_ms}ms")
        lines.append("")

        # Error section
        if error:
            lines.append("ERROR")
            lines.append(f"  {error}")
            lines.append("")

        # Footer
        lines.append("=" * 30)
        lines.append(f"User: {self.user_id}")
        lines.append(f"Time: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}")
        lines.append("```")

        return "\n".join(lines)

from datetime import datetime
from enum import Enum
from typing import Optional, List, Any
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Text, Boolean
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import relationship
import uuid
import json

from agent_factory.core.database import Base

class PydanticEnum(TypeDecorator):
    """
    Enables passing in a Pydantic Enum and storing it as a string in the db
    """
    impl = String

    def __init__(self, enumtype, *args, **kwargs):
        super(PydanticEnum, self).__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, dialect):
        if isinstance(value, self._enumtype):
            return value.value
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return self._enumtype(value)
        return value

# ============================================================================
# Enums
# ============================================================================

class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskComplexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"

class AgentType(str, Enum):
    PLANNER = "planner"
    WORKER = "worker"
    JUDGE = "judge"

class AgentStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    ERROR = "error"
    STOPPED = "stopped"

# ============================================================================
# Models
# ============================================================================

class Task(Base):
    """
    Represents a unit of work (code change) to be performed.
    """
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(PydanticEnum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(Integer, default=5) # 1-10
    complexity = Column(PydanticEnum(TaskComplexity), default=TaskComplexity.UNKNOWN)
    
    # Assignments
    created_by_id = Column(String, ForeignKey("agents.id"), nullable=True)
    assigned_to_id = Column(String, ForeignKey("agents.id"), nullable=True)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)
    
    # Git integration
    git_branch = Column(String, nullable=True)
    git_commit_hash = Column(String, nullable=True)
    
    # Details
    affected_files = Column(JSON, default=list) # List[str]
    acceptance_criteria = Column(JSON, default=list) # List[str]
    
    # Execution results
    test_output = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relations
    creator = relationship("Agent", foreign_keys=[created_by_id], backref="created_tasks")
    assignee = relationship("Agent", foreign_keys=[assigned_to_id], backref="assigned_tasks")


class Agent(Base):
    """
    Represents an autonomous agent (planner, worker, judge).
    """
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)
    role = Column(PydanticEnum(AgentType), nullable=False)
    status = Column(PydanticEnum(AgentStatus), default=AgentStatus.IDLE)
    model_name = Column(String, default="gpt-4o") # Or local model name
    
    # Metrics
    tasks_completed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    
    # Current state
    current_task_id = Column(String, ForeignKey("tasks.id"), nullable=True)


class Cycle(Base):
    """
    Represents a full development cycle (Plan -> Work -> Judge).
    """
    __tablename__ = "cycles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    status = Column(String, default="running") # running, completed, paused
    
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    
    judge_decision = Column(String, nullable=True) # continue, pause, halt
    judge_notes = Column(Text, nullable=True)
    metrics = Column(JSON, default=dict)


import time
import logging
import uuid
import json
from datetime import datetime
from agent_factory.agents.base import BaseAgent
from agent_factory.core.models import AgentType, Task, TaskStatus, TaskComplexity, AgentStatus, Cycle
from agent_factory.core.database import SessionLocal

logger = logging.getLogger(__name__)

class PlannerAgent(BaseAgent):
    def __init__(self, agent_name: str):
        super().__init__(agent_name, AgentType.PLANNER)
        self.planning_interval = 60 # Seconds between checks if a plan is needed

    def step(self):
        """
        Check if we need to plan.
        We plan if:
        1. There is an active cycle.
        2. The cycle has no pending tasks (or we want to replenish).
        """
        session = SessionLocal()
        try:
            # 1. Find active cycle
            cycle = session.query(Cycle).filter(Cycle.status == "running").first()
            if not cycle:
                # No active cycle, can't plan
                self._update_status(AgentStatus.IDLE)
                time.sleep(5)
                return

            # 2. Check if we need tasks
            # For simplicity, if total_tasks == 0 in this cycle, we plan.
            # Or if all tasks are completed.
            pending_count = session.query(Task).filter(Task.status == TaskStatus.PENDING).count()
            
            if pending_count > 0:
                # Tasks exist, no need to plan yet
                self._update_status(AgentStatus.IDLE)
                time.sleep(5)
                return

            # 3. Create Plan
            self._update_status(AgentStatus.WORKING)
            logger.info(f"Planner {self.agent_name} starting planning phase for Cycle {cycle.id}")
            
            # TODO: Real LLM Planning integration
            # For now, generate a couple of sample tasks to simulate activity
            new_tasks = self._generate_sample_tasks()
            
            for task_data in new_tasks:
                task = Task(
                    title=task_data["title"],
                    description=task_data["description"],
                    priority=task_data["priority"],
                    complexity=TaskComplexity(task_data["complexity"]),
                    created_by_id=self.agent_id,
                    affected_files=task_data.get("affected_files", []),
                    acceptance_criteria=task_data.get("acceptance_criteria", [])
                )
                session.add(task)
                cycle.total_tasks += 1
            
            session.commit()
            logger.info(f"Planner {self.agent_name} created {len(new_tasks)} tasks.")
            
        except Exception as e:
            logger.error(f"Planner step failed: {e}")
            session.rollback()
        finally:
            session.close()
            
    def _generate_sample_tasks(self):
        """Mock task generation for autonomous demo loop"""
        # In a real impl, this would read the codebase and prompt an LLM
        return [
            {
                "title": f"Refactor module {uuid.uuid4().hex[:4]}",
                "description": "Improve error handling and add type hints.",
                "priority": 5,
                "complexity": "low",
                "affected_files": ["src/module_a.py"],
                "acceptance_criteria": ["All functions have type hints", "Exceptions are caught"]
            },
            {
                "title": f"Optimize query {uuid.uuid4().hex[:4]}",
                "description": "Reduce N+1 query problem in users endpoint.",
                "priority": 8,
                "complexity": "medium",
                "affected_files": ["src/api/users.py"],
                "acceptance_criteria": ["Query count reduced to 1"]
            }
        ]

import time
import logging
from agent_factory.agents.base import BaseAgent
from agent_factory.core.models import AgentType, Task, TaskStatus, AgentStatus, Cycle
from agent_factory.core.database import SessionLocal

logger = logging.getLogger(__name__)

class JudgeAgent(BaseAgent):
    def __init__(self, agent_name: str):
        super().__init__(agent_name, AgentType.JUDGE)
        self.check_interval = 30
    
    def step(self):
        """
        Monitor the cycle.
        If all tasks are completed/failed, finalize the cycle or trigger next actions.
        """
        session = SessionLocal()
        try:
            cycle = session.query(Cycle).filter(Cycle.status == "running").first()
            if not cycle:
                self._update_status(AgentStatus.IDLE)
                time.sleep(5)
                return

            # Check tasks stats
            total = session.query(Task).count()
            completed = session.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
            failed = session.query(Task).filter(Task.status == TaskStatus.FAILED).count()
            pending = session.query(Task).filter(Task.status == TaskStatus.PENDING).count()
            assigned = session.query(Task).filter(Task.status == TaskStatus.ASSIGNED).count()

            # Update cycle metrics
            cycle.total_tasks = total
            cycle.completed_tasks = completed
            cycle.metrics = {
                "failed": failed,
                "pending": pending,
                "assigned": assigned,
                "pass_rate": completed / total if total > 0 else 0
            }
            session.commit()
            
            # If everything is done (no pending, no assigned), maybe close cycle or plan more?
            # For this continuous loop, let's keep the cycle open but maybe log "Cycle Stable"
            
            if pending == 0 and assigned == 0 and total > 0:
                # Loop implies continuous; Planner should have added more tasks if it saw 0 pending.
                # If Planner is slow, Judge just waits.
                self._update_status(AgentStatus.IDLE)
            else:
                 # working on monitoring
                self._update_status(AgentStatus.WORKING)
            
            time.sleep(5)

        except Exception as e:
            logger.error(f"Judge step failed: {e}")
            session.rollback()
        finally:
            session.close()

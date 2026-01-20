import time
import logging
import random
from datetime import datetime
from agent_factory.agents.base import BaseAgent
from agent_factory.core.models import AgentType, Task, TaskStatus, AgentStatus
from agent_factory.core.database import SessionLocal

logger = logging.getLogger(__name__)

class WorkerAgent(BaseAgent):
    def __init__(self, agent_name: str):
        super().__init__(agent_name, AgentType.WORKER)
    
    def step(self):
        """
        Check for pending tasks and execute them.
        """
        session = SessionLocal()
        try:
            # 1. Claim a task
            # Locking strategy: select first PENDING task, update it to ASSIGNED
            # This is a naive implementation; production would use SELECT FOR UPDATE
            task = session.query(Task).filter(Task.status == TaskStatus.PENDING).first()
            
            if not task:
                self._update_status(AgentStatus.IDLE)
                time.sleep(2)
                return
            
            # Claim it
            task.status = TaskStatus.ASSIGNED
            task.assigned_to_id = self.agent_id
            task.started_at = datetime.utcnow()
            session.commit()
            
            self._update_status(AgentStatus.WORKING, current_task_id=task.id)
            logger.info(f"Worker {self.agent_name} started task: {task.title}")
            
            # 2. Simulate Work
            # TODO: Real Code Transformation using Ollama
            work_duration = random.randint(5, 15) # Simulate code generation time
            time.sleep(work_duration)
            
            # 3. Complete Task
            # 90% success rate for simulation
            success = random.random() > 0.1
            
            if success:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                task.git_commit_hash = f"abc{random.randint(100,999)}"
                # Increment metrics
                agent = session.query(self.__class__).get(self.agent_id) # reload self to update metrics? No, use model
                # But self.agent_id refers to Agent model.
                # Just update counts directly via query to avoid detach issues
                # Logic handled in BaseAgent? No, specific here.
            else:
                task.status = TaskStatus.FAILED
                task.error_message = "Simulated compilation error"
                task.completed_at = datetime.utcnow()
            
            session.commit()
            logger.info(f"Worker {self.agent_name} finished task {task.title} with status {task.status.value}")
            
        except Exception as e:
            logger.error(f"Worker step failed: {e}")
            session.rollback()
        finally:
            session.close()

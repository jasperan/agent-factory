import time
import logging
import threading
import traceback
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from agent_factory.core.database import SessionLocal
from agent_factory.core.models import Agent, AgentStatus, AgentType

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Base class for all autonomous agents.
    Handles the main run loop, database connection, and status reporting.
    """
    
    def __init__(self, agent_name: str, agent_type: AgentType, model_name: str = "gpt-4o"):
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.model_name = model_name
        
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.agent_id: Optional[str] = None
        
        # Initialize agent record in DB
        self._register_agent()
        
    def _register_agent(self):
        """Ensure agent exists in the database"""
        session = SessionLocal()
        try:
            agent = session.query(Agent).filter(Agent.name == self.agent_name).first()
            if not agent:
                agent = Agent(
                    name=self.agent_name,
                    role=self.agent_type,
                    model_name=self.model_name,
                    status=AgentStatus.IDLE
                )
                session.add(agent)
                session.commit()
            
            self.agent_id = agent.id
            logger.info(f"Registered agent {self.agent_name} (ID: {self.agent_id})")
        
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to register agent {self.agent_name}: {e}")
            raise
        finally:
            session.close()

    def start(self):
        """Start the agent loop in a separate thread"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info(f"Agent {self.agent_name} started.")

    def stop(self):
        """Stop the agent loop"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
        self._update_status(AgentStatus.STOPPED)
        logger.info(f"Agent {self.agent_name} stopped.")

    def _run_loop(self):
        """Main execution loop"""
        while self.running:
            try:
                self._heartbeat()
                
                # Execute agent specific logic
                # Implementations should handle their own sleeping if idle
                self.step()
                
                # Small sleep to prevent tight loop if step returns immediately
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in agent {self.agent_name} loop: {e}")
                logger.error(traceback.format_exc())
                self._update_status(AgentStatus.ERROR)
                time.sleep(10) # Wait a bit before retrying

    def _heartbeat(self):
        """Update last_heartbeat timestamp"""
        session = SessionLocal()
        try:
            agent = session.query(Agent).get(self.agent_id)
            if agent:
                agent.last_heartbeat = datetime.utcnow()
                session.commit()
        except Exception as e:
            logger.error(f"Heartbeat failed for {self.agent_name}: {e}")
        finally:
            session.close()

    def _update_status(self, status: AgentStatus, current_task_id: Optional[str] = None):
        """Update agent status in DB"""
        session = SessionLocal()
        try:
            agent = session.query(Agent).get(self.agent_id)
            if agent:
                agent.status = status
                agent.current_task_id = current_task_id
                session.commit()
        except Exception as e:
            logger.error(f"Status update failed for {self.agent_name}: {e}")
        finally:
            session.close()

    @abstractmethod
    def step(self):
        """
        One cycle of the agent's logic.
        Should include:
        1. Check for work
        2. If work, do work (set status WORKING)
        3. If no work, sleep/wait (set status IDLE)
        """
        pass

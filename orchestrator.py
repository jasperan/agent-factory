#!/usr/bin/env python3
"""
Autonomous Agent Orchestrator
Runs the Planner -> Worker -> Judge loop 24/7.
"""

import time
import logging
import sys
import threading
from typing import List

from agent_factory.core.database import init_db, SessionLocal
from agent_factory.core.models import Cycle, AgentStatus
from agent_factory.agents.planner import PlannerAgent
from agent_factory.agents.worker import WorkerAgent
from agent_factory.agents.judge import JudgeAgent
from agent_factory.agents.base import BaseAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("orchestrator")

class Orchestrator:
    def __init__(self, num_workers=5):
        self.num_workers = num_workers
        self.agents: List[BaseAgent] = []
        self.running = False
        
        # Initialize DB
        logger.info("Initializing database...")
        init_db()
        self._ensure_cycle_exists()

    def _ensure_cycle_exists(self):
        """Make sure there's at least one active cycle"""
        session = SessionLocal()
        try:
            active_cycle = session.query(Cycle).filter(Cycle.status == "running").first()
            if not active_cycle:
                logger.info("No active cycle found. Creating new cycle.")
                new_cycle = Cycle(status="running")
                session.add(new_cycle)
                session.commit()
                logger.info(f"Created Cycle {new_cycle.id}")
        finally:
            session.close()

    def start(self):
        """Start all agents"""
        logger.info("Starting agents...")
        self.running = True
        
        # 1. Planner
        self.agents.append(PlannerAgent("Planner-Alpha"))
        
        # 2. Judge
        self.agents.append(JudgeAgent("Judge-Dredd"))
        
        # 3. Workers
        for i in range(self.num_workers):
            self.agents.append(WorkerAgent(f"Worker-{i+1}"))
            
        # Start threads
        for agent in self.agents:
            agent.start()
            
        logger.info(f"Orchestrator started with {len(self.agents)} agents.")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop all agents"""
        logger.info("Stopping agents...")
        self.running = False
        for agent in self.agents:
            agent.stop()
        logger.info("Orchestrator stopped.")

if __name__ == "__main__":
    orch = Orchestrator(num_workers=5)
    orch.start()

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime

from agent_factory.core.database import get_db, init_db
from agent_factory.core.models import Task, Agent, Cycle, TaskStatus, AgentStatus

app = FastAPI(title="AgentCommand API")

# Allow CORS for SvelteKit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def read_root():
    return {"status": "AgentCommand API Live"}

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Get global dashboard stats"""
    total_agents = db.query(Agent).count()
    active_agents = db.query(Agent).filter(Agent.status == AgentStatus.WORKING).count()
    
    # Revenue (Mocked for now as we don't track $ yet)
    revenue = 125967 
    
    # Deploys (Completed cycles? or Commit count?)
    deploys = db.query(Cycle).filter(Cycle.status == "completed").count() + 49 # Mock baseline
    
    # Lines changed (Mocked)
    lines_changed = 89478
    
    # Task Queue
    pending_tasks = db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
    
    return {
        "live_agents": total_agents,
        "running_agents": active_agents,
        "revenue": revenue,
        "deploys": deploys,
        "lines_changed": lines_changed,
        "tasks_in_queue": pending_tasks
    }

@app.get("/agents")
def get_agents(db: Session = Depends(get_db)):
    """List all agents and their status"""
    agents = db.query(Agent).all()
    return agents

@app.get("/tasks")
def get_tasks(limit: int = 50, db: Session = Depends(get_db)):
    """List recent tasks"""
    tasks = db.query(Task).order_by(Task.created_at.desc()).limit(limit).all()
    return tasks

@app.get("/pipelines")
def get_pipelines(db: Session = Depends(get_db)):
    """Get task pipeline status (Kanban)"""
    # Group tasks by status or return lists
    # Ideally, we want active initiatives. For now, just return running tasks.
    running_tasks = db.query(Task).filter(Task.status == TaskStatus.RUNNING).all()
    queued_tasks = db.query(Task).filter(Task.status == TaskStatus.PENDING).limit(5).all()
    completed_tasks = db.query(Task).filter(Task.status == TaskStatus.COMPLETED).order_by(Task.completed_at.desc()).limit(5).all()
    
    return {
        "running": running_tasks,
        "queued": queued_tasks,
        "completed": completed_tasks
    }

# Mock Logs endpoint
@app.get("/logs")
def get_logs():
    return [
        {"agent": "Planner-Alpha", "message": "Analyzing codebase...", "timestamp": datetime.now(), "level": "INFO"},
        {"agent": "Worker-1", "message": "Compiling module X...", "timestamp": datetime.now(), "level": "INFO"},
    ]

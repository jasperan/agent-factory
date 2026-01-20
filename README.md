# AgentCommand

**Autonomous Multi-Agent Development System**

AgentCommand is a closed-loop autonomous coding system where AI agents acting as Planners, Workers, and Judges continuously improve a codebase 24/7. It features a real-time SvelteKit dashboard to visualize the agent activity.

![AgentCommand Dashboard](https://i.imgur.com/example-dashboard.png)

## Overview

The system runs a continuous loop (`orchestrator.py`):
1.  **Planner Agent**: Analyzes the codebase and creates improvement tasks.
2.  **Worker Agent**: Claims tasks, writes code changes, and runs tests.
3.  **Judge Agent**: Validates the work and decides whether to continue the cycle.

All data is persisted in a local SQLite database (`agent_factory.db`).

## Quick Start

The easiest way to run the entire system (Orchestrator + API + Dashboard) is:

```bash
./start_all.sh
```

This will launch:
- **Orchestrator**: Background Python process running agent loops.
- **Backend API**: FastAPI server at `http://localhost:8000`.
- **Dashboard UI**: SvelteKit app at `http://localhost:3000`.

## Manual Setup

### 1. Backend (Orchestrator & API)

**Prerequisites:** Python 3.10+

```bash
# Install dependencies
pip install -r requirements.txt

# Run Orchestrator (Autonomous Agents)
python orchestrator.py

# Run API (in a separate terminal)
uvicorn dashboard_api.main:app --reload
```

### 2. Frontend (Dashboard)

**Prerequisites:** Node.js 18+

```bash
cd agent_command_ui
npm install
npm run dev
```

## System Architecture

- **`agent_factory/`**: Core logic for Agents and Database.
    - `agents/`: `PlannerAgent`, `WorkerAgent`, `JudgeAgent`.
    - `core/`: SQLAlchemy models (`Task`, `Agent`, `Cycle`).
- **`dashboard_api/`**: FastAPI implementation for the UI.
- **`agent_command_ui/`**: SvelteKit + Tailwind CSS frontend.
- **`orchestrator.py`**: The main entry point for the autonomous loop.

## configuration

Configuration is managed via environment variables (see `.env`) or defaults in `agent_factory/core/database.py`.

Default Database: `sqlite:///agent_factory.db`
DEFAULT Model: `gpt-4o` (configurable in `orchestrator.py`)

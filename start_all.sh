#!/bin/bash

# Trap Ctrl+C and kill all background processes
trap "kill 0" EXIT

echo "Starting AgentCommand System..."

# 1. Start Orchestrator (Autonomous Agents)
echo "Launching Orchestrator..."
python3 orchestrator.py > orchestrator.log 2>&1 &
ORCH_PID=$!
echo "Orchestrator running (PID: $ORCH_PID). Logs in orchestrator.log"

# 2. Start Dashboard API
echo "Launching Dashboard API..."
uvicorn dashboard_api.main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
API_PID=$!
echo "API running (PID: $API_PID). Logs in api.log"

# 3. Start Frontend
echo "Launching Frontend..."
cd agent_command_ui
# Use --host to expose to network if needed, though mostly local
npm run dev -- --host --port 3000 > ../frontend.log 2>&1 &
FRONT_PID=$!
echo "Frontend running (PID: $FRONT_PID). Logs in frontend.log"

echo "System fully operational!"
echo "Dashboard: http://localhost:3000"
echo "API: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop everything."

# Wait for processes
wait

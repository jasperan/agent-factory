
from agent_factory.workers.openhands_worker import OpenHandsWorker
import os

# Force Ollama mode
os.environ["USE_OLLAMA"] = "true"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"

print("Initializing worker with Ubuntu runtime...")
worker = OpenHandsWorker(model="deepseek-coder:6.7b")

print("Running task (this will take a while due to apt-get install)...")
# Simple task that requires python to be working
result = worker.run_task("Calculate 15 * 37 and print the result", timeout=600)

print(f"Success: {result.success}")
print(f"Message: {result.message}")
print("\n=== AGENT LOGS ===")
print(result.logs)
print("=== END AGENT LOGS ===\n")

if result.code:
    print(f"Code: {result.code}")

# Debug: Inspect sandbox container logs
import subprocess
print("\n=== SANDBOX CONTAINER DEBUG ===")
try:
    # List containers to find the runtime
    subprocess.run(["docker", "ps", "-a", "--filter", "name=openhands-runtime"], check=False)
    
    # Get logs of the latest runtime container
    cmd = "docker ps -a --filter name=openhands-runtime -q | head -n 1"
    container_id = subprocess.check_output(cmd, shell=True).decode().strip()
    if container_id:
        print(f"\nLogs for container {container_id}:")
        subprocess.run(["docker", "logs", container_id], check=False)
    else:
        print("No runtime container found.")
except Exception as e:
    print(f"Error inspecting sandbox: {e}")



import sys
import os
import time
import subprocess
from pathlib import Path

# Add parent dir to path so we can import agent_factory
sys.path.append(str(Path(__file__).parent.parent))

from agent_factory.workers.openhands_worker import OpenHandsWorker

def main():
    print("Initializing Worker...")
    worker = OpenHandsWorker(
        model="deepseek-coder:6.7b",
        use_ollama=True,
        port=3000
    )

    print("Running Task (cleanup=False)...")
    # Simple task to test runtime connectivity
    result = worker.run_task("print('hello world')", timeout=60, cleanup=False)

    print("\nXXX Result XXX")
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    print("Logs:")
    print(result.logs)
    
    print("\nXXX Inspecting Containers XXX")
    
    # 1. Main Worker Logs
    print(f"\n--- Logs for {worker.container_name} ---")
    try:
        # Use worker.container_engine (should be 'podman')
        subprocess.run([worker.container_engine, "logs", worker.container_name], check=False)
    except Exception as e:
        print(f"Failed to get main logs: {e}")

    # 2. Runtime Containers
    print("\n--- Searching for Runtime Containers ---")
    try:
        # List all containers (even exited) matching openhands-runtime
        ps_cmd = [worker.container_engine, "ps", "-a", "--filter", "name=openhands-runtime", "--format", "{{.ID}} {{.Names}} {{.Status}}"]
        output = subprocess.check_output(ps_cmd, text=True)
        print("Runtime Containers found:")
        print(output)
        
        for line in output.strip().splitlines():
            if not line: continue
            cid = line.split()[0]
            print(f"\n--- Logs for Runtime {cid} ---")
            subprocess.run([worker.container_engine, "logs", cid], check=False)
            
            # Inspect to see exit code and OCI error
            print(f"\n--- Inspect {cid} ---")
            subprocess.run([worker.container_engine, "inspect", cid], check=False)
            
    except Exception as e:
        print(f"Failed to inspect runtimes: {e}")

if __name__ == "__main__":
    main()

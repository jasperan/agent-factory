import os
from agent_factory.core.agent_factory import AgentFactory

# Initialize AgentFactory with Ollama settings
# Advanced logging can be triggered by VERBOSE=true environment variable
factory = AgentFactory(
    default_llm_provider="ollama",
    default_model="deepseek-coder:6.7b"
)

print("Creating OpenHands worker...")
worker = factory.create_openhands_agent()

print("Running coding task...")
# Run a specific task
result = worker.run_task("Create a directory named 'test_artifacts' and inside it create a file 'hello.txt' with the content 'Hello from OpenHands SDK!'")

if result.success:
    if result.code:
        print("\n--- Result Code ---")
        print(result.code)
    else:
        print("\n--- No Code Generated ---")
        print(f"Success: {result.success}")
        print(f"Message: {result.message}")
        print(f"Files Changed: {result.files_changed}")
        print("\n--- Full Logs ---")
        print(result.logs)
else:
    print("\n--- Task Failed ---")
    print(f"Error: {result.message}")
    print("\n--- Full Logs ---")
    print(result.logs)

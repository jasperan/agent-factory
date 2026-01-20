from agent_factory.core.agent_factory import AgentFactory

# Create factory with Ollama
factory = AgentFactory(
    default_llm_provider="ollama",
    default_model="deepseek-coder:6.7b"
)

# Create OpenHands worker
print("Creating OpenHands worker...")
worker = factory.create_openhands_agent()

# Run coding task (100% free!)
print("Running coding task...")
result = worker.run_task(
    "Write a Python function to validate email addresses using regex"
)

print("\n--- Result Code ---")
print(result.code)
# Output: Full working function with docstrings and tests

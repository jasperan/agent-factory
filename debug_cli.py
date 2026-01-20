print("Importing AgentFactory...")
try:
    from agent_factory.core.agent_factory import AgentFactory
    print("Import successful.")
except Exception as e:
    print(f"Import failed: {e}")
    exit(1)

print("Initializing AgentFactory...")
try:
    factory = AgentFactory(default_llm_provider="ollama")
    print("Initialization successful.")
except Exception as e:
    print(f"Initialization failed: {e}")
    exit(1)

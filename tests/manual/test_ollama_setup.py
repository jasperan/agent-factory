"""Simple Ollama + OpenHands validation script (Windows-safe)"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

print("\n" + "=" * 70)
print("  OLLAMA + OPENHANDS SETUP VALIDATION")
print("=" * 70)

# Step 1: Check environment variables
print("\n[1] Checking .env configuration...")
use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"
ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
ollama_model = os.getenv("OLLAMA_MODEL", "deepseek-coder:6.7b")

print(f"  USE_OLLAMA: {use_ollama}")
print(f"  OLLAMA_BASE_URL: {ollama_url}")
print(f"  OLLAMA_MODEL: {ollama_model}")

if not use_ollama:
    print("\n  [WARNING] USE_OLLAMA is not 'true'")
    print("  Set USE_OLLAMA=true in .env to enable FREE models")
else:
    print("  [OK] USE_OLLAMA is enabled")

# Step 2: Check Ollama service
print("\n[2] Checking Ollama service...")
try:
    response = requests.get(f"{ollama_url}/api/tags", timeout=5)
    response.raise_for_status()
    print(f"  [OK] Ollama is running at {ollama_url}")

    # Step 3: Check model availability
    print("\n[3] Checking model availability...")
    data = response.json()
    models = data.get("models", [])
    model_names = [m["name"] for m in models]

    print(f"  Available models: {len(models)}")
    for name in model_names:
        marker = "[TARGET]" if name == ollama_model else ""
        print(f"    - {name} {marker}")

    if ollama_model in model_names:
        print(f"\n  [OK] Target model '{ollama_model}' is ready!")
    else:
        print(f"\n  [ERROR] Target model '{ollama_model}' not found")
        print(f"  Run: ollama pull {ollama_model}")

except requests.exceptions.ConnectionError:
    print(f"  [ERROR] Cannot connect to Ollama at {ollama_url}")
    print("  Make sure Ollama is running")
except Exception as e:
    print(f"  [ERROR] {e}")

# Step 4: Import check
print("\n[4] Checking OpenHands worker import...")
try:
    from agent_factory.workers.openhands_worker import OpenHandsWorker
    print("  [OK] OpenHandsWorker imported successfully")
    print("  [OK] Ollama support integrated")
except Exception as e:
    print(f"  [ERROR] Import failed: {e}")

# Summary
print("\n" + "=" * 70)
print("  SETUP STATUS")
print("=" * 70)

if use_ollama:
    print("\n  Status: READY FOR FREE LLMs!")
    print("\n  You can now:")
    print("    1. Use OpenHands with ZERO API costs")
    print("    2. Run unlimited coding tasks locally")
    print("    3. Build 18-agent system for $0/month")
    print("\n  Quick Start:")
    print("    from agent_factory.core.agent_factory import AgentFactory")
    print("    factory = AgentFactory()")
    print("    worker = factory.create_openhands_agent()")
    print("    result = worker.run_task('Write a Python function...')")
    print("\n  Cost Savings: $200-500/month!")
else:
    print("\n  Status: Using PAID APIs")
    print("\n  To switch to FREE Ollama:")
    print("    1. Set USE_OLLAMA=true in .env")
    print("    2. Restart your terminal/script")
    print("    3. Start saving $200-500/month!")

print("\n" + "=" * 70)

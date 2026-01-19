#!/usr/bin/env python3
"""
Quick Test Script for Bob - Market Research Dominator

Run this to see Bob in action with a real market research query.

Usage:
    poetry run python test_bob.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from agents.unnamedagent_v1_0 import create_agent

def main():
    print("=" * 72)
    print("BOB - MARKET RESEARCH DOMINATOR - QUICK TEST")
    print("=" * 72)
    print()

    # Create agent
    print("[1/3] Creating Bob with full power tools...")
    try:
        bob = create_agent(llm_provider="openai", model_name="gpt-4o-mini")
        print("      [OK] Agent created")
        print(f"      [OK] Tools: 10 (research + file ops)")
        print()
    except Exception as e:
        print(f"      [ERROR] {e}")
        return 1

    # Test query
    print("[2/3] Running market research query...")
    print()
    query = (
        "Find 3 underserved niches in the AI agent marketplace that have:\n"
        "- High willingness to pay ($50-200/month)\n"
        "- Low competition (< 10 competitors)\n"
        "- Clear customer pain points\n\n"
        "Include MRR estimates and validation steps."
    )

    print("Query:")
    print("-" * 72)
    print(query)
    print("-" * 72)
    print()

    try:
        result = bob.invoke({"input": query})
        output = result.get("output", str(result))

        print("[3/3] Results:")
        print()
        print("=" * 72)
        print(output)
        print("=" * 72)
        print()

        print("[OK] Test completed successfully!")
        print()
        print("Next steps:")
        print("  1. Try more queries: poetry run python test_bob.py")
        print("  2. Chat with Bob: poetry run agentcli chat")
        print("  3. Run full demo: poetry run python agents/unnamedagent_v1_0.py")
        return 0

    except Exception as e:
        print(f"[ERROR] Error running query: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

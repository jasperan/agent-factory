"""
agent_builder_demo.py - Demonstration of AgentBuilder

Shows how to programmatically create agent configurations.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent_factory.cli_builder import AgentBuilder


def demo_create_agent_config():
    """Demo: Create a sample agent configuration programmatically."""
    print("=" * 60)
    print("DEMO: Creating Agent Configuration Programmatically")
    print("=" * 60)

    # Create agent config
    config = {
        "name": "demo_assistant",
        "role": "Demo Assistant",
        "description": "A demonstration agent for testing",
        "tool_collections": ["research", "file"],
        "llm_provider": "openai",
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "agent_type": "react",
        "system_prompt": "You are a helpful demo assistant. Always be concise and friendly.",
        "memory_enabled": True,
    }

    # Save config
    builder = AgentBuilder()
    config_file = builder.save_config(config)

    print(f"\n[OK] Demo agent saved to: {config_file}")
    print(f"\nConfiguration:")
    for key, value in config.items():
        print(f"  {key}: {value}")

    return config


def demo_load_agent_config():
    """Demo: Load an existing agent configuration."""
    print("\n" + "=" * 60)
    print("DEMO: Loading Agent Configuration")
    print("=" * 60)

    builder = AgentBuilder()
    config = builder.load_config("demo_assistant")

    if config:
        print("\n[OK] Loaded 'demo_assistant' configuration:")
        builder.show_config_summary(config)
    else:
        print("\n[ERROR] Agent 'demo_assistant' not found")


def demo_list_agents():
    """Demo: List all custom agents."""
    print("\n" + "=" * 60)
    print("DEMO: Listing All Custom Agents")
    print("=" * 60)

    builder = AgentBuilder()
    configs = builder.list_configs()

    print(f"\n Found {len(configs)} custom agent(s):\n")

    for config in configs:
        print(f"  - {config['name']}: {config['role']}")
        print(f"    Tools: {', '.join(config.get('tool_collections', [])) or 'None'}")
        print(f"    LLM: {config['llm_provider']}/{config['model']}")
        print()


def main():
    """Run all demos."""
    print("\n")
    print("*" * 60)
    print(" AGENT BUILDER DEMONSTRATION")
    print("*" * 60)

    demo_create_agent_config()
    demo_load_agent_config()
    demo_list_agents()

    print("=" * 60)
    print("All demos completed!")
    print("=" * 60)

    print("\nTry using the agent:")
    print("  agentcli chat --agent demo_assistant")
    print("  agentcli list-custom")
    print()


if __name__ == "__main__":
    main()

"""
Orchestrator Demo - Multi-agent routing
"""
import os
import sys
from pathlib import Path

# Add parent to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agent_factory.core import AgentFactory, EventType
from agent_factory.tools.research_tools import CurrentTimeTool


def main():
    print("=" * 60)
    print("ORCHESTRATOR DEMO")
    print("=" * 60)

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n[WARNING] OPENAI_API_KEY not found in environment variables")
        print("   Please set it in your .env file or environment")
        print("   Example: export OPENAI_API_KEY='your-api-key-here'\n")
        return

    # Create factory
    factory = AgentFactory(verbose=True)

    # Create a simple tool for agents
    time_tool = CurrentTimeTool()

    # Create specialist agents with minimal tools
    research_agent = factory.create_agent(
        role="Research Specialist",
        tools_list=[time_tool],
        system_prompt="You are a research assistant. Answer questions about facts and information.",
        enable_memory=False
    )

    creative_agent = factory.create_agent(
        role="Creative Writer",
        tools_list=[time_tool],
        system_prompt="You are a creative writer. Help with stories, poems, and creative content.",
        enable_memory=False
    )

    code_agent = factory.create_agent(
        role="Code Assistant",
        tools_list=[time_tool],
        system_prompt="You are a coding assistant. Help with programming questions.",
        enable_memory=False
    )

    # Create orchestrator
    orchestrator = factory.create_orchestrator(verbose=True)

    # Register agents with keywords
    orchestrator.register(
        "research",
        research_agent,
        keywords=["search", "find", "what is", "who is", "explain"],
        description="Answers factual questions and does research"
    )

    orchestrator.register(
        "creative",
        creative_agent,
        keywords=["write", "story", "poem", "creative"],
        description="Helps with creative writing and content"
    )

    orchestrator.register(
        "coding",
        code_agent,
        keywords=["code", "python", "function", "bug", "programming"],
        description="Helps with programming and code",
        is_fallback=True  # Default when nothing matches
    )

    # Subscribe to events
    def on_route(event):
        print(f"\n>>> ROUTE: {event.data['query'][:50]}...")
        print(f"    Agent: {event.data['matched_agent']}")
        print(f"    Method: {event.data['method']}")

    def on_complete(event):
        print(f"<<< COMPLETE: {event.agent_name} ({event.data['duration_ms']:.0f}ms)")

    orchestrator.event_bus.on(EventType.ROUTE_DECISION, on_route)
    orchestrator.event_bus.on(EventType.AGENT_END, on_complete)

    # Test queries
    print("\n" + "-" * 60)
    print("REGISTERED AGENTS:", orchestrator.list_agents())
    print("-" * 60)

    test_queries = [
        "What is the capital of France?",        # Should route to research
        "Write me a short poem about coding",    # Should route to creative
        "How do I write a for loop in Python?",  # Should route to coding
        "Tell me something interesting",         # Should fall back to coding
    ]

    for query in test_queries:
        print(f"\n{'=' * 60}")
        print(f"QUERY: {query}")
        print("=" * 60)

        result = orchestrator.route(query)

        if result.error:
            print(f"ERROR: {result.error}")
        else:
            # Extract response text
            if hasattr(result.response, 'get'):
                output = result.response.get('output', str(result.response))
            else:
                output = str(result.response)

            # Truncate for display
            if len(output) > 200:
                output = output[:200] + "..."

            print(f"\nRESPONSE:\n{output}")

    # Show event history
    print(f"\n{'=' * 60}")
    print("EVENT HISTORY SUMMARY")
    print("=" * 60)

    history = orchestrator.event_bus.get_history()
    print(f"Total events: {len(history)}")

    for event_type in EventType:
        count = len([e for e in history if e.event_type == event_type])
        if count > 0:
            print(f"  {event_type.value}: {count}")

    print("\nDemo complete!")


if __name__ == "__main__":
    main()

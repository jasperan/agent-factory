"""
AgentFactory Demo: Research Agent and Coding Agent Examples

This script demonstrates how to use the AgentFactory to create
specialized agents with different tool sets and capabilities.

Usage:
    # With Poetry 2.x
    poetry run python agent_factory/examples/demo.py

    # Or if environment is manually activated
    python agent_factory/examples/demo.py
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the factory and tools
from agent_factory.core.agent_factory import AgentFactory
from agent_factory.tools.research_tools import get_research_tools
from agent_factory.tools.coding_tools import get_coding_tools


def demo_research_agent():
    """Demonstrate the Research Agent with web search capabilities."""
    print("=" * 80)
    print("RESEARCH AGENT DEMO")
    print("=" * 80)

    # Initialize factory
    factory = AgentFactory(verbose=True)

    # Get research tools (Wikipedia + DuckDuckGo)
    research_tools = get_research_tools(
        include_wikipedia=True,
        include_duckduckgo=True,
        include_tavily=False,  # Set to True if you have TAVILY_API_KEY
        include_time=True
    )

    print(f"\n✓ Loaded {len(research_tools)} research tools")
    for tool in research_tools:
        print(f"  - {tool.name}: {tool.description[:60]}...")

    # Create research agent
    research_agent = factory.create_research_agent(
        tools_list=research_tools,
        system_prompt="You are a helpful research assistant. Always cite your sources."
    )

    print("\n✓ Created Research Agent")
    print(f"  Agent Type: {research_agent.metadata['agent_type']}")
    print(f"  LLM: {research_agent.metadata['llm_provider']} / {research_agent.metadata['model']}")
    print(f"  Memory: {'Enabled' if research_agent.metadata['memory_enabled'] else 'Disabled'}")

    # Example queries
    queries = [
        "What is LangChain and what are its main features?",
        "Who created Python and in what year?",
    ]

    for query in queries:
        print("\n" + "-" * 80)
        print(f"User: {query}")
        print("-" * 80)

        try:
            response = research_agent.invoke({"input": query})
            print(f"\nAgent: {response['output']}")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

    print("\n" + "=" * 80)


def demo_coding_agent():
    """Demonstrate the Coding Agent with file system capabilities."""
    print("\n\n")
    print("=" * 80)
    print("CODING AGENT DEMO")
    print("=" * 80)

    # Initialize factory
    factory = AgentFactory(verbose=True)

    # Get coding tools (file operations)
    coding_tools = get_coding_tools(
        include_read=True,
        include_write=True,
        include_list=True,
        include_git=True,
        include_search=True,
        base_dir="."  # Current directory
    )

    print(f"\n✓ Loaded {len(coding_tools)} coding tools")
    for tool in coding_tools:
        print(f"  - {tool.name}: {tool.description[:60]}...")

    # Create coding agent
    coding_agent = factory.create_coding_agent(
        tools_list=coding_tools,
        system_prompt="You are a helpful coding assistant. Write clean, well-documented code."
    )

    print("\n✓ Created Coding Agent")
    print(f"  Agent Type: {coding_agent.metadata['agent_type']}")
    print(f"  LLM: {coding_agent.metadata['llm_provider']} / {coding_agent.metadata['model']}")
    print(f"  Memory: {'Enabled' if coding_agent.metadata['memory_enabled'] else 'Disabled'}")

    # Example queries
    queries = [
        "List all Python files in the current directory",
        "What files are in the agent_factory/tools directory?",
    ]

    for query in queries:
        print("\n" + "-" * 80)
        print(f"User: {query}")
        print("-" * 80)

        try:
            response = coding_agent.invoke({"input": query})
            print(f"\nAgent: {response['output']}")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

    print("\n" + "=" * 80)


def demo_custom_agent():
    """Demonstrate creating a custom agent with mixed tools."""
    print("\n\n")
    print("=" * 80)
    print("CUSTOM AGENT DEMO (Mixed Tools)")
    print("=" * 80)

    # Initialize factory
    factory = AgentFactory(verbose=True)

    # Combine research and coding tools
    from agent_factory.tools.research_tools import WikipediaSearchTool, CurrentTimeTool
    from agent_factory.tools.coding_tools import ReadFileTool, ListDirectoryTool

    mixed_tools = [
        WikipediaSearchTool(),
        CurrentTimeTool(),
        ReadFileTool(),
        ListDirectoryTool(),
    ]

    print(f"\n✓ Loaded {len(mixed_tools)} mixed tools")

    # Create custom agent
    custom_agent = factory.create_agent(
        role="Hybrid Agent",
        tools_list=mixed_tools,
        system_prompt="You are a versatile AI assistant with both research and file access capabilities.",
        agent_type=AgentFactory.AGENT_TYPE_STRUCTURED_CHAT
    )

    print("\n✓ Created Custom Hybrid Agent")

    query = "What is the current time and what files are in the current directory?"
    print("\n" + "-" * 80)
    print(f"User: {query}")
    print("-" * 80)

    try:
        response = custom_agent.invoke({"input": query})
        print(f"\nAgent: {response['output']}")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

    print("\n" + "=" * 80)


def interactive_mode():
    """Run an interactive chat session with the research agent."""
    print("\n\n")
    print("=" * 80)
    print("INTERACTIVE MODE - Research Agent")
    print("=" * 80)
    print("Type 'exit' to quit, 'switch' to switch to coding agent")
    print("=" * 80)

    factory = AgentFactory(verbose=False)  # Less verbose for chat

    # Create agents
    research_tools = get_research_tools(include_tavily=False)
    research_agent = factory.create_research_agent(research_tools)

    coding_tools = get_coding_tools(base_dir=".")
    coding_agent = factory.create_coding_agent(coding_tools)

    current_agent = research_agent
    agent_name = "Research Agent"

    while True:
        user_input = input(f"\n[{agent_name}] You: ").strip()

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        if user_input.lower() == "switch":
            if current_agent == research_agent:
                current_agent = coding_agent
                agent_name = "Coding Agent"
            else:
                current_agent = research_agent
                agent_name = "Research Agent"
            print(f"✓ Switched to {agent_name}")
            continue

        if not user_input:
            continue

        try:
            response = current_agent.invoke({"input": user_input})
            print(f"\n[{agent_name}] Agent: {response['output']}")
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'exit' to quit.")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "AGENT FACTORY DEMONSTRATION" + " " * 31 + "║")
    print("╚" + "=" * 78 + "╝")

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  Warning: OPENAI_API_KEY not found in environment variables")
        print("   Please set it in your .env file or environment")
        print("   Example: export OPENAI_API_KEY='your-api-key-here'\n")
        return

    try:
        # Run demos
        demo_research_agent()
        demo_coding_agent()
        demo_custom_agent()

        # Ask if user wants interactive mode
        print("\n\n")
        response = input("Would you like to try interactive mode? (y/n): ").strip().lower()
        if response == 'y':
            interactive_mode()

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

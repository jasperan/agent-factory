"""
Agent Factory CLI - Typer Application

Main CLI entry point for Agent Factory.
Provides commands for interactive agent chat and management.
"""

import sys
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

from agent_factory.core.agent_factory import AgentFactory
from .agent_presets import (
    get_agent,
    list_available_agents,
    get_agent_description
)

# Load environment variables
load_dotenv()

# Initialize Typer app
app = typer.Typer(
    name="agentcli",
    help="Agent Factory - Interactive CLI for AI Agents",
    add_completion=False
)

# Rich console for formatted output
console = Console()


# =============================================================================
# Main Commands
# =============================================================================

@app.command()
def chat(
    agent: str = typer.Option(
        "research",
        "--agent", "-a",
        help="Agent to use (research, coding)"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Show detailed agent reasoning"
    ),
    temperature: float = typer.Option(
        0.0,
        "--temperature", "-t",
        help="LLM temperature (0.0-1.0)"
    ),
):
    """
    Start an interactive chat session with an AI agent.

    Examples:
        agentcli chat                    # Start with research agent
        agentcli chat --agent coding     # Start with coding agent
        agentcli chat --verbose          # Show agent reasoning
    """
    try:
        # Import here to avoid circular dependency
        from .chat_session import ChatSession

        # Check for OpenAI API key
        import os
        if not os.getenv("OPENAI_API_KEY"):
            console.print("[red]Error:[/red] OPENAI_API_KEY environment variable not set")
            console.print("\nPlease set your OpenAI API key in .env file:")
            console.print("  OPENAI_API_KEY=sk-proj-...")
            raise typer.Exit(1)

        # Create factory
        factory = AgentFactory(
            verbose=verbose,
            default_temperature=temperature
        )

        # Get agent
        try:
            agent_executor = get_agent(agent, factory)
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            console.print("\nAvailable agents:")
            for name, info in list_available_agents().items():
                console.print(f"  - {name}: {info['description']}")
            raise typer.Exit(1)

        # Start chat session
        session = ChatSession(
            agent_executor=agent_executor,
            agent_name=agent,
            verbose=verbose,
            factory=factory  # Pass factory for agent switching
        )

        session.run()

    except KeyboardInterrupt:
        console.print("\n\nGoodbye! Thanks for using Agent Factory.")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        raise typer.Exit(1)


@app.command("list-agents")
def list_agents():
    """
    List all available preset agents.

    Shows the available agents and their capabilities.
    """
    console.print("\n[bold]Available Agents:[/bold]\n")

    agents = list_available_agents()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Name", style="green")
    table.add_column("Description")

    for name, info in agents.items():
        table.add_row(name, info["description"])

    console.print(table)
    console.print(f"\n[dim]Use [bold]agentcli chat --agent <name>[/bold] to start chatting[/dim]\n")


@app.command()
def version():
    """Show the Agent Factory CLI version."""
    console.print("[bold]Agent Factory CLI[/bold]")
    console.print("Version: 0.1.0")
    console.print("\nA framework for building specialized AI agents")
    console.print("Powered by LangChain")


@app.command()
def create():
    """
    Create a new agent interactively (wizard mode).

    Launches the interactive agent creation wizard to build
    a custom agent from scratch or from a template.
    """
    try:
        from .interactive_creator import InteractiveAgentCreator

        creator = InteractiveAgentCreator()
        success = creator.run()

        if success:
            console.print("\n[green]Agent created successfully![/green]")
            raise typer.Exit(0)
        else:
            console.print("\n[yellow]Agent creation cancelled.[/yellow]")
            raise typer.Exit(1)

    except KeyboardInterrupt:
        console.print("\n\nAgent creation cancelled.")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# =============================================================================
# Utility Commands
# =============================================================================

@app.command()
def info(agent_name: str = typer.Argument(..., help="Agent name")):
    """
    Show information about a specific agent.

    Args:
        agent_name: Name of the agent (research, coding)

    Example:
        agentcli info research
    """
    description = get_agent_description(agent_name)
    console.print(f"\n{description}\n")


# =============================================================================
# Entry Point
# =============================================================================

def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()

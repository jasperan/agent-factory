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
    help="Agent Factory - Build and chat with specialized AI agents. Use 'agentcli roadmap' to view platform vision.",
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
        help="Choose which agent to chat with (research, coding, etc.). Use 'agentcli list-agents' to see all options."
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable detailed output showing the agent's thought process and tool usage"
    ),
    temperature: float = typer.Option(
        0.0,
        "--temperature", "-t",
        help="Control randomness in responses (0.0=focused and deterministic, 1.0=creative and varied)"
    ),
):
    """
    Start an interactive chat session with an AI agent.

    Chat with specialized AI agents for research, coding, or other tasks.
    Type your questions and the agent will respond using its tools and knowledge.
    Type '/exit' or press Ctrl+C to end the session.

    Examples:
        agentcli chat                           # Chat with research agent (default)
        agentcli chat --agent coding            # Chat with coding specialist
        agentcli chat --verbose                 # See agent's thought process
        agentcli chat -a research -t 0.7        # Research agent with creative responses
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

    Shows all pre-configured agents with descriptions of their capabilities.
    Use these agent names with the 'chat' command to start conversations.

    Example:
        agentcli list-agents              # View all available agents
        agentcli chat --agent research    # Then chat with chosen agent
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
    """
    Show the Agent Factory CLI version and information.

    Displays the current version, description, and technology stack.
    """
    console.print("[bold]Agent Factory CLI[/bold]")
    console.print("Version: 0.1.0")
    console.print("\nA framework for building specialized AI agents")
    console.print("Powered by LangChain and LangGraph")
    console.print("\nDocumentation: https://github.com/yourusername/agent-factory")
    console.print("Support: https://github.com/yourusername/agent-factory/issues")


@app.command()
def create():
    """
    Create a new agent interactively using the wizard.

    Launches an interactive step-by-step wizard to build custom agents.
    Choose from templates or build from scratch. The wizard will guide
    you through defining the agent's role, tools, and behavior.

    Examples:
        agentcli create                   # Start the interactive wizard
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
def roadmap():
    """
    Show the Agent Factory platform vision and development roadmap.

    Displays the transformation from CLI tool to multi-tenant SaaS platform,
    including phases, timeline, revenue targets, and key features.

    Example:
        agentcli roadmap                  # View platform development roadmap
    """
    console.print("\n[bold cyan]Agent Factory Platform Roadmap[/bold cyan]\n")

    console.print("[bold]Vision:[/bold] Transform Agent Factory from a CLI developer tool")
    console.print("into a commercial multi-tenant SaaS platform for building AI agents.\n")

    console.print("[bold]Target Market:[/bold] Indie developers, startups, and small teams\n")

    console.print("[bold yellow]Revenue Targets:[/bold yellow]")
    console.print("  Month 1:  $990 MRR    (Brain Fart Checker launch)")
    console.print("  Month 3:  $10,000 MRR (200 paid users) [green]<-- First Target[/green]")
    console.print("  Month 6:  $25,000 MRR (500 paid users)")
    console.print("  Year 1:   $66,000 MRR (1,100 paid users)\n")

    console.print("[bold yellow]Pricing Tiers:[/bold yellow]")
    console.print("  Free:       $0/month  (3 agents, 100 runs/month)")
    console.print("  Pro:        $49/month (unlimited agents, 5K runs/month)")
    console.print("  Enterprise: $299/month (multi-team, 50K runs/month)")
    console.print("  Brain Fart: $99/month (standalone spec validator)\n")

    console.print("[bold yellow]Implementation Timeline (13 weeks):[/bold yellow]\n")

    phases = [
        ("Phase 0", "Complete", "Platform Vision & Documentation", "Foundation complete"),
        ("Phase 1", "2-3 days", "LLM Abstraction Layer", "Multi-LLM routing, cost optimization"),
        ("Phase 2", "1 week", "Agent Orchestration", "Multi-agent workflows, routing"),
        ("Phase 3", "1 week", "Schema Standardization", "OpenAPI specs, validation"),
        ("Phase 4", "1 week", "Infrastructure Setup", "Google Cloud, Supabase, Redis"),
        ("Phase 5", "2 weeks", "Backend API Development", "FastAPI REST API, auth, billing"),
        ("Phase 6", "2 weeks", "Frontend Development", "Next.js dashboard, agent builder UI"),
        ("Phase 7", "1 week", "Multi-Tenancy & Auth", "Teams, RLS, SSO"),
        ("Phase 8", "1 week", "Brain Fart Checker MVP", "Standalone spec validator"),
        ("Phase 9", "1 week", "Marketplace Foundation", "Template library, discovery"),
        ("Phase 10", "1 week", "Billing Integration", "Stripe, usage tracking"),
        ("Phase 11", "1 week", "Testing & Optimization", "E2E tests, performance"),
        ("Phase 12", "1 week", "Production Launch", "Deploy, monitoring, docs"),
    ]

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Phase", style="cyan", width=8)
    table.add_column("Timeline", style="yellow", width=10)
    table.add_column("Name", style="green", width=30)
    table.add_column("Key Deliverables", width=40)

    for phase, timeline, name, deliverables in phases:
        table.add_row(phase, timeline, name, deliverables)

    console.print(table)

    console.print("\n[bold yellow]Key Differentiators:[/bold yellow]")
    console.print("  [green]+[/green] Constitutional Programming (specs are eternal, code is ephemeral)")
    console.print("  [green]+[/green] Cost Optimization (60% LLM savings via smart routing)")
    console.print("  [green]+[/green] Brain Fart Checker (standalone spec validation product)")
    console.print("  [green]+[/green] Multi-LLM Support (OpenAI, Anthropic, Google, local models)")
    console.print("  [green]+[/green] Template Marketplace (battle-tested agent templates)")
    console.print("  [green]+[/green] OpenHands Integration (autonomous coding agents)\n")

    console.print("[bold yellow]Competitive Position:[/bold yellow]")
    console.print("  Sweet spot between CrewAI (code-only), Vertex AI (enterprise-expensive),")
    console.print("  and MindStudio (no-code-locked). Developer flexibility + platform convenience.\n")

    console.print("[dim]For complete details, see docs/00_platform_roadmap.md[/dim]\n")


@app.command()
def info(agent_name: str = typer.Argument(..., help="Name of the agent (e.g., research, coding)")):
    """
    Show detailed information about a specific agent.

    Displays the agent's capabilities, available tools, and use cases.

    Examples:
        agentcli info research            # Show research agent details
        agentcli info coding              # Show coding agent details
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

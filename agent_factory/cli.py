"""
Agent Factory Interactive CLI

A user-friendly command-line interface for testing and interacting with agents.

Usage:
    agentcli chat                    # Start with default (research) agent
    agentcli chat --agent coding     # Start with coding agent
    agentcli run "Your query here"   # Quick one-off query
    agentcli list-agents             # List available agents
"""

import os
import sys
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent_factory.core.agent_factory import AgentFactory
from agent_factory.tools.coding_tools import get_coding_tools
from agent_factory.tools.research_tools import get_research_tools
from agent_factory.cli_builder import AgentBuilder

# Load environment variables
load_dotenv()

# Initialize Typer app and Rich console
app = typer.Typer(
    name="agentcli",
    help="Interactive CLI for Agent Factory - Test your AI agents with ease",
    add_completion=True,
)
console = Console()


class AgentREPL:
    """Interactive REPL for conversing with agents."""

    # Available agents configuration
    AGENTS = {
        "research": {
            "name": "Research Agent",
            "description": "Web search and information gathering",
            "type": AgentFactory.AGENT_TYPE_STRUCTURED_CHAT,
        },
        "coding": {
            "name": "Coding Agent",
            "description": "File operations and code analysis",
            "type": AgentFactory.AGENT_TYPE_REACT,
        },
    }

    def __init__(self, agent_name: str = "research", verbose: bool = False):
        """Initialize the REPL with specified agent."""
        self.factory = AgentFactory(verbose=verbose)
        self.current_agent = None
        self.agent_name = agent_name
        self.verbose = verbose
        self.history = InMemoryHistory()
        self.session = PromptSession(history=self.history)

        # Command completer for auto-completion
        self.command_completer = WordCompleter(
            ["/help", "/exit", "/agent", "/info", "/clear", "/tools", "/history"],
            ignore_case=True,
        )

        # Load initial agent
        self.load_agent(agent_name)

    def load_agent(self, name: str) -> bool:
        """Load an agent by name (built-in or custom)."""
        # Try built-in agents first
        if name in self.AGENTS:
            return self._load_builtin_agent(name)

        # Try custom agent
        builder = AgentBuilder()
        config = builder.load_config(name)

        if config is None:
            console.print(f"[red]Error: Unknown agent '{name}'[/red]")
            console.print(f"Built-in agents: {', '.join(self.AGENTS.keys())}")
            console.print("[dim]Custom agents: agentcli list-custom[/dim]")
            return False

        return self._load_custom_agent(config)

    def _load_builtin_agent(self, name: str) -> bool:
        """Load a built-in agent."""
        try:
            agent_config = self.AGENTS[name]

            if name == "research":
                tools = get_research_tools(
                    include_wikipedia=True,
                    include_duckduckgo=True,
                    include_tavily=False,  # Optional, requires API key
                    include_time=True,
                )
                self.current_agent = self.factory.create_agent(
                    role=agent_config["name"],
                    tools_list=tools,
                    system_prompt="You are a helpful research assistant. Always cite your sources and be thorough in your research.",
                    agent_type=agent_config["type"],
                )
            elif name == "coding":
                tools = get_coding_tools(
                    include_read=True,
                    include_write=True,
                    include_list=True,
                    include_git=True,
                    include_search=True,
                    base_dir=".",
                )
                self.current_agent = self.factory.create_agent(
                    role=agent_config["name"],
                    tools_list=tools,
                    system_prompt="You are a helpful coding assistant. Write clean, well-documented code and explain your reasoning.",
                    agent_type=agent_config["type"],
                )

            self.agent_name = name
            return True

        except Exception as e:
            console.print(f"[red]Error loading agent: {str(e)}[/red]")
            return False

    def _load_custom_agent(self, config: dict) -> bool:
        """Load a custom agent from configuration."""
        try:
            # Collect tools based on tool collections
            tools = []

            for collection in config.get("tool_collections", []):
                if collection == "research":
                    tools.extend(get_research_tools(
                        include_wikipedia=True,
                        include_duckduckgo=True,
                        include_tavily=False,
                        include_time=True,
                    ))
                elif collection in ["coding", "file"]:
                    tools.extend(get_coding_tools(
                        include_read=True,
                        include_write=True,
                        include_list=True,
                        include_git=collection == "coding",
                        include_search=True,
                        base_dir=".",
                    ))
                elif collection == "twin":
                    # Twin tools require ProjectTwin instance
                    from agent_factory.refs import ProjectTwin, TwinAgent
                    twin = ProjectTwin(project_root=Path.cwd())
                    twin.sync(include_patterns=["*.py"])
                    twin_agent = TwinAgent(project_twin=twin)
                    tools.extend(twin_agent.tools)

            # Create custom factory with LLM config
            custom_factory = AgentFactory(
                llm_provider=config.get("llm_provider", "openai"),
                model=config.get("model", "gpt-4o-mini"),
                temperature=config.get("temperature", 0.7),
                verbose=self.verbose,
            )

            # Create agent
            self.current_agent = custom_factory.create_agent(
                role=config["role"],
                tools_list=tools,
                system_prompt=config["system_prompt"],
                agent_type=config.get("agent_type", AgentFactory.AGENT_TYPE_REACT),
                memory=config.get("memory_enabled", True),
            )

            self.agent_name = config["name"]

            # Update AGENTS dict for display
            self.AGENTS[config["name"]] = {
                "name": config["role"],
                "description": config["description"],
                "type": config.get("agent_type", AgentFactory.AGENT_TYPE_REACT),
            }

            return True

        except Exception as e:
            console.print(f"[red]Error loading custom agent: {str(e)}[/red]")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False

    def show_welcome(self):
        """Display welcome message."""
        welcome_text = f"""
[bold cyan]Agent Factory Interactive CLI[/bold cyan]

Current Agent: [bold green]{self.AGENTS[self.agent_name]['name']}[/bold green]
Type your message to chat, or use commands:

[dim]Commands:[/dim]
  [cyan]/help[/cyan]     - Show available commands
  [cyan]/exit[/cyan]     - Exit the CLI
  [cyan]/agent[/cyan]    - Switch to different agent
  [cyan]/info[/cyan]     - Show current agent configuration
  [cyan]/clear[/cyan]    - Clear the screen
  [cyan]/tools[/cyan]    - List available tools
  [cyan]/history[/cyan]  - Show conversation history

Press [cyan]Ctrl+C[/cyan] to interrupt, [cyan]Ctrl+D[/cyan] to exit
        """
        console.print(Panel(welcome_text, title="Welcome", border_style="cyan"))

    def show_help(self):
        """Display help message."""
        help_table = Table(title="Available Commands", show_header=True, header_style="bold cyan")
        help_table.add_column("Command", style="cyan", width=15)
        help_table.add_column("Description", style="white")

        commands = [
            ("/help", "Show this help message"),
            ("/exit", "Exit the interactive CLI"),
            ("/agent <name>", "Switch agent (research, coding)"),
            ("/info", "Show current agent configuration"),
            ("/clear", "Clear the screen"),
            ("/tools", "List available tools for current agent"),
            ("/history", "Show conversation history (command history)"),
        ]

        for cmd, desc in commands:
            help_table.add_row(cmd, desc)

        console.print(help_table)

    def show_info(self):
        """Show current agent configuration."""
        if not self.current_agent:
            console.print("[yellow]No agent loaded[/yellow]")
            return

        metadata = self.current_agent.metadata
        info_table = Table(title="Current Configuration", show_header=False)
        info_table.add_column("Property", style="cyan", width=20)
        info_table.add_column("Value", style="white")

        info_table.add_row("Agent", metadata["role"])
        info_table.add_row("Type", metadata["agent_type"])
        info_table.add_row("LLM Provider", metadata["llm_provider"])
        info_table.add_row("Model", metadata["model"])
        info_table.add_row("Temperature", str(metadata["temperature"]))
        info_table.add_row("Tools Count", str(metadata["tools_count"]))
        info_table.add_row("Memory", "Enabled" if metadata["memory_enabled"] else "Disabled")

        console.print(info_table)

    def show_tools(self):
        """List available tools for current agent."""
        if not self.current_agent:
            console.print("[yellow]No agent loaded[/yellow]")
            return

        tools_table = Table(title="Available Tools", show_header=True, header_style="bold cyan")
        tools_table.add_column("Tool Name", style="cyan", width=25)
        tools_table.add_column("Description", style="white")

        for tool in self.current_agent.tools:
            tools_table.add_row(tool.name, tool.description[:80] + "..." if len(tool.description) > 80 else tool.description)

        console.print(tools_table)

    def show_history(self):
        """Show command history."""
        console.print("\n[bold cyan]Command History:[/bold cyan]")
        history_items = list(self.history.get_strings())
        if not history_items:
            console.print("[dim]No history yet[/dim]")
            return

        for i, item in enumerate(history_items[-10:], 1):  # Show last 10
            console.print(f"  [dim]{i}.[/dim] {item}")
        console.print()

    def handle_command(self, user_input: str) -> bool:
        """
        Handle special commands.

        Returns:
            bool: True if should exit, False otherwise
        """
        if not user_input.startswith("/"):
            return False

        parts = user_input.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "/exit" or cmd == "/quit":
            return True

        elif cmd == "/help":
            self.show_help()

        elif cmd == "/agent":
            if not args:
                console.print("[yellow]Usage: /agent <name>[/yellow]")
                console.print(f"Available: {', '.join(self.AGENTS.keys())}")
            else:
                agent_name = args.strip().lower()
                if self.load_agent(agent_name):
                    console.print(f"[green][OK] Switched to {self.AGENTS[agent_name]['name']}[/green]")

        elif cmd == "/info":
            self.show_info()

        elif cmd == "/clear":
            console.clear()
            self.show_welcome()

        elif cmd == "/tools":
            self.show_tools()

        elif cmd == "/history":
            self.show_history()

        else:
            console.print(f"[red]Unknown command: {cmd}[/red]")
            console.print("[dim]Type /help for available commands[/dim]")

        return False

    def query_agent(self, user_input: str):
        """Send query to agent and display response."""
        try:
            # Show thinking indicator
            with console.status("[yellow]Agent is thinking...[/yellow]", spinner="dots"):
                response = self.current_agent.invoke({"input": user_input})

            # Display response
            output = response.get("output", str(response))
            console.print(f"\n[bold green]{self.AGENTS[self.agent_name]['name']}:[/bold green]")
            console.print(Markdown(output))
            console.print()  # Add spacing

        except KeyboardInterrupt:
            console.print("\n[yellow]Query interrupted[/yellow]\n")
        except Exception as e:
            console.print(f"\n[red][ERROR] {str(e)}[/red]\n")
            if self.verbose:
                import traceback
                console.print("[dim]" + traceback.format_exc() + "[/dim]")

    def run(self):
        """Run the interactive REPL loop."""
        self.show_welcome()

        while True:
            try:
                # Get user input with agent name in prompt
                agent_display = self.AGENTS[self.agent_name]["name"]
                user_input = self.session.prompt(
                    f"[{agent_display}] You: ", completer=self.command_completer
                ).strip()

                # Skip empty input
                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    if self.handle_command(user_input):
                        break  # Exit requested
                    continue

                # Query the agent
                self.query_agent(user_input)

            except KeyboardInterrupt:
                console.print("\n[yellow]Press Ctrl+C again or type /exit to quit[/yellow]")
                continue

            except EOFError:
                # Ctrl+D pressed
                break

        console.print("\n[cyan]Goodbye! Thanks for using Agent Factory.[/cyan]\n")


@app.command()
def chat(
    agent: str = typer.Option(
        "research",
        "--agent",
        "-a",
        help="Agent to use (research, coding)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output for debugging",
    ),
):
    """
    Start interactive chat session with an agent.

    This opens an interactive REPL where you can have multi-turn
    conversations with your chosen agent.
    """
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        console.print(Panel(
            "[red]ERROR: OPENAI_API_KEY not found[/red]\n\n"
            "Please set your OpenAI API key in the .env file:\n"
            "[cyan]OPENAI_API_KEY=sk-proj-...[/cyan]\n\n"
            "Or export it as an environment variable.",
            title="Configuration Error",
            border_style="red"
        ))
        raise typer.Exit(1)

    # Validate agent name
    if agent not in AgentREPL.AGENTS:
        console.print(f"[red]Error: Unknown agent '{agent}'[/red]")
        console.print(f"Available agents: {', '.join(AgentREPL.AGENTS.keys())}")
        raise typer.Exit(1)

    # Start REPL
    repl = AgentREPL(agent_name=agent, verbose=verbose)
    repl.run()


@app.command()
def run(
    query: str = typer.Argument(..., help="Query to execute"),
    agent: str = typer.Option(
        "research",
        "--agent",
        "-a",
        help="Agent to use (research, coding)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
):
    """
    Run a single query non-interactively.

    This is useful for quick queries without entering interactive mode.
    """
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        console.print("[red]ERROR: OPENAI_API_KEY not found in environment[/red]")
        raise typer.Exit(1)

    try:
        # Initialize factory
        factory = AgentFactory(verbose=verbose)

        # Load appropriate agent
        if agent == "research":
            tools = get_research_tools(
                include_wikipedia=True,
                include_duckduckgo=True,
                include_tavily=False,
                include_time=True,
            )
            agent_executor = factory.create_agent(
                role="Research Agent",
                tools_list=tools,
                system_prompt="You are a helpful research assistant.",
                agent_type=AgentFactory.AGENT_TYPE_STRUCTURED_CHAT,
            )
        elif agent == "coding":
            tools = get_coding_tools(base_dir=".")
            agent_executor = factory.create_agent(
                role="Coding Agent",
                tools_list=tools,
                system_prompt="You are a helpful coding assistant.",
                agent_type=AgentFactory.AGENT_TYPE_REACT,
            )
        else:
            console.print(f"[red]Unknown agent: {agent}[/red]")
            raise typer.Exit(1)

        # Execute query
        console.print(f"[cyan]Query:[/cyan] {query}\n")
        with console.status("[yellow]Processing...[/yellow]", spinner="dots"):
            response = agent_executor.invoke({"input": query})

        # Display response
        output = response.get("output", str(response))
        console.print(Panel(Markdown(output), title="Response", border_style="green"))

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()
        raise typer.Exit(1)


@app.command("list-agents")
def list_agents():
    """List all available agents and their descriptions."""
    agents_table = Table(title="Available Agents", show_header=True, header_style="bold cyan")
    agents_table.add_column("Agent Name", style="cyan", width=15)
    agents_table.add_column("Description", style="white", width=50)
    agents_table.add_column("Type", style="dim", width=20)

    for key, config in AgentREPL.AGENTS.items():
        agents_table.add_row(
            key,
            config["description"],
            config["type"].replace("_", " ").title(),
        )

    console.print(agents_table)
    console.print("\n[dim]Use with: agentcli chat --agent <name>[/dim]")


@app.command()
def version():
    """Show Agent Factory version information."""
    version_info = """
[bold cyan]Agent Factory CLI[/bold cyan]
Version: 0.1.0
Python: 3.10+

[dim]https://github.com/Mikecranesync/Agent-Factory[/dim]
    """
    console.print(Panel(version_info, title="Version", border_style="cyan"))


@app.command()
def create():
    """
    Create a custom agent interactively.

    Guides you through configuring a new agent:
    - Basic info (name, role, description)
    - Tool selection (research, coding, file, twin)
    - LLM configuration (provider, model, temperature)
    - Agent type and system prompt
    - Memory settings

    The agent is saved to ~/.agent_factory/agents/ and can be used
    with 'agentcli chat --agent <name>' or 'agentcli run'.
    """
    try:
        builder = AgentBuilder()
        config = builder.build_agent_config()

        # Show summary
        builder.show_config_summary(config)

        # Confirm save
        from rich.prompt import Confirm
        if Confirm.ask("\n[cyan]Save this agent configuration?[/cyan]", default=True):
            config_file = builder.save_config(config)
            console.print(f"\n[green]✓ Agent '{config['name']}' saved to {config_file}[/green]")
            console.print(f"\n[dim]Use with: agentcli chat --agent {config['name']}[/dim]\n")
        else:
            console.print("\n[yellow]Agent not saved[/yellow]\n")

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Agent creation cancelled[/yellow]\n")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"\n[red]Error creating agent: {str(e)}[/red]\n")
        raise typer.Exit(1)


@app.command("list-custom")
def list_custom_agents():
    """List all custom agents created with 'agentcli create'."""
    builder = AgentBuilder()
    configs = builder.list_configs()

    if not configs:
        console.print("\n[yellow]No custom agents found[/yellow]")
        console.print("[dim]Create one with: agentcli create[/dim]\n")
        return

    table = Table(title="Custom Agents", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="cyan", width=15)
    table.add_column("Role", style="white", width=25)
    table.add_column("Tools", style="dim", width=30)
    table.add_column("LLM", style="green", width=20)

    for config in configs:
        tools_str = ", ".join(config.get("tool_collections", [])) or "None"
        llm_str = f"{config['llm_provider']}/{config['model']}"
        table.add_row(
            config["name"],
            config["role"],
            tools_str,
            llm_str
        )

    console.print(table)
    console.print(f"\n[dim]Use with: agentcli chat --agent <name>[/dim]\n")


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()

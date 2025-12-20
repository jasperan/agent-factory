"""
Interactive Chat Session for AI Agents.

Provides a REPL (Read-Eval-Print Loop) for chatting with AI agents
with command support, history, and rich formatting.
"""

import os
from typing import Optional, List, Dict, Any
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

from agent_factory.compat.langchain_shim import AgentExecutor
from agent_factory.core.agent_factory import AgentFactory


class ChatSession:
    """
    Interactive chat session with an AI agent.

    Features:
    - Prompt-toolkit REPL with history
    - In-chat commands (/help, /exit, /agent, etc.)
    - Rich formatted output
    - Conversation history tracking
    """

    def __init__(
        self,
        agent_executor: AgentExecutor,
        agent_name: str,
        verbose: bool = False,
        factory: Optional[AgentFactory] = None
    ):
        """
        Initialize chat session.

        Args:
            agent_executor: LangChain AgentExecutor to chat with
            agent_name: Name of the agent (for display)
            verbose: Show detailed output
            factory: AgentFactory for switching agents
        """
        self.agent_executor = agent_executor
        self.agent_name = agent_name
        self.verbose = verbose
        self.factory = factory

        # Initialize prompt-toolkit
        self.history = InMemoryHistory()
        self.session = PromptSession(
            history=self.history,
            auto_suggest=AutoSuggestFromHistory()
        )

        # Rich console
        self.console = Console()

        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []

    def run(self):
        """
        Main REPL loop.

        Continuously prompts for user input and processes it.
        Handles both regular messages and slash commands.
        """
        # Welcome message
        self._show_welcome()

        while True:
            try:
                # Get user input
                user_input = self._get_input()

                if not user_input or user_input.isspace():
                    continue

                # Handle commands
                if user_input.startswith('/'):
                    should_continue = self._handle_command(user_input)
                    if not should_continue:
                        break
                else:
                    # Regular chat message
                    self._chat(user_input)

            except KeyboardInterrupt:
                self.console.print("\n[dim]Use /exit to quit[/dim]")
                continue
            except EOFError:
                break

        # Goodbye message
        self.console.print("\nGoodbye! Thanks for using Agent Factory.")

    def _get_input(self) -> str:
        """
        Get user input with prompt-toolkit.

        Returns:
            User input string
        """
        agent_display = self.agent_name.capitalize()
        prompt_text = f"[{agent_display}] You: "

        try:
            user_input = self.session.prompt(prompt_text)
            return user_input.strip()
        except EOFError:
            return "/exit"

    def _chat(self, message: str):
        """
        Send a message to the agent and display response.

        Args:
            message: User message
        """
        try:
            # Show thinking indicator
            self.console.print("[dim]> Agent is thinking...[/dim]")

            # Invoke agent
            response = self.agent_executor.invoke({"input": message})

            # Extract output
            output = response.get("output", "No response")

            # Display response
            self.console.print()
            self.console.print(Panel(
                Markdown(output),
                title=f"[bold]{self.agent_name.capitalize()} Agent[/bold]",
                border_style="cyan"
            ))
            self.console.print()

            # Save to history
            self.conversation_history.append({
                "user": message,
                "agent": output
            })

        except Exception as e:
            self.console.print(f"[red]Error:[/red] {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()

    def _handle_command(self, command: str) -> bool:
        """
        Handle slash commands.

        Args:
            command: Command string (e.g., "/help", "/exit")

        Returns:
            bool: True to continue session, False to exit
        """
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None

        if cmd == "/help" or cmd == "/?":
            self._show_help()
        elif cmd == "/exit" or cmd == "/quit" or cmd == "/q":
            return False
        elif cmd == "/agent":
            if arg:
                self._switch_agent(arg)
            else:
                self.console.print("[yellow]Usage: /agent <name>[/yellow]")
                self.console.print("Available: research, coding")
        elif cmd == "/info":
            self._show_info()
        elif cmd == "/tools":
            self._show_tools()
        elif cmd == "/history":
            self._show_history()
        elif cmd == "/clear" or cmd == "/cls":
            self._clear_screen()
        else:
            self.console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
            self.console.print("[dim]Type /help for available commands[/dim]")

        return True

    def _show_welcome(self):
        """Display welcome message."""
        welcome = Panel(
            f"[bold cyan]Agent Factory Interactive CLI[/bold cyan]\n"
            f"Current Agent: [bold]{self.agent_name.capitalize()} Agent[/bold]\n\n"
            f"[dim]Type [bold]/help[/bold] for commands or start chatting![/dim]",
            border_style="cyan"
        )
        self.console.print()
        self.console.print(welcome)
        self.console.print()

    def _show_help(self):
        """Display help information."""
        table = Table(title="[bold]Available Commands[/bold]", show_header=True, header_style="bold cyan")
        table.add_column("Command", style="green")
        table.add_column("Description")

        commands = [
            ("/help, /?", "Show this help message"),
            ("/exit, /quit, /q", "Exit the CLI"),
            ("/agent <name>", "Switch to different agent"),
            ("/info", "Show current agent info"),
            ("/tools", "List available tools"),
            ("/history", "Show conversation history"),
            ("/clear, /cls", "Clear the screen"),
        ]

        for cmd, desc in commands:
            table.add_row(cmd, desc)

        self.console.print()
        self.console.print(table)
        self.console.print()

    def _switch_agent(self, agent_name: str):
        """
        Switch to a different agent.

        Args:
            agent_name: Name of agent to switch to
        """
        if not self.factory:
            self.console.print("[yellow]Agent switching not available (no factory)[/yellow]")
            return

        try:
            from .agent_presets import get_agent

            # Create new agent
            new_agent = get_agent(agent_name, self.factory)
            self.agent_executor = new_agent
            self.agent_name = agent_name

            self.console.print(f"[green]Switched to {agent_name.capitalize()} Agent[/green]")

        except ValueError as e:
            self.console.print(f"[red]Error:[/red] {e}")
        except Exception as e:
            self.console.print(f"[red]Error switching agent:[/red] {e}")

    def _show_info(self):
        """Display current agent information."""
        from .agent_presets import get_agent_description

        self.console.print()
        self.console.print(Panel(
            f"[bold]Current Agent:[/bold] {self.agent_name.capitalize()}\n"
            f"[bold]Description:[/bold] {get_agent_description(self.agent_name)}\n"
            f"[bold]Verbose:[/bold] {self.verbose}\n"
            f"[bold]Messages:[/bold] {len(self.conversation_history)}",
            title="Agent Information",
            border_style="cyan"
        ))
        self.console.print()

    def _show_tools(self):
        """Display available tools for current agent."""
        try:
            tools = self.agent_executor.tools

            if not tools:
                self.console.print("[yellow]No tools available[/yellow]")
                return

            table = Table(title="[bold]Available Tools[/bold]", show_header=True, header_style="bold cyan")
            table.add_column("#", style="dim")
            table.add_column("Tool Name", style="green")
            table.add_column("Description")

            for i, tool in enumerate(tools, 1):
                name = tool.name
                desc = tool.description[:60] + "..." if len(tool.description) > 60 else tool.description
                table.add_row(str(i), name, desc)

            self.console.print()
            self.console.print(table)
            self.console.print()

        except Exception as e:
            self.console.print(f"[red]Error showing tools:[/red] {e}")

    def _show_history(self):
        """Display conversation history."""
        if not self.conversation_history:
            self.console.print("[yellow]No conversation history yet[/yellow]")
            return

        self.console.print()
        self.console.print("[bold]Conversation History:[/bold]")
        self.console.print()

        for i, msg in enumerate(self.conversation_history, 1):
            self.console.print(f"[dim]{i}.[/dim] [bold]You:[/bold] {msg['user']}")
            self.console.print(f"   [bold]Agent:[/bold] {msg['agent'][:100]}...")
            self.console.print()

    def _clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
        self._show_welcome()

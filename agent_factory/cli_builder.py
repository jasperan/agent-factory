"""
Agent Builder - Interactive CLI for creating custom agents

Allows users to build custom agents through interactive prompts:
- Choose agent name and role
- Select tools from available collections
- Configure LLM settings
- Save/load agent configurations
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator, ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm, Prompt

console = Console()


class NonEmptyValidator(Validator):
    """Validator that ensures input is not empty."""

    def validate(self, document):
        if not document.text.strip():
            raise ValidationError(message="This field cannot be empty")


class AgentBuilder:
    """Interactive agent configuration builder."""

    # Available tool collections
    TOOL_COLLECTIONS = {
        "research": {
            "name": "Research Tools",
            "description": "Web search, Wikipedia, DuckDuckGo",
            "tools": ["wikipedia", "duckduckgo", "tavily", "time"],
        },
        "coding": {
            "name": "Coding Tools",
            "description": "File operations, Git, code search",
            "tools": ["read_file", "write_file", "list_directory", "file_search", "git_status"],
        },
        "file": {
            "name": "File Tools",
            "description": "Safe file operations with caching",
            "tools": ["read_file", "write_file", "list_directory", "file_search"],
        },
        "twin": {
            "name": "Project Twin",
            "description": "Codebase analysis and queries",
            "tools": ["find_file", "get_dependencies", "search_functions", "explain_file"],
        },
    }

    # LLM providers
    LLM_PROVIDERS = {
        "openai": {
            "name": "OpenAI",
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            "default": "gpt-4o-mini",
        },
        "anthropic": {
            "name": "Anthropic",
            "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
            "default": "claude-3-5-sonnet-20241022",
        },
        "google": {
            "name": "Google",
            "models": ["gemini-1.5-pro", "gemini-1.5-flash"],
            "default": "gemini-1.5-flash",
        },
    }

    # Agent types
    AGENT_TYPES = {
        "react": "ReAct - Reasoning and Acting (best for tool-heavy tasks)",
        "structured_chat": "Structured Chat - Better for conversation",
        "openai_functions": "OpenAI Functions - Function calling",
        "openai_tools": "OpenAI Tools - Latest tool format",
    }

    def __init__(self, config_dir: Path = None):
        """
        Initialize agent builder.

        Args:
            config_dir: Directory to save/load agent configs (default: ~/.agent_factory/agents/)
        """
        if config_dir is None:
            config_dir = Path.home() / ".agent_factory" / "agents"
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def show_welcome(self):
        """Display welcome message."""
        welcome = """
[bold cyan]Agent Factory - Agent Builder[/bold cyan]

Create custom AI agents interactively. You'll be guided through:
1. Basic configuration (name, role, description)
2. Tool selection (choose capabilities)
3. LLM settings (provider, model, temperature)
4. System prompt (define behavior)

Your agent will be saved and available in the CLI.
        """
        console.print(Panel(welcome, title="Welcome", border_style="cyan"))

    def show_tool_collections(self):
        """Display available tool collections."""
        table = Table(title="Available Tool Collections", show_header=True, header_style="bold cyan")
        table.add_column("Key", style="cyan", width=12)
        table.add_column("Name", style="white", width=20)
        table.add_column("Description", style="dim", width=50)

        for key, config in self.TOOL_COLLECTIONS.items():
            table.add_row(key, config["name"], config["description"])

        console.print(table)

    def show_llm_providers(self):
        """Display available LLM providers."""
        table = Table(title="Available LLM Providers", show_header=True, header_style="bold cyan")
        table.add_column("Key", style="cyan", width=12)
        table.add_column("Provider", style="white", width=20)
        table.add_column("Models", style="dim", width=50)

        for key, config in self.LLM_PROVIDERS.items():
            models = ", ".join(config["models"][:3]) + "..."
            table.add_row(key, config["name"], models)

        console.print(table)

    def prompt_basic_config(self) -> Dict[str, str]:
        """
        Prompt for basic agent configuration.

        Returns:
            Dictionary with name, role, description
        """
        console.print("\n[bold]Step 1: Basic Configuration[/bold]\n")

        name = Prompt.ask(
            "[cyan]Agent name[/cyan] (used as identifier)",
            default="my_agent"
        ).strip().lower().replace(" ", "_")

        role = Prompt.ask(
            "[cyan]Agent role[/cyan] (e.g., 'Research Assistant', 'Code Helper')",
            default="Custom Agent"
        )

        description = Prompt.ask(
            "[cyan]Short description[/cyan]",
            default="A custom AI agent"
        )

        return {
            "name": name,
            "role": role,
            "description": description,
        }

    def prompt_tool_selection(self) -> List[str]:
        """
        Prompt for tool collection selection.

        Returns:
            List of selected tool collection keys
        """
        console.print("\n[bold]Step 2: Tool Selection[/bold]\n")
        self.show_tool_collections()

        console.print("\n[dim]Enter tool collections separated by commas (e.g., 'research,file')[/dim]")
        console.print("[dim]Or press Enter to skip (no tools)[/dim]\n")

        selection = Prompt.ask(
            "[cyan]Select tool collections[/cyan]",
            default=""
        )

        if not selection.strip():
            return []

        # Parse selection
        selected = [s.strip().lower() for s in selection.split(",")]

        # Validate
        valid_selections = []
        for sel in selected:
            if sel in self.TOOL_COLLECTIONS:
                valid_selections.append(sel)
            else:
                console.print(f"[yellow]Warning: Unknown tool collection '{sel}', skipping[/yellow]")

        return valid_selections

    def prompt_llm_config(self) -> Dict[str, Any]:
        """
        Prompt for LLM configuration.

        Returns:
            Dictionary with provider, model, temperature
        """
        console.print("\n[bold]Step 3: LLM Configuration[/bold]\n")
        self.show_llm_providers()

        # Provider selection
        provider = Prompt.ask(
            "\n[cyan]Select LLM provider[/cyan]",
            choices=list(self.LLM_PROVIDERS.keys()),
            default="openai"
        )

        provider_config = self.LLM_PROVIDERS[provider]

        # Model selection
        console.print(f"\n[dim]Available models: {', '.join(provider_config['models'])}[/dim]")
        model = Prompt.ask(
            "[cyan]Select model[/cyan]",
            default=provider_config["default"]
        )

        # Temperature
        temperature = Prompt.ask(
            "[cyan]Temperature[/cyan] (0.0-1.0, lower = more focused)",
            default="0.7"
        )

        try:
            temperature = float(temperature)
            temperature = max(0.0, min(1.0, temperature))
        except ValueError:
            console.print("[yellow]Invalid temperature, using 0.7[/yellow]")
            temperature = 0.7

        return {
            "llm_provider": provider,
            "model": model,
            "temperature": temperature,
        }

    def prompt_agent_type(self) -> str:
        """
        Prompt for agent type selection.

        Returns:
            Selected agent type key
        """
        console.print("\n[bold]Step 4: Agent Type[/bold]\n")

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Type", style="cyan", width=20)
        table.add_column("Description", style="white", width=60)

        for key, desc in self.AGENT_TYPES.items():
            table.add_row(key, desc)

        console.print(table)

        agent_type = Prompt.ask(
            "\n[cyan]Select agent type[/cyan]",
            choices=list(self.AGENT_TYPES.keys()),
            default="react"
        )

        return agent_type

    def prompt_system_prompt(self) -> str:
        """
        Prompt for system prompt.

        Returns:
            System prompt string
        """
        console.print("\n[bold]Step 5: System Prompt[/bold]\n")
        console.print("[dim]Define your agent's behavior and personality.[/dim]")
        console.print("[dim]Press Enter twice to finish (or Ctrl+D)[/dim]\n")

        lines = []
        console.print("[cyan]System prompt:[/cyan]")

        try:
            while True:
                line = input()
                if not line and lines and not lines[-1]:
                    # Two empty lines = done
                    break
                lines.append(line)
        except EOFError:
            pass

        # Remove trailing empty lines
        while lines and not lines[-1]:
            lines.pop()

        system_prompt = "\n".join(lines) if lines else "You are a helpful AI assistant."

        return system_prompt

    def prompt_memory(self) -> bool:
        """
        Prompt for memory enablement.

        Returns:
            True if memory should be enabled
        """
        console.print("\n[bold]Step 6: Memory[/bold]\n")
        return Confirm.ask(
            "[cyan]Enable conversation memory?[/cyan]",
            default=True
        )

    def build_agent_config(self) -> Dict[str, Any]:
        """
        Run interactive agent builder.

        Returns:
            Complete agent configuration dictionary
        """
        self.show_welcome()

        # Gather configuration
        basic = self.prompt_basic_config()
        tools = self.prompt_tool_selection()
        llm_config = self.prompt_llm_config()
        agent_type = self.prompt_agent_type()
        system_prompt = self.prompt_system_prompt()
        memory = self.prompt_memory()

        # Build complete config
        config = {
            **basic,
            "tool_collections": tools,
            **llm_config,
            "agent_type": agent_type,
            "system_prompt": system_prompt,
            "memory_enabled": memory,
        }

        return config

    def save_config(self, config: Dict[str, Any]) -> Path:
        """
        Save agent configuration to file.

        Args:
            config: Agent configuration dictionary

        Returns:
            Path to saved config file
        """
        config_file = self.config_dir / f"{config['name']}.json"

        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        return config_file

    def load_config(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load agent configuration from file.

        Args:
            name: Agent name

        Returns:
            Agent configuration dictionary, or None if not found
        """
        config_file = self.config_dir / f"{name}.json"

        if not config_file.exists():
            return None

        with open(config_file, 'r') as f:
            return json.load(f)

    def list_configs(self) -> List[Dict[str, Any]]:
        """
        List all saved agent configurations.

        Returns:
            List of agent config dictionaries
        """
        configs = []

        for config_file in self.config_dir.glob("*.json"):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    configs.append(config)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load {config_file.name}: {e}[/yellow]")

        return configs

    def show_config_summary(self, config: Dict[str, Any]):
        """
        Display configuration summary.

        Args:
            config: Agent configuration dictionary
        """
        console.print("\n[bold green]Agent Configuration Summary[/bold green]\n")

        table = Table(show_header=False, box=None)
        table.add_column("Property", style="cyan", width=20)
        table.add_column("Value", style="white")

        table.add_row("Name", config["name"])
        table.add_row("Role", config["role"])
        table.add_row("Description", config["description"])
        table.add_row("Tool Collections", ", ".join(config["tool_collections"]) or "None")
        table.add_row("LLM Provider", config["llm_provider"])
        table.add_row("Model", config["model"])
        table.add_row("Temperature", str(config["temperature"]))
        table.add_row("Agent Type", config["agent_type"])
        table.add_row("Memory Enabled", "Yes" if config["memory_enabled"] else "No")
        table.add_row("System Prompt", config["system_prompt"][:100] + "..." if len(config["system_prompt"]) > 100 else config["system_prompt"])

        console.print(table)

#!/usr/bin/env python3
"""
OpenHands Interactive CLI

A Gemini-style interactive CLI for running OpenHands agents with local Ollama models.

Features:
- Interactive model selection from available Ollama models
- Configurable tool selection (Terminal, FileEditor, ApplyPatch, TaskTracker)
- Real-time task execution with progress indicator
- Automatic display of modified/created files
- Token usage and cost tracking

Usage:
    python openhands_cli.py
"""

import os
import sys
import subprocess
import warnings
from pathlib import Path
from typing import Set

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
import questionary

# Suppress warnings
warnings.filterwarnings("ignore")

from agent_factory.core.agent_factory import AgentFactory
from agent_factory.workers.openhands_worker import ToolOption, DEFAULT_TOOLS, ALL_TOOLS

console = Console()


def setup_workspace() -> Path:
    """Create and return the workspace directory."""
    workspace = Path("tests")
    workspace.mkdir(exist_ok=True)
    return workspace


def print_header(model: str = None, tools: Set[ToolOption] = None):
    """Print the CLI header."""
    subtitle_parts = []
    
    if model:
        subtitle_parts.append(f"Model: [cyan]{model}[/cyan]")
    else:
        subtitle_parts.append("[dim]Powered by Agent Factory & Ollama[/dim]")
    
    if tools:
        tool_names = ", ".join(t.value for t in tools)
        subtitle_parts.append(f"Tools: [green]{tool_names}[/green]")
    
    subtitle = " | ".join(subtitle_parts)
    
    console.print(Panel.fit(
        "[bold blue]OpenHands Interactive CLI[/bold blue]\n" + f"[dim]{subtitle}[/dim]",
        border_style="blue"
    ))


def display_file_content(workspace: Path, filename: Path):
    """Display the content of a file with syntax highlighting."""
    file_path = workspace / filename
    if file_path.exists() and file_path.is_file():
        try:
            content = file_path.read_text()
            ext = file_path.suffix.lstrip(".") or "txt"
            console.print(Panel(
                Syntax(content, ext, theme="monokai", line_numbers=True),
                title=f"[bold]{filename}[/bold]",
                expand=False
            ))
        except Exception as e:
            console.print(f"[red]Error reading {filename}: {e}[/red]")


def get_file_state(workspace: Path) -> dict:
    """Get current file state (path -> mtime) for change detection."""
    state = {}
    if not workspace.exists():
        return state
    for path in workspace.rglob("*"):
        if path.is_file() and ".openhands" not in str(path):
            state[str(path.relative_to(workspace))] = path.stat().st_mtime
    return state


def get_ollama_models() -> list[str]:
    """Get list of available Ollama models, sorted by priority."""
    try:
        result = subprocess.run(
            ["ollama", "list"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        if result.returncode != 0:
            return []
            
        models = []
        lines = result.stdout.strip().split('\n')[1:]  # Skip header
        for line in lines:
            if line.strip():
                models.append(line.split()[0])
        
        # Priority models for coding tasks (in order of preference)
        priority = [
            "qwen2.5-coder:latest",
            "qwen3-coder:latest",
            "deepseek-coder:latest",
            "codegemma:latest",
            "llama3.2:latest",
            "llama3.1:latest",
            "glm4:latest",
            "qwen2:latest"
        ]
        
        def sort_key(name):
            if name in priority:
                return (0, priority.index(name))
            return (1, name)
        
        return sorted(models, key=sort_key)
        
    except subprocess.TimeoutExpired:
        console.print("[yellow]Timeout getting Ollama models[/yellow]")
        return []
    except FileNotFoundError:
        console.print("[yellow]Ollama not found. Is it installed?[/yellow]")
        return []
    except Exception as e:
        console.print(f"[yellow]Could not list Ollama models: {e}[/yellow]")
        return []


def select_model() -> str:
    """Interactive model selection with arrow keys."""
    models = get_ollama_models()
    
    if not models:
        console.print("[yellow]No Ollama models found. Using default: qwen2.5-coder:latest[/yellow]")
        return "qwen2.5-coder:latest"
    
    try:
        selected = questionary.select(
            "Select Ollama Model:",
            choices=models,
            default=models[0] if models else None
        ).ask()
        
        if selected is None:  # User pressed Ctrl+C
            return None
            
        return selected
        
    except KeyboardInterrupt:
        return None


def select_tools() -> Set[ToolOption]:
    """Interactive tool selection with checkboxes."""
    tool_choices = [
        questionary.Choice(
            title=f"{tool.value} {'(default)' if tool in DEFAULT_TOOLS else ''}",
            value=tool,
            checked=tool in DEFAULT_TOOLS
        )
        for tool in ToolOption
    ]
    
    try:
        # Ask if user wants to customize tools
        customize = questionary.confirm(
            "Customize enabled tools?",
            default=False
        ).ask()
        
        if customize is None:  # Ctrl+C
            return None
            
        if not customize:
            return DEFAULT_TOOLS
        
        selected = questionary.checkbox(
            "Select tools to enable:",
            choices=tool_choices
        ).ask()
        
        if selected is None:  # User pressed Ctrl+C
            return None
            
        return set(selected) if selected else DEFAULT_TOOLS
        
    except KeyboardInterrupt:
        return None


def display_model_info(model: str, worker):
    """Display model capabilities and info."""
    table = Table(title="Model Configuration", show_header=False, box=None)
    table.add_column("Property", style="dim")
    table.add_column("Value")
    
    table.add_row("Model", model)
    table.add_row("Tool Calling", "[green]Yes[/green]" if worker.supports_tool_calling else "[yellow]Prompt-based[/yellow]")
    table.add_row("Ollama Base URL", worker.ollama_base_url)
    table.add_row("Keep Alive", worker.keep_alive)
    
    console.print(table)
    console.print()


def main():
    """Main CLI entry point."""
    print_header()
    
    # Model selection
    selected_model = select_model()
    if selected_model is None:
        console.print("\n[bold green]Goodbye![/bold green]")
        return
    
    # Tool selection
    enabled_tools = select_tools()
    if enabled_tools is None:
        console.print("\n[bold green]Goodbye![/bold green]")
        return
    
    # Setup
    workspace = setup_workspace()
    
    # Clear screen and show header with selected model and tools
    console.clear()
    print_header(selected_model, enabled_tools)
    
    # Initialize Factory and Worker
    factory = AgentFactory(
        default_llm_provider="ollama",
        default_model=selected_model,
        enable_routing=False  # Disable cloud routing for local Ollama
    )
    
    abs_workspace = workspace.resolve()
    console.print(f"[dim]Workspace: {abs_workspace}[/dim]")
    
    worker = factory.create_openhands_agent(
        workspace_dir=abs_workspace,
        enabled_tools=enabled_tools
    )
    
    # Display model info
    display_model_info(selected_model, worker)
    
    console.print("[dim]Ready. Type 'exit' or 'quit' to leave. Type 'tools' to show enabled tools.[/dim]\n")

    # Main loop
    while True:
        try:
            task = questionary.text(
                "Task >",
                qmark="",
            ).ask()
        except KeyboardInterrupt:
            console.print("\n[bold green]Goodbye![/bold green]")
            break
            
        if task is None:  # Ctrl+C
            console.print("\n[bold green]Goodbye![/bold green]")
            break
            
        if not task or task.lower() in ('exit', 'quit'):
            console.print("[bold green]Goodbye![/bold green]")
            break
        
        # Special commands
        if task.lower() == 'tools':
            console.print(f"[bold]Enabled Tools:[/bold] {', '.join(t.value for t in enabled_tools)}")
            continue
            
        if task.lower() == 'clear':
            console.clear()
            print_header(selected_model, enabled_tools)
            continue
            
        # Capture state before
        state_before = get_file_state(workspace)
        
        # Run task
        with console.status("[bold green]Agent Working...[/bold green]"):
            result = worker.run_task(task)
            
        if result.success:
            # Build result panel content
            result_content = "[bold green]Success[/bold green]"
            
            # Add token usage if available
            if result.token_usage:
                result_content += f"\n[dim]Tokens: {result.token_usage.get('total_tokens', 'N/A')} | Cost: ${result.cost:.4f}[/dim]"
            
            # Add truncated logs
            log_lines = result.logs.strip().split('\n')
            if len(log_lines) > 10:
                result_content += f"\n\n[dim]... ({len(log_lines) - 10} lines hidden)[/dim]\n"
                result_content += '\n'.join(log_lines[-10:])
            else:
                result_content += f"\n\n{result.logs.strip()}"
            
            console.print(Panel(
                result_content,
                title="Result",
                border_style="green"
            ))
            
            # Show execution context
            console.print(f"\n[dim]Working Directory: {workspace.resolve()}[/dim]")
            
            # Determine changed files
            state_after = get_file_state(workspace)
            changed_files = [
                f_path for f_path, mtime in state_after.items()
                if f_path not in state_before or state_before[f_path] != mtime
            ]
            
            if changed_files:
                console.print("\n[bold]Modified/Created Files:[/bold]")
                for f_str in changed_files:
                    display_file_content(workspace, Path(f_str))
            else:
                console.print("\n[dim]No files changed.[/dim]")
        else:
            console.print(Panel(
                f"[bold red]Failed[/bold red]\n{result.message}\n\n{result.logs}",
                title="Error",
                border_style="red"
            ))
        
        console.print()  # Add spacing between tasks


if __name__ == "__main__":
    main()

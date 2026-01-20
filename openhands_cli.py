import os
import sys
import warnings
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.tree import Tree
import questionary

# Suppress warnings
warnings.filterwarnings("ignore")

from agent_factory.core.agent_factory import AgentFactory

console = Console()

def setup_workspace():
    # Workspace relative to current directory
    workspace = Path("tests")
    workspace.mkdir(exist_ok=True)
    return workspace

def print_header():
    console.print(Panel.fit(
        "[bold blue]OpenHands Interactive CLI[/bold blue]\n"
        "[dim]Powered by Agent Factory & Ollama[/dim]",
        border_style="blue"
    ))

def display_file_tree(workspace: Path):
    tree = Tree(f"[bold gold1]{workspace.name}[/bold gold1]")
    
    paths = sorted(workspace.rglob("*"))
    visible_files = []
    
    if not paths:
        tree.add("[italic dim]Empty[/italic dim]")
    
    for path in paths:
        if path.is_file() and ".openhands" not in str(path):
            rel_path = path.relative_to(workspace)
            tree.add(str(rel_path))
            visible_files.append(rel_path)
            
    console.print(tree)
    return visible_files

def display_file_content(workspace: Path, filename: Path):
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

def get_file_state(workspace: Path):
    """Returns a dict of {rel_path: mtime} for all files in workspace."""
    state = {}
    if not workspace.exists():
        return state
    for path in workspace.rglob("*"):
        if path.is_file() and ".openhands" not in str(path):
            state[str(path.relative_to(workspace))] = path.stat().st_mtime
    return state

def main():
    print_header()
    workspace = setup_workspace()
    
    # Get available OLLAMA models
    try:
        import subprocess
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        models = []
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:] # Skip header
            for line in lines:
                if line.strip():
                     models.append(line.split()[0])
        
        # Filter for coding/tool capable models or just show all
        # Priority models
        priority = ["qwen2.5-coder:latest", "llama3.2:latest", "codegemma:latest", "glm4:latest"]
        sorted_models = sorted(models, key=lambda x: (x not in priority, x))
        
        if models:
            selected_model = questionary.select(
                "Select Ollama Model:",
                choices=sorted_models,
                default=sorted_models[0] if sorted_models else None
            ).ask()
        else:
            selected_model = "qwen2.5-coder:latest" # Fallback
            
    except Exception as e:
        console.print(f"[yellow]Could not list Ollama models: {e}[/yellow]")
        selected_model = "qwen2.5-coder:latest"

    # Initialize Factory
    factory = AgentFactory(
        default_llm_provider="ollama",
        default_model=selected_model
    )
    
    # Create Worker with specific workspace
    abs_workspace = workspace.resolve()
    console.print(f"[dim]Initializing OpenHands Worker in: {abs_workspace}[/dim]")
    worker = factory.create_openhands_agent(workspace_dir=abs_workspace)
    console.print("[dim]Ready.[/dim]\n")

    while True:
        try:
            task = questionary.text("Task >").ask()
        except KeyboardInterrupt:
            console.print("\n[bold green]Goodbye![/bold green]")
            break
            
        if not task or task.lower() in ('exit', 'quit'):
            console.print("[bold green]Goodbye![/bold green]")
            break
            
        # Capture state before
        state_before = get_file_state(workspace)
        
        with console.status("[bold green]Agent Working...[/bold green]"):
            result = worker.run_task(task)
            
        if result.success:
            console.print(Panel(
                f"[bold green]Success[/bold green]\n{result.logs.strip()}",
                title="Result",
                border_style="green"
            ))
            
            # Show execution context
            console.print(f"\n[dim]Current Working Directory: {workspace.resolve()}[/dim]")
            
            # Determine changed files
            state_after = get_file_state(workspace)
            changed_files = []
            
            for f_path, mtime in state_after.items():
                if f_path not in state_before or state_before[f_path] != mtime:
                    changed_files.append(f_path)
            
            if changed_files:
                 console.print("\n[bold]Modified/Created Files:[/bold]")
                 for f_str in changed_files:
                     display_file_content(workspace, Path(f_str))
            else:
                 console.print("\n[dim]No files changed.[/dim]")

        else:
            console.print(Panel(
                f"[bold red]Failed[/bold red]\n{result.message}\n{result.logs}",
                title="Error",
                border_style="red"
            ))

if __name__ == "__main__":
    main()

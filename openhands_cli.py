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

def main():
    print_header()
    workspace = setup_workspace()
    
    # Initialize Factory
    factory = AgentFactory(
        default_llm_provider="ollama",
        default_model="qwen2.5:7b"
    )
    
    # Create Worker with specific workspace
    console.print(f"[dim]Initializing OpenHands Worker in: {workspace.resolve()}[/dim]")
    worker = factory.create_openhands_agent(workspace_dir=workspace)
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
            
        with console.status("[bold green]Agent Working...[/bold green]"):
            result = worker.run_task(task)
            
        if result.success:
            console.print(Panel(
                f"[bold green]Success[/bold green]\n{result.logs.strip()}",
                title="Result",
                border_style="green"
            ))
            
            # Show file tree
            console.print("\n[bold]Current Workspace Files:[/bold]")
            visible_files = display_file_tree(workspace)
            
            # Show content of files
            # Since the worker returns 'files_changed' as all files in workspace (current implementation)
            # We filter/show them. 
            if result.files_changed:
                console.print("\n[bold]File Contents:[/bold]")
                # Use result.files_changed which are strings relative to workspace
                # Limit to avoid huge dumps if many files
                count = 0
                for f_str in result.files_changed:
                    if count >= 3:
                        console.print(f"[dim]... and {len(result.files_changed) - count} more files[/dim]")
                        break
                    
                    # f_str is relative path string
                    display_file_content(workspace, Path(f_str))
                    count += 1
        else:
            console.print(Panel(
                f"[bold red]Failed[/bold red]\n{result.message}\n{result.logs}",
                title="Error",
                border_style="red"
            ))

if __name__ == "__main__":
    main()

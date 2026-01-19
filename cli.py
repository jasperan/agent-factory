#!/usr/bin/env python3
"""
Agent Factory CLI
An interactive command-line interface for running autonomous coding agents.
"""
import sys
import os
import subprocess
import time
from pathlib import Path
from typing import Optional

try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt, Confirm
    import questionary
    from dotenv import load_dotenv
except ImportError:
    print("❌ Missing dependencies. Please run: pip install -r requirements.txt")
    sys.exit(1)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from datetime import datetime
from agent_factory.core.agent_factory import AgentFactory
from agent_factory.workers.openhands_worker import OpenHandsWorker
from agent_factory.scaffold.orchestrator import ScaffoldOrchestrator

# Initialize Rich Console
console = Console()
app = typer.Typer(help="Agent Factory CLI - Run autonomous agents locally")

def print_header():
    console.print(Panel.fit(
        "[bold cyan]Agent Factory CLI[/bold cyan]\n[dim]Autonomous Coding Agents Powered by Ollama[/dim]",
        border_style="cyan"
    ))

def check_dependencies() -> bool:
    """Check if Docker and Ollama are running."""
    # Check Docker
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[bold red]❌ Docker is not installed or not in PATH.[/bold red]")
        console.print("Please install Docker Desktop: https://www.docker.com/products/docker-desktop")
        return False
        
    # Check Ollama
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        import requests
        requests.get(f"{ollama_url}/api/tags", timeout=2)
    except:
        console.print(f"[bold red]❌ Ollama is not running at {ollama_url}[/bold red]")
        console.print("Run 'ollama serve' to start it.")
        return False

    return True

@app.command()
def start():
    """Start a new autonomous coding task."""
    print_header()
    load_dotenv()
    
    if not check_dependencies():
        raise typer.Exit(code=1)
        
    # Interactive Inputs
    repo_path = questionary.path(
        "Which repository or folder should the agent work on?",
        default=os.getcwd(),
        only_directories=True
    ).ask()
    
    if not repo_path:
        console.print("[yellow]Operation cancelled.[/yellow]")
        return

    task_desc = questionary.text(
        "What should the agent do?",
        multiline=True,
        validate=lambda text: True if len(text.strip()) > 5 else "Please provide a more detailed description."
    ).ask()
    
    if not task_desc:
        return

    model = questionary.select(
        "Select Model:",
        choices=[
            "deepseek-coder:6.7b (Free/Local)",
            "deepseek-coder:33b (Free/Local - Requires 32GB RAM)",
            "claude-3-5-sonnet (Paid API)",
            "gpt-4o (Paid API)"
        ]
    ).ask()
    
    model_id = model.split(" ")[0]
    use_ollama = "Free/Local" in model
    
    # Confirmation
    console.print(f"\n[bold green]🚀 Ready to Launch![/bold green]")
    console.print(f"Directory: [cyan]{repo_path}[/cyan]")
    console.print(f"Model: [cyan]{model_id}[/cyan]")
    console.print(f"Task: [italic]{task_desc}[/italic]")
    
    if not Confirm.ask("Start Agent?"):
        console.print("[yellow]Cancelled.[/yellow]")
        return

    # Execution
    try:
        factory = AgentFactory(verbose=False)
        worker = factory.create_openhands_agent(
            model=model_id, 
            use_ollama=use_ollama,
            workspace_dir=Path(repo_path)
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            # Streaming execution
            def stream_logger(msg):
                progress.console.print(f"[dim]{msg}[/dim]", highlight=False)
                
            task_id = progress.add_task("Agent is working...", total=None)
            
            # Synchronous execution with streaming
            result = worker.run_task(task_desc, timeout=600, on_log=stream_logger)
            
        if result.success:
            console.print(Panel(f"[bold green]✅ Task Completed Successfully![/bold green]\n\n{result.message}", title="Result"))
            if result.files_changed:
                console.print("\n[bold]Files Modified:[/bold]")
                for f in result.files_changed:
                    console.print(f" - {f}")
        else:
            console.print(Panel(f"[bold red]❌ Task Failed[/bold red]\n\n{result.message}\n\n[dim]Logs:[/dim]\n{result.logs[-500:]}", title="Error"))
            
    except Exception as e:
        console.print(f"[bold red]An error occurred:[/bold red] {e}")

@app.command()
def autonomous(
    mode: str = typer.Option("BACKLOG", help="Execution mode (BACKLOG or GITHUB)"),
    interval: int = typer.Option(60, help="Seconds to wait between cycles"),
    max_tasks: int = typer.Option(1, help="Max tasks per cycle"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate execution"),
    workspace: Optional[str] = typer.Option(None, help="Working directory"),
    query: Optional[str] = typer.Option(None, help="Starting task query")
):
    """Run agents in a continuous autonomous loop."""
    print_header()
    load_dotenv()
    
    repo_root = Path(workspace) if workspace else Path.cwd()
    
    if not check_dependencies():
        raise typer.Exit(code=1)
        
    console.print(f"[bold green]🤖 Starting Autonomous Runner[/bold green]")
    console.print(f"Mode: [cyan]{mode}[/cyan], Interval: [cyan]{interval}s[/cyan], Max Tasks: [cyan]{max_tasks}[/cyan]")
    if workspace:
        console.print(f"Workspace: [cyan]{workspace}[/cyan]")
    if query:
        console.print(f"Query: [cyan]{query}[/cyan]")
    if dry_run:
        console.print("[yellow]DRY RUN ACTIVE - No changes will be made[/yellow]")

    try:
        # Initialize orchestrator
        orchestrator = ScaffoldOrchestrator(
            repo_root=repo_root,
            dry_run=dry_run,
            max_tasks=max_tasks,
            query=query
        )

        console.print("\n[bold cyan]Press Ctrl+C to stop the runner[/bold cyan]\n")

        while True:
            start_time = time.time()
            timestamp = datetime.now().strftime("%H:%M:%S")
            console.print(f"[dim][{timestamp}][/dim] [bold blue]Cycle Starting...[/bold blue]")

            # Run orchestrator for one cycle
            summary = orchestrator.run()

            # Log cycle summary
            console.print(f"[bold green]Cycle Complete.[/bold green] Completed: {summary.get('tasks_completed', 0)}, Failed: {summary.get('tasks_failed', 0)}")

            # Calculate sleep time
            elapsed_time = time.time() - start_time
            sleep_time = max(0, interval - elapsed_time)

            if sleep_time > 0:
                console.print(f"[dim]Sleeping for {sleep_time:.0f}s...[/dim]")
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        console.print("\n[yellow]Shutdown signal received. Stopping...[/yellow]")
        raise typer.Exit()
    except Exception as e:
        console.print(f"\n[bold red]FATAL ERROR:[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command()
def doctor():
    """Check health of the Agent Factory environment."""
    print_header()
    load_dotenv()
    
    console.print("[bold]Diagnosing Environment...[/bold]\n")
    
    # Check Docker
    try:
        ver = subprocess.run(["docker", "--version"], check=True, capture_output=True, text=True).stdout.strip()
        console.print(f"✅ Docker: [green]{ver}[/green]")
    except:
        console.print("❌ Docker: [red]Not Found[/red]")
        
    # Check Ollama
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        import requests
        resp = requests.get(f"{ollama_url}/api/tags", timeout=2)
        if resp.status_code == 200:
            console.print(f"✅ Ollama: [green]Running at {ollama_url}[/green]")
            models = [m['name'] for m in resp.json().get('models', [])]
            console.print(f"   Available Models: {', '.join(models)}")
        else:
            console.print(f"⚠️  Ollama: [yellow]Running but returned {resp.status_code}[/yellow]")
    except:
        console.print(f"❌ Ollama: [red]Not running at {ollama_url}[/red]")

    # Check Env
    if os.path.exists(".env"):
        console.print("✅ Configuration: [green].env found[/green]")
    else:
        console.print("⚠️  Configuration: [yellow].env missing[/yellow]")

if __name__ == "__main__":
    import warnings
    # Suppress pkg_resources warning from litellm
    warnings.filterwarnings("ignore", category=UserWarning, module="litellm.utils")
    
    # Check if no arguments provided, if so, default to help (Typer does this, but users might expect 'start')
    if len(sys.argv) == 1:
        print("💡 No command provided. Did you mean 'start'?\n")
        sys.argv.append("--help")
        
    app()

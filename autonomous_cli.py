#!/usr/bin/env python3
"""
Autonomous Code Improvement CLI

A Gemini-style interactive CLI for running autonomous code improvement cycles
using the Planner → Worker → Judge pipeline.

Features:
- Interactive suggestion review and approval
- Real-time progress visualization with rich Live display
- Arrow-key navigation
- History and metrics display
- Diff visualization before verification
- Configuration menu
- Headless mode for CI/automation

Usage:
    python autonomous_cli.py                    # Interactive mode
    python autonomous_cli.py --headless         # Headless mode (auto-accept)
    python autonomous_cli.py --target /path     # Specify target repo
    python autonomous_cli.py --max-suggestions 3
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.markdown import Markdown
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
import questionary

# Ensure agent_factory is importable
sys.path.insert(0, str(Path(__file__).parent))

from agent_factory.autonomous import (
    AutonomousRunner,
    AutonomousConfig,
    Suggestion,
    SuggestionStatus,
    Verdict,
    VerdictStatus,
)

console = Console()


def print_header():
    """Print the CLI header."""
    console.print(Panel.fit(
        "[bold magenta]🤖 Autonomous Code Improvement System[/bold magenta]\n"
        "[dim]Planner → Worker → Judge Pipeline | Powered by Ollama[/dim]",
        border_style="magenta"
    ))


def print_suggestion(suggestion: Suggestion, index: int, total: int):
    """Display a suggestion in a formatted panel."""
    status_colors = {
        "pending": "yellow",
        "accepted": "green",
        "rejected": "red",
        "in_progress": "blue",
        "completed": "green",
        "failed": "red",
    }
    color = status_colors.get(suggestion.status, "white")
    
    content = f"""[bold]{suggestion.title}[/bold]

[dim]Category:[/dim] {suggestion.category}
[dim]Priority:[/dim] {'⭐' * min(suggestion.priority, 10)} ({suggestion.priority}/10)
[dim]Status:[/dim] [{color}]{suggestion.status}[/{color}]

{suggestion.description}

[dim]Affected Files:[/dim]
{chr(10).join(f'  • {f}' for f in suggestion.affected_files) or '  (none specified)'}

[dim]Acceptance Criteria:[/dim]
{chr(10).join(f'  ✓ {c}' for c in suggestion.acceptance_criteria) or '  (none specified)'}

[dim]Reasoning:[/dim] {suggestion.reasoning or '(none)'}"""

    console.print(Panel(
        content,
        title=f"[bold]Suggestion {index}/{total}[/bold]",
        border_style=color
    ))


def print_verdict(verdict: Verdict):
    """Display a judge verdict."""
    if verdict.status == VerdictStatus.PASS:
        color = "green"
        icon = "✅"
    elif verdict.status == VerdictStatus.FAIL:
        color = "red"
        icon = "❌"
    else:
        color = "yellow"
        icon = "⚠️"
    
    content = f"""{icon} [bold]Verdict: {verdict.status.upper()}[/bold]

[dim]Score:[/dim] {verdict.score:.0%}

[dim]Feedback:[/dim]
{verdict.feedback}

[dim]Criteria Met:[/dim]
{chr(10).join(f'  ✓ {c}' for c in verdict.criteria_met) or '  (none)'}

[dim]Criteria Failed:[/dim]
{chr(10).join(f'  ✗ {c}' for c in verdict.criteria_failed) or '  (none)'}"""

    if verdict.suggested_fixes:
        content += f"""

[dim]Suggested Fixes:[/dim]
{chr(10).join(f'  → {f}' for f in verdict.suggested_fixes)}"""

    console.print(Panel(content, border_style=color))


def select_model() -> Optional[str]:
    """Interactive model selection."""
    import subprocess
    
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return "qwen2.5-coder:latest"
        
        models = []
        lines = result.stdout.strip().split('\n')[1:]
        for line in lines:
            if line.strip():
                models.append(line.split()[0])
        
        if not models:
            return "qwen2.5-coder:latest"
        
        # Prioritize coding models
        priority = ["qwen2.5-coder", "qwen3-coder", "deepseek-coder", "codegemma", "llama3"]
        
        def sort_key(name):
            for i, p in enumerate(priority):
                if p in name:
                    return (0, i)
            return (1, name)
        
        models.sort(key=sort_key)
        
        selected = questionary.select(
            "Select Ollama Model:",
            choices=models,
            default=models[0]
        ).ask()
        
        return selected
        
    except Exception:
        return "qwen2.5-coder:latest"


def select_target_repo() -> Optional[str]:
    """Select target repository to analyze."""
    # Default to /home/ubuntu/git/tests for safe experimentation
    default = "/home/ubuntu/git/tests"
    
    console.print(f"[dim]Default: {default}[/dim]")
    
    path = questionary.path(
        "Target repository path:",
        default=default,
        only_directories=True
    ).ask()
    
    return path


def select_target_directory(repo_path: str) -> Optional[str]:
    """Select target directory within repository."""
    repo = Path(repo_path)
    if not repo.exists():
        return "tests"
        
    # Get all direct subdirectories
    try:
        subdirs = [d.name for d in repo.iterdir() if d.is_dir() and not d.name.startswith('.')]
    except Exception:
        return "tests"
        
    subdirs.sort()
    # Add option for root
    choices = [questionary.Choice("(root - scan entire repo)", value="")] + subdirs
    
    # Default to root for full repo scanning
    default_val = ""

    selected = questionary.select(
        "Select target directory (will only work on files in this directory):",
        choices=choices,
        default=default_val
    ).ask()
    
    return selected


def review_suggestions(suggestions: List[Suggestion]) -> List[Suggestion]:
    """Interactive suggestion review."""
    accepted = []
    
    for i, suggestion in enumerate(suggestions, 1):
        console.clear()
        print_header()
        print_suggestion(suggestion, i, len(suggestions))
        
        action = questionary.select(
            "Action:",
            choices=[
                questionary.Choice("Accept", value="accept"),
                questionary.Choice("Reject", value="reject"),
                questionary.Choice("Skip (decide later)", value="skip"),
                questionary.Choice("Accept All Remaining", value="accept_all"),
                questionary.Choice("Reject All Remaining", value="reject_all"),
                questionary.Choice("Cancel", value="cancel"),
            ]
        ).ask()
        
        if action == "accept":
            suggestion.status = SuggestionStatus.ACCEPTED
            accepted.append(suggestion)
        elif action == "reject":
            suggestion.status = SuggestionStatus.REJECTED
        elif action == "accept_all":
            suggestion.status = SuggestionStatus.ACCEPTED
            accepted.append(suggestion)
            for remaining in suggestions[i:]:
                remaining.status = SuggestionStatus.ACCEPTED
                accepted.append(remaining)
            break
        elif action == "reject_all":
            suggestion.status = SuggestionStatus.REJECTED
            for remaining in suggestions[i:]:
                remaining.status = SuggestionStatus.REJECTED
            break
        elif action == "cancel":
            return []
    
    return accepted


def show_run_summary(runner: AutonomousRunner):
    """Show summary of a completed run."""
    run = runner.current_run
    if not run:
        console.print("[yellow]No run data available[/yellow]")
        return
    
    table = Table(title="Run Summary")
    table.add_column("Metric", style="dim")
    table.add_column("Value")
    
    table.add_row("Target Repository", run.target_repo)
    table.add_row("Model", run.model)
    table.add_row("Total Suggestions", str(run.total_suggestions))
    table.add_row("Accepted", str(run.accepted_count))
    table.add_row("Completed", f"[green]{run.completed_count}[/green]")
    table.add_row("Failed", f"[red]{run.failed_count}[/red]")
    
    if run.started_at and run.completed_at:
        duration = run.completed_at - run.started_at
        table.add_row("Duration", str(duration))
    
    console.print(table)


def show_diff(runner: AutonomousRunner):
    """Show git diff of changes."""
    console.print("\n[bold]📝 Changes Made:[/bold]")
    diff = runner.get_git_diff()
    if diff and diff != "(No changes detected)":
        console.print(Panel(diff, title="Git Diff", border_style="cyan"))
    else:
        console.print("[dim]No changes detected[/dim]")


def run_with_live_progress(runner: AutonomousRunner, accepted: List[Suggestion]):
    """Run suggestions with rich live progress display and beautified agent logs."""
    
    def print_agent_output(agent: str, message: str, style: str = "dim"):
        """Print stylized agent output."""
        icons = {
            "planner": "🧠",
            "worker": "🔧", 
            "judge": "⚖️",
            "system": "🤖"
        }
        colors = {
            "planner": "blue",
            "worker": "yellow",
            "judge": "magenta",
            "system": "cyan"
        }
        icon = icons.get(agent.lower(), "📌")
        color = colors.get(agent.lower(), "white")
        console.print(f"[{color}]{icon} [{agent.upper()}][/{color}] [{style}]{message}[/{style}]")
    
    def on_status(status: str):
        # Determine agent from status message
        agent = "system"
        if "generating" in status.lower() or "suggestion" in status.lower():
            agent = "planner"
        elif "implementing" in status.lower() or "worker" in status.lower():
            agent = "worker"
        elif "verifying" in status.lower() or "judge" in status.lower():
            agent = "judge"
        print_agent_output(agent, status)
    
    def on_implementation(suggestion, logs: str):
        """Show worker implementation output."""
        console.print()
        console.print(Panel(
            logs[:3000] + ("..." if len(logs) > 3000 else ""),
            title=f"[bold yellow]🔧 WORKER OUTPUT[/bold yellow]",
            subtitle=suggestion.title[:40],
            border_style="yellow"
        ))
    
    def on_verdict(verdict: Verdict):
        console.print()
        if verdict.status == VerdictStatus.PASS:
            console.print(Panel(
                f"[bold green]✅ PASSED[/bold green] (Score: {verdict.score:.0%})\n\n{verdict.feedback}",
                title="[bold magenta]⚖️ JUDGE VERDICT[/bold magenta]",
                border_style="green"
            ))
        else:
            console.print(Panel(
                f"[bold red]❌ {verdict.status.upper()}[/bold red] (Score: {verdict.score:.0%})\n\n{verdict.feedback}\n\n[dim]Fixes: {', '.join(verdict.suggested_fixes[:3])}[/dim]",
                title="[bold magenta]⚖️ JUDGE VERDICT[/bold magenta]",
                border_style="red"
            ))
    
    # Update callbacks
    runner.on_status_change = on_status
    runner.on_implementation = on_implementation
    runner.on_verdict = on_verdict
    
    console.print()
    print_agent_output("system", f"Starting autonomous run with {len(accepted)} suggestions")
    console.print()
    
    for i, suggestion in enumerate(accepted):
        # Show suggestion header
        console.print(Panel.fit(
            f"[bold]{suggestion.title}[/bold]\n[dim]{suggestion.description[:200]}...[/dim]",
            title=f"[bold cyan]📋 Suggestion {i+1}/{len(accepted)}[/bold cyan]",
            border_style="cyan"
        ))
        
        # Run suggestion (callbacks will show progress)
        print_agent_output("worker", f"Starting implementation...")
        success = runner.run_suggestion(suggestion)
        
        # Show diff
        diff = runner.get_git_diff()
        if diff and "(No changes" not in diff:
            console.print(Panel(
                diff[:2000] + ("..." if len(diff) > 2000 else ""),
                title=f"[bold green]📝 FILE CHANGES[/bold green]",
                border_style="green" if success else "red"
            ))
        
        status_icon = "✅" if success else "❌"
        status_color = "green" if success else "red"
        console.print(f"\n[{status_color}]{status_icon} Suggestion {i+1} {'completed' if success else 'failed'}[/{status_color}]\n")
        console.print("─" * 60)
    
    print_agent_output("system", "Autonomous run complete!")


def run_autonomous_cycle(config: Optional[AutonomousConfig] = None):
    """Run the complete autonomous improvement cycle."""
    console.clear()
    print_header()
    
    if config is None:
        # Model selection
        console.print("\n[bold]Step 1: Select Model[/bold]")
        model = select_model()
        if not model:
            console.print("[yellow]Cancelled[/yellow]")
            return
        
        console.print(f"[green]✓[/green] Selected: {model}\n")
        
        # Target repo selection
        console.print("[bold]Step 2: Select Target Repository[/bold]")
        target = select_target_repo()
        if not target:
            console.print("[yellow]Cancelled[/yellow]")
            return
        
        console.print(f"[green]✓[/green] Target: {target}\n")
        
        # Target directory selection
        console.print("[bold]Step 2.5: Select Target Directory[/bold]")
        target_dir = select_target_directory(target)
        if target_dir is None:
            console.print("[yellow]Cancelled[/yellow]")
            return
            
        console.print(f"[green]✓[/green] Directory: {target_dir or '(repo root)'}\n")
        
        config = AutonomousConfig(
            target_repo=target,
            target_dir=target_dir,
            model=model,
            max_suggestions=5,
            max_iterations=3,
            verbose=True,
        )
    
    # Create runner
    runner = AutonomousRunner(config)
    
    # Generate suggestions
    console.print("\n[bold]Step 3: Generating Suggestions[/bold]")
    with console.status("[bold green]Analyzing codebase...[/bold green]"):
        suggestions = runner.generate_suggestions()
    
    if not suggestions:
        console.print("[yellow]No improvement suggestions found.[/yellow]")
        questionary.press_any_key_to_continue().ask()
        return
    
    console.print(f"[green]✓[/green] Generated {len(suggestions)} suggestions\n")
    
    # Review suggestions
    console.print("[bold]Step 4: Review Suggestions[/bold]")
    questionary.press_any_key_to_continue("Press any key to review suggestions...").ask()
    
    accepted = review_suggestions(suggestions)
    
    if not accepted:
        console.print("[yellow]No suggestions accepted.[/yellow]")
        questionary.press_any_key_to_continue().ask()
        return
    
    console.clear()
    print_header()
    console.print(f"\n[green]✓[/green] Accepted {len(accepted)} suggestions\n")
    
    # Confirm execution
    proceed = questionary.confirm(
        f"Proceed with implementing {len(accepted)} suggestions?",
        default=True
    ).ask()
    
    if not proceed:
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    # Execute with live progress
    console.print("\n[bold]Step 5: Implementing Improvements[/bold]\n")
    
    run_with_live_progress(runner, accepted)
    
    # Save run to history
    try:
        runner.save_run()
    except Exception as e:
        console.print(f"[dim]Could not save run history: {e}[/dim]")
    
    # Summary
    console.print("\n")
    show_run_summary(runner)
    show_diff(runner)
    
    questionary.press_any_key_to_continue().ask()


def show_history(config: AutonomousConfig):
    """Show run history."""
    console.clear()
    print_header()
    
    runner = AutonomousRunner(config)
    runs = runner.list_runs()
    
    if not runs:
        console.print("[yellow]No run history found.[/yellow]")
        questionary.press_any_key_to_continue().ask()
        return
    
    table = Table(title="Run History")
    table.add_column("ID", style="cyan")
    table.add_column("Status")
    table.add_column("Date")
    table.add_column("Target")
    table.add_column("Completed")
    table.add_column("Failed")
    
    for run in runs[:10]:  # Show last 10
        status_color = "green" if run["status"] == "completed" else "yellow"
        table.add_row(
            run["id"],
            f"[{status_color}]{run['status']}[/{status_color}]",
            run["started_at"][:19] if run["started_at"] else "-",
            Path(run["target_repo"]).name if run["target_repo"] else "-",
            str(run["completed"]),
            str(run["failed"]),
        )
    
    console.print(table)
    
    # Option to view details
    if questionary.confirm("View details of a run?", default=False).ask():
        run_id = questionary.text("Enter Run ID:").ask()
        if run_id:
            loaded = runner.load_run(run_id)
            if loaded:
                show_run_summary(runner)
            else:
                console.print(f"[red]Run {run_id} not found[/red]")
    
    questionary.press_any_key_to_continue().ask()


def show_settings(config: AutonomousConfig) -> AutonomousConfig:
    """Show and edit settings."""
    console.clear()
    print_header()
    
    while True:
        console.print(Panel(
            f"""[bold]Current Settings[/bold]

[dim]Model:[/dim] {config.model}
[dim]Target Directory:[/dim] {config.target_dir or '(repo root)'}
[dim]Max Suggestions:[/dim] {config.max_suggestions}
[dim]Max Iterations:[/dim] {config.max_iterations}
[dim]Context Size:[/dim] {config.num_ctx} tokens
[dim]Analysis Types:[/dim] {', '.join(config.analysis_types)}
[dim]Auto Accept:[/dim] {config.auto_accept}
[dim]Headless Mode:[/dim] {config.headless}""",
            title="Settings"
        ))
        
        action = questionary.select(
            "Edit Setting:",
            choices=[
                questionary.Choice("Change Model", value="model"),
                questionary.Choice("Change Target Directory", value="target_dir"),
                questionary.Choice("Change Max Suggestions", value="max_suggestions"),
                questionary.Choice("Change Max Iterations", value="max_iterations"),
                questionary.Choice("Change Context Size", value="num_ctx"),
                questionary.Choice("Toggle Auto Accept", value="auto_accept"),
                questionary.Choice("← Back", value="back"),
            ]
        ).ask()
        
        if action == "back" or action is None:
            break
        elif action == "model":
            new_model = select_model()
            if new_model:
                config.model = new_model
        elif action == "target_dir":
            new_dir = select_target_directory(config.target_repo)
            if new_dir is not None:
                config.target_dir = new_dir
        elif action == "max_suggestions":
            val = questionary.text("Max Suggestions (1-20):", default=str(config.max_suggestions)).ask()
            try:
                config.max_suggestions = max(1, min(20, int(val)))
            except ValueError:
                pass
        elif action == "max_iterations":
            val = questionary.text("Max Iterations (1-10):", default=str(config.max_iterations)).ask()
            try:
                config.max_iterations = max(1, min(10, int(val)))
            except ValueError:
                pass
        elif action == "num_ctx":
            val = questionary.text("Context Size:", default=str(config.num_ctx)).ask()
            try:
                config.num_ctx = max(2048, int(val))
            except ValueError:
                pass
        elif action == "auto_accept":
            config.auto_accept = not config.auto_accept
        
        console.clear()
        print_header()
    
    return config


def run_headless(config: AutonomousConfig):
    """Run in headless mode (for CI/automation)."""
    console.print("[bold]Running in headless mode...[/bold]")
    
    runner = AutonomousRunner(config)
    
    # Generate suggestions
    console.print("Generating suggestions...")
    suggestions = runner.generate_suggestions()
    
    if not suggestions:
        console.print("No suggestions generated.")
        return
    
    console.print(f"Generated {len(suggestions)} suggestions")
    
    # Auto-accept all
    for s in suggestions:
        s.status = SuggestionStatus.ACCEPTED
        console.print(f"  [green]✓[/green] {s.title}")
    
    # Run
    console.print("\nImplementing...")
    run = runner.run_all(suggestions)
    
    # Save
    try:
        runner.save_run()
    except Exception:
        pass
    
    # Summary
    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"  Completed: {run.completed_count}")
    console.print(f"  Failed: {run.failed_count}")
    
    # Exit code based on success
    if run.failed_count > 0:
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Autonomous Code Improvement CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python autonomous_cli.py                          # Interactive mode
  python autonomous_cli.py --headless               # Headless mode
  python autonomous_cli.py --target /path/to/repo   # Specify target
  python autonomous_cli.py --max-suggestions 3      # Limit suggestions
"""
    )
    parser.add_argument("--headless", action="store_true", help="Run without interactive prompts")
    parser.add_argument("--target", type=str, default=".", help="Target repository path")
    parser.add_argument("--dir", type=str, default="tests", help="Target directory within repository (default: tests)")
    parser.add_argument("--model", type=str, default="qwen2.5-coder:latest", help="Ollama model to use")
    parser.add_argument("--max-suggestions", type=int, default=5, help="Maximum suggestions to generate")
    parser.add_argument("--max-iterations", type=int, default=3, help="Maximum worker-judge iterations")
    parser.add_argument("--auto-accept", action="store_true", help="Auto-accept all suggestions")
    
    args = parser.parse_args()
    
    # Create config from args
    config = AutonomousConfig(
        target_repo=args.target,
        target_dir=args.dir,
        model=args.model,
        max_suggestions=args.max_suggestions,
        max_iterations=args.max_iterations,
        auto_accept=args.auto_accept,
        headless=args.headless,
    )
    
    # Headless mode
    if args.headless:
        run_headless(config)
        return
    
    # Interactive mode
    while True:
        console.clear()
        print_header()
        
        action = questionary.select(
            "Main Menu:",
            choices=[
                questionary.Choice("🚀 Start Autonomous Run", value="run"),
                questionary.Choice("📜 View History", value="history"),
                questionary.Choice("⚙️  Settings", value="settings"),
                questionary.Choice("❓ Help", value="help"),
                questionary.Choice("👋 Exit", value="exit"),
            ]
        ).ask()
        
        if action == "run":
            run_autonomous_cycle(config)
        elif action == "history":
            show_history(config)
        elif action == "settings":
            config = show_settings(config)
        elif action == "help":
            console.clear()
            print_header()
            console.print(Markdown("""
# Autonomous Code Improvement System

This system automatically analyzes your codebase and suggests improvements
using a **Planner → Worker → Judge** pipeline.

## How it works

1. **Planner** (LLM) scans your code and generates improvement suggestions
2. **You** review and accept/reject suggestions
3. **Worker** (OpenHands) implements accepted suggestions
4. **Judge** (LLM) verifies implementations meet criteria
5. **Diffs** are shown after each change for review
6. Worker iterates until Judge approves or max iterations reached

## CLI Features

- **Configuration Menu**: Edit model, target directory, suggestion count, iterations
- **Run History**: View and resume past runs
- **Live Progress**: Real-time status during execution
- **Diff Visualization**: See exact changes made to files
- **Headless Mode**: Use `--headless` and `--dir` for CI/automation

## Tips

- Use coding-focused models like `qwen2.5-coder` for best results
- Review suggestions carefully before accepting
- Start with small codebases to test the system

Press any key to continue...
            """))
            questionary.press_any_key_to_continue().ask()
        elif action == "exit" or action is None:
            console.print("\n[bold green]Goodbye! 👋[/bold green]")
            break


if __name__ == "__main__":
    main()

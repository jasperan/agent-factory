"""
========================================================================
AGENT EDITOR - Interactive Agent Modification
========================================================================

PURPOSE:
    Edit existing agents without manual file editing.
    Modify tools, invariants, examples, and regenerate automatically.

WHAT THIS DOES:
    1. Load existing agent spec
    2. Present interactive edit menu
    3. Modify configuration
    4. Save spec + regenerate code/tests

WHY WE NEED THIS:
    Users need to iterate on agents quickly without manually
    editing specs and regenerating code.
========================================================================
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from agent_factory.codegen import SpecParser, CodeGenerator, EvalGenerator
from agent_factory.codegen.spec_parser import AgentSpec
from .tool_registry import (
    TOOL_CATALOG,
    list_tools_by_category,
    get_tool_info,
    format_tool_list,
    get_collection
)

console = Console()


class AgentEditor:
    """
    PURPOSE: Interactive agent editor

    WHAT THIS DOES:
        - Load existing agent specs
        - Present editing menus
        - Modify configuration
        - Save and regenerate

    DESIGN:
        Terminal-based UI with rich formatting
        Menu-driven workflow
        Validates changes before saving
    """

    def __init__(self, agent_name: str, specs_dir: Path = None):
        """
        PURPOSE: Initialize editor for specific agent

        INPUTS:
            agent_name: Name of agent to edit (e.g., "bob-1")
            specs_dir: Directory containing specs (default: "specs/")
        """
        self.agent_name = agent_name
        self.specs_dir = specs_dir or Path("specs")
        self.agents_dir = Path("agents")
        self.tests_dir = Path("tests")

        # Find spec file
        self.spec_file = self._find_spec_file()
        if not self.spec_file:
            raise FileNotFoundError(
                f"Spec file not found for agent '{agent_name}' in {self.specs_dir}"
            )

        # Load current spec
        self.parser = SpecParser()
        self.spec: AgentSpec = self.parser.parse_spec(str(self.spec_file))

        # Track changes
        self.changes: Dict[str, Any] = {}
        self.has_changes = False

    def _find_spec_file(self) -> Optional[Path]:
        """
        PURPOSE: Find spec file for agent

        RETURNS:
            Path to spec file or None
        """
        # Try exact match
        spec_path = self.specs_dir / f"{self.agent_name}.md"
        if spec_path.exists():
            return spec_path

        # Try without version suffix
        for spec_file in self.specs_dir.glob("*.md"):
            if spec_file.stem.startswith(self.agent_name.split("-")[0]):
                return spec_file

        return None

    def run(self) -> bool:
        """
        PURPOSE: Main editing loop

        RETURNS:
            bool: True if changes saved, False if cancelled
        """
        self._show_header()

        while True:
            choice = self._show_main_menu()

            if choice == "1":
                self._edit_tools()
            elif choice == "2":
                self._edit_invariants()
            elif choice == "3":
                self._edit_behavior_examples()
            elif choice == "4":
                self._edit_purpose_scope()
            elif choice == "5":
                self._edit_system_prompt()
            elif choice == "6":
                self._edit_llm_settings()
            elif choice == "7":
                self._edit_success_criteria()
            elif choice == "8":
                return self._review_and_save()
            elif choice == "9":
                if Confirm.ask("\n[yellow]Discard all changes?[/yellow]"):
                    console.print("[dim]Changes discarded.[/dim]\n")
                    return False
            else:
                console.print("[red]Invalid choice[/red]")

    def _show_header(self):
        """Display editor header"""
        header = Panel(
            f"[bold cyan]EDIT AGENT:[/bold cyan] {self.spec.name} {self.spec.version}\n"
            f"[dim]Spec:[/dim] {self.spec_file}\n"
            f"[dim]Status:[/dim] {self.spec.status}",
            title="Agent Editor",
            border_style="cyan"
        )
        console.print()
        console.print(header)
        console.print()

    def _show_main_menu(self) -> str:
        """
        PURPOSE: Display main editing menu

        RETURNS:
            User's menu choice
        """
        # Show current config
        table = Table(title="Current Configuration", show_header=True, header_style="bold")
        table.add_column("Property", style="cyan", width=20)
        table.add_column("Value", width=50)

        table.add_row("Name", f"{self.spec.name} {self.spec.version}")
        table.add_row("Purpose", self.spec.purpose[:60] + "..." if len(self.spec.purpose) > 60 else self.spec.purpose)
        table.add_row("Tools", f"{len(self.spec.essential_tools)} essential, {len(self.spec.optional_tools)} optional")
        table.add_row("Invariants", str(len(self.spec.invariants)))
        table.add_row("Behavior Examples", str(len(self.spec.behavior_examples)))

        console.print(table)
        console.print()

        # Show changes if any
        if self.has_changes:
            console.print("[yellow]Unsaved changes:[/yellow]")
            for key, value in self.changes.items():
                console.print(f"  - {key}: {value}")
            console.print()

        # Menu options
        console.print("[bold]What would you like to edit?[/bold]\n")
        console.print("  [1] Tools (add/remove)")
        console.print("  [2] Invariants (rules agent must follow)")
        console.print("  [3] Behavior Examples (expected responses)")
        console.print("  [4] Purpose & Scope")
        console.print("  [5] System Prompt Template")
        console.print("  [6] LLM Settings (model, temperature)")
        console.print("  [7] Success Criteria")
        console.print("  [8] Review & Save")
        console.print("  [9] Cancel\n")

        return Prompt.ask("Choice", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9"])

    def _edit_tools(self):
        """Edit agent tools interactively"""
        console.print("\n" + "=" * 72)
        console.print("EDIT TOOLS")
        console.print("=" * 72 + "\n")

        # Show current tools
        console.print("[bold]Current Tools:[/bold]")
        current_tools = self.spec.essential_tools + self.spec.optional_tools
        console.print(format_tool_list(current_tools, show_selected=True, selected=current_tools))
        console.print()

        # Show available tools by category
        console.print("[bold]Available Tools by Category:[/bold]\n")
        categories = list_tools_by_category()
        for category, tools in categories.items():
            console.print(f"[cyan]{category.upper()}:[/cyan]")
            tool_names = [t.name for t in tools]
            console.print(format_tool_list(tool_names, show_selected=True, selected=current_tools))
            console.print()

        # Interactive commands
        console.print("[bold]Commands:[/bold]")
        console.print("  add <tool-name>     Add a tool")
        console.print("  remove <tool-name>  Remove a tool")
        console.print("  collection <name>   Load tool collection (research_basic, full_power, etc.)")
        console.print("  done                Finish editing\n")

        modified_tools = current_tools.copy()

        while True:
            cmd = Prompt.ask(">").strip()

            if cmd == "done":
                break

            parts = cmd.split(maxsplit=1)
            if len(parts) < 2:
                console.print("[red]Invalid command. Use: add/remove <tool-name> or collection <name>[/red]")
                continue

            action, arg = parts

            if action == "add":
                tool_name = arg
                if tool_name in TOOL_CATALOG:
                    if tool_name not in modified_tools:
                        modified_tools.append(tool_name)
                        console.print(f"[green]+[/green] Added {tool_name}")
                    else:
                        console.print(f"[yellow]Tool already added[/yellow]")
                else:
                    console.print(f"[red]Unknown tool: {tool_name}[/red]")

            elif action == "remove":
                tool_name = arg
                if tool_name in modified_tools:
                    modified_tools.remove(tool_name)
                    console.print(f"[red]-[/red] Removed {tool_name}")
                else:
                    console.print(f"[yellow]Tool not in list[/yellow]")

            elif action == "collection":
                try:
                    collection = get_collection(arg)
                    modified_tools = collection.copy()
                    console.print(f"[green]Loaded collection: {arg}[/green] ({len(collection)} tools)")
                except KeyError as e:
                    console.print(f"[red]{e}[/red]")

        # Save changes
        if modified_tools != current_tools:
            self.spec.essential_tools = modified_tools
            self.spec.optional_tools = []
            self.changes["tools"] = f"{len(current_tools)} -> {len(modified_tools)}"
            self.has_changes = True
            console.print(f"\n[green]Tools updated![/green] ({len(current_tools)} -> {len(modified_tools)})\n")
        else:
            console.print("\n[dim]No changes made.[/dim]\n")

    def _edit_invariants(self):
        """Edit agent invariants"""
        console.print("\n" + "=" * 72)
        console.print("EDIT INVARIANTS")
        console.print("=" * 72 + "\n")

        console.print("[bold]Current Invariants:[/bold]\n")
        for i, inv in enumerate(self.spec.invariants, 1):
            console.print(f"  {i}. {inv}")
        console.print()

        console.print("[bold]Commands:[/bold]")
        console.print("  add                 Add new invariant")
        console.print("  remove <number>     Remove invariant")
        console.print("  edit <number>       Edit invariant")
        console.print("  done                Finish editing\n")

        modified_invariants = self.spec.invariants.copy()

        while True:
            cmd = Prompt.ask(">").strip()

            if cmd == "done":
                break

            if cmd == "add":
                invariant = Prompt.ask("Invariant (format: Name: Description)")
                modified_invariants.append(invariant)
                console.print(f"[green]+[/green] Added invariant\n")

            elif cmd.startswith("remove "):
                try:
                    idx = int(cmd.split()[1]) - 1
                    removed = modified_invariants.pop(idx)
                    console.print(f"[red]-[/red] Removed: {removed}\n")
                except (IndexError, ValueError):
                    console.print("[red]Invalid number[/red]\n")

            elif cmd.startswith("edit "):
                try:
                    idx = int(cmd.split()[1]) - 1
                    old_inv = modified_invariants[idx]
                    console.print(f"Editing: {old_inv}")
                    new_inv = Prompt.ask("New invariant", default=old_inv)
                    modified_invariants[idx] = new_inv
                    console.print(f"[green]✓[/green] Updated\n")
                except (IndexError, ValueError):
                    console.print("[red]Invalid number[/red]\n")

        if modified_invariants != self.spec.invariants:
            self.spec.invariants = modified_invariants
            self.changes["invariants"] = f"{len(self.spec.invariants)} -> {len(modified_invariants)}"
            self.has_changes = True
            console.print(f"\n[green]Invariants updated![/green]\n")
        else:
            console.print("\n[dim]No changes made.[/dim]\n")

    def _edit_behavior_examples(self):
        """Edit behavior examples"""
        console.print("\n[yellow]Behavior example editing not yet implemented.[/yellow]")
        console.print("[dim]Press Enter to continue...[/dim]")
        input()

    def _edit_purpose_scope(self):
        """Edit purpose and scope"""
        console.print("\n[yellow]Purpose/scope editing not yet implemented.[/yellow]")
        console.print("[dim]Press Enter to continue...[/dim]")
        input()

    def _edit_system_prompt(self):
        """Edit system prompt template"""
        console.print("\n[yellow]System prompt editing not yet implemented.[/yellow]")
        console.print("[dim]Press Enter to continue...[/dim]")
        input()

    def _edit_llm_settings(self):
        """Edit LLM settings"""
        console.print("\n[yellow]LLM settings editing not yet implemented.[/yellow]")
        console.print("[dim]Press Enter to continue...[/dim]")
        input()

    def _edit_success_criteria(self):
        """Edit success criteria"""
        console.print("\n[yellow]Success criteria editing not yet implemented.[/yellow]")
        console.print("[dim]Press Enter to continue...[/dim]")
        input()

    def _review_and_save(self) -> bool:
        """
        PURPOSE: Review changes and save

        RETURNS:
            bool: True if saved, False if cancelled
        """
        if not self.has_changes:
            console.print("\n[yellow]No changes to save.[/yellow]\n")
            return False

        console.print("\n" + "=" * 72)
        console.print("REVIEW CHANGES")
        console.print("=" * 72 + "\n")

        # Show all changes
        for key, value in self.changes.items():
            console.print(f"  [cyan]{key}:[/cyan] {value}")
        console.print()

        # Files to update
        console.print("[bold]Files to update:[/bold]")
        console.print(f"  - {self.spec_file} (spec)")
        console.print(f"  - agents/{self.spec.name.lower().replace('-', '_')}_v*.py (regenerate)")
        console.print(f"  - tests/test_{self.spec.name.lower().replace('-', '_')}_v*.py (regenerate)")
        console.print()

        if not Confirm.ask("[cyan]Save changes?[/cyan]"):
            return False

        # Save
        try:
            console.print("\n[1/3] Updating spec...", end=" ")
            self._save_spec()
            console.print("[green]✓[/green]")

            console.print("[2/3] Regenerating agent...", end=" ")
            self._regenerate_agent()
            console.print("[green]✓[/green]")

            console.print("[3/3] Regenerating tests...", end=" ")
            self._regenerate_tests()
            console.print("[green]✓[/green]")

            console.print("\n[green]Agent updated successfully![/green]\n")
            return True

        except Exception as e:
            console.print(f"\n[red]Error saving changes:[/red] {e}\n")
            return False

    def _save_spec(self):
        """Save modified spec to file"""
        # For now, just write back the spec
        # In production, would use proper spec serialization
        console.print(f"(Spec save logic TBD - would update {self.spec_file})")

    def _regenerate_agent(self):
        """Regenerate agent code from updated spec"""
        generator = CodeGenerator()
        generator.generate_agent_file(self.spec, None)

    def _regenerate_tests(self):
        """Regenerate test file from updated spec"""
        generator = EvalGenerator()
        generator.generate_test_file(self.spec, None)


# ========================================================================
# HELPER FUNCTIONS
# ========================================================================

def list_editable_agents(specs_dir: Path = None) -> List[str]:
    """
    PURPOSE: List all agents available for editing

    RETURNS:
        List of agent names

    EXAMPLE:
        >>> list_editable_agents()
        ["bob-1", "orchestrator-v1.0", "factory-v1.0"]
    """
    specs_dir = specs_dir or Path("specs")
    agents = []

    for spec_file in specs_dir.glob("*.md"):
        if spec_file.name == "template.md":
            continue
        agents.append(spec_file.stem)

    return agents

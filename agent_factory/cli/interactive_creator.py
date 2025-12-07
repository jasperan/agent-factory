"""
========================================================================
INTERACTIVE AGENT CREATOR - Guided Agent Creation Wizard
========================================================================

PURPOSE:
    Interactive CLI wizard that guides users through creating agents
    by asking questions and generating complete specs + code.

WHAT THIS DOES:
    1. Ask questions about agent (name, purpose, scope, etc.)
    2. Let user select tools from available options
    3. Guide creation of behavior examples
    4. Generate complete spec markdown file
    5. Auto-build agent + tests from generated spec

FEATURES (NEW):
    - Navigate back/forward through steps
    - Help menu accessible at any time
    - Safe exit with draft saving
    - Resume from saved drafts
    - Progress indicators
    - Auto-save functionality

WHY WE NEED THIS:
    Makes agent creation accessible to non-technical users.
    Works with human or LLM assistance.
    No need to manually write spec files.

USAGE:
    creator = InteractiveAgentCreator()
    creator.run()  # Starts interactive session

PLC ANALOGY:
    Like a PLC wizard that guides you through configuring
    a new control program step-by-step with validation.
========================================================================
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import json
import re
import sys

from agent_factory.codegen import SpecParser, CodeGenerator, EvalGenerator
from .templates import get_template, list_templates, AgentTemplate
from .wizard_state import WizardState


class NavigationCommand(Exception):
    """
    PURPOSE: Signal navigation command (not an error)

    WHAT THIS IS:
        Exception used for control flow to signal
        navigation commands like 'back', 'goto', etc.

    USAGE:
        raise NavigationCommand("back")
        raise NavigationCommand("goto", 3)
    """
    def __init__(self, command: str, *args):
        self.command = command
        self.args = args
        super().__init__(f"{command} {args}")


class ExitWizardException(Exception):
    """
    PURPOSE: Signal wizard exit request

    USAGE:
        raise ExitWizardException()
    """
    pass


class InteractiveAgentCreator:
    """
    PURPOSE: Interactive wizard for creating agents

    WHAT THIS DOES:
        - Prompts user for agent details
        - Validates inputs
        - Generates spec file
        - Builds agent + tests
        - Handles navigation and state management

    FLOW:
        1. Agent basics (name, purpose)
        2. Scope (in/out)
        3. Invariants
        4. Tool selection
        5. Behavior examples
        6. Success criteria
        7. Review & confirm
        8. Generate files
    """

    def __init__(self):
        """Initialize creator"""
        self.state = WizardState()
        self.available_tools = self._discover_tools()
        self._auto_save_enabled = True

    def run(self, template_name: Optional[str] = None) -> bool:
        """
        PURPOSE: Run the interactive creation wizard

        INPUTS:
            template_name (str, optional): Start with a template

        OUTPUTS:
            bool: True if agent created successfully

        FLOW:
            - Check for drafts to resume
            - Load template if specified
            - Run wizard loop with navigation
            - Generate agent
        """
        print("=" * 72)
        print("AGENT FACTORY - INTERACTIVE AGENT CREATOR")
        print("=" * 72)
        print()
        self._show_welcome()

        # Check for existing drafts
        if not template_name:
            if not self._check_resume_draft():
                return False

        # Load template if specified
        if template_name:
            try:
                template = get_template(template_name)
                print(f"Starting with template: {template.description}")
                print()
                self._load_from_template(template)
            except KeyError as e:
                print(f"Error: {e}")
                return False

        # Run wizard with navigation
        try:
            return self._run_wizard_loop()

        except ExitWizardException:
            return self._handle_exit()

        except KeyboardInterrupt:
            print("\n")
            return self._handle_exit()

        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _show_welcome(self):
        """Show welcome message with command hints"""
        print("Welcome! This wizard will guide you through creating a custom agent.")
        print()
        print("Available commands (type at any prompt):")
        print("  help, ?          - Show all commands")
        print("  back, b          - Go to previous step")
        print("  next, n          - Skip to next step")
        print("  goto <N>         - Jump to step N (1-7)")
        print("  status           - Show current progress")
        print("  save [file]      - Save draft")
        print("  exit, quit, q    - Exit (will prompt to save)")
        print()
        print("-" * 72)
        print()

    def _check_resume_draft(self) -> bool:
        """
        PURPOSE: Check for existing drafts and offer to resume

        OUTPUTS:
            bool: True to continue, False to cancel
        """
        drafts = WizardState.list_drafts()

        if not drafts:
            return True  # No drafts, continue normally

        print("Found existing draft(s):")
        print()

        for i, draft in enumerate(drafts[:5], 1):  # Show max 5 most recent
            print(f"  [{i}] {draft['agent_name']}")
            print(f"      Progress: {draft['progress']}% (Step {draft['current_step']}/7)")
            print(f"      Last updated: {draft['updated_at']}")
            print()

        print("  [N] Start new agent")
        print()

        while True:
            choice = input("Resume a draft or start new? [1-5/N]: ").strip().lower()

            if choice == 'n' or choice == '':
                return True  # Start new

            try:
                idx = int(choice) - 1
                if 0 <= idx < min(len(drafts), 5):
                    # Load the selected draft
                    draft_path = drafts[idx]["path"]
                    self.state = WizardState.load_draft(draft_path)
                    print(f"\n[OK] Resumed draft: {draft_path}")
                    print()
                    return True
            except ValueError:
                pass

            print("  [!] Please enter 1-5 or N")

    def _run_wizard_loop(self) -> bool:
        """
        PURPOSE: Main wizard loop with navigation

        OUTPUTS:
            bool: True if successful, False if cancelled

        FLOW:
            Loop through steps allowing navigation
            Handle back/next/goto commands
            Auto-save after each step
        """
        step_methods = [
            self._ask_basics,
            self._ask_scope_in,
            self._ask_scope_out,
            self._ask_invariants,
            self._ask_tools,
            self._ask_behavior_examples,
            self._ask_success_criteria,
        ]

        while True:
            step_num = self.state.current_step

            # Check if we've completed all steps
            if step_num > len(step_methods):
                # Go to review
                if self._review_and_confirm():
                    return self._generate_agent()
                else:
                    print("\nAgent creation cancelled.")
                    return False

            # Run current step
            try:
                self._show_progress()
                step_methods[step_num - 1]()

                # Mark step complete and move to next
                self.state.mark_step_complete(step_num)
                self.state.set_current_step(step_num + 1)

                # Auto-save after each step
                if self._auto_save_enabled:
                    draft_path = self.state.save_draft()
                    print(f"  [Auto-saved to {draft_path}]")

            except NavigationCommand as nav:
                self._handle_navigation(nav)

    def _handle_navigation(self, nav: NavigationCommand):
        """
        PURPOSE: Handle navigation commands

        INPUTS:
            nav: NavigationCommand with command and args
        """
        cmd = nav.command.lower()

        if cmd == "back":
            if self.state.current_step > 1:
                self.state.set_current_step(self.state.current_step - 1)
                print(f"\n→ Going back to Step {self.state.current_step}\n")
            else:
                print("\n[!] Already at first step\n")

        elif cmd == "next":
            if self.state.current_step < 7:
                self.state.set_current_step(self.state.current_step + 1)
                print(f"\n→ Skipping to Step {self.state.current_step}\n")
            else:
                print("\n[!] Already at last step\n")

        elif cmd == "goto":
            target = nav.args[0] if nav.args else None
            if target and 1 <= target <= 7:
                self.state.set_current_step(target)
                print(f"\n→ Jumping to Step {target}\n")
            else:
                print(f"\n[!] Invalid step number. Use 1-7.\n")

        elif cmd == "restart":
            confirm = input("Restart wizard from beginning? (y/n): ").strip().lower()
            if confirm == 'y':
                self.state = WizardState()
                print("\n→ Restarting wizard...\n")

    def _handle_exit(self) -> bool:
        """
        PURPOSE: Handle exit request with save prompt

        OUTPUTS:
            bool: False (wizard was cancelled)
        """
        print("\nExiting wizard...")
        print()

        if self.state.spec_data:
            # Has some data, offer to save
            save = input("Save draft before exiting? (y/n/cancel): ").strip().lower()

            if save == 'cancel' or save == 'c':
                print("Exit cancelled. Continuing wizard...\n")
                return self._run_wizard_loop()  # Resume

            elif save == 'y':
                draft_path = self.state.save_draft()
                print(f"\n[OK] Draft saved to: {draft_path}")
                print(f"Resume later by running: agentcli create")
                print()

            else:
                print("\n[!] Progress not saved.")

        print("Wizard cancelled.")
        return False

    def _get_input(
        self,
        prompt: str,
        current_value: Optional[Any] = None,
        allow_empty: bool = False,
        multiline: bool = False
    ) -> str:
        """
        PURPOSE: Get user input with command handling

        INPUTS:
            prompt: str - Prompt to display
            current_value: Any - Current value (shown if re-visiting step)
            allow_empty: bool - Allow empty input
            multiline: bool - Allow multi-line input

        OUTPUTS:
            str: User input

        SIDE EFFECTS:
            May raise NavigationCommand or ExitWizardException

        COMMANDS HANDLED:
            help, ?, back, next, goto, status, save, exit, quit
        """
        # Show current value if present
        if current_value is not None:
            print(f"  (current: {current_value})")

        # Get input
        if multiline:
            print(f"{prompt} (press Ctrl+D or Ctrl+Z when done):")
            lines = []
            try:
                while True:
                    line = input()
                    lines.append(line)
            except EOFError:
                pass
            user_input = "\n".join(lines).strip()
        else:
            user_input = input(prompt).strip()

        # Check for commands
        cmd_lower = user_input.lower()

        # Help commands
        if cmd_lower in ['help', '?']:
            self._show_help()
            return self._get_input(prompt, current_value, allow_empty, multiline)

        # Navigation commands
        elif cmd_lower in ['back', 'b']:
            raise NavigationCommand("back")

        elif cmd_lower in ['next', 'n']:
            raise NavigationCommand("next")

        elif cmd_lower.startswith('goto '):
            try:
                step_num = int(cmd_lower.split()[1])
                raise NavigationCommand("goto", step_num)
            except (ValueError, IndexError):
                print("[!] Usage: goto <step number>")
                return self._get_input(prompt, current_value, allow_empty, multiline)

        elif cmd_lower == 'restart':
            raise NavigationCommand("restart")

        # Info commands
        elif cmd_lower == 'status':
            self._show_status()
            return self._get_input(prompt, current_value, allow_empty, multiline)

        elif cmd_lower == 'list-templates':
            self._list_templates()
            return self._get_input(prompt, current_value, allow_empty, multiline)

        elif cmd_lower == 'list-tools':
            self._list_tools()
            return self._get_input(prompt, current_value, allow_empty, multiline)

        # State commands
        elif cmd_lower.startswith('save'):
            parts = user_input.split(maxsplit=1)
            filepath = parts[1] if len(parts) > 1 else None
            draft_path = self.state.save_draft(filepath)
            print(f"[OK] Draft saved to: {draft_path}")
            return self._get_input(prompt, current_value, allow_empty, multiline)

        elif cmd_lower.startswith('load '):
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                filepath = parts[1]
                try:
                    self.state = WizardState.load_draft(filepath)
                    print(f"[OK] Loaded draft from: {filepath}")
                except FileNotFoundError:
                    print(f"[!] Draft not found: {filepath}")
            else:
                print("[!] Usage: load <filename>")
            return self._get_input(prompt, current_value, allow_empty, multiline)

        # Exit commands
        elif cmd_lower in ['exit', 'quit', 'q']:
            raise ExitWizardException()

        # Regular input
        if not user_input and not allow_empty:
            print("[!] Input required. Type 'help' for commands.")
            return self._get_input(prompt, current_value, allow_empty, multiline)

        return user_input

    def _show_help(self):
        """Show help menu"""
        print()
        print("=" * 72)
        print("AVAILABLE COMMANDS")
        print("=" * 72)
        print()
        print("Navigation:")
        print("  back, b          - Go to previous step")
        print("  next, n          - Skip to next step")
        print("  goto <N>         - Jump to step N (1-7)")
        print("  restart          - Start over from beginning")
        print()
        print("Information:")
        print("  help, ?          - Show this help")
        print("  status           - Show current progress and data")
        print("  list-templates   - Show available agent templates")
        print("  list-tools       - Show available tools")
        print()
        print("State Management:")
        print("  save [file]      - Save draft (auto-names if no file specified)")
        print("  load <file>      - Load draft from file")
        print()
        print("Exit:")
        print("  exit, quit, q    - Exit wizard (will prompt to save)")
        print("  Ctrl+C           - Interrupt (will prompt to save)")
        print()
        print("=" * 72)
        print()

    def _show_status(self):
        """Show current wizard status"""
        print()
        print("=" * 72)
        print("WIZARD STATUS")
        print("=" * 72)
        print()
        print(self.state.get_summary())
        print()
        print("=" * 72)
        print()

    def _list_templates(self):
        """List available templates"""
        print()
        print("Available Templates:")
        for template in list_templates():
            print(f"  - {template['name']}: {template['description']}")
        print()

    def _list_tools(self):
        """List available tools"""
        print()
        print("Available Tools by Category:")
        print()
        for category, tools in self.available_tools.items():
            print(f"{category}:")
            for tool in tools:
                print(f"  - {tool}")
            print()

    def _show_progress(self):
        """Show progress indicator"""
        step = self.state.current_step
        total = 7  # Only 7 data collection steps (step 8 is review)

        if step > 7:
            # Review phase - show as complete
            filled = "●" * 7
            bar = f"[{filled}]"
            print(f"{bar} Review & Confirm")
        else:
            # Progress bar: [●●●○○○○]
            filled = "●" * (step - 1)
            empty = "○" * (total - step + 1)
            bar = f"[{filled}{empty}]"

            step_name = self.state.get_step_name(step).replace("_", " ").title()
            print(f"{bar} Step {step} of {total}: {step_name}")

        print("-" * 72)
        print()

    def _clean_list_item(self, text: str) -> str:
        """
        PURPOSE: Clean pasted list items (remove bullets, numbers, etc.)

        INPUTS:
            text: Raw line from paste

        OUTPUTS:
            str: Cleaned text

        CLEANING RULES:
            - Strip whitespace
            - Remove leading bullets: -, *, •, ├──, └──, │
            - Remove leading numbers: 1., 2), etc.
            - Remove checkboxes: [ ], [x], ✓
        """
        text = text.strip()

        if not text:
            return ""

        # Remove leading bullets and tree characters
        bullets = ['- ', '* ', '• ', '├──', '└──', '│ ', '├─', '└─']
        for bullet in bullets:
            if text.startswith(bullet):
                text = text[len(bullet):].strip()

        # Remove leading numbers: "1. ", "2) ", etc.
        import re
        text = re.sub(r'^\d+[\.\)]\s+', '', text)

        # Remove checkboxes
        text = re.sub(r'^\[[ x]\]\s*', '', text)
        text = re.sub(r'^[✓✗]\s*', '', text)

        # Remove emoji checkmarks at start
        if text.startswith('✅ ') or text.startswith('❌ '):
            text = text[2:].strip()

        return text.strip()

    def _get_list_input(
        self,
        item_name: str,
        current_list: List[str],
        prompt_prefix: str = "  + ",
        example: Optional[str] = None,
        allow_empty_items: bool = False
    ) -> List[str]:
        """
        PURPOSE: Get list input with smart paste detection

        INPUTS:
            item_name: Name of items being collected (e.g., "capability", "restriction")
            current_list: Existing items
            prompt_prefix: Prefix for input prompt (e.g., "  + ", "  - ")
            example: Example item to show user
            allow_empty_items: Whether empty items are allowed

        OUTPUTS:
            List[str]: Updated list with new items

        FEATURES:
            - Detects multi-line paste
            - Cleans bullet points, numbers, etc.
            - Shows confirmation for pasted content
            - Visual feedback for each item added
        """
        print(f"Add {item_name}s (one per line, or paste multiple lines):")
        if example:
            print(f"  Example: \"{example}\"")
        print()
        print(f"  [Currently: {len(current_list)} {item_name}(s)]")
        print(f"  (Press Enter on empty line when done, or type 'back' to go back)")
        print()

        new_items = []

        while True:
            try:
                # Try to detect if there's a paste coming
                # by reading input with a short timeout
                import sys
                import select

                # Prompt for input
                user_input = self._get_input(prompt_prefix, allow_empty=True)

                if not user_input:
                    # Empty input - user is done
                    break

                # Clean the input
                cleaned = self._clean_list_item(user_input)

                if cleaned:
                    new_items.append(cleaned)
                    current_list.append(cleaned)
                    print(f"    [+] Added: {cleaned[:60]}{'...' if len(cleaned) > 60 else ''}")
                    print()

            except NavigationCommand:
                # User wants to navigate - re-raise
                raise

        # Summary
        if new_items:
            print(f"  [Added {len(new_items)} new {item_name}(s). Total: {len(current_list)}]")
            print()

        return current_list

    def _discover_tools(self) -> Dict[str, List[str]]:
        """
        PURPOSE: Discover available tools from agent_factory/tools

        OUTPUTS:
            Dict of {category: [tool_names]}
        """
        return {
            "Research": [
                "WikipediaSearchTool - Search Wikipedia",
                "DuckDuckGoSearchTool - Web search",
                "TavilySearchTool - Advanced web search",
                "CurrentTimeTool - Get current time/date",
            ],
            "File Operations": [
                "ReadFileTool - Read file contents",
                "WriteFileTool - Write to files",
                "ListDirectoryTool - List directory",
                "FileSearchTool - Search in files",
            ],
            "Code Tools": [
                "GitStatusTool - Check git status",
            ],
        }

    def _load_from_template(self, template: AgentTemplate):
        """Load spec data from template"""
        data = template.to_dict()
        self.state.set_data("purpose", data["purpose"])
        self.state.set_data("scope_in", data["scope_in"][:])
        self.state.set_data("scope_out", data["scope_out"][:])
        self.state.set_data("invariants", data["invariants"][:])
        self.state.set_data("tools", data["tools"][:])
        self.state.set_data("behavior_examples", data["behavior_examples"][:])
        self.state.set_data("success_criteria", data["success_criteria"].copy())

    # ========================================================================
    # STEP METHODS (Updated to use _get_input)
    # ========================================================================

    def _ask_basics(self):
        """Ask for basic agent information"""
        print()
        print("=" * 72)
        print("AGENT BASICS")
        print("=" * 72)
        print()
        print("Enter basic agent information.")
        print("(Type 'help' for commands, 'back' to go back, 'exit' to quit)")
        print()

        # Name
        if not self.state.has_data("name"):
            name = self._get_input("Agent name: ")
            self.state.set_data("name", name)
        else:
            current = self.state.get_data("name")
            print(f"  (Current: {current})")
            name = self._get_input("Agent name (or press Enter to keep current): ", allow_empty=True)
            if name:
                self.state.set_data("name", name)

        # Version
        current_version = self.state.get_data("version", "v1.0")
        version = self._get_input(f"Version [default: {current_version}]: ", allow_empty=True)
        if not version:
            version = current_version
        self.state.set_data("version", version)

        # Owner
        current_owner = self.state.get_data("owner", "Anonymous")
        owner = self._get_input(f"Owner/Author [default: {current_owner}]: ", allow_empty=True)
        if not owner:
            owner = current_owner
        self.state.set_data("owner", owner)

        # Purpose (if not from template)
        if not self.state.has_data("purpose"):
            print("\nPurpose - Why this agent exists (one line):")
            print("  Example: \"Helps users find accurate technical information quickly\"")
            purpose = self._get_input("> ")
            self.state.set_data("purpose", purpose)
        else:
            current_purpose = self.state.get_data("purpose")
            print(f"\nCurrent purpose: {current_purpose}")
            print("Keep this purpose? (y/n): ", end="")
            keep = self._get_input("", allow_empty=True).lower()
            if keep == 'n':
                purpose = self._get_input("New purpose: ")
                self.state.set_data("purpose", purpose)

        print()

    def _ask_scope_in(self):
        """Ask about scope - what agent CAN do"""
        print()
        print("=" * 72)
        print("CAPABILITIES - What CAN this agent do?")
        print("=" * 72)
        print()

        if not self.state.has_data("scope_in"):
            self.state.set_data("scope_in", [])

        scope_in = self.state.get_data("scope_in")

        # Show existing
        if scope_in:
            print("Current capabilities:")
            for i, item in enumerate(scope_in, 1):
                print(f"  {i}. {item}")
            print()

        # Add more using improved list input
        try:
            self._get_list_input(
                item_name="capability",
                current_list=scope_in,
                prompt_prefix="  + ",
                example="Search web sources for technical information"
            )
        except NavigationCommand:
            raise

        print()

    def _ask_scope_out(self):
        """Ask about scope - what agent should NEVER do"""
        print()
        print("=" * 72)
        print("RESTRICTIONS - What should this agent NEVER do?")
        print("=" * 72)
        print()

        if not self.state.has_data("scope_out"):
            self.state.set_data("scope_out", [])

        scope_out = self.state.get_data("scope_out")

        # Show existing
        if scope_out:
            print("Current restrictions:")
            for i, item in enumerate(scope_out, 1):
                print(f"  {i}. {item}")
            print()

        # Add more using improved list input
        try:
            self._get_list_input(
                item_name="restriction",
                current_list=scope_out,
                prompt_prefix="  - ",
                example="Make up information when sources are unavailable"
            )
        except NavigationCommand:
            raise

        print()

    def _ask_invariants(self):
        """Ask about invariants (rules that must never be violated)"""
        print()
        print("=" * 72)
        print("INVARIANTS - Rules that MUST NEVER be violated")
        print("=" * 72)
        print()

        if not self.state.has_data("invariants"):
            self.state.set_data("invariants", [])

        invariants = self.state.get_data("invariants")

        # Show existing
        if invariants:
            print("Current invariants:")
            for i, inv in enumerate(invariants, 1):
                print(f"  {i}. {inv['name']}: {inv['description']}")
            print()

        # Add more
        print("Add invariants (one per line, or paste multiple lines):")
        print("  Format: Name: Description")
        print("  Example: \"Accuracy First: Never fabricate sources or citations\"")
        print()
        print(f"  [Currently: {len(invariants)} invariant(s)]")
        print(f"  (Press Enter on empty line when done, or type 'back' to go back)")
        print()

        new_items = []

        while True:
            try:
                invariant = self._get_input("  > ", allow_empty=True)
                if not invariant:
                    break

                # Clean the input
                invariant = self._clean_list_item(invariant)

                if not invariant:
                    continue

                # Parse "Name: Description"
                if ":" in invariant:
                    parts = invariant.split(":", 1)
                    inv_obj = {
                        "name": parts[0].strip(),
                        "description": parts[1].strip()
                    }
                else:
                    inv_obj = {
                        "name": invariant,
                        "description": ""
                    }

                invariants.append(inv_obj)
                new_items.append(inv_obj)
                print(f"    [+] Added: {inv_obj['name']}")
                print()

            except NavigationCommand:
                raise

        # Summary
        if new_items:
            print(f"  [Added {len(new_items)} new invariant(s). Total: {len(invariants)}]")
            print()

        print()

    def _ask_tools(self):
        """Ask user to select tools"""
        print()
        print("=" * 72)
        print("TOOL SELECTION")
        print("=" * 72)
        print()

        if not self.state.has_data("tools"):
            self.state.set_data("tools", [])

        tools = self.state.get_data("tools")

        # Show existing
        if tools:
            print(f"Currently selected tools ({len(tools)}):")
            for i, tool in enumerate(tools, 1):
                print(f"  {i}. {tool}")
            print()

        # Show available tools
        print("Available tools by category:")
        print()
        tool_index = 1
        index_to_tool = {}

        for category, tool_list in self.available_tools.items():
            print(f"{category}:")
            for tool_desc in tool_list:
                tool_name = tool_desc.split(" - ")[0]
                print(f"  [{tool_index}] {tool_desc}")
                index_to_tool[tool_index] = tool_name
                tool_index += 1
            print()

        # Let user select
        print("Select tools by number (comma-separated, e.g., 1,2,5)")
        selection = self._get_input(
            "Tools to add (or press Enter to keep current): ",
            allow_empty=True
        )

        if selection:
            added = []
            selected_indices = [int(x.strip()) for x in selection.split(",") if x.strip().isdigit()]
            for idx in selected_indices:
                if idx in index_to_tool:
                    tool_name = index_to_tool[idx]
                    if tool_name not in tools:
                        tools.append(tool_name)
                        added.append(tool_name)
                        print(f"    [+] Added: {tool_name}")

            if added:
                print()
                print(f"  [Added {len(added)} tool(s). Total: {len(tools)}]")

        print()

    def _ask_behavior_examples(self):
        """Ask for behavior examples"""
        print()
        print("=" * 72)
        print("BEHAVIOR EXAMPLES")
        print("=" * 72)
        print()

        if not self.state.has_data("behavior_examples"):
            self.state.set_data("behavior_examples", [])

        examples = self.state.get_data("behavior_examples")

        # Show existing
        if examples:
            correct = [ex for ex in examples if ex['category'] == 'clearly_correct']
            wrong = [ex for ex in examples if ex['category'] == 'clearly_wrong']
            print(f"Existing examples: {len(correct)} correct, {len(wrong)} wrong")
            print()

        print("Behavior examples help define what the agent should (and shouldn't) do.")
        print("These are optional but recommended.")
        print()

        # Add correct example
        print("=" * 40)
        print("Example of CORRECT behavior (optional)")
        print("=" * 40)
        print("Show what a good response looks like.")
        print()
        try:
            user_query = self._get_input("  User asks: ", allow_empty=True)
            if user_query:
                user_query = self._clean_list_item(user_query)
                agent_response = self._get_input("  Agent should say: ", allow_empty=True)
                if agent_response:
                    agent_response = self._clean_list_item(agent_response)
                    examples.append({
                        "category": "clearly_correct",
                        "title": "User Example",
                        "user": user_query,
                        "agent": agent_response
                    })
                    print("    [+] Added correct behavior example")
                    print()

            # Add wrong example
            print("=" * 40)
            print("Example of WRONG behavior (optional)")
            print("=" * 40)
            print("Show what the agent should NOT say.")
            print()
            user_query = self._get_input("  User asks: ", allow_empty=True)
            if user_query:
                user_query = self._clean_list_item(user_query)
                bad_response = self._get_input("  Agent should NOT say: ", allow_empty=True)
                if bad_response:
                    bad_response = self._clean_list_item(bad_response)
                    examples.append({
                        "category": "clearly_wrong",
                        "title": "User Example",
                        "user": user_query,
                        "agent": bad_response
                    })
                    print("    [+] Added wrong behavior example")
                    print()

        except NavigationCommand:
            raise

        if examples:
            print(f"  [Total examples: {len(examples)}]")
        print()

    def _ask_success_criteria(self):
        """Ask about success criteria"""
        print()
        print("=" * 72)
        print("SUCCESS CRITERIA")
        print("=" * 72)
        print()

        print("Define performance targets for this agent.")
        print()

        if not self.state.has_data("success_criteria"):
            self.state.set_data("success_criteria", {})

        criteria = self.state.get_data("success_criteria")

        # Latency
        print("Max Response Time")
        print("  How long should users wait for a response?")
        while True:
            current = criteria.get("latency", 30)
            latency = self._get_input(f"  Latency target in seconds [default: {current}]: ", allow_empty=True)
            if not latency:
                criteria["latency"] = current
                break
            try:
                criteria["latency"] = int(latency)
                print(f"    [+] Set to {criteria['latency']} seconds")
                break
            except ValueError:
                print("  [!] Please enter a valid number")
        print()

        # Cost
        print("Max Cost Per Query")
        print("  How much can each query cost in API usage?")
        while True:
            current = criteria.get("cost", 0.10)
            cost = self._get_input(f"  Cost per query in USD [default: {current}]: ", allow_empty=True)
            if not cost:
                criteria["cost"] = current
                break
            try:
                criteria["cost"] = float(cost)
                print(f"    [+] Set to ${criteria['cost']:.2f}")
                break
            except ValueError:
                print("  [!] Please enter a valid number")
        print()

        # Accuracy
        print("Accuracy Requirement")
        print("  What percentage of queries should be answered correctly?")
        while True:
            current = criteria.get("accuracy", 95)
            accuracy = self._get_input(f"  Accuracy requirement as % [default: {current}]: ", allow_empty=True)
            if not accuracy:
                criteria["accuracy"] = current
                break
            try:
                criteria["accuracy"] = int(accuracy)
                print(f"    [+] Set to {criteria['accuracy']}%")
                break
            except ValueError:
                print("  [!] Please enter a valid number")
        print()

        print(f"  [Success criteria configured: {criteria['latency']}s, ${criteria['cost']:.2f}, {criteria['accuracy']}%]")
        print()

    def _review_and_confirm(self) -> bool:
        """Show summary and ask for confirmation"""
        print()
        print("=" * 72)
        print("REVIEW YOUR AGENT SPECIFICATION")
        print("=" * 72)
        print()

        # Header
        name = self.state.get_data('name', 'N/A')
        version = self.state.get_data('version', 'v1.0')
        owner = self.state.get_data('owner', 'N/A')
        purpose = self.state.get_data('purpose', 'N/A')

        print(f"Agent: {name} {version}")
        print(f"Owner: {owner}")
        print()
        print(f"Purpose:")
        print(f"  {purpose}")
        print()
        print("-" * 72)
        print()

        # Capabilities
        scope_in = self.state.get_data('scope_in', [])
        print(f"CAPABILITIES ({len(scope_in)} items):")
        if scope_in:
            for i, item in enumerate(scope_in, 1):
                # Truncate long items
                display = item[:65] + "..." if len(item) > 65 else item
                print(f"  {i}. {display}")
        else:
            print("  (none)")
        print()

        # Restrictions
        scope_out = self.state.get_data('scope_out', [])
        print(f"RESTRICTIONS ({len(scope_out)} items):")
        if scope_out:
            for i, item in enumerate(scope_out, 1):
                display = item[:65] + "..." if len(item) > 65 else item
                print(f"  {i}. {display}")
        else:
            print("  (none)")
        print()

        # Invariants
        invariants = self.state.get_data('invariants', [])
        print(f"INVARIANTS ({len(invariants)} rules):")
        if invariants:
            for i, inv in enumerate(invariants, 1):
                print(f"  {i}. {inv['name']}")
                if inv['description']:
                    desc = inv['description'][:60] + "..." if len(inv['description']) > 60 else inv['description']
                    print(f"     {desc}")
        else:
            print("  (none)")
        print()

        # Tools
        tools = self.state.get_data('tools', [])
        print(f"TOOLS ({len(tools)} selected):")
        if tools:
            for i, tool in enumerate(tools, 1):
                print(f"  {i}. {tool}")
        else:
            print("  (none)")
        print()

        # Examples
        examples = self.state.get_data('behavior_examples', [])
        correct = [ex for ex in examples if ex['category'] == 'clearly_correct']
        wrong = [ex for ex in examples if ex['category'] == 'clearly_wrong']
        print(f"BEHAVIOR EXAMPLES: {len(correct)} correct, {len(wrong)} wrong")
        print()

        # Criteria
        criteria = self.state.get_data('success_criteria', {})
        print("SUCCESS CRITERIA:")
        print(f"  Max Latency: {criteria.get('latency', 30)} seconds")
        print(f"  Max Cost: ${criteria.get('cost', 0.10):.2f} per query")
        print(f"  Min Accuracy: {criteria.get('accuracy', 95)}%")
        print()

        print("=" * 72)
        print()

        try:
            confirm = self._get_input("Generate agent with this specification? (y/n/back): ")
            return confirm.lower() == 'y'
        except NavigationCommand as nav:
            if nav.command == "back":
                self.state.set_current_step(7)  # Go back to last step
                return False  # Don't generate, return to wizard loop
            raise

    def _generate_agent(self) -> bool:
        """Generate spec file and build agent"""
        print("=" * 72)
        print("GENERATING AGENT")
        print("=" * 72)
        print()

        try:
            # Generate spec markdown
            print("[1/3] Writing spec file...")
            spec_content = self._build_spec_markdown()

            # Sanitize filename
            agent_name = self.state.get_data('name', 'agent')
            safe_name = re.sub(r'[<>:"/\\|?*]', '', agent_name.lower().replace(' ', '-'))
            spec_filename = f"{safe_name}-{self.state.get_data('version', 'v1.0')}.md"
            spec_path = Path("specs") / spec_filename

            spec_path.parent.mkdir(exist_ok=True)
            spec_path.write_text(spec_content, encoding='utf-8')
            print(f"  [OK] Spec written: {spec_path}")

            # Parse and generate agent
            print("\n[2/3] Generating agent code...")
            parser = SpecParser()
            spec = parser.parse_spec(str(spec_path))

            code_gen = CodeGenerator()
            agent_path = code_gen.generate_agent_file(spec, None)
            print(f"  [OK] Agent generated: {agent_path}")

            # Generate tests
            print("\n[3/3] Generating tests...")
            eval_gen = EvalGenerator()
            test_path = eval_gen.generate_test_file(spec, None)
            print(f"  [OK] Tests generated: {test_path}")

            # Success summary
            print()
            print("=" * 72)
            print("AGENT CREATED SUCCESSFULLY!")
            print("=" * 72)
            print()
            print("Files created:")
            print(f"  - {spec_path}")
            print(f"  - {agent_path}")
            print(f"  - {test_path}")
            print()
            print("Next steps:")
            print(f"  1. Review: less {spec_path}")
            print(f"  2. Test: poetry run pytest {test_path} -v")
            print(f"  3. Use: from agents.{Path(agent_path).stem} import create_agent")
            print()

            return True

        except Exception as e:
            print(f"\n[ERROR] Generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _build_spec_markdown(self) -> str:
        """
        PURPOSE: Build spec markdown from collected data

        OUTPUTS:
            str: Complete spec markdown content
        """
        lines = []

        # Header
        name = self.state.get_data('name', 'Agent')
        version = self.state.get_data('version', 'v1.0')
        lines.append(f"# Agent Spec: {name} {version}")
        lines.append("")
        lines.append(f"**Status:** DRAFT")
        lines.append(f"**Created:** {datetime.now().strftime('%Y-%m-%d')}")
        lines.append(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}")
        lines.append(f"**Owner:** {self.state.get_data('owner', 'Anonymous')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Purpose
        lines.append("## Purpose")
        lines.append("")
        lines.append(self.state.get_data('purpose', 'N/A'))
        lines.append("")
        lines.append("---")
        lines.append("")

        # Scope
        lines.append("## Scope")
        lines.append("")
        lines.append("### In Scope")
        lines.append("")
        for item in self.state.get_data('scope_in', []):
            lines.append(f"- ✅ {item}")
        lines.append("")
        lines.append("### Out of Scope")
        lines.append("")
        for item in self.state.get_data('scope_out', []):
            lines.append(f"- ❌ {item}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Invariants
        lines.append("## Invariants")
        lines.append("")
        for i, inv in enumerate(self.state.get_data('invariants', []), 1):
            lines.append(f"{i}. **{inv['name']}:** {inv['description']}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Success Criteria
        lines.append("## Success Criteria")
        lines.append("")
        lines.append("### Functional Requirements")
        lines.append("- [ ] Agent responds to queries accurately")
        lines.append("- [ ] Agent follows all invariants")
        lines.append("")
        lines.append("### Performance Requirements")
        criteria = self.state.get_data('success_criteria', {})
        lines.append(f"- [ ] Latency: < {criteria.get('latency', 30)} seconds")
        lines.append(f"- [ ] Cost: < ${criteria.get('cost', 0.10)} per query")
        lines.append(f"- [ ] Accuracy: >= {criteria.get('accuracy', 95)}%")
        lines.append("")
        lines.append("### User Experience Requirements")
        lines.append("- [ ] Responses are clear and helpful")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Behavior Examples
        lines.append("## Behavior Examples")
        lines.append("")

        examples = self.state.get_data('behavior_examples', [])

        # Correct examples
        correct_examples = [ex for ex in examples if ex['category'] == 'clearly_correct']
        if correct_examples:
            lines.append("### Clearly Correct")
            lines.append("")
            for i, ex in enumerate(correct_examples, 1):
                lines.append(f"**Example {i}: {ex['title']}**")
                lines.append("```")
                lines.append(f"User: \"{ex['user']}\"")
                lines.append("")
                lines.append(f"Agent: \"{ex['agent']}\"")
                lines.append("```")
                lines.append("")

        # Wrong examples
        wrong_examples = [ex for ex in examples if ex['category'] == 'clearly_wrong']
        if wrong_examples:
            lines.append("### Clearly Wrong")
            lines.append("")
            for i, ex in enumerate(wrong_examples, 1):
                lines.append(f"**Example {i}: {ex['title']}**")
                lines.append("```")
                lines.append(f"User: \"{ex['user']}\"")
                lines.append("")
                lines.append(f"❌ WRONG: \"{ex['agent']}\"")
                lines.append("```")
                lines.append("")

        lines.append("---")
        lines.append("")

        # Tools Required
        lines.append("## Tools Required")
        lines.append("")
        lines.append("### Essential Tools")
        for i, tool in enumerate(self.state.get_data('tools', []), 1):
            lines.append(f"{i}. **{tool}** - Tool for agent operations")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Data Models (minimal)
        lines.append("## Data Models")
        lines.append("")
        lines.append("```python")
        lines.append("from pydantic import BaseModel, Field")
        lines.append("")
        lines.append("class AgentResponse(BaseModel):")
        lines.append("    answer: str = Field(..., description=\"Agent response\")")
        lines.append("    confidence: float = Field(..., ge=0.0, le=1.0)")
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Evaluation
        lines.append("## Evaluation Criteria")
        lines.append("")
        lines.append("Test with behavior examples and validate performance metrics.")
        lines.append("")

        return "\n".join(lines)

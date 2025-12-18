#!/usr/bin/env python3
"""
========================================================================
AGENTCLI.PY - Agent Factory CLI Tool
========================================================================

PURPOSE:
    Command-line interface for the Agent Factory spec-to-agent pipeline.
    Makes it easy to build, validate, and test agents from specifications.

WHAT THIS DOES:
    1. Build agents from spec files -> generate Python code + tests
    2. Validate spec files against AGENTS.md requirements
    3. Run evaluation tests on generated agents
    4. Show system status and available specs

WHY WE NEED THIS:
    "Specifications are eternal, code is ephemeral"
    This CLI embodies the spec-first philosophy by making the
    spec -> agent -> test workflow simple and accessible.

COMMANDS:
    agentcli build <spec-name>     Generate agent and tests from spec
    agentcli validate <spec-file>  Validate spec format and completeness
    agentcli eval <agent-name>     Run tests on generated agent
    agentcli list                  Show available specs
    agentcli status                Show system status
    agentcli edit <agent-name>     Edit existing agent interactively

USAGE:
    # Build agent from spec
    poetry run python agentcli.py build research-agent-v1.0

    # Validate a spec file
    poetry run python agentcli.py validate specs/research-agent-v1.0.md

    # Run tests on generated agent
    poetry run python agentcli.py eval research-agent-v1.0

PLC ANALOGY:
    Like a PLC programming software's "Build" button - takes your
    ladder logic (spec) and compiles it to executable code (agent).
========================================================================
"""

import sys
import argparse
from pathlib import Path
from typing import Optional
import subprocess
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from agent_factory.codegen import SpecParser, CodeGenerator, EvalGenerator
from agent_factory.cli import InteractiveAgentCreator, list_templates
from agent_factory.cli.agent_editor import AgentEditor, list_editable_agents
from agent_factory.cli.crew_creator import CrewCreator
from agent_factory.core.crew_spec import load_crew_spec, list_crew_specs, CrewSpec
from agent_factory.core.crew import Crew, ProcessType, VotingStrategy
from agent_factory.core.agent_factory import AgentFactory
from agent_factory.scaffold import WorktreeManager, WorktreeExistsError, WorktreeNotFoundError, WorktreeLimitError


# ========================================================================
# CLI COMMANDS
# ========================================================================

class AgentCLI:
    """
    PURPOSE: Main CLI controller for Agent Factory commands

    WHAT THIS DOES:
        - Parses command-line arguments
        - Routes to appropriate command handlers
        - Provides user-friendly output
        - Handles errors gracefully

    DESIGN:
        Uses argparse for command parsing
        Each command is a method (build, validate, eval, etc.)
        Outputs are formatted for terminal display
    """

    def __init__(self):
        """Initialize CLI with specs directory"""
        self.specs_dir = Path("specs")
        self.agents_dir = Path("agents")
        self.tests_dir = Path("tests")

        # Create directories if they don't exist
        self.specs_dir.mkdir(exist_ok=True)
        self.agents_dir.mkdir(exist_ok=True)
        self.tests_dir.mkdir(exist_ok=True)

        # Initialize parsers/generators
        self.spec_parser = SpecParser()
        self.code_generator = CodeGenerator()
        self.eval_generator = EvalGenerator()

        # Initialize WorktreeManager
        self.worktree_manager = WorktreeManager(repo_root=Path.cwd(), max_concurrent=5)

    def build(self, spec_name: str, output_dir: Optional[str] = None) -> int:
        """
        PURPOSE: Build agent and tests from specification

        WHAT THIS DOES:
            1. Find spec file in specs/ directory
            2. Parse spec to AgentSpec object
            3. Generate agent Python file
            4. Generate test file
            5. Report success with file paths

        INPUTS:
            spec_name (str): Name of spec (e.g., "research-agent-v1.0")
            output_dir (str, optional): Where to save generated files

        OUTPUTS:
            int: 0 on success, 1 on error

        SIDE EFFECTS:
            - Creates agent Python file in agents/
            - Creates test file in tests/
        """
        print("=" * 72)
        print(f"BUILDING AGENT: {spec_name}")
        print("=" * 72)

        # Find spec file
        spec_file = self._find_spec_file(spec_name)
        if not spec_file:
            print(f"\n[ERROR] Spec file not found: {spec_name}")
            print(f"  Looked in: {self.specs_dir}")
            print(f"  Available specs:")
            self._list_specs()
            return 1

        try:
            # Parse spec
            print(f"\n[1/4] Parsing spec: {spec_file.name}")
            spec = self.spec_parser.parse_spec(str(spec_file))
            print(f"  [OK] Parsed: {spec.name} {spec.version}")
            print(f"      Status: {spec.status}")
            print(f"      Owner: {spec.owner}")

            # Generate agent code
            print(f"\n[2/4] Generating agent code...")
            agent_path = self.code_generator.generate_agent_file(spec, None)  # Let generator handle filename
            print(f"  [OK] Agent code: {agent_path}")
            print(f"      Size: {Path(agent_path).stat().st_size} bytes")

            # Generate tests
            print(f"\n[3/4] Generating test file...")
            test_path = self.eval_generator.generate_test_file(spec, None)  # Let generator handle filename
            print(f"  [OK] Test file: {test_path}")
            print(f"      Size: {Path(test_path).stat().st_size} bytes")

            # Summary
            print(f"\n[4/4] Build complete!")
            print(f"\n{'='*72}")
            print("BUILD SUMMARY")
            print(f"{'='*72}")
            print(f"Agent: {spec.name} {spec.version}")
            print(f"Spec:  {spec_file}")
            print(f"Code:  {agent_path}")
            print(f"Tests: {test_path}")
            print(f"\nNext steps:")
            print(f"  1. Review generated code: {agent_path}")
            print(f"  2. Run tests: poetry run pytest {test_path} -v")
            print(f"  3. Use agent: from agents.{Path(agent_path).stem} import create_agent")

            return 0

        except Exception as e:
            print(f"\n[ERROR] Build failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

    def validate(self, spec_file: str) -> int:
        """
        PURPOSE: Validate specification file

        WHAT THIS DOES:
            1. Parse spec file
            2. Check all required sections present
            3. Validate behavior examples
            4. Check invariants and success criteria
            5. Report validation results

        INPUTS:
            spec_file (str): Path to spec file

        OUTPUTS:
            int: 0 if valid, 1 if invalid

        VALIDATION CHECKS:
            - All required sections exist
            - Purpose is non-empty
            - At least one invariant
            - At least one behavior example
            - Data models are valid Python (if present)
        """
        print("=" * 72)
        print(f"VALIDATING SPEC: {spec_file}")
        print("=" * 72)

        spec_path = Path(spec_file)
        if not spec_path.exists():
            print(f"\n[ERROR] File not found: {spec_file}")
            return 1

        try:
            # Parse spec
            print(f"\n[1/3] Parsing specification...")
            spec = self.spec_parser.parse_spec(str(spec_path))
            print(f"  [OK] Successfully parsed")

            # Validate completeness
            print(f"\n[2/3] Validating completeness...")
            issues = []

            # Check required fields
            if not spec.purpose or len(spec.purpose) < 10:
                issues.append("Purpose is too short or missing")

            if not spec.scope_in:
                issues.append("No 'In Scope' items defined")

            if not spec.scope_out:
                issues.append("No 'Out of Scope' items defined")

            if not spec.invariants:
                issues.append("No invariants defined")

            if len(spec.invariants) < 2:
                issues.append("Should have at least 2 invariants")

            if not spec.behavior_examples:
                issues.append("No behavior examples provided")

            if len(spec.behavior_examples) < 2:
                issues.append("Should have at least 2 behavior examples")

            # Check for both positive and negative examples
            has_correct = any(ex.category == "clearly_correct" for ex in spec.behavior_examples)
            has_wrong = any(ex.category == "clearly_wrong" for ex in spec.behavior_examples)

            if not has_correct:
                issues.append("Missing 'clearly_correct' behavior examples")

            if not has_wrong:
                issues.append("Missing 'clearly_wrong' behavior examples")

            if not spec.essential_tools:
                issues.append("No essential tools defined")

            # Report results
            print(f"\n[3/3] Validation results...")

            if issues:
                print(f"\n  [WARNING] Found {len(issues)} issue(s):")
                for i, issue in enumerate(issues, 1):
                    print(f"    {i}. {issue}")
                print(f"\n  Spec is parseable but may not follow best practices.")
                return 1
            else:
                print(f"  [OK] All validation checks passed!")

            # Show spec summary
            print(f"\n{'='*72}")
            print("SPEC SUMMARY")
            print(f"{'='*72}")
            print(f"Name: {spec.name} {spec.version}")
            print(f"Status: {spec.status}")
            print(f"Owner: {spec.owner}")
            print(f"\nSections:")
            print(f"  Purpose: {len(spec.purpose)} chars")
            print(f"  In Scope: {len(spec.scope_in)} items")
            print(f"  Out of Scope: {len(spec.scope_out)} items")
            print(f"  Invariants: {len(spec.invariants)} rules")
            print(f"  Behavior Examples: {len(spec.behavior_examples)} examples")
            print(f"  Essential Tools: {len(spec.essential_tools)} tools")
            print(f"  Optional Tools: {len(spec.optional_tools)} tools")

            return 0

        except Exception as e:
            print(f"\n[ERROR] Validation failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

    def eval(self, agent_name: str) -> int:
        """
        PURPOSE: Run evaluation tests on generated agent

        WHAT THIS DOES:
            1. Find test file for agent
            2. Run pytest on test file
            3. Report results

        INPUTS:
            agent_name (str): Agent name (e.g., "research-agent-v1.0")

        OUTPUTS:
            int: 0 if tests pass, 1 if fail or not found
        """
        print("=" * 72)
        print(f"EVALUATING AGENT: {agent_name}")
        print("=" * 72)

        # Find test file
        test_filename = f"test_{agent_name.lower().replace('-', '_')}.py"
        test_path = self.tests_dir / test_filename

        if not test_path.exists():
            print(f"\n[ERROR] Test file not found: {test_path}")
            print(f"  Run 'agentcli build {agent_name}' first to generate tests")
            return 1

        print(f"\n[1/2] Found test file: {test_path}")
        print(f"[2/2] Running pytest...\n")

        # Run pytest
        try:
            result = subprocess.run(
                ["poetry", "run", "pytest", str(test_path), "-v"],
                capture_output=False,
                text=True
            )
            return result.returncode

        except Exception as e:
            print(f"\n[ERROR] Failed to run tests: {e}")
            return 1

    def list_specs(self) -> int:
        """
        PURPOSE: List all available specification files

        WHAT THIS DOES:
            Show all .md files in specs/ directory with metadata

        OUTPUTS:
            int: Always 0
        """
        print("=" * 72)
        print("AVAILABLE SPECIFICATIONS")
        print("=" * 72)

        self._list_specs()
        return 0

    def status(self) -> int:
        """
        PURPOSE: Show system status and statistics

        WHAT THIS DOES:
            Display counts of specs, agents, tests, and system health

        OUTPUTS:
            int: Always 0
        """
        print("=" * 72)
        print("AGENT FACTORY STATUS")
        print("=" * 72)

        # Count specs
        specs = list(self.specs_dir.glob("*.md"))
        agents = list(self.agents_dir.glob("*.py"))
        agents = [a for a in agents if not a.name.startswith('__')]  # Exclude __init__.py
        tests = list(self.tests_dir.glob("test_*.py"))

        print(f"\nDirectories:")
        print(f"  Specs:  {self.specs_dir} ({len(specs)} files)")
        print(f"  Agents: {self.agents_dir} ({len(agents)} files)")
        print(f"  Tests:  {self.tests_dir} ({len(tests)} files)")

        print(f"\nSystem:")
        print(f"  Python: {sys.version.split()[0]}")
        print(f"  Working Dir: {Path.cwd()}")

        print(f"\nComponents:")
        print(f"  SpecParser: Ready")
        print(f"  CodeGenerator: Ready")
        print(f"  EvalGenerator: Ready")

        return 0

    def create_crew(self) -> int:
        """
        PURPOSE: Launch interactive crew creation wizard

        WHAT THIS DOES:
            Run CrewCreator wizard to build crew YAML specification

        OUTPUTS:
            int: 0 on success, 1 on error
        """
        creator = CrewCreator()
        success = creator.run()
        return 0 if success else 1

    def list_crews(self) -> int:
        """
        PURPOSE: List all available crew specifications

        WHAT THIS DOES:
            Show all crew YAML files in crews/ directory

        OUTPUTS:
            int: Always 0
        """
        print("=" * 72)
        print("AVAILABLE CREWS")
        print("=" * 72)

        crew_specs = list_crew_specs()

        if not crew_specs:
            print(f"\n  No crews found in crews/")
            print(f"  Create one with: agentcli create-crew")
            return 0

        print(f"\n  Found {len(crew_specs)} crew(s):")
        for spec_path in crew_specs:
            # Load to get metadata
            try:
                spec = CrewSpec.load(spec_path)
                print(f"\n    {spec.name} (v{spec.version})")
                print(f"      Process: {spec.process}")
                print(f"      Agents: {len(spec.agents)}")
                print(f"      Description: {spec.description}")
            except Exception as e:
                print(f"\n    {spec_path.name} [ERROR: {e}]")

        print(f"\n  Run with: agentcli run-crew <crew-name> --task \"Your task\"")
        return 0

    def run_crew(self, crew_name: str, task: str, verbose: bool = False) -> int:
        """
        PURPOSE: Execute crew from YAML specification

        WHAT THIS DOES:
            1. Load crew spec from YAML
            2. Create agents from spec
            3. Build crew with correct process type
            4. Execute task
            5. Report results

        INPUTS:
            crew_name (str): Crew name or path to YAML
            task (str): Task for crew to execute
            verbose (bool): Show detailed execution logs

        OUTPUTS:
            int: 0 on success, 1 on error
        """
        print("=" * 72)
        print(f"RUNNING CREW: {crew_name}")
        print("=" * 72)

        try:
            # Load spec
            print(f"\n[1/4] Loading crew specification...")
            spec = load_crew_spec(crew_name)
            print(f"  [OK] Loaded: {spec.name} v{spec.version}")
            print(f"      Process: {spec.process}")
            print(f"      Agents: {len(spec.agents)}")

            # Create agents
            print(f"\n[2/4] Creating agents...")
            factory = AgentFactory()
            agents = []

            # Import tool classes
            from agent_factory.tools.research_tools import (
                CurrentTimeTool,
                WikipediaSearchTool,
                DuckDuckGoSearchTool,
                TavilySearchTool
            )

            tool_map = {
                "current_time": CurrentTimeTool,
                "wikipedia": WikipediaSearchTool,
                "duckduckgo": DuckDuckGoSearchTool,
                "tavily": TavilySearchTool,
            }

            for agent_spec in spec.agents:
                # Build tools list
                tools = []
                for tool_name in agent_spec.tools:
                    if tool_name in tool_map:
                        tools.append(tool_map[tool_name]())
                    else:
                        print(f"    [WARNING] Unknown tool '{tool_name}' for agent '{agent_spec.name}'")

                # Create agent
                agent = factory.create_agent(
                    role=agent_spec.role,
                    tools_list=tools,
                    system_prompt=agent_spec.prompt
                )
                agents.append(agent)
                print(f"    [OK] {agent_spec.role}")

            # Create manager if needed
            manager = None
            if spec.process == "hierarchical" and spec.manager:
                print(f"\n    Creating manager...")
                manager_tools = []
                for tool_name in spec.manager.tools:
                    if tool_name in tool_map:
                        manager_tools.append(tool_map[tool_name]())

                manager = factory.create_agent(
                    role=spec.manager.role,
                    tools_list=manager_tools,
                    system_prompt=spec.manager.prompt
                )
                print(f"    [OK] {spec.manager.role}")

            # Build crew
            print(f"\n[3/4] Building crew...")
            process_type = ProcessType[spec.process.upper()]

            crew_kwargs = {
                "agents": agents,
                "process": process_type,
                "verbose": verbose
            }

            if manager:
                crew_kwargs["manager"] = manager

            if spec.voting:
                voting_strategy = VotingStrategy[spec.voting.upper()]
                crew_kwargs["voting_strategy"] = voting_strategy

            crew = Crew(**crew_kwargs)
            print(f"  [OK] Crew ready with {len(agents)} agents")

            # Execute
            print(f"\n[4/4] Executing task...")
            print(f"  Task: {task}")
            print()

            result = crew.run(task)

            # Show results
            print()
            print("=" * 72)
            print("EXECUTION RESULTS")
            print("=" * 72)
            print(f"\nSuccess: {result.success}")
            print(f"Process: {result.process_type}")
            print(f"Agents: {len(result.agent_outputs)}")
            print(f"Execution Time: {result.execution_time:.2f}s")

            if hasattr(result, 'consensus_details') and result.consensus_details:
                print(f"Consensus: {result.consensus_details}")

            print(f"\nResult:")
            print(f"  {result.result}")

            return 0 if result.success else 1

        except FileNotFoundError as e:
            print(f"\n[ERROR] {e}")
            return 1
        except Exception as e:
            print(f"\n[ERROR] Crew execution failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

    def _find_spec_file(self, spec_name: str) -> Optional[Path]:
        """
        PURPOSE: Find spec file by name

        WHAT THIS DOES:
            Search specs/ directory for matching .md file
            Handles both full filename and just the name

        RETURNS: Path to spec file or None
        """
        # Try exact match
        spec_path = self.specs_dir / f"{spec_name}.md"
        if spec_path.exists():
            return spec_path

        # Try adding .md if missing
        if not spec_name.endswith('.md'):
            spec_path = self.specs_dir / f"{spec_name}.md"
            if spec_path.exists():
                return spec_path

        # Try case-insensitive search
        for file in self.specs_dir.glob("*.md"):
            if file.stem.lower() == spec_name.lower():
                return file

        return None

    def _list_specs(self):
        """
        PURPOSE: Print list of available specs

        WHAT THIS DOES:
            Show all .md files in specs/ with size info
        """
        specs = sorted(self.specs_dir.glob("*.md"))

        if not specs:
            print(f"\n  No specs found in {self.specs_dir}")
            print(f"  Create a spec file following specs/template.md")
            return

        print(f"\n  Found {len(specs)} specification(s):")
        for spec_file in specs:
            size_kb = spec_file.stat().st_size / 1024
            print(f"    - {spec_file.name} ({size_kb:.1f} KB)")

    def _check_worktree_safety(self, warn_only: bool = True) -> bool:
        """
        PURPOSE: Check if we're in a worktree (for multi-agent safety)

        WHAT THIS DOES:
            Check if current directory is a worktree or main directory.
            Optionally warn user if they're in main directory.

        INPUTS:
            warn_only (bool): If True, only warn. If False, block operation.

        OUTPUTS:
            bool: True if in worktree, False if in main directory

        USAGE:
            Call this before git operations to remind user about worktrees.
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return True  # Not in git repo, don't block

            git_dir = result.stdout.strip()

            # Check if in main directory
            if git_dir == ".git":
                if warn_only:
                    print("\n⚠️  WARNING: You're in the MAIN directory")
                    print("   For multi-agent safety, consider using a worktree:")
                    print("     agentcli worktree-create myfeature")
                    print("   See: docs/GIT_WORKTREE_GUIDE.md\n")
                    return False
                else:
                    print("\n[ERROR] Operation blocked - you're in the MAIN directory")
                    print("  Create a worktree first: agentcli worktree-create myfeature")
                    print("  See: docs/GIT_WORKTREE_GUIDE.md\n")
                    return False

            # In worktree - all good
            return True

        except Exception:
            # If check fails, don't block
            return True

    def worktree_create(self, name: str) -> int:
        """
        PURPOSE: Create new git worktree with branch

        WHAT THIS DOES:
            1. Validates name
            2. Creates worktree in parent directory using WorktreeManager
            3. Creates new branch
            4. Reports success with instructions

        INPUTS:
            name (str): Worktree/branch name (e.g., "myfeature")

        OUTPUTS:
            int: 0 on success, 1 on error
        """
        print("=" * 72)
        print(f"CREATING WORKTREE: {name}")
        print("=" * 72)

        # Validate name
        if not name or not name.strip():
            print("\n[ERROR] Worktree name cannot be empty")
            return 1

        # Clean name (lowercase, hyphens)
        clean_name = name.lower().replace(" ", "-").replace("_", "-")

        print(f"\n[1/3] Checking if worktree already exists...")

        try:
            # Use WorktreeManager to create worktree
            worktree_path = self.worktree_manager.create_worktree(
                task_id=clean_name,
                creator="agentcli"
            )

            print(f"  [OK] Name available")
            print(f"\n[2/3] Creating worktree with new branch...")

            # Get metadata to display info
            metadata = self.worktree_manager.get_worktree(clean_name)
            print(f"  Path: {worktree_path}")
            print(f"  Branch: {metadata.branch_name}")
            print(f"  [OK] Worktree created successfully")

            # Success message
            print(f"\n[3/3] Setup complete!")
            print(f"\n{'='*72}")
            print("WORKTREE READY")
            print(f"{'='*72}")
            print(f"\nWorktree: {worktree_path}")
            print(f"Branch: {metadata.branch_name}")
            print(f"\nNext steps:")
            print(f"  1. cd {worktree_path}")
            print(f"  2. Start coding!")
            print(f"  3. git add . && git commit -m \"Your message\"")
            print(f"  4. git push -u origin {metadata.branch_name}")
            print(f"\nWhen done:")
            print(f"  agentcli worktree-remove {clean_name}")

            return 0

        except WorktreeExistsError:
            print(f"  [ERROR] Worktree already exists!")
            print(f"\n  List worktrees with: agentcli worktree-list")
            return 1

        except WorktreeLimitError as e:
            print(f"  [ERROR] {str(e)}")
            print(f"\n  List worktrees with: agentcli worktree-list")
            return 1

        except Exception as e:
            print(f"\n[ERROR] Failed to create worktree:")
            print(f"  {str(e)}")
            return 1

    def worktree_list(self) -> int:
        """
        PURPOSE: List all git worktrees

        WHAT THIS DOES:
            Show all active worktrees with paths and branches using WorktreeManager

        OUTPUTS:
            int: Always 0
        """
        print("=" * 72)
        print("GIT WORKTREES")
        print("=" * 72)

        # Get worktrees from WorktreeManager
        worktrees = self.worktree_manager.list_worktrees()

        # Also show git worktree list for main directory
        result = subprocess.run(
            ["git", "worktree", "list"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"\n[ERROR] Failed to list worktrees:")
            print(result.stderr)
            return 1

        # Parse git worktree list to find main directory
        lines = result.stdout.strip().split("\n")
        main_dir = None
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                path = parts[0]
                if ".git" not in path or path.endswith("Agent Factory"):
                    main_dir = path
                    break

        # Display main directory
        print(f"\n  Found {len(worktrees) + 1} worktree(s):\n")

        if main_dir:
            print(f"  [MAIN] {Path(main_dir).name}")
            print(f"        Branch: main")
            print(f"        Path: {main_dir}")
            print()

        # Display tracked worktrees
        for wt in worktrees:
            status_marker = f"[{wt.status.upper()}]"
            print(f"  {status_marker} {Path(wt.worktree_path).name}")
            print(f"        Branch: {wt.branch_name}")
            print(f"        Path: {wt.worktree_path}")
            print(f"        Created: {wt.created_at}")
            print(f"        Creator: {wt.creator}")
            if wt.pr_url:
                print(f"        PR: {wt.pr_url}")
            print()

        print(f"Create new worktree with: agentcli worktree-create <name>")
        print(f"Remove worktree with: agentcli worktree-remove <name>")

        return 0

    def worktree_remove(self, name: str) -> int:
        """
        PURPOSE: Remove git worktree

        WHAT THIS DOES:
            1. Find worktree by name using WorktreeManager
            2. Remove worktree and clean up
            3. Report success

        INPUTS:
            name (str): Worktree name (e.g., "myfeature")

        OUTPUTS:
            int: 0 on success, 1 on error
        """
        print("=" * 72)
        print(f"REMOVING WORKTREE: {name}")
        print("=" * 72)

        # Clean name
        clean_name = name.lower().replace(" ", "-").replace("_", "-")

        print(f"\n[1/2] Checking if worktree exists...")

        try:
            # Get metadata before removal
            metadata = self.worktree_manager.get_worktree(clean_name)

            if metadata is None:
                raise WorktreeNotFoundError(f"Worktree '{clean_name}' not found")

            print(f"  [OK] Found worktree")

            # Remove worktree
            print(f"\n[2/2] Removing worktree...")

            # Note: cleanup_worktree will try with --force if needed
            # and will also delete the branch by default
            self.worktree_manager.cleanup_worktree(clean_name, force=True, delete_branch=True)

            print(f"  [OK] Worktree removed")

            print(f"\n{'='*72}")
            print("WORKTREE REMOVED")
            print(f"{'='*72}")
            print(f"\nRemoved: {metadata.worktree_path}")
            print(f"Branch: {metadata.branch_name} (deleted)")

            return 0

        except WorktreeNotFoundError:
            print(f"  [ERROR] Worktree not found!")
            print(f"\n  List worktrees with: agentcli worktree-list")
            return 1

        except Exception as e:
            print(f"\n[ERROR] Failed to remove worktree:")
            print(f"  {str(e)}")
            return 1

    def worktree_status(self) -> int:
        """
        PURPOSE: Show current worktree status

        WHAT THIS DOES:
            Check if we're in a worktree or main directory

        OUTPUTS:
            int: Always 0
        """
        print("=" * 72)
        print("WORKTREE STATUS")
        print("=" * 72)

        # Check git dir
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"\n[ERROR] Not in a git repository")
            return 1

        git_dir = result.stdout.strip()

        # Check if in worktree
        if git_dir == ".git":
            print(f"\n[STATUS] In MAIN directory")
            print(f"\n⚠️  WARNING: Direct commits are blocked!")
            print(f"\nYou should be working in a worktree:")
            print(f"  agentcli worktree-create myfeature")
            print(f"\nWhy? See docs/GIT_WORKTREE_GUIDE.md")
        else:
            # In a worktree
            worktree_name = Path(git_dir).parent.name
            print(f"\n[STATUS] In WORKTREE: {worktree_name}")
            print(f"\n✓ Safe to commit!")

            # Show current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True
            )
            branch = result.stdout.strip()
            print(f"\nCurrent branch: {branch}")
            print(f"Worktree path: {Path.cwd()}")

        print(f"\nList all worktrees with: agentcli worktree-list")

        return 0


# ========================================================================
# MAIN ENTRY POINT
# ========================================================================

def main():
    """
    PURPOSE: Main CLI entry point

    WHAT THIS DOES:
        1. Parse command-line arguments
        2. Route to appropriate command
        3. Exit with appropriate code
    """
    parser = argparse.ArgumentParser(
        description="Agent Factory CLI - Build agents from specifications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive agent creation (wizard mode)
  agentcli create
  agentcli create --template researcher
  agentcli create --list-templates

  # Edit existing agents
  agentcli edit bob-1
  agentcli edit --list

  # Multi-agent crew orchestration
  agentcli create-crew
  agentcli list-crews
  agentcli run-crew email-triage --task "Process this email: ..."

  # Git worktree management (required for multi-agent safety)
  agentcli worktree-create myfeature
  agentcli worktree-list
  agentcli worktree-status
  agentcli worktree-remove myfeature

  # Build from existing spec
  agentcli build research-agent-v1.0
  agentcli validate specs/research-agent-v1.0.md
  agentcli eval research-agent-v1.0

  # System info
  agentcli list
  agentcli status

Philosophy:
  "Specifications are eternal, code is ephemeral"
  This CLI generates agents from specs following the spec-first approach.
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Build command
    build_parser = subparsers.add_parser(
        'build',
        help='Build agent and tests from specification'
    )
    build_parser.add_argument('spec_name', help='Spec name (e.g., research-agent-v1.0)')
    build_parser.add_argument('--output', '-o', help='Output directory (optional)')

    # Validate command
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate specification file'
    )
    validate_parser.add_argument('spec_file', help='Path to spec file')

    # Eval command
    eval_parser = subparsers.add_parser(
        'eval',
        help='Run tests on generated agent'
    )
    eval_parser.add_argument('agent_name', help='Agent name')

    # List command
    subparsers.add_parser(
        'list',
        help='List available specifications'
    )

    # Status command
    subparsers.add_parser(
        'status',
        help='Show system status'
    )

    # Create command (interactive)
    create_parser = subparsers.add_parser(
        'create',
        help='Create agent interactively (wizard mode)'
    )
    create_parser.add_argument('--template', '-t', help='Start with template (researcher, coder, analyst, file_manager)')
    create_parser.add_argument('--list-templates', action='store_true', help='List available templates')

    # Edit command (modify existing agent)
    edit_parser = subparsers.add_parser(
        'edit',
        help='Edit existing agent interactively'
    )
    edit_parser.add_argument('agent_name', nargs='?', help='Agent name to edit (e.g., bob-1)')
    edit_parser.add_argument('--list', action='store_true', help='List all editable agents')

    # Create-crew command
    subparsers.add_parser(
        'create-crew',
        help='Create multi-agent crew interactively (wizard mode)'
    )

    # Run-crew command
    run_crew_parser = subparsers.add_parser(
        'run-crew',
        help='Execute crew from YAML specification'
    )
    run_crew_parser.add_argument('crew_name', help='Crew name or path to YAML file')
    run_crew_parser.add_argument('--task', '-t', required=True, help='Task for crew to execute')
    run_crew_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed execution logs')

    # List-crews command
    subparsers.add_parser(
        'list-crews',
        help='List all available crew specifications'
    )

    # Worktree-create command
    worktree_create_parser = subparsers.add_parser(
        'worktree-create',
        help='Create new git worktree for safe multi-agent development'
    )
    worktree_create_parser.add_argument('name', help='Worktree/branch name (e.g., myfeature)')

    # Worktree-list command
    subparsers.add_parser(
        'worktree-list',
        help='List all git worktrees'
    )

    # Worktree-remove command
    worktree_remove_parser = subparsers.add_parser(
        'worktree-remove',
        help='Remove git worktree'
    )
    worktree_remove_parser.add_argument('name', help='Worktree name to remove')

    # Worktree-status command
    subparsers.add_parser(
        'worktree-status',
        help='Show current worktree status'
    )

    args = parser.parse_args()

    # Show help if no command
    if not args.command:
        parser.print_help()
        return 0

    # Initialize CLI
    cli = AgentCLI()

    # Route to command
    if args.command == 'build':
        return cli.build(args.spec_name, args.output)
    elif args.command == 'validate':
        return cli.validate(args.spec_file)
    elif args.command == 'eval':
        return cli.eval(args.agent_name)
    elif args.command == 'list':
        return cli.list_specs()
    elif args.command == 'status':
        return cli.status()
    elif args.command == 'create':
        # List templates if requested
        if args.list_templates:
            print("=" * 72)
            print("AVAILABLE TEMPLATES")
            print("=" * 72)
            print()
            for template in list_templates():
                print(f"{template['name']}:")
                print(f"  {template['description']}")
                print()
            return 0

        # Run interactive creator
        creator = InteractiveAgentCreator()
        success = creator.run(template_name=args.template)
        return 0 if success else 1
    elif args.command == 'edit':
        # List agents if requested
        if args.list:
            print("=" * 72)
            print("EDITABLE AGENTS")
            print("=" * 72)
            print()
            agents = list_editable_agents()
            if not agents:
                print("  No agents found in specs/")
                print("  Create one with: agentcli create")
            else:
                for agent in agents:
                    print(f"  - {agent}")
                print()
                print("Edit with: agentcli edit <agent-name>")
            print()
            return 0

        # Edit agent
        if not args.agent_name:
            print("Error: agent_name required")
            print("Usage: agentcli edit <agent-name>")
            print("       agentcli edit --list")
            return 1

        try:
            editor = AgentEditor(args.agent_name)
            success = editor.run()
            return 0 if success else 1
        except FileNotFoundError as e:
            print(f"Error: {e}")
            print()
            print("Available agents:")
            for agent in list_editable_agents():
                print(f"  - {agent}")
            return 1
        except Exception as e:
            print(f"Error editing agent: {e}")
            import traceback
            traceback.print_exc()
            return 1
    elif args.command == 'create-crew':
        return cli.create_crew()
    elif args.command == 'run-crew':
        return cli.run_crew(args.crew_name, args.task, args.verbose)
    elif args.command == 'list-crews':
        return cli.list_crews()
    elif args.command == 'worktree-create':
        return cli.worktree_create(args.name)
    elif args.command == 'worktree-list':
        return cli.worktree_list()
    elif args.command == 'worktree-remove':
        return cli.worktree_remove(args.name)
    elif args.command == 'worktree-status':
        return cli.worktree_status()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

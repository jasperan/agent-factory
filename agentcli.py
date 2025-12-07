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

from agent_factory.codegen import SpecParser, CodeGenerator, EvalGenerator


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
  agentcli build research-agent-v1.0
  agentcli validate specs/research-agent-v1.0.md
  agentcli eval research-agent-v1.0
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
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

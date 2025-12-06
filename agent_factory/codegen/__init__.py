"""
Code Generation - Spec to Agent Pipeline

This module converts specification markdown files into working LangChain agents,
tests, and documentation.

Core Philosophy (from AGENTS.md):
- Specifications are eternal (versioned, debated, source of truth)
- Code is ephemeral (regenerated from specs)
- 80-90% of engineering value is structured communication

Usage:
    from agent_factory.codegen import SpecParser, CodeGenerator, EvalGenerator

    # Parse spec file
    parser = SpecParser()
    spec = parser.parse_spec("specs/research-agent-v1.0.md")

    # Generate agent code
    generator = CodeGenerator()
    code = generator.generate_agent(spec)

    # Generate tests
    eval_gen = EvalGenerator()
    tests = eval_gen.generate_tests(spec)
"""

from .spec_parser import SpecParser, AgentSpec, BehaviorExample
from .code_generator import CodeGenerator
from .eval_generator import EvalGenerator

__all__ = [
    "SpecParser",
    "AgentSpec",
    "BehaviorExample",
    "CodeGenerator",
    "EvalGenerator",
]

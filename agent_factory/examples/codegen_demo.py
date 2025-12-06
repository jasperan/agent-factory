"""
========================================================================
CODE GENERATION DEMO - Spec to Agent Pipeline
========================================================================

PURPOSE:
    Demonstrates the complete spec-to-agent generation pipeline:
    1. Parse spec markdown -> AgentSpec object
    2. Generate agent code -> Python file
    3. Generate test code -> pytest file

This showcases the "specs are eternal, code is ephemeral" philosophy.

RUN:
    poetry run python agent_factory/examples/codegen_demo.py

DEMOS:
    1. Parse the template spec
    2. Generate agent code
    3. Generate test code
    4. Display generated code samples

========================================================================
"""

from agent_factory.codegen import SpecParser, CodeGenerator, EvalGenerator
from pathlib import Path
import tempfile


def demo_1_parse_spec():
    """
    DEMO 1: Parse specification markdown to AgentSpec object

    WHAT THIS SHOWS:
        - Read template.md spec file
        - Extract all sections (purpose, scope, invariants, etc.)
        - Build structured AgentSpec object
        - Display parsed data
    """
    print("=" * 72)
    print("DEMO 1: Parse Specification Markdown")
    print("=" * 72)

    # Parse template spec
    parser = SpecParser()
    spec_path = "specs/template.md"

    try:
        spec = parser.parse_spec(spec_path)

        print(f"\n[OK] Parsed spec: {spec.name} {spec.version}")
        print(f"  Status: {spec.status}")
        print(f"  Owner: {spec.owner}")
        print(f"\nPurpose:\n  {spec.purpose[:100]}...")
        print(f"\nScope (In):")
        for item in spec.scope_in[:3]:
            print(f"  - {item}")
        print(f"\nInvariants:")
        for i, inv in enumerate(spec.invariants[:3], 1):
            print(f"  {i}. {inv}")
        print(f"\nBehavior Examples: {len(spec.behavior_examples)} total")
        for ex in spec.behavior_examples[:2]:
            print(f"  - [{ex.category}] {ex.title}")

        return spec

    except FileNotFoundError:
        print(f"\n* Spec file not found: {spec_path}")
        print("  This is expected if running from a different directory.")
        print("  Creating a minimal example spec instead...")

        # Create minimal example for demo
        example_spec = """# Agent Spec: Example Agent v1.0

**Status:** DRAFT
**Created:** 2025-12-06
**Last Updated:** 2025-12-06
**Owner:** Demo

---

## Purpose

This is an example agent for demonstration purposes.

---

## Scope

### In Scope

- ✅ Answer basic questions
- ✅ Provide helpful responses

### Out of Scope

- ❌ Execute code
- ❌ Access external systems

---

## Invariants

1. **Accuracy First:** Never fabricate information
2. **User Safety:** Refuse harmful requests

---

## Success Criteria

### Functional Requirements
- [ ] Answers questions accurately
- [ ] Provides helpful responses

### Performance Requirements
- [ ] Latency: < 5 seconds

### User Experience Requirements
- [ ] Clear and concise responses

---

## Behavior Examples

### Clearly Correct

**Example 1: Basic Query**
```
User: "Hello, can you help me?"

Agent: "Hello! Yes, I can help you. What would you like to know?"
```

### Clearly Wrong

**Example 1: Hallucination**
```
User: "What is the capital of Atlantis?"

❌ WRONG: "The capital is Poseidonis."

[OK] CORRECT: "Atlantis is a fictional place from Plato's writings and has no real capital."
```

---

## Tools Required

### Essential Tools
1. **BasicTool** - For basic operations

---

## Data Models

```python
from pydantic import BaseModel, Field

class ExampleResponse(BaseModel):
    answer: str = Field(..., description="The response")
    confidence: float = Field(..., ge=0.0, le=1.0)
```

---

## Evaluation Criteria

Test with sample queries and validate responses.
"""
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(example_spec)
            temp_path = f.name

        spec = parser.parse_spec(temp_path)
        Path(temp_path).unlink()  # Clean up

        print(f"\n[OK] Created example spec: {spec.name} {spec.version}")
        return spec


def demo_2_generate_agent_code(spec):
    """
    DEMO 2: Generate agent Python code from spec

    WHAT THIS SHOWS:
        - Take AgentSpec object
        - Generate complete Python file with:
          - Imports
          - Pydantic schemas
          - create_agent() function
          - main() demo function
        - Display generated code
    """
    print("\n" + "=" * 72)
    print("DEMO 2: Generate Agent Code")
    print("=" * 72)

    generator = CodeGenerator()
    code = generator.generate_agent(spec)

    print(f"\n[OK] Generated agent code ({len(code)} characters)")
    print("\nCode preview (first 50 lines):\n")
    lines = code.split('\n')
    for i, line in enumerate(lines[:50], 1):
        print(f"{i:3d} | {line}")

    if len(lines) > 50:
        print(f"\n... ({len(lines) - 50} more lines)")

    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(code)
        temp_path = f.name

    print(f"\n[OK] Saved to: {temp_path}")
    print("  (Temporary file - will be cleaned up)")

    return code, temp_path


def demo_3_generate_tests(spec):
    """
    DEMO 3: Generate pytest tests from spec

    WHAT THIS SHOWS:
        - Take AgentSpec object
        - Generate pytest test file with:
          - Test fixtures
          - Behavior example tests
          - Performance tests
          - Anti-sycophancy tests
        - Display generated tests
    """
    print("\n" + "=" * 72)
    print("DEMO 3: Generate Test Code")
    print("=" * 72)

    generator = EvalGenerator()
    tests = generator.generate_tests(spec)

    print(f"\n[OK] Generated test code ({len(tests)} characters)")
    print("\nTest preview (first 50 lines):\n")
    lines = tests.split('\n')
    for i, line in enumerate(lines[:50], 1):
        print(f"{i:3d} | {line}")

    if len(lines) > 50:
        print(f"\n... ({len(lines) - 50} more lines)")

    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(tests)
        temp_path = f.name

    print(f"\n[OK] Saved to: {temp_path}")
    print("  (Temporary file - will be cleaned up)")

    return tests, temp_path


def demo_4_full_pipeline():
    """
    DEMO 4: Complete pipeline - Spec -> Agent + Tests

    WHAT THIS SHOWS:
        - Complete workflow from spec to deployable code
        - Parse -> Generate -> Save
        - Shows file structure
    """
    print("\n" + "=" * 72)
    print("DEMO 4: Complete Pipeline (Spec -> Agent + Tests)")
    print("=" * 72)

    # Create temp directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        print(f"\nWorking directory: {temp_path}")

        # Create a simple spec
        spec_content = """# Agent Spec: Simple Helper v1.0

**Status:** APPROVED
**Created:** 2025-12-06
**Last Updated:** 2025-12-06
**Owner:** CodeGen Demo

---

## Purpose

A simple helper agent that answers basic questions politely.

---

## Scope

### In Scope
- ✅ Answer basic questions
- ✅ Be polite and helpful

### Out of Scope
- ❌ Execute code
- ❌ Make API calls

---

## Invariants

1. **Politeness:** Always be respectful
2. **Honesty:** Never fabricate answers

---

## Success Criteria

### Functional Requirements
- [ ] Responds to all queries
- [ ] Maintains polite tone

### Performance Requirements
- [ ] Response time < 10 seconds

### User Experience Requirements
- [ ] Clear responses

---

## Behavior Examples

### Clearly Correct

**Example 1: Greeting**
```
User: "Hello!"

Agent: "Hello! How can I help you today?"
```

**Example 2: Simple Question**
```
User: "What time is it?"

Agent: "I don't have access to real-time information, but I'm happy to help with other questions!"
```

### Clearly Wrong

**Example 1: Rude Response**
```
User: "Can you help me?"

❌ WRONG: "No, figure it out yourself."

[OK] CORRECT: "Of course! I'd be happy to help. What do you need?"
```

---

## Tools Required

### Essential Tools
1. **BasicResponseTool** - For generating responses

---

## Data Models

```python
from pydantic import BaseModel, Field

class HelperResponse(BaseModel):
    message: str = Field(..., description="Response message")
    tone: str = Field("friendly", description="Tone of response")
```

---

## Evaluation Criteria

Verify politeness and helpfulness in all responses.
"""

        # Save spec
        spec_file = temp_path / "simple_helper_v1.0.md"
        spec_file.write_text(spec_content, encoding='utf-8')
        print(f"\n1. Created spec: {spec_file.name}")

        # Parse spec
        parser = SpecParser()
        spec = parser.parse_spec(str(spec_file))
        print(f"2. Parsed spec: {spec.name} {spec.version}")

        # Generate agent
        code_gen = CodeGenerator()
        agent_file = temp_path / "simple_helper.py"
        code_gen.generate_agent_file(spec, str(agent_file))
        print(f"3. Generated agent: {agent_file.name} ({agent_file.stat().st_size} bytes)")

        # Generate tests
        test_gen = EvalGenerator()
        test_file = temp_path / "test_simple_helper.py"
        test_gen.generate_test_file(spec, str(test_file))
        print(f"4. Generated tests: {test_file.name} ({test_file.stat().st_size} bytes)")

        print("\n[OK] Complete pipeline successful!")
        print("\nGenerated files:")
        for file in temp_path.glob("*"):
            print(f"  - {file.name} ({file.stat().st_size} bytes)")

        print("\nTo actually use these files:")
        print("  1. Create a spec in specs/your-agent-v1.0.md")
        print("  2. Run: parser.parse_spec('specs/your-agent-v1.0.md')")
        print("  3. Run: code_gen.generate_agent_file(spec, 'agents/your_agent.py')")
        print("  4. Run: test_gen.generate_test_file(spec, 'tests/test_your_agent.py')")
        print("  5. Run: pytest tests/test_your_agent.py")


def main():
    """Run all demos"""
    print("\n")
    print("=" * 72)
    print(" " * 15 + "CODE GENERATION PIPELINE DEMO")
    print("=" * 72)

    print("\nThis demo shows the spec-to-agent generation pipeline:")
    print("  Spec (Markdown) -> Parse -> Generate -> Agent Code + Tests")
    print("\nPhilosophy: Specifications are eternal, code is ephemeral")

    try:
        # Demo 1: Parse spec
        spec = demo_1_parse_spec()

        # Demo 2: Generate agent code
        agent_code, agent_path = demo_2_generate_agent_code(spec)

        # Demo 3: Generate tests
        test_code, test_path = demo_3_generate_tests(spec)

        # Demo 4: Full pipeline
        demo_4_full_pipeline()

        # Cleanup temp files
        Path(agent_path).unlink(missing_ok=True)
        Path(test_path).unlink(missing_ok=True)

        print("\n" + "=" * 72)
        print("DEMO COMPLETE")
        print("=" * 72)
        print("\nKey Takeaways:")
        print("  * Specs are parsed into structured objects (AgentSpec)")
        print("  * Code is generated automatically from specs")
        print("  * Tests are generated from behavior examples")
        print("  * Changing spec -> regenerate code -> instant updates")
        print("\nNext Steps:")
        print("  1. Create your own spec in specs/")
        print("  2. Use SpecParser to parse it")
        print("  3. Use CodeGenerator to create agent")
        print("  4. Use EvalGenerator to create tests")
        print("  5. Run pytest to validate")

    except Exception as e:
        print(f"\n[X] Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

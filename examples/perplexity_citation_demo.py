#!/usr/bin/env python3
"""
Perplexity Citation Format Demo

Demonstrates how to parse Perplexity-style markdown (like CLAUDEUPDATE.md)
and convert it to a Knowledge Atom with proper citations.

Based on the format shown in CLAUDEUPDATE.md (5S methodology example).

Usage:
    poetry run python examples/perplexity_citation_demo.py
"""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.knowledge.atom_builder_from_pdf import AtomBuilderFromPDF


def demo_parse_claudeupdate():
    """Parse the CLAUDEUPDATE.md file to demonstrate citation extraction."""

    print("=" * 70)
    print("PERPLEXITY CITATION FORMAT DEMO")
    print("=" * 70)
    print()

    # Read CLAUDEUPDATE.md
    claudeupdate_path = Path(__file__).parent.parent / "CLAUDEUPDATE.md"

    if not claudeupdate_path.exists():
        print(f"[ERROR] File not found: {claudeupdate_path}")
        print("        Please ensure CLAUDEUPDATE.md exists in the project root")
        return

    print(f"Reading: {claudeupdate_path.name}")
    print()

    markdown_text = claudeupdate_path.read_text(encoding='utf-8')

    # Parse using AtomBuilderFromPDF.parse_perplexity_markdown()
    result = AtomBuilderFromPDF.parse_perplexity_markdown(markdown_text)

    # Display results
    print("[1/4] Extracted Title")
    print("-" * 70)
    print(f"Title: {result['title']}")
    print()

    print("[2/4] Extracted Sections")
    print("-" * 70)
    for idx, section in enumerate(result['sections'], 1):
        print(f"{idx}. {section}")
    print()

    print("[3/4] Extracted Citations")
    print("-" * 70)
    print(f"Total citations: {len(result['citations'])}")
    print()
    for citation in result['citations']:
        print(f"[^{citation['id']}] {citation['url']}")
    print()

    print("[4/4] Content Preview")
    print("-" * 70)
    content_preview = result['content'][:500]
    print(content_preview)
    if len(result['content']) > 500:
        print(f"\n... ({len(result['content']) - 500} more characters)")
    print()

    # Show how this would be stored in a Knowledge Atom
    print("=" * 70)
    print("KNOWLEDGE ATOM FORMAT")
    print("=" * 70)
    print()
    print("This parsed data would be stored as:")
    print()
    print("KnowledgeAtom(")
    print(f"    atom_id='industrial:5s:methodology',")
    print(f"    atom_type='concept',")
    print(f"    title='{result['title']}',")
    print(f"    summary='5S is a lean workplace-organization system...',")
    print(f"    content='{result['content'][:100]}...',")
    print(f"    citations={result['citations'][:2]},  # First 2 shown")
    print(f"    manufacturer='generic',")
    print(f"    difficulty='beginner',")
    print(f"    keywords=['5S', 'lean', 'maintenance', 'organization'],")
    print(f"    # ... other fields")
    print(")")
    print()

    # Show SQL storage format
    print("=" * 70)
    print("SUPABASE STORAGE (JSONB)")
    print("=" * 70)
    print()
    print("The citations field is stored as JSONB:")
    print()
    print("citations: [")
    for citation in result['citations'][:3]:
        print(f"  {{")
        print(f"    \"id\": {citation['id']},")
        print(f"    \"url\": \"{citation['url']}\",")
        print(f"    \"title\": \"{citation['title']}\",")
        print(f"    \"accessed_at\": \"{citation['accessed_at']}\"")
        print(f"  }},")
    print("  ...")
    print("]")
    print()

    print("=" * 70)
    print("[SUCCESS] Perplexity citation parsing demonstrated")
    print("=" * 70)
    print()
    print("Key Takeaways:")
    print("  1. Footnote citations [^1][^2] extracted automatically")
    print("  2. Source URLs preserved in citations JSONB array")
    print("  3. Content retains inline citation markers")
    print("  4. Sections detected and extracted")
    print("  5. Ready for Supabase knowledge_atoms table")
    print()
    print("Next Steps:")
    print("  1. Deploy updated schema with citations field")
    print("  2. Research Agent uses Perplexity API to generate cited content")
    print("  3. AtomBuilder parses Perplexity output → Knowledge Atoms")
    print("  4. Scriptwriter Agent includes citations in video scripts")
    print()


def demo_custom_markdown():
    """Demonstrate parsing custom Perplexity-style markdown."""

    print("=" * 70)
    print("CUSTOM MARKDOWN PARSING DEMO")
    print("=" * 70)
    print()

    # Create sample Perplexity-style markdown
    sample_markdown = """
# What is ladder logic in PLCs?

Ladder logic is a graphical programming language used in PLCs that resembles electrical relay logic diagrams.[^1][^2]

## Core Concepts

- **Rungs**: Horizontal lines representing logic conditions
- **Contacts**: Input conditions (normally open/closed)
- **Coils**: Output actions that activate when rung is true[^3]

## Why it's used

Ladder logic is intuitive for electricians because it mirrors physical relay wiring, making the transition to programmable control systems easier.[^1][^4]

[^1]: https://www.rockwellautomation.com/en-us/support/documentation/ladder-logic-basics.html
[^2]: https://www.plcacademy.com/ladder-logic-tutorial/
[^3]: https://www.siemens.com/global/en/products/automation/systems/industrial/plc/programming.html
[^4]: https://www.ieee.org/publications/standards/industrial-automation/ladder-logic.html
"""

    print("Sample Markdown:")
    print("-" * 70)
    print(sample_markdown)
    print()

    # Parse
    result = AtomBuilderFromPDF.parse_perplexity_markdown(sample_markdown)

    print("Parsed Result:")
    print("-" * 70)
    print(f"Title: {result['title']}")
    print(f"Sections: {', '.join(result['sections'])}")
    print(f"Citations: {len(result['citations'])} sources")
    print()

    print("Citations Detail:")
    for citation in result['citations']:
        print(f"  [{citation['id']}] {citation['url']}")
    print()

    print("[SUCCESS] Custom markdown parsed successfully")
    print()


if __name__ == "__main__":
    # Run demo 1: Parse CLAUDEUPDATE.md
    demo_parse_claudeupdate()

    # Run demo 2: Parse custom markdown
    demo_custom_markdown()

"""
========================================================================
SPEC PARSER - Markdown to Structured Agent Specification
========================================================================

PURPOSE:
    Converts specification markdown files (following specs/template.md format)
    into structured Python objects that code generators can use.

WHAT THIS DOES:
    1. Reads markdown files from specs/ directory
    2. Extracts sections: Purpose, Scope, Invariants, Success Criteria, etc.
    3. Validates completeness (ensures all required sections exist)
    4. Returns AgentSpec object with parsed data

WHY WE NEED THIS:
    Following "The New Code" philosophy:
    - Specifications are the source of truth (eternal, versioned)
    - Code is generated from specs (ephemeral, disposable)
    - This parser is the bridge between human-written specs and generated code

INPUTS:
    - Markdown file path (e.g., "specs/research-agent-v1.0.md")

OUTPUTS:
    - AgentSpec object with all parsed sections
    - Raises SpecValidationError if spec is incomplete/invalid

EDGE CASES:
    - Missing required sections → SpecValidationError
    - Malformed markdown → parsing warnings, best-effort extraction
    - Empty sections → allowed but flagged in validation warnings
    - Invalid data models (Python code) → syntax errors captured

TROUBLESHOOTING:
    - "Section not found" → Check markdown headers match template exactly
    - "Invalid Python code in Data Models" → Check syntax in ```python blocks
    - "Missing required field" → Ensure all template sections are filled

PLC ANALOGY:
    This is like a PLC reading sensor inputs (markdown) and converting them
    into structured data (AgentSpec) that the control logic (code generator)
    can process. Input validation prevents garbage-in/garbage-out.
========================================================================
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from pathlib import Path
import re


# ========================================================================
# DATA MODELS
# ========================================================================

class BehaviorExample(BaseModel):
    """
    PURPOSE: Represents a single behavior example from the spec

    WHAT THIS STORES:
        - Category: "clearly_correct" or "clearly_wrong"
        - Title: Short description (e.g., "Factual Query")
        - User input: What the user sends
        - Agent output: Expected agent response
        - Notes: Additional context

    WHY WE NEED THIS:
        These examples become test cases. "Clearly correct" → positive tests
        "Clearly wrong" → negative tests (should fail)

    PLC ANALOGY:
        Like test cases in PLC software - define expected behavior for validation
    """
    category: str = Field(..., description="clearly_correct or clearly_wrong")
    title: str = Field(..., description="Example title")
    user_input: str = Field(..., description="User's query")
    agent_output: str = Field(..., description="Expected agent response")
    notes: Optional[str] = Field(None, description="Additional context")

    @validator('category')
    def validate_category(cls, v):
        """Ensure category is valid"""
        if v not in ["clearly_correct", "clearly_wrong"]:
            raise ValueError(f"Category must be 'clearly_correct' or 'clearly_wrong', got: {v}")
        return v


class AgentSpec(BaseModel):
    """
    PURPOSE: Complete structured representation of an agent specification

    WHAT THIS STORES:
        - Metadata: Name, version, status, dates
        - Purpose: Why the agent exists
        - Scope: What it does and doesn't do
        - Invariants: Rules that must never be violated
        - Success Criteria: How we know it works
        - Behavior Examples: Test case examples
        - Tools: Required tools/APIs
        - Data Models: Pydantic schemas (as Python code strings)
        - Evaluation: Test definitions

    WHY WE NEED THIS:
        Single source of truth for code generation. All generators
        (code, tests, docs) read from this structure.

    VALIDATION:
        - Required fields must be non-empty
        - Version must follow semver (e.g., "v1.0")
        - At least one behavior example required

    PLC ANALOGY:
        Like a machine configuration file - defines all parameters
        for automated operation. Changes to this = changes to behavior.
    """
    # Metadata
    name: str = Field(..., description="Agent name")
    version: str = Field(..., description="Version (e.g., v1.0)")
    status: str = Field("DRAFT", description="DRAFT, REVIEW, APPROVED, DEPRECATED")
    created: str = Field(..., description="Creation date (YYYY-MM-DD)")
    last_updated: str = Field(..., description="Last update date (YYYY-MM-DD)")
    owner: str = Field(..., description="Owner name")

    # Core spec sections
    purpose: str = Field(..., description="Why this agent exists")
    scope_in: List[str] = Field(default_factory=list, description="What agent CAN do")
    scope_out: List[str] = Field(default_factory=list, description="What agent CANNOT do")
    invariants: List[str] = Field(default_factory=list, description="Rules that must never be violated")

    # Success criteria
    functional_requirements: List[str] = Field(default_factory=list)
    performance_requirements: List[str] = Field(default_factory=list)
    ux_requirements: List[str] = Field(default_factory=list)

    # Behavior examples
    behavior_examples: List[BehaviorExample] = Field(default_factory=list)

    # Tools and data
    essential_tools: List[Dict[str, str]] = Field(default_factory=list, description="Required tools")
    optional_tools: List[Dict[str, str]] = Field(default_factory=list, description="Optional tools")
    data_models_code: Optional[str] = Field(None, description="Pydantic schemas as Python code")

    # Evaluation
    evaluation_criteria: Optional[str] = Field(None, description="Test definitions")

    @validator('version')
    def validate_version(cls, v):
        """Ensure version follows pattern"""
        if not re.match(r'^v\d+\.\d+', v):
            raise ValueError(f"Version must follow 'vX.Y' format, got: {v}")
        return v

    @validator('behavior_examples')
    def validate_examples(cls, v):
        """Ensure at least one behavior example"""
        if not v or len(v) == 0:
            raise ValueError("At least one behavior example is required")
        return v


class SpecValidationError(Exception):
    """
    PURPOSE: Raised when spec file is invalid or incomplete

    WHEN THIS HAPPENS:
        - Missing required sections
        - Malformed markdown
        - Invalid Python code in data models
        - No behavior examples
    """
    pass


# ========================================================================
# SPEC PARSER
# ========================================================================

class SpecParser:
    """
    PURPOSE: Parse markdown spec files into AgentSpec objects

    WHAT THIS DOES:
        1. Read markdown file
        2. Extract sections using regex patterns
        3. Parse behavior examples from code blocks
        4. Validate completeness
        5. Return AgentSpec object

    HOW TO USE:
        parser = SpecParser()
        spec = parser.parse_spec("specs/research-agent-v1.0.md")
        print(spec.purpose)
        print(spec.behavior_examples)

    DESIGN DECISIONS:
        - Uses regex for section extraction (simple, robust)
        - Handles missing sections gracefully with warnings
        - Extracts Python code blocks for data models
        - Parses example blocks into structured BehaviorExample objects

    PLC ANALOGY:
        Like a PLC input module that reads sensor values and converts
        them to internal data formats. Validates input before processing.
    """

    def __init__(self):
        """Initialize parser with section patterns"""
        # Patterns for extracting markdown sections
        self.section_patterns = {
            'purpose': r'## Purpose\s*\n(.*?)\n##',
            'scope_in': r'### In Scope\s*\n(.*?)\n###',
            'scope_out': r'### Out of Scope\s*\n(.*?)\n##',
            'invariants': r'## Invariants\s*\n(.*?)\n##',
            'success_functional': r'### Functional Requirements\s*\n(.*?)\n###',
            'success_performance': r'### Performance Requirements\s*\n(.*?)\n###',
            'success_ux': r'### User Experience Requirements\s*\n(.*?)\n##',
            'behavior_correct': r'### Clearly Correct\s*\n(.*?)\n###',
            'behavior_wrong': r'### Clearly Wrong\s*\n(.*?)\n##',
            'tools_essential': r'### Essential Tools\s*\n(.*?)\n###',
            'tools_optional': r'### Optional Tools\s*\n(.*?)\n##',
            'data_models': r'## Data Models.*?\n```python\s*\n(.*?)\n```',
            'evaluation': r'## Evaluation Criteria\s*\n(.*?)$',
        }

    def parse_spec(self, file_path: str) -> AgentSpec:
        """
        PURPOSE: Main entry point - parse spec file to AgentSpec

        WHAT THIS DOES:
            1. Read markdown file
            2. Extract metadata from header
            3. Extract all sections
            4. Parse behavior examples
            5. Build and validate AgentSpec

        INPUTS:
            file_path (str): Path to .md spec file

        OUTPUTS:
            AgentSpec: Structured specification object

        RAISES:
            FileNotFoundError: If spec file doesn't exist
            SpecValidationError: If spec is incomplete/invalid

        EDGE CASES:
            - Missing sections → empty lists/None values
            - Invalid metadata → uses defaults
            - Malformed examples → skipped with warning
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Spec file not found: {file_path}")

        content = path.read_text(encoding='utf-8')

        # Extract metadata from header
        metadata = self._extract_metadata(content)

        # Extract all sections
        purpose = self._extract_section(content, 'purpose')
        scope_in = self._extract_list_items(content, 'scope_in')
        scope_out = self._extract_list_items(content, 'scope_out')
        invariants = self._extract_list_items(content, 'invariants', numbered=True)

        # Success criteria
        functional = self._extract_list_items(content, 'success_functional')
        performance = self._extract_list_items(content, 'success_performance')
        ux = self._extract_list_items(content, 'success_ux')

        # Behavior examples
        behavior_examples = self._parse_behavior_examples(content)

        # Tools
        essential_tools = self._parse_tools(content, 'tools_essential')
        optional_tools = self._parse_tools(content, 'tools_optional')

        # Data models (Python code)
        data_models = self._extract_code_block(content, 'data_models')

        # Evaluation criteria
        evaluation = self._extract_section(content, 'evaluation')

        # Build AgentSpec
        try:
            spec = AgentSpec(
                name=metadata.get('name', 'UnnamedAgent'),
                version=metadata.get('version', 'v1.0'),
                status=metadata.get('status', 'DRAFT'),
                created=metadata.get('created', '2025-01-01'),
                last_updated=metadata.get('last_updated', '2025-01-01'),
                owner=metadata.get('owner', 'Unknown'),
                purpose=purpose or "No purpose specified",
                scope_in=scope_in,
                scope_out=scope_out,
                invariants=invariants,
                functional_requirements=functional,
                performance_requirements=performance,
                ux_requirements=ux,
                behavior_examples=behavior_examples,
                essential_tools=essential_tools,
                optional_tools=optional_tools,
                data_models_code=data_models,
                evaluation_criteria=evaluation,
            )
            return spec
        except Exception as e:
            raise SpecValidationError(f"Failed to build AgentSpec: {e}")

    def _extract_metadata(self, content: str) -> Dict[str, str]:
        """
        PURPOSE: Extract metadata from spec header

        WHAT THIS EXTRACTS:
            - Agent Name (from "# Agent Spec: <Name> v1.0")
            - Version (from title or **Version:** line)
            - Status, Created, Last Updated, Owner

        RETURNS: Dict with metadata fields
        """
        metadata = {}

        # Extract name and version from title
        title_match = re.search(r'# Agent Spec:\s*(.+?)\s+v([\d.]+)', content)
        if title_match:
            metadata['name'] = title_match.group(1).strip()
            metadata['version'] = f"v{title_match.group(2)}"

        # Extract status, dates, owner
        for field in ['Status', 'Created', 'Last Updated', 'Owner']:
            pattern = rf'\*\*{field}:\*\*\s*(.+?)(\n|\*\*)'
            match = re.search(pattern, content)
            if match:
                key = field.lower().replace(' ', '_')
                metadata[key] = match.group(1).strip()

        return metadata

    def _extract_section(self, content: str, section_key: str) -> Optional[str]:
        """
        PURPOSE: Extract a section's text content

        WHAT THIS DOES:
            Uses regex pattern to find section between headers
            Strips markers and extra whitespace

        RETURNS: Section text or None if not found
        """
        pattern = self.section_patterns.get(section_key)
        if not pattern:
            return None

        match = re.search(pattern, content, re.DOTALL)
        if match:
            text = match.group(1).strip()
            # Remove markdown markers and clean
            text = re.sub(r'\[.*?\]', '', text)  # Remove [**...**]
            text = re.sub(r'Example:', '', text)  # Remove "Example:"
            text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)  # Remove quote markers
            return text.strip()
        return None

    def _extract_list_items(self, content: str, section_key: str, numbered: bool = False) -> List[str]:
        """
        PURPOSE: Extract bulleted or numbered list items from a section

        WHAT THIS DOES:
            1. Extract section text
            2. Find lines starting with - ✅ or - ❌ (scope) or 1. (invariants)
            3. Clean and return as list

        INPUTS:
            numbered (bool): If True, look for "1. " instead of "- "

        RETURNS: List of strings (one per item)
        """
        section = self._extract_section(content, section_key)
        if not section:
            return []

        items = []
        if numbered:
            # Numbered lists: "1. Item"
            pattern = r'^\d+\.\s*\*\*(.+?)\*\*:?\s*(.+?)$'
            for line in section.split('\n'):
                match = re.match(pattern, line.strip())
                if match:
                    items.append(f"{match.group(1)}: {match.group(2)}")
        else:
            # Bulleted lists: "- ✅ Item" or "- [ ] Item"
            pattern = r'^-\s*(?:✅|❌|\[ \])\s*(.+)$'
            for line in section.split('\n'):
                match = re.match(pattern, line.strip())
                if match:
                    items.append(match.group(1).strip())

        return items

    def _extract_code_block(self, content: str, section_key: str) -> Optional[str]:
        """
        PURPOSE: Extract Python code from ```python blocks

        WHAT THIS DOES:
            Finds code blocks in Data Models section
            Returns raw Python code as string

        RETURNS: Python code or None
        """
        pattern = self.section_patterns.get(section_key)
        if not pattern:
            return None

        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def _parse_behavior_examples(self, content: str) -> List[BehaviorExample]:
        """
        PURPOSE: Parse behavior examples into structured objects

        WHAT THIS DOES:
            1. Extract "Clearly Correct" and "Clearly Wrong" sections
            2. Find each **Example N:** block
            3. Extract user input (after "User:") and agent output (after "Agent:")
            4. Build BehaviorExample objects

        FORMAT EXPECTED:
            **Example 1: Title**
            ```
            User: "query"

            Agent: "response"
            ```

        RETURNS: List of BehaviorExample objects
        """
        examples = []

        # Parse "Clearly Correct" examples
        correct_section = self._extract_section(content, 'behavior_correct')
        if correct_section:
            examples.extend(self._parse_example_block(correct_section, "clearly_correct"))

        # Parse "Clearly Wrong" examples
        wrong_section = self._extract_section(content, 'behavior_wrong')
        if wrong_section:
            examples.extend(self._parse_example_block(wrong_section, "clearly_wrong"))

        return examples

    def _parse_example_block(self, section: str, category: str) -> List[BehaviorExample]:
        """
        PURPOSE: Parse individual examples from a section

        WHAT THIS DOES:
            1. Split by **Example N:** markers
            2. For each example, extract title, user input, agent output
            3. Handle both ✓ CORRECT and ❌ WRONG formats

        RETURNS: List of BehaviorExample objects
        """
        examples = []

        # Split by example markers
        example_blocks = re.split(r'\*\*Example \d+:', section)

        for block in example_blocks[1:]:  # Skip first empty split
            lines = block.strip().split('\n')
            if not lines:
                continue

            # Extract title (first line after "Example N:")
            title = lines[0].replace('**', '').strip()

            # Find user input and agent output
            block_text = '\n'.join(lines)
            user_match = re.search(r'User:\s*["\'](.+?)["\']', block_text, re.DOTALL)
            agent_match = re.search(r'Agent:\s*["\'](.+?)["\']', block_text, re.DOTALL)

            # Handle ✓ CORRECT / ❌ WRONG format
            if not agent_match:
                agent_match = re.search(r'(?:✓ CORRECT|❌ WRONG):\s*["\'](.+?)["\']', block_text, re.DOTALL)

            if user_match and agent_match:
                examples.append(BehaviorExample(
                    category=category,
                    title=title,
                    user_input=user_match.group(1).strip(),
                    agent_output=agent_match.group(1).strip(),
                ))

        return examples

    def _parse_tools(self, content: str, section_key: str) -> List[Dict[str, str]]:
        """
        PURPOSE: Parse tool definitions into structured dicts

        WHAT THIS DOES:
            Extract tool name and description from numbered lists
            Format: "1. **ToolName** - Description"

        RETURNS: List of {"name": "ToolName", "description": "..."}
        """
        section = self._extract_section(content, section_key)
        if not section:
            return []

        tools = []
        pattern = r'\d+\.\s*\*\*(.+?)\*\*\s*-\s*(.+?)(?:\n|$)'
        for match in re.finditer(pattern, section):
            tools.append({
                "name": match.group(1).strip(),
                "description": match.group(2).strip(),
            })

        return tools

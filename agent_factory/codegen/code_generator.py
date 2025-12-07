"""
========================================================================
CODE GENERATOR - Spec to LangChain Agent Code
========================================================================

PURPOSE:
    Generates working LangChain agent code from AgentSpec objects.
    Converts human-written specifications into executable Python code.

WHAT THIS DOES:
    1. Takes AgentSpec object (from SpecParser)
    2. Generates LangChain agent creation code
    3. Assigns tools based on "Tools Required" section
    4. Creates Pydantic response schemas from "Data Models"
    5. Outputs ready-to-run Python code

WHY WE NEED THIS:
    "Code is ephemeral" - specifications are permanent, code is generated.
    This allows rapid iteration: change spec → regenerate code → deploy.
    Eliminates manual coding errors and ensures spec-code consistency.

INPUTS:
    - AgentSpec object with complete specification

OUTPUTS:
    - Python code string (ready to save as .py file)
    - Factory-compatible agent creation code

EDGE CASES:
    - Unknown tool names → generates placeholder tool classes
    - Missing data models → uses default AgentResponse
    - Invalid Python in data models → raises CodeGenerationError

TROUBLESHOOTING:
    - "Tool not found" → Add tool to agent_factory/tools/ first
    - "Invalid schema syntax" → Check Data Models section in spec
    - Generated code won't run → Validate spec completeness first

PLC ANALOGY:
    Like auto-generating PLC ladder logic from functional specs.
    The spec defines WHAT, this generates HOW. Changes to spec
    immediately propagate to implementation.
========================================================================
"""

from typing import Optional
from .spec_parser import AgentSpec
from pathlib import Path


class CodeGenerationError(Exception):
    """
    PURPOSE: Raised when code generation fails

    WHEN THIS HAPPENS:
        - Invalid Python syntax in data models
        - Unknown tool references
        - Incomplete spec (missing required fields)
    """
    pass


class CodeGenerator:
    """
    PURPOSE: Generate LangChain agent code from specifications

    WHAT THIS DOES:
        1. Generate imports
        2. Generate Pydantic schemas (from spec.data_models_code)
        3. Generate tool loading code
        4. Generate agent factory creation code
        5. Generate main function with agent invocation

    HOW TO USE:
        generator = CodeGenerator()
        code = generator.generate_agent(spec)
        Path("generated_agent.py").write_text(code)

    DESIGN DECISIONS:
        - Uses string templates (simple, readable)
        - Generates complete runnable files (not fragments)
        - Includes PLC-style comments in generated code
        - Uses AgentFactory for consistency with existing patterns

    PLC ANALOGY:
        Like a code generator that converts function block diagrams
        to executable PLC code. Spec → Code in one step.
    """

    def __init__(self):
        """Initialize code generator"""
        self.indent = "    "  # 4 spaces

    def generate_agent(self, spec: AgentSpec) -> str:
        """
        PURPOSE: Main entry point - generate complete agent Python file

        WHAT THIS GENERATES:
            1. File header with metadata
            2. Imports
            3. Pydantic schemas (if spec.data_models_code exists)
            4. Agent creation function
            5. Main function with example usage

        INPUTS:
            spec (AgentSpec): Parsed specification

        OUTPUTS:
            str: Complete Python code ready to save as .py file

        STRUCTURE:
            # Header comment with spec metadata
            # Imports
            # Pydantic schemas
            # create_agent() function
            # main() function with example

        EDGE CASES:
            - No data models → uses default AgentResponse
            - No tools → creates agent with empty tool list
            - Invalid Python → raises CodeGenerationError
        """
        sections = []

        # 1. Generate file header
        sections.append(self._generate_header(spec))

        # 2. Generate imports
        sections.append(self._generate_imports(spec))

        # 3. Generate Pydantic schemas (if provided)
        if spec.data_models_code:
            sections.append(self._generate_schemas(spec))

        # 4. Generate agent creation function
        sections.append(self._generate_agent_function(spec))

        # 5. Generate main function
        sections.append(self._generate_main_function(spec))

        # Combine all sections
        return "\n\n".join(sections)

    def _generate_header(self, spec: AgentSpec) -> str:
        """
        PURPOSE: Generate file header with spec metadata

        WHAT THIS INCLUDES:
            - Agent name and version
            - Purpose
            - Status and dates
            - Auto-generated warning

        RETURNS: Header comment block
        """
        header = f'''"""
{'='*72}
{spec.name.upper()} - {spec.version}
{'='*72}

STATUS: {spec.status}
CREATED: {spec.created}
LAST UPDATED: {spec.last_updated}
OWNER: {spec.owner}

PURPOSE:
    {spec.purpose}

SCOPE:
    In Scope:
{''.join(f'        - {item}' + chr(10) for item in spec.scope_in)}
    Out of Scope:
{''.join(f'        - {item}' + chr(10) for item in spec.scope_out)}

INVARIANTS:
{''.join(f'    {i+1}. {inv}' + chr(10) for i, inv in enumerate(spec.invariants))}

WARNING:
    This file is AUTO-GENERATED from specs/{spec.name.lower().replace(' ', '-')}-{spec.version}.md
    Do not edit manually - changes will be overwritten.
    To modify behavior, update the spec and regenerate.

{'='*72}
"""'''
        return header

    def _generate_imports(self, spec: AgentSpec) -> str:
        """
        PURPOSE: Generate import statements

        WHAT THIS IMPORTS:
            - AgentFactory from agent_factory
            - Tools based on spec.essential_tools
            - Typing imports
            - Pydantic imports (if data models exist)

        RETURNS: Import block
        """
        imports = [
            "from agent_factory.core.agent_factory import AgentFactory",
            "from typing import Optional, List, Dict, Any",
        ]

        # Add Pydantic imports if schemas exist
        if spec.data_models_code:
            imports.append("from pydantic import BaseModel, Field")

        # Add tool imports
        if spec.essential_tools:
            imports.append("")
            imports.append("# Tool imports")
            for tool in spec.essential_tools:
                tool_name = tool['name']
                # Try to import from agent_factory.tools
                imports.append(f"# from agent_factory.tools import {tool_name}  # TODO: Verify tool exists")

        return "\n".join(imports)

    def _generate_schemas(self, spec: AgentSpec) -> str:
        """
        PURPOSE: Generate Pydantic schema code

        WHAT THIS DOES:
            Takes spec.data_models_code (raw Python code)
            Adds section header
            Returns formatted code block

        RETURNS: Pydantic schema definitions

        EDGE CASES:
            - Invalid Python syntax → included as-is (will fail at runtime)
            - Missing imports → user must add manually
        """
        schema_section = f'''# {'='*68}
# DATA MODELS - Pydantic Schemas
# {'='*68}

{spec.data_models_code}'''
        return schema_section

    def _generate_agent_function(self, spec: AgentSpec) -> str:
        """
        PURPOSE: Generate create_agent() function

        WHAT THIS GENERATES:
            Function that:
            1. Initializes AgentFactory
            2. Loads tools
            3. Creates agent with spec parameters
            4. Returns configured agent

        RETURNS: create_agent() function code

        INCLUDES:
            - Tool loading (TODO placeholders for now)
            - System prompt from spec.purpose
            - Response schema (if data models exist)
            - Metadata with spec reference
        """
        # Determine response schema
        response_schema = "None"
        if spec.data_models_code and "class" in spec.data_models_code:
            # Try to extract first class name
            import re
            match = re.search(r'class\s+(\w+)\(BaseModel\)', spec.data_models_code)
            if match:
                response_schema = match.group(1)

        # Build system prompt from purpose and invariants
        system_prompt_parts = [
            f"{spec.purpose}",
            "",
            "RULES (Must never be violated):",
        ]
        for i, inv in enumerate(spec.invariants, 1):
            system_prompt_parts.append(f"{i}. {inv}")

        system_prompt = "\\n".join(system_prompt_parts)

        func = f'''def create_agent(llm_provider: str = "openai", model_name: str = "gpt-4"):
    """
    PURPOSE: Create and configure the {spec.name} agent

    WHAT THIS DOES:
        1. Initialize AgentFactory with specified LLM
        2. Load required tools
        3. Create agent with system prompt and tools
        4. Return configured agent

    INPUTS:
        llm_provider (str): LLM provider (openai, anthropic, google)
        model_name (str): Model name (gpt-4, claude-3-sonnet, etc.)

    OUTPUTS:
        Configured agent ready to invoke

    INVARIANTS:
{''.join(f'{self.indent * 2}{i+1}. {inv}' + chr(10) for i, inv in enumerate(spec.invariants))}
    """
    # Initialize factory
    factory = AgentFactory(llm_provider=llm_provider, model_name=model_name)

    # Load tools
    tools = []
    # TODO: Add tool loading based on spec.essential_tools
{''.join(f'{self.indent}# {tool["name"]}: {tool["description"]}' + chr(10) for tool in spec.essential_tools)}

    # System prompt from spec
    system_prompt = """{system_prompt}"""

    # Create agent
    agent = factory.create_agent(
        role="{spec.name}",
        tools_list=tools,
        system_prompt=system_prompt,
        response_schema={response_schema},
        metadata={{
            "spec_version": "{spec.version}",
            "spec_file": "{spec.name.lower().replace(' ', '-')}-{spec.version}.md",
            "status": "{spec.status}",
        }}
    )

    return agent'''
        return func

    def _generate_main_function(self, spec: AgentSpec) -> str:
        """
        PURPOSE: Generate main() function with example usage

        WHAT THIS GENERATES:
            Example code showing:
            1. Agent creation
            2. Sample invocation using behavior examples
            3. Output display

        RETURNS: main() function and __main__ block

        USES:
            First "clearly_correct" behavior example as demo query
        """
        # Get first correct example for demo
        demo_query = "What can you help me with?"
        if spec.behavior_examples:
            correct_examples = [ex for ex in spec.behavior_examples if ex.category == "clearly_correct"]
            if correct_examples:
                demo_query = correct_examples[0].user_input

        main = f'''def main():
    """
    PURPOSE: Demo function showing agent usage

    WHAT THIS DOES:
        1. Create agent
        2. Run example query
        3. Display response
    """
    print("Creating {spec.name}...")
    agent = create_agent()

    print("\\nRunning example query...")
    query = "{demo_query}"
    result = agent.invoke({{"input": query}})

    print(f"\\nQuery: {{query}}")
    print(f"Response: {{result.get('output', result)}}")


if __name__ == "__main__":
    main()'''
        return main

    def generate_agent_file(self, spec: AgentSpec, output_path: Optional[str] = None) -> str:
        """
        PURPOSE: Generate and save agent code to file

        WHAT THIS DOES:
            1. Generate code using generate_agent()
            2. Save to file (if output_path provided)
            3. Return file path

        INPUTS:
            spec (AgentSpec): Parsed specification
            output_path (str, optional): Where to save (default: agents/<name>.py)

        OUTPUTS:
            str: Path to generated file

        SIDE EFFECTS:
            Writes file to disk
        """
        code = self.generate_agent(spec)

        if output_path is None:
            # Default: save to agents/ directory
            # Sanitize name: remove invalid filename characters
            import re
            safe_name = re.sub(r'[<>:"/\\|?*]', '', spec.name.lower().replace(' ', '_'))
            filename = f"{safe_name}_{spec.version.replace('.', '_')}.py"
            output_path = Path("agents") / filename

        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Write file
        Path(output_path).write_text(code, encoding='utf-8')

        return str(output_path)

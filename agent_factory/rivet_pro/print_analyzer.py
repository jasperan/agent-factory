"""Print/Schematic Analyzer for RIVET Pro.

Analyzes technical schematics, wiring diagrams, and equipment prints
using Claude Vision.
"""

from pathlib import Path
from typing import Optional, Dict, Any

from agent_factory.integrations.telegram.ocr.claude_provider import ClaudeVisionProvider


class PrintAnalyzer:
    """
    Analyzes technical prints and schematics for industrial maintenance.

    Use cases:
    - "What voltage is this motor?"
    - "How is the contactor wired?"
    - "What components are in this control circuit?"
    - "Why is relay CR2 energizing?"
    """

    def __init__(self, provider: Optional[ClaudeVisionProvider] = None):
        """
        Initialize print analyzer.

        Args:
            provider: Vision provider (defaults to Claude)
        """
        self.provider = provider or ClaudeVisionProvider()

    async def analyze(self, image_path: Path) -> str:
        """
        Full analysis of a technical schematic.

        Args:
            image_path: Path to schematic image

        Returns:
            Comprehensive analysis text

        Example:
            >>> analyzer = PrintAnalyzer()
            >>> analysis = await analyzer.analyze(Path("motor_circuit.png"))
            >>> print(analysis)
            "Components:
            - M1: 480V 3-phase motor (25HP)
            - CR1: Main contactor...
            "
        """
        result = await self.provider.analyze_image(image_path)
        return result["text"]

    async def answer_question(
        self,
        image_path: Path,
        question: str
    ) -> str:
        """
        Answer a specific question about a schematic.

        Args:
            image_path: Path to schematic
            question: User's question

        Returns:
            Answer text

        Example:
            >>> answer = await analyzer.answer_question(
            ...     Path("print.png"),
            ...     "What is the voltage rating of the motor?"
            ... )
            "The motor M1 is rated for 480V 3-phase..."
        """
        return await self.provider.answer_question(image_path, question)

    async def identify_fault_location(
        self,
        image_path: Path,
        fault_description: str
    ) -> str:
        """
        Identify where a fault might be occurring in the schematic.

        Args:
            image_path: Path to schematic
            fault_description: Description of the fault/symptom

        Returns:
            Analysis of likely fault locations

        Example:
            >>> analysis = await analyzer.identify_fault_location(
            ...     Path("circuit.png"),
            ...     "Motor starts but trips after 10 seconds"
            ... )
        """
        prompt = f"""Given this schematic and the following fault symptom:

"{fault_description}"

Please identify:
1. Which component(s) are most likely failing
2. Where to check first (test points, measurements)
3. Common causes of this symptom in this circuit
4. Step-by-step troubleshooting procedure

Be specific about which wires to check, what voltages to measure, etc."""

        return await self.provider.answer_question(image_path, prompt)

    async def extract_bill_of_materials(self, image_path: Path) -> Dict[str, Any]:
        """
        Extract a bill of materials from a schematic.

        Args:
            image_path: Path to schematic

        Returns:
            Dict with component list

        Example:
            >>> bom = await analyzer.extract_bill_of_materials(Path("print.png"))
            >>> print(bom['components'])
        """
        result = await self.provider.identify_components(image_path)

        return {
            "components": result["components"],
            "image": str(image_path),
            "provider": "claude"
        }

    async def compare_as_built_vs_design(
        self,
        design_schematic: Path,
        as_built_photo: Path
    ) -> str:
        """
        Compare design schematic vs as-built installation photo.

        Args:
            design_schematic: Path to original design drawing
            as_built_photo: Path to photo of actual installation

        Returns:
            Comparison analysis

        Example:
            >>> comparison = await analyzer.compare_as_built_vs_design(
            ...     Path("design.png"),
            ...     Path("installed.jpg")
            ... )
        """
        return await self.provider.compare_schematics(
            design_schematic,
            as_built_photo
        )

    async def get_safety_warnings(self, image_path: Path) -> str:
        """
        Identify safety hazards and warnings from schematic.

        Args:
            image_path: Path to schematic

        Returns:
            Safety analysis

        Example:
            >>> warnings = await analyzer.get_safety_warnings(Path("circuit.png"))
        """
        prompt = """Analyze this schematic for safety considerations:

1. **Electrical Hazards:**
   - High voltage points
   - Arc flash risks
   - Shock hazards

2. **Required PPE:**
   - What personal protective equipment is needed?
   - Voltage rating requirements

3. **Lockout/Tagout Points:**
   - Where to disconnect power?
   - Multiple energy sources?

4. **Safe Troubleshooting:**
   - What can be measured safely while energized?
   - What MUST be de-energized first?

Be specific and err on the side of caution."""

        return await self.provider.answer_question(image_path, prompt)

    async def suggest_improvements(self, image_path: Path) -> str:
        """
        Suggest design improvements or code compliance issues.

        Args:
            image_path: Path to schematic

        Returns:
            Improvement suggestions

        Example:
            >>> suggestions = await analyzer.suggest_improvements(Path("old_design.png"))
        """
        prompt = """Review this schematic for potential improvements:

1. **Code Compliance:**
   - NEC violations or concerns
   - Missing safety features

2. **Reliability:**
   - Components that commonly fail
   - Redundancy opportunities

3. **Efficiency:**
   - Energy waste
   - Better component selection

4. **Maintainability:**
   - Hard-to-service areas
   - Better wire labeling

Be constructive and specific."""

        return await self.provider.answer_question(image_path, prompt)

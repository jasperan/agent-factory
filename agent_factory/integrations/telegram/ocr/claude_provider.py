"""Claude Vision Provider for OCR and schematic analysis."""

import os
import base64
from pathlib import Path
from typing import Optional, Dict, Any

import anthropic


class ClaudeVisionProvider:
    """
    Claude Vision provider for analyzing technical schematics and prints.

    Uses Claude Sonnet 4 (vision) to:
    - Extract component information from schematics
    - Analyze wiring diagrams
    - Identify voltage/current ratings
    - Answer questions about technical drawings
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude Vision provider.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.client = anthropic.Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        )
        self.model = "claude-sonnet-4-20250514"  # Latest with vision
        self.max_tokens = 4096

    async def analyze_image(
        self,
        image_path: Path,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze technical schematic/print with Claude Vision.

        Args:
            image_path: Path to image file (PNG, JPEG, etc.)
            query: Optional specific question about the image

        Returns:
            Dict with 'text' (analysis) and 'provider' ('claude')

        Raises:
            FileNotFoundError: If image doesn't exist
            Exception: If Claude API call fails
        """
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Default prompt for technical schematics
        if query is None:
            prompt = """Analyze this technical schematic/print and extract:

1. **Components:**
   - Relays, motors, contactors, sensors, switches
   - Part numbers if visible
   - Component ratings (voltage, current, HP, etc.)

2. **Connections:**
   - How components are wired together
   - Control circuits vs power circuits
   - Wire colors and numbers

3. **Circuit Function:**
   - What does this circuit do?
   - What happens when activated?
   - Any safety interlocks or protections?

4. **Troubleshooting Insights:**
   - Common failure points
   - What to check if circuit isn't working
   - Key voltages/signals to measure

Be specific and technical. Use electrician/technician language."""
        else:
            prompt = query

        # Read and encode image
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode()

        # Determine media type
        media_type = self._get_media_type(image_path)

        try:
            # Call Claude Vision API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }]
            )

            # Extract text from response
            analysis_text = response.content[0].text

            return {
                "text": analysis_text,
                "provider": "claude",
                "model": self.model,
                "metadata": {
                    "image_path": str(image_path),
                    "query": query or "default_analysis"
                }
            }

        except Exception as e:
            raise Exception(f"Claude Vision analysis failed: {str(e)}") from e

    async def answer_question(
        self,
        image_path: Path,
        question: str
    ) -> str:
        """
        Answer a specific question about a schematic.

        Args:
            image_path: Path to schematic/print
            question: User's question

        Returns:
            Claude's answer as text

        Example:
            >>> answer = await provider.answer_question(
            ...     Path("motor_circuit.png"),
            ...     "What voltage does this motor run on?"
            ... )
            "This is a 480V 3-phase motor circuit..."
        """
        result = await self.analyze_image(image_path, query=question)
        return result["text"]

    async def identify_components(self, image_path: Path) -> Dict[str, Any]:
        """
        Extract structured component list from schematic.

        Args:
            image_path: Path to schematic

        Returns:
            Dict with component details
        """
        prompt = """List all components in this schematic in the following JSON-like format:

Components:
- Name: [component name]
  Type: [relay/motor/contactor/sensor/etc]
  Rating: [voltage/current/HP if visible]
  Symbol: [electrical symbol used]

Be exhaustive - list every component you can identify."""

        result = await self.analyze_image(image_path, query=prompt)

        return {
            "components": result["text"],
            "provider": "claude"
        }

    def _get_media_type(self, image_path: Path) -> str:
        """
        Determine media type from file extension.

        Args:
            image_path: Path to image

        Returns:
            Media type string (e.g., 'image/png')
        """
        suffix = image_path.suffix.lower()

        media_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }

        return media_types.get(suffix, "image/jpeg")  # Default to JPEG

    async def compare_schematics(
        self,
        schematic1: Path,
        schematic2: Path
    ) -> str:
        """
        Compare two schematics and highlight differences.

        Args:
            schematic1: First schematic
            schematic2: Second schematic

        Returns:
            Comparison analysis

        Note: This requires sequential calls since Claude doesn't support
        multiple images in one message yet. We analyze both separately
        then ask for comparison.
        """
        # Analyze first schematic
        analysis1 = await self.analyze_image(schematic1)

        # Analyze second schematic with reference to first
        comparison_prompt = f"""This is the second schematic. Compare it to this first schematic analysis:

{analysis1['text']}

What are the key differences? What changed?"""

        analysis2 = await self.analyze_image(schematic2, query=comparison_prompt)

        return analysis2["text"]

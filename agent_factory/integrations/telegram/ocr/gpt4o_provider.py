"""
GPT-4o Vision OCR Provider

Extracts equipment data from industrial nameplates using OpenAI GPT-4o Vision API.
"""

import os
import json
import base64
from datetime import datetime
from typing import Optional
from openai import AsyncOpenAI

from .providers import OCRProvider, OCRResult


# Enhanced prompt with examples for better extraction accuracy
ENHANCED_EXTRACTION_PROMPT = """This is an industrial equipment nameplate/label. Extract equipment data accurately.

EXAMPLES OF GOOD EXTRACTION:
✅ Input: "SIEMENS G120C 6SL3244-0BB13-1PA0 480V 3PH 60Hz"
   Output: {
     "manufacturer": "Siemens",
     "model_number": "G120C",
     "serial_number": null,
     "fault_code": null,
     "voltage": "480V",
     "phase": "3",
     "other_text": "6SL3244-0BB13-1PA0 60Hz"
   }

✅ Input: "Allen-Bradley PowerFlex 525 SER. A FRN 11.001"
   Output: {
     "manufacturer": "Allen-Bradley",
     "model_number": "PowerFlex 525",
     "serial_number": "SER. A",
     "fault_code": null,
     "other_text": "FRN 11.001"
   }

IMPORTANT RULES:
❌ DON'T add units if not visible: "480" (wrong) vs "480V" (correct)
❌ DON'T guess model from logo alone: use null if text not readable
❌ DON'T invent serial numbers
✅ DO include units exactly as shown (V, A, HP, Hz)
✅ DO return null for fields not clearly visible
✅ DO preserve exact text formatting

RESPOND IN THIS JSON FORMAT:
{
  "manufacturer": "exact company name or null",
  "model_number": "exact model/catalog number or null",
  "serial_number": "exact serial number or null",
  "fault_code": "fault/error code if visible on display or null",
  "other_text": "any other relevant text from nameplate"
}

If you cannot read the image clearly, explain why in other_text and set all fields to null.
"""


class GPT4oProvider(OCRProvider):
    """OCR provider using OpenAI GPT-4o Vision API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize GPT-4o provider.

        Args:
            api_key: OpenAI API key (or None to use OPENAI_API_KEY env var)
        """
        super().__init__(api_key)

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.provider_name = "gpt4o"

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set and no API key provided")

        self.client = AsyncOpenAI(api_key=self.api_key)

    async def extract(self, image_bytes: bytes) -> OCRResult:
        """
        Extract equipment data from image using GPT-4o Vision.

        Args:
            image_bytes: Raw image bytes (JPEG, PNG, etc.)

        Returns:
            OCRResult with extracted data and metadata

        Raises:
            Exception if API call fails
        """
        start_time = datetime.utcnow()

        try:
            # Encode image to base64
            image_data = base64.b64encode(image_bytes).decode("utf-8")

            # Call GPT-4o Vision API
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": ENHANCED_EXTRACTION_PROMPT
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )

            # Parse response
            ocr_text = response.choices[0].message.content
            processing_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Parse JSON (handle markdown code fences)
            data = self._parse_json_response(ocr_text)

            # Build OCRResult
            result = OCRResult(
                manufacturer=data.get("manufacturer"),
                model_number=data.get("model_number"),
                serial_number=data.get("serial_number"),
                fault_code=data.get("fault_code"),
                voltage=data.get("voltage"),
                phase=data.get("phase"),
                raw_text=data.get("other_text", ocr_text),
                confidence=self._calculate_confidence(data, data.get("other_text", "")),
                provider=self.provider_name,
                processing_time_ms=processing_ms,
            )

            return result

        except Exception as e:
            processing_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            return OCRResult(
                confidence=0.0,
                provider=self.provider_name,
                processing_time_ms=processing_ms,
                error=f"GPT-4o extraction failed: {str(e)}"
            )

    def _parse_json_response(self, ocr_text: str) -> dict:
        """
        Parse JSON from OCR response, handling markdown code fences.

        Args:
            ocr_text: Raw response from GPT-4o

        Returns:
            Parsed dictionary

        Raises:
            json.JSONDecodeError if parsing fails
        """
        # Strip markdown code fences if present
        cleaned = ocr_text.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]  # Remove ```json
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]  # Remove ```

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]  # Remove trailing ```

        cleaned = cleaned.strip()

        # Parse JSON
        data = json.loads(cleaned)

        # Clean string fields (strip whitespace, convert empty to None)
        for key in ["manufacturer", "model_number", "serial_number", "fault_code", "voltage", "phase", "other_text"]:
            if key in data and isinstance(data[key], str):
                data[key] = data[key].strip() or None

        return data

    def is_available(self) -> bool:
        """Check if GPT-4o provider is configured."""
        return self.api_key is not None

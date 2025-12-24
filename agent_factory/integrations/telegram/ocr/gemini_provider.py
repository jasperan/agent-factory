"""
Gemini Vision OCR Provider

Extracts equipment data from industrial nameplates using Google Gemini Vision API.
Uses Gemini 1.5 Flash (free tier: 15 RPM, 1M tokens/day).
"""

import os
import json
import re
from datetime import datetime
from typing import Optional
import google.generativeai as genai

from .providers import OCRProvider, OCRResult


# Enhanced prompt matching GPT-4o format for consistency
GEMINI_EXTRACTION_PROMPT = """You are an industrial maintenance expert analyzing equipment photos.

Extract ALL relevant information from this industrial equipment nameplate/label.

RESPOND IN THIS EXACT JSON FORMAT:
{
  "manufacturer": "company name or null",
  "model_number": "exact model/catalog number or null",
  "serial_number": "exact serial number or null",
  "fault_code": "error code if visible on display or null",

  "equipment_type": "vfd | motor | contactor | pump | plc | relay | breaker | sensor | valve | compressor | robot | conveyor | transformer | other | null",
  "equipment_subtype": "more specific type if identifiable (e.g., 'servo motor', 'safety relay') or null",

  "condition": "new | good | worn | damaged | burnt | corroded | unknown",
  "visible_issues": [
    "specific observable problems",
    "e.g., 'burnt terminal on T1'",
    "e.g., 'loose wire connection'"
  ],

  "voltage": "voltage rating if visible (e.g., '480V', '208-230/460V') or null",
  "current": "current rating if visible (e.g., '15A') or null",
  "horsepower": "HP rating if visible (e.g., '5HP') or null",
  "phase": "phase if visible ('1' or '3') or null",

  "additional_specs": {
    "frequency": "60Hz or 50Hz if visible",
    "rpm": "speed rating if visible",
    "frame": "frame size if visible",
    "ip_rating": "IP rating if visible"
  },

  "raw_text": "ALL visible text transcribed, preserving what you can read",

  "confidence": 0.0 to 1.0
}

IMPORTANT RULES:
- For equipment_type "vfd" or "motor": extract voltage, HP, phase carefully
- Be specific about visible_issues - technicians need actionable observations
- Extract ALL text you can read into raw_text
- If you can't determine something, use null (not empty string)
- Include units exactly as shown (V, A, HP, Hz, etc.)

Analyze this industrial equipment photo:
"""


class GeminiProvider(OCRProvider):
    """OCR provider using Google Gemini Vision API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini provider.

        Args:
            api_key: Gemini API key (or None to use GEMINI_API_KEY env var)
        """
        super().__init__(api_key)

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.provider_name = "gemini"

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set and no API key provided")

        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    async def extract(self, image_bytes: bytes) -> OCRResult:
        """
        Extract equipment data from image using Gemini Vision.

        Args:
            image_bytes: Raw image bytes (JPEG, PNG, etc.)

        Returns:
            OCRResult with extracted data and metadata

        Raises:
            Exception if API call fails
        """
        start_time = datetime.utcnow()

        try:
            # Convert bytes to Gemini-compatible format
            import base64
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')

            # Call Gemini Vision API
            response = await self.model.generate_content_async([
                GEMINI_EXTRACTION_PROMPT,
                {"mime_type": "image/jpeg", "data": image_b64}
            ])

            ocr_text = response.text
            processing_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Parse JSON
            data = self._parse_json_response(ocr_text)

            # Build OCRResult
            result = OCRResult(
                manufacturer=data.get("manufacturer"),
                model_number=data.get("model_number"),
                serial_number=data.get("serial_number"),
                fault_code=data.get("fault_code"),
                equipment_type=data.get("equipment_type"),
                condition=data.get("condition", "unknown"),
                visible_issues=data.get("visible_issues", []),
                voltage=data.get("voltage"),
                current=data.get("current"),
                horsepower=data.get("horsepower"),
                phase=data.get("phase"),
                additional_specs=data.get("additional_specs", {}),
                raw_text=data.get("raw_text"),
                confidence=data.get("confidence", 0.0),
                provider=self.provider_name,
                processing_time_ms=processing_ms,
            )

            # If Gemini didn't provide confidence, calculate it
            if result.confidence == 0.0:
                result.confidence = self._calculate_confidence(data, result.raw_text or "")

            return result

        except Exception as e:
            processing_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            return OCRResult(
                confidence=0.0,
                provider=self.provider_name,
                processing_time_ms=processing_ms,
                error=f"Gemini extraction failed: {str(e)}"
            )

    def _parse_json_response(self, ocr_text: str) -> dict:
        """
        Parse JSON from Gemini response, handling markdown code fences.

        Args:
            ocr_text: Raw response from Gemini

        Returns:
            Parsed dictionary

        Raises:
            json.JSONDecodeError if parsing fails
        """
        # Remove markdown code blocks
        text = re.sub(r'```json\s*', '', ocr_text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()

        try:
            data = json.loads(text)

            # Clean string fields
            for key in ["manufacturer", "model_number", "serial_number", "fault_code",
                        "equipment_type", "equipment_subtype", "condition",
                        "voltage", "current", "horsepower", "phase", "raw_text"]:
                if key in data and isinstance(data[key], str):
                    cleaned = data[key].strip()
                    data[key] = cleaned if cleaned else None

            # Ensure visible_issues is a list
            if "visible_issues" not in data:
                data["visible_issues"] = []
            elif not isinstance(data["visible_issues"], list):
                data["visible_issues"] = []

            # Ensure additional_specs is a dict
            if "additional_specs" not in data:
                data["additional_specs"] = {}
            elif not isinstance(data["additional_specs"], dict):
                data["additional_specs"] = {}

            return data

        except json.JSONDecodeError as e:
            # If JSON parsing fails, return minimal valid structure
            return {
                "manufacturer": None,
                "model_number": None,
                "serial_number": None,
                "fault_code": None,
                "raw_text": ocr_text[:500],  # Save first 500 chars
                "confidence": 0.0,
            }

    def is_available(self) -> bool:
        """Check if Gemini provider is configured."""
        return self.api_key is not None

"""
OCR Provider Base Classes and Data Models

Unified interface for multiple OCR providers (GPT-4o Vision, Gemini Vision).
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
from datetime import datetime


# Manufacturer alias mapping (normalize vendor names)
MANUFACTURER_ALIASES = {
    "rockwell automation": "allen_bradley",
    "rockwell": "allen_bradley",
    "a-b": "allen_bradley",
    "ab": "allen_bradley",
    "allen-bradley": "allen_bradley",
    "square d": "schneider_electric",
    "schneider": "schneider_electric",
    "cutler-hammer": "eaton",
    "westinghouse": "eaton",
    "ge": "general_electric",
    "ge fanuc": "general_electric",
    "abb": "abb",
    "siemens": "siemens",
    "omron": "omron",
    "mitsubishi": "mitsubishi",
    "yaskawa": "yaskawa",
    "fanuc": "fanuc",
    "delta": "delta",
    "fuji": "fuji_electric",
    "schneider electric": "schneider_electric",
}


def normalize_manufacturer(name: str) -> Optional[str]:
    """
    Map manufacturer aliases to canonical names.

    Args:
        name: Raw manufacturer name from OCR

    Returns:
        Canonical manufacturer name or None

    Examples:
        "Rockwell Automation" → "allen_bradley"
        "Square D" → "schneider_electric"
        "Siemens" → "siemens"
    """
    if not name:
        return None

    name_lower = name.lower().strip()
    return MANUFACTURER_ALIASES.get(name_lower, name_lower.replace(" ", "_"))


def normalize_model_number(model: str) -> Optional[str]:
    """
    Standardize model number format for KB matching.

    Args:
        model: Raw model number from OCR

    Returns:
        Normalized model number (uppercase, no hyphens/spaces)

    Examples:
        "G-120C" → "G120C"
        "S7 1200" → "S71200"
        "PowerFlex 525" → "POWERFLEX525"
    """
    if not model:
        return None

    # Remove hyphens, spaces, uppercase
    normalized = model.replace("-", "").replace(" ", "").upper()
    return normalized if normalized else None


def calculate_confidence(data: dict, raw_text: str) -> float:
    """
    Calculate OCR confidence based on extracted fields and text quality.

    Args:
        data: Extracted equipment data (manufacturer, model, etc.)
        raw_text: Raw OCR text

    Returns:
        Confidence score 0.0-0.95 (never 1.0 to indicate uncertainty)

    Scoring:
        - Manufacturer: +0.25
        - Model number: +0.30 (most critical for KB matching)
        - Serial number: +0.15
        - Electrical specs with units: +0.10
        - Sufficient text (≥20 chars): +0.10
        - Format validation (phase, etc.): +0.10
    """
    confidence = 0.0

    # Field presence (0.80 total)
    if data.get("manufacturer"):
        confidence += 0.25

    if data.get("model_number"):
        confidence += 0.30  # Most critical for KB matching

    if data.get("serial_number"):
        confidence += 0.15

    # Electrical specs with validation (0.10 total)
    voltage = data.get("voltage")
    if voltage and "V" in str(voltage):
        confidence += 0.10

    # Text quantity penalty/bonus (0.10 total)
    if len(raw_text) >= 20:
        confidence += 0.10
    elif len(raw_text) < 10:
        confidence *= 0.5  # Severe penalty for very little text

    # Format validation (0.10 total)
    phase = data.get("phase")
    if phase and str(phase) in ["1", "3"]:
        confidence += 0.05

    # Normalized manufacturer match (bonus)
    if data.get("manufacturer"):
        normalized = normalize_manufacturer(data["manufacturer"])
        if normalized in MANUFACTURER_ALIASES.values():
            confidence += 0.05

    # Cap at 95% (never 100% to indicate uncertainty)
    return min(0.95, confidence)


@dataclass
class OCRResult:
    """
    Unified OCR result from any provider (GPT-4o, Gemini, etc.).

    Contains all extracted equipment data plus metadata about the OCR process.
    """

    # Equipment identification
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    serial_number: Optional[str] = None
    fault_code: Optional[str] = None

    # Additional equipment data
    equipment_type: Optional[str] = None  # "vfd", "motor", "plc", "contactor", etc.
    condition: Optional[str] = None  # "new", "good", "worn", "damaged", "burnt", etc.
    visible_issues: List[str] = field(default_factory=list)

    # Electrical specifications
    voltage: Optional[str] = None
    current: Optional[str] = None
    horsepower: Optional[str] = None
    phase: Optional[str] = None

    # Additional specs
    additional_specs: Dict[str, Any] = field(default_factory=dict)

    # Raw OCR data
    raw_text: Optional[str] = None

    # Quality metrics
    confidence: float = 0.0  # 0.0-1.0
    provider: str = "unknown"  # "gpt4o", "gemini", etc.
    processing_time_ms: int = 0

    # Error handling
    error: Optional[str] = None

    def normalize(self):
        """Normalize manufacturer and model number for KB matching."""
        if self.manufacturer:
            self.manufacturer = normalize_manufacturer(self.manufacturer)

        if self.model_number:
            self.model_number = normalize_model_number(self.model_number)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "manufacturer": self.manufacturer,
            "model_number": self.model_number,
            "serial_number": self.serial_number,
            "fault_code": self.fault_code,
            "equipment_type": self.equipment_type,
            "condition": self.condition,
            "visible_issues": self.visible_issues,
            "voltage": self.voltage,
            "current": self.current,
            "horsepower": self.horsepower,
            "phase": self.phase,
            "additional_specs": self.additional_specs,
            "raw_text": self.raw_text,
            "confidence": self.confidence,
            "provider": self.provider,
            "processing_time_ms": self.processing_time_ms,
            "error": self.error,
        }


class OCRProvider(ABC):
    """
    Abstract base class for OCR providers.

    All providers (GPT-4o, Gemini, etc.) must implement this interface.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OCR provider.

        Args:
            api_key: API key for the provider (or None to use env var)
        """
        self.api_key = api_key
        self.provider_name = "unknown"

    @abstractmethod
    async def extract(self, image_bytes: bytes) -> OCRResult:
        """
        Extract equipment data from image bytes.

        Args:
            image_bytes: Raw image data (JPEG, PNG, etc.)

        Returns:
            OCRResult with extracted data and metadata

        Raises:
            Exception if OCR fails (caught by pipeline for fallback)
        """
        pass

    def _calculate_confidence(self, data: dict, raw_text: str) -> float:
        """Helper to calculate confidence score."""
        return calculate_confidence(data, raw_text)

    def is_available(self) -> bool:
        """
        Check if provider is configured and available.

        Returns:
            True if API key is set and provider can be used
        """
        return self.api_key is not None

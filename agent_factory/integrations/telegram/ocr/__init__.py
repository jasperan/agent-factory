"""
OCR Module - Dual Provider Photo Analysis for Equipment Nameplates

Public API:
    - OCRPipeline: Main pipeline with GPT-4o → Gemini fallback
    - OCRResult: Unified result dataclass
    - OCRProvider: Base class for providers (extensible)

Usage:
    from agent_factory.integrations.telegram.ocr import OCRPipeline

    pipeline = OCRPipeline()
    result = await pipeline.analyze_photo(image_bytes)

    print(f"Manufacturer: {result.manufacturer}")
    print(f"Model: {result.model_number}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Provider used: {result.provider}")
"""

from .pipeline import OCRPipeline, validate_photo_quality
from .providers import (
    OCRResult,
    OCRProvider,
    normalize_manufacturer,
    normalize_model_number,
    calculate_confidence,
)
from .gpt4o_provider import GPT4oProvider
from .gemini_provider import GeminiProvider


__all__ = [
    # Main pipeline
    "OCRPipeline",
    "validate_photo_quality",

    # Data models
    "OCRResult",

    # Base classes (for extensibility)
    "OCRProvider",

    # Providers
    "GPT4oProvider",
    "GeminiProvider",

    # Utilities
    "normalize_manufacturer",
    "normalize_model_number",
    "calculate_confidence",
]

"""
OCR Pipeline - Dual Provider Orchestration

Manages GPT-4o (primary) → Gemini (fallback) OCR flow with quality validation.
"""

import os
from typing import Optional, Tuple
from datetime import datetime
import logging

from .providers import OCRResult
from .gpt4o_provider import GPT4oProvider
from .gemini_provider import GeminiProvider

# LangSmith tracing
try:
    from langsmith import traceable
    from langsmith.run_helpers import get_current_run_tree
    LANGSMITH_AVAILABLE = True
except ImportError:
    # Graceful degradation if langsmith not installed
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    def get_current_run_tree():
        return None
    LANGSMITH_AVAILABLE = False


logger = logging.getLogger(__name__)


def validate_photo_quality(image_bytes: bytes) -> Tuple[bool, str]:
    """
    Check if photo is suitable for OCR before API call.

    Args:
        image_bytes: Raw image bytes

    Returns:
        (is_valid, message) tuple

    Quality checks:
        - Min resolution: 400x400
        - Not too dark (histogram check)
        - Not too bright/overexposed
        - Valid JPEG/PNG
    """
    try:
        from PIL import Image
        import io

        img = Image.open(io.BytesIO(image_bytes))

        # Min resolution check
        if img.width < 400 or img.height < 400:
            return False, f"Image too small ({img.width}x{img.height}, min 400x400)"

        # Convert to grayscale for brightness analysis
        gray = img.convert('L')
        histogram = gray.histogram()

        # Too dark check (80%+ pixels in bottom 30% of brightness range)
        dark_pixels = sum(histogram[:77])  # 0-76 out of 0-255
        total_pixels = sum(histogram)

        if dark_pixels / total_pixels > 0.8:
            return False, "Image too dark (poor lighting)"

        # Too bright check (80%+ pixels in top 30% of brightness range)
        bright_pixels = sum(histogram[178:])  # 178-255 out of 0-255

        if bright_pixels / total_pixels > 0.8:
            return False, "Image too bright/overexposed"

        return True, "OK"

    except Exception as e:
        # If validation fails, allow OCR to proceed (don't block on validation error)
        logger.warning(f"Photo quality validation failed: {e}")
        return True, "Validation skipped"


class OCRPipeline:
    """
    Main OCR pipeline with dual provider fallback.

    Flow:
        1. Validate photo quality
        2. Try GPT-4o (primary)
        3. If confidence < threshold or error, try Gemini (fallback)
        4. Return best result
    """

    def __init__(
        self,
        gpt4o_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        fallback_threshold: float = 0.5
    ):
        """
        Initialize OCR pipeline with dual providers.

        Args:
            gpt4o_api_key: OpenAI API key (or None for env var)
            gemini_api_key: Gemini API key (or None for env var)
            fallback_threshold: Confidence threshold to trigger fallback (default 0.5)
        """
        self.fallback_threshold = fallback_threshold

        # Initialize GPT-4o provider (primary)
        try:
            self.gpt4o_provider = GPT4oProvider(api_key=gpt4o_api_key)
            logger.info("[OCR Pipeline] GPT-4o provider initialized")
        except ValueError:
            logger.warning("[OCR Pipeline] GPT-4o provider unavailable (no API key)")
            self.gpt4o_provider = None

        # Initialize Gemini provider (fallback)
        try:
            self.gemini_provider = GeminiProvider(api_key=gemini_api_key)
            logger.info("[OCR Pipeline] Gemini provider initialized")
        except ValueError:
            logger.warning("[OCR Pipeline] Gemini provider unavailable (no API key)")
            self.gemini_provider = None

    @traceable(
        run_type="tool",
        name="OCR.analyze_photo",
        tags=["ocr", "photo-processing"]
    )
    async def analyze_photo(
        self,
        image_bytes: bytes,
        user_id: Optional[str] = None,
        skip_quality_check: bool = False
    ) -> OCRResult:
        """
        Analyze equipment photo with dual OCR fallback.

        Args:
            image_bytes: Raw image bytes (JPEG, PNG, etc.)
            user_id: User ID for logging (optional)
            skip_quality_check: Skip quality validation (default False)

        Returns:
            OCRResult with best extraction from available providers

        Flow:
            1. Quality check (unless skipped)
            2. Try GPT-4o (primary)
            3. If GPT-4o fails or low confidence, try Gemini
            4. Return best result
        """
        pipeline_start = datetime.utcnow()
        user_log = f"[{user_id}]" if user_id else "[OCR]"

        # Step 1: Quality check
        if not skip_quality_check:
            quality_ok, quality_msg = validate_photo_quality(image_bytes)

            if not quality_ok:
                logger.warning(f"{user_log} Quality check failed: {quality_msg}")
                return OCRResult(
                    confidence=0.0,
                    provider="quality_check",
                    error=quality_msg,
                    processing_time_ms=0
                )
        else:
            quality_msg = "Skipped"

        logger.info(f"{user_log} Quality check: {quality_msg}")

        # Step 2: Try GPT-4o (primary)
        primary_result = None
        fallback_triggered = False

        if self.gpt4o_provider and self.gpt4o_provider.is_available():
            try:
                logger.info(f"{user_log} Trying GPT-4o (primary)")
                primary_result = await self.gpt4o_provider.extract(image_bytes)

                logger.info(
                    f"{user_log} GPT-4o result: "
                    f"confidence={primary_result.confidence:.2f}, "
                    f"manufacturer={primary_result.manufacturer}, "
                    f"model={primary_result.model_number}"
                )

                # Check if result is good enough
                if primary_result.confidence >= self.fallback_threshold and not primary_result.error:
                    # Success with GPT-4o
                    total_ms = int((datetime.utcnow() - pipeline_start).total_seconds() * 1000)
                    primary_result.processing_time_ms = total_ms

                    logger.info(f"{user_log} GPT-4o success (confidence {primary_result.confidence:.2f})")
                    return primary_result

                else:
                    # Low confidence or error - trigger fallback
                    fallback_triggered = True
                    logger.warning(
                        f"{user_log} GPT-4o below threshold "
                        f"(confidence={primary_result.confidence:.2f}, error={primary_result.error})"
                    )

            except Exception as e:
                fallback_triggered = True
                logger.error(f"{user_log} GPT-4o failed: {e}")

        else:
            fallback_triggered = True
            logger.warning(f"{user_log} GPT-4o provider unavailable")

        # Step 3: Try Gemini (fallback)
        fallback_result = None

        if fallback_triggered and self.gemini_provider and self.gemini_provider.is_available():
            try:
                logger.info(f"{user_log} Trying Gemini (fallback)")
                fallback_result = await self.gemini_provider.extract(image_bytes)

                logger.info(
                    f"{user_log} Gemini result: "
                    f"confidence={fallback_result.confidence:.2f}, "
                    f"manufacturer={fallback_result.manufacturer}, "
                    f"model={fallback_result.model_number}"
                )

            except Exception as e:
                logger.error(f"{user_log} Gemini failed: {e}")

        # Step 4: Return best result
        total_ms = int((datetime.utcnow() - pipeline_start).total_seconds() * 1000)

        # Choose best result
        if fallback_result and primary_result:
            # Both available - pick higher confidence
            if fallback_result.confidence > primary_result.confidence:
                logger.info(f"{user_log} Using Gemini result (better confidence)")
                final_result = fallback_result
            else:
                logger.info(f"{user_log} Using GPT-4o result (better confidence)")
                final_result = primary_result

        elif fallback_result:
            logger.info(f"{user_log} Using Gemini result (only option)")
            final_result = fallback_result

        elif primary_result:
            logger.info(f"{user_log} Using GPT-4o result (only option)")
            final_result = primary_result

        else:
            # Both failed
            logger.error(f"{user_log} All OCR providers failed")
            return OCRResult(
                confidence=0.0,
                provider="all_failed",
                error="All OCR providers unavailable or failed",
                processing_time_ms=total_ms
            )

        # Update total processing time
        final_result.processing_time_ms = total_ms

        logger.info(
            f"{user_log} Final OCR result: "
            f"provider={final_result.provider}, "
            f"confidence={final_result.confidence:.2f}, "
            f"time={total_ms}ms"
        )

        # Add LangSmith trace metadata
        if LANGSMITH_AVAILABLE:
            run_tree = get_current_run_tree()
            if run_tree:
                run_tree.metadata.update({
                    "user_id": user_id,
                    "image_size_bytes": len(image_bytes),
                    "quality_check": quality_msg if not skip_quality_check else "Skipped",
                    "primary_provider": "gpt4o",
                    "primary_confidence": primary_result.confidence if primary_result else 0.0,
                    "fallback_triggered": fallback_triggered,
                    "fallback_provider": "gemini" if fallback_triggered else None,
                    "provider_used": final_result.provider,
                    "manufacturer": final_result.manufacturer,
                    "model_number": final_result.model_number,
                    "serial_number": final_result.serial_number,
                    "confidence": final_result.confidence,
                    "processing_ms": total_ms,
                    "has_error": final_result.error is not None,
                })

                # Add tags for equipment type and manufacturer
                if final_result.equipment_type:
                    run_tree.tags.append(f"equipment:{final_result.equipment_type}")
                if final_result.manufacturer:
                    run_tree.tags.append(f"manufacturer:{final_result.manufacturer.lower().replace(' ', '_')}")
                if final_result.provider:
                    run_tree.tags.append(f"provider:{final_result.provider}")

        return final_result

    def get_available_providers(self) -> list:
        """Get list of available provider names."""
        providers = []

        if self.gpt4o_provider and self.gpt4o_provider.is_available():
            providers.append("gpt4o")

        if self.gemini_provider and self.gemini_provider.is_available():
            providers.append("gemini")

        return providers

    def is_any_provider_available(self) -> bool:
        """Check if at least one OCR provider is configured."""
        return len(self.get_available_providers()) > 0

"""
Integration tests for OCR Pipeline E2E flow

Tests OCR extraction, KB search with model filtering, and library auto-fill.
Requires OPENAI_API_KEY in environment.
"""

import asyncio
import os
from pathlib import Path

from agent_factory.integrations.telegram.ocr import OCRPipeline, OCRResult
from agent_factory.rivet_pro.rag.retriever import search_docs
from agent_factory.rivet_pro.models import RivetIntent, VendorType, EquipmentType, KBCoverage as RivetKBCoverage


async def test_ocr_pipeline():
    """Test OCR pipeline initialization and provider detection"""
    print("\n=== Test 1: OCR Pipeline Initialization ===")

    pipeline = OCRPipeline()
    providers = pipeline.get_available_providers()

    print(f"Available providers: {providers}")
    assert "gpt4o" in providers, "GPT-4o provider should be available"
    print("[OK] OCR Pipeline initialized successfully")

    return pipeline


async def test_ocr_with_sample_image(pipeline: OCRPipeline):
    """Test OCR extraction with a sample industrial nameplate image"""
    print("\n=== Test 2: OCR Extraction ===")

    # Check if test image exists
    test_image_path = Path("tests/fixtures/sample_nameplate.jpg")

    if not test_image_path.exists():
        print(f"[SKIP] Test image not found at {test_image_path}")
        print("  To test OCR extraction, add a sample industrial nameplate image")
        print("  Expected location: tests/fixtures/sample_nameplate.jpg")
        return None

    # Read image
    with open(test_image_path, "rb") as f:
        image_bytes = f.read()

    # Run OCR
    print(f"Processing image: {test_image_path}")
    result = await pipeline.analyze_photo(image_bytes, user_id="test_user")

    # Display results
    print(f"\nOCR Results:")
    print(f"  Provider: {result.provider}")
    print(f"  Confidence: {result.confidence:.2%}")
    print(f"  Manufacturer: {result.manufacturer or 'Not detected'}")
    print(f"  Model: {result.model_number or 'Not detected'}")
    print(f"  Serial: {result.serial_number or 'Not detected'}")
    print(f"  Equipment Type: {result.equipment_type or 'Not detected'}")
    print(f"  Processing Time: {result.processing_time_ms}ms")

    if result.error:
        print(f"  [WARN] Error: {result.error}")

    assert result.confidence > 0.0, "OCR should return non-zero confidence"
    print("[OK] OCR extraction completed")

    return result


def test_kb_search_with_model_filter(ocr_result: OCRResult):
    """Test KB search with model number from OCR"""
    print("\n=== Test 3: KB Search with Model Filtering ===")

    if not ocr_result or not ocr_result.manufacturer:
        print("[SKIP] KB search test (no manufacturer from OCR)")
        return

    # Map manufacturer to VendorType
    vendor_map = {
        "siemens": VendorType.SIEMENS,
        "allen_bradley": VendorType.ALLEN_BRADLEY,
        "rockwell": VendorType.ALLEN_BRADLEY,
        "schneider": VendorType.SCHNEIDER_ELECTRIC,
        "mitsubishi": VendorType.MITSUBISHI,
    }

    manufacturer_lower = ocr_result.manufacturer.lower().replace(" ", "_")
    vendor = vendor_map.get(manufacturer_lower, VendorType.SIEMENS)

    # Create intent
    intent = RivetIntent(
        vendor=vendor,
        equipment_type=EquipmentType.VFD,
        symptom=f"troubleshooting {ocr_result.model_number or 'VFD'}",
        raw_summary=f"{ocr_result.manufacturer} {ocr_result.model_number or 'VFD'} troubleshooting",
        context_source="text_only",
        confidence=0.9,
        kb_coverage=RivetKBCoverage.NONE
    )

    # Search without model filter
    print(f"\nSearching KB for: {intent.raw_summary}")
    docs_without_filter = search_docs(intent)
    print(f"Results without model filter: {len(docs_without_filter)} documents")

    # Search with model filter
    if ocr_result.model_number:
        docs_with_filter = search_docs(intent, model_number=ocr_result.model_number)
        print(f"Results with model filter ({ocr_result.model_number}): {len(docs_with_filter)} documents")

        if docs_with_filter:
            print(f"\nTop result:")
            top_doc = docs_with_filter[0]
            print(f"  Title: {top_doc.title}")
            print(f"  Vendor: {top_doc.vendor}")
            print(f"  Similarity: {top_doc.similarity:.3f}")

        print("[OK] KB search with model filtering completed")
    else:
        print("[SKIP] No model number from OCR, skipping filtered search")


def test_library_autofill_data(ocr_result: OCRResult):
    """Test that OCR result can be used for library auto-fill"""
    print("\n=== Test 4: Library Auto-fill Data ===")

    if not ocr_result:
        print("[SKIP] Library auto-fill test (no OCR result)")
        return

    # Simulate library auto-fill data structure
    machine_data = {
        'manufacturer': ocr_result.manufacturer,
        'model_number': ocr_result.model_number,
        'serial_number': ocr_result.serial_number,
        'ocr_confidence': ocr_result.confidence,
        'ocr_provider': ocr_result.provider
    }

    print(f"\nAuto-fill data from OCR:")
    for key, value in machine_data.items():
        print(f"  {key}: {value or 'Not detected'}")

    # Validate confidence threshold
    if ocr_result.confidence >= 0.5:
        print(f"\n[OK] Confidence {ocr_result.confidence:.2%} meets threshold for auto-fill")
    else:
        print(f"\n[WARN] Confidence {ocr_result.confidence:.2%} below threshold (0.5)")

    print("[OK] Library auto-fill data validated")


async def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("OCR Integration Tests - E2E Flow")
    print("=" * 60)

    # Test 1: Pipeline initialization
    pipeline = await test_ocr_pipeline()

    # Test 2: OCR extraction
    ocr_result = await test_ocr_with_sample_image(pipeline)

    # Test 3: KB search with model filtering
    test_kb_search_with_model_filter(ocr_result)

    # Test 4: Library auto-fill
    test_library_autofill_data(ocr_result)

    print("\n" + "=" * 60)
    print("All integration tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Check prerequisites
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set in environment")
        print("Run: export OPENAI_API_KEY=your_key")
        exit(1)

    # Run tests
    asyncio.run(run_all_tests())

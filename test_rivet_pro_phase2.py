"""
Standalone validation script for RIVET Pro Phase 2 (RAG Layer)

Tests configuration, filters, and model integration WITHOUT database dependencies.
Tests retriever functions separately when database is available.

Author: Agent Factory
Created: 2025-12-17
"""

import sys
sys.path.insert(0, '.')

from agent_factory.rivet_pro.models import (
    RivetIntent,
    VendorType,
    EquipmentType,
    ContextSource,
    KBCoverage
)
from agent_factory.rivet_pro.rag.config import RAGConfig
from agent_factory.rivet_pro.rag.filters import build_filters, build_keyword_filters


def test_rag_config():
    """Test RAG configuration"""
    print("\n[TEST] RAG Configuration")
    print("-" * 50)

    # Test default config
    config = RAGConfig()
    assert config.search.top_k == 8, "Default top_k should be 8"
    assert config.search.similarity_threshold == 0.55, "Default threshold should be 0.55"
    assert config.search.use_hybrid_search is True, "Hybrid search should be enabled by default"
    print(f"  [OK] Default config created (top_k={config.search.top_k}, threshold={config.search.similarity_threshold})")

    # Test collection matching
    collections = config.get_collections_for_intent(
        VendorType.SIEMENS,
        EquipmentType.VFD
    )
    assert len(collections) >= 1, "Should find at least one collection for Siemens VFD"
    assert any(c.name == "siemens" for c in collections), "Should match siemens collection"
    print(f"  [OK] Collection matching works ({len(collections)} collections for Siemens VFD)")

    # Test coverage assessment
    coverage_strong = config.assess_coverage(num_docs=5, avg_similarity=0.82)
    assert coverage_strong == KBCoverage.STRONG, "Should assess as strong coverage"
    print(f"  [OK] Coverage assessment: strong (5 docs, 0.82 similarity)")

    coverage_thin = config.assess_coverage(num_docs=2, avg_similarity=0.65)
    assert coverage_thin == KBCoverage.THIN, "Should assess as thin coverage"
    print(f"  [OK] Coverage assessment: thin (2 docs, 0.65 similarity)")

    coverage_none = config.assess_coverage(num_docs=0, avg_similarity=0.0)
    assert coverage_none == KBCoverage.NONE, "Should assess as no coverage"
    print(f"  [OK] Coverage assessment: none (0 docs)")

    print(f"\n[PASS] RAG Configuration - All tests passed")


def test_intent_filters():
    """Test intent-to-filter conversion"""
    print("\n[TEST] Intent-to-Filter Mapping")
    print("-" * 50)

    # Create test intent
    intent = RivetIntent(
        vendor=VendorType.SIEMENS,
        equipment_type=EquipmentType.VFD,
        detected_model="G120C",
        detected_fault_codes=["F3002"],
        application="overhead_crane",
        raw_summary="VFD fault troubleshooting",
        context_source=ContextSource.TEXT_ONLY,
        confidence=0.9,
        kb_coverage=KBCoverage.STRONG
    )

    # Test build_filters
    filters = build_filters(intent)
    assert filters["vendor"] == "Siemens", "Should filter by Siemens vendor"
    assert filters["equipment_type"] == "VFD", "Should filter by VFD equipment type"
    print(f"  [OK] build_filters() returned: {filters}")

    # Test with unknown vendor/equipment
    intent_unknown = RivetIntent(
        vendor=VendorType.UNKNOWN,
        equipment_type=EquipmentType.UNKNOWN,
        raw_summary="Unknown equipment issue",
        context_source=ContextSource.TEXT_ONLY,
        confidence=0.5,
        kb_coverage=KBCoverage.NONE
    )
    filters_unknown = build_filters(intent_unknown)
    assert "vendor" not in filters_unknown, "Should not include unknown vendor"
    assert "equipment_type" not in filters_unknown, "Should not include unknown equipment"
    print(f"  [OK] build_filters() excludes unknown values")

    # Test build_keyword_filters
    keywords = build_keyword_filters(intent)
    assert "G120C" in keywords, "Should include detected model"
    assert "F3002" in keywords, "Should include fault code"
    assert "overhead_crane" in keywords, "Should include application"
    assert any("vfd" in k.lower() for k in keywords), "Should include keywords from raw_summary"
    print(f"  [OK] build_keyword_filters() returned {len(keywords)} keywords")
    print(f"       Top 5: {keywords[:5]}")

    print(f"\n[PASS] Intent-to-Filter Mapping - All tests passed")


def test_phase1_integration():
    """Test Phase 2 integrates with Phase 1 models"""
    print("\n[TEST] Phase 1 + Phase 2 Integration")
    print("-" * 50)

    # Create intent using Phase 1 models
    intent = RivetIntent(
        vendor=VendorType.ROCKWELL,
        equipment_type=EquipmentType.PLC,
        symptom="ControlLogix processor fault",
        raw_summary="ControlLogix L75 major fault troubleshooting",
        context_source=ContextSource.TEXT_ONLY,
        confidence=0.88,
        kb_coverage=KBCoverage.STRONG  # Will be updated by estimate_coverage()
    )
    print(f"  [OK] Created RivetIntent with Phase 1 enums")

    # Use Phase 2 RAG config
    config = RAGConfig()
    collections = config.get_collections_for_intent(
        intent.vendor,
        intent.equipment_type
    )
    assert len(collections) >= 1, "Should find collections for Rockwell PLC"
    print(f"  [OK] RAG config found {len(collections)} collections for intent")

    # Build filters from intent
    filters = build_filters(intent)
    assert filters["vendor"] == "Rockwell", "Should extract Rockwell vendor"
    assert filters["equipment_type"] == "PLC", "Should extract PLC equipment type"
    print(f"  [OK] Filters built from intent: {filters}")

    print(f"\n[PASS] Phase 1 + Phase 2 Integration - All tests passed")


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("RIVET Pro Phase 2 (RAG Layer) - Validation Tests")
    print("=" * 60)

    try:
        test_rag_config()
        test_intent_filters()
        test_phase1_integration()

        print("\n" + "=" * 60)
        print("[SUCCESS] All Phase 2 validation tests passed!")
        print("=" * 60)
        print("\nPhase 2 Summary:")
        print("  - RAG Configuration: WORKING")
        print("  - Intent Filters: WORKING")
        print("  - Phase 1 Integration: WORKING")
        print("  - Retriever Functions: READY (needs database connection to test)")
        print("\nNext Steps:")
        print("  1. Deploy database migration (if not done)")
        print("  2. Test search_docs() and estimate_coverage() with live database")
        print("  3. Start Phase 3 (SME Agents)")

        return 0

    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

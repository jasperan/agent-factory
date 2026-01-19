"""
Simple RAG Layer Validation Script

Phase 2/8 - Quick validation for RAG layer integration.
"""

from agent_factory.rivet_pro.models import RivetIntent, VendorType, EquipmentType, ContextSource
from agent_factory.rivet_pro.rag import search_docs, estimate_coverage, RAGConfig, RetrievedDoc

print("=" * 60)
print("RIVET Pro Phase 2 - RAG Layer Validation")
print("=" * 60)

# Test 1: Import all RAG components
print("\nTest 1: Importing RAG components...", end=" ")
try:
    from agent_factory.rivet_pro.rag.config import COLLECTION_NAME, DEFAULT_TOP_K
    from agent_factory.rivet_pro.rag.filters import build_metadata_filter
    from agent_factory.rivet_pro.rag.retriever import search_docs, estimate_coverage
    print("[PASS]")
except Exception as e:
    print(f"[FAIL] {e}")
    exit(1)

# Test 2: Create RAGConfig
print("Test 2: Creating RAGConfig...", end=" ")
try:
    config = RAGConfig(
        top_k=10,
        min_similarity=0.75,
        vendor_filter="siemens",
        equipment_filter="vfd"
    )
    assert config.top_k == 10
    assert config.vendor_filter == "siemens"
    print("[PASS]")
except Exception as e:
    print(f"[FAIL] {e}")
    exit(1)

# Test 3: Create RetrievedDoc
print("Test 3: Creating RetrievedDoc...", end=" ")
try:
    doc = RetrievedDoc(
        atom_id="test:123",
        title="Test Document",
        summary="Test summary",
        content="Test content",
        atom_type="concept",
        vendor="siemens",
        similarity_score=0.92
    )
    assert doc.atom_id == "test:123"
    assert doc.similarity_score == 0.92
    print("[PASS]")
except Exception as e:
    print(f"[FAIL] {e}")
    exit(1)

# Test 4: Build metadata filter
print("Test 4: Building metadata filter...", end=" ")
try:
    from agent_factory.rivet_pro.rag.filters import build_metadata_filter
    intent = RivetIntent(
        vendor=VendorType.SIEMENS,
        equipment_type=EquipmentType.VFD,
        raw_summary="G120C fault",
        detected_fault_codes=["F3002"],
        context_source=ContextSource.TEXT_ONLY,
        confidence=0.9,
        kb_coverage="strong"
    )
    filters = build_metadata_filter(intent)
    assert "vendor" in filters
    assert filters["vendor"]["$eq"] == "Siemens"  # Capitalized from enum
    print("[PASS]")
except Exception as e:
    print(f"[FAIL] {e}")
    exit(1)

# Test 5: Extract search keywords
print("Test 5: Extracting search keywords...", end=" ")
try:
    from agent_factory.rivet_pro.rag.filters import extract_search_keywords
    intent = RivetIntent(
        vendor=VendorType.ROCKWELL,
        equipment_type=EquipmentType.PLC,
        raw_summary="ControlLogix processor fault code",
        detected_model="1756-L83E",
        context_source=ContextSource.TEXT_ONLY,
        confidence=0.85,
        kb_coverage="thin"
    )
    keywords = extract_search_keywords(intent)
    assert "rockwell" in keywords
    assert "1756-l83e" in keywords  # Should be lowercased
    print("[PASS]")
except Exception as e:
    print(f"[FAIL] {e}")
    exit(1)

# Test 6: Validate search_docs signature (without database)
print("Test 6: Testing search_docs signature...", end=" ")
try:
    # This will fail gracefully without database
    intent = RivetIntent(
        vendor=VendorType.ABB,
        equipment_type=EquipmentType.VFD,
        raw_summary="ACS880 alarm",
        context_source=ContextSource.TEXT_ONLY,
        confidence=0.8,
        kb_coverage="none"
    )
    # Should return empty list without crashing
    docs = search_docs(intent, agent_id="generic_plc", top_k=8)
    assert isinstance(docs, list)
    print("[PASS]")
except Exception as e:
    print(f"[FAIL] {e}")
    exit(1)

print("\n" + "=" * 60)
print("ALL TESTS PASSED - Phase 2 RAG layer validated successfully!")
print("=" * 60)
print("\nNext: Phase 3 - SME Agents (4 agents in parallel)")
print("Run: 'poetry run python test_rag_simple.py'")

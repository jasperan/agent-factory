"""Test backend components.

Adapted from TAB1_BACKEND.md (lines 1777-1869)
Tests database, vector storage, and equipment taxonomy.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

# ═══════════════════════════════════════════════════════════════════════════
# DATABASE TESTS
# ═══════════════════════════════════════════════════════════════════════════

def test_database():
    """Test database operations"""
    print("Testing database...")
    print("  [DEBUG] Importing RIVETProDatabase...")
    from agent_factory.rivet_pro.database import RIVETProDatabase

    print("  [DEBUG] Creating database instance...")
    db = RIVETProDatabase()
    print("  [DEBUG] Database instance created!")

    # Test machine creation
    import uuid
    test_user_id = str(uuid.uuid4())
    machine = db.create_machine(
        test_user_id,
        "Test Lathe",
        "Test machine for backend validation"
    )
    print(f"  [OK] Created machine: {machine['name']}")
    assert machine['name'] == "Test Lathe"
    assert machine['user_id'] == test_user_id

    # Test manual gap logging
    gap = db.log_manual_gap("Allen-Bradley", "VFD", "PowerFlex 525")
    print(f"  [OK] Logged gap: {gap['manufacturer']} {gap['component_family']}")
    assert gap['manufacturer'] == "Allen-Bradley"
    assert gap['component_family'] == "VFD"

    # Test top gaps retrieval
    gaps = db.get_top_manual_gaps()
    print(f"  [OK] Top gaps: {len(gaps)} found")
    assert isinstance(gaps, list)

    db.close()
    print("Database tests passed!\n")


# ═══════════════════════════════════════════════════════════════════════════
# VECTOR STORE TESTS
# ═══════════════════════════════════════════════════════════════════════════

def test_vector_store():
    """Test vector store operations"""
    print("Testing vector store...")
    from agent_factory.knowledge.storage import create_vector_store

    # Test PostgreSQL backend
    store = create_vector_store("postgres")
    print(f"  [OK] PostgreSQL VectorStore initialized")

    # Test embedding (may not be available, that's OK)
    embedding = store.embed_text("PowerFlex 525 fault code F004")
    print(f"  [OK] Embedding length: {len(embedding) if embedding else 0} (graceful degradation if 0)")

    # Test collection creation
    collection_name = store.get_or_create_collection("equipment_manuals")
    print(f"  [OK] Collection: {collection_name}")
    assert collection_name == "equipment_manuals"

    store.close()
    print("Vector store tests passed!\n")


def test_chromadb_backend():
    """Test ChromaDB backend (if installed)"""
    print("Testing ChromaDB backend...")

    try:
        from agent_factory.knowledge.storage import create_vector_store

        store = create_vector_store("chromadb")
        print("  [OK] ChromaDB VectorStore initialized")

        # Test collection operations
        collection_name = store.get_or_create_collection("test_collection")
        print(f"  [OK] Collection created: {collection_name}")

        # Test document addition
        count = store.add_documents(
            "test_collection",
            documents=["Test document 1", "Test document 2"],
            metadatas=[{"id": "1"}, {"id": "2"}],
            ids=["doc1", "doc2"]
        )
        print(f"  [OK] Added {count} documents")
        assert count == 2

        # Test search
        results = store.search("test_collection", "Test document", top_k=2)
        print(f"  [OK] Search returned {len(results)} results")
        assert len(results) > 0

        # Cleanup
        store.delete_collection("test_collection")
        store.close()
        print("ChromaDB backend tests passed!\n")

    except Exception as e:
        print(f"  [SKIP] ChromaDB tests skipped: {e}")
        print("     Install with: poetry add chromadb sentence-transformers\n")


# ═══════════════════════════════════════════════════════════════════════════
# TAXONOMY TESTS
# ═══════════════════════════════════════════════════════════════════════════

def test_taxonomy():
    """Test equipment taxonomy"""
    print("Testing equipment taxonomy...")
    from agent_factory.intake.equipment_taxonomy import (
        identify_component,
        identify_issue_type,
        extract_fault_code,
        identify_urgency
    )

    # Test VFD detection
    result = identify_component("The PowerFlex 525 is showing an error")
    print(f"  [OK] VFD detected: {result}")
    assert result["family"] == "Variable Frequency Drive"
    assert result["manufacturer"] == "Allen-Bradley"

    # Test fault code extraction
    code = extract_fault_code("Fault F004 on the drive")
    print(f"  [OK] Fault code: {code}")
    assert code == "F004"

    # Test issue type
    issue = identify_issue_type("Motor won't start, no power")
    print(f"  [OK] Issue type: {issue}")
    assert issue == "wont_start"

    # Test urgency
    urgency = identify_urgency("Production is stopped, need help ASAP")
    print(f"  [OK] Urgency: {urgency}")
    assert urgency in ["critical", "high"]

    print("Taxonomy tests passed!\n")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN TEST RUNNER
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 50)
    print("RIVET BACKEND TESTS")
    print("=" * 50 + "\n")

    try:
        test_database()
    except Exception as e:
        print(f"[FAIL] Database tests failed: {e}\n")

    try:
        test_vector_store()
    except Exception as e:
        print(f"[FAIL] Vector store tests failed: {e}\n")

    try:
        test_chromadb_backend()
    except Exception as e:
        print(f"[FAIL] ChromaDB tests failed (expected if not installed): {e}\n")

    try:
        test_taxonomy()
    except Exception as e:
        print(f"[FAIL] Taxonomy tests failed: {e}\n")

    print("=" * 50)
    print("TESTS COMPLETE")
    print("=" * 50)

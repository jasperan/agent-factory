"""Test 2: Single Atom Insertion on VPS (ASCII-only output)"""
import asyncio
import time
from dataclasses import dataclass, field
from typing import List, Optional

from agent_factory.tools.response_gap_filler import KnowledgeGapFiller
from agent_factory.core.database_manager import DatabaseManager

@dataclass
class TestAtom:
    """Simplified atom for testing"""
    id: str
    title: str
    content: str
    manufacturer: str = "Siemens"
    product_family: str = "S7-1200"
    sources: List[str] = field(default_factory=lambda: ["Manual Test"])
    confidence_score: float = 0.95
    embedding: Optional[List[float]] = None
    
async def test_single_insert():
    print("=" * 70)
    print("TEST 2: Single Atom Insertion (VPS)")
    print("=" * 70)
    print()
    
    # Step 1: Initialize gap filler
    print("[Step 1] Initializing KnowledgeGapFiller...")
    try:
        filler = KnowledgeGapFiller()
        print("[OK] KnowledgeGapFiller initialized")
    except Exception as e:
        print(f"[FAIL] ERROR: {e}")
        return
    print()
    
    # Step 2: Create test atom
    print("[Step 2] Creating test atom...")
    atom_id = f"test:siemens:motor-start-{int(time.time())}"
    test_atom = TestAtom(
        id=atom_id,
        title="Test Motor Start Procedure",
        content="This is a test atom for motor start procedure validation. Contains sufficient content for embedding generation using OpenAI API.",
        manufacturer="Siemens",
        product_family="S7-1200",
        sources=["Manual Test"],
        confidence_score=0.95
    )
    # Note: Using 'concept' atom_type instead of 'research' to satisfy Neon CHECK constraint
    print(f"[OK] Test atom created: {atom_id}")
    print()
    
    # Step 3: Generate embedding
    print("[Step 3] Generating embedding...")
    try:
        embedding = await filler._generate_embedding(test_atom.content)
        if embedding and len(embedding) > 0:
            print(f"[OK] Embedding generated: {len(embedding)} dimensions")
            test_atom.embedding = embedding
        else:
            print("[WARN] Embedding generation failed (empty result)")
            print("       Continuing without embedding...")
    except Exception as e:
        print(f"[WARN] ERROR generating embedding: {e}")
        print("       Continuing without embedding...")
    print()
    
    # Step 4: Insert atom
    print("[Step 4] Inserting atom to database...")
    try:
        created, updated, failures = await filler._insert_atoms([test_atom])
        print("[OK] Insert completed")
        print(f"     Created: {created}")
        print(f"     Updated: {updated}")
        if failures:
            print(f"     [WARN] Failures: {failures}")
    except Exception as e:
        print(f"[FAIL] ERROR inserting atom: {e}")
        import traceback
        traceback.print_exc()
        return
    print()
    
    # Step 5: Verify in database
    print("[Step 5] Verifying atom in database...")
    try:
        # Reuse the same DatabaseManager from filler (avoid creating second instance)
        db = filler.db_manager
        result = db.execute_query(
            "SELECT atom_id, title, manufacturer, product_family, quality_score FROM knowledge_atoms WHERE atom_id = %s",
            (atom_id,)
        )
        
        if result:
            print("[OK] FOUND IN DATABASE:")
            print(f"     atom_id:        {result[0][0]}")
            print(f"     title:          {result[0][1]}")
            print(f"     manufacturer:   {result[0][2]}")
            print(f"     product_family: {result[0][3]}")
            print(f"     quality_score:  {result[0][4]}")
        else:
            print("[FAIL] NOT FOUND IN DATABASE")
            print(f"       Expected atom_id: {atom_id}")
            print("       This means INSERT failed silently!")
    except Exception as e:
        print(f"[FAIL] ERROR querying database: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    print("=" * 70)
    print("TEST 2 COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_single_insert())

"""Minimal test to isolate database issue"""
import asyncio
import os
from datetime import datetime

# Set Neon as provider BEFORE importing DatabaseManager
os.environ['DATABASE_PROVIDER'] = 'neon'

from agent_factory.core.database_manager import DatabaseManager

async def test_minimal():
    print("=" * 70)
    print("MINIMAL DATABASE TEST")
    print("=" * 70)
    print()

    db = DatabaseManager()
    print(f"Primary provider: {db.primary_provider}")
    print()

    # Test 1: Simple SELECT
    print("[Test 1] Simple SELECT query...")
    try:
        sql = "SELECT atom_id FROM knowledge_atoms WHERE atom_id = %s LIMIT 1"
        params = ("test123",)
        print(f"SQL: {sql}")
        print(f"Params: {params}")

        result = db.execute_query(sql, params)
        print(f"[OK] Query executed, result: {result}")
    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
    print()

    # Test 2: Simple INSERT
    print("[Test 2] Simple INSERT query...")
    try:
        sql = """
            INSERT INTO knowledge_atoms (
                atom_id,
                atom_type,
                title,
                summary,
                content,
                manufacturer,
                product_family,
                difficulty,
                source_document,
                source_pages,
                source_url,
                quality_score,
                embedding,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            f"test-minimal-{int(datetime.now().timestamp())}",  # $1: atom_id
            'research',  # $2: atom_type
            'Test Title',  # $3: title
            'Test summary',  # $4: summary
            'Test content for minimal test',  # $5: content
            'TestManufacturer',  # $6: manufacturer
            'TestFamily',  # $7: product_family
            'beginner',  # $8: difficulty
            'Manual Test',  # $9: source_document
            [],  # $10: source_pages
            None,  # $11: source_url
            0.95,  # $12: quality_score
            None,  # $13: embedding (NULL for test)
            datetime.utcnow()  # $14: created_at
        )

        print(f"SQL length: {len(sql)}")
        print(f"Params count: {len(params)}")
        print(f"SQL preview: {sql[:100]}...")

        result = db.execute_query(sql, params, fetch_mode="none")
        print(f"[OK] INSERT executed, result: {result}")
    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
    print()

    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_minimal())

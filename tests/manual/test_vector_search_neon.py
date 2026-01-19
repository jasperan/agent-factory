#!/usr/bin/env python3
"""Test vector search in Neon database"""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def test_vector_search():
    """Test vector search capabilities."""

    neon_url = os.getenv('NEON_DB_URL')
    conn = psycopg2.connect(neon_url)
    cur = conn.cursor()

    print("="*70)
    print("TESTING VECTOR SEARCH IN NEON")
    print("="*70)
    print()

    # Test 1: Count atoms
    print("[1/4] Counting atoms...")
    cur.execute("SELECT COUNT(*) FROM knowledge_atoms;")
    count = cur.fetchone()[0]
    print(f"      [OK] {count} atoms in database")

    # Test 2: Sample atoms
    print()
    print("[2/4] Sample atoms (first 5)...")
    cur.execute("""
        SELECT atom_id, title, manufacturer
        FROM knowledge_atoms
        LIMIT 5;
    """)
    for i, row in enumerate(cur.fetchall(), 1):
        print(f"      {i}. [{row[2]:20s}] {row[1][:50]}")

    # Test 3: Check embeddings exist
    print()
    print("[3/4] Checking embeddings...")
    cur.execute("""
        SELECT COUNT(*)
        FROM knowledge_atoms
        WHERE embedding IS NOT NULL;
    """)
    with_embeddings = cur.fetchone()[0]
    print(f"      [OK] {with_embeddings}/{count} atoms have embeddings ({with_embeddings/count*100:.1f}%)")

    # Test 4: Test vector similarity search
    print()
    print("[4/4] Testing vector similarity search...")
    print("      Query: Find atoms similar to first atom")

    # Get first atom's embedding
    cur.execute("""
        SELECT embedding FROM knowledge_atoms
        WHERE embedding IS NOT NULL
        LIMIT 1;
    """)
    test_embedding = cur.fetchone()[0]

    # Find similar atoms
    cur.execute("""
        SELECT
            atom_id,
            title,
            1 - (embedding <=> %s::vector) AS similarity
        FROM knowledge_atoms
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT 5;
    """, (test_embedding, test_embedding))

    print("\n      Top 5 similar atoms:")
    for i, row in enumerate(cur.fetchall(), 1):
        print(f"      {i}. [similarity:{row[2]:.3f}] {row[1][:50]}")

    cur.close()
    conn.close()

    print()
    print("="*70)
    print("[SUCCESS] Vector search is working!")
    print("="*70)
    print()
    print("Next steps:")
    print("  1. Build ScriptwriterAgent (uses vector search to find relevant atoms)")
    print("  2. Generate first video script")

if __name__ == "__main__":
    test_vector_search()

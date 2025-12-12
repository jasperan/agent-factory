#!/usr/bin/env python3
"""
Batch Upload Knowledge Atoms to Neon Database

Uploads all JSON atom files from data/atoms/ to Neon knowledge_atoms table.

Features:
- Direct PostgreSQL connection (works with Neon)
- Batch processing (50 atoms per batch)
- Progress tracking
- Error handling (continues on failure)
- Duplicate detection (ON CONFLICT DO NOTHING)
- Summary statistics

Usage:
    poetry run python upload_atoms_to_neon.py
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values
from tqdm import tqdm

load_dotenv()


def load_atoms_from_directory(atoms_dir: Path) -> List[Dict[str, Any]]:
    """Load all JSON atom files from directory."""
    print(f"\nLoading atoms from: {atoms_dir}")

    atom_files = list(atoms_dir.glob("**/*.json"))
    print(f"Found {len(atom_files)} JSON files")

    atoms = []
    for atom_file in tqdm(atom_files, desc="Loading atoms"):
        try:
            with open(atom_file, 'r', encoding='utf-8') as f:
                atom = json.load(f)

                # Validate required fields
                required = ['atom_id', 'atom_type', 'title', 'summary', 'content',
                           'manufacturer', 'source_document', 'source_pages',
                           'difficulty', 'keywords', 'embedding']

                if all(k in atom for k in required):
                    atoms.append(atom)
                else:
                    missing = [k for k in required if k not in atom]
                    print(f"\n[SKIP] {atom_file.name}: missing fields {missing}")

        except Exception as e:
            print(f"\n[ERROR] Failed to load {atom_file}: {e}")

    print(f"Loaded {len(atoms)} valid atoms\n")
    return atoms


def upload_atoms_batch(conn, atoms: List[Dict[str, Any]], batch_size: int = 50):
    """Upload atoms in batches with progress tracking."""

    total = len(atoms)
    uploaded = 0
    failed = 0
    skipped = 0

    print(f"Uploading {total} atoms in batches of {batch_size}...")
    print("=" * 70)

    cur = conn.cursor()

    for i in range(0, total, batch_size):
        batch = atoms[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total + batch_size - 1) // batch_size

        print(f"\nBatch {batch_num}/{total_batches} ({len(batch)} atoms)...")

        # Prepare data for batch insert
        values = []
        for atom in batch:
            values.append((
                atom['atom_id'],
                atom['atom_type'],
                atom['title'],
                atom['summary'],
                atom['content'],
                atom['manufacturer'],
                atom.get('product_family'),
                atom.get('product_version'),
                atom['difficulty'],
                atom.get('prerequisites', []),
                atom.get('related_atoms', []),
                atom['source_document'],
                atom['source_pages'],
                atom.get('source_url'),
                atom.get('citations'),
                atom.get('quality_score', 1.0),
                atom.get('safety_level', 'info'),
                atom.get('safety_notes'),
                atom.get('keywords', []),
                atom.get('embedding')
            ))

        try:
            # Batch insert with ON CONFLICT DO NOTHING (skip duplicates)
            execute_values(
                cur,
                """
                INSERT INTO knowledge_atoms (
                    atom_id, atom_type, title, summary, content,
                    manufacturer, product_family, product_version,
                    difficulty, prerequisites, related_atoms,
                    source_document, source_pages, source_url, citations,
                    quality_score, safety_level, safety_notes,
                    keywords, embedding
                ) VALUES %s
                ON CONFLICT (atom_id) DO NOTHING
                """,
                values
            )
            conn.commit()

            uploaded += len(batch)
            print(f"  [OK] Uploaded {len(batch)} atoms")

        except Exception as e:
            print(f"  [ERROR] Batch failed: {e}")
            conn.rollback()
            failed += len(batch)

    cur.close()

    print("\n" + "=" * 70)
    print("UPLOAD SUMMARY")
    print("=" * 70)
    print(f"Total atoms:    {total}")
    print(f"Uploaded:       {uploaded}")
    print(f"Failed:         {failed}")
    print(f"Success rate:   {(uploaded/total*100):.1f}%")
    print("=" * 70)

    return uploaded, failed


def main():
    """Main upload process."""

    # Check Neon connection
    neon_url = os.getenv('NEON_DB_URL')
    if not neon_url:
        print("[ERROR] NEON_DB_URL not found in .env")
        print("Please set NEON_DB_URL in your .env file")
        sys.exit(1)

    # Check atoms directory
    atoms_dir = Path("data/atoms")
    if not atoms_dir.exists():
        print(f"[ERROR] Atoms directory not found: {atoms_dir}")
        sys.exit(1)

    print("=" * 70)
    print("UPLOAD KNOWLEDGE ATOMS TO NEON")
    print("=" * 70)

    # Connect to Neon
    print("\nConnecting to Neon...")
    try:
        conn = psycopg2.connect(neon_url)
        print("[OK] Connected")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        sys.exit(1)

    # Load atoms from directory
    atoms = load_atoms_from_directory(atoms_dir)

    if len(atoms) == 0:
        print("[WARNING] No atoms found to upload")
        conn.close()
        sys.exit(0)

    # Upload atoms
    uploaded, failed = upload_atoms_batch(conn, atoms, batch_size=50)

    # Verify upload
    print("\nVerifying upload...")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM knowledge_atoms;")
    total_count = cur.fetchone()[0]
    cur.close()
    conn.close()

    print(f"[OK] Total atoms in database: {total_count}")

    if uploaded > 0:
        print("\n[SUCCESS] Atoms uploaded to Neon!")
        print("\nNext steps:")
        print("  1. Test vector search:")
        print("     poetry run python -c \"import psycopg2, os; from dotenv import load_dotenv; load_dotenv(); conn = psycopg2.connect(os.getenv('NEON_DB_URL')); cur = conn.cursor(); cur.execute('SELECT title FROM knowledge_atoms LIMIT 5'); print([r[0] for r in cur.fetchall()])\"")
        print("  2. Build ScriptwriterAgent (uses these atoms for video scripts)")
    else:
        print("\n[ERROR] No atoms were uploaded")
        sys.exit(1)


if __name__ == "__main__":
    main()

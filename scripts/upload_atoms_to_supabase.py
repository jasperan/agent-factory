#!/usr/bin/env python3
"""
Batch Upload Knowledge Atoms to Supabase

Uploads all JSON atom files from data/atoms/ to Supabase knowledge_atoms table.

Features:
- Batch processing (50 atoms per batch for speed)
- Progress tracking
- Error handling (continues on failure)
- Duplicate detection
- Summary statistics

Usage:
    poetry run python scripts/upload_atoms_to_supabase.py

Prerequisites:
    1. Deploy schema: docs/supabase_complete_schema.sql
    2. Verify: poetry run python scripts/validate_supabase_schema.py
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client
from tqdm import tqdm

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
env_path = project_root / ".env"
load_dotenv(env_path)


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


def upload_atoms_batch(client, atoms: List[Dict[str, Any]], batch_size: int = 50):
    """Upload atoms in batches with progress tracking."""

    total = len(atoms)
    uploaded = 0
    failed = 0
    skipped = 0

    print(f"Uploading {total} atoms in batches of {batch_size}...")
    print("=" * 70)

    for i in tqdm(range(0, total, batch_size), desc="Upload progress"):
        batch = atoms[i:i + batch_size]

        try:
            # Try batch insert
            result = client.table('knowledge_atoms').insert(batch).execute()
            uploaded += len(batch)

        except Exception as e:
            error_msg = str(e)

            # If batch fails due to duplicates, try one-by-one
            if 'duplicate' in error_msg.lower() or 'unique' in error_msg.lower():
                print(f"\n[INFO] Batch {i//batch_size + 1}: Duplicates detected, uploading individually...")

                for atom in batch:
                    try:
                        client.table('knowledge_atoms').insert(atom).execute()
                        uploaded += 1
                    except Exception as e2:
                        if 'duplicate' in str(e2).lower() or 'unique' in str(e2).lower():
                            skipped += 1
                        else:
                            failed += 1
                            print(f"\n[ERROR] Failed to upload {atom.get('atom_id', 'unknown')}: {e2}")
            else:
                failed += len(batch)
                print(f"\n[ERROR] Batch {i//batch_size + 1} failed: {e}")

    print("\n" + "=" * 70)
    print("UPLOAD COMPLETE")
    print("=" * 70)
    print(f"Total atoms:    {total}")
    print(f"Uploaded:       {uploaded}")
    print(f"Skipped (dup):  {skipped}")
    print(f"Failed:         {failed}")
    print("=" * 70)

    return uploaded, skipped, failed


def verify_upload(client, expected_count: int):
    """Verify atoms were uploaded successfully."""
    print("\nVerifying upload...")

    try:
        result = client.table('knowledge_atoms').select('atom_id', count='exact').execute()
        actual_count = result.count

        print(f"Expected: {expected_count}")
        print(f"Actual:   {actual_count}")

        if actual_count >= expected_count:
            print("[SUCCESS] All atoms uploaded successfully!")
        else:
            print(f"[WARNING] Missing {expected_count - actual_count} atoms")

        # Show sample atoms
        sample = client.table('knowledge_atoms').select('atom_id, title, manufacturer').limit(5).execute()
        print("\nSample atoms:")
        for atom in sample.data:
            print(f"  - {atom['atom_id']}: {atom['title']} ({atom['manufacturer']})")

        return actual_count

    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        return 0


def main():
    """Main upload workflow."""

    print("=" * 70)
    print("KNOWLEDGE ATOMS → SUPABASE UPLOAD")
    print("=" * 70)

    # Get credentials
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not url or not key:
        print("\n[ERROR] Missing Supabase credentials in .env")
        print("Required: SUPABASE_URL, SUPABASE_KEY (or SUPABASE_SERVICE_ROLE_KEY)")
        return False

    print(f"\nURL: {url}")
    print(f"Key: ***{key[-10:]}")

    # Connect to Supabase
    try:
        client = create_client(url, key)
        print("[OK] Connected to Supabase\n")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return False

    # Load atoms
    atoms_dir = project_root / "data" / "atoms"
    if not atoms_dir.exists():
        print(f"[ERROR] Atoms directory not found: {atoms_dir}")
        return False

    atoms = load_atoms_from_directory(atoms_dir)

    if not atoms:
        print("[ERROR] No valid atoms found")
        return False

    # Upload atoms
    uploaded, skipped, failed = upload_atoms_batch(client, atoms, batch_size=50)

    # Verify
    verify_upload(client, uploaded)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

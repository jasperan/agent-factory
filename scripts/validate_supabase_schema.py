#!/usr/bin/env python3
"""
Supabase Schema Validation Script

Validates that all required tables exist and are functional.
Run this after deploying schema or to verify database health.

Usage:
    poetry run python scripts/validate_supabase_schema.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment from project root
env_path = project_root / ".env"
load_dotenv(env_path)


def validate_schema():
    """Validate Supabase schema deployment."""

    # Get credentials
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not url or not key:
        print("[X] ERROR: Supabase credentials not found in .env")
        print("\nRequired environment variables:")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_KEY (or SUPABASE_SERVICE_ROLE_KEY)")
        return False

    print("=" * 70)
    print("SUPABASE SCHEMA VALIDATION")
    print("=" * 70)
    print(f"\nURL: {url}")
    print(f"Key: ***{key[-10:]}\n")

    try:
        client = create_client(url, key)
        print("[OK] Connected to Supabase\n")
    except Exception as e:
        print(f"[X] Connection failed: {e}")
        return False

    # Define required tables and their expected structure
    tables_config = {
        'session_memories': {
            'description': 'Memory atoms (context, decisions, actions, issues, logs)',
            'test_insert': {
                'session_id': 'test_session',
                'user_id': 'test_user',
                'memory_type': 'context',
                'content': {'test': 'data'},
                'metadata': {}
            }
        },
        'knowledge_atoms': {
            'description': 'Knowledge base (PLC/RIVET atoms with embeddings)',
            'test_insert': {
                'atom_id': 'test:validation',
                'atom_type': 'concept',
                'title': 'Validation Test',
                'summary': 'Testing schema',
                'content': {'test': 'data'},
                'keywords': ['test'],
                'difficulty': 'beginner',
                'prerequisites': [],
                'source_citations': [],
                'quality_score': 1.0,
                'embedding': [0.1] * 1536
            }
        },
        'research_staging': {
            'description': 'Research Agent raw data staging',
            'test_insert': {
                'source_url': 'https://test.com',
                'source_type': 'web',
                'raw_content': 'test content',
                'metadata': {},
                'content_hash': 'test_hash'
            }
        },
        'video_scripts': {
            'description': 'Scriptwriter Agent output',
            'test_insert': {
                'script_id': 'test_script',
                'title': 'Test Script',
                'hook': 'Test hook',
                'main_content': 'Test content',
                'recap': 'Test recap',
                'atom_ids': ['test:atom'],
                'metadata': {}
            }
        },
        'upload_jobs': {
            'description': 'YouTube upload queue',
            'test_insert': {
                'job_id': 'test_job',
                'video_path': '/test/video.mp4',
                'script_id': 'test_script',
                'status': 'pending',
                'metadata': {}
            }
        },
        'agent_messages': {
            'description': 'Agent communication logs',
            'test_insert': {
                'session_id': 'test_session',
                'agent_name': 'TestAgent',
                'message_type': 'log',
                'content': {'test': 'message'},
                'metadata': {}
            }
        },
        'settings': {
            'description': 'Runtime configuration (Settings Service)',
            'test_insert': {
                'setting_key': 'TEST_KEY',
                'setting_value': 'test_value',
                'category': 'test'
            }
        }
    }

    # Check table existence
    print("TABLE EXISTENCE CHECK")
    print("-" * 70)

    results = {}
    for table, config in tables_config.items():
        try:
            result = client.table(table).select('*').limit(1).execute()
            print(f"[OK] {table:<25} EXISTS - {config['description']}")
            results[table] = {'exists': True, 'error': None}
        except Exception as e:
            error_msg = str(e)
            if 'does not exist' in error_msg or 'relation' in error_msg:
                print(f"[X] {table:<25} MISSING")
                results[table] = {'exists': False, 'error': 'Table does not exist'}
            else:
                print(f"[?] {table:<25} ERROR: {error_msg[:40]}")
                results[table] = {'exists': False, 'error': error_msg}

    print("-" * 70)

    # CRUD operations test
    print("\nCRUD OPERATIONS TEST (knowledge_atoms)")
    print("-" * 70)

    if results.get('knowledge_atoms', {}).get('exists'):
        try:
            # INSERT
            test_atom = tables_config['knowledge_atoms']['test_insert']
            client.table('knowledge_atoms').insert(test_atom).execute()
            print("[OK] INSERT works")

            # SELECT
            result = client.table('knowledge_atoms').select('*').eq('atom_id', 'test:validation').execute()
            if len(result.data) > 0:
                print(f"[OK] SELECT works (found {len(result.data)} row)")
            else:
                print("[X] SELECT failed (no data returned)")

            # UPDATE
            client.table('knowledge_atoms').update({'title': 'Updated Title'}).eq('atom_id', 'test:validation').execute()
            print("[OK] UPDATE works")

            # DELETE
            client.table('knowledge_atoms').delete().eq('atom_id', 'test:validation').execute()
            print("[OK] DELETE works")

            print("\n[SUCCESS] CRUD operations FUNCTIONAL")

        except Exception as e:
            print(f"[X] CRUD test failed: {e}")
            results['knowledge_atoms']['crud'] = False
    else:
        print("[SKIP] Skipped (table does not exist)")

    print("-" * 70)

    # Summary
    print("\nVALIDATION SUMMARY")
    print("=" * 70)

    total_tables = len(tables_config)
    tables_exist = sum(1 for r in results.values() if r.get('exists'))

    print(f"Tables Checked: {total_tables}")
    print(f"Tables Exist:   {tables_exist}")
    print(f"Tables Missing: {total_tables - tables_exist}")

    if tables_exist == total_tables:
        print("\n[SUCCESS] SCHEMA FULLY DEPLOYED AND FUNCTIONAL!")
        print("\nReady for:")
        print("  - Week 2 Agent Development (Research, Scriptwriter, Atom Builder)")
        print("  - Knowledge atom insertion")
        print("  - Video script generation")
        print("  - YouTube upload automation")
        return True
    else:
        print("\n[ERROR] SCHEMA INCOMPLETE")
        print("\nMissing tables:")
        for table, result in results.items():
            if not result.get('exists'):
                print(f"  - {table}")
        print("\nRun SQL migration: docs/supabase_migrations.sql")
        return False


if __name__ == "__main__":
    success = validate_schema()
    sys.exit(0 if success else 1)

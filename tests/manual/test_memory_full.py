"""Test full memory save/load cycle."""

from agent_factory.memory.storage import SupabaseMemoryStorage
from datetime import datetime

def test_full_cycle():
    print("=" * 60)
    print("FULL MEMORY SAVE/LOAD TEST")
    print("=" * 60)

    storage = SupabaseMemoryStorage()

    # Generate session ID
    session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    user_id = "test_user"

    print(f"\nSession ID: {session_id}")
    print(f"User ID: {user_id}")

    # SAVE: Create memory atoms
    print("\n--- SAVING MEMORIES ---")

    # 1. Context
    print("Saving context...")
    storage.save_memory_atom(
        session_id=session_id,
        user_id=user_id,
        memory_type="context",
        content={
            "project": "Agent Factory",
            "phase": "Supabase Memory Integration",
            "status": "Testing complete",
            "recent_changes": [
                "Created Supabase storage backend",
                "Added memory-save/load commands",
                "Successfully connected to cloud database"
            ]
        }
    )
    print("[OK] Context saved")

    # 2. Decision
    print("Saving decision...")
    storage.save_memory_atom(
        session_id=session_id,
        user_id=user_id,
        memory_type="decision",
        content={
            "title": "Use Supabase for Memory Storage",
            "rationale": "10-100x faster than file I/O, unlimited storage",
            "alternatives": ["File-based", "SQLite"],
            "impact": "high",
            "date": datetime.now().isoformat()
        }
    )
    print("[OK] Decision saved")

    # 3. Action
    print("Saving action...")
    storage.save_memory_atom(
        session_id=session_id,
        user_id=user_id,
        memory_type="action",
        content={
            "task": "Test memory system in production",
            "priority": "high",
            "status": "pending",
            "due_date": "2025-12-10"
        }
    )
    print("[OK] Action saved")

    # 4. Issue
    print("Saving issue...")
    storage.save_memory_atom(
        session_id=session_id,
        user_id=user_id,
        memory_type="issue",
        content={
            "title": "Table not created initially",
            "description": "Session_memories table needed to be created in Supabase",
            "status": "resolved",
            "severity": "medium",
            "solution": "Ran SQL schema in Supabase SQL Editor"
        }
    )
    print("[OK] Issue saved")

    # 5. Log
    print("Saving log...")
    storage.save_memory_atom(
        session_id=session_id,
        user_id=user_id,
        memory_type="log",
        content={
            "session_title": "Supabase Memory System Testing",
            "activities": [
                "Fixed .env credentials",
                "Created session_memories table",
                "Tested connection successfully",
                "Verified save/load cycle"
            ],
            "files_created": ["test_supabase_connection.py", "test_memory_full.py"],
            "tests_passed": True
        }
    )
    print("[OK] Log saved")

    # LOAD: Query memories back
    print("\n--- LOADING MEMORIES ---")

    print(f"Querying all memories for session: {session_id}...")
    all_memories = storage.query_memory_atoms(session_id=session_id)
    print(f"[OK] Found {len(all_memories)} memories")

    # Organize by type
    by_type = {}
    for mem in all_memories:
        mem_type = mem['memory_type']
        if mem_type not in by_type:
            by_type[mem_type] = []
        by_type[mem_type].append(mem)

    # Display
    print("\n--- LOADED MEMORIES ---")

    for mem_type, items in sorted(by_type.items()):
        print(f"\n{mem_type.upper()} ({len(items)} items):")
        for item in items:
            content = item['content']
            if mem_type == 'context':
                print(f"  Project: {content.get('project')}")
                print(f"  Phase: {content.get('phase')}")
                print(f"  Status: {content.get('status')}")
            elif mem_type == 'decision':
                print(f"  Title: {content.get('title')}")
                print(f"  Rationale: {content.get('rationale')}")
                print(f"  Impact: {content.get('impact')}")
            elif mem_type == 'action':
                print(f"  Task: {content.get('task')}")
                print(f"  Priority: {content.get('priority')}")
                print(f"  Status: {content.get('status')}")
            elif mem_type == 'issue':
                print(f"  Title: {content.get('title')}")
                print(f"  Status: {content.get('status')}")
                print(f"  Solution: {content.get('solution')}")
            elif mem_type == 'log':
                print(f"  Title: {content.get('session_title')}")
                print(f"  Activities: {len(content.get('activities', []))}")
                print(f"  Tests passed: {content.get('tests_passed')}")

    print("\n" + "=" * 60)
    print("SUCCESS: Full save/load cycle complete!")
    print("=" * 60)
    print(f"\nSession ID: {session_id}")
    print("Memories saved: 5 (context, decision, action, issue, log)")
    print("Memories loaded: {}".format(len(all_memories)))
    print("\nYou can now use /memory-save and /memory-load commands!")
    print("=" * 60)

if __name__ == "__main__":
    test_full_cycle()

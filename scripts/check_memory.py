"""Quick check of what's in Supabase memory."""

import os
import sys
from agent_factory.memory.storage import SupabaseMemoryStorage
import json

# Use service role key from .env
os.environ['SUPABASE_KEY'] = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')

storage = SupabaseMemoryStorage()

print("Querying all memory atoms...")
print("="*60)

try:
    atoms = storage.query_memory_atoms(limit=50)
    print(f"Found {len(atoms)} memory atoms\n")

    if not atoms:
        print("No memory atoms found. Database is empty.")
        print("Use /memory-save to create your first session.")
        sys.exit(0)

    # Group by session
    sessions = {}
    for atom in atoms:
        sid = atom.get('session_id', 'unknown')
        if sid not in sessions:
            sessions[sid] = []
        sessions[sid].append(atom)

    print(f"Found {len(sessions)} unique sessions:\n")

    for sid, atoms_list in sessions.items():
        print(f"Session: {sid}")
        print(f"  Atoms: {len(atoms_list)}")

        # Group by type
        types = {}
        for atom in atoms_list:
            mtype = atom['memory_type']
            types[mtype] = types.get(mtype, 0) + 1

        for mtype, count in types.items():
            print(f"    {mtype}: {count}")

        # Show first atom content preview
        first = atoms_list[0]
        print(f"  Created: {first['created_at']}")
        print(f"  User: {first['user_id']}")
        print(f"  Preview: {str(first['content'])[:100]}...")
        print()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

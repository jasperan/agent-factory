"""Test Supabase connection with provided credentials."""

from agent_factory.memory.storage import SupabaseMemoryStorage
import traceback

def test_connection():
    url = "https://mggqgrxwumnnujojndub.supabase.co"
    key = "sb_publishable_oj-z7CcKu_RgfmagF7b8kw_czLYX7uA"

    print("=" * 60)
    print("SUPABASE CONNECTION TEST")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Key: {key[:20]}...")
    print()

    try:
        print("Step 1: Initializing storage...")
        storage = SupabaseMemoryStorage(
            supabase_url=url,
            supabase_key=key
        )
        print("[OK] Storage initialized successfully")
        print()

        print("Step 2: Testing query...")
        atoms = storage.query_memory_atoms(limit=1)
        print(f"[OK] Query successful - found {len(atoms)} atoms")
        print()

        print("=" * 60)
        print("SUCCESS: Supabase connection working!")
        print("=" * 60)
        return True

    except Exception as e:
        print()
        print("=" * 60)
        print("ERROR: Connection failed")
        print("=" * 60)
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")
        print()
        print("Full traceback:")
        traceback.print_exc()
        print()
        print("=" * 60)
        print("TROUBLESHOOTING STEPS:")
        print("=" * 60)
        print("1. Verify table exists: Go to Supabase -> Table Editor")
        print("2. Check key format: Should be JWT or sb_publishable_*")
        print("3. Run schema: docs/supabase_memory_schema.sql")
        print("=" * 60)
        return False

if __name__ == "__main__":
    test_connection()

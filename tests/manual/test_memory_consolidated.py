"""
Comprehensive test of consolidated memory system.

Tests:
1. All imports from agent_factory.memory
2. InMemoryStorage (basic functionality)
3. SQLiteStorage (file persistence)
4. SupabaseMemoryStorage (cloud persistence)
5. ContextManager (token window management)
6. Session lifecycle (create, save, load)
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_imports():
    """Test all memory module imports."""
    print("=== Testing Imports ===")
    try:
        from agent_factory.memory import (
            Message,
            MessageHistory,
            Session,
            MemoryStorage,
            InMemoryStorage,
            SQLiteStorage,
            SupabaseMemoryStorage,
            ContextManager,
        )
        print("[PASS] All imports successful")
        return True
    except ImportError as e:
        print(f"[FAIL] Import failed: {e}")
        return False


def test_in_memory_storage():
    """Test InMemoryStorage backend."""
    print("\n=== Testing InMemoryStorage ===")
    try:
        from agent_factory.memory import Session, InMemoryStorage

        storage = InMemoryStorage()
        session = Session(user_id="alice", storage=storage)
        session.add_user_message("Hello, I'm Alice")
        session.add_assistant_message("Hi Alice, nice to meet you!")
        session.save()

        # Load session
        loaded = session.storage.load_session(session.session_id)
        assert loaded is not None, "Session should be loadable"
        assert len(loaded) == 2, "Should have 2 messages"
        assert loaded.user_id == "alice", "User ID should match"

        print(f"[PASS] InMemoryStorage works ({len(loaded)} messages)")
        return True
    except Exception as e:
        print(f"[FAIL] InMemoryStorage failed: {e}")
        return False


def test_sqlite_storage():
    """Test SQLiteStorage backend."""
    print("\n=== Testing SQLiteStorage ===")
    try:
        from agent_factory.memory import Session, SQLiteStorage

        db_path = "test_sessions.db"
        storage = SQLiteStorage(db_path)
        session = Session(user_id="bob", storage=storage)
        session.add_user_message("My name is Bob")
        session.add_assistant_message("Hello Bob!")
        session.save()

        # Load session
        loaded = Session.load(session.session_id, storage=storage)
        assert loaded is not None, "Session should be loadable"
        assert len(loaded) == 2, "Should have 2 messages"
        assert loaded.user_id == "bob", "User ID should match"

        # Cleanup
        os.remove(db_path)

        print(f"[PASS] SQLiteStorage works ({len(loaded)} messages)")
        return True
    except Exception as e:
        print(f"[FAIL] SQLiteStorage failed: {e}")
        # Cleanup on failure
        if os.path.exists("test_sessions.db"):
            os.remove("test_sessions.db")
        return False


def test_supabase_storage():
    """Test SupabaseMemoryStorage backend."""
    print("\n=== Testing SupabaseMemoryStorage ===")

    # Check if Supabase credentials are available
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("[SKIP] SUPABASE_URL or SUPABASE_KEY not set")
        return True  # Not a failure, just skipped

    try:
        from agent_factory.memory import Session, SupabaseMemoryStorage

        storage = SupabaseMemoryStorage()
        session = Session(user_id="charlie", storage=storage)
        session.add_user_message("I'm Charlie from Supabase test")
        session.add_assistant_message("Welcome Charlie!")
        session.save()

        # Load session
        loaded = Session.load(session.session_id, storage=storage)
        assert loaded is not None, "Session should be loadable"
        assert len(loaded) == 2, "Should have 2 messages"
        assert loaded.user_id == "charlie", "User ID should match"

        # Cleanup
        storage.delete_session(session.session_id)

        print(f"[PASS] SupabaseMemoryStorage works ({len(loaded)} messages)")
        return True
    except Exception as e:
        print(f"[FAIL] SupabaseMemoryStorage failed: {e}")
        return False


def test_context_manager():
    """Test ContextManager token window management."""
    print("\n=== Testing ContextManager ===")
    try:
        from agent_factory.memory import MessageHistory, ContextManager

        history = MessageHistory()
        history.add_message("system", "You are a helpful assistant.")
        history.add_message("user", "Hello " * 100)  # Long message
        history.add_message("assistant", "Hi there!")
        history.add_message("user", "How are you?")

        # Test with small token window
        manager = ContextManager(max_tokens=200, preserve_system=True)
        messages = manager.fit_to_window(history)

        # System message should be preserved
        assert any(m.role == "system" for m in messages), "System message should be preserved"
        # Should have some messages but not necessarily all (depending on token limits)
        assert len(messages) >= 1, "Should have at least system message"
        assert len(messages) <= len(history), "Should not have more messages than history"

        print(f"[PASS] ContextManager works ({len(messages)}/{len(history)} messages fit)")
        return True
    except Exception as e:
        print(f"[FAIL] ContextManager failed: {e}")
        return False


def test_session_lifecycle():
    """Test complete session lifecycle."""
    print("\n=== Testing Session Lifecycle ===")
    try:
        from agent_factory.memory import Session, SQLiteStorage

        db_path = "test_lifecycle.db"
        storage = SQLiteStorage(db_path)

        # Create session
        session = Session(user_id="dave", storage=storage)
        session_id = session.session_id

        # Add messages
        session.add_user_message("First message")
        session.add_assistant_message("First response")
        session.save()

        # Add more messages
        session.add_user_message("Second message")
        session.add_assistant_message("Second response")
        session.save()

        # Load in new session object
        loaded = Session.load(session_id, storage=storage)
        assert loaded is not None, "Session should load"
        assert len(loaded) == 4, "Should have 4 messages"

        # Test metadata
        loaded.set_metadata("user_name", "Dave")
        loaded.save()

        # Reload and check metadata
        reloaded = Session.load(session_id, storage=storage)
        assert reloaded.get_metadata("user_name") == "Dave", "Metadata should persist"

        # Cleanup
        storage.delete_session(session_id)
        os.remove(db_path)

        print(f"[PASS] Session lifecycle works (4 messages, metadata persisted)")
        return True
    except Exception as e:
        print(f"[FAIL] Session lifecycle failed: {e}")
        if os.path.exists("test_lifecycle.db"):
            os.remove("test_lifecycle.db")
        return False


def main():
    """Run all tests."""
    print("=" * 50)
    print("  Memory System Consolidation Test")
    print("=" * 50 + "\n")

    results = {
        "Imports": test_imports(),
        "InMemoryStorage": test_in_memory_storage(),
        "SQLiteStorage": test_sqlite_storage(),
        "SupabaseMemoryStorage": test_supabase_storage(),
        "ContextManager": test_context_manager(),
        "Session Lifecycle": test_session_lifecycle(),
    }

    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status:>8}  {test_name}")

    print("="*50)
    print(f"Result: {passed}/{total} tests passed")

    if passed == total:
        print("\nSUCCESS: All tests passed! Memory system is working correctly.")
    else:
        print(f"\nWARNING: {total - passed} test(s) failed. Review output above.")

    return passed == total


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)

"""
Test RIVET Backend Infrastructure
Tests all CRUD operations for TAB 1 backend tables.
"""

import sys
import uuid
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent_factory.rivet_pro.database import RIVETProDatabase


def test_database():
    """Test database CRUD operations"""
    print("=" * 70)
    print("RIVET BACKEND TESTS")
    print("=" * 70)
    print()

    with RIVETProDatabase() as db:
        print(f"Connected to: {db.provider}")
        print()

        # Setup: Create test user first
        print("Setup: Creating test user...")
        print("-" * 70)
        test_user = db.create_user(
            email=f"test-{uuid.uuid4().hex[:8]}@rivet-test.com",
            telegram_id=None,
            tier="beta"
        )
        user_id = test_user['id']
        print(f"  [ OK ] Created test user: {user_id}")
        print()

        # Test 1: Machine CRUD
        print("Testing Machine CRUD...")
        print("-" * 70)

        # Create machine
        machine = db.create_machine(
            user_id=user_id,
            name="Test CNC Lathe",
            description="Haas TL-1 CNC Lathe for backend validation",
            location="Building A, Bay 3"
        )
        print(f"  [ OK ] Created machine: {machine['name']}")
        machine_id = machine['id']

        # Get user machines
        machines = db.get_user_machines(user_id)
        assert len(machines) >= 1, "Should have at least 1 machine"
        print(f"  [ OK ] Retrieved {len(machines)} machines for user")

        # Search by name
        found = db.get_machine_by_name(user_id, "CNC")
        assert found is not None, "Should find machine by partial name"
        print(f"  [ OK ] Found machine by name search: {found['name']}")

        # Get by ID
        found_by_id = db.get_machine_by_id(machine_id)
        assert found_by_id['id'] == machine_id
        print(f"  [ OK ] Retrieved machine by ID")

        print()

        # Test 2: Print CRUD
        print("Testing Print CRUD...")
        print("-" * 70)

        # Create print
        print_record = db.create_print(
            machine_id=machine_id,
            user_id=user_id,
            name="Electrical Schematic Page 1",
            file_path="/uploads/test_schematic.pdf",
            print_type="schematic"
        )
        print(f"  [ OK ] Created print: {print_record['name']}")
        print_id = print_record['id']

        # Mark as vectorized
        db.update_print_vectorized(
            print_id=print_id,
            chunk_count=15,
            collection_name="user_test_machine_abc123"
        )
        print(f"  [ OK ] Marked print as vectorized (15 chunks)")

        # Get machine prints
        prints = db.get_machine_prints(machine_id)
        assert len(prints) >= 1
        print(f"  [ OK ] Retrieved {len(prints)} prints for machine")

        # Get user prints
        user_prints = db.get_user_prints(user_id)
        assert len(user_prints) >= 1
        assert 'machine_name' in user_prints[0], "Should include machine name"
        print(f"  [ OK ] Retrieved {len(user_prints)} prints for user (with machine names)")

        print()

        # Test 3: Manual CRUD
        print("Testing Manual CRUD...")
        print("-" * 70)

        # Create manual
        manual = db.create_manual(
            title="Allen-Bradley PowerFlex 525 User Manual",
            manufacturer="Allen-Bradley",
            component_family="VFD",
            file_path="/manuals/powerflex525.pdf",
            document_type="user_manual"
        )
        print(f"  [ OK ] Created manual: {manual['title']}")
        manual_id = manual['id']

        # Mark as indexed
        db.update_manual_indexed(
            manual_id=manual_id,
            collection_name="equipment_manuals",
            page_count=120
        )
        print(f"  [ OK ] Marked manual as indexed (120 pages)")

        # Search manuals by manufacturer
        ab_manuals = db.search_manuals(manufacturer="Allen-Bradley")
        assert len(ab_manuals) >= 1
        print(f"  [ OK ] Found {len(ab_manuals)} Allen-Bradley manuals")

        # Search by component family
        vfd_manuals = db.search_manuals(component_family="VFD")
        assert len(vfd_manuals) >= 1
        print(f"  [ OK ] Found {len(vfd_manuals)} VFD manuals")

        # Get all manuals
        all_manuals = db.get_all_manuals()
        print(f"  [ OK ] Retrieved {len(all_manuals)} total indexed manuals")

        print()

        # Test 4: Chat History
        print("Testing Chat History...")
        print("-" * 70)

        # Save chat
        chat1 = db.save_chat(
            user_id=user_id,
            machine_id=machine_id,
            question="What does fault code F004 mean on the VFD?",
            answer="F004 indicates overcurrent on the drive output.",
            sources=["manual_abc123", "print_def456"],
            tokens_used=350
        )
        print(f"  [ OK ] Saved chat interaction (350 tokens)")

        # Save another chat
        chat2 = db.save_chat(
            user_id=user_id,
            machine_id=machine_id,
            question="How do I reset the fault?",
            answer="Press the RESET button or cycle power.",
            sources=["manual_abc123"],
            tokens_used=150
        )
        print(f"  [ OK ] Saved second chat interaction (150 tokens)")

        # Get chat history
        history = db.get_chat_history(user_id, machine_id, limit=5)
        assert len(history) == 2
        assert history[0]['question'].startswith("What does")
        assert history[1]['question'].startswith("How do I")
        print(f"  [ OK ] Retrieved {len(history)} chat messages (chronological order)")

        print()

        # Test 5: Context Extraction
        print("Testing Context Extraction...")
        print("-" * 70)

        # Log extraction
        extraction = db.log_context_extraction(
            user_id=user_id,
            telegram_id=123456789,
            message="My PowerFlex 525 VFD is showing fault F004",
            context={
                'component_name': 'PowerFlex 525',
                'component_family': 'VFD',
                'manufacturer': 'Allen-Bradley',
                'fault_code': 'F004',
                'issue_type': 'fault_code'
            },
            confidence=0.95,
            manuals_found=3
        )
        print(f"  [ OK ] Logged context extraction (confidence: {extraction['confidence']})")
        print(f"         Component: {extraction['component_name']}")
        print(f"         Manufacturer: {extraction['manufacturer']}")
        print(f"         Fault Code: {extraction['fault_code']}")

        print()

        # Test 6: Manual Gaps
        print("Testing Manual Gaps...")
        print("-" * 70)

        # Log gap (first time)
        gap1 = db.log_manual_gap(
            manufacturer="Siemens",
            component_family="PLC",
            model_pattern="S7-1200"
        )
        assert gap1['request_count'] == 1
        print(f"  [ OK ] Logged manual gap: Siemens PLC (count: 1)")

        # Log same gap (should increment count)
        gap2 = db.log_manual_gap(
            manufacturer="Siemens",
            component_family="PLC",
            model_pattern="S7-1500"  # Different model, same family
        )
        assert gap2['request_count'] == 2
        print(f"  [ OK ] Incremented gap count (count: {gap2['request_count']})")

        # Get top gaps
        top_gaps = db.get_top_manual_gaps(limit=5)
        assert len(top_gaps) >= 1
        print(f"  [ OK ] Retrieved {len(top_gaps)} top manual gaps")
        print(f"         Top gap: {top_gaps[0]['manufacturer']} {top_gaps[0]['component_family']} ({top_gaps[0]['request_count']} requests)")

        # Resolve gap
        if len(all_manuals) > 0:
            gap_id = top_gaps[0]['id']
            resolved_manual_id = all_manuals[0]['id']
            db.resolve_manual_gap(gap_id, resolved_manual_id)
            print(f"  [ OK ] Marked gap as resolved")

        print()

    print("=" * 70)
    print("ALL TESTS PASSED")
    print("=" * 70)
    print()
    print("Summary:")
    print("  - Machine CRUD: CREATE, READ (by user, by name, by ID)")
    print("  - Print CRUD: CREATE, UPDATE (vectorized), READ (by machine, by user)")
    print("  - Manual CRUD: CREATE, UPDATE (indexed), SEARCH (mfr, family), READ ALL")
    print("  - Chat History: SAVE, READ (chronological)")
    print("  - Context Extraction: LOG (with JSONB context)")
    print("  - Manual Gaps: LOG (upsert), READ TOP, RESOLVE")
    print()


if __name__ == "__main__":
    try:
        test_database()
    except Exception as e:
        print()
        print("[FAIL] Tests failed!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

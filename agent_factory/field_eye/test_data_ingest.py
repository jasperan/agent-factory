"""
Test script for Data Ingest Agent

Demonstrates end-to-end video ingestion workflow with mock data.
"""

import os
from pathlib import Path


def test_data_ingest_agent():
    """
    Test DataIngestAgent with mock video file.

    Note: This test requires:
    1. Supabase credentials in .env
    2. field_eye_sessions, field_eye_frames, field_eye_defects tables created
    3. A sample video file (or will gracefully fail with clear error)
    """
    print("=" * 60)
    print("Testing Field Eye Data Ingest Agent")
    print("=" * 60)

    # Import agent
    from agent_factory.field_eye.agents import create_data_ingest_agent

    # Create agent with Supabase storage
    try:
        agent = create_data_ingest_agent()
        print("\nAgent initialized successfully")
        print(f"Storage backend: Supabase")
    except Exception as e:
        print(f"\nERROR: Failed to initialize agent: {e}")
        print("\nMake sure you have:")
        print("1. SUPABASE_URL and SUPABASE_KEY in .env")
        print("2. Field Eye tables created (run field_eye_schema.sql)")
        return

    # Test payload
    payload = {
        "video_path": "test_videos/inspection_sample.mp4",
        "technician_id": "john_smith",
        "vehicle_id": "COASTER_001",
        "equipment_type": "coaster",
        "metadata": {
            "location": "workshop_bay_3",
            "shift": "morning",
            "weather": "sunny"
        }
    }

    print("\nTest Payload:")
    print(f"  Video: {payload['video_path']}")
    print(f"  Technician: {payload['technician_id']}")
    print(f"  Vehicle: {payload['vehicle_id']}")
    print(f"  Equipment: {payload['equipment_type']}")

    # Check if video exists
    if not Path(payload["video_path"]).exists():
        print("\n" + "=" * 60)
        print("MOCK TEST (No video file)")
        print("=" * 60)
        print("\nNo sample video found. Agent would process:")
        print("1. Extract frames (every 2 seconds)")
        print("2. Detect pauses (motion analysis)")
        print("3. Create session in database")
        print("4. Upload frames to Supabase storage")
        print("5. Create defect records for pauses")
        print("6. Build Knowledge Atoms")
        print("\nTo test with real video:")
        print(f"  mkdir -p test_videos")
        print(f"  # Place sample video at: {payload['video_path']}")
        print(f"  python -m agent_factory.field_eye.test_data_ingest")
        return

    # Run ingestion
    print("\n" + "=" * 60)
    print("Running Ingestion Pipeline...")
    print("=" * 60)

    result = agent.run(payload)

    # Display results
    print("\n" + "=" * 60)
    if result["status"] == "success":
        print("SUCCESS!")
        print("=" * 60)
        print(f"\nSession ID: {result['session_id']}")
        print(f"Frames extracted: {result['frames_extracted']}")
        print(f"Pauses detected: {result['pauses_detected']}")
        print(f"Defects found: {result['defects_found']}")
        print(f"Knowledge Atoms created: {result['atoms_created']}")
        print("\nNext steps:")
        print("1. View session in Supabase dashboard")
        print("2. Query frames: SELECT * FROM field_eye_frames WHERE session_id = '{result['session_id']}'")
        print("3. Query defects: SELECT * FROM field_eye_defects")
    else:
        print("FAILED!")
        print("=" * 60)
        print(f"\nError: {result['error']}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_data_ingest_agent()

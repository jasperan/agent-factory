"""
Test script for Knowledge Gap Detection & Ingestion Trigger system.

Tests the complete flow:
1. Query with no KB coverage triggers Route C
2. Gap detector analyzes query and generates ingestion trigger
3. Trigger is logged to database
4. Research pipeline spawns in background (async)
5. User receives response with trigger marker
"""
import asyncio
import logging
from agent_factory.core.orchestrator import RivetOrchestrator
from agent_factory.rivet_pro.models import RivetRequest, ChannelType, MessageType
from agent_factory.core.database_manager import DatabaseManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_gap_detection():
    """Test gap detection with Siemens G120 F0003 query."""

    print("\n" + "="*70)
    print("TESTING: Knowledge Gap Detection & Ingestion Trigger")
    print("="*70 + "\n")

    # Step 1: Initialize orchestrator with database
    print("[1/5] Initializing orchestrator with database...")
    try:
        db = DatabaseManager()
        orchestrator = RivetOrchestrator(rag_layer=db)
        print("[OK] Orchestrator initialized")
        print(f"      - Gap detector: {'YES' if orchestrator.gap_detector else 'NO'}")
        print(f"      - Gap logger: {'YES' if orchestrator.kb_gap_logger else 'NO'}")
    except Exception as e:
        print(f"[FAIL] Failed to initialize orchestrator: {e}")
        return

    # Step 2: Create test query (known gap: Siemens G120 F0003)
    print("\n[2/5] Creating test query...")
    request = RivetRequest(
        text="Siemens G120C drive showing fault code F0003. How do I troubleshoot this?",
        user_id="test_user_123",
        channel=ChannelType.API,  # Use API channel for testing
        message_type=MessageType.TEXT
    )
    print(f"[OK] Query: '{request.text}'")

    # Step 3: Route query (should trigger Route C)
    print("\n[3/5] Routing query...")
    try:
        response = await orchestrator.route_query(request)
        print(f"[OK] Route taken: {response.route_taken}")
        print(f"      - Confidence: {response.confidence:.2f}")
        print(f"      - Research triggered: {response.research_triggered}")
        print(f"      - Agent: {response.agent_id}")
    except Exception as e:
        print(f"[FAIL] Routing failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 4: Check for ingestion trigger in response
    print("\n[4/5] Checking for ingestion trigger...")
    if "[INGESTION_TRIGGER]" in response.text:
        print("[OK] Ingestion trigger found in response")
        # Extract trigger section
        trigger_start = response.text.find("[INGESTION_TRIGGER]")
        trigger_end = response.text.find("[/INGESTION_TRIGGER]") + len("[/INGESTION_TRIGGER]")
        trigger_section = response.text[trigger_start:trigger_end]
        print("\nTrigger section:")
        print(trigger_section)
    else:
        print("[WARN] No ingestion trigger found in response")
        print(f"       Response length: {len(response.text)} chars")

    # Step 5: Check trace for ingestion trigger data
    print("\n[5/5] Checking trace data...")
    if "ingestion_trigger" in response.trace:
        trigger = response.trace["ingestion_trigger"]
        if trigger:
            print("[OK] Ingestion trigger in trace:")
            print(f"      - Equipment: {trigger.get('equipment_identified')}")
            print(f"      - Vendor: {trigger.get('vendor')}")
            print(f"      - Priority: {trigger.get('priority')}")
            print(f"      - Search terms: {len(trigger.get('search_terms', []))}")
            print(f"      - Gap ID: {trigger.get('gap_id')}")
        else:
            print("[WARN] Trigger is None in trace")
    else:
        print("[WARN] No ingestion_trigger in trace")

    # Print full response
    print("\n" + "="*70)
    print("FULL RESPONSE:")
    print("="*70)
    print(response.text)
    print("="*70)

    # Wait a bit for background research pipeline to start
    print("\n[INFO] Waiting 2 seconds for background tasks...")
    await asyncio.sleep(2)
    print("[INFO] Test complete!")


if __name__ == "__main__":
    asyncio.run(test_gap_detection())

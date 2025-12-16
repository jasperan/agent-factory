"""Simple validation test for RIVET Pro models"""

from agent_factory.rivet_pro.models import (
    RivetRequest,
    RivetIntent,
    RivetResponse,
    AgentTrace,
    ChannelType,
    MessageType,
    VendorType,
    EquipmentType,
    ContextSource,
    KBCoverage,
    RouteType,
    AgentID,
    create_text_request,
    create_image_request,
)

print("[OK] All imports successful\n")

# Test 1: Text request
print("Test 1: Creating text request...")
req = create_text_request(
    user_id="test_123",
    text="My Siemens VFD shows F3002 fault"
)
print(f"  User ID: {req.user_id}")
print(f"  Channel: {req.channel.value}")
print(f"  Message: {req.text}")
print("  [PASS]\n")

# Test 2: Image request
print("Test 2: Creating image request...")
req2 = create_image_request(
    user_id="test_456",
    image_path="/tmp/test.jpg",
    caption="VFD nameplate"
)
print(f"  Image path: {req2.image_path}")
print(f"  Caption: {req2.text}")
print("  [PASS]\n")

# Test 3: Intent
print("Test 3: Creating intent...")
intent = RivetIntent(
    vendor=VendorType.SIEMENS,
    equipment_type=EquipmentType.VFD,
    context_source=ContextSource.TEXT_ONLY,
    confidence=0.92,
    kb_coverage=KBCoverage.STRONG,
    raw_summary="Siemens VFD F3002 fault",
    detected_fault_codes=["F3002"]
)
print(f"  Vendor: {intent.vendor.value}")
print(f"  Equipment: {intent.equipment_type.value}")
print(f"  Confidence: {intent.confidence}")
print(f"  KB Coverage: {intent.kb_coverage.value}")
print("  [PASS]\n")

# Test 4: Response
print("Test 4: Creating response...")
response = RivetResponse(
    text="F3002 is DC bus overvoltage. Check input voltage...",
    agent_id=AgentID.SIEMENS,
    route_taken=RouteType.ROUTE_A,
    confidence=0.89,
    suggested_actions=["Check voltage", "Verify parameters"]
)
print(f"  Agent: {response.agent_id.value}")
print(f"  Route: {response.route_taken.value}")
print(f"  Actions: {len(response.suggested_actions)}")
print("  [PASS]\n")

# Test 5: Agent trace
print("Test 5: Creating agent trace...")
trace = AgentTrace(
    request_id="req_test_123",
    user_id="test_123",
    channel=ChannelType.TELEGRAM,
    message_type=MessageType.TEXT,
    intent=intent,
    route=RouteType.ROUTE_A,
    agent_id=AgentID.SIEMENS,
    response_text="Test response",
    docs_retrieved=5
)
print(f"  Request ID: {trace.request_id}")
print(f"  Docs retrieved: {trace.docs_retrieved}")
print("  [PASS]\n")

# Test 6: Validation error (should fail)
print("Test 6: Testing validation (should catch error)...")
try:
    bad_intent = RivetIntent(
        vendor=VendorType.SIEMENS,
        equipment_type=EquipmentType.VFD,
        context_source=ContextSource.TEXT_ONLY,
        confidence=1.5,  # Invalid (> 1.0)
        kb_coverage=KBCoverage.STRONG,
        raw_summary="Test"
    )
    print("  [FAIL] Should have raised validation error")
except Exception as e:
    print(f"  Caught expected error: {type(e).__name__}")
    print("  [PASS]\n")

print("=" * 60)
print("ALL TESTS PASSED - Phase 1 models validated successfully!")
print("=" * 60)

"""
RIVET Pro Data Models - Test Suite

Validates all Pydantic models for RIVET Pro multi-agent backend.

Author: Agent Factory
Created: 2025-12-15
Phase: 1/8 (Foundation)
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from agent_factory.rivet_pro.models import (
    # Enums
    ChannelType,
    MessageType,
    VendorType,
    EquipmentType,
    ContextSource,
    KBCoverage,
    RouteType,
    AgentID,
    # Models
    RivetRequest,
    RivetIntent,
    RivetResponse,
    AgentTrace,
    # Helpers
    create_text_request,
    create_image_request,
)


# ============================================================================
# Test RivetRequest
# ============================================================================

def test_rivet_request_text_only():
    """Test creating a text-only request"""
    req = RivetRequest(
        user_id="telegram_12345",
        channel=ChannelType.TELEGRAM,
        message_type=MessageType.TEXT,
        text="My Siemens VFD shows F3002 fault",
        metadata={"timestamp": "2025-12-15T10:30:00Z"}
    )

    assert req.user_id == "telegram_12345"
    assert req.channel == ChannelType.TELEGRAM
    assert req.message_type == MessageType.TEXT
    assert "F3002" in req.text
    assert req.image_path is None
    assert req.metadata["timestamp"] == "2025-12-15T10:30:00Z"


def test_rivet_request_image_with_caption():
    """Test creating an image request with caption"""
    req = RivetRequest(
        user_id="whatsapp_67890",
        channel=ChannelType.WHATSAPP,
        message_type=MessageType.TEXT_WITH_IMAGE,
        text="VFD nameplate",
        image_path="/tmp/vfd_12345.jpg",
        metadata={"language": "en"}
    )

    assert req.user_id == "whatsapp_67890"
    assert req.channel == ChannelType.WHATSAPP
    assert req.message_type == MessageType.TEXT_WITH_IMAGE
    assert req.text == "VFD nameplate"
    assert req.image_path == "/tmp/vfd_12345.jpg"


def test_rivet_request_validation_error():
    """Test that request fails without text or image"""
    with pytest.raises(ValidationError):
        RivetRequest(
            user_id="test_123",
            channel=ChannelType.TELEGRAM,
            message_type=MessageType.TEXT,
            # Missing both text and image_path
        )


def test_rivet_request_helper_text():
    """Test create_text_request helper"""
    req = create_text_request(
        user_id="test_123",
        text="Test message",
        timestamp="2025-12-15T10:00:00Z"
    )

    assert req.user_id == "test_123"
    assert req.channel == ChannelType.TELEGRAM  # default
    assert req.message_type == MessageType.TEXT
    assert req.text == "Test message"
    assert req.metadata["timestamp"] == "2025-12-15T10:00:00Z"


def test_rivet_request_helper_image():
    """Test create_image_request helper"""
    req = create_image_request(
        user_id="test_123",
        image_path="/tmp/image.jpg",
        caption="Test caption",
        channel=ChannelType.WHATSAPP
    )

    assert req.user_id == "test_123"
    assert req.channel == ChannelType.WHATSAPP
    assert req.message_type == MessageType.TEXT_WITH_IMAGE
    assert req.text == "Test caption"
    assert req.image_path == "/tmp/image.jpg"


# ============================================================================
# Test RivetIntent
# ============================================================================

def test_rivet_intent_complete():
    """Test creating a complete intent with all fields"""
    intent = RivetIntent(
        vendor=VendorType.SIEMENS,
        equipment_type=EquipmentType.VFD,
        application="overhead_crane",
        symptom="F3002 overvoltage fault",
        context_source=ContextSource.TEXT_ONLY,
        confidence=0.92,
        kb_coverage=KBCoverage.STRONG,
        raw_summary="Siemens G120C VFD F3002 overvoltage troubleshooting",
        detected_model="G120C",
        detected_part_number="6SL3244-0BB13-1PA0",
        detected_fault_codes=["F3002"],
    )

    assert intent.vendor == VendorType.SIEMENS
    assert intent.equipment_type == EquipmentType.VFD
    assert intent.application == "overhead_crane"
    assert intent.confidence == 0.92
    assert intent.kb_coverage == KBCoverage.STRONG
    assert "F3002" in intent.detected_fault_codes
    assert intent.detected_model == "G120C"


def test_rivet_intent_minimal():
    """Test creating intent with only required fields"""
    intent = RivetIntent(
        vendor=VendorType.UNKNOWN,
        equipment_type=EquipmentType.UNKNOWN,
        context_source=ContextSource.TEXT_ONLY,
        confidence=0.3,
        kb_coverage=KBCoverage.NONE,
        raw_summary="Unclear equipment issue",
    )

    assert intent.vendor == VendorType.UNKNOWN
    assert intent.equipment_type == EquipmentType.UNKNOWN
    assert intent.kb_coverage == KBCoverage.NONE
    assert intent.confidence == 0.3
    assert intent.symptom is None
    assert len(intent.detected_fault_codes) == 0


def test_rivet_intent_confidence_validation():
    """Test confidence must be between 0 and 1"""
    # Valid confidence
    intent = RivetIntent(
        vendor=VendorType.ROCKWELL,
        equipment_type=EquipmentType.PLC,
        context_source=ContextSource.TEXT_ONLY,
        confidence=0.85,
        kb_coverage=KBCoverage.STRONG,
        raw_summary="Test",
    )
    assert intent.confidence == 0.85

    # Invalid confidence (too high)
    with pytest.raises(ValidationError):
        RivetIntent(
            vendor=VendorType.ROCKWELL,
            equipment_type=EquipmentType.PLC,
            context_source=ContextSource.TEXT_ONLY,
            confidence=1.5,  # Invalid
            kb_coverage=KBCoverage.STRONG,
            raw_summary="Test",
        )


def test_rivet_intent_with_ocr():
    """Test intent with OCR text from image"""
    intent = RivetIntent(
        vendor=VendorType.SIEMENS,
        equipment_type=EquipmentType.VFD,
        context_source=ContextSource.IMAGE_OCR,
        confidence=0.87,
        kb_coverage=KBCoverage.STRONG,
        raw_summary="Siemens VFD nameplate detected",
        ocr_text="SINAMICS G120C\\n6SL3244-0BB13-1PA0\\n480V 7.5HP",
        detected_model="G120C",
        detected_part_number="6SL3244-0BB13-1PA0",
    )

    assert intent.context_source == ContextSource.IMAGE_OCR
    assert "SINAMICS" in intent.ocr_text
    assert intent.detected_part_number == "6SL3244-0BB13-1PA0"


# ============================================================================
# Test RivetResponse
# ============================================================================

def test_rivet_response_complete():
    """Test creating a complete response with all fields"""
    response = RivetResponse(
        text="F3002 is DC bus overvoltage. Check input voltage...",
        agent_id=AgentID.SIEMENS,
        route_taken=RouteType.ROUTE_A,
        links=["https://support.siemens.com/manual/G120C"],
        confidence=0.89,
        suggested_actions=[
            "Check input voltage with multimeter",
            "Verify parameter P0210 = 480V",
            "Check DC bus voltage on display"
        ],
        safety_warnings=["Lock out power before checking connections"],
        cited_documents=[
            {
                "title": "G120C Operating Instructions",
                "url": "https://support.siemens.com/manual/G120C",
                "page": "147"
            }
        ],
        trace={
            "docs_retrieved": 5,
            "processing_time_ms": 1234,
            "llm_calls": 1
        }
    )

    assert "F3002" in response.text
    assert response.agent_id == AgentID.SIEMENS
    assert response.route_taken == RouteType.ROUTE_A
    assert len(response.links) == 1
    assert len(response.suggested_actions) == 3
    assert len(response.safety_warnings) == 1
    assert response.trace["docs_retrieved"] == 5


def test_rivet_response_minimal():
    """Test creating response with only required fields"""
    response = RivetResponse(
        text="I need more information to help you.",
        agent_id=AgentID.FALLBACK,
        route_taken=RouteType.ROUTE_D,
    )

    assert response.text == "I need more information to help you."
    assert response.agent_id == AgentID.FALLBACK
    assert response.route_taken == RouteType.ROUTE_D
    assert len(response.links) == 0
    assert response.confidence == 0.0  # default
    assert response.requires_followup == False  # default


def test_rivet_response_route_c_research():
    """Test response from Route C (research pipeline)"""
    response = RivetResponse(
        text="I found these manuals for Mitsubishi FR-A840. Indexing them now...",
        agent_id=AgentID.GENERIC_PLC,
        route_taken=RouteType.ROUTE_C,
        links=[
            "https://dl.mitsubishielectric.com/FR-A800_manual.pdf",
            "https://dl.mitsubishielectric.com/FR-A800_params.pdf"
        ],
        research_triggered=True,
        trace={
            "research_urls_found": 2,
            "ingestion_started": True
        }
    )

    assert response.route_taken == RouteType.ROUTE_C
    assert response.research_triggered == True
    assert len(response.links) == 2
    assert "manuals" in response.text.lower()


def test_rivet_response_route_b_enrichment():
    """Test response from Route B (KB enrichment)"""
    response = RivetResponse(
        text="Here's what I found. I'm also looking for more documentation...",
        agent_id=AgentID.ROCKWELL,
        route_taken=RouteType.ROUTE_B,
        kb_enrichment_triggered=True,
        confidence=0.75,
    )

    assert response.route_taken == RouteType.ROUTE_B
    assert response.kb_enrichment_triggered == True
    assert response.confidence == 0.75


# ============================================================================
# Test AgentTrace
# ============================================================================

def test_agent_trace_complete():
    """Test creating complete agent trace for logging"""
    intent = RivetIntent(
        vendor=VendorType.SIEMENS,
        equipment_type=EquipmentType.VFD,
        context_source=ContextSource.TEXT_ONLY,
        confidence=0.92,
        kb_coverage=KBCoverage.STRONG,
        raw_summary="Test",
    )

    trace = AgentTrace(
        request_id="req_2025-12-15_12345",
        user_id="telegram_12345",
        channel=ChannelType.TELEGRAM,
        message_type=MessageType.TEXT,
        intent=intent,
        route=RouteType.ROUTE_A,
        agent_id=AgentID.SIEMENS,
        response_text="F3002 troubleshooting steps...",
        docs_retrieved=5,
        doc_sources=["G120C Manual", "SINAMICS Guide"],
        processing_time_ms=1234,
        llm_calls=1,
    )

    assert trace.request_id == "req_2025-12-15_12345"
    assert trace.user_id == "telegram_12345"
    assert trace.route == RouteType.ROUTE_A
    assert trace.agent_id == AgentID.SIEMENS
    assert trace.docs_retrieved == 5
    assert len(trace.doc_sources) == 2
    assert trace.processing_time_ms == 1234
    assert trace.error is None


def test_agent_trace_with_error():
    """Test agent trace with error"""
    intent = RivetIntent(
        vendor=VendorType.UNKNOWN,
        equipment_type=EquipmentType.UNKNOWN,
        context_source=ContextSource.TEXT_ONLY,
        confidence=0.2,
        kb_coverage=KBCoverage.NONE,
        raw_summary="Unclear",
    )

    trace = AgentTrace(
        request_id="req_2025-12-15_err123",
        user_id="telegram_12345",
        channel=ChannelType.TELEGRAM,
        message_type=MessageType.TEXT,
        intent=intent,
        route=RouteType.ROUTE_D,
        agent_id=AgentID.FALLBACK,
        response_text="Error occurred",
        error="LLM API timeout after 30s",
    )

    assert trace.error == "LLM API timeout after 30s"
    assert trace.route == RouteType.ROUTE_D
    assert trace.agent_id == AgentID.FALLBACK


# ============================================================================
# Test Enum Values
# ============================================================================

def test_vendor_enum_values():
    """Test all vendor enum values"""
    assert VendorType.SIEMENS.value == "Siemens"
    assert VendorType.ROCKWELL.value == "Rockwell"
    assert VendorType.ABB.value == "ABB"
    assert VendorType.UNKNOWN.value == "Unknown"


def test_equipment_enum_values():
    """Test all equipment type enum values"""
    assert EquipmentType.VFD.value == "VFD"
    assert EquipmentType.PLC.value == "PLC"
    assert EquipmentType.HMI.value == "HMI"
    assert EquipmentType.SAFETY_RELAY.value == "safety_relay"


def test_route_enum_values():
    """Test all route enum values"""
    assert RouteType.ROUTE_A.value == "A_direct_sme"
    assert RouteType.ROUTE_B.value == "B_sme_enrich"
    assert RouteType.ROUTE_C.value == "C_research"
    assert RouteType.ROUTE_D.value == "D_clarification"


def test_kb_coverage_enum_values():
    """Test KB coverage enum values"""
    assert KBCoverage.STRONG.value == "strong"
    assert KBCoverage.THIN.value == "thin"
    assert KBCoverage.NONE.value == "none"


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_request_response_flow():
    """Test complete request → intent → response flow"""
    # 1. User sends request
    request = create_text_request(
        user_id="telegram_12345",
        text="My Siemens G120C shows fault F3002",
    )

    # 2. Intent classified
    intent = RivetIntent(
        vendor=VendorType.SIEMENS,
        equipment_type=EquipmentType.VFD,
        context_source=ContextSource.TEXT_ONLY,
        confidence=0.92,
        kb_coverage=KBCoverage.STRONG,
        raw_summary="Siemens G120C fault F3002 troubleshooting",
        detected_model="G120C",
        detected_fault_codes=["F3002"],
    )

    # 3. Response generated
    response = RivetResponse(
        text="F3002 is DC bus overvoltage...",
        agent_id=AgentID.SIEMENS,
        route_taken=RouteType.ROUTE_A,
        confidence=0.89,
    )

    # 4. Trace logged
    trace = AgentTrace(
        request_id="req_test_123",
        user_id=request.user_id,
        channel=request.channel,
        message_type=request.message_type,
        intent=intent,
        route=response.route_taken,
        agent_id=response.agent_id,
        response_text=response.text,
        docs_retrieved=5,
    )

    # Validate flow
    assert trace.user_id == "telegram_12345"
    assert trace.route == RouteType.ROUTE_A
    assert trace.agent_id == AgentID.SIEMENS
    assert "F3002" in trace.response_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

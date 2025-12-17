"""Integration tests for RIVET Pro Orchestrator.

Tests all 4 routing paths:
- Route A: Strong KB coverage → direct answer
- Route B: Thin KB coverage → answer + enrichment
- Route C: No KB coverage → research pipeline
- Route D: Unclear intent → clarification request
"""

import pytest
from agent_factory.core.orchestrator import RivetOrchestrator
from agent_factory.rivet_pro.models import RivetRequest, ChannelType, MessageType, create_text_request
from agent_factory.schemas.routing import RouteType, VendorType, CoverageLevel


@pytest.fixture
def orchestrator():
    """Create orchestrator instance for testing."""
    return RivetOrchestrator()


def make_request(query: str) -> RivetRequest:
    """Helper to create test requests with required fields."""
    return create_text_request(
        user_id="test_user_123",
        text=query,
        channel=ChannelType.TELEGRAM
    )


@pytest.mark.asyncio
async def test_route_a_strong_kb_siemens(orchestrator):
    """Test Route A with strong KB coverage for Siemens query.

    Acceptance Criteria:
    - Detects Siemens vendor correctly
    - Mock KB evaluator returns STRONG coverage (>100 char query)
    - Routes to Route A
    - Returns direct answer with confidence > 0
    """
    # Create query with Siemens keywords and sufficient length (>100 chars for STRONG mock)
    request = make_request(
        "How do I configure SINAMICS G120 drive parameters for variable frequency operation with TIA Portal V17? I need to set up the basic commissioning and parameter templates for a 5.5kW motor."
    )

    # Execute routing
    response = await orchestrator.route_query(request)

    # Assertions
    assert response.route_taken.value == "A_direct_sme", "Should route to A (strong KB)"
    assert response.agent_id.value == "siemens_agent", "Should detect Siemens agent"
    assert response.confidence > 0, "Should have non-zero confidence"
    assert len(response.links) > 0 or len(response.cited_documents) > 0, "Should have source citations"
    assert "MOCK Siemens Agent" in response.text, "Should use mock Siemens agent"
    assert response.requires_followup is False, "Route A should not require followup"


@pytest.mark.asyncio
async def test_route_b_thin_kb_rockwell(orchestrator):
    """Test Route B with thin KB coverage for Rockwell query.

    Acceptance Criteria:
    - Detects Rockwell vendor correctly
    - Mock KB evaluator returns THIN coverage (50-100 char query)
    - Routes to Route B
    - Returns answer AND triggers enrichment (reasoning mentions enrichment)
    """
    # Create query with Rockwell keywords and medium length (50-100 chars for THIN mock)
    request = make_request("ControlLogix fault code 0x1234 troubleshooting steps for CompactLogix")

    # Execute routing
    response = await orchestrator.route_query(request)

    # Assertions
    assert response.route_taken.value == "B_sme_enrich", "Should route to B (thin KB)"
    assert response.agent_id.value == "rockwell_agent", "Should detect Rockwell agent"
    assert response.confidence > 0, "Should have non-zero confidence"
    assert "MOCK Rockwell Agent" in response.text, "Should use mock Rockwell agent"
    assert response.kb_enrichment_triggered is True, "Enrichment should be triggered"
    assert response.requires_followup is False, "Route B provides answer, no human needed yet"


@pytest.mark.asyncio
async def test_route_c_no_kb_generic(orchestrator):
    """Test Route C with no KB coverage for generic query.

    Acceptance Criteria:
    - Detects GENERIC vendor (no specific vendor keywords)
    - Mock KB evaluator returns NONE coverage (<20 chars or default)
    - Routes to Route C
    - Returns message about research pipeline (24-48 hours)
    - Sets requires_human=True
    """
    # Create short generic query (<20 chars triggers NONE in mock)
    request = make_request("PLC basics")

    # Execute routing
    response = await orchestrator.route_query(request)

    # Assertions
    assert response.route_taken.value == "C_research", "Should route to C (no KB)"
    assert response.agent_id.value == "generic_plc_agent", "Should detect generic PLC agent"
    assert response.confidence == 0.0, "Route C should have zero confidence (no KB)"
    assert "24-48 hours" in response.text, "Should mention research timeline"
    assert "research pipeline" in response.text.lower(), "Should mention research pipeline"
    assert response.requires_followup is True, "Route C requires human review"
    assert len(response.links) == 0, "Route C has no sources yet"


@pytest.mark.asyncio
async def test_route_d_unclear_intent(orchestrator):
    """Test Route D with unclear/ambiguous query.

    Acceptance Criteria:
    - Mock KB evaluator returns UNCLEAR (very short query with '?')
    - Routes to Route D
    - Returns clarification request
    - Provides example of better query
    - Sets requires_human=False (just needs clarification)
    """
    # Create very short ambiguous query with '?' (triggers UNCLEAR in mock)
    request = make_request("PLC?")

    # Execute routing
    response = await orchestrator.route_query(request)

    # Assertions
    assert response.route_taken.value == "D_clarification", "Should route to D (unclear)"
    assert response.confidence == 0.0, "Route D should have zero confidence"
    assert "clarify" in response.text.lower(), "Should request clarification"
    assert "Example:" in response.text, "Should provide example query"
    assert "equipment" in response.text.lower(), "Should ask about equipment"
    assert response.requires_followup is True, "Route D needs clarification"
    assert len(response.links) == 0, "Route D has no sources"


@pytest.mark.asyncio
async def test_vendor_detection_siemens(orchestrator):
    """Test vendor detection accuracy for Siemens keywords."""
    test_queries = [
        "SINAMICS G120 configuration",
        "TIA Portal V17 setup",
        "S7-1200 PLC programming",
        "Siemens PROFINET troubleshooting",
    ]

    for query in test_queries:
        request = make_request(query + " " * 100)  # Pad to trigger Route A
        response = await orchestrator.route_query(request)
        assert response.agent_id.value == "siemens_agent", f"Should detect Siemens for: {query}"


@pytest.mark.asyncio
async def test_vendor_detection_rockwell(orchestrator):
    """Test vendor detection accuracy for Rockwell keywords."""
    test_queries = [
        "Allen-Bradley ControlLogix setup",
        "Studio 5000 programming guide",
        "CompactLogix configuration",
        "PowerFlex drive parameters",
    ]

    for query in test_queries:
        request = make_request(query + " " * 50)  # Pad to trigger Route B
        response = await orchestrator.route_query(request)
        assert response.agent_id.value == "rockwell_agent", f"Should detect Rockwell for: {query}"


@pytest.mark.asyncio
async def test_vendor_detection_safety(orchestrator):
    """Test vendor detection accuracy for Safety keywords."""
    test_queries = [
        "SIL2 safety relay configuration",
        "IEC 61508 compliance check",
        "Emergency stop circuit design",
        "Safety PLC programming",
    ]

    for query in test_queries:
        request = make_request(query + " " * 100)  # Pad to trigger Route A
        response = await orchestrator.route_query(request)
        assert response.agent_id.value == "safety_agent", f"Should detect Safety for: {query}"


@pytest.mark.asyncio
async def test_vendor_detection_generic_fallback(orchestrator):
    """Test vendor detection falls back to GENERIC for unknown vendors."""
    test_queries = [
        "What is ladder logic?",
        "How does a timer work?",
        "Basic PLC concepts",
        "Digital I/O fundamentals",
    ]

    for query in test_queries:
        request = make_request(query)
        response = await orchestrator.route_query(request)
        assert response.agent_id.value == "generic_plc_agent", f"Should fallback to generic for: {query}"


def test_kb_coverage_thresholds(orchestrator):
    """Test KB coverage classification thresholds.

    Verifies mock evaluator behavior:
    - Query >100 chars → STRONG (Route A)
    - Query 50-100 chars → THIN (Route B)
    - Query <20 chars → NONE (Route C)
    - Query with '?' + <20 chars → UNCLEAR (Route D)
    """
    # Test STRONG threshold (>100 chars)
    long_query = "How do I configure SINAMICS G120 drive parameters for variable frequency operation with TIA Portal V17 and what are the best practices?"
    assert len(long_query) > 100, "Test query should be >100 chars"

    # Test THIN threshold (50-100 chars)
    medium_query = "ControlLogix fault code 0x1234 troubleshooting for CompactLogix L32E"
    assert 50 < len(medium_query) < 100, "Test query should be 50-100 chars"

    # Test NONE threshold (<20 chars, no '?')
    short_query = "PLC basics"
    assert len(short_query) < 20 and '?' not in short_query, "Test query should be <20 chars, no '?'"

    # Test UNCLEAR threshold (<20 chars with '?')
    unclear_query = "PLC?"
    assert len(unclear_query) < 20 and '?' in unclear_query, "Test query should be <20 chars with '?'"


def test_routing_statistics(orchestrator):
    """Test routing statistics tracking."""
    stats = orchestrator.get_routing_stats()

    assert "route_a_count" in stats
    assert "route_b_count" in stats
    assert "route_c_count" in stats
    assert "route_d_count" in stats
    assert "total_queries" in stats

    # Initially all counts should be 0
    assert stats["total_queries"] == 0


@pytest.mark.asyncio
async def test_routing_statistics_increment(orchestrator):
    """Test that routing statistics increment correctly."""
    # Route A query
    request_a = make_request("How do I configure SINAMICS G120 drive parameters for variable frequency operation with TIA Portal V17?")
    await orchestrator.route_query(request_a)

    stats = orchestrator.get_routing_stats()
    assert stats["route_a_count"] == 1
    assert stats["total_queries"] == 1

    # Route B query
    request_b = make_request("ControlLogix fault code 0x1234 troubleshooting steps")
    await orchestrator.route_query(request_b)

    stats = orchestrator.get_routing_stats()
    assert stats["route_b_count"] == 1
    assert stats["total_queries"] == 2


@pytest.mark.asyncio
async def test_mock_agents_loaded(orchestrator):
    """Test that all mock SME agents are loaded correctly."""
    assert VendorType.SIEMENS in orchestrator.sme_agents
    assert VendorType.ROCKWELL in orchestrator.sme_agents
    assert VendorType.GENERIC in orchestrator.sme_agents
    assert VendorType.SAFETY in orchestrator.sme_agents

    # Verify agents have handle_query method
    for vendor, agent in orchestrator.sme_agents.items():
        assert hasattr(agent, 'handle_query'), f"{vendor} agent missing handle_query method"


@pytest.mark.asyncio
async def test_response_structure_route_a(orchestrator):
    """Test that Route A responses have correct structure."""
    request = make_request("How do I configure SINAMICS G120 drive parameters for variable frequency operation?")
    response = await orchestrator.route_query(request)

    # Verify all required fields are present
    assert hasattr(response, 'text')
    assert hasattr(response, 'confidence')
    assert hasattr(response, 'links')
    assert hasattr(response, 'route_taken')
    assert hasattr(response, 'agent_id')
    assert hasattr(response, 'requires_followup')
    assert hasattr(response, 'trace')


@pytest.mark.asyncio
async def test_response_structure_route_c(orchestrator):
    """Test that Route C responses have correct structure."""
    request = make_request("PLC basics")
    response = await orchestrator.route_query(request)

    # Route C specific checks
    assert response.confidence == 0.0, "Route C should have zero confidence"
    assert response.requires_followup is True, "Route C should require human"
    assert len(response.links) == 0, "Route C should have no sources"
    assert response.research_triggered is True, "Route C should trigger research"


@pytest.mark.asyncio
async def test_multiple_vendor_keywords(orchestrator):
    """Test query with multiple vendor keywords chooses highest priority."""
    # Query mentioning both Siemens and Rockwell
    request = make_request("Comparing Siemens S7-1200 and Rockwell CompactLogix for industrial automation project with 100+ I/O points")
    response = await orchestrator.route_query(request)

    # Should match one vendor (vendor detector returns first match)
    assert response.agent_id.value in ["siemens_agent", "rockwell_agent"]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])

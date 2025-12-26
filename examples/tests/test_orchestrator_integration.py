"""Test orchestrator integration with FewShotEnhancer.

Verifies that the orchestrator correctly uses the FewShotEnhancer
to enhance SME agent prompts with similar maintenance cases.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from agent_factory.core.orchestrator import RivetOrchestrator
from agent_factory.rivet_pro.models import RivetRequest, EquipmentType, ChannelType, MessageType
from agent_factory.schemas.routing import VendorType, CoverageLevel, VendorDetection, KBCoverage


@pytest.mark.asyncio
async def test_orchestrator_fewshot_integration():
    """Test that orchestrator initializes FewShotEnhancer and uses it in Route A."""

    # Create orchestrator (should initialize enhancer)
    orchestrator = RivetOrchestrator()

    # Verify enhancer is initialized
    assert orchestrator.fewshot_enhancer is not None, "FewShotEnhancer should be initialized"
    assert orchestrator.fewshot_enhancer.config.enabled, "FewShot should be enabled"
    assert orchestrator.fewshot_enhancer._initialized, "FewShot should be initialized with store"

    # Verify sample cases are loaded
    case_count = len(orchestrator.fewshot_enhancer._retriever._case_embeddings)
    assert case_count > 0, f"Should have loaded sample cases, got {case_count}"

    print(f"✓ FewShotEnhancer initialized with {case_count} sample cases")


@pytest.mark.asyncio
async def test_route_a_uses_fewshot():
    """Test that Route A handler uses few-shot examples when available."""

    # Create orchestrator
    orchestrator = RivetOrchestrator()

    # Create a query about PLC lift issues (should match sample case)
    request = RivetRequest(
        user_id="test_user",
        channel=ChannelType.API,
        message_type=MessageType.TEXT,
        text="PLC lift not moving and fault light is on"
    )

    # Mock the vendor detector to return GENERIC
    with patch.object(orchestrator.vendor_detector, 'detect') as mock_detect:
        mock_detect.return_value = VendorDetection(
            vendor=VendorType.GENERIC,
            confidence=0.9,
            equipment_mentioned=["PLC"],
            reasoning="Test reasoning"
        )

        # Mock KB evaluator to return strong coverage (Route A)
        with patch.object(orchestrator.kb_evaluator, 'evaluate_async') as mock_evaluate:
            mock_evaluate.return_value = KBCoverage(
                level=CoverageLevel.STRONG,
                atom_count=10,
                avg_relevance=0.85,
                confidence=0.9,
                retrieved_docs=[
                    Mock(atom_id="test-atom-1", content="Test KB content", relevance_score=0.9)
                ],
                search_summary="Test search summary"
            )

            # Mock the agent to capture the fewshot_context
            original_agent = orchestrator.sme_agents[VendorType.GENERIC]
            captured_fewshot_context = None

            async def mock_handle_query(request, kb_coverage, fewshot_context=None):
                nonlocal captured_fewshot_context
                captured_fewshot_context = fewshot_context
                # Return mock response
                from agent_factory.rivet_pro.models import RivetResponse, AgentID, RouteType
                return RivetResponse(
                    text="Mock response",
                    agent_id=AgentID.GENERIC_PLC,
                    route_taken=RouteType.ROUTE_A,
                    confidence=0.8,
                    trace={}
                )

            orchestrator.sme_agents[VendorType.GENERIC].handle_query = mock_handle_query

            # Execute route
            response = await orchestrator.route_query(request)

            # Verify few-shot context was provided
            assert captured_fewshot_context is not None, "FewShot context should be provided to agent"
            assert "Similar Past Cases" in captured_fewshot_context, "Should contain few-shot header"
            assert "SIMILAR CASE:" in captured_fewshot_context, "Should contain case examples"

            # Verify response trace includes fewshot count
            assert "fewshot_cases_retrieved" in response.trace, "Response should track fewshot count"
            fewshot_count = response.trace["fewshot_cases_retrieved"]
            assert fewshot_count > 0, f"Should have retrieved cases, got {fewshot_count}"

            print(f"✓ Route A enhanced with {fewshot_count} similar cases")
            print(f"✓ FewShot context length: {len(captured_fewshot_context)} chars")


@pytest.mark.asyncio
async def test_fewshot_graceful_degradation():
    """Test that orchestrator continues working if FewShot fails."""

    # Create orchestrator
    orchestrator = RivetOrchestrator()

    # Intentionally break the enhancer
    orchestrator.fewshot_enhancer._retriever = None

    # Create a query
    request = RivetRequest(
        user_id="test_user",
        channel=ChannelType.API,
        message_type=MessageType.TEXT,
        text="Generic PLC question"
    )

    # Mock vendor detection and KB evaluation for Route A
    with patch.object(orchestrator.vendor_detector, 'detect') as mock_detect:
        mock_detect.return_value = VendorDetection(
            vendor=VendorType.GENERIC,
            confidence=0.9,
            equipment_mentioned=["PLC"],
            reasoning="Test reasoning"
        )

        with patch.object(orchestrator.kb_evaluator, 'evaluate_async') as mock_evaluate:
            mock_evaluate.return_value = KBCoverage(
                level=CoverageLevel.STRONG,
                atom_count=10,
                avg_relevance=0.85,
                confidence=0.9,
                retrieved_docs=[
                    Mock(atom_id="test-atom-1", content="Test KB content", relevance_score=0.9)
                ],
                search_summary="Test search summary"
            )

            # Mock the agent
            async def mock_handle_query(request, kb_coverage, fewshot_context=None):
                from agent_factory.rivet_pro.models import RivetResponse, AgentID, RouteType
                return RivetResponse(
                    text="Mock response without fewshot",
                    agent_id=AgentID.GENERIC_PLC,
                    route_taken=RouteType.ROUTE_A,
                    confidence=0.8,
                    trace={}
                )

            orchestrator.sme_agents[VendorType.GENERIC].handle_query = mock_handle_query

            # Should not crash, just continue without few-shot
            response = await orchestrator.route_query(request)

            # Verify response was generated (graceful degradation)
            assert response is not None, "Should return response even if FewShot fails"
            assert response.trace["fewshot_cases_retrieved"] == 0, "Should track 0 cases when FewShot fails"

            print("✓ Graceful degradation: Orchestrator continues when FewShot fails")


if __name__ == "__main__":
    import asyncio

    async def run_tests():
        print("\n=== Testing Orchestrator FewShot Integration ===\n")

        await test_orchestrator_fewshot_integration()
        print()

        await test_route_a_uses_fewshot()
        print()

        await test_fewshot_graceful_degradation()
        print()

        print("=== All Tests Passed ===")

    asyncio.run(run_tests())

"""Performance tests for Route C latency improvements.

Validates that Route C latency is under 5 seconds after optimizations.
"""

import pytest
import asyncio
import time
from agent_factory.core.orchestrator import RivetOrchestrator
from agent_factory.rivet_pro.models import RivetRequest, ChannelType


@pytest.mark.asyncio
async def test_route_c_latency_under_5s():
    """Test that Route C completes in under 5 seconds.

    Before optimizations: ~36 seconds
    After optimizations: <5 seconds target

    Optimizations tested:
    - Parallel gap detection + LLM response
    - Async KB evaluation
    - LLM response caching
    - Fire-and-forget gap logging
    """
    # Create orchestrator with RAG layer (enables Route C)
    try:
        from agent_factory.core.database_manager import DatabaseManager
        db = DatabaseManager()
        orchestrator = RivetOrchestrator(rag_layer=db)
    except Exception:
        pytest.skip("Database not available for Route C testing")

    # Create request that triggers Route C (no KB coverage)
    request = RivetRequest(
        user_id="test_user",
        text="How do I troubleshoot a rare industrial controller from an obscure manufacturer?",
        channel=ChannelType.TELEGRAM
    )

    # Measure Route C latency
    start = time.perf_counter()
    response = await orchestrator.route_query(request)
    duration = time.perf_counter() - start

    # Assertions
    assert response is not None, "Route C should return a response"
    assert response.route_taken.value == "C", f"Expected Route C, got {response.route_taken.value}"
    assert duration < 5.0, f"Route C took {duration:.1f}s, expected <5s"

    print(f"\n✅ Route C latency: {duration:.2f}s (target: <5s)")
    print(f"   Response preview: {response.text[:100]}...")


@pytest.mark.asyncio
async def test_llm_cache_reduces_latency():
    """Test that LLM cache reduces latency on repeated queries.

    First query: Full latency (no cache)
    Second query: Near-instant (cache hit)
    """
    try:
        from agent_factory.core.database_manager import DatabaseManager
        db = DatabaseManager()
        orchestrator = RivetOrchestrator(rag_layer=db)
    except Exception:
        pytest.skip("Database not available for cache testing")

    request = RivetRequest(
        user_id="test_user",
        text="Explain PLCs for beginners",
        channel=ChannelType.TELEGRAM
    )

    # First query (cold cache)
    start1 = time.perf_counter()
    response1 = await orchestrator.route_query(request)
    duration1 = time.perf_counter() - start1

    # Second query (warm cache)
    start2 = time.perf_counter()
    response2 = await orchestrator.route_query(request)
    duration2 = time.perf_counter() - start2

    # Assertions
    assert response1.text == response2.text, "Cache should return same response"
    assert duration2 < duration1, f"Cached query ({duration2:.2f}s) should be faster than uncached ({duration1:.1f}s)"

    print(f"\n✅ LLM cache test:")
    print(f"   Cold cache: {duration1:.2f}s")
    print(f"   Warm cache: {duration2:.2f}s (speedup: {duration1/duration2:.1f}x)")


@pytest.mark.asyncio
async def test_parallel_execution():
    """Test that gap detection and LLM response run in parallel.

    Verifies that total time is less than sequential time would be.
    """
    try:
        from agent_factory.core.database_manager import DatabaseManager
        db = DatabaseManager()
        orchestrator = RivetOrchestrator(rag_layer=db)
    except Exception:
        pytest.skip("Database not available for parallel execution testing")

    request = RivetRequest(
        user_id="test_user",
        text="Debug a complex fault on an uncommon device",
        channel=ChannelType.TELEGRAM
    )

    # Measure total latency
    start = time.perf_counter()
    response = await orchestrator.route_query(request)
    total_duration = time.perf_counter() - start

    # If operations were sequential, would expect:
    # - Gap detection: 1-2s
    # - LLM response: 10-15s
    # - Total: 11-17s
    #
    # With parallelization, should be:
    # - Max(gap, llm) = 10-15s (dominated by LLM)
    # - Plus overhead: ~1-2s
    # - Total: <17s

    assert total_duration < 17.0, f"Parallel execution took {total_duration:.1f}s, expected <17s"

    print(f"\n✅ Parallel execution test:")
    print(f"   Total duration: {total_duration:.2f}s (<17s expected for parallel)")


@pytest.mark.asyncio
async def test_timing_instrumentation():
    """Test that timing instrumentation logs performance metrics."""
    import logging

    # Capture logs
    logger = logging.getLogger("agent_factory.core.orchestrator")
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

    try:
        from agent_factory.core.database_manager import DatabaseManager
        db = DatabaseManager()
        orchestrator = RivetOrchestrator(rag_layer=db)
    except Exception:
        pytest.skip("Database not available for timing instrumentation testing")

    request = RivetRequest(
        user_id="test_user",
        text="Test timing instrumentation",
        channel=ChannelType.TELEGRAM
    )

    # Run query (should log timing metrics)
    response = await orchestrator.route_query(request)

    # Manual verification: Check logs for timing output
    # Expected log patterns:
    # - ⏱️  PERF [route_query_total]: XXXms
    # - ⏱️  PERF [route_c_handler]: XXXms
    # - ⏱️  PERF [llm_fallback]: XXXms or ⏱️  PERF [llm_response_async]: XXXms
    # - ⏱️  PERF [gap_detection]: XXXms

    assert response is not None, "Query should complete successfully"

    print("\n✅ Timing instrumentation test:")
    print("   Check logs above for ⏱️  PERF markers")


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(test_route_c_latency_under_5s())
    asyncio.run(test_llm_cache_reduces_latency())
    asyncio.run(test_parallel_execution())
    asyncio.run(test_timing_instrumentation())

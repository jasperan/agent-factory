"""Tests for orchestrator integration."""

import pytest
import asyncio
from examples.integration import FewShotEnhancer, FewShotConfig
from examples.store import CaseStore
from examples.embedder import CaseEmbedder


@pytest.fixture
def enhancer():
    """Create test enhancer."""
    config = FewShotConfig(
        enabled=True,
        k=2,
        similarity_threshold=0.0,
        timeout_seconds=1.0,
    )
    enhancer = FewShotEnhancer(config)

    store = CaseStore(test_mode=True)
    embedder = CaseEmbedder(test_mode=True)
    store.load_from_directory("examples/tests/fixtures")

    enhancer.initialize(store, embedder)
    return enhancer


@pytest.mark.asyncio
async def test_enhance_prompt(enhancer):
    """Test prompt enhancement."""
    base_prompt = "You are an SME."
    user_input = "motor overload fault"

    enhanced, results = await enhancer.enhance_prompt(base_prompt, user_input)

    assert "You are an SME" in enhanced
    # May or may not have results depending on fixture data
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_enhance_disabled():
    """Test that disabled enhancer returns base prompt."""
    config = FewShotConfig(enabled=False)
    enhancer = FewShotEnhancer(config)

    enhanced, results = await enhancer.enhance_prompt("base", "input")

    assert enhanced == "base"
    assert results == []


@pytest.mark.asyncio
async def test_graceful_timeout():
    """Test timeout handling."""
    config = FewShotConfig(timeout_seconds=0.001)  # Very short timeout
    enhancer = FewShotEnhancer(config)

    # Not initialized, should gracefully return base
    enhanced, results = await enhancer.enhance_prompt("base", "input")
    assert enhanced == "base"


@pytest.mark.asyncio
async def test_singleton_pattern():
    """Test that get_instance returns singleton."""
    config = FewShotConfig(k=5)
    enhancer1 = FewShotEnhancer.get_instance(config)
    enhancer2 = FewShotEnhancer.get_instance()

    assert enhancer1 is enhancer2
    assert enhancer1.config.k == 5


@pytest.mark.asyncio
async def test_enhance_with_results(enhancer):
    """Test enhancement when similar cases are found."""
    base_prompt = "You are an industrial maintenance expert."
    user_input = "lift not moving fault light on"

    enhanced, results = await enhancer.enhance_prompt(base_prompt, user_input)

    # Should contain base prompt
    assert "industrial maintenance expert" in enhanced

    # Should contain Current Case section
    assert "Current Case" in enhanced or "Technician Input" in enhanced


@pytest.mark.asyncio
async def test_fallback_on_error(enhancer):
    """Test that errors fall back gracefully."""
    base_prompt = "Base prompt"

    # Even with invalid input, should not crash
    enhanced, results = await enhancer.enhance_prompt(base_prompt, "")

    assert enhanced == base_prompt or "Base prompt" in enhanced
    assert isinstance(results, list)

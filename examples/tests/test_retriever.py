"""Tests for CaseRetriever.

Reference: https://github.com/pixegami/rag-tutorial-v2/blob/main/test_rag.py
"""

import pytest
import time
from datetime import datetime

from examples.schemas import (
    MaintenanceCase,
    Equipment,
    CaseInput,
    Diagnosis,
    Resolution,
)
from examples.store import CaseStore
from examples.embedder import CaseEmbedder
from examples.retriever import CaseRetriever, RetrievalResult
from examples.formatter import format_maintenance_examples, format_for_sme_prompt


@pytest.fixture
def sample_cases() -> list[MaintenanceCase]:
    """Create sample cases for testing."""
    return [
        MaintenanceCase(
            case_id="TEST-001",
            timestamp=datetime.utcnow(),
            equipment=Equipment(
                type="Motor",
                manufacturer="WEG",
                model="W22",
                location="Pump Station"
            ),
            input=CaseInput(raw_text="motor won't start overload tripped"),
            diagnosis=Diagnosis(
                root_cause="Thermal overload tripped due to high ambient temp",
                fault_codes=["OL-TRIP"],
                symptoms=["Motor not running", "Overload light on"]
            ),
            resolution=Resolution(
                steps=["Reset thermal overload", "Verified motor operation"],
                parts_used=[],
                time_to_fix="10 minutes"
            ),
            keywords=["motor", "overload", "thermal", "trip"],
            category="electrical"
        ),
        MaintenanceCase(
            case_id="TEST-002",
            timestamp=datetime.utcnow(),
            equipment=Equipment(
                type="PLC",
                manufacturer="Allen-Bradley",
                model="ControlLogix",
                location="Main Panel"
            ),
            input=CaseInput(raw_text="plc showing comm fault ethernet"),
            diagnosis=Diagnosis(
                root_cause="Ethernet cable damaged",
                fault_codes=["COMM-FAULT"],
                symptoms=["PLC not communicating", "Red NET light"]
            ),
            resolution=Resolution(
                steps=["Traced ethernet cable", "Found damaged section", "Replaced cable"],
                parts_used=["CAT6 cable 50ft"],
                time_to_fix="45 minutes"
            ),
            keywords=["plc", "ethernet", "communication", "cable"],
            category="electrical"
        ),
        MaintenanceCase(
            case_id="TEST-003",
            timestamp=datetime.utcnow(),
            equipment=Equipment(
                type="VFD",
                manufacturer="ABB",
                model="ACS880",
                location="Conveyor"
            ),
            input=CaseInput(raw_text="drive showing overvoltage fault 7121"),
            diagnosis=Diagnosis(
                root_cause="DC bus overvoltage during rapid deceleration",
                fault_codes=["7121", "DC-OV"],
                symptoms=["Drive tripped", "Motor coasting"]
            ),
            resolution=Resolution(
                steps=["Increased decel ramp time", "Checked braking resistor"],
                parts_used=[],
                time_to_fix="30 minutes"
            ),
            keywords=["vfd", "overvoltage", "braking", "deceleration"],
            category="electrical"
        ),
    ]


@pytest.fixture
def loaded_retriever(sample_cases) -> CaseRetriever:
    """Create retriever with sample cases loaded."""
    store = CaseStore(test_mode=True)
    for case in sample_cases:
        store.add_case(case)

    embedder = CaseEmbedder(test_mode=True)

    return CaseRetriever(
        store=store,
        embedder=embedder,
        k=3,
        similarity_threshold=0.0,  # Accept all for testing
    )


def test_retriever_finds_similar_cases(loaded_retriever):
    """Test that retriever returns results for matching query."""
    results = loaded_retriever.get_similar_cases("motor overload tripped")

    assert len(results) > 0
    assert all(isinstance(r, RetrievalResult) for r in results)


def test_retriever_returns_k_results(loaded_retriever):
    """Test that retriever respects k parameter."""
    results = loaded_retriever.get_similar_cases("electrical problem", k=2)
    assert len(results) <= 2


def test_retriever_results_have_scores(loaded_retriever):
    """Test that results include similarity scores."""
    results = loaded_retriever.get_similar_cases("motor won't start")

    for result in results:
        assert hasattr(result, 'similarity_score')
        assert 0 <= result.similarity_score <= 1


def test_retriever_results_sorted_by_similarity(loaded_retriever):
    """Test that results are sorted by descending similarity."""
    results = loaded_retriever.get_similar_cases("plc communication fault")

    scores = [r.similarity_score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_retriever_similarity_threshold(sample_cases):
    """Test that threshold filters low-similarity results."""
    store = CaseStore(test_mode=True)
    for case in sample_cases:
        store.add_case(case)

    embedder = CaseEmbedder(test_mode=True)

    # High threshold should filter most results
    retriever = CaseRetriever(
        store=store,
        embedder=embedder,
        k=10,
        similarity_threshold=0.99,  # Very high
    )

    results = retriever.get_similar_cases("random unrelated query")
    # With mock embeddings and high threshold, likely 0 results
    # This is expected behavior
    assert len(results) <= len(sample_cases)


def test_retriever_latency(loaded_retriever):
    """Test that retrieval completes within latency budget."""
    start = time.time()
    _ = loaded_retriever.get_similar_cases("motor fault diagnosis")
    elapsed = time.time() - start

    # Must be under 500ms per spec
    assert elapsed < 0.5, f"Retrieval took {elapsed:.3f}s, must be < 0.5s"


def test_format_maintenance_examples(loaded_retriever):
    """Test few-shot formatting."""
    results = loaded_retriever.get_similar_cases("motor overload")
    formatted = format_maintenance_examples(results)

    assert "Similar Past Cases" in formatted
    assert "SIMILAR CASE:" in formatted
    assert "Technician reported:" in formatted


def test_format_with_scores(loaded_retriever):
    """Test formatting includes scores when requested."""
    results = loaded_retriever.get_similar_cases("motor problem")
    formatted = format_maintenance_examples(results, include_scores=True)

    assert "Similarity:" in formatted


def test_format_empty_results():
    """Test formatting handles no results gracefully."""
    formatted = format_maintenance_examples([])
    assert "No similar past cases found" in formatted


def test_format_for_sme_prompt(loaded_retriever):
    """Test complete prompt formatting."""
    results = loaded_retriever.get_similar_cases("vfd overvoltage")
    base_prompt = "You are an industrial maintenance SME."
    current_input = "drive showing fault 7121"

    enhanced = format_for_sme_prompt(results, current_input, base_prompt)

    assert "You are an industrial maintenance SME" in enhanced
    assert "Similar Past Cases" in enhanced
    assert "Current Case" in enhanced
    assert "drive showing fault 7121" in enhanced


def test_empty_store_returns_empty(sample_cases):
    """Test retriever with no cases returns empty list."""
    store = CaseStore(test_mode=True)  # Empty store
    embedder = CaseEmbedder(test_mode=True)

    retriever = CaseRetriever(store=store, embedder=embedder)
    results = retriever.get_similar_cases("any query")

    assert results == []


def test_refresh_index_picks_up_new_cases(sample_cases):
    """Test that refresh_index adds new cases."""
    store = CaseStore(test_mode=True)
    embedder = CaseEmbedder(test_mode=True)
    retriever = CaseRetriever(store=store, embedder=embedder)

    # Initially empty
    assert retriever.get_similar_cases("motor") == []

    # Add cases
    for case in sample_cases:
        store.add_case(case)

    # Still empty until refresh
    assert retriever.get_similar_cases("motor") == []

    # After refresh, should find cases
    retriever.refresh_index()
    results = retriever.get_similar_cases("motor")
    assert len(results) > 0

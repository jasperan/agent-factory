"""Tests for CaseStore.

Reference: https://github.com/pixegami/rag-tutorial-v2/blob/main/test_rag.py
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from examples.schemas import (
    MaintenanceCase,
    Equipment,
    CaseInput,
    Diagnosis,
    Resolution,
)
from examples.store import CaseStore


@pytest.fixture
def sample_case() -> MaintenanceCase:
    """Create a sample maintenance case for testing."""
    return MaintenanceCase(
        case_id="TEST-001",
        timestamp=datetime.utcnow(),
        equipment=Equipment(
            type="PLC",
            manufacturer="Allen-Bradley",
            model="ControlLogix 5580",
            location="Test Stand A"
        ),
        input=CaseInput(
            raw_text="motor won't start fault light blinking",
            photo_url=None
        ),
        diagnosis=Diagnosis(
            root_cause="Thermal overload tripped",
            fault_codes=["OL1", "F002"],
            symptoms=["Motor not running", "OL light on"]
        ),
        resolution=Resolution(
            steps=[
                "Checked thermal overload",
                "Reset overload",
                "Verified motor running"
            ],
            parts_used=[],
            time_to_fix="15 minutes"
        ),
        keywords=["motor", "overload", "thermal", "controllogix"],
        category="electrical"
    )


@pytest.fixture
def test_store() -> CaseStore:
    """Create a test mode store."""
    return CaseStore(test_mode=True)


def test_schema_validation(sample_case):
    """Test that schema validates correctly."""
    assert sample_case.case_id == "TEST-001"
    assert sample_case.equipment.type == "PLC"
    assert len(sample_case.resolution.steps) == 3


def test_to_embedding_text(sample_case):
    """Test embedding text generation."""
    text = sample_case.to_embedding_text()
    assert "PLC" in text
    assert "Allen-Bradley" in text
    assert "motor won't start" in text
    assert "Thermal overload" in text


def test_to_few_shot_example(sample_case):
    """Test few-shot example formatting."""
    example = sample_case.to_few_shot_example()
    assert "SIMILAR CASE: TEST-001" in example
    assert "Technician reported:" in example
    assert "Root cause found:" in example
    assert "Resolution steps:" in example


def test_store_add_and_get(test_store, sample_case):
    """Test adding and retrieving a case."""
    case_id = test_store.add_case(sample_case)
    assert case_id == "TEST-001"

    retrieved = test_store.get_case("TEST-001")
    assert retrieved is not None
    assert retrieved.case_id == "TEST-001"
    assert retrieved.equipment.manufacturer == "Allen-Bradley"


def test_store_list_cases(test_store, sample_case):
    """Test listing all cases."""
    test_store.add_case(sample_case)

    cases = test_store.list_cases()
    assert len(cases) == 1
    assert cases[0].case_id == "TEST-001"


def test_store_count(test_store, sample_case):
    """Test case count."""
    assert test_store.count() == 0
    test_store.add_case(sample_case)
    assert test_store.count() == 1


def test_load_from_directory(test_store, tmp_path, sample_case):
    """Test loading cases from JSON files."""
    # Create temp directory with case file
    cases_dir = tmp_path / "cases"
    cases_dir.mkdir()

    case_file = cases_dir / "TEST-001.json"
    case_file.write_text(json.dumps(sample_case.model_dump(), default=str))

    # Load from directory
    loaded = test_store.load_from_directory(str(cases_dir))
    assert loaded == 1
    assert test_store.count() == 1


def test_schema_required_fields():
    """Test that required fields are enforced."""
    with pytest.raises(Exception):  # Pydantic ValidationError
        MaintenanceCase(
            case_id="FAIL-001",
            # Missing required fields
        )


def test_embedding_text_contains_all_relevant_info(sample_case):
    """Ensure embedding text has searchable content."""
    text = sample_case.to_embedding_text()

    # Should contain equipment info
    assert sample_case.equipment.type in text
    assert sample_case.equipment.manufacturer in text

    # Should contain problem description
    assert sample_case.input.raw_text in text

    # Should contain diagnosis
    assert sample_case.diagnosis.root_cause in text

    # Should contain keywords
    for keyword in sample_case.keywords:
        assert keyword in text

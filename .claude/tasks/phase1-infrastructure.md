# Phase 1: Example Store Infrastructure

**Status:** 📋 NOT STARTED
**Duration:** 2-4 hours
**Dependencies:** None (can start before Phase 0 complete)

---

## 📖 PRE-IMPLEMENTATION: Study These First

Before writing any code, read these references:

### GitHub Files to Study

1. **Embedding Functions Pattern**
   ```
   https://github.com/pixegami/rag-tutorial-v2/blob/main/get_embedding_function.py
   ```
   - Shows how to abstract embedding providers
   - Pattern for switching between Ollama/Bedrock/OpenAI

2. **Database Population Pattern**
   ```
   https://github.com/pixegami/rag-tutorial-v2/blob/main/populate_database.py
   ```
   - Document loading
   - Chunk creation
   - Vector store insertion

3. **LangChain RAG Fundamentals**
   ```
   https://github.com/langchain-ai/rag-from-scratch/blob/main/rag_from_scratch_1_to_4.ipynb
   ```
   - Indexing concepts
   - Embedding basics

### LangChain Docs to Read

1. **SemanticSimilarityExampleSelector**
   ```
   https://python.langchain.com/docs/how_to/example_selectors_similarity/
   ```

2. **Vector Stores Overview**
   ```
   https://python.langchain.com/docs/concepts/vectorstores/
   ```

---

## 🚫 CONSTRAINTS

```python
# ✅ ALLOWED
- Create new files in examples/ directory
- Create Pydantic schemas
- Create vector store wrapper (reuse existing infra)
- Create embedding pipeline
- Create unit tests
- Read existing code for understanding

# ❌ NOT ALLOWED
- Modify existing orchestrator code
- Connect to production database (use test/mock)
- Make external API calls in tests (mock them)
- Create new infrastructure (reuse existing Pinecone/Supabase)
```

---

## 📁 Files to Create

### 1. `examples/__init__.py`

```python
"""Few-shot RAG example system for RivetCEO Bot."""

from .schemas import MaintenanceCase, Equipment, CaseInput, Diagnosis, Resolution
from .store import CaseStore
from .embedder import CaseEmbedder
from .retriever import CaseRetriever
from .formatter import format_maintenance_examples

__all__ = [
    "MaintenanceCase",
    "Equipment", 
    "CaseInput",
    "Diagnosis",
    "Resolution",
    "CaseStore",
    "CaseEmbedder",
    "CaseRetriever",
    "format_maintenance_examples",
]
```

### 2. `examples/schemas.py`

```python
"""Pydantic schemas for maintenance case validation."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Equipment(BaseModel):
    """Equipment information for a maintenance case."""
    type: str = Field(..., description="Equipment type: PLC, VFD, motor, sensor, etc.")
    manufacturer: str = Field(..., description="Equipment manufacturer")
    model: str = Field(..., description="Model number or name")
    location: Optional[str] = Field(None, description="Physical location")


class CaseInput(BaseModel):
    """Raw input from technician."""
    raw_text: str = Field(..., description="Original technician input (messy/shorthand OK)")
    photo_url: Optional[str] = Field(None, description="Telegram photo ID if provided")


class Diagnosis(BaseModel):
    """Diagnostic findings."""
    root_cause: str = Field(..., description="Root cause of the issue")
    fault_codes: List[str] = Field(default_factory=list, description="Error/fault codes")
    symptoms: List[str] = Field(default_factory=list, description="Observable symptoms")


class Resolution(BaseModel):
    """How the issue was resolved."""
    steps: List[str] = Field(..., description="Steps taken to resolve")
    parts_used: List[str] = Field(default_factory=list, description="Parts replaced/used")
    time_to_fix: str = Field(..., description="Time to resolve (e.g., '45 minutes')")


class MaintenanceCase(BaseModel):
    """Complete maintenance case for few-shot learning."""
    case_id: str = Field(..., description="Unique case identifier (e.g., RC-001)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    equipment: Equipment
    input: CaseInput
    diagnosis: Diagnosis
    resolution: Resolution
    keywords: List[str] = Field(default_factory=list, description="Searchable keywords")
    category: str = Field(..., description="Category: electrical, mechanical, instrumentation, safety")
    
    def to_embedding_text(self) -> str:
        """Convert case to text suitable for embedding."""
        return f"""
Equipment: {self.equipment.type} - {self.equipment.manufacturer} {self.equipment.model}
Location: {self.equipment.location or 'Not specified'}
Problem: {self.input.raw_text}
Symptoms: {', '.join(self.diagnosis.symptoms)}
Fault Codes: {', '.join(self.diagnosis.fault_codes)}
Root Cause: {self.diagnosis.root_cause}
Keywords: {', '.join(self.keywords)}
Category: {self.category}
""".strip()
    
    def to_few_shot_example(self) -> str:
        """Format case as a few-shot example for prompt injection."""
        steps = '\n'.join(f"  {i+1}. {step}" for i, step in enumerate(self.resolution.steps))
        return f"""
---
SIMILAR CASE: {self.case_id}
Technician reported: "{self.input.raw_text}"
Equipment: {self.equipment.type} - {self.equipment.manufacturer} {self.equipment.model}
Root cause found: {self.diagnosis.root_cause}
Resolution steps:
{steps}
Time to fix: {self.resolution.time_to_fix}
---
""".strip()
```

### 3. `examples/store.py`

```python
"""Vector store wrapper for maintenance cases.

Reference: https://github.com/pixegami/rag-tutorial-v2/blob/main/populate_database.py
"""

import json
from pathlib import Path
from typing import List, Optional
from .schemas import MaintenanceCase

# TODO: Import your existing vector store client
# from your_existing_module import PineconeClient  # or SupabaseClient


class CaseStore:
    """
    Wrapper for storing and retrieving maintenance cases.
    
    Reuses existing RivetCEO vector store infrastructure.
    DO NOT create new infrastructure - use what exists.
    """
    
    def __init__(
        self,
        collection_name: str = "maintenance_cases",
        test_mode: bool = False
    ):
        self.collection_name = collection_name
        self.test_mode = test_mode
        self._cases: List[MaintenanceCase] = []  # In-memory for test mode
        
        if not test_mode:
            # TODO: Initialize your existing vector store client
            # self.client = PineconeClient() or SupabaseClient()
            raise NotImplementedError(
                "Production mode not implemented. "
                "Connect to existing Pinecone/Supabase vector store."
            )
    
    def add_case(self, case: MaintenanceCase) -> str:
        """Add a case to the store. Returns case_id."""
        if self.test_mode:
            self._cases.append(case)
            return case.case_id
        
        # TODO: Implement production storage
        # embedding = self.embedder.embed(case.to_embedding_text())
        # self.client.upsert(case.case_id, embedding, case.model_dump())
        raise NotImplementedError()
    
    def get_case(self, case_id: str) -> Optional[MaintenanceCase]:
        """Retrieve a case by ID."""
        if self.test_mode:
            for case in self._cases:
                if case.case_id == case_id:
                    return case
            return None
        
        # TODO: Implement production retrieval
        raise NotImplementedError()
    
    def list_cases(self) -> List[MaintenanceCase]:
        """List all cases."""
        if self.test_mode:
            return self._cases.copy()
        
        # TODO: Implement production listing
        raise NotImplementedError()
    
    def load_from_directory(self, cases_dir: str = "cases") -> int:
        """Load cases from JSON files in directory."""
        path = Path(cases_dir)
        if not path.exists():
            return 0
        
        loaded = 0
        for json_file in path.glob("*.json"):
            with open(json_file) as f:
                data = json.load(f)
                case = MaintenanceCase(**data)
                self.add_case(case)
                loaded += 1
        
        return loaded
    
    def count(self) -> int:
        """Return number of cases in store."""
        if self.test_mode:
            return len(self._cases)
        raise NotImplementedError()
```

### 4. `examples/embedder.py`

```python
"""Embedding pipeline for maintenance cases.

Reference: https://github.com/pixegami/rag-tutorial-v2/blob/main/get_embedding_function.py
"""

from typing import List

# TODO: Import your existing embedding function
# from your_existing_module import get_embeddings


class CaseEmbedder:
    """
    Embedder for maintenance cases.
    
    Reuses existing RivetCEO embedding infrastructure.
    DO NOT create new embedding setup - use what exists.
    """
    
    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        
        if not test_mode:
            # TODO: Initialize your existing embeddings
            # self.embeddings = get_embeddings()  # Gemini, OpenAI, etc.
            raise NotImplementedError(
                "Production mode not implemented. "
                "Connect to existing embedding service."
            )
    
    def embed(self, text: str) -> List[float]:
        """Embed a single text string."""
        if self.test_mode:
            # Return mock embedding for testing
            import hashlib
            hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
            # Create deterministic pseudo-embedding
            return [(hash_val >> i) % 100 / 100.0 for i in range(768)]
        
        # TODO: Use your existing embedding function
        # return self.embeddings.embed_query(text)
        raise NotImplementedError()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts."""
        return [self.embed(text) for text in texts]
```

### 5. `examples/tests/__init__.py`

```python
"""Tests for few-shot RAG example system."""
```

### 6. `examples/tests/test_store.py`

```python
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
```

### 7. `examples/tests/fixtures/sample_cases.json`

```json
[
  {
    "case_id": "SAMPLE-001",
    "timestamp": "2025-12-26T10:00:00Z",
    "equipment": {
      "type": "PLC",
      "manufacturer": "Allen-Bradley",
      "model": "ControlLogix 5580",
      "location": "Lift Hill"
    },
    "input": {
      "raw_text": "lift not moving fault light on",
      "photo_url": null
    },
    "diagnosis": {
      "root_cause": "E-stop chain broken",
      "fault_codes": ["E-STOP"],
      "symptoms": ["Lift motor not energizing"]
    },
    "resolution": {
      "steps": ["Checked E-stop chain", "Found broken contact", "Replaced switch"],
      "parts_used": ["E-stop switch"],
      "time_to_fix": "30 minutes"
    },
    "keywords": ["lift", "e-stop", "safety"],
    "category": "electrical"
  },
  {
    "case_id": "SAMPLE-002",
    "timestamp": "2025-12-26T11:00:00Z",
    "equipment": {
      "type": "VFD",
      "manufacturer": "ABB",
      "model": "ACS880",
      "location": "Brake Run"
    },
    "input": {
      "raw_text": "vfd showing fault 7121 motor not running",
      "photo_url": null
    },
    "diagnosis": {
      "root_cause": "DC bus overvoltage during decel",
      "fault_codes": ["7121", "OVERVOLT"],
      "symptoms": ["Drive tripped", "Motor coasting"]
    },
    "resolution": {
      "steps": ["Checked decel ramp", "Increased decel time", "Added braking resistor"],
      "parts_used": ["Braking resistor 100ohm"],
      "time_to_fix": "2 hours"
    },
    "keywords": ["vfd", "overvoltage", "braking", "abb"],
    "category": "electrical"
  }
]
```

---

## ✅ Acceptance Criteria

Before marking Phase 1 complete:

- [ ] `examples/__init__.py` - Module exports defined
- [ ] `examples/schemas.py` - All Pydantic models validate
- [ ] `examples/store.py` - Test mode works, production mode raises NotImplementedError
- [ ] `examples/embedder.py` - Test mode works with mock embeddings
- [ ] `examples/tests/test_store.py` - All tests pass
- [ ] `examples/tests/fixtures/sample_cases.json` - Sample data present

---

## 🧪 Test Commands

```bash
# Run all Phase 1 tests
cd examples && python -m pytest tests/test_store.py -v

# Expected output: All tests should pass
```

---

## 📝 Completion Checklist

When Phase 1 is complete, update PROJECT_TRACKER.md and respond:

```markdown
## Phase 1 Complete

**Deliverables:**
- [x] examples/__init__.py
- [x] examples/schemas.py
- [x] examples/store.py
- [x] examples/embedder.py
- [x] examples/tests/test_store.py
- [x] examples/tests/fixtures/sample_cases.json

**Test Results:**
[paste pytest output here]

**CHECKPOINT:** ⛔ Waiting for user validation before Phase 2.

Questions for user:
1. Should I connect to existing Pinecone or Supabase pgvector?
2. Which embedding model should I use (Gemini, OpenAI)?
```

---

## 🚨 STOP

Do NOT proceed to Phase 2 until user approves Phase 1.

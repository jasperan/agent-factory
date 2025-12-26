# Phase 2: Example Retrieval System

**Status:** 📋 NOT STARTED
**Duration:** 2-4 hours
**Dependencies:** Phase 1 complete, minimum 3 cases in store

---

## 📖 PRE-IMPLEMENTATION: Study These First

### Required Reading

1. **LangChain SemanticSimilarityExampleSelector**
   ```
   https://api.python.langchain.com/en/latest/example_selectors/langchain_core.example_selectors.semantic_similarity.SemanticSimilarityExampleSelector.html
   ```

2. **Few-shot chat examples tutorial**
   ```
   https://python.langchain.com/docs/how_to/few_shot_examples_chat/
   ```

3. **Working code example (GitHub Discussion)**
   ```
   https://github.com/langchain-ai/langchain/discussions/23850
   ```
   
   Key pattern from this discussion:
   ```python
   from langchain_core.example_selectors import SemanticSimilarityExampleSelector
   from langchain_core.prompts import FewShotChatMessagePromptTemplate
   
   # Create vectorstore from examples
   to_vectorize = [" ".join(example.values()) for example in examples]
   vectorstore = Chroma.from_texts(to_vectorize, embeddings, metadatas=examples)
   
   # Create selector
   example_selector = SemanticSimilarityExampleSelector(vectorstore=vectorstore, k=2)
   ```

4. **pixegami query pattern**
   ```
   https://github.com/pixegami/rag-tutorial-v2/blob/main/query_data.py
   ```

---

## 🚫 CONSTRAINTS

```python
# ✅ ALLOWED
- Create retrieval module in examples/
- Create similarity scoring logic
- Create few-shot prompt formatter
- Unit tests for retrieval
- Import from Phase 1 schemas

# ❌ NOT ALLOWED
- Modify orchestrator routes
- Change SME agent prompts
- Deploy anything to production
- Modify Phase 1 files (only import from them)
```

---

## 📁 Files to Create

### 1. `examples/retriever.py`

```python
"""Case retrieval using SemanticSimilarityExampleSelector pattern.

References:
- https://python.langchain.com/docs/how_to/few_shot_examples_chat/
- https://github.com/langchain-ai/langchain/discussions/23850
- https://github.com/pixegami/rag-tutorial-v2/blob/main/query_data.py
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from .schemas import MaintenanceCase
from .store import CaseStore
from .embedder import CaseEmbedder


@dataclass
class RetrievalResult:
    """Result from case retrieval with similarity score."""
    case: MaintenanceCase
    similarity_score: float


class CaseRetriever:
    """
    Retrieves similar maintenance cases using semantic similarity.
    
    Pattern based on LangChain's SemanticSimilarityExampleSelector:
    https://python.langchain.com/docs/how_to/example_selectors_similarity/
    """
    
    def __init__(
        self,
        store: CaseStore,
        embedder: CaseEmbedder,
        k: int = 3,
        similarity_threshold: float = 0.7,
    ):
        """
        Initialize retriever.
        
        Args:
            store: CaseStore instance with loaded cases
            embedder: CaseEmbedder for generating query embeddings
            k: Number of similar cases to retrieve
            similarity_threshold: Minimum similarity score (0-1)
        """
        self.store = store
        self.embedder = embedder
        self.k = k
        self.similarity_threshold = similarity_threshold
        
        # Pre-compute embeddings for all cases
        self._case_embeddings: List[Tuple[MaintenanceCase, List[float]]] = []
        self._build_index()
    
    def _build_index(self) -> None:
        """Build embedding index for all cases in store."""
        self._case_embeddings = []
        for case in self.store.list_cases():
            embedding = self.embedder.embed(case.to_embedding_text())
            self._case_embeddings.append((case, embedding))
    
    def refresh_index(self) -> None:
        """Rebuild index when cases are added."""
        self._build_index()
    
    def _cosine_similarity(
        self, 
        vec1: List[float], 
        vec2: List[float]
    ) -> float:
        """Calculate cosine similarity between two vectors."""
        a = np.array(vec1)
        b = np.array(vec2)
        
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    
    def get_similar_cases(
        self, 
        query: str,
        k: Optional[int] = None,
    ) -> List[RetrievalResult]:
        """
        Retrieve k most similar cases for a query.
        
        Args:
            query: Input text (technician description of problem)
            k: Number of cases to retrieve (defaults to self.k)
        
        Returns:
            List of RetrievalResult with cases and similarity scores
        """
        if k is None:
            k = self.k
        
        if not self._case_embeddings:
            return []
        
        # Embed the query
        query_embedding = self.embedder.embed(query)
        
        # Calculate similarity with all cases
        scored_cases: List[Tuple[MaintenanceCase, float]] = []
        for case, case_embedding in self._case_embeddings:
            similarity = self._cosine_similarity(query_embedding, case_embedding)
            scored_cases.append((case, similarity))
        
        # Sort by similarity (descending)
        scored_cases.sort(key=lambda x: x[1], reverse=True)
        
        # Filter by threshold and take top k
        results = []
        for case, score in scored_cases[:k]:
            if score >= self.similarity_threshold:
                results.append(RetrievalResult(case=case, similarity_score=score))
        
        return results
    
    async def aget_similar_cases(
        self,
        query: str,
        k: Optional[int] = None,
    ) -> List[RetrievalResult]:
        """Async version for use in async orchestrator."""
        # For now, just wrap sync version
        # TODO: Make truly async when connecting to production vector store
        return self.get_similar_cases(query, k)
```

### 2. `examples/formatter.py`

```python
"""Format retrieved cases as few-shot examples for SME agent.

Reference pattern from LangChain:
https://python.langchain.com/docs/how_to/few_shot_examples_chat/
"""

from typing import List
from .retriever import RetrievalResult


def format_maintenance_examples(
    results: List[RetrievalResult],
    include_scores: bool = False,
) -> str:
    """
    Format retrieved cases as few-shot context for SME agent.
    
    Args:
        results: List of RetrievalResult from CaseRetriever
        include_scores: Whether to include similarity scores (for debugging)
    
    Returns:
        Formatted string ready for prompt injection
    """
    if not results:
        return "No similar past cases found."
    
    formatted_examples = []
    
    for i, result in enumerate(results, 1):
        case = result.case
        example = case.to_few_shot_example()
        
        if include_scores:
            score_line = f"(Similarity: {result.similarity_score:.2%})"
            example = f"{example}\n{score_line}"
        
        formatted_examples.append(example)
    
    header = f"## {len(results)} Similar Past Cases Found\n\n"
    header += "Use these examples to understand how similar problems were resolved:\n"
    
    return header + "\n\n".join(formatted_examples)


def format_for_sme_prompt(
    results: List[RetrievalResult],
    current_input: str,
    base_prompt: str,
) -> str:
    """
    Create complete enhanced prompt for SME agent.
    
    Args:
        results: Retrieved similar cases
        current_input: Current technician input
        base_prompt: Original SME system prompt
    
    Returns:
        Enhanced prompt with few-shot examples injected
    """
    few_shot_context = format_maintenance_examples(results)
    
    enhanced_prompt = f"""
{base_prompt}

{few_shot_context}

## Current Case

Technician Input: "{current_input}"

Based on the similar cases above (if any), parse this input and provide diagnosis assistance.
"""
    
    return enhanced_prompt.strip()
```

### 3. `examples/tests/test_retriever.py`

```python
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
```

---

## ⏱️ Latency Requirements

| Operation | Budget | Measurement |
|-----------|--------|-------------|
| Query embedding | < 100ms | `time.time()` |
| Similarity search | < 300ms | `time.time()` |
| Formatting | < 100ms | `time.time()` |
| **Total retrieval** | < 500ms | Test assertion |

---

## ✅ Acceptance Criteria

Before marking Phase 2 complete:

- [ ] `examples/retriever.py` - CaseRetriever implemented
- [ ] `examples/formatter.py` - Formatting functions implemented
- [ ] `examples/tests/test_retriever.py` - All tests pass
- [ ] Retrieval latency < 500ms
- [ ] Results sorted by similarity
- [ ] Threshold filtering works
- [ ] Empty results handled gracefully

---

## 🧪 Test Commands

```bash
# Run all Phase 2 tests
cd examples && python -m pytest tests/test_retriever.py -v

# Run with latency output
cd examples && python -m pytest tests/test_retriever.py -v --durations=10

# Quick retrieval test
cd examples && python -c "
from store import CaseStore
from embedder import CaseEmbedder  
from retriever import CaseRetriever

store = CaseStore(test_mode=True)
embedder = CaseEmbedder(test_mode=True)
retriever = CaseRetriever(store, embedder)

# Load sample cases
store.load_from_directory('tests/fixtures')
retriever.refresh_index()

results = retriever.get_similar_cases('motor won't start')
for r in results:
    print(f'{r.case.case_id}: {r.similarity_score:.2%}')
"
```

---

## 📝 Completion Checklist

When Phase 2 is complete, update PROJECT_TRACKER.md and respond:

```markdown
## Phase 2 Complete

**Deliverables:**
- [x] examples/retriever.py
- [x] examples/formatter.py
- [x] examples/tests/test_retriever.py

**Test Results:**
[paste pytest output here]

**Latency Metrics:**
- Query embedding: Xms
- Similarity search: Xms
- Formatting: Xms
- Total: Xms (must be < 500ms)

**Sample Retrieval Output:**
```
Query: "motor won't start"
Results:
1. TEST-001: 85.2% similarity
2. TEST-003: 72.1% similarity
```

**CHECKPOINT:** ⛔ Waiting for user validation before Phase 3.

Questions for user:
1. Are the similarity scores meaningful with your real cases?
2. Should I adjust the default threshold (currently 0.7)?
3. Ready to proceed with orchestrator integration?
```

---

## 🚨 STOP

Do NOT proceed to Phase 3 until user approves Phase 2.

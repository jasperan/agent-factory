# Phase 3: Orchestrator Integration

**Status:** 📋 NOT STARTED
**Duration:** 3-5 hours
**Dependencies:** Phase 2 complete, retrieval quality validated by user

---

## ⚠️ RESTRICTED PHASE

This phase modifies production code. **EVERY CHANGE requires user approval.**

---

## 📖 PRE-IMPLEMENTATION: Study These First

### Required Reading

1. **LangChain FewShotChatMessagePromptTemplate**
   ```
   https://python.langchain.com/docs/how_to/few_shot_examples_chat/
   ```

2. **pixegami query pattern**
   ```
   https://github.com/pixegami/rag-tutorial-v2/blob/main/query_data.py
   ```

3. **Your existing orchestrator code** (read before modifying!)
   - Find the Route C SME handler
   - Understand current prompt structure
   - Identify injection point

---

## 🚫 CONSTRAINTS

```python
# ✅ ALLOWED
- Modify SME agent prompt templates ONLY
- Add retrieval call before SME invocation
- Add LangSmith tracing for retrieval
- Add try/except for graceful degradation

# ⚠️ REQUIRES EXPLICIT USER APPROVAL (ask before each change)
- Any change to orchestrator routing logic
- Any change to existing route handlers
- Any modification to Telegram handlers
- Any database writes

# ❌ NOT ALLOWED (never do these)
- Remove or disable existing functionality
- Change database schemas
- Modify authentication/security code
- Deploy without user testing first
```

---

## 🎯 Integration Pattern

### Before (Current Flow)

```python
async def route_c_sme_handler(input_data):
    prompt = SME_SYSTEM_PROMPT
    response = await call_sme_agent(prompt, input_data)
    return response
```

### After (With Few-Shot Enhancement)

```python
from examples import CaseStore, CaseEmbedder, CaseRetriever, format_for_sme_prompt
from langsmith import trace

# Initialize at module level (once)
_case_store = CaseStore(test_mode=False)  # Connect to production
_case_embedder = CaseEmbedder(test_mode=False)
_case_retriever = CaseRetriever(_case_store, _case_embedder, k=3)


@trace(name="sme_handler_with_fewshot")
async def route_c_sme_handler(input_data):
    # Step 1: Retrieve similar cases
    try:
        with trace(name="fewshot_retrieval") as span:
            similar_cases = await _case_retriever.aget_similar_cases(input_data.text)
            span.add_metadata({
                "cases_found": len(similar_cases),
                "avg_similarity": sum(r.similarity_score for r in similar_cases) / len(similar_cases) if similar_cases else 0,
            })
    except Exception as e:
        # Graceful degradation: continue without few-shot if retrieval fails
        logger.warning(f"Few-shot retrieval failed: {e}")
        similar_cases = []
    
    # Step 2: Build enhanced prompt
    if similar_cases:
        enhanced_prompt = format_for_sme_prompt(
            results=similar_cases,
            current_input=input_data.text,
            base_prompt=SME_SYSTEM_PROMPT,
        )
    else:
        enhanced_prompt = SME_SYSTEM_PROMPT
    
    # Step 3: Call SME agent (existing logic)
    response = await call_sme_agent(enhanced_prompt, input_data)
    return response
```

---

## ⏱️ Latency Budget

| Component | Current | Additional | Target |
|-----------|---------|------------|--------|
| Orchestrator routing | ~36s | 0s | 36s |
| Few-shot retrieval | N/A | < 2s | < 2s |
| **Total** | ~36s | < 2s | < 38s |

**Hard limit:** If retrieval adds > 2 seconds, it MUST be disabled.

---

## 📊 LangSmith Traces to Add

Add these traces to monitor few-shot performance:

```python
# Trace keys to add
fewshot.retrieval.latency_ms    # Retrieval time in milliseconds
fewshot.cases_found             # Number of similar cases found
fewshot.avg_similarity_score    # Average similarity score
fewshot.threshold_used          # Similarity threshold
fewshot.fallback_triggered      # True if retrieval failed
```

---

## 📁 Files to Modify

### 1. Locate Existing SME Handler

First, find where the SME handler is defined:

```bash
# Search for SME handler
grep -r "route_c" --include="*.py" .
grep -r "sme_handler" --include="*.py" .
grep -r "SME_SYSTEM_PROMPT" --include="*.py" .
```

**ASK USER:** Which file contains the Route C SME handler?

### 2. Create Integration Module

**NEW FILE:** `examples/integration.py`

```python
"""Integration layer for few-shot RAG with orchestrator.

This module provides the connection between the few-shot retrieval
system and the existing RivetCEO orchestrator.
"""

import logging
from typing import Optional, List
from dataclasses import dataclass

from .store import CaseStore
from .embedder import CaseEmbedder
from .retriever import CaseRetriever, RetrievalResult
from .formatter import format_for_sme_prompt

logger = logging.getLogger(__name__)


@dataclass
class FewShotConfig:
    """Configuration for few-shot retrieval."""
    enabled: bool = True
    k: int = 3
    similarity_threshold: float = 0.7
    timeout_seconds: float = 2.0
    fallback_on_error: bool = True


class FewShotEnhancer:
    """
    Enhances SME prompts with few-shot examples.
    
    Thread-safe, singleton-friendly design for use in async orchestrator.
    """
    
    _instance: Optional['FewShotEnhancer'] = None
    
    def __init__(self, config: FewShotConfig = None):
        self.config = config or FewShotConfig()
        self._retriever: Optional[CaseRetriever] = None
        self._initialized = False
    
    @classmethod
    def get_instance(cls, config: FewShotConfig = None) -> 'FewShotEnhancer':
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance
    
    def initialize(
        self,
        store: CaseStore,
        embedder: CaseEmbedder,
    ) -> None:
        """Initialize with store and embedder."""
        self._retriever = CaseRetriever(
            store=store,
            embedder=embedder,
            k=self.config.k,
            similarity_threshold=self.config.similarity_threshold,
        )
        self._initialized = True
        logger.info(
            f"FewShotEnhancer initialized: k={self.config.k}, "
            f"threshold={self.config.similarity_threshold}"
        )
    
    async def enhance_prompt(
        self,
        base_prompt: str,
        user_input: str,
    ) -> tuple[str, List[RetrievalResult]]:
        """
        Enhance prompt with few-shot examples.
        
        Args:
            base_prompt: Original system prompt
            user_input: User's input text
        
        Returns:
            Tuple of (enhanced_prompt, retrieved_cases)
        """
        if not self.config.enabled:
            return base_prompt, []
        
        if not self._initialized or self._retriever is None:
            logger.warning("FewShotEnhancer not initialized, skipping")
            return base_prompt, []
        
        try:
            import asyncio
            
            # Retrieve with timeout
            results = await asyncio.wait_for(
                self._retriever.aget_similar_cases(user_input),
                timeout=self.config.timeout_seconds,
            )
            
            if results:
                enhanced = format_for_sme_prompt(
                    results=results,
                    current_input=user_input,
                    base_prompt=base_prompt,
                )
                return enhanced, results
            
            return base_prompt, []
            
        except asyncio.TimeoutError:
            logger.warning(
                f"Few-shot retrieval timed out after {self.config.timeout_seconds}s"
            )
            if self.config.fallback_on_error:
                return base_prompt, []
            raise
        
        except Exception as e:
            logger.error(f"Few-shot retrieval error: {e}")
            if self.config.fallback_on_error:
                return base_prompt, []
            raise
```

### 3. Add to `examples/__init__.py`

```python
# Add to existing exports
from .integration import FewShotEnhancer, FewShotConfig
```

---

## 🧪 Integration Test

Create `examples/tests/test_integration.py`:

```python
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
    store.load_from_directory("tests/fixtures")
    
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
```

---

## 📝 Step-by-Step Implementation

### Step 1: Get User Approval

Before ANY code changes, ask:

```markdown
I'm ready to integrate few-shot retrieval into the orchestrator.

**Files I need to modify:**
1. [specific file path] - Add FewShotEnhancer import and initialization
2. [specific file path] - Modify route_c_sme_handler

**Changes I'll make:**
1. Add try/except wrapped retrieval before SME call
2. Inject few-shot examples into prompt
3. Add LangSmith tracing

**Safeguards:**
- Graceful degradation if retrieval fails
- Timeout after 2 seconds
- Feature flag to disable

Do I have approval to proceed?
```

### Step 2: Implement (After Approval)

1. Create `examples/integration.py`
2. Update `examples/__init__.py`
3. Modify orchestrator file (per user guidance)
4. Add LangSmith traces
5. Run integration tests

### Step 3: Manual Testing

```bash
# Test in isolation first
python -c "
import asyncio
from examples.integration import FewShotEnhancer, FewShotConfig
from examples.store import CaseStore
from examples.embedder import CaseEmbedder

async def test():
    config = FewShotConfig()
    enhancer = FewShotEnhancer(config)
    
    store = CaseStore(test_mode=True)
    embedder = CaseEmbedder(test_mode=True)
    store.load_from_directory('cases')
    
    enhancer.initialize(store, embedder)
    
    enhanced, results = await enhancer.enhance_prompt(
        'Base prompt',
        'motor won't start'
    )
    
    print('Enhanced prompt:')
    print(enhanced[:500])
    print(f'Found {len(results)} similar cases')

asyncio.run(test())
"
```

---

## ✅ Acceptance Criteria

Before marking Phase 3 complete:

- [ ] `examples/integration.py` created
- [ ] FewShotEnhancer works in test mode
- [ ] Orchestrator modification approved by user
- [ ] Graceful degradation tested (disable retrieval, verify no errors)
- [ ] Latency increase < 2 seconds
- [ ] LangSmith traces visible
- [ ] No regression in existing functionality (test Route C without few-shot)
- [ ] Feature flag works (can disable few-shot)

---

## 📝 Completion Checklist

When Phase 3 is complete, update PROJECT_TRACKER.md and respond:

```markdown
## Phase 3 Complete

**Deliverables:**
- [x] examples/integration.py
- [x] examples/tests/test_integration.py
- [x] Orchestrator modification (file: _____)

**Test Results:**
[paste test output]

**Latency Metrics:**
- Baseline (no few-shot): Xs
- With few-shot: Xs
- Overhead: Xs (must be < 2s)

**LangSmith Screenshot:**
[describe traces visible]

**CHECKPOINT:** ⛔ Waiting for user to test in staging before Phase 4.

Suggested testing:
1. Send test message via Telegram
2. Verify few-shot examples appear in SME response
3. Check LangSmith for retrieval traces
4. Test with few-shot disabled (feature flag)
```

---

## 🚨 STOP

Do NOT proceed to Phase 4 until user validates Phase 3 in staging.

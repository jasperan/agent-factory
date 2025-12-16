# RIVET Pro - Phase 1: Data Models

**Status:** ✅ COMPLETE
**Duration:** 30 minutes
**Dependencies:** None
**Worktree:** `agent-factory-rivet-models`
**Branch:** `feature/rivet-models`

---

## What Was Built

Complete Pydantic data models for the RIVET Pro multi-agent backend. These models provide type-safe, validated data structures used by all downstream components.

### Files Created

```
agent_factory/rivet_pro/
├── models.py (450 lines)
│   ├── 8 Enums (ChannelType, MessageType, VendorType, etc.)
│   ├── RivetRequest - Unified request from any channel
│   ├── RivetIntent - Classified user intent
│   ├── RivetResponse - Agent response to user
│   ├── AgentTrace - Logging/analytics metadata
│   └── Helper functions (create_text_request, create_image_request)

tests/rivet_pro/
├── __init__.py
└── test_models.py (450 lines)
    └── 20+ comprehensive tests

test_models_simple.py (root - validation script)
README_PHASE1.md (this file)
```

---

## Models Overview

### 1. RivetRequest
**Purpose:** Unified representation of user messages from any channel (Telegram, WhatsApp, Slack, API)

**Key Fields:**
- `user_id` - Unique identifier (channel-prefixed)
- `channel` - Communication channel (telegram, whatsapp, slack)
- `message_type` - Type of message (text, image, audio)
- `text` - Message text or caption
- `image_path` - Local path to downloaded image
- `metadata` - Additional context (timestamp, language, etc.)

**Example:**
```python
from agent_factory.rivet_pro.models import create_text_request

request = create_text_request(
    user_id="telegram_12345",
    text="My Siemens G120C shows fault F3002"
)
```

### 2. RivetIntent
**Purpose:** Structured classification of user intent (output of intent classifier, input to routing)

**Key Fields:**
- `vendor` - Equipment manufacturer (Siemens, Rockwell, ABB, etc.)
- `equipment_type` - Equipment category (VFD, PLC, HMI, etc.)
- `application` - Use case (crane, conveyor, pump, etc.)
- `symptom` - Fault description
- `context_source` - Where intent came from (text, OCR, vision)
- `confidence` - Classification confidence (0.0-1.0)
- `kb_coverage` - Knowledge base coverage ("strong", "thin", "none")
- `raw_summary` - Normalized description for RAG queries

**Example:**
```python
from agent_factory.rivet_pro.models import RivetIntent, VendorType, EquipmentType

intent = RivetIntent(
    vendor=VendorType.SIEMENS,
    equipment_type=EquipmentType.VFD,
    context_source="text_only",
    confidence=0.92,
    kb_coverage="strong",
    raw_summary="Siemens G120C VFD F3002 overvoltage",
    detected_fault_codes=["F3002"]
)
```

### 3. RivetResponse
**Purpose:** Agent's answer to send back to user

**Key Fields:**
- `text` - Answer text
- `agent_id` - Which SME agent generated this
- `route_taken` - Which orchestrator route was used (A/B/C/D)
- `links` - Manual/documentation URLs
- `confidence` - Answer confidence
- `suggested_actions` - Step-by-step instructions
- `safety_warnings` - Safety reminders
- `cited_documents` - Source citations

**Example:**
```python
from agent_factory.rivet_pro.models import RivetResponse, AgentID, RouteType

response = RivetResponse(
    text="F3002 is DC bus overvoltage. Check input voltage...",
    agent_id=AgentID.SIEMENS,
    route_taken=RouteType.ROUTE_A,
    links=["https://support.siemens.com/manual/G120C"],
    suggested_actions=["Check voltage", "Verify parameters"]
)
```

### 4. AgentTrace
**Purpose:** Complete trace for conversation logging and analytics

**Key Fields:**
- `request_id` - Unique trace ID
- `intent` - Full RivetIntent
- `route` - Route taken
- `agent_id` - Agent used
- `docs_retrieved` - RAG doc count
- `processing_time_ms` - Performance metric
- `timestamp` - UTC timestamp

---

## Validation

### Quick Validation
```bash
# Import test
poetry run python -c "from agent_factory.rivet_pro.models import RivetRequest, RivetIntent, RivetResponse; print('OK')"

# Full validation
poetry run python test_models_simple.py
```

### Expected Output
```
[OK] All imports successful
Test 1: Creating text request... [PASS]
Test 2: Creating image request... [PASS]
Test 3: Creating intent... [PASS]
Test 4: Creating response... [PASS]
Test 5: Creating agent trace... [PASS]
Test 6: Testing validation... [PASS]
============================================================
ALL TESTS PASSED - Phase 1 models validated successfully!
============================================================
```

---

## Integration Points

### Phase 2 (RAG Layer)
```python
from agent_factory.rivet_pro.models import RivetIntent, KBCoverage

def estimate_coverage(intent: RivetIntent) -> KBCoverage:
    """Uses intent.vendor, intent.equipment_type to search KB"""
    pass
```

### Phase 3 (SME Agents)
```python
from agent_factory.rivet_pro.models import RivetRequest, RivetIntent, RivetResponse

def handle(request: RivetRequest, intent: RivetIntent) -> RivetResponse:
    """All agents use these models"""
    pass
```

### Phase 4 (Orchestrator)
```python
from agent_factory.rivet_pro.models import RivetRequest, RouteType

def route_request(request: RivetRequest) -> RivetResponse:
    """Orchestrator routes based on kb_coverage"""
    if intent.kb_coverage == "strong":
        return self._route_to_sme(request, intent, enrichment=False)
```

### Phase 6 (Logging)
```python
from agent_factory.rivet_pro.models import AgentTrace

def log_conversation(trace: AgentTrace):
    """Stores full trace to database"""
    pass
```

---

## Key Design Decisions

### 1. **Enum-Based Types**
- Uses Python Enums for vendor, equipment, routes
- Provides IDE autocomplete and type safety
- Easy to extend (add new vendors/equipment types)

### 2. **Pydantic Validation**
- All models validated at runtime
- Confidence must be 0.0-1.0
- Either text or image_path required
- Prevents invalid data from propagating

### 3. **Channel-Agnostic**
- Same models work for Telegram, WhatsApp, Slack, API
- Channel-specific webhooks normalize to RivetRequest
- Responses work across all channels

### 4. **Separation of Concerns**
- Request (what user sent)
- Intent (what we understood)
- Response (what we answered)
- Trace (what happened)

### 5. **Helper Functions**
- `create_text_request()` - Quick text message creation
- `create_image_request()` - Quick image message creation
- Reduces boilerplate in chat handlers

---

## Next Steps

### Phase 2: RAG Layer (45 min)
**Dependencies:** Phase 1 complete ✅

Build RAG retriever that uses `RivetIntent` to:
1. Search knowledge base with filters (vendor, equipment_type)
2. Estimate coverage ("strong", "thin", "none")
3. Return relevant docs for SME agents

### Phase 3: SME Agents (2 hours - PARALLEL!)
**Dependencies:** Phase 1, 2 complete

Build 4 SME agents that:
1. Accept `RivetRequest` and `RivetIntent`
2. Call RAG retriever
3. Generate answers
4. Return `RivetResponse`

Can be developed in parallel (4 separate tabs/worktrees)!

---

## Troubleshooting

### Import Errors
```bash
# If you get "No module named 'agent_factory'"
poetry install  # Reinstall package in dev mode
```

### Validation Errors
```python
# Check what failed
try:
    intent = RivetIntent(...)
except ValidationError as e:
    print(e.json())  # Shows detailed validation errors
```

---

## Success Metrics

- ✅ All 6 validation tests pass
- ✅ Models can be imported from other phases
- ✅ Zero changes to existing files
- ✅ Type-safe with IDE autocomplete
- ✅ Runtime validation catches errors

---

**Phase 1 Status:** ✅ **COMPLETE** - Ready for Phase 2!

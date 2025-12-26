# Phase 4: Feedback Loop (Auto-Learning)

**Duration:** 4-6 hours
**Dependencies:** Phase 3 deployed and stable
**Spec Reference:** `DYNAMIC_FEWSHOT_RAG_SPEC.md` Phase 4 section

---

## ⚠️ CLAUDE CODE CONSTRAINTS

```
ALLOWED:
- Add Telegram message handlers for resolution detection
- Create case parsing logic from conversational input
- Add embedding pipeline for new cases
- Create follow-up question templates
- Unit tests for feedback loop

REQUIRES USER APPROVAL:
- Any changes to existing Telegram handlers
- Database schema modifications
- Changes to message routing logic

NOT ALLOWED:
- Disable existing functionality
- Modify authentication code
- Change production credentials
```

---

## 📖 BEFORE STARTING - STUDY THESE

### LangChain Conversation Memory
```
https://python.langchain.com/docs/how_to/chatbots_memory/
```

### pixegami conversation patterns
```
https://github.com/pixegami/rag-tutorial-v2/blob/main/query_data.py
```

### LangSmith feedback integration
```
https://docs.smith.langchain.com/how_to_guides/evaluation/capture_feedback
```

---

## 🎯 OBJECTIVE

Build automatic case capture when technician resolves an issue:

```
User: "✅ Fixed it" or "Resolved" or "Problem solved"
         │
         ▼
Bot: "Great! Quick follow-up to help future cases:
      1. What was the root cause?
      2. What steps fixed it?
      3. How long did it take?"
         │
         ▼
User: "Bad relay in safety circuit, replaced it, 30 mins"
         │
         ▼
[Parse into structured Case JSON]
         │
         ▼
[Embed and store in vector DB]
         │
         ▼
[Available for future few-shot retrieval]
```

---

## 📋 TASKS

### Task 4.1: Resolution Detection
**File:** `examples/feedback/detector.py`

```python
"""
Create resolution detection patterns.

STUDY FIRST:
- Telegram bot update handlers
- Your existing Telegram handler patterns in orchestrator

DETECTION PATTERNS:
- Explicit: "fixed", "resolved", "solved", "working now"
- Emoji: "✅", "👍", "🎉" in context
- Gratitude: "thanks, that worked", "you were right"

RETURN:
{
    "is_resolution": bool,
    "confidence": float,  # 0.0-1.0
    "trigger_phrase": str
}
"""
```

**Test:**
```bash
python -m pytest tests/test_detector.py -v
```

### Task 4.2: Follow-up Questionnaire
**File:** `examples/feedback/questionnaire.py`

```python
"""
Create conversational follow-up to extract case details.

QUESTIONS (ask one at a time, not all at once):
1. "What ended up being the root cause?"
2. "What steps did you take to fix it?"  
3. "About how long did the fix take?"
4. "Any parts you replaced?" (optional)

PARSING:
- Handle messy natural language input
- Extract structured data from conversational responses
- Use Claude/Groq to parse if needed

OUTPUT: Partial Case schema object
"""
```

### Task 4.3: Case Assembler
**File:** `examples/feedback/assembler.py`

```python
"""
Assemble complete case from conversation context.

INPUT:
- Original problem description (from conversation start)
- Equipment identified (from OCR/analysis)
- Follow-up answers
- Resolution timestamp

OUTPUT:
- Complete Case schema object
- Ready for embedding

VALIDATION:
- Must have root_cause
- Must have at least one resolution step
- Equipment should match original context
"""
```

### Task 4.4: Embedding Pipeline Hook
**File:** `examples/feedback/ingestor.py`

```python
"""
Ingest resolved case into vector store.

REUSE:
- Same embedding model as Phase 1
- Same vector store connection as Phase 1

NEW:
- Add "source": "auto-capture" metadata
- Add "confidence": float for retrieval weighting
- Log to LangSmith for monitoring

IDEMPOTENCY:
- Generate deterministic case_id from content hash
- Prevent duplicate ingestion
"""
```

### Task 4.5: Integration Hook
**File:** `examples/feedback/__init__.py`

```python
"""
Export clean interface for orchestrator integration.

INTERFACE:
async def check_resolution(message: str) -> ResolutionDetection
async def start_feedback_flow(chat_id: str, context: ConversationContext) -> None
async def process_feedback_response(chat_id: str, response: str) -> FeedbackState
async def finalize_case(chat_id: str) -> Case

STATE MANAGEMENT:
- Track which users are in feedback flow
- Handle conversation interruption gracefully
- Timeout after 10 minutes of inactivity
"""
```

---

## 🧪 TEST FIXTURES

Create `tests/fixtures/feedback_conversations.json`:
```json
[
  {
    "conversation_id": "test-001",
    "messages": [
      {"role": "user", "text": "lift motor won't start"},
      {"role": "assistant", "text": "Based on the symptoms..."},
      {"role": "user", "text": "fixed it! thanks"},
      {"role": "assistant", "text": "Great! What was the root cause?"},
      {"role": "user", "text": "bad contactor, replaced it"},
      {"role": "assistant", "text": "How long did it take?"},
      {"role": "user", "text": "about 45 mins"}
    ],
    "expected_case": {
      "root_cause": "bad contactor",
      "resolution_steps": ["replaced contactor"],
      "time_to_fix": "45 minutes"
    }
  }
]
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Resolution detection accuracy > 90% on test fixtures
- [ ] Follow-up questions are asked naturally (not robotic)
- [ ] Messy input is parsed into structured case
- [ ] Case is embedded and stored in vector DB
- [ ] New case appears in Phase 2 retrieval results
- [ ] LangSmith shows feedback loop traces
- [ ] Graceful handling of user abandonment
- [ ] No regression in existing Telegram functionality

---

## 🛑 CHECKPOINT

**STOP** after completing all tasks.

**User Validation Required:**
1. Test resolution detection with 5 real messages
2. Complete one full feedback flow manually
3. Verify case appears in retrieval
4. Check LangSmith traces

**Only proceed to Phase 5 after user confirms feedback loop is working.**

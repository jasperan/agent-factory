# WORKSTREAM 5: INTENT PARSER + CLARIFICATION
# Computer 2, Tab 2
# Copy everything below this line into Claude Code CLI

You are WS-5 (Intent Parser) in a 6-instance parallel development sprint for Rivet MVP.

## AUTONOMOUS MODE SETTINGS
- Auto-accept all file edits
- Auto-accept bash commands except: rm -rf, sudo, DROP, DELETE
- Commit after each completed task
- If context feels long (5+ tasks done), checkpoint immediately

## YOUR IDENTITY
- Workstream: WS-5
- Branch: intent-parser
- Focus: LLM intent parsing with clarification flow

## FIRST ACTIONS (Do These Now)
1. Check if worktree exists: `git worktree list`
2. If not, create it: `git worktree add ../rivet-intent intent-parser`
3. cd into worktree
4. Read this entire prompt before starting

## CRITICAL: INTENT DETECTION ALREADY EXISTS!
Look at these files:
```
/agent_factory/rivet_pro/intent_detector.py       # FULL IMPLEMENTATION
/agent_factory/integrations/telegram/intent_detector.py  # Telegram-specific
```

The existing IntentDetector does:
- Intent classification (troubleshooting, information, booking, account)
- Equipment extraction (type, manufacturer, model, fault codes)
- Urgency scoring (1-10)
- Multi-modal support

You are ENHANCING it with:
1. Clarification flow when intent is ambiguous
2. Better handling of off-topic/weird input
3. Multi-turn clarification conversation
4. Confidence thresholds and fallbacks

## YOUR TASKS (In Order)

### Task 1: Study Existing Intent Detector
```bash
cat /agent_factory/rivet_pro/intent_detector.py
cat /agent_factory/integrations/telegram/intent_detector.py
```

Note the existing:
- IntentType enum
- EquipmentInfo dataclass
- IntentResult structure
- Detection logic

### Task 2: Add Clarification Data Models
Add to `/agent_factory/rivet_pro/models.py` or create `/agent_factory/rivet_pro/clarification.py`:
```python
"""Clarification flow models for ambiguous intents."""
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum

class ClarificationType(Enum):
    """Types of clarification needed."""
    EQUIPMENT_AMBIGUOUS = "equipment_ambiguous"    # "Which pump?"
    INTENT_UNCLEAR = "intent_unclear"              # "What do you need help with?"
    MISSING_DETAILS = "missing_details"            # "What's the issue?"
    OFF_TOPIC = "off_topic"                        # "I help with maintenance..."
    CONFIRMATION = "confirmation"                   # "Create WO for Pump-001?"

@dataclass
class ClarificationRequest:
    """Request for clarification from user."""
    type: ClarificationType
    prompt: str                                    # What to ask user
    options: List[str] = field(default_factory=list)  # Suggested options
    context: dict = field(default_factory=dict)    # Preserved context
    
@dataclass  
class ParsedIntent:
    """Enhanced intent result with clarification support."""
    intent_type: str                              # create_work_order, query_asset, etc.
    confidence: float                             # 0.0 to 1.0
    
    # Equipment info
    equipment_id: Optional[str] = None
    equipment_name: Optional[str] = None
    equipment_candidates: List[dict] = field(default_factory=list)
    
    # Issue info
    issue_description: Optional[str] = None
    priority: Optional[str] = None
    urgency_score: int = 5
    
    # Clarification
    needs_clarification: bool = False
    clarification: Optional[ClarificationRequest] = None
    
    # For schematic questions
    question: Optional[str] = None
    
    # Raw
    raw_input: str = ""
```

### Task 3: Implement Clarification Logic
Create: `/agent_factory/rivet_pro/clarifier.py`:
```python
"""Clarification flow handler."""
from typing import Optional
from langchain_anthropic import ChatAnthropic
from .clarification import ClarificationType, ClarificationRequest, ParsedIntent

class IntentClarifier:
    """Generate clarification prompts for ambiguous inputs."""
    
    CONFIDENCE_THRESHOLD = 0.7  # Below this, ask for clarification
    
    def __init__(self):
        self.llm = ChatAnthropic(model="claude-sonnet-4-20250514")
    
    def needs_clarification(self, intent: ParsedIntent) -> bool:
        """Check if intent needs clarification."""
        if intent.confidence < self.CONFIDENCE_THRESHOLD:
            return True
        if intent.intent_type == "unclear":
            return True
        if intent.equipment_candidates and len(intent.equipment_candidates) > 1:
            return True
        if intent.intent_type == "create_work_order" and not intent.issue_description:
            return True
        return False
    
    def generate_clarification(self, intent: ParsedIntent) -> ClarificationRequest:
        """Generate appropriate clarification request."""
        
        # Multiple equipment matches
        if len(intent.equipment_candidates) > 1:
            options = [c["name"] for c in intent.equipment_candidates[:5]]
            return ClarificationRequest(
                type=ClarificationType.EQUIPMENT_AMBIGUOUS,
                prompt=f"I found multiple equipment matches. Which one?\n\n" + 
                       "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(options)),
                options=options,
                context={"candidates": intent.equipment_candidates}
            )
        
        # No equipment identified for work order
        if intent.intent_type == "create_work_order" and not intent.equipment_id:
            return ClarificationRequest(
                type=ClarificationType.MISSING_DETAILS,
                prompt="Which equipment is this for? You can say the name, ID, or location.",
                options=[],
                context={"partial_intent": intent.intent_type}
            )
        
        # Missing issue description
        if intent.intent_type == "create_work_order" and not intent.issue_description:
            return ClarificationRequest(
                type=ClarificationType.MISSING_DETAILS,
                prompt="What's the issue with this equipment?",
                options=["Making unusual noise", "Not starting", "Running hot", "Error code displayed"],
                context={"equipment_id": intent.equipment_id}
            )
        
        # Unclear intent
        if intent.intent_type == "unclear" or intent.confidence < 0.5:
            return ClarificationRequest(
                type=ClarificationType.INTENT_UNCLEAR,
                prompt="I'm not sure what you need. How can I help?\n\n"
                       "• Report an equipment issue\n"
                       "• Ask about a schematic\n"
                       "• Check work order status\n"
                       "• Something else",
                options=["Report issue", "Ask about schematic", "Check status", "Other"],
                context={}
            )
        
        # Off-topic
        if intent.intent_type == "off_topic":
            return ClarificationRequest(
                type=ClarificationType.OFF_TOPIC,
                prompt="I'm Rivet, your maintenance assistant. I can help with:\n\n"
                       "• Creating work orders (just describe the issue)\n"
                       "• Answering questions about equipment schematics\n"
                       "• Tracking maintenance history\n\n"
                       "What would you like help with?",
                options=[],
                context={}
            )
        
        # Default
        return ClarificationRequest(
            type=ClarificationType.INTENT_UNCLEAR,
            prompt="Could you tell me more about what you need?",
            options=[],
            context={}
        )
```

### Task 4: Enhance Intent Detection Prompt
Update the Claude prompt in `/agent_factory/rivet_pro/intent_detector.py`:
```python
INTENT_DETECTION_PROMPT = """You are an intent classifier for a maintenance management system.

Analyze this user input and extract:
1. **Intent Type**: One of:
   - create_work_order: User reporting an equipment issue
   - query_asset: User asking about equipment status/history
   - schematic_question: User asking about a print/diagram
   - update_work_order: User updating existing work
   - off_topic: Not maintenance related
   - unclear: Can't determine

2. **Confidence**: 0.0 to 1.0 how sure you are

3. **Equipment**: If mentioned:
   - equipment_type: motor, pump, vfd, plc, conveyor, etc.
   - manufacturer: siemens, allen_bradley, rockwell, etc.
   - model: if mentioned
   - equipment_name: as user said it

4. **Issue** (for work orders):
   - issue_description: what's wrong
   - priority: LOW, MEDIUM, HIGH, CRITICAL
   - urgency_score: 1-10

5. **Question** (for schematic questions):
   - The actual question to answer

CRITICAL RULES:
- If multiple equipment could match, list them as candidates
- If confidence < 0.7, set needs_clarification: true
- Never guess equipment IDs - if unclear, ask
- For off-topic input (greetings, unrelated questions), classify as off_topic
- Extract fault codes if mentioned (E210, F001, etc.)

User input: {input}

Respond in JSON format matching the ParsedIntent schema."""
```

### Task 5: Multi-Turn Clarification Handler
Create: `/agent_factory/rivet_pro/clarification_handler.py`:
```python
"""Handle multi-turn clarification conversations."""
from typing import Optional, Dict
from .clarification import ClarificationRequest, ParsedIntent
from .clarifier import IntentClarifier

class ClarificationHandler:
    """Manage clarification conversation state."""
    
    def __init__(self):
        self.clarifier = IntentClarifier()
        self.pending_clarifications: Dict[str, ClarificationRequest] = {}
    
    async def process_response(
        self,
        user_id: str,
        response: str,
        pending: ClarificationRequest
    ) -> ParsedIntent:
        """Process user's response to clarification."""
        
        # Handle option selection (1, 2, 3 or text match)
        selected = None
        if response.isdigit() and pending.options:
            idx = int(response) - 1
            if 0 <= idx < len(pending.options):
                selected = pending.options[idx]
        elif response in pending.options:
            selected = response
        
        # Merge with preserved context
        context = pending.context.copy()
        
        if pending.type == ClarificationType.EQUIPMENT_AMBIGUOUS:
            if selected:
                # Find the selected equipment
                candidates = context.get("candidates", [])
                for c in candidates:
                    if c["name"] == selected:
                        return ParsedIntent(
                            intent_type=context.get("partial_intent", "create_work_order"),
                            confidence=0.95,
                            equipment_id=c["id"],
                            equipment_name=c["name"],
                            needs_clarification=False
                        )
        
        elif pending.type == ClarificationType.MISSING_DETAILS:
            # Add the missing detail to context
            return ParsedIntent(
                intent_type=context.get("partial_intent", "create_work_order"),
                confidence=0.9,
                equipment_id=context.get("equipment_id"),
                issue_description=response,
                needs_clarification=False
            )
        
        # Re-parse if we couldn't handle it
        from .intent_detector import IntentDetector
        detector = IntentDetector()
        return await detector.detect(response)
    
    def store_pending(self, user_id: str, clarification: ClarificationRequest):
        """Store pending clarification for user."""
        self.pending_clarifications[user_id] = clarification
    
    def get_pending(self, user_id: str) -> Optional[ClarificationRequest]:
        """Get pending clarification for user."""
        return self.pending_clarifications.get(user_id)
    
    def clear_pending(self, user_id: str):
        """Clear pending clarification."""
        self.pending_clarifications.pop(user_id, None)
```

### Task 6: Add Tests for Edge Cases
Create: `/tests/test_intent_clarification.py`:
```python
"""Test intent detection and clarification."""
import pytest
from agent_factory.rivet_pro.intent_detector import IntentDetector
from agent_factory.rivet_pro.clarifier import IntentClarifier

@pytest.fixture
def detector():
    return IntentDetector()

@pytest.fixture
def clarifier():
    return IntentClarifier()

class TestIntentDetection:
    """Test intent classification."""
    
    async def test_clear_work_order_intent(self, detector):
        """Clear equipment issue should be high confidence."""
        intent = await detector.detect("The main pump is making a grinding noise")
        assert intent.intent_type == "create_work_order"
        assert intent.confidence >= 0.8
        assert "pump" in intent.equipment_name.lower()
    
    async def test_ambiguous_equipment(self, detector):
        """'The pump' with multiple pumps should need clarification."""
        intent = await detector.detect("The pump is broken")
        # Without equipment context, this should need clarification
        assert intent.needs_clarification or len(intent.equipment_candidates) > 1
    
    async def test_off_topic(self, detector):
        """Off-topic input should be classified correctly."""
        intent = await detector.detect("What's the weather like?")
        assert intent.intent_type == "off_topic"
    
    async def test_schematic_question(self, detector):
        """Schematic questions should be detected."""
        intent = await detector.detect("What's connected to the brake solenoid?")
        assert intent.intent_type == "schematic_question"
        assert intent.question is not None

class TestClarification:
    """Test clarification generation."""
    
    def test_equipment_clarification(self, clarifier):
        """Multiple equipment should generate options."""
        intent = ParsedIntent(
            intent_type="create_work_order",
            confidence=0.6,
            equipment_candidates=[
                {"id": "pump_001", "name": "Main Floor Pump"},
                {"id": "pump_002", "name": "Basement Pump"}
            ]
        )
        clarification = clarifier.generate_clarification(intent)
        assert clarification.type == ClarificationType.EQUIPMENT_AMBIGUOUS
        assert len(clarification.options) == 2
```

## COMMIT PROTOCOL
After EACH task:
```bash
tree -L 3 --dirsfirst -I 'node_modules|__pycache__|.git|venv' > .tree_snapshot.txt
git add -A
git commit -m "WS-5: [component] description

SYSTEM MAP:
$(cat .tree_snapshot.txt | head -50)"
git push origin intent-parser
```

## DEPENDENCIES
- PROVIDES to WS-3: Clarification flow for voice input
- USES existing: IntentDetector base class

## UPDATE STATUS
After each task, create/update: `/sprint/STATUS_WS5.md`

## START NOW
Begin with Task 1. Study the existing intent detector thoroughly.

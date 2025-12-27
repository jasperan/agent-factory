"""Intent Clarification System for RIVET Pro.

Handles ambiguous user intents and missing details through
intelligent clarification questions.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from agent_factory.rivet_pro.intent_detector import TroubleshootingIntent, IntentType


class ClarificationType(Enum):
    """Types of clarification needed"""
    EQUIPMENT_AMBIGUOUS = "equipment_ambiguous"  # Multiple equipment matches
    INTENT_UNCLEAR = "intent_unclear"  # Uncertain what user wants
    MISSING_DETAILS = "missing_details"  # Need more context
    FAULT_DESCRIPTION_VAGUE = "fault_description_vague"  # Symptom not specific enough


@dataclass
class ClarificationRequest:
    """
    A request for clarification from the user.

    Attributes:
        type: Type of clarification needed
        prompt: Question to ask user
        options: List of choices (if applicable)
        context: Additional context data
        original_intent: The intent that triggered clarification
    """
    type: ClarificationType
    prompt: str
    options: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    original_intent: Optional[TroubleshootingIntent] = None

    def to_telegram_message(self) -> str:
        """
        Format clarification request for Telegram.

        Returns:
            Formatted message with numbered options
        """
        message = f"🤔 {self.prompt}\n\n"

        if self.options:
            for i, option in enumerate(self.options, 1):
                message += f"{i}. {option}\n"

            message += "\n_Reply with the number or describe in your own words._"

        return message


class IntentClarifier:
    """
    Intelligent clarification system for ambiguous intents.

    Confidence threshold: 0.7
    - Above 0.7: Proceed with intent
    - 0.5-0.7: Ask for clarification
    - Below 0.5: Reject as unclear
    """

    CONFIDENCE_THRESHOLD = 0.7
    MIN_CONFIDENCE = 0.5

    def needs_clarification(self, intent: TroubleshootingIntent) -> bool:
        """
        Check if intent requires clarification.

        Args:
            intent: Detected intent

        Returns:
            True if clarification needed, False otherwise

        Clarification triggers:
        - Low confidence (< 0.7)
        - Multiple equipment candidates
        - Missing critical details for troubleshooting
        """
        # Confidence too low
        if intent.confidence < self.CONFIDENCE_THRESHOLD:
            return True

        # Equipment ambiguous
        if hasattr(intent, 'equipment_candidates') and len(intent.equipment_candidates) > 1:
            return True

        # Troubleshooting without equipment info
        if (intent.intent_type == IntentType.TROUBLESHOOTING and
            not intent.equipment_info.equipment_type):
            return True

        # Fault description too vague
        if (intent.intent_type == IntentType.TROUBLESHOOTING and
            not intent.equipment_info.symptoms and
            not intent.equipment_info.fault_codes):
            return True

        return False

    def is_too_unclear(self, intent: TroubleshootingIntent) -> bool:
        """
        Check if intent is too unclear to even clarify.

        Args:
            intent: Detected intent

        Returns:
            True if intent is beyond help, False if clarifiable
        """
        return intent.confidence < self.MIN_CONFIDENCE

    def generate_clarification(
        self,
        intent: TroubleshootingIntent
    ) -> ClarificationRequest:
        """
        Generate appropriate clarification question.

        Args:
            intent: Ambiguous intent

        Returns:
            Clarification request

        Example:
            >>> intent = detector.detect("the pump is broken")
            >>> clarification = clarifier.generate_clarification(intent)
            >>> print(clarification.prompt)
            "Which pump are you referring to?"
        """
        # Equipment ambiguous - multiple candidates
        if hasattr(intent, 'equipment_candidates') and len(intent.equipment_candidates) > 1:
            candidates = intent.equipment_candidates[:5]  # Top 5
            options = [
                f"{c.get('manufacturer', 'Unknown')} {c.get('model', 'Unknown')} ({c.get('type', 'equipment')})"
                for c in candidates
            ]

            return ClarificationRequest(
                type=ClarificationType.EQUIPMENT_AMBIGUOUS,
                prompt="Which equipment are you asking about?",
                options=options,
                context={"candidates": candidates},
                original_intent=intent
            )

        # Missing equipment info for troubleshooting
        if (intent.intent_type == IntentType.TROUBLESHOOTING and
            not intent.equipment_info.equipment_type):

            return ClarificationRequest(
                type=ClarificationType.MISSING_DETAILS,
                prompt=(
                    "What type of equipment is having the issue?\n"
                    "Examples: motor, VFD, PLC, conveyor, pump, compressor"
                ),
                options=[],
                context={},
                original_intent=intent
            )

        # Vague fault description
        if (intent.intent_type == IntentType.TROUBLESHOOTING and
            not intent.equipment_info.symptoms and
            not intent.equipment_info.fault_codes):

            return ClarificationRequest(
                type=ClarificationType.FAULT_DESCRIPTION_VAGUE,
                prompt=(
                    "Can you describe the problem in more detail?\n\n"
                    "What I need to know:\n"
                    "• What is the equipment doing (or not doing)?\n"
                    "• Any error codes or fault lights?\n"
                    "• When does the problem happen?\n"
                    "• Has anything changed recently?"
                ),
                options=[],
                context={},
                original_intent=intent
            )

        # General low confidence
        if intent.confidence < self.CONFIDENCE_THRESHOLD:
            return ClarificationRequest(
                type=ClarificationType.INTENT_UNCLEAR,
                prompt=(
                    "I'm not sure I understand what you need. Are you:\n"
                ),
                options=[
                    "Troubleshooting a broken equipment",
                    "Looking for equipment information/specs",
                    "Trying to book an expert call",
                    "Something else (please describe)"
                ],
                context={},
                original_intent=intent
            )

        # Fallback (shouldn't reach here if needs_clarification works)
        return ClarificationRequest(
            type=ClarificationType.INTENT_UNCLEAR,
            prompt="Could you rephrase your question?",
            options=[],
            context={},
            original_intent=intent
        )

    def resolve_clarification(
        self,
        clarification: ClarificationRequest,
        user_response: str
    ) -> Dict[str, Any]:
        """
        Resolve a clarification based on user's response.

        Args:
            clarification: Original clarification request
            user_response: User's answer (text or number)

        Returns:
            Dict with resolved details

        Example:
            >>> result = clarifier.resolve_clarification(
            ...     clarification,
            ...     "2"  # User selected option 2
            ... )
            >>> print(result['equipment'])
            "Siemens S7-1200 PLC"
        """
        result = {
            "clarification_type": clarification.type.value,
            "resolved": False,
            "details": {}
        }

        # Handle equipment selection (by number)
        if clarification.type == ClarificationType.EQUIPMENT_AMBIGUOUS:
            try:
                # Try to parse as number
                selection_idx = int(user_response.strip()) - 1

                if 0 <= selection_idx < len(clarification.options):
                    selected_equipment = clarification.context["candidates"][selection_idx]

                    result["resolved"] = True
                    result["details"] = {
                        "equipment_id": selected_equipment.get("id"),
                        "equipment_type": selected_equipment.get("type"),
                        "manufacturer": selected_equipment.get("manufacturer"),
                        "model": selected_equipment.get("model")
                    }

            except ValueError:
                # Not a number - treat as freeform text
                result["resolved"] = True
                result["details"] = {
                    "equipment_freeform": user_response
                }

        # Handle intent clarification
        elif clarification.type == ClarificationType.INTENT_UNCLEAR:
            result["resolved"] = True
            result["details"] = {
                "user_clarification": user_response
            }

        # Handle missing details or vague description
        else:
            result["resolved"] = True
            result["details"] = {
                "additional_info": user_response
            }

        return result

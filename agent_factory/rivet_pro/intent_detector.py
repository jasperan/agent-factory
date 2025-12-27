"""
Intent Detection for RIVET Pro Troubleshooting Questions

Classifies user questions and extracts equipment details using LLM-based analysis.

Features:
- Intent classification (troubleshooting, information, booking, account)
- Equipment extraction (type, manufacturer, model, fault codes)
- Urgency scoring (1-10 scale)
- Multi-modal support (text, images, voice transcripts)

Example:
    >>> detector = IntentDetector()
    >>> intent = detector.detect("Motor running hot, tripping after 30 min")
    >>> print(intent.intent_type)  # troubleshooting
    >>> print(intent.equipment_info.equipment_type)  # motor
    >>> print(intent.urgency_score)  # 7
"""

import re
import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

# Lazy imports: ChatAnthropic, HumanMessage, SystemMessage imported in methods to avoid import-time hang

# TAB 3 Phase 1: Context Extractor Integration
from agent_factory.rivet_pro.context_extractor import ContextExtractor, ContextExtractionResult


class IntentType(Enum):
    """Types of user intents"""
    TROUBLESHOOTING = "troubleshooting"  # Primary: equipment issue
    INFORMATION = "information"  # Knowledge base query
    BOOKING = "booking"  # Schedule expert call
    ACCOUNT = "account"  # Subscription management
    FEEDBACK = "feedback"  # Rating/review
    UNKNOWN = "unknown"


@dataclass
class EquipmentInfo:
    """Extracted equipment details"""
    equipment_type: Optional[str] = None  # motor, vfd, plc, conveyor, etc
    manufacturer: Optional[str] = None  # allen_bradley, siemens, etc
    model: Optional[str] = None  # PowerFlex 525, S7-1200, etc
    fault_codes: List[str] = field(default_factory=list)  # E210, F001, etc
    symptoms: List[str] = field(default_factory=list)  # overheating, tripping, noise
    raw_equipment_mention: Optional[str] = None  # original text


@dataclass
class TroubleshootingIntent:
    """Complete intent analysis result"""
    # Classification
    intent_type: IntentType
    confidence: float  # 0.0-1.0

    # Equipment details
    equipment_info: EquipmentInfo

    # Urgency
    urgency_score: int  # 1-10 (1=routine, 10=emergency)
    urgency_reason: str

    # Extracted context
    raw_question: str
    keywords: List[str] = field(default_factory=list)
    requires_image: bool = False
    requires_expert: bool = False

    # Metadata
    extraction_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "intent_type": self.intent_type.value,
            "confidence": self.confidence,
            "equipment_info": {
                "equipment_type": self.equipment_info.equipment_type,
                "manufacturer": self.equipment_info.manufacturer,
                "model": self.equipment_info.model,
                "fault_codes": self.equipment_info.fault_codes,
                "symptoms": self.equipment_info.symptoms,
            },
            "urgency_score": self.urgency_score,
            "urgency_reason": self.urgency_reason,
            "keywords": self.keywords,
            "requires_image": self.requires_image,
            "requires_expert": self.requires_expert,
        }


class IntentDetector:
    """
    Detects troubleshooting intent and extracts equipment details.

    Uses LLM-based analysis to classify questions and extract structured
    information about equipment, symptoms, and urgency.
    """

    # Common equipment types
    EQUIPMENT_TYPES = [
        "motor", "vfd", "drive", "plc", "hmi", "sensor", "actuator",
        "conveyor", "pump", "compressor", "valve", "cylinder", "bearing",
        "gearbox", "transformer", "contactor", "relay", "switch", "breaker",
        "inverter", "servo", "encoder", "resolver", "panel", "junction_box"
    ]

    # Common manufacturers
    MANUFACTURERS = [
        "allen_bradley", "rockwell", "siemens", "schneider", "omron",
        "mitsubishi", "abb", "ge", "eaton", "honeywell", "emerson",
        "yokogawa", "fanuc", "yaskawa", "delta", "fuji", "weg"
    ]

    # Urgency keywords
    URGENT_KEYWORDS = [
        "emergency", "critical", "down", "stopped", "failed", "fire", "smoke",
        "burning", "sparking", "explosion", "safety", "injury", "danger"
    ]

    def __init__(self, llm_provider: str = "anthropic", model_name: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize intent detector.

        Args:
            llm_provider: LLM provider (anthropic, openai, ollama)
            model_name: Model to use for intent detection
        """
        self.llm_provider = llm_provider

        if llm_provider == "anthropic":
            # Lazy import to avoid hanging on module load
            from langchain_anthropic import ChatAnthropic
            self.llm = ChatAnthropic(model=model_name, temperature=0.0)
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")

        # Compile regex patterns for equipment extraction
        self._compile_patterns()

        # TAB 3 Phase 1: Initialize Context Extractor (plugin)
        # Only enable if feature flag is set (default: enabled)
        enable_context_extractor = os.getenv("ENABLE_CONTEXT_EXTRACTOR", "true").lower() == "true"
        self.context_extractor = ContextExtractor(enable_llm=enable_context_extractor) if enable_context_extractor else None

    def _compile_patterns(self):
        """Compile regex patterns for equipment extraction"""
        # Fault code patterns (e.g., E210, F001, A123)
        self.fault_code_pattern = re.compile(r'\b[A-Z]\d{2,4}\b')

        # Model number patterns (e.g., PowerFlex 525, S7-1200)
        self.model_pattern = re.compile(
            r'\b(?:PowerFlex|MicroLogix|CompactLogix|ControlLogix|S7|CPU|FR-|ML|CP|'
            r'VFD|ATV|Altivar)\s*[-]?\s*\d+[A-Za-z0-9-]*\b',
            re.IGNORECASE
        )

    def detect(self, question: str, context: Optional[Dict[str, Any]] = None) -> TroubleshootingIntent:
        """
        Detect intent and extract equipment details from question.

        Args:
            question: User's troubleshooting question
            context: Optional context (images, voice transcripts, etc.)

        Returns:
            TroubleshootingIntent with extracted information
        """
        # Quick pattern-based extraction first
        quick_equipment = self._quick_extract_equipment(question)

        # LLM-based structured extraction
        llm_result = self._llm_extract(question, context or {})

        # Merge results (LLM takes precedence)
        equipment_info = self._merge_equipment_info(quick_equipment, llm_result.get("equipment", {}))

        # TAB 3 Phase 1: Deep extraction if needed (confidence low or multimodal input)
        confidence = llm_result.get("confidence", 0.8)
        if self.context_extractor and self._should_use_deep_extraction(confidence, context or {}):
            try:
                deep_result = self._run_deep_extraction(question, context or {})
                equipment_info = self._merge_deep_extraction(equipment_info, deep_result)
                # Boost confidence if deep extraction found more details
                if deep_result.confidence > confidence:
                    confidence = deep_result.confidence
            except Exception as e:
                # Graceful degradation if deep extraction fails
                print(f"Deep extraction failed (continuing with standard extraction): {e}")

        # Classify intent type
        intent_type = self._classify_intent(question, llm_result)

        # Score urgency
        urgency_score, urgency_reason = self._score_urgency(question, llm_result)

        # Extract keywords
        keywords = self._extract_keywords(question)

        return TroubleshootingIntent(
            intent_type=intent_type,
            confidence=confidence,
            equipment_info=equipment_info,
            urgency_score=urgency_score,
            urgency_reason=urgency_reason,
            raw_question=question,
            keywords=keywords,
            requires_image=llm_result.get("requires_image", False),
            requires_expert=llm_result.get("requires_expert", False),
            extraction_metadata=llm_result,
        )

    def _quick_extract_equipment(self, text: str) -> Dict[str, Any]:
        """
        Quick regex-based equipment extraction.

        Faster than LLM but less accurate. Used as fallback.
        """
        result = {
            "equipment_type": None,
            "manufacturer": None,
            "model": None,
            "fault_codes": [],
        }

        # Extract fault codes
        fault_codes = self.fault_code_pattern.findall(text)
        result["fault_codes"] = list(set(fault_codes))

        # Extract model numbers
        models = self.model_pattern.findall(text)
        if models:
            result["model"] = models[0]

        # Extract equipment type (simple keyword matching)
        text_lower = text.lower()
        for eq_type in self.EQUIPMENT_TYPES:
            if eq_type in text_lower:
                result["equipment_type"] = eq_type
                break

        # Extract manufacturer
        for manufacturer in self.MANUFACTURERS:
            if manufacturer.replace("_", " ") in text_lower or manufacturer.replace("_", "-") in text_lower:
                result["manufacturer"] = manufacturer
                break

        return result

    def _llm_extract(self, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        LLM-based structured extraction of intent and equipment details.

        Uses Claude with structured output to extract comprehensive information.
        """
        # Lazy import to avoid hanging on module load
        from langchain_core.messages import HumanMessage, SystemMessage

        system_prompt = """You are an industrial maintenance expert analyzing troubleshooting questions.

Extract the following information from the user's question:

1. Intent Type: (troubleshooting, information, booking, account, feedback, unknown)
2. Equipment Details:
   - Type (motor, vfd, plc, etc.)
   - Manufacturer (if mentioned)
   - Model (if mentioned)
   - Fault codes (if mentioned)
   - Symptoms (overheating, noise, tripping, etc.)
3. Urgency Score: 1-10 (1=routine, 10=emergency)
4. Urgency Reason: Why this urgency level?
5. Requires Image: Does the user need to upload a photo? (true/false)
6. Requires Expert: Is this too complex for automated answers? (true/false)
7. Confidence: How confident are you in your extraction? (0.0-1.0)

Respond in JSON format ONLY. No additional text.

Example:
{
  "intent_type": "troubleshooting",
  "equipment": {
    "type": "motor",
    "manufacturer": "allen_bradley",
    "model": null,
    "fault_codes": [],
    "symptoms": ["overheating", "tripping"]
  },
  "urgency_score": 7,
  "urgency_reason": "Motor overheating can cause equipment damage",
  "requires_image": false,
  "requires_expert": false,
  "confidence": 0.85
}"""

        user_message = f"""Question: "{question}"

Context: {context if context else "No additional context"}

Extract information in JSON format:"""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message),
            ])

            # Parse JSON response
            import json
            content = response.content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            result = json.loads(content)
            return result

        except Exception as e:
            # Fallback if LLM extraction fails
            print(f"LLM extraction failed: {e}")
            return {
                "intent_type": "troubleshooting",
                "equipment": {},
                "urgency_score": 5,
                "urgency_reason": "Default urgency",
                "requires_image": False,
                "requires_expert": False,
                "confidence": 0.5,
            }

    def _merge_equipment_info(self, quick: Dict[str, Any], llm: Dict[str, Any]) -> EquipmentInfo:
        """Merge equipment info from quick extraction and LLM"""
        return EquipmentInfo(
            equipment_type=llm.get("type") or quick.get("equipment_type"),
            manufacturer=llm.get("manufacturer") or quick.get("manufacturer"),
            model=llm.get("model") or quick.get("model"),
            fault_codes=llm.get("fault_codes", []) + quick.get("fault_codes", []),
            symptoms=llm.get("symptoms", []),
        )

    def _classify_intent(self, question: str, llm_result: Dict[str, Any]) -> IntentType:
        """Classify intent type from LLM result"""
        intent_str = llm_result.get("intent_type", "unknown").lower()

        try:
            return IntentType(intent_str)
        except ValueError:
            # Fallback: keyword-based classification
            question_lower = question.lower()

            if any(word in question_lower for word in ["book", "schedule", "call", "expert", "help"]):
                return IntentType.BOOKING
            elif any(word in question_lower for word in ["subscribe", "upgrade", "cancel", "account", "tier"]):
                return IntentType.ACCOUNT
            elif any(word in question_lower for word in ["rating", "feedback", "review"]):
                return IntentType.FEEDBACK
            elif any(word in question_lower for word in ["how", "what", "why", "explain", "teach", "learn"]):
                return IntentType.INFORMATION
            else:
                return IntentType.TROUBLESHOOTING

    def _score_urgency(self, question: str, llm_result: Dict[str, Any]) -> tuple[int, str]:
        """Score urgency from LLM result and keywords"""
        llm_score = llm_result.get("urgency_score", 5)
        llm_reason = llm_result.get("urgency_reason", "Standard urgency")

        # Boost urgency if critical keywords present
        question_lower = question.lower()
        if any(keyword in question_lower for keyword in self.URGENT_KEYWORDS):
            llm_score = min(10, llm_score + 2)
            llm_reason = f"{llm_reason} (Critical keywords detected)"

        return llm_score, llm_reason

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords for search"""
        keywords = []

        # Equipment types
        text_lower = text.lower()
        keywords.extend([eq for eq in self.EQUIPMENT_TYPES if eq in text_lower])

        # Manufacturers
        keywords.extend([mfr for mfr in self.MANUFACTURERS if mfr.replace("_", " ") in text_lower])

        # Common troubleshooting terms
        troubleshooting_terms = [
            "fault", "error", "alarm", "trip", "fail", "malfunction",
            "overload", "overheat", "vibration", "noise", "leak", "short"
        ]
        keywords.extend([term for term in troubleshooting_terms if term in text_lower])

        return list(set(keywords))

    # TAB 3 Phase 1: Context Extractor Integration Methods

    def _should_use_deep_extraction(self, confidence: float, context: Dict[str, Any]) -> bool:
        """
        Determine if deep context extraction should be used.

        Deep extraction is triggered when:
        - Confidence < 0.7 (uncertain extraction)
        - Image present (OCR or vision caption available)
        - Voice transcript (may have transcription errors)

        Args:
            confidence: LLM extraction confidence (0.0-1.0)
            context: Context dict with image/voice flags

        Returns:
            True if deep extraction should run
        """
        # Trigger 1: Low confidence
        if confidence < 0.7:
            return True

        # Trigger 2: Image present (OCR or vision available)
        if context.get("has_image") or context.get("ocr_text") or context.get("vision_caption"):
            return True

        # Trigger 3: Voice transcript (may have errors)
        if context.get("is_voice_transcript") or context.get("audio_transcription"):
            return True

        return False

    def _run_deep_extraction(self, question: str, context: Dict[str, Any]) -> ContextExtractionResult:
        """
        Run deep context extraction using ContextExtractor.

        Args:
            question: User's question
            context: Context dict with OCR/vision data

        Returns:
            ContextExtractionResult
        """
        import asyncio

        # Extract OCR and vision caption from context
        ocr_text = context.get("ocr_text")
        vision_caption = context.get("vision_caption")

        # Run async extraction (use asyncio.run if not in async context)
        try:
            result = asyncio.run(
                self.context_extractor.extract(
                    text=question,
                    ocr_text=ocr_text,
                    vision_caption=vision_caption
                )
            )
            return result
        except RuntimeError as e:
            # If already in async context, create task
            if "event loop" in str(e).lower():
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(
                    self.context_extractor.extract(
                        text=question,
                        ocr_text=ocr_text,
                        vision_caption=vision_caption
                    )
                )
            else:
                raise

    def _merge_deep_extraction(
        self,
        equipment_info: EquipmentInfo,
        deep_result: ContextExtractionResult
    ) -> EquipmentInfo:
        """
        Merge deep extraction results into EquipmentInfo.

        Deep extraction takes precedence for fields it extracted with high confidence.

        Args:
            equipment_info: Existing equipment info from standard extraction
            deep_result: Deep extraction result

        Returns:
            Enhanced EquipmentInfo
        """
        # Use deep extraction results if they're more complete
        return EquipmentInfo(
            equipment_type=deep_result.equipment_type or equipment_info.equipment_type,
            manufacturer=deep_result.manufacturer or equipment_info.manufacturer,
            model=deep_result.model_number or equipment_info.model,
            # Combine fault codes from both sources
            fault_codes=list(set(
                deep_result.fault_codes + equipment_info.fault_codes
            )),
            # Combine symptoms from both sources
            symptoms=list(set(
                deep_result.symptoms + equipment_info.symptoms
            )),
            # Keep original raw text
            raw_equipment_mention=equipment_info.raw_equipment_mention,
        )

    def detect_batch(self, questions: List[str]) -> List[TroubleshootingIntent]:
        """
        Detect intents for multiple questions (batch processing).

        Args:
            questions: List of user questions

        Returns:
            List of TroubleshootingIntent objects
        """
        return [self.detect(q) for q in questions]


# Example usage
if __name__ == "__main__":
    # Test intent detection
    detector = IntentDetector()

    test_questions = [
        "Motor running hot, tripping after 30 min",
        "VFD showing E210 fault intermittently",
        "How do I program a timer in ladder logic?",
        "I want to upgrade to Pro tier",
        "Book an expert call for Allen-Bradley PLC",
    ]

    print("Intent Detection Test Results:\n" + "="*60)
    for question in test_questions:
        intent = detector.detect(question)
        print(f"\nQuestion: {question}")
        print(f"Intent: {intent.intent_type.value}")
        print(f"Confidence: {intent.confidence:.2f}")
        print(f"Equipment: {intent.equipment_info.equipment_type}")
        print(f"Urgency: {intent.urgency_score}/10 - {intent.urgency_reason}")
        print(f"Keywords: {', '.join(intent.keywords)}")
        print("-" * 60)

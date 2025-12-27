"""
Deep Context Extraction for Equipment Queries

Enhances basic intent detection with comprehensive equipment context extraction:
- Equipment details (manufacturer, model, part number, serial number)
- Fault code extraction with multi-pattern support
- Symptom detection (overheating, vibration, noise, tripping)
- Vendor-specific validation rules

Integrated as plugin to IntentDetector - runs when:
- Confidence < 0.7
- Image/OCR present
- Voice transcript

Author: Agent Factory
Created: 2025-12-27
Phase: TAB 3 Integration - Phase 1
"""

import re
import json
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass, field

import anthropic

logger = logging.getLogger(__name__)


@dataclass
class ContextExtractionResult:
    """Deep extraction result from ContextExtractor."""
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    part_number: Optional[str] = None
    serial_number: Optional[str] = None
    equipment_type: Optional[str] = None
    fault_codes: List[str] = field(default_factory=list)
    symptoms: List[str] = field(default_factory=list)
    confidence: float = 0.0
    validation_warnings: List[str] = field(default_factory=list)
    extraction_source: str = "rule"  # rule, llm, merged


class ContextExtractor:
    """Deep equipment/fault code extraction with validation.

    Two-stage extraction:
    1. Fast rule-based extraction (regex patterns)
    2. Claude-based deep extraction (LLM)
    3. Validation with vendor-specific rules

    Example:
        >>> extractor = ContextExtractor()
        >>> result = await extractor.extract(
        ...     text="PowerFlex 525 showing fault F003",
        ...     ocr_text="Part: 25B-D010N104"
        ... )
        >>> print(result.manufacturer)  # "Rockwell"
        >>> print(result.fault_codes)  # ["F003"]
    """

    # Fault code patterns
    FAULT_CODE_PATTERNS = [
        r'\b[FEAL]\d{1,4}\b',  # F3002, E210, A123, L45
        r'\b(?:fault|error|alarm)\s*[:#]?\s*(\d{2,5})\b',  # Fault: 3002
        r'\bErr\s*(\d{2,4})\b',  # Err 210
    ]

    # Part number patterns
    PART_NUMBER_PATTERNS = [
        r'\b\d{4}[-\s][\dA-Z]+\b',  # 1756-L83E (Rockwell)
        r'\b6[ESL][A-Z]?\d[-\s]?[\dA-Z]+(?:[-\s][\dA-Z]+)*\b',  # 6ES7-315-2AH14, 6SL3244-0BB13-1PA0 (Siemens)
        r'\b[A-Z]{2,4}\d{2,4}[-\s][A-Z0-9]{3,}\b',  # PM564-TP-ETH (ABB)
    ]

    # Serial number patterns (from OCR)
    SERIAL_PATTERNS = [
        r'\b[S|s]/?[N|n][:#]?\s*([A-Z0-9]{6,})\b',  # S/N: ABC123456
        r'\bSerial[:#]?\s*([A-Z0-9]{6,})\b',  # Serial: 12345678
    ]

    # Symptom keywords
    SYMPTOM_KEYWORDS = {
        'overheating': ['hot', 'overheat', 'temperature', 'thermal'],
        'vibration': ['vibrat', 'shaking', 'wobble'],
        'noise': ['noise', 'loud', 'grinding', 'buzzing', 'humming'],
        'tripping': ['trip', 'breaker', 'fault', 'shutdown'],
        'not_starting': ['won\'t start', 'no start', 'not starting', 'doesn\'t start'],
        'intermittent': ['intermittent', 'sometimes', 'occasional'],
        'communication': ['communication', 'comm error', 'network', 'connection'],
    }

    # Vendor-specific validation rules
    VENDOR_RULES = {
        'Siemens': {
            'part_prefixes': [r'^6ES7', r'^6SL3', r'^6AG1', r'^6EP1', r'^6AV6'],
            'fault_patterns': [r'^F\d{4}$', r'^A\d{4}$'],  # F0001-F9999, A0001-A9999
        },
        'Rockwell': {
            'part_prefixes': [r'^\d{4}[-]', r'^20[-]', r'^1756[-]', r'^1769[-]'],
            'fault_patterns': [r'^F\d{1,3}$', r'^E\d{1,3}$'],  # F003, E210
        },
        'Allen-Bradley': {
            'part_prefixes': [r'^\d{4}[-]', r'^20[-]', r'^1756[-]', r'^1769[-]'],
            'fault_patterns': [r'^F\d{1,3}$', r'^E\d{1,3}$'],
        },
        'ABB': {
            'part_prefixes': [r'^PM\d{3}', r'^AC\d{3}', r'^ACS\d{3}'],
            'fault_patterns': [r'^\d{4}$'],  # 2341, 8763
        },
        'Schneider': {
            'part_prefixes': [r'^ATV\d{2,3}', r'^LXM\d{2}', r'^TM\d{3}'],
            'fault_patterns': [r'^[A-Z]{2}\d{2}$'],  # SLF11, EPF1
        },
    }

    def __init__(self, enable_llm: bool = True):
        """Initialize context extractor.

        Args:
            enable_llm: Enable Claude API for deep extraction (default: True)
        """
        self.enable_llm = enable_llm

        if enable_llm:
            try:
                self.client = anthropic.Anthropic()
                self.model = "claude-sonnet-4-20250514"
                logger.info("ContextExtractor initialized with Claude API")
            except Exception as e:
                logger.warning(f"Claude API initialization failed, using rule-based only: {e}")
                self.enable_llm = False

    async def extract(
        self,
        text: str,
        ocr_text: Optional[str] = None,
        vision_caption: Optional[str] = None
    ) -> ContextExtractionResult:
        """Extract context from text with optional OCR and vision inputs.

        Args:
            text: User's question/message
            ocr_text: Text extracted from image (OCR)
            vision_caption: Image description from vision model

        Returns:
            ContextExtractionResult with extracted context
        """
        # Stage 1: Fast rule-based extraction
        rule_result = self._rule_extract(text, ocr_text)

        # Stage 2: LLM extraction (if enabled and needed)
        if self.enable_llm:
            try:
                llm_result = await self._claude_extract(text, ocr_text, vision_caption)
                merged = self._merge_results(rule_result, llm_result)
                merged['extraction_source'] = 'merged'
            except Exception as e:
                logger.warning(f"Claude extraction failed, using rule-based only: {e}")
                merged = rule_result
                merged['extraction_source'] = 'rule'
        else:
            merged = rule_result
            merged['extraction_source'] = 'rule'

        # Stage 3: Validate with vendor-specific rules
        validated = self._validate_context(merged)

        return ContextExtractionResult(**validated)

    def _rule_extract(self, text: str, ocr_text: Optional[str] = None) -> Dict:
        """Fast regex-based extraction.

        Args:
            text: User's message
            ocr_text: OCR text from image

        Returns:
            Dict with extracted data
        """
        combined_text = f"{text} {ocr_text or ''}"

        # Extract fault codes
        fault_codes = []
        for pattern in self.FAULT_CODE_PATTERNS:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            fault_codes.extend([m.upper() for m in matches])
        fault_codes = list(set(fault_codes))  # Deduplicate

        # Extract part numbers
        part_numbers = []
        for pattern in self.PART_NUMBER_PATTERNS:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            part_numbers.extend(matches)
        part_number = part_numbers[0] if part_numbers else None

        # Extract serial numbers (from OCR only)
        serial_number = None
        if ocr_text:
            for pattern in self.SERIAL_PATTERNS:
                match = re.search(pattern, ocr_text, re.IGNORECASE)
                if match:
                    serial_number = match.group(1)
                    break

        # Detect symptoms
        symptoms = self._detect_symptoms(combined_text)

        # Infer manufacturer from part number
        manufacturer = self._infer_manufacturer(part_number) if part_number else None

        # Calculate confidence
        confidence = 0.3  # Base
        if fault_codes:
            confidence += 0.2
        if part_number:
            confidence += 0.3
        if manufacturer:
            confidence += 0.2

        return {
            'manufacturer': manufacturer,
            'model_number': None,  # Hard to extract with regex
            'part_number': part_number,
            'serial_number': serial_number,
            'equipment_type': None,  # Hard to extract with regex
            'fault_codes': fault_codes,
            'symptoms': symptoms,
            'confidence': min(confidence, 1.0),
        }

    async def _claude_extract(
        self,
        text: str,
        ocr_text: Optional[str] = None,
        vision_caption: Optional[str] = None
    ) -> Dict:
        """LLM-based extraction with Claude.

        Args:
            text: User's message
            ocr_text: OCR text from image
            vision_caption: Image description

        Returns:
            Dict with extracted data
        """
        prompt = f"""Extract equipment context from this maintenance technician's message as JSON.

User Message: {text}

OCR Text from Image: {ocr_text or "N/A"}

Image Description: {vision_caption or "N/A"}

Extract and return ONLY valid JSON (no markdown, no explanation):
{{
  "manufacturer": "Siemens|Rockwell|Allen-Bradley|ABB|Schneider|Mitsubishi|Omron|...",
  "model_number": "G120C|PowerFlex 525|S7-1200|...",
  "part_number": "6SL3244-0BB13-1PA0|25B-D010N104|...",
  "equipment_type": "VFD|PLC|HMI|motor|sensor|contactor|...",
  "fault_codes": ["F3002", "E210", "..."],
  "symptoms": ["overheating", "tripping", "vibration", "..."],
  "confidence": 0.0-1.0
}}

Rules:
- Use exact manufacturer names (Rockwell not AB, Allen-Bradley not AB)
- Extract ALL fault codes mentioned
- List specific symptoms (overheating, not "issue")
- Confidence: 0.8+ if all fields clear, 0.5-0.8 if partial, <0.5 if vague"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON response
        text_response = response.content[0].text.strip()

        # Remove markdown code blocks if present
        if text_response.startswith("```"):
            text_response = re.sub(r'^```json?\n?', '', text_response)
            text_response = re.sub(r'\n?```$', '', text_response)

        try:
            return json.loads(text_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}\nResponse: {text_response[:200]}")
            return {}

    def _merge_results(self, rule_result: Dict, llm_result: Dict) -> Dict:
        """Merge rule-based and LLM results, preferring LLM but keeping rule-based if missing.

        Args:
            rule_result: Regex extraction result
            llm_result: Claude extraction result

        Returns:
            Merged dict
        """
        merged = {}

        # For each field, prefer LLM if available and non-empty
        for key in ['manufacturer', 'model_number', 'part_number', 'serial_number', 'equipment_type']:
            llm_val = llm_result.get(key)
            rule_val = rule_result.get(key)

            # Prefer LLM, fallback to rule
            merged[key] = llm_val if llm_val else rule_val

        # For lists, combine and deduplicate
        merged['fault_codes'] = list(set(
            (llm_result.get('fault_codes') or []) +
            (rule_result.get('fault_codes') or [])
        ))

        merged['symptoms'] = list(set(
            (llm_result.get('symptoms') or []) +
            (rule_result.get('symptoms') or [])
        ))

        # Use LLM confidence if available, otherwise rule confidence
        merged['confidence'] = llm_result.get('confidence', rule_result.get('confidence', 0.5))

        return merged

    def _validate_context(self, context: Dict) -> Dict:
        """Validate extracted context with vendor-specific rules.

        Args:
            context: Extracted context dict

        Returns:
            Context dict with validation_warnings added
        """
        warnings = []
        manufacturer = context.get('manufacturer')

        if manufacturer and manufacturer in self.VENDOR_RULES:
            rules = self.VENDOR_RULES[manufacturer]

            # Validate part number format
            part_number = context.get('part_number')
            if part_number:
                valid_part = False
                for prefix_pattern in rules.get('part_prefixes', []):
                    if re.match(prefix_pattern, part_number):
                        valid_part = True
                        break

                if not valid_part:
                    warnings.append(f"Part number '{part_number}' doesn't match {manufacturer} format")

            # Validate fault code format
            fault_codes = context.get('fault_codes', [])
            for fault_code in fault_codes:
                valid_fault = False
                for fault_pattern in rules.get('fault_patterns', []):
                    if re.match(fault_pattern, fault_code):
                        valid_fault = True
                        break

                if not valid_fault:
                    warnings.append(f"Fault code '{fault_code}' doesn't match {manufacturer} format")

        context['validation_warnings'] = warnings
        return context

    def _detect_symptoms(self, text: str) -> List[str]:
        """Detect symptoms from text.

        Args:
            text: Combined text to search

        Returns:
            List of detected symptoms
        """
        text_lower = text.lower()
        detected = []

        for symptom, keywords in self.SYMPTOM_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected.append(symptom)
                    break

        return detected

    def _infer_manufacturer(self, part_number: str) -> Optional[str]:
        """Infer manufacturer from part number format.

        Args:
            part_number: Part number string

        Returns:
            Manufacturer name or None
        """
        if not part_number:
            return None

        for manufacturer, rules in self.VENDOR_RULES.items():
            for prefix_pattern in rules.get('part_prefixes', []):
                if re.match(prefix_pattern, part_number):
                    return manufacturer

        return None


# Convenience function for simple usage
async def extract_context(
    text: str,
    ocr_text: Optional[str] = None,
    vision_caption: Optional[str] = None,
    enable_llm: bool = True
) -> ContextExtractionResult:
    """Convenience function to extract context without creating extractor instance.

    Args:
        text: User's message
        ocr_text: OCR text from image
        vision_caption: Image description
        enable_llm: Enable Claude API

    Returns:
        ContextExtractionResult

    Example:
        >>> result = await extract_context("PowerFlex 525 fault F003")
        >>> print(result.manufacturer)
    """
    extractor = ContextExtractor(enable_llm=enable_llm)
    return await extractor.extract(text, ocr_text, vision_caption)

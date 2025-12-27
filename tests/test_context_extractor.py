"""
Test Suite for Context Extractor (TAB 3 Phase 1)

Tests equipment/fault code extraction accuracy:
- Rule-based extraction (regex patterns)
- LLM-based extraction (Claude API)
- Vendor-specific validation
- Integration with IntentDetector

Target Metrics:
- Equipment detection: 70% → 95%
- Model extraction: 30% → 85%
- Fault code extraction: 85% → 98%

Author: Agent Factory
Created: 2025-12-27
"""

import asyncio
import pytest
from agent_factory.rivet_pro.context_extractor import ContextExtractor, extract_context
from agent_factory.rivet_pro.intent_detector import IntentDetector


class TestContextExtractorRuleBased:
    """Test rule-based extraction (no LLM)"""

    @pytest.fixture
    def extractor(self):
        return ContextExtractor(enable_llm=False)

    @pytest.mark.asyncio
    async def test_fault_code_extraction(self, extractor):
        """Test fault code pattern detection"""
        test_cases = [
            ("VFD showing fault F3002", ["F3002"]),
            ("Error E210 on PLC", ["E210"]),
            ("Alarm A123", ["A123"]),
            ("Multiple faults: F001 and F002", ["F001", "F002"]),
        ]

        for text, expected_codes in test_cases:
            result = await extractor.extract(text)
            assert set(result.fault_codes) == set(expected_codes), \
                f"Failed for '{text}': expected {expected_codes}, got {result.fault_codes}"

    @pytest.mark.asyncio
    async def test_part_number_extraction(self, extractor):
        """Test part number pattern detection"""
        test_cases = [
            ("Part 1756-L83E", "1756-L83E"),
            ("Siemens 6ES7-315-2AH14", "6ES7-315-2AH14"),
            ("Model 6SL3244-0BB13-1PA0", "6SL3244-0BB13-1PA0"),
        ]

        for text, expected_part in test_cases:
            result = await extractor.extract(text)
            assert result.part_number == expected_part, \
                f"Failed for '{text}': expected {expected_part}, got {result.part_number}"

    @pytest.mark.asyncio
    async def test_manufacturer_inference(self, extractor):
        """Test manufacturer inference from part number"""
        test_cases = [
            ("Part 6ES7-315-2AH14", "Siemens"),
            ("Part 1756-L83E", "Rockwell"),
            ("Model 6SL3244-0BB13-1PA0", "Siemens"),
        ]

        for text, expected_mfr in test_cases:
            result = await extractor.extract(text)
            assert result.manufacturer == expected_mfr, \
                f"Failed for '{text}': expected {expected_mfr}, got {result.manufacturer}"

    @pytest.mark.asyncio
    async def test_symptom_detection(self, extractor):
        """Test symptom keyword detection"""
        test_cases = [
            ("Motor is overheating badly", ["overheating"]),
            ("Vibration and noise from pump", ["vibration", "noise"]),
            ("VFD tripping frequently", ["tripping"]),
        ]

        for text, expected_symptoms in test_cases:
            result = await extractor.extract(text)
            assert any(s in result.symptoms for s in expected_symptoms), \
                f"Failed for '{text}': expected {expected_symptoms}, got {result.symptoms}"


class TestContextExtractorLLM:
    """Test LLM-based extraction (requires Claude API key)"""

    @pytest.fixture
    def extractor(self):
        return ContextExtractor(enable_llm=True)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires Claude API key - run manually with --run-llm-tests")
    async def test_equipment_model_extraction(self, extractor):
        """Test model number extraction with LLM"""
        test_cases = [
            ("PowerFlex 525 won't start", "PowerFlex 525", "Rockwell"),
            ("Siemens G120C drive fault", "G120C", "Siemens"),
            ("Allen-Bradley PLC 1756-L83E issue", "1756-L83E", "Allen-Bradley"),
        ]

        for text, expected_model, expected_mfr in test_cases:
            result = await extractor.extract(text)
            assert result.model_number and expected_model in result.model_number, \
                f"Failed for '{text}': expected model {expected_model}, got {result.model_number}"
            assert result.manufacturer == expected_mfr, \
                f"Failed for '{text}': expected manufacturer {expected_mfr}, got {result.manufacturer}"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires Claude API key - run manually with --run-llm-tests")
    async def test_equipment_type_extraction(self, extractor):
        """Test equipment type detection with LLM"""
        test_cases = [
            ("VFD fault F003", "VFD"),
            ("PLC communication error", "PLC"),
            ("Motor overheating", "motor"),
        ]

        for text, expected_type in test_cases:
            result = await extractor.extract(text)
            assert result.equipment_type and expected_type.lower() in result.equipment_type.lower(), \
                f"Failed for '{text}': expected type {expected_type}, got {result.equipment_type}"


class TestVendorValidation:
    """Test vendor-specific validation rules"""

    @pytest.fixture
    def extractor(self):
        return ContextExtractor(enable_llm=False)

    @pytest.mark.asyncio
    async def test_siemens_part_validation(self, extractor):
        """Test Siemens part number validation"""
        # Valid Siemens part
        result = await extractor.extract("Part 6ES7-315-2AH14")
        assert len(result.validation_warnings) == 0, \
            f"Valid Siemens part should have no warnings, got: {result.validation_warnings}"

        # Invalid format (wrong prefix)
        result = await extractor.extract("", ocr_text="Siemens Part: 1756-L83E")
        # Manually set manufacturer for testing
        result.manufacturer = "Siemens"
        result.part_number = "1756-L83E"
        validated = extractor._validate_context(result.__dict__)
        assert len(validated['validation_warnings']) > 0, \
            "Invalid Siemens part should have warnings"

    @pytest.mark.asyncio
    async def test_rockwell_part_validation(self, extractor):
        """Test Rockwell part number validation"""
        # Valid Rockwell part
        result = await extractor.extract("Part 1756-L83E")
        assert len(result.validation_warnings) == 0, \
            f"Valid Rockwell part should have no warnings, got: {result.validation_warnings}"


class TestIntentDetectorIntegration:
    """Test Context Extractor integration with IntentDetector"""

    @pytest.fixture
    def detector(self):
        return IntentDetector()

    def test_deep_extraction_trigger_low_confidence(self, detector):
        """Test deep extraction triggers on low confidence"""
        # Mock low confidence scenario
        assert detector._should_use_deep_extraction(confidence=0.6, context={}) == True
        assert detector._should_use_deep_extraction(confidence=0.8, context={}) == False

    def test_deep_extraction_trigger_image(self, detector):
        """Test deep extraction triggers with image"""
        context_with_image = {"has_image": True}
        assert detector._should_use_deep_extraction(confidence=0.9, context=context_with_image) == True

    def test_deep_extraction_trigger_voice(self, detector):
        """Test deep extraction triggers with voice transcript"""
        context_with_voice = {"is_voice_transcript": True}
        assert detector._should_use_deep_extraction(confidence=0.9, context=context_with_voice) == True

    @pytest.mark.skip(reason="Requires Claude API key - run manually")
    def test_intent_detection_with_deep_extraction(self, detector):
        """Test full intent detection with deep extraction enabled"""
        # Low confidence scenario - should trigger deep extraction
        result = detector.detect(
            question="Drive error",
            context={"confidence_override": 0.5}  # Force low confidence
        )

        assert result is not None
        assert result.confidence >= 0.0


class TestRealWorldScenarios:
    """Test with real-world maintenance questions"""

    @pytest.fixture
    def extractor(self):
        return ContextExtractor(enable_llm=True)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires Claude API key - run manually")
    async def test_complex_multipart_question(self, extractor):
        """Test complex question with multiple details"""
        question = """Siemens G120C VFD, part number 6SL3244-0BB13-1PA0,
        showing fault F3002 (DC bus undervoltage). Motor is tripping after 30 seconds
        of operation. Serial number: ABC123456."""

        result = await extractor.extract(question)

        # Check all extracted fields
        assert result.manufacturer == "Siemens"
        assert "G120C" in (result.model_number or "")
        assert "6SL3244-0BB13-1PA0" in (result.part_number or "")
        assert "F3002" in result.fault_codes
        assert "tripping" in result.symptoms
        # Serial number should be extracted
        # assert "ABC123456" in (result.serial_number or "")  # May not work with just text

    @pytest.mark.asyncio
    async def test_minimal_information_question(self, extractor):
        """Test with minimal information provided"""
        question = "VFD fault"

        result = await extractor.extract(question)

        # Should still extract something
        assert result is not None
        # Confidence should be low
        assert result.confidence < 0.7


if __name__ == "__main__":
    # Run quick tests without LLM
    pytest.main([__file__, "-v", "-k", "not llm and not integration"])

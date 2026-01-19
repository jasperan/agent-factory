#!/usr/bin/env python3
"""
Quick validation script for SEOAgent implementation

Tests core functionality without requiring pytest.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.content.seo_agent import SEOAgent, VideoMetadata


def test_basic_optimization():
    """Test basic metadata optimization"""
    print("Test 1: Basic metadata optimization...")

    sample_script = """
    PLC ladder logic is the foundation of industrial automation.
    In this tutorial, we'll learn how to program a simple motor
    control circuit using Allen-Bradley ControlLogix PLCs.
    """

    with patch('agents.content.seo_agent.SupabaseMemoryStorage') as mock_storage:
        mock_client = MagicMock()
        mock_storage.return_value.client = mock_client

        agent = SEOAgent()
        metadata = agent.optimize_metadata(
            video_id="vid:test123",
            script=sample_script,
            topic="PLC Ladder Logic Basics",
            target_keywords=["PLC tutorial", "ladder logic"]
        )

        # Validate
        assert isinstance(metadata, VideoMetadata), "Should return VideoMetadata"
        assert metadata.video_id == "vid:test123", "Video ID should match"
        assert 30 <= len(metadata.title) <= 70, f"Title length {len(metadata.title)} not in range"
        assert 100 <= len(metadata.description) <= 5000, "Description length invalid"
        assert 10 <= len(metadata.tags) <= 15, f"Tag count {len(metadata.tags)} not in range"
        assert metadata.primary_keyword, "Should have primary keyword"

        print("  PASS - Basic optimization works")
        return True


def test_title_generation():
    """Test title generation"""
    print("Test 2: Title generation...")

    with patch('agents.content.seo_agent.SupabaseMemoryStorage') as mock_storage:
        mock_client = MagicMock()
        mock_storage.return_value.client = mock_client

        agent = SEOAgent()

        # Test with short topic
        title1 = agent._generate_title("PLC Basics", "PLC tutorial")
        assert 30 <= len(title1) <= 70, f"Title length {len(title1)} invalid"

        # Test with long topic
        title2 = agent._generate_title(
            "Advanced PLC Programming with Allen-Bradley ControlLogix Systems",
            "PLC programming"
        )
        assert len(title2) <= 70, "Long title should be trimmed"

        print("  PASS - Title generation works")
        return True


def test_keyword_extraction():
    """Test keyword extraction"""
    print("Test 3: Keyword extraction...")

    with patch('agents.content.seo_agent.SupabaseMemoryStorage') as mock_storage:
        mock_client = MagicMock()
        mock_storage.return_value.client = mock_client

        agent = SEOAgent()

        script = "PLC ladder logic motor control. Start stop button circuit."
        keywords = agent._extract_keywords_from_text(script, "PLC Basics")

        assert isinstance(keywords, list), "Should return list"
        assert len(keywords) > 0, "Should extract keywords"

        # Check for technical terms
        keywords_lower = [kw.lower() for kw in keywords]
        assert any("ladder" in kw for kw in keywords_lower), "Should extract 'ladder'"
        assert any("motor" in kw for kw in keywords_lower), "Should extract 'motor'"

        print("  PASS - Keyword extraction works")
        return True


def test_performance_estimation():
    """Test CTR and watch time estimation"""
    print("Test 4: Performance estimation...")

    with patch('agents.content.seo_agent.SupabaseMemoryStorage') as mock_storage:
        mock_client = MagicMock()
        mock_storage.return_value.client = mock_client

        agent = SEOAgent()

        # Test CTR estimation
        good_title = "PLC Ladder Logic Basics: Complete Motor Control Tutorial"
        ctr = agent._estimate_ctr(good_title)
        assert 0.05 <= ctr <= 0.15, f"CTR {ctr} out of range"
        assert ctr > 0.05, "Good title should have bonus CTR"

        # Test watch time estimation
        short_script = " ".join(["word"] * 100)
        watch_time = agent._estimate_watch_time(short_script)
        assert watch_time >= 3, "Minimum watch time should be 3 minutes"

        long_script = " ".join(["word"] * 3000)
        watch_time = agent._estimate_watch_time(long_script)
        assert watch_time <= 20, "Maximum watch time should be 20 minutes"

        print("  PASS - Performance estimation works")
        return True


def test_agent_run_method():
    """Test agent run() method"""
    print("Test 5: Agent run() method...")

    with patch('agents.content.seo_agent.SupabaseMemoryStorage') as mock_storage:
        mock_client = MagicMock()
        mock_storage.return_value.client = mock_client

        agent = SEOAgent()

        payload = {
            "video_id": "vid:test123",
            "script": "PLC tutorial script",
            "topic": "PLC Basics"
        }

        result = agent.run(payload)

        assert result["status"] == "success", "Run should succeed"
        assert "result" in result, "Should return result"
        assert result["result"]["video_id"] == "vid:test123", "Video ID should match"

        print("  PASS - Agent run() method works")
        return True


def test_error_handling():
    """Test error handling"""
    print("Test 6: Error handling...")

    with patch('agents.content.seo_agent.SupabaseMemoryStorage') as mock_storage:
        mock_client = MagicMock()
        mock_storage.return_value.client = mock_client

        agent = SEOAgent()

        # Missing required fields
        payload = {"video_id": "vid:test123"}
        result = agent.run(payload)

        assert result["status"] == "error", "Should return error"
        assert "error" in result, "Should include error message"

        print("  PASS - Error handling works")
        return True


def main():
    """Run all validation tests"""
    print("=" * 80)
    print("SEOAgent Validation Tests")
    print("=" * 80)
    print()

    tests = [
        test_basic_optimization,
        test_title_generation,
        test_keyword_extraction,
        test_performance_estimation,
        test_agent_run_method,
        test_error_handling
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  FAIL - {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print()
    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

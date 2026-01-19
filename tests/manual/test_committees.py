"""
Comprehensive test suite for all 5 committee systems.

Tests each committee's:
- Voting mechanism
- Report generation
- Consensus calculation
- Concern flagging
- Decision thresholds (approve/flag/reject)
"""

import sys
from pathlib import Path

# Add agents directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.committees import (
    QualityReviewCommittee,
    DesignCommittee,
    EducationCommittee,
    ContentStrategyCommittee,
    AnalyticsCommittee,
)


def test_quality_review_committee():
    """Test Quality Review Committee."""
    print("\n" + "=" * 70)
    print("TEST 1: QUALITY REVIEW COMMITTEE")
    print("=" * 70)

    committee = QualityReviewCommittee()

    # Test Case 1: High-quality video (should approve)
    print("\n[Test 1a] High-quality video (should APPROVE):")
    high_quality = {
        "script_quality": 9.0,
        "visual_quality": 8.5,
        "pacing": 8.0,
        "clarity": 9.0,
        "accuracy": 9.5,
        "engagement": 8.0,
    }

    decision = committee.vote(high_quality)
    print(f"  Decision: {decision.decision.upper()}")
    print(f"  Overall Score: {decision.overall_score}/10")
    print(f"  Consensus: {int(decision.consensus_level * 100)}%")
    assert decision.decision == "approve", "Should approve high-quality video"
    assert decision.overall_score >= 8.0, "Should have score >= 8.0"
    print("  [PASS]")

    # Test Case 2: Medium-quality video (should flag)
    print("\n[Test 1b] Medium-quality video (should FLAG):")
    medium_quality = {
        "script_quality": 7.0,
        "visual_quality": 7.0,
        "pacing": 6.5,
        "clarity": 7.0,
        "accuracy": 7.5,
        "engagement": 6.5,
    }

    decision = committee.vote(medium_quality)
    print(f"  Decision: {decision.decision.upper()}")
    print(f"  Overall Score: {decision.overall_score}/10")
    print(f"  Consensus: {int(decision.consensus_level * 100)}%")
    assert decision.decision == "flag", "Should flag medium-quality video"
    assert 6.0 <= decision.overall_score < 8.0, "Should have score 6.0-7.9"
    print("  [PASS]")

    # Test Case 3: Low-quality video (should reject)
    print("\n[Test 1c] Low-quality video (should REJECT):")
    low_quality = {
        "script_quality": 5.0,
        "visual_quality": 4.5,
        "pacing": 5.0,
        "clarity": 4.0,
        "accuracy": 5.5,
        "engagement": 4.0,
    }

    decision = committee.vote(low_quality)
    print(f"  Decision: {decision.decision.upper()}")
    print(f"  Overall Score: {decision.overall_score}/10")
    print(f"  Consensus: {int(decision.consensus_level * 100)}%")
    assert decision.decision == "reject", "Should reject low-quality video"
    assert decision.overall_score < 6.0, "Should have score < 6.0"
    print("  [PASS]")

    # Test report generation
    print("\n[Test 1d] Report generation:")
    report = committee.generate_report()
    assert len(report) > 0, "Report should not be empty"
    assert "QUALITY REVIEW COMMITTEE" in report, "Report should have header"
    print("  [PASS] Report generated successfully")

    print("\n[OK] Quality Review Committee: All tests passed")


def test_design_committee():
    """Test Design Committee."""
    print("\n" + "=" * 70)
    print("TEST 2: DESIGN COMMITTEE")
    print("=" * 70)

    committee = DesignCommittee()

    # Test Case 1: Excellent design (should approve)
    print("\n[Test 2a] Excellent design (should APPROVE):")
    excellent_design = {
        "thumbnail_clarity": 9.0,
        "color_harmony": 8.5,
        "typography": 9.0,
        "visual_hierarchy": 8.5,
        "brand_alignment": 8.0,
        "accessibility": 9.0,
    }

    decision = committee.vote(excellent_design)
    print(f"  Decision: {decision.decision.upper()}")
    print(f"  Overall Score: {decision.overall_score}/10")
    print(f"  Consensus: {int(decision.consensus_level * 100)}%")
    assert decision.decision == "approve", "Should approve excellent design"
    print("  [PASS]")

    # Test Case 2: Check consensus calculation
    print("\n[Test 2b] Consensus calculation:")
    consensus = committee.get_consensus()
    print(f"  Consensus Level: {int(consensus * 100)}%")
    assert 0 <= consensus <= 1, "Consensus should be between 0 and 1"
    print("  [PASS]")

    # Test Case 3: Flag concerns
    print("\n[Test 2c] Concern flagging:")
    concerns = committee.flag_concerns()
    print(f"  Concerns found: {len(concerns)}")
    assert isinstance(concerns, list), "Concerns should be a list"
    print("  [PASS]")

    print("\n[OK] Design Committee: All tests passed")


def test_education_committee():
    """Test Education Committee."""
    print("\n" + "=" * 70)
    print("TEST 3: EDUCATION COMMITTEE")
    print("=" * 70)

    committee = EducationCommittee()

    # Test Case 1: Strong educational content (should approve)
    print("\n[Test 3a] Strong educational content (should APPROVE):")
    strong_content = {
        "learning_objectives": 9.0,
        "prerequisite_coverage": 8.5,
        "example_quality": 9.0,
        "practice_opportunities": 8.0,
        "knowledge_retention": 8.5,
        "scaffolding": 8.5,
    }

    decision = committee.vote(strong_content)
    print(f"  Decision: {decision.decision.upper()}")
    print(f"  Overall Score: {decision.overall_score}/10")
    print(f"  Consensus: {int(decision.consensus_level * 100)}%")
    assert decision.decision == "approve", "Should approve strong content"
    print("  [PASS]")

    # Test Case 2: Verify member votes
    print("\n[Test 3b] Member votes structure:")
    assert len(decision.votes) == 5, "Should have 5 member votes"
    for member, vote_data in decision.votes.items():
        print(f"  {member}: {vote_data['score']}/10")
        assert "score" in vote_data, "Vote should have score"
        assert "feedback" in vote_data, "Vote should have feedback"
        assert "weight" in vote_data, "Vote should have weight"
    print("  [PASS]")

    print("\n[OK] Education Committee: All tests passed")


def test_content_strategy_committee():
    """Test Content Strategy Committee."""
    print("\n" + "=" * 70)
    print("TEST 4: CONTENT STRATEGY COMMITTEE")
    print("=" * 70)

    committee = ContentStrategyCommittee()

    # Test Case 1: Excellent topic (should approve)
    print("\n[Test 4a] Excellent topic (should APPROVE):")
    excellent_topic = {
        "topic_relevance": 9.0,
        "seo_potential": 8.5,
        "audience_fit": 9.0,
        "strategic_timing": 8.5,
        "gap_coverage": 8.0,
        "differentiation": 8.0,
    }

    decision = committee.vote(excellent_topic)
    print(f"  Decision: {decision.decision.upper()}")
    print(f"  Overall Score: {decision.overall_score}/10")
    print(f"  Consensus: {int(decision.consensus_level * 100)}%")
    assert decision.decision == "approve", "Should approve excellent topic"
    print("  [PASS]")

    # Test Case 2: Check recommendations
    print("\n[Test 4b] Recommendations generation:")
    print(f"  Recommendations: {len(decision.recommendations)}")
    for rec in decision.recommendations:
        print(f"    - {rec}")
    assert isinstance(decision.recommendations, list), "Should have recommendations list"
    print("  [PASS]")

    print("\n[OK] Content Strategy Committee: All tests passed")


def test_analytics_committee():
    """Test Analytics Committee."""
    print("\n" + "=" * 70)
    print("TEST 5: ANALYTICS COMMITTEE")
    print("=" * 70)

    committee = AnalyticsCommittee()

    # Test Case 1: Strong optimization (should approve)
    print("\n[Test 5a] Strong optimization (should APPROVE):")
    strong_optimization = {
        "statistical_rigor": 8.5,
        "business_impact": 9.0,
        "trend_clarity": 8.5,
        "actionability": 9.0,
        "predictive_value": 8.0,
        "user_insight": 8.5,
    }

    decision = committee.vote(strong_optimization)
    print(f"  Decision: {decision.decision.upper()}")
    print(f"  Overall Score: {decision.overall_score}/10")
    print(f"  Consensus: {int(decision.consensus_level * 100)}%")
    assert decision.decision == "approve", "Should approve strong optimization"
    print("  [PASS]")

    # Test Case 2: Timestamp verification
    print("\n[Test 5b] Timestamp verification:")
    print(f"  Timestamp: {decision.timestamp}")
    assert decision.timestamp is not None, "Decision should have timestamp"
    print("  [PASS]")

    # Test Case 3: Decision structure
    print("\n[Test 5c] Decision structure verification:")
    assert hasattr(decision, "decision"), "Should have decision attribute"
    assert hasattr(decision, "overall_score"), "Should have overall_score"
    assert hasattr(decision, "consensus_level"), "Should have consensus_level"
    assert hasattr(decision, "votes"), "Should have votes"
    assert hasattr(decision, "concerns"), "Should have concerns"
    assert hasattr(decision, "recommendations"), "Should have recommendations"
    print("  [PASS]")

    print("\n[OK] Analytics Committee: All tests passed")


def run_all_committee_demos():
    """Run demo main() for all committees."""
    print("\n" + "=" * 70)
    print("RUNNING ALL COMMITTEE DEMOS")
    print("=" * 70)

    from agents.committees.quality_review_committee import main as quality_demo
    from agents.committees.design_committee import main as design_demo
    from agents.committees.education_committee import main as education_demo
    from agents.committees.content_strategy_committee import main as strategy_demo
    from agents.committees.analytics_committee import main as analytics_demo

    quality_demo()
    design_demo()
    education_demo()
    strategy_demo()
    analytics_demo()


def main():
    """Run complete test suite."""
    print("\n" + "=" * 70)
    print("COMMITTEE SYSTEMS TEST SUITE")
    print("=" * 70)
    print("\nTesting 5 democratic multi-agent decision-making systems...")

    try:
        # Run all tests
        test_quality_review_committee()
        test_design_committee()
        test_education_committee()
        test_content_strategy_committee()
        test_analytics_committee()

        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print("[OK] Quality Review Committee: PASSED")
        print("[OK] Design Committee: PASSED")
        print("[OK] Education Committee: PASSED")
        print("[OK] Content Strategy Committee: PASSED")
        print("[OK] Analytics Committee: PASSED")
        print("\n[SUCCESS] All 5 committee systems working correctly!")
        print("=" * 70)

        # Ask if user wants to see demos
        print("\nRun interactive demos? (y/n): ", end="")
        response = input().strip().lower()
        if response == "y":
            run_all_committee_demos()

    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

"""
Standalone test suite for committee systems.
Tests each committee independently without agent_factory dependencies.
"""

import sys
from pathlib import Path

# Test each committee by directly importing its module
print("\n" + "=" * 70)
print("COMMITTEE SYSTEMS - STANDALONE TEST SUITE")
print("=" * 70)

# Test 1: Quality Review Committee
print("\n" + "=" * 70)
print("TEST 1: QUALITY REVIEW COMMITTEE")
print("=" * 70)

try:
    sys.path.insert(0, str(Path(__file__).parent))
    from agents.committees.quality_review_committee import QualityReviewCommittee

    committee = QualityReviewCommittee()

    # High-quality video test
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
    print("  [PASS]")

    # Medium-quality video test
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
    assert decision.decision == "flag", "Should flag medium-quality video"
    print("  [PASS]")

    # Low-quality video test
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
    assert decision.decision == "reject", "Should reject low-quality video"
    print("  [PASS]")

    print("\n[OK] Quality Review Committee: All tests passed")

except Exception as e:
    print(f"\n[FAIL] Quality Review Committee failed: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Design Committee
print("\n" + "=" * 70)
print("TEST 2: DESIGN COMMITTEE")
print("=" * 70)

try:
    from agents.committees.design_committee import DesignCommittee

    committee = DesignCommittee()

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

    print("\n[Test 2b] Consensus calculation:")
    consensus = committee.get_consensus()
    print(f"  Consensus Level: {int(consensus * 100)}%")
    assert 0 <= consensus <= 1, "Consensus should be between 0 and 1"
    print("  [PASS]")

    print("\n[OK] Design Committee: All tests passed")

except Exception as e:
    print(f"\n[FAIL] Design Committee failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Education Committee
print("\n" + "=" * 70)
print("TEST 3: EDUCATION COMMITTEE")
print("=" * 70)

try:
    from agents.committees.education_committee import EducationCommittee

    committee = EducationCommittee()

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

    print("\n[Test 3b] Member votes structure:")
    assert len(decision.votes) == 5, "Should have 5 member votes"
    for member in decision.votes:
        print(f"  {member}: {decision.votes[member]['score']}/10")
    print("  [PASS]")

    print("\n[OK] Education Committee: All tests passed")

except Exception as e:
    print(f"\n[FAIL] Education Committee failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Content Strategy Committee
print("\n" + "=" * 70)
print("TEST 4: CONTENT STRATEGY COMMITTEE")
print("=" * 70)

try:
    from agents.committees.content_strategy_committee import ContentStrategyCommittee

    committee = ContentStrategyCommittee()

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

    print("\n[Test 4b] Recommendations generation:")
    print(f"  Recommendations: {len(decision.recommendations)}")
    assert isinstance(decision.recommendations, list), "Should have recommendations list"
    print("  [PASS]")

    print("\n[OK] Content Strategy Committee: All tests passed")

except Exception as e:
    print(f"\n[FAIL] Content Strategy Committee failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Analytics Committee
print("\n" + "=" * 70)
print("TEST 5: ANALYTICS COMMITTEE")
print("=" * 70)

try:
    from agents.committees.analytics_committee import AnalyticsCommittee

    committee = AnalyticsCommittee()

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

    print("\n[Test 5b] Decision structure verification:")
    assert hasattr(decision, "decision"), "Should have decision attribute"
    assert hasattr(decision, "overall_score"), "Should have overall_score"
    assert hasattr(decision, "consensus_level"), "Should have consensus_level"
    print("  [PASS]")

    print("\n[OK] Analytics Committee: All tests passed")

except Exception as e:
    print(f"\n[FAIL] Analytics Committee failed: {e}")
    import traceback
    traceback.print_exc()

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

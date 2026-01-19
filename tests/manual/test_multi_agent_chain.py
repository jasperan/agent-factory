#!/usr/bin/env python3
"""
Test Multi-Agent Content Enhancement Chain

Tests the 4-agent chain:
1. ContentResearcherAgent - KB queries for related content
2. ContentEnricherAgent - Rule-based outline generation
3. ScriptwriterAgent - Template-based script generation
4. QualityEnhancerAgent - GPT-4 fallback (if needed)

Expected results:
- 450+ word scripts
- 80% won't need LLM enhancement
- ~$0.002 cost per script (vs $0.01 with pure GPT-4)
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.content.scriptwriter_agent import ScriptwriterAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_single_topic(topic: str, use_llm: bool = True):
    """Test multi-agent chain for a single topic"""
    print("\n" + "=" * 80)
    print(f"Testing Multi-Agent Chain: {topic}")
    print("=" * 80)

    agent = ScriptwriterAgent()

    try:
        # Generate script using multi-agent chain
        script = agent.generate_script_with_chain(topic, use_llm_fallback=use_llm)

        # Display results
        print(f"\n[SUCCESS] Script Generated Successfully")
        print(f"\nMetrics:")
        print(f"  - Word Count: {script['word_count']} words")
        duration_sec = int(script['estimated_duration_seconds'])
        print(f"  - Duration: {duration_sec // 60}:{duration_sec % 60:02d} minutes")
        print(f"  - Citations: {len(script['citations'])} sources")
        print(f"  - Sections: {len(script['sections'])}")
        print(f"  - Quality Score: {script['quality_score']}/100")
        print(f"  - LLM Enhanced: {script.get('llm_enhanced', False)}")
        print(f"  - Cost: ${script.get('llm_cost', 0):.4f}")

        if script.get('quality_issues'):
            print(f"\n[WARNING] Quality Issues:")
            for issue in script['quality_issues']:
                print(f"  - {issue}")

        # Show script preview
        print(f"\n[PREVIEW] Script Preview (first 200 chars):")
        print(f"  {script['full_script'][:200]}...")

        return script

    except Exception as e:
        print(f"\n[ERROR] Test Failed: {e}")
        logger.exception("Test failed")
        return None


def write_results_to_markdown(results, chain_name, output_file):
    """Write test results to markdown file for tracking over time"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not results:
        return

    # Calculate statistics
    avg_words = sum(s['word_count'] for s in results) / len(results)
    avg_quality = sum(s['quality_score'] for s in results) / len(results)
    llm_enhanced_count = sum(1 for s in results if s.get('llm_enhanced'))
    llm_usage_rate = (llm_enhanced_count / len(results)) * 100
    total_cost = sum(s.get('llm_cost', 0) for s in results)
    avg_cost = total_cost / len(results)

    # Quality breakdown
    excellent = sum(1 for s in results if s['quality_score'] >= 80)
    good = sum(1 for s in results if 60 <= s['quality_score'] < 80)
    needs_work = sum(1 for s in results if s['quality_score'] < 60)

    # Cost comparison
    gpt4_cost = len(results) * 0.01
    savings = gpt4_cost - total_cost
    savings_pct = (savings / gpt4_cost) * 100 if gpt4_cost > 0 else 0

    # Build markdown content
    md_content = f"""# {chain_name} - Test Results

**Test Date:** {timestamp}
**Scripts Tested:** {len(results)}
**Chain Version:** v1.0 (KB-first with GPT-4 fallback)

---

## Summary Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Average Word Count** | {avg_words:.0f} words | 450-600 words | {'✅' if avg_words >= 450 else '⚠️'} |
| **Average Quality Score** | {avg_quality:.0f}/100 | 70+ | {'✅' if avg_quality >= 70 else '⚠️'} |
| **LLM Usage Rate** | {llm_usage_rate:.0f}% ({llm_enhanced_count}/{len(results)}) | <20% | {'✅' if llm_usage_rate < 20 else '⚠️'} |
| **Average Cost/Script** | ${avg_cost:.4f} | <$0.005 | {'✅' if avg_cost < 0.005 else '⚠️'} |
| **Total Cost** | ${total_cost:.4f} | - | - |

---

## Quality Distribution

| Category | Count | Percentage |
|----------|-------|------------|
| **Excellent (80+)** | {excellent} | {(excellent/len(results)*100):.0f}% |
| **Good (60-79)** | {good} | {(good/len(results)*100):.0f}% |
| **Needs Work (<60)** | {needs_work} | {(needs_work/len(results)*100):.0f}% |

---

## Cost Analysis

| Approach | Total Cost | Cost/Script | Savings |
|----------|-----------|-------------|---------|
| **Multi-Agent Chain** | ${total_cost:.4f} | ${avg_cost:.4f} | - |
| **Pure GPT-4** | ${gpt4_cost:.2f} | $0.0100 | - |
| **Difference** | ${savings:.4f} | - | {savings_pct:.0f}% |

---

## Individual Results

| Topic | Words | Quality | Citations | Sections | LLM Enhanced | Cost |
|-------|-------|---------|-----------|----------|--------------|------|
"""

    # Add individual results
    for script in results:
        topic = script['title']
        words = script['word_count']
        quality = script['quality_score']
        citations = len(script['citations'])
        sections = len(script['sections'])
        llm_enhanced = '✅' if script.get('llm_enhanced') else '❌'
        cost = f"${script.get('llm_cost', 0):.4f}"

        md_content += f"| {topic} | {words} | {quality}/100 | {citations} | {sections} | {llm_enhanced} | {cost} |\n"

    # Add quality issues section
    md_content += "\n---\n\n## Quality Issues by Topic\n\n"

    for script in results:
        issues = script.get('quality_issues', [])
        if issues:
            md_content += f"\n### {script['title']}\n\n"
            for issue in issues:
                md_content += f"- {issue}\n"

    # Add recommendations
    md_content += "\n---\n\n## Recommendations\n\n"

    if llm_usage_rate > 50:
        md_content += "- **High LLM Usage:** Consider adding more concept/procedure/pattern atoms to KB\n"

    if avg_words < 450:
        md_content += "- **Below Word Target:** Improve atom content extraction or add more related atoms per topic\n"

    if avg_quality < 70:
        md_content += "- **Below Quality Target:** Review atom type distribution and improve content formatting\n"

    if savings_pct < 50:
        md_content += "- **Low Cost Savings:** Chain isn't achieving expected efficiency gains - investigate KB coverage\n"

    if excellent == 0:
        md_content += "- **No Excellent Scripts:** Focus on increasing atom quality and improving outline generation\n"

    md_content += "\n---\n\n## Chain Architecture\n\n"
    md_content += """
1. **ContentResearcherAgent** - Queries KB for 10-15 atoms (primary, prerequisites, examples, procedures, faults)
2. **ContentEnricherAgent** - Creates structured outline with target word counts per section
3. **ScriptwriterAgent** - Generates script from outline using templates
4. **QualityEnhancerAgent** - GPT-4 fallback ONLY if < 400 words

**Expected Performance:**
- 80% of scripts should NOT need LLM enhancement
- Average cost: ~$0.002/script (vs $0.01 pure GPT-4)
- Quality: 70+ score for scripts with good KB coverage
"""

    md_content += f"\n---\n\n*Generated: {timestamp}*\n"

    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"\n[RESULTS] Written to: {output_file}")


def test_multiple_topics(output_file=None):
    """Test chain with diverse topics"""
    test_topics = [
        "Introduction to PLCs",
        "Ladder Logic Programming",
        "Motor Control Basics",
        "Timer Instructions",
        "Counter Instructions"
    ]

    results = []
    total_cost = 0
    llm_enhanced_count = 0

    print("\n" + "=" * 80)
    print("Multi-Agent Chain - Batch Test (5 Topics)")
    print("=" * 80)

    for topic in test_topics:
        script = test_single_topic(topic, use_llm=True)

        if script:
            results.append(script)
            total_cost += script.get('llm_cost', 0)
            if script.get('llm_enhanced'):
                llm_enhanced_count += 1

    # Summary statistics
    print("\n" + "=" * 80)
    print("BATCH TEST SUMMARY")
    print("=" * 80)

    if results:
        avg_words = sum(s['word_count'] for s in results) / len(results)
        avg_quality = sum(s['quality_score'] for s in results) / len(results)
        llm_usage_rate = (llm_enhanced_count / len(results)) * 100

        print(f"\nResults from {len(results)} scripts:")
        print(f"  - Average Word Count: {avg_words:.0f} words")
        print(f"  - Average Quality Score: {avg_quality:.0f}/100")
        print(f"  - LLM Usage Rate: {llm_usage_rate:.0f}% ({llm_enhanced_count}/{len(results)} scripts)")
        print(f"  - Total Cost: ${total_cost:.4f}")
        print(f"  - Average Cost/Script: ${total_cost/len(results):.4f}")

        # Compare to pure GPT-4 approach
        gpt4_cost = len(results) * 0.01  # Estimated $0.01 per script
        savings = gpt4_cost - total_cost
        savings_pct = (savings / gpt4_cost) * 100

        print(f"\n[COST] Cost Comparison:")
        print(f"  - Multi-Agent Chain: ${total_cost:.4f}")
        print(f"  - Pure GPT-4: ${gpt4_cost:.2f}")
        print(f"  - Savings: ${savings:.4f} ({savings_pct:.0f}%)")

        # Quality breakdown
        print(f"\n[QUALITY] Quality Breakdown:")
        excellent = sum(1 for s in results if s['quality_score'] >= 80)
        good = sum(1 for s in results if 60 <= s['quality_score'] < 80)
        needs_work = sum(1 for s in results if s['quality_score'] < 60)

        print(f"  - Excellent (80+): {excellent} scripts")
        print(f"  - Good (60-79): {good} scripts")
        print(f"  - Needs Work (<60): {needs_work} scripts")

        # Write results to markdown
        if output_file:
            write_results_to_markdown(results, "Multi-Agent Content Enhancement Chain", output_file)
    else:
        print("\n[ERROR] No successful results")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Multi-Agent Content Chain")
    parser.add_argument('--topic', type=str, help='Test single topic')
    parser.add_argument('--batch', action='store_true', help='Run batch test (5 topics)')
    parser.add_argument('--no-llm', action='store_true', help='Disable LLM fallback')
    parser.add_argument('--output', type=str, help='Output file for results (markdown)')

    args = parser.parse_args()

    # Generate default output filename if --batch and no output specified
    if args.batch and not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"multi_agent_chain_test_results_{timestamp}.md"

    if args.batch:
        test_multiple_topics(output_file=args.output)
    elif args.topic:
        test_single_topic(args.topic, use_llm=not args.no_llm)
    else:
        # Default: run single test
        print("Testing with single topic (use --batch for multiple topics)")
        test_single_topic("Introduction to PLCs", use_llm=not args.no_llm)

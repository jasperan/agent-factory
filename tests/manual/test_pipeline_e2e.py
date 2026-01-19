#!/usr/bin/env python3
"""
End-to-End Pipeline Integration Test

Tests the complete ISH swarm workflow:
1. Knowledge base query → Find relevant atoms
2. Script generation → Generate video script
3. Quality review → Score and approve/reject
4. Voice production → Generate narration audio
5. Video assembly → Render final video
6. Thumbnail generation → Create eye-catching thumbnail
7. SEO optimization → Generate metadata

This validates all 9 agents work together correctly.

Usage:
    poetry run python test_pipeline_e2e.py

Expected output:
    - Generated script in data/scripts/
    - Generated audio in data/audio/
    - Generated video in data/videos/
    - Generated thumbnail in data/thumbnails/
    - SEO metadata in data/seo/

Requirements:
    - OPENAI_API_KEY in .env
    - SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env
    - FFmpeg installed
    - 1,965 knowledge atoms in Supabase
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_step(step_num: int, title: str):
    """Print a step header"""
    print(f"\n--- Step {step_num}: {title} ---\n")


def print_success(message: str):
    """Print success message"""
    print(f"[SUCCESS] {message}")


def print_error(message: str):
    """Print error message"""
    print(f"[ERROR] {message}")


def print_info(message: str):
    """Print info message"""
    print(f"[INFO] {message}")


def test_step_1_knowledge_base_query() -> List[Dict[str, Any]]:
    """
    Step 1: Query knowledge base for relevant atoms

    Returns:
        List of knowledge atoms (dicts)
    """
    print_step(1, "Knowledge Base Query (Supabase)")

    try:
        from agent_factory.memory.storage import SupabaseMemoryStorage
        from supabase import create_client

        # Initialize Supabase client directly
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not url or not key:
            print_error("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found in .env")
            return []

        client = create_client(url, key)

        # Test topic: "PLC motor control"
        topic = "PLC"
        print_info(f"Querying Supabase knowledge_atoms table for: '{topic}'")

        # Perform keyword search (simpler, more reliable)
        result = client.table("knowledge_atoms") \
            .select("atom_id, atom_type, title, summary, content, keywords, source_url, source_pages") \
            .or_(f"title.ilike.%{topic}%,content.ilike.%{topic}%,keywords.cs.{{{topic}}}") \
            .limit(5) \
            .execute()

        atoms = result.data if result and result.data else []

        if not atoms:
            print_error("No atoms found in knowledge base")
            print_info("Checking if table exists and has data...")

            # Check total count
            count_result = client.table("knowledge_atoms").select("atom_id", count="exact").limit(1).execute()
            total = count_result.count if count_result else 0
            print_info(f"Total atoms in database: {total}")

            return []

        print_success(f"Found {len(atoms)} relevant atoms")
        for idx, atom in enumerate(atoms, 1):
            print(f"  {idx}. {atom.get('title', 'Untitled')} ({atom.get('atom_type', 'unknown')})")

        return atoms

    except Exception as e:
        print_error(f"Knowledge base query failed: {e}")
        logger.exception("Step 1 failed")
        return []


def test_step_2_script_generation(atoms: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Step 2: Generate video script from atoms

    Args:
        atoms: List of knowledge atoms

    Returns:
        Generated script dict with title, script, citations
    """
    print_step(2, "Script Generation")

    if not atoms:
        print_error("No atoms provided for script generation")
        return {}

    try:
        from agents.content.scriptwriter_agent import ScriptwriterAgent

        # Initialize agent
        agent = ScriptwriterAgent()

        # Generate script
        topic = "PLC Motor Control Basics"
        print_info(f"Generating script for: '{topic}'")

        script_data = agent.generate_script(
            topic=topic,
            atoms=atoms
        )

        if not script_data or 'full_script' not in script_data:
            print_error("Script generation returned invalid data")
            return {}

        # Save script to file
        output_dir = Path("data/scripts")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"e2e_test_{timestamp}.json"

        with open(output_path, 'w') as f:
            json.dump(script_data, f, indent=2, default=str)

        word_count = script_data.get('word_count', len(script_data['full_script'].split()))
        print_success(f"Script generated ({word_count} words)")
        print_info(f"Saved to: {output_path}")
        print_info(f"Quality score: {script_data.get('quality_score', 'N/A')}/100")

        return script_data

    except Exception as e:
        print_error(f"Script generation failed: {e}")
        logger.exception("Step 2 failed")
        return {}


def test_step_3_quality_review(script_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 3: Review script quality

    Args:
        script_data: Generated script dict

    Returns:
        Review result with score and decision
    """
    print_step(3, "Quality Review")

    if not script_data or 'full_script' not in script_data:
        print_error("No script provided for quality review")
        return {}

    try:
        from agents.content.video_quality_reviewer_agent import VideoQualityReviewerAgent

        # Initialize agent
        agent = VideoQualityReviewerAgent()

        # Review script
        print_info("Reviewing script quality...")

        review_result = agent.review_video(
            script_text=script_data['full_script']
        )

        if not review_result:
            print_error("Quality review failed")
            return {}

        score = review_result.get('overall_score', 0)
        decision = review_result.get('decision', 'unknown')

        print_success(f"Review complete: {decision.upper()} (score: {score}/10)")

        # Print detailed scores
        dimensions = review_result.get('dimension_scores', {})
        for dimension, dim_data in dimensions.items():
            score = dim_data.get('score', 0) if isinstance(dim_data, dict) else dim_data
            print(f"  - {dimension}: {score}/10")

        return review_result

    except Exception as e:
        print_error(f"Quality review failed: {e}")
        logger.exception("Step 3 failed")
        return {}


def test_step_4_voice_production(script_data: Dict[str, Any]) -> str:
    """
    Step 4: Generate voice narration

    Args:
        script_data: Generated script dict

    Returns:
        Path to generated audio file
    """
    print_step(4, "Voice Production")

    if not script_data or 'full_script' not in script_data:
        print_error("No script provided for voice production")
        return ""

    try:
        from agents.media.voice_production_agent import VoiceProductionAgent

        # Initialize agent (uses edge-tts by default)
        agent = VoiceProductionAgent()

        # Generate audio
        print_info("Generating voice narration (edge-tts)...")

        # Build output path
        output_dir = Path("data/audio")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"e2e_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"

        # Run async method
        import asyncio
        audio_path = asyncio.run(agent.generate_audio(
            text=script_data['full_script'],
            output_path=str(output_path)
        ))

        if not audio_path or not Path(audio_path).exists():
            print_error("Voice production failed - no audio file generated")
            return ""

        file_size = Path(audio_path).stat().st_size
        print_success(f"Audio generated ({file_size:,} bytes)")
        print_info(f"Saved to: {audio_path}")

        return audio_path

    except Exception as e:
        print_error(f"Voice production failed: {e}")
        logger.exception("Step 4 failed")
        return ""


def test_step_5_video_assembly(script_data: Dict[str, Any], audio_path: str) -> str:
    """
    Step 5: Assemble final video

    Args:
        script_data: Generated script dict
        audio_path: Path to audio file

    Returns:
        Path to generated video file
    """
    print_step(5, "Video Assembly")

    if not audio_path or not Path(audio_path).exists():
        print_error("No audio file provided for video assembly")
        return ""

    try:
        from agents.media.video_assembly_agent import VideoAssemblyAgent

        # Initialize agent
        agent = VideoAssemblyAgent()

        # Assemble video
        print_info("Assembling video with audio + visuals...")

        video_path = agent.create_video(
            audio_path=audio_path,
            title=script_data.get('title', 'Untitled'),
            script=script_data.get('full_script', ''),
            output_filename=f"e2e_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        )

        if not video_path or not Path(video_path).exists():
            print_error("Video assembly failed - no video file generated")
            return ""

        file_size = Path(video_path).stat().st_size
        print_success(f"Video assembled ({file_size:,} bytes)")
        print_info(f"Saved to: {video_path}")

        return video_path

    except Exception as e:
        print_error(f"Video assembly failed: {e}")
        logger.exception("Step 5 failed")
        return ""


def test_step_6_thumbnail_generation(script_data: Dict[str, Any]) -> List[str]:
    """
    Step 6: Generate video thumbnail

    Args:
        script_data: Generated script dict

    Returns:
        List of paths to generated thumbnail variants
    """
    print_step(6, "Thumbnail Generation")

    try:
        from agents.content.thumbnail_agent import ThumbnailAgent

        # Initialize agent
        agent = ThumbnailAgent()

        # Generate thumbnails
        print_info("Generating thumbnail variants...")

        video_id = f"e2e_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        topic = script_data.get('title', 'PLC Motor Control')

        thumbnail_paths = agent.generate_thumbnails(
            video_id=video_id,
            topic=topic,
            num_variants=3
        )

        if not thumbnail_paths:
            print_error("Thumbnail generation failed")
            return []

        print_success(f"Generated {len(thumbnail_paths)} thumbnail variants")
        for idx, path in enumerate(thumbnail_paths, 1):
            print(f"  {idx}. {path}")

        return thumbnail_paths

    except Exception as e:
        print_error(f"Thumbnail generation failed: {e}")
        logger.exception("Step 6 failed")
        return []


def test_step_7_seo_optimization(script_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 7: Optimize SEO metadata

    Args:
        script_data: Generated script dict

    Returns:
        SEO metadata dict
    """
    print_step(7, "SEO Optimization")

    if not script_data or 'full_script' not in script_data:
        print_error("No script provided for SEO optimization")
        return {}

    try:
        from agents.content.seo_agent import SEOAgent

        # Initialize agent
        agent = SEOAgent()

        # Optimize metadata
        print_info("Optimizing SEO metadata...")

        video_id = f"e2e_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        metadata = agent.optimize_metadata(
            video_id=video_id,
            script=script_data['full_script'],
            topic=script_data.get('title', 'PLC Motor Control'),
            target_keywords=['PLC', 'motor control', 'industrial automation']
        )

        if not metadata:
            print_error("SEO optimization failed")
            return {}

        print_success("SEO metadata optimized")
        print(f"  Title: {metadata.title}")
        print(f"  Primary keyword: {metadata.primary_keyword}")
        print(f"  Tags: {', '.join(metadata.tags[:5])}...")
        print(f"  Estimated CTR: {metadata.estimated_ctr:.1%}")

        return metadata.model_dump()

    except Exception as e:
        print_error(f"SEO optimization failed: {e}")
        logger.exception("Step 7 failed")
        return {}


def main():
    """Run complete end-to-end pipeline test"""

    print_section("ISH Swarm End-to-End Pipeline Test")
    print("Testing all 9 agents in sequence...")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Track results
    results = {
        'started_at': datetime.now().isoformat(),
        'steps': {}
    }

    # Step 1: Knowledge Base Query
    atoms = test_step_1_knowledge_base_query()
    results['steps']['kb_query'] = {
        'success': bool(atoms),
        'atom_count': len(atoms)
    }

    if not atoms:
        print_error("Pipeline failed at Step 1 - cannot continue")
        return

    # Step 2: Script Generation
    script_data = test_step_2_script_generation(atoms)
    results['steps']['script_generation'] = {
        'success': bool(script_data),
        'word_count': script_data.get('word_count', 0) if script_data else 0
    }

    if not script_data:
        print_error("Pipeline failed at Step 2 - cannot continue")
        return

    # Step 3: Quality Review
    review_result = test_step_3_quality_review(script_data)
    results['steps']['quality_review'] = {
        'success': bool(review_result),
        'score': review_result.get('overall_score', 0),
        'decision': review_result.get('decision', 'unknown')
    }

    if not review_result or review_result.get('decision') == 'reject':
        print_error("Script rejected by quality review - stopping pipeline")
        return

    # Step 4: Voice Production
    audio_path = test_step_4_voice_production(script_data)
    results['steps']['voice_production'] = {
        'success': bool(audio_path),
        'audio_path': str(audio_path) if audio_path else None
    }

    if not audio_path:
        print_error("Pipeline failed at Step 4 - cannot continue")
        return

    # Step 5: Video Assembly
    video_path = test_step_5_video_assembly(script_data, audio_path)
    results['steps']['video_assembly'] = {
        'success': bool(video_path),
        'video_path': str(video_path) if video_path else None
    }

    if not video_path:
        print_error("Pipeline failed at Step 5 - cannot continue")
        return

    # Step 6: Thumbnail Generation
    thumbnail_paths = test_step_6_thumbnail_generation(script_data)
    results['steps']['thumbnail_generation'] = {
        'success': bool(thumbnail_paths),
        'variant_count': len(thumbnail_paths)
    }

    # Step 7: SEO Optimization
    seo_metadata = test_step_7_seo_optimization(script_data)
    results['steps']['seo_optimization'] = {
        'success': bool(seo_metadata),
        'title': seo_metadata.get('title') if seo_metadata else None
    }

    # Final summary
    results['completed_at'] = datetime.now().isoformat()
    results['total_steps'] = 7
    results['successful_steps'] = sum(1 for step in results['steps'].values() if step['success'])

    print_section("Pipeline Test Results")

    print(f"Total steps: {results['total_steps']}")
    print(f"Successful: {results['successful_steps']}")
    print(f"Failed: {results['total_steps'] - results['successful_steps']}")

    if results['successful_steps'] == results['total_steps']:
        print_success("ALL STEPS PASSED - Pipeline working end-to-end!")
    else:
        print_error(f"Pipeline incomplete - {results['total_steps'] - results['successful_steps']} steps failed")

    # Save results
    results_path = Path("data/pipeline_test_results.json")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    print_info(f"Results saved to: {results_path}")
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        logger.exception("Pipeline test failed")
        sys.exit(1)

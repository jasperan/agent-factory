#!/usr/bin/env python3
"""
FULL AUTO VIDEO GENERATION - Topic to Finished MP4

Complete autonomous pipeline:
1. Query knowledge base for topic
2. Generate script with ScriptwriterAgent
3. Generate audio with VoiceProductionAgent
4. Create video with simple slides
5. Output ready-to-upload MP4

Usage:
    poetry run python scripts/auto_generate_video.py "PLC Basics"
    poetry run python scripts/auto_generate_video.py "Motor Control"
    poetry run python scripts/auto_generate_video.py "Ladder Logic"
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.content.scriptwriter_agent import ScriptwriterAgent
from agents.media.voice_production_agent import VoiceProductionAgent

# Simple video creation (no MoviePy complexity)
import subprocess


def create_slide_image(text: str, width: int = 1920, height: int = 1080, fontsize: int = 60):
    """Create a single slide image with text"""
    img = Image.new('RGB', (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Try to use a system font
    try:
        font = ImageFont.truetype("arial.ttf", fontsize)
    except:
        font = ImageFont.load_default()

    # Word wrap text
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] < width - 200:  # 100px margin on each side
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    # Draw text centered
    y = height // 2 - (len(lines) * fontsize) // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, y), line, fill=(255, 255, 255), font=font)
        y += fontsize + 20

    return img


def create_video_from_images_and_audio(image_paths: list, audio_path: Path, output_path: Path):
    """Create MP4 video from images and audio using ffmpeg"""
    from imageio_ffmpeg import get_ffmpeg_exe

    # Get bundled ffmpeg from imageio-ffmpeg
    ffmpeg_path = get_ffmpeg_exe()

    # Use first slide as static image with audio
    subprocess.run([
        ffmpeg_path, "-y",
        "-loop", "1",
        "-i", str(image_paths[0]),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(output_path)
    ], check=True, capture_output=True)


async def generate_video(topic: str, query: str):
    """Full auto pipeline"""
    print("=" * 70)
    print(f"AUTO VIDEO GENERATION: {topic}")
    print("=" * 70)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = project_root / "data" / "videos" / f"video_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Generate script
    print("\n[1/4] Generating script from knowledge base...")
    scriptwriter = ScriptwriterAgent()

    atoms = scriptwriter.query_atoms(query, limit=3)
    if not atoms:
        print(f"[ERROR] No knowledge atoms found for: {query}")
        return False

    script = scriptwriter.generate_script(topic, atoms)
    script = scriptwriter.add_personality_markers(script)
    script = scriptwriter.add_visual_cues(script)

    print(f"[OK] Script: {script['word_count']} words, ~{script['estimated_duration_seconds']//60}m{script['estimated_duration_seconds']%60}s")

    # Save script
    script_path = output_dir / "script.txt"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script['full_script'])

    # Step 2: Generate audio
    print("\n[2/4] Generating professional narration...")
    voice_agent = VoiceProductionAgent()

    audio_path = output_dir / "audio.mp3"

    # Clean text for TTS
    clean_text = script['full_script']
    for marker in ['[enthusiastic]', '[explanatory]', '[cautionary]', '[pause]',
                   '[emphasize]', '[show title:', '[show diagram:', '[show code:',
                   '[show table]', '[show citation:', ']']:
        clean_text = clean_text.replace(marker, ' ')
    clean_text = ' '.join(clean_text.split())

    await voice_agent.generate_audio(clean_text, str(audio_path))

    print(f"[OK] Audio: {audio_path}")

    # Step 3: Create slides
    print("\n[3/4] Creating video slides...")

    slides = []

    # Title slide
    title_img = create_slide_image(script['title'], fontsize=80)
    title_path = output_dir / "slide_title.png"
    title_img.save(title_path)
    slides.append(title_path)

    # Section slides
    for i, section in enumerate(script['sections'][:5]):  # Max 5 sections
        # Clean content
        content = section['content']
        for marker in ['[explanatory]', '[cautionary]', '[pause]', '[show code: ladder_logic]',
                       '[show diagram:', '[show table]', '[show citation:', ']']:
            content = content.replace(marker, '')

        # Limit text
        words = content.split()[:30]
        content = ' '.join(words)

        slide_text = f"{section['title']}\n\n{content}"
        slide_img = create_slide_image(slide_text, fontsize=40)
        slide_path = output_dir / f"slide_{i+1}.png"
        slide_img.save(slide_path)
        slides.append(slide_path)

    print(f"[OK] Created {len(slides)} slides")

    # Step 4: Assemble video
    print("\n[4/4] Assembling final video...")

    video_path = output_dir / f"{topic.replace(' ', '_')}.mp4"

    try:
        create_video_from_images_and_audio(slides, audio_path, video_path)
        print(f"[OK] Video: {video_path}")
    except Exception as e:
        print(f"[WARNING] ffmpeg not available: {e}")
        print("[INFO] Audio and slides created. Combine manually or install ffmpeg.")
        video_path = None

    # Summary
    print("\n" + "=" * 70)
    print("VIDEO GENERATION COMPLETE!")
    print("=" * 70)
    print(f"\nOutput directory: {output_dir}")
    print(f"  Script: script.txt")
    print(f"  Audio:  audio.mp3")
    if video_path and video_path.exists():
        print(f"  Video:  {video_path.name}")
    else:
        print(f"  Slides: slide_*.png ({len(slides)} slides)")
    print(f"\nVideo details:")
    print(f"  Title: {script['title']}")
    print(f"  Duration: ~{script['estimated_duration_seconds']//60}m {script['estimated_duration_seconds']%60}s")
    print(f"\nCitations:")
    for citation in script['citations']:
        print(f"  - {citation}")

    return True


async def main():
    """Generate videos for multiple topics"""
    topics = [
        ("Introduction to PLCs", "PLC"),
        ("Motor Control Basics", "motor control"),
        ("Ladder Logic Fundamentals", "ladder logic")
    ]

    print("=" * 70)
    print("AUTONOMOUS VIDEO GENERATION - BATCH MODE")
    print("=" * 70)
    print(f"\nGenerating {len(topics)} videos...")

    success_count = 0
    for title, query in topics:
        try:
            if await generate_video(title, query):
                success_count += 1
            print("\n")
        except Exception as e:
            print(f"[ERROR] Failed to generate '{title}': {e}\n")

    print("=" * 70)
    print(f"BATCH COMPLETE: {success_count}/{len(topics)} videos generated")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Review videos in data/videos/")
    print("2. Upload to YouTube for approval")
    print("3. If quality is good, scale up production")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Single video mode
        topic = " ".join(sys.argv[1:])
        asyncio.run(generate_video(topic, topic.lower()))
    else:
        # Batch mode
        asyncio.run(main())

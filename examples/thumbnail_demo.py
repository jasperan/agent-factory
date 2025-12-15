#!/usr/bin/env python3
"""
ThumbnailAgent Demo - Generate test thumbnails

This script demonstrates the ThumbnailAgent's capabilities:
1. Generate 3 thumbnail variants for a sample video
2. Validate dimensions (1280x720)
3. Validate file size (<2MB)
4. Display file paths and metadata
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.media.thumbnail_agent import ThumbnailAgent


def main():
    """Run ThumbnailAgent demo"""

    print("=" * 70)
    print("ThumbnailAgent Demo - YouTube Thumbnail Generation")
    print("=" * 70)
    print()

    # Initialize agent (using Pillow, not DALL-E, standalone mode without Supabase)
    print("Initializing ThumbnailAgent...")
    agent = ThumbnailAgent(use_dalle=False, enable_supabase=False)
    print(f"  Agent initialized (DALL-E: {agent.use_dalle}, Supabase: {agent.storage is not None})")
    print()

    # Test payload
    payload = {
        "video_id": "plc_demo_001",
        "title": "Master 3-Wire Motor Control Circuits",
        "script": "Learn how to wire and troubleshoot industrial motor control circuits using ladder logic and relay logic. This comprehensive guide covers safety, best practices, and common troubleshooting techniques."
    }

    print("Generating thumbnails...")
    print(f"  Video ID: {payload['video_id']}")
    print(f"  Title: {payload['title']}")
    print()

    # Run agent
    result = agent.run(payload)

    # Display results
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()

    if result["status"] == "success":
        print(f"Status: SUCCESS")
        print(f"Thumbnails generated: {len(result['result'])}")
        print()

        for variant in result["result"]:
            print("-" * 70)
            print(f"Variant {variant['variant_id']}")
            print("-" * 70)
            print(f"  File path: {variant['file_path']}")
            print(f"  Text overlay: {variant['text_overlay']}")
            print(f"  Color scheme: {variant['color_scheme']}")
            print(f"  File size: {variant['file_size_bytes']:,} bytes ({variant['file_size_bytes'] / 1024:.1f} KB)")

            # Validate file exists
            file_path = Path(variant['file_path'])
            if file_path.exists():
                print(f"  File exists: YES")

                # Validate dimensions (requires PIL)
                from PIL import Image
                img = Image.open(file_path)
                width, height = img.size
                print(f"  Dimensions: {width}x{height}")

                # Validate specs
                if width == 1280 and height == 720:
                    print(f"  YouTube specs: VALID")
                else:
                    print(f"  YouTube specs: INVALID (expected 1280x720)")

                # Validate file size
                if variant['file_size_bytes'] < 2 * 1024 * 1024:
                    print(f"  File size: VALID (<2MB)")
                else:
                    print(f"  File size: INVALID (>2MB)")
            else:
                print(f"  File exists: NO (ERROR)")

            print()

        print("=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total variants: {len(result['result'])}")
        print(f"Output directory: {agent.output_dir / payload['video_id']}")
        print()
        print("All thumbnails generated successfully!")

    else:
        print(f"Status: ERROR")
        print(f"Error message: {result.get('error', 'Unknown error')}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

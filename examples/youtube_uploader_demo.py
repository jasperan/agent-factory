#!/usr/bin/env python3
"""
YouTube Uploader Demo

Demonstrates how to use the YouTubeUploaderAgent to upload videos to YouTube.

This demo shows:
- Authentication check
- Video upload with metadata
- Custom thumbnail upload
- Privacy status management
- Quota tracking

Usage:
    # Upload a test video
    poetry run python examples/youtube_uploader_demo.py

    # Upload specific video
    poetry run python examples/youtube_uploader_demo.py --video path/to/video.mp4

    # Upload with custom metadata
    poetry run python examples/youtube_uploader_demo.py \
        --video data/videos/test.mp4 \
        --title "My Test Video" \
        --description "This is a test upload" \
        --tags "test,demo,youtube" \
        --thumbnail data/thumbnails/test.jpg \
        --privacy unlisted
"""

import sys
import argparse
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.media.youtube_uploader_agent import YouTubeUploaderAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run YouTube upload demo"""

    parser = argparse.ArgumentParser(description="YouTube Uploader Demo")
    parser.add_argument("--video", type=str, help="Path to video file (MP4)")
    parser.add_argument("--title", type=str, default="Test Upload - Delete Me", help="Video title")
    parser.add_argument("--description", type=str, default="This is an automated test upload. Safe to delete.", help="Video description")
    parser.add_argument("--tags", type=str, default="test,automation,demo", help="Comma-separated tags")
    parser.add_argument("--thumbnail", type=str, help="Path to thumbnail image (JPG/PNG)")
    parser.add_argument("--privacy", type=str, default="unlisted", choices=["public", "unlisted", "private"], help="Privacy status")
    parser.add_argument("--category", type=str, default="28", help="YouTube category ID (28=Science & Technology)")

    args = parser.parse_args()

    print("=" * 70)
    print("YouTube Uploader Demo")
    print("=" * 70)
    print()

    # Initialize agent
    logger.info("Initializing YouTubeUploaderAgent...")
    agent = YouTubeUploaderAgent()

    # Check authentication
    print("Checking authentication...")
    if not agent.authenticate():
        print()
        print("❌ Authentication failed!")
        print()
        print("Run first-time setup:")
        print("  poetry run python examples/youtube_auth_setup.py")
        print()
        print("See: examples/youtube_auth_setup.md for detailed guide")
        return 1

    print("✓ Authentication successful")
    print()

    # Show quota status
    quota = agent.get_quota_status()
    print("Quota Status:")
    print(f"  Used today:  {quota['quota_used']:,} units")
    print(f"  Remaining:   {quota['quota_remaining']:,} units")
    print(f"  Daily limit: {quota['quota_limit']:,} units")
    print()

    # Check if we have enough quota
    if quota['quota_remaining'] < 1600:
        print("❌ Insufficient quota for video upload")
        print(f"   Need: 1,600 units")
        print(f"   Have: {quota['quota_remaining']:,} units")
        print()
        print(f"Quota resets: {quota['reset_date']} (midnight Pacific)")
        return 1

    # Check video file
    if args.video:
        video_path = Path(args.video)
        if not video_path.exists():
            print(f"❌ Video file not found: {args.video}")
            return 1
    else:
        # Use a mock video for demo
        print("⚠ No video file specified")
        print()
        print("Usage examples:")
        print("  # Upload specific video")
        print("  poetry run python examples/youtube_uploader_demo.py --video data/videos/test.mp4")
        print()
        print("  # Upload with custom metadata")
        print('  poetry run python examples/youtube_uploader_demo.py \\')
        print('      --video data/videos/test.mp4 \\')
        print('      --title "My Test Video" \\')
        print('      --description "This is a test upload" \\')
        print('      --tags "test,demo,youtube" \\')
        print('      --thumbnail data/thumbnails/test.jpg \\')
        print('      --privacy unlisted')
        print()
        return 0

    # Parse tags
    tags = [tag.strip() for tag in args.tags.split(",")]

    # Prepare upload metadata
    print("Upload Configuration:")
    print(f"  Video:       {video_path.name}")
    print(f"  Title:       {args.title}")
    print(f"  Description: {args.description[:50]}...")
    print(f"  Tags:        {', '.join(tags)}")
    print(f"  Privacy:     {args.privacy}")
    print(f"  Category:    {args.category}")
    if args.thumbnail:
        print(f"  Thumbnail:   {args.thumbnail}")
    print()

    # Confirm upload
    response = input("Proceed with upload? (y/N): ").strip().lower()
    if response != 'y':
        print("Upload cancelled")
        return 0

    print()
    print("-" * 70)
    print("Uploading to YouTube...")
    print("-" * 70)
    print()

    # Execute upload
    result = agent.upload_video(
        video_path=str(video_path),
        title=args.title,
        description=args.description,
        tags=tags,
        category_id=args.category,
        privacy_status=args.privacy,
        thumbnail_path=args.thumbnail
    )

    print()
    print("=" * 70)

    if result.success:
        print("✅ Upload Successful!")
        print("=" * 70)
        print()
        print(f"Video ID:  {result.video_id}")
        print(f"Video URL: {result.video_url}")
        print(f"Status:    {result.status}")
        print(f"Privacy:   {args.privacy}")
        print()
        print(f"Quota used: {result.quota_used} units")
        print()

        # Show updated quota
        quota = agent.get_quota_status()
        print("Updated Quota:")
        print(f"  Used:      {quota['quota_used']:,} units")
        print(f"  Remaining: {quota['quota_remaining']:,} units")
        print()

        # Next steps
        print("Next Steps:")
        print("  1. View video on YouTube (may still be processing)")
        print(f"     {result.video_url}")
        print()
        print("  2. Update privacy status after review:")
        print(f"     agent.update_privacy_status('{result.video_id}', 'public')")
        print()
        print("  3. Check processing status:")
        print(f"     agent.get_upload_status('{result.video_id}')")
        print()

        return 0

    else:
        print("❌ Upload Failed")
        print("=" * 70)
        print()
        print(f"Error: {result.error_message}")
        print()
        print("Troubleshooting:")
        print("  - Check video file is valid MP4")
        print("  - Verify quota is available")
        print("  - Check YouTube API status: https://status.cloud.google.com/")
        print("  - Review logs for detailed error")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())

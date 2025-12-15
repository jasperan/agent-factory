#!/usr/bin/env python3
"""
YouTube OAuth2 Authentication Setup Script

Run this script to complete first-time OAuth2 authentication for YouTube Data API v3.

Requirements:
- client_secrets.json from Google Cloud Console (see youtube_auth_setup.md)
- Poetry environment with dependencies installed

Usage:
    poetry run python examples/youtube_auth_setup.py
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.media.youtube_uploader_agent import YouTubeUploaderAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run first-time OAuth2 authentication"""

    print("=" * 60)
    print("YouTube OAuth2 Authentication Setup")
    print("=" * 60)
    print()

    # Check for client_secrets.json
    client_secrets = Path("client_secrets.json")
    if not client_secrets.exists():
        print("❌ ERROR: client_secrets.json not found!")
        print()
        print("Setup instructions:")
        print("1. Go to: https://console.cloud.google.com")
        print("2. Create new project: 'ISH-YouTube-Automation'")
        print("3. Enable YouTube Data API v3")
        print("4. Create OAuth2 credentials (Desktop app)")
        print("5. Download client_secrets.json to project root")
        print()
        print("See: examples/youtube_auth_setup.md for detailed guide")
        return 1

    print(f"✓ Found client_secrets.json")
    print()

    # Check for existing credentials
    creds_file = Path(".youtube_credentials.json")
    if creds_file.exists():
        print(f"⚠ Existing credentials found: {creds_file}")
        print()
        response = input("Re-authenticate? (y/N): ").strip().lower()

        if response != 'y':
            print("Keeping existing credentials")
            print()

            # Verify existing credentials work
            print("Verifying credentials...")
            agent = YouTubeUploaderAgent()

            if agent.authenticate():
                print("✓ Existing credentials are valid!")
                print()
                print_quota_status(agent)
                return 0
            else:
                print("✗ Existing credentials failed verification")
                print("Continuing with re-authentication...")
                print()

        # Delete existing credentials for re-auth
        creds_file.unlink()

    # Run OAuth2 flow
    print("Starting OAuth2 authentication...")
    print()
    print("Your browser will open automatically")
    print("Please:")
    print("  1. Sign in with your Google account")
    print("  2. Grant YouTube upload permissions")
    print("  3. Return to this terminal")
    print()

    try:
        agent = YouTubeUploaderAgent()
        result = agent.authenticate(force_reauth=True)

        if result:
            print()
            print("=" * 60)
            print("✓ Authentication successful!")
            print("=" * 60)
            print()
            print(f"Credentials saved to: {agent.credentials_path}")
            print()
            print_quota_status(agent)
            print()
            print("Next steps:")
            print("  1. Test upload: poetry run python examples/youtube_uploader_demo.py")
            print("  2. Review quota limits: examples/youtube_auth_setup.md#quotas")
            print("  3. Start production pipeline!")
            print()
            return 0
        else:
            print()
            print("=" * 60)
            print("✗ Authentication failed")
            print("=" * 60)
            print()
            print("Troubleshooting:")
            print("  - Check client_secrets.json is valid")
            print("  - Verify YouTube Data API v3 is enabled")
            print("  - Review OAuth consent screen configuration")
            print("  - See: examples/youtube_auth_setup.md#troubleshooting")
            print()
            return 1

    except FileNotFoundError as e:
        print()
        print(f"❌ ERROR: {e}")
        print()
        print("See: examples/youtube_auth_setup.md for setup guide")
        return 1

    except Exception as e:
        logger.error(f"Authentication error: {e}", exc_info=True)
        print()
        print(f"❌ Unexpected error: {e}")
        print()
        print("Check logs for details")
        return 1


def print_quota_status(agent: YouTubeUploaderAgent):
    """Print current quota status"""
    quota = agent.get_quota_status()

    print("Quota Status:")
    print(f"  Used today:  {quota['quota_used']:,} units")
    print(f"  Remaining:   {quota['quota_remaining']:,} units")
    print(f"  Daily limit: {quota['quota_limit']:,} units")
    print(f"  Resets:      {quota['reset_date']} (midnight Pacific)")
    print()
    print("Estimated uploads remaining today:")

    remaining_uploads = quota['quota_remaining'] // 1600  # Cost per upload
    print(f"  Videos (with thumbnails): ~{remaining_uploads}")


if __name__ == "__main__":
    sys.exit(main())

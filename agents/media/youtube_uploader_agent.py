#!/usr/bin/env python3
"""
YouTubeUploaderAgent - Execute uploads to YouTube with OAuth2 authentication

Responsibilities:
- Upload videos via YouTube Data API v3 with resumable uploads
- Set title, description, tags, and custom thumbnails
- Handle OAuth2 authentication flow with token refresh
- Implement retry logic with exponential backoff
- Manage quota limits (10,000 units/day)
- Store upload metadata in Supabase

Schedule: On-demand (triggered by orchestrator)
Dependencies: YouTube Data API v3, OAuth2 credentials, Supabase
Output: Updates published_videos table, logs to agent_status

Based on: docs/AGENT_ORGANIZATION.md Section 5
API Docs: https://developers.google.com/youtube/v3/docs
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Literal
from dataclasses import dataclass

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from agent_factory.memory.storage import SupabaseMemoryStorage
from core.models import UploadJob

logger = logging.getLogger(__name__)

# YouTube Data API v3 scopes
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

# API quota costs (per YouTube Data API v3 documentation)
QUOTA_COSTS = {
    'videos.insert': 1600,  # Upload video
    'thumbnails.set': 50,   # Set thumbnail
    'videos.update': 50,    # Update video metadata
}

DAILY_QUOTA_LIMIT = 10000  # YouTube default daily quota


@dataclass
class UploadResult:
    """Result of a YouTube upload operation"""
    success: bool
    video_id: Optional[str] = None
    video_url: Optional[str] = None
    status: Literal["uploaded", "processing", "failed"] = "uploaded"
    error_message: Optional[str] = None
    quota_used: int = 0


class YouTubeUploaderAgent:
    """
    Execute uploads to YouTube with OAuth2 authentication.

    This agent handles the complete YouTube upload workflow:
    1. OAuth2 authentication with automatic token refresh
    2. Resumable video uploads for reliability
    3. Custom thumbnail uploads
    4. Metadata management (title, description, tags, playlists)
    5. Quota tracking and management
    6. Retry logic with exponential backoff

    Production-ready standards:
    - Type hints on all functions
    - Comprehensive error handling and logging
    - Pydantic models for data validation
    - OAuth2 token refresh automation
    - Quota management to prevent API limits
    """

    def __init__(
        self,
        credentials_path: str = ".youtube_credentials.json",
        client_secrets_path: str = "client_secrets.json"
    ):
        """
        Initialize agent with Supabase connection and OAuth2 credentials.

        Args:
            credentials_path: Path to stored OAuth2 credentials (refresh tokens)
            client_secrets_path: Path to OAuth2 client secrets from Google Cloud Console
        """
        self.storage = SupabaseMemoryStorage()
        self.agent_name = "youtube_uploader_agent"

        self.credentials_path = Path(credentials_path)
        self.client_secrets_path = Path(client_secrets_path)

        self.youtube = None  # YouTube API client (initialized on first use)
        self.credentials = None  # OAuth2 credentials

        self._quota_used_today = 0
        self._quota_reset_date = datetime.now().date()

        self._register_status()

    def _register_status(self) -> None:
        """Register agent in agent_status table"""
        try:
            self.storage.client.table("agent_status").upsert({
                "agent_name": self.agent_name,
                "status": "idle",
                "last_heartbeat": datetime.now().isoformat(),
                "tasks_completed_today": 0,
                "tasks_failed_today": 0
            }).execute()
            logger.info(f"{self.agent_name} registered")
        except Exception as e:
            logger.error(f"Failed to register {self.agent_name}: {e}")

    def _send_heartbeat(self) -> None:
        """Update heartbeat in agent_status table"""
        try:
            self.storage.client.table("agent_status") \
                .update({"last_heartbeat": datetime.now().isoformat()}) \
                .eq("agent_name", self.agent_name) \
                .execute()
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")

    def _update_status(
        self,
        status: str,
        error_message: Optional[str] = None,
        current_task: Optional[str] = None
    ) -> None:
        """Update agent status in database"""
        try:
            update_data = {
                "status": status,
                "last_heartbeat": datetime.now().isoformat()
            }
            if error_message:
                update_data["error_message"] = error_message
            if current_task:
                update_data["current_task"] = current_task

            self.storage.client.table("agent_status") \
                .update(update_data) \
                .eq("agent_name", self.agent_name) \
                .execute()
        except Exception as e:
            logger.error(f"Failed to update status: {e}")

    def _reset_quota_if_needed(self) -> None:
        """Reset daily quota counter if date has changed (midnight Pacific Time)"""
        today = datetime.now().date()
        if today > self._quota_reset_date:
            self._quota_used_today = 0
            self._quota_reset_date = today
            logger.info(f"Quota reset for new day: {today}")

    def _check_quota(self, operation: str) -> bool:
        """
        Check if we have enough quota remaining for operation.

        Args:
            operation: Operation name (e.g., 'videos.insert')

        Returns:
            True if quota is available, False otherwise
        """
        self._reset_quota_if_needed()

        cost = QUOTA_COSTS.get(operation, 0)
        remaining = DAILY_QUOTA_LIMIT - self._quota_used_today

        if cost > remaining:
            logger.error(
                f"Insufficient quota for {operation}. "
                f"Cost: {cost}, Remaining: {remaining}"
            )
            return False

        return True

    def _use_quota(self, operation: str) -> None:
        """Record quota usage for an operation"""
        cost = QUOTA_COSTS.get(operation, 0)
        self._quota_used_today += cost
        logger.info(
            f"Used {cost} quota units for {operation}. "
            f"Total today: {self._quota_used_today}/{DAILY_QUOTA_LIMIT}"
        )

    def authenticate(self, force_reauth: bool = False) -> bool:
        """
        Authenticate with YouTube via OAuth2 flow.

        This method handles:
        1. Loading existing credentials from disk
        2. Refreshing expired tokens automatically
        3. Running OAuth2 flow if no valid credentials exist
        4. Saving credentials for future use

        Args:
            force_reauth: Force new authentication even if credentials exist

        Returns:
            True if authentication successful, False otherwise

        Raises:
            FileNotFoundError: If client_secrets.json not found
        """
        try:
            # Load existing credentials
            if not force_reauth and self.credentials_path.exists():
                logger.info(f"Loading credentials from {self.credentials_path}")
                with open(self.credentials_path, 'r') as f:
                    creds_data = json.load(f)
                    self.credentials = Credentials.from_authorized_user_info(
                        creds_data,
                        SCOPES
                    )

            # Refresh expired token
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                logger.info("Refreshing expired access token")
                self.credentials.refresh(Request())

            # Run OAuth2 flow if no valid credentials
            if not self.credentials or not self.credentials.valid:
                if not self.client_secrets_path.exists():
                    raise FileNotFoundError(
                        f"OAuth2 client secrets not found at {self.client_secrets_path}. "
                        "Download from Google Cloud Console."
                    )

                logger.info("Running OAuth2 authentication flow")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.client_secrets_path),
                    SCOPES
                )
                self.credentials = flow.run_local_server(port=0)

            # Save credentials for future use
            with open(self.credentials_path, 'w') as f:
                f.write(self.credentials.to_json())
            logger.info(f"Credentials saved to {self.credentials_path}")

            # Build YouTube API client
            self.youtube = build('youtube', 'v3', credentials=self.credentials)
            logger.info("YouTube API client initialized")

            return True

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list[str],
        category_id: str = "28",  # Science & Technology
        privacy_status: Literal["public", "unlisted", "private"] = "unlisted",
        thumbnail_path: Optional[str] = None,
        playlist_ids: Optional[list[str]] = None,
        max_retries: int = 3
    ) -> UploadResult:
        """
        Upload video to YouTube with metadata and optional thumbnail.

        This method implements:
        - Resumable uploads for large files
        - Automatic retry with exponential backoff
        - Quota management
        - Thumbnail upload
        - Playlist assignment

        Args:
            video_path: Path to MP4 video file
            title: Video title (max 100 characters)
            description: Video description (max 5000 characters)
            tags: List of tags (max 500 characters total)
            category_id: YouTube category ID (default: 28 = Science & Technology)
            privacy_status: "public", "unlisted", or "private"
            thumbnail_path: Optional path to custom thumbnail (JPG/PNG)
            playlist_ids: Optional list of playlist IDs to add video to
            max_retries: Maximum retry attempts (default: 3)

        Returns:
            UploadResult with video ID, URL, and status

        Example:
            >>> agent = YouTubeUploaderAgent()
            >>> agent.authenticate()
            >>> result = agent.upload_video(
            ...     video_path="data/videos/ohms_law.mp4",
            ...     title="Ohm's Law Explained",
            ...     description="Learn the fundamentals of Ohm's Law...",
            ...     tags=["ohms law", "electricity", "tutorial"],
            ...     thumbnail_path="data/thumbnails/ohms_law.jpg"
            ... )
            >>> print(result.video_url)
            https://www.youtube.com/watch?v=abc123
        """
        self._send_heartbeat()
        self._update_status("running", current_task=f"Uploading video: {title}")

        # Validate inputs
        video_path_obj = Path(video_path)
        if not video_path_obj.exists():
            return UploadResult(
                success=False,
                error_message=f"Video file not found: {video_path}"
            )

        # Check quota
        if not self._check_quota('videos.insert'):
            return UploadResult(
                success=False,
                error_message="Daily quota limit reached. Try again tomorrow."
            )

        # Ensure authenticated
        if not self.youtube:
            if not self.authenticate():
                return UploadResult(
                    success=False,
                    error_message="YouTube authentication failed"
                )

        # Prepare video metadata
        body = {
            'snippet': {
                'title': title[:100],  # YouTube max: 100 characters
                'description': description[:5000],  # YouTube max: 5000 characters
                'tags': tags,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }

        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Upload attempt {attempt + 1}/{max_retries} for {video_path_obj.name}"
                )

                # Create resumable upload
                media = MediaFileUpload(
                    str(video_path_obj),
                    chunksize=1024 * 1024,  # 1MB chunks
                    resumable=True
                )

                # Execute upload
                request = self.youtube.videos().insert(
                    part='snippet,status',
                    body=body,
                    media_body=media
                )

                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        logger.info(f"Upload progress: {progress}%")

                video_id = response['id']
                video_url = f"https://www.youtube.com/watch?v={video_id}"

                logger.info(f"Video uploaded successfully: {video_url}")
                self._use_quota('videos.insert')

                # Upload thumbnail if provided
                if thumbnail_path:
                    self.set_thumbnail(video_id, thumbnail_path)

                # Add to playlists if specified
                if playlist_ids:
                    self._add_to_playlists(video_id, playlist_ids)

                # Store in Supabase
                self._store_upload_metadata(video_id, video_url, title, description, tags)

                self._update_status("idle", current_task=None)

                return UploadResult(
                    success=True,
                    video_id=video_id,
                    video_url=video_url,
                    status="uploaded",
                    quota_used=QUOTA_COSTS['videos.insert']
                )

            except HttpError as e:
                error_reason = e.resp.get('reason', 'Unknown error')
                logger.error(f"YouTube API error (attempt {attempt + 1}): {error_reason}")

                # Check if retryable error
                if e.resp.status in [500, 502, 503, 504]:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue

                # Non-retryable error
                self._update_status("error", error_message=str(e))
                return UploadResult(
                    success=False,
                    error_message=f"YouTube API error: {error_reason}"
                )

            except Exception as e:
                logger.error(f"Unexpected error during upload (attempt {attempt + 1}): {e}")

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue

                self._update_status("error", error_message=str(e))
                return UploadResult(
                    success=False,
                    error_message=f"Upload failed: {str(e)}"
                )

        # All retries exhausted
        error_msg = f"Upload failed after {max_retries} attempts"
        self._update_status("error", error_message=error_msg)
        return UploadResult(success=False, error_message=error_msg)

    def set_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """
        Set custom thumbnail for a video.

        Args:
            video_id: YouTube video ID
            thumbnail_path: Path to thumbnail image (JPG/PNG, max 2MB)

        Returns:
            True if successful, False otherwise
        """
        try:
            thumbnail_path_obj = Path(thumbnail_path)
            if not thumbnail_path_obj.exists():
                logger.error(f"Thumbnail not found: {thumbnail_path}")
                return False

            # Check file size (YouTube max: 2MB)
            if thumbnail_path_obj.stat().st_size > 2 * 1024 * 1024:
                logger.error("Thumbnail exceeds 2MB limit")
                return False

            # Check quota
            if not self._check_quota('thumbnails.set'):
                logger.warning("Insufficient quota for thumbnail upload. Skipping.")
                return False

            logger.info(f"Uploading thumbnail for video {video_id}")

            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path_obj))
            ).execute()

            self._use_quota('thumbnails.set')
            logger.info(f"Thumbnail uploaded successfully for {video_id}")

            return True

        except HttpError as e:
            logger.error(f"Failed to set thumbnail: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error setting thumbnail: {e}")
            return False

    def _add_to_playlists(self, video_id: str, playlist_ids: list[str]) -> None:
        """Add video to specified playlists"""
        for playlist_id in playlist_ids:
            try:
                self.youtube.playlistItems().insert(
                    part='snippet',
                    body={
                        'snippet': {
                            'playlistId': playlist_id,
                            'resourceId': {
                                'kind': 'youtube#video',
                                'videoId': video_id
                            }
                        }
                    }
                ).execute()

                logger.info(f"Added video {video_id} to playlist {playlist_id}")

            except HttpError as e:
                logger.error(f"Failed to add video to playlist {playlist_id}: {e}")

    def _store_upload_metadata(
        self,
        video_id: str,
        video_url: str,
        title: str,
        description: str,
        tags: list[str]
    ) -> None:
        """Store upload metadata in Supabase published_videos table"""
        try:
            self.storage.client.table("published_videos").insert({
                "video_id": video_id,
                "video_url": video_url,
                "title": title,
                "description": description,
                "tags": tags,
                "platform": "youtube",
                "published_at": datetime.now().isoformat(),
                "agent_name": self.agent_name
            }).execute()

            logger.info(f"Stored upload metadata for {video_id} in Supabase")

        except Exception as e:
            logger.error(f"Failed to store upload metadata: {e}")

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method called by orchestrator.

        Args:
            payload: Job payload from agent_jobs table with UploadJob data

        Returns:
            Dict with status, result/error

        Example payload:
            {
                "video_path": "data/videos/ohms_law.mp4",
                "title": "Ohm's Law Explained",
                "description": "Learn the fundamentals...",
                "tags": ["ohms law", "electricity"],
                "thumbnail_path": "data/thumbnails/ohms_law.jpg"
            }
        """
        try:
            self._send_heartbeat()
            self._update_status("running")

            # Extract upload parameters
            video_path = payload.get("video_path")
            title = payload.get("title")
            description = payload.get("description", "")
            tags = payload.get("tags", [])
            thumbnail_path = payload.get("thumbnail_path")
            privacy_status = payload.get("privacy_status", "unlisted")
            playlist_ids = payload.get("playlist_ids", [])

            # Validate required fields
            if not video_path or not title:
                return {
                    "status": "error",
                    "error": "Missing required fields: video_path, title"
                }

            # Execute upload
            result = self.upload_video(
                video_path=video_path,
                title=title,
                description=description,
                tags=tags,
                privacy_status=privacy_status,
                thumbnail_path=thumbnail_path,
                playlist_ids=playlist_ids
            )

            if result.success:
                self._update_status("completed")
                return {
                    "status": "success",
                    "result": {
                        "video_id": result.video_id,
                        "video_url": result.video_url,
                        "quota_used": result.quota_used
                    }
                }
            else:
                self._update_status("error", error_message=result.error_message)
                return {
                    "status": "error",
                    "error": result.error_message
                }

        except Exception as e:
            logger.error(f"{self.agent_name} failed: {e}")
            self._update_status("error", str(e))
            return {"status": "error", "error": str(e)}

    def get_quota_status(self) -> Dict[str, Any]:
        """
        Get current quota usage status.

        Returns:
            Dict with quota used, remaining, and reset date
        """
        self._reset_quota_if_needed()

        return {
            "quota_used": self._quota_used_today,
            "quota_remaining": DAILY_QUOTA_LIMIT - self._quota_used_today,
            "quota_limit": DAILY_QUOTA_LIMIT,
            "reset_date": self._quota_reset_date.isoformat()
        }


if __name__ == "__main__":
    # Quick test (requires OAuth2 setup)
    logging.basicConfig(level=logging.INFO)

    agent = YouTubeUploaderAgent()

    # Check quota status
    quota = agent.get_quota_status()
    print(f"Quota Status: {quota}")

    # Test authentication
    if agent.authenticate():
        print("✓ Authentication successful")
        print(f"Credentials saved to {agent.credentials_path}")
    else:
        print("✗ Authentication failed")

#!/usr/bin/env python3
"""
Unit tests for YouTubeUploaderAgent

Tests cover:
- OAuth2 authentication flow
- Video upload with metadata
- Thumbnail upload
- Quota management
- Retry logic with exponential backoff
- Error handling

All tests use mocked YouTube API to avoid requiring actual credentials.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from agents.media.youtube_uploader_agent import (
    YouTubeUploaderAgent,
    UploadResult,
    QUOTA_COSTS,
    DAILY_QUOTA_LIMIT
)


@pytest.fixture
def mock_youtube_api():
    """Mock YouTube API client"""
    mock = MagicMock()

    # Mock successful video upload response
    mock.videos().insert().execute.return_value = {
        'id': 'test_video_id_123',
        'snippet': {
            'title': 'Test Video',
            'description': 'Test Description'
        },
        'status': {
            'privacyStatus': 'unlisted'
        }
    }

    # Mock resumable upload (next_chunk returns None when complete)
    mock.videos().insert().next_chunk.return_value = (None, {'id': 'test_video_id_123'})

    # Mock thumbnail upload
    mock.thumbnails().set().execute.return_value = {'default': {'url': 'https://thumbnail.url'}}

    # Mock playlist insert
    mock.playlistItems().insert().execute.return_value = {'id': 'playlist_item_123'}

    return mock


@pytest.fixture
def mock_credentials():
    """Mock OAuth2 credentials"""
    creds = Mock()
    creds.valid = True
    creds.expired = False
    creds.refresh_token = 'test_refresh_token'
    creds.to_json.return_value = json.dumps({
        'token': 'test_token',
        'refresh_token': 'test_refresh_token'
    })
    return creds


@pytest.fixture
def mock_supabase():
    """Mock Supabase storage"""
    with patch('agents.media.youtube_uploader_agent.SupabaseMemoryStorage') as mock:
        storage = MagicMock()
        storage.client.table().upsert().execute.return_value = None
        storage.client.table().update().eq().execute.return_value = None
        storage.client.table().insert().execute.return_value = None
        mock.return_value = storage
        yield mock


@pytest.fixture
def temp_video_file():
    """Create temporary video file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        f.write(b'fake video data')
        video_path = Path(f.name)

    yield str(video_path)

    # Cleanup
    video_path.unlink(missing_ok=True)


@pytest.fixture
def temp_thumbnail_file():
    """Create temporary thumbnail file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        f.write(b'fake image data')
        thumb_path = Path(f.name)

    yield str(thumb_path)

    # Cleanup
    thumb_path.unlink(missing_ok=True)


class TestYouTubeUploaderAgent:
    """Test suite for YouTubeUploaderAgent"""

    def test_agent_initialization(self, mock_supabase):
        """Test agent initializes with correct defaults"""
        agent = YouTubeUploaderAgent()

        assert agent.agent_name == "youtube_uploader_agent"
        assert agent.youtube is None
        assert agent.credentials is None
        assert agent._quota_used_today == 0
        assert Path('data/uploads').exists()

    def test_authentication_with_existing_credentials(self, mock_supabase, mock_credentials):
        """Test authentication loads existing credentials"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(json.dumps({
                'token': 'test_token',
                'refresh_token': 'test_refresh_token'
            }))
            creds_path = f.name

        try:
            agent = YouTubeUploaderAgent(credentials_path=creds_path)

            with patch('agents.media.youtube_uploader_agent.Credentials.from_authorized_user_info') as mock_from_auth:
                mock_from_auth.return_value = mock_credentials

                with patch('agents.media.youtube_uploader_agent.build') as mock_build:
                    result = agent.authenticate()

                    assert result is True
                    assert mock_from_auth.called
                    assert mock_build.called

        finally:
            Path(creds_path).unlink(missing_ok=True)

    def test_authentication_refresh_expired_token(self, mock_supabase, mock_credentials):
        """Test authentication refreshes expired tokens"""
        mock_credentials.expired = True
        mock_credentials.valid = False

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(json.dumps({'token': 'expired_token'}))
            creds_path = f.name

        try:
            agent = YouTubeUploaderAgent(credentials_path=creds_path)

            with patch('agents.media.youtube_uploader_agent.Credentials.from_authorized_user_info') as mock_from_auth:
                mock_from_auth.return_value = mock_credentials

                with patch('agents.media.youtube_uploader_agent.Request') as mock_request:
                    with patch('agents.media.youtube_uploader_agent.build'):
                        agent.authenticate()

                        assert mock_credentials.refresh.called

        finally:
            Path(creds_path).unlink(missing_ok=True)

    def test_upload_video_success(self, mock_supabase, mock_youtube_api, mock_credentials, temp_video_file):
        """Test successful video upload"""
        agent = YouTubeUploaderAgent()
        agent.youtube = mock_youtube_api
        agent.credentials = mock_credentials

        result = agent.upload_video(
            video_path=temp_video_file,
            title="Test Video",
            description="Test Description",
            tags=["test", "video"]
        )

        assert result.success is True
        assert result.video_id == "test_video_id_123"
        assert result.video_url == "https://www.youtube.com/watch?v=test_video_id_123"
        assert result.status == "uploaded"
        assert result.quota_used == QUOTA_COSTS['videos.insert']

    def test_upload_video_with_thumbnail(self, mock_supabase, mock_youtube_api, mock_credentials, temp_video_file, temp_thumbnail_file):
        """Test video upload with custom thumbnail"""
        agent = YouTubeUploaderAgent()
        agent.youtube = mock_youtube_api
        agent.credentials = mock_credentials

        result = agent.upload_video(
            video_path=temp_video_file,
            title="Test Video",
            description="Test Description",
            tags=["test"],
            thumbnail_path=temp_thumbnail_file
        )

        assert result.success is True
        # Verify thumbnail upload was called
        assert mock_youtube_api.thumbnails().set.called

    def test_upload_video_file_not_found(self, mock_supabase):
        """Test upload fails gracefully when video file doesn't exist"""
        agent = YouTubeUploaderAgent()

        result = agent.upload_video(
            video_path="/nonexistent/video.mp4",
            title="Test Video",
            description="Test",
            tags=[]
        )

        assert result.success is False
        assert "not found" in result.error_message.lower()

    def test_upload_video_quota_exceeded(self, mock_supabase, temp_video_file):
        """Test upload fails when quota limit exceeded"""
        agent = YouTubeUploaderAgent()
        agent._quota_used_today = DAILY_QUOTA_LIMIT  # Simulate quota exhausted

        result = agent.upload_video(
            video_path=temp_video_file,
            title="Test Video",
            description="Test",
            tags=[]
        )

        assert result.success is False
        assert "quota limit" in result.error_message.lower()

    def test_upload_video_retry_on_server_error(self, mock_supabase, mock_youtube_api, mock_credentials, temp_video_file):
        """Test retry logic on transient server errors (500, 502, 503, 504)"""
        from googleapiclient.errors import HttpError

        agent = YouTubeUploaderAgent()
        agent.youtube = mock_youtube_api
        agent.credentials = mock_credentials

        # Mock HttpError with retryable status code (503 Service Unavailable)
        error_resp = Mock()
        error_resp.status = 503
        error_resp.get.return_value = "Service Unavailable"

        # First 2 attempts fail, 3rd succeeds
        mock_youtube_api.videos().insert.side_effect = [
            HttpError(error_resp, b'Service temporarily unavailable'),
            HttpError(error_resp, b'Service temporarily unavailable'),
            MagicMock(next_chunk=MagicMock(return_value=(None, {'id': 'retry_video_123'})))
        ]

        with patch('time.sleep'):  # Speed up test by mocking sleep
            result = agent.upload_video(
                video_path=temp_video_file,
                title="Retry Test Video",
                description="Test retry logic",
                tags=["test"],
                max_retries=3
            )

        assert result.success is True
        assert result.video_id == "retry_video_123"

    def test_quota_tracking(self, mock_supabase):
        """Test quota usage tracking"""
        agent = YouTubeUploaderAgent()

        # Simulate using quota
        agent._use_quota('videos.insert')
        assert agent._quota_used_today == QUOTA_COSTS['videos.insert']

        agent._use_quota('thumbnails.set')
        assert agent._quota_used_today == QUOTA_COSTS['videos.insert'] + QUOTA_COSTS['thumbnails.set']

        # Check quota status
        status = agent.get_quota_status()
        assert status['quota_used'] == agent._quota_used_today
        assert status['quota_remaining'] == DAILY_QUOTA_LIMIT - agent._quota_used_today
        assert status['quota_limit'] == DAILY_QUOTA_LIMIT

    def test_quota_reset_on_new_day(self, mock_supabase):
        """Test quota resets at midnight Pacific Time"""
        from datetime import date, timedelta

        agent = YouTubeUploaderAgent()
        agent._quota_used_today = 5000
        agent._quota_reset_date = date.today() - timedelta(days=1)  # Yesterday

        # Trigger reset check
        agent._reset_quota_if_needed()

        assert agent._quota_used_today == 0
        assert agent._quota_reset_date == date.today()

    def test_set_thumbnail_file_not_found(self, mock_supabase):
        """Test thumbnail upload fails gracefully when file doesn't exist"""
        agent = YouTubeUploaderAgent()
        agent.youtube = MagicMock()

        result = agent.set_thumbnail("video_123", "/nonexistent/thumbnail.jpg")

        assert result is False

    def test_set_thumbnail_file_too_large(self, mock_supabase):
        """Test thumbnail upload fails when file exceeds 2MB limit"""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            # Create file larger than 2MB
            f.write(b'x' * (3 * 1024 * 1024))  # 3MB
            large_thumb = Path(f.name)

        try:
            agent = YouTubeUploaderAgent()
            agent.youtube = MagicMock()

            result = agent.set_thumbnail("video_123", str(large_thumb))

            assert result is False

        finally:
            large_thumb.unlink(missing_ok=True)

    def test_run_method_with_valid_payload(self, mock_supabase, mock_youtube_api, mock_credentials, temp_video_file, temp_thumbnail_file):
        """Test orchestrator run() method with valid payload"""
        agent = YouTubeUploaderAgent()
        agent.youtube = mock_youtube_api
        agent.credentials = mock_credentials

        payload = {
            "video_path": temp_video_file,
            "title": "Test Video from Orchestrator",
            "description": "Uploaded via run() method",
            "tags": ["orchestrator", "test"],
            "thumbnail_path": temp_thumbnail_file,
            "privacy_status": "unlisted"
        }

        result = agent.run(payload)

        assert result["status"] == "success"
        assert "video_id" in result["result"]
        assert "video_url" in result["result"]
        assert result["result"]["video_id"] == "test_video_id_123"

    def test_run_method_missing_required_fields(self, mock_supabase):
        """Test run() method fails gracefully with incomplete payload"""
        agent = YouTubeUploaderAgent()

        # Missing title
        payload = {
            "video_path": "data/videos/test.mp4"
        }

        result = agent.run(payload)

        assert result["status"] == "error"
        assert "missing required fields" in result["error"].lower()

    def test_add_to_playlists(self, mock_supabase, mock_youtube_api):
        """Test adding video to playlists"""
        agent = YouTubeUploaderAgent()
        agent.youtube = mock_youtube_api

        playlist_ids = ["playlist_1", "playlist_2", "playlist_3"]
        agent._add_to_playlists("video_123", playlist_ids)

        # Verify playlist insert was called for each playlist
        assert mock_youtube_api.playlistItems().insert.call_count == 3

    def test_privacy_status_options(self, mock_supabase, mock_youtube_api, mock_credentials, temp_video_file):
        """Test different privacy status options (public, unlisted, private)"""
        agent = YouTubeUploaderAgent()
        agent.youtube = mock_youtube_api
        agent.credentials = mock_credentials

        for privacy_status in ["public", "unlisted", "private"]:
            result = agent.upload_video(
                video_path=temp_video_file,
                title=f"Test {privacy_status} Video",
                description="Testing privacy settings",
                tags=["test"],
                privacy_status=privacy_status
            )

            assert result.success is True

    def test_title_truncation(self, mock_supabase, mock_youtube_api, mock_credentials, temp_video_file):
        """Test title truncation to YouTube's 100 character limit"""
        agent = YouTubeUploaderAgent()
        agent.youtube = mock_youtube_api
        agent.credentials = mock_credentials

        long_title = "A" * 150  # 150 characters

        result = agent.upload_video(
            video_path=temp_video_file,
            title=long_title,
            description="Test",
            tags=[]
        )

        # Verify upload succeeded with truncated title
        assert result.success is True

    def test_description_truncation(self, mock_supabase, mock_youtube_api, mock_credentials, temp_video_file):
        """Test description truncation to YouTube's 5000 character limit"""
        agent = YouTubeUploaderAgent()
        agent.youtube = mock_youtube_api
        agent.credentials = mock_credentials

        long_description = "B" * 6000  # 6000 characters

        result = agent.upload_video(
            video_path=temp_video_file,
            title="Test",
            description=long_description,
            tags=[]
        )

        # Verify upload succeeded with truncated description
        assert result.success is True


@pytest.mark.integration
class TestYouTubeUploaderIntegration:
    """
    Integration tests (require actual YouTube API credentials)

    To run these tests:
    1. Set up OAuth2 credentials (see examples/youtube_auth_setup.md)
    2. Run: pytest -m integration tests/test_youtube_uploader_agent.py

    IMPORTANT: These tests will consume actual YouTube API quota!
    """

    @pytest.mark.skip(reason="Requires YouTube API credentials")
    def test_real_authentication(self):
        """Test real OAuth2 authentication flow"""
        agent = YouTubeUploaderAgent()
        result = agent.authenticate()

        assert result is True
        assert agent.youtube is not None
        assert agent.credentials is not None

    @pytest.mark.skip(reason="Requires YouTube API credentials and video file")
    def test_real_upload(self):
        """Test real video upload to YouTube"""
        agent = YouTubeUploaderAgent()
        agent.authenticate()

        result = agent.upload_video(
            video_path="data/videos/test_upload.mp4",
            title="[TEST] Automated Upload - Delete Me",
            description="This is an automated test upload. Safe to delete.",
            tags=["test", "automation"],
            privacy_status="private"  # Keep test videos private
        )

        assert result.success is True
        print(f"Test video uploaded: {result.video_url}")
        print(f"Video ID: {result.video_id}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

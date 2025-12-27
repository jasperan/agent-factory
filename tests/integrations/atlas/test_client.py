"""Unit tests for Atlas CMMS client.

These tests cover:
- AtlasTokenCache token expiry and refresh logic
- AtlasClient authentication and error handling
- API method functionality (with mocked responses)
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import httpx

from agent_factory.integrations.atlas.client import AtlasClient, AtlasTokenCache
from agent_factory.integrations.atlas.exceptions import (
    AtlasAuthError,
    AtlasAPIError,
    AtlasNotFoundError,
    AtlasValidationError,
    AtlasRateLimitError,
    AtlasConfigError
)


# ==========================================================================
# AtlasTokenCache Tests
# ==========================================================================

@pytest.mark.asyncio
async def test_token_cache_stores_token():
    """Test that token cache stores and retrieves tokens correctly."""
    cache = AtlasTokenCache()

    # Initially empty
    token = await cache.get_token()
    assert token is None

    # Set token
    await cache.set_token("test_token_123", ttl_seconds=3600)

    # Retrieve token
    token = await cache.get_token()
    assert token == "test_token_123"


@pytest.mark.asyncio
async def test_token_cache_expiry():
    """Test that expired tokens are not returned."""
    cache = AtlasTokenCache()

    # Set token with 1 second TTL
    await cache.set_token("test_token", ttl_seconds=1)

    # Token should be valid immediately
    token = await cache.get_token()
    assert token == "test_token"

    # Wait for expiry
    await asyncio.sleep(1.5)

    # Token should be expired
    token = await cache.get_token()
    assert token is None


@pytest.mark.asyncio
async def test_token_cache_refresh_buffer():
    """Test that tokens are considered expired within refresh buffer."""
    cache = AtlasTokenCache()

    # Set token with 10 second TTL (default buffer is 5 minutes)
    # For this test, we'll manually set expiry to test buffer logic
    cache._token = "test_token"
    cache._expires_at = datetime.utcnow() + timedelta(seconds=10)

    # Token should be considered expired because 10s < 300s buffer
    # (with default atlas_config.atlas_token_refresh_buffer = 300)
    # This will fail with default config, so we need to test with shorter buffer

    # For testing, let's use a 3-second buffer by modifying expiry calculation
    from agent_factory.integrations.atlas.config import atlas_config
    original_buffer = atlas_config.atlas_token_refresh_buffer

    try:
        # Temporarily set buffer to 3 seconds
        atlas_config.atlas_token_refresh_buffer = 3

        # Set token to expire in 10 seconds
        await cache.set_token("test_token", ttl_seconds=10)

        # Token should still be valid (10s > 3s buffer)
        token = await cache.get_token()
        assert token == "test_token"

        # Set token to expire in 2 seconds
        await cache.set_token("test_token_2", ttl_seconds=2)

        # Token should be expired (2s < 3s buffer)
        token = await cache.get_token()
        assert token is None

    finally:
        # Restore original buffer
        atlas_config.atlas_token_refresh_buffer = original_buffer


@pytest.mark.asyncio
async def test_token_cache_clear():
    """Test that clear() removes cached token."""
    cache = AtlasTokenCache()

    # Set token
    await cache.set_token("test_token", ttl_seconds=3600)
    assert await cache.get_token() == "test_token"

    # Clear token
    await cache.clear()

    # Token should be gone
    assert await cache.get_token() is None


@pytest.mark.asyncio
async def test_token_cache_thread_safety():
    """Test that token cache is thread-safe with concurrent access."""
    cache = AtlasTokenCache()

    # Simulate concurrent set operations
    tasks = [
        cache.set_token(f"token_{i}", ttl_seconds=3600)
        for i in range(10)
    ]
    await asyncio.gather(*tasks)

    # Should have last token set
    token = await cache.get_token()
    assert token is not None
    assert token.startswith("token_")


# ==========================================================================
# AtlasClient Configuration Tests
# ==========================================================================

def test_atlas_client_requires_base_url():
    """Test that AtlasClient raises error if base URL not configured."""
    with pytest.raises(AtlasConfigError, match="base URL not configured"):
        AtlasClient(base_url="", email="test@example.com", password="pass")


def test_atlas_client_requires_credentials():
    """Test that AtlasClient raises error if credentials not configured."""
    with pytest.raises(AtlasConfigError, match="credentials not configured"):
        AtlasClient(base_url="http://localhost:8080/api", email="", password="")


# ==========================================================================
# AtlasClient Authentication Tests
# ==========================================================================

@pytest.mark.asyncio
async def test_authenticate_success():
    """Test successful authentication flow."""
    # Mock httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"token": "jwt_token_123"}
    mock_client.post.return_value = mock_response

    async with AtlasClient(
        base_url="http://localhost:8080/api",
        email="admin@example.com",
        password="admin"
    ) as client:
        client._client = mock_client

        token = await client._authenticate()

        assert token == "jwt_token_123"
        mock_client.post.assert_called_once_with(
            "/auth/signin",
            json={"email": "admin@example.com", "password": "admin"}
        )


@pytest.mark.asyncio
async def test_authenticate_invalid_credentials():
    """Test authentication with invalid credentials."""
    # Mock httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = Mock()
    mock_response.status_code = 401
    mock_client.post.return_value = mock_response

    async with AtlasClient(
        base_url="http://localhost:8080/api",
        email="bad@example.com",
        password="wrong"
    ) as client:
        client._client = mock_client

        with pytest.raises(AtlasAuthError, match="Invalid Atlas credentials"):
            await client._authenticate()


@pytest.mark.asyncio
async def test_authenticate_no_token_in_response():
    """Test authentication when response doesn't contain token."""
    # Mock httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": "Success"}  # No token
    mock_client.post.return_value = mock_response

    async with AtlasClient(
        base_url="http://localhost:8080/api",
        email="admin@example.com",
        password="admin"
    ) as client:
        client._client = mock_client

        with pytest.raises(AtlasAuthError, match="No token in authentication response"):
            await client._authenticate()


# ==========================================================================
# AtlasClient Request Tests
# ==========================================================================

@pytest.mark.asyncio
async def test_request_auto_authenticates():
    """Test that requests automatically authenticate if no cached token."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    # Mock auth response
    auth_response = Mock()
    auth_response.status_code = 200
    auth_response.json.return_value = {"token": "jwt_123"}

    # Mock API response
    api_response = Mock()
    api_response.status_code = 200
    api_response.json.return_value = {"id": "wo-123"}
    api_response.content = b'{"id": "wo-123"}'

    mock_client.post.side_effect = [auth_response, api_response]
    mock_client.request.return_value = api_response

    async with AtlasClient(
        base_url="http://localhost:8080/api",
        email="admin@example.com",
        password="admin"
    ) as client:
        client._client = mock_client

        result = await client._request("POST", "/work-orders", json_data={"title": "Test"})

        assert result == {"id": "wo-123"}
        # Should have authenticated first
        assert mock_client.post.call_count >= 1


@pytest.mark.asyncio
async def test_request_refreshes_token_on_401():
    """Test that 401 responses trigger token refresh."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    # Mock auth response
    auth_response = Mock()
    auth_response.status_code = 200
    auth_response.json.return_value = {"token": "new_jwt_123"}

    # First request returns 401, second succeeds
    expired_response = Mock()
    expired_response.status_code = 401

    success_response = Mock()
    success_response.status_code = 200
    success_response.json.return_value = {"id": "wo-123"}
    success_response.content = b'{"id": "wo-123"}'

    mock_client.post.return_value = auth_response
    mock_client.request.side_effect = [expired_response, success_response]

    async with AtlasClient(
        base_url="http://localhost:8080/api",
        email="admin@example.com",
        password="admin"
    ) as client:
        client._client = mock_client

        # Pre-cache an expired token
        await client._token_cache.set_token("old_jwt", ttl_seconds=3600)

        result = await client._request("GET", "/work-orders/123")

        assert result == {"id": "wo-123"}
        # Should have made 2 requests (401, then success)
        assert mock_client.request.call_count == 2


@pytest.mark.asyncio
async def test_request_handles_404():
    """Test that 404 responses raise AtlasNotFoundError."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    # Mock auth response
    auth_response = Mock()
    auth_response.status_code = 200
    auth_response.json.return_value = {"token": "jwt_123"}
    mock_client.post.return_value = auth_response

    # Mock 404 response
    not_found_response = Mock()
    not_found_response.status_code = 404
    mock_client.request.return_value = not_found_response

    async with AtlasClient(
        base_url="http://localhost:8080/api",
        email="admin@example.com",
        password="admin"
    ) as client:
        client._client = mock_client

        with pytest.raises(AtlasNotFoundError, match="Resource not found"):
            await client._request("GET", "/work-orders/999")


@pytest.mark.asyncio
async def test_request_handles_400_validation_error():
    """Test that 400 responses raise AtlasValidationError."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    # Mock auth response
    auth_response = Mock()
    auth_response.status_code = 200
    auth_response.json.return_value = {"token": "jwt_123"}
    mock_client.post.return_value = auth_response

    # Mock 400 response
    validation_response = Mock()
    validation_response.status_code = 400
    validation_response.json.return_value = {"errors": {"title": "Title is required"}}
    validation_response.content = b'{"errors": {"title": "Title is required"}}'
    mock_client.request.return_value = validation_response

    async with AtlasClient(
        base_url="http://localhost:8080/api",
        email="admin@example.com",
        password="admin"
    ) as client:
        client._client = mock_client

        with pytest.raises(AtlasValidationError, match="Validation failed"):
            await client._request("POST", "/work-orders", json_data={})


@pytest.mark.asyncio
async def test_request_handles_429_rate_limit():
    """Test that 429 responses raise AtlasRateLimitError."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    # Mock auth response
    auth_response = Mock()
    auth_response.status_code = 200
    auth_response.json.return_value = {"token": "jwt_123"}
    mock_client.post.return_value = auth_response

    # Mock 429 response
    rate_limit_response = Mock()
    rate_limit_response.status_code = 429
    rate_limit_response.headers = {"Retry-After": "60"}
    mock_client.request.return_value = rate_limit_response

    async with AtlasClient(
        base_url="http://localhost:8080/api",
        email="admin@example.com",
        password="admin"
    ) as client:
        client._client = mock_client

        with pytest.raises(AtlasRateLimitError, match="rate limit exceeded"):
            await client._request("GET", "/work-orders")


@pytest.mark.asyncio
async def test_request_retries_on_network_error():
    """Test that network errors trigger exponential backoff retry."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    # Mock auth response
    auth_response = Mock()
    auth_response.status_code = 200
    auth_response.json.return_value = {"token": "jwt_123"}
    mock_client.post.return_value = auth_response

    # First 2 requests fail with network error, third succeeds
    success_response = Mock()
    success_response.status_code = 200
    success_response.json.return_value = {"id": "wo-123"}
    success_response.content = b'{"id": "wo-123"}'

    mock_client.request.side_effect = [
        httpx.RequestError("Connection failed"),
        httpx.RequestError("Connection failed"),
        success_response
    ]

    async with AtlasClient(
        base_url="http://localhost:8080/api",
        email="admin@example.com",
        password="admin",
        max_retries=3
    ) as client:
        client._client = mock_client

        result = await client._request("GET", "/work-orders/123")

        assert result == {"id": "wo-123"}
        # Should have made 3 requests
        assert mock_client.request.call_count == 3


# ==========================================================================
# AtlasClient API Method Tests
# ==========================================================================

@pytest.mark.asyncio
async def test_create_work_order():
    """Test create_work_order API method."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    async with AtlasClient(
        base_url="http://localhost:8080/api",
        email="admin@example.com",
        password="admin"
    ) as client:
        client._request = AsyncMock(return_value={"id": "wo-123", "title": "Test WO"})

        result = await client.create_work_order({"title": "Test WO"})

        assert result["id"] == "wo-123"
        client._request.assert_called_once_with(
            "POST",
            "/work-orders",
            json_data={"title": "Test WO"}
        )


@pytest.mark.asyncio
async def test_health_check():
    """Test health_check method (no authentication required)."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    # Mock health response
    health_response = Mock()
    health_response.status_code = 200
    health_response.json.return_value = {"status": "UP"}
    health_response.content = b'{"status": "UP"}'
    mock_client.get.return_value = health_response

    async with AtlasClient(
        base_url="http://localhost:8080/api",
        email="admin@example.com",
        password="admin"
    ) as client:
        client._client = mock_client

        result = await client.health_check()

        assert result["status"] == "UP"
        mock_client.get.assert_called_once_with("/health")

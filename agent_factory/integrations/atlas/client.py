"""Async HTTP client for Atlas CMMS API.

This module provides a complete async client for interacting with Atlas CMMS,
including JWT authentication, token caching, automatic token refresh, and
comprehensive error handling with retries.
"""

import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from langsmith import traceable

from .config import atlas_config
from .exceptions import (
    AtlasAuthError,
    AtlasAPIError,
    AtlasNotFoundError,
    AtlasValidationError,
    AtlasRateLimitError,
    AtlasConfigError
)


class AtlasTokenCache:
    """Thread-safe JWT token cache with automatic expiry.

    This class provides a safe way to cache Atlas JWT tokens across multiple
    concurrent requests while respecting token expiration times. It uses
    asyncio locks to prevent race conditions.

    Attributes:
        _token: Cached JWT token string
        _expires_at: Token expiration datetime
        _lock: Asyncio lock for thread-safe access

    Example:
        >>> cache = AtlasTokenCache()
        >>> await cache.set_token("eyJhbGci...", ttl_seconds=86400)
        >>> token = await cache.get_token()
        >>> print(token)  # Returns token if not expired, None otherwise
    """

    def __init__(self):
        """Initialize empty token cache with lock."""
        self._token: Optional[str] = None
        self._expires_at: Optional[datetime] = None
        self._lock = asyncio.Lock()

    async def get_token(self) -> Optional[str]:
        """Get cached token if still valid.

        Returns cached token only if it exists and won't expire within the
        refresh buffer period (default 5 minutes). This prevents mid-request
        token expiration.

        Returns:
            JWT token string if valid, None if expired or not set.
        """
        async with self._lock:
            if self._token and self._expires_at:
                # Check if token is still valid with buffer
                buffer = timedelta(seconds=atlas_config.atlas_token_refresh_buffer)
                if datetime.utcnow() + buffer < self._expires_at:
                    return self._token
            return None

    async def set_token(self, token: str, ttl_seconds: int = None):
        """Cache a new token with expiration time.

        Args:
            token: JWT token string to cache
            ttl_seconds: Token lifetime in seconds (default from config)
        """
        if ttl_seconds is None:
            ttl_seconds = atlas_config.atlas_token_ttl

        async with self._lock:
            self._token = token
            self._expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

    async def clear(self):
        """Clear cached token (force re-authentication on next request)."""
        async with self._lock:
            self._token = None
            self._expires_at = None

    @property
    def is_valid(self) -> bool:
        """Check if token exists and is not expired (with buffer).

        Returns:
            True if token is cached and valid, False otherwise.
        """
        if not self._token or not self._expires_at:
            return False
        buffer = timedelta(seconds=atlas_config.atlas_token_refresh_buffer)
        return datetime.utcnow() + buffer < self._expires_at


class AtlasClient:
    """Async HTTP client for Atlas CMMS API.

    This client provides a high-level interface for all Atlas CMMS operations
    including authentication, work order management, asset management, and user
    management. It handles JWT token caching, automatic refresh, retry logic,
    and comprehensive error handling.

    Features:
        - Automatic JWT authentication and token caching
        - Token refresh on expiration (401 responses)
        - Exponential backoff retry for network errors
        - LangSmith tracing for observability
        - Async context manager support
        - Type-safe API methods

    Example:
        >>> async with AtlasClient() as client:
        ...     work_order = await client.create_work_order({
        ...         "title": "Fix pump",
        ...         "priority": "HIGH"
        ...     })
        ...     print(work_order["id"])
    """

    def __init__(
        self,
        base_url: str = None,
        email: str = None,
        password: str = None,
        timeout: float = None,
        max_retries: int = None
    ):
        """Initialize Atlas client with configuration.

        Args:
            base_url: Atlas API base URL (default from config)
            email: Admin email for auth (default from config)
            password: Admin password (default from config)
            timeout: Request timeout in seconds (default from config)
            max_retries: Max retry attempts (default from config)

        Raises:
            AtlasConfigError: If required configuration is missing
        """
        self.base_url = (base_url or atlas_config.atlas_base_url).rstrip('/')
        self.email = email or atlas_config.atlas_email
        self.password = password or atlas_config.atlas_password
        self.timeout = timeout or atlas_config.atlas_timeout
        self.max_retries = max_retries or atlas_config.atlas_max_retries

        # Validate configuration
        if not self.base_url:
            raise AtlasConfigError("Atlas base URL not configured")
        if not self.email or not self.password:
            raise AtlasConfigError("Atlas credentials not configured")

        self._token_cache = AtlasTokenCache()
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry - creates HTTP client."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"Content-Type": "application/json"}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - closes HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @traceable(name="atlas_authenticate")
    async def _authenticate(self) -> str:
        """Authenticate with Atlas and return JWT token.

        Returns:
            JWT token string

        Raises:
            AtlasAuthError: If authentication fails
            AtlasAPIError: If API communication fails
        """
        try:
            response = await self._client.post(
                "/auth/signin",
                json={"email": self.email, "password": self.password}
            )

            if response.status_code == 401:
                raise AtlasAuthError(
                    "Invalid Atlas credentials",
                    details={"email": self.email}
                )

            response.raise_for_status()
            data = response.json()

            # Extract token from response
            token = data.get("token")
            if not token:
                raise AtlasAuthError(
                    "No token in authentication response",
                    details={"response_keys": list(data.keys())}
                )

            # Cache token
            await self._token_cache.set_token(token)
            return token

        except httpx.HTTPStatusError as e:
            raise AtlasAPIError(
                f"Authentication failed: HTTP {e.response.status_code}",
                details={"status_code": e.response.status_code},
                status_code=e.response.status_code,
                response_body=e.response.text
            )
        except httpx.RequestError as e:
            raise AtlasAPIError(
                f"Network error during authentication: {str(e)}",
                details={"error_type": type(e).__name__}
            )

    @traceable(name="atlas_request")
    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Execute HTTP request with authentication, retry, and error handling.

        This method handles:
        - Token retrieval/refresh
        - Automatic retry on 401 (token expired)
        - Exponential backoff on network errors
        - Comprehensive error mapping

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path (e.g., "/work-orders")
            json_data: Request body as dictionary
            params: Query parameters as dictionary
            retry_count: Current retry attempt (internal use)

        Returns:
            Response JSON as dictionary

        Raises:
            AtlasAuthError: Authentication failed
            AtlasNotFoundError: Resource not found (404)
            AtlasValidationError: Request validation failed (400)
            AtlasRateLimitError: Rate limit exceeded (429)
            AtlasAPIError: Other API errors
        """
        # Get or refresh token
        token = await self._token_cache.get_token()
        if not token:
            token = await self._authenticate()

        try:
            # Execute request
            response = await self._client.request(
                method=method,
                url=endpoint,
                json=json_data,
                params=params,
                headers={"Authorization": f"Bearer {token}"}
            )

            # Handle 401 - token expired, refresh once
            if response.status_code == 401 and retry_count == 0:
                await self._token_cache.clear()
                return await self._request(method, endpoint, json_data, params, retry_count=1)

            # Handle 404 - resource not found
            if response.status_code == 404:
                raise AtlasNotFoundError(
                    f"Resource not found: {method} {endpoint}",
                    details={"endpoint": endpoint, "params": params}
                )

            # Handle 400 - validation error
            if response.status_code == 400:
                error_data = response.json() if response.content else {}
                raise AtlasValidationError(
                    f"Validation failed: {method} {endpoint}",
                    details={"endpoint": endpoint, "response": error_data},
                    field_errors=error_data.get("errors", {})
                )

            # Handle 429 - rate limit
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise AtlasRateLimitError(
                    "Atlas API rate limit exceeded",
                    details={"endpoint": endpoint},
                    retry_after=int(retry_after) if retry_after else None
                )

            # Raise for other HTTP errors
            response.raise_for_status()

            # Return JSON response
            return response.json() if response.content else {}

        except httpx.RequestError as e:
            # Network error - retry with exponential backoff
            if retry_count < self.max_retries:
                wait_time = 2 ** retry_count  # 1s, 2s, 4s
                await asyncio.sleep(wait_time)
                return await self._request(method, endpoint, json_data, params, retry_count + 1)

            raise AtlasAPIError(
                f"Network error after {retry_count + 1} attempts: {str(e)}",
                details={
                    "error_type": type(e).__name__,
                    "endpoint": endpoint,
                    "retries": retry_count
                }
            )

    # ========================================================================
    # Work Order API Methods
    # ========================================================================

    @traceable(name="atlas_create_work_order")
    async def create_work_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new work order in Atlas CMMS.

        Args:
            data: Work order data dictionary with fields:
                - title (required): Work order title
                - description: Detailed description
                - priority: LOW, MEDIUM, HIGH, CRITICAL
                - status: PENDING, IN_PROGRESS, COMPLETED, CANCELLED
                - assignedTo: User ID array
                - assetId: Asset ID (optional)
                - dueDate: ISO 8601 datetime

        Returns:
            Created work order object with ID

        Raises:
            AtlasValidationError: If required fields missing or invalid
            AtlasAPIError: If creation fails
        """
        return await self._request("POST", "/work-orders", json_data=data)

    @traceable(name="atlas_get_work_order")
    async def get_work_order(self, work_order_id: str) -> Dict[str, Any]:
        """Get work order by ID.

        Args:
            work_order_id: Work order ID

        Returns:
            Work order object

        Raises:
            AtlasNotFoundError: If work order doesn't exist
        """
        return await self._request("GET", f"/work-orders/{work_order_id}")

    @traceable(name="atlas_update_work_order")
    async def update_work_order(self, work_order_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing work order.

        Args:
            work_order_id: Work order ID
            updates: Fields to update (partial update)

        Returns:
            Updated work order object

        Raises:
            AtlasNotFoundError: If work order doesn't exist
            AtlasValidationError: If updates are invalid
        """
        return await self._request("PUT", f"/work-orders/{work_order_id}", json_data=updates)

    @traceable(name="atlas_list_work_orders")
    async def list_work_orders(
        self,
        status: Optional[str] = None,
        page: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """List work orders with optional filtering.

        Args:
            status: Filter by status (PENDING, IN_PROGRESS, COMPLETED, CANCELLED)
            page: Page number (0-indexed)
            limit: Results per page (max 100)

        Returns:
            Paginated work order list with metadata
        """
        params = {"page": page, "size": limit}
        if status:
            params["status"] = status
        return await self._request("GET", "/work-orders", params=params)

    @traceable(name="atlas_complete_work_order")
    async def complete_work_order(self, work_order_id: str) -> Dict[str, Any]:
        """Mark work order as completed.

        Args:
            work_order_id: Work order ID

        Returns:
            Updated work order object with COMPLETED status

        Raises:
            AtlasNotFoundError: If work order doesn't exist
        """
        return await self._request("POST", f"/work-orders/{work_order_id}/complete")

    # ========================================================================
    # Asset API Methods
    # ========================================================================

    @traceable(name="atlas_search_assets")
    async def search_assets(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search assets by name or description.

        Args:
            query: Search query string
            limit: Max results to return

        Returns:
            List of matching asset objects
        """
        response = await self._request(
            "POST",
            "/assets/search",
            json_data={"query": query, "limit": limit}
        )
        return response.get("content", [])

    @traceable(name="atlas_get_asset")
    async def get_asset(self, asset_id: str) -> Dict[str, Any]:
        """Get asset by ID.

        Args:
            asset_id: Asset ID

        Returns:
            Asset object

        Raises:
            AtlasNotFoundError: If asset doesn't exist
        """
        return await self._request("GET", f"/assets/{asset_id}")

    # ========================================================================
    # User API Methods
    # ========================================================================

    @traceable(name="atlas_create_user")
    async def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user in Atlas CMMS.

        Args:
            data: User data dictionary with fields:
                - email (required): User email
                - firstName (required): First name
                - lastName (required): Last name
                - password (required): User password
                - role: USER, TECHNICIAN, ADMIN

        Returns:
            Created user object with ID

        Raises:
            AtlasValidationError: If required fields missing or invalid
            AtlasAPIError: If creation fails
        """
        return await self._request("POST", "/users", json_data=data)

    # ========================================================================
    # Health Check
    # ========================================================================

    @traceable(name="atlas_health_check")
    async def health_check(self) -> Dict[str, Any]:
        """Check Atlas CMMS health status (no authentication required).

        Returns:
            Health status object with database and service status

        Example:
            >>> async with AtlasClient() as client:
            ...     health = await client.health_check()
            ...     print(health["status"])  # "UP" if healthy
        """
        # Health endpoint doesn't require authentication
        response = await self._client.get("/health")
        response.raise_for_status()
        return response.json() if response.content else {"status": "UP"}

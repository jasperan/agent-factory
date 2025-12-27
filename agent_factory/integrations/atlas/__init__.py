"""Atlas CMMS integration module.

This module provides a complete async client for Atlas CMMS including
authentication, work order management, asset management, and user management.

Example:
    >>> from agent_factory.integrations.atlas import AtlasClient, atlas_config
    >>> async with AtlasClient() as client:
    ...     work_order = await client.create_work_order({
    ...         "title": "Fix broken pump",
    ...         "priority": "HIGH"
    ...     })
    ...     print(f"Created work order: {work_order['id']}")
"""

from .client import AtlasClient, AtlasTokenCache
from .config import atlas_config, AtlasConfig
from .exceptions import (
    AtlasError,
    AtlasAuthError,
    AtlasAPIError,
    AtlasNotFoundError,
    AtlasValidationError,
    AtlasRateLimitError,
    AtlasConfigError
)

__all__ = [
    # Client
    "AtlasClient",
    "AtlasTokenCache",

    # Configuration
    "atlas_config",
    "AtlasConfig",

    # Exceptions
    "AtlasError",
    "AtlasAuthError",
    "AtlasAPIError",
    "AtlasNotFoundError",
    "AtlasValidationError",
    "AtlasRateLimitError",
    "AtlasConfigError",
]

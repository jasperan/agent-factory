"""
Centralized configuration for all recovery mechanisms.

Provides a single source of truth for configuring all 7 recovery systems:
- HTTP Retry
- Database Failover
- LLM Fallback
- Safety Monitor
- Health Monitoring
- Error Tracking
- Ingestion Monitoring

Configuration can be loaded from:
1. Environment variables (highest priority)
2. Database settings via settings_service (runtime changes)
3. Code defaults (fallback)

Example:
    >>> from agent_factory.recovery import RecoveryConfig
    >>>
    >>> # Use defaults
    >>> config = RecoveryConfig()
    >>>
    >>> # Load from environment variables
    >>> config = RecoveryConfig.from_env()
    >>>
    >>> # Load from database
    >>> config = RecoveryConfig.from_database()
    >>>
    >>> # Custom configuration
    >>> config = RecoveryConfig(
    >>>     http=HTTPRetryConfig(max_attempts=5),
    >>>     safety=SafetyMonitorConfig(max_cost_usd=10.0)
    >>> )
"""

import os
from typing import List, Optional
from pydantic import BaseModel, Field


class HTTPRetryConfig(BaseModel):
    """Configuration for HTTP retry logic."""

    max_attempts: int = Field(
        3,
        description="Maximum number of retry attempts",
        ge=1,
        le=10
    )
    initial_wait: float = Field(
        0.5,
        description="Initial wait time in seconds before first retry",
        ge=0.1,
        le=10.0
    )
    max_wait: float = Field(
        10.0,
        description="Maximum wait time in seconds between retries",
        ge=1.0,
        le=60.0
    )
    exponential_base: float = Field(
        2.0,
        description="Exponential backoff base multiplier",
        ge=1.5,
        le=3.0
    )
    jitter: bool = Field(
        True,
        description="Add random jitter to wait times to prevent thundering herd"
    )
    retry_on: List[str] = Field(
        default_factory=lambda: [
            "timeout",
            "connection_error",
            "rate_limited",
            "server_error"
        ],
        description="Error categories that should trigger retries"
    )


class DatabaseFailoverConfig(BaseModel):
    """Configuration for database failover logic."""

    failover_enabled: bool = Field(
        True,
        description="Enable automatic database failover"
    )
    failover_order: List[str] = Field(
        default_factory=lambda: ["neon", "supabase", "railway", "local"],
        description="Provider failover order (cloud → local)"
    )
    health_check_ttl: int = Field(
        60,
        description="Health check cache TTL in seconds",
        ge=10,
        le=300
    )
    pool_min_size: int = Field(
        2,
        description="Minimum connection pool size per provider",
        ge=1,
        le=10
    )
    pool_max_size: int = Field(
        20,
        description="Maximum connection pool size per provider",
        ge=5,
        le=100
    )
    pool_timeout: float = Field(
        15.0,
        description="Connection pool timeout in seconds",
        ge=5.0,
        le=60.0
    )


class LLMFallbackConfig(BaseModel):
    """Configuration for LLM fallback logic."""

    fallback_enabled: bool = Field(
        True,
        description="Enable LLM fallback on model unavailable"
    )
    max_retries: int = Field(
        3,
        description="Maximum LLM retry attempts",
        ge=1,
        le=5
    )
    retry_delay: float = Field(
        1.0,
        description="Delay in seconds before retrying LLM call",
        ge=0.5,
        le=10.0
    )
    enable_cache: bool = Field(
        False,
        description="Enable LLM response caching (Phase 2 feature)"
    )
    cost_optimization: bool = Field(
        True,
        description="Enable capability-aware routing for cost optimization"
    )


class SafetyMonitorConfig(BaseModel):
    """Configuration for safety monitoring and circuit breaker."""

    max_cost_usd: float = Field(
        5.0,
        description="Maximum cost in USD per session before stopping",
        ge=1.0,
        le=100.0
    )
    max_time_hours: float = Field(
        4.0,
        description="Maximum time in hours per session before stopping",
        ge=0.5,
        le=24.0
    )
    max_consecutive_failures: int = Field(
        3,
        description="Maximum consecutive failures before circuit breaker trips",
        ge=2,
        le=10
    )
    per_issue_timeout_minutes: int = Field(
        30,
        description="Per-issue timeout in minutes",
        ge=5,
        le=120
    )


class HealthMonitorConfig(BaseModel):
    """Configuration for health monitoring."""

    enabled: bool = Field(
        True,
        description="Enable health monitoring for all providers"
    )
    check_interval_minutes: int = Field(
        5,
        description="Interval in minutes between automated health checks",
        ge=1,
        le=60
    )
    telegram_alerts: bool = Field(
        False,
        description="Send Telegram alerts on provider failures"
    )
    alert_on_failure: bool = Field(
        True,
        description="Alert when provider health check fails"
    )


class ErrorTrackingConfig(BaseModel):
    """Configuration for error tracking and categorization."""

    enabled: bool = Field(
        True,
        description="Enable error tracking and categorization"
    )
    alert_threshold: int = Field(
        10,
        description="Alert after N errors in the same category",
        ge=5,
        le=100
    )
    track_per_agent: bool = Field(
        True,
        description="Track errors per agent for pattern detection"
    )
    track_per_provider: bool = Field(
        True,
        description="Track errors per provider (database, LLM, etc.)"
    )


class RecoveryConfig(BaseModel):
    """
    Centralized configuration for all recovery mechanisms.

    Combines configuration for all 7 recovery systems into a single object.
    Supports loading from environment variables, database, or code defaults.

    Example:
        >>> # Use defaults
        >>> config = RecoveryConfig()
        >>>
        >>> # Override specific settings
        >>> config = RecoveryConfig(
        >>>     http=HTTPRetryConfig(max_attempts=5),
        >>>     safety=SafetyMonitorConfig(max_cost_usd=10.0)
        >>> )
        >>>
        >>> # Load from environment
        >>> config = RecoveryConfig.from_env()
        >>>
        >>> # Load from database
        >>> config = RecoveryConfig.from_database()
    """

    http: HTTPRetryConfig = Field(
        default_factory=HTTPRetryConfig,
        description="HTTP retry configuration"
    )
    database: DatabaseFailoverConfig = Field(
        default_factory=DatabaseFailoverConfig,
        description="Database failover configuration"
    )
    llm: LLMFallbackConfig = Field(
        default_factory=LLMFallbackConfig,
        description="LLM fallback configuration"
    )
    safety: SafetyMonitorConfig = Field(
        default_factory=SafetyMonitorConfig,
        description="Safety monitor configuration"
    )
    health: HealthMonitorConfig = Field(
        default_factory=HealthMonitorConfig,
        description="Health monitor configuration"
    )
    errors: ErrorTrackingConfig = Field(
        default_factory=ErrorTrackingConfig,
        description="Error tracking configuration"
    )

    @classmethod
    def from_env(cls) -> "RecoveryConfig":
        """
        Load configuration from environment variables.

        Environment variables use the pattern: RECOVERY_<SYSTEM>_<SETTING>

        Example:
            RECOVERY_HTTP_MAX_ATTEMPTS=5
            RECOVERY_DB_FAILOVER_ORDER=neon,local
            RECOVERY_SAFETY_MAX_COST=10.0

        Returns:
            RecoveryConfig instance with environment variable overrides
        """
        # HTTP Retry
        http_config = HTTPRetryConfig(
            max_attempts=int(os.getenv("RECOVERY_HTTP_MAX_ATTEMPTS", "3")),
            initial_wait=float(os.getenv("RECOVERY_HTTP_INITIAL_WAIT", "0.5")),
            max_wait=float(os.getenv("RECOVERY_HTTP_MAX_WAIT", "10.0")),
            exponential_base=float(os.getenv("RECOVERY_HTTP_EXPONENTIAL_BASE", "2.0")),
            jitter=os.getenv("RECOVERY_HTTP_JITTER", "true").lower() == "true",
            retry_on=os.getenv(
                "RECOVERY_HTTP_RETRY_ON",
                "timeout,connection_error,rate_limited,server_error"
            ).split(",")
        )

        # Database Failover
        database_config = DatabaseFailoverConfig(
            failover_enabled=os.getenv("RECOVERY_DB_FAILOVER_ENABLED", "true").lower() == "true",
            failover_order=os.getenv(
                "RECOVERY_DB_FAILOVER_ORDER",
                "neon,supabase,railway,local"
            ).split(","),
            health_check_ttl=int(os.getenv("RECOVERY_DB_HEALTH_CHECK_TTL", "60")),
            pool_min_size=int(os.getenv("RECOVERY_DB_POOL_MIN_SIZE", "2")),
            pool_max_size=int(os.getenv("RECOVERY_DB_POOL_MAX_SIZE", "20")),
            pool_timeout=float(os.getenv("RECOVERY_DB_POOL_TIMEOUT", "15.0"))
        )

        # LLM Fallback
        llm_config = LLMFallbackConfig(
            fallback_enabled=os.getenv("RECOVERY_LLM_FALLBACK_ENABLED", "true").lower() == "true",
            max_retries=int(os.getenv("RECOVERY_LLM_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("RECOVERY_LLM_RETRY_DELAY", "1.0")),
            enable_cache=os.getenv("RECOVERY_LLM_ENABLE_CACHE", "false").lower() == "true",
            cost_optimization=os.getenv("RECOVERY_LLM_COST_OPTIMIZATION", "true").lower() == "true"
        )

        # Safety Monitor
        safety_config = SafetyMonitorConfig(
            max_cost_usd=float(os.getenv("RECOVERY_SAFETY_MAX_COST", "5.0")),
            max_time_hours=float(os.getenv("RECOVERY_SAFETY_MAX_TIME_HOURS", "4.0")),
            max_consecutive_failures=int(os.getenv("RECOVERY_SAFETY_MAX_FAILURES", "3")),
            per_issue_timeout_minutes=int(os.getenv("RECOVERY_SAFETY_PER_ISSUE_TIMEOUT", "30"))
        )

        # Health Monitor
        health_config = HealthMonitorConfig(
            enabled=os.getenv("RECOVERY_HEALTH_ENABLED", "true").lower() == "true",
            check_interval_minutes=int(os.getenv("RECOVERY_HEALTH_CHECK_INTERVAL", "5")),
            telegram_alerts=os.getenv("RECOVERY_HEALTH_TELEGRAM_ALERTS", "false").lower() == "true",
            alert_on_failure=os.getenv("RECOVERY_HEALTH_ALERT_ON_FAILURE", "true").lower() == "true"
        )

        # Error Tracking
        errors_config = ErrorTrackingConfig(
            enabled=os.getenv("RECOVERY_ERRORS_ENABLED", "true").lower() == "true",
            alert_threshold=int(os.getenv("RECOVERY_ERRORS_ALERT_THRESHOLD", "10")),
            track_per_agent=os.getenv("RECOVERY_ERRORS_TRACK_PER_AGENT", "true").lower() == "true",
            track_per_provider=os.getenv("RECOVERY_ERRORS_TRACK_PER_PROVIDER", "true").lower() == "true"
        )

        return cls(
            http=http_config,
            database=database_config,
            llm=llm_config,
            safety=safety_config,
            health=health_config,
            errors=errors_config
        )

    @classmethod
    def from_database(cls) -> "RecoveryConfig":
        """
        Load configuration from database via settings_service.

        Queries settings_service for all recovery.* keys and builds config.

        Example:
            >>> from agent_factory.core.settings_service import settings
            >>> settings.set("recovery.http.max_attempts", "5", category="recovery")
            >>> config = RecoveryConfig.from_database()

        Returns:
            RecoveryConfig instance with database overrides

        Raises:
            ImportError: If settings_service not available
            Exception: If database query fails
        """
        try:
            from agent_factory.core.settings_service import settings
        except ImportError:
            # Fallback to defaults if settings_service unavailable
            return cls()

        # Load HTTP config
        http_config = HTTPRetryConfig(
            max_attempts=settings.get_int("max_attempts", default=3, category="recovery.http"),
            initial_wait=settings.get_float("initial_wait", default=0.5, category="recovery.http"),
            max_wait=settings.get_float("max_wait", default=10.0, category="recovery.http"),
            exponential_base=settings.get_float("exponential_base", default=2.0, category="recovery.http"),
            jitter=settings.get_bool("jitter", default=True, category="recovery.http"),
            retry_on=settings.get("retry_on", default="timeout,connection_error,rate_limited,server_error", category="recovery.http").split(",")
        )

        # Load Database config
        database_config = DatabaseFailoverConfig(
            failover_enabled=settings.get_bool("failover_enabled", default=True, category="recovery.database"),
            failover_order=settings.get("failover_order", default="neon,supabase,railway,local", category="recovery.database").split(","),
            health_check_ttl=settings.get_int("health_check_ttl", default=60, category="recovery.database"),
            pool_min_size=settings.get_int("pool_min_size", default=2, category="recovery.database"),
            pool_max_size=settings.get_int("pool_max_size", default=20, category="recovery.database"),
            pool_timeout=settings.get_float("pool_timeout", default=15.0, category="recovery.database")
        )

        # Load LLM config
        llm_config = LLMFallbackConfig(
            fallback_enabled=settings.get_bool("fallback_enabled", default=True, category="recovery.llm"),
            max_retries=settings.get_int("max_retries", default=3, category="recovery.llm"),
            retry_delay=settings.get_float("retry_delay", default=1.0, category="recovery.llm"),
            enable_cache=settings.get_bool("enable_cache", default=False, category="recovery.llm"),
            cost_optimization=settings.get_bool("cost_optimization", default=True, category="recovery.llm")
        )

        # Load Safety config
        safety_config = SafetyMonitorConfig(
            max_cost_usd=settings.get_float("max_cost_usd", default=5.0, category="recovery.safety"),
            max_time_hours=settings.get_float("max_time_hours", default=4.0, category="recovery.safety"),
            max_consecutive_failures=settings.get_int("max_consecutive_failures", default=3, category="recovery.safety"),
            per_issue_timeout_minutes=settings.get_int("per_issue_timeout_minutes", default=30, category="recovery.safety")
        )

        # Load Health config
        health_config = HealthMonitorConfig(
            enabled=settings.get_bool("enabled", default=True, category="recovery.health"),
            check_interval_minutes=settings.get_int("check_interval_minutes", default=5, category="recovery.health"),
            telegram_alerts=settings.get_bool("telegram_alerts", default=False, category="recovery.health"),
            alert_on_failure=settings.get_bool("alert_on_failure", default=True, category="recovery.health")
        )

        # Load Errors config
        errors_config = ErrorTrackingConfig(
            enabled=settings.get_bool("enabled", default=True, category="recovery.errors"),
            alert_threshold=settings.get_int("alert_threshold", default=10, category="recovery.errors"),
            track_per_agent=settings.get_bool("track_per_agent", default=True, category="recovery.errors"),
            track_per_provider=settings.get_bool("track_per_provider", default=True, category="recovery.errors")
        )

        return cls(
            http=http_config,
            database=database_config,
            llm=llm_config,
            safety=safety_config,
            health=health_config,
            errors=errors_config
        )

    def reload(self):
        """
        Reload configuration from database.

        Useful for picking up runtime configuration changes without restart.

        Example:
            >>> config = RecoveryConfig.from_database()
            >>> # ... configuration changed in database ...
            >>> config.reload()  # Pick up new settings
        """
        new_config = self.from_database()

        self.http = new_config.http
        self.database = new_config.database
        self.llm = new_config.llm
        self.safety = new_config.safety
        self.health = new_config.health
        self.errors = new_config.errors

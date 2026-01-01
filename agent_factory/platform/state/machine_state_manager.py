"""
Machine State Manager for Factory.io Polling & Caching

Provides background polling of Factory.io I/O tags with circuit breaker,
change detection, and subscription-based notifications.

Usage:
    from agent_factory.platform.state.machine_state_manager import MachineStateManager
    from agent_factory.platform.config import load_machine_config

    # Initialize with machine configurations
    config = load_machine_config()
    manager = MachineStateManager(config.machines)

    # Start polling (in FastAPI lifespan)
    await manager.start()

    # Subscribe to state changes
    async def my_callback(machine_id: str, changed_tags: List[IOTagStatus]):
        for tag in changed_tags:
            print(f"{tag.tag_name} changed to {tag.value}")

    sub_id = manager.subscribe("scene1_sorting", my_callback)

    # Query current state
    state = manager.get_state("scene1_sorting")

    # Stop polling (in FastAPI shutdown)
    await manager.stop()
"""

import asyncio
import json
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Awaitable, Callable, Dict, List, Optional, Set

from agent_factory.platform.config import MachineConfig
from agent_factory.platform.types import IOTagStatus
from agent_factory.tools.factoryio.readwrite_tool import FactoryIOReadWriteTool

logger = logging.getLogger(__name__)


# ============================================================================
# Circuit Breaker (Resilience Pattern)
# ============================================================================


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # Too many failures, backoff active
    HALF_OPEN = "half_open"    # Testing recovery


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for Factory.io connection resilience.

    Implements the Circuit Breaker pattern to prevent hammering a dead service:
    - CLOSED: Normal operation, allows polling
    - OPEN: Too many failures, exponential backoff (5s → 10s → 20s → 30s max)
    - HALF_OPEN: Testing recovery, allows ONE poll attempt

    Attributes:
        failure_threshold: Number of consecutive failures before opening circuit
        backoff_base_seconds: Initial backoff time when circuit opens
        backoff_max_seconds: Maximum backoff time (cap for exponential growth)
        state: Current circuit state
        failure_count: Consecutive failures counter
        last_failure_time: Timestamp of last failure
        current_backoff_seconds: Current backoff duration
    """
    failure_threshold: int = 3
    backoff_base_seconds: int = 5
    backoff_max_seconds: int = 30

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    current_backoff_seconds: int = field(default=0)  # Will be set in __post_init__

    def __post_init__(self):
        """Initialize current_backoff_seconds to backoff_base_seconds if not set."""
        if self.current_backoff_seconds == 0:
            self.current_backoff_seconds = self.backoff_base_seconds

    def should_attempt_poll(self) -> bool:
        """
        Check if polling should be attempted.

        Returns:
            True if polling is allowed (CLOSED or backoff expired)
        """
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if backoff period has elapsed
            if self._backoff_elapsed():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker transitioning to HALF_OPEN (testing recovery)")
                return True
            return False

        # HALF_OPEN: allow ONE test poll
        return True

    def record_success(self) -> None:
        """
        Record successful poll - reset circuit to CLOSED.

        Doubles backoff timeout as penalty for flapping (if circuit was open).
        This means: "You recovered, but if you fail again, longer timeout."
        """
        if self.state != CircuitState.CLOSED:
            logger.info(f"Circuit breaker recovered: {self.state.value} → CLOSED")

            # Double backoff for next failure cycle (penalty for flapping)
            self.current_backoff_seconds = min(
                self.current_backoff_seconds * 2,
                self.backoff_max_seconds
            )

        self.state = CircuitState.CLOSED
        self.failure_count = 0

    def record_failure(self) -> None:
        """
        Record failed poll - may open circuit.

        Increments failure count. If threshold reached, opens circuit.
        Backoff time is set during recovery (record_success), not here.
        """
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

            logger.warning(
                f"Circuit breaker OPEN after {self.failure_count} failures "
                f"(backoff: {self.current_backoff_seconds}s)"
            )
        else:
            logger.warning(
                f"Circuit breaker failure {self.failure_count}/{self.failure_threshold}"
            )

    def _backoff_elapsed(self) -> bool:
        """
        Check if backoff period has elapsed.

        Returns:
            True if enough time has passed since last failure
        """
        if not self.last_failure_time:
            return True

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.current_backoff_seconds


# ============================================================================
# Machine State (Change Detection)
# ============================================================================


@dataclass
class MachineState:
    """
    Caches current I/O state for a single machine with change detection.

    Attributes:
        machine_id: Unique machine identifier
        current_state: Dict of tag_name → IOTagStatus (cached values)
        circuit_breaker: Circuit breaker instance for this machine
    """
    machine_id: str
    current_state: Dict[str, IOTagStatus] = field(default_factory=dict)
    circuit_breaker: CircuitBreaker = field(default_factory=CircuitBreaker)

    def get_changed_tags(self, new_tags: List[IOTagStatus]) -> List[IOTagStatus]:
        """
        Compare new tags with cached state, return only changed tags.

        First poll: All tags are considered "changed" (initial state)
        Subsequent polls: Only tags with value changes are returned

        Args:
            new_tags: New tag values from Factory.io

        Returns:
            List of tags that changed (or are new)
        """
        changed = []

        for tag in new_tags:
            cached = self.current_state.get(tag.tag_name)

            # New tag (first poll)
            if cached is None:
                changed.append(tag)
                self.current_state[tag.tag_name] = tag
                continue

            # Value changed
            if cached.value != tag.value:
                changed.append(tag)
                self.current_state[tag.tag_name] = tag

        return changed


# ============================================================================
# Subscription (Observer Pattern)
# ============================================================================


@dataclass
class Subscription:
    """
    Observer pattern subscription for state change notifications.

    Attributes:
        subscription_id: Unique identifier for this subscription
        machine_id: Machine this subscription is for
        callback: Async function to call on state change
        tag_filter: Optional set of tag names to filter (None = all tags)
    """
    subscription_id: str
    machine_id: str
    callback: Callable[[str, List[IOTagStatus]], Awaitable[None]]
    tag_filter: Optional[Set[str]] = None

    async def notify(self, changed_tags: List[IOTagStatus]) -> None:
        """
        Call subscriber callback with changed tags.

        Filters tags if tag_filter is set.
        Catches and logs errors to prevent one bad callback from crashing others.

        Args:
            changed_tags: List of tags that changed
        """
        try:
            # Filter tags if specified
            if self.tag_filter:
                filtered_tags = [
                    tag for tag in changed_tags
                    if tag.tag_name in self.tag_filter
                ]
            else:
                filtered_tags = changed_tags

            # Only notify if there are relevant changes
            if filtered_tags:
                await self.callback(self.machine_id, filtered_tags)

        except Exception as e:
            logger.error(
                f"Subscription callback failed (sub_id={self.subscription_id}): {e}",
                exc_info=True
            )


# ============================================================================
# Machine State Manager (Main Orchestrator)
# ============================================================================


class MachineStateManager:
    """
    Main orchestrator for Factory.io background polling and state management.

    Manages background polling for multiple machines, with per-machine:
    - Circuit breaker for resilience
    - State caching with change detection
    - Subscription-based notifications

    Features:
    - Async background polling (doesn't block FastAPI)
    - ThreadPoolExecutor for sync tool calls (4 workers)
    - Graceful shutdown (cancels all tasks)
    - Per-machine poll intervals (configurable)

    Usage:
        manager = MachineStateManager(machines)
        await manager.start()  # Start background polling
        sub_id = manager.subscribe("scene1_sorting", my_callback)
        state = manager.get_state("scene1_sorting")
        await manager.stop()  # Stop polling, cleanup
    """

    def __init__(self, machines: List[MachineConfig]):
        """
        Initialize state manager with machine configurations.

        Args:
            machines: List of MachineConfig objects
        """
        self.machines = {m.machine_id: m for m in machines}
        self.states: Dict[str, MachineState] = {}
        self.subscriptions: Dict[str, List[Subscription]] = defaultdict(list)
        self.polling_tasks: Dict[str, asyncio.Task] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.running = False

        # Initialize Factory.io tools
        self.readwrite_tool = FactoryIOReadWriteTool()

        # Initialize state for each machine
        for machine_id in self.machines:
            self.states[machine_id] = MachineState(machine_id=machine_id)
            self.subscriptions[machine_id] = []

        logger.info(f"MachineStateManager initialized with {len(machines)} machine(s)")

    async def start(self) -> None:
        """
        Start background polling for all machines.

        Creates one asyncio.Task per machine that polls Factory.io
        at the configured interval.
        """
        if self.running:
            logger.warning("MachineStateManager already running")
            return

        self.running = True

        for machine_id, config in self.machines.items():
            task = asyncio.create_task(
                self._polling_loop(machine_id, config),
                name=f"poll_{machine_id}"
            )
            self.polling_tasks[machine_id] = task
            logger.info(
                f"Started polling for {machine_id} "
                f"(interval: {config.poll_interval_seconds}s)"
            )

        logger.info(f"MachineStateManager started ({len(self.polling_tasks)} task(s))")

    async def stop(self) -> None:
        """
        Stop all polling tasks and cleanup.

        Cancels all background tasks, waits for them to finish,
        and shuts down the ThreadPoolExecutor.
        """
        if not self.running:
            logger.warning("MachineStateManager not running")
            return

        self.running = False

        # Cancel all tasks
        for machine_id, task in self.polling_tasks.items():
            task.cancel()
            logger.info(f"Stopping polling for {machine_id}")

        # Wait for cancellation
        await asyncio.gather(*self.polling_tasks.values(), return_exceptions=True)

        # Shutdown executor
        self.executor.shutdown(wait=True)

        logger.info("MachineStateManager stopped")

    async def _polling_loop(self, machine_id: str, config: MachineConfig) -> None:
        """
        Background polling loop for one machine.

        Polls Factory.io at configured interval, detects changes,
        notifies subscribers, and updates circuit breaker.

        Args:
            machine_id: Machine to poll
            config: Machine configuration
        """
        state = self.states[machine_id]
        poll_interval = config.poll_interval_seconds

        logger.info(
            f"Polling loop started for {machine_id} "
            f"(interval: {poll_interval}s)"
        )

        while self.running:
            try:
                # Check circuit breaker
                if not state.circuit_breaker.should_attempt_poll():
                    await asyncio.sleep(1)  # Short sleep, check again
                    continue

                # Read tags from Factory.io (async wrapper around sync tool)
                new_tags = await self._read_tags_async(config)

                # Detect changes
                changed_tags = state.get_changed_tags(new_tags)

                # Notify subscribers (if changes detected)
                if changed_tags:
                    logger.debug(
                        f"{machine_id}: {len(changed_tags)} tag(s) changed"
                    )
                    await self._notify_subscribers(machine_id, changed_tags)

                # Record success
                state.circuit_breaker.record_success()

            except asyncio.CancelledError:
                # Task cancelled during shutdown
                logger.info(f"Polling loop cancelled for {machine_id}")
                break

            except Exception as e:
                logger.error(
                    f"Polling failed for {machine_id}: {e}",
                    exc_info=True
                )
                state.circuit_breaker.record_failure()

            # Sleep until next poll
            await asyncio.sleep(poll_interval)

        logger.info(f"Polling loop stopped for {machine_id}")

    async def _read_tags_async(self, config: MachineConfig) -> List[IOTagStatus]:
        """
        Read tags from Factory.io (async wrapper around sync tool).

        Uses ThreadPoolExecutor to avoid blocking event loop.

        Args:
            config: Machine configuration

        Returns:
            List of IOTagStatus objects with current values

        Raises:
            Exception: If Factory.io returns error
        """
        # Collect all tag names (inputs + outputs)
        tag_names = []
        for tag_config in config.monitored_inputs:
            tag_names.append(tag_config.tag)
        for tag_config in config.controllable_outputs:
            tag_names.append(tag_config.tag)

        if not tag_names:
            logger.warning(f"No tags configured for {config.machine_id}")
            return []

        # Call sync tool in executor
        loop = asyncio.get_event_loop()
        result_json = await loop.run_in_executor(
            self.executor,
            self.readwrite_tool._run,
            "read",
            tag_names,
            None
        )

        # Parse result
        if result_json.startswith("ERROR:"):
            raise Exception(f"Factory.io error: {result_json}")

        result = json.loads(result_json)
        if not result.get("success"):
            errors = result.get("errors", [])
            raise Exception(f"Factory.io returned errors: {errors}")

        # Convert to IOTagStatus objects
        values = result["values"]
        tags = []

        for tag_name, value in values.items():
            # Determine tag type (Input or Output)
            tag_type = "Output"  # Default

            for tag_config in config.monitored_inputs:
                if tag_config.tag == tag_name:
                    tag_type = "Input"
                    break

            tags.append(IOTagStatus(
                tag_name=tag_name,
                value=value,
                tag_type=tag_type
            ))

        return tags

    async def _notify_subscribers(
        self,
        machine_id: str,
        changed_tags: List[IOTagStatus]
    ) -> None:
        """
        Notify all subscribers for this machine.

        Calls all subscription callbacks in parallel with error isolation.

        Args:
            machine_id: Machine that changed
            changed_tags: List of tags that changed
        """
        subs = self.subscriptions.get(machine_id, [])
        if not subs:
            return

        # Notify all in parallel (with error isolation)
        await asyncio.gather(
            *[sub.notify(changed_tags) for sub in subs],
            return_exceptions=True
        )

    def subscribe(
        self,
        machine_id: str,
        callback: Callable[[str, List[IOTagStatus]], Awaitable[None]],
        tag_filter: Optional[Set[str]] = None
    ) -> str:
        """
        Subscribe to state changes for a machine.

        Args:
            machine_id: Machine to subscribe to
            callback: async def(machine_id, changed_tags)
            tag_filter: Optional set of tag names to filter (None = all tags)

        Returns:
            Subscription ID (for unsubscribe)

        Raises:
            ValueError: If machine_id not found
        """
        if machine_id not in self.machines:
            raise ValueError(f"Unknown machine_id: {machine_id}")

        sub_id = f"{machine_id}_{len(self.subscriptions[machine_id])}"
        sub = Subscription(
            subscription_id=sub_id,
            machine_id=machine_id,
            callback=callback,
            tag_filter=tag_filter
        )
        self.subscriptions[machine_id].append(sub)

        logger.info(
            f"Added subscription {sub_id} "
            f"(filter: {tag_filter if tag_filter else 'all'})"
        )

        return sub_id

    def unsubscribe(self, subscription_id: str) -> None:
        """
        Remove a subscription.

        Args:
            subscription_id: Subscription ID returned from subscribe()
        """
        for machine_id, subs in self.subscriptions.items():
            original_count = len(subs)
            self.subscriptions[machine_id] = [
                s for s in subs if s.subscription_id != subscription_id
            ]
            if len(self.subscriptions[machine_id]) < original_count:
                logger.info(f"Removed subscription {subscription_id}")
                return

        logger.warning(f"Subscription not found: {subscription_id}")

    def get_state(self, machine_id: str) -> Optional[Dict[str, IOTagStatus]]:
        """
        Get current cached state for a machine.

        Args:
            machine_id: Machine identifier

        Returns:
            Dict of tag_name → IOTagStatus, or None if machine not found
        """
        state = self.states.get(machine_id)
        return state.current_state if state else None

    def is_healthy(self, machine_id: str) -> bool:
        """
        Check if machine circuit is CLOSED (healthy).

        Args:
            machine_id: Machine identifier

        Returns:
            True if circuit is CLOSED (polling normally), False otherwise
        """
        state = self.states.get(machine_id)
        if not state:
            return False

        return state.circuit_breaker.state == CircuitState.CLOSED

    def get_all_states(self) -> Dict[str, Dict[str, IOTagStatus]]:
        """
        Get current cached state for all machines.

        Returns:
            Dict of machine_id → {tag_name → IOTagStatus}
        """
        return {
            machine_id: state.current_state
            for machine_id, state in self.states.items()
        }

    def get_health_status(self) -> Dict[str, Dict[str, any]]:
        """
        Get health status for all machines.

        Returns:
            Dict with per-machine health info:
            {
                "machine_id": {
                    "state": "CLOSED" | "OPEN" | "HALF_OPEN",
                    "failure_count": int,
                    "backoff_seconds": int,
                    "tag_count": int
                }
            }
        """
        health = {}

        for machine_id, state in self.states.items():
            cb = state.circuit_breaker
            health[machine_id] = {
                "state": cb.state.value,
                "failure_count": cb.failure_count,
                "backoff_seconds": cb.current_backoff_seconds,
                "tag_count": len(state.current_state)
            }

        return health

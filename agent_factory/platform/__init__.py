"""
Platform Layer - Universal Abstraction for Factory.io Integration

Provides platform-agnostic interfaces for:
- State management (polling, caching, subscriptions)
- Message formatting (Telegram, WhatsApp, Slack, etc.)
- Configuration (YAML-based machine definitions)

Usage:
    from agent_factory.platform.types import IOTagStatus, ControlButton
    from agent_factory.platform.state.machine_state_manager import MachineStateManager
    from agent_factory.platform.adapters.telegram_adapter import TelegramAdapter
"""

__version__ = "2.0.0"

"""
Workers module - Specialized AI workers for the Agent Factory.

This module contains integrations with external AI coding agents and services
that can be used as specialized workers in multi-agent workflows.

Available Workers:
    - OpenHandsWorker: AI coding agent for autonomous software development tasks
"""

from agent_factory.workers.openhands_worker import OpenHandsWorker

__all__ = ["OpenHandsWorker"]

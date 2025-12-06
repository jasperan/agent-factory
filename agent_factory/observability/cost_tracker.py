"""
Cost Tracker - Track API costs across LLM providers

Calculates and tracks costs for agent requests across different
LLM providers (OpenAI, Anthropic, Google) based on token usage.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime


class CostTracker:
    """
    Track API costs across providers.

    Calculates costs based on token usage and provider pricing.
    Supports OpenAI, Anthropic, and Google pricing models.

    Attributes:
        total_cost: Total cost across all requests (USD)
        costs_by_agent: Cost breakdown by agent name
        costs_by_provider: Cost breakdown by LLM provider
        costs_by_model: Cost breakdown by model name
        request_costs: List of individual request costs

    Example:
        >>> tracker = CostTracker()
        >>> tracker.record_cost(
        ...     agent_name="research",
        ...     provider="openai",
        ...     model="gpt-4o",
        ...     prompt_tokens=1000,
        ...     completion_tokens=500
        ... )
        >>> print(f"Total cost: ${tracker.total_cost:.4f}")
        >>> summary = tracker.summary()
    """

    # Pricing per 1K tokens (USD)
    # Updated as of December 2025
    PRICING = {
        "openai": {
            "gpt-4o": {"input": 0.0025, "output": 0.01},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "gpt-3.5-turbo-16k": {"input": 0.001, "output": 0.002}
        },
        "anthropic": {
            "claude-sonnet-4": {"input": 0.003, "output": 0.015},
            "claude-opus-4": {"input": 0.015, "output": 0.075},
            "claude-haiku-3": {"input": 0.00025, "output": 0.00125},
            "claude-sonnet-3.5": {"input": 0.003, "output": 0.015}
        },
        "google": {
            "gemini-pro": {"input": 0.00025, "output": 0.0005},
            "gemini-pro-vision": {"input": 0.00025, "output": 0.0005},
            "gemini-ultra": {"input": 0.00125, "output": 0.00375}
        }
    }

    def __init__(self):
        """Initialize cost tracker with zero costs."""
        self.total_cost: float = 0.0
        self.costs_by_agent: Dict[str, float] = {}
        self.costs_by_provider: Dict[str, float] = {}
        self.costs_by_model: Dict[str, float] = {}
        self.request_costs: list = []

    def calculate_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        Calculate cost for a request.

        Args:
            provider: LLM provider (openai, anthropic, google)
            model: Model name (gpt-4o, claude-sonnet-4, etc.)
            prompt_tokens: Number of prompt/input tokens
            completion_tokens: Number of completion/output tokens

        Returns:
            Cost in USD

        Example:
            >>> cost = tracker.calculate_cost("openai", "gpt-4o", 1000, 500)
            >>> # 1K * 0.0025 + 0.5K * 0.01 = 0.0025 + 0.005 = 0.0075
            >>> print(f"${cost:.4f}")
            $0.0075
        """
        if provider not in self.PRICING:
            return 0.0

        model_pricing = self.PRICING[provider].get(model)
        if not model_pricing:
            # Try to find partial match (e.g., "gpt-4" matches "gpt-4o")
            for model_key, pricing in self.PRICING[provider].items():
                if model_key in model or model in model_key:
                    model_pricing = pricing
                    break

        if not model_pricing:
            return 0.0

        # Calculate costs per 1K tokens
        input_cost = (prompt_tokens / 1000) * model_pricing["input"]
        output_cost = (completion_tokens / 1000) * model_pricing["output"]

        return input_cost + output_cost

    def record_cost(
        self,
        agent_name: str,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Record cost for a request.

        Args:
            agent_name: Name of agent that made the request
            provider: LLM provider
            model: Model name
            prompt_tokens: Prompt tokens used
            completion_tokens: Completion tokens used
            metadata: Optional additional context

        Returns:
            Cost for this request (USD)

        Example:
            >>> cost = tracker.record_cost(
            ...     agent_name="coding",
            ...     provider="openai",
            ...     model="gpt-4o",
            ...     prompt_tokens=2000,
            ...     completion_tokens=1000
            ... )
        """
        cost = self.calculate_cost(provider, model, prompt_tokens, completion_tokens)

        # Update totals
        self.total_cost += cost
        self.costs_by_agent[agent_name] = self.costs_by_agent.get(agent_name, 0.0) + cost
        self.costs_by_provider[provider] = self.costs_by_provider.get(provider, 0.0) + cost
        self.costs_by_model[model] = self.costs_by_model.get(model, 0.0) + cost

        # Record individual request
        self.request_costs.append({
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent_name,
            "provider": provider,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost_usd": cost,
            "metadata": metadata or {}
        })

        return cost

    def get_agent_cost(self, agent_name: str) -> float:
        """
        Get total cost for a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Total cost for that agent (USD)

        Example:
            >>> cost = tracker.get_agent_cost("research")
            >>> print(f"Research agent cost: ${cost:.4f}")
        """
        return self.costs_by_agent.get(agent_name, 0.0)

    def get_provider_cost(self, provider: str) -> float:
        """Get total cost for a specific provider."""
        return self.costs_by_provider.get(provider, 0.0)

    def get_model_cost(self, model: str) -> float:
        """Get total cost for a specific model."""
        return self.costs_by_model.get(model, 0.0)

    def summary(self) -> Dict[str, Any]:
        """
        Get comprehensive cost summary.

        Returns:
            Dictionary with cost breakdowns

        Example:
            >>> summary = tracker.summary()
            >>> print(f"Total: {summary['total_cost_usd']}")
            >>> for agent, cost in summary['by_agent'].items():
            ...     print(f"{agent}: {cost}")
        """
        return {
            "total_cost_usd": f"${self.total_cost:.4f}",
            "total_requests": len(self.request_costs),
            "avg_cost_per_request": f"${(self.total_cost / len(self.request_costs)):.4f}"
            if self.request_costs else "$0.0000",
            "by_agent": {
                name: f"${cost:.4f}"
                for name, cost in sorted(
                    self.costs_by_agent.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            },
            "by_provider": {
                name: f"${cost:.4f}"
                for name, cost in sorted(
                    self.costs_by_provider.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            },
            "by_model": {
                name: f"${cost:.4f}"
                for name, cost in sorted(
                    self.costs_by_model.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            }
        }

    def reset(self) -> None:
        """
        Reset all cost tracking.

        Useful for starting a new measurement period.

        Example:
            >>> tracker.reset()
            >>> tracker.total_cost
            0.0
        """
        self.total_cost = 0.0
        self.costs_by_agent.clear()
        self.costs_by_provider.clear()
        self.costs_by_model.clear()
        self.request_costs.clear()

    def export_request_costs(self) -> list:
        """
        Export individual request costs.

        Returns:
            List of request cost dictionaries

        Example:
            >>> import json
            >>> costs_json = json.dumps(tracker.export_request_costs(), indent=2)
        """
        return self.request_costs.copy()

    def get_top_agents_by_cost(self, n: int = 5) -> list:
        """
        Get top N agents by cost.

        Args:
            n: Number of agents to return

        Returns:
            List of (agent_name, cost) tuples

        Example:
            >>> top_agents = tracker.get_top_agents_by_cost(3)
            >>> for agent, cost in top_agents:
            ...     print(f"{agent}: ${cost:.4f}")
        """
        return sorted(
            self.costs_by_agent.items(),
            key=lambda x: x[1],
            reverse=True
        )[:n]

    def estimate_monthly_cost(self, days_of_data: int = 1) -> float:
        """
        Estimate monthly cost based on current usage.

        Args:
            days_of_data: Number of days of data collected

        Returns:
            Estimated monthly cost (USD)

        Example:
            >>> # After 1 day of usage
            >>> monthly = tracker.estimate_monthly_cost(days_of_data=1)
            >>> print(f"Estimated monthly: ${monthly:.2f}")
        """
        if days_of_data <= 0:
            return 0.0

        daily_avg = self.total_cost / days_of_data
        return daily_avg * 30  # 30 days in month

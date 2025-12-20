"""
LangChain Adapter - Bridge LLMRouter to LangChain ChatModel Interface

Wraps LLMRouter in LangChain-compatible ChatModel interface, enabling
intelligent cost-optimized routing within LangChain agents.

Part of Phase 2: Cost-Optimized Model Routing
"""

from typing import Any, Dict, List, Optional, Iterator, ClassVar
import os

try:
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
    from langchain_core.outputs import ChatGeneration, ChatResult
    from langchain_core.callbacks import CallbackManagerForLLMRun
except ImportError:
    raise ImportError(
        "LangChain not installed. Run: poetry add langchain langchain-core"
    )

from .router import LLMRouter
from .types import LLMConfig, LLMProvider, ModelCapability, LLMResponse
from .config import get_cheapest_model, DEFAULT_MODELS
from .tracker import get_global_tracker


class RoutedChatModel(BaseChatModel):
    """
    LangChain-compatible ChatModel with intelligent routing.

    Automatically selects the most cost-effective model based on
    task complexity, with optional fallback chains and cost tracking.

    Example:
        >>> model = RoutedChatModel(capability=ModelCapability.SIMPLE)
        >>> response = model.invoke([HumanMessage(content="Hello!")])
        >>> print(f"Model used: {model.last_model_used}")
    """

    # Model provider mapping (regex patterns)
    MODEL_PROVIDER_MAP: ClassVar[Dict[str, LLMProvider]] = {
        r"^gpt-": LLMProvider.OPENAI,
        r"^o1-": LLMProvider.OPENAI,
        r"^o3-": LLMProvider.OPENAI,
        r"^o1mini": LLMProvider.OPENAI,
        r"^text-": LLMProvider.OPENAI,
        r"^claude-": LLMProvider.ANTHROPIC,
        r"^claude-opus-": LLMProvider.ANTHROPIC,
        r"^claude-sonnet-": LLMProvider.ANTHROPIC,
        r"^gemini-": LLMProvider.GOOGLE,
    }

    capability: ModelCapability = ModelCapability.MODERATE
    exclude_local: bool = False
    track_costs: bool = True
    explicit_model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None

    # Internal state
    _router: Optional[LLMRouter] = None
    _last_model_used: Optional[str] = None
    _last_cost: float = 0.0

    class Config:
        """Pydantic config for extra attributes."""
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        """Initialize routed chat model."""
        super().__init__(**kwargs)
        self._router = LLMRouter(
            enable_fallback=True,
            enable_cache=False  # Disable for now
        )

    @property
    def _llm_type(self) -> str:
        """Return identifier for LangChain."""
        return "routed_chat_model"

    @property
    def last_model_used(self) -> Optional[str]:
        """Get the model used in the last call."""
        return self._last_model_used

    @property
    def last_cost(self) -> float:
        """Get the cost of the last call (USD)."""
        return self._last_cost

    def _convert_messages_to_litellm(
        self,
        messages: List[BaseMessage]
    ) -> List[Dict[str, str]]:
        """Convert LangChain messages to LiteLLM format."""
        litellm_messages = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            elif isinstance(msg, SystemMessage):
                role = "system"
            else:
                # Default to user for unknown types
                role = "user"

            litellm_messages.append({
                "role": role,
                "content": msg.content
            })

        return litellm_messages

    def _infer_provider_from_model(self, model_name: str) -> LLMProvider:
        """
        Infer provider from model name using regex mapping.

        Args:
            model_name: Model identifier (e.g., "gpt-4o", "o1-mini", "claude-opus-4")

        Returns:
            LLMProvider enum value

        Raises:
            ValueError: If model provider cannot be determined
        """
        import re
        model_lower = model_name.lower()

        for pattern, provider in self.MODEL_PROVIDER_MAP.items():
            if re.match(pattern, model_lower):
                return provider

        raise ValueError(
            f"Unknown model provider for '{model_name}'. "
            f"Supported prefixes: gpt-, o1-, o3-, text-, claude-, gemini-"
        )

    def _select_model(self) -> LLMConfig:
        """
        Select appropriate model based on capability and constraints.

        Returns:
            LLMConfig for the selected model
        """
        # If explicit model specified, use it directly
        if self.explicit_model:
            # Infer provider using regex mapping
            provider = self._infer_provider_from_model(self.explicit_model)

            return LLMConfig(
                provider=provider,
                model=self.explicit_model,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

        # Select cheapest capable model
        model_info = get_cheapest_model(
            capability=self.capability,
            exclude_local=self.exclude_local
        )

        return LLMConfig(
            provider=model_info.provider,
            model=model_info.name,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Generate response using intelligent routing.

        Args:
            messages: LangChain messages
            stop: Stop sequences
            run_manager: Callback manager
            **kwargs: Additional arguments

        Returns:
            ChatResult with generated response
        """
        # Convert messages
        litellm_messages = self._convert_messages_to_litellm(messages)

        # Select model
        config = self._select_model()

        # Override with kwargs if provided
        if stop:
            config.stop = stop

        # Call router
        response: LLMResponse = self._router.complete(
            messages=litellm_messages,
            config=config
        )

        # Track state
        self._last_model_used = response.model
        self._last_cost = response.usage.total_cost_usd

        # Track globally if enabled
        if self.track_costs:
            tracker = get_global_tracker()
            tracker.track(response, tags=[f"capability:{self.capability.value}"])

        # Convert to LangChain format
        ai_message = AIMessage(content=response.text)
        generation = ChatGeneration(message=ai_message)

        return ChatResult(
            generations=[generation],
            llm_output={
                "model": response.model,
                "provider": response.provider.value,
                "cost_usd": response.usage.total_cost_usd,
                "tokens": response.usage.total_tokens,
                "latency_ms": response.latency_ms,
            }
        )

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGeneration]:
        """
        Stream response (not yet implemented).

        For now, falls back to non-streaming generation.
        """
        # TODO: Implement streaming support
        result = self._generate(messages, stop, run_manager, **kwargs)
        yield result.generations[0]


def create_routed_chat_model(
    capability: ModelCapability = ModelCapability.MODERATE,
    exclude_local: bool = False,
    track_costs: bool = True,
    explicit_model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    **kwargs
) -> RoutedChatModel:
    """
    Factory function to create a routed chat model.

    Args:
        capability: Task complexity level (SIMPLE, MODERATE, COMPLEX, CODING, RESEARCH)
        exclude_local: Exclude local Ollama models (require cloud APIs)
        track_costs: Track costs in global tracker
        explicit_model: Override routing with specific model name
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
        max_tokens: Maximum tokens to generate
        **kwargs: Additional arguments passed to RoutedChatModel

    Returns:
        RoutedChatModel instance configured for intelligent routing

    Example:
        >>> # Simple classification task (uses cheapest model)
        >>> model = create_routed_chat_model(
        ...     capability=ModelCapability.SIMPLE,
        ...     temperature=0.0
        ... )
        >>>
        >>> # Complex reasoning task (uses premium model)
        >>> model = create_routed_chat_model(
        ...     capability=ModelCapability.COMPLEX,
        ...     temperature=0.8
        ... )
        >>>
        >>> # Override with specific model
        >>> model = create_routed_chat_model(
        ...     explicit_model="gpt-4o",
        ...     temperature=0.7
        ... )
    """
    return RoutedChatModel(
        capability=capability,
        exclude_local=exclude_local,
        track_costs=track_costs,
        explicit_model=explicit_model,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )

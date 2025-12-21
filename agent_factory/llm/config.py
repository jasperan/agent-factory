"""
LLM Configuration - Model Registry and Pricing

Centralized registry of supported models with pricing, capabilities,
and configuration. Updated regularly to reflect current provider pricing.

Pricing data sources:
- OpenAI: https://openai.com/pricing (verified Dec 21, 2025)
- Anthropic: https://anthropic.com/pricing (verified Dec 21, 2025)
- Google: https://ai.google.dev/gemini-api/docs/pricing (verified Dec 21, 2025)
- Ollama: Free (local models)

PRICING VERIFIED: December 21, 2025
All rates confirmed against official provider pricing pages.

Part of Phase 1: LLM Abstraction Layer
"""

from typing import Dict, Optional, List
from .types import ModelInfo, LLMProvider, ModelCapability


# Model Registry - All supported models with metadata
MODEL_REGISTRY: Dict[str, ModelInfo] = {
    # OpenAI Models
    "gpt-4o": ModelInfo(
        provider=LLMProvider.OPENAI,
        model_name="gpt-4o",
        input_cost_per_1k=0.0025,      # $2.50 per 1M input tokens
        output_cost_per_1k=0.010,      # $10.00 per 1M output tokens
        context_window=128000,         # 128K context
        capability=ModelCapability.COMPLEX,
        supports_streaming=True,
        supports_function_calling=True
    ),
    "gpt-4o-mini": ModelInfo(
        provider=LLMProvider.OPENAI,
        model_name="gpt-4o-mini",
        input_cost_per_1k=0.00015,     # $0.15 per 1M input tokens
        output_cost_per_1k=0.0006,     # $0.60 per 1M output tokens
        context_window=128000,
        capability=ModelCapability.MODERATE,
        supports_streaming=True,
        supports_function_calling=True
    ),
    "gpt-4-turbo": ModelInfo(
        provider=LLMProvider.OPENAI,
        model_name="gpt-4-turbo",
        input_cost_per_1k=0.010,       # $10 per 1M input tokens
        output_cost_per_1k=0.030,      # $30 per 1M output tokens
        context_window=128000,
        capability=ModelCapability.COMPLEX,
        supports_streaming=True,
        supports_function_calling=True
    ),
    "gpt-3.5-turbo": ModelInfo(
        provider=LLMProvider.OPENAI,
        model_name="gpt-3.5-turbo",
        input_cost_per_1k=0.0005,      # $0.50 per 1M input tokens
        output_cost_per_1k=0.0015,     # $1.50 per 1M output tokens
        context_window=16385,
        capability=ModelCapability.SIMPLE,
        supports_streaming=True,
        supports_function_calling=True
    ),
    "gpt-4-vision-preview": ModelInfo(
        provider=LLMProvider.OPENAI,
        model_name="gpt-4-vision-preview",
        input_cost_per_1k=0.010,       # $10 per 1M input tokens
        output_cost_per_1k=0.030,      # $30 per 1M output tokens
        context_window=128000,
        capability=ModelCapability.VISION,
        supports_streaming=False,
        supports_function_calling=False,
        supports_vision=True           # Vision support
    ),

    # Anthropic Models
    "claude-3-5-sonnet-20241022": ModelInfo(
        provider=LLMProvider.ANTHROPIC,
        model_name="claude-3-5-sonnet-20241022",
        input_cost_per_1k=0.003,       # $3 per 1M input tokens
        output_cost_per_1k=0.015,      # $15 per 1M output tokens
        context_window=200000,         # 200K context
        capability=ModelCapability.COMPLEX,
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True           # Vision support
    ),
    "claude-3-opus-20240229": ModelInfo(
        provider=LLMProvider.ANTHROPIC,
        model_name="claude-3-opus-20240229",
        input_cost_per_1k=0.015,       # $15 per 1M input tokens
        output_cost_per_1k=0.075,      # $75 per 1M output tokens
        context_window=200000,         # 200K context
        capability=ModelCapability.COMPLEX,
        supports_streaming=True,
        supports_function_calling=False
    ),
    "claude-3-sonnet-20240229": ModelInfo(
        provider=LLMProvider.ANTHROPIC,
        model_name="claude-3-sonnet-20240229",
        input_cost_per_1k=0.003,       # $3 per 1M input tokens
        output_cost_per_1k=0.015,      # $15 per 1M output tokens
        context_window=200000,
        capability=ModelCapability.MODERATE,
        supports_streaming=True,
        supports_function_calling=False
    ),
    "claude-3-haiku-20240307": ModelInfo(
        provider=LLMProvider.ANTHROPIC,
        model_name="claude-3-haiku-20240307",
        input_cost_per_1k=0.00025,     # $0.25 per 1M input tokens
        output_cost_per_1k=0.00125,    # $1.25 per 1M output tokens
        context_window=200000,
        capability=ModelCapability.SIMPLE,
        supports_streaming=True,
        supports_function_calling=False
    ),

    # Google Models
    "gemini-pro": ModelInfo(
        provider=LLMProvider.GOOGLE,
        model_name="gemini-pro",
        input_cost_per_1k=0.0005,      # $0.50 per 1M input tokens
        output_cost_per_1k=0.0015,     # $1.50 per 1M output tokens
        context_window=32760,
        capability=ModelCapability.MODERATE,
        supports_streaming=True,
        supports_function_calling=True
    ),
    "gemini-1.5-pro": ModelInfo(
        provider=LLMProvider.GOOGLE,
        model_name="gemini-1.5-pro",
        input_cost_per_1k=0.00125,     # $1.25 per 1M input tokens (≤200K context)
        output_cost_per_1k=0.010,      # $10.00 per 1M output tokens (≤200K context)
        context_window=2000000,        # 2M context (!)
        capability=ModelCapability.COMPLEX,
        supports_streaming=True,
        supports_function_calling=True
    ),
    "gemini-2.5-pro": ModelInfo(
        provider=LLMProvider.GOOGLE,
        model_name="gemini-2.5-pro",
        input_cost_per_1k=0.00125,     # $1.25 per 1M input tokens (≤200K context)
        output_cost_per_1k=0.010,      # $10.00 per 1M output tokens (≤200K context)
        context_window=2000000,        # 2M context
        capability=ModelCapability.COMPLEX,
        supports_streaming=True,
        supports_function_calling=True
    ),
    "gemini-2.0-flash": ModelInfo(
        provider=LLMProvider.GOOGLE,
        model_name="gemini-2.0-flash",
        input_cost_per_1k=0.0001,      # $0.10 per 1M input tokens
        output_cost_per_1k=0.0004,     # $0.40 per 1M output tokens
        context_window=1000000,        # 1M context
        capability=ModelCapability.MODERATE,
        supports_streaming=True,
        supports_function_calling=True
    ),

    # Ollama Models (Local - Free)
    "llama3": ModelInfo(
        provider=LLMProvider.OLLAMA,
        model_name="llama3",
        input_cost_per_1k=0.0,         # Free (local)
        output_cost_per_1k=0.0,        # Free (local)
        context_window=8192,
        capability=ModelCapability.MODERATE,
        supports_streaming=True,
        supports_function_calling=False
    ),
    "codellama": ModelInfo(
        provider=LLMProvider.OLLAMA,
        model_name="codellama",
        input_cost_per_1k=0.0,
        output_cost_per_1k=0.0,
        context_window=16384,
        capability=ModelCapability.CODING,
        supports_streaming=True,
        supports_function_calling=False
    ),
    "mistral": ModelInfo(
        provider=LLMProvider.OLLAMA,
        model_name="mistral",
        input_cost_per_1k=0.0,
        output_cost_per_1k=0.0,
        context_window=8192,
        capability=ModelCapability.SIMPLE,
        supports_streaming=True,
        supports_function_calling=False
    ),
}


# Default models by provider
DEFAULT_MODELS: Dict[LLMProvider, str] = {
    LLMProvider.OPENAI: "gpt-4o-mini",
    LLMProvider.ANTHROPIC: "claude-3-haiku-20240307",
    LLMProvider.GOOGLE: "gemini-pro",
    LLMProvider.OLLAMA: "llama3",
}


# Cost-optimized routing tiers (Phase 2)
# Strategy: Use cheapest capable model for task complexity
ROUTING_TIERS: Dict[ModelCapability, List[str]] = {
    ModelCapability.SIMPLE: [
        "llama3",                    # Free (local)
        "mistral",                   # Free (local)
        "gemini-2.0-flash",         # $0.0001 input (best cloud option!)
        "claude-3-haiku-20240307",  # $0.00025 input
        "gemini-pro",                # $0.0005 input
        "gpt-3.5-turbo",            # $0.0005 input
    ],
    ModelCapability.MODERATE: [
        "llama3",                    # Free (local)
        "gemini-2.0-flash",         # $0.0001 input (best cloud option!)
        "gpt-4o-mini",              # $0.00015 input
        "claude-3-haiku-20240307",  # $0.00025 input
        "gemini-pro",                # $0.0005 input
        "claude-3-sonnet-20240229", # $0.003 input
    ],
    ModelCapability.COMPLEX: [
        "gpt-4o-mini",              # $0.00015 input
        "gemini-2.5-pro",           # $0.00125 input (≤200K context)
        "gemini-1.5-pro",           # $0.00125 input (≤200K context)
        "gpt-4o",                    # $0.0025 input
        "claude-3-sonnet-20240229", # $0.003 input
        "gpt-4-turbo",              # $0.010 input
        "claude-3-opus-20240229",   # $0.015 input
    ],
    ModelCapability.CODING: [
        "codellama",                # Free (local)
        "gpt-4o-mini",              # $0.00015 input
        "gpt-4o",                    # $0.0025 input
        "claude-3-sonnet-20240229", # $0.003 input
    ],
    ModelCapability.RESEARCH: [
        "gpt-4o-mini",              # $0.00015 input
        "gemini-1.5-pro",           # $0.007 input (1M context!)
        "gpt-4o",                    # $0.0025 input
        "claude-3-opus-20240229",   # $0.015 input
    ],
    ModelCapability.VISION: [
        "claude-3-5-sonnet-20241022",  # $0.003 input (best vision model)
        "gpt-4-vision-preview",        # $0.010 input
    ],
}


def get_model_info(model_name: str) -> Optional[ModelInfo]:
    """
    Get metadata for a specific model.

    Args:
        model_name: Name of the model (e.g., "gpt-4o-mini")

    Returns:
        ModelInfo if model exists, None otherwise
    """
    return MODEL_REGISTRY.get(model_name)


def get_default_model(provider: LLMProvider) -> str:
    """
    Get default model for a provider.

    Args:
        provider: LLM provider

    Returns:
        Default model name for the provider
    """
    return DEFAULT_MODELS.get(provider, "gpt-4o-mini")


def get_models_by_provider(provider: LLMProvider) -> List[ModelInfo]:
    """
    Get all models for a specific provider.

    Args:
        provider: LLM provider to filter by

    Returns:
        List of ModelInfo for the provider
    """
    return [
        info for info in MODEL_REGISTRY.values()
        if info.provider == provider
    ]


def get_models_by_capability(capability: ModelCapability) -> List[str]:
    """
    Get recommended models for a capability level (Phase 2).

    Returns models in cost-optimized order (cheapest first).

    Args:
        capability: Task complexity/capability required

    Returns:
        List of model names, ordered by cost (cheapest first)
    """
    return ROUTING_TIERS.get(capability, [])


def validate_model_exists(model_name: str) -> bool:
    """
    Check if a model exists in the registry.

    Args:
        model_name: Name of the model to check

    Returns:
        True if model exists, False otherwise
    """
    return model_name in MODEL_REGISTRY


def get_cheapest_model(
    capability: ModelCapability,
    exclude_local: bool = False
) -> Optional[str]:
    """
    Get the cheapest model for a capability level (Phase 2).

    Args:
        capability: Required capability level
        exclude_local: If True, exclude local Ollama models

    Returns:
        Model name of cheapest option, or None if no models available
    """
    models = get_models_by_capability(capability)

    if exclude_local:
        # Filter out Ollama models
        models = [
            m for m in models
            if get_model_info(m) and get_model_info(m).provider != LLMProvider.OLLAMA
        ]

    return models[0] if models else None

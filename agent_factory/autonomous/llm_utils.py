"""Shared LLM helpers for the autonomous pipeline.

Centralizes the lazy litellm/Ollama completion call and the markdown-fenced
JSON extraction logic that the planner (SuggestionGenerator) and judge
(AutonomousRunner) both rely on.
"""

import json
from typing import Any

from .config import AutonomousConfig


def ollama_complete(
    prompt: str,
    config: AutonomousConfig,
    system_prompt: str = "",
) -> str:
    """Run a single completion against the configured Ollama model via litellm.

    Args:
        prompt: User prompt content.
        config: Autonomous configuration providing model, base URL and context size.
        system_prompt: Optional system prompt prepended to the conversation.

    Returns:
        The assistant message content as a string.
    """
    try:
        import litellm
    except ImportError as exc:  # pragma: no cover - import guard
        raise ImportError("litellm not installed. Run: pip install litellm") from exc

    litellm.set_verbose = False

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = litellm.completion(
        model=f"ollama/{config.model}",
        messages=messages,
        api_base=config.ollama_base_url,
        num_ctx=config.num_ctx,
    )

    return response.choices[0].message.content


def extract_json(response: str) -> Any:
    """Extract and parse JSON from an LLM response that may wrap it in fences.

    Handles ```json ... ``` and bare ``` ... ``` code blocks, taking the first
    fenced block when present, otherwise parsing the whole string.

    Args:
        response: Raw LLM response text.

    Returns:
        The parsed JSON value (object, array, etc.).

    Raises:
        json.JSONDecodeError: If no valid JSON can be parsed.
    """
    text = response.strip()

    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in text:
        # First fenced block: content between the first and second fence.
        parts = text.split("```")
        if len(parts) >= 3:
            text = parts[1]

    return json.loads(text.strip())

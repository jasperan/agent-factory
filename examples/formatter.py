"""Format retrieved cases as few-shot examples for SME agent.

Reference pattern from LangChain:
https://python.langchain.com/docs/how_to/few_shot_examples_chat/
"""

from typing import List
from .retriever import RetrievalResult


def format_maintenance_examples(
    results: List[RetrievalResult],
    include_scores: bool = False,
) -> str:
    """
    Format retrieved cases as few-shot context for SME agent.

    Args:
        results: List of RetrievalResult from CaseRetriever
        include_scores: Whether to include similarity scores (for debugging)

    Returns:
        Formatted string ready for prompt injection
    """
    if not results:
        return "No similar past cases found."

    formatted_examples = []

    for i, result in enumerate(results, 1):
        case = result.case
        example = case.to_few_shot_example()

        if include_scores:
            score_line = f"(Similarity: {result.similarity_score:.2%})"
            example = f"{example}\n{score_line}"

        formatted_examples.append(example)

    header = f"## {len(results)} Similar Past Cases Found\n\n"
    header += "Use these examples to understand how similar problems were resolved:\n"

    return header + "\n\n".join(formatted_examples)


def format_for_sme_prompt(
    results: List[RetrievalResult],
    current_input: str,
    base_prompt: str,
) -> str:
    """
    Create complete enhanced prompt for SME agent.

    Args:
        results: Retrieved similar cases
        current_input: Current technician input
        base_prompt: Original SME system prompt

    Returns:
        Enhanced prompt with few-shot examples injected
    """
    few_shot_context = format_maintenance_examples(results)

    enhanced_prompt = f"""
{base_prompt}

{few_shot_context}

## Current Case

Technician Input: "{current_input}"

Based on the similar cases above (if any), parse this input and provide diagnosis assistance.
"""

    return enhanced_prompt.strip()

"""Integration layer for few-shot RAG with orchestrator.

This module provides the connection between the few-shot retrieval
system and the existing RivetCEO orchestrator.
"""

import logging
from typing import Optional, List
from dataclasses import dataclass

from .store import CaseStore
from .embedder import CaseEmbedder
from .retriever import CaseRetriever, RetrievalResult
from .formatter import format_for_sme_prompt

logger = logging.getLogger(__name__)


@dataclass
class FewShotConfig:
    """Configuration for few-shot retrieval."""
    enabled: bool = True
    k: int = 3
    similarity_threshold: float = 0.7
    timeout_seconds: float = 2.0
    fallback_on_error: bool = True


class FewShotEnhancer:
    """
    Enhances SME prompts with few-shot examples.

    Thread-safe, singleton-friendly design for use in async orchestrator.
    """

    _instance: Optional['FewShotEnhancer'] = None

    def __init__(self, config: FewShotConfig = None):
        self.config = config or FewShotConfig()
        self._retriever: Optional[CaseRetriever] = None
        self._initialized = False

    @classmethod
    def get_instance(cls, config: FewShotConfig = None) -> 'FewShotEnhancer':
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance

    def initialize(
        self,
        store: CaseStore,
        embedder: CaseEmbedder,
    ) -> None:
        """Initialize with store and embedder."""
        self._retriever = CaseRetriever(
            store=store,
            embedder=embedder,
            k=self.config.k,
            similarity_threshold=self.config.similarity_threshold,
        )
        self._initialized = True
        logger.info(
            f"FewShotEnhancer initialized: k={self.config.k}, "
            f"threshold={self.config.similarity_threshold}"
        )

    async def enhance_prompt(
        self,
        base_prompt: str,
        user_input: str,
    ) -> tuple[str, List[RetrievalResult]]:
        """
        Enhance prompt with few-shot examples.

        Args:
            base_prompt: Original system prompt
            user_input: User's input text

        Returns:
            Tuple of (enhanced_prompt, retrieved_cases)
        """
        if not self.config.enabled:
            return base_prompt, []

        if not self._initialized or self._retriever is None:
            logger.warning("FewShotEnhancer not initialized, skipping")
            return base_prompt, []

        try:
            import asyncio

            # Retrieve with timeout
            results = await asyncio.wait_for(
                self._retriever.aget_similar_cases(user_input),
                timeout=self.config.timeout_seconds,
            )

            if results:
                enhanced = format_for_sme_prompt(
                    results=results,
                    current_input=user_input,
                    base_prompt=base_prompt,
                )
                return enhanced, results

            return base_prompt, []

        except asyncio.TimeoutError:
            logger.warning(
                f"Few-shot retrieval timed out after {self.config.timeout_seconds}s"
            )
            if self.config.fallback_on_error:
                return base_prompt, []
            raise

        except Exception as e:
            logger.error(f"Few-shot retrieval error: {e}")
            if self.config.fallback_on_error:
                return base_prompt, []
            raise

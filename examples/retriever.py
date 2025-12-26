"""Case retrieval using SemanticSimilarityExampleSelector pattern.

References:
- https://python.langchain.com/docs/how_to/few_shot_examples_chat/
- https://github.com/langchain-ai/langchain/discussions/23850
- https://github.com/pixegami/rag-tutorial-v2/blob/main/query_data.py
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from .schemas import MaintenanceCase
from .store import CaseStore
from .embedder import CaseEmbedder


@dataclass
class RetrievalResult:
    """Result from case retrieval with similarity score."""
    case: MaintenanceCase
    similarity_score: float


class CaseRetriever:
    """
    Retrieves similar maintenance cases using semantic similarity.

    Pattern based on LangChain's SemanticSimilarityExampleSelector:
    https://python.langchain.com/docs/how_to/example_selectors_similarity/
    """

    def __init__(
        self,
        store: CaseStore,
        embedder: CaseEmbedder,
        k: int = 3,
        similarity_threshold: float = 0.7,
    ):
        """
        Initialize retriever.

        Args:
            store: CaseStore instance with loaded cases
            embedder: CaseEmbedder for generating query embeddings
            k: Number of similar cases to retrieve
            similarity_threshold: Minimum similarity score (0-1)
        """
        self.store = store
        self.embedder = embedder
        self.k = k
        self.similarity_threshold = similarity_threshold

        # Pre-compute embeddings for all cases
        self._case_embeddings: List[Tuple[MaintenanceCase, List[float]]] = []
        self._build_index()

    def _build_index(self) -> None:
        """Build embedding index for all cases in store."""
        self._case_embeddings = []
        for case in self.store.list_cases():
            embedding = self.embedder.embed(case.to_embedding_text())
            self._case_embeddings.append((case, embedding))

    def refresh_index(self) -> None:
        """Rebuild index when cases are added."""
        self._build_index()

    def _cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """Calculate cosine similarity between two vectors."""
        a = np.array(vec1)
        b = np.array(vec2)

        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))

    def get_similar_cases(
        self,
        query: str,
        k: Optional[int] = None,
    ) -> List[RetrievalResult]:
        """
        Retrieve k most similar cases for a query.

        Args:
            query: Input text (technician description of problem)
            k: Number of cases to retrieve (defaults to self.k)

        Returns:
            List of RetrievalResult with cases and similarity scores
        """
        if k is None:
            k = self.k

        if not self._case_embeddings:
            return []

        # Embed the query
        query_embedding = self.embedder.embed(query)

        # Calculate similarity with all cases
        scored_cases: List[Tuple[MaintenanceCase, float]] = []
        for case, case_embedding in self._case_embeddings:
            similarity = self._cosine_similarity(query_embedding, case_embedding)
            scored_cases.append((case, similarity))

        # Sort by similarity (descending)
        scored_cases.sort(key=lambda x: x[1], reverse=True)

        # Filter by threshold and take top k
        results = []
        for case, score in scored_cases[:k]:
            if score >= self.similarity_threshold:
                results.append(RetrievalResult(case=case, similarity_score=score))

        return results

    async def aget_similar_cases(
        self,
        query: str,
        k: Optional[int] = None,
    ) -> List[RetrievalResult]:
        """Async version for use in async orchestrator."""
        # For now, just wrap sync version
        # TODO: Make truly async when connecting to production vector store
        return self.get_similar_cases(query, k)

"""
Abstract Vector Store Interface

Defines the common interface for vector storage backends.
Implementations: PostgresVectorStore, ChromaDBVectorStore

This abstraction allows runtime switching between storage backends
while maintaining a consistent API surface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class SearchResult:
    """
    Standardized search result format.

    Attributes:
        text: Document content
        metadata: Document metadata (manual_id, title, manufacturer, etc.)
        distance: Similarity distance (lower = more similar)
        score: Similarity score (higher = more similar, normalized 0-1)
    """
    text: str
    metadata: Dict
    distance: float
    score: float


class AbstractVectorStore(ABC):
    """
    Abstract base class for vector storage backends.

    Implementations must provide:
    - Document indexing (add_documents)
    - Semantic search (search)
    - Collection management (get_or_create_collection, delete_collection)
    - Embedding generation (embed_text, embed_texts)

    All implementations should be thread-safe and handle errors gracefully.
    """

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding vector for single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector.
            Returns empty list if embedding fails or is unavailable.
        """
        pass

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for multiple texts (batch operation).

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors. Returns empty lists if embedding fails.
        """
        pass

    @abstractmethod
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict],
        ids: List[str]
    ) -> int:
        """
        Add documents to a collection with embeddings.

        Args:
            collection_name: Name of the collection (e.g., "equipment_manuals")
            documents: List of document texts
            metadatas: List of metadata dicts (parallel to documents)
            ids: List of unique IDs (parallel to documents)

        Returns:
            Number of documents successfully added

        Raises:
            ValueError: If input lists have mismatched lengths
            StorageError: If storage operation fails
        """
        pass

    @abstractmethod
    def search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        Search collection for relevant documents.

        Args:
            collection_name: Name of the collection to search
            query: Search query text
            top_k: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {"manufacturer": "Siemens"})

        Returns:
            List of SearchResult objects, sorted by relevance (most relevant first)
        """
        pass

    @abstractmethod
    def get_or_create_collection(self, name: str, metadata: Optional[Dict] = None) -> str:
        """
        Get existing collection or create if doesn't exist.

        Args:
            name: Collection name
            metadata: Optional collection metadata

        Returns:
            Collection name (for chaining)
        """
        pass

    @abstractmethod
    def delete_collection(self, name: str) -> bool:
        """
        Delete a collection and all its documents.

        Args:
            name: Collection name

        Returns:
            True if deleted successfully, False otherwise
        """
        pass

    @abstractmethod
    def list_collections(self) -> List[str]:
        """
        List all collection names.

        Returns:
            List of collection names
        """
        pass

    @abstractmethod
    def get_collection_stats(self, name: str) -> Dict:
        """
        Get statistics for a collection.

        Args:
            name: Collection name

        Returns:
            Dict with keys: document_count, size_bytes (if available)
        """
        pass

    @abstractmethod
    def close(self):
        """Close any open connections or resources."""
        pass

    # Context manager support
    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class StorageError(Exception):
    """Custom exception for storage-related errors"""
    pass

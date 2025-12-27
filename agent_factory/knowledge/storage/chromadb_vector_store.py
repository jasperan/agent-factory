"""
ChromaDB Vector Store Implementation

Implements AbstractVectorStore using ChromaDB as specified in TAB1_BACKEND.md.

Features:
- Persistent local storage (./chroma_db directory)
- sentence-transformers/all-MiniLM-L6-v2 embeddings
- Collections: equipment_manuals, user_{id}_machine_{id}
- Optimized for local development and experimentation
"""

import logging
import os
from typing import List, Dict, Optional
from pathlib import Path

from agent_factory.knowledge.storage.abstract_vector_store import (
    AbstractVectorStore,
    SearchResult,
    StorageError
)

logger = logging.getLogger(__name__)


class ChromaDBVectorStore(AbstractVectorStore):
    """
    ChromaDB-based vector store implementation.

    Follows TAB1_BACKEND.md specification (lines 615-774).

    Advantages:
    - Pure vector similarity search (no text preprocessing needed)
    - Local persistent storage (no cloud dependencies)
    - Simple setup (single directory)
    - Excellent for development/testing

    Requirements:
    - chromadb package installed
    - sentence-transformers package installed
    """

    def __init__(self, persist_dir: Optional[str] = None):
        """
        Initialize ChromaDB vector store.

        Args:
            persist_dir: Directory for persistent storage.
                        Defaults to CHROMA_PERSIST_DIR env var or ./chroma_db
        """
        # Lazy imports (only load if user selects ChromaDB backend)
        try:
            import chromadb
            from chromadb.config import Settings
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise StorageError(
                f"ChromaDB dependencies not installed: {e}. "
                "Install with: poetry add chromadb sentence-transformers"
            )

        self.persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )

        # Initialize embedding model
        self.embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self._embeddings_available = True

        logger.info(f"ChromaDBVectorStore initialized at {self.persist_dir}")

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        if not self._embeddings_available:
            return []

        try:
            return self.embedder.encode(text).tolist()
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return []

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch operation).

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not self._embeddings_available:
            return [[] for _ in texts]

        try:
            return self.embedder.encode(texts).tolist()
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            return [[] for _ in texts]

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
            collection_name: Name of the collection
            documents: List of document texts
            metadatas: List of metadata dicts
            ids: List of unique IDs

        Returns:
            Number of documents added

        Raises:
            ValueError: If input lists have mismatched lengths
            StorageError: If storage operation fails
        """
        if len(documents) != len(metadatas) or len(documents) != len(ids):
            raise ValueError(
                f"Mismatched input lengths: documents={len(documents)}, "
                f"metadatas={len(metadatas)}, ids={len(ids)}"
            )

        try:
            # Get or create collection
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": f"Collection: {collection_name}"}
            )

            # Generate embeddings
            embeddings = self.embed_texts(documents)

            # Add to collection
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )

            logger.info(f"Added {len(documents)} documents to {collection_name}")
            return len(documents)

        except Exception as e:
            logger.error(f"Failed to add documents to {collection_name}: {e}")
            raise StorageError(f"Document addition failed: {e}")

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
            collection_name: Collection to search
            query: Search query text
            top_k: Number of results
            filter_metadata: Metadata filters (e.g., {"manufacturer": "Siemens"})

        Returns:
            List of SearchResult objects, sorted by relevance

        Raises:
            StorageError: If search fails or collection doesn't exist
        """
        try:
            # Get collection
            collection = self.client.get_collection(name=collection_name)

            # Generate query embedding
            query_embedding = self.embed_text(query)

            # Build query kwargs
            query_kwargs = {
                "query_embeddings": [query_embedding],
                "n_results": top_k,
                "include": ["documents", "metadatas", "distances"]
            }

            # Add metadata filter if provided
            if filter_metadata:
                # ChromaDB uses "where" for filtering
                # Convert to ChromaDB where clause format
                where_clause = {}
                for key, value in filter_metadata.items():
                    where_clause[key] = {"$eq": value}
                query_kwargs["where"] = where_clause

            # Execute search
            results = collection.query(**query_kwargs)

            # Convert to SearchResult format
            search_results = []
            for i, doc in enumerate(results["documents"][0]):
                distance = results["distances"][0][i]
                # Convert distance to score (closer distance = higher score)
                # Using 1 / (1 + distance) to normalize score to 0-1 range
                score = 1.0 / (1.0 + distance)

                search_results.append(SearchResult(
                    text=doc,
                    metadata=results["metadatas"][0][i],
                    distance=distance,
                    score=score
                ))

            return search_results

        except Exception as e:
            logger.error(f"Search failed for {collection_name}: {e}")
            raise StorageError(f"Search failed: {e}")

    def get_or_create_collection(self, name: str, metadata: Optional[Dict] = None) -> str:
        """
        Get existing collection or create if doesn't exist.

        Args:
            name: Collection name
            metadata: Optional collection metadata

        Returns:
            Collection name
        """
        try:
            meta = metadata or {"description": f"Collection: {name}"}
            self.client.get_or_create_collection(name=name, metadata=meta)
            logger.info(f"Collection ready: {name}")
            return name
        except Exception as e:
            logger.error(f"Failed to get/create collection {name}: {e}")
            raise StorageError(f"Collection operation failed: {e}")

    def delete_collection(self, name: str) -> bool:
        """
        Delete a collection and all its documents.

        Args:
            name: Collection name

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            self.client.delete_collection(name=name)
            logger.info(f"Deleted collection: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {name}: {e}")
            return False

    def list_collections(self) -> List[str]:
        """
        List all collection names.

        Returns:
            List of collection names
        """
        try:
            collections = self.client.list_collections()
            return [c.name for c in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []

    def get_collection_stats(self, name: str) -> Dict:
        """
        Get statistics for a collection.

        Args:
            name: Collection name

        Returns:
            Dict with document_count and other stats
        """
        try:
            collection = self.client.get_collection(name=name)
            count = collection.count()

            return {
                "collection_name": name,
                "document_count": count,
                "size_bytes": None  # ChromaDB doesn't expose size directly
            }
        except Exception as e:
            logger.error(f"Failed to get stats for {name}: {e}")
            return {
                "collection_name": name,
                "document_count": 0,
                "size_bytes": None,
                "error": str(e)
            }

    def close(self):
        """Close ChromaDB client (cleanup)"""
        # ChromaDB client doesn't require explicit closing
        # Persists automatically
        logger.info("ChromaDBVectorStore closed")

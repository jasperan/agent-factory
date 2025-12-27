"""
PostgreSQL Vector Store Implementation

Wraps the existing PostgreSQL-based VectorStore to conform to AbstractVectorStore interface.

Features:
- Full-text search using PostgreSQL ts_rank (always available)
- Optional vector embeddings with sentence-transformers (lazy-loaded)
- Integrates with existing RIVETProDatabase
- Production-ready (85% complete RAG retriever)
"""

import logging
from typing import List, Dict, Optional

from agent_factory.knowledge.storage.abstract_vector_store import (
    AbstractVectorStore,
    SearchResult,
    StorageError
)
from agent_factory.knowledge.vector_store import VectorStore

logger = logging.getLogger(__name__)


class PostgresVectorStore(AbstractVectorStore):
    """
    PostgreSQL-based vector store implementation.

    Wraps the existing VectorStore class to provide AbstractVectorStore interface.
    Uses PostgreSQL full-text search (ts_rank) with optional vector embeddings.

    Advantages:
    - No additional dependencies (reuses existing DB infrastructure)
    - Production-proven (RAG retriever 85% complete)
    - Graceful degradation if embeddings unavailable
    - Multi-provider support (Neon, Supabase, Railway)
    """

    def __init__(self):
        """Initialize PostgreSQL vector store"""
        self._store = VectorStore()
        logger.info("PostgresVectorStore initialized")

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for single text.

        Delegates to existing VectorStore implementation.
        Returns empty list if embeddings unavailable (graceful degradation).
        """
        return self._store.embed_text(text)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch operation).

        Delegates to existing VectorStore implementation.
        """
        return self._store.embed_texts(texts)

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict],
        ids: List[str]
    ) -> int:
        """
        Add documents to a collection.

        Args:
            collection_name: "equipment_manuals" or "user_{id}_machine_{id}"
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
            # Prepare chunks for storage
            chunks = []
            for doc, meta, doc_id in zip(documents, metadatas, ids):
                chunks.append({
                    "id": doc_id,
                    "text": doc,
                    "metadata": meta
                })

            # Route to appropriate collection
            if collection_name == "equipment_manuals":
                count = self._store.add_documents_to_manuals(chunks)
            elif collection_name.startswith("user_"):
                # Extract user_id and machine_id from collection name
                # Format: user_{id[:8]}_machine_{id[:8]}
                parts = collection_name.split("_")
                if len(parts) >= 4:
                    user_id = parts[1]  # Will be truncated ID
                    machine_id = parts[3]  # Will be truncated ID
                    count = self._store.add_documents_to_prints(user_id, machine_id, chunks)
                else:
                    raise ValueError(f"Invalid collection name format: {collection_name}")
            else:
                raise ValueError(f"Unknown collection: {collection_name}")

            logger.info(f"Added {count} documents to {collection_name}")
            return count

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
            filter_metadata: Filters (e.g., {"manufacturer": "Siemens"})

        Returns:
            List of SearchResult objects
        """
        try:
            if collection_name == "equipment_manuals":
                # Search manuals with optional manufacturer filter
                manufacturer = filter_metadata.get("manufacturer") if filter_metadata else None
                raw_results = self._store.search_manuals(query, top_k, manufacturer)

            elif collection_name.startswith("user_"):
                # Search user prints
                parts = collection_name.split("_")
                if len(parts) >= 4:
                    user_id = parts[1]
                    machine_id = parts[3]
                    raw_results = self._store.search_prints(user_id, machine_id, query, top_k)
                else:
                    raise ValueError(f"Invalid collection name: {collection_name}")
            else:
                raise ValueError(f"Unknown collection: {collection_name}")

            # Convert to SearchResult format
            results = []
            for r in raw_results:
                results.append(SearchResult(
                    text=r.get("text", ""),
                    metadata=r.get("metadata", {}),
                    distance=r.get("distance", 0.0),
                    score=r.get("score", 0.0)
                ))

            return results

        except Exception as e:
            logger.error(f"Search failed for {collection_name}: {e}")
            raise StorageError(f"Search failed: {e}")

    def get_or_create_collection(self, name: str, metadata: Optional[Dict] = None) -> str:
        """
        Get or create collection.

        For PostgreSQL implementation, collections are implicit (based on table structure).
        This method validates the collection name and returns it.

        Args:
            name: Collection name
            metadata: Optional collection metadata (not used in PostgreSQL impl)

        Returns:
            Collection name

        Raises:
            ValueError: If collection name is invalid
        """
        valid_prefixes = ["equipment_manuals", "user_", "knowledge_atoms"]

        if not any(name.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError(
                f"Invalid collection name: {name}. "
                f"Must start with one of: {valid_prefixes}"
            )

        logger.info(f"Collection validated: {name}")
        return name

    def delete_collection(self, name: str) -> bool:
        """
        Delete a collection.

        Note: In PostgreSQL implementation, this is stubbed.
        Actual deletion would require database CASCADE operations.

        Args:
            name: Collection name

        Returns:
            Success status
        """
        return self._store.delete_collection(name)

    def list_collections(self) -> List[str]:
        """
        List all collections.

        Returns:
            List of collection names (currently returns standard collections)
        """
        # Standard collections
        collections = ["equipment_manuals"]

        # Note: User print collections are dynamically named
        # Would need database query to enumerate all user_{id}_machine_{id} collections

        return collections

    def get_collection_stats(self, name: str) -> Dict:
        """
        Get collection statistics.

        Args:
            name: Collection name

        Returns:
            Dict with document_count (and size_bytes if available)
        """
        # Note: This would require database queries to count documents
        # Stubbed for now
        return {
            "collection_name": name,
            "document_count": 0,  # Would query database
            "size_bytes": None
        }

    def close(self):
        """Close database connection"""
        if hasattr(self._store, 'close'):
            self._store.close()

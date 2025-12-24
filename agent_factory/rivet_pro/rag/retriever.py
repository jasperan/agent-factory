"""
Document Retriever for RIVET Pro RAG

Semantic search over knowledge base with vendor/equipment filtering
and coverage estimation for routing decisions.

Author: Agent Factory
Created: 2025-12-17
Phase: 2/8 (RAG Layer)
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from agent_factory.rivet_pro.models import RivetIntent, KBCoverage
from agent_factory.rivet_pro.rag.config import RAGConfig
from agent_factory.rivet_pro.rag.filters import build_filters, build_keyword_filters
from agent_factory.core.database_manager import DatabaseManager

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class RetrievedDoc:
    """
    Single retrieved document from knowledge base.

    Attributes:
        atom_id: Unique atom identifier
        title: Document title
        summary: Brief summary (1-2 sentences)
        content: Full content text
        atom_type: Type of atom (concept, procedure, fault, etc.)
        vendor: Equipment vendor
        equipment_type: Equipment type
        similarity: Similarity score (0.0-1.0)
        source: Source document/URL
        page_number: Page number in source (if applicable)
        created_at: When atom was created
    """
    atom_id: int
    title: str
    summary: str
    content: str
    atom_type: str
    vendor: str
    equipment_type: str
    similarity: float
    source: Optional[str] = None
    page_number: Optional[int] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "atom_id": self.atom_id,
            "title": self.title,
            "summary": self.summary,
            "content": self.content,
            "atom_type": self.atom_type,
            "vendor": self.vendor,
            "equipment_type": self.equipment_type,
            "similarity": self.similarity,
            "source": self.source,
            "page_number": self.page_number,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


def search_docs(
    intent: RivetIntent,
    config: Optional[RAGConfig] = None,
    db: Optional[DatabaseManager] = None,
    model_number: Optional[str] = None,
    part_number: Optional[str] = None
) -> List[RetrievedDoc]:
    """
    Search knowledge base for relevant documents.

    Performs keyword search with vendor/equipment/model filtering.
    Returns top-k most relevant documents sorted by text relevance.

    Args:
        intent: Parsed user intent with vendor/equipment/symptom info
        config: RAG configuration (uses default if not provided)
        db: DatabaseManager instance (creates new if not provided)
        model_number: Equipment model number from OCR (e.g., "G120C", "PowerFlex 525")
        part_number: Equipment part number from OCR (e.g., "6SL3244-0BB13-1PA0")

    Returns:
        List of RetrievedDoc objects sorted by similarity (highest first)

    Examples:
        >>> from agent_factory.rivet_pro.models import RivetIntent, VendorType, EquipmentType
        >>> intent = RivetIntent(
        ...     vendor=VendorType.SIEMENS,
        ...     equipment_type=EquipmentType.VFD,
        ...     symptom="F3002 overvoltage fault",
        ...     raw_summary="Siemens VFD F3002 troubleshooting",
        ...     context_source="text_only",
        ...     confidence=0.9,
        ...     kb_coverage="strong"
        ... )
        >>> docs = search_docs(intent, model_number="G120C")
        >>> len(docs)
        8
        >>> docs[0].similarity > 0.75
        True
    """
    # Use default config if not provided
    if config is None:
        config = RAGConfig()

    # Use default DatabaseManager if not provided
    if db is None:
        db = DatabaseManager()

    # Build filters from intent
    filters = build_filters(intent)
    keywords = build_keyword_filters(intent)

    logger.info(
        f"Searching with filters: {filters}, keywords: {keywords[:5]}, "
        f"model_number: {model_number}, part_number: {part_number}"
    )

    try:
        # Get search text from intent
        query_text = intent.raw_summary

        # Build SQL query with filters
        where_clauses = []
        params = []

        # Add manufacturer filter (maps from vendor detection)
        if "manufacturer" in filters:
            where_clauses.append("manufacturer = %s")
            params.append(filters["manufacturer"])

        # Add model number filter (normalized - remove hyphens/spaces)
        if model_number:
            # Normalize: "G-120C" -> "G120C", "S7 1200" -> "S71200"
            normalized_model = model_number.replace("-", "").replace(" ", "").upper()
            where_clauses.append(
                "REPLACE(REPLACE(UPPER(product_family), '-', ''), ' ', '') LIKE %s"
            )
            params.append(f"%{normalized_model}%")
            logger.info(f"Model filter applied: {model_number} (normalized: {normalized_model})")

        # Add part number filter (exact match if provided)
        if part_number:
            where_clauses.append(
                "(source_document ILIKE %s OR content ILIKE %s)"
            )
            part_pattern = f"%{part_number}%"
            params.extend([part_pattern, part_pattern])
            logger.info(f"Part number filter applied: {part_number}")

        # Note: equipment_type column does not exist in knowledge_atoms table
        # Filtering by equipment type removed until schema is updated

        # Add text search with PostgreSQL full-text ranking
        search_query_tsquery = None
        if keywords:
            # Use OR condition for keywords
            keyword_conditions = []
            for keyword in keywords[:5]:  # Limit to top 5 keywords
                keyword_param = f"%{keyword}%"
                params.append(keyword_param)
                params.append(keyword_param)
                params.append(keyword_param)
                keyword_conditions.append(
                    "(title ILIKE %s OR summary ILIKE %s OR content ILIKE %s)"
                )
            if keyword_conditions:
                where_clauses.append(f"({' OR '.join(keyword_conditions)})")

            # Build ts_query for ranking (use first 3 keywords)
            search_query_tsquery = " | ".join(keywords[:3])  # OR operator for ts_query

        # Build complete query
        where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"

        # Use ts_rank for text relevance scoring instead of hardcoded 0.8
        if search_query_tsquery:
            sql = f"""
                SELECT
                    atom_id,
                    title,
                    summary,
                    content,
                    atom_type,
                    manufacturer,
                    source_document as source,
                    source_pages,
                    created_at,
                    ts_rank(
                        to_tsvector('english', title || ' ' || summary || ' ' || content),
                        plainto_tsquery('english', %s)
                    ) as similarity
                FROM knowledge_atoms
                WHERE {where_sql}
                ORDER BY similarity DESC, created_at DESC
                LIMIT {config.search.top_k}
            """
            params.append(search_query_tsquery)
        else:
            # No keywords - use default relevance
            sql = f"""
                SELECT
                    atom_id,
                    title,
                    summary,
                    content,
                    atom_type,
                    manufacturer,
                    source_document as source,
                    source_pages,
                    created_at,
                    0.5 as similarity  -- Default relevance when no keywords
                FROM knowledge_atoms
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT {config.search.top_k}
            """

        # Execute query
        logger.info(f"Executing search with {len(params)} params, search_query: '{search_query_tsquery if search_query_tsquery else 'NONE'}'")
        result = db.execute_query(sql, tuple(params))

        if not result:
            logger.warning(f"No documents found for intent: {intent.raw_summary}")
            return []

        # Convert to RetrievedDoc objects
        docs = []
        similarity_scores = []
        for row in result:
            similarity_scores.append(float(row[9]))
            # Extract first page number from source_pages array (if it exists)
            source_pages = row[7]  # source_pages array
            page_number = source_pages[0] if source_pages and len(source_pages) > 0 else None

            doc = RetrievedDoc(
                atom_id=row[0],
                title=row[1],
                summary=row[2],
                content=row[3],
                atom_type=row[4],
                vendor=row[5],  # manufacturer from DB
                equipment_type="unknown",  # Column doesn't exist in schema yet
                source=row[6],
                page_number=page_number,  # First page from source_pages array
                created_at=row[8],
                similarity=row[9]
            )
            docs.append(doc)

        if similarity_scores:
            avg_sim = sum(similarity_scores) / len(similarity_scores)
            logger.info(f"Retrieved {len(docs)} documents, similarity scores: min={min(similarity_scores):.3f}, max={max(similarity_scores):.3f}, avg={avg_sim:.3f}")
        else:
            logger.info(f"Retrieved {len(docs)} documents (no similarity scores)")
        return docs

    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []


def estimate_coverage(
    intent: RivetIntent,
    config: Optional[RAGConfig] = None,
    db: Optional[DatabaseManager] = None,
    model_number: Optional[str] = None
) -> KBCoverage:
    """
    Estimate knowledge base coverage for a given intent.

    Used by orchestrator to decide routing (A/B/C/D).

    Args:
        intent: Parsed user intent
        config: RAG configuration (uses default if not provided)
        db: DatabaseManager instance (creates new if not provided)
        model_number: Equipment model number for filtering (optional)

    Returns:
        KBCoverage enum (strong/thin/none)

    Examples:
        >>> from agent_factory.rivet_pro.models import RivetIntent, VendorType, EquipmentType
        >>> intent = RivetIntent(
        ...     vendor=VendorType.SIEMENS,
        ...     equipment_type=EquipmentType.VFD,
        ...     symptom="F3002 overvoltage fault",
        ...     raw_summary="Siemens VFD F3002 troubleshooting",
        ...     context_source="text_only",
        ...     confidence=0.9,
        ...     kb_coverage="strong"  # Will be updated by this function
        ... )
        >>> coverage = estimate_coverage(intent, model_number="G120C")
        >>> coverage in [KBCoverage.STRONG, KBCoverage.THIN, KBCoverage.NONE]
        True
    """
    # Use default config if not provided
    if config is None:
        config = RAGConfig()

    # Search for relevant docs (with model filtering if provided)
    docs = search_docs(intent, config=config, db=db, model_number=model_number)

    # Calculate average similarity
    if not docs:
        avg_similarity = 0.0
    else:
        avg_similarity = sum(doc.similarity for doc in docs) / len(docs)

    # Assess coverage using config thresholds
    coverage = config.assess_coverage(
        num_docs=len(docs),
        avg_similarity=avg_similarity
    )

    logger.info(
        f"Coverage assessment: {coverage.value} "
        f"(docs={len(docs)}, avg_similarity={avg_similarity:.2f})"
    )

    return coverage

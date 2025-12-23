"""KB Coverage Evaluator for RIVET Pro queries.

Evaluates Knowledge Base coverage level (strong/thin/none/unclear) using Phase 2 RAG layer.
"""

from typing import Optional
from agent_factory.schemas.routing import (
    VendorType,
    CoverageLevel,
    KBCoverage,
    CoverageThresholds,
)
from agent_factory.rivet_pro.models import (
    RivetRequest,
    RivetIntent,
    EquipmentType,
    VendorType as RivetVendorType,
    KBCoverage as RivetKBCoverage,
)


class KBCoverageEvaluator:
    """Evaluates Knowledge Base coverage for queries."""

    # Mapping from routing VendorType to rivet_pro VendorType
    _VENDOR_MAP = {
        VendorType.SIEMENS: RivetVendorType.SIEMENS,
        VendorType.ROCKWELL: RivetVendorType.ROCKWELL,
        VendorType.GENERIC: RivetVendorType.GENERIC,
        VendorType.SAFETY: RivetVendorType.UNKNOWN,
    }

    def __init__(self, rag_layer=None):
        """Initialize KB evaluator.

        Args:
            rag_layer: Phase 2 RAG layer retriever (optional for testing)
        """
        self.rag = rag_layer

    def evaluate(self, request: RivetRequest, vendor: VendorType) -> KBCoverage:
        """Evaluate KB coverage for a query.

        Args:
            request: User query request
            vendor: Detected vendor type

        Returns:
            KBCoverage with level, metrics, and confidence
        """
        # TODO: Phase 3 dependency - real SME agents not yet implemented
        # Using mock evaluation for now
        if self.rag is None:
            return self._mock_evaluate(request, vendor)

        # Real evaluation using Phase 2 RAG layer
        try:
            from agent_factory.rivet_pro.rag.retriever import search_docs, estimate_coverage
            from agent_factory.rivet_pro.rag.config import RAGConfig

            # Convert routing VendorType to rivet_pro VendorType
            rivet_vendor = self._VENDOR_MAP.get(vendor, RivetVendorType.UNKNOWN)

            # Create intent from request (kb_coverage determined after search)
            intent = RivetIntent(
                vendor=rivet_vendor,
                equipment_type=EquipmentType.UNKNOWN,  # Could be parsed from request
                symptom=request.text or "",
                raw_summary=request.text or "",
                context_source="text_only",
                confidence=0.8,
                kb_coverage=RivetKBCoverage.NONE  # Placeholder, updated after search
            )

            # Search for relevant KB atoms with DatabaseManager
            config = RAGConfig(top_k=10)
            docs = search_docs(intent=intent, config=config, db=self.rag)

            # Calculate metrics from RetrievedDoc objects
            atom_count = len(docs)
            relevance_scores = [float(doc.similarity) for doc in docs]
            avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0

            # Classify coverage level
            level = self._classify_coverage(atom_count, avg_relevance)

            # Calculate confidence
            confidence = self._calculate_confidence(atom_count, relevance_scores)

            return KBCoverage(
                level=level,
                atom_count=atom_count,
                avg_relevance=avg_relevance,
                confidence=confidence,
                retrieved_docs=docs  # Include actual KB documents for SME agents
            )

        except ImportError:
            # Phase 2 RAG not available → fallback to mock
            return self._mock_evaluate(request, vendor)

    def _classify_coverage(self, atom_count: int, avg_relevance: float) -> CoverageLevel:
        """Classify coverage as strong, thin, or none.

        Classification rules:
        - STRONG: >=8 atoms AND avg_relevance >=0.7
        - THIN: 3-7 atoms OR avg_relevance 0.4-0.7
        - NONE: <3 atoms OR avg_relevance <0.4

        Args:
            atom_count: Number of retrieved atoms
            avg_relevance: Average relevance score

        Returns:
            CoverageLevel enum
        """
        if atom_count >= CoverageThresholds.STRONG_ATOM_COUNT and \
           avg_relevance >= CoverageThresholds.STRONG_RELEVANCE:
            return CoverageLevel.STRONG

        if atom_count < CoverageThresholds.THIN_ATOM_COUNT or \
           avg_relevance < CoverageThresholds.THIN_RELEVANCE:
            return CoverageLevel.NONE

        return CoverageLevel.THIN

    def _calculate_confidence(
        self,
        atom_count: int,
        relevance_scores: list[float]
    ) -> float:
        """Calculate confidence in coverage classification.

        Higher confidence when:
        - More atoms retrieved
        - Higher average relevance
        - Lower variance in relevance scores

        Args:
            atom_count: Number of retrieved atoms
            relevance_scores: List of relevance scores

        Returns:
            Confidence score 0-1
        """
        if not relevance_scores:
            return 0.0

        # Base confidence from atom count (0-8 atoms → 0.0-0.6 confidence)
        count_confidence = min(atom_count / 8.0, 1.0) * 0.6

        # Add relevance confidence (avg relevance → 0.0-0.3 confidence)
        avg_relevance = sum(relevance_scores) / len(relevance_scores)
        relevance_confidence = avg_relevance * 0.3

        # Subtract variance penalty (high variance → lower confidence)
        if len(relevance_scores) > 1:
            variance = sum((x - avg_relevance) ** 2 for x in relevance_scores) / len(relevance_scores)
            variance_penalty = min(variance, 0.1)  # Cap penalty at 0.1
        else:
            variance_penalty = 0.0

        confidence = count_confidence + relevance_confidence - variance_penalty
        return max(0.0, min(confidence, 1.0))  # Clamp to [0, 1]

    def _mock_evaluate(self, request: RivetRequest, vendor: VendorType) -> KBCoverage:
        """Mock evaluation for testing without Phase 2 RAG layer.

        Generates realistic coverage based on query length and vendor.

        Args:
            request: User query request
            vendor: Detected vendor type

        Returns:
            Mock KBCoverage
        """
        query_text = request.text or ""
        query_len = len(query_text)

        # Mock logic: longer queries → more specific → potentially better coverage
        if query_len > 100:
            # Long, detailed query → likely strong coverage
            return KBCoverage(
                level=CoverageLevel.STRONG,
                atom_count=12,
                avg_relevance=0.85,
                confidence=0.90,
                retrieved_docs=[]  # Mock mode - no real docs
            )
        elif query_len >= 50:
            # Medium query → thin coverage (50-100 chars)
            return KBCoverage(
                level=CoverageLevel.THIN,
                atom_count=5,
                avg_relevance=0.55,
                confidence=0.70,
                retrieved_docs=[]  # Mock mode - no real docs
            )
        elif "?" in query_text and query_len < 20:
            # Very short AND has question mark → unclear intent
            return KBCoverage(
                level=CoverageLevel.UNCLEAR,
                atom_count=1,
                avg_relevance=0.30,
                confidence=0.40,
                retrieved_docs=[]  # Mock mode - no real docs
            )
        else:
            # Short queries without "?" → no coverage
            return KBCoverage(
                level=CoverageLevel.NONE,
                atom_count=2,
                avg_relevance=0.35,
                confidence=0.50,
                retrieved_docs=[]  # Mock mode - no real docs
            )

    def is_strong_coverage(self, coverage: KBCoverage) -> bool:
        """Check if coverage is strong enough for Route A.

        Args:
            coverage: KBCoverage result

        Returns:
            True if coverage level is STRONG
        """
        return coverage.level == CoverageLevel.STRONG

    def is_thin_coverage(self, coverage: KBCoverage) -> bool:
        """Check if coverage is thin (Route B).

        Args:
            coverage: KBCoverage result

        Returns:
            True if coverage level is THIN
        """
        return coverage.level == CoverageLevel.THIN

    def is_no_coverage(self, coverage: KBCoverage) -> bool:
        """Check if coverage is none (Route C).

        Args:
            coverage: KBCoverage result

        Returns:
            True if coverage level is NONE
        """
        return coverage.level == CoverageLevel.NONE

    def is_unclear(self, coverage: KBCoverage) -> bool:
        """Check if query intent is unclear (Route D).

        Args:
            coverage: KBCoverage result

        Returns:
            True if coverage level is UNCLEAR
        """
        return coverage.level == CoverageLevel.UNCLEAR

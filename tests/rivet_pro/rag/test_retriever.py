"""
Tests for RIVET Pro RAG retriever module.

Author: Agent Factory
Created: 2025-12-17
Phase: 2/8 (RAG Layer)
"""

import pytest
from agent_factory.rivet_pro.models import (
    RivetIntent,
    VendorType,
    EquipmentType,
    ContextSource,
    KBCoverage
)
from agent_factory.rivet_pro.rag.config import RAGConfig
from agent_factory.rivet_pro.rag.retriever import search_docs, estimate_coverage, RetrievedDoc


class TestRetrievedDoc:
    """Test RetrievedDoc dataclass"""

    def test_create_retrieved_doc(self):
        """Test creating RetrievedDoc instance"""
        doc = RetrievedDoc(
            atom_id=1,
            title="Test Document",
            summary="Test summary",
            content="Test content",
            atom_type="concept",
            vendor="Siemens",
            equipment_type="VFD",
            similarity=0.85,
            source="test_manual.pdf",
            page_number=10
        )

        assert doc.atom_id == 1
        assert doc.title == "Test Document"
        assert doc.similarity == 0.85
        assert doc.vendor == "Siemens"

    def test_to_dict(self):
        """Test converting RetrievedDoc to dictionary"""
        doc = RetrievedDoc(
            atom_id=1,
            title="Test",
            summary="Summary",
            content="Content",
            atom_type="concept",
            vendor="Siemens",
            equipment_type="VFD",
            similarity=0.85
        )

        doc_dict = doc.to_dict()

        assert isinstance(doc_dict, dict)
        assert doc_dict["atom_id"] == 1
        assert doc_dict["title"] == "Test"
        assert doc_dict["similarity"] == 0.85


class TestRAGConfig:
    """Test RAG configuration"""

    def test_default_config(self):
        """Test default RAG configuration"""
        config = RAGConfig()

        assert config.search.top_k == 8
        assert config.search.similarity_threshold == 0.55
        assert config.search.use_hybrid_search is True
        assert config.coverage.strong_min_docs == 3
        assert config.coverage.strong_min_similarity == 0.75

    def test_custom_config(self):
        """Test custom RAG configuration"""
        from agent_factory.rivet_pro.rag.config import SearchConfig, CoverageThresholds

        config = RAGConfig(
            search=SearchConfig(top_k=10, similarity_threshold=0.60),
            coverage=CoverageThresholds(strong_min_docs=5, strong_min_similarity=0.80)
        )

        assert config.search.top_k == 10
        assert config.search.similarity_threshold == 0.60
        assert config.coverage.strong_min_docs == 5
        assert config.coverage.strong_min_similarity == 0.80

    def test_get_collections_for_intent(self):
        """Test collection matching for intent"""
        config = RAGConfig()

        # Test Siemens VFD
        collections = config.get_collections_for_intent(
            VendorType.SIEMENS,
            EquipmentType.VFD
        )

        assert len(collections) >= 1
        assert any(c.name == "siemens" for c in collections)
        # Should be sorted by priority
        assert collections[0].priority <= collections[-1].priority

    def test_assess_coverage_strong(self):
        """Test strong coverage assessment"""
        config = RAGConfig()

        coverage = config.assess_coverage(num_docs=5, avg_similarity=0.82)

        assert coverage == KBCoverage.STRONG

    def test_assess_coverage_thin(self):
        """Test thin coverage assessment"""
        config = RAGConfig()

        coverage = config.assess_coverage(num_docs=2, avg_similarity=0.65)

        assert coverage == KBCoverage.THIN

    def test_assess_coverage_none(self):
        """Test no coverage assessment"""
        config = RAGConfig()

        # No docs
        coverage = config.assess_coverage(num_docs=0, avg_similarity=0.0)
        assert coverage == KBCoverage.NONE

        # Low similarity
        coverage = config.assess_coverage(num_docs=2, avg_similarity=0.50)
        assert coverage == KBCoverage.NONE


class TestFilters:
    """Test intent-to-filter conversion"""

    def test_build_filters_with_vendor_and_equipment(self):
        """Test building filters with vendor and equipment type"""
        from agent_factory.rivet_pro.rag.filters import build_filters

        intent = RivetIntent(
            vendor=VendorType.SIEMENS,
            equipment_type=EquipmentType.VFD,
            raw_summary="Test query",
            context_source=ContextSource.TEXT_ONLY,
            confidence=0.9,
            kb_coverage=KBCoverage.STRONG
        )

        filters = build_filters(intent)

        assert filters["vendor"] == "Siemens"
        assert filters["equipment_type"] == "VFD"

    def test_build_filters_with_unknown(self):
        """Test building filters with unknown vendor/equipment"""
        from agent_factory.rivet_pro.rag.filters import build_filters

        intent = RivetIntent(
            vendor=VendorType.UNKNOWN,
            equipment_type=EquipmentType.UNKNOWN,
            raw_summary="Test query",
            context_source=ContextSource.TEXT_ONLY,
            confidence=0.5,
            kb_coverage=KBCoverage.NONE
        )

        filters = build_filters(intent)

        # Should not include unknown values
        assert "vendor" not in filters
        assert "equipment_type" not in filters

    def test_build_keyword_filters(self):
        """Test extracting keywords from intent"""
        from agent_factory.rivet_pro.rag.filters import build_keyword_filters

        intent = RivetIntent(
            vendor=VendorType.SIEMENS,
            equipment_type=EquipmentType.VFD,
            detected_model="G120C",
            detected_fault_codes=["F3002"],
            application="overhead_crane",
            raw_summary="VFD fault troubleshooting",
            context_source=ContextSource.TEXT_ONLY,
            confidence=0.9,
            kb_coverage=KBCoverage.STRONG
        )

        keywords = build_keyword_filters(intent)

        assert "G120C" in keywords
        assert "F3002" in keywords
        assert "overhead_crane" in keywords
        # Keywords from raw_summary
        assert any("vfd" in k.lower() for k in keywords)
        assert any("fault" in k.lower() for k in keywords)


# Note: search_docs() and estimate_coverage() require database connection
# These should be tested with integration tests using a test database
# Unit tests above cover the configuration and filter logic

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

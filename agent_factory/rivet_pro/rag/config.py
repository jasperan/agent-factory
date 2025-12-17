"""
RAG Configuration for RIVET Pro

Defines collection mappings, search parameters, and coverage thresholds
for knowledge base retrieval.

Author: Agent Factory
Created: 2025-12-17
Phase: 2/8 (RAG Layer)
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from agent_factory.rivet_pro.models import VendorType, EquipmentType, KBCoverage


class CollectionConfig(BaseModel):
    """Configuration for a single KB collection"""

    name: str = Field(
        ...,
        description="Collection name in database"
    )

    vendors: List[VendorType] = Field(
        ...,
        description="Vendors covered by this collection"
    )

    equipment_types: List[EquipmentType] = Field(
        ...,
        description="Equipment types covered by this collection"
    )

    priority: int = Field(
        ...,
        description="Search priority (1=highest, used for ranking when multiple collections match)"
    )


class CoverageThresholds(BaseModel):
    """Thresholds for determining KB coverage levels"""

    strong_min_docs: int = Field(
        default=3,
        description="Minimum docs retrieved to consider coverage 'strong'"
    )

    strong_min_similarity: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Minimum avg similarity score for 'strong' coverage"
    )

    thin_min_docs: int = Field(
        default=1,
        description="Minimum docs retrieved to consider coverage 'thin'"
    )

    thin_min_similarity: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Minimum avg similarity score for 'thin' coverage"
    )


class SearchConfig(BaseModel):
    """Configuration for document retrieval"""

    top_k: int = Field(
        default=8,
        description="Number of documents to retrieve per search"
    )

    similarity_threshold: float = Field(
        default=0.55,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score to include doc in results"
    )

    use_hybrid_search: bool = Field(
        default=True,
        description="Enable hybrid semantic + keyword search"
    )

    keyword_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for keyword search in hybrid mode (0.3 = 30% keyword, 70% semantic)"
    )


class RAGConfig(BaseModel):
    """
    Complete RAG configuration for RIVET Pro.

    Defines how to search the knowledge base, which collections to use,
    and how to assess KB coverage for routing decisions.

    Examples:
        # Default configuration
        config = RAGConfig()

        # Custom configuration
        config = RAGConfig(
            search=SearchConfig(top_k=10, similarity_threshold=0.60),
            coverage=CoverageThresholds(strong_min_docs=5)
        )
    """

    collections: List[CollectionConfig] = Field(
        default_factory=lambda: [
            # Siemens collection (highest priority for Siemens equipment)
            CollectionConfig(
                name="siemens",
                vendors=[VendorType.SIEMENS],
                equipment_types=[
                    EquipmentType.VFD,
                    EquipmentType.PLC,
                    EquipmentType.HMI,
                    EquipmentType.SERVO
                ],
                priority=1
            ),

            # Rockwell / Allen-Bradley collection
            CollectionConfig(
                name="rockwell",
                vendors=[VendorType.ROCKWELL, VendorType.ALLEN_BRADLEY],
                equipment_types=[
                    EquipmentType.PLC,
                    EquipmentType.HMI,
                    EquipmentType.VFD,
                    EquipmentType.SAFETY_RELAY
                ],
                priority=1
            ),

            # ABB collection
            CollectionConfig(
                name="abb",
                vendors=[VendorType.ABB],
                equipment_types=[
                    EquipmentType.VFD,
                    EquipmentType.SERVO,
                    EquipmentType.MCC
                ],
                priority=1
            ),

            # Generic PLC collection (fallback for any PLC)
            CollectionConfig(
                name="generic_plc",
                vendors=[
                    VendorType.MITSUBISHI,
                    VendorType.OMRON,
                    VendorType.SCHNEIDER,
                    VendorType.GENERIC,
                    VendorType.UNKNOWN
                ],
                equipment_types=[
                    EquipmentType.PLC,
                    EquipmentType.HMI
                ],
                priority=2
            ),

            # Safety systems collection (cross-vendor)
            CollectionConfig(
                name="safety",
                vendors=[
                    VendorType.SIEMENS,
                    VendorType.ROCKWELL,
                    VendorType.ABB,
                    VendorType.SCHNEIDER,
                    VendorType.GENERIC
                ],
                equipment_types=[
                    EquipmentType.SAFETY_RELAY
                ],
                priority=1
            ),

            # General industrial collection (cross-vendor, lower priority)
            CollectionConfig(
                name="general",
                vendors=[v for v in VendorType],
                equipment_types=[
                    EquipmentType.SENSOR,
                    EquipmentType.CONTACTOR,
                    EquipmentType.BREAKER,
                    EquipmentType.MOTOR,
                    EquipmentType.ENCODER,
                    EquipmentType.UNKNOWN
                ],
                priority=3
            )
        ],
        description="KB collection definitions"
    )

    search: SearchConfig = Field(
        default_factory=SearchConfig,
        description="Search parameters"
    )

    coverage: CoverageThresholds = Field(
        default_factory=CoverageThresholds,
        description="Coverage assessment thresholds"
    )

    def get_collections_for_intent(
        self,
        vendor: VendorType,
        equipment_type: EquipmentType
    ) -> List[CollectionConfig]:
        """
        Get relevant collections for a given intent.

        Returns collections sorted by priority (highest first).

        Args:
            vendor: Equipment vendor
            equipment_type: Equipment type

        Returns:
            List of matching CollectionConfig objects

        Examples:
            >>> config = RAGConfig()
            >>> collections = config.get_collections_for_intent(
            ...     VendorType.SIEMENS,
            ...     EquipmentType.VFD
            ... )
            >>> [c.name for c in collections]
            ['siemens', 'general']
        """
        matching = []

        for collection in self.collections:
            # Check if vendor and equipment type match
            vendor_match = vendor in collection.vendors
            equipment_match = equipment_type in collection.equipment_types

            if vendor_match and equipment_match:
                matching.append(collection)

        # Sort by priority (lower priority number = higher importance)
        matching.sort(key=lambda c: c.priority)

        return matching

    def assess_coverage(
        self,
        num_docs: int,
        avg_similarity: float
    ) -> KBCoverage:
        """
        Assess KB coverage based on retrieval results.

        Used by orchestrator to decide routing (A/B/C/D).

        Args:
            num_docs: Number of docs retrieved
            avg_similarity: Average similarity score of top docs

        Returns:
            KBCoverage enum (strong/thin/none)

        Examples:
            >>> config = RAGConfig()
            >>> config.assess_coverage(5, 0.82)
            <KBCoverage.STRONG: 'strong'>
            >>> config.assess_coverage(2, 0.65)
            <KBCoverage.THIN: 'thin'>
            >>> config.assess_coverage(0, 0.0)
            <KBCoverage.NONE: 'none'>
        """
        # No docs found
        if num_docs == 0:
            return KBCoverage.NONE

        # Strong coverage: sufficient docs with high similarity
        if (num_docs >= self.coverage.strong_min_docs and
            avg_similarity >= self.coverage.strong_min_similarity):
            return KBCoverage.STRONG

        # Thin coverage: some docs but weak matches
        if (num_docs >= self.coverage.thin_min_docs and
            avg_similarity >= self.coverage.thin_min_similarity):
            return KBCoverage.THIN

        # Below thresholds = no useful coverage
        return KBCoverage.NONE

    class Config:
        json_schema_extra = {
            "example": {
                "search": {
                    "top_k": 8,
                    "similarity_threshold": 0.55,
                    "use_hybrid_search": True,
                    "keyword_weight": 0.3
                },
                "coverage": {
                    "strong_min_docs": 3,
                    "strong_min_similarity": 0.75,
                    "thin_min_docs": 1,
                    "thin_min_similarity": 0.60
                }
            }
        }

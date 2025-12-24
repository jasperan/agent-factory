"""Routing schemas for RIVET Pro Orchestrator.

Pydantic models for routing decisions, vendor detection, and KB coverage evaluation.
"""

from enum import Enum
from typing import Optional, List, Any
from pydantic import BaseModel, Field


class VendorType(str, Enum):
    """PLC vendor types supported by RIVET Pro."""

    SIEMENS = "siemens"
    ROCKWELL = "rockwell_automation"
    GENERIC = "generic_plc"
    SAFETY = "safety"


class CoverageLevel(str, Enum):
    """Knowledge Base coverage levels."""

    STRONG = "strong"  # >8 atoms, avg relevance >0.7
    THIN = "thin"      # 3-7 atoms, or avg relevance 0.4-0.7
    NONE = "none"      # <3 atoms, or avg relevance <0.4
    UNCLEAR = "unclear"  # Query intent is ambiguous


class KBCoverage(BaseModel):
    """Knowledge Base coverage metrics for a query."""

    level: CoverageLevel = Field(
        ...,
        description="Coverage classification: strong, thin, none, or unclear"
    )
    atom_count: int = Field(
        ...,
        ge=0,
        description="Number of relevant KB atoms found"
    )
    avg_relevance: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Average relevance score of retrieved atoms"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in coverage classification"
    )
    retrieved_docs: List[Any] = Field(
        default_factory=list,
        description="Retrieved KB documents (RetrievedDoc objects from RAG layer)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "level": "strong",
                "atom_count": 12,
                "avg_relevance": 0.85,
                "confidence": 0.92,
                "retrieved_docs": []
            }
        }


class RouteType(str, Enum):
    """Orchestrator routing paths."""

    ROUTE_A = "A"  # Strong KB → direct answer
    ROUTE_B = "B"  # Thin KB → answer + enrichment trigger
    ROUTE_C = "C"  # No KB → research pipeline trigger
    ROUTE_D = "D"  # Unclear → clarification request


class VendorDetection(BaseModel):
    """Vendor detection result with confidence score."""

    vendor: VendorType = Field(
        ...,
        description="Detected vendor type"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in vendor detection"
    )
    keywords_matched: list[str] = Field(
        default_factory=list,
        description="Vendor keywords found in query"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "vendor": "siemens",
                "confidence": 0.95,
                "keywords_matched": ["siemens", "sinamics", "s7-1200"]
            }
        }


class RoutingDecision(BaseModel):
    """Complete routing decision with reasoning."""

    route: RouteType = Field(
        ...,
        description="Selected route: A, B, C, or D"
    )
    vendor_detection: VendorDetection = Field(
        ...,
        description="Vendor detection result"
    )
    kb_coverage: KBCoverage = Field(
        ...,
        description="Knowledge base coverage metrics"
    )
    reasoning: str = Field(
        ...,
        min_length=10,
        description="Human-readable explanation of routing decision"
    )
    sme_agent: Optional[str] = Field(
        None,
        description="SME agent to route to (for routes A and B)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "route": "A",
                "vendor_detection": {
                    "vendor": "siemens",
                    "confidence": 0.95,
                    "keywords_matched": ["siemens", "sinamics"]
                },
                "kb_coverage": {
                    "level": "strong",
                    "atom_count": 12,
                    "avg_relevance": 0.85,
                    "confidence": 0.92
                },
                "reasoning": "Strong KB coverage (12 atoms, 0.85 relevance) for Siemens query. Routing to Siemens SME agent for direct answer.",
                "sme_agent": "siemens_agent"
            }
        }


# Thresholds for coverage classification
class CoverageThresholds:
    """Thresholds for KB coverage classification."""

    # Atom count thresholds (lowered for small KB - 1,964 atoms)
    STRONG_ATOM_COUNT = 3          # Was: 8 (lowered for growing KB)
    THIN_ATOM_COUNT = 1            # Was: 3 (very permissive)

    # Relevance score thresholds (lowered to work with ts_rank scores)
    STRONG_RELEVANCE = 0.05        # Was: 0.7 (allows PostgreSQL ts_rank scores)
    THIN_RELEVANCE = 0.0           # Was: 0.4 (any match counts)

    # Confidence thresholds
    MIN_VENDOR_CONFIDENCE = 0.6
    MIN_COVERAGE_CONFIDENCE = 0.5

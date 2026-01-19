"""
Knowledge Gap Detector - Analyzes queries and triggers document ingestion.

Detects equipment identifiers, checks KB coverage, and generates structured
ingestion triggers for autonomous knowledge base enrichment.

ULTRA-AGGRESSIVE MODE: Logs gaps on EVERY interaction and triggers immediate research.
"""
import re
import json
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass

from agent_factory.rivet_pro.models import (
    RivetRequest,
    RivetIntent,
    VendorType,
    EquipmentType,
    ChannelType,
    MessageType
)
from agent_factory.routers.kb_evaluator import KBCoverageEvaluator
from agent_factory.schemas.routing import CoverageLevel

logger = logging.getLogger(__name__)

# ULTRA-AGGRESSIVE MODE: Import research trigger components
try:
    from agent_factory.observability.phoenix_trace_analyzer import WeaknessType, WeaknessSignal
    from agent_factory.core.kb_gap_logger import KBGapLogger
    AGGRESSIVE_MODE_AVAILABLE = True
except ImportError:
    AGGRESSIVE_MODE_AVAILABLE = False
    logger.warning("Ultra-aggressive mode unavailable - missing dependencies")
    
    # Fallback definitions to prevent NameError in type hints and methods
    class WeaknessType(str, Enum):
        ZERO_ATOMS = "zero_atoms"
        THIN_COVERAGE = "thin_coverage"
        LOW_RELEVANCE = "low_relevance"
        HALLUCINATION_RISK = "hallucination_risk"
        MISSING_CITATIONS = "missing_citations"
        HIGH_LATENCY = "high_latency"

    class WeaknessSignal:
        pass


class GapPriority(str, Enum):
    """Priority levels for ingestion triggers."""
    HIGH = "high"      # Critical equipment, safety-related
    MEDIUM = "medium"  # Standard troubleshooting
    LOW = "low"        # General questions, common knowledge


class IngestionSource(str, Enum):
    """Sources to search for documentation."""
    MANUFACTURER_WEBSITE = "manufacturer_website"
    MANUALSLIB = "manualslib"
    PARTS_DIAGRAMS = "parts_diagrams"
    SERVICE_BULLETINS = "service_bulletins"
    INDUSTRY_FORUMS = "industry_forums"
    TECHNICAL_STANDARDS = "technical_standards"


class GapDetector:
    """Detects knowledge gaps and generates ingestion triggers."""

    # Equipment identifier patterns
    MODEL_NUMBER_PATTERNS = [
        r'\b[A-Z]{1,3}[-\s]?\d{3,6}[A-Z]?\b',  # S7-1200, G120C, etc.
        r'\b\d{4}[-/]\d{2,4}\b',                 # 1756-L83E, etc.
        r'\b[A-Z]\d{2,4}[A-Z]{0,2}\b',          # F0003, E123, etc.
    ]

    # Equipment type keywords
    EQUIPMENT_TYPES = {
        'drive': ['drive', 'vfd', 'inverter', 'frequency converter'],
        'plc': ['plc', 'controller', 'cpu', 'processor'],
        'hmi': ['hmi', 'panel view', 'touch panel', 'display'],
        'motor': ['motor', 'servo', 'stepper'],
        'sensor': ['sensor', 'encoder', 'proximity', 'photoelectric'],
        'safety': ['safety relay', 'e-stop', 'light curtain', 'safety plc'],
    }

    # Safety-related keywords (high priority)
    SAFETY_KEYWORDS = [
        'safety', 'lockout', 'tagout', 'loto', 'emergency stop', 'e-stop',
        'fail-safe', 'safety rated', 'sil', 'category'
    ]

    def __init__(self, kb_evaluator: KBCoverageEvaluator):
        """
        Initialize gap detector.

        Args:
            kb_evaluator: KB coverage evaluator for checking existing coverage
        """
        self.kb_evaluator = kb_evaluator

    def analyze_query(
        self,
        request: RivetRequest,
        intent: RivetIntent,
        kb_coverage: CoverageLevel
    ) -> Optional[Dict]:
        """
        Analyze query and generate ingestion trigger if gap detected.

        Args:
            request: Original user request
            intent: Parsed intent with vendor, equipment, symptom
            kb_coverage: KB coverage level (from evaluator)

        Returns:
            Ingestion trigger dict if gap detected, None otherwise
        """
        # Only trigger for NONE or THIN coverage
        if kb_coverage not in [CoverageLevel.NONE, CoverageLevel.THIN]:
            logger.debug(f"Coverage {kb_coverage.value} - no ingestion trigger needed")
            return None

        query_text = request.text or request.image_text or ""

        # Extract equipment identifiers
        equipment_ids = self._extract_equipment_identifiers(query_text)

        # Determine priority
        priority = self._determine_priority(query_text, intent)

        # Generate search terms
        search_terms = self._generate_search_terms(
            query_text, intent, equipment_ids
        )

        # Determine sources to try
        sources = self._determine_sources(intent, priority)

        # Build ingestion trigger
        trigger = {
            "trigger": "knowledge_gap",
            "query_text": query_text[:500],  # Truncate for storage
            "equipment_identified": ", ".join(equipment_ids) if equipment_ids else "unknown",
            "vendor": intent.vendor.value if intent.vendor else "unknown",
            "equipment_type": intent.equipment_type.value if intent.equipment_type else "unknown",
            "symptom": intent.symptom[:200] if intent.symptom else "",
            "search_terms": search_terms,
            "priority": priority.value,
            "sources_to_try": [s.value for s in sources],
            "timestamp": datetime.utcnow().isoformat(),
            "kb_coverage": kb_coverage.value
        }

        logger.info(
            f"Generated ingestion trigger: priority={priority.value}, "
            f"equipment={trigger['equipment_identified']}, "
            f"search_terms={len(search_terms)}"
        )

        return trigger

    def _extract_equipment_identifiers(self, text: str) -> List[str]:
        """
        Extract equipment identifiers from query text.

        Args:
            text: Query text to analyze

        Returns:
            List of identified equipment models, part numbers, etc.
        """
        identifiers = []
        text_upper = text.upper()

        # Try each model number pattern
        for pattern in self.MODEL_NUMBER_PATTERNS:
            matches = re.findall(pattern, text_upper)
            identifiers.extend(matches)

        # Remove duplicates while preserving order
        seen = set()
        unique_ids = []
        for id in identifiers:
            normalized = id.replace(' ', '').replace('-', '')
            if normalized not in seen:
                seen.add(normalized)
                unique_ids.append(id)

        return unique_ids[:5]  # Limit to 5 most relevant

    def _determine_priority(
        self, query_text: str, intent: RivetIntent
    ) -> GapPriority:
        """
        Determine ingestion priority based on query content.

        Args:
            query_text: Original query text
            intent: Parsed intent

        Returns:
            Priority level (HIGH, MEDIUM, LOW)
        """
        text_lower = query_text.lower()

        # HIGH: Safety-related or critical equipment
        for keyword in self.SAFETY_KEYWORDS:
            if keyword in text_lower:
                return GapPriority.HIGH

        # HIGH: Specific fault codes or error messages
        if any(word in text_lower for word in ['fault', 'error', 'alarm', 'trip']):
            return GapPriority.HIGH

        # MEDIUM: Equipment troubleshooting
        if any(word in text_lower for word in ['troubleshoot', 'diagnose', 'fix', 'repair']):
            return GapPriority.MEDIUM

        # MEDIUM: Specific vendor queries
        if intent.vendor and intent.vendor != VendorType.GENERIC:
            return GapPriority.MEDIUM

        # LOW: General questions
        return GapPriority.LOW

    def _generate_search_terms(
        self,
        query_text: str,
        intent: RivetIntent,
        equipment_ids: List[str]
    ) -> List[str]:
        """
        Generate search terms for document ingestion.

        Args:
            query_text: Original query text
            intent: Parsed intent
            equipment_ids: Extracted equipment identifiers

        Returns:
            List of search terms for finding documentation
        """
        terms = []

        # Add equipment identifiers
        for eq_id in equipment_ids:
            terms.append(f'"{eq_id}" manual filetype:pdf')
            terms.append(f'"{eq_id}" troubleshooting guide')

        # Add vendor + equipment type
        if intent.vendor and intent.vendor != VendorType.GENERIC:
            vendor_name = intent.vendor.value.replace('_', ' ')
            if intent.equipment_type and intent.equipment_type != EquipmentType.UNKNOWN:
                eq_type = intent.equipment_type.value.replace('_', ' ')
                terms.append(f'{vendor_name} {eq_type} manual filetype:pdf')
                terms.append(f'{vendor_name} {eq_type} service bulletin')

        # Add fault code searches
        fault_codes = re.findall(r'\b[FE]\d{3,5}\b', query_text.upper())
        for code in fault_codes[:3]:  # Limit to 3
            if equipment_ids:
                terms.append(f'{equipment_ids[0]} {code} fault code')

        # Add manufacturer website if known
        if intent.vendor and intent.vendor != VendorType.GENERIC:
            vendor_name = intent.vendor.value.lower()
            if vendor_name == 'siemens':
                terms.append('site:siemens.com technical documentation')
            elif vendor_name in ['rockwell', 'allen_bradley']:
                terms.append('site:rockwellautomation.com literature library')

        return terms[:10]  # Limit to 10 search terms

    def _determine_sources(
        self, intent: RivetIntent, priority: GapPriority
    ) -> List[IngestionSource]:
        """
        Determine which sources to search based on intent and priority.

        Args:
            intent: Parsed intent
            priority: Ingestion priority

        Returns:
            List of sources to search (in order of preference)
        """
        sources = []

        # Always try manufacturer website first
        sources.append(IngestionSource.MANUFACTURER_WEBSITE)

        # Add manualslib for all equipment queries
        sources.append(IngestionSource.MANUALSLIB)

        # High priority: add service bulletins
        if priority == GapPriority.HIGH:
            sources.append(IngestionSource.SERVICE_BULLETINS)

        # Safety queries: add technical standards
        if intent.equipment_type == EquipmentType.SAFETY_RELAY:
            sources.append(IngestionSource.TECHNICAL_STANDARDS)

        # Medium/Low priority: add industry forums
        if priority in [GapPriority.MEDIUM, GapPriority.LOW]:
            sources.append(IngestionSource.INDUSTRY_FORUMS)

        return sources

    def format_trigger_for_display(self, trigger: Dict) -> str:
        """
        Format ingestion trigger for display in bot response.

        Args:
            trigger: Ingestion trigger dictionary

        Returns:
            Formatted string for user display
        """
        return (
            f"\n\n[INGESTION_TRIGGER]\n"
            f"Equipment: {trigger['equipment_identified']}\n"
            f"Priority: {trigger['priority'].upper()}\n"
            f"Search terms: {len(trigger['search_terms'])}\n"
            f"Status: Queued for research\n"
            f"[/INGESTION_TRIGGER]"
        )

    def format_trigger_for_logging(self, trigger: Dict) -> str:
        """
        Format ingestion trigger for logging/database storage.

        Args:
            trigger: Ingestion trigger dictionary

        Returns:
            JSON string for storage
        """
        return json.dumps(trigger, indent=2)

    # ========================================================================
    # ULTRA-AGGRESSIVE MODE: Log gaps on EVERY interaction
    # ========================================================================

    async def detect_and_log_gap_aggressive(
        self,
        request: RivetRequest,
        intent: RivetIntent,
        kb_coverage: CoverageLevel,
        atoms_found: int = 0,
        confidence: float = 0.0,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        ULTRA-AGGRESSIVE MODE: Log gap for EVERY interaction.

        Unlike analyze_query() which only triggers on NONE/THIN coverage,
        this logs EVERY user interaction as a potential gap and triggers research.

        Args:
            request: Original user request
            intent: Parsed intent
            kb_coverage: Coverage level (logs regardless of value)
            atoms_found: Number of atoms found in KB
            confidence: Routing confidence score
            context: Additional context

        Returns:
            gap_id if logged, None if failed
        """
        if not AGGRESSIVE_MODE_AVAILABLE:
            logger.warning("Ultra-aggressive mode disabled - dependencies unavailable")
            return None

        try:
            query_text = request.text or request.image_text or ""

            # Determine weakness type
            weakness_type = self._map_coverage_to_weakness(
                kb_coverage, atoms_found, confidence
            )

            # Calculate priority score (0-100)
            priority_score = self._calculate_priority_score(
                weakness_type, kb_coverage, atoms_found, confidence
            )

            # Build equipment string
            equipment = f"{intent.vendor.value if intent.vendor else 'unknown'}:{intent.equipment_type.value if intent.equipment_type else 'unknown'}"

            # Create WeaknessSignal
            weakness = WeaknessSignal(
                weakness_type=weakness_type,
                priority_score=priority_score,
                query_text=query_text,
                equipment_detected=equipment,
                atoms_found=atoms_found,
                confidence=confidence,
                relevance_scores=[],  # Not available in this context
                trace_id="",  # Not from Phoenix trace
                timestamp=datetime.utcnow(),
                context=context or {}
            )

            # Log to gap_requests (triggers auto-research)
            gap_logger = KBGapLogger()
            gap_id = await gap_logger.log_weakness_signal(weakness)

            logger.info(
                f"AGGRESSIVE MODE: Logged gap_id={gap_id}, "
                f"weakness={weakness_type.value}, priority={priority_score}"
            )

            return gap_id

        except Exception as e:
            logger.error(f"Failed to log aggressive gap: {e}", exc_info=True)
            return None

    def _map_coverage_to_weakness(
        self, kb_coverage: CoverageLevel, atoms_found: int, confidence: float
    ) -> WeaknessType:
        """Map KB coverage to WeaknessType enum."""
        if kb_coverage == CoverageLevel.NONE or atoms_found == 0:
            return WeaknessType.ZERO_ATOMS
        elif kb_coverage == CoverageLevel.THIN or atoms_found < 3:
            return WeaknessType.THIN_COVERAGE
        elif confidence < 0.5:
            return WeaknessType.LOW_RELEVANCE
        else:
            # Even with good coverage, log as thin_coverage to ensure research
            return WeaknessType.THIN_COVERAGE

    def _calculate_priority_score(
        self,
        weakness_type: WeaknessType,
        kb_coverage: CoverageLevel,
        atoms_found: int,
        confidence: float
    ) -> int:
        """
        Calculate priority score (0-100) for gap.

        Higher priority = more urgent research needed.
        """
        base_priority = {
            WeaknessType.ZERO_ATOMS: 100,
            WeaknessType.HALLUCINATION_RISK: 95,
            WeaknessType.THIN_COVERAGE: 70,
            WeaknessType.LOW_RELEVANCE: 50,
            WeaknessType.MISSING_CITATIONS: 40,
            WeaknessType.HIGH_LATENCY: 30,
        }.get(weakness_type, 50)

        # Boost priority if confidence is very low
        if confidence < 0.3:
            base_priority = min(100, base_priority + 20)

        # Boost priority if zero atoms
        if atoms_found == 0:
            base_priority = min(100, base_priority + 10)

        return base_priority


# ========================================================================
# GLOBAL CONVENIENCE FUNCTIONS (for easy integration)
# ========================================================================

async def log_every_interaction(
    user_query: str,
    vendor: str = "unknown",
    equipment_type: str = "unknown",
    atoms_found: int = 0,
    confidence: float = 0.0,
    kb_coverage: str = "none",
    context: Optional[Dict[str, Any]] = None
) -> Optional[int]:
    """
    ULTRA-AGGRESSIVE MODE: Log EVERY user interaction as potential gap.

    Call this after EVERY agent interaction to ensure comprehensive research.

    Args:
        user_query: User's query text
        vendor: Vendor name (e.g., "siemens", "rockwell")
        equipment_type: Equipment type (e.g., "plc", "drive")
        atoms_found: Number of KB atoms found
        confidence: Routing confidence (0.0-1.0)
        kb_coverage: Coverage level ("none", "thin", "partial", "good")
        context: Additional context

    Returns:
        gap_id if logged, None if failed

    Example:
        gap_id = await log_every_interaction(
            user_query="How to reset S7-1200 fault F0003?",
            vendor="siemens",
            equipment_type="plc",
            atoms_found=2,
            confidence=0.4,
            kb_coverage="thin"
        )
    """
    if not AGGRESSIVE_MODE_AVAILABLE:
        logger.warning("Aggressive mode unavailable - skipping gap log")
        return None

    try:
        # Build RivetRequest
        request = RivetRequest(
            user_id="system",
            channel=ChannelType.API,
            message_type=MessageType.TEXT,
            text=user_query,
            metadata={"source": "aggressive_mode"}
        )

        # Build RivetIntent
        try:
            vendor_enum = VendorType(vendor.lower())
        except ValueError:
            vendor_enum = VendorType.GENERIC

        try:
            equipment_enum = EquipmentType(equipment_type.lower())
        except ValueError:
            equipment_enum = EquipmentType.UNKNOWN

        intent = RivetIntent(
            vendor=vendor_enum,
            equipment_type=equipment_enum,
            symptom=user_query[:200],
            raw_question=user_query
        )

        # Map coverage string to enum
        coverage_map = {
            "none": CoverageLevel.NONE,
            "thin": CoverageLevel.THIN,
            "partial": CoverageLevel.PARTIAL,
            "good": CoverageLevel.GOOD,
        }
        kb_coverage_enum = coverage_map.get(kb_coverage.lower(), CoverageLevel.NONE)

        # Create detector (with mock evaluator since we don't need it)
        detector = GapDetector(kb_evaluator=None)  # type: ignore

        # Log gap
        gap_id = await detector.detect_and_log_gap_aggressive(
            request=request,
            intent=intent,
            kb_coverage=kb_coverage_enum,
            atoms_found=atoms_found,
            confidence=confidence,
            context=context
        )

        return gap_id

    except Exception as e:
        logger.error(f"Failed to log interaction gap: {e}", exc_info=True)
        return None

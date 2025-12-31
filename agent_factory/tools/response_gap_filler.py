"""
Knowledge Gap Detector and Filler - Integration for RivetCEO Bot

This module detects when the knowledge base cannot answer a query
and automatically triggers research to fill the gap.

Usage:
    from agent_factory.tools.response_gap_filler import KnowledgeGapFiller

    filler = KnowledgeGapFiller(kb_client=supabase_client)

    # In your orchestrator
    if response.confidence < 0.6:
        gap = await filler.detect_gap(query, response)
        if gap:
            filled = await filler.fill_gap(gap)
            # New atoms are now in KB
"""

import asyncio
import hashlib
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

from .research_executor import (
    ResearchExecutorTool,
    ResearchResult,
    ResearchTask,
    ResearchPriority,
    ExtractedFaultCode,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Models
# ============================================================================

class GapType(str, Enum):
    """Types of knowledge gaps"""
    UNKNOWN_MANUFACTURER = "unknown_manufacturer"
    UNKNOWN_MODEL = "unknown_model"
    MISSING_FAULT_CODE = "missing_fault_code"
    INCOMPLETE_PROCEDURE = "incomplete_procedure"
    OUTDATED_INFO = "outdated_info"
    NO_MATCH = "no_match"


class KnowledgeGap(BaseModel):
    """Detected knowledge gap"""
    gap_id: str = Field(default_factory=lambda: str(uuid4()))
    gap_type: GapType
    description: str

    # Context from the original query
    original_query: str
    extracted_manufacturer: Optional[str] = None
    extracted_equipment_type: Optional[str] = None
    extracted_model: Optional[str] = None
    extracted_fault_code: Optional[str] = None

    # KB search results that triggered gap detection
    search_results_count: int = 0
    best_match_score: float = 0.0

    # Metadata
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    priority: ResearchPriority = ResearchPriority.MEDIUM

    class Config:
        use_enum_values = True


class FilledGap(BaseModel):
    """Result of filling a knowledge gap"""
    gap: KnowledgeGap
    research_result: ResearchResult

    # Created atoms
    atoms_created: List[str] = Field(default_factory=list, description="IDs of created atoms")
    atoms_updated: List[str] = Field(default_factory=list, description="IDs of updated atoms")

    # Quality metrics
    fill_successful: bool = False
    confidence: float = 0.0

    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class AtomCandidate(BaseModel):
    """Candidate atom to be inserted into knowledge base"""
    id: str
    title: str
    content: str
    domain: str = "industrial"
    equipment_type: Optional[str] = None
    manufacturer: Optional[str] = None

    # From research
    fault_codes: List[Dict[str, Any]] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    citations: str = ""

    # Quality
    confidence_score: float = 0.0

    # Embedding placeholder
    embedding: Optional[List[float]] = None


# ============================================================================
# Gap Detector
# ============================================================================

class ResponseGapDetector:
    """
    Detects knowledge gaps from low-confidence responses in agent outputs.

    Triggers gap detection when:
    - No results found for a query
    - Low confidence scores
    - Missing information for known equipment
    - Unknown manufacturer/model mentioned
    """

    # Keywords that indicate specific equipment
    EQUIPMENT_KEYWORDS = {
        "vfd": "VFD",
        "drive": "VFD",
        "inverter": "VFD",
        "plc": "PLC",
        "hmi": "HMI",
        "motor": "Motor",
        "servo": "Servo",
        "sensor": "Sensor",
        "relay": "Relay",
        "contactor": "Contactor",
        "breaker": "Circuit Breaker",
    }

    # Known manufacturers (expand this list)
    KNOWN_MANUFACTURERS = {
        "siemens", "allen-bradley", "allen bradley", "ab", "rockwell",
        "schneider", "abb", "mitsubishi", "omron", "fanuc", "yaskawa",
        "danfoss", "lenze", "sew", "nord", "weg", "nidec", "emerson",
        "ge", "honeywell", "phoenix contact", "wago", "beckhoff",
        "keyence", "banner", "sick", "ifm", "turck", "balluff",
    }

    def __init__(
        self,
        confidence_threshold: float = 0.6,
        min_results_threshold: int = 1,
    ):
        self.confidence_threshold = confidence_threshold
        self.min_results_threshold = min_results_threshold

    def detect(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
        response_confidence: float,
    ) -> Optional[KnowledgeGap]:
        """
        Analyze query and results to detect knowledge gaps.

        Args:
            query: Original user query
            search_results: Results from KB vector search
            response_confidence: Confidence score of generated response

        Returns:
            KnowledgeGap if detected, None otherwise
        """
        query_lower = query.lower()

        # Extract entities from query
        manufacturer = self._extract_manufacturer(query_lower)
        equipment_type = self._extract_equipment_type(query_lower)
        fault_code = self._extract_fault_code(query)
        model = self._extract_model(query)

        best_score = max((r.get("score", 0) for r in search_results), default=0)

        # Decision logic for gap detection
        gap_type = None
        description = ""
        priority = ResearchPriority.MEDIUM

        # Case 1: No results at all
        if len(search_results) < self.min_results_threshold:
            gap_type = GapType.NO_MATCH
            description = f"No knowledge base matches for: {query[:100]}"
            priority = ResearchPriority.HIGH

        # Case 2: Low confidence response
        elif response_confidence < self.confidence_threshold:
            if manufacturer and manufacturer not in self._get_known_kb_manufacturers():
                gap_type = GapType.UNKNOWN_MANUFACTURER
                description = f"Unknown manufacturer: {manufacturer}"
                priority = ResearchPriority.HIGH
            elif fault_code:
                gap_type = GapType.MISSING_FAULT_CODE
                description = f"Missing fault code documentation: {fault_code}"
                priority = ResearchPriority.CRITICAL
            else:
                gap_type = GapType.INCOMPLETE_PROCEDURE
                description = f"Incomplete information for query: {query[:100]}"
                priority = ResearchPriority.MEDIUM

        # Case 3: Fault code query with poor match
        elif fault_code and best_score < 0.7:
            gap_type = GapType.MISSING_FAULT_CODE
            description = f"Fault code {fault_code} not well documented"
            priority = ResearchPriority.HIGH

        # Case 4: Unknown model mentioned
        elif model and best_score < 0.6:
            gap_type = GapType.UNKNOWN_MODEL
            description = f"Unknown model: {model}"
            priority = ResearchPriority.MEDIUM

        if gap_type:
            return KnowledgeGap(
                gap_type=gap_type,
                description=description,
                original_query=query,
                extracted_manufacturer=manufacturer,
                extracted_equipment_type=equipment_type,
                extracted_model=model,
                extracted_fault_code=fault_code,
                search_results_count=len(search_results),
                best_match_score=best_score,
                priority=priority,
            )

        return None

    def _extract_manufacturer(self, query: str) -> Optional[str]:
        """Extract manufacturer name from query"""
        for mfr in self.KNOWN_MANUFACTURERS:
            if mfr in query:
                # Normalize manufacturer name
                return mfr.replace("-", " ").title()
        return None

    def _extract_equipment_type(self, query: str) -> Optional[str]:
        """Extract equipment type from query"""
        for keyword, eq_type in self.EQUIPMENT_KEYWORDS.items():
            if keyword in query:
                return eq_type
        return None

    def _extract_fault_code(self, query: str) -> Optional[str]:
        """Extract fault code from query"""
        import re

        # Common fault code patterns
        patterns = [
            r'\b[Ff](?:ault)?[\s\-_]?(\d{1,4})\b',  # F001, Fault 123
            r'\b[Ee](?:rror)?[\s\-_]?(\d{1,4})\b',  # E001, Error 123
            r'\b[Aa](?:larm)?[\s\-_]?(\d{1,4})\b',  # A001, Alarm 123
            r'\b([A-Z]{1,3}\d{3,5})\b',              # ABC123, AB1234
        ]

        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(0).upper()

        return None

    def _extract_model(self, query: str) -> Optional[str]:
        """Extract model number from query"""
        import re

        # Common model patterns
        patterns = [
            r'\b([A-Z]{2,4}[\-\s]?\d{3,5}[A-Z]?)\b',  # S7-1200, AB-1756
            r'\b(\d{4}[\-\s]?[A-Z]{1,3})\b',          # 1756-L8
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).upper()

        return None

    def _get_known_kb_manufacturers(self) -> set:
        """Get manufacturers already in KB (stub - connect to actual KB)"""
        # TODO: Query actual KB for known manufacturers
        return {"siemens", "allen bradley", "rockwell", "abb", "schneider"}


# ============================================================================
# Gap Filler
# ============================================================================

class KnowledgeGapFiller:
    """
    Fills knowledge gaps using autonomous research.

    Workflow:
    1. Receive detected gap
    2. Generate research task
    3. Execute research via ResearchExecutorTool
    4. Parse results into atom candidates
    5. Insert atoms into knowledge base
    6. Return filled gap report
    """

    def __init__(
        self,
        kb_client: Any = None,  # Supabase client
        research_executor: Optional[ResearchExecutorTool] = None,
        auto_insert: bool = True,
        require_approval: bool = False,
    ):
        self.kb_client = kb_client
        self.research_executor = research_executor or ResearchExecutorTool()
        self.auto_insert = auto_insert
        self.require_approval = require_approval

        self.gap_detector = ResponseGapDetector()
        self._pending_atoms: Dict[str, AtomCandidate] = {}
        self._db_manager = None  # Lazy-init singleton

    @property
    def db_manager(self):
        """Lazy-init singleton DatabaseManager"""
        if self._db_manager is None:
            from agent_factory.core.database_manager import DatabaseManager
            self._db_manager = DatabaseManager()
        return self._db_manager

    async def detect_and_fill(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
        response_confidence: float,
    ) -> Optional[FilledGap]:
        """
        Detect gap and fill it if found.

        Convenience method that combines detection and filling.
        """
        gap = self.gap_detector.detect(query, search_results, response_confidence)

        if gap:
            logger.info(f"Detected knowledge gap: {gap.gap_type} - {gap.description}")
            return await self.fill_gap(gap)

        return None

    async def fill_gap(self, gap: KnowledgeGap) -> FilledGap:
        """
        Fill a detected knowledge gap via research.

        Args:
            gap: The detected knowledge gap

        Returns:
            FilledGap with research results and created atoms
        """
        started_at = datetime.utcnow()

        # Build research task from gap
        task = self._build_research_task(gap)

        logger.info(f"Starting research to fill gap: {gap.gap_id}")

        # Execute research
        research_result = await self.research_executor.execute(task)

        # Parse into atom candidates
        atom_candidates = self._parse_atoms(gap, research_result)

        # Insert atoms if auto_insert enabled
        atoms_created = []
        atoms_updated = []

        if self.auto_insert and atom_candidates:
            if self.require_approval:
                # Store for approval
                for atom in atom_candidates:
                    self._pending_atoms[atom.id] = atom
                logger.info(f"Stored {len(atom_candidates)} atoms pending approval")
            else:
                # Auto-insert
                atoms_created, atoms_updated, failures = await self._insert_atoms(atom_candidates)
                if failures:
                    logger.warning(f"Failed to insert {len(failures)} atoms: {[f['atom_id'] for f in failures]}")

        completed_at = datetime.utcnow()
        duration = (completed_at - started_at).total_seconds()

        filled = FilledGap(
            gap=gap,
            research_result=research_result,
            atoms_created=atoms_created,
            atoms_updated=atoms_updated,
            fill_successful=research_result.status == "completed" and len(atoms_created) > 0,
            confidence=research_result.confidence_score,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
        )

        logger.info(
            f"Gap fill completed: {len(atoms_created)} created, "
            f"{len(atoms_updated)} updated, "
            f"confidence={filled.confidence:.0%}"
        )

        return filled

    def _build_research_task(self, gap: KnowledgeGap) -> ResearchTask:
        """Build research task from gap"""

        specific_queries = []

        if gap.gap_type == GapType.UNKNOWN_MANUFACTURER:
            specific_queries = [
                f"Official {gap.extracted_manufacturer} documentation",
                f"{gap.extracted_manufacturer} {gap.extracted_equipment_type or 'equipment'} manuals",
                f"Common {gap.extracted_manufacturer} fault codes",
                f"{gap.extracted_manufacturer} troubleshooting guides",
            ]

        elif gap.gap_type == GapType.MISSING_FAULT_CODE:
            specific_queries = [
                f"What does fault code {gap.extracted_fault_code} mean?",
                f"Causes of {gap.extracted_fault_code}",
                f"How to resolve {gap.extracted_fault_code}",
                f"Related fault codes to {gap.extracted_fault_code}",
            ]

        elif gap.gap_type == GapType.UNKNOWN_MODEL:
            specific_queries = [
                f"{gap.extracted_model} specifications",
                f"{gap.extracted_model} user manual",
                f"{gap.extracted_model} fault codes",
                f"{gap.extracted_model} programming guide",
            ]

        else:
            # Generic research
            specific_queries = [
                "Find relevant technical documentation",
                "Extract troubleshooting procedures",
                "Identify common issues and solutions",
            ]

        return ResearchTask(
            objective=gap.description,
            manufacturer=gap.extracted_manufacturer,
            equipment_type=gap.extracted_equipment_type,
            model_number=gap.extracted_model,
            specific_queries=specific_queries,
            context=f"Original user query: {gap.original_query}",
            priority=gap.priority,
            timeout_minutes=20 if gap.priority == ResearchPriority.CRITICAL else 30,
        )

    def _parse_atoms(
        self,
        gap: KnowledgeGap,
        result: ResearchResult,
    ) -> List[AtomCandidate]:
        """Parse research results into atom candidates"""

        atoms = []

        # Create main atom from research summary
        if result.suggested_atom_title and result.suggested_atom_content:
            main_atom = AtomCandidate(
                id=self._generate_atom_id(result.suggested_atom_title),
                title=result.suggested_atom_title,
                content=result.suggested_atom_content + "\n\n" + result.citations_markdown,
                domain="industrial",
                equipment_type=gap.extracted_equipment_type,
                manufacturer=gap.extracted_manufacturer,
                sources=[s.url for s in result.sources],
                citations=result.citations_markdown,
                confidence_score=result.confidence_score,
            )
            atoms.append(main_atom)

        # Create atoms for each fault code
        for fc in result.fault_codes:
            fc_atom = AtomCandidate(
                id=self._generate_atom_id(f"{gap.extracted_manufacturer}_{fc.code}"),
                title=f"{gap.extracted_manufacturer or 'Unknown'} Fault Code {fc.code}",
                content=self._format_fault_code_content(fc, gap),
                domain="industrial",
                equipment_type=gap.extracted_equipment_type,
                manufacturer=gap.extracted_manufacturer,
                fault_codes=[{
                    "code": fc.code,
                    "description": fc.description,
                    "causes": fc.possible_causes,
                    "actions": fc.recommended_actions,
                }],
                sources=[fc.source_citation],
                confidence_score=result.confidence_score,
            )
            atoms.append(fc_atom)

        return atoms

    def _format_fault_code_content(
        self,
        fc: ExtractedFaultCode,
        gap: KnowledgeGap,
    ) -> str:
        """Format fault code into atom content"""

        content = f"""# {fc.code}: {fc.description}

## Equipment
- **Manufacturer:** {gap.extracted_manufacturer or 'Unknown'}
- **Equipment Type:** {gap.extracted_equipment_type or 'Unknown'}
{f'- **Model:** {gap.extracted_model}' if gap.extracted_model else ''}

## Description
{fc.description}

## Possible Causes
{chr(10).join(f'- {cause}' for cause in fc.possible_causes) if fc.possible_causes else '- Not documented'}

## Recommended Actions
{chr(10).join(f'{i}. {action}' for i, action in enumerate(fc.recommended_actions, 1)) if fc.recommended_actions else '1. Consult manufacturer documentation'}

## Source
{fc.source_citation}
"""
        return content

    def _generate_atom_id(self, title: str) -> str:
        """Generate deterministic atom ID from title"""
        normalized = title.lower().replace(" ", "_").replace("-", "_")
        hash_suffix = hashlib.md5(title.encode()).hexdigest()[:8]
        return f"atom:{normalized[:50]}_{hash_suffix}"

    async def _insert_atoms(
        self,
        atoms: List[AtomCandidate],
    ) -> Tuple[List[str], List[str], List[Dict]]:
        """
        Insert atoms into knowledge base

        Returns:
            Tuple of (created_ids, updated_ids, failures)
            failures is list of dicts with atom_id, error, traceback
        """

        created = []
        updated = []
        failures = []  # Track failures instead of swallowing errors

        # REMOVED: kb_client check - we use DatabaseManager now
        # if not self.kb_client:
        #     logger.warning("No KB client configured, atoms not inserted")
        #     return created, updated

        for atom in atoms:
            try:
                # Generate embedding
                embedding = await self._generate_embedding(atom.content)
                atom.embedding = embedding

                # Check if exists
                existing = await self._check_existing_atom(atom.id)

                if existing:
                    # Update existing
                    await self._update_atom(atom)
                    updated.append(atom.id)
                else:
                    # Insert new
                    await self._insert_atom(atom)
                    created.append(atom.id)

            except Exception as e:
                logger.error(f"Failed to insert atom {atom.id}: {e}")
                import traceback
                failures.append({
                    'atom_id': atom.id,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                })

        return created, updated, failures

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for atom content"""
        try:
            from langchain_openai import OpenAIEmbeddings

            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            return await embeddings.aembed_query(text)
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return []

    async def _check_existing_atom(self, atom_id: str) -> bool:
        """Check if atom already exists in KB (CORRECTED)"""
        try:
            db = self.db_manager

            # Use atom_id column (not id which is UUID)
            sql = "SELECT atom_id FROM knowledge_atoms WHERE atom_id = $1 LIMIT 1"
            result = await asyncio.to_thread(db.execute_query, sql, (atom_id,))

            # DatabaseManager returns list of dicts or None
            return result is not None and len(result) > 0
        except Exception as e:
            logger.warning(f"Failed to check existing atom: {e}")
            return False

    async def _insert_atom(self, atom: AtomCandidate) -> None:
        """Insert new atom into KB (CORRECTED)"""
        db = self.db_manager

        # Let database auto-generate UUID id
        # Use atom.id for atom_id string field
        sql = """
            INSERT INTO knowledge_atoms (
                atom_id,
                atom_type,
                title,
                summary,
                content,
                manufacturer,
                product_family,
                difficulty,
                source_document,
                source_pages,
                source_url,
                quality_score,
                embedding,
                created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        """

        # Generate summary if not provided
        summary = atom.content[:200] if len(atom.content) > 200 else atom.content

        # Convert embedding to PostgreSQL vector format
        embedding_vector = f"[{','.join(map(str, atom.embedding))}]" if atom.embedding else None

        # Extract product_family with fallback (handles both old equipment_type and new product_family)
        product_family = getattr(atom, 'product_family', None) or \
                        getattr(atom, 'equipment_type', None) or \
                        'Unknown'

        # DEBUG: Log SQL and params
        logger.info(f"INSERT SQL length: {len(sql)}")
        logger.info(f"INSERT SQL repr: {repr(sql[:100])}")
        logger.info(f"Params count: 14")

        await asyncio.to_thread(
            db.execute_query,
            sql,
            (
                atom.id,  # $1: atom_id (string)
                'research',  # $2: atom_type
                atom.title,  # $3: title
                summary,  # $4: summary
                atom.content,  # $5: content
                atom.manufacturer or 'Unknown',  # $6: manufacturer
                product_family,  # $7: product_family (FIXED)
                'intermediate',  # $8: difficulty
                atom.sources[0] if atom.sources else 'Autonomous Research',  # $9: source_document
                [],  # $10: source_pages
                atom.sources[0] if atom.sources else None,  # $11: source_url
                atom.confidence_score,  # $12: quality_score
                embedding_vector,  # $13: embedding
                datetime.utcnow()  # $14: created_at
            ),
            "none"  # fetch_mode for INSERT
        )

        logger.info(f"Inserted research atom: {atom.id} - {atom.title}")

    async def _update_atom(self, atom: AtomCandidate) -> None:
        """Update existing atom in KB (CORRECTED)"""
        db = self.db_manager

        sql = """
            UPDATE knowledge_atoms
            SET content = $1,
                quality_score = $2,
                embedding = $3,
                updated_at = $4
            WHERE atom_id = $5
        """

        # Convert embedding
        embedding_vector = f"[{','.join(map(str, atom.embedding))}]" if atom.embedding else None

        await asyncio.to_thread(
            db.execute_query,
            sql,
            (atom.content, atom.confidence_score, embedding_vector, datetime.utcnow(), atom.id),
            "none"  # fetch_mode for UPDATE
        )

        logger.info(f"Updated research atom: {atom.id} - {atom.title}")

    # ========================================================================
    # Approval workflow
    # ========================================================================

    def get_pending_atoms(self) -> List[AtomCandidate]:
        """Get atoms pending approval"""
        return list(self._pending_atoms.values())

    async def approve_atom(self, atom_id: str) -> bool:
        """Approve and insert a pending atom"""
        if atom_id not in self._pending_atoms:
            return False

        atom = self._pending_atoms.pop(atom_id)
        created, _, failures = await self._insert_atoms([atom])
        if failures:
            logger.error(f"Failed to approve atom {atom_id}: {failures[0]['error']}")
        return len(created) > 0

    def reject_atom(self, atom_id: str) -> bool:
        """Reject a pending atom"""
        if atom_id in self._pending_atoms:
            del self._pending_atoms[atom_id]
            return True
        return False


# ============================================================================
# Integration helper for RivetCEO Bot
# ============================================================================

class RivetCEOGapIntegration:
    """
    Drop-in integration for RivetCEO Bot orchestrator.

    Usage in your orchestrator:

        from agent_factory.tools.response_gap_filler import RivetCEOGapIntegration

        gap_integration = RivetCEOGapIntegration(supabase_client)

        # In your response flow
        async def handle_query(query: str, image_analysis: dict):
            # ... existing KB search ...
            response = await generate_response(query, kb_results)

            # Check for gaps and fill automatically
            if response.confidence < 0.6:
                filled = await gap_integration.check_and_fill(
                    query=query,
                    kb_results=kb_results,
                    response_confidence=response.confidence,
                    manufacturer=image_analysis.get("manufacturer"),
                    equipment_type=image_analysis.get("equipment_type"),
                )

                if filled and filled.fill_successful:
                    # Re-query with new knowledge
                    response = await generate_response(query, kb_results + filled.new_atoms)

            return response
    """

    def __init__(
        self,
        kb_client: Any,
        llm_provider: str = "ollama",
        auto_fill: bool = True,
    ):
        self.filler = KnowledgeGapFiller(
            kb_client=kb_client,
            research_executor=ResearchExecutorTool(llm_provider=llm_provider),
            auto_insert=auto_fill,
        )

    async def check_and_fill(
        self,
        query: str,
        kb_results: List[Dict[str, Any]],
        response_confidence: float,
        manufacturer: Optional[str] = None,
        equipment_type: Optional[str] = None,
        fault_code: Optional[str] = None,
    ) -> Optional[FilledGap]:
        """
        Check for knowledge gap and fill if detected.

        Call this after your initial KB search when confidence is low.
        """
        # Enrich gap detector with OCR results
        if manufacturer:
            self.filler.gap_detector.KNOWN_MANUFACTURERS.add(manufacturer.lower())

        return await self.filler.detect_and_fill(
            query=query,
            search_results=kb_results,
            response_confidence=response_confidence,
        )

    async def research_manufacturer(
        self,
        manufacturer: str,
        equipment_type: str,
    ) -> FilledGap:
        """
        Proactively research a manufacturer.

        Call this when you detect an unknown manufacturer in OCR.
        """
        gap = KnowledgeGap(
            gap_type=GapType.UNKNOWN_MANUFACTURER,
            description=f"Research {manufacturer} {equipment_type} documentation",
            original_query=f"Unknown manufacturer: {manufacturer}",
            extracted_manufacturer=manufacturer,
            extracted_equipment_type=equipment_type,
            priority=ResearchPriority.HIGH,
        )

        return await self.filler.fill_gap(gap)


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys

    async def main():
        filler = KnowledgeGapFiller(
            kb_client=None,  # No KB for testing
            auto_insert=False,
        )

        # Simulate a gap detection
        gap = KnowledgeGap(
            gap_type=GapType.UNKNOWN_MANUFACTURER,
            description="Research Lenze VFD fault codes",
            original_query="My Lenze drive shows F0001 fault",
            extracted_manufacturer="Lenze",
            extracted_equipment_type="VFD",
            extracted_fault_code="F0001",
            priority=ResearchPriority.HIGH,
        )

        print(f"Filling gap: {gap.description}\n")

        filled = await filler.fill_gap(gap)

        print(f"Status: {'Success' if filled.fill_successful else 'Failed'}")
        print(f"Confidence: {filled.confidence:.0%}")
        print(f"Duration: {filled.duration_seconds:.1f}s")
        print(f"\nSummary:\n{filled.research_result.summary}")

        if filled.research_result.fault_codes:
            print(f"\nFault codes found: {len(filled.research_result.fault_codes)}")
            for fc in filled.research_result.fault_codes:
                print(f"  - {fc.code}: {fc.description[:60]}...")

    asyncio.run(main())

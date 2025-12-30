"""
Base SME Agent for RIVET Pro

Abstract base class for all Subject Matter Expert agents.

Phase 3/8 of RIVET Pro Multi-Agent Backend.
Updated 2025-12-28: Integrated with LLMRouter for Phase 4 orchestrator compatibility.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import logging
from datetime import datetime

from agent_factory.rivet_pro.models import (
    RivetRequest,
    RivetIntent,
    RivetResponse,
    AgentID,
    RouteType,
    VendorType,
    EquipmentType,
    ContextSource,
    KBCoverage,
    MessageType
)
from agent_factory.rivet_pro.rag import search_docs, RetrievedDoc
from agent_factory.llm.router import LLMRouter
from agent_factory.llm.types import LLMConfig, LLMProvider

logger = logging.getLogger(__name__)


class BaseSMEAgent(ABC):
    """
    Abstract base class for SME agents.

    All agent implementations must inherit from this class.

    Updated 2025-12-28: Uses LLMRouter for model selection and fallbacks.
    """

    def __init__(self, agent_id: AgentID, llm_router: Optional[LLMRouter] = None):
        """
        Initialize SME agent.

        Args:
            agent_id: Unique agent identifier
            llm_router: LLMRouter instance (creates new if None)
        """
        self.agent_id = agent_id
        self.llm_router = llm_router if llm_router else LLMRouter()

    @abstractmethod
    def _build_system_prompt(self) -> str:
        """Build system prompt with SME persona."""
        pass

    @abstractmethod
    def _build_user_prompt(
        self,
        intent: RivetIntent,
        docs: List[RetrievedDoc]
    ) -> str:
        """Build user prompt from intent and retrieved docs."""
        pass

    async def handle_query(
        self,
        request: RivetRequest,
        kb_coverage: Optional[float] = None,
        fewshot_context: Optional[str] = None
    ) -> RivetResponse:
        """
        Handle query - async wrapper for orchestrator compatibility.

        Args:
            request: Original user request
            kb_coverage: Knowledge base coverage metric (unused)
            fewshot_context: Few-shot examples context (unused)

        Returns:
            RivetResponse with answer
        """
        # Map message_type to context_source
        context_source_map = {
            MessageType.TEXT: ContextSource.TEXT_ONLY,
            MessageType.IMAGE: ContextSource.IMAGE_TEXT,
            MessageType.AUDIO: ContextSource.AUDIO_TRANSCRIPTION,
            MessageType.VIDEO: ContextSource.IMAGE_TEXT,
        }

        # Get message type (handle both enum and string)
        msg_type = request.message_type
        if isinstance(msg_type, str):
            msg_type = MessageType(msg_type)

        context_source = context_source_map.get(msg_type, ContextSource.TEXT_ONLY)

        # Create complete RivetIntent with all required fields
        intent = RivetIntent(
            vendor=self.vendor_type if hasattr(self, 'vendor_type') else VendorType.UNKNOWN,
            equipment_type=EquipmentType.UNKNOWN,  # SME agents don't extract equipment type
            context_source=context_source,
            confidence=0.8,  # Default confidence for SME agent handling
            kb_coverage=KBCoverage.NONE,  # SME agents don't evaluate KB coverage
            raw_summary=request.text or "",  # Use request text as summary
            detected_fault_codes=[],  # SME agents don't extract fault codes in wrapper
            detected_model=None,
            detected_symptoms=[]
        )

        # Call synchronous handle method
        return self.handle(request, intent, RouteType.ROUTE_A)

    def handle(
        self,
        request: RivetRequest,
        intent: RivetIntent,
        route: RouteType = RouteType.ROUTE_A
    ) -> RivetResponse:
        """
        Handle user request and generate response.

        Args:
            request: Original user request
            intent: Classified intent
            route: Orchestrator route taken

        Returns:
            RivetResponse with answer
        """
        try:
            # Query knowledge base
            docs = self._query_kb(intent)

            # Generate answer
            answer_text = self._generate_answer(intent, docs)

            # Build response
            response = RivetResponse(
                text=answer_text,
                agent_id=self.agent_id,
                route_taken=route,
                links=self._extract_links(docs),
                cited_documents=[doc.source for doc in docs if doc.source],
                confidence=self._estimate_confidence(intent, docs)
            )

            return response

        except Exception as e:
            logger.error(f"Error in {self.agent_id}: {e}", exc_info=True)
            return self._error_response(str(e))

    def _query_kb(self, intent: RivetIntent) -> List[RetrievedDoc]:
        """Query knowledge base using RAG layer."""
        try:
            docs = search_docs(
                intent,
                agent_id=self.agent_id.value,
                top_k=8
            )
            logger.info(f"{self.agent_id}: Retrieved {len(docs)} documents")
            return docs
        except Exception as e:
            logger.warning(f"{self.agent_id}: KB query failed: {e}")
            return []

    def _generate_answer(
        self,
        intent: RivetIntent,
        docs: List[RetrievedDoc]
    ) -> str:
        """Generate answer using LLM via LLMRouter.

        Uses LLMRouter for automatic model selection, retries, and fallbacks.
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(intent, docs)

        # Call LLM via router (handles retries and fallbacks)
        try:
            # Prefer Groq for fast, cheap responses
            config = LLMConfig(
                provider=LLMProvider.GROQ,
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=1500
            )

            response = self.llm_router.generate(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                config=config
            )

            return response.content
        except Exception as e:
            logger.error(f"{self.agent_id}: LLM generation failed: {e}")
            return f"I encountered an error generating a response: {str(e)}"

    def _extract_links(self, docs: List[RetrievedDoc]) -> List[str]:
        """Extract documentation links from retrieved docs."""
        links = []
        for doc in docs:
            if doc.source and doc.source.startswith("http"):
                links.append(doc.source)
        return list(set(links))[:5]  # Max 5 unique links

    def _estimate_confidence(
        self,
        intent: RivetIntent,
        docs: List[RetrievedDoc]
    ) -> float:
        """Estimate response confidence based on intent and docs."""
        base_confidence = intent.confidence

        # Adjust based on number of docs
        if len(docs) >= 5:
            doc_bonus = 0.1
        elif len(docs) >= 3:
            doc_bonus = 0.05
        else:
            doc_bonus = -0.1

        return min(0.95, max(0.3, base_confidence + doc_bonus))

    def _error_response(self, error_msg: str) -> RivetResponse:
        """Generate error response."""
        return RivetResponse(
            text=f"I apologize, but I encountered an error: {error_msg}",
            agent_id=self.agent_id,
            route_taken=RouteType.ROUTE_D,
            confidence=0.0
        )

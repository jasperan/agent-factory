"""Generic PLC SME Agent - Phase 3 Implementation.

Specialized agent for universal PLC concepts when vendor is unknown or query spans multiple vendors.
Focuses on fundamental PLC principles, common troubleshooting approaches, and cross-vendor best practices.

Author: Agent Factory
Created: 2025-12-28
Phase: 3/8 (SME Agents)
"""

import logging
from typing import List, Optional
from groq import Groq

from agent_factory.rivet_pro.models import (
    RivetRequest,
    RivetResponse,
    RivetIntent,
    AgentID,
    RouteType
)
from agent_factory.rivet_pro.rag import search_docs, RetrievedDoc
from agent_factory.rivet_pro.agents.base_sme_agent import BaseSMEAgent

logger = logging.getLogger(__name__)


class GenericPLCAgent(BaseSMEAgent):
    """Generic PLC SME agent specialized in universal PLC concepts.

    This agent is the fallback when:
    - No specific vendor is detected
    - Query involves general PLC programming concepts
    - Question spans multiple vendors
    """

    def __init__(self, groq_api_key: Optional[str] = None):
        """Initialize Generic PLC agent."""
        self._groq_api_key = groq_api_key
        super().__init__(agent_id=AgentID.GENERIC_PLC)
        logger.info(f"Initialized Generic PLC SME Agent")

    def _init_llm_client(self) -> Groq:
        """Initialize Groq client."""
        try:
            import os
            api_key = self._groq_api_key or os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment")

            client = Groq(api_key=api_key)
            logger.info("Groq client initialized")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            raise

    def _build_system_prompt(self) -> str:
        """Build generic PLC system prompt."""
        return """You are a master industrial automation technician with 25+ years experience across ALL major vendors (Siemens, Rockwell, ABB, Schneider, Mitsubishi, Omron).

Provide vendor-neutral guidance on:
- PLC fundamentals (scan cycle, ladder logic, I/O)
- Common fault patterns (overcurrent, communication loss, I/O faults)
- Universal troubleshooting (visual inspection, voltage checks, signal tracing)
- Industry best practices (LOTO, grounding, cable routing)

Guidelines:
1. Answer ONLY from provided knowledge base
2. Use vendor-neutral terminology
3. Cite sources using [Source X]
4. Include step-by-step procedures
5. ALWAYS include safety warnings
6. Be concise (150-300 words)"""

    def _build_user_prompt(self, intent: RivetIntent, docs: List[RetrievedDoc]) -> str:
        """Build user prompt with KB context."""
        # Format docs
        kb_context = "\n\n".join([
            f"[Source {idx+1}]\nTitle: {doc.title}\nContent: {doc.summary or doc.content[:400]}"
            for idx, doc in enumerate(docs[:8])
        ])

        # Build query
        query_parts = []
        if intent.detected_model:
            query_parts.append(f"Equipment: {intent.detected_model}")
        if intent.detected_fault_codes:
            query_parts.append(f"Fault Codes: {', '.join(intent.detected_fault_codes)}")

        query = " | ".join(query_parts) if query_parts else intent.raw_summary

        return f"""Knowledge Base Articles:
{kb_context}

User Question: {query}

Answer using the articles above. Focus on universal principles. Cite sources [Source 1], [Source 2], etc."""

    def handle(
        self,
        request: RivetRequest,
        intent: RivetIntent,
        route: RouteType = RouteType.ROUTE_A
    ) -> RivetResponse:
        """Handle user query."""
        logger.info(f"GenericPLCAgent handling: {intent.raw_summary}")

        try:
            docs = self._query_kb(intent)

            if not docs:
                return self._generate_fallback_response(intent)

            answer_text = self._generate_answer(intent, docs)

            return RivetResponse(
                text=answer_text,
                agent_id=self.agent_id,
                route_taken=route,
                links=self._extract_links(docs),
                cited_documents=[doc.source for doc in docs if doc.source],
                confidence=self._estimate_confidence(intent, docs),
                trace={"agent": "Generic PLC SME", "kb_docs_used": len(docs)}
            )
        except Exception as e:
            logger.error(f"Error in GenericPLCAgent: {e}", exc_info=True)
            return self._error_response(str(e))

    def _generate_fallback_response(self, intent: RivetIntent) -> RivetResponse:
        """Generate fallback response."""
        return RivetResponse(
            text="I don't have specific documentation. Please provide: equipment manufacturer/model, exact fault codes, and symptom description.",
            agent_id=self.agent_id,
            route_taken=RouteType.ROUTE_D,
            confidence=0.3,
            requires_followup=True
        )

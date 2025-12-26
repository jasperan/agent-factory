"""Generic PLC SME Agent - Phase 3 Implementation.

Handles industrial maintenance queries across all equipment vendors when specific vendor cannot be identified.
Uses KB atoms to generate informed responses with proper citations.

Author: Agent Factory
Created: 2025-12-23
Phase: 3/8 (SME Agents)
"""

from typing import List, Optional
from agent_factory.rivet_pro.models import (
    RivetRequest,
    RivetResponse,
    AgentID,
    RouteType as ModelRouteType
)
from agent_factory.llm.router import LLMRouter
from agent_factory.llm.types import LLMConfig, LLMProvider
from agent_factory.schemas.routing import KBCoverage


class GenericAgent:
    """Generic PLC SME agent for cross-vendor industrial maintenance queries.

    This agent handles queries when:
    - No specific vendor is detected
    - Query spans multiple vendors
    - General industrial automation questions

    Uses knowledge base atoms to generate accurate, cited responses.
    """

    def __init__(self, llm_router: Optional[LLMRouter] = None):
        """Initialize Generic PLC agent.

        Args:
            llm_router: LLMRouter instance (creates new if None)
        """
        self.agent_id = AgentID.GENERIC_PLC
        self.agent_name = "Generic PLC Agent"
        self.llm_router = llm_router if llm_router else LLMRouter()

    async def handle_query(
        self,
        request: RivetRequest,
        kb_coverage: Optional[KBCoverage] = None,
        fewshot_context: Optional[str] = None
    ) -> RivetResponse:
        """Handle user query using KB atoms and LLM generation.

        Args:
            request: User query request
            kb_coverage: KB coverage with retrieved documents
            fewshot_context: Optional few-shot examples from similar maintenance cases

        Returns:
            RivetResponse with generated answer and citations
        """
        query_text = request.text or ""

        # Get KB atoms from coverage (if available)
        kb_atoms = []
        if kb_coverage and kb_coverage.retrieved_docs:
            kb_atoms = kb_coverage.retrieved_docs

        # Generate response using LLM
        if kb_atoms:
            response_text = await self._generate_response_with_kb(query_text, kb_atoms, fewshot_context)
            cited_docs = self._format_citations(kb_atoms)
            links = [f"atom_{doc.atom_id}" for doc in kb_atoms[:5]]  # Top 5 atoms
            confidence = min(0.85, kb_coverage.confidence + 0.1)  # Boost confidence slightly
        else:
            # Fallback: No KB coverage
            response_text = self._generate_fallback_response(query_text)
            cited_docs = []
            links = []
            confidence = 0.4

        return RivetResponse(
            text=response_text,
            agent_id=self.agent_id,
            route_taken=ModelRouteType.ROUTE_B,  # Default to Route B
            links=links,
            confidence=confidence,
            cited_documents=cited_docs,
            trace={
                "agent": self.agent_name,
                "kb_atoms_used": len(kb_atoms),
                "query_length": len(query_text)
            }
        )

    async def _generate_response_with_kb(self, query: str, kb_atoms: List, fewshot_context: Optional[str] = None) -> str:
        """Generate LLM response using KB atoms as context.

        Args:
            query: User's question
            kb_atoms: List of RetrievedDoc objects from KB search
            fewshot_context: Optional few-shot examples from similar maintenance cases

        Returns:
            Generated response text
        """
        # Format KB atoms into context string
        kb_context = self._format_kb_atoms(kb_atoms)

        # Create base system prompt
        system_prompt = """You are an expert industrial maintenance technician and PLC programmer with 20+ years of experience across all major equipment vendors (Siemens, Rockwell, ABB, Schneider, Mitsubishi, Omron).

Your role is to answer technical questions about:
- PLCs (Programmable Logic Controllers)
- VFDs (Variable Frequency Drives)
- HMIs (Human-Machine Interfaces)
- Industrial sensors and actuators
- Motor control systems
- Safety systems"""

        # Inject few-shot examples if provided (Phase 3: Dynamic Few-Shot RAG)
        if fewshot_context:
            system_prompt += f"\n\n{fewshot_context}"

        # Add guidelines
        system_prompt += """

Guidelines:
1. Answer based ONLY on the provided knowledge base articles
2. Cite sources using [Source X] notation
3. If KB doesn't cover the question, say "I don't have specific documentation on this"
4. Use clear, step-by-step explanations
5. Include safety warnings when relevant
6. Be concise but thorough (aim for 150-300 words)

Format your response as:
- Direct answer to the question
- Relevant technical details
- Step-by-step procedure (if applicable)
- Safety warnings (if applicable)
- Source citations"""

        # Create user prompt with KB context
        user_prompt = f"""Knowledge Base Articles:
{kb_context}

User Question: {query}

Answer the user's question using the knowledge base articles above. Cite sources using [Source 1], [Source 2], etc."""

        # Call LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",  # Cost-effective for this task
            temperature=0.3,  # Low temp for factual responses
            max_tokens=500
        )

        response = self.llm_router.complete(messages, config)
        return response.content

    def _format_kb_atoms(self, kb_atoms: List) -> str:
        """Format KB atoms into readable context for LLM.

        Args:
            kb_atoms: List of RetrievedDoc objects

        Returns:
            Formatted string with numbered sources
        """
        formatted = []
        for idx, doc in enumerate(kb_atoms[:10], 1):  # Top 10 atoms
            # Extract key fields from RetrievedDoc
            title = getattr(doc, 'title', 'Unknown')
            summary = getattr(doc, 'summary', '')
            content = getattr(doc, 'content', '')
            atom_type = getattr(doc, 'atom_type', 'unknown')
            vendor = getattr(doc, 'vendor', 'Generic')
            source = getattr(doc, 'source', 'Unknown source')
            page = getattr(doc, 'page_number', None)

            # Build source reference
            source_ref = f"{source}"
            if page:
                source_ref += f", page {page}"

            # Format this atom
            formatted.append(f"""[Source {idx}]
Title: {title}
Type: {atom_type}
Vendor: {vendor}
Summary: {summary}
Content: {content[:500]}...  # Truncate long content
Reference: {source_ref}
""")

        return "\n\n".join(formatted)

    def _format_citations(self, kb_atoms: List) -> List[dict]:
        """Format KB atoms into citation dictionaries.

        Args:
            kb_atoms: List of RetrievedDoc objects

        Returns:
            List of citation dicts with title and url/source
        """
        citations = []
        for doc in kb_atoms[:5]:  # Top 5 sources
            title = getattr(doc, 'title', 'Unknown Document')
            source = getattr(doc, 'source', '')
            atom_id = getattr(doc, 'atom_id', 0)

            citations.append({
                "title": title,
                "url": source if source.startswith('http') else f"kb://atom/{atom_id}",
                "atom_id": atom_id
            })

        return citations

    def _generate_fallback_response(self, query: str) -> str:
        """Generate fallback response when no KB coverage available.

        Args:
            query: User's question

        Returns:
            Fallback response text
        """
        return f"""I don't have specific documentation in my knowledge base about "{query}".

To help you better, I would need:
1. More specific details about the equipment (make, model, etc.)
2. Exact error codes or symptoms you're seeing
3. What troubleshooting steps you've already tried

I recommend:
- Checking the equipment manual for your specific model
- Reviewing manufacturer technical bulletins
- Contacting the equipment vendor's technical support

Would you like to provide more details so I can search my knowledge base more effectively?"""

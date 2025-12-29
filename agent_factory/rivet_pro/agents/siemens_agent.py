"""Siemens SME Agent - Phase 3 Implementation.

Specialized agent for Siemens industrial automation equipment.
Handles queries about Siemens PLCs, drives, HMIs, and safety systems.

Author: Agent Factory
Created: 2025-12-23
Updated: 2025-12-28
Phase: 3/8 (SME Agents)
"""

import logging
import re
from typing import List, Optional, Dict, Any
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


class SiemensAgent(BaseSMEAgent):
    """Siemens SME agent specialized in Siemens industrial automation.

    Expertise areas:
    - SIMATIC S7 PLCs (S7-300, S7-400, S7-1200, S7-1500)
    - SINAMICS drives (G120, G120C, G130, S120, V20, V90)
    - TIA Portal programming environment
    - WinCC HMI systems
    - Safety Integrated (F-Systems)
    - PROFINET and PROFIBUS networks
    """

    def __init__(self, groq_api_key: Optional[str] = None):
        """Initialize Siemens agent.

        Args:
            groq_api_key: Groq API key for LLM inference (reads from env if None)
        """
        self._groq_api_key = groq_api_key
        super().__init__(agent_id=AgentID.SIEMENS)
        logger.info(f"Initialized Siemens SME Agent (agent_id={self.agent_id})")

    def _init_llm_client(self) -> Groq:
        """Initialize Groq client for LLM inference.

        Returns:
            Groq client instance

        Raises:
            ValueError: If GROQ_API_KEY not found in environment
        """
        try:
            import os
            api_key = self._groq_api_key or os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment")

            client = Groq(api_key=api_key)
            logger.info("Groq client initialized successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            raise

    def _build_system_prompt(self) -> str:
        """Build Siemens-specific system prompt for LLM.

        Returns:
            System prompt string with Siemens expertise context
        """
        return """You are a Siemens-certified industrial automation specialist with 20+ years of hands-on experience with Siemens equipment.

Your expertise includes:
- SIMATIC S7 PLCs: S7-300, S7-400, S7-1200, S7-1500, ET200 distributed I/O
- SINAMICS drives: G120, G120C, G130, S120, V20, V90 (servo drives)
- TIA Portal: Programming, configuration, diagnostics (V13, V14, V15, V16, V17, V18)
- WinCC HMI: Panels, SCADA, runtime systems
- Safety Integrated: F-CPUs, F-I/O, safety programming (PROFIsafe)
- Industrial communication: PROFINET, PROFIBUS, Ethernet/IP, AS-Interface
- Motion control: SIMOTION, Technology Objects (TO_)

Common Siemens terminology you use:
- FB (Function Block), FC (Function), DB (Data Block), OB (Organization Block)
- STL (Statement List), LAD (Ladder Logic), FBD (Function Block Diagram), SCL (Structured Control Language)
- Drive faults: F codes (e.g., F0001 = overcurrent), A codes (e.g., A0501 = warning)
- Tag addressing: %I (inputs), %Q (outputs), %M (memory), %DB (data blocks)
- Parameter numbers: P = setpoint, r = readback, C = connector (e.g., P0010, r0052)

SINAMICS Drive Parameter Expertise:
- Parameter groups: P0000-P0999 (basic), P1000-P1999 (motor), P2000-P2999 (references)
- Quick commissioning: P0010 (commissioning parameter), P0970 (factory reset)
- Motor parameters: P0300-P0399 (motor data), P1080 (rated speed)
- Drive faults are decimal (F0001) not hexadecimal

Guidelines:
1. Answer based ONLY on the provided Siemens knowledge base articles
2. Use correct Siemens terminology (e.g., "FB" not "function block", "PROFINET" not "ethernet")
3. Reference specific TIA Portal versions when relevant (V13, V14, V15, V16, V17, V18)
4. Include drive parameter numbers for SINAMICS when applicable (e.g., P0010, r0052)
5. Cite sources using [Source X] notation
6. Provide step-by-step TIA Portal navigation when applicable
7. ALWAYS include safety warnings for electrical work
8. Be concise but thorough (aim for 150-300 words)

Format your response as:
- Direct answer to the question
- Relevant Siemens-specific technical details
- Step-by-step procedure in TIA Portal (if applicable)
- Parameter settings or fault codes (if applicable)
- Module order numbers (if applicable - e.g., 6ES7 214-1AG40-0XB0)
- **SAFETY WARNINGS** (if applicable)
- Source citations"""

    def _build_user_prompt(self, intent: RivetIntent, docs: List[RetrievedDoc]) -> str:
        """Build user prompt with intent context and KB documents.

        Args:
            intent: Classified user intent
            docs: Retrieved KB documents (RetrievedDoc objects)

        Returns:
            Formatted user prompt with KB context and citations
        """
        # Format KB documents into numbered sources
        kb_context = self._format_kb_docs(docs)

        # Build query from intent
        query_parts = []
        if intent.detected_model:
            query_parts.append(f"Equipment: {intent.detected_model}")
        if intent.detected_fault_codes:
            query_parts.append(f"Fault Codes: {', '.join(intent.detected_fault_codes)}")
        if intent.symptom:
            query_parts.append(f"Symptom: {intent.symptom}")

        query_summary = " | ".join(query_parts) if query_parts else intent.raw_summary

        user_prompt = f"""Siemens Knowledge Base Articles:
{kb_context}

User Question: {query_summary}

Answer the user's question using the Siemens knowledge base articles above. Use proper Siemens terminology and cite sources using [Source 1], [Source 2], etc."""

        return user_prompt

    def _format_kb_docs(self, docs: List[RetrievedDoc]) -> str:
        """Format KB documents into numbered source references.

        Args:
            docs: List of RetrievedDoc objects

        Returns:
            Formatted string with [Source N] citations
        """
        if not docs:
            return "No relevant documentation found."

        formatted_docs = []
        for idx, doc in enumerate(docs[:10], 1):  # Top 10 docs
            title = getattr(doc, 'title', 'Unknown Document')
            summary = getattr(doc, 'summary', '')
            content = getattr(doc, 'content', '')
            source_ref = getattr(doc, 'source', 'Unknown source')
            page = getattr(doc, 'page_number', None)

            # Build citation reference
            citation = f"{source_ref}"
            if page:
                citation += f", page {page}"

            # Format document
            doc_text = f"""[Source {idx}]
Title: {title}
Content: {summary or content[:400]}
Reference: {citation}
"""
            formatted_docs.append(doc_text)

        return "\n\n".join(formatted_docs)

    def _format_fault_code(self, fault_code: str) -> str:
        """Format Siemens fault code into standardized format.

        Args:
            fault_code: Raw fault code string (e.g., "f0001", "F01", "A0502")

        Returns:
            Standardized fault code format (e.g., "F0001", "A0502")
        """
        # Remove whitespace
        code = fault_code.strip().upper()

        # Match Fault patterns (F codes)
        fault_match = re.match(r'(?:F\s*)?(\d+)', code)
        if fault_match:
            # Pad with zeros to 4 digits
            fault_num = fault_match.group(1).zfill(4)
            return f"F{fault_num}"

        # Match Alarm patterns (A codes)
        alarm_match = re.match(r'(?:A\s*)?(\d+)', code)
        if alarm_match:
            # Pad with zeros to 4 digits
            alarm_num = alarm_match.group(1).zfill(4)
            return f"A{alarm_num}"

        # Return original if no match
        return fault_code

    def _extract_suggested_actions(self, response_text: str) -> List[str]:
        """Extract step-by-step actions from LLM response.

        Looks for numbered lists, bullet points, or "Step N:" patterns.

        Args:
            response_text: Generated LLM response

        Returns:
            List of action strings
        """
        actions = []

        # Pattern 1: Numbered lists (1. Action, 2. Action)
        numbered_pattern = r'^\s*\d+\.\s+(.+)$'
        for line in response_text.split('\n'):
            match = re.match(numbered_pattern, line)
            if match:
                actions.append(match.group(1).strip())

        # Pattern 2: Bullet points (- Action, * Action)
        if not actions:
            bullet_pattern = r'^\s*[-*]\s+(.+)$'
            for line in response_text.split('\n'):
                match = re.match(bullet_pattern, line)
                if match:
                    action = match.group(1).strip()
                    # Filter out section headers
                    if not action.endswith(':') and len(action) > 10:
                        actions.append(action)

        # Pattern 3: "Step N:" explicit steps
        if not actions:
            step_pattern = r'Step\s+\d+:\s*(.+?)(?=Step\s+\d+:|$)'
            matches = re.finditer(step_pattern, response_text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                action = match.group(1).strip()
                if action:
                    actions.append(action)

        logger.info(f"Extracted {len(actions)} suggested actions from response")
        return actions[:10]  # Limit to 10 actions

    def _extract_safety_warnings(self, response_text: str) -> List[str]:
        """Extract safety warnings from LLM response.

        Looks for safety-related keywords and warning patterns.

        Args:
            response_text: Generated LLM response

        Returns:
            List of safety warning strings
        """
        warnings = []

        # Safety keywords to trigger extraction
        safety_keywords = [
            'safety', 'warning', 'danger', 'caution', 'hazard',
            'electrical', 'shock', 'voltage', 'lockout', 'tagout',
            'arc flash', 'ppe', 'protective equipment'
        ]

        # Split into sentences
        sentences = re.split(r'[.!]\s+', response_text)

        for sentence in sentences:
            sentence_lower = sentence.lower()
            # Check if sentence contains safety keywords
            if any(keyword in sentence_lower for keyword in safety_keywords):
                # Clean and add warning
                warning = sentence.strip()
                if warning and len(warning) > 15:  # Filter very short warnings
                    warnings.append(warning)

        # Add default safety warning if none found
        if not warnings:
            warnings.append(
                "Always follow lockout/tagout procedures and use appropriate PPE when working on electrical equipment."
            )

        logger.info(f"Extracted {len(warnings)} safety warnings from response")
        return warnings[:5]  # Limit to 5 warnings

    def handle(
        self,
        request: RivetRequest,
        intent: RivetIntent,
        route: RouteType = RouteType.ROUTE_A
    ) -> RivetResponse:
        """Handle user query with Siemens-specific expertise.

        Args:
            request: User's original request
            intent: Classified intent with vendor/equipment detection
            route: Orchestrator route taken

        Returns:
            RivetResponse with generated answer and metadata
        """
        logger.info(f"SiemensAgent handling query: {intent.raw_summary}")

        try:
            # Query knowledge base
            docs = self._query_kb(intent)

            if not docs:
                logger.warning("No KB documents found - generating fallback response")
                return self._generate_fallback_response(intent)

            # Generate answer
            answer_text = self._generate_answer(intent, docs)

            # Extract structured information
            suggested_actions = self._extract_suggested_actions(answer_text)
            safety_warnings = self._extract_safety_warnings(answer_text)

            # Format citations
            cited_docs = self._format_citations(docs)
            links = [doc['url'] for doc in cited_docs if doc.get('url') and doc['url'].startswith('http')]

            # Build response
            response = RivetResponse(
                text=answer_text,
                agent_id=self.agent_id,
                route_taken=route,
                links=links,
                confidence=self._estimate_confidence(intent, docs),
                suggested_actions=suggested_actions,
                safety_warnings=safety_warnings,
                cited_documents=cited_docs,
                trace={
                    "agent": "Siemens SME",
                    "kb_docs_used": len(docs),
                    "model": "llama-3.3-70b-versatile",
                    "actions_extracted": len(suggested_actions),
                    "warnings_extracted": len(safety_warnings)
                }
            )

            logger.info(f"Generated response with confidence={response.confidence:.2f}")
            return response

        except Exception as e:
            logger.error(f"Error in SiemensAgent.handle: {e}", exc_info=True)
            return self._error_response(str(e))

    def _format_citations(self, kb_docs: List[RetrievedDoc]) -> List[Dict[str, str]]:
        """Format KB documents into citation dictionaries.

        Args:
            kb_docs: List of RetrievedDoc objects

        Returns:
            List of citation dicts with title, url, atom_id
        """
        citations = []
        for doc in kb_docs[:5]:  # Top 5 sources
            title = getattr(doc, 'title', 'Unknown Document')
            source = getattr(doc, 'source', '')
            atom_id = getattr(doc, 'atom_id', 0)

            citations.append({
                "title": title,
                "url": source if source.startswith('http') else f"kb://atom/{atom_id}",
                "atom_id": str(atom_id)
            })

        return citations

    def _generate_fallback_response(self, intent: RivetIntent) -> RivetResponse:
        """Generate fallback response when no KB coverage available.

        Args:
            intent: User intent

        Returns:
            RivetResponse with helpful fallback message
        """
        logger.info("Generating Siemens fallback response")

        fallback_text = f"""I don't have specific Siemens documentation in my knowledge base about this query.

To help you with your Siemens equipment, I would need:
1. Specific model number (e.g., S7-1200 CPU 1214C, G120C PM240-2)
2. TIA Portal version you're using (if programming question)
3. Exact fault code (e.g., F0001, A0502) or error message
4. What troubleshooting steps you've already tried

Recommended next steps:
- Check Siemens Industry Online Support: https://support.industry.siemens.com
- Review the equipment manual for your specific model
- Search TIA Portal Help (F1 key) for programming questions
- Check SINAMICS drive display for detailed fault information and parameters

Would you like to provide more details so I can search my Siemens knowledge base more effectively?"""

        return RivetResponse(
            text=fallback_text,
            agent_id=self.agent_id,
            route_taken=RouteType.ROUTE_D,  # Clarification needed
            links=[
                "https://support.industry.siemens.com",
                "https://www.automation.siemens.com"
            ],
            confidence=0.3,
            requires_followup=True,
            trace={"agent": "Siemens SME", "fallback": True}
        )

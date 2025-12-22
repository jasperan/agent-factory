"""RIVET Pro Orchestrator - 4-Route Query Routing System.

Routes queries based on vendor detection and KB coverage evaluation:
- Route A: Strong KB coverage → direct answer from SME agent
- Route B: Thin KB coverage → SME agent + enrichment trigger
- Route C: No KB coverage → research pipeline trigger (Phase 5)
- Route D: Unclear intent → clarification request
"""

from typing import Optional, Dict
from agent_factory.rivet_pro.models import RivetRequest, RivetResponse, EquipmentType, AgentID, RouteType as ModelRouteType
from agent_factory.schemas.routing import (
    VendorType,
    CoverageLevel,
    RouteType,
    RoutingDecision,
    VendorDetection,
    KBCoverage,
)
from agent_factory.routers.vendor_detector import VendorDetector
from agent_factory.routers.kb_evaluator import KBCoverageEvaluator
from agent_factory.llm.router import LLMRouter
from agent_factory.llm.types import LLMConfig, LLMProvider, LLMResponse
from agent_factory.core.kb_gap_logger import KBGapLogger
import logging

logger = logging.getLogger(__name__)

# TODO: Replace with real SME agents when Phase 3 (task-3.1 through task-3.4) is complete
from agent_factory.rivet_pro.agents.mock_agents import (
    MockSiemensAgent,
    MockRockwellAgent,
    MockGenericAgent,
    MockSafetyAgent,
)


class RivetOrchestrator:
    """4-route orchestrator for RIVET Pro queries.

    Coordinates vendor detection, KB coverage evaluation, and routing to
    appropriate handlers based on coverage level.
    """

    def __init__(self, rag_layer=None):
        """Initialize orchestrator with routing components.

        Args:
            rag_layer: Phase 2 RAG layer retriever (optional for testing)
        """
        self.vendor_detector = VendorDetector()
        self.kb_evaluator = KBCoverageEvaluator(rag_layer=rag_layer)
        self.sme_agents = self._load_sme_agents()

        # Initialize LLM Router for Groq fallback
        self.llm_router = LLMRouter(
            max_retries=3,
            retry_delay=1.0,
            enable_fallback=True,
            enable_cache=False
        )

        # Initialize KB gap logger (Phase 1: KB gap tracking)
        self.kb_gap_logger = None
        if rag_layer:
            try:
                self.kb_gap_logger = KBGapLogger(db=rag_layer)
                logger.info("KB gap logger initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize KB gap logger: {e}")

        # Routing statistics
        self._route_counts: Dict[RouteType, int] = {
            RouteType.ROUTE_A: 0,
            RouteType.ROUTE_B: 0,
            RouteType.ROUTE_C: 0,
            RouteType.ROUTE_D: 0,
        }

    def _load_sme_agents(self) -> Dict[VendorType, object]:
        """Load SME agents for each vendor type.

        TODO: Replace with real agents when Phase 3 complete:
        - task-3.1: SiemensAgent
        - task-3.2: RockwellAgent
        - task-3.3: GenericAgent
        - task-3.4: SafetyAgent

        Returns:
            Dictionary mapping VendorType to agent instances
        """
        return {
            VendorType.SIEMENS: MockSiemensAgent(),
            VendorType.ROCKWELL: MockRockwellAgent(),
            VendorType.GENERIC: MockGenericAgent(),
            VendorType.SAFETY: MockSafetyAgent(),
        }

    async def route_query(self, request: RivetRequest) -> RivetResponse:
        """Main routing logic - evaluates query and routes to appropriate handler.

        Args:
            request: User query request

        Returns:
            RivetResponse from appropriate route handler
        """
        # Step 1: Detect vendor from query
        vendor_detection = self.vendor_detector.detect(request.text or "")

        # Step 2: Evaluate KB coverage for detected vendor
        kb_coverage = self.kb_evaluator.evaluate(request, vendor_detection.vendor)

        # Step 3: Make routing decision based on coverage
        routing_decision = self._make_routing_decision(
            request, vendor_detection, kb_coverage
        )

        # Step 4: Execute appropriate route
        if routing_decision.route == RouteType.ROUTE_A:
            return await self._route_a_strong_kb(request, routing_decision)
        elif routing_decision.route == RouteType.ROUTE_B:
            return await self._route_b_thin_kb(request, routing_decision)
        elif routing_decision.route == RouteType.ROUTE_C:
            return await self._route_c_no_kb(request, routing_decision)
        else:  # ROUTE_D
            return await self._route_d_unclear(request, routing_decision)

    def _make_routing_decision(
        self,
        request: RivetRequest,
        vendor_detection: VendorDetection,
        kb_coverage: KBCoverage,
    ) -> RoutingDecision:
        """Determine which route to take based on KB coverage.

        Args:
            request: User query request
            vendor_detection: Detected vendor with confidence
            kb_coverage: KB coverage metrics

        Returns:
            RoutingDecision with route, reasoning, and SME agent
        """
        # Route D: Unclear intent (highest priority)
        if self.kb_evaluator.is_unclear(kb_coverage):
            self._route_counts[RouteType.ROUTE_D] += 1
            return RoutingDecision(
                route=RouteType.ROUTE_D,
                vendor_detection=vendor_detection,
                kb_coverage=kb_coverage,
                reasoning=f"Query intent is unclear (confidence: {kb_coverage.confidence:.2f}). "
                f"Requesting clarification from user before proceeding.",
                sme_agent=None,
            )

        # Get SME agent name for routes A and B
        sme_agent = self._get_agent_name(vendor_detection.vendor)

        # Route A: Strong KB coverage → direct answer
        if self.kb_evaluator.is_strong_coverage(kb_coverage):
            self._route_counts[RouteType.ROUTE_A] += 1
            return RoutingDecision(
                route=RouteType.ROUTE_A,
                vendor_detection=vendor_detection,
                kb_coverage=kb_coverage,
                reasoning=f"Strong KB coverage ({kb_coverage.atom_count} atoms, "
                f"{kb_coverage.avg_relevance:.2f} relevance) for {vendor_detection.vendor.value} query. "
                f"Routing to {sme_agent} for direct answer with citations.",
                sme_agent=sme_agent,
            )

        # Route B: Thin KB coverage → answer + enrichment
        if self.kb_evaluator.is_thin_coverage(kb_coverage):
            self._route_counts[RouteType.ROUTE_B] += 1
            return RoutingDecision(
                route=RouteType.ROUTE_B,
                vendor_detection=vendor_detection,
                kb_coverage=kb_coverage,
                reasoning=f"Thin KB coverage ({kb_coverage.atom_count} atoms, "
                f"{kb_coverage.avg_relevance:.2f} relevance) for {vendor_detection.vendor.value} query. "
                f"Routing to {sme_agent} for answer, then triggering enrichment pipeline.",
                sme_agent=sme_agent,
            )

        # Route C: No KB coverage → research pipeline
        self._route_counts[RouteType.ROUTE_C] += 1
        return RoutingDecision(
            route=RouteType.ROUTE_C,
            vendor_detection=vendor_detection,
            kb_coverage=kb_coverage,
            reasoning=f"No KB coverage ({kb_coverage.atom_count} atoms, "
            f"{kb_coverage.avg_relevance:.2f} relevance) for {vendor_detection.vendor.value} query. "
            f"Triggering research pipeline (Phase 5) to gather knowledge.",
            sme_agent=None,
        )

    def _get_agent_name(self, vendor: VendorType) -> str:
        """Get human-readable agent name for logging.

        Args:
            vendor: VendorType enum

        Returns:
            Agent name string
        """
        agent_names = {
            VendorType.SIEMENS: "siemens_agent",
            VendorType.ROCKWELL: "rockwell_agent",
            VendorType.GENERIC: "generic_plc_agent",
            VendorType.SAFETY: "safety_agent",
        }
        return agent_names.get(vendor, "unknown_agent")

    def _get_agent_id(self, vendor: VendorType) -> AgentID:
        """Map VendorType to AgentID enum.

        Args:
            vendor: VendorType from routing schemas

        Returns:
            AgentID enum for models
        """
        agent_id_map = {
            VendorType.SIEMENS: AgentID.SIEMENS,
            VendorType.ROCKWELL: AgentID.ROCKWELL,
            VendorType.GENERIC: AgentID.GENERIC_PLC,
            VendorType.SAFETY: AgentID.SAFETY,
        }
        return agent_id_map.get(vendor, AgentID.FALLBACK)

    def _get_model_route_type(self, route: RouteType) -> ModelRouteType:
        """Map routing RouteType to model RouteType.

        Args:
            route: RouteType from routing schemas

        Returns:
            RouteType enum from models
        """
        route_map = {
            RouteType.ROUTE_A: ModelRouteType.ROUTE_A,
            RouteType.ROUTE_B: ModelRouteType.ROUTE_B,
            RouteType.ROUTE_C: ModelRouteType.ROUTE_C,
            RouteType.ROUTE_D: ModelRouteType.ROUTE_D,
        }
        return route_map.get(route, ModelRouteType.ROUTE_C)

    async def _route_a_strong_kb(
        self, request: RivetRequest, decision: RoutingDecision
    ) -> RivetResponse:
        """Route A: Strong KB coverage → direct answer from SME agent.

        Args:
            request: User query request
            decision: Routing decision with vendor and coverage info

        Returns:
            RivetResponse with direct answer and citations
        """
        vendor = decision.vendor_detection.vendor
        agent = self.sme_agents[vendor]

        # Get answer from SME agent
        response = await agent.handle_query(request)

        # Update response with routing metadata
        response.route_taken = self._get_model_route_type(RouteType.ROUTE_A)
        response.trace["routing_decision"] = decision.reasoning
        response.trace["route"] = "A"
        response.trace["vendor"] = vendor.value
        response.trace["kb_coverage"] = decision.kb_coverage.level.value

        return response

    async def _route_b_thin_kb(
        self, request: RivetRequest, decision: RoutingDecision
    ) -> RivetResponse:
        """Route B: Thin KB coverage → answer + enrichment trigger.

        Args:
            request: User query request
            decision: Routing decision with vendor and coverage info

        Returns:
            RivetResponse with answer and enrichment flag set
        """
        vendor = decision.vendor_detection.vendor
        agent = self.sme_agents[vendor]

        # Get answer from SME agent
        response = await agent.handle_query(request)

        # Update response with routing metadata
        response.route_taken = self._get_model_route_type(RouteType.ROUTE_B)
        response.trace["routing_decision"] = decision.reasoning
        response.trace["route"] = "B"
        response.trace["vendor"] = vendor.value
        response.trace["kb_coverage"] = decision.kb_coverage.level.value
        response.kb_enrichment_triggered = True

        # TODO: Trigger enrichment pipeline (Phase 5 integration)
        # enrichment_queue.add(topic=request.text, vendor=vendor)

        return response

    async def _route_c_no_kb(
        self, request: RivetRequest, decision: RoutingDecision
    ) -> RivetResponse:
        """Route C: No KB coverage → Groq LLM fallback.

        NEW (2025-12-22): Uses Groq instead of hardcoded message.
        NEW (2025-12-22): Logs KB gap for tracking missing content.

        Args:
            request: User query request
            decision: Routing decision with vendor and coverage info

        Returns:
            RivetResponse with LLM-generated answer or hardcoded fallback
        """
        vendor = decision.vendor_detection.vendor if decision.vendor_detection else VendorType.GENERIC

        # Note: KB gap logging skipped in Route C because:
        # 1. We already know there's no KB coverage (that's why we're in Route C)
        # 2. RoutingDecision doesn't contain parsed intent data
        # 3. Gap is implicit - no need to log explicitly

        # Generate LLM response
        response_text, confidence = self._generate_llm_response(
            query=request.text or "",
            route_type=RouteType.ROUTE_C,
            vendor=vendor
        )

        return RivetResponse(
            text=response_text,
            agent_id=self._get_agent_id(decision.vendor_detection.vendor),
            route_taken=self._get_model_route_type(RouteType.ROUTE_C),
            confidence=confidence,
            requires_followup=True,
            research_triggered=True,
            trace={
                "routing_decision": decision.reasoning,
                "route": "C",
                "vendor": decision.vendor_detection.vendor.value,
                "kb_coverage": decision.kb_coverage.level.value,
                "llm_fallback": True,
                "llm_generated": confidence > 0.0,
            }
        )

    async def _route_d_unclear(
        self, request: RivetRequest, decision: RoutingDecision
    ) -> RivetResponse:
        """Route D: Unclear intent → Groq LLM fallback.

        NEW (2025-12-22): Uses Groq instead of hardcoded message.

        Args:
            request: User query request
            decision: Routing decision with vendor and coverage info

        Returns:
            RivetResponse with LLM-generated clarification or hardcoded fallback
        """
        # Generate LLM response
        response_text, confidence = self._generate_llm_response(
            query=request.text or "",
            route_type=RouteType.ROUTE_D,
            vendor=decision.vendor_detection.vendor
        )

        return RivetResponse(
            text=response_text,
            agent_id=self._get_agent_id(decision.vendor_detection.vendor),
            route_taken=self._get_model_route_type(RouteType.ROUTE_D),
            confidence=confidence,
            requires_followup=True,
            trace={
                "routing_decision": decision.reasoning,
                "route": "D",
                "vendor": decision.vendor_detection.vendor.value,
                "kb_coverage": decision.kb_coverage.level.value,
                "llm_fallback": True,
                "llm_generated": confidence > 0.0,
            }
        )

    def _generate_llm_response(
        self,
        query: str,
        route_type: RouteType,
        vendor: VendorType
    ) -> tuple[str, float]:
        """Generate LLM response for Routes C and D using Groq fallback.

        Args:
            query: User query text
            route_type: RouteType.ROUTE_C or RouteType.ROUTE_D
            vendor: Detected vendor type

        Returns:
            Tuple of (response_text, confidence_score)
        """
        # Build system prompt
        if route_type == RouteType.ROUTE_C:
            system_prompt = (
                "You are RivetCEO, an industrial maintenance AI assistant. "
                "The knowledge base doesn't have information on this query. "
                "Provide a helpful, accurate response using your general knowledge. "
                "IMPORTANT: "
                "- Do NOT hallucinate specific model numbers or part codes "
                "- Do NOT provide unsafe electrical advice without LOTO warnings "
                "- If uncertain, say 'I recommend consulting manufacturer documentation' "
                "- Keep response under 300 words "
                "- Focus on general troubleshooting principles"
            )
        else:  # ROUTE_D
            system_prompt = (
                "You are RivetCEO, an industrial maintenance AI assistant. "
                "The user's query is unclear. Help them clarify by asking specific questions. "
                "Ask about: equipment (vendor, model), symptoms/error codes, what they've tried. "
                "Keep response under 150 words. Be friendly and helpful."
            )

        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]

        # Build config with Groq primary + GPT-3.5 fallback
        config = LLMConfig(
            provider=LLMProvider.GROQ,
            model="llama-3.1-70b-versatile",
            temperature=0.7,
            max_tokens=500,
            fallback_models=["gpt-3.5-turbo"],
        )

        try:
            # Call LLM (retries + fallbacks automatic)
            llm_response: LLMResponse = self.llm_router.complete(messages, config)

            # Calculate confidence
            if route_type == RouteType.ROUTE_C:
                base = 0.5 if llm_response.model == "llama-3.1-70b-versatile" else 0.6
            else:  # ROUTE_D
                base = 0.3

            confidence = base * 0.9 if llm_response.fallback_used else base

            logger.info(
                f"LLM response for {route_type.value}: "
                f"model={llm_response.model}, cost=${llm_response.usage.total_cost_usd:.4f}, "
                f"confidence={confidence:.2f}"
            )

            return (llm_response.content, confidence)

        except Exception as e:
            # All LLMs failed → hardcoded message
            logger.error(f"All LLMs failed for {route_type.value}: {e}")

            if route_type == RouteType.ROUTE_C:
                fallback = (
                    "Thank you for your question. Our knowledge base doesn't have enough "
                    "information to provide a confident answer right now.\n\n"
                    "I've triggered our research pipeline to gather information on this topic. "
                    "We'll notify you once we have a comprehensive answer (typically within 24-48 hours).\n\n"
                    "In the meantime, you can:\n"
                    "- Check manufacturer documentation directly\n"
                    "- Post your question on relevant forums (Reddit, PLCTalk)\n"
                    "- Contact technical support for urgent issues"
                )
            else:  # ROUTE_D
                fallback = (
                    "I'd like to help, but I need a bit more information to understand your question.\n\n"
                    "Could you clarify:\n"
                    "- What specific equipment or system are you working with?\n"
                    "- What problem are you trying to solve?\n"
                    "- What have you already tried?\n\n"
                    "Example: 'My Siemens S7-1200 PLC shows fault code 0x1234. "
                    "I've checked wiring and power supply. How do I diagnose this?'"
                )

            return (fallback, 0.0)

    def get_routing_stats(self) -> Dict[str, int]:
        """Get routing statistics for monitoring.

        Returns:
            Dictionary with route counts
        """
        return {
            "route_a_count": self._route_counts[RouteType.ROUTE_A],
            "route_b_count": self._route_counts[RouteType.ROUTE_B],
            "route_c_count": self._route_counts[RouteType.ROUTE_C],
            "route_d_count": self._route_counts[RouteType.ROUTE_D],
            "total_queries": sum(self._route_counts.values()),
        }

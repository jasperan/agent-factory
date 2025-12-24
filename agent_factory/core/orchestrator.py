"""RIVET Pro Orchestrator - 4-Route Query Routing System.

Routes queries based on vendor detection and KB coverage evaluation:
- Route A: Strong KB coverage → direct answer from SME agent
- Route B: Thin KB coverage → SME agent + enrichment trigger
- Route C: No KB coverage → research pipeline trigger (Phase 5)
- Route D: Unclear intent → clarification request
"""

from typing import Optional, Dict
import asyncio
import time
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
from agent_factory.core.gap_detector import GapDetector
from agent_factory.core.performance import timed_operation, PerformanceTracker
import logging

logger = logging.getLogger(__name__)

# Phase 3 SME Agents - PRODUCTION (replaced mocks on 2025-12-23)
from agent_factory.rivet_pro.agents.siemens_agent import SiemensAgent
from agent_factory.rivet_pro.agents.rockwell_agent import RockwellAgent
from agent_factory.rivet_pro.agents.generic_agent import GenericAgent
from agent_factory.rivet_pro.agents.safety_agent import SafetyAgent


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

        # Initialize LLM Router for Groq fallback (before SME agents)
        self.llm_router = LLMRouter(
            max_retries=3,
            retry_delay=1.0,
            enable_fallback=True,
            enable_cache=False
        )

        # Load SME agents (requires llm_router to be initialized)
        self.sme_agents = self._load_sme_agents()

        # Initialize KB gap logger (Phase 1: KB gap tracking)
        self.kb_gap_logger = None
        # Initialize gap detector (Phase 2: Auto-trigger ingestion)
        self.gap_detector = None
        if rag_layer:
            try:
                self.kb_gap_logger = KBGapLogger(db=rag_layer)
                self.gap_detector = GapDetector(kb_evaluator=self.kb_evaluator)
                logger.info("KB gap logger and gap detector initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize KB gap systems: {e}")

        # Routing statistics
        self._route_counts: Dict[RouteType, int] = {
            RouteType.ROUTE_A: 0,
            RouteType.ROUTE_B: 0,
            RouteType.ROUTE_C: 0,
            RouteType.ROUTE_D: 0,
        }

        # LLM response cache (5-minute TTL to reduce API costs)
        self._llm_cache: Dict[str, tuple[tuple[str, float], float]] = {}  # {cache_key: ((response, confidence), timestamp)}
        self._cache_ttl = 300  # 5 minutes in seconds

    def _load_sme_agents(self) -> Dict[VendorType, object]:
        """Load SME agents for each vendor type.

        Phase 3 COMPLETE (2025-12-23):
        - SiemensAgent: Specialized for Siemens equipment
        - RockwellAgent: Specialized for Allen-Bradley equipment
        - GenericAgent: Cross-vendor industrial automation
        - SafetyAgent: Safety systems and standards

        Returns:
            Dictionary mapping VendorType to agent instances
        """
        return {
            VendorType.SIEMENS: SiemensAgent(llm_router=self.llm_router),
            VendorType.ROCKWELL: RockwellAgent(llm_router=self.llm_router),
            VendorType.GENERIC: GenericAgent(llm_router=self.llm_router),
            VendorType.SAFETY: SafetyAgent(llm_router=self.llm_router),
        }

    @timed_operation("route_query_total")
    async def route_query(self, request: RivetRequest) -> RivetResponse:
        """Main routing logic - evaluates query and routes to appropriate handler.

        Args:
            request: User query request

        Returns:
            RivetResponse from appropriate route handler
        """
        # Step 1: Detect vendor from query
        vendor_detection = self.vendor_detector.detect(request.text or "")

        # Step 2: Evaluate KB coverage for detected vendor (async to avoid blocking)
        kb_coverage = await self.kb_evaluator.evaluate_async(request, vendor_detection.vendor)

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

        # Get answer from SME agent with KB coverage
        response = await agent.handle_query(request, decision.kb_coverage)

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

        # Get answer from SME agent with KB coverage
        response = await agent.handle_query(request, decision.kb_coverage)

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

    @timed_operation("route_c_handler")
    async def _route_c_no_kb(
        self, request: RivetRequest, decision: RoutingDecision
    ) -> RivetResponse:
        """Route C: No KB coverage → Gap detection + LLM fallback + Ingestion trigger.

        NEW (2025-12-22): Uses Groq instead of hardcoded message.
        NEW (2025-12-22): Logs KB gap for tracking missing content.
        NEW (2025-12-23): Gap detector analyzes query and triggers ingestion.
        NEW (2025-12-24): Parallelized gap detection + LLM response (36s → <5s target).

        Args:
            request: User query request
            decision: Routing decision with vendor and coverage info

        Returns:
            RivetResponse with LLM-generated answer + ingestion trigger
        """
        vendor = decision.vendor_detection.vendor if decision.vendor_detection else VendorType.GENERIC

        # PARALLEL EXECUTION: Gap detection + LLM response (don't block each other)
        gap_task = asyncio.create_task(
            self._analyze_gap_async(request, decision, vendor)
        )
        llm_task = asyncio.create_task(
            self._generate_llm_response_async(request.text or "", RouteType.ROUTE_C, vendor)
        )

        # Wait for both to complete
        ingestion_trigger, (response_text, confidence) = await asyncio.gather(
            gap_task, llm_task
        )

        # Append ingestion trigger marker to response (if generated)
        if ingestion_trigger:
            trigger_display = self.gap_detector.format_trigger_for_display(ingestion_trigger)
            response_text += trigger_display

            # Fire-and-forget: Gap logging + research trigger (don't block user response)
            intent_data = ingestion_trigger.get("intent")  # Intent returned from gap analysis
            if intent_data:
                asyncio.create_task(
                    self._log_and_trigger_research(ingestion_trigger, intent_data, request, vendor, decision)
                )

        return RivetResponse(
            text=response_text,
            agent_id=self._get_agent_id(decision.vendor_detection.vendor),
            route_taken=self._get_model_route_type(RouteType.ROUTE_C),
            confidence=confidence,
            requires_followup=True,
            research_triggered=bool(ingestion_trigger),
            trace={
                "routing_decision": decision.reasoning,
                "route": "C",
                "vendor": decision.vendor_detection.vendor.value,
                "kb_coverage": decision.kb_coverage.level.value,
                "llm_fallback": True,
                "llm_generated": confidence > 0.0,
                "ingestion_trigger": ingestion_trigger if ingestion_trigger else None,
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

    @timed_operation("gap_detection")
    async def _analyze_gap_async(
        self,
        request: RivetRequest,
        decision: RoutingDecision,
        vendor: VendorType
    ) -> Optional[Dict]:
        """Analyze knowledge gap asynchronously (runs in parallel with LLM).

        Args:
            request: User query request
            decision: Routing decision with coverage info
            vendor: Detected vendor type

        Returns:
            Ingestion trigger dict (with intent) or None if gap detection unavailable
        """
        if not (self.gap_detector and self.kb_gap_logger):
            return None

        try:
            # Map routing VendorType to RivetIntent VendorType
            from agent_factory.rivet_pro.models import VendorType as RivetVendorType
            vendor_map = {
                VendorType.SIEMENS: RivetVendorType.SIEMENS,
                VendorType.ROCKWELL: RivetVendorType.ROCKWELL,
                VendorType.GENERIC: RivetVendorType.GENERIC,
                VendorType.SAFETY: RivetVendorType.UNKNOWN,
            }
            rivet_vendor = vendor_map.get(vendor, RivetVendorType.UNKNOWN)

            # Create RivetIntent for gap analysis
            from agent_factory.rivet_pro.models import RivetIntent, KBCoverage as RivetKBCoverage
            intent = RivetIntent(
                vendor=rivet_vendor,
                equipment_type=EquipmentType.UNKNOWN,  # Could parse from request
                symptom=request.text or "",
                raw_summary=request.text or "",
                context_source="text_only",
                confidence=0.8,
                kb_coverage=RivetKBCoverage.NONE
            )

            # Analyze query for knowledge gaps (synchronous, but runs in parallel with LLM)
            ingestion_trigger = self.gap_detector.analyze_query(
                request=request,
                intent=intent,
                kb_coverage=decision.kb_coverage.level
            )

            # Attach intent to trigger for later use
            if ingestion_trigger:
                ingestion_trigger["intent"] = intent

            return ingestion_trigger

        except Exception as e:
            logger.error(f"Failed to analyze gap: {e}", exc_info=True)
            return None

    @timed_operation("llm_response_async")
    async def _generate_llm_response_async(
        self,
        query: str,
        route_type: RouteType,
        vendor: VendorType
    ) -> tuple[str, float]:
        """Generate LLM response asynchronously (runs in thread pool to avoid blocking).

        Args:
            query: User query text
            route_type: RouteType.ROUTE_C or RouteType.ROUTE_D
            vendor: Detected vendor type

        Returns:
            Tuple of (response_text, confidence_score)
        """
        # Run synchronous LLM call in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,  # Use default ThreadPoolExecutor
            self._generate_llm_response,
            query,
            route_type,
            vendor
        )

    @timed_operation("gap_logging_and_research")
    async def _log_and_trigger_research(
        self,
        ingestion_trigger: Dict,
        intent: "RivetIntent",
        request: RivetRequest,
        vendor: VendorType,
        decision: RoutingDecision
    ) -> None:
        """Log gap to database and trigger research pipeline (fire-and-forget).

        This runs in background after user receives response, so DB write latency
        doesn't block the user.

        Args:
            ingestion_trigger: Trigger dict from gap detector
            intent: Parsed RivetIntent for logging
            request: User query request
            vendor: Detected vendor type
            decision: Routing decision
        """
        try:
            # Log gap to database
            gap_id = self.kb_gap_logger.log_gap(
                query=request.text or "",
                intent=intent,
                search_filters={
                    "vendor": vendor.value,
                    "kb_coverage": decision.kb_coverage.level.value
                },
                user_id=request.user_id
            )
            ingestion_trigger["gap_id"] = gap_id
            logger.info(
                f"Gap logged: gap_id={gap_id}, "
                f"priority={ingestion_trigger['priority']}, "
                f"equipment={ingestion_trigger['equipment_identified']}"
            )

            # Trigger research pipeline
            await self._trigger_research_async(ingestion_trigger, intent)

        except Exception as e:
            logger.error(f"Failed to log gap and trigger research: {e}", exc_info=True)

    @timed_operation("llm_fallback")
    def _generate_llm_response(
        self,
        query: str,
        route_type: RouteType,
        vendor: VendorType
    ) -> tuple[str, float]:
        """Generate LLM response for Routes C and D using Groq fallback.

        Uses 5-minute cache to avoid redundant API calls for similar queries.

        Args:
            query: User query text
            route_type: RouteType.ROUTE_C or RouteType.ROUTE_D
            vendor: Detected vendor type

        Returns:
            Tuple of (response_text, confidence_score)
        """
        # Check cache (5-minute TTL)
        cache_key = f"{route_type.value}:{vendor.value}:{hash(query)}"
        current_time = time.time()

        if cache_key in self._llm_cache:
            cached_response, cached_time = self._llm_cache[cache_key]
            age_seconds = current_time - cached_time

            if age_seconds < self._cache_ttl:
                logger.info(
                    f"LLM cache HIT for {route_type.value} (age: {age_seconds:.1f}s, "
                    f"saved ~$0.002)"
                )
                return cached_response

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

            # Cache response for 5 minutes
            response_tuple = (llm_response.content, confidence)
            self._llm_cache[cache_key] = (response_tuple, current_time)
            logger.debug(f"LLM cache STORE for {route_type.value} (TTL: {self._cache_ttl}s)")

            return response_tuple

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

    @timed_operation("research_trigger")
    async def _trigger_research_async(
        self, trigger: Dict, intent: "RivetIntent"
    ) -> None:
        """
        Trigger research pipeline asynchronously (background task).

        This method spawns the research pipeline in the background to avoid
        blocking the user response. Results are logged but not returned to user.

        Args:
            trigger: Ingestion trigger dictionary from gap detector
            intent: Parsed RivetIntent for research query
        """
        try:
            logger.info(
                f"Spawning research pipeline in background: "
                f"gap_id={trigger.get('gap_id')}, "
                f"equipment={trigger['equipment_identified']}, "
                f"priority={trigger['priority']}"
            )

            # Import ResearchPipeline (lazy import to avoid circular dependencies)
            from agent_factory.rivet_pro.research.research_pipeline import ResearchPipeline

            # Create research pipeline with existing database manager
            if hasattr(self, 'kb_evaluator') and hasattr(self.kb_evaluator, 'rag'):
                pipeline = ResearchPipeline(db_manager=self.kb_evaluator.rag)
            else:
                from agent_factory.core.database_manager import DatabaseManager
                pipeline = ResearchPipeline(db_manager=DatabaseManager())

            # Run research pipeline in thread pool (it's synchronous)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,  # Use default ThreadPoolExecutor
                pipeline.run,
                intent
            )

            # Log results
            logger.info(
                f"Research pipeline completed: "
                f"gap_id={trigger.get('gap_id')}, "
                f"status={result.status}, "
                f"sources_found={len(result.sources_found)}, "
                f"sources_queued={result.sources_queued}, "
                f"estimated_completion={result.estimated_completion}"
            )

            # Update gap logger if research succeeded
            if result.status == "success" and self.kb_gap_logger:
                gap_id = trigger.get('gap_id')
                if gap_id and gap_id > 0:
                    # Note: Gap will be marked resolved after atoms are ingested
                    # For now, just log that research was triggered
                    logger.info(f"Research triggered for gap_id={gap_id}")

        except Exception as e:
            logger.error(
                f"Failed to trigger research pipeline: {e}",
                exc_info=True
            )

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

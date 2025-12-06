"""
Orchestrator - Multi-Agent Routing System

Generated from: specs/orchestrator-v1.0.md
Generated on: 2025-12-05
Spec SHA256: orchestrator-hash

REGENERATION: python factory.py specs/orchestrator-v1.0.md

Routes queries to specialist agents using hybrid logic:
1. Keyword matching (fast, deterministic)
2. LLM classification (flexible, intelligent)
3. Fallback agent (graceful degradation)
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime
import time

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

from .callbacks import EventBus, EventType, create_default_event_bus


@dataclass
class AgentRegistration:
    """
    Metadata for a registered agent.

    Implements: REQ-ORCH-001 (Agent Registration)
    Spec: specs/orchestrator-v1.0.md#section-3.1
    """
    name: str                          # Unique identifier
    agent: Any                         # LangChain AgentExecutor
    keywords: List[str] = field(default_factory=list)  # Trigger words (lowercase)
    description: str = ""              # Human-readable purpose
    priority: int = 0                  # Tie-breaker (higher wins)


@dataclass
class RouteResult:
    """
    Result of routing operation.

    Implements: REQ-ORCH-004 (Agent Execution)
    Spec: specs/orchestrator-v1.0.md#section-3.2

    The response field can be:
    - Raw dict (default, backwards compatible)
    - Pydantic BaseModel instance (if agent has response_schema)
    - None (if error occurred)
    """
    agent_name: str                    # Which agent handled query
    method: str                        # "keyword" | "llm" | "fallback" | "direct"
    confidence: float                  # 0.0-1.0 routing confidence
    response: Union[Dict[str, Any], BaseModel, None] = None  # Agent output (dict or Pydantic model)
    error: Optional[str] = None        # Error message if failed
    duration_ms: Optional[float] = None  # Execution time
    trace_id: Optional[str] = None     # Trace ID for observability (Phase 3)


class AgentOrchestrator:
    """
    Multi-agent routing system with hybrid matching.

    Implements: REQ-ORCH-003 through REQ-ORCH-009
    Spec: specs/orchestrator-v1.0.md

    Routes queries using priority order:
    1. Keyword matching (fast, deterministic)
    2. LLM classification (flexible, intelligent)
    3. Fallback agent (graceful degradation)
    4. Error response (no agent available)

    Attributes:
        _agents: Registry of registered agents
        _llm: Optional LLM for classification fallback
        _event_bus: Event system for observability
        _fallback_agent: Agent name to use when no match

    Examples:
        >>> orch = AgentOrchestrator(llm=my_llm)
        >>> orch.register("calendar", agent, keywords=["schedule", "meeting"])
        >>> result = orch.route("What's on my schedule?")
        >>> result.agent_name
        'calendar'
    """

    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        event_bus: Optional[EventBus] = None,
        verbose: bool = False,
        enable_observability: bool = True
    ):
        self._agents: Dict[str, AgentRegistration] = {}
        self._llm = llm
        self._event_bus = event_bus or create_default_event_bus(verbose)
        self._verbose = verbose
        self._fallback_agent: Optional[str] = None

        # Observability (Phase 3)
        self._enable_observability = enable_observability
        if enable_observability:
            from agent_factory.observability import Tracer, Metrics, CostTracker
            self.tracer = Tracer()
            self.metrics = Metrics()
            self.cost_tracker = CostTracker()
        else:
            self.tracer = None
            self.metrics = None
            self.cost_tracker = None

    @property
    def event_bus(self) -> EventBus:
        """Access event bus for external subscriptions."""
        return self._event_bus

    def register(
        self,
        name: str,
        agent: Any,
        keywords: Optional[List[str]] = None,
        description: str = "",
        priority: int = 0,
        is_fallback: bool = False
    ) -> None:
        """
        Register an agent with the orchestrator.

        Args:
            name: Unique identifier for the agent
            agent: LangChain agent instance
            keywords: Words that trigger this agent (case-insensitive)
            description: Human-readable description for LLM classification
            priority: Higher priority wins ties (default 0)
            is_fallback: Use this agent when no match found
        """
        if name in self._agents:
            raise ValueError(f"Agent '{name}' already registered")

        self._agents[name] = AgentRegistration(
            name=name,
            agent=agent,
            keywords=[k.lower() for k in (keywords or [])],
            description=description or f"Agent: {name}",
            priority=priority
        )

        if is_fallback:
            self._fallback_agent = name

        if self._verbose:
            print(f"[Orchestrator] Registered: {name} (keywords: {keywords})")

    def unregister(self, name: str) -> None:
        """Remove an agent from the orchestrator."""
        if name in self._agents:
            del self._agents[name]
            if self._fallback_agent == name:
                self._fallback_agent = None

    def list_agents(self) -> List[str]:
        """Return list of registered agent names."""
        return list(self._agents.keys())

    def get_agent(self, name: str) -> Optional[Any]:
        """Get agent by name."""
        reg = self._agents.get(name)
        return reg.agent if reg else None

    def _parse_response(
        self,
        response: Any,
        agent: Any
    ) -> Union[Dict[str, Any], BaseModel]:
        """
        Parse agent response into structured format if schema is defined.

        Args:
            response: Raw agent response
            agent: Agent that generated the response

        Returns:
            Either the raw response (dict) or a validated Pydantic model instance
        """
        # Check if agent has a response schema
        response_schema = getattr(agent, 'metadata', {}).get('response_schema')

        if not response_schema:
            # No schema defined, return raw response
            return response

        # Try to parse response into schema
        try:
            # Extract output from response dict
            if isinstance(response, dict):
                output_text = response.get('output', str(response))
            else:
                output_text = str(response)

            # Create schema instance with parsed data
            # For now, we'll create a basic instance with success=True and output
            # More sophisticated parsing can be added later
            schema_instance = response_schema(
                success=True,
                output=output_text,
                metadata={}
            )
            return schema_instance

        except (ValidationError, TypeError, AttributeError) as e:
            # Schema parsing failed, return raw response
            # Could emit error event here
            if self._verbose:
                print(f"[Orchestrator] Schema validation failed: {e}")
            return response

    def _match_keywords(self, query: str) -> Optional[AgentRegistration]:
        """
        Find agent by keyword matching.
        Returns highest priority match.
        """
        query_lower = query.lower()
        matches: List[AgentRegistration] = []

        for reg in self._agents.values():
            for keyword in reg.keywords:
                if keyword in query_lower:
                    matches.append(reg)
                    break

        if not matches:
            return None

        # Return highest priority
        return max(matches, key=lambda r: r.priority)

    def _classify_with_llm(self, query: str) -> Optional[AgentRegistration]:
        """
        Use LLM to classify query when keywords don't match.
        """
        if not self._llm:
            return None

        if not self._agents:
            return None

        # Build agent descriptions
        agent_list = "\n".join([
            f"- {name}: {reg.description}"
            for name, reg in self._agents.items()
        ])

        system_prompt = f"""You are a query router. Given a user query, select the most appropriate agent.

Available agents:
{agent_list}

Respond with ONLY the agent name, nothing else. If no agent fits, respond with "NONE"."""

        try:
            response = self._llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=query)
            ])

            agent_name = response.content.strip()

            if agent_name == "NONE":
                return None

            return self._agents.get(agent_name)

        except Exception as e:
            self._event_bus.emit(
                EventType.ERROR,
                {"error_type": "llm_classification", "message": str(e)}
            )
            return None

    def _extract_tokens(self, response: Any) -> Dict[str, int]:
        """Extract token usage from agent response."""
        # Try to extract token usage from response metadata
        # LangChain responses may have usage_metadata
        try:
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                return {
                    "prompt": usage.get("input_tokens", 0),
                    "completion": usage.get("output_tokens", 0),
                    "total": usage.get("total_tokens", 0)
                }
            # Fallback to empty
            return {"prompt": 0, "completion": 0, "total": 0}
        except:
            return {"prompt": 0, "completion": 0, "total": 0}

    def route(self, query: str) -> RouteResult:
        """
        Route query to appropriate agent and execute.

        Routing order:
        1. Keyword match (fast, deterministic)
        2. LLM classification (flexible)
        3. Fallback agent (if configured)
        4. Error response

        Returns:
            RouteResult with agent response or error
        """
        start_time = time.time()
        trace_id = None

        # Start trace (Phase 3 - Observability)
        if self._enable_observability:
            trace_id = self.tracer.start_trace(query)

        # Try keyword matching first
        matched = self._match_keywords(query)
        method = "keyword"
        confidence = 1.0

        # Fall back to LLM
        if not matched:
            matched = self._classify_with_llm(query)
            method = "llm"
            confidence = 0.8  # LLM classification is less certain

        # Fall back to fallback agent
        if not matched and self._fallback_agent:
            matched = self._agents.get(self._fallback_agent)
            method = "fallback"
            confidence = 0.5

        # No match at all
        if not matched:
            if self._enable_observability:
                self.tracer.finish_trace(success=False, error="No agent found")
            return RouteResult(
                agent_name="",
                method="none",
                confidence=0.0,
                error="No agent found for query",
                trace_id=trace_id
            )

        # Emit routing decision
        self._event_bus.emit(
            EventType.ROUTE_DECISION,
            {
                "query": query,
                "matched_agent": matched.name,
                "method": method,
                "confidence": confidence
            }
        )

        # Execute agent
        try:
            if self._enable_observability:
                span = self.tracer.start_span("agent_execution", agent=matched.name)

            self._event_bus.emit(
                EventType.AGENT_START,
                {"query": query},
                agent_name=matched.name
            )

            # Invoke the agent
            raw_response = matched.agent.invoke({"input": query})

            # Parse response into schema if defined
            parsed_response = self._parse_response(raw_response, matched.agent)

            duration_ms = (time.time() - start_time) * 1000

            # Extract token usage
            tokens = self._extract_tokens(raw_response)

            # Record observability metrics (Phase 3)
            if self._enable_observability:
                span.finish()

                # Record metrics
                self.metrics.record_request(
                    agent_name=matched.name,
                    duration_ms=duration_ms,
                    success=True,
                    tokens=tokens
                )

                # Record costs
                agent_metadata = matched.agent.metadata
                self.cost_tracker.record_cost(
                    agent_name=matched.name,
                    provider=agent_metadata.get("llm_provider", "unknown"),
                    model=agent_metadata.get("model", "unknown"),
                    prompt_tokens=tokens.get("prompt", 0),
                    completion_tokens=tokens.get("completion", 0)
                )

                # Finish trace
                self.tracer.finish_trace(
                    success=True,
                    agent_name=matched.name,
                    method=method
                )

            self._event_bus.emit(
                EventType.AGENT_END,
                {"output": str(parsed_response), "duration_ms": duration_ms},
                agent_name=matched.name
            )

            return RouteResult(
                agent_name=matched.name,
                method=method,
                confidence=confidence,
                response=parsed_response,
                duration_ms=duration_ms,
                trace_id=trace_id
            )

        except Exception as e:
            # Record error metrics
            if self._enable_observability:
                self.metrics.record_request(
                    agent_name=matched.name,
                    duration_ms=(time.time() - start_time) * 1000,
                    success=False,
                    error_type="agent_execution"
                )
                self.tracer.finish_trace(success=False, error=str(e))

            self._event_bus.emit(
                EventType.ERROR,
                {"error_type": "agent_execution", "message": str(e)},
                agent_name=matched.name
            )

            return RouteResult(
                agent_name=matched.name,
                method=method,
                confidence=confidence,
                error=str(e),
                trace_id=trace_id
            )

    def route_to(self, agent_name: str, query: str) -> RouteResult:
        """
        Route directly to a specific agent (bypass routing).
        Useful for testing or explicit routing.
        """
        if agent_name not in self._agents:
            return RouteResult(
                agent_name=agent_name,
                method="direct",
                confidence=0.0,
                error=f"Agent '{agent_name}' not found"
            )

        matched = self._agents[agent_name]
        start_time = time.time()

        try:
            self._event_bus.emit(
                EventType.AGENT_START,
                {"query": query},
                agent_name=agent_name
            )

            raw_response = matched.agent.invoke({"input": query})

            # Parse response into schema if defined
            parsed_response = self._parse_response(raw_response, matched.agent)

            duration_ms = (time.time() - start_time) * 1000

            self._event_bus.emit(
                EventType.AGENT_END,
                {"output": str(parsed_response), "duration_ms": duration_ms},
                agent_name=agent_name
            )

            return RouteResult(
                agent_name=agent_name,
                method="direct",
                confidence=1.0,
                response=parsed_response,
                duration_ms=duration_ms
            )

        except Exception as e:
            self._event_bus.emit(
                EventType.ERROR,
                {"error_type": "agent_execution", "message": str(e)},
                agent_name=agent_name
            )

            return RouteResult(
                agent_name=agent_name,
                method="direct",
                confidence=1.0,
                error=str(e)
            )

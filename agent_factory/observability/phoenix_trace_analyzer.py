"""
Phoenix Trace Analyzer - Detect KB Weaknesses from Traces

Analyzes Phoenix traces to automatically detect knowledge base weaknesses
and calculate priority scores for automated research triggering.

Detects 6 weakness patterns:
1. Zero Atoms - Complete KB gap (CRITICAL: 100)
2. Thin Coverage - Weak KB match (HIGH: 70-90)
3. Low Relevance - Poor semantic matching (MEDIUM: 50-70)
4. Missing Citations - Content exists but not traceable (MEDIUM: 40-60)
5. Hallucination - Safety issue (CRITICAL: 95-100)
6. High Latency - Infrastructure or KB structure issue (MEDIUM: 30-50)
"""

import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class WeaknessType(str, Enum):
    """KB weakness types detected from traces."""
    ZERO_ATOMS = "zero_atoms"
    THIN_COVERAGE = "thin_coverage"
    LOW_RELEVANCE = "low_relevance"
    MISSING_CITATIONS = "missing_citations"
    HALLUCINATION_RISK = "hallucination_risk"
    HIGH_LATENCY = "high_latency"


@dataclass
class WeaknessSignal:
    """
    KB weakness detected from Phoenix trace.

    Attributes:
        weakness_type: Type of weakness detected
        priority_score: Urgency score (0-100, higher = more urgent)
        query_text: Original user query
        equipment_detected: Equipment identifier (e.g., "siemens:s7_1200")
        atoms_found: Number of KB atoms retrieved
        confidence: Route confidence score (0.0-1.0)
        relevance_scores: Top match relevance scores
        trace_id: Phoenix trace ID for tracking
        timestamp: When weakness was detected
        context: Additional trace metadata
    """
    weakness_type: WeaknessType
    priority_score: int
    query_text: str
    equipment_detected: str
    atoms_found: int
    confidence: float
    relevance_scores: List[float] = field(default_factory=list)
    trace_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Dict = field(default_factory=dict)


class PhoenixTraceAnalyzer:
    """
    Analyzes Phoenix traces to detect KB weaknesses.

    Connects to Phoenix backend and extracts weakness signals from trace spans.
    """

    def __init__(self, phoenix_url: str = "http://localhost:6006"):
        """
        Initialize analyzer.

        Args:
            phoenix_url: Phoenix server URL
        """
        self.phoenix_url = phoenix_url
        self.graphql_url = f"{phoenix_url}/graphql"
        self.last_analyzed_timestamp = None
        logger.info(f"PhoenixTraceAnalyzer initialized: {phoenix_url}")

    def poll_recent_traces(
        self,
        lookback_minutes: int = 5
    ) -> List[Dict]:
        """
        Poll Phoenix for traces from last N minutes.

        Uses Phoenix GraphQL API to fetch spans with KB retrieval data.

        Args:
            lookback_minutes: How far back to look for traces

        Returns:
            List of trace dictionaries with KB signals
        """
        try:
            # Calculate start time
            if self.last_analyzed_timestamp:
                start_time = self.last_analyzed_timestamp
            else:
                start_time = datetime.utcnow() - timedelta(minutes=lookback_minutes)

            # GraphQL query for KB retrieval and route decision spans
            query = """
                query GetRecentKBTraces($startTime: DateTime!) {
                    spans(
                        where: {
                            startTime: { gte: $startTime }
                            name: { in: ["knowledge_base.retrieval", "orchestrator.route_decision", "agent.reasoning"] }
                        }
                        first: 100
                    ) {
                        edges {
                            span: node {
                                context {
                                    spanId
                                    traceId
                                }
                                name
                                spanKind
                                statusCode
                                startTime
                                latencyMs
                                attributes
                            }
                        }
                    }
                }
            """

            variables = {
                "startTime": start_time.isoformat() + "Z"
            }

            logger.info(f"Polling Phoenix for traces since {start_time}")

            response = requests.post(
                self.graphql_url,
                json={"query": query, "variables": variables},
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code != 200:
                logger.error(f"Phoenix GraphQL error: {response.status_code}")
                return []

            data = response.json()

            if not data or "data" not in data:
                logger.warning("No data returned from Phoenix")
                return []

            spans_data = data.get("data", {}).get("spans", {})
            edges = spans_data.get("edges", [])

            traces = [edge["span"] for edge in edges]

            logger.info(f"Found {len(traces)} traces to analyze")

            # Update timestamp for next poll
            if traces:
                latest = max(traces, key=lambda t: t.get("startTime", ""))
                self.last_analyzed_timestamp = datetime.fromisoformat(
                    latest["startTime"].replace("Z", "+00:00")
                )

            return traces

        except Exception as e:
            logger.error(f"Failed to poll Phoenix traces: {e}", exc_info=True)
            return []

    def detect_weaknesses(self, trace: Dict) -> List[WeaknessSignal]:
        """
        Detect KB weakness patterns from trace.

        Analyzes trace attributes for 6 weakness types:
        1. Zero atoms (coverage=0.0) → CRITICAL
        2. Thin coverage (<0.5 confidence, <3 atoms) → HIGH
        3. Low relevance (<0.6 top match) → MEDIUM
        4. Missing citations (atoms found but sources=[]) → MEDIUM
        5. Hallucination risk (confidence>0.7 but atoms=0) → CRITICAL
        6. High latency (>2000ms) → MEDIUM

        Args:
            trace: Phoenix trace dictionary

        Returns:
            List of WeaknessSignal objects
        """
        weaknesses = []

        try:
            # Extract trace data
            trace_id = trace.get("context", {}).get("traceId", "unknown")
            span_name = trace.get("name", "")
            latency_ms = trace.get("latencyMs", 0)

            # Parse attributes
            attributes_str = trace.get("attributes", "{}")
            if isinstance(attributes_str, str):
                import json
                attributes = json.loads(attributes_str)
            else:
                attributes = attributes_str

            # Extract KB signals
            atoms_found = attributes.get("kb.atoms_found", 0)
            coverage = attributes.get("kb.coverage", 0.0)
            confidence = attributes.get("route.confidence", 0.0)
            query_text = attributes.get("query", "")
            equipment = attributes.get("equipment_detected", "unknown:unknown")

            # Extract relevance scores
            relevance_scores = []
            if "kb.top_matches" in attributes:
                try:
                    matches = json.loads(attributes["kb.top_matches"])
                    relevance_scores = [m[1] for m in matches if len(m) > 1]
                except:
                    pass

            # Pattern 1: Zero Atoms (CRITICAL)
            if atoms_found == 0 and coverage == 0.0:
                weaknesses.append(WeaknessSignal(
                    weakness_type=WeaknessType.ZERO_ATOMS,
                    priority_score=100,
                    query_text=query_text,
                    equipment_detected=equipment,
                    atoms_found=0,
                    confidence=confidence,
                    relevance_scores=[],
                    trace_id=trace_id,
                    context={"span_name": span_name}
                ))

            # Pattern 2: Thin Coverage (HIGH)
            if 0 < atoms_found < 3 and confidence < 0.5:
                priority = self.calculate_priority(
                    WeaknessType.THIN_COVERAGE,
                    {"atoms_found": atoms_found, "confidence": confidence}
                )
                weaknesses.append(WeaknessSignal(
                    weakness_type=WeaknessType.THIN_COVERAGE,
                    priority_score=priority,
                    query_text=query_text,
                    equipment_detected=equipment,
                    atoms_found=atoms_found,
                    confidence=confidence,
                    relevance_scores=relevance_scores,
                    trace_id=trace_id,
                    context={"span_name": span_name}
                ))

            # Pattern 3: Low Relevance (MEDIUM)
            if relevance_scores and max(relevance_scores) < 0.6:
                priority = self.calculate_priority(
                    WeaknessType.LOW_RELEVANCE,
                    {"top_score": max(relevance_scores)}
                )
                weaknesses.append(WeaknessSignal(
                    weakness_type=WeaknessType.LOW_RELEVANCE,
                    priority_score=priority,
                    query_text=query_text,
                    equipment_detected=equipment,
                    atoms_found=atoms_found,
                    confidence=confidence,
                    relevance_scores=relevance_scores,
                    trace_id=trace_id,
                    context={"span_name": span_name}
                ))

            # Pattern 4: Missing Citations (MEDIUM)
            citations = attributes.get("kb.citations", [])
            if atoms_found > 0 and not citations:
                weaknesses.append(WeaknessSignal(
                    weakness_type=WeaknessType.MISSING_CITATIONS,
                    priority_score=50,
                    query_text=query_text,
                    equipment_detected=equipment,
                    atoms_found=atoms_found,
                    confidence=confidence,
                    relevance_scores=relevance_scores,
                    trace_id=trace_id,
                    context={"span_name": span_name}
                ))

            # Pattern 5: Hallucination Risk (CRITICAL)
            if confidence > 0.7 and atoms_found == 0:
                weaknesses.append(WeaknessSignal(
                    weakness_type=WeaknessType.HALLUCINATION_RISK,
                    priority_score=95,
                    query_text=query_text,
                    equipment_detected=equipment,
                    atoms_found=0,
                    confidence=confidence,
                    relevance_scores=[],
                    trace_id=trace_id,
                    context={"span_name": span_name}
                ))

            # Pattern 6: High Latency (MEDIUM)
            if latency_ms > 2000:
                priority = min(50, int(30 + (latency_ms - 2000) / 100))
                weaknesses.append(WeaknessSignal(
                    weakness_type=WeaknessType.HIGH_LATENCY,
                    priority_score=priority,
                    query_text=query_text,
                    equipment_detected=equipment,
                    atoms_found=atoms_found,
                    confidence=confidence,
                    relevance_scores=relevance_scores,
                    trace_id=trace_id,
                    context={"span_name": span_name, "latency_ms": latency_ms}
                ))

        except Exception as e:
            logger.error(f"Failed to detect weaknesses from trace: {e}", exc_info=True)

        return weaknesses

    def calculate_priority(
        self,
        weakness_type: WeaknessType,
        context: Dict
    ) -> int:
        """
        Calculate priority score (0-100) for weakness.

        Scoring:
        - Zero atoms: 100 (always CRITICAL)
        - Thin coverage: 70-90 (depends on confidence)
        - Low relevance: 50-70 (depends on score)
        - Missing citations: 40-60
        - Hallucination: 95-100 (CRITICAL)
        - High latency: 30-50

        Args:
            weakness_type: Type of weakness
            context: Additional context for scoring

        Returns:
            Priority score (higher = more urgent)
        """
        if weakness_type == WeaknessType.ZERO_ATOMS:
            return 100

        elif weakness_type == WeaknessType.THIN_COVERAGE:
            confidence = context.get("confidence", 0.0)
            atoms_found = context.get("atoms_found", 0)
            # Lower confidence + fewer atoms = higher priority
            base_score = 70
            confidence_penalty = int((0.5 - confidence) * 40)  # 0-20
            atoms_penalty = (3 - atoms_found) * 3  # 0-9
            return min(90, base_score + confidence_penalty + atoms_penalty)

        elif weakness_type == WeaknessType.LOW_RELEVANCE:
            top_score = context.get("top_score", 0.0)
            # Lower relevance = higher priority
            base_score = 50
            relevance_penalty = int((0.6 - top_score) * 50)  # 0-30
            return min(70, base_score + relevance_penalty)

        elif weakness_type == WeaknessType.MISSING_CITATIONS:
            return 50

        elif weakness_type == WeaknessType.HALLUCINATION_RISK:
            confidence = context.get("confidence", 0.7)
            # Higher confidence with no atoms = higher priority
            return min(100, int(95 + (confidence - 0.7) * 10))

        elif weakness_type == WeaknessType.HIGH_LATENCY:
            latency_ms = context.get("latency_ms", 2000)
            # Higher latency = higher priority (up to 50)
            return min(50, int(30 + (latency_ms - 2000) / 100))

        return 50  # Default fallback

    def analyze_recent_traces(
        self,
        lookback_minutes: int = 5
    ) -> List[WeaknessSignal]:
        """
        Poll and analyze recent traces for weaknesses.

        Convenience method that combines polling and detection.

        Args:
            lookback_minutes: How far back to look

        Returns:
            List of all detected weakness signals
        """
        all_weaknesses = []

        traces = self.poll_recent_traces(lookback_minutes)

        for trace in traces:
            weaknesses = self.detect_weaknesses(trace)
            all_weaknesses.extend(weaknesses)

        logger.info(
            f"Analyzed {len(traces)} traces, "
            f"found {len(all_weaknesses)} weaknesses"
        )

        return all_weaknesses

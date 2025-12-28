#!/usr/bin/env python3
"""
Phoenix Trace Monitor - Standalone Version

Monitors Phoenix for KB weaknesses without heavy dependencies.
Logs detected weaknesses to console in monitoring mode.

Usage:
    python scripts/phoenix_monitor_standalone.py
"""

import os
import sys
import time
import requests
import json
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict

# Minimal dependencies - no agent_factory imports


class WeaknessType(str, Enum):
    """KB weakness types."""
    ZERO_ATOMS = "zero_atoms"
    THIN_COVERAGE = "thin_coverage"
    LOW_RELEVANCE = "low_relevance"
    MISSING_CITATIONS = "missing_citations"
    HALLUCINATION_RISK = "hallucination_risk"
    HIGH_LATENCY = "high_latency"


@dataclass
class WeaknessSignal:
    """KB weakness detected from trace."""
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


class PhoenixMonitor:
    """Lightweight Phoenix monitor."""

    def __init__(self, phoenix_url="http://localhost:6006"):
        self.phoenix_url = phoenix_url
        self.graphql_url = f"{phoenix_url}/graphql"
        self.last_analyzed_timestamp = None

    def poll_recent_traces(self, lookback_minutes=5):
        """Poll Phoenix for recent traces."""
        try:
            if self.last_analyzed_timestamp:
                start_time = self.last_analyzed_timestamp
            else:
                start_time = datetime.utcnow() - timedelta(minutes=lookback_minutes)

            query = """
                query GetRecentKBTraces($startTime: DateTime!) {
                    spans(
                        where: {
                            startTime: { gte: $startTime }
                            name: { in: ["knowledge_base.retrieval", "orchestrator.route_decision"] }
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
                                statusCode
                                startTime
                                latencyMs
                                attributes
                            }
                        }
                    }
                }
            """

            variables = {"startTime": start_time.isoformat() + "Z"}

            response = requests.post(
                self.graphql_url,
                json={"query": query, "variables": variables},
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code != 200:
                print(f"[ERROR] Phoenix GraphQL error: {response.status_code}")
                return []

            data = response.json()
            if not data or "data" not in data:
                return []

            edges = data.get("data", {}).get("spans", {}).get("edges", [])
            traces = [edge["span"] for edge in edges]

            if traces:
                latest = max(traces, key=lambda t: t.get("startTime", ""))
                self.last_analyzed_timestamp = datetime.fromisoformat(
                    latest["startTime"].replace("Z", "+00:00")
                )

            return traces

        except Exception as e:
            print(f"[ERROR] Failed to poll Phoenix: {e}")
            return []

    def detect_weaknesses(self, trace):
        """Detect KB weaknesses from trace."""
        weaknesses = []

        try:
            trace_id = trace.get("context", {}).get("traceId", "unknown")
            latency_ms = trace.get("latencyMs", 0)

            # Parse attributes
            attributes_str = trace.get("attributes", "{}")
            if isinstance(attributes_str, str):
                attributes = json.loads(attributes_str)
            else:
                attributes = attributes_str

            # Extract KB signals
            atoms_found = attributes.get("kb.atoms_found", 0)
            coverage = attributes.get("kb.coverage", 0.0)
            confidence = attributes.get("route.confidence", 0.0)
            query_text = attributes.get("query", "")
            equipment = attributes.get("equipment_detected", "unknown:unknown")

            # Pattern 1: Zero Atoms
            if atoms_found == 0 and coverage == 0.0:
                weaknesses.append(WeaknessSignal(
                    weakness_type=WeaknessType.ZERO_ATOMS,
                    priority_score=100,
                    query_text=query_text,
                    equipment_detected=equipment,
                    atoms_found=0,
                    confidence=confidence,
                    trace_id=trace_id
                ))

            # Pattern 2: Thin Coverage
            if 0 < atoms_found < 3 and confidence < 0.5:
                priority = min(90, 70 + int((0.5 - confidence) * 40))
                weaknesses.append(WeaknessSignal(
                    weakness_type=WeaknessType.THIN_COVERAGE,
                    priority_score=priority,
                    query_text=query_text,
                    equipment_detected=equipment,
                    atoms_found=atoms_found,
                    confidence=confidence,
                    trace_id=trace_id
                ))

            # Pattern 5: Hallucination Risk
            if confidence > 0.7 and atoms_found == 0:
                weaknesses.append(WeaknessSignal(
                    weakness_type=WeaknessType.HALLUCINATION_RISK,
                    priority_score=95,
                    query_text=query_text,
                    equipment_detected=equipment,
                    atoms_found=0,
                    confidence=confidence,
                    trace_id=trace_id
                ))

            # Pattern 6: High Latency
            if latency_ms > 2000:
                priority = min(50, int(30 + (latency_ms - 2000) / 100))
                weaknesses.append(WeaknessSignal(
                    weakness_type=WeaknessType.HIGH_LATENCY,
                    priority_score=priority,
                    query_text=query_text,
                    equipment_detected=equipment,
                    atoms_found=atoms_found,
                    confidence=confidence,
                    trace_id=trace_id,
                    context={"latency_ms": latency_ms}
                ))

        except Exception as e:
            print(f"[ERROR] Failed to detect weaknesses: {e}")

        return weaknesses


def main():
    print("=" * 70)
    print("PHOENIX TRACE MONITOR - Standalone Mode")
    print("=" * 70)
    print()
    print("Monitoring Phoenix for KB weaknesses...")
    print("MONITORING MODE: Logs only (no auto-research)")
    print("Press Ctrl+C to stop")
    print()

    phoenix_url = os.getenv("PHOENIX_URL", "http://localhost:6006")
    poll_interval = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))  # 5 minutes

    monitor = PhoenixMonitor(phoenix_url=phoenix_url)

    print(f"Phoenix URL: {phoenix_url}")
    print(f"Poll interval: {poll_interval} seconds")
    print()

    iteration = 0

    try:
        while True:
            iteration += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"\n[{timestamp}] Iteration {iteration}")
            print("-" * 70)

            traces = monitor.poll_recent_traces(lookback_minutes=5)
            print(f"Found {len(traces)} traces to analyze")

            total_weaknesses = 0
            weakness_summary = {}

            for trace in traces:
                weaknesses = monitor.detect_weaknesses(trace)

                for weakness in weaknesses:
                    total_weaknesses += 1

                    weakness_type = weakness.weakness_type.value
                    weakness_summary[weakness_type] = weakness_summary.get(weakness_type, 0) + 1

                    # Print weakness details
                    priority_label = (
                        "CRITICAL" if weakness.priority_score >= 90
                        else "HIGH" if weakness.priority_score >= 70
                        else "MEDIUM" if weakness.priority_score >= 40
                        else "LOW"
                    )

                    print(f"\n  [{priority_label}] {weakness_type} (priority={weakness.priority_score})")
                    print(f"    Equipment: {weakness.equipment_detected}")
                    print(f"    Query: {weakness.query_text[:80]}...")
                    print(f"    Atoms: {weakness.atoms_found}, Confidence: {weakness.confidence:.2f}")

                    if "latency_ms" in weakness.context:
                        print(f"    Latency: {weakness.context['latency_ms']}ms")

            if total_weaknesses > 0:
                print(f"\nSummary: {total_weaknesses} weaknesses detected")
                for wtype, count in weakness_summary.items():
                    print(f"  - {wtype}: {count}")
            else:
                print("\nNo weaknesses detected")

            print(f"\nNext poll in {poll_interval} seconds...")
            time.sleep(poll_interval)

    except KeyboardInterrupt:
        print("\n\nShutting down monitor...")
        print("=" * 70)


if __name__ == "__main__":
    main()

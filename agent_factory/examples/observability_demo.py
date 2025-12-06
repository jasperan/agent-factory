"""
Observability Demo - Production monitoring and metrics

Demonstrates Phase 3 observability features:
1. Request tracing (end-to-end visibility)
2. Performance metrics (latency, success rates)
3. Cost tracking (API usage costs)
"""
import os
import sys
import json
from pathlib import Path

# Add parent to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agent_factory.core import AgentFactory
from agent_factory.tools.research_tools import CurrentTimeTool


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print("=" * 60)


def print_metrics_summary(orchestrator):
    """Print comprehensive metrics summary."""
    print_section("METRICS SUMMARY")

    summary = orchestrator.metrics.summary()

    print(f"\nTotal Requests: {summary['total_requests']}")
    print(f"Success Rate: {summary['success_rate']}")
    print(f"Failure Rate: {summary['failure_rate']}")

    print(f"\nLatency:")
    print(f"  Average: {summary['latency']['avg_ms']}ms")
    print(f"  P50 (median): {summary['latency']['p50_ms']}ms")
    print(f"  P95: {summary['latency']['p95_ms']}ms")
    print(f"  P99: {summary['latency']['p99_ms']}ms")

    print(f"\nToken Usage:")
    print(f"  Total: {summary['tokens']['total']}")
    print(f"  Prompt: {summary['tokens']['prompt']}")
    print(f"  Completion: {summary['tokens']['completion']}")

    if summary['agents']:
        print(f"\nPer-Agent Stats:")
        for agent_name, stats in summary['agents'].items():
            print(f"  {agent_name}:")
            print(f"    Requests: {stats['requests']}")
            print(f"    Success rate: {stats['success_rate']:.1f}%")
            print(f"    Avg latency: {stats['avg_latency_ms']}ms")


def print_cost_summary(orchestrator):
    """Print cost tracking summary."""
    print_section("COST SUMMARY")

    summary = orchestrator.cost_tracker.summary()

    print(f"\nTotal Cost: {summary['total_cost_usd']}")
    print(f"Total Requests: {summary['total_requests']}")
    print(f"Avg Cost/Request: {summary['avg_cost_per_request']}")

    if summary['by_agent']:
        print(f"\nCost by Agent:")
        for agent, cost in summary['by_agent'].items():
            print(f"  {agent}: {cost}")

    if summary['by_provider']:
        print(f"\nCost by Provider:")
        for provider, cost in summary['by_provider'].items():
            print(f"  {provider}: {cost}")

    if summary['by_model']:
        print(f"\nCost by Model:")
        for model, cost in summary['by_model'].items():
            print(f"  {model}: {cost}")


def print_trace_details(orchestrator, trace_id: str):
    """Print detailed trace information."""
    trace = orchestrator.tracer.get_trace(trace_id)

    if not trace:
        print(f"Trace {trace_id} not found")
        return

    print(f"\nTrace ID: {trace.trace_id}")
    print(f"Query: {trace.query}")
    print(f"Agent: {trace.agent_name}")
    print(f"Method: {trace.method}")
    print(f"Duration: {trace.duration_ms:.2f}ms")
    print(f"Success: {trace.success}")
    if trace.error:
        print(f"Error: {trace.error}")

    if trace.spans:
        print(f"\nSpans ({len(trace.spans)}):")
        for span in trace.spans:
            print(f"  - {span.name}: {span.duration_ms:.2f}ms")


def main():
    print_section("OBSERVABILITY DEMO")

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n[WARNING] OPENAI_API_KEY not found")
        print("Observability features will still work, but agents won't execute")
        print("\nSet your API key: export OPENAI_API_KEY='your-key'")
        return

    # Create factory with observability ENABLED (default)
    factory = AgentFactory(verbose=False)

    # Create tool
    time_tool = CurrentTimeTool()

    # Create agents
    research_agent = factory.create_agent(
        role="Research Agent",
        tools_list=[time_tool],
        system_prompt="You are a research assistant.",
        enable_memory=False
    )

    creative_agent = factory.create_agent(
        role="Creative Writer",
        tools_list=[time_tool],
        system_prompt="You are a creative writer.",
        enable_memory=False
    )

    code_agent = factory.create_agent(
        role="Code Assistant",
        tools_list=[time_tool],
        system_prompt="You are a coding assistant.",
        enable_memory=False
    )

    # Create orchestrator with observability enabled
    orchestrator = factory.create_orchestrator(verbose=False, enable_observability=True)

    print("\nOrchestrator created with observability ENABLED")
    print("  - Tracer: Request tracing")
    print("  - Metrics: Performance tracking")
    print("  - CostTracker: API cost monitoring")

    # Register agents
    orchestrator.register("research", research_agent, keywords=["what", "who", "explain"])
    orchestrator.register("creative", creative_agent, keywords=["write", "story", "poem"])
    orchestrator.register("coding", code_agent, keywords=["code", "function", "debug"], is_fallback=True)

    print_section("EXECUTING QUERIES")

    # Test queries
    queries = [
        "What is the capital of France?",
        "Write a haiku about coding",
        "How do I sort a list in Python?",
        "Tell me something interesting"
    ]

    trace_ids = []

    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/4] Query: {query}")

        result = orchestrator.route(query)
        trace_ids.append(result.trace_id)

        print(f"  -> Agent: {result.agent_name}")
        print(f"  -> Method: {result.method}")
        print(f"  -> Duration: {result.duration_ms:.2f}ms")
        print(f"  -> Trace ID: {result.trace_id}")

        if result.error:
            print(f"  -> ERROR: {result.error}")
        else:
            # Extract output
            if hasattr(result.response, 'get'):
                output = result.response.get('output', str(result.response))
            else:
                output = str(result.response)

            # Show first 100 chars
            print(f"  -> Response: {output[:100]}...")

    # Show detailed metrics
    print_metrics_summary(orchestrator)

    # Show cost tracking
    print_cost_summary(orchestrator)

    # Show trace details for first query
    print_section(f"TRACE DETAILS (First Query)")
    if trace_ids:
        print_trace_details(orchestrator, trace_ids[0])

    # Export traces
    print_section("EXPORT TRACES")

    all_traces = orchestrator.tracer.export_traces()
    print(f"\nTotal traces: {len(all_traces)}")
    print(f"Exportable to JSON for analysis")

    # Example: Save to file
    # with open("traces.json", "w") as f:
    #     json.dump(all_traces, f, indent=2)

    # Show top agents by cost
    print_section("TOP AGENTS BY COST")

    top_agents = orchestrator.cost_tracker.get_top_agents_by_cost(3)
    for i, (agent, cost) in enumerate(top_agents, 1):
        print(f"{i}. {agent}: ${cost:.4f}")

    # Monthly estimate
    monthly_cost = orchestrator.cost_tracker.estimate_monthly_cost(days_of_data=1)
    print(f"\nEstimated Monthly Cost: ${monthly_cost:.2f}")
    print("  (Based on today's usage)")

    print_section("OBSERVABILITY FEATURES")

    print("\nEnabled Features:")
    print("  [X] Request Tracing - Every request has unique trace_id")
    print("  [X] Performance Metrics - Latency percentiles (p50, p95, p99)")
    print("  [X] Token Tracking - Prompt + completion tokens")
    print("  [X] Cost Calculation - Real-time cost tracking")
    print("  [X] Error Categorization - Track error types")
    print("  [X] Per-Agent Stats - Breakdown by agent")

    print("\nAccess Observability Data:")
    print("  orchestrator.tracer.get_trace(trace_id)")
    print("  orchestrator.metrics.summary()")
    print("  orchestrator.cost_tracker.summary()")

    print("\nDisable Observability:")
    print("  orchestrator = factory.create_orchestrator(enable_observability=False)")

    print_section("DEMO COMPLETE")


if __name__ == "__main__":
    main()

"""
========================================================================
<AGENT NAME> - v1.0
========================================================================

STATUS: DRAFT
CREATED: YYYY-MM-DD
LAST UPDATED: YYYY-MM-DD
OWNER: <Your Name>

PURPOSE:
    This agent automates research tasks for developers who need to quickly find accurate technical information across multiple sources without manual searching.

---

SCOPE:
    In Scope:
        - Search web sources (Google, Stack Overflow, documentation sites)
        - Synthesize information from multiple sources
        - Provide citations for all claims
        - Ask clarifying questions when query is ambiguous
        - Admit when information is not found or uncertain

    Out of Scope:
        - Make up information when sources are unavailable
        - Access private/internal company data
        - Perform actions that modify external systems
        - Provide medical, legal, or financial advice
        - Execute code or commands


INVARIANTS:
    1. Accuracy First:: Never fabricate sources or citations
    2. User Safety:: Refuse requests that could cause harm
    3. Data Privacy:: Never log or store sensitive user data
    4. Cost Limit:: Each query must cost < $0.10 in API usage
    5. Latency:: Response time must be < 30 seconds for 95% of queries


WARNING:
    This file is AUTO-GENERATED from specs/<agent-name>-v1.0.md
    Do not edit manually - changes will be overwritten.
    To modify behavior, update the spec and regenerate.

========================================================================
"""

from agent_factory.core.agent_factory import AgentFactory
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# Tool imports
# from agent_factory.tools import WebSearchTool  # TODO: Verify tool exists
# from agent_factory.tools import DocumentRetrieverTool  # TODO: Verify tool exists
# from agent_factory.tools import CitationFormatterTool  # TODO: Verify tool exists

# ====================================================================
# DATA MODELS - Pydantic Schemas
# ====================================================================

from pydantic import BaseModel, Field
from typing import List, Optional

class ResearchQuery(BaseModel):
    """Input to research agent"""
    query: str = Field(..., description="User's question")
    max_sources: int = Field(5, description="Maximum sources to cite")
    depth: str = Field("medium", description="Search depth: quick, medium, deep")

class Citation(BaseModel):
    """A single source citation"""
    source_name: str
    url: str
    relevant_quote: Optional[str] = None

class ResearchResponse(BaseModel):
    """Output from research agent"""
    answer: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    citations: List[Citation]
    follow_up_questions: Optional[List[str]] = None
    cost_usd: float
    latency_seconds: float

def create_agent(llm_provider: str = "openai", model_name: str = "gpt-4"):
    """
    PURPOSE: Create and configure the <Agent Name> agent

    WHAT THIS DOES:
        1. Initialize AgentFactory with specified LLM
        2. Load required tools
        3. Create agent with system prompt and tools
        4. Return configured agent

    INPUTS:
        llm_provider (str): LLM provider (openai, anthropic, google)
        model_name (str): Model name (gpt-4, claude-3-sonnet, etc.)

    OUTPUTS:
        Configured agent ready to invoke

    INVARIANTS:
        1. Accuracy First:: Never fabricate sources or citations
        2. User Safety:: Refuse requests that could cause harm
        3. Data Privacy:: Never log or store sensitive user data
        4. Cost Limit:: Each query must cost < $0.10 in API usage
        5. Latency:: Response time must be < 30 seconds for 95% of queries

    """
    # Initialize factory
    factory = AgentFactory(llm_provider=llm_provider, model_name=model_name)

    # Load tools
    tools = []
    # TODO: Add tool loading based on spec.essential_tools
    # WebSearchTool: For finding current information
    # DocumentRetrieverTool: For searching documentation sites
    # CitationFormatterTool: For generating proper citations


    # System prompt from spec
    system_prompt = """This agent automates research tasks for developers who need to quickly find accurate technical information across multiple sources without manual searching.

---\n\nRULES (Must never be violated):\n1. Accuracy First:: Never fabricate sources or citations\n2. User Safety:: Refuse requests that could cause harm\n3. Data Privacy:: Never log or store sensitive user data\n4. Cost Limit:: Each query must cost < $0.10 in API usage\n5. Latency:: Response time must be < 30 seconds for 95% of queries"""

    # Create agent
    agent = factory.create_agent(
        role="<Agent Name>",
        tools_list=tools,
        system_prompt=system_prompt,
        response_schema=ResearchQuery,
        metadata={
            "spec_version": "v1.0",
            "spec_file": "<agent-name>-v1.0.md",
            "status": "DRAFT",
        }
    )

    return agent

def main():
    """
    PURPOSE: Demo function showing agent usage

    WHAT THIS DOES:
        1. Create agent
        2. Run example query
        3. Display response
    """
    print("Creating <Agent Name>...")
    agent = create_agent()

    print("\nRunning example query...")
    query = "What is the time complexity of Python"
    result = agent.invoke({"input": query})

    print(f"\nQuery: {query}")
    print(f"Response: {result.get('output', result)}")


if __name__ == "__main__":
    main()
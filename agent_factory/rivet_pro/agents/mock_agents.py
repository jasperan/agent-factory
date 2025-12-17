"""Mock SME Agents for Task 4 testing.

TODO: Replace with real SME agents when Phase 3 (task-3.1 through task-3.4) is complete.

These mocks provide the same interface as real agents but return placeholder responses.
"""

from typing import Optional
from agent_factory.rivet_pro.models import RivetRequest, RivetResponse, EquipmentType, AgentID, RouteType


class MockSMEAgent:
    """Base mock SME agent."""

    def __init__(self, agent_name: str, agent_id: AgentID):
        self.agent_name = agent_name
        self.agent_id = agent_id

    async def handle_query(self, request: RivetRequest) -> RivetResponse:
        """Generate mock response for testing.

        Args:
            request: User query request

        Returns:
            Mock RivetResponse
        """
        query_text = request.text or ""
        return RivetResponse(
            text=f"[MOCK {self.agent_name}] This is a placeholder response for: {query_text}",
            agent_id=self.agent_id,
            route_taken=RouteType.ROUTE_A,  # Assume strong KB route
            links=[f"mock_kb_atom_{self.agent_id.value}_001"],
            confidence=0.85,
            cited_documents=[{"title": f"Mock {self.agent_name} Document", "url": "https://example.com/mock"}],
            trace={"mock": True, "agent": self.agent_name}
        )


class MockSiemensAgent(MockSMEAgent):
    """Mock Siemens SME agent.

    TODO: Replace with agent_factory/rivet_pro/agents/siemens_agent.py when implemented (task-3.1)
    """

    def __init__(self):
        super().__init__(agent_name="Siemens Agent", agent_id=AgentID.SIEMENS)


class MockRockwellAgent(MockSMEAgent):
    """Mock Rockwell SME agent.

    TODO: Replace with agent_factory/rivet_pro/agents/rockwell_agent.py when implemented (task-3.2)
    """

    def __init__(self):
        super().__init__(agent_name="Rockwell Agent", agent_id=AgentID.ROCKWELL)


class MockGenericAgent(MockSMEAgent):
    """Mock Generic PLC SME agent.

    TODO: Replace with agent_factory/rivet_pro/agents/generic_agent.py when implemented (task-3.3)
    """

    def __init__(self):
        super().__init__(agent_name="Generic PLC Agent", agent_id=AgentID.GENERIC_PLC)


class MockSafetyAgent(MockSMEAgent):
    """Mock Safety SME agent.

    TODO: Replace with agent_factory/rivet_pro/agents/safety_agent.py when implemented (task-3.4)
    """

    def __init__(self):
        super().__init__(agent_name="Safety Agent", agent_id=AgentID.SAFETY)

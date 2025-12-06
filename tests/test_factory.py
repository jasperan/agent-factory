"""
Tests for agent_factory.core.agent_factory module

Tests the AgentFactory class - the main entry point for creating agents,
orchestrators, and configuring the system.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest

from agent_factory.core.agent_factory import AgentFactory
from agent_factory.core.orchestrator import AgentOrchestrator
from agent_factory.schemas import ResearchResponse, CodeResponse
from agent_factory.tools.research_tools import CurrentTimeTool

from langchain_core.tools import BaseTool


class DummyTool(BaseTool):
    """Simple tool for testing."""
    name: str = "dummy_tool"
    description: str = "A dummy tool for testing"

    def _run(self, query: str) -> str:
        return f"Dummy response to: {query}"


class TestFactoryInitialization:
    """Test AgentFactory initialization and configuration."""

    def test_factory_creation_default(self):
        """REQ-FACTORY-001: Factory creates with default settings."""
        factory = AgentFactory()

        assert factory is not None
        assert factory.default_llm_provider == "openai"
        assert factory.default_model == "gpt-4o"
        assert factory.default_temperature == 0.0

    def test_factory_creation_with_api_key(self):
        """REQ-FACTORY-001: Factory creates with custom API key."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"}):
            factory = AgentFactory()
            assert factory is not None

    def test_factory_verbose_mode(self):
        """REQ-FACTORY-001: Factory supports verbose mode."""
        factory = AgentFactory(verbose=True)
        assert factory is not None
        assert factory.verbose is True


class TestAgentCreation:
    """Test agent creation methods."""

    def test_create_agent_minimal(self):
        """REQ-FACTORY-002: Create agent with minimal parameters."""
        factory = AgentFactory()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = factory.create_agent(
                role="Test Agent",
                tools_list=[DummyTool()],
                system_prompt="You are a test agent"
            )

        assert agent is not None
        assert hasattr(agent, 'invoke')
        assert hasattr(agent, 'metadata')

    def test_create_agent_with_memory(self):
        """REQ-FACTORY-002: Create agent with memory enabled."""
        factory = AgentFactory()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = factory.create_agent(
                role="Memory Agent",
                tools_list=[DummyTool()],
                system_prompt="Test",
                enable_memory=True
            )

        assert agent is not None
        # Memory should be in agent setup

    def test_create_agent_with_response_schema(self):
        """REQ-FACTORY-002: Create agent with Pydantic response schema."""
        factory = AgentFactory()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = factory.create_agent(
                role="Research Agent",
                tools_list=[DummyTool()],
                system_prompt="Test",
                response_schema=ResearchResponse
            )

        assert agent is not None
        assert agent.metadata.get('response_schema') == ResearchResponse

    def test_create_research_agent(self):
        """REQ-FACTORY-003: Create research agent using helper."""
        factory = AgentFactory()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = factory.create_research_agent(tools_list=[DummyTool()])

        assert agent is not None
        assert "research" in agent.metadata.get('role', '').lower()

    def test_create_coding_agent(self):
        """REQ-FACTORY-003: Create coding agent using helper."""
        factory = AgentFactory()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = factory.create_coding_agent(tools_list=[DummyTool()])

        assert agent is not None
        assert "cod" in agent.metadata.get('role', '').lower()


class TestLLMConfiguration:
    """Test LLM provider and model configuration."""

    def test_custom_llm_provider_openai(self):
        """REQ-FACTORY-004: Create agent with OpenAI provider."""
        factory = AgentFactory(default_llm_provider="openai", default_model="gpt-4o")

        assert factory.default_llm_provider == "openai"
        assert factory.default_model == "gpt-4o"

    def test_custom_llm_provider_anthropic(self):
        """REQ-FACTORY-004: Create agent with Anthropic provider."""
        factory = AgentFactory(default_llm_provider="anthropic", default_model="claude-sonnet-4")

        assert factory.default_llm_provider == "anthropic"
        assert factory.default_model == "claude-sonnet-4"

    def test_custom_llm_provider_google(self):
        """REQ-FACTORY-004: Create agent with Google provider."""
        factory = AgentFactory(default_llm_provider="google", default_model="gemini-2.0-flash")

        assert factory.default_llm_provider == "google"
        assert factory.default_model == "gemini-2.0-flash"

    def test_invalid_llm_provider(self):
        """REQ-FACTORY-004: Handle invalid provider gracefully."""
        factory = AgentFactory(default_llm_provider="invalid_provider")

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with pytest.raises(ValueError, match="Unsupported LLM provider"):
                factory.create_agent(
                    role="Test",
                    tools_list=[DummyTool()],
                    system_prompt="Test"
                )

    def test_temperature_configuration(self):
        """REQ-FACTORY-004: Configure LLM temperature."""
        factory = AgentFactory(default_temperature=0.9)

        assert factory.default_temperature == 0.9


class TestOrchestratorCreation:
    """Test orchestrator creation."""

    def test_create_orchestrator_default(self):
        """REQ-FACTORY-005: Create orchestrator with default settings."""
        factory = AgentFactory()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            orchestrator = factory.create_orchestrator()

        assert isinstance(orchestrator, AgentOrchestrator)
        assert orchestrator.tracer is not None  # Observability enabled by default
        assert orchestrator.metrics is not None
        assert orchestrator.cost_tracker is not None

    def test_create_orchestrator_without_observability(self):
        """REQ-FACTORY-005: Create orchestrator with observability disabled."""
        factory = AgentFactory()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            orchestrator = AgentOrchestrator(enable_observability=False)

        assert isinstance(orchestrator, AgentOrchestrator)
        assert orchestrator.tracer is None
        assert orchestrator.metrics is None
        assert orchestrator.cost_tracker is None

    def test_create_orchestrator_verbose(self):
        """REQ-FACTORY-005: Create orchestrator in verbose mode."""
        factory = AgentFactory(verbose=True)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            orchestrator = factory.create_orchestrator(verbose=True)

        assert isinstance(orchestrator, AgentOrchestrator)


class TestIntegration:
    """Integration tests - end-to-end workflows."""

    def test_full_agent_creation_workflow(self):
        """REQ-FACTORY-006: Complete workflow from factory to agent."""
        factory = AgentFactory()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            # Create agent
            agent = factory.create_agent(
                role="Integration Test Agent",
                tools_list=[DummyTool()],
                system_prompt="Test agent",
                response_schema=CodeResponse
            )

            # Verify agent is properly configured
            assert agent is not None
            assert agent.metadata.get('response_schema') == CodeResponse
            assert agent.metadata.get('role') == "Integration Test Agent"

    def test_orchestrator_with_multiple_agents(self):
        """REQ-FACTORY-006: Create orchestrator and register multiple agents."""
        factory = AgentFactory()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            # Create agents
            research_agent = factory.create_research_agent(tools_list=[DummyTool()])
            coding_agent = factory.create_coding_agent(tools_list=[DummyTool()])

            # Create orchestrator
            orchestrator = factory.create_orchestrator()

            # Register agents
            orchestrator.register("research", research_agent, keywords=["what", "explain"])
            orchestrator.register("coding", coding_agent, keywords=["code", "function"])

            # Verify registration
            assert len(orchestrator.list_agents()) == 2
            assert "research" in orchestrator.list_agents()
            assert "coding" in orchestrator.list_agents()


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_create_agent_without_api_key(self):
        """REQ-FACTORY-007: Handle missing API key gracefully."""
        factory = AgentFactory()

        # Clear all API keys
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception):
                factory.create_agent(
                    role="Test",
                    tools_list=[DummyTool()],
                    system_prompt="Test"
                )

    def test_create_agent_empty_tools(self):
        """REQ-FACTORY-007: Handle empty tools list."""
        factory = AgentFactory()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with pytest.raises(ValueError, match="tools_list cannot be empty"):
                factory.create_agent(
                    role="No Tools Agent",
                    tools_list=[],
                    system_prompt="Test"
                )

    def test_invalid_agent_type(self):
        """REQ-FACTORY-007: Handle invalid agent type."""
        factory = AgentFactory()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with pytest.raises(ValueError, match="Unsupported agent type"):
                factory.create_agent(
                    role="Test",
                    tools_list=[DummyTool()],
                    system_prompt="Test",
                    agent_type="invalid_type"
                )


class TestMetadata:
    """Test agent metadata storage and retrieval."""

    def test_agent_metadata_storage(self):
        """REQ-FACTORY-008: Agent stores metadata correctly."""
        factory = AgentFactory()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = factory.create_agent(
                role="Metadata Test",
                tools_list=[DummyTool()],
                system_prompt="Test",
                response_schema=ResearchResponse
            )

            assert agent.metadata.get('role') == "Metadata Test"
            assert agent.metadata.get('response_schema') == ResearchResponse
            assert 'llm_provider' in agent.metadata
            assert 'model' in agent.metadata

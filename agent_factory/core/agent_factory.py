"""
AgentFactory: Dynamic LangChain Agent Creation System

This module provides a flexible factory pattern for creating specialized AI agents
with custom capabilities, tools, and configurations.

Based on patterns from: https://github.com/Mikecranesync/langchain-crash-course
"""

from typing import List, Dict, Optional, Any, Union, Type
import langchainhub as hub
from agent_factory.compat.langchain_shim import AgentExecutor, create_react_agent, create_structured_chat_agent
# ConversationBufferMemory moved to langchain_community in 1.2.0
try:
    from langchain.memory import ConversationBufferMemory
except ImportError:
    from langchain_community.chat_message_histories import ChatMessageHistory
    # Create a simple memory replacement
    class ConversationBufferMemory:
        """Minimal ConversationBufferMemory replacement for compatibility."""
        def __init__(self, memory_key="chat_history", return_messages=True, **kwargs):
            self.memory_key = memory_key
            self.return_messages = return_messages
            self.chat_memory = ChatMessageHistory()

        def load_memory_variables(self, inputs):
            return {self.memory_key: self.chat_memory.messages}

        def save_context(self, inputs, outputs):
            self.chat_memory.add_user_message(str(inputs))
            self.chat_memory.add_ai_message(str(outputs))
from langchain_core.tools import BaseTool
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from .orchestrator import RivetOrchestrator
from .callbacks import EventBus, create_default_event_bus
from ..workers.openhands_worker import OpenHandsWorker, create_openhands_worker

# Phase 2: Intelligent routing imports
try:
    from ..llm.langchain_adapter import RoutedChatModel, create_routed_chat_model
    from ..llm.types import ModelCapability
    from ..llm.tracker import UsageTracker
    ROUTING_AVAILABLE = True
except ImportError:
    ROUTING_AVAILABLE = False
    ModelCapability = None  # type: ignore
    UsageTracker = None  # type: ignore


class AgentFactory:
    """
    Factory for creating LangChain agents with custom configurations.

    Supports:
    - Multiple LLM providers (OpenAI, Anthropic, Google)
    - Dynamic tool assignment
    - Memory configuration
    - ReAct and Structured Chat agent types
    """

    # Supported agent types
    AGENT_TYPE_REACT = "react"
    AGENT_TYPE_STRUCTURED_CHAT = "structured_chat"

    # Supported LLM providers
    LLM_OPENAI = "openai"
    LLM_ANTHROPIC = "anthropic"
    LLM_GOOGLE = "google"

    def __init__(
        self,
        default_llm_provider: str = LLM_OPENAI,
        default_model: str = "gpt-4o",
        default_temperature: float = 0.0,
        verbose: bool = True,
        enable_routing: bool = True,
        exclude_local: bool = False
    ):
        """
        Initialize the AgentFactory.

        Args:
            default_llm_provider: Default LLM provider ("openai", "anthropic", "google")
            default_model: Default model name
            default_temperature: Default temperature for LLM
            verbose: Whether to show agent reasoning steps
            enable_routing: Enable Phase 2 intelligent routing (cost-optimized model selection)
            exclude_local: Exclude local Ollama models from routing (requires cloud APIs)
        """
        self.default_llm_provider = default_llm_provider
        self.default_model = default_model
        self.default_temperature = default_temperature
        self.verbose = verbose
        self.enable_routing = enable_routing
        self.exclude_local = exclude_local

        # Phase 2: Initialize routing components
        if enable_routing:
            if not ROUTING_AVAILABLE:
                raise ImportError(
                    "Routing not available. Phase 1 LLM module may not be installed correctly."
                )
            self.usage_tracker = UsageTracker()
        else:
            self.usage_tracker = None

    def _create_llm(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        capability: Optional[Any] = None,  # ModelCapability (Any for type compatibility)
        **kwargs
    ):
        """
        Create LLM instance based on provider.

        Phase 2: If routing enabled, returns RoutedChatModel for cost optimization.
        Otherwise returns direct provider LLM (backward compatible).
        """
        provider = provider or self.default_llm_provider
        model = model or self.default_model
        temperature = temperature if temperature is not None else self.default_temperature

        # Phase 2: Use routed chat model if enabled
        if self.enable_routing and ROUTING_AVAILABLE:
            return create_routed_chat_model(
                capability=capability or ModelCapability.MODERATE,
                exclude_local=self.exclude_local,
                track_costs=True,
                explicit_model=model if model != self.default_model else None,
                temperature=temperature,
                **kwargs
            )

        # Legacy path: Direct provider LLM (backward compatible)
        if provider == self.LLM_OPENAI:
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                **kwargs
            )
        elif provider == self.LLM_ANTHROPIC:
            return ChatAnthropic(
                model=model,
                temperature=temperature,
                **kwargs
            )
        elif provider == self.LLM_GOOGLE:
            return ChatGoogleGenerativeAI(
                model=model,
                temperature=temperature,
                **kwargs
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    def _infer_capability(
        self,
        role: str,
        tools_list: List[Union[BaseTool, Any]],
        agent_type: str
    ) -> Any:  # Returns ModelCapability
        """
        Infer appropriate capability level from agent role and tools.

        Uses heuristics to determine task complexity:
        - Role keywords (research, coding, simple, complex)
        - Tool count (more tools = more complex)
        - Agent type (structured_chat for conversations, react for coding)

        Args:
            role: Agent role string
            tools_list: List of tools
            agent_type: Agent type (react/structured_chat)

        Returns:
            ModelCapability enum value

        Examples:
            "Research Agent" + 8 tools → RESEARCH
            "Coding Agent" + 10 tools → CODING
            "Simple Task" + 2 tools → SIMPLE
            "Complex Analysis" + 12 tools → COMPLEX
        """
        if not ROUTING_AVAILABLE:
            return None

        role_lower = role.lower()

        # Explicit role-based detection (highest priority)
        if any(kw in role_lower for kw in ['research', 'researcher', 'search', 'investigate']):
            return ModelCapability.RESEARCH

        if any(kw in role_lower for kw in ['cod', 'developer', 'programmer', 'engineer']):
            return ModelCapability.CODING

        if any(kw in role_lower for kw in ['simple', 'basic', 'quick', 'easy', 'trivial']):
            return ModelCapability.SIMPLE

        if any(kw in role_lower for kw in ['complex', 'advanced', 'sophisticated', 'expert']):
            return ModelCapability.COMPLEX

        # Tool count-based inference (fallback)
        tool_count = len(tools_list) if tools_list else 0

        if tool_count >= 8:
            # Many tools suggest complex multi-step tasks
            return ModelCapability.COMPLEX
        elif tool_count >= 4:
            # Moderate tool count for moderate complexity
            return ModelCapability.MODERATE
        elif tool_count >= 1:
            # Few tools for simple tasks
            return ModelCapability.SIMPLE
        else:
            # No tools? Default to moderate
            return ModelCapability.MODERATE

    def create_agent(
        self,
        role: str,
        tools_list: List[Union[BaseTool, Any]],
        system_prompt: Optional[str] = None,
        agent_type: str = AGENT_TYPE_REACT,
        enable_memory: bool = True,
        llm_provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        memory_key: str = "chat_history",
        handle_parsing_errors: bool = True,
        response_schema: Optional[Type[BaseModel]] = None,
        capability: Optional[Any] = None,  # ModelCapability for routing
        **kwargs
    ) -> AgentExecutor:
        """
        Create a fully configured agent executor.

        Args:
            role: Agent role/description (e.g., "Research Agent", "Coding Agent")
            tools_list: List of tools the agent can use
            system_prompt: Optional system prompt to guide agent behavior
            agent_type: Type of agent ("react" or "structured_chat")
            enable_memory: Whether to enable conversation memory
            llm_provider: LLM provider override
            model: Model name override
            temperature: Temperature override
            memory_key: Key for storing chat history in memory
            handle_parsing_errors: Whether to gracefully handle LLM parsing errors
            response_schema: Optional Pydantic model for structured outputs
            capability: ModelCapability for routing (auto-inferred if not specified)
            **kwargs: Additional arguments passed to AgentExecutor

        Returns:
            AgentExecutor: Configured and ready-to-use agent executor

        Example:
            >>> from agent_factory.schemas import ResearchResponse
            >>> factory = AgentFactory()
            >>> agent = factory.create_agent(
            ...     role="Research Agent",
            ...     tools_list=[search_tool, wikipedia_tool],
            ...     system_prompt="You are a helpful research assistant.",
            ...     response_schema=ResearchResponse
            ... )
            >>> response = agent.invoke({"input": "What is LangChain?"})
        """
        # Phase 2: Infer capability if routing enabled and not specified
        if self.enable_routing and capability is None and ROUTING_AVAILABLE:
            capability = self._infer_capability(role, tools_list, agent_type)

        # Create LLM (with routing if enabled)
        llm = self._create_llm(
            provider=llm_provider,
            model=model,
            temperature=temperature,
            capability=capability
        )

        # Bind structured output schema if provided
        # Note: Structured output is applied at executor level, not LLM level
        # We store the schema in metadata for use in response parsing
        structured_output_llm = llm
        if response_schema:
            try:
                # Try to bind structured output (works with OpenAI, Anthropic)
                structured_output_llm = llm.with_structured_output(response_schema)
            except (AttributeError, NotImplementedError):
                # Fallback: schema will be used for validation only
                pass

        # Validate tools
        if not tools_list:
            raise ValueError("tools_list cannot be empty")

        # Load appropriate prompt template
        if agent_type == self.AGENT_TYPE_REACT:
            prompt = hub.pull("hwchase17/react")
        elif agent_type == self.AGENT_TYPE_STRUCTURED_CHAT:
            prompt = hub.pull("hwchase17/structured-chat-agent")
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")

        # Create agent
        # Use regular llm for agents (structured output is post-processed)
        # LangChain agents need standard LLM interface
        if agent_type == self.AGENT_TYPE_REACT:
            agent = create_react_agent(
                llm=llm,
                tools=tools_list,
                prompt=prompt
            )
        else:  # structured_chat
            agent = create_structured_chat_agent(
                llm=llm,
                tools=tools_list,
                prompt=prompt
            )

        # Configure memory
        memory = None
        if enable_memory:
            memory = ConversationBufferMemory(
                memory_key=memory_key,
                return_messages=True
            )

            # Add system message if provided
            if system_prompt:
                initial_message = f"{system_prompt}\n\nRole: {role}"
                memory.chat_memory.add_message(SystemMessage(content=initial_message))

        # Create agent executor
        executor_kwargs = {
            "agent": agent,
            "tools": tools_list,
            "verbose": self.verbose,
            "handle_parsing_errors": handle_parsing_errors,
            **kwargs
        }

        if memory:
            executor_kwargs["memory"] = memory

        agent_executor = AgentExecutor.from_agent_and_tools(**executor_kwargs)

        # Store metadata for reference
        agent_executor.metadata = {
            "role": role,
            "agent_type": agent_type,
            "llm_provider": llm_provider or self.default_llm_provider,
            "model": model or self.default_model,
            "tools_count": len(tools_list),
            "memory_enabled": enable_memory,
            "response_schema": response_schema
        }

        return agent_executor

    def create_research_agent(
        self,
        tools_list: List[Union[BaseTool, Any]],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AgentExecutor:
        """
        Create a pre-configured research agent.

        Args:
            tools_list: List of research tools (search, wikipedia, etc.)
            system_prompt: Optional custom system prompt
            **kwargs: Additional arguments passed to create_agent

        Returns:
            AgentExecutor: Research agent executor
        """
        default_prompt = (
            "You are an AI research assistant that provides accurate, well-researched answers. "
            "Use the available tools to search for information, verify facts, and provide "
            "comprehensive responses with citations when possible."
        )

        return self.create_agent(
            role="Research Agent",
            tools_list=tools_list,
            system_prompt=system_prompt or default_prompt,
            agent_type=self.AGENT_TYPE_STRUCTURED_CHAT,
            **kwargs
        )

    def create_coding_agent(
        self,
        tools_list: List[Union[BaseTool, Any]],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AgentExecutor:
        """
        Create a pre-configured coding agent.

        Args:
            tools_list: List of coding tools (file operations, git, etc.)
            system_prompt: Optional custom system prompt
            **kwargs: Additional arguments passed to create_agent

        Returns:
            AgentExecutor: Coding agent executor
        """
        default_prompt = (
            "You are an AI coding assistant that helps with software development tasks. "
            "You can read and write files, analyze code, and perform version control operations. "
            "Always write clean, well-documented code following best practices."
        )

        return self.create_agent(
            role="Coding Agent",
            tools_list=tools_list,
            system_prompt=system_prompt or default_prompt,
            agent_type=self.AGENT_TYPE_REACT,
            **kwargs
        )

    def create_orchestrator(
        self,
        event_bus: Optional[EventBus] = None,
        verbose: Optional[bool] = None
    ) -> RivetOrchestrator:
        """
        Create an orchestrator for multi-agent routing.

        Args:
            event_bus: Optional shared event bus
            verbose: Override factory verbose setting

        Returns:
            AgentOrchestrator configured with factory's LLM
        """
        llm = self._create_llm()

        return AgentOrchestrator(
            llm=llm,
            event_bus=event_bus,
            verbose=verbose if verbose is not None else self.verbose
        )

    def create_openhands_agent(
        self,
        model: Optional[str] = None,
        port: int = 3000
    ) -> OpenHandsWorker:
        """
        Create an OpenHands autonomous coding agent worker.

        PURPOSE (PLC-Style Explanation):
            Creates a worker that can autonomously write code, fix bugs, run tests.
            Like hiring a robot programmer - you give it tasks, it codes for you.

        WHAT THIS DOES:
            1. Creates OpenHandsWorker instance configured with your preferred LLM
            2. Worker manages its own Docker container lifecycle
            3. Returns ready-to-use worker you can send coding tasks to

        WHY USE THIS:
            - Avoid $200/month Claude Code fee (deadline Dec 15th!)
            - Get production-grade AI coder (50%+ SWE-Bench accuracy)
            - Sandboxed execution (safe, won't mess up your system)
            - Works with Claude, GPT, Gemini, Llama (model-agnostic)

        PARAMETERS:
            model: Which LLM to use for coding (default: uses factory's default)
                Examples:
                    "claude-3-5-sonnet-20241022" (default, recommended)
                    "gpt-4"
                    "gemini-2.0-flash"
            port: Port for OpenHands API (default: 3000)
                Change if 3000 is already in use

        RETURNS:
            OpenHandsWorker instance ready to run coding tasks

        HOW TO USE:
            # Create the worker
            worker = factory.create_openhands_agent()

            # Run a coding task
            result = worker.run_task("Add a function to calculate factorial")

            # Check results
            if result.success:
                print(f"Code generated: {result.code}")
                print(f"Files changed: {result.files_changed}")
            else:
                print(f"Task failed: {result.message}")

        COST SAVINGS:
            - Claude Code CLI: $200/month subscription
            - OpenHands: Free (open source) + only pay for LLM API usage
            - Typical task: $0.10 - $0.50 in API costs
            - Break-even: 400-2000 tasks per month

        TROUBLESHOOTING:
            - "Docker not found" → Install Docker Desktop
            - "Port 3000 in use" → Change port parameter
            - Tasks failing → Try different model or clarify task description
            - Slow performance → Simplify task or increase timeout

        EDGE CASES:
            - If model=None, uses factory's default model (usually Claude)
            - If Docker not installed, worker creation fails with helpful error
            - Container auto-cleans up after each task (ephemeral)

        Args:
            model: LLM model name (optional, uses factory default if not specified)
            port: HTTP port for OpenHands API (default 3000)

        Returns:
            OpenHandsWorker: Configured worker ready to execute coding tasks

        Raises:
            RuntimeError: If Docker is not installed or not running
        """
        # Use factory's default model if not specified
        # Map factory providers to OpenHands-compatible model names
        if model is None:
            # Use the factory's configured model
            provider = self.default_llm_provider
            factory_model = self.default_model

            # Map to OpenHands-compatible names
            if provider == self.LLM_ANTHROPIC:
                # Already in correct format (e.g., "claude-3-5-sonnet-20241022")
                model = factory_model
            elif provider == self.LLM_OPENAI:
                # Already in correct format (e.g., "gpt-4o")
                model = factory_model
            elif provider == self.LLM_GOOGLE:
                # Map to Gemini format (e.g., "gemini-2.0-flash")
                model = factory_model
            else:
                # Fallback to latest Claude if unknown provider
                model = "claude-3-5-sonnet-20241022"

        # Create and return worker
        return OpenHandsWorker(
            model=model,
            port=port
        )

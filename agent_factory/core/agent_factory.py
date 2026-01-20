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
try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

from pydantic import BaseModel

from ..workers.openhands_worker import OpenHandsWorker, create_openhands_worker, ToolOption, DEFAULT_TOOLS


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
    LLM_OLLAMA = "ollama"

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
            if not OPENAI_AVAILABLE:
                raise ImportError("langchain-openai package not installed. Run 'pip install langchain-openai'")
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                **kwargs
            )
        elif provider == self.LLM_ANTHROPIC:
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("langchain-anthropic package not installed. Run 'pip install langchain-anthropic'")
            return ChatAnthropic(
                model=model,
                temperature=temperature,
                **kwargs
            )
        elif provider == self.LLM_GOOGLE:
            if not GOOGLE_AVAILABLE:
                raise ImportError("langchain-google-genai package not installed. Run 'pip install langchain-google-genai'")
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

        # Load appropriate prompt template
        if not tools_list:
            # Dropdown to simple chat if no tools provided
            if self.verbose:
                logger.warning(f"No tools provided for agent '{role}'. Creating simple chat agent.")
            
            # Use a minimal system prompt if none provided
            prompt = system_prompt or "You are a helpful assistant."
            
            # Create a simple agent executor that just calls the LLM
            from langchain_core.runnables import RunnablePassthrough
            
            # For simplicity in the shim, we still wrap it in AgentExecutor 
            # but it won't have tools to call.
            agent = (
                {"input": RunnablePassthrough(), "chat_history": lambda x: []}
                | llm
            )
            
            agent_executor = AgentExecutor(
                agent=agent,
                tools=[],
                verbose=self.verbose,
                handle_parsing_errors=handle_parsing_errors,
                **kwargs
            )
            
            agent_executor.metadata = {
                "role": role,
                "agent_type": "simple_chat",
                "llm_provider": llm_provider or self.default_llm_provider,
                "model": model or self.default_model,
                "tools_count": 0,
                "memory_enabled": enable_memory,
                "response_schema": response_schema
            }
            return agent_executor

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

    def create_openhands_agent(

        self,
        model: Optional[str] = None,
        workspace_dir: Optional[Any] = None,
        use_ollama: Optional[bool] = None,
        enabled_tools: Optional[set] = None,
        enable_tool_calling: bool = True,
        keep_alive: str = "5m",
        **kwargs
    ) -> OpenHandsWorker:
        """
        Create an OpenHands autonomous coding agent worker.
        
        Args:
            model: LLM model name (e.g., "qwen2.5-coder:latest")
            workspace_dir: Directory where agent will work
            use_ollama: Whether to use local Ollama (auto-detected if None)
            enabled_tools: Set of ToolOption to enable (default: terminal, file_editor, apply_patch)
            enable_tool_calling: Use native tool calling for supported models
            keep_alive: How long Ollama keeps model loaded (default: 5m)
            **kwargs: Additional arguments passed to OpenHandsWorker
            
        Returns:
            OpenHandsWorker: Configured worker instance
        """
        # Use factory's default model if not specified
        if model is None:
            provider = self.default_llm_provider
            
            # Auto-enable ollama if factory defaults to it
            if provider == self.LLM_OLLAMA and use_ollama is None:
                use_ollama = True
                
            if use_ollama or provider == self.LLM_OLLAMA:
                model = self.default_model
            else:
                model = self.default_model

        # Create and return worker with all options
        return OpenHandsWorker(
            model=model,
            workspace_dir=workspace_dir,
            use_ollama=use_ollama,
            enabled_tools=enabled_tools or DEFAULT_TOOLS,
            enable_tool_calling=enable_tool_calling,
            keep_alive=keep_alive,
            verbose=self.verbose,
            **kwargs
        )


"""
AgentFactory: Dynamic LangChain Agent Creation System

This module provides a flexible factory pattern for creating specialized AI agents
with custom capabilities, tools, and configurations.

Based on patterns from: https://github.com/Mikecranesync/langchain-crash-course
"""

from typing import List, Dict, Optional, Any, Union
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent, create_structured_chat_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.tools import BaseTool
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI


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
        verbose: bool = True
    ):
        """
        Initialize the AgentFactory.

        Args:
            default_llm_provider: Default LLM provider ("openai", "anthropic", "google")
            default_model: Default model name
            default_temperature: Default temperature for LLM
            verbose: Whether to show agent reasoning steps
        """
        self.default_llm_provider = default_llm_provider
        self.default_model = default_model
        self.default_temperature = default_temperature
        self.verbose = verbose

    def _create_llm(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs
    ):
        """Create LLM instance based on provider."""
        provider = provider or self.default_llm_provider
        model = model or self.default_model
        temperature = temperature if temperature is not None else self.default_temperature

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
            **kwargs: Additional arguments passed to AgentExecutor

        Returns:
            AgentExecutor: Configured and ready-to-use agent executor

        Example:
            >>> factory = AgentFactory()
            >>> agent = factory.create_agent(
            ...     role="Research Agent",
            ...     tools_list=[search_tool, wikipedia_tool],
            ...     system_prompt="You are a helpful research assistant."
            ... )
            >>> response = agent.invoke({"input": "What is LangChain?"})
        """
        # Create LLM
        llm = self._create_llm(
            provider=llm_provider,
            model=model,
            temperature=temperature
        )

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
            "memory_enabled": enable_memory
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

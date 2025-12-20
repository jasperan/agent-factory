"""
Compatibility shim for LangChain 1.2.0 API changes.

LangChain 1.2.0 removed AgentExecutor and create_react_agent in favor of
a unified create_agent() API. This shim provides backward compatibility
so existing code continues to work without modification.

Migration Path:
    1. Use this shim short-term to unblock development
    2. Schedule full migration to new create_agent() API
    3. Remove shim once migration complete

New API Reference:
    https://docs.langchain.com/oss/python/langchain/agents
"""

from typing import List, Dict, Any, Optional, Sequence, Callable
from langchain.agents import create_agent as _new_create_agent
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
import logging

logger = logging.getLogger(__name__)


class AgentExecutor:
    """
    Backward-compatible wrapper for LangChain 1.2.0's create_agent().

    Provides the same interface as old AgentExecutor but uses new API internally.
    Supports .invoke() and basic memory/metadata functionality.

    Note: This is a simplified compatibility layer. Some advanced features
    of the old AgentExecutor may not be fully supported.
    """

    def __init__(
        self,
        agent: Any,
        tools: List[BaseTool],
        memory: Optional[Any] = None,
        verbose: bool = False,
        handle_parsing_errors: bool = True,
        **kwargs
    ):
        """
        Initialize AgentExecutor wrapper.

        Args:
            agent: Agent graph from create_react_agent (new API)
            tools: List of tools available to agent
            memory: Memory instance (not directly used in new API)
            verbose: Enable debug output
            handle_parsing_errors: Gracefully handle parsing errors
            **kwargs: Additional arguments (stored in metadata)
        """
        self._agent = agent
        self.tools = tools
        self.memory = memory
        self.verbose = verbose
        self.handle_parsing_errors = handle_parsing_errors
        self.metadata = kwargs.get('metadata', {})

        # Store checkpointer for conversation memory
        self._checkpointer = MemorySaver() if memory else None

    def invoke(self, inputs: Dict[str, Any], config: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Invoke agent with inputs.

        Maps old {"input": "query"} format to new {"messages": [...]} format.

        Args:
            inputs: Input dictionary (old format: {"input": "query"})
            config: Optional configuration
            **kwargs: Additional arguments

        Returns:
            Response dictionary
        """
        try:
            # Map old format to new format
            if "input" in inputs:
                # Old format: {"input": "query"}
                user_query = inputs["input"]
                messages = [("user", user_query)]
                new_inputs = {"messages": messages}
            else:
                # Already in new format
                new_inputs = inputs

            # Add thread_id for memory if checkpointer enabled
            if config is None and self._checkpointer:
                config = {"configurable": {"thread_id": "default"}}

            # Invoke agent
            result = self._agent.invoke(new_inputs, config=config, **kwargs)

            # Map response back to old format if needed
            if "messages" in result and "input" in inputs:
                # Extract last message content as output
                messages = result.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, 'content'):
                        output = last_message.content
                    elif isinstance(last_message, tuple) and len(last_message) > 1:
                        output = last_message[1]
                    else:
                        output = str(last_message)

                    return {
                        "input": inputs["input"],
                        "output": output,
                        "intermediate_steps": [],  # Not easily accessible in new API
                    }

            return result

        except Exception as e:
            if self.handle_parsing_errors:
                logger.error(f"Agent execution error: {e}")
                return {
                    "input": inputs.get("input", ""),
                    "output": f"Error: {str(e)}",
                    "error": str(e)
                }
            raise

    async def ainvoke(self, inputs: Dict[str, Any], config: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Async version of invoke."""
        # For now, delegate to sync version
        # TODO: Implement proper async support if needed
        return self.invoke(inputs, config, **kwargs)

    @classmethod
    def from_agent_and_tools(
        cls,
        agent: Any,
        tools: List[BaseTool],
        memory: Optional[Any] = None,
        verbose: bool = False,
        handle_parsing_errors: bool = True,
        **kwargs
    ) -> "AgentExecutor":
        """
        Create AgentExecutor from agent and tools.

        This matches the old API's factory method.

        Args:
            agent: Agent graph
            tools: List of tools
            memory: Optional memory
            verbose: Enable debug output
            handle_parsing_errors: Handle parsing errors
            **kwargs: Additional arguments

        Returns:
            AgentExecutor instance
        """
        return cls(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=verbose,
            handle_parsing_errors=handle_parsing_errors,
            **kwargs
        )


def create_react_agent(
    llm: BaseChatModel,
    tools: List[BaseTool],
    prompt: Any,
    **kwargs
) -> Any:
    """
    Backward-compatible wrapper for create_agent().

    Creates a ReAct-style agent using the new unified API.

    Args:
        llm: Language model
        tools: List of tools
        prompt: Prompt template (converted to system_prompt string)
        **kwargs: Additional arguments

    Returns:
        Agent graph (new CompiledStateGraph)
    """
    # Convert prompt to system_prompt string
    if prompt is None:
        system_prompt = "You are a helpful assistant."
    elif isinstance(prompt, str):
        system_prompt = prompt
    elif isinstance(prompt, ChatPromptTemplate):
        # Extract system message from prompt template
        try:
            system_prompt = str(prompt)
        except Exception:
            system_prompt = "You are a helpful assistant."
    else:
        # Fallback: convert to string
        system_prompt = str(prompt)

    # Create agent using new API
    agent = _new_create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        **kwargs
    )

    return agent


def create_structured_chat_agent(
    llm: BaseChatModel,
    tools: List[BaseTool],
    prompt: Any,
    **kwargs
) -> Any:
    """
    Backward-compatible wrapper for structured chat agents.

    In LangChain 1.2.0, structured chat functionality is unified
    into create_agent(). This wrapper provides compatibility.

    Args:
        llm: Language model
        tools: List of tools
        prompt: Prompt template
        **kwargs: Additional arguments

    Returns:
        Agent graph
    """
    # Structured chat is now handled by create_agent
    return create_react_agent(llm, tools, prompt, **kwargs)

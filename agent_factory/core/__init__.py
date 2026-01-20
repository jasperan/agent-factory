# Agent Factory Core Module
# Provides AgentFactory for creating OpenHands agents with Ollama

try:
    from .agent_factory import AgentFactory
    _agent_factory_available = True
except ImportError:
    _agent_factory_available = False
    AgentFactory = None

__all__ = []

if _agent_factory_available:
    __all__.append("AgentFactory")

# RIVET Pro Orchestrator imports
from .orchestrator import RivetOrchestrator

# Try to import AgentFactory (may fail due to langchain import issues)
try:
    from .agent_factory import AgentFactory
    _agent_factory_available = True
except ImportError:
    _agent_factory_available = False
    AgentFactory = None

# Try to import callbacks (for old orchestrator compatibility)
try:
    from .callbacks import EventBus, EventType, Event, create_default_event_bus
    _callbacks_available = True
except ImportError:
    _callbacks_available = False
    EventBus = EventType = Event = create_default_event_bus = None

__all__ = [
    "RivetOrchestrator",  # New: RIVET Pro orchestrator
]

# Add old exports if available (for backwards compatibility)
if _agent_factory_available:
    __all__.append("AgentFactory")

if _callbacks_available:
    __all__.extend(["EventBus", "EventType", "Event", "create_default_event_bus"])

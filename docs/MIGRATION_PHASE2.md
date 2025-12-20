# Migration Guide: Phase 2 - Cost-Optimized Model Routing

**Date:** 2025-12-19
**Phase:** Phase 2 Complete
**Impact:** Breaking change for users with direct-provider code

---

## Breaking Change: `enable_routing` Default

### What Changed

In Phase 2, we introduced cost-optimized model routing with `LLMRouter` and `RoutedChatModel`. To enable this feature by default, the `enable_routing` parameter in `AgentFactory.create_agent()` now defaults to **True** (previously **False**).

**Before (Phase 1):**
```python
factory = AgentFactory()
agent = factory.create_agent(
    role="researcher",
    tools_list=[search_tool],
    enable_routing=False  # Default was False
)
# Agent used explicit provider (OpenAI, Anthropic, etc.)
```

**After (Phase 2):**
```python
factory = AgentFactory()
agent = factory.create_agent(
    role="researcher",
    tools_list=[search_tool],
    enable_routing=True  # Default is now True
)
# Agent automatically selects cheapest capable model
```

---

## Who Is Affected

### ✅ Not Affected (Most Users)
If your code does NOT explicitly set `enable_routing=False`, you are **not affected**. Your agents will now automatically use cost-optimized routing (better performance, lower costs).

### ❌ Affected (Explicit Provider Users)
If your code relies on **explicit provider selection** (e.g., always using OpenAI GPT-4), you must **opt out** of routing.

**Example affected code:**
```python
# Phase 1 code that assumed direct provider usage
agent = factory.create_agent(
    role="coder",
    tools_list=[code_tool],
    # No enable_routing specified (defaulted to False)
)
# In Phase 1: Used explicit provider
# In Phase 2: Now uses routing (may select different model)
```

---

## Migration Steps

### Option 1: Embrace Routing (Recommended)

**Do nothing!** Cost-optimized routing provides:
- ✅ Lower costs (automatic cheapest model selection)
- ✅ Better performance (intelligent fallback chains)
- ✅ Cost tracking (via `get_global_tracker()`)

Most users should adopt routing for immediate cost savings.

---

### Option 2: Opt Out (Preserve Old Behavior)

If you **require specific providers** (e.g., compliance, testing), explicitly disable routing:

```python
agent = factory.create_agent(
    role="researcher",
    tools_list=[search_tool],
    enable_routing=False  # Opt out of routing
)
# Agent uses explicit provider (same as Phase 1)
```

---

## New Capabilities

Phase 2 introduces powerful routing features:

### 1. Capability-Based Selection
```python
from agent_factory.llm.types import ModelCapability

# Simple task → cheapest model (haiku, gpt-3.5-turbo)
agent = factory.create_agent(
    role="summarizer",
    capability=ModelCapability.SIMPLE,
    enable_routing=True
)

# Complex task → capable model (sonnet, gpt-4)
agent = factory.create_agent(
    role="architect",
    capability=ModelCapability.ADVANCED,
    enable_routing=True
)
```

### 2. Cost Tracking
```python
from agent_factory.llm.tracker import get_global_tracker

# Run agent
agent.run("Analyze this codebase")

# Get cost stats
tracker = get_global_tracker()
print(f"Total cost: ${tracker.total_cost:.4f}")
print(f"Total tokens: {tracker.total_tokens}")
print(tracker.get_cost_by_provider())
```

### 3. Fallback Chains
```python
# Automatic fallback if primary model fails
agent = factory.create_agent(
    role="coder",
    enable_routing=True,
    enable_fallback=True  # Auto-retry with backup model
)
```

---

## Provider Inference Improvements

Phase 2 also includes enhanced model provider detection using **regex patterns** instead of fragile `startswith` checks.

**Supported model families:**
- **OpenAI:** `gpt-*`, `o1-*`, `o3-*`, `text-*`
- **Anthropic:** `claude-*`, `claude-opus-*`, `claude-sonnet-*`
- **Google:** `gemini-*`

**Example:**
```python
from agent_factory.llm.langchain_adapter import RoutedChatModel

# All these now work correctly
model1 = RoutedChatModel(explicit_model="gpt-4o")      # ✅ OpenAI
model2 = RoutedChatModel(explicit_model="o1-mini")     # ✅ OpenAI o1
model3 = RoutedChatModel(explicit_model="o3-full")     # ✅ OpenAI o3
model4 = RoutedChatModel(explicit_model="claude-opus-4")  # ✅ Anthropic
```

---

## Testing Your Migration

### 1. Run Import Validation
```bash
poetry run python -c "from agent_factory.core.agent_factory import AgentFactory; from agent_factory.llm.langchain_adapter import RoutedChatModel; print('OK')"
```

### 2. Test Routing Behavior
```python
from agent_factory.core.agent_factory import AgentFactory
from agent_factory.llm.types import ModelCapability

factory = AgentFactory()

# Create agent with routing enabled (default)
agent = factory.create_agent(
    role="test_agent",
    capability=ModelCapability.SIMPLE,
    enable_routing=True
)

# Verify routing is active
print(f"Routing enabled: {agent.config.enable_routing}")
print(f"Selected model: {agent.config.model}")
```

### 3. Run Full Test Suite
```bash
poetry run pytest tests/ -v
```

---

## Rollback Plan

If Phase 2 causes issues, you can rollback to Phase 1 behavior **globally** by patching the default:

```python
# In your main application entry point
from agent_factory.core.agent_factory import AgentFactory

# Monkey-patch to restore Phase 1 default
original_create_agent = AgentFactory.create_agent

def create_agent_no_routing(self, *args, **kwargs):
    if 'enable_routing' not in kwargs:
        kwargs['enable_routing'] = False  # Phase 1 default
    return original_create_agent(self, *args, **kwargs)

AgentFactory.create_agent = create_agent_no_routing
```

**Note:** This is a temporary workaround. Please report issues so we can fix them.

---

## FAQ

**Q: Will my agents use different models now?**
A: Yes, if you didn't explicitly set `enable_routing=False`. Agents will now use the cheapest capable model for each task.

**Q: Will this increase costs?**
A: No! Routing **reduces** costs by selecting cheaper models when possible. You should see cost savings.

**Q: Can I still use specific models (e.g., always GPT-4)?**
A: Yes, set `enable_routing=False` OR use `explicit_model="gpt-4"` in LangChain adapters.

**Q: What if I'm using environment variables (OPENAI_API_KEY, etc.)?**
A: No change needed. Routing respects your API key configuration.

**Q: Does routing work with local LLMs (Ollama)?**
A: Yes! Set `exclude_local=False` to include local models in routing decisions.

**Q: How do I track costs across multiple agents?**
A: Use `get_global_tracker()` to aggregate costs:
```python
from agent_factory.llm.tracker import get_global_tracker
tracker = get_global_tracker()
print(tracker.get_summary())
```

---

## Support

**Issues:** https://github.com/Mikecranesync/Agent-Factory/issues
**Phase 2 Spec:** `docs/PHASE2_SPEC.md`
**Routing Docs:** `agent_factory/llm/router.py`

---

## Timeline

- **2025-12-15:** Phase 2 development complete
- **2025-12-19:** Breaking change deployed (`enable_routing=True` default)
- **2025-12-20:** Migration guide published
- **2026-01-05:** Phase 1 compatibility removed (opt-out required for direct providers)

---

**Bottom Line:** Most users should adopt routing for immediate cost savings. If you require specific providers, set `enable_routing=False`.

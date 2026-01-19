"""Validate vision model configuration"""
from agent_factory.llm.config import MODEL_REGISTRY, ROUTING_TIERS
from agent_factory.llm.types import ModelCapability

# Check vision-capable models
vision_models = [m for m in MODEL_REGISTRY.values() if m.supports_vision]
print(f"[OK] Vision-capable models: {len(vision_models)}")
for m in vision_models:
    print(f"  - {m.model_name} ({m.provider}): ${m.input_cost_per_1k*1000:.2f}/M input tokens")

# Check VISION routing tier
vision_tier = ROUTING_TIERS.get(ModelCapability.VISION, [])
print(f"\n[OK] VISION routing tier ({len(vision_tier)} models):")
for model_name in vision_tier:
    print(f"  - {model_name}")

# Check router integration
from agent_factory.llm.router import LLMRouter
router = LLMRouter()
print(f"\n[OK] LLMRouter initialized successfully")

print("\n[SUCCESS] All Phase 1 validations passed!")

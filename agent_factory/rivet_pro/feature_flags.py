"""Feature access control by subscription tier.

MVP: Everyone gets "beta" tier with full Pro access.
Later: Enforce tier restrictions after monetization.
"""
from typing import Set

# Tier hierarchy (higher tiers include lower tier features)
TIER_FEATURES = {
    "free": {
        "basic_chat",
        "equipment_lookup",
    },
    "beta": {
        # Beta users get EVERYTHING free during MVP
        "basic_chat",
        "equipment_lookup",
        "voice_work_orders",
        "unlimited_prints",
        "chat_with_print",
        "priority_support",
        "predictive_ai",  # Even enterprise features!
        "api_access",
    },
    "basic": {
        "basic_chat",
        "equipment_lookup",
        "voice_work_orders",
        "limited_prints",  # 5 prints
    },
    "pro": {
        "basic_chat",
        "equipment_lookup",
        "voice_work_orders",
        "unlimited_prints",
        "chat_with_print",
        "priority_support",
    },
    "enterprise": {
        "basic_chat",
        "equipment_lookup",
        "voice_work_orders",
        "unlimited_prints",
        "chat_with_print",
        "priority_support",
        "predictive_ai",
        "api_access",
        "sso",
        "dedicated_support",
    },
}

# Default tier for new users (MVP = beta, Later = free)
DEFAULT_TIER = "beta"


def get_tier_features(tier: str) -> Set[str]:
    """Get all features available for a tier."""
    return TIER_FEATURES.get(tier, TIER_FEATURES["free"])


def has_feature(user_tier: str, feature: str) -> bool:
    """Check if a tier has access to a feature."""
    tier_features = get_tier_features(user_tier)
    return feature in tier_features


def require_feature(feature: str):
    """
    Decorator to require a feature for an API endpoint or handler.
    
    Usage:
        @require_feature("chat_with_print")
        async def handle_print_question(update, context):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user from args (works for both FastAPI and Telegram)
            user_tier = kwargs.get("user_tier", DEFAULT_TIER)
            
            if not has_feature(user_tier, feature):
                # For Telegram handlers
                if "update" in kwargs:
                    update = kwargs["update"]
                    await update.message.reply_text(
                        f"⬆️ This feature requires an upgrade.\n\n"
                        f"You're on the {user_tier} plan.\n"
                        f"Upgrade to access {feature.replace('_', ' ')}."
                    )
                    return None
                # For FastAPI
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=402,
                    detail=f"Feature '{feature}' requires upgrade from {user_tier} tier"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Quick checks for common features
def can_use_voice(tier: str) -> bool:
    return has_feature(tier, "voice_work_orders")


def can_chat_with_print(tier: str) -> bool:
    return has_feature(tier, "chat_with_print")


def can_use_api(tier: str) -> bool:
    return has_feature(tier, "api_access")


def get_print_limit(tier: str) -> int:
    """Get number of prints allowed for tier. -1 = unlimited."""
    if has_feature(tier, "unlimited_prints"):
        return -1
    if has_feature(tier, "limited_prints"):
        return 5
    return 0


# For display purposes
TIER_DISPLAY_NAMES = {
    "free": "Free",
    "beta": "Beta (Full Access)",
    "basic": "Rivet Basic",
    "pro": "Rivet Pro",
    "enterprise": "Rivet Enterprise",
}

TIER_PRICES = {
    "free": 0,
    "beta": 0,  # Free during beta!
    "basic": 20,
    "pro": 40,
    "enterprise": 99,
}

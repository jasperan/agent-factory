"""User management endpoints.

Handles:
- User provisioning from Stripe
- User lookup
- Telegram linking
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Literal, Optional
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# SCHEMAS
# =============================================================================

class UserProvisionRequest(BaseModel):
    """Request to provision a new user."""
    email: Optional[EmailStr] = None
    telegram_user_id: Optional[int] = None
    telegram_username: Optional[str] = None
    stripe_customer_id: Optional[str] = None  # Optional for MVP
    subscription_tier: Literal["free", "beta", "basic", "pro", "enterprise"] = "beta"


class UserProvisionResponse(BaseModel):
    """Response after provisioning a user."""
    user_id: str
    atlas_user_id: Optional[str] = None
    telegram_link: str
    tier: str


class UserResponse(BaseModel):
    """User details response."""
    user_id: str
    email: str
    tier: str
    stripe_customer_id: Optional[str] = None
    telegram_id: Optional[str] = None
    atlas_user_id: Optional[str] = None
    created_at: Optional[str] = None


class TelegramLinkRequest(BaseModel):
    """Request to link Telegram account."""
    user_id: str
    telegram_user_id: int
    telegram_username: Optional[str] = None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/users/provision", response_model=UserProvisionResponse)
async def provision_user(request: UserProvisionRequest):
    """
    Provision a new user.
    
    MVP Flow (no Stripe):
    - Called when user starts Telegram bot
    - Everyone gets "beta" tier with full access
    
    Future Flow (with Stripe):
    - Called by Stripe webhook after payment
    - Tier based on subscription
    
    Flow:
    1. Create user in our database
    2. Create user in Atlas CMMS (optional)
    3. Return user info
    """
    logger.info(f"Provisioning user: {request.email} ({request.subscription_tier})")
    
    # Generate user ID
    user_id = str(uuid4())
    
    # ==========================================================================
    # TODO: Create user in database
    # ==========================================================================
    # from agent_factory.rivet_pro.database import create_user
    # user = await create_user(
    #     email=request.email,
    #     stripe_customer_id=request.stripe_customer_id,
    #     tier=request.subscription_tier
    # )
    
    # ==========================================================================
    # TODO: Create user in Atlas CMMS (WS-1)
    # ==========================================================================
    # from agent_factory.integrations.atlas import AtlasClient
    # atlas = AtlasClient()
    # atlas_user = await atlas.create_user(
    #     email=request.email,
    #     role="technician",
    #     metadata={"stripe_id": request.stripe_customer_id}
    # )
    # atlas_user_id = atlas_user["id"]
    atlas_user_id = None  # Placeholder
    
    # Generate Telegram deep link
    telegram_link = f"https://t.me/RivetCEO_bot?start={user_id}"
    
    logger.info(f"User provisioned: {user_id}")
    
    return UserProvisionResponse(
        user_id=user_id,
        atlas_user_id=atlas_user_id,
        telegram_link=telegram_link,
        tier=request.subscription_tier
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """
    Get user details by ID.
    """
    # ==========================================================================
    # TODO: Fetch from database
    # ==========================================================================
    # from agent_factory.rivet_pro.database import get_user_by_id
    # user = await get_user_by_id(user_id)
    # if not user:
    #     raise HTTPException(404, "User not found")
    # return user
    
    raise HTTPException(501, "Not implemented yet")


@router.get("/users/by-email/{email}", response_model=UserResponse)
async def get_user_by_email(email: str):
    """
    Get user details by email.
    """
    # ==========================================================================
    # TODO: Fetch from database
    # ==========================================================================
    raise HTTPException(501, "Not implemented yet")


@router.get("/users/by-telegram/{telegram_id}", response_model=UserResponse)
async def get_user_by_telegram(telegram_id: int):
    """
    Get user details by Telegram user ID.
    
    Used by the Telegram bot to look up users.
    """
    # ==========================================================================
    # TODO: Fetch from database
    # ==========================================================================
    raise HTTPException(501, "Not implemented yet")


@router.post("/users/from-telegram", response_model=UserProvisionResponse)
async def provision_from_telegram(telegram_user_id: int, telegram_username: Optional[str] = None):
    """
    Provision a new user from Telegram bot /start command.
    
    This is the MVP signup flow - no payment required.
    User gets full "beta" access.
    
    Called by the Telegram bot when a new user sends /start.
    """
    logger.info(f"Provisioning user from Telegram: {telegram_user_id} (@{telegram_username})")
    
    # Generate user ID
    user_id = str(uuid4())
    
    # ==========================================================================
    # TODO: Check if user already exists
    # ==========================================================================
    # existing = await get_user_by_telegram(telegram_user_id)
    # if existing:
    #     return existing
    
    # ==========================================================================
    # TODO: Create user in database
    # ==========================================================================
    # user = await create_user(
    #     telegram_id=telegram_user_id,
    #     telegram_username=telegram_username,
    #     tier="beta"
    # )
    
    # For MVP, just return success
    return UserProvisionResponse(
        user_id=user_id,
        atlas_user_id=None,
        telegram_link=f"https://t.me/RivetCEO_bot",
        tier="beta"  # Everyone gets full access during beta
    )


@router.post("/users/link-telegram")
async def link_telegram_account(request: TelegramLinkRequest):
    """
    Link a Telegram account to an existing user.
    
    Called when a user starts the Telegram bot with their user ID
    from the deep link.
    """
    logger.info(f"Linking Telegram {request.telegram_user_id} to user {request.user_id}")
    
    # ==========================================================================
    # TODO: Update user in database
    # ==========================================================================
    # await update_user_telegram(
    #     user_id=request.user_id,
    #     telegram_id=request.telegram_user_id,
    #     telegram_username=request.telegram_username
    # )
    
    return {"status": "linked", "user_id": request.user_id}


@router.put("/users/{user_id}/tier")
async def update_user_tier(user_id: str, tier: Literal["basic", "pro", "enterprise"]):
    """
    Update a user's subscription tier.
    
    Called by Stripe webhook when subscription changes.
    """
    logger.info(f"Updating user {user_id} to tier {tier}")
    
    # ==========================================================================
    # TODO: Update in database and Atlas
    # ==========================================================================
    
    return {"status": "updated", "user_id": user_id, "tier": tier}

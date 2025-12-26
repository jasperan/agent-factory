"""Stripe payment endpoints.

Handles:
- Checkout session creation
- Webhook processing
- Billing portal
- Subscription management
"""
import stripe
from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel, EmailStr
from typing import Literal, Optional
import logging

from agent_factory.api.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


# =============================================================================
# SCHEMAS
# =============================================================================

class CreateCheckoutRequest(BaseModel):
    """Request to create a checkout session."""
    email: EmailStr
    tier: Literal["basic", "pro", "enterprise"]
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CreateCheckoutResponse(BaseModel):
    """Checkout session response."""
    checkout_url: str
    session_id: str


class BillingPortalRequest(BaseModel):
    """Request to create billing portal session."""
    customer_id: str
    return_url: Optional[str] = None


class BillingPortalResponse(BaseModel):
    """Billing portal response."""
    portal_url: str


class WebhookResponse(BaseModel):
    """Webhook processing response."""
    status: str
    event_type: Optional[str] = None


class CheckoutSuccessResponse(BaseModel):
    """Checkout success page data."""
    status: str
    email: Optional[str]
    tier: Optional[str]
    telegram_link: str
    next_steps: list[str]


# =============================================================================
# PRICE MAPPING
# =============================================================================

def get_tier_prices() -> dict:
    """Get tier to price mapping from settings."""
    return {
        "basic": settings.stripe_price_basic,
        "pro": settings.stripe_price_pro,
        "enterprise": settings.stripe_price_enterprise,
    }


def get_price_tiers() -> dict:
    """Get price to tier mapping."""
    tier_prices = get_tier_prices()
    return {v: k for k, v in tier_prices.items() if v}


# =============================================================================
# CHECKOUT ENDPOINTS
# =============================================================================

@router.post("/checkout/create", response_model=CreateCheckoutResponse)
async def create_checkout_session(request: CreateCheckoutRequest):
    """
    Create a Stripe Checkout session for subscription.
    
    Returns a URL to redirect the user to Stripe's hosted checkout page.
    
    **Tiers:**
    - basic: $20/month - Voice work orders, 5 prints
    - pro: $40/month - Unlimited prints, Chat with Print
    - enterprise: $99/month - Predictive AI, API access
    """
    tier_prices = get_tier_prices()
    price_id = tier_prices.get(request.tier)
    
    if not price_id:
        raise HTTPException(400, f"Invalid tier: {request.tier}. Price ID not configured.")
    
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            customer_email=request.email,
            success_url=request.success_url or f"{settings.app_url}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=request.cancel_url or f"{settings.app_url}/pricing",
            metadata={
                "tier": request.tier,
                "source": "rivet_api"
            },
            subscription_data={
                "metadata": {
                    "tier": request.tier
                }
            },
            # Allow promotion codes for discounts
            allow_promotion_codes=True,
            # Collect billing address for tax
            billing_address_collection="auto",
        )
        
        logger.info(f"Created checkout session {session.id} for {request.email} ({request.tier})")
        
        return CreateCheckoutResponse(
            checkout_url=session.url,
            session_id=session.id
        )
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout: {e}")
        raise HTTPException(500, f"Payment service error: {str(e)}")


@router.get("/checkout/success", response_model=CheckoutSuccessResponse)
async def checkout_success(session_id: str):
    """
    Handle successful checkout redirect.
    
    Retrieve session details and return user info + next steps.
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        return CheckoutSuccessResponse(
            status="success",
            email=session.customer_email,
            tier=session.metadata.get("tier"),
            telegram_link="https://t.me/RivetCEO_bot?start=new",
            next_steps=[
                "Check your email for confirmation",
                "Open Telegram on your phone",
                "Search for @RivetCEO_bot",
                "Tap Start to begin"
            ]
        )
    except stripe.error.StripeError as e:
        raise HTTPException(400, f"Could not retrieve session: {str(e)}")


# =============================================================================
# WEBHOOK ENDPOINT
# =============================================================================

@router.post("/webhooks/stripe", response_model=WebhookResponse)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(alias="Stripe-Signature")
):
    """
    Handle Stripe webhook events.
    
    **Events handled:**
    - `checkout.session.completed`: Provision new user
    - `customer.subscription.updated`: Update tier
    - `customer.subscription.deleted`: Handle cancellation
    - `invoice.payment_failed`: Notify user
    
    **Setup:** Configure webhook in Stripe Dashboard pointing to:
    `https://your-domain.com/api/webhooks/stripe`
    """
    # Get raw body for signature verification
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            settings.stripe_webhook_secret
        )
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {e}")
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {e}")
        raise HTTPException(400, "Invalid signature")
    
    event_type = event["type"]
    event_data = event["data"]["object"]
    
    logger.info(f"Processing Stripe webhook: {event_type}")
    
    # Route to appropriate handler
    handlers = {
        "checkout.session.completed": handle_checkout_completed,
        "customer.subscription.created": handle_subscription_created,
        "customer.subscription.updated": handle_subscription_updated,
        "customer.subscription.deleted": handle_subscription_deleted,
        "invoice.payment_succeeded": handle_payment_succeeded,
        "invoice.payment_failed": handle_payment_failed,
    }
    
    handler = handlers.get(event_type)
    if handler:
        await handler(event_data)
    else:
        logger.info(f"Unhandled webhook event type: {event_type}")
    
    return WebhookResponse(status="ok", event_type=event_type)


# =============================================================================
# WEBHOOK HANDLERS
# =============================================================================

async def handle_checkout_completed(session: dict):
    """
    Handle successful checkout - provision new user.
    
    This is the critical path: payment → user creation → bot access
    """
    customer_email = session.get("customer_email")
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")
    tier = session.get("metadata", {}).get("tier", "basic")
    
    logger.info(f"Checkout completed: {customer_email} ({tier})")
    
    # Get subscription details for more info
    if subscription_id:
        subscription = stripe.Subscription.retrieve(subscription_id)
        logger.info(f"Subscription status: {subscription.status}")
    
    # ==========================================================================
    # TODO: Implement user provisioning (WS-1 provides this)
    # ==========================================================================
    # from agent_factory.integrations.atlas import AtlasClient
    # from agent_factory.api.routers.users import provision_user_internal
    # 
    # user = await provision_user_internal(
    #     email=customer_email,
    #     stripe_customer_id=customer_id,
    #     subscription_tier=tier
    # )
    # 
    # # Send welcome message via Telegram if they've already started the bot
    # await send_telegram_welcome(user.telegram_id, tier)
    
    # For now, log what we would do
    logger.info(f"[TODO] Provision user: email={customer_email}, tier={tier}, stripe_id={customer_id}")


async def handle_subscription_created(subscription: dict):
    """Handle new subscription creation."""
    customer_id = subscription.get("customer")
    status = subscription.get("status")
    tier = subscription.get("metadata", {}).get("tier", "unknown")
    
    logger.info(f"Subscription created: customer={customer_id}, status={status}, tier={tier}")


async def handle_subscription_updated(subscription: dict):
    """Handle subscription update (tier change, renewal, etc.)."""
    customer_id = subscription.get("customer")
    status = subscription.get("status")
    
    # Get the price ID to determine tier
    price_tiers = get_price_tiers()
    items = subscription.get("items", {}).get("data", [])
    
    if items:
        price_id = items[0].get("price", {}).get("id")
        new_tier = price_tiers.get(price_id, "unknown")
    else:
        new_tier = subscription.get("metadata", {}).get("tier", "unknown")
    
    logger.info(f"Subscription updated: customer={customer_id}, status={status}, tier={new_tier}")
    
    # ==========================================================================
    # TODO: Update user's tier in database
    # ==========================================================================
    # await update_user_tier(customer_id, new_tier)


async def handle_subscription_deleted(subscription: dict):
    """Handle subscription cancellation."""
    customer_id = subscription.get("customer")
    
    logger.info(f"Subscription deleted: customer={customer_id}")
    
    # ==========================================================================
    # TODO: Downgrade user to free tier or deactivate
    # ==========================================================================
    # await downgrade_user(customer_id)


async def handle_payment_succeeded(invoice: dict):
    """Handle successful payment (renewal)."""
    customer_id = invoice.get("customer")
    amount_paid = invoice.get("amount_paid", 0) / 100  # cents to dollars
    
    logger.info(f"Payment succeeded: customer={customer_id}, amount=${amount_paid}")


async def handle_payment_failed(invoice: dict):
    """Handle failed payment."""
    customer_id = invoice.get("customer")
    customer_email = invoice.get("customer_email")
    amount_due = invoice.get("amount_due", 0) / 100  # cents to dollars
    attempt_count = invoice.get("attempt_count", 1)
    
    logger.warning(
        f"Payment failed: customer={customer_id}, email={customer_email}, "
        f"amount=${amount_due}, attempt={attempt_count}"
    )
    
    # ==========================================================================
    # TODO: Notify user via email and/or Telegram
    # ==========================================================================
    # await notify_payment_failed(customer_email, amount_due, attempt_count)


# =============================================================================
# BILLING PORTAL
# =============================================================================

@router.post("/billing/portal", response_model=BillingPortalResponse)
async def create_billing_portal(request: BillingPortalRequest):
    """
    Create a Stripe Billing Portal session for subscription management.
    
    Allows users to:
    - Update payment method
    - Change subscription tier
    - Cancel subscription
    - View invoices
    """
    try:
        session = stripe.billing_portal.Session.create(
            customer=request.customer_id,
            return_url=request.return_url or f"{settings.app_url}/account"
        )
        return BillingPortalResponse(portal_url=session.url)
    except stripe.error.StripeError as e:
        logger.error(f"Error creating billing portal: {e}")
        raise HTTPException(400, f"Could not create portal: {str(e)}")


# =============================================================================
# SUBSCRIPTION MANAGEMENT
# =============================================================================

@router.post("/subscriptions/cancel")
async def cancel_subscription(customer_id: str, immediate: bool = False):
    """
    Cancel a customer's subscription.
    
    Args:
        customer_id: Stripe customer ID
        immediate: If True, cancel now. If False, cancel at period end.
    """
    try:
        # Get customer's subscriptions
        subscriptions = stripe.Subscription.list(customer=customer_id, limit=1)
        
        if not subscriptions.data:
            raise HTTPException(404, "No active subscription found")
        
        subscription = subscriptions.data[0]
        
        if immediate:
            # Cancel immediately
            stripe.Subscription.delete(subscription.id)
            logger.info(f"Subscription {subscription.id} cancelled immediately")
        else:
            # Cancel at period end
            stripe.Subscription.modify(
                subscription.id,
                cancel_at_period_end=True
            )
            logger.info(f"Subscription {subscription.id} set to cancel at period end")
        
        return {"status": "cancelled", "immediate": immediate}
        
    except stripe.error.StripeError as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise HTTPException(400, f"Could not cancel: {str(e)}")


@router.post("/subscriptions/reactivate")
async def reactivate_subscription(customer_id: str):
    """
    Reactivate a subscription that was set to cancel at period end.
    """
    try:
        subscriptions = stripe.Subscription.list(customer=customer_id, limit=1)
        
        if not subscriptions.data:
            raise HTTPException(404, "No subscription found")
        
        subscription = subscriptions.data[0]
        
        if not subscription.cancel_at_period_end:
            return {"status": "already_active"}
        
        stripe.Subscription.modify(
            subscription.id,
            cancel_at_period_end=False
        )
        
        logger.info(f"Subscription {subscription.id} reactivated")
        return {"status": "reactivated"}
        
    except stripe.error.StripeError as e:
        logger.error(f"Error reactivating subscription: {e}")
        raise HTTPException(400, f"Could not reactivate: {str(e)}")

# RIVET API - FASTAPI + STRIPE SETUP

## Quick Start (Copy-Paste Ready)

### 1. Install Dependencies

```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"

# Add to requirements.txt or pyproject.toml
pip install fastapi uvicorn stripe python-multipart pydantic-settings

# Or with poetry
poetry add fastapi uvicorn stripe python-multipart pydantic-settings
```

### 2. Environment Variables

Add to your `.env`:

```bash
# ===================
# STRIPE CONFIGURATION
# ===================

# Get from: https://dashboard.stripe.com/apikeys
STRIPE_SECRET_KEY=sk_test_xxx          # Use sk_live_xxx for production
STRIPE_PUBLISHABLE_KEY=pk_test_xxx     # Use pk_live_xxx for production

# Get from: https://dashboard.stripe.com/webhooks
# Create webhook endpoint pointing to: https://your-domain.com/api/webhooks/stripe
STRIPE_WEBHOOK_SECRET=whsec_xxx

# ===================
# STRIPE PRICE IDS
# ===================
# Create these in Stripe Dashboard > Products > Add Product
# Each product needs a recurring price

STRIPE_PRICE_BASIC=price_xxx           # $20/month
STRIPE_PRICE_PRO=price_xxx             # $40/month  
STRIPE_PRICE_ENTERPRISE=price_xxx      # $99/month

# ===================
# APP CONFIG
# ===================
APP_URL=https://rivet.io               # Your domain
API_URL=https://api.rivet.io           # API domain (can be same)
```

### 3. Create Stripe Products in Dashboard

Go to: https://dashboard.stripe.com/products

**Product 1: Rivet Basic**
- Name: Rivet Basic
- Price: $20.00 USD / month
- Copy the `price_xxx` ID → `STRIPE_PRICE_BASIC`

**Product 2: Rivet Pro**
- Name: Rivet Pro
- Price: $40.00 USD / month
- Copy the `price_xxx` ID → `STRIPE_PRICE_PRO`

**Product 3: Rivet Enterprise**
- Name: Rivet Enterprise
- Price: $99.00 USD / month
- Copy the `price_xxx` ID → `STRIPE_PRICE_ENTERPRISE`

### 4. Create Webhook Endpoint in Stripe

Go to: https://dashboard.stripe.com/webhooks

1. Click "Add endpoint"
2. URL: `https://your-domain.com/api/webhooks/stripe`
3. Select events:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Copy the signing secret → `STRIPE_WEBHOOK_SECRET`

---

## FastAPI Application Code

### File Structure

```
agent_factory/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry
│   ├── config.py            # Settings
│   ├── deps.py              # Dependencies (auth, etc.)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── stripe.py        # Stripe endpoints
│   │   ├── users.py         # User provisioning
│   │   ├── work_orders.py   # Work order CRUD
│   │   ├── assets.py        # Asset lookup
│   │   └── prints.py        # Chat with Print
│   └── models/
│       ├── __init__.py
│       ├── stripe.py        # Stripe schemas
│       ├── user.py          # User schemas
│       └── work_order.py    # Work order schemas
```

---

### `/agent_factory/api/config.py`

```python
"""API Configuration."""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment."""
    
    # App
    app_name: str = "Rivet API"
    app_url: str = "https://rivet.io"
    api_url: str = "https://api.rivet.io"
    debug: bool = False
    
    # Stripe
    stripe_secret_key: str
    stripe_publishable_key: str
    stripe_webhook_secret: str
    stripe_price_basic: str
    stripe_price_pro: str
    stripe_price_enterprise: str
    
    # Database
    database_url: str
    
    # External APIs
    anthropic_api_key: str
    openai_api_key: str
    telegram_bot_token: str
    
    # Atlas CMMS
    atlas_api_url: str = "http://localhost:8080/api"
    atlas_api_key: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

---

### `/agent_factory/api/main.py`

```python
"""Rivet API - FastAPI Application."""
import stripe
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent_factory.api.config import get_settings
from agent_factory.api.routers import stripe_router, users_router, work_orders_router

# Initialize settings
settings = get_settings()

# Configure Stripe
stripe.api_key = settings.stripe_secret_key

# Create FastAPI app
app = FastAPI(
    title="Rivet API",
    description="Voice-First CMMS with AI Schematic Understanding",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - adjust origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://rivet.io",
        "https://www.rivet.io",
        "http://localhost:3000",  # Dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stripe_router, prefix="/api", tags=["Stripe"])
app.include_router(users_router, prefix="/api", tags=["Users"])
app.include_router(work_orders_router, prefix="/api", tags=["Work Orders"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "rivet-api"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Rivet API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Run with: uvicorn agent_factory.api.main:app --reload --port 8000
```

---

### `/agent_factory/api/routers/stripe.py`

```python
"""Stripe payment endpoints."""
import stripe
from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel, EmailStr
from typing import Literal, Optional
import logging

from agent_factory.api.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# Configure Stripe
stripe.api_key = settings.stripe_secret_key


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


class WebhookResponse(BaseModel):
    """Webhook processing response."""
    status: str
    event_type: Optional[str] = None


# =============================================================================
# PRICE MAPPING
# =============================================================================

TIER_TO_PRICE = {
    "basic": settings.stripe_price_basic,
    "pro": settings.stripe_price_pro,
    "enterprise": settings.stripe_price_enterprise,
}

PRICE_TO_TIER = {v: k for k, v in TIER_TO_PRICE.items()}


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/checkout/create", response_model=CreateCheckoutResponse)
async def create_checkout_session(request: CreateCheckoutRequest):
    """
    Create a Stripe Checkout session for subscription.
    
    Returns a URL to redirect the user to Stripe's hosted checkout page.
    """
    price_id = TIER_TO_PRICE.get(request.tier)
    if not price_id:
        raise HTTPException(400, f"Invalid tier: {request.tier}")
    
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
                "source": "rivet_landing"
            },
            subscription_data={
                "metadata": {
                    "tier": request.tier
                }
            },
            # Allow promotion codes
            allow_promotion_codes=True,
        )
        
        logger.info(f"Created checkout session {session.id} for {request.email} ({request.tier})")
        
        return CreateCheckoutResponse(
            checkout_url=session.url,
            session_id=session.id
        )
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout: {e}")
        raise HTTPException(500, f"Payment service error: {str(e)}")


@router.post("/webhooks/stripe", response_model=WebhookResponse)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(alias="Stripe-Signature")
):
    """
    Handle Stripe webhook events.
    
    Events handled:
    - checkout.session.completed: Provision new user
    - customer.subscription.updated: Update tier
    - customer.subscription.deleted: Handle cancellation
    - invoice.payment_failed: Notify user
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
    
    # ==========================================================================
    # CHECKOUT COMPLETED - New subscription
    # ==========================================================================
    if event_type == "checkout.session.completed":
        await handle_checkout_completed(event_data)
    
    # ==========================================================================
    # SUBSCRIPTION UPDATED - Tier change
    # ==========================================================================
    elif event_type == "customer.subscription.updated":
        await handle_subscription_updated(event_data)
    
    # ==========================================================================
    # SUBSCRIPTION DELETED - Cancellation
    # ==========================================================================
    elif event_type == "customer.subscription.deleted":
        await handle_subscription_deleted(event_data)
    
    # ==========================================================================
    # PAYMENT FAILED
    # ==========================================================================
    elif event_type == "invoice.payment_failed":
        await handle_payment_failed(event_data)
    
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
    
    # Get subscription details
    subscription = stripe.Subscription.retrieve(subscription_id)
    
    # TODO: Import and call user provisioning (from WS-1)
    # from agent_factory.integrations.atlas import AtlasClient
    # atlas = AtlasClient()
    # user = await atlas.provision_user_from_stripe(
    #     email=customer_email,
    #     stripe_customer_id=customer_id,
    #     subscription_tier=tier
    # )
    
    # For now, log what we would do:
    logger.info(f"Would provision user: email={customer_email}, tier={tier}, stripe_id={customer_id}")
    
    # TODO: Send welcome email with Telegram bot link
    # telegram_link = f"https://t.me/RivetCEO_bot?start={user.id}"
    # await send_welcome_email(customer_email, telegram_link, tier)


async def handle_subscription_updated(subscription: dict):
    """Handle subscription update (tier change, renewal, etc.)."""
    customer_id = subscription.get("customer")
    status = subscription.get("status")
    
    # Get the price ID to determine tier
    items = subscription.get("items", {}).get("data", [])
    if items:
        price_id = items[0].get("price", {}).get("id")
        new_tier = PRICE_TO_TIER.get(price_id, "unknown")
    else:
        new_tier = "unknown"
    
    logger.info(f"Subscription updated: customer={customer_id}, status={status}, tier={new_tier}")
    
    # TODO: Update user's tier in database
    # await update_user_tier(customer_id, new_tier)


async def handle_subscription_deleted(subscription: dict):
    """Handle subscription cancellation."""
    customer_id = subscription.get("customer")
    
    logger.info(f"Subscription deleted: customer={customer_id}")
    
    # TODO: Downgrade user to free tier or deactivate
    # await downgrade_user(customer_id)


async def handle_payment_failed(invoice: dict):
    """Handle failed payment."""
    customer_id = invoice.get("customer")
    customer_email = invoice.get("customer_email")
    amount_due = invoice.get("amount_due", 0) / 100  # Convert cents to dollars
    
    logger.warning(f"Payment failed: customer={customer_id}, email={customer_email}, amount=${amount_due}")
    
    # TODO: Notify user via email and/or Telegram
    # await notify_payment_failed(customer_email, amount_due)


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@router.get("/checkout/success")
async def checkout_success(session_id: str):
    """
    Handle successful checkout redirect.
    
    Retrieve session details and return user info.
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        return {
            "status": "success",
            "email": session.customer_email,
            "tier": session.metadata.get("tier"),
            "telegram_link": f"https://t.me/RivetCEO_bot?start=new",
            "next_steps": [
                "Open Telegram",
                "Search for @RivetCEO_bot",
                "Send /start to begin"
            ]
        }
    except stripe.error.StripeError as e:
        raise HTTPException(400, f"Could not retrieve session: {str(e)}")


@router.post("/billing/portal")
async def create_billing_portal(customer_id: str):
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
            customer=customer_id,
            return_url=f"{settings.app_url}/account"
        )
        return {"portal_url": session.url}
    except stripe.error.StripeError as e:
        raise HTTPException(400, f"Could not create portal: {str(e)}")
```

---

### `/agent_factory/api/routers/__init__.py`

```python
"""API Routers."""
from agent_factory.api.routers.stripe import router as stripe_router
from agent_factory.api.routers.users import router as users_router
from agent_factory.api.routers.work_orders import router as work_orders_router

__all__ = ["stripe_router", "users_router", "work_orders_router"]
```

---

## Run the API

```bash
# Development (with auto-reload)
uvicorn agent_factory.api.main:app --reload --port 8000

# Production
uvicorn agent_factory.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**API Docs:** http://localhost:8000/docs

---

## Test Stripe Integration

### 1. Test Checkout (curl)

```bash
curl -X POST http://localhost:8000/api/checkout/create \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "tier": "pro"
  }'
```

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_xxx",
  "session_id": "cs_test_xxx"
}
```

### 2. Test Webhook Locally

Use Stripe CLI to forward webhooks:

```bash
# Install Stripe CLI: https://stripe.com/docs/stripe-cli
stripe login

# Forward webhooks to local server
stripe listen --forward-to localhost:8000/api/webhooks/stripe

# Note the webhook signing secret it prints (whsec_xxx)
# Use this as STRIPE_WEBHOOK_SECRET for local testing
```

### 3. Test Cards

| Number | Description |
|--------|-------------|
| `4242424242424242` | Succeeds |
| `4000000000000002` | Declined |
| `4000002500003155` | Requires authentication |

---

## Production Checklist

- [ ] Switch to live Stripe keys (`sk_live_xxx`, `pk_live_xxx`)
- [ ] Update webhook endpoint URL in Stripe Dashboard
- [ ] Update `STRIPE_WEBHOOK_SECRET` with live webhook secret
- [ ] Enable HTTPS (required for Stripe)
- [ ] Set up proper logging/monitoring
- [ ] Test full checkout flow with real card
- [ ] Configure Stripe email receipts
- [ ] Set up tax collection if needed (Stripe Tax)

---

## Stripe Dashboard Links

- **API Keys:** https://dashboard.stripe.com/apikeys
- **Products:** https://dashboard.stripe.com/products
- **Webhooks:** https://dashboard.stripe.com/webhooks
- **Test Mode Toggle:** Top-right of dashboard
- **Customers:** https://dashboard.stripe.com/customers
- **Subscriptions:** https://dashboard.stripe.com/subscriptions

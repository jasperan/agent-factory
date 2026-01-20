"""
Stripe Integration for RIVET Pro Payments

Handles:
- Subscription management (Pro, Enterprise)
- One-time payments (Expert calls)
- Stripe Connect (Expert payouts)
- Webhooks (payment events)

Security:
- Uses Stripe API v2023-10-16
- Validates webhook signatures
- Stores only last 4 digits of payment methods

Example:
    >>> from agent_factory.rivet_pro.stripe_integration import StripeManager
    >>> manager = StripeManager()
    >>> checkout_url = manager.create_subscription_checkout(
    ...     user_id="123",
    ...     tier="pro",
    ...     success_url="https://t.me/rivetprobot"
    ... )
"""

import os
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class StripeManager:
    """
    Manages Stripe payment processing for RIVET Pro.

    Handles subscriptions, one-time payments, and expert payouts.
    """

    # Price IDs (set in Stripe Dashboard)
    PRICE_IDS = {
        "pro_monthly": os.getenv("STRIPE_PRICE_PRO_MONTHLY", "price_xxx"),
        "enterprise_monthly": os.getenv("STRIPE_PRICE_ENTERPRISE_MONTHLY", "price_yyy"),
    }

    # Pricing
    PRO_PRICE = 29.00
    ENTERPRISE_PRICE = 499.00
    EXPERT_CALL_BASE_PRICE = 75.00

    # Platform fees
    PLATFORM_FEE_PERCENT = 0.30  # 30% platform fee on expert calls

    def __init__(self, test_mode: bool = True):
        """
        Initialize Stripe manager.

        Args:
            test_mode: Use Stripe test mode keys (default: True)
        """
        self.test_mode = test_mode

        # Set API key
        if test_mode:
            self.api_key = os.getenv("STRIPE_TEST_SECRET_KEY", "")
            self.publishable_key = os.getenv("STRIPE_TEST_PUBLISHABLE_KEY", "")
        else:
            self.api_key = os.getenv("STRIPE_SECRET_KEY", "")
            self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

        if not self.api_key:
            raise ValueError("Stripe API key not configured")

        if STRIPE_AVAILABLE:
            stripe.api_key = self.api_key
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # =========================================================================
    # Subscription Management
    # =========================================================================

    def create_subscription_checkout(
        self,
        user_id: str,
        telegram_user_id: int,
        tier: str,
        success_url: str,
        cancel_url: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Create Stripe Checkout session for subscription signup.

        Args:
            user_id: Internal user ID
            telegram_user_id: Telegram user ID
            tier: Subscription tier (pro, enterprise)
            success_url: Redirect URL after successful payment
            cancel_url: Redirect URL if user cancels

        Returns:
            {
                "checkout_url": "https://checkout.stripe.com/...",
                "session_id": "cs_xxx"
            }
        """
        if tier not in ["pro", "enterprise"]:
            raise ValueError(f"Invalid tier: {tier}")

        # Get price ID
        price_id = self.PRICE_IDS.get(f"{tier}_monthly")
        if not price_id or price_id.startswith("price_xxx"):
            raise ValueError(f"Price ID not configured for tier: {tier}")

        # Create or get Stripe customer
        customer = self._get_or_create_customer(user_id, telegram_user_id)

        # Create checkout session
        try:
            session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=cancel_url or success_url,
                metadata={
                    "user_id": user_id,
                    "telegram_user_id": str(telegram_user_id),
                    "tier": tier,
                },
                subscription_data={
                    "metadata": {
                        "user_id": user_id,
                        "tier": tier,
                    }
                },
                allow_promotion_codes=True,  # Allow discount codes
            )

            return {
                "checkout_url": session.url,
                "session_id": session.id,
            }

        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {e.user_message}")

    def create_billing_portal_session(
        self,
        user_id: str,
        return_url: str,
    ) -> str:
        """
        Create Stripe billing portal session for managing subscription.

        Allows users to:
        - Update payment method
        - Cancel subscription
        - View invoices

        Args:
            user_id: Internal user ID
            return_url: URL to return to after portal

        Returns:
            Portal URL
        """
        customer = self._get_customer(user_id)

        if not customer:
            raise Exception("Customer not found")

        try:
            session = stripe.billing_portal.Session.create(
                customer=customer.id,
                return_url=return_url,
            )

            return session.url

        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {e.user_message}")

    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Cancel subscription immediately.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Cancelled subscription object
        """
        try:
            subscription = stripe.Subscription.delete(subscription_id)
            return {
                "id": subscription.id,
                "status": subscription.status,
                "cancelled_at": subscription.canceled_at,
            }

        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {e.user_message}")

    # =========================================================================
    # One-Time Payments (Expert Calls)
    # =========================================================================

    def create_expert_call_payment(
        self,
        user_id: str,
        telegram_user_id: int,
        expert_id: str,
        expert_name: str,
        duration_minutes: int,
        hourly_rate: float,
        success_url: str,
        cancel_url: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Create payment for expert call booking.

        Args:
            user_id: User ID
            telegram_user_id: Telegram user ID
            expert_id: Expert ID
            expert_name: Expert name
            duration_minutes: Call duration
            hourly_rate: Expert's hourly rate
            success_url: Success redirect URL
            cancel_url: Cancel redirect URL

        Returns:
            {
                "checkout_url": "...",
                "session_id": "...",
                "total_price": 75.00,
                "expert_payout": 52.50,
                "platform_fee": 22.50
            }
        """
        # Calculate pricing
        call_price = (duration_minutes / 60.0) * hourly_rate
        platform_fee = call_price * self.PLATFORM_FEE_PERCENT
        expert_payout = call_price - platform_fee

        # Create or get customer
        customer = self._get_or_create_customer(user_id, telegram_user_id)

        # Create checkout session
        try:
            session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": f"Expert Call: {expert_name}",
                                "description": f"{duration_minutes} minute troubleshooting session",
                            },
                            "unit_amount": int(call_price * 100),  # Cents
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=cancel_url or success_url,
                metadata={
                    "user_id": user_id,
                    "telegram_user_id": str(telegram_user_id),
                    "expert_id": expert_id,
                    "duration_minutes": str(duration_minutes),
                    "hourly_rate": str(hourly_rate),
                    "platform_fee": str(platform_fee),
                    "expert_payout": str(expert_payout),
                },
            )

            return {
                "checkout_url": session.url,
                "session_id": session.id,
                "total_price": call_price,
                "expert_payout": expert_payout,
                "platform_fee": platform_fee,
            }

        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {e.user_message}")

    # =========================================================================
    # Expert Payouts (Stripe Connect)
    # =========================================================================

    def create_expert_connect_account(
        self,
        expert_id: str,
        email: str,
        name: str,
    ) -> Dict[str, Any]:
        """
        Create Stripe Connect account for expert.

        Args:
            expert_id: Internal expert ID
            email: Expert email
            name: Expert name

        Returns:
            {
                "account_id": "acct_xxx",
                "onboarding_url": "https://connect.stripe.com/..."
            }
        """
        try:
            account = stripe.Account.create(
                type="express",
                country="US",
                email=email,
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
                business_type="individual",
                metadata={
                    "expert_id": expert_id,
                },
            )

            # Create onboarding link
            account_link = stripe.AccountLink.create(
                account=account.id,
                refresh_url="https://rivetpro.com/expert/onboarding/refresh",
                return_url="https://rivetpro.com/expert/onboarding/complete",
                type="account_onboarding",
            )

            return {
                "account_id": account.id,
                "onboarding_url": account_link.url,
            }

        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {e.user_message}")

    def transfer_to_expert(
        self,
        expert_connect_account_id: str,
        amount_usd: float,
        description: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Transfer funds to expert's Stripe Connect account.

        Args:
            expert_connect_account_id: Stripe Connect account ID
            amount_usd: Amount to transfer (USD)
            description: Transfer description
            metadata: Optional metadata

        Returns:
            {
                "transfer_id": "tr_xxx",
                "amount": 52.50,
                "status": "paid"
            }
        """
        try:
            transfer = stripe.Transfer.create(
                amount=int(amount_usd * 100),  # Cents
                currency="usd",
                destination=expert_connect_account_id,
                description=description,
                metadata=metadata or {},
            )

            return {
                "transfer_id": transfer.id,
                "amount": transfer.amount / 100.0,
                "status": transfer.status,
            }

        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {e.user_message}")

    # =========================================================================
    # Webhooks
    # =========================================================================

    def verify_webhook_signature(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """
        Verify and parse Stripe webhook event.

        Args:
            payload: Request body (bytes)
            sig_header: Stripe-Signature header

        Returns:
            Parsed event object

        Raises:
            ValueError: If signature verification fails
        """
        if not self.webhook_secret:
            raise ValueError("Webhook secret not configured")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            return event

        except ValueError as e:
            raise ValueError(f"Invalid payload: {e}")
        except stripe.error.SignatureVerificationError as e:
            raise ValueError(f"Invalid signature: {e}")

    def handle_webhook_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Stripe webhook event.

        Args:
            event: Verified webhook event

        Returns:
            Action to take based on event type
        """
        event_type = event["type"]
        data = event["data"]["object"]

        # Subscription events
        if event_type == "customer.subscription.created":
            return self._handle_subscription_created(data)
        elif event_type == "customer.subscription.updated":
            return self._handle_subscription_updated(data)
        elif event_type == "customer.subscription.deleted":
            return self._handle_subscription_deleted(data)

        # Payment events
        elif event_type == "checkout.session.completed":
            return self._handle_checkout_completed(data)
        elif event_type == "payment_intent.succeeded":
            return self._handle_payment_succeeded(data)
        elif event_type == "payment_intent.payment_failed":
            return self._handle_payment_failed(data)

        # Refund events
        elif event_type == "charge.refunded":
            return self._handle_refund(data)

        else:
            return {"action": "ignore", "event_type": event_type}

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _get_or_create_customer(self, user_id: str, telegram_user_id: int) -> stripe.Customer:
        """Get or create Stripe customer"""
        # Search for existing customer
        customers = stripe.Customer.list(
            limit=1,
            email=f"{telegram_user_id}@telegram.rivetpro.internal"
        )

        if customers.data:
            return customers.data[0]

        # Create new customer
        customer = stripe.Customer.create(
            email=f"{telegram_user_id}@telegram.rivetpro.internal",
            metadata={
                "user_id": user_id,
                "telegram_user_id": str(telegram_user_id),
            },
        )

        return customer

    def _get_customer(self, user_id: str) -> Optional[stripe.Customer]:
        """Get Stripe customer by user ID"""
        customers = stripe.Customer.search(
            query=f"metadata['user_id']:'{user_id}'"
        )

        if customers.data:
            return customers.data[0]

        return None

    def _handle_subscription_created(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription created event"""
        user_id = subscription.get("metadata", {}).get("user_id")
        tier = subscription.get("metadata", {}).get("tier")

        return {
            "action": "activate_subscription",
            "user_id": user_id,
            "tier": tier,
            "subscription_id": subscription["id"],
            "current_period_end": subscription["current_period_end"],
        }

    def _handle_subscription_updated(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription updated event"""
        return {
            "action": "update_subscription",
            "subscription_id": subscription["id"],
            "status": subscription["status"],
        }

    def _handle_subscription_deleted(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription deleted/cancelled event"""
        user_id = subscription.get("metadata", {}).get("user_id")

        return {
            "action": "cancel_subscription",
            "user_id": user_id,
            "subscription_id": subscription["id"],
        }

    def _handle_checkout_completed(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle checkout session completed"""
        mode = session.get("mode")
        metadata = session.get("metadata", {})

        if mode == "subscription":
            return {
                "action": "subscription_checkout_completed",
                "user_id": metadata.get("user_id"),
                "session_id": session["id"],
            }
        elif mode == "payment":
            return {
                "action": "payment_checkout_completed",
                "user_id": metadata.get("user_id"),
                "expert_id": metadata.get("expert_id"),
                "session_id": session["id"],
            }

        return {"action": "ignore"}

    def _handle_payment_succeeded(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment"""
        return {
            "action": "payment_succeeded",
            "payment_intent_id": payment_intent["id"],
            "amount": payment_intent["amount"] / 100.0,
        }

    def _handle_payment_failed(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment"""
        return {
            "action": "payment_failed",
            "payment_intent_id": payment_intent["id"],
            "failure_message": payment_intent.get("last_payment_error", {}).get("message"),
        }

    def _handle_refund(self, charge: Dict[str, Any]) -> Dict[str, Any]:
        """Handle refund"""
        return {
            "action": "refund_issued",
            "charge_id": charge["id"],
            "amount_refunded": charge["amount_refunded"] / 100.0,
        }


# Example usage
if __name__ == "__main__":
    # Initialize manager (test mode)
    manager = StripeManager(test_mode=True)

    # Create subscription checkout
    print("Creating Pro subscription checkout...")
    result = manager.create_subscription_checkout(
        user_id="test_user_123",
        telegram_user_id=123456789,
        tier="pro",
        success_url="https://t.me/rivetprobot?start=success",
        cancel_url="https://t.me/rivetprobot?start=cancel",
    )
    print(f"Checkout URL: {result['checkout_url']}")
    print(f"Session ID: {result['session_id']}")

    # Create expert call payment
    print("\nCreating expert call payment...")
    call_result = manager.create_expert_call_payment(
        user_id="test_user_123",
        telegram_user_id=123456789,
        expert_id="expert_001",
        expert_name="Mike Thompson",
        duration_minutes=60,
        hourly_rate=75.00,
        success_url="https://t.me/rivetprobot?start=booking_success",
    )
    print(f"Call Price: ${call_result['total_price']:.2f}")
    print(f"Expert Payout: ${call_result['expert_payout']:.2f}")
    print(f"Platform Fee: ${call_result['platform_fee']:.2f}")
    print(f"Checkout URL: {call_result['checkout_url']}")

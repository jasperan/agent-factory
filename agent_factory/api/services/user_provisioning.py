"""User provisioning service for Stripe webhook handlers.

This service handles user creation, tier updates, and downgrades based on Stripe events.
Designed to be idempotent and handle race conditions gracefully.
"""
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


async def provision_user_internal(
    email: str,
    stripe_customer_id: str,
    subscription_tier: str,
    stripe_subscription_id: Optional[str] = None,
    current_period_end: Optional[datetime] = None
):
    """
    Provision or update user after successful checkout.

    Idempotent: Safe to call multiple times with same data.

    Args:
        email: Customer email address
        stripe_customer_id: Stripe customer ID
        subscription_tier: Tier ('beta', 'pro', 'team')
        stripe_subscription_id: Stripe subscription ID (if applicable)
        current_period_end: Subscription end date (if applicable)

    Returns:
        User object (mocked until database integration complete)
    """
    print_limit = 5 if subscription_tier == 'beta' else -1  # -1 = unlimited

    logger.info(
        f"Provisioning user: email={email}, tier={subscription_tier}, "
        f"stripe_id={stripe_customer_id}, print_limit={print_limit}"
    )

    # TODO: Database integration (Phase 7 completion)
    # from agent_factory.database.session import get_db_session
    # from agent_factory.database.models import RivetUser, RivetSubscription
    # from sqlalchemy.dialects.postgresql import insert
    #
    # async with get_db_session() as session:
    #     # Upsert user
    #     stmt = insert(RivetUser).values(
    #         email=email,
    #         stripe_customer_id=stripe_customer_id,
    #         subscription_tier=subscription_tier,
    #         monthly_print_limit=print_limit
    #     ).on_conflict_do_update(
    #         index_elements=['email'],
    #         set_={
    #             'stripe_customer_id': stripe_customer_id,
    #             'subscription_tier': subscription_tier,
    #             'monthly_print_limit': print_limit,
    #             'updated_at': datetime.utcnow()
    #         }
    #     ).returning(RivetUser)
    #
    #     result = await session.execute(stmt)
    #     user = result.scalar_one()
    #
    #     # If paid tier, create subscription record
    #     if stripe_subscription_id and subscription_tier != 'beta':
    #         sub_stmt = insert(RivetSubscription).values(
    #             user_id=user.id,
    #             stripe_subscription_id=stripe_subscription_id,
    #             stripe_customer_id=stripe_customer_id,
    #             tier=subscription_tier,
    #             status='active',
    #             current_period_end=current_period_end
    #         ).on_conflict_do_update(
    #             index_elements=['stripe_subscription_id'],
    #             set_={'status': 'active', 'updated_at': datetime.utcnow()}
    #         )
    #         await session.execute(sub_stmt)
    #
    #     await session.commit()
    #     logger.info(f"User provisioned: {email} ({subscription_tier})")
    #     return user

    # Placeholder return (until database integration)
    logger.info(f"[MOCK] User provisioned: {email} ({subscription_tier})")
    return {
        'email': email,
        'subscription_tier': subscription_tier,
        'telegram_id': None,  # Not linked yet
        'monthly_print_limit': print_limit
    }


async def update_user_tier(stripe_customer_id: str, new_tier: str):
    """
    Update user's subscription tier.

    Args:
        stripe_customer_id: Stripe customer ID
        new_tier: New subscription tier ('beta', 'pro', 'team')
    """
    print_limit = 5 if new_tier == 'beta' else -1

    logger.info(f"Updating tier: customer={stripe_customer_id} → {new_tier}")

    # TODO: Database integration (Phase 7 completion)
    # from agent_factory.database.session import get_db_session
    # from agent_factory.database.models import RivetUser
    # from sqlalchemy import update
    #
    # async with get_db_session() as session:
    #     stmt = update(RivetUser).where(
    #         RivetUser.stripe_customer_id == stripe_customer_id
    #     ).values(
    #         subscription_tier=new_tier,
    #         monthly_print_limit=print_limit,
    #         updated_at=datetime.utcnow()
    #     )
    #     await session.execute(stmt)
    #     await session.commit()

    logger.info(f"[MOCK] Tier updated: {stripe_customer_id} → {new_tier}")


async def downgrade_user(stripe_customer_id: str):
    """
    Downgrade user to beta tier on subscription cancellation.

    Args:
        stripe_customer_id: Stripe customer ID
    """
    logger.info(f"Downgrading user: customer={stripe_customer_id} → beta")
    await update_user_tier(stripe_customer_id, 'beta')

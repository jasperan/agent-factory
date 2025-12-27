"""Telegram bot notification service.

Sends lifecycle notifications to users via Telegram bot:
- Welcome messages on successful payment
- Payment failure alerts
- Subscription cancellation notices
"""
import logging
import httpx
from agent_factory.api.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def send_telegram_welcome(telegram_id: int, tier: str):
    """
    Send welcome message to user after successful payment.

    Args:
        telegram_id: Telegram user ID (chat_id)
        tier: Subscription tier ('pro', 'team')
    """
    if not telegram_id:
        logger.warning("Cannot send Telegram welcome: telegram_id is null")
        return

    messages = {
        'pro': "🎉 Welcome to Rivet Pro! You now have unlimited print uploads and priority support.",
        'team': "🎉 Welcome to Rivet Team! Your team account is active with admin dashboard access."
    }

    message = messages.get(tier, "🎉 Welcome to Rivet!")

    # Check if telegram bot token is configured
    if not hasattr(settings, 'telegram_bot_token') or not settings.telegram_bot_token:
        logger.warning(f"Telegram bot token not configured, skipping welcome message to {telegram_id}")
        logger.info(f"[MOCK] Would send Telegram welcome to {telegram_id}: {message}")
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                json={'chat_id': telegram_id, 'text': message},
                timeout=10.0
            )
            response.raise_for_status()
        logger.info(f"Sent Telegram welcome to {telegram_id} ({tier})")
    except Exception as e:
        logger.error(f"Failed to send Telegram welcome: {e}")


async def notify_payment_failed(telegram_id: int, email: str, amount: float, attempt: int):
    """
    Notify user of failed payment.

    Args:
        telegram_id: Telegram user ID (chat_id)
        email: User email (fallback for logging)
        amount: Payment amount in dollars
        attempt: Payment attempt number
    """
    if not telegram_id:
        # Fallback to email notification (future implementation)
        logger.warning(f"Payment failed for {email}, but no telegram_id to notify")
        return

    message = (
        f"⚠️ Payment Failed\n\n"
        f"Amount: ${amount:.2f}\n"
        f"Attempt: {attempt}\n\n"
        f"Please update your payment method to avoid service interruption."
    )

    # Check if telegram bot token is configured
    if not hasattr(settings, 'telegram_bot_token') or not settings.telegram_bot_token:
        logger.warning(f"Telegram bot token not configured, skipping payment failure notification to {telegram_id}")
        logger.info(f"[MOCK] Would send payment failure notification to {telegram_id}: {message}")
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                json={'chat_id': telegram_id, 'text': message},
                timeout=10.0
            )
            response.raise_for_status()
        logger.info(f"Sent payment failure notification to {telegram_id}")
    except Exception as e:
        logger.error(f"Failed to send payment failure notification: {e}")


async def notify_subscription_canceled(telegram_id: int, tier: str, cancel_at_period_end: bool = True):
    """
    Notify user of subscription cancellation.

    Args:
        telegram_id: Telegram user ID (chat_id)
        tier: Subscription tier that was canceled
        cancel_at_period_end: If True, access continues until period end
    """
    if not telegram_id:
        logger.warning("Cannot send cancellation notice: telegram_id is null")
        return

    if cancel_at_period_end:
        message = (
            f"📋 Subscription Canceled\n\n"
            f"Your {tier.capitalize()} subscription has been canceled.\n"
            f"You'll continue to have access until the end of your billing period.\n\n"
            f"We're sad to see you go! Feel free to reactivate anytime."
        )
    else:
        message = (
            f"📋 Subscription Canceled\n\n"
            f"Your {tier.capitalize()} subscription has been canceled immediately.\n"
            f"You've been downgraded to the Beta tier.\n\n"
            f"We're sad to see you go! Feel free to reactivate anytime."
        )

    # Check if telegram bot token is configured
    if not hasattr(settings, 'telegram_bot_token') or not settings.telegram_bot_token:
        logger.warning(f"Telegram bot token not configured, skipping cancellation notice to {telegram_id}")
        logger.info(f"[MOCK] Would send cancellation notice to {telegram_id}: {message}")
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                json={'chat_id': telegram_id, 'text': message},
                timeout=10.0
            )
            response.raise_for_status()
        logger.info(f"Sent subscription canceled notification to {telegram_id}")
    except Exception as e:
        logger.error(f"Failed to send cancellation notification: {e}")

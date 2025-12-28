"""
RIVET Pro Telegram Onboarding Manager

Manages tier-aware, multi-step onboarding flow with:
- API key authentication from landing page
- Tier-specific feature tours (Beta/Pro/Enterprise)
- Interactive tutorials with inline buttons
- Resumable progress tracking
- Skip functionality

Created: 2025-12-27
Phase: Telegram Onboarding (Phase 2/6)
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from agent_factory.rivet_pro.database import RIVETProDatabase
from agent_factory.integrations.telegram.api_client import RivetAPIClient


class OnboardingManager:
    """
    Manages multi-step Telegram onboarding flow.

    Features:
    - API key authentication (/start <api_key>)
    - Tier-aware welcome messages (Beta/Pro/Enterprise)
    - 5-step interactive tutorial (~4 minutes)
    - Resumable progress tracking
    - Skip option at any step

    Onboarding Steps:
    1. Welcome + Tier Explanation (30 sec)
    2. Feature Tour - Interactive buttons (1 min)
    3. First Troubleshooting - Hands-on example (1 min)
    4. Machine Library Tutorial (1 min)
    5. Completion + Quick Reference (30 sec)
    """

    def __init__(self, db: Optional[RIVETProDatabase] = None):
        """Initialize onboarding manager"""
        self.db = db or RIVETProDatabase()
        self.api_client = RivetAPIClient()

        # Backend API URL for user lookup
        self.backend_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")

    async def start_onboarding(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_data: Dict[str, Any]
    ):
        """
        Entry point: Determine if new user or returning user.

        Args:
            update: Telegram update object
            context: Bot context
            user_data: User subscription data from database
        """
        telegram_id = str(update.effective_user.id)

        # Check onboarding status
        onboarding_completed = user_data.get("onboarding_completed", False)
        onboarding_skipped = user_data.get("onboarding_skipped", False)
        onboarding_step = user_data.get("onboarding_step", 0)

        # Returning user who completed onboarding
        if onboarding_completed and not onboarding_skipped:
            return await self.show_welcome_back(update, user_data)

        # Returning user who skipped onboarding
        if onboarding_skipped:
            return await self.show_welcome_back_skipped(update, user_data)

        # Resuming partial onboarding
        if onboarding_step > 0:
            return await self.resume_onboarding(update, context, user_data, onboarding_step)

        # New user - start from Step 1
        return await self.begin_step_1(update, context, user_data)

    async def authenticate_with_api_key(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        api_key: str
    ):
        """
        Authenticate user with API key from landing page.

        Flow:
        1. Validate API key against backend (/api/users/by-api-key)
        2. Get user profile (email, tier, etc.)
        3. Link telegram_user_id to user account
        4. Start onboarding if not completed

        Args:
            update: Telegram update object
            context: Bot context
            api_key: API key from /start command
        """
        telegram_id = str(update.effective_user.id)

        # Validate API key via backend
        try:
            user_profile = await self.api_client.validate_api_key(api_key)
        except Exception as e:
            await update.message.reply_text(
                "❌ **Invalid API Key**\n\n"
                "Please check your API key and try again.\n"
                "Get your API key from: https://landing-zeta-plum.vercel.app\n\n"
                f"Error: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        if not user_profile:
            await update.message.reply_text(
                "❌ **Invalid API Key**\n\n"
                "Please check your API key and try again.\n"
                "Get your API key from: https://landing-zeta-plum.vercel.app",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Link Telegram ID to user account
        await self.db.link_telegram_id(
            user_id=user_profile["user_id"],
            telegram_id=telegram_id
        )

        # Store in session context
        context.user_data['user_id'] = user_profile["user_id"]
        context.user_data['api_key'] = api_key
        context.user_data['tier'] = user_profile.get("subscription_tier", "beta")
        context.user_data['email'] = user_profile.get("email")

        # Get full user data from database
        user_data = await self.db.get_user_by_telegram_id(telegram_id)

        # Start onboarding
        await update.message.reply_text(
            f"✅ **Authenticated Successfully!**\n\n"
            f"Welcome, {user_profile.get('email', 'User')}!\n"
            f"Your plan: **{user_profile.get('subscription_tier', 'beta').upper()}**",
            parse_mode=ParseMode.MARKDOWN
        )

        return await self.start_onboarding(update, context, user_data)

    async def begin_step_1(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_data: Dict[str, Any]
    ):
        """
        Step 1: Welcome + Tier Explanation (30 sec)

        Shows tier-specific welcome message and onboarding options.
        """
        tier = user_data.get("subscription_tier", "beta")
        telegram_id = str(update.effective_user.id)

        # Get tier-specific welcome message
        message = self.get_tier_welcome_message(tier)

        # Build inline keyboard
        keyboard = self.get_step_1_keyboard()

        # Send welcome message
        await update.message.reply_text(
            text=message,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

        # Update onboarding step in database
        await self.update_onboarding_step(telegram_id, step=1)

    async def begin_step_2(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_data: Dict[str, Any]
    ):
        """
        Step 2: Feature Tour - Interactive buttons (1 min)

        Shows interactive feature tour with tier-specific features.
        This will be handled by FeatureTour module (Phase 3).
        """
        telegram_id = str(update.effective_user.id)

        # Placeholder for now - will integrate with FeatureTour module
        message = (
            "📖 **Feature Tour**\n\n"
            "Let's explore what RIVET can do for you!\n\n"
            "Click on any feature below to learn more:"
        )

        tier = user_data.get("subscription_tier", "beta")
        keyboard = self.get_feature_tour_keyboard(tier)

        # Edit message if callback query, otherwise send new
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                text=message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )

        # Update step
        await self.update_onboarding_step(telegram_id, step=2)

    async def begin_step_3(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_data: Dict[str, Any]
    ):
        """
        Step 3: First Troubleshooting - Hands-on example (1 min)

        User asks a sample question and gets an answer.
        """
        telegram_id = str(update.effective_user.id)

        message = (
            "🔧 **Try Your First Question!**\n\n"
            "Let's do a quick hands-on test. Try asking me a troubleshooting question.\n\n"
            "**Example questions:**\n"
            "• \"Motor running hot and tripping\"\n"
            "• \"VFD showing E210 fault\"\n"
            "• \"How do I troubleshoot a PLC?\"\n\n"
            "Go ahead, ask me anything! 👇"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⏭️ Skip This Step", callback_data="onboard_step_4")]
        ])

        # Edit or send message
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                text=message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )

        # Update step
        await self.update_onboarding_step(telegram_id, step=3)

        # Set flag in context to know we're waiting for first question
        context.user_data['awaiting_first_question'] = True

    async def begin_step_4(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_data: Dict[str, Any]
    ):
        """
        Step 4: Machine Library Tutorial (1 min)

        Shows how to add equipment to personal library.
        """
        telegram_id = str(update.effective_user.id)

        message = (
            "📚 **Machine Library**\n\n"
            "Keep track of your equipment for faster troubleshooting!\n\n"
            "**What you can do:**\n"
            "• Add machines to your personal library\n"
            "• Upload electrical schematics (prints)\n"
            "• Upload equipment manuals\n"
            "• Get instant answers about YOUR specific equipment\n\n"
            "**Commands:**\n"
            "• `/add_machine` - Add equipment to library\n"
            "• `/list_machines` - View your equipment\n"
            "• `/upload_print` - Upload electrical schematics\n"
            "• `/upload_manual` - Add manual to shared library\n\n"
            "Ready to finish onboarding?"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Finish Onboarding", callback_data="onboard_step_5")],
            [InlineKeyboardButton("⏭️ Skip", callback_data="onboard_step_5")]
        ])

        # Edit or send message
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                text=message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )

        # Update step
        await self.update_onboarding_step(telegram_id, step=4)

    async def begin_step_5(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_data: Dict[str, Any]
    ):
        """
        Step 5: Completion + Quick Reference (30 sec)

        Shows completion message and quick reference card.
        """
        telegram_id = str(update.effective_user.id)
        tier = user_data.get("subscription_tier", "beta")

        # Generate tier-specific quick reference
        from agent_factory.integrations.telegram.quick_reference import get_quickstart_message
        quick_ref = get_quickstart_message(tier)

        completion_message = (
            "🎉 **Onboarding Complete!**\n\n"
            "You're all set to start troubleshooting with RIVET!\n\n"
            f"{quick_ref}\n\n"
            "Need help? Use `/tutorial` to replay this onboarding anytime."
        )

        # Edit or send message
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=completion_message,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                text=completion_message,
                parse_mode=ParseMode.MARKDOWN
            )

        # Mark onboarding as complete
        await self.complete_onboarding(telegram_id)

    async def skip_onboarding(self, update: Update, user_data: Dict[str, Any]):
        """
        User clicked "Skip Tutorial" button.

        Shows quick reference and marks as skipped.
        """
        telegram_id = str(update.effective_user.id)
        tier = user_data.get("subscription_tier", "beta")

        from agent_factory.integrations.telegram.quick_reference import get_quickstart_message
        quick_ref = get_quickstart_message(tier)

        skip_message = (
            "⏭️ **Tutorial Skipped**\n\n"
            "No problem! Here's a quick reference card:\n\n"
            f"{quick_ref}\n\n"
            "Use `/tutorial` anytime to start the full onboarding."
        )

        await update.callback_query.edit_message_text(
            text=skip_message,
            parse_mode=ParseMode.MARKDOWN
        )

        # Mark as skipped in database
        await self.db.update_user(
            telegram_id=telegram_id,
            updates={
                "onboarding_skipped": True,
                "onboarding_step": 0,
                "onboarding_completed_at": datetime.utcnow()
            }
        )

    async def show_about(self, update: Update):
        """Show "What's RIVET?" explanation"""
        about_text = (
            "🤖 **What is RIVET?**\n\n"
            "RIVET is an AI-powered industrial troubleshooting assistant built for field technicians.\n\n"
            "**Our Knowledge Base:**\n"
            "• 1,964+ validated maintenance solutions\n"
            "• Covering VFDs, PLCs, motors, sensors, and more\n"
            "• Backed by official manuals and real-world experience\n\n"
            "**How It Works:**\n"
            "1. You ask a troubleshooting question\n"
            "2. RIVET analyzes your question and equipment\n"
            "3. We search our validated knowledge base\n"
            "4. You get an answer with citations and steps\n\n"
            "**Why Trust RIVET?**\n"
            "✅ All answers cite official documentation\n"
            "✅ Safety warnings included\n"
            "✅ Connect with expert technicians for complex issues\n\n"
            "Ready to get started?"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📖 Start Tutorial", callback_data="onboard_step_2")],
            [InlineKeyboardButton("⏭️ Skip Tutorial", callback_data="onboard_skip")]
        ])

        await update.callback_query.edit_message_text(
            text=about_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

    async def resume_onboarding(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_data: Dict[str, Any],
        step: int
    ):
        """Resume onboarding from saved step"""
        resume_message = (
            f"👋 **Welcome back!**\n\n"
            f"You left off at Step {step} of onboarding.\n"
            f"Would you like to continue where you left off?"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Continue", callback_data=f"onboard_step_{step}")],
            [InlineKeyboardButton("🔄 Restart", callback_data="onboard_step_1")],
            [InlineKeyboardButton("⏭️ Skip", callback_data="onboard_skip")]
        ])

        await update.message.reply_text(
            text=resume_message,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

    async def show_welcome_back(self, update: Update, user_data: Dict[str, Any]):
        """Show welcome back message for returning users"""
        tier = user_data.get("subscription_tier", "beta")

        welcome_back_text = (
            f"👋 **Welcome back to RIVET!**\n\n"
            f"Your plan: **{tier.upper()}**\n\n"
            "What would you like to do?\n\n"
            "• Ask a troubleshooting question\n"
            "• `/tutorial` - Replay onboarding\n"
            "• `/tour` - Explore features\n"
            "• `/help` - See all commands"
        )

        await update.message.reply_text(
            text=welcome_back_text,
            parse_mode=ParseMode.MARKDOWN
        )

    async def show_welcome_back_skipped(self, update: Update, user_data: Dict[str, Any]):
        """Show welcome back message for users who skipped onboarding"""
        tier = user_data.get("subscription_tier", "beta")

        from agent_factory.integrations.telegram.quick_reference import get_quickstart_message
        quick_ref = get_quickstart_message(tier)

        welcome_text = (
            f"👋 **Welcome back!**\n\n"
            f"{quick_ref}\n\n"
            "Use `/tutorial` to see the full onboarding."
        )

        await update.message.reply_text(
            text=welcome_text,
            parse_mode=ParseMode.MARKDOWN
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def get_tier_welcome_message(self, tier: str) -> str:
        """Return tier-specific welcome message"""
        # Check if beta mode is enabled
        beta_mode = os.getenv("BETA_MODE", "true").lower() == "true"
        beta_banner = ""
        if beta_mode:
            beta_banner = """🚀 **BETA ACCESS - UNLIMITED EVERYTHING!**

━━━━━━━━━━━━━━━━━━━━━━━
✨ No rate limits
✨ All Pro features unlocked
✨ Unlimited troubleshooting
✨ Unlimited equipment tracking
✨ Full manual library access
━━━━━━━━━━━━━━━━━━━━━━━

"""

        messages = {
            "beta": beta_banner + """🎉 **Welcome to RIVET Beta!**

You're one of our early users! Here's what you get:
✅ AI-powered troubleshooting (unlimited during beta!)
✅ Access to 1,964+ validated maintenance solutions
✅ Community knowledge base
✅ Equipment library tracking
✅ Manual library with vector search

Ready to get started? 🚀""",

            "pro": """🔥 **Welcome to RIVET Pro!**

You've unlocked premium features:
✅ UNLIMITED troubleshooting questions
✅ Field Eye (image analysis for equipment)
✅ PDF export of solutions
✅ Priority support (email + chat)
✅ Advanced search filters

Let's get you set up! 🛠️""",

            "team": """🏢 **Welcome to RIVET Enterprise!**

Your team has access to:
✅ Everything in Pro
✅ Up to 10 team members
✅ Shared equipment library
✅ Team work order management
✅ Admin dashboard
✅ Dedicated phone support

Let's configure your workspace! 📊"""
        }
        return messages.get(tier, messages["beta"])

    def get_step_1_keyboard(self) -> InlineKeyboardMarkup:
        """Inline keyboard for Step 1"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📖 Start Tutorial", callback_data="onboard_step_2")],
            [InlineKeyboardButton("⏭️ Skip Tutorial", callback_data="onboard_skip")],
            [InlineKeyboardButton("❓ What's RIVET?", callback_data="onboard_about")]
        ])

    def get_feature_tour_keyboard(self, tier: str) -> InlineKeyboardMarkup:
        """Build keyboard based on user's tier"""
        buttons = [
            [InlineKeyboardButton("🔧 Troubleshooting", callback_data="tour_troubleshooting")],
            [InlineKeyboardButton("📚 Machine Library", callback_data="tour_machine_lib")],
        ]

        if tier in ["pro", "team"]:
            buttons.append([InlineKeyboardButton("📷 Field Eye", callback_data="tour_field_eye")])
            buttons.append([InlineKeyboardButton("📄 PDF Export", callback_data="tour_pdf_export")])

        if tier == "team":
            buttons.append([InlineKeyboardButton("👥 Team Management", callback_data="tour_team_mgmt")])

        buttons.append([InlineKeyboardButton("➡️ Next Step", callback_data="onboard_step_3")])

        return InlineKeyboardMarkup(buttons)

    async def update_onboarding_step(self, telegram_id: str, step: int):
        """Update user's onboarding progress in database"""
        await self.db.update_user(
            telegram_id=telegram_id,
            updates={"onboarding_step": step}
        )

    async def complete_onboarding(self, telegram_id: str):
        """Mark onboarding as complete"""
        await self.db.update_user(
            telegram_id=telegram_id,
            updates={
                "onboarding_completed": True,
                "onboarding_step": 5,
                "onboarding_completed_at": datetime.utcnow()
            }
        )

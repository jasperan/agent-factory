"""
RIVET Pro Feature Tour Module

Interactive feature tour with tier-specific content.
Shows users what RIVET can do based on their subscription level.

Created: 2025-12-27
Phase: Telegram Onboarding (Phase 2/6)
"""

from typing import Optional, Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode


class FeatureTour:
    """
    Interactive feature tour with inline buttons.

    Shows tier-specific features:
    - Beta: Basic troubleshooting, machine library
    - Pro: + Field Eye, PDF export, priority support
    - Team: + Team management, shared library, admin dashboard
    """

    async def show_tour_menu(
        self,
        update: Update,
        user_data: Dict
    ):
        """
        Show main tour menu with all features.

        User can select which feature to learn about.
        """
        tier = user_data.get("subscription_tier", "beta")

        message = f"""🎓 **RIVET Feature Tour**

Your plan: **{tier.upper()}**

Choose a feature to learn about:"""

        keyboard = self.get_tour_keyboard(tier)

        # Edit if callback query, send if message
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )

    def get_tour_keyboard(self, tier: str) -> InlineKeyboardMarkup:
        """Build keyboard based on user's tier"""
        buttons = [
            [InlineKeyboardButton("🔧 Troubleshooting", callback_data="tour_troubleshooting")],
            [InlineKeyboardButton("📚 Machine Library", callback_data="tour_machine_lib")],
        ]

        if tier in ["pro", "team"]:
            buttons.append([InlineKeyboardButton("📷 Field Eye (Image Analysis)", callback_data="tour_field_eye")])
            buttons.append([InlineKeyboardButton("📄 PDF Export", callback_data="tour_pdf_export")])

        if tier == "team":
            buttons.append([InlineKeyboardButton("👥 Team Management", callback_data="tour_team_mgmt")])

        buttons.append([InlineKeyboardButton("✅ Finish Tour", callback_data="tour_complete")])

        return InlineKeyboardMarkup(buttons)

    async def show_troubleshooting_tour(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Explain troubleshooting workflow"""
        message = """🔧 **Troubleshooting Workflow**

Ask me any equipment question, and I'll:

1️⃣ **Analyze your question**
   - Equipment type (VFD, PLC, motor, etc.)
   - Fault codes
   - Symptoms

2️⃣ **Search 1,964+ solutions**
   - Validated maintenance atoms
   - Official manuals
   - Real-world experience

3️⃣ **Provide answer with:**
   - Step-by-step troubleshooting
   - Safety warnings
   - Manual citations (page numbers!)

**Try it now!**
Ask "PowerFlex 525 showing F004"

Or click "Next Feature" to continue the tour."""

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Next Feature", callback_data="tour_machine_lib")],
            [InlineKeyboardButton("🏠 Back to Menu", callback_data="tour_menu")]
        ])

        await update.callback_query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

    async def show_machine_lib_tour(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Explain machine library feature"""
        message = """📚 **Machine Library**

Keep track of YOUR equipment for faster troubleshooting!

**What you can do:**

📋 **Add Machines**
   - Store equipment details (model, serial, location)
   - Track maintenance history
   - Get equipment-specific answers

📄 **Upload Electrical Schematics**
   - Upload ladder diagrams, wiring prints
   - Ask questions about YOUR specific setup
   - No need to re-explain your configuration

📖 **Upload Manuals**
   - Add manuals to shared knowledge base
   - Help the community
   - Get better answers for rare equipment

**Commands:**
• `/add_machine` - Add equipment
• `/list_machines` - View your library
• `/upload_print` - Upload schematics
• `/upload_manual` - Share manuals"""

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Next Feature", callback_data="tour_field_eye")],
            [InlineKeyboardButton("🏠 Back to Menu", callback_data="tour_menu")]
        ])

        await update.callback_query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

    async def show_field_eye_tour(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Explain Field Eye (Pro/Team only)"""
        message = """📷 **Field Eye - Image Analysis**

🔥 **Pro Feature**: Unlock visual troubleshooting!

**How it works:**

1️⃣ **Take a photo** of:
   - Equipment nameplate
   - Error screen
   - Damaged components
   - Wiring diagram

2️⃣ **Send to RIVET**
   - I'll analyze the image with AI vision
   - Extract fault codes, model numbers
   - Identify issues visually

3️⃣ **Get instant diagnosis**
   - Equipment identification
   - Visual fault detection
   - Troubleshooting steps

**Example questions:**
• "What's this fault code?" [photo of VFD screen]
• "Is this wiring correct?" [photo of panel]
• "What model is this?" [photo of nameplate]

**Try it:**
Just send me a photo with a caption like "VFD won't start"

No camera needed - describe the fault and I'll help!"""

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Next Feature", callback_data="tour_pdf_export")],
            [InlineKeyboardButton("🏠 Back to Menu", callback_data="tour_menu")]
        ])

        await update.callback_query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

    async def show_pdf_export_tour(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Explain PDF export (Pro/Team only)"""
        message = """📄 **PDF Export**

🔥 **Pro Feature**: Professional troubleshooting reports!

**What gets exported:**

✅ **Full conversation history**
   - All Q&A from troubleshooting session
   - Equipment details
   - Timestamps

✅ **Citations & References**
   - Manual page numbers
   - Documentation links
   - Source materials

✅ **Safety Warnings**
   - All safety reminders included
   - Organized by severity

✅ **Professional formatting**
   - Clean, printable layout
   - Company branding (Enterprise)
   - Shareable with team

**Use cases:**
• Document troubleshooting for compliance
• Share solutions with colleagues
• Keep maintenance records
• Training new technicians

**Commands:**
• `/export_session` - Export current session
• `/my_sessions` - View past sessions"""

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Next Feature", callback_data="tour_team_mgmt")],
            [InlineKeyboardButton("🏠 Back to Menu", callback_data="tour_menu")]
        ])

        await update.callback_query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

    async def show_team_mgmt_tour(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Explain team management (Enterprise only)"""
        message = """👥 **Team Management**

🚀 **Enterprise Feature**: Collaborate with your team!

**Team Features:**

👔 **Admin Dashboard**
   - Invite up to 10 team members
   - Manage user permissions
   - View team usage analytics

📊 **Shared Resources**
   - Shared equipment library
   - Centralized manual database
   - Team knowledge base

🔧 **Work Order Integration**
   - Create work orders from troubleshooting
   - Assign to team members
   - Track completion status

📈 **Analytics**
   - Team troubleshooting metrics
   - Most common issues
   - Time-to-resolution tracking

☎️ **Dedicated Support**
   - Phone support hotline
   - Priority email response
   - Dedicated account manager

**Commands:**
• `/team_dashboard` - Admin panel
• `/team_invite` - Invite members
• `/team_library` - Shared equipment"""

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Finish Tour", callback_data="tour_complete")],
            [InlineKeyboardButton("🏠 Back to Menu", callback_data="tour_menu")]
        ])

        await update.callback_query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

    async def complete_tour(self, update: Update, user_data: Dict):
        """Tour completed - return to onboarding or show summary"""
        tier = user_data.get("subscription_tier", "beta")

        completion_message = """🎉 **Feature Tour Complete!**

You now know what RIVET can do for you!

**Next steps:**
• Ask a troubleshooting question
• Add equipment to your library
• Upload a manual or print

**Commands to remember:**
• `/help` - See all commands
• `/tour` - Replay this tour
• `/quickstart` - Quick reference card

Ready to start troubleshooting? 🚀"""

        # No keyboard - just completion message
        await update.callback_query.edit_message_text(
            completion_message,
            parse_mode=ParseMode.MARKDOWN
        )

    # =========================================================================
    # Callback Router
    # =========================================================================

    async def handle_tour_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_data: Dict
    ):
        """
        Route tour callbacks to appropriate handler.

        Callback data format: "tour_<feature>"
        """
        query = update.callback_query
        await query.answer()

        data = query.data

        handlers = {
            "tour_menu": lambda: self.show_tour_menu(update, user_data),
            "tour_troubleshooting": lambda: self.show_troubleshooting_tour(update, context),
            "tour_machine_lib": lambda: self.show_machine_lib_tour(update, context),
            "tour_field_eye": lambda: self.show_field_eye_tour(update, context),
            "tour_pdf_export": lambda: self.show_pdf_export_tour(update, context),
            "tour_team_mgmt": lambda: self.show_team_mgmt_tour(update, context),
            "tour_complete": lambda: self.complete_tour(update, user_data),
        }

        handler = handlers.get(data)
        if handler:
            await handler()
        else:
            # Unknown callback - show menu
            await self.show_tour_menu(update, user_data)

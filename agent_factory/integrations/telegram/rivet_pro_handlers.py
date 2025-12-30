"""
RIVET Pro Telegram Bot Handlers

Comprehensive conversation flows for monetizable troubleshooting service.

Features:
- Onboarding new users
- Troubleshooting Q&A with confidence scoring
- Subscription upgrades (Free → Pro → Enterprise)
- Expert booking flow
- Session history and exports

Commands:
- /start - Onboarding flow
- /troubleshoot - Start troubleshooting session
- /upgrade - Upgrade to Pro/Enterprise
- /book_expert - Schedule expert call
- /my_sessions - View troubleshooting history
- /export_session - Export session as PDF
- /pro_stats - View usage stats

Integrates with:
- intent_detector: Classify questions
- confidence_scorer: Quality gates and upsells
- Stripe: Payment processing
- Supabase: Session tracking
"""

import os
import json
from typing import Optional, Dict, Any
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatAction

from agent_factory.rivet_pro.intent_detector import IntentDetector, IntentType
from agent_factory.rivet_pro.confidence_scorer import ConfidenceScorer, AnswerAction
from agent_factory.rivet_pro.database import RIVETProDatabase
from agent_factory.rivet_pro.vps_kb_client import VPSKBClient
from agent_factory.integrations.telegram.conversation_manager import ConversationManager
from agent_factory.rivet_pro.clarification import IntentClarifier, ClarificationRequest
from agent_factory.integrations.telegram.api_client import RivetAPIClient
from agent_factory.integrations.telegram.onboarding_manager import OnboardingManager
from agent_factory.integrations.telegram.feature_tour import FeatureTour
from agent_factory.integrations.telegram.quick_reference import (
    get_quickstart_message,
    get_help_message,
    get_about_message,
    get_tier_comparison,
    get_upgrade_prompt
)


class RIVETProHandlers:
    """
    Telegram handlers for RIVET Pro monetization features.

    Manages complete user journey from onboarding to troubleshooting
    to premium upgrades.

    Now with conversation memory for natural language intelligence!
    """

    def __init__(self):
        """Initialize handlers with dependencies"""
        self.intent_detector = IntentDetector()
        self.confidence_scorer = ConfidenceScorer()
        self.clarifier = IntentClarifier()  # WS-3: Clarification system
        self.db = RIVETProDatabase()  # Uses DATABASE_PROVIDER from .env
        self.conversation_manager = ConversationManager(db=self.db)  # Phase 1: Memory
        self.vps_client = VPSKBClient()  # VPS KB Factory connection
        self.api_client = RivetAPIClient()  # WS-3: Backend API for work orders

        # Onboarding system
        self.onboarding_manager = OnboardingManager(db=self.db)
        self.feature_tour = FeatureTour()

        # Stripe config (test mode)
        self.stripe_api_key = os.getenv("STRIPE_API_KEY", "")
        self.stripe_publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

        # Pricing
        self.PRO_PRICE_MONTHLY = 29.00
        self.ENTERPRISE_PRICE_MONTHLY = 499.00
        self.EXPERT_CALL_PRICE_HOURLY = 75.00

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /start command - Enhanced onboarding flow with API key authentication.

        Usage:
        - /start → Auto-provision beta user + onboarding
        - /start <api_key> → Authenticate with landing page-generated key
        """
        user = update.effective_user
        user_id = str(user.id)

        # Check for API key in args
        if context.args and len(context.args) > 0:
            api_key = context.args[0]
            return await self.onboarding_manager.authenticate_with_api_key(
                update, context, api_key
            )

        # Auto-provision flow (existing behavior)
        user_sub = await self._get_or_create_user(user_id, user.username or "unknown")

        # Start onboarding system
        await self.onboarding_manager.start_onboarding(update, context, user_sub)

    async def handle_troubleshoot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle troubleshooting questions (main conversation flow).

        Flow (ENHANCED with Phase 1 - Conversation Memory):
        1. Load conversation session (NEW)
        2. Detect intent with context awareness (ENHANCED)
        3. Check user tier and question limits
        4. Search knowledge base
        5. Score confidence
        6. Respond with answer + upsell if needed
        7. Save conversation history (NEW)
        """
        user = update.effective_user
        user_id = str(user.id)
        question = update.message.text

        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

        # 🆕 Phase 1: Load conversation session
        session = self.conversation_manager.get_or_create_session(
            user_id=user_id,
            telegram_username=user.username
        )

        # Get user subscription
        user_sub = await self._get_or_create_user(user_id, user.username or "unknown")

        # Check question limits
        can_ask, limit_message = await self._check_question_limit(user_sub)
        if not can_ask:
            # Question limit reached - show upgrade prompt
            await self._send_upgrade_prompt(update, trigger="question_limit")
            return

        # 🆕 Phase 1: Add user message to history
        self.conversation_manager.add_user_message(
            session,
            question,
            metadata={
                "telegram_message_id": update.message.message_id,
                "user_tier": user_sub["tier"]
            }
        )

        # 🆕 Phase 1: Get conversation context
        conv_context = self.conversation_manager.get_context(session)

        # Detect intent (now context-aware)
        intent = self.intent_detector.detect(question)

        # 🆕 Phase 1: Enhance intent with conversation context
        # If user says "what about bearings?" we know they're still talking about motors
        if conv_context.last_equipment_type and not intent.equipment_info.equipment_type:
            intent.equipment_info.equipment_type = conv_context.last_equipment_type

        # 🆕 WS-3: Check if clarification is needed
        if self.clarifier.needs_clarification(intent):
            # Intent too unclear to proceed
            if self.clarifier.is_too_unclear(intent):
                await update.message.reply_text(
                    "❌ I'm having trouble understanding your question. "
                    "Could you please rephrase it with more details?\n\n"
                    "Try including:\n"
                    "• What equipment (motor, VFD, PLC, etc.)\n"
                    "• What's happening (error, noise, stopped, etc.)\n"
                    "• Any error codes"
                )
                return

            # Generate clarification question
            clarification = self.clarifier.generate_clarification(intent)

            # Store clarification in user context
            context.user_data["pending_clarification"] = {
                "clarification": clarification,
                "original_question": question
            }

            # Send clarification request
            await update.message.reply_text(
                clarification.to_telegram_message(),
                parse_mode=ParseMode.MARKDOWN
            )

            return  # Wait for user response

        # Handle non-troubleshooting intents
        if intent.intent_type == IntentType.BOOKING:
            await self._handle_booking_intent(update, context)
            return
        elif intent.intent_type == IntentType.ACCOUNT:
            await self._handle_account_intent(update, context)
            return

        # Search knowledge base
        matched_atoms = await self._search_knowledge_base(
            question=question,
            equipment_type=intent.equipment_info.equipment_type,
            keywords=intent.keywords,
        )

        # Score confidence
        quality = self.confidence_scorer.score_answer(
            question=question,
            matched_atoms=matched_atoms,
            user_tier=user_sub["tier"],
            questions_today=user_sub["questions_today"],
            daily_limit=user_sub["daily_limit"],
            intent_data=intent.to_dict(),
        )

        # Create troubleshooting session
        session_id = await self._create_troubleshooting_session(
            user_id=user_id,
            question=question,
            intent=intent,
            quality=quality,
            matched_atoms=matched_atoms,
        )

        # Increment question count
        await self._increment_question_count(user_id)

        # Handle response based on confidence
        bot_response = ""
        if quality.answer_action == AnswerAction.AUTO_RESPOND:
            # High confidence - send answer
            bot_response = await self._send_answer(update, question, matched_atoms, intent, quality)

        elif quality.answer_action == AnswerAction.SUGGEST_UPGRADE:
            # Medium confidence - send answer + upsell
            bot_response = await self._send_answer(update, question, matched_atoms, intent, quality)
            if quality.should_upsell:
                await self._send_upsell(update, quality)

        elif quality.answer_action == AnswerAction.REQUIRE_EXPERT:
            # Low confidence - suggest expert call
            bot_response = await self._send_expert_required(update, question, intent, quality)

        # 🆕 Phase 1: Save bot response to conversation history
        self.conversation_manager.add_bot_message(
            session,
            bot_response,
            metadata={
                "confidence": quality.overall_confidence,
                "intent_type": intent.intent_type.value,
                "equipment_type": intent.equipment_info.equipment_type,
                "atoms_used": len(matched_atoms),
                "session_id": session_id
            }
        )

        # 🆕 Phase 1: Persist conversation session to database
        self.conversation_manager.save_session(session)

        # Log conversion event
        await self._log_conversion_event(
            user_id=user_id,
            event_type="troubleshooting_question",
            trigger_context={
                "confidence": quality.overall_confidence,
                "intent_type": intent.intent_type.value,
                "urgency": intent.urgency_score,
            },
        )

    async def handle_clarification_response(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_response: str
    ) -> bool:
        """
        Handle user's response to a clarification question.

        Args:
            update: Telegram update
            context: Telegram context
            user_response: User's clarification response

        Returns:
            True if clarification was processed, False if no pending clarification

        This is called when a user responds after being asked for clarification.
        It resolves the clarification and retries the original query.
        """
        pending = context.user_data.get("pending_clarification")

        if not pending:
            return False  # No pending clarification

        clarification: ClarificationRequest = pending["clarification"]
        original_question: str = pending["original_question"]

        # Resolve clarification
        resolution = self.clarifier.resolve_clarification(
            clarification,
            user_response
        )

        if not resolution["resolved"]:
            await update.message.reply_text(
                "❌ I didn't understand your response. Please try again."
            )
            return True

        # Clear pending clarification
        context.user_data.pop("pending_clarification", None)

        # Rebuild question with clarified details
        enhanced_question = original_question

        # Add clarified details to question
        if clarification.type.value == "equipment_ambiguous":
            equipment_info = resolution["details"]
            enhanced_question = (
                f"{original_question}\n"
                f"(Equipment: {equipment_info.get('manufacturer', '')} "
                f"{equipment_info.get('model', equipment_info.get('equipment_freeform', ''))})"
            )

        elif clarification.type.value == "missing_details":
            enhanced_question = (
                f"{original_question}\n"
                f"Additional info: {resolution['details'].get('additional_info', '')}"
            )

        elif clarification.type.value == "fault_description_vague":
            enhanced_question = (
                f"{original_question}\n"
                f"Details: {resolution['details'].get('additional_info', '')}"
            )

        # Acknowledge clarification
        await update.message.reply_text(
            "✅ Got it! Let me help with that...",
            parse_mode=ParseMode.MARKDOWN
        )

        # Retry with enhanced question
        # Create a synthetic update with enhanced question
        update.message.text = enhanced_question

        await self.handle_troubleshooting_question(update, context)

        return True

    async def handle_upgrade(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /upgrade command - Show upgrade options with payment links.
        """
        user = update.effective_user
        user_id = str(user.id)

        user_sub = await self._get_or_create_user(user_id, user.username or "unknown")
        current_tier = user_sub["tier"]

        if current_tier == "pro":
            await update.message.reply_text(
                "You're already on the Pro tier! 🎉\n\n"
                "Want to upgrade to Enterprise? Contact us at enterprise@rivetpro.com"
            )
            return

        # Create payment link (Stripe Checkout)
        payment_link = await self._create_stripe_checkout_link(user_id, "pro")

        upgrade_text = f"""
💼 **Upgrade to RIVET Pro**

**Current Plan:** {current_tier.upper()}

🚀 **Pro Benefits:**
• ✅ Unlimited questions/day
• ✅ Priority support (<1hr response)
• ✅ Image analysis (Field Eye)
• ✅ Export troubleshooting reports (PDF)
• ✅ Session history (unlimited)

**Price:** ${self.PRO_PRICE_MONTHLY}/month
**Billing:** Monthly, cancel anytime

[Upgrade Now]({payment_link})

Questions? Reply /help for support.
"""

        keyboard = [
            [InlineKeyboardButton("💳 Upgrade to Pro - $29/mo", url=payment_link)],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_upgrade")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text=upgrade_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup,
        )

    async def handle_book_expert(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /book_expert command - Expert marketplace and booking flow.
        """
        user = update.effective_user
        user_id = str(user.id)

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

        # Get available experts
        experts = await self._get_available_experts()

        if not experts:
            await update.message.reply_text(
                "😔 No experts available right now.\n\n"
                "Join the waitlist: /waitlist"
            )
            return

        # Format expert list
        expert_text = "👨‍🔧 **Available Experts**\n\n"

        for i, expert in enumerate(experts[:5], 1):
            expert_text += (
                f"{i}. **{expert['name']}**\n"
                f"   ⭐ {expert['average_rating']:.1f}/5.0 ({expert['total_calls_completed']} calls)\n"
                f"   💰 ${expert['hourly_rate_usd']}/hr\n"
                f"   🔧 {', '.join(expert['specialties'][:3])}\n"
                f"   ⏰ Available: Now\n"
                f"   [Book]({self._create_booking_link(expert['id'])})\n\n"
            )

        expert_text += (
            "📅 **How it works:**\n"
            "1. Select an expert and time slot\n"
            "2. Pay securely via Stripe\n"
            "3. Join video call at scheduled time\n"
            "4. Receive post-call summary report\n\n"
            "Questions? Reply /help"
        )

        await update.message.reply_text(
            text=expert_text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )

    async def handle_my_sessions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /my_sessions command - Show user's troubleshooting history.
        """
        user = update.effective_user
        user_id = str(user.id)

        # Fetch recent sessions
        sessions = await self._get_user_sessions(user_id, limit=10)

        if not sessions:
            await update.message.reply_text(
                "No troubleshooting sessions yet.\n\n"
                "Ask me a question to get started!"
            )
            return

        # Format sessions
        session_text = f"📋 **Your Troubleshooting History** ({len(sessions)} sessions)\n\n"

        for i, session in enumerate(sessions, 1):
            status_emoji = "✅" if session.get("resolved") else "⏳"
            session_text += (
                f"{i}. {status_emoji} **{session.get('equipment_type', 'Unknown')}**\n"
                f"   Issue: {session['issue_description'][:60]}...\n"
                f"   Confidence: {session.get('confidence_score', 0):.0%}\n"
                f"   Date: {session['created_at'][:10]}\n"
                f"   [View Details](/session_{session['id']})\n\n"
            )

        session_text += "\n💡 Tip: Use /export_session to download PDF reports"

        await update.message.reply_text(
            text=session_text,
            parse_mode=ParseMode.MARKDOWN,
        )

    async def handle_pro_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /pro_stats command - Show user's usage statistics.
        """
        user = update.effective_user
        user_id = str(user.id)

        user_sub = await self._get_or_create_user(user_id, user.username or "unknown")

        # Calculate stats
        total_sessions = await self._count_user_sessions(user_id)
        resolved_sessions = await self._count_resolved_sessions(user_id)
        avg_confidence = await self._calc_avg_confidence(user_id)

        stats_text = f"""
📊 **Your RIVET Pro Stats**

**Subscription:**
• Tier: {user_sub['tier'].upper()}
• Member since: {user_sub['created_at'][:10]}
• Status: {'Active ✅' if user_sub['is_active'] else 'Inactive ❌'}

**Usage This Month:**
• Questions asked: {user_sub['questions_this_month']}
• Questions today: {user_sub['questions_today']}/{user_sub['daily_limit']}
• Total sessions: {total_sessions}
• Resolved: {resolved_sessions} ({(resolved_sessions/max(1, total_sessions)*100):.0f}%)

**Quality:**
• Average confidence: {avg_confidence:.0%}

**Next Renewal:** {user_sub.get('renews_at', 'N/A')[:10]}

Need help? Reply /help
"""

        await update.message.reply_text(
            text=stats_text,
            parse_mode=ParseMode.MARKDOWN,
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _get_or_create_user(self, user_id: str, username: str) -> Dict[str, Any]:
        """Get or create user subscription record"""
        try:
            # Check if user exists
            user = self.db.get_user(user_id)

            if user:
                return user

            # Create new user
            user = self.db.create_user(
                user_id=user_id,
                telegram_user_id=int(user_id),
                telegram_username=username,
                tier="free",
                daily_limit=5,
                questions_today=0,
                questions_this_month=0,
                is_active=True,
                signup_source="telegram"
            )
            return user

        except Exception as e:
            print(f"Error getting/creating user: {e}")
            # Return default
            return {
                "user_id": user_id,
                "tier": "free",
                "daily_limit": 5,
                "questions_today": 0,
                "questions_this_month": 0,
            }

    async def _check_question_limit(self, user_sub: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Check if user can ask another question"""
        if user_sub["tier"] in ["pro", "enterprise"]:
            return True, None

        if user_sub["questions_today"] >= user_sub["daily_limit"]:
            return False, f"Daily limit reached ({user_sub['daily_limit']} questions/day)"

        return True, None

    async def _increment_question_count(self, user_id: str):
        """Increment user's question count"""
        try:
            self.db.increment_question_count(user_id)
        except Exception as e:
            print(f"Error incrementing question count: {e}")

    async def _search_knowledge_base(
        self,
        question: str,
        equipment_type: Optional[str],
        keywords: list,
    ) -> list:
        """
        Search VPS Knowledge Base for relevant atoms.

        Uses multi-stage fallback strategy:
        1. Semantic search (best results)
        2. Equipment-specific search (if equipment type detected)
        3. Keyword search (fallback)

        Returns:
            List of atom dictionaries with similarity scores
        """
        try:
            # Strategy 1: Semantic search (best results)
            atoms = self.vps_client.query_atoms_semantic(
                query_text=question,
                limit=5,
                similarity_threshold=0.7
            )

            if atoms:
                print(f"[KB] Semantic search returned {len(atoms)} atoms")
                return atoms

            # Strategy 2: Equipment-specific search
            if equipment_type:
                atoms = self.vps_client.search_by_equipment(
                    equipment_type=equipment_type,
                    limit=5
                )

                if atoms:
                    print(f"[KB] Equipment search ({equipment_type}) returned {len(atoms)} atoms")
                    return atoms

            # Strategy 3: Keyword search (fallback)
            if keywords:
                for keyword in keywords[:3]:  # Try top 3 keywords
                    atoms = self.vps_client.query_atoms(
                        topic=keyword,
                        limit=5
                    )

                    if atoms:
                        print(f"[KB] Keyword search ('{keyword}') returned {len(atoms)} atoms")
                        return atoms

            # No results found
            print(f"[KB] No atoms found for question: '{question[:50]}...'")
            return []

        except Exception as e:
            print(f"Error searching KB: {e}")
            # Graceful degradation - return empty list rather than crashing
            return []

    async def _create_troubleshooting_session(
        self,
        user_id: str,
        question: str,
        intent: Any,
        quality: Any,
        matched_atoms: list,
    ) -> str:
        """Create troubleshooting session record"""
        try:
            session = self.db.create_session(
                user_id=user_id,
                issue_description=question,
                equipment_type=intent.equipment_info.equipment_type,
                equipment_manufacturer=intent.equipment_info.manufacturer,
                equipment_model=intent.equipment_info.model,
                fault_codes=intent.equipment_info.fault_codes,
                urgency_score=intent.urgency_score,
                confidence_score=quality.overall_confidence,
                status="open",
                matched_atoms=[atom.get("atom_id") for atom in matched_atoms],
                atoms_used_count=len(matched_atoms)
            )
            return str(session["id"])

        except Exception as e:
            print(f"Error creating session: {e}")
            return "mock_session_id"

    async def _send_answer(self, update: Update, question: str, atoms: list, intent: Any, quality: Any) -> str:
        """
        Send detailed answer with citations to user.

        Generates professional response using atom content with:
        - Clear problem/solution structure
        - Step-by-step instructions (if available)
        - Source citations with page numbers
        - Follow-up suggestions
        """
        if not atoms:
            # No results - suggest alternatives
            answer_text = (
                "😔 **No Knowledge Base Matches**\n\n"
                "I couldn't find specific documentation for your question in the knowledge base.\n\n"
                "**Options:**\n"
                "• Try rephrasing your question\n"
                "• /book_expert for live tech support\n"
                "• Describe more symptoms or equipment details\n"
            )
            await update.message.reply_text(answer_text, parse_mode=ParseMode.MARKDOWN)
            return answer_text

        # Format equipment context
        equipment_context = ""
        if intent.equipment_info.equipment_type:
            equipment_context = f"{intent.equipment_info.equipment_type.title()} "
            if intent.equipment_info.manufacturer:
                equipment_context += f"({intent.equipment_info.manufacturer.title()}) "

        # Header
        answer_text = (
            f"🔧 **{equipment_context}Troubleshooting**\n\n"
            f"Confidence: {quality.overall_confidence:.0%} | "
            f"Found: {len(atoms)} atom{'s' if len(atoms) > 1 else ''}\n\n"
        )

        # Main answer from top 3 atoms
        for i, atom in enumerate(atoms[:3], 1):
            similarity = atom.get('similarity', 0)
            relevance_emoji = "🎯" if similarity > 0.85 else "✅" if similarity > 0.75 else "📍"

            answer_text += f"{relevance_emoji} **{atom.get('title', 'Unknown')}**\n"

            # Add summary
            summary = atom.get('summary', atom.get('content', ''))[:200]
            answer_text += f"{summary}...\n\n"

            # Add specific details based on atom type
            if atom.get('symptoms'):
                symptoms = atom.get('symptoms', [])
                if isinstance(symptoms, list) and symptoms:
                    answer_text += f"**Symptoms:** {', '.join(symptoms[:3])}\n"

            if atom.get('causes'):
                causes = atom.get('causes', [])
                if isinstance(causes, list) and causes:
                    answer_text += f"**Likely Causes:** {', '.join(causes[:3])}\n"

            if atom.get('fixes'):
                fixes = atom.get('fixes', [])
                if isinstance(fixes, list) and fixes:
                    answer_text += f"**Solutions:** {', '.join(fixes[:3])}\n"

            # Add steps if available
            if atom.get('steps'):
                steps = atom.get('steps', [])
                if isinstance(steps, list) and len(steps) > 0:
                    answer_text += f"\n**Steps:**\n"
                    for j, step in enumerate(steps[:4], 1):
                        answer_text += f"{j}. {step}\n"

            answer_text += "\n"

        # Citations
        answer_text += "📚 **Sources:**\n"
        cited_sources = set()
        for atom in atoms[:3]:
            source_url = atom.get('source_url', '')
            source_pages = atom.get('source_pages', [])

            if source_url and source_url not in cited_sources:
                cited_sources.add(source_url)
                page_info = f" (p.{source_pages[0]})" if source_pages else ""
                # Truncate URL for readability
                display_url = source_url if len(source_url) < 50 else source_url[:47] + "..."
                answer_text += f"• {display_url}{page_info}\n"

        # Follow-up suggestions
        answer_text += "\n💬 **Follow-up:**\n"
        if equipment_context:
            answer_text += f"• \"Tell me more about {atom.get('title', 'this')}\"\n"
        answer_text += "• \"What are the next steps?\"\n"
        answer_text += "• \"Show me related issues\"\n"

        await update.message.reply_text(
            text=answer_text,
            parse_mode=ParseMode.MARKDOWN,
        )

        return answer_text  # Return for conversation history

    async def _send_upsell(self, update: Update, quality: Any):
        """Send upsell message based on quality assessment"""
        if not quality.upsell_message:
            return

        await update.message.reply_text(
            text=quality.upsell_message,
            parse_mode=ParseMode.MARKDOWN,
        )

    async def _send_expert_required(self, update: Update, question: str, intent: Any, quality: Any) -> str:
        """Send expert call required message and return the text"""
        message = f"""
⚠️ **Complex Issue Detected**

Confidence: {quality.overall_confidence:.0%}
Urgency: {intent.urgency_score}/10

This appears to require expert assistance.

📞 **Book Expert Call** - $75/hour
• Real-time video support
• 30-60 minute sessions
• Post-call summary report

[Book Now](/book_expert) [Try AI Answer Anyway](/force_answer)
"""

        await update.message.reply_text(
            text=message,
            parse_mode=ParseMode.MARKDOWN,
        )

        return message  # Return for conversation history

    async def _send_upgrade_prompt(self, update: Update, trigger: str):
        """Send upgrade prompt when limits reached"""
        message = """
🚫 **Daily Question Limit Reached**

You've used all 5 free questions today.

💼 **Upgrade to Pro** for:
• Unlimited questions/day
• Priority support
• Image analysis
• PDF exports

**Only $29/month** - Cancel anytime

[Upgrade Now](/upgrade)
"""

        await update.message.reply_text(
            text=message,
            parse_mode=ParseMode.MARKDOWN,
        )

    async def _get_available_experts(self) -> list:
        """Fetch available experts from database"""
        try:
            experts = self.db.get_available_experts(specialty=None)
            return experts or []
        except Exception as e:
            print(f"Error fetching experts: {e}")
            return []

    async def _get_user_sessions(self, user_id: str, limit: int = 10) -> list:
        """Fetch user's troubleshooting sessions"""
        try:
            sessions = self.db.get_user_sessions(user_id, limit)
            return sessions or []
        except Exception as e:
            print(f"Error fetching sessions: {e}")
            return []

    async def _count_user_sessions(self, user_id: str) -> int:
        """Count total sessions for user"""
        try:
            sessions = self.db.get_user_sessions(user_id, limit=1000)  # Get all
            return len(sessions)
        except Exception as e:
            return 0

    async def _count_resolved_sessions(self, user_id: str) -> int:
        """Count resolved sessions for user"""
        try:
            sessions = self.db.get_user_sessions(user_id, limit=1000)
            return len([s for s in sessions if s.get("resolved")])
        except Exception as e:
            return 0

    async def _calc_avg_confidence(self, user_id: str) -> float:
        """Calculate average confidence for user's sessions"""
        try:
            sessions = self.db.get_user_sessions(user_id, limit=1000)
            scores = [s["confidence_score"] for s in sessions if s.get("confidence_score")]
            return sum(scores) / len(scores) if scores else 0.0
        except Exception as e:
            return 0.0

    async def _create_stripe_checkout_link(self, user_id: str, tier: str) -> str:
        """Create Stripe Checkout session link"""
        # TODO: Implement actual Stripe integration
        return f"https://rivetpro.com/checkout?user={user_id}&tier={tier}"

    def _create_booking_link(self, expert_id: str) -> str:
        """Create expert booking link"""
        # TODO: Implement actual booking system (Calendly/Cal.com integration)
        return f"https://rivetpro.com/book?expert={expert_id}"

    async def _log_conversion_event(self, user_id: str, event_type: str, trigger_context: Dict[str, Any]):
        """Log conversion event for analytics"""
        try:
            user = self.db.get_user(user_id)
            current_tier = user["tier"] if user else "free"

            self.db.track_conversion_event(
                user_id=user_id,
                event_type=event_type,
                converted=False,
                telegram_user_id=int(user_id),
                current_tier=current_tier,
                trigger_context=trigger_context
            )
        except Exception as e:
            print(f"Error logging conversion event: {e}")

    async def _handle_booking_intent(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle booking intent from natural language"""
        await update.message.reply_text(
            "I see you want to book an expert call!\n\n"
            "Use /book_expert to see available experts."
        )

    async def _handle_account_intent(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle account management intent"""
        await update.message.reply_text(
            "Account management:\n\n"
            "/upgrade - Upgrade subscription\n"
            "/pro_stats - View your stats\n"
            "/cancel - Cancel subscription"
        )

    async def handle_vps_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display VPS KB Factory health status"""
        await update.message.reply_text("Checking VPS KB Factory status...")

        try:
            health = self.vps_client.health_check()

            # Format status message
            status_emoji = {
                "healthy": "✅",
                "degraded": "⚠️",
                "down": "❌"
            }.get(health.get("status", "unknown"), "❓")

            db_status = "✅ Connected" if health.get("database_connected") else "❌ Down"
            ollama_status = "✅ Available" if health.get("ollama_available") else "❌ Down"

            atom_count = health.get("atom_count", 0)
            last_ingestion = health.get("last_ingestion", "Unknown")
            response_time = health.get("response_time_ms", 0)

            status_text = (
                f"{status_emoji} **VPS KB Factory Status**\n\n"
                f"**Overall:** {health.get('status', 'unknown').title()}\n"
                f"**Database:** {db_status}\n"
                f"**Ollama:** {ollama_status}\n"
                f"**Atoms:** {atom_count:,}\n"
                f"**Last Ingestion:** {last_ingestion}\n"
                f"**Response Time:** {response_time}ms\n"
                f"**Checked At:** {health.get('checked_at', 'Unknown')}\n"
            )

            if health.get("status") == "healthy":
                status_text += "\n✅ All systems operational"
            elif health.get("status") == "degraded":
                status_text += "\n⚠️ Systems operational but degraded"
            else:
                status_text += "\n❌ Systems experiencing issues"

            await update.message.reply_text(status_text, parse_mode='Markdown')

        except Exception as e:
            await update.message.reply_text(
                f"❌ Failed to check VPS status:\n{str(e)}",
                parse_mode='Markdown'
            )

    async def handle_tutorial(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /tutorial command - Replay onboarding tutorial.

        Allows users to re-experience onboarding anytime.
        """
        user = update.effective_user
        user_id = str(user.id)

        user_sub = await self._get_or_create_user(user_id, user.username or "unknown")

        # Start onboarding from Step 1
        await self.onboarding_manager.begin_step_1(update, context, user_sub)

    async def handle_tour(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /tour command - Show feature tour menu.

        Interactive exploration of tier-specific features.
        """
        user = update.effective_user
        user_id = str(user.id)

        user_sub = await self._get_or_create_user(user_id, user.username or "unknown")

        # Show feature tour menu
        await self.feature_tour.show_tour_menu(update, user_sub)

    async def handle_quickstart(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /quickstart command - Show quick reference card.

        Provides tier-specific command cheat sheet.
        """
        user = update.effective_user
        user_id = str(user.id)

        user_sub = await self._get_or_create_user(user_id, user.username or "unknown")
        tier = user_sub.get("subscription_tier", "beta")

        # Get quick reference message
        quick_ref = get_quickstart_message(tier)

        await update.message.reply_text(
            text=quick_ref,
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /help command - Show comprehensive help message.

        Lists all available commands based on user's tier.
        """
        user = update.effective_user
        user_id = str(user.id)

        user_sub = await self._get_or_create_user(user_id, user.username or "unknown")
        tier = user_sub.get("subscription_tier", "beta")

        # Get help message
        help_text = get_help_message(tier)

        await update.message.reply_text(
            text=help_text,
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /about command - Show "About RIVET" information.

        Explains what RIVET is, how it works, and pricing tiers.
        """
        about_text = get_about_message()

        await update.message.reply_text(
            text=about_text,
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_pricing(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /pricing command - Show tier comparison table.

        Displays detailed pricing and feature comparison.
        """
        pricing_text = get_tier_comparison()

        await update.message.reply_text(
            text=pricing_text,
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_onboarding_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle inline button callbacks for onboarding flow.

        Routes callbacks to appropriate onboarding step or tour handler.
        """
        query = update.callback_query
        await query.answer()

        user = update.effective_user
        user_id = str(user.id)
        user_sub = await self._get_or_create_user(user_id, user.username or "unknown")

        data = query.data

        # Route to onboarding handlers
        if data.startswith("onboard_"):
            if data == "onboard_step_2":
                await self.onboarding_manager.begin_step_2(update, context, user_sub)
            elif data == "onboard_step_3":
                await self.onboarding_manager.begin_step_3(update, context, user_sub)
            elif data == "onboard_step_4":
                await self.onboarding_manager.begin_step_4(update, context, user_sub)
            elif data == "onboard_step_5":
                await self.onboarding_manager.begin_step_5(update, context, user_sub)
            elif data == "onboard_skip":
                await self.onboarding_manager.skip_onboarding(update, user_sub)
            elif data == "onboard_about":
                await self.onboarding_manager.show_about(update)

        # Route to feature tour handlers
        elif data.startswith("tour_"):
            await self.feature_tour.handle_tour_callback(update, context, user_sub)


# Lazy singleton instance (avoid database connection at import time)
_rivet_pro_handlers_instance = None

def get_rivet_pro_handlers():
    """Get or create singleton RIVETProHandlers instance."""
    global _rivet_pro_handlers_instance
    if _rivet_pro_handlers_instance is None:
        _rivet_pro_handlers_instance = RIVETProHandlers()
    return _rivet_pro_handlers_instance


# Export handler functions for registration
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_rivet_pro_handlers().handle_start(update, context)


async def handle_troubleshoot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_rivet_pro_handlers().handle_troubleshoot(update, context)


async def handle_upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_rivet_pro_handlers().handle_upgrade(update, context)


async def handle_book_expert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_rivet_pro_handlers().handle_book_expert(update, context)


async def handle_my_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_rivet_pro_handlers().handle_my_sessions(update, context)


async def handle_pro_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_rivet_pro_handlers().handle_pro_stats(update, context)


async def handle_vps_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_rivet_pro_handlers().handle_vps_status(update, context)


async def handle_tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_rivet_pro_handlers().handle_tutorial(update, context)


async def handle_tour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_rivet_pro_handlers().handle_tour(update, context)


async def handle_quickstart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_rivet_pro_handlers().handle_quickstart(update, context)


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_rivet_pro_handlers().handle_help(update, context)


async def handle_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_rivet_pro_handlers().handle_about(update, context)


async def handle_pricing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_rivet_pro_handlers().handle_pricing(update, context)


async def handle_onboarding_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_rivet_pro_handlers().handle_onboarding_callback(update, context)

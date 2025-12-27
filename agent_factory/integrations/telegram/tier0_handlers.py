"""
TIER 0.1: Telegram Bot Infrastructure for CEO Command & Control

This module implements the foundation of the three-layer autonomous company:
- Voice message transcription (OpenAI Whisper)
- Image OCR extraction (OpenAI Vision API)
- Session management (conversation context per user)
- Intent Decoder integration stub (placeholder for task-38.2)
- Status Pipeline integration stub (placeholder for task-38.5)

Part of TIER 0 Supercritical components (task-38.1).
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
import json
import tempfile

from telegram import Update, File
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

# OpenAI client for Whisper (voice) and Vision (OCR)
from openai import AsyncOpenAI

# WS-3 RIVET Pro integration
from agent_factory.rivet_pro.intent_detector import IntentDetector, IntentType


logger = logging.getLogger(__name__)


# ============================================================================
# Session Management - Conversation Context Tracking
# ============================================================================

class SessionManager:
    """
    Manages conversation context per Telegram user.

    Stores:
    - Message history (last N messages per user)
    - User preferences
    - Active task context
    - Conversation state

    Storage: PostgreSQL (Supabase) with in-memory cache
    """

    def __init__(self, storage, max_history: int = 10, cache_ttl_seconds: int = 300):
        """
        Initialize session manager.

        Args:
            storage: SupabaseMemoryStorage instance
            max_history: Max messages to keep per user (default: 10)
            cache_ttl_seconds: Cache TTL in seconds (default: 300 = 5 min)
        """
        self.storage = storage
        self.max_history = max_history
        self.cache_ttl_seconds = cache_ttl_seconds

        # In-memory cache: user_id -> session data
        self._cache: Dict[int, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[int, datetime] = {}

    def _is_cache_valid(self, user_id: int) -> bool:
        """Check if cached session is still valid"""
        if user_id not in self._cache_timestamps:
            return False

        age = datetime.now() - self._cache_timestamps[user_id]
        return age.total_seconds() < self.cache_ttl_seconds

    async def get_session(self, user_id: int) -> Dict[str, Any]:
        """
        Get session data for user.

        Returns:
            Session dict with:
            - user_id: int
            - message_history: List[Dict] (last N messages)
            - context: Dict (arbitrary key-value pairs)
            - created_at: str (ISO timestamp)
            - updated_at: str (ISO timestamp)
        """
        # Check cache first
        if self._is_cache_valid(user_id):
            logger.debug(f"Session cache hit for user {user_id}")
            return self._cache[user_id]

        logger.debug(f"Session cache miss for user {user_id}, querying database")

        try:
            # Query Supabase
            response = self.storage.client.table("telegram_sessions") \
                .select("*") \
                .eq("user_id", user_id) \
                .execute()

            if response.data:
                session = response.data[0]

                # Update cache
                self._cache[user_id] = session
                self._cache_timestamps[user_id] = datetime.now()

                return session
            else:
                # Create new session
                session = {
                    "user_id": user_id,
                    "message_history": [],
                    "context": {},
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }

                # Save to database
                self.storage.client.table("telegram_sessions") \
                    .insert(session) \
                    .execute()

                # Update cache
                self._cache[user_id] = session
                self._cache_timestamps[user_id] = datetime.now()

                logger.info(f"Created new session for user {user_id}")
                return session

        except Exception as e:
            logger.error(f"Failed to get session for user {user_id}: {e}")

            # Return minimal session (graceful degradation)
            return {
                "user_id": user_id,
                "message_history": [],
                "context": {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

    async def add_message(self, user_id: int, role: str, content: str, message_type: str = "text"):
        """
        Add message to user's conversation history.

        Args:
            user_id: Telegram user ID
            role: 'user' or 'assistant'
            content: Message content (text, transcription, or OCR result)
            message_type: 'text', 'voice', 'image', 'command'
        """
        session = await self.get_session(user_id)

        # Add message to history
        message = {
            "role": role,
            "content": content,
            "type": message_type,
            "timestamp": datetime.now().isoformat()
        }

        session["message_history"].append(message)

        # Keep only last N messages
        if len(session["message_history"]) > self.max_history:
            session["message_history"] = session["message_history"][-self.max_history:]

        # Update timestamp
        session["updated_at"] = datetime.now().isoformat()

        # Save to database
        try:
            self.storage.client.table("telegram_sessions") \
                .update({
                    "message_history": session["message_history"],
                    "updated_at": session["updated_at"]
                }) \
                .eq("user_id", user_id) \
                .execute()

            # Update cache
            self._cache[user_id] = session
            self._cache_timestamps[user_id] = datetime.now()

        except Exception as e:
            logger.error(f"Failed to save message for user {user_id}: {e}")

    async def update_context(self, user_id: int, context_updates: Dict[str, Any]):
        """
        Update arbitrary context for user.

        Args:
            user_id: Telegram user ID
            context_updates: Dict of key-value pairs to merge into context
        """
        session = await self.get_session(user_id)

        # Merge context
        session["context"].update(context_updates)
        session["updated_at"] = datetime.now().isoformat()

        # Save to database
        try:
            self.storage.client.table("telegram_sessions") \
                .update({
                    "context": session["context"],
                    "updated_at": session["updated_at"]
                }) \
                .eq("user_id", user_id) \
                .execute()

            # Update cache
            self._cache[user_id] = session
            self._cache_timestamps[user_id] = datetime.now()

        except Exception as e:
            logger.error(f"Failed to update context for user {user_id}: {e}")

    async def clear_session(self, user_id: int):
        """Clear session for user (reset conversation)"""
        try:
            self.storage.client.table("telegram_sessions") \
                .delete() \
                .eq("user_id", user_id) \
                .execute()

            # Clear cache
            if user_id in self._cache:
                del self._cache[user_id]
            if user_id in self._cache_timestamps:
                del self._cache_timestamps[user_id]

            logger.info(f"Cleared session for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to clear session for user {user_id}: {e}")


# ============================================================================
# Intent Decoder Stub (Placeholder for task-38.2)
# ============================================================================

class IntentDecoderStub:
    """
    Placeholder for Intent Decoder (task-38.2).

    When task-38.2 is implemented, this will:
    - Extract structured task from CEO message (text, voice, image)
    - Return JSON with: task_type, priority, description, context, confidence
    - Use Ollama Mistral 7B for local NLP

    For now, returns placeholder response.
    """

    async def decode_intent(
        self,
        message: str,
        message_type: str = "text",
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Decode user message into structured task intent.

        Args:
            message: Message content (text, transcription, or OCR result)
            message_type: 'text', 'voice', 'image'
            user_context: User's conversation context

        Returns:
            {
                "task_type": str,  # "code", "research", "deploy", "status", etc.
                "priority": str,   # "high", "medium", "low"
                "description": str,
                "context": dict,
                "confidence": float  # 0-1
            }
        """
        logger.info(f"[STUB] Intent Decoder called with message_type={message_type}")
        logger.debug(f"[STUB] Message: {message[:100]}...")

        # Placeholder implementation
        # TODO: Replace with Ollama Mistral when task-38.2 is complete

        return {
            "task_type": "unknown",
            "priority": "medium",
            "description": message,
            "context": user_context or {},
            "confidence": 0.5,
            "stub_note": "Intent Decoder not implemented yet (task-38.2 pending)"
        }


# ============================================================================
# Status Pipeline Stub (Placeholder for task-38.5)
# ============================================================================

class StatusPipelineStub:
    """
    Placeholder for Status Reporting Pipeline (task-38.5).

    When task-38.5 is implemented, this will:
    - Receive status events from Orchestrator and agents
    - Format clean Telegram messages
    - Send real-time updates to CEO

    For now, formats basic status messages.
    """

    def format_status(
        self,
        status_type: str,
        task_id: str = None,
        task_description: str = None,
        progress: float = None,
        error: str = None
    ) -> str:
        """
        Format status update for Telegram.

        Args:
            status_type: 'started', 'progress', 'completed', 'failed'
            task_id: Task identifier
            task_description: Human-readable task description
            progress: Progress percentage (0-100)
            error: Error message if failed

        Returns:
            Formatted markdown message
        """
        logger.info(f"[STUB] Status Pipeline formatting {status_type} status")

        # Emoji mapping
        emoji = {
            "started": "▶️",
            "progress": "📊",
            "completed": "✅",
            "failed": "❌"
        }.get(status_type, "ℹ️")

        # Build message
        if status_type == "started":
            return f"{emoji} *Task Started*\n\n{task_description or task_id}"

        elif status_type == "progress":
            progress_bar = "█" * int((progress or 0) / 10) + "░" * (10 - int((progress or 0) / 10))
            return f"{emoji} *Progress Update*\n\n{task_description or task_id}\n{progress_bar} {progress or 0:.0f}%"

        elif status_type == "completed":
            return f"{emoji} *Task Complete*\n\n{task_description or task_id}"

        elif status_type == "failed":
            return f"{emoji} *Task Failed*\n\n{task_description or task_id}\n\nError: {error or 'Unknown error'}"

        else:
            return f"{emoji} *Status Update*\n\n{task_description or task_id}"


# ============================================================================
# TIER0Handlers - Main Handler Class
# ============================================================================

class TIER0Handlers:
    """
    TIER 0.1: CEO Command & Control Infrastructure

    Handles:
    - Text messages (with confirmation)
    - Voice messages (with Whisper transcription)
    - Image messages (with Vision API OCR)
    - Session management (conversation context)
    - Integration with Intent Decoder (stub)
    - Status formatting (stub)
    """

    def __init__(self, storage, rivet_handlers=None, openai_api_key: str = None):
        """
        Initialize TIER0 handlers.

        Args:
            storage: SupabaseMemoryStorage instance
            rivet_handlers: RIVETProHandlers instance for routing intents (WS-3)
            openai_api_key: OpenAI API key (for Whisper + Vision)
        """
        self.storage = storage
        self.rivet_handlers = rivet_handlers
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        if not self.openai_api_key:
            logger.warning("OpenAI API key not set - voice and image features disabled")

        # Initialize components
        self.session_manager = SessionManager(storage)

        # Use real IntentDetector if RIVET handlers available, otherwise stub
        if rivet_handlers:
            self.intent_detector = IntentDetector()
            logger.info("TIER0: Using real IntentDetector (WS-3 integration)")
        else:
            self.intent_detector = IntentDecoderStub()
            logger.warning("TIER0: Using stub IntentDecoder (RIVET handlers not available)")

        self.status_pipeline = StatusPipelineStub()

        # OpenAI client (async)
        self.openai_client = AsyncOpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

        logger.info("TIER0Handlers initialized")

    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle text messages from CEO.

        Acceptance Criteria #1: Receives text messages and sends confirmation
        """
        user_id = update.effective_user.id
        message_text = update.message.text

        logger.info(f"Text message from user {user_id}: {message_text[:50]}...")

        try:
            # Add to session history
            await self.session_manager.add_message(
                user_id=user_id,
                role="user",
                content=message_text,
                message_type="text"
            )

            # Get session context
            session = await self.session_manager.get_session(user_id)

            # Decode intent (stub)
            intent = await self.intent_decoder.decode_intent(
                message=message_text,
                message_type="text",
                user_context=session["context"]
            )

            # Send confirmation
            confirmation = (
                f"✅ *Message Received*\n\n"
                f"Message: {message_text[:100]}{'...' if len(message_text) > 100 else ''}\n\n"
                f"_Intent Decoder is analyzing your request..._\n\n"
                f"[TIER 0.1 Active - Full orchestration pending]"
            )

            await update.message.reply_text(
                confirmation,
                parse_mode=ParseMode.MARKDOWN
            )

            # Add assistant response to history
            await self.session_manager.add_message(
                user_id=user_id,
                role="assistant",
                content=confirmation,
                message_type="text"
            )

            logger.info(f"Text confirmation sent to user {user_id}")

        except Exception as e:
            logger.error(f"Error handling text message: {e}")
            await update.message.reply_text(
                f"❌ Error processing your message.\n\n`{str(e)}`",
                parse_mode=ParseMode.MARKDOWN
            )

    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle voice messages from CEO.

        Acceptance Criteria #2: Receives voice messages and extracts transcript

        Uses OpenAI Whisper API for transcription.
        """
        user_id = update.effective_user.id
        voice = update.message.voice

        logger.info(f"Voice message from user {user_id}, duration={voice.duration}s")

        if not self.openai_client:
            await update.message.reply_text(
                "❌ Voice transcription unavailable (OpenAI API key not configured)"
            )
            return

        try:
            # Send processing message
            processing_msg = await update.message.reply_text(
                "🎤 *Processing voice message...*\n\n_Transcribing with Whisper..._",
                parse_mode=ParseMode.MARKDOWN
            )

            # Download voice file
            voice_file: File = await voice.get_file()

            # Create temp file for voice
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_voice:
                await voice_file.download_to_drive(temp_voice.name)
                temp_voice_path = temp_voice.name

            try:
                # Transcribe with Whisper API
                with open(temp_voice_path, "rb") as audio_file:
                    transcript_response = await self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text"
                    )

                transcript = transcript_response

                logger.info(f"Voice transcribed: {transcript[:100]}...")

                # Add to session history
                await self.session_manager.add_message(
                    user_id=user_id,
                    role="user",
                    content=transcript,
                    message_type="voice"
                )

                # Acknowledge transcription to user
                await processing_msg.edit_text(
                    f"🎤 *I heard:* \"{transcript}\"\n\n_Processing your request..._",
                    parse_mode=ParseMode.MARKDOWN
                )

                # Route to RIVET Pro handlers if available
                if self.rivet_handlers:
                    logger.info(f"Routing voice transcript to RIVET Pro: {transcript[:50]}...")

                    # Detect intent from transcribed text
                    intent = await self.intent_detector.detect(transcript)

                    # Add to conversation history (using conversation_manager if available)
                    if hasattr(self.rivet_handlers, 'conversation_manager'):
                        self.rivet_handlers.conversation_manager.add_message(
                            user_id=user_id,
                            role="user",
                            content=transcript,
                            metadata={"source": "voice", "intent": intent.to_dict()}
                        )

                    # Route based on intent type
                    if intent.intent_type == IntentType.TROUBLESHOOTING:
                        await self.rivet_handlers.handle_troubleshooting_question(
                            update=update,
                            context=context,
                            question=transcript,
                            intent=intent
                        )

                    elif intent.intent_type == IntentType.INFORMATION:
                        await self.rivet_handlers.handle_information_query(
                            update=update,
                            context=context,
                            question=transcript
                        )

                    elif intent.intent_type == IntentType.BOOKING:
                        await update.message.reply_text(
                            "📞 I see you want to book an expert call. "
                            "Use /book_expert to schedule a session."
                        )

                    elif intent.intent_type == IntentType.ACCOUNT:
                        await update.message.reply_text(
                            "⚙️ For account management, use:\n"
                            "/upgrade - Upgrade subscription\n"
                            "/pro_stats - View usage stats\n"
                            "/my_sessions - View history"
                        )

                    else:
                        # Unknown intent - ask for clarification
                        await update.message.reply_text(
                            "🤔 I'm not sure what you need help with. "
                            "Could you rephrase that? Or try:\n"
                            "/troubleshoot - Technical support\n"
                            "/book_expert - Schedule expert call"
                        )

                    logger.info(f"Voice routed to RIVET Pro: intent={intent.intent_type.value}")

                else:
                    # No RIVET handlers - send stub confirmation
                    logger.warning("Voice transcribed but no RIVET handlers available")

                    confirmation = (
                        f"🎤 *Voice Message Transcribed*\n\n"
                        f"Transcript: _{transcript}_\n\n"
                        f"Duration: {voice.duration}s\n\n"
                        f"_RIVET Pro handlers not available - using fallback mode_"
                    )

                    await processing_msg.edit_text(
                        confirmation,
                        parse_mode=ParseMode.MARKDOWN
                    )

                    # Add to session history
                    await self.session_manager.add_message(
                        user_id=user_id,
                        role="assistant",
                        content=confirmation,
                        message_type="text"
                    )

            finally:
                # Clean up temp file
                Path(temp_voice_path).unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"Error handling voice message: {e}")
            await update.message.reply_text(
                f"❌ Error transcribing voice message.\n\n`{str(e)}`",
                parse_mode=ParseMode.MARKDOWN
            )

    async def handle_image_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle image/screenshot messages from CEO.

        Acceptance Criteria #3: Receives screenshot images and extracts OCR text

        Uses OpenAI Vision API for OCR.
        """
        user_id = update.effective_user.id
        photo = update.message.photo[-1]  # Highest resolution

        logger.info(f"Image message from user {user_id}, size={photo.file_size} bytes")

        if not self.openai_client:
            await update.message.reply_text(
                "❌ Image OCR unavailable (OpenAI API key not configured)"
            )
            return

        try:
            # Send processing message
            processing_msg = await update.message.reply_text(
                "🖼️ *Processing image...*\n\n_Extracting text with Vision API..._",
                parse_mode=ParseMode.MARKDOWN
            )

            # Download image file
            photo_file: File = await photo.get_file()

            # Create temp file for image
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_image:
                await photo_file.download_to_drive(temp_image.name)
                temp_image_path = temp_image.name

            try:
                # Read image and encode as base64
                import base64
                with open(temp_image_path, "rb") as image_file:
                    image_data = base64.b64encode(image_file.read()).decode("utf-8")

                # Use Vision API for OCR
                vision_response = await self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Extract all text from this image. Return only the extracted text, nothing else."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_data}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=1000
                )

                ocr_text = vision_response.choices[0].message.content

                logger.info(f"Image OCR extracted: {ocr_text[:100]}...")

                # Add to session history
                await self.session_manager.add_message(
                    user_id=user_id,
                    role="user",
                    content=ocr_text,
                    message_type="image"
                )

                # Get session context
                session = await self.session_manager.get_session(user_id)

                # Decode intent (stub)
                intent = await self.intent_decoder.decode_intent(
                    message=ocr_text,
                    message_type="image",
                    user_context=session["context"]
                )

                # Update processing message with OCR result
                confirmation = (
                    f"🖼️ *Image Text Extracted*\n\n"
                    f"Extracted Text:\n_{ocr_text[:500]}{'...' if len(ocr_text) > 500 else ''}_\n\n"
                    f"_Intent Decoder is analyzing your request..._\n\n"
                    f"[TIER 0.1 Active - Full orchestration pending]"
                )

                await processing_msg.edit_text(
                    confirmation,
                    parse_mode=ParseMode.MARKDOWN
                )

                # Add assistant response to history
                await self.session_manager.add_message(
                    user_id=user_id,
                    role="assistant",
                    content=confirmation,
                    message_type="text"
                )

                logger.info(f"Image OCR confirmation sent to user {user_id}")

            finally:
                # Clean up temp file
                Path(temp_image_path).unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"Error handling image message: {e}")
            await update.message.reply_text(
                f"❌ Error extracting text from image.\n\n`{str(e)}`",
                parse_mode=ParseMode.MARKDOWN
            )

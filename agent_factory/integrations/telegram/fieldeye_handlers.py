"""
Field Eye handlers for Telegram bot.

Commands:
- /fieldeye_upload <video_file> - Upload and process inspection video
- /fieldeye_stats - Show Field Eye statistics (sessions, frames, defects)
- /fieldeye_defects [limit] - List recent defects (default: 10)
- /fieldeye_sessions [limit] - List recent sessions (default: 5)

Integration with Field Eye vision platform for industrial inspection automation.
"""

import sys
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List, Dict
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatAction

# Add project root for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agent_factory.memory.storage import SupabaseMemoryStorage
from agent_factory.field_eye.utils.video_processor import VideoProcessor
from agent_factory.field_eye.utils.pause_detector import PauseDetector


# =============================================================================
# Helper Functions
# =============================================================================

async def send_typing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show typing indicator"""
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )


async def send_progress(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
    """Send progress update to user"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message
    )


def format_timestamp(seconds: float) -> str:
    """Format timestamp as MM:SS"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


# =============================================================================
# Field Eye Upload Handler
# =============================================================================

async def fieldeye_upload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /fieldeye_upload command.

    Accepts video file attachment, processes it through Field Eye pipeline:
    1. Download video to temp location
    2. Extract frames at intervals
    3. Detect pause events (defect markers)
    4. Store frames and metadata in Supabase
    5. Return summary with defect candidates

    Usage:
        /fieldeye_upload <attach video file>

    Example:
        User: /fieldeye_upload [uploads inspection_001.mp4]
        Bot:
        📹 Processing video...
        ✅ Processed! Found 3 defect candidates in 450 frames

        Pause Events:
        1. Time: 00:45, Duration: 2.3s, Confidence: 0.87
        2. Time: 02:12, Duration: 1.8s, Confidence: 0.76
        3. Time: 04:33, Duration: 3.1s, Confidence: 0.92
    """
    chat_id = update.effective_chat.id

    # Check if video file is attached
    if not update.message.document and not update.message.video:
        await update.message.reply_text(
            "❌ *Usage:* `/fieldeye_upload` with video attachment\n\n"
            "*How to use:*\n"
            "1. Click attachment button\n"
            "2. Select your inspection video (.mp4, .mov, .avi)\n"
            "3. Add caption: `/fieldeye_upload`\n"
            "4. Send\n\n"
            "*Example:*\n"
            "Attach `inspection_001.mp4` with caption `/fieldeye_upload`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Get video file
    if update.message.video:
        file = update.message.video
        file_name = f"video_{chat_id}_{file.file_id}.mp4"
    else:
        file = update.message.document
        file_name = file.file_name or f"video_{chat_id}_{file.file_id}.mp4"

    # Check file size (limit: 20MB for Telegram free tier)
    if file.file_size > 20 * 1024 * 1024:
        await update.message.reply_text(
            "❌ *File too large*\n\n"
            f"Your video: {file.file_size / (1024*1024):.1f}MB\n"
            f"Maximum: 20MB\n\n"
            "💡 Compress video or trim to shorter duration",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    await send_progress(update, context, "📹 *Downloading video...*")
    await send_typing(update, context)

    # Download video to temp location
    temp_dir = Path(tempfile.mkdtemp(prefix="fieldeye_"))
    video_path = temp_dir / file_name

    try:
        # Download file
        telegram_file = await file.get_file()
        await telegram_file.download_to_drive(str(video_path))

        await send_progress(update, context, "🎬 *Extracting frames...*")
        await send_typing(update, context)

        # Process video
        processor = VideoProcessor(str(video_path))

        # Get metadata
        metadata = processor.get_metadata()

        # Extract frames (every 2 seconds)
        frames = await asyncio.to_thread(
            processor.extract_frames,
            interval_sec=2.0,
            max_frames=500  # Limit to 500 frames for performance
        )

        await send_progress(update, context, "🔍 *Detecting pauses (defect markers)...*")
        await send_typing(update, context)

        # Detect pauses
        detector = PauseDetector(
            motion_threshold=5000.0,
            min_pause_duration_sec=1.0,
            max_pause_duration_sec=30.0
        )

        pauses = await asyncio.to_thread(
            detector.analyze_video,
            str(video_path)
        )

        defect_candidates = detector.get_defect_candidates(pauses, min_confidence=0.5)

        processor.release()

        # Store in database
        await send_progress(update, context, "💾 *Saving to database...*")
        await send_typing(update, context)

        storage = SupabaseMemoryStorage()

        # Create session record
        session_data = {
            'technician_id': str(chat_id),
            'equipment_type': 'unknown',  # User can specify later
            'duration_sec': int(metadata.duration_sec),
            'total_frames': metadata.total_frames,
            'pause_count': len(pauses),
            'pauses': [
                {
                    'frame': p.frame_start,
                    'timestamp': p.timestamp_start,
                    'duration': p.duration_sec,
                    'confidence': p.confidence,
                    'is_defect_candidate': p.is_defect_candidate
                }
                for p in pauses
            ],
            'camera_model': 'telegram_upload',
            'video_path': str(video_path),
            'metadata': {
                'file_size_mb': metadata.file_size_mb,
                'codec': metadata.codec,
                'resolution': f"{metadata.width}x{metadata.height}",
                'fps': metadata.fps
            }
        }

        result = storage.client.table("field_eye_sessions").insert(session_data).execute()
        session_id = result.data[0]['id'] if result.data else None

        # Format response
        response = "✅ *Video Processed Successfully!*\n\n"
        response += f"📊 *Summary:*\n"
        response += f"  • Duration: {format_timestamp(metadata.duration_sec)}\n"
        response += f"  • Total Frames: {metadata.total_frames:,}\n"
        response += f"  • Extracted: {len(frames)} frames\n"
        response += f"  • Pause Events: {len(pauses)}\n"
        response += f"  • Defect Candidates: {len(defect_candidates)}\n\n"

        if defect_candidates:
            response += f"🔴 *Top Defect Candidates:*\n"
            for i, pause in enumerate(defect_candidates[:5], 1):
                response += (
                    f"{i}. Time: {format_timestamp(pause.timestamp_start)}, "
                    f"Duration: {pause.duration_sec:.1f}s, "
                    f"Confidence: {pause.confidence:.2f}\n"
                )
            response += "\n"

        if session_id:
            response += f"💾 Session ID: `{session_id}`\n\n"

        response += f"💡 Use `/fieldeye_sessions` to view all sessions"

        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await update.message.reply_text(
            f"❌ *Processing failed*\n\n"
            f"Error: {str(e)}\n\n"
            "Make sure:\n"
            "• File is a valid video (.mp4, .mov, .avi)\n"
            "• File is not corrupted\n"
            "• Video codec is supported",
            parse_mode=ParseMode.MARKDOWN
        )

    finally:
        # Cleanup temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


# =============================================================================
# Field Eye Stats Handler
# =============================================================================

async def fieldeye_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /fieldeye_stats command.

    Shows Field Eye platform statistics:
    - Total sessions
    - Total frames
    - Total defects detected
    - Labeled frames count
    - Active product kits

    Usage:
        /fieldeye_stats

    Example:
        Bot:
        📊 Field Eye Statistics

        Total Sessions: 45
        Total Frames: 22,500
        Total Defects: 127
        Labeled Frames: 890
        Active Kits: 12
        Latest Session: 2025-12-11 14:23
    """
    try:
        await send_typing(update, context)

        storage = SupabaseMemoryStorage()

        # Call database function for stats
        result = storage.client.rpc('get_field_eye_stats').execute()

        if not result.data:
            await update.message.reply_text(
                "❌ Could not fetch statistics\n\n"
                "Database may be empty or function not available."
            )
            return

        stats = result.data

        # Format response
        response = "📊 *Field Eye Statistics*\n\n"
        response += f"*Sessions:*\n"
        response += f"  • Total: {stats.get('total_sessions', 0):,}\n"
        response += f"  • Avg Pauses: {stats.get('avg_pauses_per_session', 0):.1f}\n\n"

        response += f"*Frames:*\n"
        response += f"  • Total: {stats.get('total_frames', 0):,}\n"
        response += f"  • Labeled: {stats.get('labeled_frames', 0):,}\n\n"

        response += f"*Defects:*\n"
        response += f"  • Total: {stats.get('total_defects', 0):,}\n\n"

        response += f"*Hardware:*\n"
        response += f"  • Active Kits: {stats.get('active_kits', 0)}\n\n"

        latest_session = stats.get('latest_session')
        if latest_session:
            response += f"*Latest Activity:*\n"
            response += f"  • {latest_session}\n\n"

        response += f"💡 Use `/fieldeye_sessions` to view recent sessions\n"
        response += f"💡 Use `/fieldeye_defects` to view recent defects"

        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await update.message.reply_text(
            f"❌ Error fetching stats: {str(e)}\n\n"
            "Make sure Field Eye database schema is deployed."
        )


# =============================================================================
# Field Eye Defects Handler
# =============================================================================

async def fieldeye_defects_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /fieldeye_defects command.

    Lists recent defects detected by Field Eye.
    Shows defect type, confidence, severity, and timestamp.

    Usage:
        /fieldeye_defects [limit]

    Examples:
        /fieldeye_defects         # Show 10 most recent
        /fieldeye_defects 20      # Show 20 most recent

    Response:
        🔴 Recent Defects (10)

        1. Torque Stripe Missing
           Confidence: 0.94
           Severity: warning
           Time: 2025-12-11 14:23

        2. Bearing Overheat
           Confidence: 0.87
           Severity: critical
           Time: 2025-12-11 13:45
    """
    # Parse limit from args
    limit = 10
    if context.args and len(context.args) > 0:
        try:
            limit = int(context.args[0])
            limit = max(1, min(limit, 50))  # Clamp to 1-50
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid limit. Must be a number between 1 and 50.\n\n"
                "*Usage:* `/fieldeye_defects [limit]`\n"
                "*Example:* `/fieldeye_defects 20`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

    try:
        await send_typing(update, context)

        storage = SupabaseMemoryStorage()

        # Query recent defects
        result = storage.client.table("field_eye_defects")\
            .select("id, defect_type, confidence, severity, created_at, auto_detected, human_verified")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()

        defects = result.data

        if not defects:
            await update.message.reply_text(
                "📭 *No defects found*\n\n"
                "Upload inspection videos with `/fieldeye_upload` to start detecting defects.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Format response
        response = f"🔴 *Recent Defects ({len(defects)})*\n\n"

        for i, defect in enumerate(defects, 1):
            defect_type = defect.get('defect_type', 'unknown').replace('_', ' ').title()
            confidence = defect.get('confidence', 0.0)
            severity = defect.get('severity', 'info').upper()
            created_at = defect.get('created_at', 'unknown')
            auto_detected = defect.get('auto_detected', True)
            human_verified = defect.get('human_verified', False)

            # Severity emoji
            severity_emoji = {
                'CRITICAL': '🔴',
                'WARNING': '⚠️',
                'INFO': 'ℹ️'
            }.get(severity, '•')

            response += f"*{i}. {defect_type}*\n"
            response += f"   {severity_emoji} Severity: {severity}\n"
            response += f"   🎯 Confidence: {confidence:.2f}\n"

            if auto_detected:
                response += f"   🤖 Auto-detected\n"

            if human_verified:
                response += f"   ✅ Human verified\n"

            response += f"   🕐 {created_at[:19]}\n\n"

        response += f"💡 Use `/fieldeye_stats` for overall statistics"

        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await update.message.reply_text(
            f"❌ Error fetching defects: {str(e)}"
        )


# =============================================================================
# Field Eye Sessions Handler
# =============================================================================

async def fieldeye_sessions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /fieldeye_sessions command.

    Lists recent inspection sessions.
    Shows technician, equipment, duration, pause count, and date.

    Usage:
        /fieldeye_sessions [limit]

    Examples:
        /fieldeye_sessions         # Show 5 most recent
        /fieldeye_sessions 10      # Show 10 most recent

    Response:
        📋 Recent Sessions (5)

        1. Session: abc123...
           Technician: user_12345
           Equipment: coaster
           Duration: 15:30
           Pauses: 12
           Date: 2025-12-11 14:23

        2. Session: def456...
           Technician: user_12345
           Equipment: motor
           Duration: 08:45
           Pauses: 5
           Date: 2025-12-11 13:10
    """
    # Parse limit from args
    limit = 5
    if context.args and len(context.args) > 0:
        try:
            limit = int(context.args[0])
            limit = max(1, min(limit, 20))  # Clamp to 1-20
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid limit. Must be a number between 1 and 20.\n\n"
                "*Usage:* `/fieldeye_sessions [limit]`\n"
                "*Example:* `/fieldeye_sessions 10`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

    try:
        await send_typing(update, context)

        storage = SupabaseMemoryStorage()

        # Query recent sessions
        result = storage.client.table("field_eye_sessions")\
            .select("id, technician_id, equipment_type, duration_sec, pause_count, date, total_frames")\
            .order("date", desc=True)\
            .limit(limit)\
            .execute()

        sessions = result.data

        if not sessions:
            await update.message.reply_text(
                "📭 *No sessions found*\n\n"
                "Upload your first inspection video with `/fieldeye_upload`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Format response
        response = f"📋 *Recent Sessions ({len(sessions)})*\n\n"

        for i, session in enumerate(sessions, 1):
            session_id = session.get('id', 'unknown')[:8]  # First 8 chars
            technician = session.get('technician_id', 'unknown')
            equipment = session.get('equipment_type', 'unknown')
            duration_sec = session.get('duration_sec', 0)
            pause_count = session.get('pause_count', 0)
            total_frames = session.get('total_frames', 0)
            date = session.get('date', 'unknown')

            response += f"*{i}. Session {session_id}...*\n"
            response += f"   👤 Tech: {technician}\n"
            response += f"   🔧 Equipment: {equipment}\n"
            response += f"   ⏱️ Duration: {format_timestamp(duration_sec)}\n"
            response += f"   🎬 Frames: {total_frames:,}\n"
            response += f"   ⏸️ Pauses: {pause_count}\n"
            response += f"   📅 {date[:19]}\n\n"

        response += f"💡 Use `/fieldeye_defects` to view detected defects"

        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await update.message.reply_text(
            f"❌ Error fetching sessions: {str(e)}"
        )


# =============================================================================
# Natural Language Wrappers
# =============================================================================

async def fieldeye_stats_natural(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle natural language Field Eye stats requests.

    Called when user says things like:
    - "Show Field Eye stats"
    - "Field Eye statistics"
    - "How many inspection sessions?"
    """
    await fieldeye_stats_handler(update, context)


async def fieldeye_sessions_natural(update: Update, context: ContextTypes.DEFAULT_TYPE, limit: int = 5):
    """
    Handle natural language Field Eye sessions requests.

    Called when user says things like:
    - "Show recent inspections"
    - "List Field Eye sessions"
    - "What videos have been uploaded?"
    """
    context.args = [str(limit)]
    await fieldeye_sessions_handler(update, context)


async def fieldeye_defects_natural(update: Update, context: ContextTypes.DEFAULT_TYPE, limit: int = 10):
    """
    Handle natural language Field Eye defects requests.

    Called when user says things like:
    - "Show recent defects"
    - "What defects were found?"
    - "List Field Eye detections"
    """
    context.args = [str(limit)]
    await fieldeye_defects_handler(update, context)

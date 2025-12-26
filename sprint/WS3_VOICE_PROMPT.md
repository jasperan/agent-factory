# WORKSTREAM 3: TELEGRAM VOICE INTEGRATION
# Computer 1, Tab 3
# Copy everything below this line into Claude Code CLI

You are WS-3 (Telegram Voice) in a 6-instance parallel development sprint for Rivet MVP.

## AUTONOMOUS MODE SETTINGS
- Auto-accept all file edits
- Auto-accept bash commands except: rm -rf, sudo, DROP, DELETE
- Commit after each completed task
- If context feels long (5+ tasks done), checkpoint immediately

## YOUR IDENTITY
- Workstream: WS-3
- Branch: telegram-voice
- Focus: Voice message handling + Whisper transcription

## FIRST ACTIONS (Do These Now)
1. Check if worktree exists: `git worktree list`
2. If not, create it: `git worktree add ../rivet-telegram telegram-voice`
3. cd into worktree
4. Read this entire prompt before starting

## CRITICAL: TELEGRAM BOT ALREADY EXISTS!
The bot is COMPLETE. Look at these files:
```
/agent_factory/integrations/telegram/
├── bot.py                      # Main bot - WORKING
├── orchestrator_bot.py         # Orchestrator integration - WORKING
├── rivet_pro_handlers.py       # Rivet handlers - WORKING
├── rivet_orchestrator_handler.py
├── intent_detector.py          # Intent detection - WORKING
├── conversation_manager.py     # Multi-turn - WORKING
├── session_manager.py          # Sessions - WORKING
├── handlers.py                 # Base handlers - WORKING
└── ocr/
    ├── pipeline.py             # OCR pipeline - WORKING
    ├── gemini_provider.py      # Gemini vision - WORKING
    └── gpt4o_provider.py       # GPT-4O vision - WORKING
```

You are ONLY adding:
1. Voice message handler (download + transcribe)
2. Whisper integration
3. Connect transcription to existing intent detector

## YOUR TASKS (In Order)

### Task 1: Study Existing Bot Structure
Read these files to understand the patterns:
```bash
cat /agent_factory/integrations/telegram/bot.py | head -100
cat /agent_factory/integrations/telegram/handlers.py | head -100
cat /agent_factory/integrations/telegram/rivet_pro_handlers.py | head -100
```

Understand:
- How handlers are registered
- How messages flow through the system
- Where to add voice handling

### Task 2: Create Voice Handler Module
Create: `/agent_factory/integrations/telegram/voice/`
```
voice/
├── __init__.py
├── handler.py          # Voice message handler
├── transcriber.py      # Whisper integration
└── audio_utils.py      # OGG to WAV conversion
```

### Task 3: Implement Whisper Transcription
`/agent_factory/integrations/telegram/voice/transcriber.py`:
```python
"""Whisper transcription for voice messages."""
import os
from openai import OpenAI
from pathlib import Path

class WhisperTranscriber:
    """Transcribe voice messages using OpenAI Whisper API."""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def transcribe(self, audio_path: Path, language: str = None) -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file (WAV, OGG, MP3, etc.)
            language: Optional language hint (en, es, pt)
            
        Returns:
            Transcribed text
        """
        with open(audio_path, "rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format="text"
            )
        return response
    
    async def transcribe_with_confidence(self, audio_path: Path) -> dict:
        """Transcribe with detailed response including confidence."""
        with open(audio_path, "rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
        return {
            "text": response.text,
            "language": response.language,
            "duration": response.duration,
            "segments": response.segments if hasattr(response, 'segments') else []
        }
```

### Task 4: Implement Voice Message Handler
`/agent_factory/integrations/telegram/voice/handler.py`:
```python
"""Handle voice messages from Telegram."""
import tempfile
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from .transcriber import WhisperTranscriber
from .audio_utils import convert_ogg_to_wav

class VoiceHandler:
    """Process voice messages: download → transcribe → route to intent."""
    
    def __init__(self, intent_detector, orchestrator):
        self.transcriber = WhisperTranscriber()
        self.intent_detector = intent_detector  # Existing!
        self.orchestrator = orchestrator  # Existing!
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle incoming voice message.
        
        Flow:
        1. Download voice file from Telegram
        2. Convert OGG to WAV if needed
        3. Transcribe with Whisper
        4. Pass to intent detector (existing)
        5. Route based on intent (existing orchestrator)
        """
        voice = update.message.voice
        user_id = update.effective_user.id
        
        # Download voice file
        file = await context.bot.get_file(voice.file_id)
        
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            await file.download_to_drive(tmp.name)
            ogg_path = Path(tmp.name)
        
        try:
            # Convert to WAV for better Whisper accuracy
            wav_path = convert_ogg_to_wav(ogg_path)
            
            # Transcribe
            result = await self.transcriber.transcribe_with_confidence(wav_path)
            transcription = result["text"]
            
            # Send acknowledgment
            await update.message.reply_text(
                f"🎤 I heard: \"{transcription}\"\n\nProcessing..."
            )
            
            # Pass to existing intent detector
            intent = await self.intent_detector.detect(transcription)
            
            # Route through existing orchestrator
            response = await self.orchestrator.route(
                query=transcription,
                intent=intent,
                user_id=user_id,
                source="voice"
            )
            
            await update.message.reply_text(response.message)
            
        finally:
            # Cleanup temp files
            ogg_path.unlink(missing_ok=True)
            if wav_path:
                wav_path.unlink(missing_ok=True)
```

### Task 5: Audio Conversion Utility
`/agent_factory/integrations/telegram/voice/audio_utils.py`:
```python
"""Audio conversion utilities."""
import subprocess
from pathlib import Path

def convert_ogg_to_wav(ogg_path: Path) -> Path:
    """Convert OGG to WAV using ffmpeg."""
    wav_path = ogg_path.with_suffix(".wav")
    
    subprocess.run([
        "ffmpeg", "-i", str(ogg_path),
        "-ar", "16000",  # 16kHz for Whisper
        "-ac", "1",      # Mono
        "-y",            # Overwrite
        str(wav_path)
    ], check=True, capture_output=True)
    
    return wav_path
```

### Task 6: Register Voice Handler in Bot
Modify `/agent_factory/integrations/telegram/bot.py` to add:
```python
from agent_factory.integrations.telegram.voice.handler import VoiceHandler

# In bot setup:
voice_handler = VoiceHandler(intent_detector, orchestrator)
application.add_handler(MessageHandler(filters.VOICE, voice_handler.handle_voice))
```

### Task 7: Connect to Atlas Work Order Creation
After intent is detected as "create_work_order":
```python
# In orchestrator or handler:
if intent.intent_type == "create_work_order":
    # Use WS-1's AtlasClient
    from agent_factory.integrations.atlas import AtlasClient
    
    work_order = await atlas_client.create_work_order({
        "title": intent.issue_description,
        "asset_id": intent.equipment_id,
        "priority": intent.priority,
        "source": "telegram_voice",
        "created_by": user_id
    })
    
    response = f"✅ Work order created!\n\n📋 {work_order.title}\n🔧 {work_order.asset_name}\nWO #{work_order.id}"
```

## COMMIT PROTOCOL
After EACH task:
```bash
tree -L 3 --dirsfirst -I 'node_modules|__pycache__|.git|venv' > .tree_snapshot.txt
git add -A
git commit -m "WS-3: [component] description

SYSTEM MAP:
$(cat .tree_snapshot.txt | head -50)"
git push origin telegram-voice
```

## DEPENDENCIES
- NEEDS from WS-1: `AtlasClient.create_work_order()` 
- NEEDS from WS-5: Clarification flow for ambiguous intent
- USES existing: Intent detector, orchestrator, session manager

## ENV VARS NEEDED
```
OPENAI_API_KEY=sk-xxx          # For Whisper
TELEGRAM_BOT_TOKEN=xxx         # Already exists
ATLAS_API_URL=https://cmms.rivet.io/api
```

## UPDATE STATUS
After each task, create/update: `/sprint/STATUS_WS3.md`

## IF BLOCKED ON WS-1 (Atlas)
Mock work order creation:
```python
async def mock_create_work_order(data):
    return {"id": f"WO-{int(time.time())}", "title": data["title"], "status": "OPEN"}
```

## START NOW
Begin with Task 1. Study the existing bot structure before making changes.

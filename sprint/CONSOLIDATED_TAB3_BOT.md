# TAB 3: BOT COMPLETE
# Copy everything below into Claude Code CLI

You are Tab 3 in a 3-tab sprint to build Rivet - AI-powered CMMS for field technicians.

## AUTONOMOUS MODE SETTINGS
- Auto-accept all file edits
- Auto-accept bash commands except: rm -rf, sudo, DROP, DELETE
- Commit after each completed phase

## YOUR IDENTITY
- Workstream: Telegram Bot + AI
- Branch: bot-complete
- Focus: Voice, Context Extraction, Prints, Response Synthesis, All Commands

## FIRST ACTIONS
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
git checkout -b bot-complete
git push -u origin bot-complete
```

## DEPENDENCIES
Tab 1 creates (use when ready, mock if not):
- `agent_factory/knowledge/vector_store.py` - VectorStore class
- `agent_factory/knowledge/manual_search.py` - ManualSearch class
- `agent_factory/knowledge/print_indexer.py` - PrintIndexer class
- `agent_factory/intake/equipment_taxonomy.py` - Equipment identification
- Database methods for machines, prints, manuals

---

## PHASE 1: CONTEXT EXTRACTOR (Day 1)

### Task 1.1: Data Models
Create `agent_factory/intake/models.py`:
```python
"""Data models for intelligent intake."""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

class IssueType(Enum):
    FAULT_CODE = "fault_code"
    WONT_START = "wont_start"
    INTERMITTENT = "intermittent"
    NOISE_VIBRATION = "noise_vibration"
    OVERHEATING = "overheating"
    COMMUNICATION = "communication"
    UNKNOWN = "unknown"

@dataclass
class EquipmentContext:
    """Rich context extracted from user message."""
    raw_message: str
    component_name: str = ""
    component_family: str = ""
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    category: str = ""
    issue_type: IssueType = IssueType.UNKNOWN
    fault_code: Optional[str] = None
    symptoms: List[str] = field(default_factory=list)
    location: Optional[str] = None
    urgency: str = "medium"
    search_keywords: List[str] = field(default_factory=list)
    confidence: float = 0.0
    needs_clarification: bool = False
    clarification_prompt: Optional[str] = None

@dataclass
class ManualResult:
    """Result from manual search."""
    title: str
    manufacturer: str
    page_num: int
    snippet: str
    score: float
```

### Task 1.2: Context Extractor
Create `agent_factory/intake/context_extractor.py`:
```python
"""Extract equipment context from messages."""
import anthropic
import json
import re
import logging
from typing import List

from .models import EquipmentContext, IssueType

logger = logging.getLogger(__name__)

# Try to import taxonomy, mock if not available
try:
    from .equipment_taxonomy import identify_component, extract_fault_code
except ImportError:
    def identify_component(text):
        return {"family": None, "category": None, "manufacturer": None}
    def extract_fault_code(text):
        match = re.search(r'\b[fFeE]\d{1,4}\b', text)
        return match.group(0).upper() if match else None


class ContextExtractor:
    """Extract equipment context using Claude + rules."""
    
    PROMPT = '''Analyze this maintenance technician's message and extract equipment context as JSON.

Message: "{message}"

Return ONLY valid JSON:
{{
    "component_name": "specific model if mentioned",
    "component_family": "VFD, PLC, motor, sensor, etc.",
    "manufacturer": "brand name if identifiable",
    "category": "Motor Controls, PLCs, Sensors, etc.",
    "issue_type": "fault_code|wont_start|intermittent|noise_vibration|overheating|communication|unknown",
    "fault_code": "exact code if mentioned",
    "symptoms": ["list of symptoms"],
    "urgency": "critical|high|medium|low",
    "confidence": 0.0-1.0,
    "needs_clarification": true/false,
    "clarification_prompt": "question if needed"
}}'''

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = "claude-sonnet-4-20250514"
    
    async def extract(self, message: str) -> EquipmentContext:
        """Extract context from message."""
        # Rule-based first
        context = self._rule_extract(message)
        
        # Enhance with Claude
        try:
            claude_data = await self._claude_extract(message)
            context = self._merge(context, claude_data)
        except Exception as e:
            logger.warning(f"Claude extraction failed: {e}")
        
        # Generate search keywords
        context.search_keywords = self._gen_keywords(context)
        
        return context
    
    def _rule_extract(self, message: str) -> EquipmentContext:
        """Fast rule-based extraction."""
        component = identify_component(message)
        fault_code = extract_fault_code(message)
        
        # Detect issue type
        issue_type = IssueType.UNKNOWN
        msg_lower = message.lower()
        if fault_code or "fault" in msg_lower or "error" in msg_lower:
            issue_type = IssueType.FAULT_CODE
        elif "won't start" in msg_lower or "no start" in msg_lower:
            issue_type = IssueType.WONT_START
        elif "noise" in msg_lower or "vibrat" in msg_lower:
            issue_type = IssueType.NOISE_VIBRATION
        
        # Detect urgency
        urgency = "medium"
        if any(w in msg_lower for w in ["down", "stopped", "urgent", "emergency"]):
            urgency = "critical"
        elif any(w in msg_lower for w in ["asap", "important"]):
            urgency = "high"
        
        return EquipmentContext(
            raw_message=message,
            component_family=component.get("family") or "",
            category=component.get("category") or "",
            manufacturer=component.get("manufacturer"),
            issue_type=issue_type,
            fault_code=fault_code,
            urgency=urgency,
            confidence=0.5 if component.get("family") else 0.2
        )
    
    async def _claude_extract(self, message: str) -> dict:
        """Use Claude for rich extraction."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=800,
            messages=[{"role": "user", "content": self.PROMPT.format(message=message)}]
        )
        
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = re.sub(r'^```json?\n?', '', text)
            text = re.sub(r'\n?```$', '', text)
        
        return json.loads(text)
    
    def _merge(self, ctx: EquipmentContext, data: dict) -> EquipmentContext:
        """Merge Claude data into context."""
        ctx.component_name = data.get("component_name") or ctx.component_name
        ctx.component_family = data.get("component_family") or ctx.component_family
        ctx.manufacturer = data.get("manufacturer") or ctx.manufacturer
        ctx.category = data.get("category") or ctx.category
        ctx.fault_code = data.get("fault_code") or ctx.fault_code
        ctx.symptoms = data.get("symptoms", [])
        ctx.urgency = data.get("urgency") or ctx.urgency
        ctx.confidence = data.get("confidence", 0.7)
        ctx.needs_clarification = data.get("needs_clarification", False)
        ctx.clarification_prompt = data.get("clarification_prompt")
        
        issue_str = data.get("issue_type", "unknown")
        try:
            ctx.issue_type = IssueType(issue_str)
        except ValueError:
            pass
        
        return ctx
    
    def _gen_keywords(self, ctx: EquipmentContext) -> List[str]:
        """Generate search keywords."""
        kw = []
        if ctx.component_name:
            kw.append(ctx.component_name)
        if ctx.component_family:
            kw.append(ctx.component_family)
        if ctx.manufacturer:
            kw.append(ctx.manufacturer)
        if ctx.fault_code:
            kw.append(f"fault {ctx.fault_code}")
        kw.extend(ctx.symptoms[:2])
        return list(set(kw))
```

**COMMIT:**
```bash
git add -A && git commit -m "bot: context extractor" && git push
```

---

## PHASE 2: RESPONSE SYNTHESIZER (Day 2)

### Task 2.1: Response Synthesizer
Create `agent_factory/intake/response_synthesizer.py`:
```python
"""Synthesize responses with manual content."""
import anthropic
from typing import List
import logging

from .models import EquipmentContext, ManualResult

logger = logging.getLogger(__name__)


class ResponseSynthesizer:
    """Combine context + manual results into helpful response."""
    
    SYSTEM = '''You are an expert industrial maintenance assistant helping field technicians.

RULES:
1. ALWAYS include safety warnings for electrical/hydraulic work
2. Cite sources with page numbers when available
3. Be specific about wire colors, terminals, components
4. Prioritize de-energization and LOTO
5. If info is limited, say so and suggest next steps'''

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = "claude-sonnet-4-20250514"
    
    async def synthesize(
        self,
        context: EquipmentContext,
        manual_results: List[ManualResult],
        user_query: str
    ) -> dict:
        """Synthesize response from context and manual results."""
        
        manual_content = self._format_manuals(manual_results)
        response = await self._generate(context, manual_content, user_query)
        safety = self._safety_warnings(context)
        sources = [{"title": r.title, "page": r.page_num} for r in manual_results[:3]]
        
        return {
            "response": response,
            "sources": sources,
            "safety_warnings": safety,
            "has_manual_content": len(manual_results) > 0
        }
    
    def _format_manuals(self, results: List[ManualResult]) -> str:
        """Format manual results for prompt."""
        if not results:
            return "No specific manual content found."
        
        sections = []
        for r in results[:3]:
            sections.append(f"**[{r.title}** (p.{r.page_num})]:\n{r.snippet}")
        return "\n\n".join(sections)
    
    async def _generate(self, ctx: EquipmentContext, manual_content: str, query: str) -> str:
        """Generate response with Claude."""
        prompt = f'''Technician's question: "{query}"

Equipment:
- Component: {ctx.component_name or ctx.component_family or "Unknown"}
- Manufacturer: {ctx.manufacturer or "Unknown"}
- Fault Code: {ctx.fault_code or "None"}
- Symptoms: {", ".join(ctx.symptoms) if ctx.symptoms else "Not specified"}

Manual content:
{manual_content}

Provide a helpful response:
1. Answer their question directly
2. Include troubleshooting steps if relevant
3. Add safety warnings
4. Cite manual sources'''

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1200,
                system=self.SYSTEM,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude failed: {e}")
            return self._fallback(ctx, manual_content)
    
    def _fallback(self, ctx: EquipmentContext, manual_content: str) -> str:
        """Fallback response if Claude fails."""
        component = ctx.component_name or ctx.component_family or "Equipment"
        return f"""🔧 **{component}**

{manual_content}

⚠️ Always follow lockout/tagout before servicing.

Need more specific help? Upload the equipment manual with /upload_manual."""
    
    def _safety_warnings(self, ctx: EquipmentContext) -> List[str]:
        """Generate appropriate safety warnings."""
        warnings = []
        family = (ctx.component_family or "").lower()
        
        if any(kw in family for kw in ["vfd", "drive", "motor", "electrical", "panel"]):
            warnings.append("⚠️ De-energize and verify zero energy before servicing")
            warnings.append("⚠️ VFDs retain voltage in capacitors - wait 5+ minutes")
        
        if not warnings:
            warnings.append("⚠️ Follow facility lockout/tagout procedures")
        
        return warnings


class TelegramFormatter:
    """Format responses for Telegram."""
    
    MAX_LEN = 4096
    
    @staticmethod
    def format(result: dict) -> str:
        """Format synthesis result for Telegram."""
        response = result["response"]
        sources = result.get("sources", [])
        warnings = result.get("safety_warnings", [])
        
        # Add sources if not in response
        if sources and "Source" not in response:
            response += "\n\n📄 **Sources:**\n"
            for s in sources:
                response += f"• {s['title']} (p.{s['page']})\n"
        
        # Add warnings if not prominent
        if warnings and "⚠️" not in response[:500]:
            response += "\n\n" + "\n".join(warnings)
        
        # Truncate if needed
        if len(response) > TelegramFormatter.MAX_LEN:
            response = response[:TelegramFormatter.MAX_LEN - 50] + "\n\n... (truncated)"
        
        return response
    
    @staticmethod
    def format_no_results(ctx: EquipmentContext) -> str:
        """Format when no manual content found."""
        component = ctx.component_name or ctx.component_family or "this equipment"
        mfr = f" ({ctx.manufacturer})" if ctx.manufacturer else ""
        
        return f"""🔍 I identified **{component}**{mfr} but don't have specific manuals yet.

**What you can do:**
1. Upload the manual: /upload_manual
2. Ask a general question
3. Check manufacturer website

**General guidance:**
• Always follow lockout/tagout
• Document fault codes and symptoms
• Check power, connections, fuses first

Want me to help with general troubleshooting?"""
```

**COMMIT:**
```bash
git add -A && git commit -m "bot: response synthesizer" && git push
```

---

## PHASE 3: VOICE TRANSCRIPTION (Day 2)

### Task 3.1: Whisper Integration
Create `agent_factory/integrations/telegram/voice.py`:
```python
"""Voice message transcription with Whisper."""
import openai
from pathlib import Path
import tempfile
import logging

logger = logging.getLogger(__name__)

class VoiceTranscriber:
    """Transcribe voice messages using OpenAI Whisper."""
    
    def __init__(self):
        self.client = openai.OpenAI()
    
    async def transcribe(self, audio_path: Path) -> str:
        """Transcribe audio file to text."""
        try:
            with open(audio_path, "rb") as f:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language="en"
                )
            
            text = response.text.strip()
            logger.info(f"Transcribed: {text[:100]}...")
            return text
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
    
    async def transcribe_telegram_voice(self, bot, voice_message) -> str:
        """Download and transcribe Telegram voice message."""
        # Download voice file
        file = await bot.get_file(voice_message.file_id)
        
        temp_path = Path(tempfile.mktemp(suffix=".ogg"))
        await file.download_to_drive(temp_path)
        
        try:
            text = await self.transcribe(temp_path)
            return text
        finally:
            temp_path.unlink(missing_ok=True)
```

**COMMIT:**
```bash
git add -A && git commit -m "bot: voice transcription" && git push
```

---

## PHASE 4: INTELLIGENT INTAKE HANDLER (Day 3)

### Task 4.1: Main Intake Handler
Create `agent_factory/intake/telegram_intake.py`:
```python
"""Intelligent intake handler for all Telegram messages."""
import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes

from .context_extractor import ContextExtractor
from .response_synthesizer import ResponseSynthesizer, TelegramFormatter
from .models import EquipmentContext, ManualResult

logger = logging.getLogger(__name__)

# Try imports, mock if not ready
try:
    from agent_factory.knowledge.manual_search import ManualSearch
    from agent_factory.knowledge.vector_store import VectorStore
except ImportError:
    ManualSearch = None
    VectorStore = None


class IntelligentIntakeHandler:
    """Process every message with context extraction and proactive help."""
    
    def __init__(self):
        self.extractor = ContextExtractor()
        self.synthesizer = ResponseSynthesizer()
        self.formatter = TelegramFormatter()
        self.manual_search = ManualSearch() if ManualSearch else None
    
    async def process(self, message: str, user_id: str) -> dict:
        """
        Process message with full intelligence.
        
        Returns:
            {
                "response": str,
                "context": EquipmentContext,
                "manual_results": list,
                "needs_clarification": bool
            }
        """
        # 1. Extract context
        context = await self.extractor.extract(message)
        logger.info(f"Context: {context.component_name}, {context.manufacturer}, {context.fault_code}")
        
        # 2. Check if clarification needed
        if context.needs_clarification and context.clarification_prompt:
            return {
                "response": context.clarification_prompt,
                "context": context,
                "manual_results": [],
                "needs_clarification": True
            }
        
        # 3. Search manuals
        manual_results = []
        if self.manual_search and context.confidence > 0.3:
            for kw in context.search_keywords[:2]:
                results = self.manual_search.search(kw, top_k=2, manufacturer=context.manufacturer)
                manual_results.extend([
                    ManualResult(
                        title=r.title,
                        manufacturer=r.manufacturer,
                        page_num=r.page_num,
                        snippet=r.snippet,
                        score=r.score
                    ) for r in results
                ])
        
        # 4. Synthesize response
        if manual_results:
            synthesis = await self.synthesizer.synthesize(context, manual_results, message)
            response = self.formatter.format(synthesis)
        else:
            response = self.formatter.format_no_results(context)
        
        return {
            "response": response,
            "context": context,
            "manual_results": manual_results,
            "needs_clarification": False
        }


# Telegram handler
async def intelligent_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main message handler with intelligent intake."""
    message = update.message.text
    user_id = str(update.effective_user.id)
    
    # Get or create handler
    if "intake" not in context.bot_data:
        context.bot_data["intake"] = IntelligentIntakeHandler()
    
    handler = context.bot_data["intake"]
    
    await update.message.chat.send_action("typing")
    
    result = await handler.process(message, user_id)
    
    # Send response (split if too long)
    response = result["response"]
    if len(response) > 4096:
        for i in range(0, len(response), 4096):
            await update.message.reply_text(response[i:i+4096])
    else:
        await update.message.reply_text(response)
    
    # Store context for follow-up
    context.user_data["last_context"] = result["context"]
```

**COMMIT:**
```bash
git add -A && git commit -m "bot: intelligent intake handler" && git push
```

---

## PHASE 5: PRINT COMMANDS (Day 3-4)

### Task 5.1: Print Handlers
Create `agent_factory/integrations/telegram/print_handlers.py`:
```python
"""Telegram handlers for print upload and query."""
import tempfile
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import logging

logger = logging.getLogger(__name__)

# Try imports
try:
    from agent_factory.knowledge.print_indexer import PrintIndexer
    from agent_factory.knowledge.vector_store import VectorStore
    from agent_factory.rivet_pro.database import DatabaseManager
except ImportError:
    PrintIndexer = None
    VectorStore = None
    DatabaseManager = None

# Conversation states
WAITING_MACHINE, WAITING_PRINT = range(2)


async def add_machine_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /add_machine <name> command."""
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /add_machine <machine_name>\n\nExample: /add_machine Lathe_1")
        return
    
    machine_name = " ".join(args)
    user_id = str(update.effective_user.id)
    
    if DatabaseManager:
        db = DatabaseManager()
        await db.connect()
        machine = await db.create_machine(user_id, machine_name)
        await update.message.reply_text(f"✅ Machine **{machine_name}** created!\n\nUpload prints with:\n/upload_print {machine_name}")
    else:
        await update.message.reply_text(f"✅ Machine **{machine_name}** created! (DB not connected)")


async def list_machines_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /list_machines command."""
    user_id = str(update.effective_user.id)
    
    if DatabaseManager:
        db = DatabaseManager()
        await db.connect()
        machines = await db.get_user_machines(user_id)
        
        if machines:
            msg = "🏭 **Your Machines:**\n\n"
            for m in machines:
                msg += f"• {m['name']}\n"
            msg += "\nUpload prints: /upload_print <machine>"
        else:
            msg = "No machines yet.\n\nCreate one: /add_machine <name>"
    else:
        msg = "Database not connected."
    
    await update.message.reply_text(msg)


async def upload_print_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /upload_print <machine> command."""
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /upload_print <machine_name>\n\nExample: /upload_print Lathe_1")
        return
    
    machine_name = " ".join(args)
    context.user_data["upload_machine"] = machine_name
    context.user_data["awaiting_print"] = True
    
    await update.message.reply_text(
        f"📄 **Upload Print for {machine_name}**\n\n"
        "Send a PDF of the electrical print or schematic.\n\n"
        "/cancel to abort"
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle uploaded PDF documents."""
    if not context.user_data.get("awaiting_print"):
        return
    
    context.user_data["awaiting_print"] = False
    
    doc = update.message.document
    if not doc.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("Please send a PDF file.")
        return
    
    machine_name = context.user_data.get("upload_machine", "Unknown")
    user_id = str(update.effective_user.id)
    
    await update.message.reply_text("📥 Processing print...")
    
    # Download file
    file = await context.bot.get_file(doc.file_id)
    temp_path = Path(tempfile.mktemp(suffix=".pdf"))
    await file.download_to_drive(temp_path)
    
    try:
        if PrintIndexer and DatabaseManager:
            db = DatabaseManager()
            await db.connect()
            
            # Get or create machine
            machine = await db.get_machine_by_name(user_id, machine_name)
            if not machine:
                machine = await db.create_machine(user_id, machine_name)
            
            # Create print record
            print_record = await db.create_print(
                machine["id"], user_id, doc.file_name, str(temp_path)
            )
            
            # Index the print
            indexer = PrintIndexer()
            result = indexer.index_print(
                temp_path,
                str(print_record["id"]),
                user_id,
                str(machine["id"]),
                doc.file_name
            )
            
            if result["success"]:
                await db.update_print_vectorized(
                    print_record["id"],
                    result["chunk_count"],
                    result["collection_name"]
                )
                
                await update.message.reply_text(
                    f"✅ **Print Uploaded!**\n\n"
                    f"📄 {doc.file_name}\n"
                    f"🔧 Machine: {machine_name}\n"
                    f"📑 Pages: {result['page_count']}\n"
                    f"🧩 Chunks: {result['chunk_count']}\n\n"
                    f"Use /chat_print {machine_name} to ask questions!"
                )
            else:
                await update.message.reply_text(f"❌ Failed: {result.get('error')}")
        else:
            await update.message.reply_text("✅ Print received! (Indexer not connected)")
    
    finally:
        temp_path.unlink(missing_ok=True)


async def chat_print_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /chat_print <machine> command."""
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /chat_print <machine_name>")
        return
    
    machine_name = " ".join(args)
    user_id = str(update.effective_user.id)
    
    # Start print chat session
    context.user_data["print_chat_machine"] = machine_name
    context.user_data["print_chat_active"] = True
    
    if DatabaseManager:
        db = DatabaseManager()
        await db.connect()
        machine = await db.get_machine_by_name(user_id, machine_name)
        
        if machine:
            prints = await db.get_machine_prints(machine["id"])
            count = len(prints)
            await update.message.reply_text(
                f"🔍 **Chat with {machine_name} Prints**\n\n"
                f"📄 {count} print(s) loaded\n\n"
                "Ask me anything about the electrical prints!\n"
                "Examples:\n"
                "• What's the wire gauge for the main feeder?\n"
                "• Where is the E-stop circuit?\n"
                "• What components are on Panel 3?\n\n"
                "/end_chat to exit"
            )
        else:
            await update.message.reply_text(f"Machine '{machine_name}' not found. Create it with /add_machine {machine_name}")
    else:
        await update.message.reply_text(f"🔍 Chat started for {machine_name} (DB not connected)")


async def end_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /end_chat command."""
    context.user_data["print_chat_active"] = False
    context.user_data.pop("print_chat_machine", None)
    await update.message.reply_text("Chat session ended. Use /chat_print <machine> to start a new session.")


async def list_prints_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /list_prints <machine> command."""
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /list_prints <machine_name>")
        return
    
    machine_name = " ".join(args)
    user_id = str(update.effective_user.id)
    
    if DatabaseManager:
        db = DatabaseManager()
        await db.connect()
        machine = await db.get_machine_by_name(user_id, machine_name)
        
        if machine:
            prints = await db.get_machine_prints(machine["id"])
            if prints:
                msg = f"📄 **Prints for {machine_name}:**\n\n"
                for p in prints:
                    status = "✅" if p["vectorized"] else "⏳"
                    msg += f"{status} {p['name']}\n"
            else:
                msg = f"No prints for {machine_name} yet.\n\nUpload with /upload_print {machine_name}"
        else:
            msg = f"Machine '{machine_name}' not found."
    else:
        msg = "Database not connected."
    
    await update.message.reply_text(msg)
```

**COMMIT:**
```bash
git add -A && git commit -m "bot: print upload + query commands" && git push
```

---

## PHASE 6: MANUAL COMMANDS (Day 4)

### Task 6.1: Manual Upload Handler
Create `agent_factory/integrations/telegram/manual_handlers.py`:
```python
"""Manual library Telegram handlers."""
import tempfile
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

try:
    from agent_factory.knowledge.manual_indexer import ManualIndexer
    from agent_factory.rivet_pro.database import DatabaseManager
except ImportError:
    ManualIndexer = None
    DatabaseManager = None


async def upload_manual_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /upload_manual command."""
    context.user_data["awaiting_manual"] = True
    
    await update.message.reply_text(
        "📚 **Upload Equipment Manual**\n\n"
        "Send a PDF of an OEM manual.\n"
        "Best results with:\n"
        "• User manuals\n"
        "• Troubleshooting guides\n"
        "• Fault code references\n\n"
        "/cancel to abort"
    )


async def handle_manual_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle uploaded manual PDF."""
    if not context.user_data.get("awaiting_manual"):
        return False  # Not handled
    
    context.user_data["awaiting_manual"] = False
    
    doc = update.message.document
    if not doc.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("Please send a PDF file.")
        return True
    
    await update.message.reply_text("📥 Processing manual...")
    
    file = await context.bot.get_file(doc.file_id)
    temp_path = Path(tempfile.mktemp(suffix=".pdf"))
    await file.download_to_drive(temp_path)
    
    try:
        if ManualIndexer and DatabaseManager:
            import uuid
            
            db = DatabaseManager()
            await db.connect()
            
            manual = await db.create_manual(
                doc.file_name,
                "Unknown",  # Could prompt for manufacturer
                "Unknown",
                str(temp_path)
            )
            
            indexer = ManualIndexer()
            result = indexer.index_manual(
                temp_path,
                str(manual["id"]),
                doc.file_name,
                "Unknown",
                "Unknown"
            )
            
            if result["success"]:
                await db.update_manual_indexed(manual["id"], "equipment_manuals", result["page_count"])
                
                await update.message.reply_text(
                    f"✅ **Manual Indexed!**\n\n"
                    f"📄 {doc.file_name}\n"
                    f"📑 Pages: {result['page_count']}\n"
                    f"🧩 Chunks: {result['chunk_count']}\n\n"
                    "I'll reference this when you ask about this equipment!"
                )
            else:
                await update.message.reply_text(f"❌ Failed: {result.get('error')}")
        else:
            await update.message.reply_text("✅ Manual received! (Indexer not connected)")
    
    finally:
        temp_path.unlink(missing_ok=True)
    
    return True


async def manual_gaps_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /manual_gaps command."""
    if DatabaseManager:
        db = DatabaseManager()
        await db.connect()
        gaps = await db.get_top_manual_gaps(10)
        
        if gaps:
            msg = "📊 **Most Requested Missing Manuals:**\n\n"
            for i, g in enumerate(gaps, 1):
                msg += f"{i}. **{g['manufacturer']} {g['component_family']}** - {g['request_count']} requests\n"
            msg += "\nUpload these to improve assistance!"
        else:
            msg = "No manual gaps tracked yet."
    else:
        msg = "Database not connected."
    
    await update.message.reply_text(msg)
```

**COMMIT:**
```bash
git add -A && git commit -m "bot: manual library commands" && git push
```

---

## PHASE 7: BOT INTEGRATION (Day 4-5)

### Task 7.1: Register All Handlers
Create `agent_factory/integrations/telegram/register_handlers.py`:
```python
"""Register all handlers with the bot application."""
from telegram.ext import MessageHandler, CommandHandler, filters

from .print_handlers import (
    add_machine_command,
    list_machines_command,
    upload_print_command,
    chat_print_command,
    end_chat_command,
    list_prints_command,
    handle_document
)
from .manual_handlers import (
    upload_manual_command,
    handle_manual_document,
    manual_gaps_command
)
from .telegram_intake import intelligent_message_handler


def register_all_handlers(application):
    """Register all Rivet handlers with the bot."""
    
    # Machine commands
    application.add_handler(CommandHandler("add_machine", add_machine_command))
    application.add_handler(CommandHandler("list_machines", list_machines_command))
    
    # Print commands
    application.add_handler(CommandHandler("upload_print", upload_print_command))
    application.add_handler(CommandHandler("chat_print", chat_print_command))
    application.add_handler(CommandHandler("end_chat", end_chat_command))
    application.add_handler(CommandHandler("list_prints", list_prints_command))
    
    # Manual commands
    application.add_handler(CommandHandler("upload_manual", upload_manual_command))
    application.add_handler(CommandHandler("manual_gaps", manual_gaps_command))
    
    # Document handler (for PDF uploads)
    application.add_handler(MessageHandler(filters.Document.PDF, handle_pdf_upload))
    
    # Intelligent message handler (lowest priority)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, intelligent_message_handler),
        group=5
    )


async def handle_pdf_upload(update, context):
    """Route PDF uploads to correct handler."""
    # Check if waiting for manual
    if context.user_data.get("awaiting_manual"):
        await handle_manual_document(update, context)
        return
    
    # Check if waiting for print
    if context.user_data.get("awaiting_print"):
        await handle_document(update, context)
        return
    
    # Prompt user
    await update.message.reply_text(
        "📄 I received a PDF!\n\n"
        "What would you like to do?\n"
        "• /upload_print <machine> - Add as electrical print\n"
        "• /upload_manual - Add to manual library"
    )
```

### Task 7.2: Update bot.py
Add to existing `agent_factory/integrations/telegram/bot.py`:
```python
# Add import at top
from .register_handlers import register_all_handlers

# In your setup function, after other handlers:
register_all_handlers(application)
```

### Task 7.3: Voice Handler
Add to bot.py:
```python
from .voice import VoiceTranscriber
from .telegram_intake import IntelligentIntakeHandler

transcriber = VoiceTranscriber()
intake = IntelligentIntakeHandler()

async def voice_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages."""
    voice = update.message.voice
    
    await update.message.reply_text("🎤 Transcribing...")
    
    try:
        text = await transcriber.transcribe_telegram_voice(context.bot, voice)
        await update.message.reply_text(f"📝 Heard: \"{text}\"")
        
        # Process through intelligent intake
        result = await intake.process(text, str(update.effective_user.id))
        await update.message.reply_text(result["response"])
        
    except Exception as e:
        await update.message.reply_text(f"❌ Transcription failed: {e}")

# Register voice handler
application.add_handler(MessageHandler(filters.VOICE, voice_message_handler))
```

**COMMIT:**
```bash
git add -A && git commit -m "bot: all handlers registered + voice" && git push
```

---

## PHASE 8: TESTING (Day 5)

### Task 8.1: Test Script
Create `test_bot.py`:
```python
"""Test bot components."""
import asyncio
from agent_factory.intake.context_extractor import ContextExtractor
from agent_factory.intake.response_synthesizer import ResponseSynthesizer
from agent_factory.intake.models import ManualResult

async def test_context():
    print("Testing context extraction...")
    extractor = ContextExtractor()
    
    messages = [
        "PowerFlex 525 showing fault F004",
        "The main pump motor won't start",
        "S7-1500 PLC has SF light on",
        "Proximity sensor not detecting parts"
    ]
    
    for msg in messages:
        ctx = await extractor.extract(msg)
        print(f"\nMessage: {msg}")
        print(f"  Component: {ctx.component_name or ctx.component_family}")
        print(f"  Manufacturer: {ctx.manufacturer}")
        print(f"  Fault Code: {ctx.fault_code}")
        print(f"  Issue Type: {ctx.issue_type.value}")

async def test_response():
    print("\n\nTesting response synthesis...")
    synth = ResponseSynthesizer()
    
    from agent_factory.intake.models import EquipmentContext, IssueType
    
    ctx = EquipmentContext(
        raw_message="PowerFlex fault F004",
        component_name="PowerFlex 525",
        component_family="VFD",
        manufacturer="Allen-Bradley",
        fault_code="F004",
        issue_type=IssueType.FAULT_CODE
    )
    
    # Mock manual result
    manual = ManualResult(
        title="PowerFlex 520 User Manual",
        manufacturer="Allen-Bradley",
        page_num=47,
        snippet="F004 - DC Bus Undervoltage. Check incoming power voltage...",
        score=0.85
    )
    
    result = await synth.synthesize(ctx, [manual], "PowerFlex showing F004")
    print(f"\nResponse:\n{result['response'][:500]}...")

if __name__ == "__main__":
    asyncio.run(test_context())
    asyncio.run(test_response())
```

Run: `python test_bot.py`

**FINAL COMMIT:**
```bash
git add -A && git commit -m "bot: complete with tests" && git push
```

---

## COMPLETE COMMAND REFERENCE

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | Show all commands |
| `/add_machine <name>` | Create a machine |
| `/list_machines` | Show your machines |
| `/upload_print <machine>` | Upload electrical print |
| `/list_prints <machine>` | Show machine's prints |
| `/chat_print <machine>` | Start Q&A session |
| `/end_chat` | End Q&A session |
| `/upload_manual` | Upload OEM manual |
| `/manual_gaps` | Show missing manuals |
| 🎤 Voice | Speak naturally |

---

## SUCCESS CRITERIA
- [ ] Context extractor identifies equipment
- [ ] Response synthesizer includes safety warnings
- [ ] Voice transcription works
- [ ] /upload_print accepts PDFs
- [ ] /chat_print enables Q&A
- [ ] /upload_manual indexes documents
- [ ] All commands registered in bot

## TAB 3 COMPLETE
Bot has full intelligent intake:
1. Text → Context extraction → Manual search → Rich response
2. Voice → Transcribe → Same pipeline
3. PDF → Index → Searchable

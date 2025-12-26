# WORKSTREAM 4: CHAT WITH PRINT (CLAUDE VISION)
# Computer 2, Tab 1
# Copy everything below this line into Claude Code CLI

You are WS-4 (Chat with Print) in a 6-instance parallel development sprint for Rivet MVP.

## AUTONOMOUS MODE SETTINGS
- Auto-accept all file edits
- Auto-accept bash commands except: rm -rf, sudo, DROP, DELETE
- Commit after each completed task
- If context feels long (5+ tasks done), checkpoint immediately

## YOUR IDENTITY
- Workstream: WS-4
- Branch: chat-with-print
- Focus: Claude Vision for schematic understanding

## FIRST ACTIONS (Do These Now)
1. Check if worktree exists: `git worktree list`
2. If not, create it: `git worktree add ../rivet-chat-print chat-with-print`
3. cd into worktree
4. Read this entire prompt before starting

## CRITICAL: OCR PIPELINE ALREADY EXISTS!
Look at existing vision code:
```
/agent_factory/integrations/telegram/ocr/
├── pipeline.py             # OCR processing - WORKING
├── providers.py            # Provider interface - WORKING
├── gemini_provider.py      # Gemini vision - WORKING
└── gpt4o_provider.py       # GPT-4O vision - WORKING
```

You are adding Claude Vision as a provider AND building the "Chat with Print" feature:
1. Claude Vision provider (add to existing pipeline)
2. Print metadata extraction (components, connections)
3. Q&A interface for prints
4. Feature flag by subscription tier

## YOUR TASKS (In Order)

### Task 1: Study Existing OCR Pipeline
```bash
cat /agent_factory/integrations/telegram/ocr/pipeline.py
cat /agent_factory/integrations/telegram/ocr/providers.py
cat /agent_factory/integrations/telegram/ocr/gemini_provider.py
```

Understand:
- Provider interface pattern
- How images are processed
- Where to add Claude provider

### Task 2: Create Claude Vision Provider
Create: `/agent_factory/integrations/telegram/ocr/claude_provider.py`:
```python
"""Claude Vision provider for schematic analysis."""
import anthropic
import base64
from pathlib import Path
from typing import Optional
from .providers import OCRProvider, OCRResult

class ClaudeVisionProvider(OCRProvider):
    """Use Claude's vision capabilities for schematic understanding."""
    
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = "claude-sonnet-4-20250514"
    
    async def analyze_image(
        self,
        image_path: Path,
        query: Optional[str] = None
    ) -> OCRResult:
        """
        Analyze an image using Claude Vision.
        
        Args:
            image_path: Path to image file
            query: Optional specific question about the image
            
        Returns:
            OCRResult with extracted text and metadata
        """
        # Read and encode image
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")
        
        # Determine media type
        suffix = image_path.suffix.lower()
        media_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg", 
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }.get(suffix, "image/png")
        
        # Build prompt
        if query:
            prompt = f"""Analyze this technical schematic/diagram and answer this question:
            
Question: {query}

Provide a detailed, accurate answer based on what you can see in the schematic."""
        else:
            prompt = """Analyze this technical schematic/diagram and extract:

1. **Components**: List all components visible (relays, contactors, motors, etc.)
2. **Connections**: Describe how components are connected
3. **Ratings**: Any voltage, current, or power ratings visible
4. **Labels**: All text labels and identifiers
5. **Circuit Function**: What does this circuit/system do?

Be specific and reference locations in the image (top-left, center, etc.)."""

        # Call Claude Vision
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )
        
        return OCRResult(
            text=response.content[0].text,
            provider="claude",
            confidence=0.95,  # Claude is highly accurate
            metadata={
                "model": self.model,
                "query": query,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens
            }
        )
```

### Task 3: Create Print Analyzer Service
Create: `/agent_factory/rivet_pro/print_analyzer.py`:
```python
"""Chat with Print - Schematic analysis and Q&A service."""
from typing import Optional, List
from pathlib import Path
from pydantic import BaseModel
from agent_factory.integrations.telegram.ocr.claude_provider import ClaudeVisionProvider

class PrintComponent(BaseModel):
    """A component extracted from a print."""
    name: str
    type: str  # relay, contactor, motor, sensor, etc.
    location: Optional[str]  # Position in schematic
    ratings: Optional[dict]  # Voltage, current, etc.

class PrintConnection(BaseModel):
    """A connection between components."""
    from_component: str
    to_component: str
    wire_label: Optional[str]
    connection_type: Optional[str]  # series, parallel, control, power

class PrintMetadata(BaseModel):
    """Full metadata extracted from a print."""
    components: List[PrintComponent]
    connections: List[PrintConnection]
    ratings: dict
    circuit_function: str
    raw_analysis: str

class PrintAnalyzer:
    """Analyze technical prints and answer questions."""
    
    def __init__(self):
        self.provider = ClaudeVisionProvider()
    
    async def extract_metadata(self, image_path: Path) -> PrintMetadata:
        """Extract structured metadata from a print."""
        result = await self.provider.analyze_image(image_path)
        
        # Parse Claude's response into structured format
        # This is a simplified version - enhance with better parsing
        return PrintMetadata(
            components=[],  # Parse from result.text
            connections=[],
            ratings={},
            circuit_function="",
            raw_analysis=result.text
        )
    
    async def answer_question(
        self,
        image_path: Path,
        question: str
    ) -> str:
        """Answer a specific question about a print."""
        result = await self.provider.analyze_image(image_path, query=question)
        return result.text
    
    async def get_bill_of_materials(self, image_path: Path) -> str:
        """Extract bill of materials from schematic."""
        question = """List all components in this schematic as a bill of materials:

Format:
- Qty x Component Name (Part Number if visible) - Rating

Example:
- 1x Main Contactor (CRA-01) - 230V/10A
- 2x Relay (Q1, Q2) - 24VDC"""
        
        return await self.answer_question(image_path, question)
```

### Task 4: Integrate with Telegram Bot
Add to `/agent_factory/integrations/telegram/rivet_pro_handlers.py`:
```python
from agent_factory.rivet_pro.print_analyzer import PrintAnalyzer

# Add handler for print Q&A
async def handle_print_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle questions about uploaded prints."""
    user_id = update.effective_user.id
    question = update.message.text
    
    # Check subscription tier (Pro or higher)
    user = await get_user(user_id)
    if user.tier not in ["pro", "enterprise"]:
        await update.message.reply_text(
            "📊 Chat with Print is a Pro feature.\n\n"
            "Upgrade to Pro to ask unlimited questions about your equipment schematics.\n"
            "/upgrade to see pricing"
        )
        return
    
    # Get user's current print (from session/context)
    print_path = context.user_data.get("current_print")
    if not print_path:
        await update.message.reply_text(
            "📎 Please upload a schematic first, then ask your question."
        )
        return
    
    # Analyze and answer
    analyzer = PrintAnalyzer()
    answer = await analyzer.answer_question(Path(print_path), question)
    
    await update.message.reply_text(answer)
```

### Task 5: Add Print Upload Handler
```python
async def handle_print_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle print/schematic upload."""
    user_id = update.effective_user.id
    
    # Get the document or photo
    if update.message.document:
        file = await context.bot.get_file(update.message.document.file_id)
        filename = update.message.document.file_name
    elif update.message.photo:
        file = await context.bot.get_file(update.message.photo[-1].file_id)
        filename = f"photo_{user_id}_{int(time.time())}.jpg"
    else:
        return
    
    # Save to user's print library
    save_path = Path(f"/data/prints/{user_id}/{filename}")
    save_path.parent.mkdir(parents=True, exist_ok=True)
    await file.download_to_drive(save_path)
    
    # Store in session
    context.user_data["current_print"] = str(save_path)
    
    # Initial analysis
    analyzer = PrintAnalyzer()
    metadata = await analyzer.extract_metadata(save_path)
    
    await update.message.reply_text(
        f"📊 Print uploaded and analyzed!\n\n"
        f"**What I found:**\n{metadata.raw_analysis[:500]}...\n\n"
        f"Ask me anything about this schematic! For example:\n"
        f"• 'What's connected to the relay?'\n"
        f"• 'Give me a bill of materials'\n"
        f"• 'How does this circuit work?'"
    )
    
    # Also upload to Atlas asset if linked (WS-1)
    if context.user_data.get("linked_asset_id"):
        from agent_factory.integrations.atlas import AtlasClient
        atlas = AtlasClient()
        await atlas.upload_asset_file(
            context.user_data["linked_asset_id"],
            save_path.read_bytes(),
            filename
        )
```

### Task 6: Feature Flag by Tier
Create: `/agent_factory/rivet_pro/feature_flags.py`:
```python
"""Feature access control by subscription tier."""

TIER_FEATURES = {
    "free": ["basic_chat", "equipment_lookup"],
    "basic": ["free_features", "voice_work_orders", "limited_prints"],
    "pro": ["basic_features", "chat_with_print", "unlimited_prints", "priority_support"],
    "enterprise": ["pro_features", "predictive_ai", "api_access", "sso"]
}

def has_feature(user_tier: str, feature: str) -> bool:
    """Check if a tier has access to a feature."""
    tier_features = TIER_FEATURES.get(user_tier, [])
    
    # Expand inherited features
    all_features = set()
    for f in tier_features:
        if f.endswith("_features"):
            parent = f.replace("_features", "")
            all_features.update(TIER_FEATURES.get(parent, []))
        else:
            all_features.add(f)
    
    return feature in all_features

def require_feature(feature: str):
    """Decorator to require a feature for a handler."""
    def decorator(func):
        async def wrapper(update, context, *args, **kwargs):
            user = await get_user(update.effective_user.id)
            if not has_feature(user.tier, feature):
                await update.message.reply_text(
                    f"⬆️ This feature requires an upgrade. /upgrade"
                )
                return
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator
```

## COMMIT PROTOCOL
After EACH task:
```bash
tree -L 3 --dirsfirst -I 'node_modules|__pycache__|.git|venv' > .tree_snapshot.txt
git add -A
git commit -m "WS-4: [component] description

SYSTEM MAP:
$(cat .tree_snapshot.txt | head -50)"
git push origin chat-with-print
```

## DEPENDENCIES
- NEEDS from WS-1: `AtlasClient.upload_asset_file()` for linking prints to assets
- PROVIDES to WS-3: Print analysis can be triggered after voice "analyze this schematic"

## ENV VARS NEEDED
```
ANTHROPIC_API_KEY=sk-ant-xxx   # For Claude Vision
```

## UPDATE STATUS
After each task, create/update: `/sprint/STATUS_WS4.md`

## START NOW
Begin with Task 1. Study the existing OCR pipeline before adding Claude.

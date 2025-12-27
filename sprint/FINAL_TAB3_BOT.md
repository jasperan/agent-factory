# TAB 3: BOT + AI INTELLIGENCE
## Phase 1 MVP + Atlas Vision Foundation

You are Tab 3 in a 3-tab sprint building Rivet - an AI-powered CMMS that learns from every interaction.

## THE VISION (Read First)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   EVERY MESSAGE MAKES THE SYSTEM SMARTER                                    │
│                                                                              │
│   Tech: "PowerFlex showing F004"                                            │
│                     │                                                        │
│                     ▼                                                        │
│   ┌─────────────────────────────────┐                                       │
│   │     CONTEXT EXTRACTOR           │  ← Identifies equipment, fault code   │
│   │     • Component: PowerFlex 525  │                                       │
│   │     • Manufacturer: A-B         │                                       │
│   │     • Fault: F004               │                                       │
│   └─────────────────┬───────────────┘                                       │
│                     │                                                        │
│                     ▼                                                        │
│   ┌─────────────────────────────────┐                                       │
│   │     KNOWLEDGE SEARCH            │  ← Searches prints + manuals          │
│   │     • User prints (ChromaDB)    │                                       │
│   │     • OEM manuals (ChromaDB)    │                                       │
│   │     • Knowledge atoms (Phase 2) │                                       │
│   └─────────────────┬───────────────┘                                       │
│                     │                                                        │
│                     ▼                                                        │
│   ┌─────────────────────────────────┐                                       │
│   │     RESPONSE SYNTHESIZER        │  ← Generates answer with citations    │
│   │     • Manual excerpts           │                                       │
│   │     • Safety warnings           │                                       │
│   │     • Troubleshooting steps     │                                       │
│   └─────────────────┬───────────────┘                                       │
│                     │                                                        │
│                     ▼                                                        │
│   ┌─────────────────────────────────┐                                       │
│   │     PHASE 2: LEARNING LOOP      │  ← Future: KB grows automatically     │
│   │     • Log research decisions    │                                       │
│   │     • Extract knowledge atoms   │                                       │
│   │     • Expert review → KB        │                                       │
│   └─────────────────────────────────┘                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## AUTONOMOUS MODE SETTINGS
- Auto-accept all file edits
- Auto-accept bash commands except: rm -rf, sudo, DROP, DELETE
- Commit after each completed phase

## YOUR IDENTITY
- Workstream: Telegram Bot + AI Intelligence
- Branch: bot-complete
- Focus: Voice, Context Extraction, Prints, Response Synthesis

## FIRST ACTIONS
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
git checkout -b bot-complete
git push -u origin bot-complete
```

## DEPENDENCIES ON TAB 1
Tab 1 creates these (wait for them or mock):
- `agent_factory/knowledge/vector_store.py`
- `agent_factory/knowledge/manual_search.py`
- `agent_factory/knowledge/print_indexer.py`
- `agent_factory/intake/equipment_taxonomy.py`
- `agent_factory/rivet_pro/database.py`

---

# PHASE 1: DATA MODELS (Day 1)

## Task 1.1: Intake Models
Create `agent_factory/intake/models.py`:

```python
"""
Data models for intelligent intake system.
Phase 1: Core context extraction
Phase 2 Prep: Ready for knowledge atoms integration
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class IssueType(Enum):
    """Types of maintenance issues."""
    FAULT_CODE = "fault_code"
    WONT_START = "wont_start"
    INTERMITTENT = "intermittent"
    NOISE_VIBRATION = "noise_vibration"
    OVERHEATING = "overheating"
    COMMUNICATION = "communication"
    CALIBRATION = "calibration"
    PHYSICAL_DAMAGE = "physical_damage"
    PERFORMANCE = "performance"
    LEAK = "leak"
    UNKNOWN = "unknown"


class WorkContext(Enum):
    """Context of the maintenance work."""
    TROUBLESHOOTING = "troubleshooting"
    INSTALLATION = "installation"
    MAINTENANCE = "maintenance"
    REPLACEMENT = "replacement"
    PROGRAMMING = "programming"
    COMMISSIONING = "commissioning"
    INSPECTION = "inspection"


@dataclass
class EquipmentContext:
    """
    Rich context extracted from technician message.
    This is the core data structure for intelligent routing.
    """
    # Original message
    raw_message: str
    
    # Component identification
    component_name: str = ""          # "PowerFlex 525"
    component_family: str = ""        # "Variable Frequency Drive"
    manufacturer: Optional[str] = None  # "Allen-Bradley"
    model_number: Optional[str] = None  # "25B-D030N114"
    category: str = ""                # "Motor Controls"
    
    # Issue details
    issue_type: IssueType = IssueType.UNKNOWN
    fault_code: Optional[str] = None  # "F004"
    symptoms: List[str] = field(default_factory=list)
    
    # Work context
    work_context: WorkContext = WorkContext.TROUBLESHOOTING
    location: Optional[str] = None    # "Line 2", "Panel 3"
    urgency: str = "medium"           # "critical", "high", "medium", "low"
    
    # Search optimization
    search_keywords: List[str] = field(default_factory=list)
    manual_search_queries: List[str] = field(default_factory=list)
    
    # Confidence and clarification
    confidence: float = 0.0
    needs_clarification: bool = False
    clarification_prompt: Optional[str] = None
    
    # Phase 2: Link to research job
    # research_job_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "component_name": self.component_name,
            "component_family": self.component_family,
            "manufacturer": self.manufacturer,
            "model_number": self.model_number,
            "category": self.category,
            "issue_type": self.issue_type.value,
            "fault_code": self.fault_code,
            "symptoms": self.symptoms,
            "work_context": self.work_context.value,
            "location": self.location,
            "urgency": self.urgency,
            "confidence": self.confidence,
            "needs_clarification": self.needs_clarification
        }


@dataclass
class ManualResult:
    """Result from manual/print search."""
    title: str
    manufacturer: str
    page_num: int
    snippet: str
    score: float
    source_type: str = "manual"  # "manual", "print", "atom" (Phase 2)
    source_id: Optional[str] = None
    
    # Phase 2: Track if this came from knowledge atom
    # atom_id: Optional[str] = None
    # verified_by_expert: bool = False


@dataclass
class SynthesizedResponse:
    """Complete response with all components."""
    main_response: str
    sources: List[Dict[str, Any]]
    safety_warnings: List[str]
    has_manual_content: bool
    confidence: float
    
    # Phase 2: Track for learning loop
    # atoms_used: List[str] = field(default_factory=list)
    # should_extract_atoms: bool = False
```

**COMMIT:**
```bash
git add -A && git commit -m "bot: intake data models" && git push
```

---

# PHASE 2: CONTEXT EXTRACTOR (Day 1-2)

## Task 2.1: Context Extractor
Create `agent_factory/intake/context_extractor.py`:

```python
"""
Context Extractor - The brain of intelligent intake.
Phase 1: Rule-based + Claude extraction
Phase 2 Prep: Integrate with knowledge atoms for better extraction
"""
import anthropic
import json
import re
import logging
from typing import List, Optional

from .models import EquipmentContext, IssueType, WorkContext

logger = logging.getLogger(__name__)

# Import taxonomy (from Tab 1)
try:
    from .equipment_taxonomy import (
        identify_component, identify_issue_type, 
        identify_urgency, extract_fault_code, extract_model_number
    )
    TAXONOMY_AVAILABLE = True
except ImportError:
    TAXONOMY_AVAILABLE = False
    logger.warning("Equipment taxonomy not available, using basic extraction")


class ContextExtractor:
    """
    Extract rich equipment context from technician messages.
    
    Uses hybrid approach:
    1. Fast rule-based extraction (taxonomy patterns)
    2. Claude enhancement for nuance and clarification
    
    Phase 2: Will also query knowledge_atoms for context enrichment
    """
    
    EXTRACTION_PROMPT = '''Analyze this maintenance technician's message and extract equipment context.

Message: "{message}"

Return ONLY valid JSON (no markdown, no explanation):
{{
    "component_name": "specific model mentioned (e.g., 'PowerFlex 525')",
    "component_family": "general type (VFD, PLC, motor, sensor, etc.)",
    "manufacturer": "brand if identifiable (Allen-Bradley, Siemens, etc.)",
    "model_number": "specific model number if mentioned",
    "category": "Motor Controls, PLCs, Sensors, Safety, Pneumatics, etc.",
    "issue_type": "fault_code|wont_start|intermittent|noise_vibration|overheating|communication|calibration|physical_damage|performance|unknown",
    "fault_code": "exact fault/error code if mentioned (e.g., 'F004', 'E-47')",
    "symptoms": ["list", "of", "symptoms", "mentioned"],
    "location": "where equipment is located if mentioned",
    "urgency": "critical|high|medium|low",
    "confidence": 0.0 to 1.0,
    "needs_clarification": true or false,
    "clarification_prompt": "question to ask if more info needed (or null)"
}}

Rules:
1. Be specific about component names when mentioned
2. Identify manufacturer from model names (PowerFlex = Allen-Bradley, S7 = Siemens)
3. Extract exact fault codes in their original format
4. Set needs_clarification=true if critical info is missing (like fault code for a fault report)
5. Generate a helpful, specific clarification question when needed'''

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = "claude-sonnet-4-20250514"
    
    async def extract(self, message: str, 
                     conversation_history: List[dict] = None) -> EquipmentContext:
        """
        Extract equipment context from message.
        
        Args:
            message: The technician's message
            conversation_history: Previous messages for multi-turn context
            
        Returns:
            EquipmentContext with all extracted information
        """
        # Start with rule-based extraction (fast)
        context = self._rule_based_extract(message)
        
        # Enhance with Claude (more nuanced)
        try:
            claude_data = await self._claude_extract(message, conversation_history)
            context = self._merge_contexts(context, claude_data)
        except Exception as e:
            logger.warning(f"Claude extraction failed: {e}, using rule-based only")
        
        # Generate search queries
        context.search_keywords = self._generate_search_keywords(context)
        context.manual_search_queries = self._generate_manual_queries(context)
        
        return context
    
    def _rule_based_extract(self, message: str) -> EquipmentContext:
        """Fast rule-based extraction using taxonomy patterns."""
        context = EquipmentContext(raw_message=message)
        
        if TAXONOMY_AVAILABLE:
            # Use full taxonomy
            component = identify_component(message)
            context.component_family = component.get("family") or ""
            context.category = component.get("category") or ""
            context.manufacturer = component.get("manufacturer")
            
            context.issue_type = IssueType(identify_issue_type(message))
            context.urgency = identify_urgency(message)
            context.fault_code = extract_fault_code(message)
            context.model_number = extract_model_number(message)
            context.confidence = 0.6 if component.get("family") else 0.3
        else:
            # Basic fallback extraction
            context = self._basic_extract(message)
        
        return context
    
    def _basic_extract(self, message: str) -> EquipmentContext:
        """Basic extraction when taxonomy not available."""
        context = EquipmentContext(raw_message=message)
        msg_lower = message.lower()
        
        # Basic component detection
        if any(w in msg_lower for w in ["vfd", "drive", "powerflex", "sinamics"]):
            context.component_family = "Variable Frequency Drive"
            context.category = "Motor Controls"
            if "powerflex" in msg_lower:
                context.manufacturer = "Allen-Bradley"
            elif "sinamics" in msg_lower:
                context.manufacturer = "Siemens"
        
        if any(w in msg_lower for w in ["plc", "controllogix", "s7"]):
            context.component_family = "PLC"
            context.category = "PLCs & Controllers"
        
        # Fault code
        fault_match = re.search(r'\b[fFeE]\d{1,4}\b', message)
        if fault_match:
            context.fault_code = fault_match.group(0).upper()
            context.issue_type = IssueType.FAULT_CODE
        
        # Urgency
        if any(w in msg_lower for w in ["down", "stopped", "urgent", "emergency"]):
            context.urgency = "critical"
        
        context.confidence = 0.4
        return context
    
    async def _claude_extract(self, message: str, 
                             history: List[dict] = None) -> dict:
        """Use Claude for rich context extraction."""
        messages = []
        
        # Add conversation history if available
        if history:
            for h in history[-4:]:  # Last 4 turns
                messages.append({"role": h["role"], "content": h["content"]})
        
        messages.append({
            "role": "user",
            "content": self.EXTRACTION_PROMPT.format(message=message)
        })
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=800,
            messages=messages
        )
        
        text = response.content[0].text.strip()
        
        # Handle markdown code blocks
        if text.startswith("```"):
            text = re.sub(r'^```json?\n?', '', text)
            text = re.sub(r'\n?```$', '', text)
        
        return json.loads(text)
    
    def _merge_contexts(self, rule_ctx: EquipmentContext, 
                       claude_data: dict) -> EquipmentContext:
        """Merge rule-based and Claude extractions, preferring Claude when available."""
        # Component identification
        rule_ctx.component_name = claude_data.get("component_name") or rule_ctx.component_name
        rule_ctx.component_family = claude_data.get("component_family") or rule_ctx.component_family
        rule_ctx.manufacturer = claude_data.get("manufacturer") or rule_ctx.manufacturer
        rule_ctx.model_number = claude_data.get("model_number") or rule_ctx.model_number
        rule_ctx.category = claude_data.get("category") or rule_ctx.category
        
        # Issue details
        issue_str = claude_data.get("issue_type", "unknown")
        try:
            rule_ctx.issue_type = IssueType(issue_str)
        except ValueError:
            pass
        
        rule_ctx.fault_code = claude_data.get("fault_code") or rule_ctx.fault_code
        rule_ctx.symptoms = claude_data.get("symptoms", [])
        rule_ctx.location = claude_data.get("location")
        
        # Work context and urgency
        rule_ctx.urgency = claude_data.get("urgency") or rule_ctx.urgency
        
        # Confidence and clarification
        rule_ctx.confidence = claude_data.get("confidence", 0.7)
        rule_ctx.needs_clarification = claude_data.get("needs_clarification", False)
        rule_ctx.clarification_prompt = claude_data.get("clarification_prompt")
        
        return rule_ctx
    
    def _generate_search_keywords(self, ctx: EquipmentContext) -> List[str]:
        """Generate keywords for knowledge base search."""
        keywords = []
        
        if ctx.component_name:
            keywords.append(ctx.component_name)
        if ctx.component_family:
            keywords.append(ctx.component_family)
        if ctx.manufacturer:
            keywords.append(ctx.manufacturer)
        if ctx.model_number:
            keywords.append(ctx.model_number)
        if ctx.fault_code:
            keywords.append(f"fault {ctx.fault_code}")
            keywords.append(ctx.fault_code)
        
        keywords.extend(ctx.symptoms[:3])
        
        return list(set(k for k in keywords if k))
    
    def _generate_manual_queries(self, ctx: EquipmentContext) -> List[str]:
        """Generate specific queries for manual search."""
        queries = []
        
        # Fault code + component (most specific)
        if ctx.fault_code and ctx.component_name:
            queries.append(f"{ctx.component_name} {ctx.fault_code}")
        
        # Fault code + manufacturer + family
        if ctx.fault_code and ctx.manufacturer:
            queries.append(f"{ctx.manufacturer} {ctx.component_family} {ctx.fault_code}")
        
        # Component + issue type
        if ctx.component_name and ctx.issue_type != IssueType.UNKNOWN:
            issue_words = ctx.issue_type.value.replace("_", " ")
            queries.append(f"{ctx.component_name} {issue_words}")
        
        # Manufacturer + family + troubleshooting
        if ctx.manufacturer and ctx.component_family:
            queries.append(f"{ctx.manufacturer} {ctx.component_family} troubleshooting")
        
        return queries[:4]  # Limit to 4 queries


# Convenience function for simple extraction
async def extract_context(message: str) -> EquipmentContext:
    """Quick extraction without instantiating class."""
    extractor = ContextExtractor()
    return await extractor.extract(message)
```

**COMMIT:**
```bash
git add -A && git commit -m "bot: context extractor" && git push
```

---

# PHASE 3: RESPONSE SYNTHESIZER (Day 2)

## Task 3.1: Response Synthesizer
Create `agent_factory/intake/response_synthesizer.py`:

```python
"""
Response Synthesizer - Combines knowledge into helpful responses.
Phase 1: Manual excerpts + safety warnings
Phase 2 Prep: Extract atoms from generated content
"""
import anthropic
from typing import List, Dict, Any, Optional
import logging

from .models import EquipmentContext, ManualResult, SynthesizedResponse, IssueType

logger = logging.getLogger(__name__)


class ResponseSynthesizer:
    """
    Combine equipment context + manual results into helpful, safe responses.
    
    Key principles:
    1. Safety warnings ALWAYS included for electrical/mechanical work
    2. Source citations for every factual claim
    3. Clear, actionable troubleshooting steps
    4. Appropriate caveats when using AI-generated content
    """
    
    SYSTEM_PROMPT = '''You are an expert industrial maintenance assistant helping field technicians.

Your job is to provide helpful, accurate, and SAFE guidance based on equipment manuals and documentation.

CRITICAL RULES:
1. ALWAYS include safety warnings for electrical, hydraulic, or pneumatic work
2. Cite your sources with page numbers when available
3. If you don't have enough information, say so clearly
4. Prioritize de-energization and lockout/tagout procedures
5. Be specific about wire colors, terminal numbers, and component locations when available
6. Suggest diagnostic steps in logical order (easiest/safest first)
7. If content is from manuals, cite it. If you're inferring, say so.

Response Format:
- Start with a direct answer or acknowledgment
- Include relevant manual excerpts or troubleshooting steps
- Add safety warnings appropriate to the equipment type
- Cite sources at the end'''

    SYNTHESIS_PROMPT = '''Technician's question: "{query}"

Equipment Context:
- Component: {component}
- Manufacturer: {manufacturer}
- Category: {category}
- Fault Code: {fault_code}
- Symptoms: {symptoms}
- Urgency: {urgency}

{manual_section}

Generate a helpful response that:
1. Directly addresses their question
2. Includes specific troubleshooting steps if relevant
3. Cites the manual sources with page numbers
4. Adds appropriate safety warnings for this equipment type
5. Suggests next steps if the issue isn't resolved

If manual content is limited, provide general guidance based on your training but clearly indicate what's from manuals vs. general knowledge.'''

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.model = "claude-sonnet-4-20250514"
    
    async def synthesize(
        self,
        context: EquipmentContext,
        manual_results: List[ManualResult],
        user_query: str
    ) -> SynthesizedResponse:
        """
        Synthesize a complete response from context and manual results.
        
        Returns SynthesizedResponse with:
        - main_response: The formatted response text
        - sources: List of cited sources
        - safety_warnings: Relevant safety warnings
        - has_manual_content: Whether we found relevant manuals
        """
        # Format manual content
        manual_section = self._format_manual_content(manual_results)
        has_manual = len(manual_results) > 0
        
        # Generate response
        response_text = await self._generate_response(
            context, manual_section, user_query, has_manual
        )
        
        # Extract/generate safety warnings
        safety_warnings = self._generate_safety_warnings(context)
        
        # Format sources
        sources = self._format_sources(manual_results)
        
        return SynthesizedResponse(
            main_response=response_text,
            sources=sources,
            safety_warnings=safety_warnings,
            has_manual_content=has_manual,
            confidence=context.confidence
        )
    
    def _format_manual_content(self, results: List[ManualResult]) -> str:
        """Format manual search results for the prompt."""
        if not results:
            return "Manual content: No specific documentation found for this equipment."
        
        sections = ["Manual content found:"]
        for i, r in enumerate(results[:3], 1):
            sections.append(f"\n**[{r.title}]** (Page {r.page_num}):")
            sections.append(r.snippet)
        
        return "\n".join(sections)
    
    async def _generate_response(
        self,
        ctx: EquipmentContext,
        manual_section: str,
        query: str,
        has_manual: bool
    ) -> str:
        """Generate the main response using Claude."""
        
        prompt = self.SYNTHESIS_PROMPT.format(
            query=query,
            component=ctx.component_name or ctx.component_family or "Unknown",
            manufacturer=ctx.manufacturer or "Unknown",
            category=ctx.category or "Unknown",
            fault_code=ctx.fault_code or "None specified",
            symptoms=", ".join(ctx.symptoms) if ctx.symptoms else "Not specified",
            urgency=ctx.urgency,
            manual_section=manual_section
        )
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude synthesis failed: {e}")
            return self._fallback_response(ctx, manual_section, has_manual)
    
    def _fallback_response(self, ctx: EquipmentContext, 
                          manual_section: str, has_manual: bool) -> str:
        """Generate fallback response if Claude fails."""
        component = ctx.component_name or ctx.component_family or "Equipment"
        
        if has_manual:
            return f"""🔧 **{component}** - Information Found

{manual_section}

⚠️ **Safety Reminder:** Always follow lockout/tagout procedures before servicing.

If you need more specific help, please describe the exact symptoms."""
        else:
            return f"""🔧 **{component}** Issue

I don't have specific documentation for this equipment yet.

**General troubleshooting steps:**
1. Document the exact error code or symptoms
2. Check power supply and connections
3. Review any recent changes to the system
4. Consult the equipment's physical manual if available

⚠️ Always follow lockout/tagout before servicing.

**Tip:** Upload the equipment manual with `/upload_manual` for better assistance next time."""
    
    def _generate_safety_warnings(self, ctx: EquipmentContext) -> List[str]:
        """Generate appropriate safety warnings based on equipment type."""
        warnings = []
        
        family_lower = (ctx.component_family or "").lower()
        category_lower = (ctx.category or "").lower()
        
        # Electrical hazards
        if any(kw in family_lower + category_lower for kw in 
               ["vfd", "drive", "motor", "electrical", "panel", "power", "plc"]):
            warnings.append("⚠️ ELECTRICAL HAZARD: De-energize and verify zero energy before servicing")
        
        # VFD-specific
        if "vfd" in family_lower or "drive" in family_lower:
            warnings.append("⚠️ VFDs retain dangerous voltage in DC bus capacitors - wait 5+ minutes after power off")
        
        # High voltage fault codes
        if ctx.fault_code and any(kw in str(ctx.fault_code).lower() for kw in 
                                   ["over", "under", "volt", "ground"]):
            warnings.append("⚠️ Check incoming power with rated meter before troubleshooting")
        
        # Overheating issues
        if ctx.issue_type == IssueType.OVERHEATING:
            warnings.append("⚠️ Allow equipment to cool before touching. Risk of burns.")
        
        # Hydraulic/pneumatic
        if any(kw in family_lower + category_lower for kw in 
               ["hydraulic", "pneumatic", "cylinder", "valve"]):
            warnings.append("⚠️ Release all stored pressure before servicing")
        
        # Safety systems
        if any(kw in family_lower for kw in ["safety", "e-stop", "guard"]):
            warnings.append("⚠️ Do not bypass safety systems. Test all safety functions after service.")
        
        # Generic fallback
        if not warnings:
            warnings.append("⚠️ Follow facility lockout/tagout procedures before servicing")
        
        return warnings
    
    def _format_sources(self, results: List[ManualResult]) -> List[Dict[str, Any]]:
        """Format source citations."""
        return [
            {
                "title": r.title,
                "page": r.page_num,
                "manufacturer": r.manufacturer,
                "score": round(r.score, 2),
                "type": r.source_type
            }
            for r in results[:5]
        ]
    
    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 2 STUBS: Atom Extraction
    # ═══════════════════════════════════════════════════════════════════════
    
    async def extract_atoms(self, response: str, 
                           context: EquipmentContext) -> List[Dict]:
        """
        Phase 2: Extract knowledge atoms from generated response.
        These will be queued for expert review before adding to KB.
        """
        raise NotImplementedError("Phase 2 feature")
    
    async def should_extract_atoms(self, response: SynthesizedResponse) -> bool:
        """
        Phase 2: Determine if this response should have atoms extracted.
        Criteria: Low manual content + high-quality generation.
        """
        raise NotImplementedError("Phase 2 feature")


class TelegramFormatter:
    """Format responses for Telegram's message constraints."""
    
    MAX_MESSAGE_LENGTH = 4096
    
    @staticmethod
    def format(response: SynthesizedResponse) -> str:
        """Format SynthesizedResponse for Telegram."""
        text = response.main_response
        
        # Add sources if not already in response
        if response.sources and "Source" not in text and "📄" not in text:
            text += "\n\n📄 **Sources:**\n"
            for s in response.sources[:3]:
                text += f"• {s['title']} (p.{s['page']})\n"
        
        # Add safety warnings if not prominent in response
        if response.safety_warnings:
            # Check if warnings already included
            has_warnings = any(w in text for w in ["⚠️", "SAFETY", "WARNING", "CAUTION"])
            if not has_warnings:
                text += "\n\n" + "\n".join(response.safety_warnings)
        
        # Truncate if needed
        if len(text) > TelegramFormatter.MAX_MESSAGE_LENGTH:
            truncate_at = TelegramFormatter.MAX_MESSAGE_LENGTH - 100
            text = text[:truncate_at] + "\n\n... _(truncated - ask for specific details)_"
        
        return text
    
    @staticmethod
    def format_no_results(context: EquipmentContext) -> str:
        """Format response when no manual content found."""
        component = context.component_name or context.component_family or "this equipment"
        mfr = f" ({context.manufacturer})" if context.manufacturer else ""
        
        msg = f"""🔍 I identified **{component}**{mfr}"""
        
        if context.fault_code:
            msg += f" with fault code **{context.fault_code}**"
        
        msg += """ but don't have specific documentation yet.

**What you can do:**
1. 📤 Upload the manual: `/upload_manual`
2. 💬 Ask a general question and I'll help with my training knowledge
3. 🌐 Check manufacturer website for documentation

**General guidance:**
• Always follow lockout/tagout before servicing
• Document the exact fault code and symptoms
• Check power, connections, and fuses first

Would you like general troubleshooting help for this type of equipment?"""
        
        return msg
    
    @staticmethod
    def format_clarification(context: EquipmentContext) -> str:
        """Format clarification request."""
        return context.clarification_prompt or "Could you provide more details about the issue?"
```

**COMMIT:**
```bash
git add -A && git commit -m "bot: response synthesizer" && git push
```

---

# PHASE 4: VOICE TRANSCRIPTION (Day 2)

## Task 4.1: Whisper Integration
Create `agent_factory/integrations/telegram/voice.py`:

```python
"""
Voice Message Transcription
Uses OpenAI Whisper for high-quality speech-to-text
"""
import openai
from pathlib import Path
import tempfile
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class VoiceTranscriber:
    """Transcribe voice messages using OpenAI Whisper API."""
    
    def __init__(self):
        self.client = openai.OpenAI()
    
    async def transcribe(self, audio_path: Path) -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file (OGG, MP3, WAV, etc.)
            
        Returns:
            Transcribed text
        """
        try:
            with open(audio_path, "rb") as f:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language="en",
                    prompt="Industrial maintenance, equipment troubleshooting, fault codes"
                )
            
            text = response.text.strip()
            logger.info(f"Transcribed ({len(text)} chars): {text[:100]}...")
            return text
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
    
    async def transcribe_telegram_voice(self, bot, voice_message) -> str:
        """
        Download and transcribe Telegram voice message.
        
        Args:
            bot: Telegram bot instance
            voice_message: Voice message object from update
            
        Returns:
            Transcribed text
        """
        # Download voice file
        file = await bot.get_file(voice_message.file_id)
        
        # Save to temp file
        temp_path = Path(tempfile.mktemp(suffix=".ogg"))
        await file.download_to_drive(temp_path)
        
        try:
            text = await self.transcribe(temp_path)
            return text
        finally:
            # Clean up temp file
            temp_path.unlink(missing_ok=True)


# Singleton instance
_transcriber: Optional[VoiceTranscriber] = None

def get_transcriber() -> VoiceTranscriber:
    """Get or create transcriber instance."""
    global _transcriber
    if _transcriber is None:
        _transcriber = VoiceTranscriber()
    return _transcriber
```

**COMMIT:**
```bash
git add -A && git commit -m "bot: voice transcription" && git push
```

---

# PHASE 5: INTELLIGENT INTAKE HANDLER (Day 3)

## Task 5.1: Main Intake Handler
Create `agent_factory/intake/telegram_intake.py`:

```python
"""
Intelligent Intake Handler - The main entry point for all messages.
Every message goes through context extraction → knowledge search → synthesis.
"""
import logging
from typing import Dict, Any, List, Optional
from telegram import Update
from telegram.ext import ContextTypes
from dataclasses import asdict

from .context_extractor import ContextExtractor
from .response_synthesizer import ResponseSynthesizer, TelegramFormatter
from .models import EquipmentContext, ManualResult

logger = logging.getLogger(__name__)

# Import knowledge components (from Tab 1)
try:
    from agent_factory.knowledge.manual_search import ManualSearch
    from agent_factory.knowledge.vector_store import VectorStore
    from agent_factory.rivet_pro.database import DatabaseManager
    KNOWLEDGE_AVAILABLE = True
except ImportError:
    KNOWLEDGE_AVAILABLE = False
    logger.warning("Knowledge components not available")


class IntelligentIntakeHandler:
    """
    Process every message with full context extraction and knowledge retrieval.
    
    Flow:
    1. Extract equipment context from message
    2. Search for relevant manuals/prints
    3. Synthesize response with citations and safety warnings
    4. Log extraction for analytics (Phase 2: learning loop)
    """
    
    def __init__(self):
        self.extractor = ContextExtractor()
        self.synthesizer = ResponseSynthesizer()
        self.formatter = TelegramFormatter()
        
        if KNOWLEDGE_AVAILABLE:
            self.manual_search = ManualSearch()
            self.db = DatabaseManager()
        else:
            self.manual_search = None
            self.db = None
    
    async def process(
        self,
        message: str,
        user_id: str,
        telegram_id: int,
        conversation_history: List[dict] = None
    ) -> Dict[str, Any]:
        """
        Process a message with full intelligent intake.
        
        Args:
            message: The user's message text
            user_id: Internal user ID
            telegram_id: Telegram user ID
            conversation_history: Previous messages for context
            
        Returns:
            {
                "response": str (formatted for Telegram),
                "context": EquipmentContext,
                "manual_results": List[ManualResult],
                "needs_clarification": bool,
                "logged": bool (whether we logged to DB)
            }
        """
        # 1. Extract context
        context = await self.extractor.extract(message, conversation_history)
        
        logger.info(
            f"Context extracted: component={context.component_name}, "
            f"mfr={context.manufacturer}, fault={context.fault_code}, "
            f"confidence={context.confidence:.2f}"
        )
        
        # 2. Check if clarification needed BEFORE searching
        if context.needs_clarification and context.clarification_prompt:
            return {
                "response": self.formatter.format_clarification(context),
                "context": context,
                "manual_results": [],
                "needs_clarification": True,
                "logged": False
            }
        
        # 3. Search knowledge base
        manual_results = await self._search_knowledge(context)
        
        logger.info(f"Found {len(manual_results)} manual results")
        
        # 4. Synthesize response
        if manual_results:
            synthesis = await self.synthesizer.synthesize(
                context, manual_results, message
            )
            response = self.formatter.format(synthesis)
        else:
            response = self.formatter.format_no_results(context)
            
            # Log manual gap for future acquisition
            if self.db and context.manufacturer and context.component_family:
                try:
                    await self.db.connect()
                    await self.db.log_manual_gap(
                        context.manufacturer,
                        context.component_family,
                        context.model_number
                    )
                except Exception as e:
                    logger.warning(f"Failed to log manual gap: {e}")
        
        # 5. Log extraction for analytics
        logged = await self._log_extraction(
            user_id, telegram_id, message, context, len(manual_results)
        )
        
        return {
            "response": response,
            "context": context,
            "manual_results": manual_results,
            "needs_clarification": False,
            "logged": logged
        }
    
    async def _search_knowledge(self, context: EquipmentContext) -> List[ManualResult]:
        """Search manuals and prints for relevant content."""
        if not self.manual_search or context.confidence < 0.3:
            return []
        
        results = []
        seen_ids = set()
        
        # Search with each generated query
        for query in context.manual_search_queries[:3]:
            try:
                search_results = self.manual_search.search(
                    query, 
                    top_k=3,
                    manufacturer=context.manufacturer,
                    component_family=context.component_family
                )
                
                for r in search_results:
                    if r.manual_id not in seen_ids:
                        seen_ids.add(r.manual_id)
                        results.append(ManualResult(
                            title=r.title,
                            manufacturer=r.manufacturer,
                            page_num=r.page_num,
                            snippet=r.snippet,
                            score=r.score,
                            source_type="manual",
                            source_id=r.manual_id
                        ))
            except Exception as e:
                logger.warning(f"Search failed for query '{query}': {e}")
        
        # Sort by score and return top results
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:5]
    
    async def _log_extraction(
        self, user_id: str, telegram_id: int, message: str,
        context: EquipmentContext, manuals_found: int
    ) -> bool:
        """Log extraction for analytics and future learning."""
        if not self.db:
            return False
        
        try:
            await self.db.connect()
            await self.db.log_context_extraction(
                user_id=user_id,
                telegram_id=telegram_id,
                message=message,
                context=context.to_dict(),
                confidence=context.confidence,
                manuals_found=manuals_found
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to log extraction: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════
# TELEGRAM HANDLER FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

async def intelligent_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main Telegram message handler with intelligent intake.
    Wire this into your bot as a MessageHandler for TEXT messages.
    """
    message = update.message.text
    user_id = str(update.effective_user.id)
    telegram_id = update.effective_user.id
    
    # Get or create intake handler
    if "intake_handler" not in context.bot_data:
        context.bot_data["intake_handler"] = IntelligentIntakeHandler()
    
    handler = context.bot_data["intake_handler"]
    
    # Show typing indicator
    await update.message.chat.send_action("typing")
    
    # Get conversation history from user_data
    history = context.user_data.get("conversation_history", [])
    
    # Process message
    result = await handler.process(message, user_id, telegram_id, history)
    
    # Update conversation history
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": result["response"]})
    context.user_data["conversation_history"] = history[-10:]  # Keep last 10
    
    # Store context for follow-up commands
    context.user_data["last_equipment_context"] = result["context"]
    
    # Send response (split if too long)
    response = result["response"]
    if len(response) > 4096:
        for i in range(0, len(response), 4096):
            await update.message.reply_text(
                response[i:i+4096],
                parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(response, parse_mode="Markdown")
```

**COMMIT:**
```bash
git add -A && git commit -m "bot: intelligent intake handler" && git push
```

---

# PHASE 6: PRINT & MANUAL COMMANDS (Day 3-4)

## Task 6.1: Print Handlers
Create `agent_factory/integrations/telegram/print_handlers.py`:

```python
"""Print upload and query Telegram handlers."""
import tempfile
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

# Import knowledge components
try:
    from agent_factory.knowledge.print_indexer import PrintIndexer
    from agent_factory.knowledge.vector_store import VectorStore
    from agent_factory.rivet_pro.database import DatabaseManager
    INDEXER_AVAILABLE = True
except ImportError:
    INDEXER_AVAILABLE = False
    logger.warning("Print indexer not available")


async def add_machine_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /add_machine <n> command."""
    args = context.args
    if not args:
        await update.message.reply_text(
            "📋 **Add Machine**\n\n"
            "Usage: `/add_machine <machine_name>`\n\n"
            "Example: `/add_machine Lathe_1`",
            parse_mode="Markdown"
        )
        return
    
    machine_name = " ".join(args)
    user_id = str(update.effective_user.id)
    
    if INDEXER_AVAILABLE:
        try:
            db = DatabaseManager()
            await db.connect()
            machine = await db.create_machine(user_id, machine_name)
            await update.message.reply_text(
                f"✅ **Machine Created**\n\n"
                f"🔧 Name: **{machine_name}**\n\n"
                f"Next steps:\n"
                f"• Upload prints: `/upload_print {machine_name}`\n"
                f"• List machines: `/list_machines`",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to create machine: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    else:
        await update.message.reply_text(f"✅ Machine **{machine_name}** created! (DB not connected)")


async def list_machines_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /list_machines command."""
    user_id = str(update.effective_user.id)
    
    if INDEXER_AVAILABLE:
        try:
            db = DatabaseManager()
            await db.connect()
            machines = await db.get_user_machines(user_id)
            
            if machines:
                msg = "🏭 **Your Machines:**\n\n"
                for m in machines:
                    msg += f"• **{m['name']}**\n"
                msg += "\n📤 Upload prints: `/upload_print <machine>`\n"
                msg += "🔍 Query prints: `/chat_print <machine>`"
            else:
                msg = "No machines yet.\n\nCreate one: `/add_machine <n>`"
            
            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to list machines: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    else:
        await update.message.reply_text("Database not connected.")


async def upload_print_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /upload_print <machine> command."""
    args = context.args
    if not args:
        await update.message.reply_text(
            "📄 **Upload Print**\n\n"
            "Usage: `/upload_print <machine_name>`\n\n"
            "Example: `/upload_print Lathe_1`",
            parse_mode="Markdown"
        )
        return
    
    machine_name = " ".join(args)
    context.user_data["upload_machine"] = machine_name
    context.user_data["awaiting_print"] = True
    
    await update.message.reply_text(
        f"📤 **Upload Print for {machine_name}**\n\n"
        "Send a PDF of the electrical print or schematic.\n\n"
        "Supported: Wiring diagrams, schematics, P&IDs\n\n"
        "Send `/cancel` to abort.",
        parse_mode="Markdown"
    )


async def handle_print_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handle uploaded print PDF. Returns True if handled."""
    if not context.user_data.get("awaiting_print"):
        return False
    
    context.user_data["awaiting_print"] = False
    
    doc = update.message.document
    if not doc.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("❌ Please send a PDF file.")
        return True
    
    machine_name = context.user_data.get("upload_machine", "Unknown")
    user_id = str(update.effective_user.id)
    
    await update.message.reply_text("📥 Processing print... This may take a moment.")
    
    # Download file
    file = await context.bot.get_file(doc.file_id)
    temp_path = Path(tempfile.mktemp(suffix=".pdf"))
    await file.download_to_drive(temp_path)
    
    try:
        if INDEXER_AVAILABLE:
            db = DatabaseManager()
            await db.connect()
            
            # Get or create machine
            machine = await db.get_machine_by_name(user_id, machine_name)
            if not machine:
                machine = await db.create_machine(user_id, machine_name)
            
            # Create print record
            print_record = await db.create_print(
                str(machine["id"]), user_id, doc.file_name, str(temp_path)
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
                    str(print_record["id"]),
                    result["chunk_count"],
                    result["collection_name"]
                )
                
                await update.message.reply_text(
                    f"✅ **Print Uploaded & Indexed!**\n\n"
                    f"📄 File: `{doc.file_name}`\n"
                    f"🔧 Machine: **{machine_name}**\n"
                    f"📑 Pages: {result['page_count']}\n"
                    f"🧩 Chunks indexed: {result['chunk_count']}\n\n"
                    f"💡 Use `/chat_print {machine_name}` to ask questions!",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(f"❌ Indexing failed: {result.get('error')}")
        else:
            await update.message.reply_text(
                "✅ Print received! (Indexer not connected)\n"
                "File saved for future processing."
            )
    except Exception as e:
        logger.error(f"Print processing failed: {e}")
        await update.message.reply_text(f"❌ Error: {e}")
    finally:
        temp_path.unlink(missing_ok=True)
    
    return True


async def chat_print_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /chat_print <machine> command."""
    args = context.args
    if not args:
        await update.message.reply_text(
            "🔍 **Chat with Prints**\n\n"
            "Usage: `/chat_print <machine_name>`\n\n"
            "Example: `/chat_print Lathe_1`",
            parse_mode="Markdown"
        )
        return
    
    machine_name = " ".join(args)
    user_id = str(update.effective_user.id)
    
    context.user_data["print_chat_machine"] = machine_name
    context.user_data["print_chat_active"] = True
    
    if INDEXER_AVAILABLE:
        try:
            db = DatabaseManager()
            await db.connect()
            machine = await db.get_machine_by_name(user_id, machine_name)
            
            if machine:
                prints = await db.get_machine_prints(str(machine["id"]))
                count = len(prints)
                
                await update.message.reply_text(
                    f"🔍 **Chat with {machine_name} Prints**\n\n"
                    f"📄 {count} print(s) loaded\n\n"
                    "Ask me anything about the electrical prints!\n\n"
                    "**Example questions:**\n"
                    "• What's the wire gauge for the main feeder?\n"
                    "• Where is the E-stop circuit?\n"
                    "• What voltage is the control transformer?\n\n"
                    "Send `/end_chat` to exit.",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    f"❌ Machine '{machine_name}' not found.\n\n"
                    f"Create it: `/add_machine {machine_name}`"
                )
        except Exception as e:
            logger.error(f"Chat print setup failed: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    else:
        await update.message.reply_text(
            f"🔍 Chat started for **{machine_name}** (DB not connected)",
            parse_mode="Markdown"
        )


async def end_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /end_chat command."""
    context.user_data["print_chat_active"] = False
    context.user_data.pop("print_chat_machine", None)
    context.user_data.pop("conversation_history", None)
    
    await update.message.reply_text(
        "✅ Chat session ended.\n\n"
        "Use `/chat_print <machine>` to start a new session."
    )


async def list_prints_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /list_prints <machine> command."""
    args = context.args
    if not args:
        await update.message.reply_text(
            "📄 **List Prints**\n\n"
            "Usage: `/list_prints <machine_name>`",
            parse_mode="Markdown"
        )
        return
    
    machine_name = " ".join(args)
    user_id = str(update.effective_user.id)
    
    if INDEXER_AVAILABLE:
        try:
            db = DatabaseManager()
            await db.connect()
            machine = await db.get_machine_by_name(user_id, machine_name)
            
            if machine:
                prints = await db.get_machine_prints(str(machine["id"]))
                if prints:
                    msg = f"📄 **Prints for {machine_name}:**\n\n"
                    for p in prints:
                        status = "✅" if p.get("vectorized") else "⏳"
                        msg += f"{status} `{p['name']}`\n"
                else:
                    msg = f"No prints for {machine_name} yet.\n\nUpload: `/upload_print {machine_name}`"
            else:
                msg = f"Machine '{machine_name}' not found."
            
            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"List prints failed: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    else:
        await update.message.reply_text("Database not connected.")
```

## Task 6.2: Manual Handlers
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
    INDEXER_AVAILABLE = True
except ImportError:
    INDEXER_AVAILABLE = False


async def upload_manual_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /upload_manual command."""
    context.user_data["awaiting_manual"] = True
    
    await update.message.reply_text(
        "📚 **Upload Equipment Manual**\n\n"
        "Send a PDF of an OEM manual.\n\n"
        "**Best results with:**\n"
        "• User manuals\n"
        "• Troubleshooting guides\n"
        "• Fault code references\n"
        "• Installation manuals\n\n"
        "Send `/cancel` to abort.",
        parse_mode="Markdown"
    )


async def handle_manual_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handle uploaded manual PDF. Returns True if handled."""
    if not context.user_data.get("awaiting_manual"):
        return False
    
    context.user_data["awaiting_manual"] = False
    
    doc = update.message.document
    if not doc.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("❌ Please send a PDF file.")
        return True
    
    await update.message.reply_text("📥 Processing manual... This may take a moment.")
    
    file = await context.bot.get_file(doc.file_id)
    temp_path = Path(tempfile.mktemp(suffix=".pdf"))
    await file.download_to_drive(temp_path)
    
    try:
        if INDEXER_AVAILABLE:
            import uuid
            
            db = DatabaseManager()
            await db.connect()
            
            # Create manual record
            manual = await db.create_manual(
                doc.file_name,
                "Unknown",  # TODO: Could prompt for manufacturer
                "Unknown",
                str(temp_path)
            )
            
            # Index the manual
            indexer = ManualIndexer()
            result = indexer.index_manual(
                temp_path,
                str(manual["id"]),
                doc.file_name,
                "Unknown",
                "Unknown"
            )
            
            if result["success"]:
                await db.update_manual_indexed(
                    str(manual["id"]), 
                    "equipment_manuals", 
                    result["page_count"]
                )
                
                sections_text = ""
                if result.get("sections"):
                    sections_text = "\n\n**Sections detected:**\n"
                    for s in result["sections"][:5]:
                        sections_text += f"• {s['type']}: p.{s['page_start']}-{s['page_end']}\n"
                
                await update.message.reply_text(
                    f"✅ **Manual Indexed!**\n\n"
                    f"📄 File: `{doc.file_name}`\n"
                    f"📑 Pages: {result['page_count']}\n"
                    f"🧩 Chunks indexed: {result['chunk_count']}"
                    f"{sections_text}\n\n"
                    f"💡 I'll reference this when you ask about this equipment!",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(f"❌ Indexing failed: {result.get('error')}")
        else:
            await update.message.reply_text("✅ Manual received! (Indexer not connected)")
    except Exception as e:
        logger.error(f"Manual processing failed: {e}")
        await update.message.reply_text(f"❌ Error: {e}")
    finally:
        temp_path.unlink(missing_ok=True)
    
    return True


async def manual_gaps_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /manual_gaps command."""
    if INDEXER_AVAILABLE:
        try:
            db = DatabaseManager()
            await db.connect()
            gaps = await db.get_top_manual_gaps(10)
            
            if gaps:
                msg = "📊 **Most Requested Missing Manuals:**\n\n"
                for i, g in enumerate(gaps, 1):
                    msg += f"{i}. **{g['manufacturer']} {g['component_family']}**\n"
                    msg += f"   Requested {g['request_count']} times\n\n"
                msg += "📤 Upload these with `/upload_manual` to improve assistance!"
            else:
                msg = "No manual gaps tracked yet.\n\nGaps are logged when users ask about equipment we don't have docs for."
            
            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Manual gaps failed: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    else:
        await update.message.reply_text("Database not connected.")
```

**COMMIT:**
```bash
git add -A && git commit -m "bot: print and manual handlers" && git push
```

---

# PHASE 7: BOT INTEGRATION (Day 4-5)

## Task 7.1: Register All Handlers
Create `agent_factory/integrations/telegram/rivet_handlers.py`:

```python
"""Register all Rivet handlers with the bot."""
from telegram.ext import MessageHandler, CommandHandler, filters
import logging

from .print_handlers import (
    add_machine_command, list_machines_command, upload_print_command,
    chat_print_command, end_chat_command, list_prints_command,
    handle_print_document
)
from .manual_handlers import (
    upload_manual_command, handle_manual_document, manual_gaps_command
)
from .telegram_intake import intelligent_message_handler
from .voice import get_transcriber

logger = logging.getLogger(__name__)


async def voice_message_handler(update, context):
    """Handle voice messages with transcription + intelligent intake."""
    from .telegram_intake import IntelligentIntakeHandler
    
    voice = update.message.voice
    user_id = str(update.effective_user.id)
    telegram_id = update.effective_user.id
    
    await update.message.reply_text("🎤 Transcribing...")
    
    try:
        # Transcribe
        transcriber = get_transcriber()
        text = await transcriber.transcribe_telegram_voice(context.bot, voice)
        
        await update.message.reply_text(f"📝 _Heard: \"{text}\"_", parse_mode="Markdown")
        
        # Process through intelligent intake
        if "intake_handler" not in context.bot_data:
            context.bot_data["intake_handler"] = IntelligentIntakeHandler()
        
        handler = context.bot_data["intake_handler"]
        
        await update.message.chat.send_action("typing")
        
        result = await handler.process(text, user_id, telegram_id)
        
        await update.message.reply_text(result["response"], parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Voice processing failed: {e}")
        await update.message.reply_text(f"❌ Voice processing failed: {e}")


async def handle_pdf_upload(update, context):
    """Route PDF uploads to correct handler."""
    # Check if waiting for manual
    if context.user_data.get("awaiting_manual"):
        await handle_manual_document(update, context)
        return
    
    # Check if waiting for print
    if context.user_data.get("awaiting_print"):
        await handle_print_document(update, context)
        return
    
    # Not waiting for anything - prompt user
    await update.message.reply_text(
        "📄 I received a PDF!\n\n"
        "**What would you like to do?**\n"
        "• `/upload_print <machine>` - Add as electrical print\n"
        "• `/upload_manual` - Add to manual library",
        parse_mode="Markdown"
    )


async def cancel_command(update, context):
    """Handle /cancel command."""
    context.user_data.pop("awaiting_print", None)
    context.user_data.pop("awaiting_manual", None)
    context.user_data.pop("upload_machine", None)
    await update.message.reply_text("✅ Operation cancelled.")


async def help_command(update, context):
    """Handle /help command."""
    await update.message.reply_text(
        "🔧 **Rivet Commands**\n\n"
        "**Equipment Management:**\n"
        "`/add_machine <n>` - Create machine\n"
        "`/list_machines` - Show your machines\n\n"
        "**Print Management:**\n"
        "`/upload_print <machine>` - Upload schematic\n"
        "`/list_prints <machine>` - Show prints\n"
        "`/chat_print <machine>` - Ask about prints\n"
        "`/end_chat` - End print Q&A\n\n"
        "**Manual Library:**\n"
        "`/upload_manual` - Upload OEM manual\n"
        "`/manual_gaps` - Show missing manuals\n\n"
        "**General:**\n"
        "`/help` - Show this message\n"
        "`/cancel` - Cancel current operation\n\n"
        "💡 **Tip:** Just describe your issue naturally!\n"
        "_'PowerFlex showing F004'_ → I'll find the answer.",
        parse_mode="Markdown"
    )


def register_rivet_handlers(application):
    """
    Register all Rivet handlers with the bot application.
    Call this in your bot.py setup.
    """
    # Help
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
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
    
    # Document handler (for PDF uploads) - priority 3
    application.add_handler(
        MessageHandler(filters.Document.PDF, handle_pdf_upload),
        group=3
    )
    
    # Voice handler - priority 4
    application.add_handler(
        MessageHandler(filters.VOICE, voice_message_handler),
        group=4
    )
    
    # Intelligent text handler (catches all other text) - priority 5 (lowest)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, intelligent_message_handler),
        group=5
    )
    
    logger.info("Rivet handlers registered")
```

## Task 7.2: Integration Code
Add to your existing `bot.py`:

```python
# At the top, add import:
from agent_factory.integrations.telegram.rivet_handlers import register_rivet_handlers

# In your setup function, AFTER other handlers:
register_rivet_handlers(application)
```

**COMMIT:**
```bash
git add -A && git commit -m "bot: all handlers registered" && git push
```

---

# PHASE 8: TESTING (Day 5)

## Task 8.1: Test Script
Create `test_bot.py`:

```python
"""Test bot components."""
import asyncio

async def test_context_extraction():
    print("Testing context extraction...")
    from agent_factory.intake.context_extractor import ContextExtractor
    
    extractor = ContextExtractor()
    
    test_cases = [
        ("PowerFlex 525 showing fault F004", "VFD", "Allen-Bradley", "F004"),
        ("The main pump motor won't start", "motor", None, None),
        ("S7-1500 PLC has SF light on", "PLC", "Siemens", None),
        ("Proximity sensor not detecting parts", "Sensor", None, None),
        ("Control panel overheating", None, None, None),
    ]
    
    for msg, expected_family, expected_mfr, expected_fault in test_cases:
        ctx = await extractor.extract(msg)
        print(f"\n  Message: '{msg}'")
        print(f"    Component: {ctx.component_name or ctx.component_family}")
        print(f"    Manufacturer: {ctx.manufacturer}")
        print(f"    Fault: {ctx.fault_code}")
        print(f"    Confidence: {ctx.confidence:.2f}")
    
    print("\n✅ Context extraction tests complete!")


async def test_response_synthesis():
    print("\n\nTesting response synthesis...")
    from agent_factory.intake.response_synthesizer import ResponseSynthesizer
    from agent_factory.intake.models import EquipmentContext, ManualResult, IssueType
    
    synth = ResponseSynthesizer()
    
    # Create test context
    ctx = EquipmentContext(
        raw_message="PowerFlex fault F004",
        component_name="PowerFlex 525",
        component_family="Variable Frequency Drive",
        manufacturer="Allen-Bradley",
        fault_code="F004",
        issue_type=IssueType.FAULT_CODE,
        confidence=0.85
    )
    
    # Test with manual result
    manual = ManualResult(
        title="PowerFlex 520 User Manual",
        manufacturer="Allen-Bradley",
        page_num=47,
        snippet="F004 - DC Bus Undervoltage. This fault occurs when the DC bus voltage drops below the undervoltage threshold. Common causes include: incoming power sag, loose connections on input terminals, or failing DC bus capacitors.",
        score=0.92,
        source_type="manual"
    )
    
    result = await synth.synthesize(ctx, [manual], "PowerFlex showing F004")
    
    print(f"\n  Response preview:")
    print(f"    {result.main_response[:200]}...")
    print(f"\n  Sources: {len(result.sources)}")
    print(f"  Safety warnings: {len(result.safety_warnings)}")
    print(f"  Has manual content: {result.has_manual_content}")
    
    # Verify safety warning for VFD
    assert any("capacitor" in w.lower() or "voltage" in w.lower() for w in result.safety_warnings), \
        "Should have VFD-specific safety warning"
    
    print("\n✅ Response synthesis tests complete!")


def test_taxonomy():
    print("\n\nTesting equipment taxonomy...")
    
    try:
        from agent_factory.intake.equipment_taxonomy import (
            identify_component, extract_fault_code, identify_urgency
        )
        
        # Test component identification
        result = identify_component("The PowerFlex 525 VFD is faulting")
        assert result["manufacturer"] == "Allen-Bradley"
        print(f"  ✅ VFD: {result}")
        
        result = identify_component("S7-1500 PLC communication error")
        assert result["manufacturer"] == "Siemens"
        print(f"  ✅ PLC: {result}")
        
        # Test fault code extraction
        code = extract_fault_code("Error F004 on the drive")
        assert code == "F004"
        print(f"  ✅ Fault code: {code}")
        
        # Test urgency
        urg = identify_urgency("Production is down, need help ASAP")
        assert urg in ["critical", "high"]
        print(f"  ✅ Urgency: {urg}")
        
        print("\n✅ Taxonomy tests complete!")
        
    except ImportError:
        print("  ⚠️ Taxonomy not available (Tab 1 not complete)")


if __name__ == "__main__":
    print("=" * 60)
    print("RIVET BOT TESTS")
    print("=" * 60)
    
    asyncio.run(test_context_extraction())
    asyncio.run(test_response_synthesis())
    test_taxonomy()
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE ✅")
    print("=" * 60)
```

Run:
```bash
python test_bot.py
```

**FINAL COMMIT:**
```bash
git add -A && git commit -m "bot: complete with tests" && git push
```

---

# COMMAND REFERENCE

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/add_machine <n>` | Create a machine |
| `/list_machines` | Show your machines |
| `/upload_print <machine>` | Upload electrical print |
| `/list_prints <machine>` | Show machine's prints |
| `/chat_print <machine>` | Start print Q&A |
| `/end_chat` | End Q&A session |
| `/upload_manual` | Upload OEM manual |
| `/manual_gaps` | Show missing manuals |
| `/cancel` | Cancel operation |
| 🎤 Voice | Speak naturally! |

---

# SUCCESS CRITERIA

- [ ] Context extractor identifies equipment + manufacturer + fault codes
- [ ] Response synthesizer includes safety warnings
- [ ] Voice transcription works
- [ ] `/upload_print` accepts and indexes PDFs
- [ ] `/chat_print` enables Q&A
- [ ] `/upload_manual` indexes to library
- [ ] Manual gaps are tracked
- [ ] All commands registered
- [ ] Tests pass

---

# TAB 3 COMPLETE

Bot has full intelligent intake:
1. **Text** → Context extraction → Manual search → Synthesized response
2. **Voice** → Whisper transcribe → Same pipeline
3. **PDF** → Index → Searchable via Q&A

Phase 2 additions (after MVP):
- Extract knowledge atoms from responses
- Log research jobs for analytics
- Expert review workflow
- Feedback collection

"""
RIVET Pro Multi-Agent Backend - Data Models

Unified data models for multimodal industrial maintenance assistant.
All agents, orchestrator, RAG, and chat handlers use these models.

Author: Agent Factory
Created: 2025-12-15
Phase: 1/8 (Foundation)
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class ChannelType(str, Enum):
    """Communication channels supported by RIVET Pro"""
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    SLACK = "slack"
    API = "api"  # Direct API calls


class MessageType(str, Enum):
    """Types of messages RIVET can process"""
    TEXT = "text"
    IMAGE = "image"
    TEXT_WITH_IMAGE = "text_with_image"
    AUDIO = "audio"  # Future: voice messages
    VIDEO = "video"  # Future: video troubleshooting


class VendorType(str, Enum):
    """Equipment vendors RIVET recognizes"""
    SIEMENS = "Siemens"
    ROCKWELL = "Rockwell"
    ABB = "ABB"
    MITSUBISHI = "Mitsubishi"
    SCHNEIDER = "Schneider"
    OMRON = "Omron"
    ALLEN_BRADLEY = "Allen-Bradley"
    GENERIC = "Generic"
    UNKNOWN = "Unknown"


class EquipmentType(str, Enum):
    """Equipment categories for routing"""
    VFD = "VFD"
    PLC = "PLC"
    HMI = "HMI"
    SENSOR = "sensor"
    CONTACTOR = "contactor"
    BREAKER = "breaker"
    MCC = "MCC"
    SAFETY_RELAY = "safety_relay"
    SERVO = "servo"
    MOTOR = "motor"
    ENCODER = "encoder"
    UNKNOWN = "unknown"


class ContextSource(str, Enum):
    """Where intent information came from"""
    TEXT_ONLY = "text_only"
    IMAGE_OCR = "image_ocr"
    IMAGE_TEXT = "image+text"
    IMAGE_VISION = "image_vision"  # GPT-4 Vision / CLIP
    AUDIO_TRANSCRIPTION = "audio_transcription"


class KBCoverage(str, Enum):
    """Knowledge base coverage levels"""
    STRONG = "strong"  # Good docs, high similarity matches
    THIN = "thin"      # Some docs, weak matches
    NONE = "none"      # No relevant docs found


class RouteType(str, Enum):
    """Orchestrator routing decisions"""
    ROUTE_A = "A_direct_sme"           # Strong KB → Direct SME
    ROUTE_B = "B_sme_enrich"           # Thin KB → SME + enrichment
    ROUTE_C = "C_research"             # No KB → Research pipeline
    ROUTE_D = "D_clarification"        # Unclear → Ask for clarification


class AgentID(str, Enum):
    """SME agent identifiers"""
    SIEMENS = "siemens_agent"
    ROCKWELL = "rockwell_agent"
    ABB = "abb_agent"
    GENERIC_PLC = "generic_plc_agent"
    SAFETY = "safety_agent"
    FALLBACK = "fallback_agent"


# ============================================================================
# Request Model
# ============================================================================

class RivetRequest(BaseModel):
    """
    Unified request model for all RIVET Pro inputs.

    This is the normalized representation of user messages from any channel
    (Telegram, WhatsApp, Slack, API). Chat handlers convert channel-specific
    formats into this model.

    Examples:
        # Text-only request
        RivetRequest(
            user_id="telegram_12345",
            channel="telegram",
            message_type="text",
            text="My Siemens G120C shows F3002 fault",
            metadata={"timestamp": "2025-12-15T10:30:00Z"}
        )

        # Image request with caption
        RivetRequest(
            user_id="whatsapp_67890",
            channel="whatsapp",
            message_type="image",
            text="VFD won't start",
            image_path="/tmp/vfd_nameplate_12345.jpg",
            metadata={"language": "en"}
        )
    """

    user_id: str = Field(
        ...,
        description="Unique user identifier (channel-prefixed, e.g., 'telegram_12345')"
    )

    channel: ChannelType = Field(
        ...,
        description="Communication channel this request came from"
    )

    message_type: MessageType = Field(
        ...,
        description="Type of message (text, image, audio, etc.)"
    )

    text: Optional[str] = Field(
        None,
        description="Message text or image caption"
    )

    image_path: Optional[str] = Field(
        None,
        description="Local path to downloaded image (if message_type includes image)"
    )

    audio_path: Optional[str] = Field(
        None,
        description="Local path to audio file (future: voice messages)"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context (timestamp, language, location, etc.)"
    )

    conversation_id: Optional[str] = Field(
        None,
        description="Thread ID for multi-turn conversations"
    )

    @validator('text')
    def validate_text_or_image(cls, v, values):
        """Ensure either text or image_path is provided"""
        if not v and not values.get('image_path'):
            raise ValueError("Either text or image_path must be provided")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "telegram_12345",
                "channel": "telegram",
                "message_type": "text",
                "text": "Siemens VFD fault F3002",
                "metadata": {"timestamp": "2025-12-15T10:30:00Z"}
            }
        }


# ============================================================================
# Intent Model
# ============================================================================

class RivetIntent(BaseModel):
    """
    Classified intent extracted from user request.

    This is the output of the intent classifier and drives routing decisions.
    Contains all structured information needed to route to the correct agent
    and retrieve relevant documentation.

    Examples:
        RivetIntent(
            vendor="Siemens",
            equipment_type="VFD",
            application="overhead_crane",
            symptom="F3002 overvoltage fault on start",
            context_source="text_only",
            confidence=0.92,
            kb_coverage="strong",
            raw_summary="Siemens G120C VFD fault F3002 overvoltage",
            detected_model="G120C",
            detected_part_number="6SL3244-0BB13-1PA0"
        )
    """

    vendor: VendorType = Field(
        ...,
        description="Equipment manufacturer"
    )

    equipment_type: EquipmentType = Field(
        ...,
        description="Type of industrial equipment"
    )

    application: Optional[str] = Field(
        None,
        description="Application context (overhead_crane, conveyor, pump, etc.)",
        examples=["overhead_crane", "conveyor", "pump", "compressor", "fan"]
    )

    symptom: Optional[str] = Field(
        None,
        description="Fault description or behavior (fault codes, won't start, trips, etc.)"
    )

    context_source: ContextSource = Field(
        ...,
        description="Where intent information was extracted from"
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Classification confidence (0.0-1.0)"
    )

    kb_coverage: KBCoverage = Field(
        ...,
        description="Knowledge base coverage assessment"
    )

    raw_summary: str = Field(
        ...,
        description="Normalized problem description for RAG queries"
    )

    detected_model: Optional[str] = Field(
        None,
        description="Specific model/series detected (G120C, ControlLogix, etc.)"
    )

    detected_part_number: Optional[str] = Field(
        None,
        description="Part number from nameplate OCR or text"
    )

    detected_fault_codes: List[str] = Field(
        default_factory=list,
        description="Fault codes extracted from text or OCR"
    )

    ocr_text: Optional[str] = Field(
        None,
        description="Raw OCR text from image (for research pipeline)"
    )

    vision_caption: Optional[str] = Field(
        None,
        description="Vision model caption of image (if applicable)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "vendor": "Siemens",
                "equipment_type": "VFD",
                "application": "overhead_crane",
                "symptom": "F3002 overvoltage fault",
                "context_source": "text_only",
                "confidence": 0.92,
                "kb_coverage": "strong",
                "raw_summary": "Siemens G120C VFD F3002 overvoltage troubleshooting",
                "detected_model": "G120C",
                "detected_fault_codes": ["F3002"]
            }
        }


# ============================================================================
# Response Model
# ============================================================================

class RivetResponse(BaseModel):
    """
    Unified response model from RIVET Pro.

    This is what gets sent back to the user via their channel (Telegram, etc.).
    Contains the answer text, citations, and any additional resources.

    Examples:
        RivetResponse(
            text="F3002 is an overvoltage fault on DC bus. Check input voltage...",
            agent_id="siemens_agent",
            route_taken="A_direct_sme",
            links=["https://support.siemens.com/manual/G120C"],
            confidence=0.89,
            trace={"docs_retrieved": 5, "processing_time_ms": 1234}
        )
    """

    text: str = Field(
        ...,
        description="Answer text to send to user"
    )

    agent_id: AgentID = Field(
        ...,
        description="Which SME agent generated this response"
    )

    route_taken: RouteType = Field(
        ...,
        description="Which orchestrator route was used"
    )

    links: List[str] = Field(
        default_factory=list,
        description="Manual/documentation URLs referenced or found"
    )

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Agent confidence in this answer (0.0-1.0)"
    )

    requires_followup: bool = Field(
        default=False,
        description="True if agent needs more information from user"
    )

    suggested_actions: List[str] = Field(
        default_factory=list,
        description="Step-by-step actions for technician"
    )

    safety_warnings: List[str] = Field(
        default_factory=list,
        description="Safety reminders relevant to this issue"
    )

    cited_documents: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Documents cited in answer (title, URL, page)"
    )

    trace: Dict[str, Any] = Field(
        default_factory=dict,
        description="Debug/logging metadata (processing time, docs retrieved, etc.)"
    )

    research_triggered: bool = Field(
        default=False,
        description="True if research pipeline was triggered (Route C)"
    )

    kb_enrichment_triggered: bool = Field(
        default=False,
        description="True if KB enrichment was triggered (Route B)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "F3002 is DC bus overvoltage. Check input voltage is 480V +/-10%...",
                "agent_id": "siemens_agent",
                "route_taken": "A_direct_sme",
                "links": ["https://support.siemens.com/manual/G120C"],
                "confidence": 0.89,
                "suggested_actions": [
                    "Check input voltage with multimeter",
                    "Verify parameter P0210 = 480V",
                    "Check DC bus voltage on display"
                ]
            }
        }


# ============================================================================
# Trace/Logging Models
# ============================================================================

class AgentTrace(BaseModel):
    """
    Detailed trace information for conversation logging.

    Used by conversation logger to track full lifecycle of request processing.
    """

    request_id: str = Field(
        ...,
        description="Unique request ID for tracing"
    )

    user_id: str
    channel: ChannelType
    message_type: MessageType

    intent: RivetIntent
    route: RouteType
    agent_id: AgentID

    response_text: str

    docs_retrieved: int = Field(
        default=0,
        description="Number of RAG documents retrieved"
    )

    doc_sources: List[str] = Field(
        default_factory=list,
        description="Source URLs/titles of retrieved docs"
    )

    processing_time_ms: int = Field(
        default=0,
        description="Total processing time in milliseconds"
    )

    llm_calls: int = Field(
        default=1,
        description="Number of LLM API calls made"
    )

    research_triggered: bool = False
    kb_enrichment_triggered: bool = False

    error: Optional[str] = Field(
        None,
        description="Error message if request failed"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Request timestamp (UTC)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req_2025-12-15_12345",
                "user_id": "telegram_12345",
                "channel": "telegram",
                "message_type": "text",
                "route": "A_direct_sme",
                "agent_id": "siemens_agent",
                "docs_retrieved": 5,
                "processing_time_ms": 1234
            }
        }


# ============================================================================
# Helper Functions
# ============================================================================

def create_text_request(
    user_id: str,
    text: str,
    channel: ChannelType = ChannelType.TELEGRAM,
    **metadata
) -> RivetRequest:
    """Helper to create text-only request"""
    return RivetRequest(
        user_id=user_id,
        channel=channel,
        message_type=MessageType.TEXT,
        text=text,
        metadata=metadata
    )


def create_image_request(
    user_id: str,
    image_path: str,
    caption: Optional[str] = None,
    channel: ChannelType = ChannelType.TELEGRAM,
    **metadata
) -> RivetRequest:
    """Helper to create image request"""
    return RivetRequest(
        user_id=user_id,
        channel=channel,
        message_type=MessageType.IMAGE if not caption else MessageType.TEXT_WITH_IMAGE,
        text=caption,
        image_path=image_path,
        metadata=metadata
    )

# Universal Knowledge Atom Specification v1.0

## Overview

The **Knowledge Atom** is the fundamental unit of knowledge in the Agent Factory system. One atom = one teachable/learnable/actionable concept, pattern, fault, or procedure.

**Design Principles**:
- **Universal**: Works across RIVET, PLC Tutor, and future verticals
- **IEEE LOM-Aligned**: Based on Learning Object Metadata standard
- **Queryable**: Vector search + structured filters + graph traversal
- **Versionable**: Semantic versioning, deprecation support
- **Auditable**: Source attribution, review history, validation status

---

## Base Schema: LearningObject

All atoms inherit from this base class (IEEE LOM-inspired):

```python
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import List, Optional, Literal
from enum import Enum

class RelationType(str, Enum):
    IS_PART_OF = "isPartOf"
    HAS_PART = "hasPart"
    REQUIRES = "requires"
    IS_REQUIRED_BY = "isRequiredBy"
    REFERENCES = "references"
    IS_REFERENCED_BY = "isReferencedBy"
    IS_VERSION_OF = "isVersionOf"
    HAS_VERSION = "hasVersion"
    SIMULATES = "simulates"
    IS_SIMULATED_BY = "isSimulatedBy"

class Relation(BaseModel):
    type: RelationType
    target_id: str
    description: Optional[str] = None

class Identifier(BaseModel):
    catalog: str  # "DOI", "ISBN", "internal", "youtube"
    entry: str

class LearningObject(BaseModel):
    """Base class for all knowledge atoms (IEEE LOM-inspired)"""

    # === Identity ===
    id: str = Field(..., description="Unique identifier (e.g., plc:ab:motor-start-stop)")
    identifiers: List[Identifier] = Field(default_factory=list, description="External identifiers")
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)

    # === Lifecycle ===
    version: str = Field(default="1.0.0", description="Semantic version (semver)")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: Literal["draft", "review", "approved", "deprecated"] = "draft"

    # === Contributors ===
    authors: List[str] = Field(..., min_items=1, description="Creator(s) of this atom")
    reviewers: List[str] = Field(default_factory=list, description="Who validated this")

    # === Educational ===
    educational_level: Literal["intro", "intermediate", "advanced"] = "intro"
    learning_resource_type: str = Field(
        ...,
        description="explanation, example, exercise, simulation, assessment, etc."
    )
    typical_learning_time_minutes: int = Field(
        ge=1,
        le=480,
        description="Expected time to learn/complete"
    )
    intended_audience: List[str] = Field(
        default_factory=list,
        description="student, technician, engineer, manager, etc."
    )

    # === Content ===
    keywords: List[str] = Field(..., min_items=1, description="Searchable tags")
    language: str = Field(default="en", description="ISO 639-1 code")

    # === Sources ===
    source_urls: List[HttpUrl] = Field(default_factory=list, description="Origin references")
    source_citation: Optional[str] = Field(None, description="Formal citation")

    # === Graph Structure ===
    relations: List[Relation] = Field(
        default_factory=list,
        description="Links to other atoms (prerequisites, etc.)"
    )

    # === Validation ===
    confidence_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Agent or human confidence (0-1)"
    )
    validation_notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "elec:basic:ohms-law",
                "title": "Ohm's Law: V = I × R",
                "description": "The fundamental relationship between voltage, current, and resistance in electrical circuits.",
                "authors": ["IndustrialSkillsHub"],
                "educational_level": "intro",
                "learning_resource_type": "explanation",
                "typical_learning_time_minutes": 15,
                "keywords": ["electricity", "ohms law", "voltage", "current", "resistance"],
                "source_urls": ["https://en.wikipedia.org/wiki/Ohm%27s_law"],
                "relations": [
                    {"type": "requires", "target_id": "elec:basic:voltage"},
                    {"type": "requires", "target_id": "elec:basic:current"}
                ]
            }
        }
```

---

## Specialized Schema: PLCAtom

For PLC Tutor vertical:

```python
class PLCAtom(LearningObject):
    """PLC/automation-specific knowledge atom"""

    # === Domain ===
    domain: Literal[
        "electricity",      # Voltage, current, Ohm's Law, power
        "plc",              # Ladder, ST, timers, counters
        "drives",           # VFDs, servo, motion control
        "safety",           # Lockout/tagout, E-stops, guarding
        "ai_agent",         # Meta-content: how the AI learns
        "networking",       # Modbus, Ethernet/IP, Profinet
        "hmi_scada"         # Human-machine interfaces
    ]

    # === Vendor Specifics ===
    vendor: Literal["siemens", "allen_bradley", "generic", "other"] = "generic"
    platform: Optional[str] = Field(
        None,
        description="s7-1200, control_logix, codesys, etc."
    )

    # === Programming ===
    plc_language: Optional[Literal["ladder", "stl", "fbd", "scl", "st"]] = None
    code_snippet: Optional[str] = Field(
        None,
        description="Canonical code example (ladder export or ST)"
    )

    # === I/O & Signals ===
    io_signals: List[str] = Field(
        default_factory=list,
        description="Tag names or addresses (e.g., Start_PB, Motor_Run)"
    )

    # === Safety ===
    hazards: List[str] = Field(
        default_factory=list,
        description="Safety warnings (e.g., 'Live electrical work', 'Rotating machinery')"
    )
    safety_level: Literal["info", "caution", "warning", "danger"] = "info"

    # === Assessment ===
    quiz_question_ids: List[str] = Field(
        default_factory=list,
        description="IDs of quiz questions testing this atom"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "plc:ab:motor-start-stop-seal",
                "title": "3-Wire Motor Start/Stop/Seal-In",
                "description": "Basic motor control circuit using start button, stop button, and auxiliary contact seal-in.",
                "domain": "plc",
                "vendor": "allen_bradley",
                "platform": "control_logix",
                "plc_language": "ladder",
                "educational_level": "intro",
                "learning_resource_type": "pattern",
                "typical_learning_time_minutes": 20,
                "io_signals": ["Start_PB", "Stop_PB", "Motor_Run", "Motor_Contactor"],
                "code_snippet": "BST\nXIC Start_PB\nNXB\nXIC Motor_Run\nBND\nXIC Stop_PB\nOTE Motor_Contactor\nOTL Motor_Run",
                "hazards": ["Live electrical work - lockout/tagout required"],
                "safety_level": "caution",
                "keywords": ["motor control", "start stop", "seal in", "ladder logic"],
                "relations": [
                    {"type": "requires", "target_id": "plc:generic:contacts-coils"},
                    {"type": "requires", "target_id": "elec:basic:motor-basics"}
                ]
            }
        }
```

---

## Specialized Schema: RIVETAtom

For RIVET (industrial maintenance) vertical:

```python
class RootCause(BaseModel):
    cause: str
    probability: float = Field(ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)

class CorrectiveAction(BaseModel):
    action: str
    parts_needed: List[str] = Field(default_factory=list)
    time_estimate_minutes: int
    skill_level: Literal["basic", "intermediate", "advanced", "expert"]

class RIVETAtom(LearningObject):
    """Industrial maintenance/troubleshooting knowledge atom"""

    # === Equipment ===
    equipment_class: str = Field(
        ...,
        description="VFD, motor, conveyor, HVAC, packaging_machine, etc."
    )
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    environment: Optional[str] = Field(
        None,
        description="outdoor, food_processing, high_temp, etc."
    )

    # === Failure Pattern ===
    symptoms: List[str] = Field(
        ...,
        min_items=1,
        description="Observable signs (codes, sounds, behaviors)"
    )
    root_causes: List[RootCause] = Field(
        default_factory=list,
        description="Likely causes with probabilities"
    )

    # === Diagnosis ===
    diagnostic_steps: List[str] = Field(
        default_factory=list,
        description="Ordered troubleshooting steps"
    )
    required_tools: List[str] = Field(
        default_factory=list,
        description="Multimeter, megger, infrared camera, etc."
    )

    # === Repair ===
    corrective_actions: List[CorrectiveAction] = Field(
        default_factory=list,
        description="Fixes with parts, time, skill level"
    )

    # === Safety ===
    constraints: List[str] = Field(
        default_factory=list,
        description="Safety notes, lockout/tagout, when NOT to apply"
    )
    safety_level: Literal["info", "caution", "warning", "danger"] = "caution"

    # === Validation ===
    validation_stage: int = Field(
        default=1,
        ge=1,
        le=6,
        description="RIVET's 6-stage validation pipeline"
    )
    validated_by_expert: bool = False
    expert_notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "rivet:vfd:overcurrent-on-startup",
                "title": "VFD Overcurrent Fault on Motor Startup",
                "description": "Variable frequency drive trips with overcurrent (OC) fault code immediately when starting motor.",
                "equipment_class": "VFD",
                "manufacturer": "Allen-Bradley",
                "model": "PowerFlex 525",
                "educational_level": "intermediate",
                "learning_resource_type": "fault",
                "typical_learning_time_minutes": 30,
                "symptoms": [
                    "Fault code: OC (overcurrent)",
                    "Trips within 1-2 seconds of start command",
                    "Motor does not rotate or barely moves"
                ],
                "root_causes": [
                    {
                        "cause": "Motor winding short/ground fault",
                        "probability": 0.4,
                        "evidence": ["Low insulation resistance", "Megger test < 1MΩ"]
                    },
                    {
                        "cause": "Incorrect motor parameters (FLA setting too low)",
                        "probability": 0.3,
                        "evidence": ["Motor nameplate FLA doesn't match drive settings"]
                    },
                    {
                        "cause": "Mechanical overload (seized bearing, jammed load)",
                        "probability": 0.2,
                        "evidence": ["Motor shaft won't turn freely", "Unusual noise"]
                    }
                ],
                "diagnostic_steps": [
                    "Check VFD fault history and logged current values",
                    "Verify motor nameplate FLA matches drive parameter P011",
                    "Disconnect motor from VFD, megger test motor windings (500V DC)",
                    "Manually rotate motor shaft to check for mechanical binding",
                    "Measure motor winding resistance (should be balanced)"
                ],
                "corrective_actions": [
                    {
                        "action": "Adjust FLA parameter to match motor nameplate",
                        "parts_needed": [],
                        "time_estimate_minutes": 10,
                        "skill_level": "basic"
                    },
                    {
                        "action": "Replace motor (winding failure confirmed)",
                        "parts_needed": ["Replacement motor (same HP, frame, voltage)"],
                        "time_estimate_minutes": 120,
                        "skill_level": "intermediate"
                    }
                ],
                "constraints": [
                    "Lockout/tagout required before working on motor or VFD",
                    "Do not bypass overcurrent protection",
                    "Ensure proper motor grounding before re-energizing"
                ],
                "safety_level": "danger",
                "validation_stage": 4,
                "keywords": ["vfd", "overcurrent", "troubleshooting", "motor", "drive"]
            }
        }
```

---

## Supporting Schemas

### Module & Course (Curriculum Structure)

```python
class Module(BaseModel):
    """Group of related atoms forming one lesson/module"""
    id: str
    title: str
    description: str
    atom_ids: List[str] = Field(
        ...,
        description="Ordered list of atoms to cover"
    )
    level: Literal["intro", "intermediate", "advanced"]
    estimated_hours: float
    prerequisites: List[str] = Field(
        default_factory=list,
        description="Module IDs that must be completed first"
    )

class Course(BaseModel):
    """Complete learning path across multiple modules"""
    id: str
    title: str
    description: str
    module_ids: List[str] = Field(
        ...,
        description="Ordered modules"
    )
    estimated_hours: float
    price_usd: Optional[float] = None
    target_audience: List[str]
```

### VideoScript (Content Production)

```python
class VideoScript(BaseModel):
    """Script for one educational video"""
    id: str
    title: str
    description: str
    outline: List[str] = Field(
        ...,
        description="Bullet sections (hook, main points, recap)"
    )
    script_text: str = Field(
        ...,
        description="Full narration with emotion markers [enthusiastic], [concerned]"
    )
    atom_ids: List[str] = Field(
        ...,
        description="Which atoms this video teaches"
    )
    level: Literal["intro", "intermediate", "advanced"]
    duration_minutes: int
    visual_cues: List[str] = Field(
        default_factory=list,
        description="Timing for diagrams, code, simulations"
    )

class MediaAssets(BaseModel):
    audio_path: str
    video_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    b_roll_clips: List[str] = Field(default_factory=list)

class UploadJob(BaseModel):
    """Ready-to-publish video"""
    id: str
    channel: str  # "industrial_skills_hub", "rivet_official"
    video_script_id: str
    media: MediaAssets

    # YouTube metadata
    youtube_title: str
    youtube_description: str
    tags: List[str]
    playlist_ids: List[str] = Field(default_factory=list)

    # Publishing
    visibility: Literal["public", "unlisted", "private"] = "public"
    scheduled_time: Optional[datetime] = None

    # Tracking
    uploaded: bool = False
    youtube_video_id: Optional[str] = None
    upload_timestamp: Optional[datetime] = None
```

---

## Storage & Querying

### Database Schema (Supabase + pgvector)

```sql
-- Main atoms table
CREATE TABLE knowledge_atoms (
    id TEXT PRIMARY KEY,
    atom_type TEXT NOT NULL CHECK (atom_type IN ('LearningObject', 'PLCAtom', 'RIVETAtom')),

    -- JSON storage for full atom
    content JSONB NOT NULL,

    -- Extracted fields for fast filtering
    title TEXT NOT NULL,
    educational_level TEXT,
    domain TEXT,  -- For PLCAtom
    equipment_class TEXT,  -- For RIVETAtom
    status TEXT DEFAULT 'draft',

    -- Vector embedding for semantic search
    embedding vector(1536),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    CONSTRAINT valid_json CHECK (jsonb_typeof(content) = 'object')
);

-- Vector similarity index (HNSW for speed)
CREATE INDEX ON knowledge_atoms USING hnsw (embedding vector_cosine_ops);

-- Text search index
CREATE INDEX atoms_title_idx ON knowledge_atoms USING gin(to_tsvector('english', title));
CREATE INDEX atoms_content_idx ON knowledge_atoms USING gin(to_tsvector('english', content::text));

-- Fast filters
CREATE INDEX atoms_level_idx ON knowledge_atoms(educational_level);
CREATE INDEX atoms_status_idx ON knowledge_atoms(status);
CREATE INDEX atoms_type_idx ON knowledge_atoms(atom_type);
```

### Query Patterns

**Hybrid Search** (vector + keyword):
```python
def search_atoms(
    query: str,
    filters: dict = None,
    limit: int = 10
) -> List[LearningObject]:
    """
    Hybrid search: semantic similarity + keyword match + structured filters
    """
    # 1. Generate embedding for query
    query_embedding = embed(query)

    # 2. Semantic search (pgvector)
    semantic_results = supabase.rpc(
        'match_atoms',
        {
            'query_embedding': query_embedding,
            'match_threshold': 0.7,
            'match_count': limit * 2
        }
    )

    # 3. Keyword search (full-text)
    keyword_results = supabase.from_('knowledge_atoms') \
        .select('*') \
        .text_search('title', query) \
        .limit(limit * 2)

    # 4. Apply structured filters
    if filters:
        if 'educational_level' in filters:
            # Filter by level
            pass
        if 'domain' in filters:
            # Filter by domain
            pass

    # 5. Merge and rank (RRF: Reciprocal Rank Fusion)
    combined = merge_and_rank(semantic_results, keyword_results)

    return combined[:limit]
```

**Prerequisite Graph Traversal**:
```python
def get_learning_path(target_atom_id: str) -> List[str]:
    """
    Returns ordered list of atom IDs from prerequisites to target
    """
    # BFS traversal of 'requires' relations
    visited = set()
    queue = [target_atom_id]
    path = []

    while queue:
        current = queue.pop(0)
        if current in visited:
            continue

        atom = get_atom(current)
        prereqs = [r.target_id for r in atom.relations if r.type == 'requires']

        queue.extend(prereqs)
        visited.add(current)
        path.insert(0, current)  # Prepend prerequisites

    return path
```

---

## Validation Pipeline

### 6-Stage Validation (RIVET)

For safety-critical maintenance knowledge:

1. **Stage 1: Schema Validation**
   - Pydantic model validation
   - Required fields present
   - Data types correct

2. **Stage 2: Source Verification**
   - Citations traceable
   - Credible sources (OEM docs, standards)
   - No plagiarism

3. **Stage 3: Technical Accuracy**
   - Cross-checked against multiple sources
   - Math/physics correct
   - No contradictions

4. **Stage 4: Safety Review**
   - Hazards identified
   - Safety level appropriate
   - No dangerous omissions

5. **Stage 5: Expert Review**
   - Human technician validates
   - Real-world applicability confirmed
   - Edge cases considered

6. **Stage 6: Field Testing**
   - Used in real troubleshooting
   - Feedback incorporated
   - Success rate tracked

**Only Stage 6 atoms used for production responses.**

### Quality Checks (PLC Tutor)

For educational content (less stringent than RIVET):

1. **Schema Validation**: Pydantic enforcement
2. **Originality Check**: Plagiarism scan (Copyscape)
3. **Code Correctness**: Syntax check, simulation test
4. **Pedagogical Review**: Clear explanation, appropriate level
5. **Human Spot-Check**: Sample review (1 in 10 after calibration)

---

## Usage Examples

### Creating a New PLCAtom

```python
from datetime import datetime

ohms_law_atom = PLCAtom(
    id="elec:basic:ohms-law",
    title="Ohm's Law: V = I × R",
    description="The fundamental relationship between voltage, current, and resistance.",
    domain="electricity",
    vendor="generic",
    authors=["IndustrialSkillsHub"],
    educational_level="intro",
    learning_resource_type="explanation",
    typical_learning_time_minutes=15,
    keywords=["electricity", "ohms law", "voltage", "current", "resistance"],
    source_urls=["https://en.wikipedia.org/wiki/Ohm%27s_law"],
    relations=[
        Relation(type=RelationType.REQUIRES, target_id="elec:basic:voltage"),
        Relation(type=RelationType.REQUIRES, target_id="elec:basic:current")
    ],
    confidence_score=0.95
)

# Save to database
save_atom(ohms_law_atom)
```

### Querying for Prerequisites

```python
# Find all atoms needed before learning PLC timers
path = get_learning_path("plc:generic:timer-ton")
# Returns: ["elec:basic:voltage", "elec:basic:current", "plc:generic:contacts-coils", "plc:generic:timer-ton"]
```

### Video Production Pipeline

```python
# 1. Select atoms for video
atoms = search_atoms("ohms law", filters={"educational_level": "intro"})

# 2. Generate script
script = scriptwriter_agent.create_script(
    topic="Ohm's Law for Industrial Techs",
    atoms=atoms,
    duration_minutes=10
)

# 3. Produce media
audio = voice_agent.generate_audio(script.script_text)
video = video_agent.assemble(audio=audio, atoms=atoms)

# 4. Upload
job = UploadJob(
    id="upload_ohms_law_v1",
    channel="industrial_skills_hub",
    video_script_id=script.id,
    media=MediaAssets(audio_path=audio.path, video_path=video.path),
    youtube_title="Ohm's Law Explained for Industrial Technicians",
    youtube_description="Learn V = I × R with real-world examples...",
    tags=["ohms law", "electricity", "industrial", "maintenance"],
    visibility="public"
)

uploader_agent.publish(job)
```

---

## Atom Lifecycle

```
Draft → Review → Approved → Published → (Feedback) → Updated → Deprecated
```

1. **Draft**: Agent creates from sources
2. **Review**: Quality Checker + Human review
3. **Approved**: Passes validation, ready for use
4. **Published**: Used in videos, courses, chatbot responses
5. **Feedback**: User questions, corrections, suggestions
6. **Updated**: New version created (v1.0.0 → v1.1.0)
7. **Deprecated**: Superseded by better atom, marked obsolete

---

## Version Management

**Semantic Versioning**:
- **MAJOR** (1.0.0 → 2.0.0): Breaking change (incompatible with old queries)
- **MINOR** (1.0.0 → 1.1.0): Added content, same structure
- **PATCH** (1.0.0 → 1.0.1): Typo fixes, clarifications

**Deprecation**:
```python
atom.status = "deprecated"
atom.relations.append(
    Relation(
        type=RelationType.IS_VERSION_OF,
        target_id="new_atom_id",
        description="Superseded by improved version"
    )
)
```

---

## Success Metrics

**Quality**:
- 95%+ of atoms pass Stage 1 validation (schema)
- 80%+ of atoms pass Stage 4 (safety review)
- 50%+ of RIVET atoms reach Stage 6 (field-tested)

**Quantity**:
- PLC Tutor: 500-1K atoms by Month 6
- RIVET: 300-500 atoms per equipment family
- Total: 10K-20K atoms by Year 3

**Utility**:
- 90%+ of user questions answered with atom-backed knowledge
- 80%+ of videos reference 3+ atoms
- 70%+ of atoms used in at least one video or course

---

## Conclusion

The Universal Knowledge Atom Standard is the **data contract** across all Agent Factory verticals.

- **IEEE LOM-based**: Industry-recognized, proven for education
- **Extensible**: Add new atom types without breaking existing ones
- **Queryable**: Vector + keyword + graph traversal
- **Versionable**: Track changes, deprecate safely
- **The Moat**: 100K+ validated atoms = competitive advantage

All agents produce/consume atoms. All videos teach atoms. All courses sequence atoms. All APIs serve atoms.

**Atoms are the foundation. Everything else builds on them.**

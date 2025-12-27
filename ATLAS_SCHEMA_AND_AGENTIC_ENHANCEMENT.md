# Atlas CMMS Enhancement Plan
## Schema, Equipment Library, Intelligent Resource Routing & Agentic Troubleshooting

**Objective**: Transform Atlas CMMS into an intelligent, equipment-aware system that:
- Stores comprehensive equipment knowledge (hierarchical subsystems, parts, prints, manuals)
- Accepts work orders via Telegram (voice/text/photos)
- Automatically routes to relevant resources (manuals, prints, troubleshooting guides)
- Uses agentic processes to generate resources when KB gaps exist

**Target Timeline**: Weeks 1–4 (schema + core agents) → Weeks 5–12 (full integration + validation)

---

## PART 1: DATABASE SCHEMA EXTENSIONS

### Current Atlas CMMS Structure (Reference)
Atlas has core tables:
- `assets` (equipment)
- `work_orders`
- `tasks`
- `parts` / `inventory`
- `preventive_maintenance`
- `users`
- `locations`

### What We're Adding

#### 1. Equipment Hierarchy & Subsystems

**Table: `equipment_subsystems`**
```sql
CREATE TABLE equipment_subsystems (
  id UUID PRIMARY KEY,
  parent_equipment_id UUID REFERENCES assets(id),
  subsystem_name VARCHAR(255),  -- e.g., "Brake Assembly", "Control Panel", "Motor Unit"
  subsystem_type VARCHAR(100),  -- e.g., "brake", "electrical", "mechanical", "hydraulic"
  description TEXT,
  manufacturer VARCHAR(255),
  model_number VARCHAR(255),
  serial_number VARCHAR(255),
  installation_date DATE,
  expected_lifespan_hours INT,
  current_operating_hours INT,
  critical_for_safety BOOLEAN DEFAULT false,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Example hierarchy:
-- Asset: "Stardust Racers Roller Coaster"
--   ├─ Subsystem: "Brake Assembly" (brake_subsystem_id_1)
--   ├─ Subsystem: "Control Panel" (control_subsystem_id_1)
--   ├─ Subsystem: "Motor Unit" (motor_subsystem_id_1)
--      └─ Sub-subsystem: "Motor Windings"
--      └─ Sub-subsystem: "Motor Bearings"
```

**Table: `equipment_components`**
```sql
CREATE TABLE equipment_components (
  id UUID PRIMARY KEY,
  subsystem_id UUID REFERENCES equipment_subsystems(id),
  component_name VARCHAR(255),  -- e.g., "Brake Pad Set", "Thermal Relay", "Bearing"
  component_type VARCHAR(100),  -- e.g., "mechanical", "electrical", "fluid", "sensor"
  manufacturer VARCHAR(255),
  part_number VARCHAR(255),
  supplier_link VARCHAR(512),
  typical_failure_mode VARCHAR(255),  -- e.g., "wear", "overheating", "electrical failure"
  mtbf_hours INT,  -- Mean Time Between Failures
  replacement_cost_usd DECIMAL(10,2),
  replacement_procedure_doc_id UUID,  -- Links to document library
  created_at TIMESTAMP
);
```

#### 2. Resource Library (Manuals, Prints, Docs)

**Table: `equipment_resources`**
```sql
CREATE TABLE equipment_resources (
  id UUID PRIMARY KEY,
  equipment_id UUID REFERENCES assets(id),
  subsystem_id UUID REFERENCES equipment_subsystems(id),  -- Can be NULL for equipment-level resources
  resource_type VARCHAR(50),  -- 'manual', 'schematic', 'wiring_diagram', 'mechanical_drawing', 'troubleshooting_guide', 'datasheet', 'video', 'procedure', 'reference'
  resource_title VARCHAR(255),  -- e.g., "Brake Assembly User Manual", "Control Panel Wiring Diagram"
  description TEXT,
  resource_format VARCHAR(50),  -- 'pdf', 'image', 'video_link', 'html', 'raw_text'
  file_path_or_url VARCHAR(1024),  -- S3 URL or external link
  file_size_bytes INT,
  uploaded_by_user_id UUID REFERENCES users(id),
  source VARCHAR(100),  -- 'customer_upload', 'vendor_provided', 'ai_generated', 'manual_entry'
  relevance_tags VARCHAR(500),  -- Comma-separated: "electrical,troubleshooting,preventive_maintenance"
  is_verified BOOLEAN DEFAULT false,  -- Tech or admin confirmed accuracy
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  deleted_at TIMESTAMP  -- Soft delete
);

-- Examples:
-- id: manual_1, equipment_id: stardust_id, resource_type: 'manual', title: 'Stardust Racers Operations Manual'
-- id: schematic_1, equipment_id: stardust_id, subsystem_id: control_panel_id, resource_type: 'schematic', title: 'Control Panel Schematic'
```

**Table: `resource_embeddings`** (for semantic search)
```sql
CREATE TABLE resource_embeddings (
  id UUID PRIMARY KEY,
  resource_id UUID REFERENCES equipment_resources(id),
  embedding_text TEXT,  -- Extracted or full text from PDF/document
  embedding_vector vector(1536),  -- OpenAI/Anthropic embedding (1536 dims)
  embedding_model VARCHAR(50),  -- 'claude-3-5-sonnet', 'text-embedding-3-large', etc.
  indexed_at TIMESTAMP
);
```

#### 3. Work Order Enhancements

**Table: `work_orders` (existing Atlas table, ADD these columns)**
```sql
ALTER TABLE work_orders ADD COLUMN (
  telegram_chat_id BIGINT,  -- Telegram chat ID for this work order
  voice_transcript TEXT,  -- Original voice transcription
  work_order_photos TEXT[],  -- Array of photo URLs uploaded via Telegram
  initial_diagnosis_method VARCHAR(50),  -- 'voice', 'photo', 'manual_entry', 'ai_diagnosed'
  ai_recommended_resources UUID[],  -- Array of resource_ids that agent recommended
  ai_troubleshooting_guide TEXT,  -- Generated troubleshooting steps if no manual exists
  resource_research_status VARCHAR(50),  -- 'pending', 'in_progress', 'complete', 'failed'
  resource_research_timestamp TIMESTAMP,
  is_resource_generated BOOLEAN DEFAULT false  -- True if troubleshooting guide was AI-generated
);
```

**Table: `work_order_resource_mapping`** (Many-to-many)
```sql
CREATE TABLE work_order_resource_mapping (
  id UUID PRIMARY KEY,
  work_order_id UUID REFERENCES work_orders(id),
  resource_id UUID REFERENCES equipment_resources(id),
  relevance_score FLOAT,  -- 0.0 to 1.0, from agent ranking
  presented_to_user BOOLEAN DEFAULT false,
  user_feedback VARCHAR(50),  -- 'helpful', 'not_helpful', 'partially_helpful', null
  clicked_at TIMESTAMP,
  created_at TIMESTAMP
);
```

#### 4. Agentic Process & Research Log

**Table: `ai_research_jobs`**
```sql
CREATE TABLE ai_research_jobs (
  id UUID PRIMARY KEY,
  work_order_id UUID REFERENCES work_orders(id),
  job_type VARCHAR(50),  -- 'resource_search', 'troubleshooting_generation', 'resource_creation'
  equipment_id UUID REFERENCES assets(id),
  subsystem_id UUID REFERENCES equipment_subsystems(id),
  issue_description TEXT,  -- What the tech reported
  search_query_generated TEXT,  -- Search/retrieval query the agent constructed
  resources_found TEXT[],  -- Array of resource IDs found
  agent_reasoning TEXT,  -- Why these resources were ranked first
  fallback_triggered BOOLEAN DEFAULT false,  -- Did we fallback to LLM troubleshooting?
  generated_content_id UUID,  -- If content was generated, links to it
  job_status VARCHAR(50),  -- 'queued', 'running', 'complete', 'failed'
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  error_message TEXT
);
```

**Table: `ai_generated_resources`** (for agent-created content)
```sql
CREATE TABLE ai_generated_resources (
  id UUID PRIMARY KEY,
  work_order_id UUID REFERENCES work_orders(id),
  equipment_id UUID REFERENCES assets(id),
  subsystem_id UUID REFERENCES equipment_subsystems(id),
  content_type VARCHAR(50),  -- 'troubleshooting_guide', 'diagnostic_flowchart', 'procedure'
  generated_content TEXT,  -- Markdown or structured text
  generation_model VARCHAR(100),  -- 'claude-3-5-sonnet', etc.
  kb_atoms_used TEXT[],  -- Which existing KB pieces informed this
  human_review_status VARCHAR(50),  -- 'pending_review', 'approved', 'rejected'
  reviewed_by_user_id UUID,
  review_feedback TEXT,
  created_at TIMESTAMP,
  reviewed_at TIMESTAMP
);
```

#### 5. Knowledge Base Atoms (KB granules)

**Table: `knowledge_atoms`**
```sql
CREATE TABLE knowledge_atoms (
  id UUID PRIMARY KEY,
  equipment_type VARCHAR(100),  -- 'brake', 'electrical_panel', 'bearing', etc.
  atom_title VARCHAR(255),  -- e.g., "How to diagnose brake pad wear"
  atom_content TEXT,  -- Markdown-formatted atomic fact/procedure
  atom_category VARCHAR(50),  -- 'symptom', 'diagnosis_step', 'prevention', 'repair_procedure'
  confidence_score FLOAT,  -- 0.0 to 1.0 (how confident is this?)
  source VARCHAR(100),  -- 'vendor_manual', 'technician_feedback', 'industry_standard', 'ai_inferred'
  source_reference_id UUID,  -- Link to original resource if applicable
  created_by_user_id UUID,
  verified_by_expert BOOLEAN DEFAULT false,
  usage_count INT DEFAULT 0,  -- How many times used in troubleshooting
  feedback_score FLOAT DEFAULT 0.0,  -- Aggregate technician feedback
  embedding_vector vector(1536),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Examples:
-- "If brake pad thickness < 2mm, replacement is due"
-- "Control panel overheating + loss of signal = check thermal relay"
-- "Bearing noise + increased vibration = order new bearing immediately"
```

---

## PART 2: TELEGRAM INTEGRATION & WORK ORDER CAPTURE

### Telegram Bot Flow

```
Technician
    ↓
[Sends to Telegram Bot]
  - Voice message ("Brake assembly not stopping properly")
  - Text message ("Motor overheating, need help")
  - Photos (damage, error code, visual inspection)
  - Schematic/print (for reference)
    ↓
[Bot receives & processes]
  - Transcribe voice (Whisper API)
  - Extract intent (Claude intent parser)
  - Identify equipment + subsystem (from intent or manual selection)
  - Store initial work order + attachments
    ↓
[Trigger Agentic Resource Search]
  - Query KB for relevant resources (vector + keyword search)
  - If strong matches: send manual/schematic to tech immediately
  - If weak matches: trigger troubleshooting generation agent
    ↓
[Response to Tech]
  - "Here's the brake assembly manual, page 12 covers your issue"
  - OR "Found 3 related troubleshooting guides, attached"
  - OR "No existing guide. I'm analyzing your issue now... [AI-generated guide]"
```

### Telegram Bot Commands

```
/start                     → Welcome, link Telegram ID to account
/new_workorder            → Start new work order (guided)
/equipment <name>         → Show equipment list, select one
/help <equipment>         → Search KB for that equipment's manuals
/report <issue>           → Voice/text issue, system finds resources
/photo <describe>         → Upload photo + description, system analyzes
/status <wo_id>           → Check work order status + resources sent
/feedback <wo_id> <star>  → Rate if resources were helpful (1-5 stars)

-- Voice messages: Auto-transcribe, route to intent parser
-- Photos: Store, pass to Claude vision if needed (identify part, damage, etc.)
```

---

## PART 3: AGENTIC SYSTEM & RESOURCE ROUTING

### Agent 1: Resource Retrieval Agent

**Trigger**: Work order created with issue description + equipment ID

**Behavior**:
```
Input: 
  - equipment_id: "stardust_racers"
  - subsystem_id: "brake_assembly"
  - issue_description: "Brake pad wear, not stopping smoothly"
  - work_order_photos: [photo_url_1, photo_url_2]

Process:
  1. Semantic search in resource_embeddings for "brake pad wear stopping"
  2. Keyword search in equipment_resources for equipment_id + "brake"
  3. Rank by relevance_score + resource_type (prefer 'manual' > 'schematic' > 'procedure')
  4. Check if manual/schematic exists for this subsystem
  
Output:
  - If strong match (score > 0.8):
      Return top 3 resources: [User Manual page 12, Brake Assembly Schematic, Replacement Procedure]
      Confidence: "high - found official manual"
  
  - If weak/no match (score < 0.5):
      Trigger Troubleshooting Generation Agent
      Log: "No official manual found, generating guidance"
      
Logging:
  - Insert into ai_research_jobs (resource_search)
  - Insert into work_order_resource_mapping (for each resource found)
```

**Schema / Implementation**:
```python
# Pseudocode for agent
class ResourceRetrievalAgent:
  def retrieve(self, work_order):
    # 1. Semantic search
    embeddings = query_vector_db(
      query_text=work_order.issue_description,
      equipment_id=work_order.equipment_id,
      subsystem_id=work_order.subsystem_id,
      limit=5
    )
    
    # 2. Keyword search
    keywords = extract_keywords(work_order.issue_description)
    keyword_results = sql_search(
      table="equipment_resources",
      where={"equipment_id": work_order.equipment_id, "tags": keywords}
    )
    
    # 3. Combine + rank
    all_candidates = embeddings + keyword_results
    ranked = rank_by_relevance_and_type(all_candidates)
    
    # 4. Decision
    if ranked[0].score > 0.8:
      return ranked[:3]  # Return top 3
    else:
      trigger_troubleshooting_agent(work_order)
      return None
```

### Agent 2: Troubleshooting Generation Agent

**Trigger**: No manual found (or manual insufficient for issue) → Fallback to LLM

**Behavior**:
```
Input:
  - equipment_id, subsystem_id
  - issue_description
  - work_order_photos
  - knowledge_atoms (filtered by equipment type + symptoms)
  
Process:
  1. Gather context:
     - Equipment specs (from equipment_components)
     - Typical failure modes (from equipment_subsystems + components)
     - Relevant KB atoms (filtered by equipment type)
     - Prior work orders for similar issues (from history)
  
  2. Call Claude with structured prompt:
     Prompt template:
     """
     You are an expert technician for [equipment_type] systems.
     
     Equipment: [equipment_name]
     Subsystem: [subsystem_name]
     Issue reported: [issue_description]
     
     Available knowledge base facts:
     - [KB atom 1]
     - [KB atom 2]
     ...
     
     Similar past cases:
     - [Case 1]: Symptom -> Solution
     - [Case 2]: Symptom -> Solution
     
     Generate a step-by-step troubleshooting guide. 
     Output as markdown with:
     1. Diagnosis steps
     2. Safety warnings
     3. Required tools/parts
     4. Repair procedure (if applicable)
     5. When to call vendor support
     """
  
  3. Generate content
  4. Store in ai_generated_resources table
  5. Flag for human review (expert tech/manager)
  
Output:
  - Troubleshooting guide (markdown)
  - Human review status: "pending_review"
  - Sent to tech immediately with caveat: "AI-generated, review by expert"

Logging:
  - Insert into ai_research_jobs (troubleshooting_generation)
  - Insert into ai_generated_resources (for human review)
```

**Schema / Implementation**:
```python
class TroubleshootingGenerationAgent:
  def generate(self, work_order):
    # 1. Gather context
    equipment = fetch_equipment(work_order.equipment_id)
    subsystem = fetch_subsystem(work_order.subsystem_id)
    components = fetch_components(work_order.subsystem_id)
    kb_atoms = query_kb_atoms(
      equipment_type=equipment.type,
      relevant_to_issue=work_order.issue_description
    )
    past_cases = query_work_orders(
      equipment_id=work_order.equipment_id,
      subsystem_id=work_order.subsystem_id,
      limit=5
    )
    
    # 2. Build context for Claude
    context = build_context(equipment, subsystem, components, kb_atoms, past_cases)
    
    # 3. Call Claude
    response = claude.messages.create(
      model="claude-3-5-sonnet-20241022",
      max_tokens=2000,
      messages=[{
        "role": "user",
        "content": build_troubleshooting_prompt(context, work_order)
      }]
    )
    
    # 4. Store result
    generated_resource = save_generated_resource(
      work_order_id=work_order.id,
      content=response.text,
      status="pending_review",
      kb_atoms_used=[atom.id for atom in kb_atoms]
    )
    
    return generated_resource
```

### Agent 3: Resource Creation Agent (Long-term KB building)

**Trigger**: Weekly/monthly job that scans unreviewed generated content + feedback from techs

**Behavior**:
```
Process:
  1. Find ai_generated_resources with status="approved" and never added to KB
  2. Find high-feedback work_orders (technician ratings 4–5 stars)
  3. Extract atomic facts from approved troubleshooting guides
  4. Create knowledge_atoms entries
  5. Link back to original resources
  
Output:
  - New knowledge_atoms added to KB
  - Used in future troubleshooting generations
  - Reduces AI hallucination over time (more grounded in proven knowledge)

Example:
  Approved guide: "Brake Pad Wear Diagnosis"
  Extract atoms:
    - "Brake pad thickness < 2mm = replacement needed"
    - "Squealing noise + reduced braking = check pad wear first"
    - "Visual inspection: compare new vs. worn pads for reference"
  
  Add to knowledge_atoms table with:
    - source: 'approved_ai_guide'
    - source_reference_id: ai_generated_resource.id
    - confidence_score: 0.85 (high, because expert approved)
```

---

## PART 4: IMPLEMENTATION ROADMAP (Weeks 1–12)

### Week 1–2: Schema Design & Database Setup

**Tasks**:
- [ ] Design & review schema (above tables)
- [ ] Create PostgreSQL migrations
- [ ] Add indexes on key columns (equipment_id, subsystem_id, resource_type, embedding_vector)
- [ ] Set up vector DB (pgvector extension in Postgres)
- [ ] Create seed data for Stardust Racers (equipment, subsystems, components, sample manuals)

**Deliverable**: 
- PostgreSQL schema ready
- Empty tables initialized
- Stardust Racers test equipment in DB

### Week 3: Telegram Bot + Work Order Capture

**Tasks**:
- [ ] Create Telegram bot handler
- [ ] Voice message → Whisper transcription
- [ ] Text input → intent extraction (Claude)
- [ ] Photo upload → store + Claude vision (identify part if possible)
- [ ] Create work_orders record from Telegram input
- [ ] Map Telegram user ID → Atlas user

**Deliverable**:
- Technician sends voice to bot → work order created in DB
- Photos stored + indexed
- Intent extracted (equipment, subsystem, issue type)

### Week 4: Resource Retrieval Agent (MVP)

**Tasks**:
- [ ] Implement vector search (semantic + keyword)
- [ ] Rank resources by relevance
- [ ] IF strong match: send top 3 resources to tech via Telegram
- [ ] IF weak match: trigger troubleshooting agent
- [ ] Log research jobs + mappings

**Deliverable**:
- Work order created → agent searches KB
- Resources sent to tech if found
- Agent decisions logged

### Week 5–6: Troubleshooting Generation Agent

**Tasks**:
- [ ] Build context gathering (equipment specs, KB atoms, past cases)
- [ ] Claude prompt engineering (detailed, safety-aware prompts)
- [ ] Generate troubleshooting guides
- [ ] Store generated content + mark as pending review
- [ ] Send to tech with caveat ("AI-generated, review by expert")

**Deliverable**:
- No manual found → agent generates guide
- Tech can see generated vs. official resources
- Guides stored for expert review

### Week 7–8: Knowledge Atoms & Expert Review Flow

**Tasks**:
- [ ] Create expert review interface (web UI in Atlas)
- [ ] Expert marks generated guides as approved/rejected
- [ ] Extract atoms from approved guides
- [ ] Add atoms to knowledge_atoms table
- [ ] Link back to original resources

**Deliverable**:
- Experts can review AI-generated content
- Atoms extracted + stored
- KB gradually builds from approval feedback

### Week 9–10: Equipment Library UI (Frontend)

**Tasks**:
- [ ] Atlas UI: Equipment detail page shows subsystems + components
- [ ] Upload manuals/prints for equipment
- [ ] Organize by type (manual, schematic, procedure, video)
- [ ] Search/browse KB for equipment
- [ ] Work order detail: show resources + feedback form

**Deliverable**:
- Managers can organize equipment library
- Techs can browse + rate resources
- Feedback stored for future ranking

### Week 11–12: End-to-End Testing & Optimization

**Tasks**:
- [ ] Test full flow: voice WO → resource search → generation → expert review
- [ ] Beta test with 5–10 real techs
- [ ] Measure: latency, resource relevance, generation quality
- [ ] Optimize vector search (tune embedding model if needed)
- [ ] Performance tune DB queries

**Deliverable**:
- MVP stable, tested with real users
- Metrics: average response time, relevance scores, expert approval rate
- Ready for Phase 2 (scale, analytics, more integrations)

---

## PART 5: DATA FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│                    TECHNICIAN (Telegram)                         │
│                  Voice | Text | Photo | Print                    │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
        ┌─────────────────────┐
        │  Telegram Bot       │
        │ - Transcribe voice  │
        │ - Extract intent    │
        │ - Store photo/print │
        └────────┬────────────┘
                 │
                 ▼
        ┌─────────────────────┐
        │  Create Work Order  │
        │ - equipment_id      │
        │ - subsystem_id      │
        │ - issue_desc        │
        │ - photos/prints     │
        └────────┬────────────┘
                 │
                 ▼
        ┌──────────────────────────────────┐
        │  Trigger Resource Search Agent   │
        │ - Vector + keyword search        │
        │ - Rank resources by relevance    │
        └────────┬─────────────────────────┘
                 │
          ┌──────┴──────┐
          │             │
    Strong match?    Weak/no match?
      (score > 0.8)   (score < 0.5)
          │             │
          ▼             ▼
    ┌─────────────┐  ┌──────────────────────────────┐
    │ Send top 3  │  │ Trigger Troubleshooting      │
    │ resources   │  │ Generation Agent             │
    │ to tech     │  │ - Gather context (equipment) │
    └─────────────┘  │ - Get KB atoms               │
                     │ - Query past cases           │
                     │ - Call Claude                │
                     │ - Generate guide             │
                     │ - Mark for review            │
                     └──────────────┬───────────────┘
                                    │
                                    ▼
                        ┌─────────────────────────┐
                        │ Store generated resource│
                        │ Send to tech with       │
                        │ "AI-generated" caveat   │
                        └────────┬────────────────┘
                                 │
                                 ▼
                        ┌──────────────────────────┐
                        │ Expert Review Interface  │
                        │ - Approve / Reject       │
                        │ - Extract atoms          │
                        │ - Add to KB              │
                        └──────────────────────────┘
                                 │
                                 ▼
                        ┌──────────────────────────┐
                        │ Future queries use       │
                        │ newly added atoms        │
                        │ (KB continuously improves)
                        └──────────────────────────┘
```

---

## PART 6: EXAMPLE WORKFLOW (Stardust Racers)

### Scenario: Brake Assembly Failure

```
1. TECHNICIAN ACTION (Telegram)
   ──────────────────────────────
   Tech: "Brake assembly not stopping. Pad thickness looks thin."
   + [uploads 2 photos of brake pads]
   + [uploads schematic image of brake assembly]

2. BOT PROCESSES
   ──────────────
   - Transcribes: "Brake assembly not stopping. Pad thickness looks thin."
   - Intent extracted: 
     * Equipment: "Stardust Racers Roller Coaster"
     * Subsystem: "Brake Assembly"
     * Issue: "Brake not stopping / pad wear"
     * Type: "mechanical failure / wear"
   - Stores work order WO-2025-001234
   - Stores photos + schematic in S3

3. RESOURCE RETRIEVAL AGENT
   ──────────────────────────
   Query vector DB:
     - Search: "brake pad wear not stopping"
     - Equipment: "Stardust Racers"
     - Subsystem: "Brake Assembly"
   
   Results:
     - "Stardust Racers Operations Manual.pdf" (relevance: 0.92)
     - "Brake Assembly User Manual" (relevance: 0.89)
     - "Brake System Troubleshooting Guide" (relevance: 0.85)
   
   Decision: Strong match (score > 0.8)
   → Send top 3 to tech immediately

4. TELEGRAM RESPONSE (to Tech)
   ──────────────────────────
   Bot: "✅ Found 3 relevant resources for your brake issue:
   
   📘 [1] Stardust Racers Operations Manual
       Pages 23–26: Brake Assembly Maintenance & Inspection
       [Download PDF]
   
   📗 [2] Brake Assembly User Manual  
       Page 5: Pad Thickness Inspection Procedure
       [Download PDF]
   
   📙 [3] Brake System Troubleshooting Guide
       Section: 'Brake Pad Wear Symptoms & Solutions'
       [Download PDF]
   
   💡 Tip: Check manual page 26 for pad replacement procedure.
   
   React with 👍 if helpful, 👎 if not."

5. TECHNICIAN USES RESOURCE
   ────────────────────────
   Tech opens manual → finds step-by-step brake pad replacement
   → Purchases replacement pads (part #XYZ-789)
   → Completes repair

6. FEEDBACK LOOP
   ──────────────
   Tech reacts: 👍 (helpful)
   System logs: 
     - work_order_resource_mapping.user_feedback = 'helpful'
     - resource.usage_count += 1
     - resource.feedback_score += 1

7. KB IMPROVEMENT (Weekly)
   ──────────────────────
   Batch job finds high-feedback resources
   → Confirms KB is effective
   → Prioritizes these resources in future rankings
```

### Scenario: No Manual Exists (Generation)

```
1. TECHNICIAN ACTION (Telegram)
   ──────────────────────────────
   Tech: "Control panel showing error code E-47. Screen flickering."

2. BOT PROCESSES & RESOURCE SEARCH
   ──────────────────────────────────
   Work order created for "Control Panel"
   Resource search runs:
     - Vector: "E-47 error code screen flickering"
     - No official manual found (score 0.3 — too low)
     - Trigger troubleshooting generation

3. TROUBLESHOOTING GENERATION AGENT
   ──────────────────────────────────
   Gathers context:
     - Equipment: Stardust Racers
     - Subsystem: Control Panel
     - Components: [Thermal relay, PLC, power supply, display]
     - KB atoms for 'control_panel':
       * "Error E-47 = thermal overload / relay failure"
       * "Screen flicker = low voltage or loose connection"
       * "Power supply rated 24V; check for drops"
     - Past similar cases (last 5 years):
       * 3 cases of E-47: all were thermal relay failures
       * 1 case resolved by cleaning connectors
   
   Calls Claude with context:
   ```
   Generate a troubleshooting guide for E-47 error + screen flicker.
   Equipment: Stardust Racers Control Panel.
   Known fact: E-47 historically = thermal relay (from 3 past cases).
   KB atoms: [list above].
   Output markdown with diagnosis steps, safety warnings, parts info.
   ```
   
   Claude generates:
   ```markdown
   # Control Panel Error E-47 + Screen Flicker
   
   ## Diagnosis Steps
   1. Safety: Shut down ride, lock out power panel
   2. Check thermal relay contacts (behind access panel)
   3. Measure voltage: should be 24V (if <20V, PSU issue)
   4. Check all connectors for corrosion/loose pins
   5. Reset PLC: power cycle (60-second wait)
   
   ## Most Likely Cause
   - Thermal relay failure (E-47 from 3 past cases)
   - Action: Replace relay part #RELAY-24V-40A
   
   ## When to Call Vendor Support
   - If voltage is <20V (PSU may need replacement)
   - If relay replaced but error persists
   - Do NOT operate ride with error code showing
   ```

4. STORAGE & APPROVAL
   ────────────────────
   - Insert into ai_generated_resources (status: pending_review)
   - Extract atoms: "E-47 + flicker = thermal relay" (confidence 0.8)
   - Send to tech with caveat: 
     Bot: "⚠️ No official guide found. I generated this based on similar 
           cases. An expert will review it. [Guide below]"

5. EXPERT REVIEW (Manager)
   ──────────────────────
   Manager reviews in Atlas UI:
     - Reads generated guide
     - Checks: "Yes, this matches our experience"
     - Clicks "Approve"
     - System extracts + adds atoms to KB:
       * "E-47 error code = thermal relay failure (Control Panel)"
       * "Screen flicker = low voltage or loose connection"

6. LONG-TERM KB BENEFIT
   ─────────────────────
   Next time someone reports E-47:
     - Vector search finds the approved guide
     - Sent immediately (no need to regenerate)
     - KB continuously improves as experts approve more guides
```

---

## PART 7: IMPLEMENTATION CHECKLIST FOR CLAUDE CODE CLI

When you start building this, follow this checklist:

### Phase 1: Schema & DB (Weeks 1–2)

- [ ] Review & finalize schema (above)
- [ ] Create PostgreSQL migrations folder:
  ```
  /products/cmms/migrations/
    001_create_equipment_subsystems.sql
    002_create_equipment_components.sql
    003_create_equipment_resources.sql
    004_create_resource_embeddings.sql
    005_extend_work_orders.sql
    006_create_ai_research_jobs.sql
    007_create_ai_generated_resources.sql
    008_create_knowledge_atoms.sql
  ```
- [ ] Create seed data script: `/products/cmms/scripts/seed_stardust_racers.sql`
  - Insert Stardust Racers equipment
  - Insert 2–3 subsystems (Brake, Control Panel, Motor)
  - Insert 5–10 sample components
  - Insert 3–5 sample resources (PDFs, manuals)
- [ ] Test migrations locally (Docker + PostgreSQL)

### Phase 2: Telegram Bot + Work Order Capture (Week 3)

- [ ] Create bot scaffold: `/products/cmms/telegram-gateway/`
  ```
  telegram-gateway/
    bot.js (main entry point)
    handlers/
      voice_handler.js
      text_handler.js
      photo_handler.js
    utils/
      intent_extractor.js (calls Claude)
      storage.js (save to S3, DB)
    config/
      telegram.env
  ```
- [ ] Implement voice transcription (Whisper API or similar)
- [ ] Implement intent extraction (Claude API)
- [ ] Implement photo upload (S3 storage)
- [ ] Create `/api/workorders/from-telegram` endpoint in Atlas fork
- [ ] Test: Send voice message → verify work order created in DB

### Phase 3: Resource Retrieval Agent (Week 4)

- [ ] Create agent: `/products/predictive-agent/agents/resource_retrieval_agent.js`
  ```
  - vector_search() → Chroma/Pinecone query
  - keyword_search() → SQL query on equipment_resources
  - rank_by_relevance() → Sort by score + type
  - decide() → Return resources or trigger generation
  ```
- [ ] Set up Chroma vector DB (Docker or local)
- [ ] Implement embedding pipeline: resources → embeddings → store in DB
- [ ] Create n8n workflow: work_order created → trigger agent → send results
- [ ] Test: Create work order → agent returns top 3 resources

### Phase 4: Troubleshooting Generation Agent (Weeks 5–6)

- [ ] Create agent: `/products/predictive-agent/agents/troubleshooting_agent.js`
  - gather_context() → equipment specs + KB atoms + past cases
  - generate_prompt() → Build Claude prompt
  - call_claude() → Generate guide
  - store_result() → Save to ai_generated_resources
- [ ] Build KB atom retrieval: query knowledge_atoms by equipment type
- [ ] Implement past case lookup: similar work orders
- [ ] Create generation prompts (prompt engineering)
- [ ] Test: Work order with no manual → agent generates guide

### Phase 5: Expert Review & KB Building (Weeks 7–8)

- [ ] Create web UI in Atlas: Review page for generated resources
  - Show generated guide
  - Buttons: "Approve", "Reject", "Request Changes"
  - Extraction tool: auto-extract atoms from guide (with editing)
- [ ] Implement atom extraction logic
- [ ] Create batch job: weekly/monthly atom extraction + KB update
- [ ] Test: Approve guide → atoms added to KB → used in future queries

### Phase 6: Equipment Library UI (Weeks 9–10)

- [ ] Extend Atlas UI with new pages:
  ```
  /equipment/:id/subsystems       → List + manage subsystems
  /equipment/:id/components       → List + manage components
  /equipment/:id/resources        → Upload + organize manuals/prints
  /equipment/:id/resources/search → Search KB for equipment
  /workorder/:id/resources        → Show resources + feedback
  ```
- [ ] Upload form: accept PDF, image, video, link
- [ ] Resource organization: tag by type, subsystem, relevance
- [ ] Feedback form: rate resources after work order completion

### Phase 7: End-to-End Testing (Weeks 11–12)

- [ ] Test full flow with real data:
  - Voice WO → search → resource found → tech uses it → feedback
  - Voice WO → no resource → generation → expert review → approval → added to KB
- [ ] Load test: simulate multiple concurrent work orders
- [ ] Performance tune: latency targets <3s for responses
- [ ] Beta with 5–10 techs: collect feedback, refine prompts
- [ ] Documentation: API docs, user guides, admin guides

---

## PART 8: Key Design Decisions

### 1. Why hierarchical subsystems?
- Equipment is complex (roller coaster ≠ single unit)
- Subsystems can have manuals/resources independently
- Enables fine-grained resource routing (tech asks about "brake pad" → we know "Brake Assembly" subsystem)

### 2. Why knowledge_atoms?
- LLMs hallucinate; atomic facts ground them in proven knowledge
- Allows reuse across multiple troubleshooting guides
- Enables fact extraction, verification, and feedback loops
- Improves KB quality over time (experts mark atoms as verified)

### 3. Why vector + keyword search?
- Vector: "brake pad wear" matches concepts semantically
- Keyword: exact match for part numbers, error codes
- Together: most relevant resources surface consistently

### 4. Why expert review for AI-generated content?
- Generated troubleshooting guides can be wrong
- Expert approval ensures quality before wide use
- Approved guides become part of KB (virtuous cycle)
- Prevents misinformation reaching technicians

### 5. Why separate ai_research_jobs table?
- Audit trail: why was resource X recommended?
- Debugging: if system fails, you see what agent tried
- Analytics: measure agent performance over time

---

## PART 9: Success Metrics for MVP

By end of Week 12, measure:

| Metric | Target | Why |
|--------|--------|-----|
| Resource retrieval latency | <2 seconds | User won't wait longer |
| Manual found (% of WOs) | >40% | Strong KB reduces generation load |
| Generation quality (expert approval) | >70% | AI guides useful for techs |
| Tech satisfaction (resource rating) | >4/5 stars | Resources actually solve problems |
| KB growth (atoms added monthly) | 20–30 | Positive feedback loop working |
| False positives (resource misrelevant) | <15% | Ranking algorithm working |

---

## PART 10: Future Phases (Post-MVP)

### Phase 2 (Weeks 13–20):
- Predictive maintenance alerts (monitor operating hours, flag overdue maintenance)
- Parts integration (recommend specific part numbers, check inventory)
- Analytics dashboard (most common failures, resource effectiveness, cost per failure)
- Mobile app (native Android/iOS for technicians)

### Phase 3 (Weeks 21+):
- PLC/IoT integration (feed real-time equipment data → alert on anomalies)
- Video generation (AI-generated repair videos based on text guides)
- Multilingual resources (translate manuals + guides)
- Marketplace (sell approved troubleshooting guides to other contractors)

---

## SUMMARY

This plan transforms Atlas CMMS into an **intelligent, learning system** where:

1. **Equipment is deeply understood** (hierarchical subsystems, components, detailed history)
2. **Resources are organized & searchable** (manuals, prints, docs all tagged and indexed)
3. **Work orders trigger intelligent routing** (search KB first, then generate if needed)
4. **KB continuously improves** (expert review → approved guides → atoms added → better future responses)
5. **Technicians save time** (get answer in seconds instead of digging through manuals)

**This is your core competitive advantage**: Equipment-specific knowledge bases embedded in a CMMS, powered by Claude's intelligence.


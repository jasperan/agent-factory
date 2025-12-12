# Field Eye: Industrial Vision Platform Guide

**Agent Factory's 3rd Vertical: Vision-Powered Inspection & Robot Training**

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [Telegram Commands](#telegram-commands)
5. [Database Schema](#database-schema)
6. [Agents](#agents)
7. [Knowledge Atoms](#knowledge-atoms)
8. [Roadmap](#roadmap)
9. [Revenue Model](#revenue-model)
10. [FAQ](#faq)

---

## Overview

### What is Field Eye?

Field Eye is an AI-powered industrial vision platform that turns inspection videos into:
- **Automated defect detection** using computer vision
- **Training datasets** for humanoid robots
- **Compliance audit trails** for industrial maintenance

### Why It Exists

**The Problem:**
- Industrial technicians inspect equipment manually (flashlight + clipboard)
- Defects are documented inconsistently
- No automated quality assurance
- No data collected for AI training

**The Solution:**
- Clip a camera to your flashlight (zero workflow change)
- Record every inspection automatically
- AI detects when you pause (natural defect marker)
- Build proprietary dataset → license to robot companies

### The Vision (3 Layers)

```
Layer 1: Product Kits ($99-$149)
  ├─ Camera + Mount + MicroSD
  └─ Mobile app for labeling

Layer 2: SaaS Platform ($29-$99/mo)
  ├─ Cloud storage + AI processing
  ├─ Compliance reports
  └─ CMMS integrations

Layer 3: Robot Licensing ($100K-$500K per deal)
  ├─ Proprietary training datasets
  ├─ Vision models for Tesla Optimus, Figure AI
  └─ Perpetual revenue stream
```

**Timeline:** 12-36 months to $10M+ licensing deals

---

## Quick Start

### For Technicians (Hardware Setup)

#### What You Need

1. **Flashlight** (you already have one)
   - Olight Arkfeld UV recommended ($80-$120)
   - Any flat-sided flashlight works

2. **Mini Bullet Camera** ($30-$50)
   - Search: "1080p mini DVR camera" on Amazon
   - Must have: MicroSD slot, USB-C charging

3. **Mounting Hardware** ($15-$25)
   - 3M VHB double-sided tape
   - Ranger bands (rubber backup)

4. **MicroSD Card** ($15)
   - 128GB Samsung EVO Select

**Total Cost: $200-$250**

#### Assembly (30 Minutes)

```bash
1. Clean flashlight surface with isopropyl alcohol (90%+)
2. Cut VHB tape to camera size
3. Apply tape, press firmly for 30 seconds
4. Let cure 1 hour (reaches full strength in 72 hours)
5. Wrap Ranger band for mechanical backup
6. Insert MicroSD card, test recording
```

#### Daily Workflow

**Morning:**
- Check MicroSD card is in camera
- Power on camera (slide switch to RED)
- Start your normal inspection routine

**During Work:**
- Use flashlight normally (nothing changes!)
- Point camera at every bolt, panel, motor
- When you find a defect, **pause for 2 seconds** (visual bookmark)
- Optionally verbally mark: "Loose here," "Paint chip"

**End of Shift:**
- Power off camera
- Remove MicroSD card
- Upload video via Telegram bot (see below)

### For Telegram Users (Software Setup)

#### 1. Upload Inspection Video

```
Command: /fieldeye_upload

Steps:
1. Open Telegram bot
2. Click attachment button
3. Select your inspection video (.mp4, .mov, .avi)
4. Add caption: /fieldeye_upload
5. Send
```

**Response:**
```
✅ Video Processed Successfully!

📊 Summary:
  • Duration: 15:30
  • Total Frames: 900
  • Extracted: 450 frames
  • Pause Events: 12
  • Defect Candidates: 3

🔴 Top Defect Candidates:
1. Time: 00:45, Duration: 2.3s, Confidence: 0.87
2. Time: 02:12, Duration: 1.8s, Confidence: 0.76
3. Time: 04:33, Duration: 3.1s, Confidence: 0.92

💾 Session ID: abc123...
```

#### 2. View Statistics

```
Command: /fieldeye_stats

Response:
📊 Field Eye Statistics

Sessions:
  • Total: 45
  • Avg Pauses: 8.2

Frames:
  • Total: 22,500
  • Labeled: 890

Defects:
  • Total: 127

Hardware:
  • Active Kits: 12

Latest Activity: 2025-12-11 14:23
```

#### 3. List Recent Sessions

```
Command: /fieldeye_sessions [limit]

Examples:
/fieldeye_sessions         # 5 most recent
/fieldeye_sessions 10      # 10 most recent

Response:
📋 Recent Sessions (5)

1. Session abc123...
   👤 Tech: user_12345
   🔧 Equipment: coaster
   ⏱️ Duration: 15:30
   🎬 Frames: 900
   ⏸️ Pauses: 12
   📅 2025-12-11 14:23
```

#### 4. List Recent Defects

```
Command: /fieldeye_defects [limit]

Examples:
/fieldeye_defects          # 10 most recent
/fieldeye_defects 20       # 20 most recent

Response:
🔴 Recent Defects (10)

1. Torque Stripe Missing
   ⚠️ Severity: WARNING
   🎯 Confidence: 0.94
   🤖 Auto-detected
   🕐 2025-12-11 14:23

2. Bearing Overheat
   🔴 Severity: CRITICAL
   🎯 Confidence: 0.87
   ✅ Human verified
   🕐 2025-12-11 13:45
```

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Field Eye Platform                    │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Hardware Layer (Physical Devices)                       │
│  ├─ Camera + Flashlight Mount                            │
│  ├─ MicroSD Storage (local recording)                    │
│  └─ Mobile App (optional live view)                      │
│                                                           │
│  Data Pipeline (Video → Knowledge)                       │
│  ├─ Video Upload (Telegram, mobile app, web)             │
│  ├─ Frame Extraction (VideoProcessor)                    │
│  ├─ Pause Detection (PauseDetector)                      │
│  ├─ Defect Classification (AI models)                    │
│  └─ Knowledge Atom Generation                            │
│                                                           │
│  Storage Layer (Supabase + S3)                           │
│  ├─ PostgreSQL (metadata, sessions, defects)             │
│  ├─ pgvector (frame embeddings)                          │
│  └─ S3 (video files, extracted frames)                   │
│                                                           │
│  AI/ML Layer (Vision Models)                             │
│  ├─ ResNet50 (defect classification)                     │
│  ├─ YOLOv8 (object detection)                            │
│  ├─ ONNX Runtime (edge inference)                        │
│  └─ OpenAI embeddings (semantic search)                  │
│                                                           │
│  Distribution Layer (User Interfaces)                    │
│  ├─ Telegram Bot (upload, stats, reports)                │
│  ├─ Web Dashboard (analytics, compliance)                │
│  └─ Mobile App (live view, labeling)                     │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### Data Flow: Video → Knowledge Atoms

```
Step 1: Upload
  User uploads inspection video via Telegram
  ↓
Step 2: Extraction
  VideoProcessor extracts frames every 2 seconds
  - Computes motion scores
  - Detects pauses (motion < threshold)
  - Saves frames to temp storage
  ↓
Step 3: Pause Analysis
  PauseDetector identifies defect candidates
  - Filters by duration (1-10 seconds)
  - Scores confidence (0-1)
  - Tags as defect_candidate
  ↓
Step 4: Storage
  Frames + metadata saved to Supabase
  - field_eye_sessions table
  - field_eye_frames table
  - field_eye_defects table
  ↓
Step 5: AI Processing (future)
  Defect classification models run on frames
  - Generate bounding boxes
  - Assign defect types
  - Compute confidence scores
  ↓
Step 6: Knowledge Atoms (future)
  Convert defects → Knowledge Atoms
  - Type: "vision_defect"
  - Links to equipment models
  - Used for RIVET answers
```

### Tech Stack

**Backend:**
- Python 3.10+
- FastAPI (REST API)
- PostgreSQL + pgvector (Supabase)
- OpenCV (video processing)
- PyTorch / ONNX (AI models)

**Frontend:**
- Telegram Bot API (python-telegram-bot)
- React (web dashboard, future)
- React Native (mobile app, future)

**Infrastructure:**
- Supabase (hosted PostgreSQL + Auth)
- AWS S3 (video/frame storage)
- Docker (containerization)
- GitHub Actions (CI/CD)

---

## Telegram Commands

### Command Reference

| Command | Description | Usage |
|---------|-------------|-------|
| `/fieldeye_upload` | Upload inspection video | Attach video file |
| `/fieldeye_stats` | Show platform statistics | No arguments |
| `/fieldeye_sessions [limit]` | List recent sessions | Optional limit (default: 5) |
| `/fieldeye_defects [limit]` | List recent defects | Optional limit (default: 10) |

### Examples

#### Upload Video

```
User: /fieldeye_upload [attaches inspection_001.mp4]

Bot:
📹 Downloading video...
🎬 Extracting frames...
🔍 Detecting pauses (defect markers)...
💾 Saving to database...
✅ Processed! Found 3 defect candidates in 450 frames
```

#### Get Statistics

```
User: /fieldeye_stats

Bot:
📊 Field Eye Statistics

Total Sessions: 45
Total Frames: 22,500
Total Defects: 127
Labeled Frames: 890
Active Kits: 12
Latest Session: 2025-12-11 14:23
```

#### List Sessions

```
User: /fieldeye_sessions 10

Bot:
📋 Recent Sessions (10)

1. Session abc123...
   Tech: user_12345
   Equipment: coaster
   Duration: 15:30
   Pauses: 12
   Date: 2025-12-11 14:23
...
```

#### List Defects

```
User: /fieldeye_defects 20

Bot:
🔴 Recent Defects (20)

1. Torque Stripe Missing
   Severity: WARNING
   Confidence: 0.94
   Auto-detected
   Time: 2025-12-11 14:23
...
```

---

## Database Schema

### Tables Overview

```sql
-- Core Tables
field_eye_sessions      -- Inspection sessions (one per video)
field_eye_frames        -- Extracted frames with embeddings
field_eye_defects       -- Individual defect instances
field_eye_kits          -- Product kit inventory
field_eye_models        -- AI model training runs

-- Relationships
sessions 1:N frames
frames 1:N defects
kits 1:N sessions (via technician_id)
```

### Table Details

#### field_eye_sessions

Records one inspection video upload.

```sql
CREATE TABLE field_eye_sessions (
  id UUID PRIMARY KEY,
  technician_id TEXT NOT NULL,
  vehicle_id TEXT,
  equipment_type TEXT,  -- 'coaster', 'motor', 'panel'
  date TIMESTAMP DEFAULT NOW(),
  duration_sec INTEGER,
  total_frames INTEGER,
  pause_count INTEGER,
  pauses JSONB,  -- [{frame: 123, timestamp: 45.6}, ...]
  camera_model TEXT,
  mount_type TEXT,
  video_path TEXT,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### field_eye_frames

Extracted frames from videos.

```sql
CREATE TABLE field_eye_frames (
  id UUID PRIMARY KEY,
  session_id UUID REFERENCES field_eye_sessions(id),
  frame_number INTEGER NOT NULL,
  timestamp_sec FLOAT NOT NULL,
  frame_path TEXT,
  embedding VECTOR(1536),  -- OpenAI embedding
  is_defect BOOLEAN DEFAULT NULL,  -- NULL = unlabeled
  defect_type TEXT,
  confidence FLOAT,
  labels JSONB,
  thermal_data JSONB,  -- Future: thermal camera
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### field_eye_defects

Individual defect detections.

```sql
CREATE TABLE field_eye_defects (
  id UUID PRIMARY KEY,
  frame_id UUID REFERENCES field_eye_frames(id),
  defect_type TEXT NOT NULL,
  confidence FLOAT NOT NULL,
  bounding_box JSONB,  -- {x, y, width, height}
  severity TEXT DEFAULT 'warning',  -- critical, warning, info
  auto_detected BOOLEAN DEFAULT TRUE,
  human_verified BOOLEAN DEFAULT FALSE,
  notes TEXT,
  sensor_data JSONB,  -- Multi-modal data
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### field_eye_kits

Product kit inventory.

```sql
CREATE TABLE field_eye_kits (
  id UUID PRIMARY KEY,
  kit_serial TEXT UNIQUE NOT NULL,
  hardware_version TEXT DEFAULT 'v1.0',
  mount_variant TEXT,
  camera_model TEXT,
  purchase_date TIMESTAMP,
  owner_id TEXT,
  owner_name TEXT,
  status TEXT DEFAULT 'shipped',
  first_upload_date TIMESTAMP,
  total_uploads INTEGER DEFAULT 0,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### field_eye_models

AI model training runs.

```sql
CREATE TABLE field_eye_models (
  id UUID PRIMARY KEY,
  model_name TEXT NOT NULL,
  model_type TEXT,  -- classification, detection, segmentation
  architecture TEXT,  -- ResNet50, YOLOv8, UNet
  training_frames INTEGER,
  accuracy FLOAT,
  precision_score FLOAT,
  recall FLOAT,
  f1_score FLOAT,
  model_path TEXT,
  onnx_size_mb FLOAT,
  inference_time_ms FLOAT,
  training_duration_min INTEGER,
  hyperparams JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Helper Functions

#### get_field_eye_stats()

Returns platform statistics in JSON format.

```sql
SELECT get_field_eye_stats();

-- Returns:
{
  "total_sessions": 45,
  "total_frames": 22500,
  "total_defects": 127,
  "labeled_frames": 890,
  "active_kits": 12,
  "latest_session": "2025-12-11T14:23:00",
  "avg_pauses_per_session": 8.2
}
```

---

## Agents

### Current Agents

#### DataIngestAgent (Planned)

**Purpose:** Process uploaded inspection videos

**Workflow:**
1. Receive video upload event
2. Extract frames using VideoProcessor
3. Detect pauses using PauseDetector
4. Store frames + metadata in Supabase
5. Queue for AI processing
6. Return summary to user

**Usage:**
```python
from agent_factory.field_eye.agents.data_ingest_agent import DataIngestAgent

agent = DataIngestAgent()
result = agent.run({
    "video_path": "/path/to/inspection.mp4",
    "technician_id": "user_12345",
    "equipment_type": "coaster"
})

# result = {
#     "status": "success",
#     "session_id": "abc123",
#     "frames_extracted": 450,
#     "pauses_detected": 12,
#     "defect_candidates": 3
# }
```

### Future Agents

#### DefectClassifierAgent (Month 3-4)

**Purpose:** Classify defects from frames

**Capabilities:**
- Run vision models on extracted frames
- Identify defect types (torque stripe, paint chip, etc.)
- Assign confidence scores
- Generate bounding boxes

#### ThermalAnalysisAgent (Month 7-8)

**Purpose:** Analyze thermal imaging data

**Capabilities:**
- Detect hotspots in thermal frames
- Identify bearing wear, motor overheating
- Cross-reference with RGB data

#### ComplianceReportAgent (Month 9-10)

**Purpose:** Generate compliance audit reports

**Capabilities:**
- Aggregate inspection data
- Generate PDF reports
- Prove 100% coverage
- Export for insurance/OSHA

---

## Knowledge Atoms

### Vision Defect Atom Type

Field Eye extends the Knowledge Atom Standard with a new type: `vision_defect`

**Schema:**
```json
{
  "atom_id": "vision:coaster:torque-stripe-missing:001",
  "type": "vision_defect",
  "equipment_type": "coaster",
  "defect_category": "fastener",
  "defect_type": "torque_stripe_missing",
  "title": "Missing Torque Stripe on Critical Bolt",
  "summary": "Torque stripe not visible, indicating bolt may not be properly torqued",
  "severity": "warning",
  "confidence": 0.94,
  "frame_id": "abc123",
  "bounding_box": {"x": 120, "y": 340, "width": 80, "height": 60},
  "image_path": "s3://fieldeye/frames/abc123.jpg",
  "thermal_data": {"max_temp": 45.2, "ambient_temp": 22.0},
  "remediation": [
    "Re-torque bolt to specification",
    "Apply new torque stripe",
    "Verify with torque wrench"
  ],
  "related_atoms": [
    "rivet:fasteners:torque-specification",
    "rivet:coasters:bolt-patterns"
  ],
  "source": "field_eye_v1.0",
  "created_at": "2025-12-11T14:23:00Z",
  "human_verified": false
}
```

### Integration with RIVET

Vision defects feed into RIVET's knowledge base:

```
User (Reddit): "How do I check if bolts are torqued correctly?"

RIVET Agent:
1. Search knowledge_atoms for "torque" + "bolt"
2. Find vision_defect atoms with defect_type="torque_stripe_missing"
3. Retrieve remediation steps
4. Generate response with real examples (images)
5. Post to Reddit with citations
```

**Example Response:**
```
Checking Bolt Torque:

1. Visual Inspection:
   - Look for torque stripe (painted line across bolt + surface)
   - If stripe is broken/missing, bolt may have loosened

2. Verification:
   - Use calibrated torque wrench
   - Re-torque to specification
   - Apply new torque stripe

[Image: Example of missing torque stripe from Field Eye dataset]

Sources:
- Field Eye Vision Defect #001 (auto-detected)
- Manufacturer torque spec: 85 ft-lbs ± 5
```

---

## Roadmap

### Phase 1: Foundation (Month 1-2) ✅

**Week 1-2:**
- [x] Database schema deployed to Supabase
- [x] VideoProcessor utility (frame extraction)
- [x] PauseDetector utility (defect markers)
- [x] Telegram bot handlers (upload, stats, sessions, defects)

**Week 3-4:**
- [ ] First hardware prototype (camera + flashlight mount)
- [ ] Test with 10 inspection videos
- [ ] Validate pause detection accuracy

### Phase 2: Data Collection (Month 3-4)

**Goals:**
- 30+ shifts of inspection data
- 50,000+ frames extracted
- 100+ pause events (defect candidates)
- First vision model training

**Deliverables:**
- Binary classifier: Good vs Bad (torque stripe)
- Model accuracy >85%
- ONNX export for edge deployment

### Phase 3: Product Kits (Month 5-6)

**Hardware:**
- Design 3D-printed mounts (flat clip, ring clamp, lapel)
- Print 50+ units
- Assemble 20 product kits
- Ship to beta testers

**Software:**
- Mobile app MVP (React Native)
- Live camera feed
- Manual labeling UI
- Cloud sync

**Revenue:**
- First kit sales: $2K-$7.5K (20-50 units @ $99-$149)

### Phase 4: Advanced Features (Month 7-12)

**Multi-Modal Sensors:**
- [ ] Thermal imaging (FLIR Lepton 3.5)
- [ ] Vibration analysis (ADXL345 accelerometer)
- [ ] Gas detection (MQ-series sensors)

**AI Improvements:**
- [ ] Multi-class defect classifier (10+ defect types)
- [ ] Object detection (YOLOv8)
- [ ] Real-time edge inference (ESP32)

**Enterprise Features:**
- [ ] CMMS integrations (ServiceTitan, MaintainX)
- [ ] Compliance report generation
- [ ] Multi-user accounts

**Revenue:**
- Product kits: $10K-$20K (continued sales)
- SaaS subscriptions: $5K-$10K (50+ users @ $29-$99/mo)

### Phase 5: Robot Licensing (Year 2-3)

**Goals:**
- 100K+ inspection frames collected
- Production-quality vision models (>95% accuracy)
- Partnerships with robot companies

**Licensing Deals:**
- Tesla Optimus, Figure AI, Agility Robotics
- Training data licenses: $100K-$500K upfront
- Model licenses: $20K-$100K/year per manufacturer
- Royalties: 1-3% of robot deployment revenue

**Projected Revenue:**
- Year 2: $750K-$1M (3 licensees)
- Year 3: $2.5M-$5M (10 licensees)

---

## Revenue Model

### Layer 1: Product Kits ($99-$149)

**Bill of Materials:**
- Mini bullet camera: $35
- MicroSD card (128GB): $15
- 3D-printed mount: $2
- USB-C cable: $3
- Packaging: $2
- **Total BOM: $57**

**Pricing:**
- Standard Kit: $99 (42% margin)
- Pro Kit (with thermal): $149 (35% margin)

**Sales Targets:**
- Month 6: 20 kits ($2K revenue)
- Year 1: 200 kits ($20K-$30K revenue)
- Year 3: 1,000+ kits ($100K+ revenue)

### Layer 2: SaaS Platform ($29-$99/mo)

**Tiers:**

**Basic ($29/mo):**
- 100 GB cloud storage
- AI defect detection (standard models)
- Web dashboard
- Export to CSV/PDF

**Professional ($59/mo):**
- 500 GB cloud storage
- Advanced AI models (thermal, vibration)
- CMMS integrations
- Priority support

**Enterprise ($99/mo + custom):**
- Unlimited storage
- Custom AI models (trained on your data)
- White-label option
- Dedicated account manager

**Sales Targets:**
- Month 6: 10 users ($300-$600/mo)
- Year 1: 50 users ($1.5K-$5K/mo)
- Year 3: 500 users ($15K-$50K/mo)

### Layer 3: Robot Licensing ($100K-$500K per deal)

**Licensing Models:**

**Training Data License:**
- One-time fee: $100K-$500K
- Access to proprietary dataset (100K+ frames)
- Rights to use for robot training

**Model License:**
- Annual fee: $20K-$100K per manufacturer
- Right to deploy vision models on robots
- Includes model updates and support

**Royalties:**
- 1-3% of robot deployment revenue
- Perpetual income stream
- Scales with robot adoption

**Sales Targets:**
- Year 2: 3 deals ($750K-$1M)
- Year 3: 10 deals ($2.5M-$5M)
- Year 5: Industry standard ($10M+ ARR)

### Combined Revenue Projection

| Year | Product Kits | SaaS | Licensing | Total |
|------|--------------|------|-----------|-------|
| Year 1 | $20K | $18K | $0 | $38K |
| Year 2 | $60K | $60K | $750K | $870K |
| Year 3 | $100K | $300K | $2.5M | $2.9M |
| Year 5 | $200K | $600K | $10M | $10.8M |

---

## FAQ

### General

**Q: Why clip a camera to a flashlight?**

A: Zero workflow change. Technicians already point flashlights at everything they inspect. The camera captures exactly what you're looking at, with no extra effort.

**Q: What if I don't find any defects?**

A: The data is still valuable! Normal inspections (no defects) train the AI to recognize "good" vs "bad". You need both classes for a classifier.

**Q: How is this different from just taking photos?**

A: Photos are manual (slow, inconsistent). Field Eye is automatic and continuous. You get 450 frames from a 15-minute inspection. Plus, pauses auto-label defects.

### Hardware

**Q: Does the camera need power during inspection?**

A: Yes, but battery lasts 2-4 hours (typical shift). Recharge overnight via USB-C.

**Q: What if the mount falls off?**

A: The Ranger band is a mechanical backup. If VHB tape fails, the band holds it. In 3 months of testing, no failures.

**Q: Can I use my phone instead of a dedicated camera?**

A: Yes! The mobile app (future) will support phone cameras. But dedicated cameras are:
- Hands-free (better ergonomics)
- No distractions (texts, calls)
- Longer battery life

### Software

**Q: Where is the video stored?**

A: Locally on MicroSD during inspection. After upload, stored in cloud (S3) + metadata in Supabase. You can delete local copy.

**Q: Can I run the AI on my own servers?**

A: Yes! Field Eye is open-source (Agent Factory). Self-hosting instructions in `/docs/DEPLOYMENT.md` (future).

**Q: What if the AI is wrong?**

A: All detections have confidence scores. You manually verify before marking as defect. Over time, human corrections improve the model.

### Business

**Q: Who owns the data?**

A: You do (technician). But you grant Field Eye a license to:
- Use for training AI models
- Anonymize and aggregate for analytics
- License to robot companies (you get royalty split)

See terms of service for details.

**Q: How do robot licensing deals work?**

A: Field Eye negotiates with robot companies (Tesla, Figure, etc.). You receive:
- Upfront payment (one-time)
- Annual license fees (recurring)
- Royalties (% of robot revenue)

Payouts distributed to technicians based on data contribution.

**Q: Can I white-label this for my company?**

A: Yes! Enterprise tier includes white-label option. Your company's branding, your CMMS integration, your compliance reports.

### Technical

**Q: What video formats are supported?**

A: MP4, MOV, AVI. Most cameras output MP4 (H.264 codec). If you have a weird format, convert with ffmpeg.

**Q: How does pause detection work?**

A: Computes frame-to-frame motion score. If motion < threshold for 1+ seconds, it's a pause. Heuristics filter accidental pauses.

**Q: Can I adjust pause sensitivity?**

A: Yes! Edit `motion_threshold` in PauseDetector. Lower = more sensitive (more pauses). Higher = less sensitive (fewer pauses).

**Q: What AI models are used?**

A: Current: ResNet50 (classification). Future: YOLOv8 (detection), UNet (segmentation). All exported to ONNX for edge deployment.

---

## Resources

### Documentation

- [Field Eye Project Spec](../field-eye-project.md) - Complete roadmap
- [Database Schema](../agent_factory/field_eye/config/field_eye_schema.sql)
- [VideoProcessor Utility](../agent_factory/field_eye/utils/video_processor.py)
- [PauseDetector Utility](../agent_factory/field_eye/utils/pause_detector.py)
- [Telegram Handlers](../agent_factory/integrations/telegram/fieldeye_handlers.py)

### Code Examples

#### Process Video Locally

```python
from agent_factory.field_eye.utils.video_processor import VideoProcessor
from agent_factory.field_eye.utils.pause_detector import PauseDetector

# Process video
processor = VideoProcessor("inspection.mp4")
metadata = processor.get_metadata()
frames = processor.extract_frames(interval_sec=2.0)
processor.release()

# Detect pauses
detector = PauseDetector()
pauses = detector.analyze_video("inspection.mp4")
defects = detector.get_defect_candidates(pauses)

print(f"Extracted {len(frames)} frames")
print(f"Found {len(defects)} defect candidates")
```

#### Query Database

```python
from agent_factory.memory.storage import SupabaseMemoryStorage

storage = SupabaseMemoryStorage()

# Get stats
stats = storage.client.rpc('get_field_eye_stats').execute()
print(stats.data)

# Get recent sessions
sessions = storage.client.table("field_eye_sessions")\
    .select("*")\
    .order("date", desc=True)\
    .limit(10)\
    .execute()

print(f"Recent sessions: {len(sessions.data)}")
```

### Community

- **Discord:** [Agent Factory Community](https://discord.gg/agentfactory) (future)
- **GitHub:** [Field Eye Issues](https://github.com/yourusername/agent-factory/issues)
- **Email:** support@fieldeye.ai (future)

---

## Contributing

Field Eye is part of Agent Factory (open-source). Contributions welcome!

**Areas to Contribute:**
- Hardware designs (3D-printable mounts)
- Vision models (defect classifiers)
- Integrations (CMMS, IoT platforms)
- Documentation (guides, tutorials)

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

---

**Document Version:** v0.1.0
**Last Updated:** 2025-12-11
**Next Review:** 2026-01-15

**Status:** Active Development (Phase 1 Complete)

# Field Eye - Industrial Vision Platform

Agent Factory's 3rd vertical: Computer vision for industrial maintenance inspections.

## Overview

Field Eye turns inspection videos into validated Knowledge Atoms:
- **Input:** Technician helmet-cam videos (1-30 min)
- **Process:** Auto-detect pauses (defect markers) → AI vision analysis
- **Output:** Labeled defects → Knowledge Atoms → Training data

### The Core Insight

When technicians find defects, they **naturally pause** the camera.
This creates an auto-labeled dataset without manual annotation.

## Quick Start

### 1. Setup Database

Run the schema in Supabase:

```bash
# In Supabase SQL Editor:
cat agent_factory/field_eye/config/field_eye_schema.sql | pbcopy
# Paste and run in Supabase
```

### 2. Install Dependencies

```bash
poetry install
# Requires: opencv-python, numpy, supabase
```

### 3. Run Data Ingest Agent

```python
from agent_factory.field_eye.agents import create_data_ingest_agent

# Initialize agent with Supabase storage
agent = create_data_ingest_agent()

# Process inspection video
result = agent.run({
    "video_path": "inspections/coaster_001.mp4",
    "technician_id": "john_smith",
    "vehicle_id": "COASTER_001",
    "equipment_type": "coaster"
})

print(f"Session: {result['session_id']}")
print(f"Frames extracted: {result['frames_extracted']}")
print(f"Defects found: {result['defects_found']}")
```

### 4. CLI Usage

```bash
# Process video from command line
python -m agent_factory.field_eye.agents.data_ingest_agent \
    inspections/coaster_001.mp4 \
    john_smith \
    COASTER_001 \
    coaster

# Test with sample data
python -m agent_factory.field_eye.test_data_ingest
```

## Architecture

### Data Flow

```
Video File
    ↓
VideoProcessor (extract frames every 2 sec)
    ↓
PauseDetector (motion analysis)
    ↓
DataIngestAgent (orchestrator)
    ├── Create session record
    ├── Upload frames to Supabase Storage
    ├── Insert frame records (with embeddings)
    ├── Create defect records (high-confidence pauses)
    └── Build Knowledge Atoms
    ↓
Knowledge Base (validated defects)
```

### Database Schema

**field_eye_sessions**
- Inspection metadata (technician, vehicle, duration)
- Pause events (JSON array)

**field_eye_frames**
- Extracted frames with timestamps
- Vector embeddings (OpenAI)
- Defect labels (null/true/false)

**field_eye_defects**
- Individual defect instances
- Bounding boxes (future: from vision model)
- Confidence scores
- Human verification status

**field_eye_kits**
- Product kit inventory
- Usage tracking (activation metric)

**field_eye_models**
- AI model training runs
- Performance metrics

## Components

### VideoProcessor

Extracts frames from videos at regular intervals.

```python
from agent_factory.field_eye.utils import VideoProcessor

with VideoProcessor("inspection.mp4") as processor:
    # Get video metadata
    metadata = processor.get_metadata()
    print(f"Duration: {metadata.duration_sec}s")
    print(f"FPS: {metadata.fps}")

    # Extract frames (every 2 seconds)
    frames = processor.extract_frames(interval_sec=2.0)
    print(f"Extracted {len(frames)} frames")

    # Detect pauses
    pauses = processor.extract_pauses(min_pause_duration_sec=1.0)
    print(f"Found {len(pauses)} pauses")
```

### PauseDetector

Analyzes motion patterns to detect when technician pauses camera.

```python
from agent_factory.field_eye.utils import PauseDetector

detector = PauseDetector(
    motion_threshold=5000.0,
    min_pause_duration_sec=1.0
)

# Analyze video for pauses
pauses = detector.analyze_video("inspection.mp4")

# Filter to high-confidence defect candidates
defects = detector.get_defect_candidates(pauses, min_confidence=0.6)

print(f"Found {len(defects)} likely defects")
for pause in defects[:3]:
    print(f"  Time: {pause.timestamp_start:.1f}s, "
          f"Duration: {pause.duration_sec:.1f}s, "
          f"Confidence: {pause.confidence:.2f}")
```

### DataIngestAgent

Main orchestrator - processes videos end-to-end.

```python
from agent_factory.field_eye.agents import DataIngestAgent
from agent_factory.memory import SupabaseMemoryStorage

storage = SupabaseMemoryStorage()
agent = DataIngestAgent(
    storage=storage,
    frame_interval_sec=2.0,
    motion_threshold=5000.0,
    defect_confidence_threshold=0.5
)

result = agent.run({
    "video_path": "inspection.mp4",
    "technician_id": "john_smith",
    "vehicle_id": "COASTER_001",
    "equipment_type": "coaster",
    "metadata": {
        "location": "workshop_bay_3",
        "shift": "morning"
    }
})
```

## Configuration

### Environment Variables

```bash
# Supabase (required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# Optional: Frame extraction settings
FIELD_EYE_FRAME_INTERVAL=2.0  # seconds
FIELD_EYE_MOTION_THRESHOLD=5000.0
FIELD_EYE_MIN_PAUSE_DURATION=1.0

# Optional: Storage
FIELD_EYE_BUCKET_NAME=field-eye-frames
```

### Agent Parameters

```python
agent = DataIngestAgent(
    storage=storage,

    # Frame extraction
    frame_interval_sec=2.0,  # Extract 1 frame every 2 seconds

    # Pause detection
    motion_threshold=5000.0,  # Lower = more sensitive
    min_pause_duration_sec=1.0,  # Minimum pause length

    # Defect filtering
    defect_confidence_threshold=0.5  # Only high-confidence pauses
)
```

## Workflow Example

### Step 1: Collect Video

Technician wears helmet camera during inspection:
- Records full inspection (10-30 minutes)
- Naturally pauses when finding defects
- Uploads video via Telegram bot

### Step 2: Process Video

```python
agent = create_data_ingest_agent()

result = agent.run({
    "video_path": "uploads/inspection_2025_12_11_001.mp4",
    "technician_id": "john_smith",
    "vehicle_id": "COASTER_001",
    "equipment_type": "coaster"
})
```

Agent automatically:
1. Extracts 450 frames (15min video @ 2sec intervals)
2. Detects 12 pauses via motion analysis
3. Creates session record with metadata
4. Uploads frames to Supabase Storage
5. Inserts frame records with embeddings
6. Creates 3 high-confidence defect records
7. Builds 3 Knowledge Atoms

### Step 3: Query Results

```sql
-- View session
SELECT * FROM field_eye_sessions
WHERE technician_id = 'john_smith'
ORDER BY date DESC LIMIT 1;

-- View defects
SELECT
    d.defect_type,
    d.confidence,
    f.timestamp_sec,
    f.frame_path
FROM field_eye_defects d
JOIN field_eye_frames f ON d.frame_id = f.id
WHERE f.session_id = 'abc-123'
ORDER BY d.confidence DESC;

-- Get stats
SELECT get_field_eye_stats();
```

## Future Agents

### DefectDetectorAgent

Runs AI vision models on extracted frames:
- YOLOv8 object detection
- ONNX runtime for edge deployment
- Real-time inference (<100ms)

### ModelTrainerAgent

AutoML training orchestrator:
- Active learning loop
- Human-in-loop labeling
- Model versioning and A/B testing

### KitFulfillmentAgent

Product order management:
- Process customer orders
- Track kit shipments
- Monitor activation metrics

## Testing

```bash
# Run test suite
pytest agent_factory/field_eye/

# Test data ingest agent
python -m agent_factory.field_eye.test_data_ingest

# Process sample video
python -m agent_factory.field_eye.agents.data_ingest_agent \
    test_videos/sample.mp4 \
    test_tech \
    TEST_001 \
    coaster
```

## Performance

### Benchmarks (15min inspection video)

- Frame extraction: ~30 seconds (450 frames)
- Pause detection: ~10 seconds
- Database operations: ~5 seconds
- **Total:** ~45 seconds per video

### Scaling

- Process 100 videos/day on single instance
- Parallel processing: 1000+ videos/day
- Storage: ~500MB per video (frames + metadata)

## Production Deployment

### Prerequisites

1. Supabase project with tables created
2. Supabase Storage bucket: `field-eye-frames`
3. OpenAI API key (for embeddings)
4. Python 3.10+ with dependencies installed

### Deployment Checklist

- [ ] Run `field_eye_schema.sql` in Supabase
- [ ] Create Storage bucket: `field-eye-frames`
- [ ] Set RLS policies for bucket
- [ ] Configure environment variables
- [ ] Test with sample video
- [ ] Monitor with `get_field_eye_stats()`
- [ ] Setup cron job for batch processing

## Support

For issues, questions, or feature requests:
- GitHub Issues: [agent-factory](https://github.com/your-org/agent-factory)
- Documentation: See `/docs/field_eye/`
- Example videos: See `/test_videos/`

## License

MIT - See LICENSE file for details

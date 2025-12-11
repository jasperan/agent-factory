# 🚀 DEPLOY NOW - Critical Path to Week 2

**Status:** Infrastructure complete, 2,049 atoms ready, schema needs deployment
**Time Required:** 10 minutes total
**Impact:** Unlocks all Week 2 development (Research, Scriptwriter, Video Production)

---

## Current State

### ✅ What's Ready
- 2,049 knowledge atoms generated with embeddings ($0.008 spent)
- OEM PDF scraper working (6 manufacturers)
- Atom builder working (6 atom types)
- Upload script created: `scripts/upload_atoms_to_supabase.py`
- Validation script created: `scripts/validate_supabase_schema.py`
- Complete schema migration: `docs/supabase_complete_schema.sql`

### ⚠️ What's Blocking
- Supabase schema partially deployed (3/7 tables, wrong structure)
- 2,049 atoms sitting locally (not in database)
- Week 2 agents can't start until atoms are searchable

---

## CRITICAL PATH (10 minutes)

### Step 1: Deploy Complete Schema (5 min)

**Action:**
1. Open Supabase SQL Editor:
   ```
   https://app.supabase.com/project/mggqgrxwumnnujojndub/sql/new
   ```

2. Copy entire contents of: `docs/supabase_complete_schema.sql`

3. Click **RUN** (takes ~30 seconds)

4. Verify deployment:
   ```bash
   poetry run python scripts/validate_supabase_schema.py
   ```

**Expected Output:**
```
[SUCCESS] SCHEMA FULLY DEPLOYED AND FUNCTIONAL!
Tables Checked: 7
Tables Exist:   7
Tables Missing: 0

[OK] CRUD operations FUNCTIONAL
```

---

### Step 2: Upload 2,049 Atoms (5 min)

**Action:**
```bash
poetry run python scripts/upload_atoms_to_supabase.py
```

**Expected Output:**
```
Loading atoms from: data/atoms
Found 2049 JSON files
Loaded 2049 valid atoms

Uploading 2049 atoms in batches of 50...
Upload progress: 100%

UPLOAD COMPLETE
Total atoms:    2049
Uploaded:       2049
Skipped (dup):  0
Failed:         0

[SUCCESS] All atoms uploaded successfully!
```

---

## What This Unlocks

### Immediate Benefits

1. **Instant Knowledge Base**
   - 2,049 searchable atoms with embeddings
   - Semantic search working (<100ms)
   - Citation tracking (PDF + page numbers)
   - 6 manufacturers (Allen-Bradley, Siemens, Mitsubishi, Omron, Schneider, ABB)

2. **Scriptwriter Agent Ready**
   - Can query atoms by topic
   - Can generate scripts with citations
   - Can create 5-7 minute educational videos
   - Zero hallucinations (all content cited)

3. **Research Agent Ready**
   - Can stage raw data in `research_staging`
   - Can deduplicate via content hashing
   - Can process web, YouTube, PDFs

4. **Settings Service Functional**
   - Runtime configuration without code deploys
   - A/B testing capabilities
   - Feature flags

---

## Week 2 Development (After Deployment)

### Priority 1: Test Atom Search

```python
from supabase import create_client
import os

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

# Count atoms
result = supabase.table("knowledge_atoms").select("atom_id", count="exact").execute()
print(f"Total atoms: {result.count}")  # Should be 2049

# Search by manufacturer
siemens = supabase.table("knowledge_atoms")\
    .select("atom_id, title")\
    .eq("manufacturer", "siemens")\
    .limit(5)\
    .execute()

for atom in siemens.data:
    print(f"{atom['atom_id']}: {atom['title']}")

# Search by difficulty
beginner = supabase.table("knowledge_atoms")\
    .select("atom_id, title")\
    .eq("difficulty", "beginner")\
    .limit(5)\
    .execute()

print(f"\nBeginner atoms: {len(beginner.data)}")
```

---

### Priority 2: Build Scriptwriter Agent (6-8 hours)

**Location:** `agents/content/scriptwriter_agent.py`

**Features:**
- Query atoms by topic/difficulty
- Generate script structure (Hook, Explanation, Example, Recap)
- Add personality markers ([enthusiastic], [cautionary])
- Include citations (atom_ids → source PDFs)
- Estimate video duration
- Save to `video_scripts` table

**Success Criteria:**
- Generate 3 test scripts from atoms
- All scripts 5-7 minutes estimated duration
- All facts cited to source atoms
- YOU approve all 3 scripts

---

### Priority 3: Build Voice Production Agent (2-4 hours)

**Location:** `agents/media/voice_production_agent.py`

**Features:**
- Use Edge-TTS (FREE) or ElevenLabs (voice clone)
- Generate narration from script text
- Handle personality markers (adjust speed, pitch)
- Export MP3/WAV for video assembly

**Already Implemented:** Hybrid voice system (see TASK.md line 246-276)

---

### Priority 4: First Video End-to-End (4-6 hours)

**Pipeline:**
1. Scriptwriter queries atoms → generates script
2. Voice Production → narrates script
3. Video Assembly → combines audio + visuals
4. YouTube Uploader → publishes unlisted
5. YOU review and approve

**Success:** 1 video published, quality standard set

---

## Alternative: Create Foundational Atoms (4-6 hours)

If you prefer to create 10 manual foundational atoms BEFORE uploading the 2,049:

### 5 Electrical Fundamentals
1. **voltage** - What is voltage, units (volts), water analogy
2. **current** - What is current, units (amps), electron flow
3. **resistance** - What is resistance, units (ohms), opposition to flow
4. **ohms-law** - V=IR relationship, calculations, applications
5. **power** - What is power, units (watts), P=VI formula

### 5 PLC Basics
1. **what-is-plc** - Definition, purpose, industrial applications
2. **scan-cycle** - Input scan → program execution → output update
3. **contacts-coils** - NO/NC contacts, coil symbols, relay logic
4. **io-basics** - Digital vs analog, addressing, wiring
5. **ladder-fundamentals** - Rungs, logic, series/parallel circuits

**Format:** Use IEEE LOM structure from `docs/ATOM_SPEC_UNIVERSAL.md`
**Tool:** Copy structure from existing atoms in `data/atoms/`
**Embeddings:** Use OpenAI API ($0.000004 per atom)

---

## Recommendation: Do Step 1 + Step 2 NOW

**Why upload 2,049 atoms first:**
- Embeddings already paid for ($0.008)
- Instant knowledge base (no waiting)
- Proves end-to-end pipeline works
- Scriptwriter can start immediately
- Foundational atoms can be added later (complementary, not blocking)

**Total Time:** 10 minutes
**Unlocks:** All Week 2 development
**Next:** Scriptwriter Agent → First Video → YouTube Launch

---

## Validation Commands

```bash
# 1. Schema validation
poetry run python scripts/validate_supabase_schema.py

# 2. Upload atoms
poetry run python scripts/upload_atoms_to_supabase.py

# 3. Verify upload
poetry run python -c "
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

result = client.table('knowledge_atoms').select('atom_id', count='exact').execute()
print(f'Total atoms in Supabase: {result.count}')
"

# 4. Test search
poetry run python -c "
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Search for PLC atoms
result = client.table('knowledge_atoms')\
    .select('title, manufacturer')\
    .ilike('title', '%PLC%')\
    .limit(10)\
    .execute()

print('PLC-related atoms:')
for atom in result.data:
    print(f'  - {atom[\"title\"]} ({atom[\"manufacturer\"]})')
"
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `docs/supabase_complete_schema.sql` | Complete 7-table schema (DEPLOY THIS) |
| `scripts/validate_supabase_schema.py` | Schema validation (RUN AFTER DEPLOY) |
| `scripts/upload_atoms_to_supabase.py` | Batch upload 2,049 atoms (RUN AFTER VALIDATION) |
| `data/atoms/*.json` | 2,049 atoms with embeddings (READY TO UPLOAD) |
| `KB_STATUS.md` | Current knowledge base status |
| `TASK.md` | Task tracking and priorities |

---

## Next Steps After Deployment

1. ✅ Deploy schema
2. ✅ Upload atoms
3. ✅ Verify upload
4. 🔨 Build Scriptwriter Agent
5. 🔨 Generate first video script
6. 🔨 Produce first video
7. 🔨 Upload to YouTube
8. 🎉 Public launch

**Estimated Timeline:**
- Deploy + Upload: 10 minutes (TODAY)
- Scriptwriter Agent: 6-8 hours (TOMORROW)
- First Video: 4-6 hours (DAY 3)
- YouTube Launch: Week 2 complete

---

## Support

**Stuck? Run these:**
```bash
# Check .env
cat .env | grep SUPABASE

# Test connection
poetry run python -c "from supabase import create_client; import os; from dotenv import load_dotenv; load_dotenv(); print('OK')"

# Re-run validation
poetry run python scripts/validate_supabase_schema.py
```

**Expected .env entries:**
```
SUPABASE_URL=https://mggqgrxwumnnujojndub.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sb_secret_x67ttLFGhQY_KsNmBB-fMQ_WC5Ab_tP
```

---

## 🚀 READY TO DEPLOY

**Total Time:** 10 minutes
**Files:** 3 (schema SQL, validation script, upload script)
**Result:** 2,049-atom knowledge base live and searchable
**Unlocks:** Week 2 development, Scriptwriter Agent, first video

**DO THIS NOW:**
1. Open Supabase SQL Editor
2. Paste `docs/supabase_complete_schema.sql`
3. Click RUN
4. Run `poetry run python scripts/upload_atoms_to_supabase.py`
5. Celebrate 🎉

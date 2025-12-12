# Production Deployment Plan - KB → Telegram → YouTube

**Goal:** Connect ScriptwriterAgent to Telegram bot, enable users to generate scripts, then manually create first video.

**Status:** ScriptwriterAgent is built and tested. 1,964 atoms in Supabase. Ready to integrate.

---

## Path to Production (4 Steps)

### Step 1: Integrate ScriptwriterAgent into Telegram Bot [2-3 hours]

**What:** Users can generate video scripts via Telegram natural language commands.

**User Experience:**
```
User: "Create a video script about PLC basics"
Bot: [Generating script from knowledge base...]
Bot: ✓ Script ready!
     Title: Introduction to PLCs
     Word count: 438 words
     Duration: ~3 minutes

     [Downloads script as .txt file]

     Citations:
     - 1756-um001-sample.pdf (pages 1)
     - siemens_24ad847469a7d540.pdf (pages 9)
```

**Implementation Tasks:**

1. **Update `kb_handlers.py`** - Add script generation handler
2. **Update `handlers.py`** - Route "create video" intent to script generator
3. **Update `intent_detector.py`** - Detect script generation requests
4. **Test flow** - Verify end-to-end from Telegram → Supabase → Script → Telegram

**Files to modify:**
- `agent_factory/integrations/telegram/kb_handlers.py` (add `generate_script_natural()`)
- `agent_factory/integrations/telegram/intent_detector.py` (add "script_gen" intent)
- `agent_factory/integrations/telegram/handlers.py` (already routes to kb_handlers)

**Success criteria:**
- User sends "create video about PLCs" in Telegram
- Bot generates script using ScriptwriterAgent
- Bot sends script back as downloadable .txt file
- Script includes personality markers and visual cues

---

### Step 2: KB Search Integration [1 hour]

**What:** Users can search knowledge base via Telegram for troubleshooting.

**User Experience:**
```
User: "Find troubleshooting for motor faults"
Bot: Found 3 knowledge atoms:

     1. Motor Fault Code 2210 (Allen Bradley)
        Summary: Overvoltage fault, check input power...
        Source: 1756-um001.pdf, page 45

     2. Motor Protection Settings (Siemens)
        Summary: Configure overload protection...
        Source: siemens_s7.pdf, page 112

     [show more] [get details #1]
```

**Implementation Tasks:**

1. **Add KB search handler** - Query atoms by keyword
2. **Format results for Telegram** - Clean output with inline buttons
3. **Add "get details" callback** - Show full atom content

**Success criteria:**
- User searches for topic in Telegram
- Bot returns relevant atoms from Supabase
- User can click to see full details

---

### Step 3: Test & Deploy Updated Bot [30 min]

**What:** Deploy updated Telegram bot with KB features to production.

**Tasks:**

1. **Test locally:**
   ```bash
   # Kill existing bot
   taskkill /F /IM python.exe /FI "WINDOWTITLE eq Agent Factory*"

   # Start updated bot
   cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
   poetry run python -m agent_factory.integrations.telegram
   ```

2. **Test commands:**
   - "Find troubleshooting for PLCs"
   - "Create video about motor control"
   - "Search for ladder logic examples"

3. **Deploy to production:**
   - Update Windows Task Scheduler task (if using)
   - Or: Keep running in background terminal
   - Verify bot responds after restart

**Success criteria:**
- Bot running 24/7
- KB search works via Telegram
- Script generation works via Telegram
- No errors in logs

---

### Step 4: Create First YouTube Video (Manual) [3-4 hours]

**What:** Use a generated script to create the first video manually, validate the content.

**Why manual first?**
- Validates script quality before automating
- Sets quality baseline for automation
- Faster than building VoiceProductionAgent + VideoAssemblyAgent

**Tasks:**

1. **Generate script via Telegram:**
   - Send: "Create video about Introduction to PLCs"
   - Download generated script .txt file

2. **Record narration (3 options):**

   **Option A: You narrate (10 min)**
   - Read script into phone/mic
   - Natural, authentic voice
   - Use personality markers as guides

   **Option B: Edge-TTS (5 min)**
   ```bash
   # Install Edge-TTS
   poetry add edge-tts

   # Generate audio from script
   edge-tts --text "$(cat script.txt)" --voice en-US-GuyNeural --write-media output.mp3
   ```

   **Option C: ElevenLabs (15 min)**
   - Copy script to elevenlabs.io
   - Use free tier (10k chars/month)
   - Download MP3

3. **Create visuals (30 min - simple version):**

   **Option A: PowerPoint video**
   - Create 5-8 slides with key points
   - Add text overlays for visual cues `[show diagram]`
   - Export as video (File → Export → Create Video)

   **Option B: Canva video**
   - Use Canva.com free tier
   - Create simple text + image slides
   - Export as MP4

   **Option C: Screen recording**
   - Open relevant documentation PDFs
   - Screen record while audio plays
   - Highlight sections matching visual cues

4. **Combine audio + visuals (15 min):**

   **Option A: Windows Photos app**
   - Open Photos → New video project
   - Add visuals, sync with audio
   - Export

   **Option B: DaVinci Resolve (free)**
   - Import audio + visuals
   - Sync on timeline
   - Export MP4

   **Option C: MoviePy (Python)**
   ```python
   from moviepy.editor import VideoClip, AudioFileClip
   # This is what VideoAssemblyAgent will automate later
   ```

5. **Upload to YouTube:**
   - Title: Use script title
   - Description: Include citations from script
   - Tags: PLC, automation, industrial, tutorial
   - Visibility: Unlisted (for review first)

6. **Review & validate:**
   - Watch full video
   - Check: Are facts accurate? (compare to atoms)
   - Check: Is pacing good? (adjust script template if needed)
   - Check: Are visuals helpful?

**Success criteria:**
- 1 video published to YouTube (unlisted)
- Video uses script generated by ScriptwriterAgent
- Video is 2-4 minutes long
- Content is factually accurate (based on atoms)
- Quality is acceptable for public release

---

## Timeline

**Total: 6-8 hours to first video**

| Step | Task | Time | When |
|------|------|------|------|
| 1 | Integrate ScriptwriterAgent → Telegram | 2-3h | Today |
| 2 | Add KB search to Telegram | 1h | Today |
| 3 | Test & deploy bot | 30m | Today |
| 4 | Create first video manually | 3-4h | Tomorrow |

**By end of Day 2:**
- ✓ Telegram bot can generate scripts
- ✓ Telegram bot can search knowledge base
- ✓ 1 video published on YouTube
- ✓ Quality baseline established

---

## After First Video

**Then we decide:**

1. **If quality is good:**
   - Create 2 more videos manually (Week 1)
   - Build VoiceProductionAgent + VideoAssemblyAgent (Week 2-3)
   - Automate video pipeline (Week 4)

2. **If quality needs work:**
   - Adjust script templates
   - Refine personality markers
   - Test different voices/styles
   - Iterate until satisfied

**The manual video proves the concept before investing in automation.**

---

## What NOT to Build Yet

❌ Don't build VoiceProductionAgent yet (wait for first video validation)
❌ Don't build VideoAssemblyAgent yet (wait for first video validation)
❌ Don't build YouTubeUploaderAgent yet (manual upload is fine for now)
❌ Don't build AnalyticsAgent yet (need views first)

**Why?** Validate the CONTENT first. If the script quality isn't good enough, automation won't help.

---

## Success Metrics

**Week 1:**
- ✓ 3 scripts generated via Telegram
- ✓ 1 video published (unlisted)
- ✓ Script template validated

**Week 2-3:**
- Build automation IF manual process validated
- 5-10 videos published
- First 100 views

**Month 1:**
- 20 videos published
- 1K views
- First subscriber comments

---

## Next Action: Integrate ScriptwriterAgent → Telegram

Ready to start Step 1?

**Command to run after integration:**
```bash
# Test script generation via Telegram
# 1. Start bot: poetry run python -m agent_factory.integrations.telegram
# 2. Send in Telegram: "Create video about PLC basics"
# 3. Verify script is generated and sent back
```

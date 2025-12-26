# Phase 5: Industrial Forum Backfill (Optional)

**Duration:** 8-16 hours
**Dependencies:** Phases 1-4 complete and validated
**Spec Reference:** `DYNAMIC_FEWSHOT_RAG_SPEC.md` Phase 5 section

---

## ⚠️ CLAUDE CODE CONSTRAINTS - CRITICAL

```
⛔ THIS PHASE REQUIRES MANUAL SUPERVISION

DO NOT:
- Run any scraping without user physically present
- Scrape any site without user confirming robots.txt compliance
- Ingest any data without human review step
- Store any personally identifiable information
- Exceed rate limits under any circumstance

ALLOWED (with supervision):
- Create scraping scripts (but don't run them)
- Create parsing templates
- Create quality filters
- Create ingestion pipelines (test mode only)
```

---

## 📖 BEFORE STARTING - STUDY THESE

### Industrial Datasets Reference
```
https://github.com/jonathanwvd/awesome-industrial-datasets
```

### Ethical Scraping Practices
```
https://www.scrapingbee.com/blog/web-scraping-best-practices/
```

### PLCTalk Forum Structure
```
https://www.plctalk.net/  (study HTML structure manually)
```

---

## 🎯 OBJECTIVE

Backfill knowledge base with high-quality industrial maintenance cases from professional forums.

**Why NOT Reddit:**
- Reddit = mostly DIY/homeowner content
- PLCTalk/Control.com = actual industrial technicians
- Higher signal-to-noise ratio

---

## 📊 SOURCE PRIORITIZATION

| Priority | Source | URL | Content Quality | Difficulty |
|----------|--------|-----|-----------------|------------|
| 1 | Your Roller Coaster Cases | Local | ⭐⭐⭐⭐⭐ | Easy |
| 2 | PLCTalk.net | https://plctalk.net | ⭐⭐⭐⭐⭐ | Medium |
| 3 | Control.com | https://control.com | ⭐⭐⭐⭐ | Medium |
| 4 | MrPLC.com | https://mrplc.com | ⭐⭐⭐⭐ | Medium |
| 5 | Siemens Support | Rockwell TechConnect | ⭐⭐⭐⭐⭐ | Hard (auth) |

---

## 📋 TASKS

### Task 5.1: Thread Quality Analyzer
**File:** `examples/backfill/quality_filter.py`

```python
"""
Create quality scoring for forum threads.

SCORING CRITERIA (0-100):
- has_accepted_solution: +30 points
- reply_count >= 3: +15 points
- contains_equipment_reference: +20 points
- has_fault_code_discussion: +15 points
- recent (< 5 years): +10 points
- author_reputation (if available): +10 points

THRESHOLD: Only process threads scoring >= 60

EQUIPMENT DETECTION:
- PLC brands: Allen-Bradley, Siemens, Mitsubishi, Omron
- VFD brands: ABB, Yaskawa, Danfoss, Rockwell
- Sensor types: proximity, photoelectric, encoder
- Fault codes: regex patterns like F-001, E123, AL-xx
"""
```

### Task 5.2: Thread Parser (Template Only)
**File:** `examples/backfill/thread_parser.py`

```python
"""
Parse forum thread into Case schema.

⚠️ DO NOT RUN - CREATE TEMPLATE ONLY

INPUT: Raw HTML of forum thread
OUTPUT: Case schema JSON

EXTRACTION TARGETS:
- original_problem: First post content
- equipment_mentioned: From all posts
- solution_posts: Posts marked as solution or highly upvoted
- fault_codes: Extracted from any post
- keywords: Auto-extracted from technical terms

USE CLAUDE TO:
- Summarize lengthy threads
- Extract root cause from discussion
- Identify resolution steps from solution post
- Generate keywords for embedding
"""
```

### Task 5.3: Rate-Limited Fetcher (Dry Run Mode)
**File:** `examples/backfill/fetcher.py`

```python
"""
Create rate-limited HTTP fetcher.

⚠️ DEFAULT: DRY_RUN = True (logs but doesn't fetch)

RATE LIMITS:
- PLCTalk: 1 request per 10 seconds
- Control.com: 1 request per 10 seconds
- MrPLC: 1 request per 10 seconds

HEADERS:
User-Agent: RivetCEO-KnowledgeBot/1.0 (Contact: your-email@domain.com)

REQUIRED CHECKS (before any request):
1. Check robots.txt (cache for 24h)
2. Respect Crawl-delay if specified
3. Skip disallowed paths
4. Log all requests for audit

AUDIT LOG FORMAT:
{
    "timestamp": "ISO8601",
    "url": "...",
    "status": "fetched|skipped|rate_limited|disallowed",
    "robots_txt_allowed": bool,
    "response_code": int
}
"""
```

### Task 5.4: Human Review Interface
**File:** `examples/backfill/reviewer.py`

```python
"""
Create CLI for human review of scraped cases.

WORKFLOW:
1. Load pending cases from staging/
2. Display one case at a time
3. Human chooses: [A]pprove, [R]eject, [E]dit, [S]kip
4. Approved cases move to approved/
5. Generate review statistics

DISPLAY FORMAT:
========================================
Case ID: PLCTalk-12345
Source: https://plctalk.net/thread/12345
Quality Score: 75/100
----------------------------------------
EQUIPMENT: Allen-Bradley ControlLogix
PROBLEM: Motor drives faulting intermittently
ROOT CAUSE: Loose terminal on DC bus
RESOLUTION: Retorqued all terminals
KEYWORDS: controllogix, vfd, fault, terminal
----------------------------------------
[A]pprove  [R]eject  [E]dit  [S]kip  [Q]uit
========================================
"""
```

### Task 5.5: Batch Ingestion Pipeline
**File:** `examples/backfill/ingestor.py`

```python
"""
Batch ingest approved cases into vector store.

INPUT: approved/ directory of reviewed cases
OUTPUT: Cases in vector store with metadata

METADATA TO ADD:
- source: "forum-backfill"
- source_url: original thread URL
- review_status: "human-approved"
- quality_score: from analyzer
- ingested_at: timestamp

DEDUPLICATION:
- Hash case content
- Check against existing embeddings
- Skip if similarity > 0.95 to existing case
"""
```

---

## 📁 DIRECTORY STRUCTURE

```
examples/backfill/
├── __init__.py
├── quality_filter.py      # Thread scoring
├── thread_parser.py       # HTML to Case schema
├── fetcher.py             # Rate-limited HTTP (dry run default)
├── reviewer.py            # Human review CLI
├── ingestor.py            # Batch ingestion
├── staging/               # Raw scraped threads (pending review)
├── approved/              # Human-approved cases
├── rejected/              # Cases rejected during review
└── audit_log.jsonl        # All fetch attempts
```

---

## 🧪 TEST MODE

```bash
# Run quality filter on sample HTML
python -m pytest tests/test_quality_filter.py -v

# Test parser on fixture (not live scrape)
python -m pytest tests/test_thread_parser.py -v

# Test fetcher in DRY_RUN mode
python examples/backfill/fetcher.py --dry-run --url "https://plctalk.net/..."

# Run human review on test fixtures
python examples/backfill/reviewer.py --test-mode
```

---

## 📜 ROBOTS.TXT COMPLIANCE

Before ANY scraping, manually verify:

**PLCTalk.net:**
```bash
curl https://www.plctalk.net/robots.txt
```

**Control.com:**
```bash
curl https://control.com/robots.txt
```

**If robots.txt disallows scraping:** DO NOT PROCEED. Contact site owner or find alternative source.

---

## ✅ ACCEPTANCE CRITERIA

- [ ] Quality filter scores sample threads accurately
- [ ] Parser extracts structured data from thread HTML
- [ ] Fetcher respects robots.txt and rate limits
- [ ] Human review interface is functional
- [ ] Batch ingestion adds metadata correctly
- [ ] Deduplication prevents duplicate cases
- [ ] 50+ cases approved through human review
- [ ] Retrieval diversity improves (test with varied queries)

---

## 🛑 CHECKPOINT

**STOP** after creating all scripts (but before running fetcher).

**User Must:**
1. Manually check robots.txt for each target site
2. Decide which sites to proceed with
3. Supervise first batch of fetching
4. Review first 20 cases personally
5. Validate retrieval improvements

**This phase is OPTIONAL.** Your roller coaster cases + Phase 4 auto-capture may be sufficient.

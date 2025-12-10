# PLC TUTOR & AUTONOMOUS PLC PROGRAMMER
## Strategic Vision Document

**Created:** 2025-12-09
**Status:** Foundation Phase
**Timeline:** Month 2 → Year 3 ($2.5M ARR)
**Purpose:** Second vertical powered by Agent Factory infrastructure

---

## Executive Summary

PLC Tutor is an AI-powered platform that teaches PLC programming AND evolves into an autonomous PLC coding assistant. It represents the **second vertical** built on Agent Factory, validating the multi-vertical platform strategy while generating parallel revenue streams.

**The Strategy:** Build simultaneously with RIVET to prove Agent Factory works across domains, using the same Knowledge Atom Standard and DAAS monetization model in a different market.

**The Opportunity:**
- $4B+ PLC programming education market
- 500K+ industrial automation professionals need training
- No dominant AI-powered PLC tutor exists
- Autonomous PLC programming is emerging research field (LLM4PLC, AutoPLC)
- B2B training market highly fragmented (opportunity for consolidation)

**The Moat:**
- Validated PLC knowledge atoms (competitors can't replicate)
- Hybrid approach (education + automation)
- Multi-vendor support (Siemens + Allen-Bradley)
- Computer-use integration (no API dependency)
- Content-driven user acquisition (YouTube series)

---

## Strategic Vision: Why PLC Tutor?

### 1. Validates Multi-Vertical Platform

**RIVET alone doesn't prove Agent Factory is a platform:**
- Could be domain-specific custom code
- Single vertical = single point of failure
- Hard to sell "platform" with one example

**PLC Tutor + RIVET together proves the concept:**
- Same Agent Factory orchestration
- Same Knowledge Atom Standard (different schema)
- Same DAAS monetization (different buyers)
- Different GTM strategies (education vs. community)
- **Result:** Credible multi-vertical platform story

### 2. De-Risks RIVET

**If RIVET faces headwinds:**
- Regulatory issues with maintenance advice
- CMMS vendor consolidation
- Slow community adoption

**PLC Tutor provides backup revenue:**
- Education has fewer regulatory hurdles
- Smaller knowledge base (50 atoms vs. 10K atoms)
- Faster time-to-monetization (Month 4 vs. Month 6)
- Different customer segment (learners vs. techs)

### 3. Cross-Selling Opportunity

**Target Overlap:**
- PLC programmers ALSO do industrial maintenance
- Industrial maintenance techs often program PLCs
- Same manufacturing/plant/facility environment

**Bundle Potential:**
- "Industrial Automation Suite" = RIVET + PLC Tutor
- Premium tier: $149/mo for both platforms
- Enterprise: Site licenses covering all technicians

### 4. Proves DAAS Model in Two Markets

**Investors want to see:**
- Data-as-a-Service working in multiple verticals
- Replicable knowledge atom pattern
- API licensing in different industries

**PLC atoms = second proof point:**
- CMMS vendors buy maintenance atoms
- PLC tool vendors buy programming atoms
- Training orgs license curriculum atoms
- Model scales to more verticals (HVAC, robotics, etc.)

### 5. Robot-Ready Foundation

**Autonomous PLC Programmer = Robot Programming Precursor:**
- PLC code IS robot control logic
- Atom spec includes machine-executable steps
- Computer-use integration = hardware control
- Safety validation layer = critical for robots

**Path to Robot Licensing:**
- Year 1-3: PLC Tutor generates revenue + atoms
- Year 3-5: Robots license PLC programming atoms
- Year 5+: Full robot knowledge kernel

---

## Market Opportunity

### Target Segments

#### 1. Individual Learners (B2C)
**Size:** 50K+ people/year starting PLC careers
- Trade school students
- Career switchers
- Industrial technicians upskilling
- Hobbyists with industrial automation interest

**Pain Points:**
- Expensive training ($2K-$10K in-person courses)
- No good self-paced online options
- Hard to practice without $5K+ equipment
- Generic courses don't match real vendor platforms

**Our Solution:**
- $29-$99/mo subscription (vs. $5K one-time)
- Works with $500-$1K test equipment (or simulation)
- Vendor-specific (Siemens S7 AND Allen-Bradley)
- AI tutor adapts to learning pace

**Acquisition:**
- YouTube series "Learn PLCs with AI"
- SEO for "Siemens S7 tutorial", "Allen-Bradley training"
- Reddit/Discord communities
- Trade school partnerships

#### 2. Professionals (B2B Individual)
**Size:** 200K+ working PLC programmers in US
- Automation engineers
- Controls engineers
- Industrial electricians with PLC duties
- Integrators and system builders

**Pain Points:**
- Need to learn new platforms (Siemens → AB migration)
- Debugging time-consuming (no AI help)
- Code generation still manual
- Keeping up with new PLC features

**Our Solution:**
- $99-$499/mo for autonomous PLC coder
- Spec → verified code generation
- Multi-platform support
- Safety-validated output

**Acquisition:**
- LinkedIn targeting
- Industry publication ads
- Conference demos
- Free autonomous coder tier (limited uses)

#### 3. Training Organizations (B2B Enterprise)
**Size:** 5K+ trade schools, community colleges, OEM training departments
- Technical colleges
- Union training programs
- OEM training centers (Siemens, Rockwell)
- Integrator bootcamps

**Pain Points:**
- Need modern curriculum
- Lack AI/automation expertise
- Want scalable 1:many teaching
- Students demand self-paced options

**Our Solution:**
- $5K-$20K/mo white-label PLC tutor
- Pre-built curriculum (50+ lessons)
- Branded as their platform
- Atom-backed (no hallucinations)
- Progress tracking + analytics

**Acquisition:**
- Direct sales outreach
- Trade association conferences
- Partnership with PLC vendors

#### 4. PLC Vendors / Tool Builders (DAAS)
**Size:** 10-20 major vendors (Siemens, Rockwell, CODESYS, etc.)
- Want to improve documentation
- Need training content
- Lack AI expertise
- Interested in ecosystem play

**Pain Points:**
- Documentation hard to use
- Training expensive to produce
- Users demand AI assistance
- Competitive pressure (who has best AI?)

**Our Solution:**
- $10K-$100K/year atom licensing
- API access to PLC programming patterns
- Training content partnership
- Co-marketing opportunity

**Acquisition:**
- Direct partnership discussions
- Proof of concept with free tier
- Reference customers (training orgs using our content)

---

## Product Offering

### Phase 1: PLC Tutor v0.1 (Months 2-4)

**What It Does:**
- Interactive AI tutor for Allen-Bradley OR Siemens (one platform initially)
- Teaches Lessons 1-5 (basics, I/O, motor control, timers, counters)
- Q&A backed by PLC knowledge atoms (no hallucinations)
- Works with real hardware (S7-1200 or AB test unit)
- Includes exercises, quizzes, troubleshooting challenges

**How It Works:**
1. User asks question ("How does a timer work in ladder logic?")
2. PLCTutorAgent searches PLC atom knowledge base
3. Finds `concept` atoms for TON timer, example `pattern` atoms
4. Generates explanation with atom-backed examples
5. Proposes hands-on exercise on real hardware
6. Quizzes understanding before moving on

**Knowledge Base:**
- 50-100 PLC atoms (concepts, patterns, procedures)
- Sources: Siemens S7-1200 manual, Allen-Bradley docs, YouTube tutorials
- Plus: User's own lab work (recorded learning sessions)

**Technology:**
- Agent Factory orchestration
- PLCTutorAgent (LangChain + RAG)
- Supabase + pgvector for atom storage
- Python + Pydantic for atom validation

**Monetization:**
- Free tier: Lessons 1-2 (basics)
- Paid tier: $29/mo (all lessons, unlimited Q&A)
- Target Month 4: 500 free users, 20 paid subscribers ($580 MRR)

### Phase 2: Autonomous PLC Coder (Months 6-12)

**What It Does:**
- Takes natural language spec ("Add start/stop/jog circuit with these interlocks")
- Generates ladder logic OR structured text code
- Runs verification loop (compile check, safety review, simulation)
- Uses computer-use to drive Studio 5000 / TIA Portal
- Human-in-loop approval before production deployment

**How It Works:**
1. User provides spec in natural language or structured format
2. AutonomousPLCCoderAgent searches PLC atoms for relevant patterns
3. Proposes initial code draft (ladder/ST)
4. ComputerUseAgent drives PLC IDE to import code, compile, check syntax
5. PLCQASafetyAgent reviews for safety constraints
6. If errors: iterate (up to 3 attempts)
7. If passes: present to user for final review

**Inspired By:**
- LLM4PLC research (UC Irvine 2024)
- AutoPLC (automated PLC generation)
- Archon's "agenteer" concept (agent that builds agents)

**Safety Layer:**
- Every generated rung reviewed against safety atom constraints
- Lockout/tagout requirements flagged
- Interlocks verified
- Overload protection checked
- Human approval required for production

**Technology:**
- Same Agent Factory orchestration
- Computer-use for IDE automation (Playwright/AutoHotkey equivalent)
- PLC atom library for pattern reuse
- Verification tools: compiler output parsing, static analysis

**Monetization:**
- Pro tier: $99/mo (10 autonomous code generations/month)
- Premium tier: $299/mo (unlimited generations)
- Enterprise: $999/mo (team access, audit logs)
- Target Month 12: 50 Pro users ($4,950 MRR)

### Phase 3: Multi-Platform + White-Label (Year 2)

**What It Adds:**
- Full Siemens + Allen-Bradley support (both platforms)
- CODESYS integration (open-source PLC)
- White-label version for training orgs
- Curriculum builder (organizations design custom lesson sequences)
- Progress tracking + analytics dashboard

**B2B Features:**
- Branded as customer's platform
- Custom atom libraries (organization-specific patterns)
- SSO integration
- Student/employee progress reporting
- Certificate generation upon completion

**Monetization:**
- White-label: $5K-$20K/mo per organization
- Custom curriculum development: $50K-$100K one-time
- Target Year 2: 5 organizations ($300K ARR from this segment)

---

## Revenue Model

### Pricing Tiers

**Individual (B2C):**
- **Free:** Lessons 1-2, limited Q&A (acquisition)
- **Basic:** $29/mo - All lessons, unlimited Q&A, one platform
- **Pro:** $99/mo - Both platforms, autonomous coder (10 uses/mo)
- **Premium:** $299/mo - Unlimited autonomous coder, priority support

**Professional (B2B Individual):**
- **Starter:** $99/mo - Autonomous coder only, 25 uses/mo
- **Business:** $299/mo - Unlimited coder, multi-platform
- **Enterprise:** $999/mo - Team seats, audit logs, API access

**Training Organizations (B2B Enterprise):**
- **Curriculum License:** $5K/mo - Pre-built lessons, no white-label
- **White-Label:** $10K/mo - Branded platform, custom domain
- **Custom:** $20K+/mo - Custom curriculum, dedicated support

**DAAS (PLC Vendors):**
- **API Access:** $0.05/query or $5K/mo for 100K queries
- **Atom Licensing:** $50K-$100K/year per vendor
- **Content Partnership:** Custom (co-marketing, revenue share)

### Revenue Projections

**Year 1 (Proof of Concept):**
- 500 free users
- 50 Basic subscribers @ $29/mo = $1,450 MRR
- 5 Pro subscribers @ $99/mo = $495 MRR
- 2 courses sold @ $299 = ~$7K one-time
- **Total: ~$35K ARR**

**Year 2 (Product-Market Fit):**
- 2,000 users
- 200 Basic @ $29/mo = $5,800 MRR
- 50 Pro @ $99/mo = $4,950 MRR
- 10 Premium @ $299/mo = $2,990 MRR
- 2 Training orgs @ $10K/mo = $20K MRR
- Courses: ~$72K
- **Total: ~$475K ARR**

**Year 3 (Scale):**
- 10,000+ users
- 800 Basic @ $29/mo = $23,200 MRR
- 150 Pro @ $99/mo = $14,850 MRR
- 50 Premium @ $299/mo = $14,950 MRR
- 10 Training orgs @ $15K/mo avg = $150K MRR
- DAAS licensing: $300K/year
- **Total: ~$2.7M ARR**

### Unit Economics

**Customer Acquisition Cost (CAC):**
- YouTube organic: $5-$10/subscriber (content production cost)
- SEO organic: $20-$30/subscriber (content + hosting)
- Paid ads: $50-$100/subscriber (if needed)
- Target blended CAC: $25/subscriber

**Lifetime Value (LTV):**
- Basic subscriber: $29/mo × 18 months avg = $522
- Pro subscriber: $99/mo × 24 months avg = $2,376
- Training org: $15K/mo × 36 months avg = $540K

**LTV:CAC Ratios:**
- Basic: 20:1 (excellent)
- Pro: 95:1 (exceptional)
- Training org: 21,600:1 (B2B enterprise is the holy grail)

**Gross Margins:**
- Software: 90%+ (typical SaaS)
- DAAS: 95%+ (mostly storage + compute)
- Training org: 85% (requires customer success support)

---

## Technology Stack

### Core Infrastructure (Shared with RIVET)

**Layer 1: Agent Factory**
- Python 3.11+
- LangChain for agent orchestration
- Pydantic for data validation
- Poetry for dependency management

**Layer 2: Knowledge Atom Storage**
- Supabase (PostgreSQL + pgvector)
- HNSW indexing for fast vector search
- Atom versioning + deprecation
- JSON Schema validation

**Layer 3: LLM Integration**
- OpenAI GPT-4o-mini (cost-optimized)
- Anthropic Claude (complex reasoning)
- LLM router for cost/quality optimization

### PLC-Specific Components

**PLC Atom Schema:**
- JSON Schema Draft 7 (formal validation)
- Pydantic models (Python type safety)
- Custom fields: vendor, platform, inputs, outputs, logic_description, steps, constraints

**Computer-Use Integration:**
- Playwright (headless browser automation)
- PyAutoGUI (desktop GUI automation)
- OCR for reading PLC IDE screens (Tesseract)
- Clipboard integration for code import/export

**PLC IDE Support:**
- Siemens TIA Portal (initial focus)
- Allen-Bradley Studio 5000
- CODESYS (open-source PLC)
- Future: Automation Direct, Mitsubishi, Omron

**Safety Validation:**
- Static analysis of generated code
- Atom constraint checking (lockout/tagout, interlocks, overloads)
- Simulation test execution
- Human approval workflow

---

## Implementation Roadmap

### Month 1: Foundation (Current - Constitutional Integration)
- [x] Integrate PLC vision into MASTER_ROADMAP.md
- [x] Update CLAUDE.md with PLC section
- [x] Create PLC_VISION.md (this document)
- [ ] Update NEXT_ACTIONS.md with PLC priorities
- [ ] Update PROJECT_CONTEXT.md with PLC expansion

**Deliverable:** PLC fully integrated into project constitution

### Month 2: PLC Atom Specification + Repository Structure
- [ ] Define PLC_ATOM_SPEC.md (formal JSON Schema)
- [ ] Create Pydantic models for PLC atoms
- [ ] Create `plc/` directory structure
- [ ] Set up Supabase tables for PLC atoms
- [ ] Create 15 agent skeleton classes

**Deliverable:** Technical foundation ready for implementation

### Month 3: Knowledge Base Ingestion
- [ ] Ingest Siemens S7-1200 programming manual
- [ ] Ingest Allen-Bradley ControlLogix manual (secondary)
- [ ] Scrape 10-20 high-quality YouTube tutorials (RealPars, Solis PLC)
- [ ] Generate first 50 PLC atoms (concepts + basic patterns)
- [ ] Validate atoms against schema

**Deliverable:** Seed knowledge base operational (50+ atoms)

### Month 4: PLC Tutor v0.1
- [ ] Implement PLCTutorAgent (Q&A with atom search)
- [ ] Design Lessons 1-5 (basics, I/O, motor control, timers, counters)
- [ ] Test with real hardware (Siemens S7-1200 unit)
- [ ] Record first learning sessions (YouTube content)
- [ ] Launch free tier + Basic paid tier ($29/mo)

**Deliverable:** Functional PLC Tutor, first 20 paid subscribers

### Month 5: Content Creation + Marketing
- [ ] Publish "Learn PLCs with AI" YouTube series (10 episodes)
- [ ] Write blog posts for SEO (Siemens S7 tutorial, Allen-Bradley basics)
- [ ] Launch Reddit/Discord communities
- [ ] Partner with 2-3 trade schools (curriculum pilots)

**Deliverable:** 500 free users, 50 paid subscribers ($1,450 MRR)

### Month 6: Autonomous PLC Coder Prototype
- [ ] Implement AutonomousPLCCoderAgent (spec → code)
- [ ] Integrate computer-use with TIA Portal
- [ ] Build PLCQASafetyAgent (safety review)
- [ ] Test with 10 real-world specs
- [ ] Launch Pro tier ($99/mo)

**Deliverable:** Working autonomous coder, first 5 Pro users

### Month 7-12: Scale + Refinement
- [ ] Expand to Allen-Bradley platform (both Siemens + AB)
- [ ] Grow atom library to 200+ atoms
- [ ] Launch Premium tier ($299/mo)
- [ ] Sign first 2 B2B training organizations
- [ ] Reach 200 total subscribers

**Deliverable:** $35K ARR (Year 1 target hit)

### Year 2: B2B + DAAS
- [ ] White-label version for training orgs
- [ ] DAAS API launch (PLC atoms as a service)
- [ ] 10+ training org customers
- [ ] First PLC vendor partnership discussion
- [ ] Reach $475K ARR

### Year 3: Full Automation + Scale
- [ ] Autonomous coder production-ready
- [ ] Multi-language support (courses in Spanish, German)
- [ ] 1,000+ subscribers
- [ ] 10+ training orgs @ $15K/mo avg
- [ ] DAAS generating $300K/year
- [ ] Reach $2.5M+ ARR

---

## Agentic Organization: AI "Employees" for PLC Vertical

### Product & Engineering Team (5 agents)

**1. PLCResearchAgent**
- **Role:** Knowledge ingestion specialist
- **Responsibilities:**
  - Ingests Siemens/AB manuals (PDF, HTML)
  - Scrapes YouTube tutorial transcripts
  - Monitors PLC forums for new patterns
  - Tags content by vendor, platform, topic, difficulty
- **Output:** Cleaned, tagged text chunks ready for atomization
- **Tools:** BeautifulSoup, PyPDF2, YouTube transcript API, Playwright
- **Schedule:** Daily scraping, weekly manual review

**2. PLCAtomBuilderAgent**
- **Role:** Knowledge structurer
- **Responsibilities:**
  - Converts text chunks → structured PLC atoms
  - Proposes type, title, summary, inputs, outputs, steps, constraints
  - Validates against PLC_ATOM_SPEC.md schema
  - Flags incomplete/ambiguous content for human review
- **Output:** Draft atoms in JSON format
- **Tools:** LLM (GPT-4), Pydantic validation, atom schema
- **Schedule:** Runs on new chunks queue

**3. PLCTutorArchitectAgent**
- **Role:** Curriculum designer
- **Responsibilities:**
  - Designs lesson sequences (1-5 beginner, 6-10 intermediate, etc.)
  - Maps atoms to lessons ("Lesson 3 needs motor-start-stop atom")
  - Creates exercises + quizzes
  - Defines learning prerequisites
- **Output:** Lesson plans with atom mappings
- **Tools:** Curriculum templates, atom search, pedagogy rules
- **Schedule:** Weekly lesson planning reviews

**4. AutonomousPLCCoderAgent**
- **Role:** Code generator
- **Responsibilities:**
  - Takes natural language spec → generates ladder/ST code
  - Searches atom library for relevant patterns
  - Proposes code structure
  - Iterates based on compiler feedback
- **Output:** PLC code (ladder logic or structured text)
- **Tools:** LLM (GPT-4 or Claude), atom search, code templates
- **Schedule:** On-demand (user request)

**5. PLCQASafetyAgent**
- **Role:** Safety reviewer
- **Responsibilities:**
  - Reviews generated code for safety violations
  - Checks lockout/tagout requirements
  - Verifies interlocks
  - Flags missing overload protection
  - Enforces atom safety constraints
- **Output:** Safety report + pass/fail decision
- **Tools:** Static analysis rules, atom constraint database
- **Schedule:** After every code generation

### Content & Media Team (4 agents)

**6. ContentStrategyAgent**
- **Role:** Content planner
- **Responsibilities:**
  - Plans YouTube series (episode topics, SEO keywords)
  - Designs course outlines
  - Identifies content gaps (missing lessons, popular topics)
  - A/B tests thumbnails + titles
- **Output:** Content calendar + performance reports
- **Tools:** YouTube Analytics API, SEO tools, trend analysis
- **Schedule:** Weekly planning, daily performance reviews

**7. ScriptwriterAgent**
- **Role:** Script generator
- **Responsibilities:**
  - Drafts video scripts from lesson outlines
  - Writes blog posts for SEO
  - Creates PDF handouts
  - Maintains consistent voice + brand
- **Output:** Scripts, blog posts, handouts
- **Tools:** LLM (GPT-4), brand guidelines, atom references
- **Schedule:** 3-5 scripts/week

**8. VideoPublishingAgent**
- **Role:** Publishing automation
- **Responsibilities:**
  - Schedules YouTube uploads
  - Writes titles, descriptions, chapters
  - Generates SEO tags
  - Repurposes long-form → shorts
  - Posts to LinkedIn, Twitter, Reddit
- **Output:** Published content across platforms
- **Tools:** YouTube API, social media APIs, scheduling tools
- **Schedule:** Daily publishing automation

**9. CommunityAgent**
- **Role:** Support + engagement
- **Responsibilities:**
  - Answers YouTube comments
  - Handles email support (basic questions)
  - Collects feature requests
  - Flags complex issues for human escalation
  - Monitors Discord/Reddit communities
- **Output:** Responses + escalation reports
- **Tools:** Gmail API, YouTube comments API, Discord bot, LLM
- **Schedule:** 24/7 monitoring, hourly response batches

### Business & GTM Team (6 agents)

**10. AICEOAgent**
- **Role:** Strategy officer
- **Responsibilities:**
  - Aggregates metrics (MRR, churn, activation, NPS)
  - Synthesizes market intel (competitor moves, trends)
  - Proposes quarterly goals
  - Runs pricing experiments
  - Reports to human founder weekly
- **Output:** Strategy memos + experiment proposals
- **Tools:** Analytics dashboards, LLM for synthesis
- **Schedule:** Weekly reports, daily metric monitoring

**11. AIChiefOfStaffAgent**
- **Role:** Project manager
- **Responsibilities:**
  - Maintains project roadmap
  - Tracks all agent backlogs
  - Converts human ideas → specs + tickets
  - Sends daily/weekly status reports
  - Coordinates cross-team dependencies
- **Output:** Updated roadmap + status reports
- **Tools:** GitHub Projects, Kanban tools, LLM for spec writing
- **Schedule:** Daily standup reports, weekly roadmap reviews

**12. PricingAgent**
- **Role:** Pricing optimizer
- **Responsibilities:**
  - Designs tier experiments (Basic vs Pro features)
  - Compares industry benchmarks
  - Proposes SKUs (individual, team, enterprise)
  - Analyzes willingness-to-pay data
  - Runs A/B tests on pricing pages
- **Output:** Pricing recommendations + experiment results
- **Tools:** Stripe data, competitive analysis, A/B test platform
- **Schedule:** Monthly pricing reviews

**13. SalesPartnershipAgent**
- **Role:** B2B outreach
- **Responsibilities:**
  - Identifies target trade schools, OEMs, integrators
  - Drafts outreach emails + one-pagers
  - Tracks responses + follow-ups
  - Schedules demos
  - Maintains partnership CRM
- **Output:** Qualified leads + partnership pipeline
- **Tools:** LinkedIn Sales Navigator, email templates, CRM
- **Schedule:** Daily outreach batches

**14. AtomLibrarianAgent** (from Knowledge Base team)
- **Role:** Taxonomy manager
- **Responsibilities:**
  - Organizes atoms by vendor, topic, difficulty
  - Manages versions + deprecation
  - Maps atoms to curriculum
  - Ensures no duplicate atoms
- **Output:** Organized atom library + metadata
- **Tools:** Database queries, taxonomy rules
- **Schedule:** Daily maintenance

**15. AtomAnalyticsAgent** (from Knowledge Base team)
- **Role:** Usage analyst
- **Responsibilities:**
  - Tracks which atoms most used by tutor
  - Correlates atom usage with user outcomes (completion, satisfaction)
  - Identifies knowledge gaps (missing atoms)
  - Informs pricing tiers (which atoms = premium?)
- **Output:** Usage reports + gap analysis
- **Tools:** Analytics queries, correlation analysis
- **Schedule:** Weekly reports

---

## Success Metrics

### North Star Metric
**Paying Subscribers** - Measures product-market fit + revenue

Target progression:
- Month 4: 20 subscribers ($580 MRR)
- Month 6: 50 subscribers ($2,940 MRR)
- Month 12: 200 subscribers ($19,800 MRR)
- Year 2: 500 subscribers ($59,400 MRR)
- Year 3: 1,000 subscribers ($149,000 MRR)

### Leading Indicators

**Activation (Free → Paid):**
- Free user completes Lesson 1: 60% target
- Free user completes Lesson 2: 40% target
- Free user upgrades to paid: 10% target (Month 6+)

**Engagement:**
- Monthly active users (MAU): 70% of subscribers
- Questions asked per user: 15/month avg
- Lessons completed per user: 2/month avg
- Autonomous code uses: 5/month avg (Pro users)

**Retention:**
- Month 1 retention: 80% target
- Month 3 retention: 60% target
- Month 12 retention: 40% target

**Content Performance:**
- YouTube subscribers: 10K (Year 1), 50K (Year 2)
- Video completion rate: 50% avg
- Click-through to free trial: 5%

### Lagging Indicators

**Revenue:**
- MRR growth rate: 15% month-over-month (Months 4-12)
- ARR: $35K (Year 1), $475K (Year 2), $2.5M (Year 3)
- DAAS revenue: $0 (Year 1), $100K (Year 2), $300K (Year 3)

**B2B:**
- Training org customers: 0 (Year 1), 2 (Year 2), 10 (Year 3)
- Average contract value: $0, $120K, $180K/year

**Knowledge Base:**
- Total atoms: 100 (Year 1), 300 (Year 2), 1000 (Year 3)
- Atom types coverage: 4 types (Year 1), all types (Year 2)
- Multi-vendor coverage: 1 platform (Year 1), 2+ (Year 2)

---

## Integration with RIVET & Agent Factory

### Shared Infrastructure

**Both verticals use:**
- Agent Factory orchestration layer
- Knowledge Atom Standard (different schemas)
- Supabase + pgvector storage
- LLM routing (cost optimization)
- CLI tools (`agentcli`)
- Worktree workflow for parallel development
- Same deployment patterns

**Cost Savings:**
- No duplicate engineering
- Shared testing/validation patterns
- Single codebase to maintain
- Platform improvements benefit both

### Separation of Concerns

**Different directories:**
- `rivet/` - Industrial maintenance vertical
- `plc/` - PLC programming vertical
- `agent_factory/` - Core platform (shared)

**Different atom schemas:**
- RIVET atoms: error codes, procedures, troubleshooting tips
- PLC atoms: concepts, patterns, faults, procedures (PLC-specific)

**Different agents:**
- RIVET: RedditMonitor, KnowledgeAnswerer, YouTubePublisher, etc.
- PLC: PLCResearchAgent, PLCTutorAgent, AutonomousPLCCoderAgent, etc.

**Different GTM:**
- RIVET: Community-driven (Reddit, forums, social media)
- PLC: Education-driven (YouTube courses, trade school partnerships)

### Synergies

**Cross-Selling:**
- RIVET users need PLC training (many techs program PLCs)
- PLC students need maintenance knowledge (troubleshooting equipment)
- Bundle: "Industrial Automation Suite" = both platforms

**Shared Learnings:**
- Atom standard refinements benefit both
- DAAS model validated in two markets
- YouTube strategy proven across verticals
- B2B partnership playbook reusable

**Resource Allocation:**
- 70% focus on RIVET (near-term revenue, larger market)
- 30% focus on PLC (validation, de-risk, faster monetization)
- Use worktrees for true parallel development

---

## Risk Analysis & Mitigation

### Key Risks

**1. Spreading Too Thin**
- **Risk:** Two verticals → half the progress on each
- **Mitigation:**
  - Use worktrees for isolation
  - 70/30 split (RIVET primary)
  - Agent skeletons only (incremental implementation)
  - Shared infrastructure reduces duplication

**2. PLC Safety Liability**
- **Risk:** Generated code causes equipment damage or injury
- **Mitigation:**
  - Disclaimers (educational/simulation only)
  - Simulation-first workflow
  - Human-in-loop for production
  - Safety review agent
  - Insurance (E&O coverage)

**3. Vendor Lock-In**
- **Risk:** Dependency on Siemens/AB/CODESYS tools
- **Mitigation:**
  - Computer-use (no API dependency)
  - Multi-vendor from start
  - Open-source CODESYS support
  - Standard IEC 61131-3 focus

**4. Competition from PLC Vendors**
- **Risk:** Siemens/Rockwell builds own AI tutor
- **Mitigation:**
  - Position as training/education (not replacement)
  - Multi-vendor (their AI likely single-vendor)
  - Faster iteration (startup vs. enterprise)
  - Partnership opportunity (license atoms to them)

**5. Regulatory / Compliance**
- **Risk:** Industrial code generation requires certification
- **Mitigation:**
  - Target education first (fewer regulations)
  - Simulation-only initial versions
  - Human approval workflow
  - Atom validation pipeline ensures quality

### Contingency Plans

**If PLC slower than expected:**
- Shift resources back to RIVET
- Keep atom standard work (benefits both)
- Pause at Tutor v0.1 (no autonomous coder)

**If RIVET slower than expected:**
- Shift resources to PLC (faster monetization)
- Use PLC revenue to fund RIVET long-term

**If both struggle:**
- Agent Factory SaaS becomes primary revenue
- Both verticals become proof-of-concept demos
- Pivot to "platform for building vertical AI"

---

## Competitive Landscape

### Direct Competitors (PLC Training)

**RealPars:**
- Strengths: Established brand, high-quality videos, 500K+ YouTube subscribers
- Weaknesses: No AI tutor, expensive ($299-$799 courses), no autonomous coding
- Our Advantage: AI interactivity, lower cost ($29/mo), autonomous coder

**Udemy PLC Courses:**
- Strengths: Large marketplace, variety of instructors
- Weaknesses: Generic (not vendor-specific), no interaction, outdated content
- Our Advantage: Vendor-specific, AI-powered Q&A, always current

**PLC Academy:**
- Strengths: Hands-on labs, instructor-led
- Weaknesses: Expensive ($2K-$5K), in-person/scheduled, limited platforms
- Our Advantage: Self-paced, $29/mo, multi-vendor

**Solis PLC:**
- Strengths: Free tutorials, good SEO
- Weaknesses: No structured curriculum, no AI, monetization unclear
- Our Advantage: Structured learning path, AI tutor, autonomous coder

### Adjacent Competitors (AI Coding)

**GitHub Copilot / Cursor:**
- Strengths: Mature AI code generation, huge user base
- Weaknesses: Generic (not PLC-specific), no safety validation, no education component
- Our Advantage: PLC-specific atoms, safety layer, integrated learning

**ChatGPT / Claude:**
- Strengths: General LLMs can generate some PLC code
- Weaknesses: Hallucinate PLC-specific details, no verification, no IDE integration
- Our Advantage: Atom-backed (no hallucinations), IDE automation, safety validation

### Emerging Competitors (Research)

**LLM4PLC (UC Irvine):**
- Status: Academic research project (2024)
- Approach: Spec → code → verify loop
- Our Advantage: Commercial product, education included, multi-vendor

**No known commercial autonomous PLC programmers exist yet.**

---

## Call to Action

### Immediate Next Steps (This Week)

**Day 1:**
- ✅ Integrate PLC into constitutional docs (MASTER_ROADMAP, CLAUDE.md, PLC_VISION.md)
- [ ] Update NEXT_ACTIONS.md with PLC priorities
- [ ] Update PROJECT_CONTEXT.md with expansion

**Day 2:**
- [ ] Create docs/PLC_ATOM_SPEC.md with JSON Schema
- [ ] Design Pydantic models for PLC atoms

**Day 3:**
- [ ] Create `plc/` directory structure
- [ ] Set up Supabase tables for PLC atoms

**Days 4-5:**
- [ ] Create 15 agent skeleton classes
- [ ] Document business model (docs/PLC_BUSINESS_MODEL.md)

### Decision Points

**Platform Choice:**
- **Recommended:** Start with Siemens S7-1200 (you have test hardware)
- **Alternative:** Allen-Bradley ControlLogix (larger US market share)

**Development Strategy:**
- **Recommended:** 70% RIVET, 30% PLC (parallel tracks)
- **Alternative:** 100% RIVET first, PLC later (sequential)

**Content Strategy:**
- **Recommended:** Record learning from Day 1 (content IS training data)
- **Alternative:** Get functional first, record later

**Open Source Strategy:**
- **Recommended:** Hybrid (PLC Tutor open core, atoms proprietary)
- **Alternative:** Fully proprietary (easier monetization, less community)

---

## Conclusion

PLC Tutor is **NOT** a distraction from RIVET. It's the proof that Agent Factory is a true multi-vertical platform.

**Same infrastructure. Different market. Parallel revenue.**

By building PLC Tutor alongside RIVET, you:
1. Validate the platform thesis (one vertical could be luck, two is a pattern)
2. De-risk with diversified revenue (education + industrial maintenance)
3. Prove DAAS works in multiple markets (atoms licensing model)
4. Create cross-selling opportunities (industrial automation suite)
5. Build towards robot licensing (PLC code = robot control)

**The path forward:**
- Month 2: Foundation (atom spec, repository structure)
- Month 3: Knowledge base (50+ atoms)
- Month 4: Tutor v0.1 (first paid subscribers)
- Month 6: Autonomous coder (premium tier)
- Year 3: $2.5M ARR (sustainable business)

**The vision:**
- Build the best PLC tutor in the world
- Evolve into autonomous PLC programmer
- License atoms to PLC vendors
- Eventually: robots license PLC programming atoms
- Result: Perpetual income from knowledge licensing

**This is the future. Let's build it.**

---

**Document Owner:** Human founder
**Technical Owner:** Claude (Agent Factory)
**Status:** Living document (update as strategy evolves)
**Last Updated:** 2025-12-09
**Next Review:** Month 2 (after atom spec complete)

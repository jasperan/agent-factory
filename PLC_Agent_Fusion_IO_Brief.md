# PLC Agent Fusion I/O Integration — Comprehensive Research & Architecture Brief

**Objective:** Build an agentic system that connects Factory I/O simulation, natural-language PLC code generation, multi-agent orchestration, and a CMMS knowledge backbone so that Claude Code can evaluate all approaches and recommend the best architecture for your specific workflow.

---

## Part 1: The Problem You're Solving

You are building an **industrial maintenance CMMS** powered by autonomous agents that:
1. Ingest technical manuals, electrical prints, and maintenance history.
2. Generate and deploy PLC code in natural language via agents (e.g., "enable pump interlock when tank pressure exceeds 50 PSI").
3. Test code in a live Factory I/O simulation loop.
4. Store results back into the CMMS so every work order teaches the system.
5. Continuously improve machine-specific "knowledge" over time.

**Your unique angle:** The CMMS work-order history and per-machine metadata become the **long-term memory** and **control plane** for the agents, something no one else is doing in this exact way.

---

## Part 2: Core Architecture Pattern (High-Level)

### The Three-Layer Agentic Stack

1. **Short-Term Agents (Frontline/Reactive)**
   - Live in Telegram or web UI
   - Answer: "Get me the PowerFlex 525 manual" or "What did I do on Machine 2143 last week?"
   - Fast RAG over local KB; escalate if manual missing
   - Return PDFs/results immediately

2. **Mid-Term Agents (Workflow/Orchestration)**
   - Manage work orders, parts tracking, follow-ups
   - Link troubleshooting sessions to case files
   - Ensure every closed job enriches the CMMS metalayer

3. **Long-Term Agents (Research/Knowledge Acquisition)**
   - Run background crawlers (Firecrawl, ScraperAPI) to fetch missing manuals
   - Ingest PDFs, normalize model numbers, create vector embeddings
   - Build and heal the global maintenance knowledge base

### The Factory I/O Integration Loop

- **Factory I/O** (local Windows box or small-form PC): 3D industrial simulation
- **VPS Agent Brain:** Agent factory, orchestration, scheduling, CMMS logic
- **Bridge Service:** Connects VPS agents to Factory I/O via Web API or OPC UA
- **Display:** RDP/VNC to see 3D simulation while agents control via API

### The PLC Code Generation Loop

- **User Request in Telegram:** "Make the conveyor start when the button is pressed and stop when full"
- **Agent processes:** NL → Structured Text (ST) or Ladder Logic
- **Verification agent:** Checks syntax, logic, safety constraints
- **Deploy agent:** Writes to Factory I/O tags via API
- **Observe:** Simulation runs the logic; results feed back to CMMS

---

## Part 3: Research Resources & Reference Implementations

### A. Multi-Agent Orchestration & Long-Running Agentic Stacks

**Open Manus Ecosystem (the inspiration for your "Open Mantis" approach)**

- **FoundationAgents/OpenManus** (main repo): 50.5k stars, 8.8k forks
  - Link: https://github.com/FoundationAgents/OpenManus
  - What it shows: Long-running agents on cloud VMs, planner → executor → validator patterns, durable task queues
  - Why study it: Proves the orchestration pattern is proven; yours adds industrial domain & CMMS backbone

- **henryalps/OpenManus** (focused variant): ~790 stars
  - Link: https://github.com/henryalps/OpenManus
  - What it shows: Simplified multi-agent planner for smaller use cases

- **OpenManus Architecture Deep Dive (case study article)**
  - Link: https://dev.to/jamesli/openmanus-architecture-deep-dive-enterprise-ai-agent-development-with-real-world-case-studies-5hi4
  - What it covers: Real-world patterns for planning, execution, validation loops; enterprise use case breakdowns

- **Nate's Newsletter: Complete Guide to AI Multi-Agent Orchestration with Manus**
  - Link: https://natesnewsletter.substack.com/p/the-complete-guide-to-ai-multi-agent
  - What it covers: Detailed walkthrough of multi-agent coordination, tool binding, state management

- **ZenML: Manus AI Agent Platform (cloud runtime deep-dive)**
  - Link: https://www.zenml.io/llmops-database/building-an-ai-agent-platform-with-cloud-based-virtual-machines-and-extended-context
  - What it covers: Long-running tasks, extended context, persistence, background workers on remote VMs

- **Wing Venture Capital: The Agentic AI Runtime Stack (2025)**
  - Link: https://www.wing.vc/content/the-agentic-ai-runtime-stack
  - What it covers: 7-layer stack breakdown; identifies which layers have moats vs are commodities
  - Key insight: Runtime + orchestration are medium-moat; domain-specific reasoning + observation layers are the real value

- **AI Multiple: The 7 Layers of Agentic AI Stack in 2026**
  - Link: https://research.aimultiple.com/agentic-ai-stack/
  - What it covers: Model layer, reasoning, tools, runtime, observability, memory — how they stack; where to invest
  - Relevance: Shows where your industrial + CMMS layer sits in the bigger picture

### B. Natural Language → PLC Code Generation

**Academic & Research Projects**

- **Agents4PLC (the gold standard for NL → PLC code)**
  - GitHub Release: https://github.com/Luoji-zju/Agents4PLC_release
  - Paper (Oct 2024): https://arxiv.org/abs/2410.14209
  - What it does: Multi-agent system (planner, code generator, verifier) that takes requirements in English and outputs verified Structured Text for PLCs
  - Why it matters: Exactly the "write PLC code from English" pattern you need; agents + verification is the right mental model
  - Watchout: This is research-grade; you'll need to adapt the prompts and validation logic to your domain

- **Agents4PLC: Literature Review & Deep-Dive**
  - Link: https://www.themoonlight.io/en/review/agents4plc-automating-closed-loop-plc-code-generation-and-verification-in-industrial-contr...
  - What it covers: Breakdown of the multi-agent loop, failure modes, improvements

- **Agents4PLC: Breaking and Fixing Defenses (Scribd PDF)**
  - Link: https://www.scribd.com/document/817273711/2024-Agents4PLC-Automating-Closed-loop-PLC-Code
  - What it covers: Implementation details, agent prompts, verification strategies

- **LLM4PLC (another major approach)**
  - GitHub: https://github.com/AICPS/LLM_4_PLC
  - What it does: LLM-driven PLC code generation with iterative refinement
  - Why study it: Alternative to multi-agent; shows single-model + prompt-engineering approach

- **NLPforSTGen (fine-tuned Structured Text generation)**
  - GitHub: https://github.com/racarr202/NLPforSTGen
  - What it does: Fine-tunes a model on NL → ST pairs specifically for Structured Text
  - Why it matters: Specialized models can outperform general LLMs; shows the training path if you want to build a custom PLC "brain"

- **ChatGPT for PLC/DCS Control Logic Generation (paper)**
  - ArXiv: https://arxiv.org/abs/2305.15809
  - What it covers: Empirical study of how well GPT-4 handles PLC logic from natural language; benchmarks and pitfalls

- **Control Logic Generation Prompts (curated library)**
  - GitHub: https://github.com/hkoziolek/control-logic-generation-prompts
  - What it is: A collection of carefully engineered prompts for generating ladder logic and ST from specifications
  - Why use it: Copy their prompt patterns; they've already solved a lot of the "how do I ask the LLM for good PLC code?" problem

- **GPT-4: AI Co-piloting for PLC Programming (LinkedIn article)**
  - Link: https://www.linkedin.com/pulse/gpt-4-ai-co-piloting-plc-programming-iec-61131-3-languages-hayat
  - What it covers: How to structure prompts for IEC 61131-3 languages; practical tips for code gen quality

- **Studio 5000 AI Assistant (MCP Server)**
  - Link: https://lobehub.com/mcp/rivie13-studio5000-ai-assistant
  - What it is: An MCP server that exposes a `generate_ladder_logic` tool; converts NL specs to ladder logic with verification
  - Why study it: Shows a production-ready integration of NL → PLC in a real development environment (Allen-Bradley); you can adapt the UX for your Telegram + Factory I/O setup

- **Copia's AI Copilot for PLC Code (commercial reference)**
  - YouTube: https://www.youtube.com/watch?v=Mgd2YD7eMqU
  - What it shows: Real-world UI/UX for "write PLC code in plain English"; watch how they present it to engineers
  - Why it's relevant: Gives you a reference for what "polished" looks like, even though you're building open source

### C. Factory I/O Integration & Simulation

**Official Factory I/O Documentation**

- **Factory I/O Web API (primary integration method)**
  - Link: https://docs.factoryio.com/manual/web-api/
  - What it is: HTTP/JSON interface to read/write Factory I/O tags and control logic
  - How to use: Your bridge service (Python, Node, etc.) calls `/api/tags` to list, then GET/PUT tag values
  - Why: Simplest path to connect your agent services to Factory I/O

- **Factory I/O OPC UA Support (alternative integration)**
  - Link: https://docs.factoryio.com/manual/drivers/opc/
  - What it is: Factory I/O as OPC client/server for industrial protocol-standard communication
  - How to use: Set up a Python OPC UA server on your VPS or a soft PLC, connect Factory I/O as client
  - Why: If you want to go the "protocol-correct" route; more overhead but integrates with real industrial stacks

- **Factory I/O SDK (if you need tighter coupling)**
  - GitHub: https://github.com/realgamessoftware/factoryio-sdk
  - What it is: .NET SDK for programmatic access to Factory I/O engine
  - Use case: Lower latency, memory-mapped access if you're running agents on the same Windows machine
  - Watchout: Requires .NET; your agent Python code would need a small wrapper

- **Factory I/O Installation & Trial Setup**
  - Link: https://docs.factoryio.com/installing/
  - What it covers: How to get a 30-day full-feature trial running on Windows
  - Next step: Start with the trial; it's enough to prove the integration pattern

- **Factory I/O Console (headless/scriptable control)**
  - Link: https://docs.factoryio.com/manual/console/
  - What it is: Headless command-line tool to automate Factory I/O scenes
  - Why useful: Can run Factory I/O on a VPS (Windows box) and control via CLI from your agent services

**Integration Guides & Examples**

- **RealPars: How to Connect CODESYS PLC to Factory I/O Using OPC UA (tutorial)**
  - Link: https://www.realpars.com/blog/codesys-factory-io-opc-ua
  - What it covers: Step-by-step OPC UA setup; shows the handshake between soft PLC and Factory I/O
  - Why study it: Use as a template for your own OPC configuration if you go that route

- **YouTube: How to Connect CODESYS PLC to Factory I/O Using OPC UA (video)**
  - Link: https://www.youtube.com/watch?v=dTwNGASMe84
  - What it shows: Visual walkthrough of the entire OPC connection process; easier than reading docs

- **PLC & RTU Simulator (GitHub example)**
  - Link: https://github.com/LiuYuancheng/PLC_and_RTU_Simulator
  - What it is: An open-source PLC simulator with Factory I/O hooks; shows how to wire a soft PLC
  - Why it matters: Reference architecture for "soft PLC on VPS talking to Factory I/O"

- **OPC UA Examples (RealTimeLogic)**
  - Link: https://github.com/RealTimeLogic/OPC-UA-Examples
  - What it is: Python/C examples of OPC UA client/server code
  - Use case: Copy the OPC UA boilerplate if you're building your own server

- **Factory I/O Community: Distance Learning & Remote Visualization (forum)**
  - Link: https://community.factoryio.com/t/an-idea-for-distance-learning/981
  - What it covers: Community discussion on running Factory I/O remotely, RDP/VNC tips
  - Why useful: Real-world Q&A on your exact problem (remote visualization)

### D. Remote Desktop & Visualization

**RDP / VNC for Remote Visibility**

- **SocketXP: IoT Remote Desktop (XRDP) Access**
  - Link: https://docs.socketxp.com/guide/iot-remote-desktop-xrdp-access/
  - What it covers: How to set up RDP on a Linux or Windows machine to see the desktop remotely
  - Relevance: If Factory I/O is on a small remote box, this is how you see the 3D scene from your laptop

- **Pinggy: Remotely Connect to IoT Devices Using VNC**
  - Link: https://pinggy.io/blog/remotely_connect_to_iol__using_vnc/
  - What it covers: VNC as an alternative to RDP; good for headless Linux + VNC server
  - Use case: If your Factory I/O Windows machine is behind a NAT, VNC + SSH tunnel can get you access

- **DEV Community: Remotely Connect to IoT Devices Using VNC (tutorial)**
  - Link: https://dev.to/lightningdev123/remotely-connect-to-iot-devices-using-vnc-4g9g
  - What it covers: Setup and troubleshooting for VNC over SSH

### E. CMMS & Industrial Maintenance Integration

**How the big players are doing it (reference)**

- **Maintenance World: Is Agentic AI Just a Fancy CMMS? (opinion piece)**
  - Link: https://maintenanceworld.com/2025/10/02/is-agentic-ai-just-a-fancy-cmms/
  - What it covers: Industry take on the gap between traditional CMMS and agentic systems
  - Why study it: Validates your thesis that no one is doing the CMMS-as-control-plane idea

- **Digiqt: AI Agents in Maintenance & Asset Management for Warehousing**
  - Link: https://digiqt.com/blog/ai-agents-in-maintenance-&-asset-management-for-warehousing/
  - What it covers: Real-world use of AI agents for predictive maintenance, asset tracking

- **KMS Technology: Agentic AI-Powered Industrial IoT (detailed case study)**
  - Link: https://kms-technology.com/blog/agentic-ai-powered-industrial-iot-modernizing-legacy-systems-for-autonomous-resilient-factories/
  - What it covers: How agentic systems can modernize legacy factories; agent-based orchestration of industrial systems

- **Plant Engineering: How to Use Generative AI for Plant Maintenance (6-step guide)**
  - Link: https://www.plantengineering.com/how-to-use-generative-ai-for-plant-maintenance-in-six-steps/
  - What it covers: Practical framework for deploying generative AI in maintenance workflows

- **MaintainX Blog: AI for Maintenance Data Analysis**
  - Link: https://www.getmaintainx.com/blog/ai-for-maintenance-data-analysis
  - What it covers: How a major CMMS vendor is using AI to analyze work-order history and predict failures

- **Augmentir Blog: Asset Hierarchy for Maintenance (asset metadata structure)**
  - Link: https://www.augmentir.com/blog/asset-hierarchy-maintenance
  - What it covers: How to structure asset data (machines, parts, dependencies) for maintenance optimization
  - Relevance: Shows the data model you should use for your CMMS metalayer

- **Innovapptive: Agentic AI Automates Maintenance Decision-Making (case study)**
  - Link: https://www.innovapptive.com/blog/how-agentic-ai-automates-maintenance-decision-making-task-execution
  - What it covers: Concrete example of agents making maintenance decisions; shows the decision loop

- **Mapcon: AI in CMMS for Predictive Maintenance**
  - Link: https://www.mapcon.com/blog/2025/11/ai-in-cmms-powering-predictive-maintenance
  - What it covers: CMMS + AI integration patterns for predictive maintenance

- **ChaiOne: Agentic AI in Manufacturing (ROI & production-floor wins)**
  - Link: https://www.chaione.com/blog/ai-manufacturing-operations-agentic-ai-production-floor-roi
  - What it covers: Business case for agentic AI in industrial settings; concrete production-floor improvements

### F. Document Ingestion & Knowledge Base Building

**For your manual-finder and PDF ingestion loops**

- **Your earlier research (Firecrawl & ScraperAPI for ingestion):**
  - Firecrawl: https://www.firecrawl.dev/ (web scraping + cleaning for PDFs and docs)
  - ScraperAPI: https://www.scraperapi.com/ (API-based web scraping for heavy sites)
  - Use case: When a tech needs a manual, your long-term agents use these to crawl manufacturer sites

---

## Part 4: Your Architecture Sketch (as you envision it)

1. **Telegram / Web UI (Short-term frontline)**
   - Tech snaps picture of nameplate or types a question
   - Short-term agent in your factory routes to KB lookup or escalates

2. **CMMS metalayer (Work-order spine)**
   - Every troubleshooting session → work order in the CMMS
   - Metadata: machine_id, session_id, user_id, timestamp, results, artifacts (PDFs, code snippets, etc.)
   - This history becomes the "long-term memory" for future agents on that machine

3. **Factory I/O simulation (Testing ground)**
   - Mid-term + long-term agents use Factory I/O to test generated PLC code
   - Write logic in English → agents generate ST → verify in Factory I/O → store verified code in CMMS
   - Each test run adds to the machine's knowledge base

4. **PLC code generation loop (Core innovation)**
   - Agents4PLC-style multi-agent: planner → coder → verifier
   - Input: "When tank fills above 50 PSI, close inlet valve and open drain"
   - Output: Verified Structured Text in Factory I/O
   - Feedback: Results stored in CMMS; next request on same machine is smarter

5. **VPS backbone (Agent brain)**
   - All three agent departments (short/mid/long term) live here
   - Background workers for crawling, ingestion, long-running research tasks
   - APIs exposed for Telegram bot, web UI, Factory I/O bridge, CMMS integration

---

## Part 5: What Claude Code Should Research & Recommend

Given all these resources, Claude Code should be able to:

1. **Evaluate which multi-agent orchestration pattern fits your stack best:**
   - OpenManus-style (long-running cloud VMs, task queues)?
   - Or simpler FastAPI + background workers on a VPS?
   - Trade-offs: complexity vs. scalability vs. your time budget

2. **Choose the best NL → PLC code generation approach:**
   - Use Agents4PLC's multi-agent loop (planner + coder + verifier)?
   - Or start simpler with prompt engineering + GPT-4 + manual verification?
   - How to adapt the approach for Factory I/O specifically?

3. **Design the Factory I/O bridge:**
   - Web API (simpler) or OPC UA (more "correct")?
   - Local Windows box or remote Windows VPS?
   - RDP/VNC for visualization?

4. **Propose the CMMS metalayer schema:**
   - How to structure work orders, session histories, per-machine KB?
   - How to feed results back into embeddings/vectors so agents improve?
   - Example: after fixing Machine 2143's pump issue, what does the CMMS record so the next agent can use it?

5. **Create a phased implementation plan:**
   - Phase 1 (this week): Factory I/O + simple bridge + test one PLC code gen loop
   - Phase 2: Integrate CMMS metalayer so results persist
   - Phase 3: Add long-term agents for crawling/ingestion
   - Phase 4: Hardening, observability, monitoring

6. **Identify what's novel about your approach:**
   - "No one is doing CMMS-as-control-plane for agentic maintenance"
   - How do you leverage that uniqueness for moat and market fit?

---

## Part 6: Resources for Implementation Decisions

Once Claude Code has analyzed the landscape, here are quick links for **concrete implementation:**

- **Factory I/O Quick Start:** Install → enable Web API → follow RealPars CODESYS tutorial for config
- **Agents4PLC Prompts:** Adapt their planner/verifier prompts from the paper for your domain
- **OpenManus Job Queue Pattern:** Use Redis + RQ or Celery for background workers on your VPS
- **FastAPI for Bridge:** Simple Python FastAPI service to translate between agents and Factory I/O Web API
- **CMMS Schema:** Start with a simple Postgres table: `work_orders(id, machine_id, session_id, code_generated, code_verified, result, created_at)`

---

## Summary: What You're Building

An **industrial maintenance CMMS powered by autonomous agents** that:
- **Stores history per machine** in the work-order metalayer
- **Generates PLC code in English** using multi-agent verification
- **Tests in real-time** using Factory I/O
- **Continuously improves** because every job teaches the system
- **Never been done before** at this level of integration

Your competitors (Siemens, Cognite, MaintainX, Augmentir) are still thinking in terms of "AI-powered dashboards" or "analytics layers." You're building the **agency layer** that owns the control plane.

---

## Next Steps for Claude Code

1. Read through the Agents4PLC paper and codebase to understand the multi-agent code generation pattern.
2. Review the OpenManus architecture and orchestration patterns.
3. Study the Factory I/O Web API documentation and pick a bridge language (Python FastAPI recommended).
4. Design the CMMS metalayer schema and how agents will query/update it.
5. Propose a 12-week phased implementation plan with concrete milestones.
6. Identify the three riskiest assumptions and how to de-risk them quickly.

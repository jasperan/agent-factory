# WORKSTREAM PROMPTS - Copy/Paste These Into Each Claude Code CLI Tab

---

## TAB 1: ATLAS CMMS (Computer 1, Tab 1)

```
You are working on the Rivet MVP sprint as part of a 6-instance parallel development team.

YOUR WORKSTREAM: atlas-cmms
YOUR WORKTREE: ../rivet-atlas
YOUR BRANCH: atlas-cmms

FIRST ACTIONS:
1. cd into your worktree: cd ../rivet-atlas (or the appropriate path)
2. Read sprint/CLAUDE_SHARED.md for full context
3. Read sprint/STATUS_BOARD.md for current state

YOUR RESPONSIBILITIES:
- Deploy Atlas CMMS to VPS (72.60.175.144) via Docker
- White-label it as "Rivet" (logo, colors, domain)
- Document all REST API endpoints
- Create user provisioning endpoint for Stripe webhook
- Set up cmms.rivet.io subdomain

PHASE 1 TASKS (Dec 26-28):
1. Clone Atlas CMMS repo into products/cmms/
2. Create docker-compose.yml for production
3. Deploy to VPS, verify it runs
4. Configure white-label branding
5. Document API endpoints in API_CONTRACTS.md

DEPENDENCIES:
- VPS access (should be available)
- Domain DNS (coordinate with WS-2)

After each task, update sprint/STATUS_BOARD.md with your progress.
When blocked, log in sprint/BLOCKERS.md and work on another task.

Start by exploring the existing codebase and checking STATUS_BOARD.md.
```

---

## TAB 2: LANDING + STRIPE (Computer 1, Tab 2)

```
You are working on the Rivet MVP sprint as part of a 6-instance parallel development team.

YOUR WORKSTREAM: landing-stripe
YOUR WORKTREE: ../rivet-landing
YOUR BRANCH: landing-stripe

FIRST ACTIONS:
1. cd into your worktree: cd ../rivet-landing
2. Read sprint/CLAUDE_SHARED.md for full context
3. Read sprint/STATUS_BOARD.md for current state

YOUR RESPONSIBILITIES:
- Create landing page at rivet.io
- Integrate Stripe checkout with 3 tiers (Basic $20, Pro $40, Enterprise $99)
- Build webhook handler for checkout.session.completed
- Trigger user creation in Atlas CMMS after payment

PHASE 1 TASKS (Dec 26-28):
1. Create products/landing/ directory
2. Use v0.dev or Framer to generate landing page
3. Set up Stripe test mode with 3 products
4. Create checkout flow (select tier → Stripe → success page)
5. Build webhook endpoint for payment confirmation

TECH CHOICE:
- Next.js for landing (or static HTML + Stripe JS)
- Stripe Checkout (hosted, not embedded)
- Webhook in Python (FastAPI) or Node

DEPENDENCIES:
- Atlas CMMS API for user creation (WS-1)
- Domain DNS setup

After each task, update sprint/STATUS_BOARD.md with your progress.
When blocked, log in sprint/BLOCKERS.md and work on another task.

Start now - landing page can be built independently.
```

---

## TAB 3: TELEGRAM VOICE (Computer 1, Tab 3)

```
You are working on the Rivet MVP sprint as part of a 6-instance parallel development team.

YOUR WORKSTREAM: telegram-voice
YOUR WORKTREE: ../rivet-telegram
YOUR BRANCH: telegram-voice

FIRST ACTIONS:
1. cd into your worktree: cd ../rivet-telegram
2. Read sprint/CLAUDE_SHARED.md for full context
3. Read sprint/STATUS_BOARD.md for current state

YOUR RESPONSIBILITIES:
- Extend existing telegram_bot.py for voice messages
- Integrate with Whisper for transcription
- Connect to intent-parser (WS-5) for understanding
- Create work orders in Atlas via API
- Handle clarification flow when intent is unclear

PHASE 1 TASKS (Dec 26-28):
1. Review existing telegram_bot.py - understand current architecture
2. Add voice message handler (download OGG, convert to WAV if needed)
3. Integrate Whisper API for transcription
4. Pass transcription to intent parser (mock for now)
5. Test end-to-end: voice → text → response

EXISTING CODE TO REUSE:
- telegram_bot.py (main bot logic)
- orchestrator.py (routing patterns)
- Agent factory patterns

DEPENDENCIES:
- Intent parser (WS-5) - can mock initially
- Atlas API (WS-1) - can mock initially

After each task, update sprint/STATUS_BOARD.md with your progress.
When blocked, log in sprint/BLOCKERS.md and work on another task.

Start by reading the existing telegram_bot.py code.
```

---

## TAB 4: CHAT WITH PRINT (Computer 2, Tab 1)

```
You are working on the Rivet MVP sprint as part of a 6-instance parallel development team.

YOUR WORKSTREAM: chat-with-print
YOUR WORKTREE: ../rivet-chat-print
YOUR BRANCH: chat-with-print

FIRST ACTIONS:
1. cd into your worktree: cd ../rivet-chat-print
2. Read sprint/CLAUDE_SHARED.md for full context
3. Read sprint/STATUS_BOARD.md for current state

YOUR RESPONSIBILITIES:
- Build Claude Vision wrapper for schematic analysis
- Create print metadata extraction (components, connections)
- Build Q&A interface for prints
- Integrate as feature in Atlas CMMS (feature-flagged by tier)

PHASE 1 TASKS (Dec 26-28):
1. Create products/chat-with-print/ directory
2. Build Claude Vision API wrapper (image → analysis)
3. Test with sample electrical schematic
4. Create print metadata schema (Pydantic model)
5. Build simple Q&A endpoint (POST /ask with image + question)

TECH STACK:
- Python + FastAPI for API
- Claude Vision (claude-sonnet-4-20250514)
- Pydantic for data models
- LangSmith for tracing

DEPENDENCIES:
- Claude API key (available)
- Sample schematics for testing (Stardust Racers print)

After each task, update sprint/STATUS_BOARD.md with your progress.
When blocked, log in sprint/BLOCKERS.md and work on another task.

Start by building the Claude Vision wrapper - it's independent.
```

---

## TAB 5: INTENT PARSER (Computer 2, Tab 2)

```
You are working on the Rivet MVP sprint as part of a 6-instance parallel development team.

YOUR WORKSTREAM: intent-parser
YOUR WORKTREE: ../rivet-intent
YOUR BRANCH: intent-parser

FIRST ACTIONS:
1. cd into your worktree: cd ../rivet-intent
2. Read sprint/CLAUDE_SHARED.md for full context
3. Read sprint/STATUS_BOARD.md for current state

YOUR RESPONSIBILITIES:
- Build LLM-based intent parser for voice transcriptions
- Detect intent type: create_work_order, query_asset, schematic_question, unclear
- Extract structured data (equipment, issue, priority)
- Generate clarification prompts when intent is ambiguous
- Handle off-topic or weird input gracefully

PHASE 1 TASKS (Dec 26-28):
1. Create products/intent-parser/ directory
2. Define ParsedIntent Pydantic model
3. Build Claude-based intent extraction
4. Create clarification prompt generator
5. Test with 20+ sample transcriptions

KEY REQUIREMENTS:
- If confidence < 0.7, ask for clarification
- Never guess equipment ID - ask if not clear
- Handle multilingual (English, Spanish, Portuguese)
- Log all parsing to LangSmith

SAMPLE INPUTS TO HANDLE:
- "The pump is making a weird noise" → create_work_order, ask which pump
- "What's connected to the brake solenoid?" → schematic_question
- "How's it going Claude" → unclear, ask what they need help with
- "La bomba hace ruido" → create_work_order (Spanish)

After each task, update sprint/STATUS_BOARD.md with your progress.
When blocked, log in sprint/BLOCKERS.md and work on another task.

Start building - this is independent work.
```

---

## TAB 6: INTEGRATION TESTING (Computer 2, Tab 3)

```
You are working on the Rivet MVP sprint as part of a 6-instance parallel development team.

YOUR WORKSTREAM: integration-testing
YOUR WORKTREE: ../rivet-integration
YOUR BRANCH: integration-testing

FIRST ACTIONS:
1. cd into your worktree: cd ../rivet-integration
2. Read sprint/CLAUDE_SHARED.md for full context
3. Read sprint/STATUS_BOARD.md for current state

YOUR RESPONSIBILITIES:
- Set up test harness for all components
- Pull from all branches and verify integration
- Write E2E tests for critical flows
- Coordinate merges to main branch
- Catch integration issues early

PHASE 1 TASKS (Dec 26-28):
1. Create tests/ directory structure
2. Set up pytest with fixtures
3. Write mock versions of each component for testing
4. Create CI/CD skeleton (GitHub Actions)
5. Document test procedures in TESTING.md

E2E TEST SCENARIOS:
1. User pays → account created in Atlas
2. Voice message → transcription → work order created
3. Print uploaded → metadata extracted → Q&A works
4. Intent unclear → clarification asked → user clarifies → action taken

MERGE PROTOCOL:
- Pull from all 5 other branches daily
- Run full test suite
- If all pass, merge to main
- If conflicts, document in BLOCKERS.md

After each task, update sprint/STATUS_BOARD.md with your progress.
When blocked, log in sprint/BLOCKERS.md and work on another task.

Start by setting up the test harness - it's foundational.
```

---

## HOW TO USE THESE PROMPTS

1. Open Claude Code CLI in each tab
2. Copy the relevant prompt above
3. Paste it as your first message
4. Claude will start working on that workstream

Each instance will:
- Read the shared context files
- Work on its assigned tasks
- Update STATUS_BOARD.md
- Log blockers

You manage by:
- Watching git commits from all branches
- Checking STATUS_BOARD.md periodically
- Resolving blockers as they arise
- Providing domain knowledge when asked

**Let's ship this.**

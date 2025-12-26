# CLAUDE_SHARED.md - Shared Context for All Instances
## Read This First Before Starting Any Work

---

## WHAT WE'RE BUILDING

**Rivet** - A voice-first CMMS with AI schematic understanding

```
Customer pays → Gets Atlas CMMS account → Uses Telegram bot for voice work orders
                                       → Uses Chat with Print for schematic Q&A
                                       → Gets predictive maintenance alerts (later)
```

---

## ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                         RIVET                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  rivet.io ────→ Stripe ────→ Atlas CMMS (cmms.rivet.io)    │
│  (landing)      (pay)        (the product)                  │
│                                                             │
│                              ┌──────────────────────────┐   │
│                              │ Atlas CMMS Features      │   │
│                              │ - Work orders            │   │
│                              │ - Asset management       │   │
│                              │ - PM schedules           │   │
│                              │ - Inventory              │   │
│                              │ - Chat with Print (Pro)  │   │
│                              └───────────┬──────────────┘   │
│                                          │ REST API         │
│                                          ▼                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              RIVET AI LAYER (our value-add)            │ │
│  │                                                        │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐   │ │
│  │  │ Telegram Bot│  │Intent Parser│  │ Claude Vision│   │ │
│  │  │             │  │             │  │              │   │ │
│  │  │ Voice input │──│ Understand  │  │ Read prints  │   │ │
│  │  │ Photo OCR   │  │ Ask clarify │  │ Answer Q's   │   │ │
│  │  └─────────────┘  └─────────────┘  └──────────────┘   │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## EXISTING CODEBASE TO REUSE

The `/agent_factory/` directory has working code from RivetCEO Bot:

| File | What It Does | Reuse For |
|------|--------------|-----------|
| `telegram_bot.py` | Telegram message handling | Extend for voice + Atlas |
| `orchestrator.py` | 4-route orchestrator | Adapt for intent routing |
| `agent_factory/ocr/` | Photo OCR pipeline | Nameplate reading |
| `agent_factory/knowledge/` | RAG infrastructure | Equipment docs |
| `config/` | Configuration management | Shared settings |

**DO NOT rebuild from scratch.** Extend existing code.

---

## SHARED CONFIGURATION

All instances use these environment variables:

```bash
# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://...

# Redis
REDIS_URL=redis://...

# Claude API
ANTHROPIC_API_KEY=sk-ant-...

# Telegram
TELEGRAM_BOT_TOKEN=...

# Atlas CMMS (after deployment)
ATLAS_API_URL=https://cmms.rivet.io/api
ATLAS_ADMIN_TOKEN=...

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=rivet-mvp
```

---

## API CONTRACTS (Cross-Workstream Interfaces)

### 1. Intent Parser Output (intent-parser → telegram-voice)

```python
class ParsedIntent:
    intent_type: Literal["create_work_order", "query_asset", "schematic_question", "unclear"]
    confidence: float  # 0.0 to 1.0
    
    # For create_work_order
    equipment_id: Optional[str]
    equipment_name: Optional[str]  # If ID not found
    issue_description: Optional[str]
    priority: Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]]
    
    # For schematic_question
    question: Optional[str]
    asset_context: Optional[str]
    
    # If clarification needed
    clarification_needed: bool
    clarification_prompt: Optional[str]  # What to ask user
```

### 2. Atlas API Wrapper (atlas-cmms → all)

```python
class AtlasClient:
    def create_work_order(self, data: WorkOrderCreate) -> WorkOrder
    def get_asset(self, asset_id: str) -> Asset
    def get_asset_files(self, asset_id: str) -> List[AssetFile]
    def upload_asset_file(self, asset_id: str, file: bytes, filename: str) -> AssetFile
    def create_user(self, email: str, role: str) -> User
    def list_work_orders(self, filters: dict) -> List[WorkOrder]
```

### 3. Chat with Print (chat-with-print → atlas-cmms)

```python
class PrintAnalyzer:
    def analyze_print(self, image_bytes: bytes) -> PrintMetadata
    def answer_question(self, image_bytes: bytes, question: str) -> str
    
class PrintMetadata:
    components: List[str]
    connections: List[dict]
    ratings: dict
    raw_text: str
```

### 4. Stripe → Atlas User Flow (landing-stripe → atlas-cmms)

```python
# Webhook payload after successful payment
{
    "event": "checkout.session.completed",
    "customer_email": "tech@example.com",
    "subscription_tier": "pro",  # basic, pro, enterprise
    "stripe_customer_id": "cus_xxx"
}

# Atlas user creation
{
    "email": "tech@example.com",
    "role": "TECHNICIAN",
    "subscription_tier": "pro",
    "stripe_customer_id": "cus_xxx"
}
```

---

## CODING STANDARDS

1. **Python 3.10+** for all backend code
2. **Type hints** on all functions
3. **Pydantic** for data validation
4. **pytest** for tests (minimum: happy path + one failure)
5. **LangSmith tracing** on all Claude API calls
6. **Structured logging** (JSON format)
7. **No hardcoded secrets** - use environment variables

---

## GIT WORKFLOW

```bash
# Your branch only
git add .
git commit -m "WS-X: [component] what you did"
git push origin your-branch

# Example commit messages:
# "WS-1: [atlas] Docker compose working, white-label config added"
# "WS-3: [telegram] Voice message handler complete, needs intent parser"
# "WS-5: [intent] Clarification prompts for ambiguous input"
```

Commit message prefix by workstream:
- WS-1: atlas-cmms
- WS-2: landing-stripe
- WS-3: telegram-voice
- WS-4: chat-with-print
- WS-5: intent-parser
- WS-6: integration-testing

---

## COMMUNICATION VIA FILES

Since we can't talk directly, we communicate via:

1. **STATUS_BOARD.md** - Update after each task
2. **BLOCKERS.md** - Log blockers immediately
3. **API_CONTRACTS.md** - Document interfaces (this section)
4. **Git commits** - Be verbose

**Check these files every hour.** They're your only link to other instances.

---

## FEATURE TIER LOGIC

```python
TIERS = {
    "basic": {
        "price": 20,  # per tech per month
        "features": ["work_orders", "assets", "pm_schedules", "telegram_voice"]
    },
    "pro": {
        "price": 40,
        "features": ["basic_features", "chat_with_print", "priority_support"]
    },
    "enterprise": {
        "price": 99,
        "features": ["pro_features", "predictive_ai", "api_access", "sso"]
    }
}

def has_feature(user, feature):
    tier = user.subscription_tier
    return feature in TIERS[tier]["features"]
```

---

## CRITICAL REMINDERS

1. **Don't rebuild what exists** - Check existing code first
2. **Use LangSmith** - All Claude calls must be traced
3. **Update STATUS_BOARD.md** - Others depend on knowing your progress
4. **Ask for clarification via intent parser** - Never guess user intent
5. **Test locally first** - Don't break production
6. **Commit often** - Small, atomic commits

---

## IF YOU GET STUCK

1. Read the existing codebase in `/agent_factory/`
2. Check `STATUS_BOARD.md` for related work
3. Check `BLOCKERS.md` for known issues
4. Log your blocker in `BLOCKERS.md`
5. Work on a different task from your backlog
6. Check back in 30 minutes

---

## LET'S BUILD THIS

We have until Jan 10 to ship. That's 15 days with 6 parallel workstreams.
That's effectively 90 dev-days of work compressed into 2 weeks.

**Move fast. Ship it. Make millions.**

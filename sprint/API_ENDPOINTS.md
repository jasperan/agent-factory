# RIVET MVP - API ENDPOINTS TO BUILD

## 1. STRIPE WEBHOOK API (WS-2 Builds)

**Endpoint:** `POST /api/webhooks/stripe`

**Purpose:** Receive Stripe payment events, provision users in Atlas

```python
# /products/landing/src/pages/api/webhooks/stripe.ts (Next.js)
# OR /agent_factory/rivet_pro/api/stripe_webhook.py (FastAPI)

@app.post("/api/webhooks/stripe")
async def stripe_webhook(request: Request):
    """
    Receives:
    - checkout.session.completed → Create user in Atlas
    - customer.subscription.updated → Update tier
    - customer.subscription.deleted → Downgrade/cancel
    - invoice.payment_failed → Notify user
    
    Signature verification: Stripe-Signature header
    """
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    
    event = stripe.Webhook.construct_event(
        payload, sig_header, STRIPE_WEBHOOK_SECRET
    )
    
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        await provision_user(
            email=session["customer_email"],
            stripe_id=session["customer"],
            tier=session["metadata"]["tier"]
        )
    
    return {"status": "ok"}
```

---

## 2. USER PROVISIONING API (WS-1 Builds)

**Endpoint:** `POST /api/users/provision`

**Purpose:** Create user in Atlas CMMS after Stripe payment

```python
# /agent_factory/integrations/atlas/api.py

class UserProvisionRequest(BaseModel):
    email: str
    stripe_customer_id: str
    subscription_tier: Literal["basic", "pro", "enterprise"]
    
class UserProvisionResponse(BaseModel):
    user_id: str
    atlas_user_id: str
    telegram_link: str  # Deep link to start bot

@app.post("/api/users/provision")
async def provision_user(req: UserProvisionRequest) -> UserProvisionResponse:
    """
    1. Create user in Atlas CMMS
    2. Store mapping: stripe_id → atlas_user_id
    3. Generate Telegram deep link
    4. Send welcome email
    """
    atlas_user = await atlas_client.create_user(
        email=req.email,
        role="technician",
        metadata={"stripe_id": req.stripe_customer_id, "tier": req.subscription_tier}
    )
    
    return UserProvisionResponse(
        user_id=str(uuid4()),
        atlas_user_id=atlas_user["id"],
        telegram_link=f"https://t.me/RivetCEO_bot?start={atlas_user['id']}"
    )
```

---

## 3. CHAT WITH PRINT API (WS-4 Builds - Optional Standalone)

**If you want Chat with Print as a standalone web service:**

**Endpoints:**
- `POST /api/print/upload` - Upload schematic
- `POST /api/print/analyze` - Get initial analysis
- `POST /api/print/ask` - Ask question about print
- `GET /api/print/{print_id}` - Get print metadata

```python
# /agent_factory/rivet_pro/api/print_api.py

@app.post("/api/print/upload")
async def upload_print(
    file: UploadFile,
    user_id: str = Depends(get_current_user)
) -> PrintUploadResponse:
    """Upload and analyze a schematic."""
    # Save file
    path = save_uploaded_file(file, user_id)
    
    # Initial analysis
    analyzer = PrintAnalyzer()
    metadata = await analyzer.extract_metadata(path)
    
    return PrintUploadResponse(
        print_id=str(uuid4()),
        filename=file.filename,
        analysis=metadata.raw_analysis,
        components=metadata.components
    )

@app.post("/api/print/ask")
async def ask_about_print(
    print_id: str,
    question: str,
    user_id: str = Depends(get_current_user)
) -> PrintAnswerResponse:
    """Ask a question about an uploaded print."""
    # Check tier
    user = await get_user(user_id)
    if user.tier not in ["pro", "enterprise"]:
        raise HTTPException(402, "Upgrade to Pro for Chat with Print")
    
    # Get print path
    print_path = get_print_path(print_id, user_id)
    
    # Answer question
    analyzer = PrintAnalyzer()
    answer = await analyzer.answer_question(print_path, question)
    
    return PrintAnswerResponse(answer=answer)
```

---

## 4. WORK ORDER API (WS-1 Builds - Wraps Atlas)

**Purpose:** Wrapper around Atlas CMMS work order API for our bot

**Endpoints:**
- `POST /api/work-orders` - Create work order
- `GET /api/work-orders/{id}` - Get work order
- `PUT /api/work-orders/{id}` - Update work order
- `GET /api/work-orders?user_id=xxx` - List user's work orders

```python
# /agent_factory/integrations/atlas/api.py

class WorkOrderCreate(BaseModel):
    title: str
    description: Optional[str]
    asset_id: str
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    created_by: str  # Telegram user ID or Atlas user ID
    source: Literal["telegram_voice", "telegram_text", "web", "api"] = "api"

@app.post("/api/work-orders")
async def create_work_order(
    req: WorkOrderCreate,
    user_id: str = Depends(get_current_user)
) -> WorkOrderResponse:
    """Create a work order in Atlas CMMS."""
    # Map our user to Atlas user
    atlas_user = await get_atlas_user(user_id)
    
    # Create in Atlas
    work_order = await atlas_client.create_work_order({
        "title": req.title,
        "description": req.description,
        "asset": {"id": req.asset_id},
        "priority": req.priority,
        "assignedTo": [atlas_user["id"]],
        "category": {"name": "Corrective"},
    })
    
    # Log to LangSmith
    log_work_order_created(work_order, source=req.source)
    
    return WorkOrderResponse(
        id=work_order["id"],
        title=work_order["title"],
        status="OPEN",
        asset_name=work_order["asset"]["name"]
    )
```

---

## 5. ASSET LOOKUP API (WS-1 Builds)

**Purpose:** Search/lookup equipment for intent clarification

**Endpoints:**
- `GET /api/assets?q=pump` - Search assets
- `GET /api/assets/{id}` - Get asset details
- `GET /api/assets/{id}/prints` - Get asset schematics

```python
@app.get("/api/assets")
async def search_assets(
    q: str,
    user_id: str = Depends(get_current_user),
    limit: int = 10
) -> List[AssetSummary]:
    """
    Search assets by name, location, or ID.
    Used by intent clarification when user says "the pump".
    """
    # Get user's organization
    org_id = await get_user_org(user_id)
    
    # Search Atlas
    assets = await atlas_client.search_assets(
        query=q,
        organization_id=org_id,
        limit=limit
    )
    
    return [
        AssetSummary(
            id=a["id"],
            name=a["name"],
            location=a["location"]["name"] if a.get("location") else None,
            type=a["category"]["name"] if a.get("category") else None
        )
        for a in assets
    ]
```

---

## 6. HEALTH/STATUS API (WS-6 Builds)

**Purpose:** Monitoring and health checks

```python
@app.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/status")
async def system_status():
    """Detailed system status."""
    return {
        "services": {
            "atlas_cmms": await check_atlas_connection(),
            "database": await check_db_connection(),
            "stripe": await check_stripe_connection(),
            "telegram_bot": await check_bot_status()
        },
        "metrics": {
            "work_orders_today": await count_work_orders_today(),
            "active_users": await count_active_users(),
            "api_latency_ms": get_avg_latency()
        }
    }
```

---

## API ARCHITECTURE SUMMARY

```
┌─────────────────────────────────────────────────────────────┐
│                      EXTERNAL TRAFFIC                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    RIVET API GATEWAY                         │
│                   (FastAPI or Next.js)                       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   /api/      │  │  /api/       │  │  /api/       │       │
│  │  webhooks/   │  │  users/      │  │  work-       │       │
│  │  stripe      │  │  provision   │  │  orders      │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   /api/      │  │  /api/       │  │  /health     │       │
│  │   print/     │  │  assets      │  │  /status     │       │
│  │   *          │  │              │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Atlas CMMS   │     │   Stripe     │     │  Telegram    │
│ (Self-hosted)│     │   (Cloud)    │     │   (Cloud)    │
└──────────────┘     └──────────────┘     └──────────────┘
```

---

## WHO BUILDS WHAT

| API Endpoint | Workstream | Priority |
|--------------|------------|----------|
| `/api/webhooks/stripe` | WS-2 (Landing) | P0 - Day 1 |
| `/api/users/provision` | WS-1 (Atlas) | P0 - Day 1 |
| `/api/work-orders` | WS-1 (Atlas) | P0 - Day 1 |
| `/api/assets` | WS-1 (Atlas) | P1 - Day 2 |
| `/api/print/*` | WS-4 (Print) | P1 - Day 2 |
| `/health`, `/status` | WS-6 (Integration) | P2 - Day 3 |

---

## FRAMEWORK CHOICE

**Option A: Single FastAPI Backend**
- All APIs in one Python service
- Easier to deploy
- Recommended for MVP

**Option B: Split (Next.js + FastAPI)**
- Next.js for landing page + Stripe webhook
- FastAPI for everything else
- More complex but separates concerns

**Recommendation:** Start with **Option A** (single FastAPI) for speed, split later if needed.

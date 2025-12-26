# API CONTRACTS - Cross-Workstream Interfaces
## Document Interfaces HERE Before Implementing

All workstreams must agree on these interfaces. Update this file when you define a new interface.

---

## 1. INTENT PARSER (WS-5 → WS-3)

### Endpoint
```
POST /api/parse-intent
```

### Request
```json
{
  "transcription": "The main pump is making a grinding noise",
  "language": "en",
  "user_id": "user_123",
  "context": {
    "recent_assets": ["pump_001", "pump_002"],
    "recent_work_orders": ["wo_456"]
  }
}
```

### Response
```json
{
  "intent_type": "create_work_order",
  "confidence": 0.85,
  "equipment_id": null,
  "equipment_candidates": [
    {"id": "pump_001", "name": "Main Floor Pump", "match_score": 0.9},
    {"id": "pump_002", "name": "Basement Pump", "match_score": 0.7}
  ],
  "issue_description": "grinding noise",
  "priority": "MEDIUM",
  "clarification_needed": true,
  "clarification_prompt": "Which pump are you referring to - Main Floor Pump or Basement Pump?"
}
```

### Intent Types
- `create_work_order` - User wants to log maintenance work
- `query_asset` - User asking about equipment status/history
- `schematic_question` - User asking about a print/schematic
- `update_work_order` - User updating existing work order
- `unclear` - Can't determine intent, need clarification
- `off_topic` - Not maintenance related

---

## 2. ATLAS CMMS API (WS-1 → All)

### Work Orders

#### Create Work Order
```
POST /api/v1/work-orders
Authorization: Bearer {token}
```

```json
{
  "title": "Pump grinding noise",
  "description": "Main floor pump making grinding noise, needs inspection",
  "asset_id": "asset_123",
  "priority": "HIGH",
  "assigned_to": ["user_456"],
  "due_date": "2025-01-02T10:00:00Z",
  "source": "telegram_voice",
  "metadata": {
    "transcription_id": "trans_789",
    "telegram_user_id": "tg_user_001"
  }
}
```

Response:
```json
{
  "id": "wo_001",
  "title": "Pump grinding noise",
  "status": "OPEN",
  "created_at": "2025-12-26T15:00:00Z",
  "...": "..."
}
```

#### List Work Orders
```
GET /api/v1/work-orders?asset_id=xxx&status=OPEN&limit=20
```

### Assets

#### Get Asset
```
GET /api/v1/assets/{asset_id}
```

Response:
```json
{
  "id": "asset_123",
  "name": "Main Floor Pump",
  "location": "Building A, Floor 1",
  "category": "HVAC",
  "status": "OPERATIONAL",
  "files": [
    {
      "id": "file_001",
      "name": "pump_schematic.pdf",
      "url": "/api/v1/assets/asset_123/files/file_001",
      "type": "schematic"
    }
  ]
}
```

#### Upload File to Asset
```
POST /api/v1/assets/{asset_id}/files
Content-Type: multipart/form-data

file: [binary]
type: "schematic" | "manual" | "photo"
```

### Users

#### Create User (from Stripe webhook)
```
POST /api/v1/users/provision
Authorization: Bearer {admin_token}
```

```json
{
  "email": "tech@example.com",
  "name": "John Tech",
  "role": "TECHNICIAN",
  "subscription_tier": "pro",
  "stripe_customer_id": "cus_xxx",
  "telegram_user_id": "tg_user_001"
}
```

---

## 3. CHAT WITH PRINT (WS-4)

### Analyze Print
```
POST /api/analyze-print
Content-Type: multipart/form-data

file: [binary PDF or image]
```

Response:
```json
{
  "print_id": "print_001",
  "components": [
    {"name": "Q-Relay", "type": "relay", "location": "top-left"},
    {"name": "Contactor CRA", "type": "contactor", "location": "center"},
    {"name": "MCB", "type": "circuit_breaker", "location": "bottom"}
  ],
  "connections": [
    {"from": "Q-Relay", "to": "Contactor CRA", "wire": "L1"},
    {"from": "MCB", "to": "Q-Relay", "wire": "N"}
  ],
  "ratings": {
    "voltage": "230V",
    "current": "10A"
  },
  "raw_text": "...",
  "confidence": 0.92
}
```

### Ask Question About Print
```
POST /api/ask-print
```

```json
{
  "print_id": "print_001",
  "question": "What happens if the Q-Relay fails?",
  "include_image": true
}
```

Response:
```json
{
  "answer": "If the Q-Relay fails in the open position, the Contactor CRA will not energize, which means the main load circuit will remain de-energized. This is a fail-safe design. If it fails closed, the contactor may remain energized even when it shouldn't.",
  "confidence": 0.88,
  "referenced_components": ["Q-Relay", "Contactor CRA"],
  "visual_reference": "See the Q-Relay in the top-left of the schematic, connected via L1 to the contactor."
}
```

---

## 4. STRIPE WEBHOOK (WS-2 → WS-1)

### Webhook Payload (Stripe → Our Server)
```json
{
  "type": "checkout.session.completed",
  "data": {
    "object": {
      "id": "cs_xxx",
      "customer": "cus_xxx",
      "customer_email": "tech@example.com",
      "metadata": {
        "tier": "pro"
      },
      "subscription": "sub_xxx"
    }
  }
}
```

### Our Handler Calls Atlas
```python
# After receiving webhook
atlas_client.create_user({
    "email": customer_email,
    "role": "TECHNICIAN",
    "subscription_tier": metadata["tier"],
    "stripe_customer_id": customer_id
})
```

---

## 5. TELEGRAM MESSAGES (WS-3)

### Voice Message Flow
```
User sends voice message
    ↓
Bot downloads OGG file
    ↓
Convert to WAV (if needed)
    ↓
POST /api/transcribe (Whisper)
    ↓
POST /api/parse-intent (WS-5)
    ↓
If clarification_needed:
    Reply with clarification_prompt
    Wait for response
    ↓
POST /api/v1/work-orders (Atlas)
    ↓
Reply with confirmation
```

### Response Format
```python
def format_work_order_confirmation(wo: WorkOrder) -> str:
    return f"""✅ Work order created!

📋 {wo.title}
🔧 Equipment: {wo.asset_name}
⚡ Priority: {wo.priority}
📅 Due: {wo.due_date}

WO #{wo.id}"""
```

---

## ADDING NEW INTERFACES

When you need to define a new interface between workstreams:

1. Add it to this document with request/response examples
2. Commit: `git add sprint/API_CONTRACTS.md && git commit -m "WS-X: added Y interface"`
3. Push to origin
4. Notify the consuming workstream in STATUS_BOARD.md

**The interface is the contract. Implement to the contract. Test against the contract.**

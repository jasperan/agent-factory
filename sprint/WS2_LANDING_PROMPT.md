# WORKSTREAM 2: LANDING PAGE + STRIPE CHECKOUT
# Computer 1, Tab 2
# Copy everything below this line into Claude Code CLI

You are WS-2 (Landing + Stripe) in a 6-instance parallel development sprint for Rivet MVP.

## AUTONOMOUS MODE SETTINGS
- Auto-accept all file edits
- Auto-accept bash commands except: rm -rf, sudo, DROP, DELETE
- Commit after each completed task
- If context feels long (5+ tasks done), checkpoint immediately

## YOUR IDENTITY
- Workstream: WS-2
- Branch: landing-stripe
- Focus: Landing page and Stripe checkout flow

## FIRST ACTIONS (Do These Now)
1. Check if worktree exists: `git worktree list`
2. If not, create it: `git worktree add ../rivet-landing landing-stripe`
3. cd into worktree
4. Read this entire prompt before starting

## CRITICAL: STRIPE ALREADY EXISTS!
Look at: `/agent_factory/rivet_pro/stripe_integration.py`
```python
# Already configured:
PRICE_IDS = {
    "pro_monthly": "price_xxx",
    "enterprise_monthly": "price_yyy",
}
PRO_PRICE = 29.00
ENTERPRISE_PRICE = 499.00
```

You are NOT building Stripe from scratch. You're building:
1. Public landing page
2. Checkout flow that uses existing StripeManager
3. Webhook handler to call Atlas user provisioning

## YOUR TASKS (In Order)

### Task 1: Create Landing Page Structure
Create: `/products/landing/`
```
landing/
├── package.json
├── src/
│   ├── pages/
│   │   ├── index.tsx          # Landing page
│   │   ├── pricing.tsx        # Pricing page
│   │   └── api/
│   │       └── webhooks/
│   │           └── stripe.ts  # Webhook handler
│   ├── components/
│   │   ├── Hero.tsx
│   │   ├── Features.tsx
│   │   ├── Pricing.tsx
│   │   └── CTA.tsx
│   └── styles/
└── public/
    └── images/
```

Use Next.js or Astro (your choice for speed).

### Task 2: Landing Page Content
Hero section:
- Headline: "Voice-First CMMS with AI Schematic Understanding"
- Subhead: "Field technicians create work orders by voice. Ask questions about any equipment print. Get predictive maintenance alerts."
- CTA: "Start Free Trial" → Stripe checkout

Features section:
- Voice Work Orders (Telegram bot)
- Chat with Your Print (Claude vision)
- Predictive Maintenance (coming soon)
- Multi-language (English, Spanish, Portuguese)

### Task 3: Pricing Component
Three tiers (match existing Stripe config):
```
Basic - $20/tech/month
- Work orders via Telegram
- Voice transcription
- 5 equipment prints

Pro - $40/tech/month  
- Everything in Basic
- Unlimited prints
- Chat with Print (AI schematic Q&A)
- Priority support

Enterprise - $99/tech/month
- Everything in Pro
- Predictive maintenance
- API access
- SSO/SAML
- Dedicated support
```

Each tier has "Get Started" button → Stripe Checkout

### Task 4: Stripe Checkout Integration
Create checkout flow:
```typescript
// /pages/api/create-checkout-session.ts
import Stripe from 'stripe';

export default async function handler(req, res) {
  const { tier, email } = req.body;
  
  const priceId = {
    basic: process.env.STRIPE_PRICE_BASIC,
    pro: process.env.STRIPE_PRICE_PRO,
    enterprise: process.env.STRIPE_PRICE_ENTERPRISE,
  }[tier];

  const session = await stripe.checkout.sessions.create({
    mode: 'subscription',
    payment_method_types: ['card'],
    line_items: [{ price: priceId, quantity: 1 }],
    success_url: `${process.env.NEXT_PUBLIC_URL}/success?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${process.env.NEXT_PUBLIC_URL}/pricing`,
    customer_email: email,
    metadata: { tier }
  });

  res.json({ url: session.url });
}
```

### Task 5: Webhook Handler
Create: `/pages/api/webhooks/stripe.ts`
```typescript
// On checkout.session.completed:
// 1. Extract customer email, tier from session
// 2. Call Atlas API to create user (WS-1 provides this)
// 3. Send welcome email / Telegram message
```

This connects to WS-1's `AtlasClient.provision_user_from_stripe()`

### Task 6: Success Page
Create `/pages/success.tsx`:
- "Welcome to Rivet!"
- Next steps:
  1. Open Telegram, search @RivetCEO_bot
  2. Send /start
  3. You're ready to create your first voice work order

## COMMIT PROTOCOL
After EACH task:
```bash
# Generate system map
tree -L 3 --dirsfirst -I 'node_modules|__pycache__|.git|venv|.next' > .tree_snapshot.txt

# Commit with map
git add -A
git commit -m "WS-2: [component] description

SYSTEM MAP:
$(cat .tree_snapshot.txt | head -50)"

git push origin landing-stripe
```

## DEPENDENCIES
- NEEDS from WS-1: `AtlasClient.provision_user_from_stripe()` endpoint
- PROVIDES to WS-3: User tier info in database after payment

## ENV VARS NEEDED
```
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_BASIC=price_xxx
STRIPE_PRICE_PRO=price_xxx
STRIPE_PRICE_ENTERPRISE=price_xxx
NEXT_PUBLIC_URL=https://rivet.io
ATLAS_API_URL=https://cmms.rivet.io/api
```

## UPDATE STATUS
After each task, create/update: `/sprint/STATUS_WS2.md`

## IF BLOCKED ON WS-1
Mock the Atlas API call:
```typescript
// Temporary mock until WS-1 ready
async function provisionUser(email: string, tier: string) {
  console.log(`[MOCK] Would provision ${email} with tier ${tier}`);
  return { success: true, userId: 'mock_' + Date.now() };
}
```

## START NOW
Begin with Task 1. Create the landing page structure.

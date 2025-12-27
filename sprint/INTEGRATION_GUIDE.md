# Rivet MVP - WS-1 + WS-2 Integration Guide

**Status**: Both workstreams code-complete, ready for deployment
**Last Updated**: 2025-12-26

## Overview

This guide covers the integration of:
- **WS-1**: Backend API (FastAPI + Stripe + PostgreSQL)
- **WS-2**: Frontend Landing Page (Next.js + Tailwind)

Both are ready to deploy and connect.

## Current Status

### WS-1 Backend ✅ Code Complete
- **Location**: `agent-factory-ws1-backend/` (worktree)
- **Branch**: `rivet-backend`
- **Status**: Ready for deployment
- **Docs**: `agent_factory/api/README.md`, `sprint/STATUS_WS1.md`

**Key Files:**
- `agent_factory/api/.env.example` - Environment template
- `agent_factory/api/main.py` - FastAPI app with CORS config
- `agent_factory/api/routers/stripe.py` - Stripe checkout (complete)
- `agent_factory/api/config.py` - Settings with cors_origins

**What Works:**
- ✅ Stripe checkout endpoint (`POST /api/checkout/create`)
- ✅ Health check with database status
- ✅ Environment-based CORS configuration
- ✅ User provisioning (database)
- ⏳ Work orders (stubbed, not needed for MVP)

### WS-2 Frontend ✅ Code Complete
- **Location**: `products/landing/` (main directory)
- **Branch**: `rivet-frontend` / `rivet-bot`
- **Status**: Ready for Vercel deployment
- **Docs**: `products/landing/README.md`, `products/landing/VERCEL_DEPLOY.md`, `sprint/STATUS_WS2.md`

**Key Files:**
- `products/landing/vercel.json` - Vercel configuration
- `products/landing/VERCEL_DEPLOY.md` - Deployment guide
- `products/landing/app/pricing/page.tsx` - Pricing page
- `products/landing/app/api/checkout/route.ts` - Backend API client

**What Works:**
- ✅ Landing page with Hero, Features, How It Works, CTA
- ✅ Pricing page with 3 tiers
- ✅ Checkout flow (calls backend API)
- ✅ Success page with onboarding
- ✅ Mobile responsive

## Deployment Workflow (1-2 hours total)

### Step 1: Deploy Backend (WS-1) - 45 minutes

**Navigate to Backend Worktree:**
```bash
cd "C:\Users\hharp\OneDrive\Desktop\agent-factory-ws1-backend"
```

**Choose Deployment Platform:**

**Option A: Railway (Recommended)**
1. Visit [railway.app](https://railway.app)
2. New Project → Import from GitHub
3. Select repository → Choose `rivet-backend` branch
4. Configure:
   - Root directory: `agent_factory/api`
   - Start command: Auto-detected (uvicorn)
5. Add environment variables (see below)
6. Deploy → Get URL

**Option B: Render**
1. Visit [render.com](https://render.com)
2. New Web Service
3. Connect GitHub → `rivet-backend` branch
4. Settings:
   - Build: `pip install poetry && poetry install`
   - Start: `poetry run uvicorn agent_factory.api.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables
6. Deploy → Get URL

**Backend Environment Variables:**
```env
# Required
STRIPE_SECRET_KEY=sk_test_xxx           # From Stripe dashboard
STRIPE_PRICE_BASIC=price_xxx_basic      # From Stripe products
STRIPE_PRICE_PRO=price_xxx_pro
STRIPE_PRICE_ENTERPRISE=price_xxx_enterprise
NEON_DB_URL=postgresql://user:pass@host/db  # From Neon
APP_URL=https://your-frontend.vercel.app    # Will get in Step 2
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000

# Optional
STRIPE_WEBHOOK_SECRET=whsec_xxx         # For webhook verification
LANGCHAIN_API_KEY=lsv2_xxx              # For LangSmith tracing
```

**Test Backend:**
```bash
curl https://your-backend.railway.app/health
# Should return: {"status": "healthy", "database": {"healthy": true}}
```

**Save Backend URL:** You'll need this for Step 2.

### Step 2: Deploy Frontend (WS-2) - 30 minutes

**Navigate to Frontend:**
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory\products\landing"
```

**Deploy to Vercel:**

**Option A: Vercel Dashboard (Easiest)**
1. Visit [vercel.com/new](https://vercel.com/new)
2. Import Git Repository → Select your repo
3. Configure:
   - **Root Directory**: `products/landing`
   - **Framework**: Next.js (auto-detected)
4. Deploy (will fail initially due to missing env vars)
5. Add environment variables (see below)
6. Redeploy

**Option B: Vercel CLI**
```bash
npm i -g vercel
vercel login
vercel --prod
```

**Frontend Environment Variables (Vercel):**
```env
NEXT_PUBLIC_STRIPE_PRICE_BASIC=price_xxx_basic
NEXT_PUBLIC_STRIPE_PRICE_PRO=price_xxx_pro
NEXT_PUBLIC_STRIPE_PRICE_ENTERPRISE=price_xxx_enterprise
API_URL=https://your-backend.railway.app         # From Step 1
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

**Save Frontend URL:** You'll need this for Step 3.

### Step 3: Connect Backend to Frontend - 15 minutes

**Update Backend CORS:**
1. Go to Railway/Render dashboard
2. Update environment variable:
   ```
   CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
   ```
3. Update:
   ```
   APP_URL=https://your-frontend.vercel.app
   ```
4. Redeploy backend

**Update Frontend API URL (if using localhost):**
1. Go to Vercel dashboard
2. Update:
   ```
   API_URL=https://your-backend.railway.app
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app
   ```
3. Redeploy frontend

### Step 4: Test End-to-End - 10 minutes

**Test Checklist:**

1. **Backend Health:**
   ```bash
   curl https://your-backend.railway.app/health
   ```
   ✅ Should return: `{"status": "healthy", ...}`

2. **Frontend Loads:**
   - Visit: `https://your-frontend.vercel.app`
   - ✅ Should see landing page

3. **Pricing Page:**
   - Visit: `https://your-frontend.vercel.app/pricing`
   - ✅ Should see 3 pricing tiers

4. **Checkout Flow:**
   - Enter email: `test@example.com`
   - Click "Start Free Trial" on Pro tier
   - ✅ Should redirect to Stripe checkout
   - Use test card: `4242 4242 4242 4242`
   - ✅ Should redirect to `/success` page

5. **Success Page:**
   - ✅ Should see onboarding instructions
   - ✅ Should see Telegram bot link

**If Any Step Fails:** See Troubleshooting section below.

## Environment Variables Summary

### Backend (Railway/Render)

| Variable | Required | Example | Where to Get |
|----------|----------|---------|--------------|
| `STRIPE_SECRET_KEY` | ✅ Yes | `sk_test_xxx` | Stripe Dashboard → API keys |
| `STRIPE_PRICE_BASIC` | ✅ Yes | `price_xxx` | Stripe Dashboard → Products |
| `STRIPE_PRICE_PRO` | ✅ Yes | `price_xxx` | Stripe Dashboard → Products |
| `STRIPE_PRICE_ENTERPRISE` | ✅ Yes | `price_xxx` | Stripe Dashboard → Products |
| `NEON_DB_URL` | ✅ Yes | `postgresql://...` | Neon Dashboard → Connection string |
| `APP_URL` | ✅ Yes | `https://your-frontend.vercel.app` | Vercel deployment URL |
| `CORS_ORIGINS` | ✅ Yes | `https://your-frontend.vercel.app,http://localhost:3000` | Your frontend URL |
| `STRIPE_WEBHOOK_SECRET` | ⚪ Optional | `whsec_xxx` | Stripe Webhooks (for production) |
| `LANGCHAIN_API_KEY` | ⚪ Optional | `lsv2_xxx` | LangSmith (for tracing) |

### Frontend (Vercel)

| Variable | Required | Example | Where to Get |
|----------|----------|---------|--------------|
| `NEXT_PUBLIC_STRIPE_PRICE_BASIC` | ✅ Yes | `price_xxx` | Stripe Dashboard → Products |
| `NEXT_PUBLIC_STRIPE_PRICE_PRO` | ✅ Yes | `price_xxx` | Stripe Dashboard → Products |
| `NEXT_PUBLIC_STRIPE_PRICE_ENTERPRISE` | ✅ Yes | `price_xxx` | Stripe Dashboard → Products |
| `API_URL` | ✅ Yes | `https://your-backend.railway.app` | Backend deployment URL |
| `NEXT_PUBLIC_API_URL` | ✅ Yes | `https://your-backend.railway.app` | Backend deployment URL |

## Troubleshooting

### CORS Error

**Symptom:** Browser console shows "Access-Control-Allow-Origin" error

**Fix:**
1. Verify backend `CORS_ORIGINS` includes frontend URL
2. Check backend logs for "CORS origins: [...]"
3. Ensure no trailing slashes in URLs
4. Redeploy backend after CORS changes

**Test:**
```bash
curl -H "Origin: https://your-frontend.vercel.app" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     https://your-backend.railway.app/api/checkout/create
```

### Checkout Fails

**Symptom:** "Failed to fetch" or "Network error"

**Fix:**
1. Check frontend `API_URL` is correct
2. Verify backend is healthy: `/health` endpoint
3. Check browser Network tab for exact error
4. Verify CORS is configured correctly

**Symptom:** "Invalid tier: pro. Price ID not configured"

**Fix:**
1. Verify backend has `STRIPE_PRICE_PRO` set
2. Check Stripe dashboard for correct price ID
3. Redeploy backend after adding variable

### Build Fails

**Frontend Build Error:**
- Ensure `package.json` and `package-lock.json` are committed
- Check all imports are correct
- Verify environment variables are set in Vercel

**Backend Build Error:**
- Ensure `pyproject.toml` is committed
- Check Python version (3.10+)
- Verify all dependencies in poetry.lock

### Database Connection Failed

**Symptom:** Health check shows `"database": {"healthy": false}`

**Fix:**
1. Verify `NEON_DB_URL` is correct
2. Check Neon dashboard for database status
3. Ensure IP whitelist includes deployment platform IPs
4. Test connection: `psql $NEON_DB_URL`

## Architecture Diagram

```
┌─────────────────────┐
│   User's Browser    │
└──────────┬──────────┘
           │
           │ HTTPS
           ▼
┌─────────────────────┐
│  Vercel (Frontend)  │  ← WS-2
│  Next.js Landing    │
│  - /                │
│  - /pricing         │
│  - /success         │
└──────────┬──────────┘
           │
           │ API Calls
           ▼
┌─────────────────────┐
│ Railway (Backend)   │  ← WS-1
│ FastAPI + Stripe    │
│ - /api/checkout     │
│ - /health           │
└──────┬──────┬───────┘
       │      │
       │      │
       ▼      ▼
   ┌────┐  ┌──────┐
   │Neon│  │Stripe│
   │ DB │  │ API  │
   └────┘  └──────┘
```

## Quick Reference

### Backend URLs
- Health: `https://your-backend.railway.app/health`
- Docs: `https://your-backend.railway.app/docs`
- Checkout: `POST https://your-backend.railway.app/api/checkout/create`

### Frontend URLs
- Home: `https://your-frontend.vercel.app`
- Pricing: `https://your-frontend.vercel.app/pricing`
- Success: `https://your-frontend.vercel.app/success`

### Documentation
- **WS-1 Backend**: `agent-factory-ws1-backend/agent_factory/api/README.md`
- **WS-1 Status**: `agent-factory-ws1-backend/sprint/STATUS_WS1.md`
- **WS-2 Frontend**: `products/landing/README.md`
- **WS-2 Deploy**: `products/landing/VERCEL_DEPLOY.md`
- **WS-2 Status**: `sprint/STATUS_WS2.md`

## Next Steps After Deployment

1. ✅ Both deployed and integrated
2. ⏳ Test with real Stripe test cards
3. ⏳ Set up Stripe webhooks for production
4. ⏳ Configure custom domain (optional)
5. ⏳ Enable monitoring/analytics
6. ⏳ Start WS-3 (Telegram bot) in parallel

## Support

**Get Stripe Test Keys:**
1. [Stripe Dashboard](https://dashboard.stripe.com)
2. Developers → API keys → "Test mode" toggle
3. Copy "Secret key" (starts with `sk_test_`)

**Get Database:**
1. [Neon](https://neon.tech) - Free PostgreSQL
2. Create project → Copy connection string

**Deploy Platforms:**
- Backend: [Railway](https://railway.app) or [Render](https://render.com)
- Frontend: [Vercel](https://vercel.com)

All platforms have free tiers sufficient for MVP testing.

---

**Both WS-1 and WS-2 are code-complete and ready for deployment!**

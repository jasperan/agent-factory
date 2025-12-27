# Rivet Landing Page - Vercel Deployment Guide

## Quick Deploy (5 minutes)

### Step 1: Push Code to GitHub

If not already pushed:
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
git add products/landing
git commit -m "WS-2: Frontend ready for Vercel deployment"
git push origin rivet-frontend  # or your current branch
```

### Step 2: Deploy to Vercel

**Option A: Vercel Dashboard (Recommended)**

1. Go to [vercel.com/new](https://vercel.com/new)
2. Click "Import Git Repository"
3. Select your GitHub repository
4. Configure:
   - **Root Directory**: `products/landing`
   - **Framework Preset**: Next.js (auto-detected)
   - Leave build settings as default
5. Click "Deploy"

**Option B: Vercel CLI**

```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory\products\landing"
npm i -g vercel
vercel login
vercel --prod
```

### Step 3: Add Environment Variables

In Vercel Dashboard → Your Project → Settings → Environment Variables:

```
NEXT_PUBLIC_STRIPE_PRICE_BASIC=price_xxx_basic
NEXT_PUBLIC_STRIPE_PRICE_PRO=price_xxx_pro
NEXT_PUBLIC_STRIPE_PRICE_ENTERPRISE=price_xxx_enterprise
API_URL=http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Note**: Start with localhost URLs, then update with backend deployment URL later.

### Step 4: Redeploy

After adding environment variables:
- Dashboard: Settings → Deployments → Click "..." → Redeploy
- CLI: `vercel --prod`

### Step 5: Get Deployment URL

Your site will be live at: `https://your-project.vercel.app`

## Connect to Backend

### Once Backend is Deployed

1. Deploy WS-1 backend to Railway/Render (see `agent-factory-ws1-backend/agent_factory/api/README.md`)
2. Get backend URL (e.g., `https://your-backend.railway.app`)
3. Update Vercel environment variables:
   - `API_URL` = `https://your-backend.railway.app`
   - `NEXT_PUBLIC_API_URL` = `https://your-backend.railway.app`
4. Redeploy frontend

### Update Backend CORS

In backend `.env`:
```env
CORS_ORIGINS=https://your-project.vercel.app,http://localhost:3000
```

Redeploy backend.

## Test End-to-End

1. Visit `https://your-project.vercel.app`
2. Go to `/pricing` page
3. Enter email and click "Start Free Trial"
4. Should redirect to Stripe checkout
5. Complete test payment (use test card: `4242 4242 4242 4242`)
6. Should redirect to `/success` page
7. Should see onboarding instructions

## Troubleshooting

### Build Fails on Vercel

**Error**: "Cannot find module..."
- **Fix**: Ensure all dependencies in `package.json`
- **Fix**: Check `package-lock.json` is committed

**Error**: "Environment variable not found"
- **Fix**: Add variables in Vercel dashboard
- **Fix**: Redeploy after adding variables

### Checkout Fails

**Error**: "Network error" or "Failed to fetch"
- **Fix**: Check `API_URL` environment variable
- **Fix**: Verify backend is deployed and healthy
- **Fix**: Check CORS configuration in backend

**Error**: "Invalid tier: pro. Price ID not configured"
- **Fix**: Set `STRIPE_PRICE_*` variables in backend
- **Fix**: Verify price IDs are correct in Stripe dashboard

### CORS Error

**Error**: "Access to fetch... has been blocked by CORS policy"
- **Fix**: Add frontend URL to backend `CORS_ORIGINS`
- **Fix**: Ensure backend is deployed with correct CORS config
- **Fix**: Check browser console for exact blocked URL

## Environment Variables Reference

### Frontend (Vercel)

| Variable | Purpose | Example |
|----------|---------|---------|
| `NEXT_PUBLIC_STRIPE_PRICE_BASIC` | Basic tier Stripe price ID | `price_1ABC123basic` |
| `NEXT_PUBLIC_STRIPE_PRICE_PRO` | Pro tier Stripe price ID | `price_1ABC123pro` |
| `NEXT_PUBLIC_STRIPE_PRICE_ENTERPRISE` | Enterprise tier Stripe price ID | `price_1ABC123enterprise` |
| `API_URL` | Backend API URL (server-side) | `https://backend.railway.app` |
| `NEXT_PUBLIC_API_URL` | Backend API URL (client-side) | `https://backend.railway.app` |

**Note**: Variables with `NEXT_PUBLIC_` prefix are exposed to the browser.

### Backend (Railway/Render)

| Variable | Purpose |
|----------|---------|
| `CORS_ORIGINS` | Allowed frontend origins (comma-separated) |
| `STRIPE_SECRET_KEY` | Stripe API secret key |
| `STRIPE_PRICE_BASIC` | Basic tier price ID (backend validation) |
| `STRIPE_PRICE_PRO` | Pro tier price ID |
| `STRIPE_PRICE_ENTERPRISE` | Enterprise tier price ID |
| `NEON_DB_URL` | PostgreSQL database connection string |
| `APP_URL` | Frontend URL (for redirects) |

## Deployment Checklist

### Frontend (Vercel)
- [ ] Code pushed to GitHub
- [ ] Project imported to Vercel
- [ ] Root directory set to `products/landing`
- [ ] Environment variables added
- [ ] Deployment successful
- [ ] Site accessible at Vercel URL

### Backend (Railway/Render)
- [ ] Code deployed to Railway/Render
- [ ] Environment variables configured
- [ ] Health endpoint returns 200
- [ ] CORS includes frontend URL
- [ ] Stripe keys configured

### Integration
- [ ] Frontend `API_URL` points to backend
- [ ] Backend `CORS_ORIGINS` includes frontend
- [ ] Backend `APP_URL` set to frontend
- [ ] Checkout flow tested end-to-end
- [ ] Success page displays correctly

## Custom Domain (Optional)

### Add Custom Domain to Vercel

1. Vercel Dashboard → Your Project → Settings → Domains
2. Enter your domain (e.g., `rivet.com`)
3. Configure DNS:
   - Type: `A` Record
   - Name: `@` (or subdomain)
   - Value: `76.76.21.21` (Vercel's IP)
4. Wait for DNS propagation (5-60 minutes)
5. Vercel will auto-provision SSL certificate

### Update Environment Variables

After adding custom domain:

**Backend:**
```env
CORS_ORIGINS=https://rivet.com,https://your-project.vercel.app,http://localhost:3000
APP_URL=https://rivet.com
```

**Frontend:** No changes needed (environment variables are domain-agnostic)

## Monitoring

### Vercel Analytics

Enable in Vercel Dashboard:
1. Project → Analytics tab
2. Enable Web Analytics
3. View real-time traffic and performance

### Error Tracking

View deployment logs:
1. Vercel Dashboard → Deployments
2. Click deployment
3. View build logs and runtime logs

### Performance

Check Lighthouse scores:
1. Run audit: `npx lighthouse https://your-project.vercel.app`
2. Or use Chrome DevTools → Lighthouse tab

## Cost

**Vercel:**
- Free Tier: 100GB bandwidth, unlimited deployments
- Pro Tier: $20/month for custom domains and analytics

**Railway (Backend):**
- Free Tier: $5 credit/month
- Paid: Usage-based, typically $5-10/month

**Stripe:**
- No monthly fees
- 2.9% + $0.30 per transaction

## Support

- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **Next.js Docs**: [nextjs.org/docs](https://nextjs.org/docs)
- **Deployment Help**: See `DEPLOYMENT.md` for detailed guides

## Next Steps

1. ✅ Deploy frontend to Vercel
2. ⏳ Deploy backend to Railway/Render (see WS-1 guide)
3. ⏳ Connect frontend to backend
4. ⏳ Test end-to-end checkout flow
5. ⏳ (Optional) Add custom domain
6. ⏳ (Optional) Enable analytics

Frontend deployment is independent - you can deploy it now and connect the backend later.

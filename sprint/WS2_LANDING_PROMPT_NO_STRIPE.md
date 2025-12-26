# WORKSTREAM 2: LANDING PAGE (NO STRIPE - MVP)
# Computer 1, Tab 2
# Copy everything below this line into Claude Code CLI

You are WS-2 (Landing Page) in a 6-instance parallel development sprint for Rivet MVP.

## AUTONOMOUS MODE SETTINGS
- Auto-accept all file edits
- Auto-accept bash commands except: rm -rf, sudo, DROP, DELETE
- Commit after each completed task
- If context feels long (5+ tasks done), checkpoint immediately

## YOUR IDENTITY
- Workstream: WS-2
- Branch: landing-stripe (name kept for consistency)
- Focus: Landing page with waitlist/early access signup

## FIRST ACTIONS (Do These Now)
1. Check if worktree exists: `git worktree list`
2. If not, create it: `git worktree add ../rivet-landing landing-stripe`
3. cd into worktree
4. Read this entire prompt before starting

## SCOPE CHANGE: NO STRIPE FOR MVP
We're skipping payment integration for now. Instead:
- Landing page with "Get Early Access" CTA
- Direct link to Telegram bot
- Optional: Simple email waitlist

## YOUR TASKS (In Order)

### Task 1: Create Landing Page Structure
Create: `/products/landing/`

Use Next.js or Astro (your choice). Simple structure:
```
landing/
├── package.json
├── src/
│   ├── pages/
│   │   ├── index.tsx          # Landing page
│   │   └── success.tsx        # After signup
│   ├── components/
│   │   ├── Hero.tsx
│   │   ├── Features.tsx
│   │   ├── HowItWorks.tsx
│   │   └── CTA.tsx
│   └── styles/
└── public/
    └── images/
```

### Task 2: Hero Section
```
Headline: "Voice-First CMMS for Field Technicians"

Subhead: "Create work orders by voice. Ask AI about any schematic. 
Works on Telegram - no app to install."

CTA Button: "Get Early Access" → links to Telegram bot
Secondary: "See How It Works" → scrolls to demo section
```

### Task 3: Features Section
Three feature cards:

**1. Voice Work Orders**
- Icon: 🎤
- "Describe the problem, we create the work order"
- "Works in English, Spanish, Portuguese"

**2. Chat with Your Print**
- Icon: 📊
- "Upload any schematic, ask questions"
- "AI understands electrical, mechanical, P&ID diagrams"

**3. Works on Telegram**
- Icon: 📱
- "No app to download"
- "Works on any phone, even offline"

### Task 4: How It Works Section
Three steps with illustrations/icons:

1. **Open Telegram** → Search @RivetCEO_bot
2. **Send a voice message** → "The main pump is making a grinding noise"
3. **Work order created** → Automatically logged with equipment details

### Task 5: CTA Section (Bottom)
```
"Ready to modernize your maintenance?"

[Get Early Access - Free] → https://t.me/RivetCEO_bot?start=beta

"No credit card required. Free during beta."
```

### Task 6: Simple Analytics (Optional)
Add basic tracking to know people are visiting:
- Plausible Analytics (privacy-friendly, free tier)
- Or just console.log for now

### Task 7: Deploy to Vercel/Netlify
```bash
# If using Next.js
npx vercel

# Or Netlify
npx netlify deploy --prod
```

Get a live URL we can share.

## DESIGN GUIDELINES
- Clean, professional, not flashy
- Mobile-first (technicians use phones)
- Fast loading (field = bad internet)
- Colors: Industrial blue/orange or keep it simple black/white
- No stock photos of people in hard hats (overused)

## DO NOT BUILD
- ❌ Stripe integration (later)
- ❌ User accounts/login (Telegram handles identity)
- ❌ Pricing page (free for now)
- ❌ Complex forms (just Telegram link)

## COMMIT PROTOCOL
After EACH task:
```bash
tree -L 3 --dirsfirst -I 'node_modules|__pycache__|.git|venv|.next' > .tree_snapshot.txt
git add -A
git commit -m "WS-2: [component] description

SYSTEM MAP:
$(cat .tree_snapshot.txt | head -50)"
git push origin landing-stripe
```

## SUCCESS CRITERIA
- [ ] Landing page loads fast (<2s)
- [ ] Clear value proposition above fold
- [ ] One-click path to Telegram bot
- [ ] Mobile responsive
- [ ] Deployed to public URL

## UPDATE STATUS
After each task, create/update: `/sprint/STATUS_WS2.md`

## START NOW
Begin with Task 1. Create the landing page structure.

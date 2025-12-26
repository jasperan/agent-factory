# MULTI-LAPTOP DEVELOPMENT SETUP

## The Problem
- Project files live on Laptop 1
- You want to run parallel Claude CLI instances on Laptop 2
- `.env` file has secrets that shouldn't be in git

## Solution Options (Choose One)

---

## OPTION 1: OneDrive Sync (Easiest - You Already Have This!)

Your project is already in OneDrive:
```
C:\Users\hharp\OneDrive\Desktop\Agent Factory
```

**On Laptop 2:**
1. Sign into the same Microsoft account
2. OneDrive will sync the folder automatically
3. Everything including `.env` syncs
4. ⚠️ **Warning:** File conflicts if both edit same file

**Best for:** Same person, different machines, not simultaneous edits to same files

---

## OPTION 2: Git Clone + Secure .env Copy (Recommended for Parallel Dev)

### Step 1: Push repo to GitHub (if not already)
```bash
# On Laptop 1
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
git remote add origin https://github.com/YOUR_USERNAME/agent-factory.git
git push -u origin main
```

### Step 2: Clone on Laptop 2
```bash
# On Laptop 2
cd ~/Desktop
git clone https://github.com/YOUR_USERNAME/agent-factory.git
cd agent-factory
```

### Step 3: Copy .env securely (choose one method)

**Method A: Encrypted email to yourself**
- Zip the .env with password
- Email to yourself
- Download on Laptop 2

**Method B: Secure cloud storage**
- Put .env in OneDrive/Google Drive (NOT in repo folder)
- Download on Laptop 2
- Copy to project folder

**Method C: Use a password manager**
- Store secrets in 1Password/Bitwarden
- Create .env manually on Laptop 2

**Method D: Environment secrets file (best)**
Create `~/.rivet-secrets` on both laptops:
```bash
# ~/.rivet-secrets (same content on both machines)
export STRIPE_SECRET_KEY=sk_test_xxx
export ANTHROPIC_API_KEY=sk-ant-xxx
export OPENAI_API_KEY=sk-xxx
# ... etc
```

Then in each terminal session:
```bash
source ~/.rivet-secrets
```

### Step 4: Create worktrees on BOTH laptops
```bash
# Laptop 1 - Workstreams 1, 2, 3
git worktree add ../rivet-atlas atlas-cmms
git worktree add ../rivet-landing landing-stripe
git worktree add ../rivet-telegram telegram-voice

# Laptop 2 - Workstreams 4, 5, 6
git worktree add ../rivet-chat-print chat-with-print
git worktree add ../rivet-intent intent-parser
git worktree add ../rivet-integration integration-testing
```

### Step 5: Sync changes via git
```bash
# When done with a task, push
git add -A && git commit -m "WS-X: description" && git push

# On other laptop, pull to see changes
git fetch --all
```

---

## OPTION 3: GitHub Codespaces (Cloud Dev Environment)

Use GitHub Codespaces for Laptop 2's workstreams:

1. Go to your repo on GitHub
2. Click "Code" → "Codespaces" → "Create codespace"
3. Add secrets in GitHub Settings → Secrets → Codespaces
4. Run Claude CLI in the codespace

**Pros:** No local setup, secrets stored securely in GitHub
**Cons:** Requires internet, may have latency

---

## OPTION 4: Docker Dev Container (Portable)

Create a dev container that both laptops can run:

```dockerfile
# .devcontainer/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
# Secrets passed via docker run -e or .env file
```

```bash
# Run on any laptop
docker run -it --env-file .env -v $(pwd):/app rivet-dev
```

---

## RECOMMENDED SETUP FOR YOU

Since you're using OneDrive AND want parallel dev:

### Laptop 1 (Primary - Windows)
- Keep project in OneDrive folder
- Run WS-1, WS-2, WS-3 (Atlas, Landing, Voice)
- Push to GitHub frequently

### Laptop 2 (Secondary)
- Clone from GitHub (NOT OneDrive - avoid conflicts)
- Copy .env once via secure method
- Run WS-4, WS-5, WS-6 (Print, Intent, Integration)
- Push to GitHub frequently

### Sync Protocol
```bash
# Before starting work (both laptops)
git fetch --all
git pull origin <your-branch>

# After completing a task (both laptops)
git add -A
git commit -m "WS-X: task description"
git push origin <your-branch>

# If conflict, integration branch (WS-6) resolves
```

---

## QUICK SETUP SCRIPT FOR LAPTOP 2

Run this on Laptop 2 to get started:

```bash
#!/bin/bash
# laptop2_setup.sh

# 1. Clone repo
cd ~/Desktop
git clone https://github.com/YOUR_USERNAME/agent-factory.git rivet
cd rivet

# 2. Create .env (paste your secrets)
cat > .env << 'EOF'
# Paste your .env contents here
# Or copy from Laptop 1 via secure method
EOF

# 3. Fetch all branches
git fetch --all

# 4. Create worktrees for Laptop 2 workstreams
git worktree add ../rivet-chat-print chat-with-print
git worktree add ../rivet-intent intent-parser  
git worktree add ../rivet-integration integration-testing

# 5. Install dependencies
pip install -r requirements.txt

echo "✅ Laptop 2 ready for WS-4, WS-5, WS-6"
```

---

## .ENV SYNC CHECKLIST

Before starting on Laptop 2, verify these are set:

```bash
# Required for Rivet MVP
✅ STRIPE_SECRET_KEY
✅ STRIPE_PUBLISHABLE_KEY
✅ STRIPE_WEBHOOK_SECRET
✅ STRIPE_PRICE_BASIC
✅ STRIPE_PRICE_PRO
✅ STRIPE_PRICE_ENTERPRISE
✅ ANTHROPIC_API_KEY
✅ OPENAI_API_KEY
✅ TELEGRAM_BOT_TOKEN
✅ DATABASE_URL (or NEON_DB_URL)
✅ LANGSMITH_API_KEY
```

---

## SECURITY REMINDER

⚠️ **NEVER commit .env to git!**

Verify .gitignore includes:
```
.env
.env.*
!.env.example
```

If you accidentally committed secrets:
1. Rotate ALL keys immediately
2. Use `git filter-branch` or BFG to remove from history
3. Force push (coordinate with team)

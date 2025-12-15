# GitHub Secrets Setup for Automated VPS Deployment

**Repository:** https://github.com/Mikecranesync/Agent-Factory
**Workflow:** `.github/workflows/deploy-vps.yml`

---

## 🔐 Required Secrets

You need to configure 3 secrets in your GitHub repository for automated deployment:

1. **VPS_SSH_KEY** - SSH private key for VPS access
2. **VPS_ENV_FILE** - Complete .env file contents
3. **TELEGRAM_BOT_TOKEN** - For deployment notifications (already have)
4. **TELEGRAM_ADMIN_CHAT_ID** - Your Telegram user ID (already have)

---

## 📋 Step-by-Step Setup

### 1. Generate SSH Key for GitHub Actions

Run these commands on your **LOCAL machine** (Windows PowerShell or Git Bash):

```bash
# Generate new SSH key pair
ssh-keygen -t ed25519 -C "github-actions@agent-factory" -f ~/.ssh/vps_deploy_key -N ""

# This creates two files:
# - ~/.ssh/vps_deploy_key (PRIVATE key - for GitHub Secrets)
# - ~/.ssh/vps_deploy_key.pub (PUBLIC key - for VPS)
```

**Location:**
- Windows: `C:\Users\hharp\.ssh\vps_deploy_key`
- Git Bash: `~/.ssh/vps_deploy_key`

---

### 2. Add Public Key to VPS

Copy the PUBLIC key to your VPS:

```bash
# Option A: Copy/paste manually
cat ~/.ssh/vps_deploy_key.pub
# Copy the output

# SSH into VPS
ssh root@72.60.175.144

# Add key to authorized_keys
echo "YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Test the key works
exit
ssh -i ~/.ssh/vps_deploy_key root@72.60.175.144
# Should connect without password
```

**Option B: Use ssh-copy-id (easier)**
```bash
ssh-copy-id -i ~/.ssh/vps_deploy_key.pub root@72.60.175.144
```

---

### 3. Add Secrets to GitHub

Go to: https://github.com/Mikecranesync/Agent-Factory/settings/secrets/actions

#### Secret 1: VPS_SSH_KEY

```bash
# Get the PRIVATE key content
cat ~/.ssh/vps_deploy_key
# On Windows PowerShell:
# Get-Content C:\Users\hharp\.ssh\vps_deploy_key -Raw
```

**Copy the ENTIRE output** (including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`)

1. Click "New repository secret"
2. Name: `VPS_SSH_KEY`
3. Value: Paste the private key
4. Click "Add secret"

**Example format:**
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
... (many lines) ...
-----END OPENSSH PRIVATE KEY-----
```

#### Secret 2: VPS_ENV_FILE

```bash
# Get the .env.vps file content
cat .env.vps
# On Windows:
# Get-Content .env.vps -Raw
```

1. Click "New repository secret"
2. Name: `VPS_ENV_FILE`
3. Value: Paste the ENTIRE .env.vps file contents
4. Click "Add secret"

**This should include:**
- `TELEGRAM_BOT_TOKEN=8264955123:AAHLiOZmJXrOepJ82XGs_pcGwk6BIfEgGAs`
- `SUPABASE_URL=https://mggqgrxwumnnujojndub.supabase.co`
- All other environment variables from `.env.vps`

#### Secret 3: TELEGRAM_BOT_TOKEN (probably already exists)

1. Click "New repository secret"
2. Name: `TELEGRAM_BOT_TOKEN`
3. Value: `8264955123:AAHLiOZmJXrOepJ82XGs_pcGwk6BIfEgGAs`
4. Click "Add secret"

#### Secret 4: TELEGRAM_ADMIN_CHAT_ID (probably already exists)

1. Click "New repository secret"
2. Name: `TELEGRAM_ADMIN_CHAT_ID`
3. Value: `8445149012`
4. Click "Add secret"

---

## ✅ Verify Secrets Are Set

Go to: https://github.com/Mikecranesync/Agent-Factory/settings/secrets/actions

You should see:
- ✅ `VPS_SSH_KEY`
- ✅ `VPS_ENV_FILE`
- ✅ `TELEGRAM_BOT_TOKEN`
- ✅ `TELEGRAM_ADMIN_CHAT_ID`

---

## 🚀 Test the Workflow

### Option 1: Manual Trigger

1. Go to: https://github.com/Mikecranesync/Agent-Factory/actions
2. Click "Deploy RIVET Pro to VPS" workflow
3. Click "Run workflow" button
4. Click green "Run workflow" button
5. Watch the deployment live!

### Option 2: Automatic Trigger (on git push)

The workflow will auto-trigger when you push code that changes:
- `agent_factory/**` (any Python code)
- `telegram_bot.py` (main bot file)
- `deploy_rivet_pro.sh` (deployment script)
- `rivet-pro.service` (systemd service)
- `.github/workflows/deploy-vps.yml` (this workflow)

```bash
# Make a small change
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"

# Commit and push
git add .
git commit -m "test: Trigger automated deployment"
git push origin main

# Watch deployment at:
# https://github.com/Mikecranesync/Agent-Factory/actions
```

---

## 📊 What the Workflow Does

When triggered, GitHub Actions will:

1. **Checkout code** from GitHub repository
2. **Setup SSH** using your private key
3. **Copy .env file** from GitHub Secrets to VPS
4. **Connect to VPS via SSH** and run:
   - `git pull origin main` (get latest code)
   - `./deploy_rivet_pro.sh` (run deployment script)
   - Verify health endpoint responds
5. **Send Telegram notification** to your admin chat
   - ✅ Success: "RIVET Pro deployed successfully"
   - ❌ Failure: "RIVET Pro deployment FAILED"

**Deployment takes ~2-3 minutes.**

---

## 🐛 Troubleshooting

### Error: "Permission denied (publickey)"

**Problem:** SSH key not properly configured

**Solution:**
```bash
# On VPS
ssh root@72.60.175.144
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
cat ~/.ssh/authorized_keys  # Verify public key is there
```

### Error: ".env file not found"

**Problem:** VPS_ENV_FILE secret not set or empty

**Solution:**
1. Go to GitHub Secrets
2. Edit `VPS_ENV_FILE`
3. Make sure it contains the FULL .env.vps file
4. Re-run workflow

### Error: "Bot failed to start"

**Problem:** Missing dependencies or invalid .env

**Solution:**
```bash
# SSH into VPS
ssh root@72.60.175.144
cd /root/Agent-Factory

# Check logs
tail -f logs/bot-error.log

# Verify .env exists
cat .env | head -5

# Manually run deployment
./deploy_rivet_pro.sh
```

### Workflow doesn't trigger on push

**Problem:** Changed files don't match workflow `paths` filter

**Solution:**
- Push changes to `agent_factory/**` or `telegram_bot.py`
- Or use manual trigger via "Run workflow" button

---

## 🔒 Security Best Practices

### ✅ DO:
- Keep SSH private key in GitHub Secrets only
- Rotate SSH keys periodically
- Use dedicated deploy key (not your personal SSH key)
- Restrict VPS firewall to allow SSH from GitHub Actions IPs (optional)

### ❌ DON'T:
- Commit SSH private keys to repository
- Share SSH keys via email/Slack
- Use the same SSH key for multiple services
- Store secrets in plain text files

---

## 📈 Monitoring Deployments

### GitHub Actions Dashboard
**URL:** https://github.com/Mikecranesync/Agent-Factory/actions

Shows:
- ✅ Success/failure status
- ⏱️ Deployment duration
- 📝 Full deployment logs
- 🔄 Re-run failed deployments

### Telegram Notifications

You'll receive messages like:

**Success:**
```
✅ RIVET Pro deployed successfully to VPS!

Commit: 1457eff
Author: Mikecranesync
Health: http://72.60.175.144:9876/health
```

**Failure:**
```
❌ RIVET Pro deployment FAILED!

Commit: 1457eff
Author: Mikecranesync

Check GitHub Actions for details.
```

### Health Endpoint

Check bot status anytime:
```bash
curl http://72.60.175.144:9876/health
```

**Expected response:**
```json
{
  "status": "running",
  "pid": 12345,
  "uptime_seconds": 3600
}
```

---

## 🎯 Quick Command Reference

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/vps_deploy_key -N ""

# Copy public key to VPS
ssh-copy-id -i ~/.ssh/vps_deploy_key.pub root@72.60.175.144

# Test SSH connection
ssh -i ~/.ssh/vps_deploy_key root@72.60.175.144

# View private key (for GitHub Secret)
cat ~/.ssh/vps_deploy_key

# View .env file (for GitHub Secret)
cat .env.vps

# Trigger deployment manually
# Go to: https://github.com/Mikecranesync/Agent-Factory/actions
# Click "Run workflow"

# Check deployment logs
ssh root@72.60.175.144
tail -f /root/Agent-Factory/logs/bot.log

# Check bot health
curl http://72.60.175.144:9876/health
```

---

## 🎉 Success!

Once secrets are configured:

1. **Push code to main branch** → Auto-deploys to VPS
2. **Receive Telegram notification** → Deployment status
3. **Bot auto-restarts** → Zero downtime
4. **Health check passes** → Verified working

**Your workflow:** Code → Push → Auto-Deploy → Done! 🚀

---

**Next:** See `VPS_DEPLOYMENT_GUIDE.md` for manual deployment or `DEPLOY_TO_VPS.md` for quick start.

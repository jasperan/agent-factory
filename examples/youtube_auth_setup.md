# YouTube API OAuth2 Setup Guide

Complete guide to setting up YouTube Data API v3 authentication for the YouTubeUploaderAgent.

## Overview

The YouTubeUploaderAgent requires OAuth2 credentials to upload videos to YouTube. This guide walks through the complete setup process.

**Time Required:** 10-15 minutes
**Prerequisites:** Google Account with access to YouTube channel

---

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click **"Select a project"** → **"New Project"**
3. Enter project details:
   - **Project name:** `ISH-YouTube-Automation` (or your preferred name)
   - **Organization:** (optional, leave default)
4. Click **"Create"**
5. Wait for project creation (10-30 seconds)

---

## Step 2: Enable YouTube Data API v3

1. In Google Cloud Console, ensure your new project is selected
2. Go to **APIs & Services** → **Library**
3. Search for: `YouTube Data API v3`
4. Click the **YouTube Data API v3** result
5. Click **"Enable"**
6. Wait for API to enable (5-10 seconds)

---

## Step 3: Create OAuth2 Credentials

### Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **User Type:**
   - **External** (for personal use or testing)
   - **Internal** (if you have a Google Workspace organization)
3. Click **"Create"**

4. Fill out **App Information:**
   - **App name:** `ISH YouTube Uploader`
   - **User support email:** Your email address
   - **Developer contact email:** Your email address
5. Click **"Save and Continue"**

6. **Scopes** screen:
   - Click **"Add or Remove Scopes"**
   - Search for: `YouTube Data API v3`
   - Select these scopes:
     - `https://www.googleapis.com/auth/youtube.upload`
     - `https://www.googleapis.com/auth/youtube`
     - `https://www.googleapis.com/auth/youtube.force-ssl`
   - Click **"Update"**
   - Click **"Save and Continue"**

7. **Test users** (if using External type):
   - Click **"Add Users"**
   - Enter your Google account email
   - Click **"Add"**
   - Click **"Save and Continue"**

8. **Summary** screen:
   - Review settings
   - Click **"Back to Dashboard"**

### Create OAuth2 Client ID

1. Go to **APIs & Services** → **Credentials**
2. Click **"+ Create Credentials"** → **"OAuth client ID"**
3. Application type: **"Desktop app"**
4. Name: `ISH YouTube Uploader Desktop`
5. Click **"Create"**

6. **OAuth client created** dialog appears:
   - Click **"Download JSON"**
   - Save file as: `client_secrets.json`
   - Click **"OK"**

7. Move `client_secrets.json` to your project root:
   ```bash
   # Windows
   move Downloads\client_secrets.json C:\Users\hharp\OneDrive\Desktop\agent-factory-ish-youtube\

   # Linux/Mac
   mv ~/Downloads/client_secrets.json ~/agent-factory-ish-youtube/
   ```

---

## Step 4: Run First-Time Authentication

### Install Dependencies

```bash
cd C:\Users\hharp\OneDrive\Desktop\agent-factory-ish-youtube

# Install YouTube API libraries
poetry add google-api-python-client google-auth-oauthlib google-auth-httplib2
```

### Run Authentication Script

```bash
poetry run python examples/youtube_auth_setup.py
```

**What happens:**
1. Script detects `client_secrets.json`
2. Opens browser automatically
3. Prompts you to sign in with Google
4. Shows OAuth consent screen
5. Asks for permission to manage YouTube account
6. Redirects to success page
7. Saves refresh token to `.youtube_credentials.json`

### Expected Output

```
Starting OAuth2 authentication...
Your browser will open automatically
Please sign in and grant permissions

✓ Authentication successful!
Credentials saved to: .youtube_credentials.json

You're ready to upload videos!
```

---

## Step 5: Verify Setup

### Test Authentication

```bash
poetry run python -c "
from agents.media.youtube_uploader_agent import YouTubeUploaderAgent
agent = YouTubeUploaderAgent()
if agent.authenticate():
    print('✓ YouTube API ready!')
    print(f'Quota status: {agent.get_quota_status()}')
else:
    print('✗ Authentication failed')
"
```

**Expected output:**
```
✓ YouTube API ready!
Quota status: {'quota_used': 0, 'quota_remaining': 10000, 'quota_limit': 10000, 'reset_date': '2025-12-12'}
```

---

## Understanding YouTube API Quotas

### Default Quota Limits

- **Daily quota:** 10,000 units
- **Resets:** Midnight Pacific Time (PST/PDT)

### Operation Costs

| Operation | Cost (units) | Max per day |
|-----------|--------------|-------------|
| Upload video (`videos.insert`) | 1,600 | ~6 videos |
| Set thumbnail (`thumbnails.set`) | 50 | 200 |
| Update metadata (`videos.update`) | 50 | 200 |

### Request Quota Increase

For production use (uploading more than 6 videos/day):

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to **APIs & Services** → **Quotas**
3. Filter by: `YouTube Data API v3`
4. Find: **Queries per day**
5. Click **"Edit Quotas"**
6. Fill out quota increase request form:
   - **New quota limit:** 1,000,000 (typical approval)
   - **Use case:** "Automated educational content publishing for Industrial Skills Hub"
7. Submit request

**Approval time:** 2-5 business days

---

## Troubleshooting

### Issue: `client_secrets.json not found`

**Solution:**
- Ensure file is in project root directory
- Check filename is exactly `client_secrets.json`
- Re-download from Google Cloud Console if needed

### Issue: `Access blocked: This app's request is invalid`

**Solution:**
- Verify OAuth consent screen is configured
- Check scopes include `youtube.upload`
- Ensure you're signed in with correct Google account
- Add your email to test users (if using External consent type)

### Issue: `The user has not granted the app [scopes]`

**Solution:**
- Delete `.youtube_credentials.json`
- Re-run authentication script
- Carefully grant all requested permissions

### Issue: `Quota exceeded`

**Solution:**
- Check quota status: `agent.get_quota_status()`
- Wait until midnight Pacific Time for quota reset
- Request quota increase (see above)

### Issue: `Invalid grant: Token expired or revoked`

**Solution:**
- Delete `.youtube_credentials.json`
- Re-run authentication to get fresh tokens

---

## Security Best Practices

### Protect Your Credentials

**DO:**
- ✅ Add `.youtube_credentials.json` to `.gitignore`
- ✅ Add `client_secrets.json` to `.gitignore`
- ✅ Store credentials securely (use environment variables in production)
- ✅ Use separate credentials for production vs development

**DON'T:**
- ❌ Commit credentials to Git
- ❌ Share credentials publicly
- ❌ Use same credentials across multiple environments

### Credential Files

```bash
# Add to .gitignore
echo ".youtube_credentials.json" >> .gitignore
echo "client_secrets.json" >> .gitignore
```

### Production Deployment

For production environments:

1. Use Google Cloud Secret Manager or similar
2. Set credentials via environment variables
3. Rotate credentials regularly (every 90 days)
4. Monitor quota usage and set alerts

---

## Next Steps

Once authenticated, you can:

1. **Upload a test video:**
   ```bash
   poetry run python examples/youtube_uploader_demo.py
   ```

2. **Integrate with orchestrator:**
   - Agent is automatically registered in Supabase
   - Orchestrator can queue upload jobs
   - See: `agents/orchestration/master_orchestrator_agent.py`

3. **Set up automated uploads:**
   - Configure video production pipeline
   - Schedule uploads with PublishingStrategyAgent
   - Monitor upload logs in `data/uploads/`

---

## Additional Resources

- [YouTube Data API v3 Documentation](https://developers.google.com/youtube/v3/docs)
- [OAuth2 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Quota Calculator](https://developers.google.com/youtube/v3/determine_quota_cost)
- [API Explorer](https://developers.google.com/youtube/v3/docs/videos/insert)

---

## Support

If you encounter issues not covered in this guide:

1. Check `logs/youtube_uploader.log` for detailed error messages
2. Verify API status: [Google API Status Dashboard](https://status.cloud.google.com/)
3. Review [YouTube API known issues](https://issuetracker.google.com/issues?q=componentid:186900)

Happy uploading! 🎥

# API Key Sync Script

Automatically syncs your `.env` file API keys to GitHub Secrets.

## Quick Start

```powershell
# Run the sync script
.\sync-api-keys.ps1
```

## What It Does

1. ✅ Reads `ANTHROPIC_API_KEY` from `.env` file
2. ✅ Validates the key format
3. ✅ Tests the key with Anthropic API
4. ✅ Updates GitHub Secret automatically
5. ✅ Verifies the update succeeded

## Requirements

- **GitHub CLI (`gh`)** - Install from: https://cli.github.com/
- **Authenticated with GitHub** - Run: `gh auth login`
- **`.env` file** with `ANTHROPIC_API_KEY`

## Usage

### Basic Sync

```powershell
.\sync-api-keys.ps1
```

### Sync and Test

```powershell
.\sync-api-keys.ps1 -Test
```

## Troubleshooting

### "GitHub CLI (gh) not found"

Install GitHub CLI:
```powershell
winget install --id GitHub.cli
```

Then authenticate:
```powershell
gh auth login
```

### "Not logged in to GitHub CLI"

Run:
```powershell
gh auth login
```

Follow the prompts to authenticate.

### "ANTHROPIC_API_KEY not found in .env"

Make sure your `.env` file contains:
```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

## Security Notes

- ✅ API key is never printed in full (only masked)
- ✅ Script validates key format before uploading
- ✅ Uses GitHub CLI's secure secret storage
- ✅ No API key is stored in git history

## After Syncing

Test that @claude works in GitHub:

1. Go to any issue: https://github.com/Mikecranesync/Agent-Factory/issues
2. Comment: `@claude hello`
3. Wait 30 seconds
4. Claude should respond!

## What Gets Synced

Currently syncs:
- `ANTHROPIC_API_KEY` → GitHub Secret `ANTHROPIC_API_KEY`

## Future Enhancements

Could be extended to sync:
- `OPENAI_API_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- Other secrets needed for CI/CD

## Manual Alternative

If you prefer to update manually:

1. Copy your API key from `.env`
2. Go to: https://github.com/Mikecranesync/Agent-Factory/settings/secrets/actions
3. Click "Update" on `ANTHROPIC_API_KEY`
4. Paste your key
5. Save

But why do that when the script does it in one command? 😎

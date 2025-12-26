# RIVET MVP SPRINT - QUICK START GUIDE
# Run these commands to set up parallel development

## STEP 1: Create Git Branches (Run Once)
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"

# Create all branches from main
git checkout main
git pull origin main

# Create branches
git branch atlas-cmms
git branch landing-stripe
git branch telegram-voice
git branch chat-with-print
git branch intent-parser
git branch integration-testing

# Push all branches to remote
git push origin --all

echo "✅ Branches created"
```

## STEP 2: Create Worktrees

### Computer 1 (3 tabs):
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"

git worktree add ../rivet-atlas atlas-cmms
git worktree add ../rivet-landing landing-stripe
git worktree add ../rivet-telegram telegram-voice

echo "✅ Computer 1 worktrees ready"
```

### Computer 2 (3 tabs):
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"

git worktree add ../rivet-chat-print chat-with-print
git worktree add ../rivet-intent intent-parser
git worktree add ../rivet-integration integration-testing

echo "✅ Computer 2 worktrees ready"
```

## STEP 3: Open Claude Code CLI Tabs

### Computer 1:
- **Tab 1**: Open Claude CLI, cd to `../rivet-atlas`, paste contents of `sprint/WS1_ATLAS_PROMPT.md`
- **Tab 2**: Open Claude CLI, cd to `../rivet-landing`, paste contents of `sprint/WS2_LANDING_PROMPT.md`
- **Tab 3**: Open Claude CLI, cd to `../rivet-telegram`, paste contents of `sprint/WS3_VOICE_PROMPT.md`

### Computer 2:
- **Tab 1**: Open Claude CLI, cd to `../rivet-chat-print`, paste contents of `sprint/WS4_PRINT_PROMPT.md`
- **Tab 2**: Open Claude CLI, cd to `../rivet-intent`, paste contents of `sprint/WS5_INTENT_PROMPT.md`
- **Tab 3**: Open Claude CLI, cd to `../rivet-integration`, paste contents of `sprint/WS6_INTEGRATION_PROMPT.md`

## STEP 4: MCP Server Configuration

Add this to each Claude CLI session or your claude config:

```
DISABLE these MCP servers (context heavy, not needed for dev):
- google_drive_search
- google_drive_fetch
- conversation_search
- recent_chats

KEEP these MCP servers:
- Filesystem (required)
- Context7 (library docs)
- PDF Tools (schematics)
- web_search (external docs)
- web_fetch (GitHub, APIs)
```

## STEP 5: Verify Setup

Each Claude instance should:
1. Read its prompt file
2. Navigate to its worktree
3. Start on Task 1
4. Begin committing with system maps

## MONITORING

Check overall progress:
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
python scripts/check_status.py
```

Check git activity:
```bash
git fetch --all
git log --oneline --graph --all -20
```

## DIRECTORY STRUCTURE AFTER SETUP

```
C:\Users\hharp\OneDrive\Desktop\
├── Agent Factory/           # Main repo (main branch)
│   ├── agent_factory/       # Core code
│   ├── sprint/              # Sprint management files
│   │   ├── WS1_ATLAS_PROMPT.md
│   │   ├── WS2_LANDING_PROMPT.md
│   │   ├── WS3_VOICE_PROMPT.md
│   │   ├── WS4_PRINT_PROMPT.md
│   │   ├── WS5_INTENT_PROMPT.md
│   │   └── WS6_INTEGRATION_PROMPT.md
│   └── ...
│
├── rivet-atlas/             # Worktree: atlas-cmms branch
├── rivet-landing/           # Worktree: landing-stripe branch
├── rivet-telegram/          # Worktree: telegram-voice branch
├── rivet-chat-print/        # Worktree: chat-with-print branch
├── rivet-intent/            # Worktree: intent-parser branch
└── rivet-integration/       # Worktree: integration-testing branch
```

## IF SOMETHING GOES WRONG

### Remove a worktree:
```bash
git worktree remove ../rivet-atlas --force
```

### Start fresh:
```bash
git worktree prune
# Then recreate worktrees
```

### Reset a branch:
```bash
git checkout branch-name
git reset --hard origin/main
```

## TIMELINE

| Day | Goal |
|-----|------|
| Dec 26-27 | All WS complete Task 1-3 |
| Dec 28-29 | Core integration working |
| Dec 30-31 | Full E2E flow working |
| Jan 1-3 | Polish, edge cases |
| Jan 4-7 | Beta testing |
| Jan 8-10 | Launch prep |

---
**LET'S SHIP THIS THING! 🚀**

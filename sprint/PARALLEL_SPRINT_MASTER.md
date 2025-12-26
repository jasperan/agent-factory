# RIVET PARALLEL SPRINT - Dec 26 to Jan 10
## 6 Claude Code CLI Instances, 2 Computers, GitHub Worktrees

**Goal**: Launch Rivet MVP (Atlas CMMS + Telegram Voice Bot + Chat with Print)
**Timeline**: ~2 weeks (extended Claude usage until Jan 1, push to Jan 10 for polish)
**Setup**: 2 computers × 3 tabs each = 6 parallel workstreams

---

## QUICK START (Run This First on Each Computer)

### Computer 1 (Workstreams 1-3)
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"

# Create worktrees
git worktree add ../rivet-atlas atlas-cmms
git worktree add ../rivet-landing landing-stripe  
git worktree add ../rivet-telegram telegram-voice

# If branches don't exist yet:
git branch atlas-cmms
git branch landing-stripe
git branch telegram-voice
git worktree add ../rivet-atlas atlas-cmms
git worktree add ../rivet-landing landing-stripe
git worktree add ../rivet-telegram telegram-voice
```

### Computer 2 (Workstreams 4-6)
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"

# Create worktrees
git worktree add ../rivet-chat-print chat-with-print
git worktree add ../rivet-intent intent-parser
git worktree add ../rivet-integration integration-testing

# If branches don't exist yet:
git branch chat-with-print
git branch intent-parser
git branch integration-testing
git worktree add ../rivet-chat-print chat-with-print
git worktree add ../rivet-intent intent-parser
git worktree add ../rivet-integration integration-testing
```

---

## WORKSTREAM ASSIGNMENTS

| Worktree | Branch | Tab | Computer | Owner | Focus |
|----------|--------|-----|----------|-------|-------|
| rivet-atlas | atlas-cmms | Tab 1 | Computer 1 | Claude 1 | Atlas CMMS deployment + white-label |
| rivet-landing | landing-stripe | Tab 2 | Computer 1 | Claude 2 | Landing page + Stripe checkout |
| rivet-telegram | telegram-voice | Tab 3 | Computer 1 | Claude 3 | Telegram voice → Atlas API |
| rivet-chat-print | chat-with-print | Tab 4 | Computer 2 | Claude 4 | Chat with Print feature |
| rivet-intent | intent-parser | Tab 5 | Computer 2 | Claude 5 | LLM intent parsing + clarification |
| rivet-integration | integration-testing | Tab 6 | Computer 2 | Claude 6 | E2E testing + merge coordination |

---

## SHARED FILES (All Instances Read These)

These files stay in main branch and are accessible from all worktrees:

```
/sprint/
├── PARALLEL_SPRINT_MASTER.md    # This file
├── CLAUDE_SHARED.md             # Shared context for all Claude instances
├── API_CONTRACTS.md             # Interface definitions between components
├── STATUS_BOARD.md              # Real-time status (update after each task)
└── BLOCKERS.md                  # Cross-team blockers

/config/
├── .env.example                 # Environment template
└── rivet.config.json            # Shared configuration
```

---

## PHASE TIMELINE

### Phase 1: Foundation (Dec 26-28) - 3 days
| Workstream | Deliverable | Dependencies |
|------------|-------------|--------------|
| atlas-cmms | Atlas running on VPS, white-labeled | VPS access |
| landing-stripe | Landing page live, Stripe test mode | Domain |
| telegram-voice | Bot receives voice, responds | Telegram token |
| chat-with-print | Claude vision API wrapper working | Claude API key |
| intent-parser | Intent extraction with clarification | None |
| integration-testing | Test harness setup, CI/CD skeleton | All above |

### Phase 2: Integration (Dec 29-Jan 2) - 5 days
| Workstream | Deliverable | Dependencies |
|------------|-------------|--------------|
| atlas-cmms | API documented, user provisioning | Phase 1 |
| landing-stripe | Stripe → Atlas user creation flow | atlas-cmms |
| telegram-voice | Voice → intent → Atlas work order | intent-parser, atlas-cmms |
| chat-with-print | UI complete, integrated as Atlas feature | atlas-cmms |
| intent-parser | Production prompts, edge case handling | telegram-voice |
| integration-testing | Full E2E tests passing | All above |

### Phase 3: Launch Prep (Jan 3-10) - 7 days
| Workstream | Deliverable | Dependencies |
|------------|-------------|--------------|
| atlas-cmms | Production hardened, backups | Phase 2 |
| landing-stripe | Production Stripe, pricing live | Phase 2 |
| telegram-voice | Multi-language, error handling | Phase 2 |
| chat-with-print | Feature flag by tier working | Phase 2 |
| intent-parser | Logging, LangSmith tracing | Phase 2 |
| integration-testing | Load testing, security audit | All above |

---

## MERGE STRATEGY

```
         main
           │
     ┌─────┴─────┬─────────┬──────────┬─────────┬──────────┐
     │           │         │          │         │          │
atlas-cmms  landing  telegram  chat-print  intent  integration
     │           │         │          │         │          │
     └─────┬─────┴─────────┴──────────┴─────────┴──────────┘
           │
     integration-testing (merge point)
           │
         main (after E2E passes)
```

**Rules**:
1. Each workstream commits to its own branch only
2. `integration-testing` pulls from all branches daily
3. Only `integration-testing` merges to `main` after tests pass
4. Conflicts resolved in `integration-testing` branch

---

## SYNC PROTOCOL

Every 4 hours (or at natural break points):

1. **Commit your work** to your branch
2. **Push to origin** 
3. **Update STATUS_BOARD.md** with current state
4. **Check BLOCKERS.md** for dependencies
5. **Pull shared files** from main if updated

---

## COMMUNICATION PROTOCOL

Since Claude instances can't talk to each other directly:

1. **STATUS_BOARD.md** - Update after every completed task
2. **BLOCKERS.md** - Log blockers immediately with workaround attempts
3. **API_CONTRACTS.md** - Document interfaces before implementing
4. **Git commit messages** - Be verbose, other instances read these

---

## EMERGENCY PROTOCOLS

### If a workstream is blocked:
1. Document in BLOCKERS.md with timestamp
2. Tag the blocking workstream
3. Work on non-blocking tasks from backlog
4. Check every 30 minutes for resolution

### If there's a merge conflict:
1. Only integration-testing resolves conflicts
2. Document conflict in BLOCKERS.md
3. Both workstreams pause conflicting work until resolved

### If a Claude instance crashes/resets:
1. Read CLAUDE_SHARED.md first
2. Read your workstream's README
3. Check git log for recent work
4. Continue from last commit

---

## SUCCESS CRITERIA

**Week 1 (Dec 26 - Jan 1)**:
- [ ] Atlas CMMS accessible at cmms.rivet.io
- [ ] Landing page live at rivet.io  
- [ ] Stripe checkout working (test mode)
- [ ] Telegram bot creates work orders in Atlas
- [ ] Chat with Print returns accurate answers
- [ ] All components talking to each other

**Week 2 (Jan 2 - Jan 10)**:
- [ ] Production Stripe (real payments)
- [ ] 5 beta users onboarded
- [ ] <2 second voice → response latency
- [ ] Feature tiers working (Basic/Pro/Enterprise)
- [ ] MaintainX partnership demo ready
- [ ] YouTube demo video recorded

---

## RESOURCES

- **VPS**: 72.60.175.144 (existing RivetCEO)
- **Database**: Neon PostgreSQL (existing)
- **Redis**: Existing setup
- **Domain**: TBD (rivet.io or similar)
- **Telegram Bot**: RivetCEO_bot (extend existing)
- **Claude API**: Existing key
- **LangSmith**: Existing project

---

## NEXT IMMEDIATE ACTION

After setting up worktrees, each Claude instance should:

1. `cd` into their worktree directory
2. Run `git pull origin main` to get latest
3. Read `sprint/CLAUDE_SHARED.md` 
4. Read their workstream-specific README
5. Start on Phase 1 tasks

**Let's ship this thing.**

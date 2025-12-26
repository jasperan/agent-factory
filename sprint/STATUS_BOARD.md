# STATUS BOARD - Rivet MVP Sprint
## Last Updated: Dec 26, 2025 - SPRINT START

---

## OVERALL PROGRESS

| Phase | Status | Target Date | Actual Date |
|-------|--------|-------------|-------------|
| Phase 1: Foundation | 🟡 IN PROGRESS | Dec 28 | - |
| Phase 2: Integration | ⬜ NOT STARTED | Jan 2 | - |
| Phase 3: Launch | ⬜ NOT STARTED | Jan 10 | - |

---

## WORKSTREAM STATUS

### WS-1: Atlas CMMS (atlas-cmms branch)
| Task | Status | Notes |
|------|--------|-------|
| Clone Atlas repo | ⬜ TODO | |
| Docker compose setup | ⬜ TODO | |
| Deploy to VPS | ⬜ TODO | |
| White-label config | ⬜ TODO | |
| API documentation | ⬜ TODO | |
| User provisioning endpoint | ⬜ TODO | |

**Current Focus**: 
**Blockers**: None
**Last Commit**: 

---

### WS-2: Landing + Stripe (landing-stripe branch)
| Task | Status | Notes |
|------|--------|-------|
| Landing page design | ⬜ TODO | |
| Landing page build | ⬜ TODO | |
| Stripe products setup | ⬜ TODO | |
| Checkout flow | ⬜ TODO | |
| Webhook handler | ⬜ TODO | |
| Atlas user creation | ⬜ TODO | Depends on WS-1 |

**Current Focus**: 
**Blockers**: None
**Last Commit**: 

---

### WS-3: Telegram Voice (telegram-voice branch)
| Task | Status | Notes |
|------|--------|-------|
| Review existing bot | ⬜ TODO | |
| Voice message handler | ⬜ TODO | |
| Whisper integration | ⬜ TODO | |
| Intent parser connection | ⬜ TODO | Depends on WS-5 |
| Atlas API connection | ⬜ TODO | Depends on WS-1 |
| Clarification flow | ⬜ TODO | |

**Current Focus**: 
**Blockers**: None
**Last Commit**: 

---

### WS-4: Chat with Print (chat-with-print branch)
| Task | Status | Notes |
|------|--------|-------|
| Claude Vision wrapper | ⬜ TODO | |
| Metadata extraction | ⬜ TODO | |
| Q&A endpoint | ⬜ TODO | |
| Test with real schematics | ⬜ TODO | |
| Atlas integration | ⬜ TODO | Depends on WS-1 |
| Feature flag by tier | ⬜ TODO | |

**Current Focus**: 
**Blockers**: None
**Last Commit**: 

---

### WS-5: Intent Parser (intent-parser branch)
| Task | Status | Notes |
|------|--------|-------|
| ParsedIntent model | ⬜ TODO | |
| Claude extraction logic | ⬜ TODO | |
| Clarification prompts | ⬜ TODO | |
| Edge case handling | ⬜ TODO | |
| Multilingual support | ⬜ TODO | |
| Test with 20+ samples | ⬜ TODO | |

**Current Focus**: 
**Blockers**: None
**Last Commit**: 

---

### WS-6: Integration Testing (integration-testing branch)
| Task | Status | Notes |
|------|--------|-------|
| Test harness setup | ⬜ TODO | |
| Pytest fixtures | ⬜ TODO | |
| Mock components | ⬜ TODO | |
| CI/CD skeleton | ⬜ TODO | |
| E2E test scenarios | ⬜ TODO | |
| First merge to main | ⬜ TODO | After Phase 1 |

**Current Focus**: 
**Blockers**: None
**Last Commit**: 

---

## CROSS-WORKSTREAM DEPENDENCIES

```
WS-2 (Landing) ──needs──→ WS-1 (Atlas API for user creation)
WS-3 (Telegram) ──needs──→ WS-5 (Intent Parser)
WS-3 (Telegram) ──needs──→ WS-1 (Atlas API for work orders)
WS-4 (Chat Print) ──needs──→ WS-1 (Atlas for file storage)
WS-6 (Integration) ──needs──→ ALL (to test)
```

---

## DAILY LOG

### Dec 26, 2025
- Sprint started
- Worktrees created
- All instances assigned

### Dec 27, 2025
(Update as work progresses)

### Dec 28, 2025
(Update as work progresses)

---

## UPDATE INSTRUCTIONS

After completing a task:
1. Change status: ⬜ TODO → 🟡 IN PROGRESS → ✅ DONE → ❌ BLOCKED
2. Add notes if relevant
3. Update "Last Commit" with your most recent commit hash
4. Commit this file: `git add sprint/STATUS_BOARD.md && git commit -m "WS-X: status update"`
5. Push to origin

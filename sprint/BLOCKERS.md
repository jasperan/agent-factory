# BLOCKERS LOG - Rivet MVP Sprint
## Check This File Frequently - Log Issues Immediately

---

## ACTIVE BLOCKERS

| ID | Workstream | Blocker | Blocking | Workaround | Status | Logged |
|----|------------|---------|----------|------------|--------|--------|
| - | - | No active blockers | - | - | - | - |

---

## HOW TO LOG A BLOCKER

Add a new row to the table above:

```markdown
| B-001 | WS-3 | Atlas API not deployed yet | Can't test work order creation | Using mock responses | 🔴 ACTIVE | Dec 26 10:00 |
```

**Status options:**
- 🔴 ACTIVE - Blocking work right now
- 🟡 WORKAROUND - Using temporary solution
- 🟢 RESOLVED - Fixed, can remove after 24h

---

## RESOLVED BLOCKERS

| ID | Workstream | Blocker | Resolution | Resolved |
|----|------------|---------|------------|----------|
| - | - | - | - | - |

---

## BLOCKER ESCALATION

If blocked for more than 2 hours:
1. Try a different approach
2. Check if another workstream can help
3. Log in detail here
4. Move to another task

If blocked for more than 4 hours:
1. Tag Mike in the blocker description
2. Pause that task entirely
3. Focus on independent work

---

## COMMON BLOCKERS & SOLUTIONS

### "Waiting for API from WS-X"
**Solution**: Create a mock version of the API. Define the interface in API_CONTRACTS.md and mock it locally. Real integration happens in Phase 2.

### "Don't have access to VPS/Domain"
**Solution**: Log blocker, work locally with Docker. Deployment can happen later.

### "Unclear requirements"
**Solution**: Check PRD in cmms_Voice_Print_MVP.txt. If still unclear, make reasonable assumption, document it, and proceed.

### "Merge conflict with another branch"
**Solution**: Only WS-6 (integration-testing) resolves conflicts. Log the conflict, continue on non-conflicting work.

### "Test data needed"
**Solution**: Create synthetic test data. Document in tests/fixtures/. Real data comes from beta users later.

---

## UPDATE PROTOCOL

1. When blocked: Add row to ACTIVE BLOCKERS immediately
2. When workaround found: Update status to 🟡 WORKAROUND
3. When resolved: Move to RESOLVED BLOCKERS section
4. Commit changes: `git add sprint/BLOCKERS.md && git commit -m "WS-X: blocker update"`

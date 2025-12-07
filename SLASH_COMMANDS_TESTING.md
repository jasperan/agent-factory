# Slash Commands Testing Guide

## What Was Fixed

Your `/content-clear` and `/content-load` commands have been fixed to work reliably:

### Changes Made:
1. **Renamed command files:**
   - `context-clear.md` → `content-clear.md`
   - `context-load.md` → `content-load.md`

2. **Added explicit file paths** to both commands:
   - `C:\Users\hharp\OneDrive\Desktop\Agent Factory\PROJECT_CONTEXT.md`
   - `C:\Users\hharp\OneDrive\Desktop\Agent Factory\NEXT_ACTIONS.md`
   - `C:\Users\hharp\OneDrive\Desktop\Agent Factory\DEVELOPMENT_LOG.md`
   - `C:\Users\hharp\OneDrive\Desktop\Agent Factory\ISSUES_LOG.md`
   - `C:\Users\hharp\OneDrive\Desktop\Agent Factory\DECISIONS_LOG.md`

## How to Test

### Test 1: `/content-load` (Load Context)

**Purpose:** Reads the 5 memory files and provides a session resume.

**Command:**
```
/content-load
```

**Expected Behavior:**
- Reads all 5 memory files using explicit paths
- Shows current project status
- Lists top 3 immediate tasks
- Summarizes last session
- Lists open issues
- Shows recent decisions
- Indicates if ready to continue

**Success Criteria:**
- ✅ No "file not found" errors
- ✅ Displays formatted resume with all sections
- ✅ Takes 30-60 seconds to complete
- ✅ Provides clear context to resume work

---

### Test 2: `/content-clear` (Save Context)

**Purpose:** Updates all 5 memory files with current session information.

**Command:**
```
/content-clear
```

**Expected Behavior:**
- Reads current state of all 5 files
- Analyzes current session work
- Adds new timestamped entries at TOP of each file
- Preserves all existing content
- Reports what was saved

**Success Criteria:**
- ✅ All 5 files updated successfully
- ✅ New entries added at top with timestamps
- ✅ Existing content preserved
- ✅ Summary report provided
- ✅ Takes 1-2 minutes to complete

**After running, verify files manually:**
```bash
# Check that new entries were added to top
head -n 20 PROJECT_CONTEXT.md
head -n 20 NEXT_ACTIONS.md
head -n 20 DEVELOPMENT_LOG.md
head -n 20 ISSUES_LOG.md
head -n 20 DECISIONS_LOG.md
```

---

## Common Issues and Solutions

### Issue: "Command not found"
**Solution:** Make sure you're typing the command exactly:
- `/content-load` (with hyphen)
- NOT `/content load` (with space)

### Issue: "File not found" errors
**Solution:** Commands now have explicit paths hardcoded. If files were moved, update paths in:
- `.claude/commands/content-clear.md` (line 10-14)
- `.claude/commands/content-load.md` (line 10-14)

### Issue: Commands read wrong files
**Solution:** Commands now specify exact paths. If you have duplicates in `docs/memory/`, you can safely delete them:
```bash
rm -rf docs/memory/*.md
```

---

## Command Invocation Format

Claude CLI supports these formats:

1. **With hyphen** (recommended):
   ```
   /content-clear
   /content-load
   ```

2. **With underscore** (if you prefer):
   - Rename files to: `content_clear.md` and `content_load.md`
   - Use: `/content_clear` and `/content_load`

---

## Testing Workflow

### Full Test Cycle:

1. **Load context at start of session:**
   ```
   /content-load
   ```
   Verify you see current project status and immediate tasks.

2. **Work on tasks** (make changes, complete work)

3. **Save context before ending session:**
   ```
   /content-clear
   ```
   Verify all 5 files are updated with new entries.

4. **Start new session and load context:**
   ```
   /content-load
   ```
   Verify you see the updates from previous session.

---

## What Each Command Does

### `/content-load`
**Purpose:** Quick session resume
**Reads:** Top entry from each memory file
**Output:** Formatted summary with:
- Current project status
- Top 3 tasks
- Last session summary
- Open issues
- Recent decisions

### `/content-clear`
**Purpose:** Preserve current session
**Updates:** All 5 memory files
**Adds:**
- PROJECT_CONTEXT: Current status
- NEXT_ACTIONS: New/updated tasks
- DEVELOPMENT_LOG: Today's activities
- ISSUES_LOG: New/fixed issues
- DECISIONS_LOG: Technical decisions

---

## Files Modified

1. `.claude/commands/content-clear.md` - Save context command
2. `.claude/commands/content-load.md` - Load context command

Both now include:
- Explicit file paths (no ambiguity)
- Clear instructions
- Expected output format
- Success criteria

---

## Next Steps After Testing

If commands work:
- ✅ Delete duplicate files in `docs/memory/` (optional cleanup)
- ✅ Use commands regularly for session management
- ✅ Trust the memory system to preserve context

If commands fail:
- Check file paths are correct
- Ensure memory files exist in root directory
- Verify command names match files (hyphen vs underscore)
- Check `.claude/commands/` directory exists

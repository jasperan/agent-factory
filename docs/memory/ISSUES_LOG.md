# ISSUES_LOG.md

## [OPEN] Issues

None currently

---

## [RESOLVED] Issues

### 2025-12-06

**Issue:** Module import failures in demo and tests
**Status:** RESOLVED
**Solution:** Added `sys.path.insert(0, str(project_root))` to demo and test files
**Impact:** Demo and tests now run successfully
**Resolution Time:** ~5 minutes

**Issue:** Git commit failure due to 'nul' file
**Status:** RESOLVED
**Solution:** Explicitly added only necessary files, excluded 'nul'
**Impact:** Phase 5 commit succeeded
**Resolution Time:** ~2 minutes

---

### 2025-12-05

**Issue:** Dependency conflict between LangChain and LangGraph
**Status:** DEFERRED
**Notes:** Not critical for current phase, postponed for Phase 6+

---

## Known Limitations

1. **Project Twin Scope**
   - Currently only analyzes Python files
   - Could extend to JavaScript, TypeScript, etc.
   - Vector embeddings not yet implemented (future enhancement)

2. **Performance**
   - Large codebase sync may be slow
   - No incremental sync yet (rescans all files)
   - Caching strategy TBD

3. **LLM Integration**
   - Twin Agent requires API key for LLM queries
   - Gracefully falls back to basic twin.query() without LLM
   - Some queries require LLM for best results

4. **Windows Path Handling**
   - Path separators handled (\ vs /)
   - Temporary file paths work correctly
   - No outstanding Windows issues

---

## Technical Debt

1. **Low Priority:** Pydantic deprecation warnings
   - Using class-based `config` instead of ConfigDict
   - 7 warnings in test suite
   - Should migrate to Pydantic V2 ConfigDict
   - Not blocking functionality

2. **Low Priority:** Test path setup
   - Each test file adds project root to sys.path
   - Could use pytest conftest.py for centralized setup
   - Works fine as-is, just not DRY

3. **Low Priority:** Demo script path handling
   - Uses sys.path.insert for imports
   - Could use proper package installation
   - Works for demo purposes

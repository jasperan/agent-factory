# Git Secret Removal Playbook

**Tool**: BFG Repo-Cleaner v1.14.0
**Use Case**: Emergency removal of accidentally committed API keys, credentials, or sensitive data from git history
**Last Updated**: 2025-12-27

## When to Use This Playbook

### ✅ Use BFG When:
- Accidentally committed API keys, tokens, or passwords
- GitHub secret scanning blocked your push
- Need to remove specific files from entire git history
- Large repository (>10k commits) where git filter-branch is too slow
- Time-sensitive incident (BFG is 10-720x faster)

### ❌ Don't Use BFG When:
- Files are still in working tree (just use `git rm` and `.gitignore`)
- Want to rewrite commit messages (use `git filter-branch` or `git filter-repo`)
- Need fine-grained control over specific commits
- Files only in latest commit (use `git reset --soft HEAD~1`)

## Prerequisites

1. **Java Runtime Environment (JRE) 8+**
   ```bash
   java -version  # Should show version 8 or higher
   ```

2. **BFG JAR file**
   - Download: https://rtyley.github.io/bfg-repo-cleaner/
   - Direct link: https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar
   - Storage: `C:\Users\hharp\Tools\bfg\bfg-1.14.0.jar` (Windows)
   - Storage: `~/Tools/bfg/bfg-1.14.0.jar` (Mac/Linux)

3. **Git repository** (local clone)

4. **Backup** (MANDATORY)
   ```bash
   # Create git bundle backup (recommended - smaller, faster)
   git bundle create ../repo-backup-$(date +%Y%m%d).bundle --all

   # Or full directory backup
   cp -r repo-name repo-name-backup-$(date +%Y%m%d)
   ```

## Step-by-Step Process

### Phase 1: Preparation (5 min)

#### 1.1 Verify Java Installation
```bash
java -version
# Should output: openjdk version "17.0.16" or similar
```

#### 1.2 Create Backup
```bash
cd /path/to/your/repo
git bundle create ../repo-backup-$(date +%Y%m%d).bundle --all
# Or on Windows PowerShell:
# git bundle create "..\repo-backup-$(Get-Date -Format 'yyyyMMdd').bundle" --all
```

#### 1.3 Identify Files to Remove
```bash
# Search git history for sensitive strings
git log --all -p | grep -i "api.*key\|password\|token" | head -20

# Find files containing secrets
git log --all --name-only --pretty=format: | sort -u | grep -i "secret\|credential\|password"

# Check specific file history
git log --all -p -- "path/to/file.txt" | head -50
```

#### 1.4 Verify Clean Working Tree
```bash
git status
# Should show "nothing to commit, working tree clean"
# If not, commit or stash changes first
```

### Phase 2: Run BFG (2-5 min)

#### 2.1 Create Mirror Clone
```bash
cd /path/to/parent/directory
git clone --mirror /path/to/your/repo/.git repo-mirror.git
```

#### 2.2 Run BFG to Remove Files

**Option A: Single File**
```bash
java -jar ~/Tools/bfg/bfg-1.14.0.jar \
  --delete-files "secret-file.txt" \
  --no-blob-protection \
  repo-mirror.git
```

**Option B: Multiple Files (from list)**
```bash
# Create file list
cat > files-to-delete.txt << 'EOF'
api-keys.txt
credentials.json
.env.production
EOF

# Run BFG
java -jar ~/Tools/bfg/bfg-1.14.0.jar \
  --delete-files files-to-delete.txt \
  --no-blob-protection \
  repo-mirror.git
```

**Option C: Files by Pattern**
```bash
java -jar ~/Tools/bfg/bfg-1.14.0.jar \
  --delete-files "*.{env,key,pem}" \
  --no-blob-protection \
  repo-mirror.git
```

**Option D: Replace Text (redact keys)**
```bash
# Create replacements file
cat > replacements.txt << 'EOF'
sk-proj-REAL_OPENAI_KEY==>OPENAI_KEY_REDACTED
npg_REAL_NEON_PASSWORD==>NEON_PASSWORD_REDACTED
EOF

java -jar ~/Tools/bfg/bfg-1.14.0.jar \
  --replace-text replacements.txt \
  --no-blob-protection \
  repo-mirror.git
```

#### 2.3 Verify BFG Output
Look for:
```
Deleted files
-------------
Filename             Git id
--------------------------------------
api-keys.txt       | a1b2c3d4 (2.3 KB)

In total, 57 object ids were changed.
```

**Success indicators:**
- ✅ "Deleted files" section shows your files
- ✅ "X object ids were changed" > 0
- ✅ No errors in output

**Failure indicators:**
- ❌ "BFG aborting: No refs to update - no dirty commits found"
  - **Fix**: Add `--no-blob-protection` flag
  - **Cause**: Files not in current HEAD
- ❌ "No files matched"
  - **Fix**: Check filename case sensitivity and path
  - **Cause**: Incorrect filename or pattern

#### 2.4 Cleanup Reflog and Garbage Collect
```bash
cd repo-mirror.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### Phase 3: Push to Remote (1-5 min)

#### 3.1 Add GitHub Remote (if not already added)
```bash
cd repo-mirror.git
git remote add github https://github.com/username/repo.git
git remote -v
```

#### 3.2 Push Cleaned History

**Option A: Single Branch (safer, test first)**
```bash
git push --force github main
# Or your working branch:
# git push --force github feature-branch
```

**Option B: All Branches (full cleanup)**
```bash
git push --force github --all
git push --force github --tags
```

**Common Errors:**

1. **Secret still detected**
   ```
   remote: error: GH013: Repository rule violations found
   remote: - Push cannot contain secrets
   ```
   **Fix**: Secrets still in OTHER branches. Clean those too or clean all with `--all`

2. **Large file detected**
   ```
   remote: error: File is 141.34 MB; this exceeds GitHub's file size limit of 100.00 MB
   ```
   **Fix**: Set up Git LFS before pushing, or remove large file with BFG:
   ```bash
   java -jar bfg.jar --strip-blobs-bigger-than 100M repo-mirror.git
   ```

3. **Branch currently checked out (local remote)**
   ```
   error: refusing to update checked out branch: refs/heads/main
   ```
   **Fix**: Push to GitHub remote, not local .git

### Phase 4: Update Local Repository (2 min)

#### 4.1 Fetch Cleaned History
```bash
cd /path/to/your/repo
git fetch origin --force
```

#### 4.2 Reset to Cleaned Branch
```bash
git reset --hard origin/main
# Or your working branch:
# git reset --hard origin/feature-branch
```

#### 4.3 Verify Secrets Removed
```bash
# Search for specific API key
git log --all -p | grep -i "sk-proj-YOUR_OLD_KEY"
# Should return nothing

# Search for patterns
git log --all -p | grep -E "api.*key|password|token" | head -20
```

### Phase 5: Prevent Future Incidents (10 min)

#### 5.1 Update .gitignore
```bash
cat >> .gitignore << 'EOF'
# API Keys & Credentials
*_secret*.txt
*_credentials*.json
*.env.production
*.env.local
*.pem
*.key
api-keys.txt
secrets.json
EOF

git add .gitignore
git commit -m "chore: Update .gitignore to prevent future secret commits"
```

#### 5.2 Install Pre-Commit Hook

**Option A: gitleaks (recommended - fast, zero dependencies)**
```bash
# Download gitleaks
# macOS: brew install gitleaks
# Linux: https://github.com/gitleaks/gitleaks/releases
# Windows: Download .exe from releases

# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
gitleaks protect --staged --verbose
if [ $? -eq 1 ]; then
  echo "⚠️  gitleaks detected secrets. Commit aborted."
  exit 1
fi
EOF

chmod +x .git/hooks/pre-commit
```

**Option B: detect-secrets (Python-based)**
```bash
pip install detect-secrets

# Create baseline
detect-secrets scan > .secrets.baseline

# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
detect-secrets scan --baseline .secrets.baseline
if [ $? -ne 0 ]; then
  echo "⚠️  Secrets detected. Commit aborted."
  exit 1
fi
EOF

chmod +x .git/hooks/pre-commit
```

#### 5.3 Test Pre-Commit Hook
```bash
# Try to commit a file with fake API key
echo "OPENAI_API_KEY=sk-test123" > test-secret.txt
git add test-secret.txt
git commit -m "test"
# Should abort with secret detection warning
```

## Common Scenarios

### Scenario 1: Single File with API Key
```bash
# 1. Backup
git bundle create ../backup.bundle --all

# 2. Create mirror and clean
git clone --mirror .git ../mirror.git
cd ../mirror.git
java -jar ~/Tools/bfg/bfg.jar --delete-files "api-keys.txt" --no-blob-protection .

# 3. Cleanup and push
git reflog expire --expire=now --all && git gc --prune=now --aggressive
git remote add github https://github.com/user/repo.git
git push --force github main

# 4. Update local
cd /original/repo
git fetch origin --force
git reset --hard origin/main
```

### Scenario 2: Multiple .env Files
```bash
# Create list
cat > env-files.txt << 'EOF'
.env.production
.env.staging
.env.local
EOF

# Clean with BFG
java -jar bfg.jar --delete-files env-files.txt --no-blob-protection mirror.git
```

### Scenario 3: Replace Key Text (Don't Delete File)
```bash
# Create replacements
cat > replacements.txt << 'EOF'
sk-proj-abc123xyz789==>OPENAI_KEY_REDACTED
gsk_real_groq_key==>GROQ_KEY_REDACTED
EOF

# Run BFG
java -jar bfg.jar --replace-text replacements.txt --no-blob-protection mirror.git
```

## Troubleshooting

### Issue: BFG Says "No dirty commits found"
**Cause**: Files not in current HEAD (already deleted in latest commit)
**Fix**: Add `--no-blob-protection` flag
```bash
java -jar bfg.jar --delete-files "file.txt" --no-blob-protection mirror.git
```

### Issue: Files Still Showing in Git History
**Cause**: Only cleaned one branch, secrets in others
**Fix**: Clean all branches
```bash
git push --force github --all  # Push ALL cleaned branches
```

### Issue: GitHub Rejects Push (Secret Detected)
**Cause**: Secret still in a different branch
**Fix**: Use `git log --all -p | grep "secret"` to find which branch, then clean that branch too

### Issue: GitHub Rejects Push (Large File)
**Cause**: File >100MB in repository
**Fix**: Install Git LFS or remove large file with BFG
```bash
java -jar bfg.jar --strip-blobs-bigger-than 100M mirror.git
```

### Issue: Lost My Changes After Reset
**Cause**: Used `git reset --hard` without committing local changes
**Fix**: Check reflog for lost commits
```bash
git reflog  # Find commit before reset
git cherry-pick <commit-hash>  # Restore changes
```

## Rollback Plan

If BFG causes issues:

```bash
# 1. Delete compromised repo
cd /parent/directory
rm -rf original-repo

# 2. Restore from bundle backup
git clone backup.bundle original-repo

# 3. Verify restoration
cd original-repo
git log --oneline -10
git status
```

## Best Practices

### ✅ Do:
- Always create backup before running BFG
- Test on single branch before cleaning all branches
- Verify secrets removed with `git log --all -p | grep "secret"`
- Rotate compromised API keys IMMEDIATELY
- Update .gitignore to prevent recurrence
- Install pre-commit hook for future protection

### ❌ Don't:
- Run BFG without backup
- Skip verification step
- Forget to push cleaned history to remote
- Assume one branch cleaned = all branches cleaned
- Reuse compromised API keys "just this once"

## Emergency Checklist

```
[ ] 1. Create git bundle backup
[ ] 2. Identify files with secrets (git log search)
[ ] 3. Create mirror clone
[ ] 4. Run BFG with --no-blob-protection
[ ] 5. Verify "Deleted files" section in output
[ ] 6. Run git reflog expire + git gc
[ ] 7. Push cleaned history to GitHub (test single branch first)
[ ] 8. Verify secrets removed (git log grep)
[ ] 9. Update local repository (git reset --hard)
[ ] 10. Rotate ALL exposed API keys
[ ] 11. Update .gitignore
[ ] 12. Install pre-commit hook
[ ] 13. Document incident (INCIDENT_YYYY-MM-DD.md)
```

## Resources

- **BFG Official Docs**: https://rtyley.github.io/bfg-repo-cleaner/
- **BFG GitHub**: https://github.com/rtyley/bfg-repo-cleaner
- **Git Filter-Repo** (alternative): https://github.com/newren/git-filter-repo
- **Gitleaks** (secret detection): https://github.com/gitleaks/gitleaks
- **Detect-Secrets**: https://github.com/Yelp/detect-secrets
- **GitHub Secret Scanning**: https://docs.github.com/en/code-security/secret-scanning

## Performance Benchmarks

From Agent Factory incident (2025-12-27):
- **Repository size**: 752 commits, ~50 branches
- **Files cleaned**: 4 files (total 22 KB)
- **Objects rewritten**: 1,087 git objects
- **Time**: <5 seconds for all 4 files
- **Comparison**: Estimated 2-4 hours with manual git filter-branch

---

**Maintained by**: Agent Factory Security Team
**Last Incident**: 2025-12-27 (see `docs/security/INCIDENT_2025-12-27.md`)
**Tool Location**: `C:\Users\hharp\Tools\bfg\bfg-1.14.0.jar`

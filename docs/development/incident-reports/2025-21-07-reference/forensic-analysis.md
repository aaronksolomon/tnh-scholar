# Forensic Analysis: December 7, 2025 Git Data Loss Incident

**Analyst**: Claude Sonnet 4.5
**Date**: December 8, 2025
**Evidence Sources**:

- Session log: `convo-with-hard-reset.txt`
- Incident report: `docs/development/incident-reports/2025-12-07-git-recovery.md`
- Git reflog analysis

---

## Executive Summary

**Root Cause Identified**: The data loss was caused by resetting `main` to a **branch reference** (`version-0.2.0`) that did NOT yet contain the prompt system work, instead of waiting for the work to be merged to that branch first.

**Critical Timeline Error**:

- The `git reset --hard version-0.2.0` occurred at line 396 of the session
- At that moment, PR #12 (which would merge the prompt system work into `version-0.2.0`) had only just been created at line 316
- PR #12 was not merged until line 321 ("done!")
- This means **main was reset to version-0.2.0 BEFORE version-0.2.0 received the prompt system work**

**Severity**: High - 39 files (4,508 lines) orphaned
**Impact**: No permanent data loss (recovered via reflog)
**Prevention Status**: Partially addressed; additional safeguards needed

---

## Detailed Timeline Reconstruction

### Phase 1: PR Creation and Merge Sequence (Lines 251-321)

| Line | Event | Status |
|------|-------|--------|
| 251 | User merges PR #11 (`prompt-system-refactor` → `version-0.1.4`) | ✅ Complete |
| 252 | Claude recognizes need to merge 0.1.4 → 0.2.0 | ✅ Correct |
| 268-316 | Claude creates PR #12 (`version-0.1.4` → `version-0.2.0`) | ✅ PR Created |
| 321 | User: "done! next is the complex main work." | ⚠️ PR #12 merged |

**Key Point**: At line 321, PR #12 is merged, so `version-0.2.0` branch NOW contains the prompt system work.

### Phase 2: Main Branch Analysis (Lines 322-378)

| Line | Event | Analysis |
|------|-------|----------|
| 322-378 | Claude analyzes divergence between `main` and `version-0.2.0` | Correct process |
| 368-378 | Finds common ancestor `8e82804`, counts divergent commits | Good forensics |
| 379-391 | Proposes reset workflow | ⚠️ Workflow correct IF executed properly |

**Key Point**: The analysis at this stage is correct - `version-0.2.0` has all the work after PR #12 merged.

### Phase 3: THE FATAL ERROR (Lines 392-398)

```text
Line 392: User: "agreed! proceed."
Line 393: Claude: "Perfect! Let me proceed with resetting main to version-0.2.0:"
Line 394-396:
    Bash Reset main to version-0.2.0
    IN: git reset --hard version-0.2.0
Line 397-398:
    OUT: HEAD is now at d51fc87 feat: Automate PyPI README frontmatter stripping
```

**CRITICAL FINDING**:

The reset moved main to commit `d51fc87` - but this commit is the **version bump commit** from line 363:

```text
Line 363: d51fc87 feat: Automate PyPI README frontmatter stripping in release workflow
Line 364: 0d7d459 chore: Bump version to 0.2.0
```

This commit `d51fc87` is BEFORE the PR #12 merge that added prompt system work!

---

## Root Cause Analysis

### The Critical Mistake

**What the agent THOUGHT it was doing:**

- Resetting `main` to the branch `version-0.2.0` which (after PR #12 merge at line 321) should contain all the prompt system work

**What ACTUALLY happened:**

- The local git reference `version-0.2.0` had NOT been updated after the remote PR #12 merge
- The local branch still pointed to commit `d51fc87` (the version bump, before the merge)
- Therefore `git reset --hard version-0.2.0` moved main to the pre-merge state
- This orphaned all the work that was ONLY accessible via the now-deleted branches

### The Missing Step

**What should have been done between line 391 and line 396:**

```bash
# REQUIRED: Update local branch reference after remote merge
git fetch origin version-0.2.0
git checkout version-0.2.0
git pull origin version-0.2.0

# THEN verify the prompt system work is present
git log --oneline -10
ls -la src/tnh_scholar/prompt_system/  # Verify directory exists

# ONLY THEN proceed with reset
git checkout main
git reset --hard version-0.2.0
```

---

## Why This Happened: Conceptual Confusion

### Understanding Branch References

The agent made a fundamental error about git branch references:

1. **After a PR merge on GitHub**: The remote branch `origin/version-0.2.0` updates
2. **Local branch reference unchanged**: The local `version-0.2.0` still points to old commit
3. **Reset uses local reference**: `git reset --hard version-0.2.0` uses the **local**, outdated reference
4. **Result**: Reset to wrong commit, orphaning all new work

### The Tag vs Branch Confusion (Red Herring)

The incident report focuses heavily on "tag vs branch confusion" but the session log proves this was NOT the issue:

- The agent correctly used `version-0.2.0` (branch name, no `v` prefix)
- The agent correctly distinguished from tag `v0.2.0`
- The command `git reset --hard version-0.2.0` was syntactically correct

**The real issue**: Using a **stale local branch reference** without fetching after remote merge.

---

## Contributing Factors

### 1. Workflow Complexity

The multi-branch merge sequence created multiple opportunities for error:

- PR #11: `prompt-system-refactor` → `version-0.1.4`
- PR #12: `version-0.1.4` → `version-0.2.0`
- Reset: `main` to `version-0.2.0`

Each step assumed the previous step's remote changes were reflected locally.

### 2. Implicit Assumptions

The agent assumed that:

- After user said "done!" (line 321), the branch reference was up-to-date
- The branch name `version-0.2.0` would automatically point to the merged state
- No fetch/pull was needed between remote merge and local reset

### 3. Lack of Verification

No verification step between the merge and reset:

- No `git fetch` before reset
- No `git log` to verify prompt_system commits present
- No file system check (`ls src/tnh_scholar/prompt_system/`)

### 4. Agent Safety Rules Incomplete

The existing git safety rules (from incident report, lines 284-299) don't cover:

- **Fetch requirement**: Always fetch before using branch references after remote operations
- **Post-merge verification**: Verify work is present before destructive operations
- **State validation**: Check that local branch matches expected remote state

---

## What Saved Us

### Recovery Factors

1. **Git Reflog**: All commits preserved locally (30-90 day retention)
2. **Quick Discovery**: Issue found within hours
3. **User Expertise**: User recognized orphaned commits and knew reflog recovery
4. **No Local Cleanup**: Local repo still had commit `c6532f5` in reflog

### Lucky Breaks

1. **Branches not yet deleted from remote**: PR branches auto-delete after 3 hours, incident happened within window
2. **Backup-main existed**: Though not needed, provided psychological safety
3. **Work was pushed**: PRs #11 and #12 pushed work to remote, providing alternative recovery path

---

## Critical Gaps in Safeguards

### Gap 1: No Post-Remote-Merge Fetch Requirement

**Current git safety rules DO NOT require:**

- Fetching before using branch references
- Verifying local branch matches remote after remote operations

**Proposed addition:**

```markdown
**ALWAYS fetch and verify after remote PR merges:**
- Run `git fetch origin <branch>` before using branch in local operations
- Run `git log <branch> --oneline -5` to verify expected commits present
- Verify key directories/files exist if doing destructive operations
```

### Gap 2: No Pre-Reset Content Verification

**Current rules check for unpushed work but NOT for expected content:**

**Proposed addition:**

```markdown
**Before git reset --hard, verify target contains expected work:**
- List key files/directories that should be present after reset
- Use `git diff --name-only HEAD..<target>` to preview what will change
- If adding work (like prompt_system/), verify target has those files:
  `git ls-tree -r <target> --name-only | grep <expected-path>`
```

### Gap 3: No Branch Staleness Detection

**No way to detect if local branch reference is stale:**

**Proposed addition:**

```markdown
**Check local branch staleness before destructive operations:**
```bash
# Compare local vs remote branch
git fetch origin
LOCAL=$(git rev-parse <branch>)
REMOTE=$(git rev-parse origin/<branch>)
if [ "$LOCAL" != "$REMOTE" ]; then
    echo "⚠️ WARNING: Local branch is stale!"
    echo "Local:  $LOCAL"
    echo "Remote: $REMOTE"
    read -p "Update local branch first? (Y/n) " confirm
fi
```

---

## Recommended Safeguards

### Immediate (High Priority)

#### 1. Enhanced Git Safety Rules

Add to `.claude/CLAUDE.md`:

```markdown
### Post-Merge Safety Protocol

**CRITICAL: After ANY GitHub PR merge, ALWAYS:**
1. Fetch the branch: `git fetch origin <branch>`
2. Verify the merge commit is present: `git log origin/<branch> --oneline -5`
3. If using branch for reset/merge, check local vs remote: `git rev-parse <branch>` vs `git rev-parse origin/<branch>`
4. Update local branch if stale: `git checkout <branch> && git pull`

### Pre-Reset Verification Protocol

**BEFORE `git reset --hard <target>`, ALWAYS:**
1. Verify target exists and is up-to-date: `git fetch && git rev-parse <target>`
2. Preview changes: `git diff --stat HEAD..<target>`
3. If expecting new work, verify it's in target: `git ls-tree -r <target> --name-only | grep <expected-path>`
4. Check for unpushed work: `git log --branches --not --remotes`
5. Confirm with user showing exactly what will be lost/gained
```

#### 2. Pre-Reset Hook Enhancement

Update `.git/hooks/pre-reset` (if feasible) or add to automation:

```bash
#!/bin/bash
# Check if target branch reference is stale

target="$1"
if git show-ref --verify --quiet "refs/heads/$target"; then
    git fetch origin "$target" 2>/dev/null
    local_sha=$(git rev-parse "$target" 2>/dev/null)
    remote_sha=$(git rev-parse "origin/$target" 2>/dev/null)

    if [ -n "$remote_sha" ] && [ "$local_sha" != "$remote_sha" ]; then
        echo "⚠️  ERROR: Local branch '$target' is stale!"
        echo "   Local:  $local_sha"
        echo "   Remote: $remote_sha"
        echo ""
        echo "   Update first: git checkout $target && git pull"
        exit 1
    fi
fi
```

### Short-term (Medium Priority)

#### 3. Workflow Simplification

**Avoid complex multi-branch merge chains:**

- Prefer: Feature branch → main (direct)
- Avoid: Feature → version-0.1.4 → version-0.2.0 → main (complex)

**Recommendation**: Use GitHub's merge queue or single-step merges to main

#### 4. Agent Prompt Enhancement

Add to Claude Code system prompt for git operations:

```
**Git Branch Reference Safety:**
- Branch names in git commands refer to LOCAL references, not remote state
- After any GitHub PR merge, local branches are STALE until fetched
- ALWAYS run `git fetch origin <branch>` before using branch in reset/merge
- NEVER assume local branch = remote branch without explicit fetch
```

### Long-term (Lower Priority)

#### 5. Automated Pre-Flight Checks

Create `scripts/safe-reset.sh`:

```bash
#!/bin/bash
# Safe git reset with verification
target="$1"
git fetch origin
# ... verification logic ...
git reset --hard "$target"
```

Configure agent to use this instead of direct `git reset --hard`

#### 6. Session State Persistence

Track session state across commands:

- Record when PRs are merged (remote state change)
- Mark local branches as "needs fetch" after remote changes
- Require fetch before using marked branches

---

## Incident Report Updates Needed

### Section: "Why It Happened (Root Cause: Unknown)"

**Current text** (line 80):
> We cannot definitively determine the exact git command that caused the incident.

**Should be updated to**:
> **Root Cause Identified**: The incident was caused by resetting `main` to a stale local branch reference. The command `git reset --hard version-0.2.0` used the local branch reference that pointed to commit `d51fc87` (version bump commit), while the remote `origin/version-0.2.0` had been updated with PR #12 merge to include prompt system work at commit `5bf012d`. The agent failed to fetch the branch after the remote PR merge, causing the reset to use outdated state.

### Section: "Contributing Factors"

**Add**:

- **Stale branch reference**: Local `version-0.2.0` not updated after remote PR #12 merge
- **No post-merge fetch**: Agent proceeded with reset immediately after user confirmed merge without fetching
- **No content verification**: Agent did not verify prompt_system work was present in reset target

### Section: Tag vs Branch Confusion

**Revise** (lines 92-98):
> This section can be removed or significantly reduced. The session log proves the agent correctly used the branch name `version-0.2.0` (not the tag `v0.2.0`). The issue was NOT tag vs branch confusion, but rather using a stale local branch reference.

---

## Lessons Learned (Additional)

### What Went Wrong (Not Previously Documented)

❌ **Stale branch reference**: Reset used local reference without fetching after remote merge
❌ **No post-merge verification**: Did not verify prompt_system work was in target before reset
❌ **Implicit assumptions**: Assumed branch name would point to merged state without explicit fetch
❌ **Incomplete safety rules**: Existing rules did not cover post-remote-merge fetch requirements

### New Understanding

🔍 **Git branch references are local**: Branch names in git commands use local refs, not remote state
🔍 **Remote merges don't update local**: GitHub PR merges update `origin/branch`, not local `branch`
🔍 **Fetch is not optional**: After remote changes, fetch is REQUIRED before using branch references
🔍 **Content verification crucial**: Before destructive operations, verify expected files/commits present

---

## Testing the Fix

### Simulation Test

To verify safeguards prevent recurrence:

```bash
# Simulate the incident scenario
git checkout -b test-main
git reset --hard <some-old-commit>

# Simulate remote PR merge (don't fetch)
# Now try reset WITHOUT fetch - should be blocked by new safeguards

git reset --hard <branch-name>  # Should fail or warn about staleness
```

### Expected Behavior with Safeguards

1. **Pre-reset hook**: Detects local branch is behind remote, blocks operation
2. **Agent prompt**: Requires fetch before reset, verifies content present
3. **User confirmation**: Shows diff of what will change, requires explicit approval

---

## Conclusion

### The Smoking Gun

Line 396: `git reset --hard version-0.2.0` used a **stale local branch reference** that pointed to commit `d51fc87`, orphaning all work that had been merged to the remote branch via PR #12.

### The Fix

**Required action between line 321 (PR merge) and line 396 (reset):**

```bash
git fetch origin version-0.2.0
git log origin/version-0.2.0 --oneline -10  # Verify merge commit present
git checkout version-0.2.0
git pull  # Update local reference
# NOW safe to reset main to version-0.2.0
```

### Safeguard Priority

**Critical** (implement immediately):

- Post-merge fetch requirement in git safety rules
- Pre-reset content verification protocol
- Branch staleness detection

**Important** (implement soon):

- Workflow simplification to reduce merge chain complexity
- Agent prompt enhancement about branch reference semantics

**Nice-to-have** (future):

- Automated safe-reset script
- Session state tracking for branch staleness

---

**Analysis complete. All evidence points to stale branch reference as root cause.**

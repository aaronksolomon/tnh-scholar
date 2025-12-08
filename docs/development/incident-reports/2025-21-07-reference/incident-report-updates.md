# Proposed Updates to Incident Report

Based on forensic analysis of session log `convo-with-hard-reset.txt`

---

## 1. Update Executive Summary (Line 22)

**Current:**
> **Root Cause**: Reset to TAG v0.2.0 instead of merging BRANCH version-0.2.0

**Proposed:**
> **Root Cause**: Reset to stale local branch reference - local `version-0.2.0` not fetched after remote PR merge

---

## 2. Update Timeline (Line 46-49)

**Current:**
```markdown
- **19:37**: **INCIDENT**: Destructive git operation executed on main (exact command unknown)
  - Git reflog shows: "reset: moving to version-0.2.0"
  - Main branch did not include prompt system work after operation
  - This orphaned all prompt system work (commit `c6532f5` and descendants)
```

**Proposed:**
```markdown
- **19:37**: **INCIDENT**: Reset main to stale branch reference
  - Command: `git reset --hard version-0.2.0` (session log line 396)
  - Problem: Local `version-0.2.0` not fetched after remote PR #12 merge
  - Local branch pointed to `d51fc87` (version bump), not `5bf012d` (merged state)
  - Missing step: `git fetch origin version-0.2.0` before reset
  - This orphaned all prompt system work (commit `c6532f5` and descendants)
```

---

## 3. Rewrite Root Cause Section (Lines 80-106)

**Replace entire section "Why It Happened (Root Cause: Unknown)" with:**

### Why It Happened (Root Cause: Stale Branch Reference)

**Root Cause Identified**: The incident was caused by resetting `main` to a **stale local branch reference** that had not been updated after a remote PR merge.

**The Fatal Sequence** (from session log):

1. **Line 316**: PR #12 created (`version-0.1.4` → `version-0.2.0`)
2. **Line 321**: User confirms "done!" - PR #12 merged on GitHub
   - Remote `origin/version-0.2.0` now points to `5bf012d` (includes prompt system)
   - Local `version-0.2.0` still points to `d51fc87` (version bump only)
3. **Line 396**: Agent executes `git reset --hard version-0.2.0`
   - Uses **local** reference `d51fc87` (stale)
   - Should have used **remote** reference `5bf012d` (current)
   - Result: Reset to pre-merge state, orphaning all new work

**The Missing Step**:

Between the PR merge (line 321) and the reset (line 396), this was required but omitted:

```bash
# REQUIRED: Update local branch after remote merge
git fetch origin version-0.2.0
git checkout version-0.2.0
git pull

# Verify prompt system work is present
git log --oneline -10
ls -la src/tnh_scholar/prompt_system/

# THEN safe to reset
git checkout main
git reset --hard version-0.2.0
```

**Why This Mistake Happened**:

- **Git semantics misunderstanding**: Branch names in git commands refer to **local** references, not remote state
- **Implicit assumption**: Agent assumed `version-0.2.0` would automatically point to merged state after user said "done"
- **No verification**: No check that local branch matched remote branch before reset
- **Workflow complexity**: Three-tier merge chain (feature → 0.1.4 → 0.2.0 → main) created multiple opportunities for staleness

**Evidence**:

Session log line 397-398:
```
git reset --hard version-0.2.0
HEAD is now at d51fc87 feat: Automate PyPI README frontmatter stripping
```

Commit `d51fc87` is the version bump commit **before** PR #12 merge. The prompt system work was in merge commit `5bf012d`, which was on remote but not in local branch reference.

**Contributing Factors**:

- **No branch protection on main**: Allowed direct reset without review
- **No post-merge fetch protocol**: Safety rules didn't require fetch after remote operations
- **No content verification**: Didn't verify expected files present in reset target
- **Complex workflow**: Multi-branch merge chain increased surface area for errors
- **Missing session logging**: Unable to see exact git state at time of operation (though we recovered it from log)

---

## 4. Update Preventative Measures (Add New Section)

**Add after line 299 (existing git safety rules):**

### 2. Post-Remote-Merge Safety Protocol

Added to `.claude/CLAUDE.md`:

```markdown
### Post-Merge Safety Protocol

**CRITICAL: After ANY GitHub PR merge, ALWAYS:**

1. **Fetch the branch**: `git fetch origin <branch>`
2. **Verify merge commit present**: `git log origin/<branch> --oneline -5`
3. **Check local vs remote**: Compare `git rev-parse <branch>` vs `git rev-parse origin/<branch>`
4. **Update local if stale**: `git checkout <branch> && git pull`
5. **Verify expected content**: List key files/dirs that should be present

**Example**:
```bash
# After PR merges feature → target-branch on GitHub
git fetch origin target-branch
git log origin/target-branch --oneline -5  # See merge commit
git checkout target-branch
git pull
ls -la expected/new/directory/  # Verify content present
# NOW safe to use target-branch in local operations
```

### Pre-Reset Content Verification

**BEFORE `git reset --hard <target>`, ALWAYS:**

1. **Fetch target**: `git fetch origin <target>` (if branch exists on remote)
2. **Preview changes**: `git diff --stat HEAD..<target>`
3. **Verify expected work present**:
   ```bash
   # If expecting new directories/files
   git ls-tree -r <target> --name-only | grep <expected-path>
   ```
4. **Check unpushed work**: `git log --branches --not --remotes --oneline`
5. **Confirm with user**: Show exactly what will be lost/gained

**Example**:
```bash
# Before: git reset --hard version-0.2.0
git fetch origin version-0.2.0
git diff --stat HEAD..version-0.2.0  # Preview changes
git ls-tree -r version-0.2.0 --name-only | grep prompt_system  # Verify content
git log --branches --not --remotes --oneline  # Check unpushed work
# Show user the diff and get explicit confirmation
```
```

---

## 5. Update Lessons Learned (Line 359-365)

**Add to "What Could Be Improved" section:**

```markdown
❌ **No post-merge fetch protocol**: Local branches not updated after remote PR merges
❌ **No content verification**: Did not verify expected files present before reset
❌ **Git semantics gap**: Agent didn't understand branch names use local refs, not remote state
❌ **Insufficient verification**: No check that local branch matched remote before destructive operation
```

---

## 6. Update Action Items (Line 367-390)

**Add to "Immediate (Completed)" section:**

```markdown
- [x] Add post-remote-merge fetch protocol to `.claude/CLAUDE.md`
- [x] Add pre-reset content verification protocol
- [x] Document git branch reference semantics in safety rules
```

**Add to "Short-term (Recommended)" section:**

```markdown
- [ ] Create `scripts/safe-reset.sh` wrapper with automatic staleness detection
- [ ] Add pre-reset hook to detect stale branch references
- [ ] Simplify workflow: prefer feature → main (avoid multi-tier merge chains)
```

---

## 7. Remove/Revise Tag vs Branch Confusion Discussion

**Lines 92-98 (in old "Root Cause" section) should be removed or revised:**

The session log proves the agent correctly used `version-0.2.0` (branch name) and not `v0.2.0` (tag name). The issue was NOT tag/branch confusion but rather using a stale local branch reference.

**If keeping any discussion of naming:**

```markdown
**Note on naming**: While tag `v0.2.0` and branch `version-0.2.0` have similar names, the session log confirms the agent correctly used the branch name. The issue was that the local branch reference was stale, not that the wrong ref type was used.
```

---

## 8. Update Appendix B (Feature Request) - Lines 394-455

**Add new section at line 409 (after shell command log example):**

```markdown
**3. Branch Staleness Log** (`~/.claude/audit/branch-state.jsonl`):
```jsonl
{"timestamp": "2025-12-07T19:37:30-08:00", "session_id": "abc123", "operation": "pr_merge_detected", "branch": "version-0.2.0", "local_sha": "d51fc87", "remote_sha": "5bf012d", "stale": true}
{"timestamp": "2025-12-07T19:37:51-08:00", "session_id": "abc123", "operation": "git_reset", "target": "version-0.2.0", "target_sha": "d51fc87", "warning": "target_may_be_stale"}
```

**Why This Matters**:

This incident would have been **prevented** with branch staleness tracking. The audit log would have shown:
1. Local branch `version-0.2.0` = `d51fc87`
2. Remote branch `origin/version-0.2.0` = `5bf012d` (after PR #12)
3. WARNING: Using stale local reference in reset operation
```

---

## Summary of Key Changes

1. **Root cause identified**: Stale local branch reference (was "unknown")
2. **Exact command sequence**: Documented from session log (was missing)
3. **Missing step documented**: Need to fetch after remote merge (new finding)
4. **Tag confusion removed**: Not the actual issue (was red herring)
5. **New safeguards added**: Post-merge fetch protocol, content verification
6. **Agent understanding gap**: Document git branch reference semantics

---

## Files to Update

1. `docs/development/incident-reports/2025-12-07-git-recovery.md` - Main incident report
2. `.claude/CLAUDE.md` - Add post-merge fetch protocol (if not already done)
3. `docs/development/git-workflow.md` - Add branch staleness section (if exists)

---

**Next Steps**: Review forensic analysis and apply updates to incident report as appropriate.

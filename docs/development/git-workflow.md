---
title: "Git Workflow & Safety Guide"
description: "Safe git practices for TNH Scholar development to prevent data loss"
author: "Claude Sonnet 4.5"
status: "current"
created: "2025-12-07"
updated: "2025-12-15"
owner: "Engineering"
---

# Git Workflow & Safety Guide

This guide establishes safe git practices to prevent accidental data loss.

## Pre-Commit Hooks: DISABLED

**Status**: Pre-commit hooks are **permanently disabled** for this project.

**Reason**: Pre-commit hooks with `pass_filenames: false` (mypy, version-sync) automatically stash unstaged changes during commit. If the restore fails (due to branch switching, interruptions, or timing issues), **work is silently lost** to `.cache/pre-commit/patch*` files instead of git stash, making recovery difficult.

**New Workflow**: Run quality checks manually before committing:

```bash
# BEFORE every commit, run:
make ci-check

# This runs all checks that pre-commit would have run:
# - Ruff linting
# - Type checking (mypy)
# - Documentation validation
# - Tests

# If checks pass, commit with hooks disabled:
git add .
git commit -m "your message"
git push
```

**Recovery if work was lost**: Check `/Users/phapman/.cache/pre-commit/patch*` files (sorted by timestamp) and apply with `git apply <patch-file>`.

## Untracked Files Rule

**NEVER stash untracked files.** Untracked → commit to new branch → return to workflow.

## Critical Safety Rules

### Commands That Must NEVER Be Executed by AI - User Only

These commands are **FORBIDDEN** for AI agents to execute. **Only humans** should run these commands:

```bash
# FORBIDDEN FOR AI AGENTS - User must run manually
git reset --hard <ref>
git reset --soft <ref>
git reset --mixed <ref>
git push --force
git push --force-with-lease
git branch -D <branch>
git branch -d <branch>
git rebase (any flags)
git tag -d <tag>
git clean -fd
git checkout -- .
git restore (with destructive flags)
git filter-branch
```

**If AI agents identify a need for these operations:**

- STOP immediately
- Explain to the user why the operation may be useful
- Provide context for understanding the command and how it is intended to be used as well as its non-recoverable aspects (destructive consequences) in detail
- Provide potential backup operations that will allow full recovery
- Allow the user to consider this path and explore other options. Confirm if the user has indeed executed.

### ALWAYS Check Before Switching Branches

Before `git checkout <branch>`:

```bash
# Check for unpushed commits
git log --branches --not --remotes --oneline

# Check branch tracking status
git branch -vv

# If unpushed commits exist, push first!
git push -u origin <current-branch>
```

## Safe Workflow

### Recommended Approach: Simple Feature Branches

**Best practice**: Merge feature branches directly to main, avoiding complex multi-tier merge chains.

```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/my-feature

# Push immediately - safety first!
git push -u origin feature/my-feature

# Work and commit
git add .
git commit -m "feat: implement feature"

# Push frequently
git push

# When ready: Create PR to main
gh pr create --base main --head feature/my-feature

# After PR merges: Delete branch
git checkout main
git pull
git branch -d feature/my-feature
git push origin --delete feature/my-feature
```

**Why this is safer**:

- Simpler workflow = fewer opportunities for staleness errors
- No intermediate version branches to keep in sync
- Clear linear path: feature → main
- Tags (not branches) preserve release points

### Alternative: Multi-Tier Merges (More Complex)

If you must use version branches (e.g., `version-0.2.0`), follow these **critical steps**:

```bash
# 1. Create feature branch
git checkout -b feature/my-feature
git push -u origin feature/my-feature

# 2. Create PR #1: feature → version-branch
gh pr create --base version-0.2.0 --head feature/my-feature

# 3. CRITICAL: After PR merges, UPDATE LOCAL REFERENCE
git fetch origin version-0.2.0
git checkout version-0.2.0
git pull origin version-0.2.0

# 4. VERIFY work is present
git log --oneline -10
ls -la path/to/expected/new/files/

# 5. Check staleness before any destructive operations
./scripts/git-check-staleness.sh version-0.2.0

# 6. Now safe to create next PR
gh pr create --base main --head version-0.2.0

# 7. After final merge to main, update main
git fetch origin main
git checkout main
git pull origin main

# 8. Verify and delete temporary branches
git branch -d version-0.2.0 feature/my-feature
```

**Warning**: This workflow is more error-prone. The December 7 incident occurred because step #3 (fetch after PR merge) was skipped.

### Switching Branches

```bash
# ALWAYS check unpushed work first
git check-unpushed

# If unpushed commits exist:
git push

# Then switch
git checkout main
```

### Recovering from Mistakes

If you accidentally lose commits:

```bash
# Check reflog for lost commits
git reflog

# Find the commit SHA (e.g., c6532f5)
git log <sha> --stat

# Recover the commit
git checkout -b recovery-branch <sha>

# Or cherry-pick it
git cherry-pick <sha>
```

## Recovery Examples

### Lost Branch After Reset

**Scenario**: Ran `git reset --hard` and lost work

```bash
# Find lost commit in reflog
git reflog | grep "commit:"

# Recreate branch at lost commit
git checkout -b recovered-work <lost-commit-sha>

# Push immediately!
git push -u origin recovered-work
```

### Unpushed Branch Switched Away

**Scenario**: Switched away from branch without pushing

```bash
# Find the branch in reflog
git reflog show <old-branch-name>

# Checkout the commit
git checkout <commit-sha>

# Recreate branch
git checkout -b <old-branch-name>

# Push it!
git push -u origin <old-branch-name>
```

## Branch Staleness Detection

### Using git-check-staleness.sh

**Purpose**: Detects if a local branch reference is stale (out of sync) compared to its remote tracking branch.

**Location**: `scripts/git-check-staleness.sh`

**When to use**:

- Before any destructive git operation (performed by user, never by AI)
- After a PR merges on GitHub (before using that branch locally)
- Before complex git operations involving branch references
- When you're unsure if local branch matches remote

**Usage**:

```bash
# Check specific branch
./scripts/git-check-staleness.sh version-0.2.0

# Check current branch
./scripts/git-check-staleness.sh

# Check a branch against a specific remote/branch (non-origin setups)
./scripts/git-check-staleness.sh --remote upstream --branch main feature/123-new-flow
```

The script resolves the branch's configured upstream tracking ref by default (e.g., `feature/foo@{u}`) so it works with custom tracking branches. Use `--remote`/`--branch` only when you need to override that default.

**Example output (up-to-date)**:

```text
Fetching remote state...
✓ Branch 'main' is up-to-date
  SHA: a6523a9...
```

**Example output (stale)**:

```text
Fetching remote state...
✗ Branch 'version-0.2.0' is STALE!

  Local:  d51fc87...
  Remote: 5bf012d...

⚠  Local is 5 commit(s) BEHIND remote

To update local branch:
  git checkout version-0.2.0 && git pull
```

**Exit codes**:

- `0` - Branch is up-to-date or has no remote tracking branch
- `1` - Branch is stale (local differs from remote)
- `2` - Invalid usage or branch doesn't exist

**Critical use case**: The December 7 incident would have been prevented if this script was run before the destructive reset operation. As of the updated safety rules, AI agents are now forbidden from executing such commands - only users may run them after proper verification.

### Post-Remote-Merge Protocol

**ALWAYS after a GitHub PR merge**:

```bash
# 1. Fetch the merged branch
git fetch origin <branch-name>

# 2. Check staleness
./scripts/git-check-staleness.sh <branch-name>

# 3. Update local if stale
git checkout <branch-name>
git pull

# 4. Verify expected content
ls -la path/to/new/files/
git log --oneline -5

# NOW safe to use branch in local operations
```

**Why this matters**: Branch names in git commands refer to **LOCAL** references, not remote state. After a PR merge on GitHub, the remote branch updates but your local reference stays stale until explicitly fetched and updated.

## Git Aliases (Already Configured)

These safe aliases are configured globally:

```bash
# Check unpushed commits
git check-unpushed

# Reset with confirmation prompt
git safe-reset <ref>

# Push with unpushed summary
git safe-push
```

## Branch Protection Rules

### Main Branch

- Never `git reset` on main without approval
- Never force push to main
- Always create feature branches for new work

### Feature Branches

- Push to origin immediately after creation
- Push after every significant commit
- Never delete until merged and pushed

## Automation & Hooks

### Pre-checkout Hook

Warns when switching branches with unpushed commits. Located at:

- `.git/hooks/pre-checkout`

To bypass (not recommended):

```bash
git checkout --no-verify <branch>
```

## Emergency Steps

If you lose work and can't recover:

1. **DO NOT RUN ANY MORE GIT COMMANDS** (you might overwrite reflog)
2. Check `.git/logs/` manually for historical refs
3. Run `git fsck --lost-found` to find dangling commits
4. Contact repository maintainer with reflog output

## Incident: December 7, 2025

**What Happened**: `git reset --hard version-0.2.0` on main orphaned 39 files (4,508 lines) of prompt system work.

**Root Cause**: Reset used **stale local branch reference**. Local `version-0.2.0` was not fetched after remote PR #12 merge on GitHub. Local branch pointed to `d51fc87` (version bump), while remote had merged work at `5bf012d`.

**Key Learning**: Branch names in git commands refer to LOCAL references, not remote state. After a GitHub PR merge, the remote branch updates but the local reference stays stale until explicitly fetched.

**Recovery**: All work recovered from git reflog (commit `c6532f5`).

**Prevention Measures Implemented**:

- **Absolute prohibition**: AI agents forbidden from executing destructive git commands (`.claude/CLAUDE.md`)
- Added educational protocol: AI must explain commands, consequences, and recovery options before user executes
- Added post-remote-merge fetch protocol to `.claude/CLAUDE.md`
- Created `scripts/git-check-staleness.sh` to detect stale branches
- Enhanced this workflow guide with simplified workflow recommendations
- Installed pre-checkout hook
- Configured git safety aliases

**Full Details**: See [Incident Report: Git Recovery 2025-12-07](/development/incident-reports/2025-12-07-git-recovery.md)

---

## References

- [Git Best Practices](https://git-scm.com/book/en/v2)
- [Git Reflog Documentation](https://git-scm.com/docs/git-reflog)
- [Contributing Guide](/project/repo-root/contributing-root.md)

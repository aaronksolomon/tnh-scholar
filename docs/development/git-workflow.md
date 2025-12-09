---
title: "Git Workflow & Safety Guide"
description: "Safe git practices for TNH Scholar development to prevent data loss"
author: "Claude Sonnet 4.5"
created: "2025-12-07"
---

# Git Workflow & Safety Guide

This guide establishes safe git practices to prevent accidental data loss.

## Critical Safety Rules

### NEVER Execute Without Approval

These commands are **destructive** and require explicit human approval:

```bash
# DANGEROUS - Never run without approval
git reset --hard <ref>
git push --force
git branch -D <branch>
git rebase -i
git filter-branch
```

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

### Starting New Feature Work

```bash
# Create and push branch immediately
git checkout -b feature/my-feature
git push -u origin feature/my-feature

# Work and commit
git add .
git commit -m "feat: implement feature"

# Push frequently
git push
```

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

## Emergency Contacts

If you lose work and can't recover:

1. **DO NOT RUN ANY MORE GIT COMMANDS** (you might overwrite reflog)
2. Check `.git/logs/` manually for historical refs
3. Run `git fsck --lost-found` to find dangling commits
4. Contact repository maintainer with reflog output

## Incident: December 7, 2025

**What Happened**: `git reset --hard version-0.2.0` on main caused `prompt-system-refactor` branch to become orphaned (30+ files, commit c6532f5).

**Root Cause**: Branch was never pushed to origin before switching away.

**Recovery**: Commit found in reflog and recovered.

**Prevention**:
- Added git safety rules to `.claude/CLAUDE.md`
- Installed pre-checkout hook
- Created this workflow guide
- Configured git safety aliases

---

## References

- [Git Best Practices](https://git-scm.com/book/en/v2)
- [Git Reflog Documentation](https://git-scm.com/docs/git-reflog)
- [Contributing Guide](/project/repo-root/contributing-root.md)

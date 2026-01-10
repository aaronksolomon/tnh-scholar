---
title: "Release Workflow"
description: "Automated release process for TNH Scholar with biweekly cadence during rapid prototyping."
owner: ""
author: "Claude (Sonnet 4.5) with Aaron Solomon"
status: current
created: "2025-12-06"
---
# Release Workflow

This document describes the automated release process for TNH Scholar, designed to support biweekly (or faster) releases during rapid prototyping with minimal manual effort.

## Quick Reference

Standard patch release workflow (e.g., x.x.y → 0.x.y+1):

```bash
make release-patch       # Bump version + update TODO.md
make changelog-draft     # Generate CHANGELOG entry
# Edit CHANGELOG.md with generated content
make release-commit      # Commit version changes
make release-tag         # Tag and push to remote
make release-publish     # Strip frontmatter, build, publish to PyPI, restore README (automated)
```

**Dry-run mode**: Add `DRY_RUN=1` to any command to preview without making changes:

```bash
make release-patch DRY_RUN=1    # Preview version bump
make release-commit DRY_RUN=1   # Preview commit
make release-tag DRY_RUN=1      # Preview tag and push
make release-publish DRY_RUN=1  # Preview PyPI publish
```

## Prerequisites

### One-Time Setup

Before first release, complete these configuration steps:

1. **PyPI API Token**: Configure Poetry with your PyPI credentials

   ```bash
   poetry config pypi-token.pypi <your-api-token>
   ```

   Get a token from: [https://pypi.org/manage/account/token/](https://pypi.org/manage/account/token/)

2. **Git Configuration**: Ensure git is configured with your name and email

   ```bash
   git config user.name "Your Name"
   git config user.email "your.email@example.com"
   ```

3. **Quality Checks Pass**: Verify the project builds cleanly

   ```bash
   make release-check  # Runs: test, type-check, lint, docs-verify
   ```

### Pre-Release Verification

Before starting any release, ensure all quality checks pass:

```bash
make release-check
```

This runs:

- `make test` - Full test suite with pytest
- `make type-check` - MyPy type checking
- `make lint` - Ruff linting
- `make docs-verify` - Documentation build, link check, and spell check

**Expected output**: `✅ All quality checks passed - ready to release`

If checks fail, fix the issues before proceeding with the release.

## Release Types

Choose the appropriate version bump based on the changes:

### Patch Release (0.x.Y → 0.x.Y+1)

```bash
make release-patch
```

**Use for**:

- Bug fixes
- Documentation improvements
- Minor refactoring without API changes
- Dependency updates
- Code cleanup and formatting

### Minor Release (0.X.y → 0.X+1.0)

```bash
make release-minor
```

**Use for**:

- New features that maintain backward compatibility
- Significant documentation reorganization
- New CLI commands or subcommands
- Major improvements to existing features

**⚠️ Documentation Review Required**: Minor releases with new features require manual review of user-facing documentation to catch docs issues. See Step 1.5 below.

### Major Release (X.y.z → X+1.0.0)

```bash
make release-major
```

**Use for**:

- Breaking API changes
- Incompatible CLI changes
- Major architectural shifts

**Note**: Major releases are rare during alpha/beta phases.

## Step-by-Step Workflow

### Step 1: Bump Version

Choose the appropriate version bump:

```bash
make release-patch   # For 0.1.4 → 0.1.5
# OR
make release-minor   # For 0.1.4 → 0.2.0
# OR
make release-major   # For 0.1.4 → 1.0.0
```

**What happens**:

- Updates `pyproject.toml` version field
- Updates `TODO.md` version header to match
- Displays next steps

**Example output**:

```plaintext
🚀 Bumping patch version (0.x.Y -> 0.x.Y+1)...
Bumping version from 0.1.4 to 0.1.5
📝 Updating version to 0.1.5 in TODO.md...
✅ Version updated to 0.1.5

Next steps:
  1. Review user-facing documentation (see Step 1.5 below for minor/major releases)
  2. Run 'make changelog-draft' to generate CHANGELOG entry
  3. Edit CHANGELOG.md with the generated content
  4. Run 'make release-commit' to commit changes
  5. Run 'make release-tag' to tag and push
  6. Run 'make release-publish' to publish to PyPI
```

### Step 1.5: Review User-Facing Documentation (Minor/Major Releases Only)

**⚠️ Critical for feature releases**: Automated tests catch code issues, but documentation changes require human review.

**When to do this**: After `make release-minor` or `make release-major`, before generating CHANGELOG.

**What to review**:

Human review is comprehensive - read all changed user-facing docs looking for any textual inconsistencies, outdated claims, or confusing language that crept in during development.

**Step 1: Get AI-assisted summary of documentation changes**

```bash
# List ALL documentation files modified since last release
git diff v$(git describe --tags --abbrev=0)..HEAD --name-only \
  | grep -E '\.md$' \
  | grep -v '^(CHANGELOG.md|TODO.md|AGENTLOG.md|archive/)'

# For each changed file, get one-sentence summary of changes
# (Ask AI agent: "Summarize changes in one sentence per file")
git diff v$(git describe --tags --abbrev=0)..HEAD --stat \
  -- '*.md' ':!CHANGELOG.md' ':!TODO.md' ':!AGENTLOG.md' ':!archive/'
```

**Step 2: Human review priorities (read in order)**:

1. **Core user-facing docs** (comprehensive read-through):
   - `README.md` - Features list, examples, getting started
   - `docs/getting-started/` - Installation, quick start, configuration
   - `docs/user-guide/` - Workflows, prompt system, common tasks
   - `docs/cli-reference/` - Command docs, examples, usage patterns
   - `AGENTS.md` - CLI tools section, status markers

2. **Supporting docs** (scan for consistency):
   - Architecture ADRs - Status fields, implementation notes
   - Development guides - Setup instructions, workflow references
   - API docs - Docstring updates, type signatures

**Common issues to catch** (examples, not exhaustive):

- **Status claims**: "in development" → "available" | "coming soon" → current feature
- **Tool references**: Deprecated tool shown as current, new tool marked as future
- **Examples**: Commands using old syntax, removed flags, deprecated tools
- **Version notes**: "As of v0.X" that should update, or remove if no longer relevant
- **Cross-references**: Links to moved/renamed files, outdated ADR references
- **Tone shifts**: Dev notes like "TODO" or "WIP" left in user docs

**Review checklist**:

- [ ] README.md features list reflects current state
- [ ] README.md example commands use current CLI tools and syntax
- [ ] Getting Started guides reference available (not planned) features
- [ ] CLI reference examples show current tool names
- [ ] User guide workflows use non-deprecated tools
- [ ] AGENTS.md CLI tools section shows correct status (v0.X.Y+)

**Fix and commit before proceeding**:

```bash
# Make documentation fixes
git add README.md docs/
git commit -m "docs: Update status references for v0.X.0 release"
```

### Step 2: Generate CHANGELOG Entry

```bash
make changelog-draft
```

**What happens**:

- Analyzes git commits since the last tag
- Categorizes commits by type (Added, Changed, Fixed, Documentation, etc.)
- Generates a formatted CHANGELOG entry

**Example output**:

```text
📝 Generating CHANGELOG entry from git history...

## [0.1.5] - 2025-12-06

### Added

- Automated version sync between pyproject.toml and TODO.md in release targets
- Python-based link checker (md-dead-link-check) for documentation

### Changed

- Replaced lychee with Python-native link checking tool
- Improved developer onboarding with fewer external dependencies

### Documentation

- Created comprehensive release workflow documentation

============================================================
📝 Draft CHANGELOG entry for v0.1.5
Based on 8 commits since v0.1.4
============================================================

👆 Copy this to CHANGELOG.md and edit as needed
```

### Step 3: Edit CHANGELOG.md

1. Open `CHANGELOG.md` (in project root) in your editor
2. Copy the generated entry from your terminal
3. Paste at the top of the file (after the header, before previous versions)
4. Edit the entry for clarity and completeness:
   - Remove noise commits (merge commits, trivial fixes)
   - Rewrite commit messages for user-facing clarity
   - Group related changes together
   - Add context or references where needed
   - Add "Notes" or "Breaking Changes" sections if applicable
5. Save the file

**Example polished entry**:

```markdown
# Changelog

All notable changes to TNH Scholar will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [0.1.5] - 2025-12-06

### Added

- **Automated Version Sync**: Release targets automatically sync pyproject.toml and TODO.md versions
- **Python-based Link Checker**: Replaced lychee (Rust tool) with md-dead-link-check for pure Python toolchain

### Changed

- Simplified developer setup by removing non-Python tooling requirements
- Restored full documentation verification pipeline with Python-native tools

### Documentation

- Created comprehensive release workflow documentation in docs/development/

### Notes

- This release focuses on release automation improvements (Phase 2)
- No code functionality changes - purely tooling and documentation infrastructure
- External link checking now uses pure Python stack for better Poetry integration

## [0.1.4] - 2025-12-05
...
```

### Step 4: Commit Version Changes

```bash
make release-commit
```

**What happens**:

- Stages `pyproject.toml`, `TODO.md`, `CHANGELOG.md`, and `poetry.lock`
- Creates a formatted commit with a standard message
- Shows next steps

**Commit message format**:

```plaintext
chore: Bump version to 0.1.5

- Update version in pyproject.toml
- Update TODO.md version header
- Add 0.1.5 release notes to CHANGELOG.md

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Step 5: Tag and Push

```bash
make release-tag
```

**What happens**:

- Creates an annotated git tag (e.g., `v0.1.5`)
- Pushes the current branch to the remote
- Pushes the tag to the remote

**Tag message format**:

```plaintext
Release v0.1.5

See CHANGELOG.md for full details.

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Example output**:

```plaintext
🏷️  Tagging version v0.1.5...
📤 Pushing branch and tag...
✅ Tagged and pushed v0.1.5

Next: Run 'make release-publish' to publish to PyPI
```

### Step 6: Publish to PyPI

```bash
make release-publish
```

**What happens** (all automated):

1. **Prepares README for PyPI**: Strips YAML frontmatter to ensure clean rendering
   - Creates backup at `README.md.bak`
   - Removes frontmatter that would display as plain text on PyPI

2. **Builds distributions**: Creates wheel and source distribution using Poetry

3. **Publishes to PyPI**: Uploads both distributions

4. **Restores README**: Automatically restores original README with frontmatter

**Why frontmatter stripping is needed**: PyPI doesn't process YAML frontmatter and will display it as plain text, making your project description look unprofessional. The automation handles this for you.

**Example output**:

```text
📝 Preparing README for PyPI (stripping YAML frontmatter)...
✓ Backed up README.md to /path/to/README.md.bak
✓ Stripped 443 bytes of frontmatter from README.md

📦 README.md is ready for PyPI build
💡 Run 'python scripts/prepare_pypi_readme.py --restore' to restore original

📦 Building package...
Building tnh-scholar (0.1.5)
  - Building sdist
  - Built tnh_scholar-0.1.5.tar.gz
  - Building wheel
  - Built tnh_scholar-0.1.5-py3-none-any.whl

📤 Publishing to PyPI...
Publishing tnh-scholar (0.1.5) to PyPI
 - Uploading tnh_scholar-0.1.5-py3-none-any.whl 100%
 - Uploading tnh_scholar-0.1.5.tar.gz 100%

📝 Restoring original README...
✓ Restored README.md from backup

✅ Published v0.1.5 to PyPI

🎉 Release complete! Check https://pypi.org/project/tnh-scholar/
```

### Step 7: Verify Release

After publishing, verify the release was successful:

1. **Check PyPI**: Visit [https://pypi.org/project/tnh-scholar/](https://pypi.org/project/tnh-scholar/)
   - Verify the new version is listed
   - **Important**: Check that README renders correctly without YAML frontmatter
   - Confirm the project description starts with "# TNH Scholar README" and not with "---"

2. **Test Installation**:

   ```bash
   pip install --upgrade tnh-scholar==0.1.5
   python -c "import tnh_scholar; print(tnh_scholar.__version__)"
   ```

   Expected output: `0.1.5`

3. **Check GitHub**:
   - Tag appears in releases: [https://github.com/aaronksolomon/tnh-scholar/tags](https://github.com/aaronksolomon/tnh-scholar/tags)
   - Verify the commit and tag messages are correct

## Advanced Usage

### All-in-One Release

If you've already edited CHANGELOG.md and are confident in your changes:

```bash
make release-full
```

This runs: `release-commit` → `release-tag` → `release-publish` in sequence.

**⚠️ Use with caution**: This skips intermediate verification steps. Only use this after you've verified CHANGELOG.md is correct.

### Dry Run Mode

Preview any release command without making changes by adding `DRY_RUN=1`:

```bash
# Preview version bump
make release-patch DRY_RUN=1

# Preview commit
make release-commit DRY_RUN=1

# Preview tag and push
make release-tag DRY_RUN=1

# Preview PyPI publish
make release-publish DRY_RUN=1
```

**Example dry-run output for version bump**:

```plaintext
🔍 DRY RUN MODE - No changes will be made

🚀 Would bump patch version: 0.1.4 → 0.1.5

Commands that would run:
  poetry version patch
  sed -i.bak 's/> \*\*Version\*\*:.*/> **Version**: 0.1.5 (Alpha)/' TODO.md

To execute: make release-patch
```

**Benefits**:

- See exact commands that will run
- Verify commit messages and tag messages before creating them
- Catch errors early (wrong version bump, missing files, etc.)
- Safe way to learn the release workflow
- Useful for documenting the process

**When to use dry-run**:

- First time using a release target
- Testing a new release workflow
- Verifying what will be committed/tagged/published
- Training new contributors
- Before major releases

**Test version bumps without dry-run**:

```bash
# Check current version
poetry version -s

# Test version bump calculation (doesn't modify files)
poetry version --dry-run patch   # Shows: 0.1.4 → 0.1.5
poetry version --dry-run minor   # Shows: 0.1.4 → 0.2.0

# Actually bump (modifies pyproject.toml)
make release-patch

# Undo if needed (before committing)
git checkout pyproject.toml TODO.md poetry.lock
```

### Skip Steps

You can run individual targets if you need to customize the workflow:

```bash
# Just generate changelog (no version bump)
make changelog-draft

# Just commit (if you bumped version manually)
make release-commit

# Just tag (if you committed manually)
make release-tag

# Just publish (if you tagged manually)
make release-publish
```

## Automation Features

### Version Sync

The release targets automatically sync versions between `pyproject.toml` and `TODO.md` to prevent version drift bugs.

**How version sync works**:

- `make release-patch/minor/major` updates both files simultaneously
- Version is read from `pyproject.toml` via `poetry version -s`
- TODO.md version header is updated to match

**If versions get out of sync**, use a release target to sync them:

```bash
# Use one of the release targets to sync versions
make release-patch   # Bump patch version
make release-minor   # Bump minor version
make release-major   # Bump major version
```

### Documentation Verification

The `make docs-verify` target runs a comprehensive documentation quality check:

1. **Drift Check**: Ensures README.md and docs/index.md are in sync
2. **Build Check**: Runs MkDocs in strict mode (fails on warnings)
3. **Link Check**: Validates external links using md-dead-link-check (Python-native)
4. **Spell Check**: Runs codespell on README and docs

All documentation tools are Python-based and managed by Poetry for consistent developer experience.

## Troubleshooting

### "No previous tag found"

**Problem**: First release, no git tags exist yet.

**Solution**: Write the CHANGELOG entry manually, skip `make changelog-draft`.

### "Version mismatch in TODO.md"

**Problem**: TODO.md version marker not found or malformed.

**Solution**: Ensure TODO.md contains a line matching the pattern:

```markdown
> **Version**: 0.1.4 (Alpha)
```

The version sync hook validates this format.

### "PyPI authentication failed"

**Problem**: No PyPI API token configured.

**Solution**:

```bash
poetry config pypi-token.pypi <your-token>
```

Get a token from: [https://pypi.org/manage/account/token/](https://pypi.org/manage/account/token/)

### "Tests failing in release-check"

**Problem**: Code has failing tests, type errors, or lint violations.

**Solution**: Fix issues before releasing:

```bash
make test           # Run pytest test suite
make type-check     # Run mypy type checks
make lint           # Run ruff linting
make docs-verify    # Build and validate docs
```

Address all failures before proceeding with the release.

### "Git push rejected"

**Problem**: Remote has changes you don't have locally.

**Solution**:

```bash
git pull --rebase origin $(git branch --show-current)
# Resolve conflicts if any
make release-tag  # Try again
```

### "Link check failing"

**Problem**: External links are broken or timing out.

**Solution**:

1. Review the failing links in the output
2. Update or remove broken links
3. For transient failures, retry after a few minutes
4. For sites that block automated requests, add to the exclude list in `pyproject.toml`:

   ```toml
   [tool.md_dead_link_check]
   exclude_links = [
       "https://example.com/*",  # Add problematic domains
   ]
   ```

## Tips for Efficient Releases

### Use Conventional Commits

Format commits to make CHANGELOG generation more accurate:

```bash
git commit -m "feat: add new feature X"
git commit -m "fix: resolve bug in Y"
git commit -m "docs: update getting started guide"
git commit -m "chore: bump dependencies"
```

**Commit prefixes**:

- `feat:` → Added section
- `fix:` → Fixed section
- `docs:` → Documentation section
- `chore:`, `build:`, `ci:` → Infrastructure section
- `refactor:`, `perf:` → Changed section
- `test:` → Testing section

### Batch Related Changes

For rapid iteration, you can release after any logical batch of commits:

```bash
# Week 1: Development
git commit -m "feat: implement feature A"
git commit -m "feat: implement feature B"
git commit -m "fix: resolve edge case in feature A"
git commit -m "docs: document features A and B"

# Week 2: Release day
make release-patch
make changelog-draft
# Edit CHANGELOG.md
make release-commit
make release-tag
make release-publish

# Total time: 10-15 minutes
```

### Schedule Regular Releases

Consider a biweekly release cadence during active development:

- **Every other Friday**: Release day
- **Morning**: Run `make release-check` to catch issues early
- **Afternoon**: Execute release workflow
- **Result**: Consistent, predictable releases that build user trust

### Parallel Development

You can work on multiple features in parallel using branches:

```bash
# Create feature branches from stable release
git checkout -b feature-a v0.1.4
# ... work on feature A ...

git checkout -b feature-b v0.1.4
# ... work on feature B ...

# When ready, merge to main and release
git checkout main
git merge feature-a
make release-patch  # Release 0.1.5
```

This allows rapid iteration without blocking work on new features.

## Release Checklist

Use this checklist to ensure complete releases:

- [ ] All quality checks pass (`make release-check`)
- [ ] Version bumped with appropriate type (`make release-patch/minor/major`)
- [ ] CHANGELOG.md updated with clear, user-friendly descriptions
- [ ] Version changes committed (`make release-commit`)
- [ ] Tag created and pushed (`make release-tag`)
- [ ] Package published to PyPI (`make release-publish` - automatically strips/restores README frontmatter)
- [ ] PyPI listing verified at [https://pypi.org/project/tnh-scholar/](https://pypi.org/project/tnh-scholar/)
- [ ] Installation test from PyPI successful (`pip install tnh-scholar==X.Y.Z`)
- [ ] GitHub tag appears in [repository tags](https://github.com/aaronksolomon/tnh-scholar/tags)
- [ ] GitHub Release created with release notes

## Related Documentation

- `Makefile` (project root) - Release automation implementation
- `CHANGELOG.md` (project root) - Version history
- [Contributing Guide](/development/contributing-prototype-phase.md) - Contribution guidelines
- [Markdown Standards](/docs-ops/markdown-standards.md) - Documentation standards

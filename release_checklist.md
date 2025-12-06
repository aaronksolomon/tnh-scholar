---
title: "TNH Scholar Release Checklist"
description: "Checklist of tasks required before publishing a TNH Scholar release."
owner: ""
author: ""
status: processing
created: "2025-01-22"
updated: "2025-12-06"
---
# TNH Scholar Release Checklist

Checklist of tasks required before publishing a TNH Scholar release.

**Note**: During 0.x (rapid prototype phase), breaking changes are acceptable in any release. See [VERSIONING.md](VERSIONING.md) for policy.

## Pre-Release

- [ ] Update version in pyproject.toml
- [ ] Update CHANGELOG.md (include breaking changes if any)
- [ ] If breaking changes: update migration guides/ADRs
- [ ] Run full test suite: `pytest`
- [ ] Run type checks: `mypy`
- [ ] Run linting: `ruff check .`
- [ ] Build test
- [ ] TestPyPI upload & install test

## Release

- [ ] PyPI upload
- [ ] Tag release in git
- [ ] Update GitHub release notes (link to CHANGELOG, highlight breaking changes)

## Post-Release

- [ ] Verify installation: `pip install tnh-scholar` in clean environment
- [ ] Update docs if needed
- [ ] Close related issues/PRs

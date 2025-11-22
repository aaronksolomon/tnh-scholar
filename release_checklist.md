---
title: "Release Checklist"
description: "Checklist of tasks required before publishing a TNH Scholar release."
owner: ""
author: ""
status: processing
created: "2025-01-22"
---
# Release Checklist

Checklist of tasks required before publishing a TNH Scholar release.

- [ ] Update version in pyproject.toml
- [ ] Update CHANGELOG.md
- [ ] Run full test suite: `pytest`
- [ ] Run type checks: `mypy`
- [ ] Run linting: `ruff check .`
- [ ] Build test
- [ ] TestPyPI upload & install test
- [ ] PyPI upload
- [ ] Tag release in git

---
title: "Release Checklist"
description: "- [ ] Update version in pyproject.toml"
owner: ""
status: processing
created: "2025-01-22"
---
# Release Checklist

- [ ] Update version in pyproject.toml
- [ ] Update CHANGELOG.md
- [ ] Run full test suite: `pytest`
- [ ] Run type checks: `mypy`
- [ ] Run linting: `ruff check .`
- [ ] Build test
- [ ] TestPyPI upload & install test
- [ ] PyPI upload
- [ ] Tag release in git

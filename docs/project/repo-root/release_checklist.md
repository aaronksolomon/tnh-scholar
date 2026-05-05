---
title: TNH Scholar Release Checklist
description: Checklist of tasks required before publishing a TNH Scholar release.
owner: ''
author: ''
status: current
created: '2025-01-22'
auto_generated: true
generated_from: /release_checklist.md
---

<!-- DO NOT EDIT: Auto-generated from /release_checklist.md. Edit the root file instead. -->

# TNH Scholar Release Checklist

Checklist of tasks required before publishing a TNH Scholar release.

## Pre-Release

- [ ] Confirm the release scope and choose the correct bump type (`make release-patch`, `make release-minor`, or `make release-major`)
- [ ] Run the full local gate on the actual release candidate state: `make release-check`
- [ ] Run all live golden tests for the release candidate state and capture their outputs as release artifacts; today this includes the live `tnh-gen` golden pipeline under `tests/golden/`, and future CLIs should be added here as they gain live goldens
- [ ] For minor or major releases, review user-facing docs (`README.md`, `docs/getting-started/`, `docs/user-guide/`, `docs/cli-reference/`, `AGENTS.md`) for stale claims and examples
- [ ] Ensure `CHANGELOG.md` reflects the actual unreleased work clearly and user-readably

## Versioning

- [ ] Update `pyproject.toml` version via the release target
- [ ] Confirm `TODO.md` version header matches the bumped version
- [ ] Verify user-facing version references are not stale (`README.md`, `VERSIONING.md`, release docs as needed)

## Validation

- [ ] Full test suite passes
- [ ] Type checks pass
- [ ] Linting passes
- [ ] Documentation verification passes
- [ ] Any release-adjacent focused checks for the changed surface have been run

## Publish

- [ ] Commit release metadata updates (`make release-commit`)
- [ ] Tag and push the release (`make release-tag`)
- [ ] Publish to PyPI (`make release-publish`)
- [ ] Verify the package on PyPI and confirm README rendering
- [ ] Test install the published version from PyPI
- [ ] Confirm the GitHub tag and release notes are present

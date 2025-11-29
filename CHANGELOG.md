---
title: "Changelog"
description: "Chronological log of notable TNH Scholar changes."
owner: ""
author: ""
status: current
created: "2025-02-28"
---
# Changelog

## Unreleased

### Documentation

- Standardized Markdown front matter, titles, and summary paragraphs across the docs tree (prompt-pattern files excluded pending dedicated schema).
- Updated `docs/docs-ops/markdown-standards.md` to spell out the Prompt Template front matter exception.
- Regenerated `documentation_index.md` after metadata fixes.
- **Filesystem-driven navigation**: Removed hardcoded `mkdocs.yaml` nav section and adopted `mkdocs-literate-nav` + `mkdocs-gen-files`.
  - Added `docs/nav.md` as the source of truth for navigation hierarchy.
  - MkDocs now automatically syncs nav with filesystem structure.
  - CLI docs and prompt template catalog are auto-generated from codebase artifacts.
- Fixed GitHub Actions workflows: YAML parsing errors in frontmatter, package installation, and GitHub Pages deployment permissions.
- Cleaned docstrings and type hints in the AI/text/audio/journal/ocr modules so MkDocs + Griffe stop emitting annotation warnings.
- Added project philosophy and vision documentation in `docs/project/` (philosophy.md, vision.md, principles.md, conceptual-architecture.md, future-directions.md).
- Added Parallax Press stakeholder overview document at `docs/tnh_scholar_parallax_overview.md`.
- Updated README.md with refined vision statement and getting started section.
- Updated docs/index.md with expanded vision and goals.
- Updated TODO.md with Part 4g documentation testing workflow.

### Developer Experience

- Added pre-commit hooks configuration with codespell, trailing whitespace removal, and basic file checks.
- Added lychee link checker with `.lychee.toml` configuration for documentation quality assurance.
- Added Makefile targets for link checking (`make check-links`, `make check-links-verbose`).
- Added `scripts/sync_root_docs.py` to sync root-level docs into MkDocs structure and wired into build system.
- **MkDocs strict mode cleanup**: Fixed all 136 warnings to achieve zero-warning builds.
  - Fixed autorefs warnings in TODO.md and regenerated mirrored root docs.
  - Aligned docstrings/signatures and type annotations across AI/text/audio/journal/OCR/utils modules to satisfy griffe.
  - Restored full mkdocstrings options in API documentation.
  - Created `docs/docs-ops/mkdocs-warning-backlog.md` to track progress and future doc additions.

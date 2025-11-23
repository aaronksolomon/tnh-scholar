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

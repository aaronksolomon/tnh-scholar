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
- Switched `mkdocs.yaml` to filesystem-driven navigation, added build warning filters via `sitecustomize.py`, and verified `poetry run mkdocs build` succeeds.
- Adopted `mkdocs-literate-nav` + `mkdocs-gen-files` so MkDocs builds consume the docs tree ordering automatically.
- Cleaned docstrings and type hints in the AI/text/audio/journal/ocr modules so MkDocs + Griffe stop emitting annotation warnings.

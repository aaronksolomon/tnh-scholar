---
title: "TNH Scholar CHANGELOG"
description: "Chronological log of notable TNH Scholar changes."
owner: ""
author: ""
status: current
created: "2025-02-28"
---
# TNH Scholar CHANGELOG

All notable changes to TNH Scholar will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Documentation

- **Auto-generated Documentation Index System** (2025-12-05):
  - Implemented dual-format auto-generated documentation indexing (ADR-DD01 Addendum 3)
  - Created `scripts/generate_doc_index.py` to generate both `documentation_index.md` (comprehensive searchable table) and `documentation_map.md` (hierarchical navigation)
  - Created `scripts/append_doc_map_to_index.py` to inject documentation map into index.md at build time
  - Documentation Map now auto-generated from filesystem and frontmatter metadata, eliminating manual maintenance
  - Both formats always in sync with actual documentation structure

- **Phase 2 Documentation Reorganization** (ADR-DD01/ADR-DD02 completion):
  - Completed comprehensive file reorganization: renamed 75+ architecture documents for clarity and consistency
  - Established canonical naming patterns: `adr-XX-descriptive-name.md` for ADRs, `system-design.md` for design docs
  - Created README.md files for major sections (architecture/, cli/, development/, getting-started/)
  - Removed obsolete CLI reference stubs (pending auto-generation)
  - Archived historical research artifacts and experiment files
  - Reorganized reference materials (yt-dlp docs, GPT-4 experiments) into categorized subdirectories
  - Updated all cross-references and internal links for reorganized structure
  - Achieved zero mkdocs build warnings after reorganization

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
- **Pattern→Prompt terminology standardization** (ADR-DD03 Phase 1): Updated all user-facing documentation to use "Prompt" instead of "Pattern" to align with industry standards and gen-ai-service refactoring.
  - Added historical terminology note to docs/index.md
  - Updated README, getting-started/, user-guide/ documentation
  - Renamed docs/user-guide/patterns.md → prompts.md
  - Renamed docs/architecture/pattern-system/ → prompt-system/
  - Updated ADR-DD01 and ADR-DD02 references
- **Documentation structure reorganization** (Python community standards):
  - Split design-guide.md into style-guide.md (code formatting, PEP 8) and design-principles.md (architectural patterns)
  - Moved object-service architecture to canonical location (development/architecture/ → architecture/object-service/)
  - Converted object-service-design-blueprint-v2 to ADR-OS01 (adopted V3, deleted V1)
  - Created design-overview.md and updated implementation-status.md with resolved items
  - Created forward-looking prompt-architecture.md documenting current V1 and planned V2 (PromptCatalog, fingerprinting, VS Code integration)
  - Moved pattern-core-design.md to archive/ with historical terminology note
  - Fixed all 35 mkdocs build --strict warnings from reorganization (link updates, regenerated index)
 - Navigation cleanup: removed the mirrored “Project Docs” (repo-root copies) from MkDocs navigation to avoid confusing duplication with `docs/project`.

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

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

## [Unreleased]

### Changed

- **tnh-gen Provenance YAML Frontmatter** (2025-12-30)
  - Switched file output provenance headers from HTML comments to YAML frontmatter
  - Updated CLI reference to document the YAML provenance format
  - Updated tests to assert YAML provenance markers
  - Files: `src/tnh_scholar/cli_tools/tnh_gen/output/provenance.py`, `tests/cli_tools/test_tnh_gen.py`, `docs/cli-reference/tnh-gen.md`

- **Documentation Standards - ADR Status Lifecycle** (2025-12-28)
  - Formalized ADR status lifecycle: `proposed` → `accepted` → `implemented` → `superseded`/`archived`
  - Clarified status separation: ADRs use `accepted`/`implemented`, guides/docs use `current`
  - Updated markdown-standards.md with universal vs ADR-specific status values and lifecycle flows
  - Updated adr-template.md with complete ADR status definitions and editing policy
  - Standardized on `rejected` (not `discarded`) for proposed-but-not-approved ADRs
  - Updated 3 implemented ADRs to correct status: ADR-TG01, ADR-TG01.1, ADR-DD03
  - Added TODO task for 25 historical ADRs marked `current` (low priority audit needed)
  - Files: `docs/docs-ops/markdown-standards.md`, `docs/docs-ops/adr-template.md`, `docs/architecture/tnh-gen/adr/*.md`, `docs/architecture/docs-system/adr/adr-dd03-pattern-to-prompt.md`, `TODO.md`

- **Documentation Build Infrastructure**
  - Updated `mkdocstrings-python` from 1.13.0 to 2.0.1 to resolve deprecation warnings
  - Eliminated all mkdocstrings-related deprecation warnings in docs build process
  - Build now completes cleanly without any warnings about deprecated import paths or handler methods
  - Updated references from deprecated `tnh-fab.md` to `tnh-gen.md` in CLI reference and user guide
  - Made dev dependencies non-optional in `pyproject.toml` (removed `optional = true` from dev group) to ensure `poetry install` always includes dev tools (pytest, mkdocs, mypy, etc.) and prevent accidental removal

### Fixed

- **Post-PR21 Merge Hotfix**
  - Fixed IndentationError in `filesystem_catalog_adapter.py` caused by duplicate lines from merge conflict resolution
  - Removed orphaned code fragments (lines 84-85) that were incomplete fragments of a closed `Prompt()` constructor
  - Restored test collection functionality (all 210 tests passing)
  - Preserved warning logging functionality (`_log_warnings` call at lines 82-83)

### Added

- **tnh-gen CLI Tool** - New prompt-driven content generation CLI (ADR-TG01, ADR-TG01.1, ADR-TG02)
  - **Core Implementation (Dec 2025)** - Initial CLI based on ADR-TG01 and ADR-TG02:
    - Typer-based command structure (`list`, `run`, `config`, `version` subcommands)
    - JSON-first output with structured metadata for VS Code integration
    - Layered configuration system (defaults → env → user → workspace → CLI overrides)
    - Multiple output formats (JSON, YAML, text, table) with provenance tracking
    - Protocol-based dependency injection (GenAIServiceProtocol, PromptCatalogProtocol)
    - Legacy prompt compatibility with graceful degradation and warnings
    - Environment variable loading (.env support) and input_text auto-injection
    - Variable precedence (inline vars > JSON file > input file)
    - Comprehensive test coverage for CLI commands and variable precedence
    - `src/tnh_scholar/cli_tools/tnh_gen/`: Core CLI package with modular command structure
    - `src/tnh_scholar/gen_ai_service/protocols.py`: Service and catalog protocol definitions
    - `tests/cli_tools/test_tnh_gen.py`: CLI test suite
  - **Human-Friendly Defaults (Dec 23-28, 2025)** - ADR-TG01.1 implementation:
    - Redesigned default output mode from JSON-first to human-readable text
    - Added `--api` flag for machine-readable contract output (VS Code, scripts)
    - Dual output modes: simplified text for CLI users, full JSON/YAML for programmatic consumption
    - Simplified default output: `list` shows readable descriptions, `run` shows text only
    - Added output format policy with validation: `--api` incompatible with `--format text/table`
    - Updated all commands (list, run, config, version) for dual-mode output
    - Enhanced error messages for dual-mode: plain text (human) vs JSON envelope (API)
    - Refactored run command from 222 lines with 90-line function to 380 lines with 12 focused functions
    - Introduced RunContext dataclass to encapsulate execution state
    - `src/tnh_scholar/cli_tools/tnh_gen/output/human_formatter.py`: Human-readable formatters
    - `src/tnh_scholar/cli_tools/tnh_gen/output/policy.py`: Format policy resolution/validation
    - Enhanced test coverage for API vs human output modes (100% coverage achieved Dec 28, 2025)
  - **Documentation (Dec 28, 2025)**:
    - `docs/cli-reference/tnh-gen.md`: Complete CLI reference documentation
    - `docs/cli-reference/archive/`: Archived legacy tnh-fab documentation
    - Updated getting-started guides with tnh-gen workflows
    - Updated CLI reference overview to feature tnh-gen

- **AI Text Processing Design Work**
  - Add ADR-AT03: Minimal ai_text_processing refactor for tnh-gen
  - Add ADR-AT03.1: Transition plan for phased implementation
  - Add ADR-AT03.2: NumberedText section boundary validation (ACCEPTED)
  - Add ADR-AT03.3: TextObject robustness improvements
  - Add ADR-AT04: Future AI text processing platform strategy

- **UI/UX Design Work**
  - Add ADR-VSC03: Python-JavaScript impedance investigation
  - Add ADR-VSC03.1: Investigation findings
  - Add ADR-VSC03.2: Real-world survey addendum
  - Add ADR-VSC03.3: Investigation synthesis
  - Add JVB Viewer ADR series for UI architecture

- **Test Coverage**
  - Add comprehensive CLI test coverage for json_to_srt, nfmt, sent_split, srt_translate, token_count
  - Add tnh_fab CLI tests for deprecated tool
  - Add shared CLI utilities module for test helpers
  - Add tnh-gen coverage tests achieving 100% module coverage (Dec 28, 2025)

### Changed

- **Type Safety Improvements**
  - Improved type safety across gen_ai_service modules
  - Changed RenderVars type from `Dict` to `Mapping[str, Any]` for broader compatibility
  - Fixed TypedDict optionality in `ConfigValuePayload` for mapping-compatible typing

- **Prompt System Enhancements**
  - Best-effort prompt loading with synthetic metadata for invalid frontmatter
  - Warnings field in PromptMetadata threaded through list/run outputs
  - Frontmatter parsing leniency (leading whitespace/BOM handling)
  - Invalid-metadata tagging for filtering in downstream clients
  - Whitelisted `input_text` in validator for legacy prompt compatibility

- **Documentation Infrastructure**
  - Added comprehensive tnh-gen CLI reference documentation (`docs/cli-reference/tnh-gen.md`)
  - Documented ADR-TG01.1 human-friendly defaults implementation
  - Enhanced ADR template with clearer structure and examples
  - Updated markdown standards for consistency
  - Refined human-AI software engineering principles
  - Improved documentation navigation (index, map)
  - Enhanced tnh-zen CSS styling for better readability
  - Updated docs/index.md with current feature status
  - Updated VS Code integration ADRs to use `--api` flag

## [0.2.2] - 2025-12-11

### Deprecated

- **tnh-fab CLI Tool**
  - Added comprehensive deprecation warnings for tnh-fab CLI tool
  - Runtime warning displayed on all tnh-fab command invocations
  - Help text updated to indicate deprecation and migration path to tnh-gen
  - All user-facing documentation updated with deprecation notices
  - Migration guidance pointing to TNH-Gen Architecture (ADR-TG01, ADR-TG02)

### Changed

- **Documentation Updates**
  - Updated README.md, docs/index.md with tnh-fab deprecation notices
  - Updated CLI reference documentation to mark tnh-fab as deprecated
  - Updated getting started guide and user guide with migration information
  - Updated architecture overview to note CLI tool transition
  - Changed status metadata for tnh-fab.md to "deprecated"

### Infrastructure

- **Makefile Improvements**
  - Minor robustness enhancements to build and release targets

## [0.2.1] - 2025-12-11

### Infrastructure & Tooling

This patch release focuses on hardening release automation, improving developer experience, and expanding project documentation infrastructure.

### Added

- **Archive System Infrastructure**
  - Comprehensive archive linking system with automated AGENTLOG management
  - Search capabilities for archived documentation and session logs
  - AGENTLOG template for structured agent work tracking
  - Issue draft system for capturing work-in-progress documentation

- **GenAI Service Core Implementation**
  - Complete policy, routing, and safety gate implementation per ADR-A08/A09/A11
  - Expanded test coverage (+128% improvement)
  - Sourcery fixes for code quality improvements

- **CI/CD Enhancements**
  - Local CI check command (`make ci-check`) for pre-push validation
  - Non-blocking quality checks (mypy, ruff, markdown lint) to prevent CI bottlenecks
  - Pre-commit hooks for notebook preparation and code quality

### Changed

- **Release Automation Hardening**
  - Makefile robustness improvements (UTF-8 handling, GitHub CLI access checks)
  - Enhanced version sync mechanism between pyproject.toml and TODO.md
  - Fixed Python heredoc formatting in release-publish target

- **Documentation Quality**
  - Codespell configuration now skips .txt archival files
  - Documentation metadata validation and normalization
  - Enhanced markdown link verification with warning-only default mode

### Fixed

- Node.js setup for markdown linting in CI
- Git workflow improvements with staleness detection
- Directory tree generation for CI verification
- Documentation build automation scripts

### Documentation

- Training pipeline research documentation
- Archive linking patterns (ADR-DD01 Addendum 4)
- Long-term project initiatives in TODO
- Comprehensive session logs in archive/agentlogs/

### Notes

- All 124 tests passing
- Pre-existing lint/type-check issues tracked separately (technical debt)
- Focus on infrastructure stability for rapid prototyping phase

## [0.2.0] - 2025-12-06

### Major Infrastructure Improvements

This release represents a significant maturation of project infrastructure, building on the documentation reorganization from v0.1.4. Combined, these releases deliver comprehensive documentation tooling and streamlined release automation.

**Versioning Note**: The v0.1.3 → v0.1.4 transition should have been v0.1.3 → v0.2.0 given the scope of documentation system changes. This release (v0.2.0) acknowledges both the documentation infrastructure (v0.1.4) and release automation improvements as a cohesive minor release milestone.

### Added

- **Comprehensive Dry-Run Mode for Release Workflow**
  - Preview all release commands before execution (`DRY_RUN=1` parameter)
  - Shows exact commands, commit messages, and tag messages before creating them
  - Prevents costly mistakes (git tags, PyPI publishes)
  - Supports all release targets: version bump, commit, tag, publish
  - Clear visual feedback with "🔍 DRY RUN MODE" indicator

- **Version Sync Pre-commit Hook**
  - Automatically validates `pyproject.toml` and `TODO.md` versions match
  - Prevents version drift bugs before commit
  - Clear error messages with fix instructions
  - Runs on every commit via pre-commit framework

- **Python-Native Link Checker**
  - Replaced lychee (Rust tool) with md-dead-link-check (Python package)
  - Pure Python toolchain, no external dependencies required
  - Configured to check external links only (MkDocs validates internal links)
  - Better Poetry integration and developer onboarding

- **Comprehensive Release Workflow Documentation**
  - Production-ready documentation at `docs/development/release-workflow.md`
  - Complete guide covering prerequisites, step-by-step workflow, troubleshooting
  - Conforms to ADR-DD01 markdown standards
  - Documents dry-run mode, automation features, and best practices
  - Examples, tips for efficient releases, and conventional commit guidance

- **Markdown Link Standard Enforcement**
  - Added validation to detect relative links (`../`) in documentation
  - Enforces absolute path links from `/docs/` root
  - Updated markdown standards with clear examples and guidelines
  - Prevents MkDocs strict mode issues

### Changed

- **Simplified Developer Setup**
  - Removed non-Python tooling hard requirements (lychee now optional)
  - All documentation tools managed by Poetry
  - Improved new contributor onboarding experience

- **Code Quality Improvements**
  - Applied ruff auto-fixes to 21 files (28 automatic style fixes)
  - Import organization and sorting
  - Removed unused imports and trailing whitespace
  - All tests passing after cleanup (94/94)

### Infrastructure

- **Release Automation Phase 2**
  - Restored full `docs-verify` pipeline with Python-native tools
  - Enhanced Makefile with dry-run support for all release targets
  - Version sync validation integrated into git workflow
  - Reduced external tool dependencies

### Notes

- No code functionality changes - purely tooling, automation, and documentation infrastructure
- This release focuses on making the development and release process "feel very smooth"
- External link checking now uses pure Python stack
- All 94 tests passing with 1 deprecation warning (audioop in pydub, Python 3.13)

## [0.1.4] - 2025-12-05

### Added

- **Documentation System Reorganization (Phase 1)** - Major infrastructure overhaul:
  - New hierarchical directory structure with 13 architecture modules
  - Automated documentation tooling (8 build scripts for generation and validation)
  - Comprehensive markdown standards with quality enforcement (markdownlint, codespell, lychee)
  - Auto-generated documentation index and navigation map
  - MkDocs configuration rewrite with filesystem-driven navigation
  - Custom zen-inspired theme with collapsible navigation
  - GitHub Pages deployment with CI/CD verification
  - Drift monitoring between README.md and docs/index.md

- **Pattern → Prompt Terminology Standardization (ADR-DD03 Phase 1)**:
  - Renamed user-facing documentation from "Pattern" to "Prompt" terminology
  - Updated README.md, docs/index.md, getting-started/, user-guide/
  - Retained legacy compatibility (TNH_PATTERN_DIR, --pattern flags)

- **Release Automation (Phase 1)**:
  - Makefile release targets for streamlined release workflow
  - CHANGELOG generator script (auto-generate from git commits)
  - Automated version bump, commit, tag, and publish workflow
  - Reduces release time from 2 hours to 10 minutes (83% reduction)

- **Architecture Documentation**:
  - 3 new ADRs: ADR-DD01 (docs reorganization), ADR-DD02 (navigation strategy), ADR-DD03 (terminology migration)
  - Reorganized and standardized existing ADRs across 13 architecture modules
  - Created comprehensive architecture overview and index pages
  - 30+ design documents reorganized and renamed to match standards

- **Enhanced Root Documentation**:
  - AGENTLOG.md: Detailed session logs for all work sessions
  - CHANGELOG.md: Maintained and updated changelog
  - Expanded README.md with refined vision and architecture snapshot
  - Restructured TODO.md with priority roadmap (Priority 1-3)
  - Enhanced CONTRIBUTING.md and DEV_SETUP.md

- **Build & Quality Infrastructure**:
  - Pre-commit hooks configuration for markdown linting and spell checking
  - Makefile targets: `docs`, `docs-verify`, `docs-quickcheck`, `check-drift`, `release-*`
  - .lychee.toml for link checking configuration
  - .codespell-ignore.txt for technical/dharma terms
  - .markdownlint.json for markdown linting rules

- **Research Documentation**:
  - New: RAG research directions document
  - Reorganized: Existing research files renamed to match markdown standards

### Changed

- **Directory Structure**: Reorganized from flat to hierarchical architecture
  - docs/cli/ → docs/cli-reference/ (consolidated CLI documentation)
  - docs/design/ → docs/architecture/<module>/ (module-specific organization)
  - docs/user-guide/patterns.md → docs/user-guide/prompt-system.md
  - Split design-guide.md into style-guide.md and design-principles.md (Python standards)
  - Moved object-service architecture from development/ to architecture/

- **CI/CD Workflows**:
  - Enhanced .github/workflows/ci.yml with markdownlint, codespell, link checking
  - Added .github/workflows/docs.yml for documentation build and GitHub Pages deployment

- **Navigation**: MkDocs configuration rewrite with absolute link validation enabled

### Documentation

- Established comprehensive markdown standards in docs/docs-ops/markdown-standards.md
- ADR naming convention: `adr-<modulecode><number>-<descriptor>.md`
- Module-specific storage: `docs/architecture/<module>/adr/` organization
- Archive structure: `docs/archive/` (top-level) + `docs/architecture/<module>/archive/` (module-specific)

### Notes

- **No breaking changes**: Purely documentation infrastructure improvements
- **Navigation changes**: Users should update bookmarks from docs/cli/ to docs/cli-reference/
- **Phase 2 work**: Outstanding items tracked in TODO #9 (archive expansion, gap filling, additional testing)
- **Merge PR**: Merged docs-reorg branch with 96 commits, 429 files changed (67,885 additions, 7,616 deletions)

### References

- [ADR-DD01: Documentation System Reorganization Strategy](docs/architecture/docs-system/adr/adr-dd01-docs-reorg-strategy.md)
- [ADR-DD02: Main Content and Navigation Strategy](docs/architecture/docs-system/adr/adr-dd02-main-content-nav.md)
- [ADR-DD03: Pattern→Prompt Terminology Migration](docs/architecture/docs-system/adr/adr-dd03-pattern-to-prompt.md)
- [TODO #9: Documentation Reorganization](TODO.md#9--documentation-reorganization-adr-dd01--adr-dd02)

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

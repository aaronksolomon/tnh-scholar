---
title: "TNH Scholar TODO List"
description: "Roadmap tracking the highest-priority TNH Scholar tasks and release blockers."
owner: ""
author: ""
status: processing
created: "2025-01-20"
---
# TNH Scholar TODO List

Roadmap tracking the highest-priority TNH Scholar tasks and release blockers.

> **Last Updated**: 2025-11-16
> **Version**: 0.1.3 (Alpha)
> **Status**: Active Development - Quick Wins Phase

---

## Priority Roadmap

This section organizes work into three priority levels based on criticality for production readiness.

### Priority 1: Critical Path to Beta

**Goal**: Remove blockers to production readiness. These items must be completed before beta release.

**Status**: 3/5 Complete ✅

#### 1. ✅ Add pytest to CI

- **Status**: COMPLETED
- **Location**: [.github/workflows/ci.yml](.github/workflows/ci.yml)
- **What**: Tests now run in CI with coverage reporting
- **Command**: `pytest --maxfail=1 --cov=tnh_scholar --cov-report=term-missing`

#### 2. ✅ Fix Packaging Issues

- **Status**: COMPLETED
- **Location**: [pyproject.toml](pyproject.toml)
- **What**:
  - ✅ Runtime dependencies declared (pydantic-settings, python-json-logger, tenacity)
  - ✅ Python version pinned to 3.12.4
  - ⚠️ Pattern directory import issue still pending (see Configuration & Data Layout below)

#### 3. ✅ Remove Library sys.exit() Calls

- **Status**: COMPLETED
- **Location**: [gen_ai_service/infra/issue_handler.py](src/tnh_scholar/gen_ai_service/infra/issue_handler.py)
- **What**: Library code now raises ConfigurationError by default
- **Test**: [tests/gen_ai_service/test_service.py::test_missing_api_key_raises_configuration_error](tests/gen_ai_service/test_service.py)

#### 4. 🚧 Implement Core Stubs

- **Status**: IN PROGRESS - Needs Implementation
- **Priority**: HIGH
- **Tasks**:
  - [ ] <https://github.com/aaronksolomon/tnh-scholar/blob/main/src/tnh_scholar/gen_ai_service/config/params_policy.py> — Implement actual policy logic (currently pass-through)
    - Policy precedence: call hint → prompt metadata → defaults
    - Cache Settings instead of re-instantiating per call
  - [ ] <https://github.com/aaronksolomon/tnh-scholar/blob/main/src/tnh_scholar/gen_ai_service/routing/model_router.py> — Implement model selection logic (currently echoes input)
    - Intent-based routing
    - Provider capability mapping
  - [ ] <https://github.com/aaronksolomon/tnh-scholar/blob/main/src/tnh_scholar/gen_ai_service/safety/safety_gate.py> — Implement content safety (currently placeholder)
    - Pre-submission content checks
    - Post-completion validation
  - [ ] <https://github.com/aaronksolomon/tnh-scholar/blob/main/src/tnh_scholar/gen_ai_service/mappers/completion_mapper.py> — Surface provider error bodies
    - Structured error propagation
    - Don't just raise ValueError on non-OK status

#### 5. 🚧 Unify OpenAI Clients

- **Status**: PHASE 1 COMPLETE ✅ 
- **Priority**: HIGH
- **ADR**: [ADR-A13: Legacy Client Migration](docs/architecture/gen-ai-service/adr/adr-a13-legacy-client-migration.md)
- **Plan**: [Migration Plan](docs/architecture/gen-ai-service/design/migration-plan.md)
- **Problem**: Two implementations causing code divergence (legacy client now removed)
  - **Modern**: [gen_ai_service/providers/openai_client.py](src/tnh_scholar/gen_ai_service/providers/openai_client.py) - typed, retrying
  - **Legacy**: `openai_interface/` – removed as of Phase 6
- **Phase 1: Utilities & Adapters** ✅ COMPLETE
  - [x] Create [token_utils.py](src/tnh_scholar/gen_ai_service/utils/token_utils.py) - token counting
  - [x] Create [response_utils.py](src/tnh_scholar/gen_ai_service/utils/response_utils.py) - response extraction
  - [x] Create [simple_completion.py](src/tnh_scholar/gen_ai_service/adapters/simple_completion.py) - migration adapter
  - [x] Add comprehensive tests (33 new tests)
  - [x] Fix hard-coded literals (use policy dataclass)
- **Phase 2-6: Migration**
  - [x] Phase 2: Migrate core modules (ai_text_processing, journal_processing)
  - [x] Phase 3: Migrate CLI tools
  - [x] Phase 4: Migrate tests
  - [x] Phase 5: Update notebooks
  - [x] Phase 6: Delete legacy code (openai_interface/)

---

### Priority 2: Beta Quality

**Goal**: Improve maintainability, user experience, and code quality for beta release.

#### 6. 🚧 Expand Test Coverage

- **Status**: NOT STARTED
- **Current Coverage**: ~5% (4 test modules)
- **Target**: 50%+ for gen_ai_service
- **Tasks**:
  - [ ] GenAI service flows: prompt rendering, policy resolution, provider adapters
  - [ ] CLI integration tests (option parsing, environment validation)
  - [ ] Configuration loading edge cases
  - [ ] Error handling scenarios
  - [ ] Pattern catalog validation

#### 7. 🚧 Consolidate Environment Loading

- **Status**: NOT STARTED
- **Problem**: Multiple modules call `load_dotenv()` at import time
  - <https://github.com/aaronksolomon/tnh-scholar/blob/main/src/tnh_scholar/ai_text_processing/prompts.py>
  - <https://github.com/aaronksolomon/tnh-scholar/blob/main/src/tnh_scholar/audio_processing/diarization/pyannote_client.py>
- **Tasks**:
  - [ ] Create single startup hook for dotenv loading
  - [ ] Use Pydantic Settings consistently
  - [ ] Pass configuration objects instead of `os.getenv()` calls
  - [ ] Remove import-time side effects

#### 8. 🚧 Clean Up CLI Tool Versions

- **Status**: NOT STARTED
- **Location**: [cli_tools/audio_transcribe/](src/tnh_scholar/cli_tools/audio_transcribe/)
- **Tasks**:
  - [x] Remove [audio_transcribe0.py](src/tnh_scholar/cli_tools/audio_transcribe/audio_transcribe0.py)
  - [x] Remove audio_transcribe1.py
  - [x] Remove audio_transcribe2.py
  - [x] Keep only current version
  - [ ] Create shared utilities (argument parsing, environment validation, logging)

#### 9. 🚧 Documentation Reorganization (ADR-DD01 & ADR-DD02)

- **Status**: IN PROGRESS (Parts 1–4 ✅, Part 3b ✅ COMPLETE, Parts 5+ remaining)
- **Reference**:
  - [ADR-DD01: Docs Reorganization Strategy](docs/architecture/docs-system/adr/adr-dd01-docs-reorg-strat.md)
  - [ADR-DD02: Documentation Main Content and Navigation Strategy](docs/architecture/docs-system/adr/adr-dd02-docs-content-nav.md) ✅ APPROVED
- **Goal**: Execute the phased documentation overhaul for `docs/` tree, keep README ≈ docs/index with drift monitoring, automate verification. **Note**: `patterns/` directory is managed separately (TODO #16).
- **Next Sequence**: Part 5 (Archive) → Part 6 (Gap Filling) → Part 7 (Standalone Tasks)
- **Checkpoints / Tasks**:
  1. **Inventory + Tagging**
     - [x] Catalog every Markdown file (owner, status: current/needs-update/historical)
     - [x] Add front matter metadata + PromptTemplate terminology notes
     - [ ] Identify raw research assets to offload to external storage
  2. **Filesystem Reorg**
     - [x] Create the target hierarchy (overview, getting-started, user-guide, cli-reference, prompt-templates, api-reference, architecture/adr, development, research, docs-ops, archive)
     - [x] Move existing docs into the new layout with stub `index.md` files
     - [ ] Tag archival folders explicitly for mkdocs-literate-nav auto-generation
  3. **Terminology + README Sweep** (Part 3b: ✅ COMPLETED - ADR-DD02)
     - [x] **3b (COMPLETED)**: Designed content architecture for README.md and docs/index.md (ADR-DD02)
     - [x] Implemented drift reporting script (`check_readme_docs_drift.py`) for non-blocking sync monitoring
     - [x] Established persona-based navigation strategy (Practitioners, Developers, Researchers)
     - [x] Updated markdown standards to enforce exact YAML title ↔ heading match
     - [ ] Rename Pattern → PromptTemplate across docs text (incl. CLI references)
     - [ ] Add prompt authoring schema guidance (deferred to Part 6)
  4. **MkDocs + Automation** (✅ ALL PARTS COMPLETE)
     - [x] Install `mkdocs-literate-nav` and `mkdocs-gen-files` to dev dependencies
     - [x] Restructure `mkdocs.yaml` to remove hardcoded nav and use literate-nav plugin
     - [x] Create `docs/nav.md` as the source-of-truth navigation hierarchy
     - [x] Configure gen-files to auto-generate CLI docs and prompt template catalogs
     - [x] Add doc-index automation (`scripts/generate_doc_index.py`) and flag generated outputs
     - [x] **4b (COMPLETED)**: Add doc-generation scripts (`generate_cli_docs.py`, `sync_readme.py`) and Makefile `docs` targets
     - [x] **4c (COMPLETED)**: Wire CI to run `mkdocs build` + doc verification + GitHub Pages deployment
     - [x] Add markdownlint to CI/CD (MD025/MD013 ignored via `.markdownlint.json`)
     - [x] **4d (COMPLETED)**: Normalize internal documentation links; refactor doc-index generation to single `docs/documentation_index.md` with relative links
     - [x] **4e (COMPLETED)**: Enable filesystem-driven nav with mkdocs-literate-nav
     - [x] **4f (COMPLETED - ADR-DD02)**: Add drift reporting (`check_readme_docs_drift.py`) with Makefile target and CI integration
     - [ ] **4g (PLANNED)**: Documentation testing and validation workflow
       - **Phase 1: Quick Wins** (CI now)
         - [x] Enable `mkdocs build --strict` in `docs-verify` (fail on warnings)
         - [x] Add link checking with `lychee` + `.lychee.toml` (ignore flaky/external as needed)
         - [x] Add `codespell` with `.codespell-ignore.txt` (dharma terms/proper nouns); wire into pre-commit/CI
         - [x] Create `docs-quickcheck` make target: sync_root_docs → mkdocs --strict → lychee → codespell
       - **Phase 2: Metadata Validation** (Beta gate)
         - [ ] Add `scripts/check_doc_metadata.py` to validate front matter (title/description/status) and warn on empty descriptions
         - [ ] Detect orphaned docs not reachable from nav (using generated nav) and report missing descriptions
         - [ ] Add metadata check to pre-commit and CI
       - **Phase 3: Coverage & Structure** (Prod polish)
         - [ ] Add `interrogate` for Python docstring coverage (threshold on `src/tnh_scholar`, skip tests/scripts)
         - [ ] Validate ADRs follow template sections (Context/Decision/Consequences) + required front matter
         - [ ] Run offline/internal link check on built site (`lychee --offline` on `site/`)
         - [ ] Optional: add `vale` with a minimal style guide for docs tone/consistency
  5. **Historical Archive + Discoverability**
     - [ ] Move legacy ADRs/prototypes/research transcripts into `docs/archive/**`
     - [ ] Create archive index + add summary links from primary sections
     - [ ] Host raw transcripts externally (S3/KB) and link from summaries
  6. **Backlog + Gap Filling**
     - [ ] Populate `docs/docs-ops/roadmap.md` with missing topics (PromptTemplate catalog, workflow playbooks, evaluation guides, KB, deployment, research summaries, doc ops)
     - [ ] Open GitHub issues per backlog item with owners/priorities
  7. **Outstanding Standalone Tasks**
     - [ ] Deprecate outdated CLI examples (e.g., `punctuate` usage) once cli-reference regenerates
     - [ ] Add practical user guides for new features post-reorg
     - [ ] Create refreshed architecture overview page within `architecture/`
     - [ ] Finish Pattern → PromptTemplate rename across docs/CLI text
     - [ ] Establish research artifact archival workflow (external storage + summary linking)
  8. **Include Root Markdown Files in MkDocs Navigation**
     - **Status**: NOT STARTED
     - **Priority**: MEDIUM (Part of docs-reorg cleanup)
     - **Goal**: Make root-level config/meta files (README, TODO, CHANGELOG, CONTRIBUTING, DEV_SETUP, release_checklist) discoverable in mkdocs navigation and documentation index
     - **Approach**: Build-time copy with "DO NOT EDIT" warnings
       - [ ] Create `docs/project/` directory for project meta-documentation
       - [ ] Create `scripts/sync_root_docs.py` to copy root markdown files:
         - [ ] Copy root `.md` files (README, TODO, CHANGELOG, CONTRIBUTING, DEV_SETUP, release_checklist) to `docs/project/`
         - [ ] Prepend HTML comment warning to each copied file: `<!-- DO NOT EDIT: Auto-generated from /{filename}. Edit the root file instead. -->`
         - [ ] Mark files with `auto_generated: true` in front matter or add to existing front matter
       - [ ] Add `docs/project/*.md` to `.gitignore` (except `index.md` if hand-written)
       - [ ] Update `scripts/generate_mkdocs_nav.py` or add to gen-files plugin to run sync script
       - [ ] Update Makefile `docs` target to run sync script before mkdocs build
       - [ ] Test documentation build: `make docs`
       - [ ] Verify copied files appear in navigation and documentation index
       - [ ] Update internal doc references from GitHub URLs to relative paths:
         - [ ] Search: `https://github.com/aaronksolomon/tnh-scholar/blob/main/CONTRIBUTING.md`
         - [ ] Replace with: `project/CONTRIBUTING.md` (or appropriate relative path)
       - [ ] Verify docs/index.md links resolve correctly
       - [ ] Create `docs/project/index.md` with section overview explaining these are project meta-docs
       - [ ] Add CI check to verify docs/project/ files are in sync (optional safety check)

#### 10. 🚧 Type System Improvements

- **Status**: PARTIAL (see detailed section below)
- **Current**: 58 errors across 16 files
- **Tasks**: See [Type System Improvements](#type-system-improvements) section below

---

### Priority 3: Production Readiness

**Goal**: Long-term sustainability, advanced features, and production hardening.

#### 11. 🚧 Refactor Monolithic Modules

- **Status**: NOT STARTED
- **Targets**:
  - [ ] <https://github.com/aaronksolomon/tnh-scholar/blob/main/src/tnh_scholar/ai_text_processing/prompts.py> (34KB)
    - Break into: prompt model, repository manager, git helpers, lock helpers
    - Add docstrings and tests for each unit
    - Document front-matter schema
  - [ ] <https://github.com/aaronksolomon/tnh-scholar/blob/main/src/tnh_scholar/journal_processing/journal_process.py> (28KB)
    - Identify focused units
    - Extract reusable components

#### 12. 🚧 Complete Provider Abstraction

- **Status**: NOT STARTED
- **Tasks**:
  - [ ] Implement [Anthropic adapter](src/tnh_scholar/gen_ai_service/providers/anthropic_adapter.py)
  - [ ] Add provider-specific error handling
  - [ ] Test fallback/retry across providers
  - [ ] Provider capability discovery
  - [ ] Multi-provider cost optimization

#### 13. 🚧 Knowledge Base Implementation

- **Status**: DESIGN COMPLETE
- **ADR**: [ADR-K01: Preliminary Architectural Strategy](docs/architecture/knowledge-base/adr/adr-k01-preliminary-architectural-design.md)
- **Tasks**:
  - [ ] Implement Supabase integration
  - [ ] Vector search functionality
  - [ ] Query capabilities
  - [ ] Semantic similarity search

#### 14. 🚧 Developer Experience Improvements

- **Status**: NOT STARTED
- **Tasks**:
  - [ ] Add pre-commit hooks (Black, Ruff, MyPy)
  - [ ] Create Makefile/justfile for common tasks (lint, test, docs, format)
  - [ ] Add contribution templates
  - [ ] Improve CONTRIBUTING.md
  - [ ] Release automation
  - [ ] Changelog automation

#### 15. 🚧 Configuration & Data Layout

- **Status**: NOT STARTED
- **Priority**: HIGH (blocks pip install)
- **Problem**: [src/tnh_scholar/**init**.py](src/tnh_scholar/__init__.py) raises FileNotFoundError when repo layout missing
- **Tasks**:
  - [ ] Package pattern assets as resources
  - [ ] Make patterns directory optional
  - [ ] Move directory checks to CLI entry points only
  - [ ] Ensure installed wheels work without patterns/ directory

#### 16. 🚧 Prompt Catalog Safety

- **Status**: NOT STARTED
- **Priority**: MEDIUM
- **Problem**: Adapter doesn't handle missing keys or invalid front-matter gracefully
- **Tasks**:
  - [ ] Add manifest validation
  - [ ] Implement caching
  - [ ] Better error messages (unknown prompt, hash mismatch)
  - [ ] Front-matter validation
  - [ ] Document pattern schema

---

## Type System Improvements

**Current Status**:

- Total Type Errors: 58
- Affected Files: 16
- Files Checked: 62

### High Priority (Pre-Beta)

#### Install Missing Type Stubs ✅ COMPLETED

- [x] Install required type stub packages:
  - [x] types-PyYAML
  - [x] types-requests

#### Critical Type Errors

- [ ] Fix audio processing boundary type inconsistencies
  - [ ] Resolve return type mismatches in `audio_processing/audio.py`
  - [ ] Standardize Boundary type usage
- [ ] Fix core text processing type errors
  - [ ] Fix str vs list[str] return type in `bracket.py`
  - [ ] Resolve object extension error in `video_processing.py`
- [ ] Address function redefinitions in `run_oa_batch_jobs.py`:
  - [ ] Resolve `calculate_enqueued_tokens` redefinition
  - [ ] Fix `process_batch_files` redefinition
  - [ ] Fix `main` function redefinition

### Medium Priority (Beta Stage)

#### Add Missing Type Annotations

- [ ] Add variable type annotations:
  - [ ] `attributes_with_values` in clean_parse_tag.py
  - [ ] `current_page` in xml_processing.py
  - [ ] `covered_lines` in ai_text_processing.py
  - [ ] `seen_names` in patterns.py

#### Pattern System Type Improvements

- [ ] Fix Pattern class type issues:
  - [ ] Resolve `apply_template` attribute errors
  - [ ] Fix `name` attribute access issues
  - [ ] Standardize Pattern type definition

### Low Priority (Post-Beta)

#### General Type Improvements

- [ ] Clean up Any return types:
  - [ ] Properly type `getch` handling in user_io_utils.py
  - [ ] Type language code returns in lang.py
  - [ ] Remove Any returns in ai_text_processing.py
- [ ] Standardize type usage:
  - [ ] Implement consistent string formatting in patterns.py
  - [ ] Update callable type usage
  - [ ] Clean up type hints in openai_interface.py

### Implementation Strategy

#### Phase 1: Core Type Safety

- [ ] Focus on high-priority items affecting core functionality
- [x] Implement type checking in CI pipeline
- [ ] Document type decisions

#### Phase 2: Beta Preparation

- [ ] Address medium-priority items
- [ ] Set up pre-commit type checking hooks
- [ ] Update documentation with type information

#### Phase 3: Post-Beta Cleanup

- [ ] Handle low-priority type improvements
- [ ] Implement stricter type checking settings
- [ ] Full type coverage audit

### Typing Guidelines

**Standards**:

- [ ] Use explicit types over Any
- [ ] Create type aliases for complex types
- [ ] Document typing decisions
- [ ] Implement consistent Optional handling

**References**:

- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Type Checking Best Practices](https://mypy.readthedocs.io/en/stable/common_issues.html)

---

## Additional Tasks

### Medium Priority

#### Improve NumberedText Ergonomics

- **Location**: [text_processing/numbered_text.py](src/tnh_scholar/text_processing/numbered_text.py)
- **Problem**: Constructor raises for content=None even though typed as optional
- **Tasks**:
  - [ ] Decide whether empty content should mean "no lines yet"
  - [ ] Add file-based round-trip tests
  - [ ] Trim redundant pytest boilerplate in tests

#### Logging System Scope

- **Location**: [logging_config.py](src/tnh_scholar/logging_config.py)
- **Problem**: Modules call setup_logging individually
- **Tasks**:
  - [ ] Define single application bootstrap
  - [ ] Document logger acquisition pattern (get_logger only)
  - [ ] Create shared CLI bootstrap helper

### Low Priority

#### Package API Definition

- **Status**: Deferred during prototyping
- **Tasks**:
  - [ ] Review and document all intended public exports
  - [ ] Implement `__all__` in key `__init__.py` files
  - [ ] Verify exports match documentation

#### Repo Hygiene

- **Problem**: Generated artifacts in repo
- **Files**: build/, dist/, site/, current_pip_freeze.txt, mypy_errors.txt, project_directory_tree.txt
- **Tasks**:
  - [ ] Add to .gitignore
  - [ ] Document regeneration process
  - [ ] Rely on release pipelines for builds

#### Notebook & Research Management

- **Location**: notebooks/, docs/research/
- **Problem**: Valuable but not curated exploratory work
- **Tasks**:
  - [ ] Adopt naming/linting convention
  - [ ] Keep reproducible notebooks in notebooks/experiments
  - [ ] Publish vetted analyses to docs/research via nbconvert
  - [ ] Archive obsolete notebooks

---

## Progress Summary

**Quick Wins Completed (2025-11-16)**:

- ✅ Packaging & dependencies fixed
- ✅ CI pytest integration
- ✅ Library exception handling (removed sys.exit)

**Next Sprint Focus**:

- 🎯 Implement core stubs (policy, routing, safety)
- 🎯 Unify OpenAI clients
- 🎯 Expand test coverage to 50%+

**Beta Blockers**:

- Configuration & data layout (pattern directory)
- Core stub implementations
- OpenAI client unification

---

## Notes for Maintainers

### Test Running

```bash
# Run all tests with coverage
poetry run pytest --maxfail=1 --cov=tnh_scholar --cov-report=term-missing -v

# Run specific test file
poetry run pytest tests/gen_ai_service/test_service.py -v

# Run with coverage report
poetry run pytest --cov=tnh_scholar --cov-report=html
```

### Type Checking

```bash
# Check types
poetry run mypy src/

# Generate error report
poetry run mypy src/ > mypy_errors.txt
```

### Code Quality

```bash
# Format code
poetry run black src/ tests/

# Lint
poetry run ruff check src/

# Run all checks (as CI does)
poetry run black --check src/
poetry run mypy src/
poetry run ruff check src/
poetry run pytest --maxfail=1 --cov=tnh_scholar
```

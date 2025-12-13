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

> **Last Updated**: 2025-12-12
> **Version**: 0.2.2 (Alpha)
> **Status**: Active Development - ADR-AT03 Implementation Phase

---

## Priority Roadmap

This section organizes work into three priority levels based on criticality for production readiness.

### Priority 1: Critical Path to Beta

**Goal**: Remove blockers to production readiness. These items must be completed before beta release.

**Status**: 4/5 Complete ✅

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

- **Status**: PRELIMINARY IMPLEMENTATION COMPLETE ✅ - Needs Polish & Registry Integration
- **Priority**: HIGH
- **Review**: Code review completed 2025-12-10 - **Grade: A- (92/100)** ⭐⭐⭐⭐⭐
- **Core Implementation**:
  - [x] [params_policy.py](src/tnh_scholar/gen_ai_service/config/params_policy.py) — Policy precedence implemented ✅
    - ✅ Policy precedence: call hint → prompt metadata → defaults
    - ✅ Settings cached via `@lru_cache` (excellent optimization)
    - ✅ Strong typing with `ResolvedParams` Pydantic model
    - ✅ Routing diagnostics in `routing_reason` field
    - **Score**: 95/100 - Excellent implementation
  - [x] [model_router.py](src/tnh_scholar/gen_ai_service/routing/model_router.py) — Capability-based routing implemented ✅
    - ✅ Declarative routing table with `_MODEL_CAPABILITIES`
    - ✅ Structured output fallback (JSON mode capability switching)
    - ✅ Intent-aware architecture foundation
    - ⚠️ Intent routing currently placeholder (line 98-101)
    - **Score**: 92/100 - Strong implementation
  - [x] [safety_gate.py](src/tnh_scholar/gen_ai_service/safety/safety_gate.py) — Three-layer safety checks implemented ✅
    - ✅ Character limit, context window, budget estimation
    - ✅ Typed exceptions (`SafetyBlocked`)
    - ✅ Structured `SafetyReport` with actionable diagnostics
    - ✅ Content type handling (string/list with warnings)
    - ✅ Prompt metadata integration (`safety_level`)
    - ⚠️ Price constant hardcoded (line 30: `_PRICE_PER_1K_TOKENS = 0.005`)
    - ⚠️ Post-check currently stubbed
    - **Score**: 94/100 - Excellent implementation
  - [x] [completion_mapper.py](src/tnh_scholar/gen_ai_service/mappers/completion_mapper.py) — Bi-directional mapping implemented ✅
    - ✅ Clean transport → domain transformation
    - ✅ Error details surfaced in `policy_applied`
    - ✅ Status handling (OK/FAILED/INCOMPLETE)
    - ✅ Pure mapper functions (no side effects)
    - ⚠️ `policy_applied` uses `Dict[str, object]` (should be more specific)
    - **Score**: 91/100 - Strong implementation

- **High Priority (Before Merging)**:
  - [x] Add Google-style docstrings to public functions (see [style-guide.md](docs/development/style-guide.md))
    - `apply_policy()`, `select_provider_and_model()`, `pre_check()`, `post_check()`, `provider_to_completion()`
  - [x] Move `_PRICE_PER_1K_TOKENS` constant to Settings or registry (blocks ADR-A14)
    - Moved to `Settings.price_per_1k_tokens`; safety gate now consumes setting.
  - [x] Type tightening in completion_mapper
    - Added `PolicyApplied` alias (`dict[str, str | int | float]`).
  
- **Medium Priority (V1 Completion)**:
  - [ ] Promote `policy_applied` typing to a shared domain type (CompletionEnvelope) to avoid loose `dict` usage across the service.

  - [ ] Capability registry extraction (**→ ADR-A14**)
    - Create `runtime_assets/registries/providers/openai.jsonc`
    - Implement `RegistryLoader` with JSONC support
    - Refactor `model_router.py` to use registry
    - Refactor `safety_gate.py` to use registry pricing
    - See: [ADR-A14: File-Based Registry System](docs/architecture/gen-ai-service/adr/adr-a14-file-based-registry-system.md)
  - [ ] Intent routing implementation
    - Document planned approach or create follow-up issue
    - Current: placeholder at [model_router.py:98-101](src/tnh_scholar/gen_ai_service/routing/model_router.py#L98-L101)
  - [ ] Post-check safety implementation
    - Add content validation logic to `safety_gate.post_check()`
    - Current: stubbed at [safety_gate.py:124-133](src/tnh_scholar/gen_ai_service/safety/safety_gate.py#L124-L133)

- **Low Priority (Future Work)**:
  - [ ] Warning enum system
    - Create typed warning codes instead of strings
    - Affects: safety_gate, completion_mapper, model_router
  - [ ] Enhanced diagnostics
    - More granular routing reasons
    - Detailed safety check diagnostics
  - [ ] **Message.content Type Architecture Investigation** (design quality, non-blocking)
    - **Location**: [gen_ai_service/models/domain.py:92-96](src/tnh_scholar/gen_ai_service/models/domain.py#L92-L96)
    - **Issue**: Sourcery identifies `Union[str, List[ChatCompletionContentPartParam]]` as source of complexity
    - **Context**: Current design intentionally supports OpenAI's flexible content API (plain text OR structured parts with images/etc)
    - **Investigation Areas**:
      - Document current usage patterns across codebase
      - Assess downstream complexity: where are type checks needed?
      - Evaluate normalization strategies (always list? separate fields? utility methods?)
      - Consider provider compatibility (Anthropic, etc)
      - Draft ADR or addendum to existing GenAI ADRs if design change warranted
    - **Impact**: Affects message representation throughout GenAIService

- **Review Summary**:
  - **Strengths**: Excellent architectural alignment, strong typing, proper separation of concerns, clean integration
  - **Minor Issues**: Missing function docstrings, hardcoded price constant, one dict type needing refinement
  - **Overall**: Production-ready with minor polish (estimated 1 hour total)
  - **Detailed Review**: See code review session 2025-12-10

#### 5. ✅ Unify OpenAI Clients

- **Status**: COMPLETED ✅
- **Priority**: HIGH
- **ADR**: [ADR-A13: Legacy Client Migration](docs/architecture/gen-ai-service/adr/adr-a13-migrate-openai-to-genaiservice.md)
- **Plan**: [Migration Plan](docs/architecture/gen-ai-service/design/openai-interface-migration-plan.md)
- **What**: Unified OpenAI client implementations by migrating from legacy to modern architecture
  - **Modern**: [gen_ai_service/providers/openai_client.py](src/tnh_scholar/gen_ai_service/providers/openai_client.py) - typed, retrying
  - **Legacy**: `openai_interface/` – removed as of Phase 6
- **Phase 1: Utilities & Adapters** ✅ COMPLETE
  - [x] Create [token_utils.py](src/tnh_scholar/gen_ai_service/utils/token_utils.py) - token counting
  - [x] Create [response_utils.py](src/tnh_scholar/gen_ai_service/utils/response_utils.py) - response extraction
  - [x] Create [simple_completion.py](src/tnh_scholar/gen_ai_service/adapters/simple_completion.py) - migration adapter
  - [x] Add comprehensive tests (33 new tests)
  - [x] Fix hard-coded literals (use policy dataclass)
- **Phase 2-6: Migration** ✅ COMPLETE
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

- **Status**: PARTIAL (old versions removed, utilities pending)
- **Location**: [cli_tools/audio_transcribe/](src/tnh_scholar/cli_tools/audio_transcribe/)
- **Tasks**:
  - [x] Remove [audio_transcribe0.py](src/tnh_scholar/cli_tools/audio_transcribe/audio_transcribe0.py)
  - [x] Remove audio_transcribe1.py
  - [x] Remove audio_transcribe2.py
  - [x] Keep only current version
  - [ ] Create shared utilities (argument parsing, environment validation, logging)

#### 9. ✅ Documentation Reorganization (ADR-DD01 & ADR-DD02)

- **Status**: PHASE 1 COMPLETE ✅ (Parts 1–4 ✅ COMPLETE, Part 8 ✅ COMPLETE, File Reorganization ✅ COMPLETE; Parts 5–7 deferred to Phase 2)
- **Reference**:
  - [ADR-DD01: Docs Reorganization Strategy](docs/architecture/docs-system/adr/adr-dd01-docs-reorg-strategy.md)
  - [ADR-DD02: Documentation Main Content and Navigation Strategy](docs/architecture/docs-system/adr/adr-dd02-main-content-nav.md) ✅ APPROVED
- **Goal**: Execute the phased documentation overhaul for `docs/` tree, keep README ≈ docs/index with drift monitoring, automate verification. **Note**: `patterns/` directory is managed separately (TODO #16).
- **Next Sequence**: Part 5 (Archive) → Part 6 (Gap Filling) → Part 7 (Standalone Tasks)
- **Checkpoints / Tasks**:
  1. **Inventory + Tagging**
     - [x] Catalog every Markdown file (owner, status: current/needs-update/historical)
     - [x] Add front matter metadata + PromptTemplate terminology notes
     - [ ] Identify raw research assets to offload to external storage
  2. **Filesystem Reorg** (✅ COMPLETE)
     - [x] Create the target hierarchy (overview, getting-started, user-guide, cli-reference, prompt-templates, api-reference, architecture/adr, development, research, docs-ops, archive)
     - [x] Move existing docs into the new layout with stub `index.md` files
     - [x] Rename all architecture documents for clarity and consistency (ADR naming, design doc naming)
     - [x] Create README.md files for major sections (architecture/, cli/, development/, getting-started/)
     - [x] Remove obsolete CLI reference stubs (auto-generation removed, see TODO #17)
     - [x] Reorganize reference materials into categorized subdirectories
     - [ ] Tag archival folders explicitly for mkdocs-literate-nav auto-generation (deferred to Phase 2)
  3. **Terminology + README Sweep** (Part 3b: ✅ COMPLETED - ADR-DD02 + ADR-DD03)
     - [x] **3b (COMPLETED)**: Designed content architecture for README.md and docs/index.md (ADR-DD02)
     - [x] Implemented drift reporting script (`check_readme_docs_drift.py`) for non-blocking sync monitoring
     - [x] Established persona-based navigation strategy (Practitioners, Developers, Researchers)
     - [x] Updated markdown standards to enforce exact YAML title ↔ heading match
     - [x] **Pattern → Prompt terminology standardization** (ADR-DD03 Phase 1 ✅ COMPLETE)
       - [x] Updated all user-facing documentation (README, docs/index.md, getting-started/, user-guide/)
       - [x] Renamed patterns.md → prompts.md; pattern-system/ → prompt-system/
       - [x] Added historical terminology note to docs/index.md
       - [x] Retained legacy compatibility: TNH_PATTERN_DIR, --pattern flags
       - [ ] Phase 2: CLI documentation updates (deferred post-merge, many tools deprecated)
       - [ ] Phase 3: Code refactoring (tracked separately, many modules scheduled for deletion)
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
     - [x] **4g (PHASE 1 COMPLETE)**: Documentation testing and validation workflow
       - **Phase 1: Quick Wins** ✅ COMPLETE
         - [x] Enable `mkdocs build --strict` in `docs-verify` (fail on warnings)
         - [x] Add link checking with `lychee` + `.lychee.toml` (ignore flaky/external as needed)
         - [x] Add `codespell` with `.codespell-ignore.txt` (dharma terms/proper nouns); wire into pre-commit/CI
         - [x] Create `docs-quickcheck` make target: sync_root_docs → mkdocs --strict → lychee → codespell
         - [x] Fixed all 136 MkDocs strict mode warnings (autorefs, griffe type annotations)
       - **Phase 2: Metadata Validation** (Beta gate)
         - [ ] Add `scripts/check_doc_metadata.py` to validate front matter (title/description/status) and warn on empty descriptions
         - [ ] Detect orphaned docs not reachable from nav (using generated nav) and report missing descriptions
         - [ ] Add metadata check to pre-commit and CI
       - **Phase 3: Coverage & Structure** (Prod polish)
         - [ ] Add `interrogate` for Python docstring coverage (threshold on `src/tnh_scholar`, skip tests/scripts)
         - [ ] Validate ADRs follow template sections (Context/Decision/Consequences) + required front matter
         - [ ] Run offline/internal link check on built site (`lychee --offline` on `site/`)
         - [ ] Optional: add `vale` with a minimal style guide for docs tone/consistency
  5. **Historical Archive + Discoverability** (Phase 2)
     - [x] Archived historical research artifacts and experiment files
     - [ ] Move additional legacy ADRs/prototypes into `docs/archive/**`
     - [ ] Create comprehensive archive index + add summary links from primary sections
     - [ ] Host raw transcripts externally (S3/KB) and link from summaries
  6. **Backlog + Gap Filling**
     - [ ] Populate `docs/docs-ops/roadmap.md` with missing topics (PromptTemplate catalog, workflow playbooks, evaluation guides, KB, deployment, research summaries, doc ops)
     - [ ] Open GitHub issues per backlog item with owners/priorities
  7. **Documentation Structure Reorganization** (✅ COMPLETE - Python Community Standards)
     - [x] **Split design-guide.md** into Python standard docs:
       - [x] style-guide.md: Code formatting, naming, PEP 8, type annotations
       - [x] design-principles.md: Architectural patterns, modularity, composition
     - [x] **Move object-service architecture** to canonical location:
       - [x] Moved from development/architecture/ to architecture/object-service/
       - [x] Converted V2 blueprint to ADR-OS01 (adopted V3, deleted V1)
       - [x] Created design-overview.md with high-level summary
       - [x] Updated implementation-status.md with resolved items
     - [x] **Create forward-looking prompt architecture**:
       - [x] Created prompt-architecture.md (current + planned V2 with PromptCatalog)
       - [x] Moved pattern-core-design.md to archive/ with terminology note
       - [x] Documented VS Code integration requirements
     - [x] **Fix all broken links** from reorganization:
       - [x] Fixed 35 mkdocs build --strict warnings → 0 warnings ✅
       - [x] Updated docs/index.md, contributing.md, ADR cross-references
       - [x] Regenerated documentation_index.md
     - [x] Established Python community standard structure:
       - docs/architecture/ = ADRs, design decisions (the "why")
       - docs/development/ = Developer guides (the "how")
       - docs/project/ = Vision, philosophy (stakeholders)
  8. **Outstanding Standalone Tasks** (Phase 2 - Future Work)
     - [x] Created architecture/README.md overview
     - [ ] Deprecate outdated CLI examples (deferred post-CLI-refactor, see TODO #17)
     - [ ] Add practical user guides for new features post-reorg
     - [ ] Expand architecture overview with component diagrams
     - [ ] Establish research artifact archival workflow (external storage + summary linking)
  9. **Include Root Markdown Files in MkDocs Navigation**
     - **Status**: ✅ COMPLETE
     - **Priority**: MEDIUM (Part of docs-reorg cleanup)
     - **Goal**: Make root-level config/meta files (README, TODO, CHANGELOG, CONTRIBUTING, DEV_SETUP, release_checklist) discoverable in mkdocs navigation and documentation index
     - **Approach**: Build-time copy with "DO NOT EDIT" warnings
       - [x] Create `docs/project/repo-root/` directory for project meta-documentation
       - [x] Create `scripts/sync_root_docs.py` to copy root markdown files
       - [x] Copy root `.md` files (README, TODO, CHANGELOG, CONTRIBUTING, DEV_SETUP, release_checklist) to `docs/project/repo-root/`
       - [x] Prepend HTML comment warning to each copied file
       - [x] Update Makefile `docs` target to run sync script before mkdocs build
       - [x] Test documentation build: `make docs`
       - [x] Verify copied files appear in navigation and documentation index
       - [x] Create `docs/project/index.md` with section overview
       - [x] Wire into gen-files plugin for automatic sync on build

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

#### 13. 🚧 Complete Provider Abstraction

- **Status**: NOT STARTED
- **Tasks**:
  - [ ] Implement [Anthropic adapter](src/tnh_scholar/gen_ai_service/providers/anthropic_adapter.py)
  - [ ] Add provider-specific error handling
  - [ ] Test fallback/retry across providers
  - [ ] Provider capability discovery
  - [ ] Multi-provider cost optimization

#### 14. 🚧 Knowledge Base Implementation

- **Status**: DESIGN COMPLETE
- **ADR**: [ADR-K01: Preliminary Architectural Strategy](docs/architecture/knowledge-base/adr/adr-k01-kb-architecture-strategy.md)
- **Tasks**:
  - [ ] Implement Supabase integration
  - [ ] Vector search functionality
  - [ ] Query capabilities
  - [ ] Semantic similarity search

#### 15. 🚧 Developer Experience Improvements

- **Status**: PARTIAL (hooks and Makefile exist, automation pending)
- **Tasks**:
  - [x] Add pre-commit hooks (Ruff, notebook prep)
  - [x] Create Makefile for common tasks (lint, test, docs, format, setup)
  - [ ] Add MyPy to pre-commit hooks
  - [ ] Add contribution templates (issue/PR templates)
  - [x] CONTRIBUTING.md exists and documented
  - [ ] Release automation
  - [ ] Changelog automation

#### 16. 🚧 Configuration & Data Layout

- **Status**: NOT STARTED
- **Priority**: HIGH (blocks pip install)
- **Problem**: [src/tnh_scholar/**init**.py](src/tnh_scholar/__init__.py) raises FileNotFoundError when repo layout missing
- **Tasks**:
  - [ ] Package pattern assets as resources
  - [ ] Make patterns directory optional
  - [ ] Move directory checks to CLI entry points only
  - [ ] Ensure installed wheels work without patterns/ directory

#### 17. 🚧 Prompt Catalog Safety

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

#### ✅ Improve NumberedText Ergonomics

- **Status**: IN PROGRESS - ADR-AT03.2 ACCEPTED
- **Location**: [text_processing/numbered_text.py](src/tnh_scholar/text_processing/numbered_text.py)
- **ADR**: [ADR-AT03.2: NumberedText Section Boundary Validation](docs/architecture/ai-text-processing/adr/adr-at03.2-numberedtext-validation.md)
- **Tasks**:
  - [x] ADR-AT03.2 design approved and accepted (2025-12-12)
  - [ ] Implement `validate_section_boundaries()` method
  - [ ] Implement `get_coverage_report()` method
  - [ ] Add comprehensive unit tests for validation
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

#### 17. 🚧 Comprehensive CLI Reference Documentation

- **Status**: NOT STARTED (deferred post-CLI-refactor)
- **Priority**: MEDIUM
- **Context**: Removed auto-generated CLI reference stubs (2025-12-03). Renamed `docs/cli/` to `docs/cli-reference/` to reflect reference-style content. CLI structure scheduled for overhaul.
- **Blocked By**: CLI tool consolidation (TODO #8)
- **Tasks**:
  - [ ] Review final CLI structure after refactor
  - [ ] Create comprehensive CLI reference using actual `--help` output at all command levels
  - [ ] Generate structured documentation for each command:
    - Command purpose and use cases
    - Full option/argument reference
    - Usage examples
    - Common workflows
  - [ ] Automate CLI reference generation in `scripts/generate_cli_docs.py`
  - [ ] Integrate with MkDocs build process
  - [ ] Enhance existing `docs/cli-reference/` structure with comprehensive reference material
- **Notes**:
  - Previously had placeholder stubs with minimal content
  - Current `docs/cli-reference/` contains hand-written per-command reference pages
  - Requires examining actual CLI code structure for comprehensive coverage
  - Should align with user guide examples

#### 18. ✅ Convert Documentation Links to Absolute Paths

- **Status**: COMPLETED (PR #14, commit 85ec6b0)
- **Priority**: MEDIUM
- **Context**: Enabled MkDocs 1.6+ absolute link validation (2025-12-04). Absolute links (`/path/to/file.md`) are clearer, easier to maintain, and automation-friendly compared to relative links (`../../../path/to/file.md`).
- **Reference**: [ADR-DD01 Addendum 2025-12-04: Absolute Link Strategy](docs/architecture/docs-system/adr/adr-dd01-docs-reorg-strategy.md)
- **Completed**: 2025-12-05
- **Tasks**:
  - [x] Audit all Markdown files for relative internal links (120 links found across 25 files)
  - [x] Convert relative links to absolute paths (e.g., `../../../cli-reference/overview.md` → `/cli-reference/overview.md`)
  - [x] Update documentation generation scripts to emit absolute links (created `scripts/convert_relative_links.py`)
  - [x] Verify all links resolve correctly with `mkdocs build --strict` (passed)
  - [x] Run link checker to validate changes (verified with `scripts/verify_doc_links.py`)
  - [x] Update markdown standards documentation to mandate absolute links
  - [x] Add Makefile targets for link verification (`docs-links`, `docs-links-apply`)
- **Results**:
  - 964 absolute links now in use across 96 markdown files
  - All internal documentation links use absolute paths
  - MkDocs configured with `validation.links.absolute_links: relative_to_docs`
  - Link verification integrated into docs build process

#### 19. 🚧 Document Success Cases

- **Status**: NOT STARTED
- **Priority**: MEDIUM
- **Goal**: Create comprehensive documentation of TNH Scholar's successful real-world applications
- **Context**: Cleanly document proven use cases to demonstrate project value and guide future development
- **Success Cases to Document**:
  - [ ] **Deer Park Monastery Cooking Course**
    - Generating translated SRTs for video recordings
    - Diarization implementation
    - SRT generation workflow
  - [ ] **1950s JVB (Journal of Vietnamese Buddhism) Translation**
    - OCR work on Thay's 1950s editorial work
    - Proof-of-concept translations
    - Historical document processing pipeline
  - [ ] **Dharma Talk Transcriptions**
    - Generating polished standalone XML documents from recordings
    - Transcription to structured format workflow
  - [ ] **Sr. Dang Nhiem's Dharma Talks**
    - Clean transcription work using audio-transcribe and related tools
    - Audio processing pipeline
- **Tasks**:
  - [ ] Create `docs/case-studies/` directory structure
  - [ ] Document each success case with:
    - Project context and goals
    - Tools and workflows used
    - Technical challenges and solutions
    - Results and outcomes
    - Lessons learned
  - [ ] Add references to relevant code, prompts, and configuration
  - [ ] Include sample outputs where appropriate
  - [ ] Link from main documentation and README

#### 20. 🚧 Notebook System Overhaul

- **Status**: NOT STARTED
- **Priority**: HIGH
- **Goal**: Transform notebook collection from exploratory/testing to production-quality examples and convert testing notebooks to proper test cases
- **Context**: Current notebooks include valuable work but mix exploration, testing, and examples without clear organization
- **Tasks**:
  - [ ] **Audit & Categorize**:
    - [ ] Inventory all notebooks with purpose classification
    - [ ] Identify core example notebooks (referencing success cases from TODO #19)
    - [ ] Identify testing notebooks to convert to pytest
    - [ ] Identify legacy/archival notebooks
  - [ ] **Core Example Notebooks** (keep and polish):
    - [ ] Fully annotate with current code
    - [ ] Ensure working with latest codebase
    - [ ] Add clear documentation headers
    - [ ] Reference relevant success cases
    - [ ] Add to docs as working examples
  - [ ] **Testing Notebooks → Pytest Migration**:
    - [ ] Convert notebook-based tests to standard pytest test cases
    - [ ] Ensure pytest coverage for all testing scenarios
    - [ ] Remove testing notebooks after conversion
    - [ ] Update test documentation
  - [ ] **Legacy/Archival Notebooks**:
    - [ ] Mark clearly as legacy/archival
    - [ ] Add context notes for understanding past work
    - [ ] Move to `notebooks/archive/` or similar
    - [ ] Document their historical purpose
  - [ ] **Documentation Updates**:
    - [ ] Update notebook documentation structure
    - [ ] Create notebook usage guide
    - [ ] Link core examples from user guide
    - [ ] Document notebook development workflow
- **ADR Decision**: May require architecture decision record for notebook management strategy

---

## Progress Summary

**Recently Completed (as of 2025-12-09)**:

- ✅ Packaging & dependencies fixed
- ✅ CI pytest integration
- ✅ Library exception handling (removed sys.exit)
- ✅ OpenAI client unification (all 6 phases complete)
- ✅ Documentation reorganization (Phase 1 complete)
- ✅ Pre-commit hooks and Makefile setup
- ✅ Documentation links converted to absolute paths (TODO #18)

**Current Sprint Focus**:

- 🎯 Implement core stubs (policy, routing, safety)
- 🎯 Expand test coverage to 50%+
- 🎯 Type system improvements (58 errors to resolve)

**Beta Blockers**:

- Configuration & data layout (pattern directory)
- Core stub implementations (params_policy, model_router, safety_gate)
- Test coverage expansion

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

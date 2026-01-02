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

> **Last Updated**: 2026-01-01 (ADR-A14 Registry System Completed)
> **Version**: 0.2.3 (Alpha)
> **Status**: Active Development - VS Code Extension Ready
>
> **Style Note**: Tasks use descriptive headers (not numbered items) to avoid renumbering churn when reorganizing.
> Use `####` (h4) for task headers within priority sections.

---

## Priority Roadmap

This section organizes work into three priority levels based on criticality for production readiness.

### Priority 1: VS Code Integration Enablement (Bootstrap Path)

**Goal**: Enable AI-assisted development of TNH Scholar itself via VS Code extension. Prioritizes foundational work for tnh-gen + extension integration.

**Status**: Foundation Complete (tnh-gen CLI ✅, Registry System ✅)

#### ✅ tnh-gen CLI Implementation

- **Status**: COMPLETED ✅
- **ADR**: [ADR-TG01: CLI Architecture](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md), [ADR-TG01.1: Human-Friendly Defaults](/architecture/tnh-gen/adr/adr-tg01.1-human-friendly-defaults.md)
- **What**: Protocol-driven CLI with dual modes (human-friendly default, `--api` for machine consumption)
- **Commands**: `list`, `run`, `config`, `version`
- **Documentation**: [tnh-gen CLI Reference](/cli-reference/tnh-gen.md) (661 lines, comprehensive)
- **Next**: Consumed by VS Code extension for prompt discovery and execution

#### ✅ File-Based Registry System (ADR-A14)

- **Status**: COMPLETED ✅ (Merged PR #24, 2026-01-01)
- **ADR**: [ADR-A14: File-Based Registry System](/architecture/gen-ai-service/adr/adr-a14-file-based-registry-system.md), [ADR-A14.1: Staleness Detection](/architecture/gen-ai-service/adr/adr-a14.1-registry-staleness-detection.md)
- **Completed**: Implemented JSONC-based registry with multi-tier pricing, TNHContext path resolution, and staleness detection
- **Key Features**:
  - JSONC format with VS Code schema validation
  - Three-layer path resolution (workspace → user → built-in)
  - Multi-tier pricing support (batch/flex/standard/priority)
  - Staleness detection with configurable 90-day threshold
  - Comprehensive test coverage (264 tests passing)
- **Deliverables**:
  - [x] Created `runtime_assets/registries/providers/openai.jsonc` with model metadata
  - [x] Implemented `RegistryLoader` with JSONC parsing (comment/trailing comma support)
  - [x] Created Pydantic schemas for validation (`ModelInfo`, `ProviderRegistry`)
  - [x] Created JSON Schema for VS Code autocomplete in registry files
  - [x] Refactored `model_router.py` to use registry capabilities
  - [x] Refactored `safety_gate.py` to use registry pricing (removed hardcoded constants)
  - [x] Added comprehensive unit tests for registry loading and validation
  - [x] Implemented ADR-A14.1 staleness detection with environment config
- **Files Created**:
  - `src/tnh_scholar/configuration/context.py` (TNHContext)
  - `src/tnh_scholar/runtime_assets/registries/providers/openai.jsonc`
  - `src/tnh_scholar/runtime_assets/registries/providers/schema.json`
  - `src/tnh_scholar/gen_ai_service/config/registry.py` (RegistryLoader)
  - `src/tnh_scholar/gen_ai_service/models/registry.py` (Pydantic models)
  - `src/tnh_scholar/gen_ai_service/adapters/registry/jsonc_parser.py`
  - `src/tnh_scholar/gen_ai_service/adapters/registry/override_merger.py`
  - `tests/gen_ai_service/test_registry_*.py` (comprehensive test suite)
- **Related**: Unblocks VS Code Extension Walking Skeleton

#### 🔮 VS Code Extension Walking Skeleton

- **Status**: NOT STARTED - **READY TO START** (Registry unblocked)
- **Priority**: **HIGHEST PRIORITY** (Foundation complete)
- **ADR**: [ADR-VSC01: VS Code Integration Strategy](/architecture/ui-ux/vs-code-integration/adr-vsc01-vscode-integration-strategy.md), [ADR-VSC02: Extension Implementation](/architecture/ui-ux/vs-code-integration/adr-vsc02-tnh-gen-cli-implementation.md)
- **Estimate**: 8-12 hours (first working prototype)
- **What**: Minimal VS Code extension that enables "Run Prompt on Active File" workflow
- **Capabilities**:
  - Command: "TNH Scholar: Run Prompt on Active File"
  - QuickPick prompt selector (from `tnh-gen list --api`)
  - Dynamic variable input form based on prompt metadata
  - Execute via `tnh-gen run` subprocess
  - Open output file in split pane
- **Validation**: Proves bootstrapping concept - use extension to develop TNH Scholar faster
- **Dependencies**: ✅ Registry system complete (model metadata available)

#### 🚧 Provenance Format Refactor - YAML Frontmatter

- **Status**: COMPLETED
- **Priority**: HIGH (critical for tnh-gen usability - parsing generated output)
- **Estimate**: 2-3 hours
- **Context**: Current tnh-gen uses HTML comments for provenance, inconsistent with TNH Scholar's YAML frontmatter standard
- **ADR**: [ADR-TG01 Addendum 2025-12-28](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md#addendum-2025-12-28---provenance-format-standardization)
- **Why Critical**: Generated files need machine-parsable metadata for downstream processing, VS Code integration, and provenance tracking
- **Deliverables**:
  - [x] Update `provenance.py` to generate YAML frontmatter instead of HTML comments
  - [x] Update tests for new format
  - [x] Validate YAML parsing roundtrip
- **Files Modified**: `src/tnh_scholar/cli_tools/tnh_gen/output/provenance.py`, `tests/cli_tools/test_tnh_gen.py`, `docs/cli-reference/tnh-gen.md`

#### 🚧 GenAIService Core Components - Final Polish

- **Status**: PRELIMINARY IMPLEMENTATION COMPLETE ✅ - Needs Polish & Registry Integration
- **Priority**: MEDIUM (minor cleanup, not blocking)
- **Review**: Code review completed 2025-12-10 - **Grade: A- (92/100)** ⭐⭐⭐⭐⭐
- **What**: Core GenAI service components (params_policy, model_router, safety_gate, completion_mapper) are implemented and working, need minor polish
- **Components Implemented**:
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

#### ⏸️ GenAIService Thread Safety and Rate Limiting (ADR-A15)

- **Status**: DEFERRED - Not needed for VS Code integration (process isolation)
- **Priority**: MEDIUM (revisit when building Python batch pipelines)
- **Issue**: [#22](https://github.com/aaronksolomon/tnh-scholar/issues/22)
- **ADR**: [ADR-A15: Thread Safety and Rate Limiting](/architecture/gen-ai-service/adr/adr-a15-thread-safety-rate-limiting.md)
- **Why Deferred**: VS Code extension uses process isolation (each `tnh-gen` call = separate GenAIService instance). Thread safety only matters for Python-native batch pipelines.
- **When to Revisit**: When implementing concurrent corpus processing loops or batch translation pipelines
- **Estimate**: 3-6 hours (Phase 1: 1-2 hours, Phase 2: 2-4 hours)
- **Quick Summary**: Add thread-safe retry state, locked cache, and optional rate limiting for high-throughput scenarios

---

### Priority 2: Production Hardening (Post-Bootstrap)

**Goal**: Harden TNH Scholar for production use after VS Code integration enables AI-assisted development. Focuses on reliability, test coverage, and type safety.

#### 🚧 Expand Test Coverage

- **Status**: NOT STARTED
- **Current Coverage**: ~5% (4 test modules)
- **Target**: 50%+ for gen_ai_service
- **Tasks**:
  - [ ] GenAI service flows: prompt rendering, policy resolution, provider adapters
  - [ ] CLI integration tests (option parsing, environment validation)
  - [ ] Configuration loading edge cases
  - [ ] Error handling scenarios
  - [ ] Pattern catalog validation
  - [ ] **tnh-gen CLI comprehensive coverage** (HIGH PRIORITY - Missing basic command tests):
    - [ ] Add tests for all `tnh-gen config` commands (show, get, set, list)
    - [ ] Add tests for all `tnh-gen list` commands (simple, query)
    - [ ] Add tests for `tnh-gen gen` command with various options
    - [ ] Test Path serialization in config commands (regression test for model_dump)
    - [ ] Test config precedence: defaults → user → workspace → CLI flags
    - [ ] Test error handling for all commands
    - [ ] Integration tests for full workflows
    - **Context**: Basic command `tnh-gen config show` failed with Path serialization bug that should have been caught by tests

#### 🚧 Consolidate Environment Loading

- **Status**: NOT STARTED
- **Problem**: Multiple modules call `load_dotenv()` at import time
  - <https://github.com/aaronksolomon/tnh-scholar/blob/main/src/tnh_scholar/ai_text_processing/prompts.py>
  - <https://github.com/aaronksolomon/tnh-scholar/blob/main/src/tnh_scholar/audio_processing/diarization/pyannote_client.py>
- **Tasks**:
  - [ ] Create single startup hook for dotenv loading
  - [ ] Use Pydantic Settings consistently
  - [ ] Pass configuration objects instead of `os.getenv()` calls
  - [ ] Remove import-time side effects

#### 🚧 Clean Up CLI Tool Versions

- **Status**: PARTIAL (old versions removed, utilities pending)
- **Location**: [cli_tools/audio_transcribe/](src/tnh_scholar/cli_tools/audio_transcribe/)
- **Tasks**:
  - [x] Remove [audio_transcribe0.py](src/tnh_scholar/cli_tools/audio_transcribe/audio_transcribe0.py)
  - [x] Remove audio_transcribe1.py
  - [x] Remove audio_transcribe2.py
  - [x] Keep only current version
  - [ ] Create shared utilities (argument parsing, environment validation, logging)

#### ✅ Documentation Reorganization (ADR-DD01 & ADR-DD02)

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

#### 🚧 Type System Improvements

- **Status**: PARTIAL (see detailed section below)
- **Current**: 58 errors across 16 files
- **Tasks**: See [Type System Improvements](#type-system-improvements) section below

---

### Priority 3: Future Work & Advanced Features

**Goal**: Long-term sustainability, advanced features, and nice-to-have improvements. Address after bootstrap loop is working.

#### 🚧 Refactor Monolithic Modules

- **Status**: NOT STARTED
- **Targets**:
  - [ ] <https://github.com/aaronksolomon/tnh-scholar/blob/main/src/tnh_scholar/ai_text_processing/prompts.py> (34KB)
    - Break into: prompt model, repository manager, git helpers, lock helpers
    - Add docstrings and tests for each unit
    - Document front-matter schema
  - [ ] <https://github.com/aaronksolomon/tnh-scholar/blob/main/src/tnh_scholar/journal_processing/journal_process.py> (28KB)
    - Identify focused units
    - Extract reusable components

#### 🚧 Complete Provider Abstraction

- **Status**: NOT STARTED
- **Tasks**:
  - [ ] Implement [Anthropic adapter](src/tnh_scholar/gen_ai_service/providers/anthropic_adapter.py)
  - [ ] Add provider-specific error handling
  - [ ] Test fallback/retry across providers
  - [ ] Provider capability discovery
  - [ ] Multi-provider cost optimization

#### 🚧 Knowledge Base Implementation

- **Status**: DESIGN COMPLETE
- **ADR**: [ADR-K01: Preliminary Architectural Strategy](docs/architecture/knowledge-base/adr/adr-k01-kb-architecture-strategy.md)
- **Tasks**:
  - [ ] Implement Supabase integration
  - [ ] Vector search functionality
  - [ ] Query capabilities
  - [ ] Semantic similarity search

#### 🚧 Developer Experience Improvements

- **Status**: PARTIAL (hooks and Makefile exist, automation pending)
- **Tasks**:
  - [x] Add pre-commit hooks (Ruff, notebook prep)
  - [x] Create Makefile for common tasks (lint, test, docs, format, setup)
  - [ ] Add MyPy to pre-commit hooks
  - [ ] Add contribution templates (issue/PR templates)
  - [x] CONTRIBUTING.md exists and documented
  - [ ] Release automation
  - [ ] Changelog automation

#### 🚧 Configuration & Data Layout

- **Status**: NOT STARTED
- **Priority**: HIGH (blocks pip install)
- **Problem**: [src/tnh_scholar/**init**.py](src/tnh_scholar/__init__.py) raises FileNotFoundError when repo layout missing
- **Tasks**:
  - [ ] Package pattern assets as resources
  - [ ] Make patterns directory optional
  - [ ] Move directory checks to CLI entry points only
  - [ ] Ensure installed wheels work without patterns/ directory

#### 🚧 Prompt Catalog Safety

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

- **Status**: COMPLETED ✅
- **Location**: [text_processing/numbered_text.py](src/tnh_scholar/text_processing/numbered_text.py)
- **ADR**: [ADR-AT03.2: NumberedText Section Boundary Validation](docs/architecture/ai-text-processing/adr/adr-at03.2-numberedtext-validation.md)
- **What**: Implemented section boundary validation and coverage reporting
- **Completed**:
  - [x] ADR-AT03.2 design approved and accepted (2025-12-12)
  - [x] Implemented `validate_section_boundaries()` method (numbered_text.py:367)
  - [x] Implemented `get_coverage_report()` method (numbered_text.py:510)
- **Note**: ADR status should be updated from "accepted" → "implemented" when updating ADRs

#### Logging System Scope

- **Location**: [logging_config.py](src/tnh_scholar/logging_config.py)
- **Problem**: Modules call setup_logging individually
- **Tasks**:
  - [ ] Define single application bootstrap
  - [ ] Document logger acquisition pattern (get_logger only)
  - [ ] Create shared CLI bootstrap helper

### Low Priority

#### Historical ADR Status Audit

- **Status**: NOT STARTED
- **Priority**: LOW (documentation hygiene)
- **Context**: 25 ADRs marked with `status: current` from pre-markdown-standards migration (2025-12-28 audit)
- **Background**:
  - These ADRs were created before ADR status lifecycle was formalized
  - When migrated to YAML frontmatter system, default was `current` for all kept files
  - Per new markdown-standards.md, ADRs should use: `proposed` → `accepted` → `implemented` → `superseded`/`archived`
  - `current` status is now reserved for guides/references only, not ADRs
- **Issue**: Need manual review to determine actual status - most likely `implemented`, but some may be `superseded` or `rejected`
- **ADRs requiring review** (25 total):
  - adr-a01-object-service-genai.md
  - adr-a02-patterncatalog-integration-v1.md
  - adr-a08-config-params-policy-taxonomy.md
  - adr-a09-v1-simplified.md
  - adr-a11-model-parameters-fix.md
  - adr-a12-prompt-system-fingerprinting-v1.md
  - adr-a13-migrate-openai-to-genaiservice.md
  - adr-at01-ai-text-processing.md
  - adr-dd01-docs-reorg-strategy.md
  - adr-dd02-main-content-nav.md
  - adr-k01-kb-architecture-strategy.md
  - adr-md01-json-ld-metadata.md
  - adr-md02-metadata-object-service-integration.md
  - adr-os01-object-service-architecture-v3.md
  - adr-pp01-rapid-prototype-versioning.md
  - adr-pt01-pattern-access-strategy.md
  - adr-pt02-adopt-pattern-and-patterncatalog.md
  - adr-pt04-prompt-system-refactor.md
  - adr-tr01-assemblyai-integration.md
  - adr-tr02-optimized-srt-design.md
  - adr-tr03-ms-timestamps.md
  - adr-tr04-assemblyai-improvements.md
  - adr-vp01-video-processing.md
  - adr-yf01-yt-transcript-source-handling.md
  - adr-yf02-yt-transcript-format-selection.md
- **Tasks**:
  - [ ] Review each ADR to determine if decision was implemented, superseded, or rejected
  - [ ] Update status field in YAML frontmatter accordingly
  - [ ] Check for code evidence of implementation where applicable
  - [ ] Cross-reference with newer ADRs to identify superseded decisions
  - [ ] Document any ADRs that should be archived vs marked implemented

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

#### 🚧 Comprehensive CLI Reference Documentation

- **Status**: IN PROGRESS - tnh-gen documentation complete ✅, other CLIs pending
- **Priority**: MEDIUM
- **Context**: tnh-gen CLI (ADR-TG01, ADR-TG01.1) implementation complete; documentation work started 2025-12-28
- **Completed (2025-12-28)**:
  - [x] Created comprehensive tnh-gen CLI reference (`docs/cli-reference/tnh-gen.md`)
    - Complete command reference: `list`, `run`, `config`, `version`
    - Human-friendly vs API mode documentation
    - Variable precedence, error handling, environment variables
    - Migration guide from tnh-fab
  - [x] Archived legacy tnh-fab documentation
    - Moved `docs/cli-reference/tnh-fab.md` to `docs/cli-reference/archive/`
    - Created `docs/cli-reference/archive/README.md` with archiving policy
  - [x] Updated CLI reference overview (`docs/cli-reference/overview.md`)
    - Promoted tnh-gen to primary tool
    - Added tnh-gen quick start examples
    - Moved tnh-fab to "Archived Tools" section
  - [x] Updated getting-started documentation
    - Updated quick-start-guide with tnh-gen workflows
    - Updated installation guide verification steps
  - [x] Updated CHANGELOG with ADR-TG01.1 implementation details
- **Remaining Tasks**:
  - [ ] Update user-guide examples to use tnh-gen
    - [ ] `docs/user-guide/prompt-system.md` - Replace tnh-fab examples
    - [ ] `docs/user-guide/best-practices.md` - Update CLI workflows
  - [ ] Update architecture docs with tnh-gen examples
  - [ ] Document other CLI tools (audio-transcribe, ytt-fetch, nfmt, etc.)
  - [ ] Consider automation for CLI reference generation (`scripts/generate_cli_docs.py`)
- **Notes**:
  - tnh-gen follows ADR-TG01 (CLI Architecture) and ADR-TG01.1 (Human-Friendly Defaults)
  - Archive system uses MkDocs `exclude_docs: **/archive/**` pattern
  - Documentation links use absolute paths
  - Provenance format refactor moved to Priority 1 (critical for tnh-gen usability)

#### 🚧 Document Success Cases

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

#### 🚧 Notebook System Overhaul

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

**Recently Completed (as of 2025-12-28)**:

- ✅ tnh-gen CLI implementation (ADR-TG01, ADR-TG01.1) - protocol-driven, dual-mode (`--api` flag)
- ✅ tnh-gen comprehensive documentation (661 lines, CLI reference)
- ✅ OpenAI client unification (all 6 phases complete, legacy code removed)
- ✅ Documentation reorganization (Phase 1 complete, absolute links, MkDocs strict mode)
- ✅ Core stubs implementation (params_policy, model_router, safety_gate, completion_mapper)
- ✅ Packaging & dependencies fixed, CI pytest integration, pre-commit hooks

**Current Sprint Focus (Bootstrap Path)**:

- 🎯 **ADR-A14 Registry System** (P0 - blocks VS Code extension)
- 🎯 VS Code Extension Walking Skeleton (after registry)
- 🎯 Validate bootstrapping concept (use extension to develop TNH Scholar)

**Key Dependencies**:

- Registry system unblocks: VS Code extension, model metadata in UI, capability-based routing
- VS Code integration enables: AI-assisted development, faster iteration, bootstrapping loop

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

---

## Recently Completed Tasks (Archive)

### tnh-gen CLI Implementation ✅

- **Completed**: 2025-12-27
- **ADR**: [ADR-TG01](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md), [ADR-TG01.1](/architecture/tnh-gen/adr/adr-tg01.1-human-friendly-defaults.md)
- **What**: Protocol-driven CLI replacing tnh-fab, dual modes (human-friendly default, `--api` for machine consumption)
- **Documentation**: [tnh-gen CLI Reference](/cli-reference/tnh-gen.md) (661 lines)

### OpenAI Client Unification ✅

- **Completed**: 2025-12-10
- **ADR**: [ADR-A13](/architecture/gen-ai-service/adr/adr-a13-migrate-openai-to-genaiservice.md)
- **What**: Migrated from legacy `openai_interface/` to modern `gen_ai_service/providers/` architecture (6 phases)

### Core Stubs Implementation ✅

- **Completed**: 2025-12-10
- **What**: Implemented params_policy, model_router, safety_gate, completion_mapper with strong typing
- **Grade**: A- (92/100) - Production ready with minor polish

### Documentation Reorganization Phase 1 ✅

- **Completed**: 2025-12-05
- **ADR**: [ADR-DD01](/architecture/docs-system/adr/adr-dd01-docs-reorg-strategy.md), [ADR-DD02](/architecture/docs-system/adr/adr-dd02-main-content-nav.md)
- **What**: Absolute links, MkDocs strict mode, filesystem-driven nav, lychee link checking

### Packaging & CI Infrastructure ✅

- **Completed**: 2025-11-20
- **What**: pytest in CI, runtime dependencies declared, pre-commit hooks, Makefile targets

### Remove Library sys.exit() Calls ✅

- **Completed**: 2025-11-15
- **What**: Library code raises ConfigurationError instead of exiting process

### Convert Documentation Links to Absolute Paths ✅

- **Completed**: 2025-12-05 (PR #14)
- **What**: Converted 964 links to absolute paths, enabled MkDocs strict link validation, integrated link verification

### NumberedText Section Boundary Validation ✅

- **Completed**: 2025-12-12
- **ADR**: [ADR-AT03.2](/architecture/ai-text-processing/adr/adr-at03.2-numberedtext-validation.md) (status: accepted → should be implemented)
- **What**: Implemented `validate_section_boundaries()` and `get_coverage_report()` methods for robust section management
- **Commits**: cf99375 (docs), 798a552 (refactor unused methods)

### TextObject Robustness Improvements ✅

- **Completed**: 2025-12-14
- **ADR**: [ADR-AT03.3](/architecture/ai-text-processing/adr/adr-at03.3-textobject-robustness.md) (status: accepted → should be implemented)
- **What**: Implemented merge_metadata() with MergeStrategy enum, validate_sections() with fail-fast, converted to Pydantic v2, added structured exception hierarchy
- **Commits**: 096e528 (implementation), 03654fe (docs/docstrings)

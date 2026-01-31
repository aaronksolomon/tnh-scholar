---
title: "TNH Scholar TODO List"
description: "Roadmap tracking the highest-priority TNH Scholar tasks and release blockers."
owner: ""
author: ""
status: processing
created: "2025-01-20"
updated: "2026-01-27"
---
# TNH Scholar TODO List

Roadmap tracking the highest-priority TNH Scholar tasks and release blockers.

> **Last Updated**: 2026-01-28 (Added JVB VS Code Parallel Viewer P1 item)
> **Version**: 0.3.1 (Alpha)
> **Status**: Active Development - Bootstrap path complete, production hardening phase
>
> **Style Note**: Tasks use descriptive headers (not numbered items) to avoid renumbering churn when reorganizing.
> Use `####` (h4) for task headers within priority sections.

---

## Progress Summary

**Bootstrap Path Status**: ✅ **COMPLETE** — VS Code integration working, AI-assisted development enabled.

**Next Steps**:

1. 🔮 **JVB VS Code Parallel Viewer** (P1, design phase) — ADR-JVB02 strategy + UI-UX design
2. 🔮 Add `--prompt-dir` Global Flag to tnh-gen (P1, minor)
3. 🚧 GenAIService Final Polish - promote `policy_applied` typing (P1, minor)
4. 🚧 Prompt Catalog Safety - error handling, validation (P2, critical infrastructure)
5. 🚧 Knowledge Base Implementation (P2, design complete)
6. 🚧 Expand Test Coverage to 50%+ (P2)

**For completed items**: See [Archive](#recently-completed-tasks-archive) section at end.

---

## Priority Roadmap

This section organizes work into three priority levels based on criticality for production readiness.

### Priority 1: VS Code Integration Enablement (Bootstrap Path)

**Goal**: Enable AI-assisted development of TNH Scholar itself via VS Code extension. Prioritizes foundational work for tnh-gen + extension integration.

**Status**: Foundation Complete (tnh-gen CLI ✅, Registry System ✅)

#### ✅ tnh-gen CLI Implementation — *See [Archive](#tnh-gen-cli-implementation-)*

#### ✅ File-Based Registry System (ADR-A14) — *See [Archive](#file-based-registry-system-adr-a14-)*

#### ✅ VS Code Extension Walking Skeleton — *See [Archive](#vs-code-extension-walking-skeleton-)*

#### ✅ Pattern→Prompt Migration — *See [Archive](#patternprompt-migration-)*

#### ✅ Provenance Format Refactor (YAML Frontmatter) — *See [Archive](#provenance-format-refactor-)*

#### 🔮 JVB VS Code Parallel Viewer (ADR-JVB02)

- **Status**: NOT STARTED (Design Phase)
- **Priority**: HIGH (flagship feature, builds on VS Code integration foundation)
- **Context**: The JVB (Journal of Vietnamese Buddhism) parallel viewer enables scholars to view scanned historical journal pages alongside OCR text and English translations. v1 was a bespoke browser-based prototype; v2 will integrate into the tnh-scholar VS Code extension.
- **Project Paused**: This work was on hold while VS Code integration and tnh-gen were developed. Now that the walking skeleton is complete, we can resume with fresh design.

**Related Documentation**:

- **v1 As-Built**: [ADR-JVB01](/architecture/jvb-viewer/adr/adr-jvb01_as-built_jvb_viewer_v1.md) — Browser-based prototype architecture
- **v2 Strategy (Draft)**: [JVB Viewer V2 Strategy](/architecture/jvb-viewer/design/jvb-viewer-v2-strategy.md) — Pre-ADR strategy note (good foundations, needs formalization)
- **VS Code Platform Strategy**: [VS Code as UI Platform](/architecture/ui-ux/design/vs-code-as-ui-platform.md) — Overall UI-UX direction
- **VS Code Integration**: [ADR-VSC01](/architecture/ui-ux/vs-code-integration/adr-vsc01-vscode-integration-strategy.md) — CLI-first extension strategy (implemented)

**Proposed ADR Structure**:

```text
docs/architecture/jvb-viewer/adr/
├── adr-jvb01_as-built_jvb_viewer_v1.md              # ✅ Exists
├── adr-jvb02-vscode-parallel-viewer-strategy.md     # 🆕 Main strategy ADR
├── adr-jvb02.1-ui-ux-design.md                      # 🆕 Mockups, pane layout, workflows
├── adr-jvb02.2-data-model-api-contract.md           # 🆕 JSON schema, extension↔backend API
└── adr-jvb02.3-implementation-guide.md              # 🆕 Phase-by-phase implementation
```

**Key Design Decisions Needed**:

1. **VS Code Pane Architecture**: Which panes for scan overlay, text views, reconciliation controls, navigation?
2. **Webview vs Custom Editor**: Custom editor for `.jvb.json` files or webview panel approach?
3. **Backend Integration**: Python service via CLI (`tnh-gen` patterns) or dedicated HTTP service?
4. **Data Model**: Refine per-page JSON schema from v2 strategy, define API contract
5. **Dual OCR Reconciliation UI**: How users choose between Google OCR vs AI vision sources

**Deliverables**:

- [ ] **ADR-JVB02**: Main strategy ADR (formalize v2 strategy, VS Code integration focus)
- [ ] **ADR-JVB02.1**: UI-UX design with mockups/screen visualizations
- [ ] **ADR-JVB02.2**: Data model and API contract specification
- [ ] **ADR-JVB02.3**: Implementation guide with milestones
- [ ] **M0 Prototype**: Static HTML mockup in VS Code webview (validate approach)

**Implementation Milestones** (from v2 strategy, to be refined):

- **M0**: Static prototype — HTML showing page image, word bboxes, selectable sentences
- **M1**: VS Code extension — load/save per-page JSON, overlay modes, section breadcrumb
- **M2**: Dual-source UI — GOCR vs AI diff chooser, batch adoption, "reviewed" status
- **M3**: Structure cues — columns, heading levels, emphasis flags captured and rendered
- **M4**: Beta — section-level navigation, export HTML, light theming

#### 🔮 Add `--prompt-dir` Global Flag to tnh-gen

- **Status**: NOT STARTED
- **Priority**: HIGH (improves tnh-gen UX for one-off operations and testing)
- **Estimate**: 1-2 hours
- **Context**: Users need convenient way to override prompt catalog directory for one-off CLI calls without setting environment variables or creating temp config files
- **ADR**: [ADR-TG01 Addendum 2026-01-02](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md#addendum-2026-01-02---add---prompt-dir-global-flag)
- **Why Important**: Enables clean one-off operations (`tnh-gen --prompt-dir ./test-prompts list`) for testing, CI/CD, and development workflows
- **Current Workarounds**:
  - Environment variable: `TNH_PROMPT_DIR=/path tnh-gen list` (awkward)
  - Temp config file: `tnh-gen --config /tmp/config.yaml list` (verbose)
- **Deliverables**:
  - [ ] Add `--prompt-dir` flag to `cli_callback()` in `src/tnh_scholar/cli_tools/tnh_gen/tnh_gen.py:26`
  - [ ] Update `config_loader.py` to handle prompt directory override at CLI precedence level
  - [ ] Update `ConfigData` type to accept `prompt_catalog_dir` override
  - [ ] Add unit tests for flag precedence (CLI flag > workspace > user > env)
  - [ ] Update help text and CLI reference documentation
  - [ ] Update `docs/cli-reference/tnh-gen.md` global flags section
- **Files to Modify**:
  - `src/tnh_scholar/cli_tools/tnh_gen/tnh_gen.py` (add flag)
  - `src/tnh_scholar/cli_tools/tnh_gen/config_loader.py` (precedence handling)
  - `src/tnh_scholar/cli_tools/tnh_gen/types.py` (type definitions)
  - `tests/cli_tools/test_tnh_gen.py` (unit tests)
  - `docs/cli-reference/tnh-gen.md` (documentation)
- **Testing**: Verify `--prompt-dir` flag overrides all other config sources (workspace, user, env)

#### 🚧 GenAIService Core Components - Final Polish

- **Status**: PRELIMINARY IMPLEMENTATION COMPLETE ✅ - Needs Polish & Registry Integration
- **Priority**: MEDIUM (minor cleanup, not blocking)
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

#### 🚧 OpenAI SDK 2.15.0 Validation (High Priority)

- **Status**: NOT STARTED
- **Why**: SDK bump impacts OpenAI adapter. *(Codex harness suspended — see ADR-OA03.2 addendum)*
- **Tasks**:
  - [ ] Revalidate OpenAI adapter request/response mappings against 2.15.0
  - [ ] Update compatibility notes/docs if schema drift is found

#### ⏸️ Agent Orchestration - Codex Runner (ADR-OA03.2)

- **Status**: TABLED (2026-01-25)
- **ADR**: [ADR-OA03.2](/architecture/agent-orchestration/adr/adr-oa03.2-codex-runner.md)
- **Why Tabled**:
  1. **Scope**: Spike revealed that a proper Codex harness requires implementing full client-side agent orchestration (the VS Code extension uses a proprietary app server, not raw API calls)
  2. **Cost-benefit**: Current human-in-the-loop workflow with Claude Code + VS Code Codex extension is effective and cost-efficient for project needs
  3. **No compelling need**: Investment not justified when manual workflow works well
- **Findings**: [Codex Harness Spike Findings](/architecture/agent-orchestration/notes/codex-harness-spike-findings.md)
- **Preserved Artifacts**: `src/tnh_scholar/agent_orchestration/codex_harness/`, `src/tnh_scholar/cli_tools/tnh_codex_harness/`
- **Conditions for Resumption**: Further insight or clear business need that justifies full agent orchestration investment

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
  - [ ] **Full CLI test suite with 100% coverage** (HIGH PRIORITY - include all CLI tools, not just tnh-gen)
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

#### ✅ Documentation Reorganization (ADR-DD01 & ADR-DD02) — *See [Archive](#documentation-reorganization-phase-1-)*

**Phase 1 COMPLETE** - Remaining Phase 2 tasks:

- [ ] Doc metadata validation script (`check_doc_metadata.py`) - validate front matter
- [ ] Docstring coverage (`interrogate`) - threshold on `src/tnh_scholar`
- [ ] Archive index + legacy ADR migration to `docs/archive/**`
- [ ] Backlog: populate `docs/docs-ops/roadmap.md` with missing topics
- [ ] User guides for new features, architecture component diagrams

#### 🚧 Type System Improvements

- **Status**: PARTIAL
- **Current**: 58 errors across 16 files
- **High Priority**: Fix audio processing boundary types, core text processing types, function redefinitions
- **Medium Priority**: Add missing type annotations, fix Pattern class type issues
- **Low Priority**: Clean up Any return types, standardize type usage

#### 🚧 Prompt Catalog Safety

- **Status**: NOT STARTED
- **Priority**: HIGH (critical infrastructure)
- **Problem**: Adapter doesn't handle missing keys or invalid front-matter gracefully
- **Tasks**:
  - [ ] Add manifest validation
  - [ ] Implement caching
  - [ ] Better error messages (unknown prompt, hash mismatch)
  - [ ] Front-matter validation
  - [ ] Document prompt schema

#### 🚧 Knowledge Base Implementation

- **Status**: DESIGN COMPLETE
- **ADR**: [ADR-K01](/architecture/knowledge-base/adr/adr-k01-kb-architecture-strategy.md)
- **Tasks**:
  - [ ] Implement Supabase integration
  - [ ] Vector search functionality
  - [ ] Query capabilities
  - [ ] Semantic similarity search

#### 🚧 Configuration & Data Layout

- **Status**: NOT STARTED
- **Priority**: HIGH (blocks pip install)
- **Problem**: `src/tnh_scholar/__init__.py` raises FileNotFoundError when repo layout missing
- **Tasks**:
  - [ ] Package pattern assets as resources
  - [ ] Make patterns directory optional
  - [ ] Move directory checks to CLI entry points only
  - [ ] Ensure installed wheels work without patterns/ directory

#### 🚧 Logging System Scope

- **Location**: `src/tnh_scholar/logging_config.py`
- **Problem**: Modules call setup_logging individually
- **Tasks**:
  - [ ] Define single application bootstrap
  - [ ] Document logger acquisition pattern (get_logger only)
  - [ ] Create shared CLI bootstrap helper

#### 🚧 Comprehensive CLI Reference Documentation

- **Status**: IN PROGRESS (tnh-gen complete ✅, other CLIs pending)
- **Tasks**:
  - [ ] Update user-guide examples to use tnh-gen
  - [ ] Document other CLI tools (audio-transcribe, ytt-fetch, nfmt, etc.)
  - [ ] Consider automation for CLI reference generation

#### 🚧 Document Success Cases

- **Status**: NOT STARTED
- **Goal**: Document TNH Scholar's successful real-world applications
- **Cases**: Deer Park Cooking Course (SRTs), 1950s JVB Translation (OCR), Dharma Talk Transcriptions, Sr. Dang Nhiem's talks
- **Tasks**:
  - [ ] Create `docs/case-studies/` directory structure
  - [ ] Document each case with context, tools, challenges, outcomes

#### 🚧 Notebook System Overhaul

- **Status**: NOT STARTED
- **Priority**: HIGH
- **Goal**: Transform notebooks from exploratory/testing to production-quality examples
- **Tasks**:
  - [ ] Audit & categorize all notebooks
  - [ ] Polish core example notebooks
  - [ ] Convert testing notebooks to pytest
  - [ ] Archive legacy notebooks with context notes

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

#### 🚧 Historical ADR Status Audit

- **Status**: NOT STARTED
- **Context**: 25 ADRs marked with `status: current` from pre-markdown-standards migration
- **Tasks**:
  - [ ] Review each ADR to determine actual status (implemented/superseded/rejected)
  - [ ] Update status field in YAML frontmatter
  - [ ] Cross-reference with newer ADRs for superseded decisions

#### 🚧 Package API Definition

- **Status**: Deferred during prototyping
- **Tasks**:
  - [ ] Review and document all intended public exports
  - [ ] Implement `__all__` in key `__init__.py` files
  - [ ] Verify exports match documentation

#### 🚧 Repo Hygiene

- **Problem**: Generated artifacts in repo (build/, dist/, site/, *.txt)
- **Tasks**:
  - [ ] Add to .gitignore
  - [ ] Document regeneration process
  - [ ] Rely on release pipelines for builds

#### 🚧 Notebook & Research Management

- **Location**: notebooks/, docs/research/
- **Problem**: Valuable but not curated exploratory work
- **Tasks**:
  - [ ] Adopt naming/linting convention
  - [ ] Publish vetted analyses to docs/research via nbconvert
  - [ ] Archive obsolete notebooks

---

## Recently Completed Tasks (Archive)

### tnh-gen CLI Implementation ✅

- **Completed**: 2025-12-27
- **ADR**: [ADR-TG01](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md), [ADR-TG01.1](/architecture/tnh-gen/adr/adr-tg01.1-human-friendly-defaults.md)
- **What**: Protocol-driven CLI replacing tnh-fab, dual modes (human-friendly default, `--api` for machine consumption)
- **Documentation**: [tnh-gen CLI Reference](/cli-reference/tnh-gen.md) (661 lines)

### File-Based Registry System (ADR-A14) ✅

- **Completed**: 2026-01-01 (PR #24)
- **ADR**: [ADR-A14](/architecture/gen-ai-service/adr/adr-a14-file-based-registry-system.md), [ADR-A14.1](/architecture/gen-ai-service/adr/adr-a14.1-registry-staleness-detection.md)
- **What**: JSONC-based registry with multi-tier pricing, TNHContext path resolution, staleness detection
- **Key Deliverables**: `openai.jsonc` registry, `RegistryLoader`, Pydantic schemas, JSON Schema for VS Code, refactored `model_router.py` and `safety_gate.py`, 264 tests passing

### VS Code Extension Walking Skeleton ✅

- **Completed**: 2026-01-07
- **ADR**: [ADR-VSC01](/architecture/ui-ux/vs-code-integration/adr-vsc01-vscode-integration-strategy.md), [ADR-VSC02](/architecture/ui-ux/vs-code-integration/adr-vsc02-tnh-gen-cli-implementation.md)
- **What**: TypeScript extension enabling "Run Prompt on Active File" workflow
- **Capabilities**: QuickPick prompt selector, dynamic variable input, `tnh-gen run` subprocess execution, split-pane output, unit/integration tests
- **Validation**: Proves bootstrapping concept - extension ready to accelerate TNH Scholar development

### Pattern→Prompt Migration ✅

- **Completed**: 2026-01-19
- **ADR**: [ADR-PT04](/architecture/prompt-system/adr/adr-pt04-prompt-system-refactor.md)
- **What**: Pattern→Prompt terminology migration and directory restructuring
- **Key Changes**: `patterns/` → `prompts/` (standalone `tnh-prompts` repo), `TNH_PATTERN_DIR` → `TNH_PROMPT_DIR`, removed legacy `tnh-fab` CLI
- **Breaking**: `TNH_PATTERN_DIR` env var removed, `tnh-fab` CLI removed

### Provenance Format Refactor ✅

- **Completed**: 2026-01-19
- **ADR**: [ADR-TG01 Addendum 2025-12-28](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md#addendum-2025-12-28---provenance-format-standardization)
- **What**: Switched tnh-gen from HTML comments to YAML frontmatter for provenance metadata
- **Files Modified**: `provenance.py`, `test_tnh_gen.py`, `tnh-gen.md`

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

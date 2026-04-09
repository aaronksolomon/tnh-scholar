---
title: "TNH Scholar TODO List"
description: "Roadmap tracking the highest-priority TNH Scholar tasks and release blockers."
owner: ""
author: ""
status: processing
created: "2025-01-20"
updated: "2026-03-06"
---
# TNH Scholar TODO List

Roadmap tracking the highest-priority TNH Scholar tasks and release blockers.

> **Last Updated**: 2026-04-03 (PR-5 OA04.2 runner adapters merged)
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
2. 🔮 Finish yt-dlp reliability suite + monthly ops trigger (P1, reliability)
3. 🔮 Finish ytt-fetch robustness hardening (P1, reliability)
4. 🔮 Add `--prompt-dir` Global Flag to tnh-gen (P1, minor)
5. 🚧 GenAIService Final Polish - promote `policy_applied` typing (P1, minor)
6. 🚧 Prompt Catalog Safety - error handling, validation (P2, critical infrastructure)
7. 🚧 Knowledge Base Implementation (P2, design complete)
8. 🚧 Expand Test Coverage to 50%+ (P2)

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

#### 🚨 Agent-Orch OA07 Runtime Implementation Sequence

- **Status**: IN PROGRESS - maintained execution/validation/kernel slice landed and tested
- **Priority**: HIGH (foundation work for durable MVP)
- **Context**: The accepted OA07 ADR set defines the maintained runtime architecture. The current `conductor_mvp/` and `spike/` code remains useful as migration source/reference, but should not receive forward-path feature growth.
- **Why This Matters**:
  - current implementation readiness is medium, but in-place extension readiness is low
  - the highest-risk boundary is still subprocess execution and typed validation/runner contracts
  - coding should proceed by subsystem extraction, not by continuing prototype package growth
- **Implementation Order**:
  - [x] Build `agent_orchestration/execution/`
    - typed invocation families
    - cwd/env/timeout policy
    - termination/result taxonomy
    - final argv rendering boundary
  - [x] Build `agent_orchestration/validation/` on top of `execution/`
    - preserve OA04 external YAML compatibility by normalizing source shapes into typed internal models
    - migrate behavior out of `conductor_mvp/providers/validation_runner.py`
  - [x] Extract `agent_orchestration/kernel/`
    - `WorkflowCatalog`
    - `WorkflowValidator`
    - `KernelState`
    - `KernelRunService`
  - [x] Introduce `agent_orchestration/workspace/` and `agent_orchestration/run_artifacts/`
    - move rollback/state capture and durable run record ownership out of prototype packages
  - [x] Migrate maintained runner behavior into `agent_orchestration/runners/`
    - use `reference/spike/` only as reference material
    - no new forward-path runner work in spike code
- **Current Slice Completed**:
  - Added maintained `execution/`, `validation/`, `kernel/`, `workspace/`, `run_artifacts/`, and `runners/` package scaffolding
  - Added focused OA07 regression coverage and validated the new slice plus legacy `conductor_mvp` kernel tests
  - Sourcery installed successfully via `poetry install --with local`, but the CLI currently hangs even for `--help`, so local Sourcery review remains blocked by Sourcery runtime behavior rather than repo config
- **Migration Rules**:
  - [ ] Do not add substantive new feature work to `conductor_mvp/`
  - [ ] Do not add new forward-path implementation work to `spike/`
  - [ ] Treat `conductor_mvp/` as a temporary migration-source package to be deleted after subsystem extraction
  - [ ] Treat `codex_harness/` and `spike/` as reference packages during OA07 migration
- **Initial Files in Scope**:
  - `src/tnh_scholar/agent_orchestration/conductor_mvp/`
  - `src/tnh_scholar/agent_orchestration/spike/`
  - `src/tnh_scholar/agent_orchestration/common/`
  - `tests/agent_orchestration/`
  - `docs/architecture/agent-orchestration/adr/adr-oa03-agent-runner-architecture.md`
  - `docs/architecture/agent-orchestration/adr/adr-oa03.1-claude-code-runner.md`
  - `docs/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-runner.md`
  - `docs/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md`
  - `docs/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md`

#### 🚨 OA07.1 Bootstrap Worktree Slice

- **Status**: READY TO START
- **Priority**: HIGHEST (next operational bootstrap slice)
- **Context**: The maintained OA04.x runtime contracts are now substantial, but the system is not yet operational because mutable execution still lacks a real worktree boundary. Follow [ADR-OA07](/architecture/agent-orchestration/adr/adr-oa07-diff-policy-safety-rails.md) and [ADR-OA07.1](/architecture/agent-orchestration/adr/adr-oa07.1-worktree-lifecycle-and-rollback.md).
- **Bootstrap Goal**:
  - create a managed git worktree from a committed base ref
  - run `RUN_AGENT` and `RUN_VALIDATION` against the worktree root
  - keep canonical run artifacts in the run directory
  - support `ROLLBACK(pre_run)` to recorded base state
  - establish the headless path needed for later commit/push/PR automation
- **Why This Is Next**:
  - current kernel/workspace code is contract-shaped but not operational
  - the run directory and mutable workspace are still conflated in the maintained path
  - OA05/OA06 depth work should follow a live bootstrap loop, not precede it
- **Recommended PR sizing**:
  - Prefer **2 PRs** to stay comfortably under diff-size guidance
  - A single PR is possible only if the implementation stays narrow and avoids CLI/app-layer work
- **PR Sequence**:
  - [ ] **PR-7** `feat/oa07.1-worktree-workspace-service` — Worktree runtime boundary (medium)
    - replace `NullWorkspaceService` as the forward-path maintained implementation with a real git-backed workspace service
    - add typed workspace context models: `repo_root`, `worktree_path`, `branch_name`, `base_ref`, `base_sha`
    - implement managed branch + worktree creation from committed base ref
    - update the workspace protocol so pre-run setup returns structured workspace context and does not rely on the run directory as the workspace handle
    - pass the worktree root as `working_directory` to runner and validation services for mutable steps
    - implement `ROLLBACK(pre_run)` by discarding and recreating the managed worktree from recorded `base_sha`
    - persist workspace context into canonical run artifacts or run metadata extension
    - tests for worktree creation, mutable-step execution in the worktree root, recorded base state, and `ROLLBACK(pre_run)` semantics
    - keep `NullWorkspaceService` only for tests or explicit non-operational contexts
  - [ ] **PR-8** `feat/oa07-bootstrap-headless-entry` — Maintained headless bootstrap entry (small/medium)
    - load one workflow
    - create worktree context
    - execute workflow end to end
    - write canonical artifacts and final state
    - keep the initial entry local/headless; no GitHub automation required
  - [ ] **PR-9** `feat/oa07-review-automation` — Commit/push/PR automation (optional, small/medium)
    - create local commits on the managed branch
    - push the work branch
    - open or update a PR
    - keep protected-branch merge human-only
- **Explicit deferrals for this slice**:
  - [ ] commit/push/PR automation if it causes PR-7 or PR-8 to exceed preferred diff size
  - [ ] strict OA05 compile-validation as a blocker for bootstrap
  - [ ] full OA06 planner fixture/vector suite beyond the bootstrap path
  - [ ] non-script harness backends
  - [ ] stacked PR orchestration
  - [ ] multi-agent mutable collaboration inside one worktree
  - [ ] `pre_step` rollback and named checkpoints
- **Files likely in scope**:
  - `src/tnh_scholar/agent_orchestration/workspace/`
  - `src/tnh_scholar/agent_orchestration/kernel/service.py`
  - `src/tnh_scholar/agent_orchestration/run_artifacts/`
  - `tests/agent_orchestration/test_oa07_execution_validation_kernel.py`
  - `docs/architecture/agent-orchestration/adr/adr-oa07-diff-policy-safety-rails.md`
  - `docs/architecture/agent-orchestration/adr/adr-oa07.1-worktree-lifecycle-and-rollback.md`

#### ✅ OA04 Contract Family — PR Sequence (Complete)

- **Status**: COMPLETE — contract ADRs implemented in maintained code; bootstrap remains blocked on OA07.1 worktree execution
- **Context**: OA04.2–OA04.5 are the contract-layer ADRs between the OA07 runtime foundations and the maintained runner/policy/provenance implementations. That contract family is now landed in code and should no longer be treated as pending. See implementation notes in [ADR-OA04.1 Addendum 2026-03-27](/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md) for the original scaffolding gaps and [ADR-OA04.1 Addendum 2026-04-05](/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md) for the bootstrap-first reprioritization.
- **Dependency chain**:
  - OA04.3 (run dir + manifests + evaluator evidence seam) → OA04.2 (runners normalize into canonical evidence)
  - OA04.4 (policy taxonomy + requested/effective split) → OA04.2 (runner request carries typed requested policy)
  - OA04.5 (harness backend) → `validation/` subsystem (extends empty package)
  - OA04.2 (runner adapters) → milestone: first real agent invocations
- **Implementation Notes (default choices for implementers)**:
  - Apply OS01 pragmatically: add structure where it protects a real boundary or likely evolution seam, not just to mirror the taxonomy mechanically.
  - Prefer moving maintained code toward the ADR contracts when the migration path is clean; do not preserve stub shapes just for short-term compatibility inside maintained packages.
  - Treat `run_artifacts/` as the canonical evidence boundary. If a choice arises between storing data in runner-local files versus canonical artifact roles + manifests, choose canonical artifact roles + manifests.
  - Keep evaluator assembly strict: evaluators read `metadata.json`, `events.ndjson`, `manifest.json`, and canonical artifact roles only. Do not add evaluator dependencies on adapter-local raw capture filenames.
  - Keep manifests thin and stable. Put compact cross-step evidence in `evidence_summary`; put detailed per-step policy data in canonical `policy_summary.json`.
  - Keep persistence ownership in `run_artifacts/`. Runner adapters and validation backends should return typed normalized outputs and artifact payloads; they should not own final manifest writing policy.
  - Evolve existing maintained code where it already matches the target shape. In particular, refactor `validation/service.py` toward the script backend/resolver seam rather than replacing it wholesale.
  - Expand `kernel/service.py` by extraction, not accretion. If per-step provenance writing starts to crowd the kernel, extract focused collaborators rather than growing one large procedural service.
  - Use explicit mapper/normalizer classes whenever native CLI or harness output is translated into maintained models. Do not hide parsing, normalization, termination mapping, and persistence decisions in one adapter class.
  - Keep policy taxonomy aligned with OS01: init-time settings/config, per-step requested policy, execution-time effective policy, persisted `PolicySummary`. Avoid “policy blob” models that mix those concerns.
  - Do not add ceremony without benefit: avoid speculative service/factory layers, unnecessary mappers for nearly identical shapes, or package splits that do not improve testability, replaceability, or clarity.
  - Existing thin models in `run_artifacts/`, `runners/`, and `validation/` are scaffolding, not target architecture. It is acceptable to break those internal shapes in favor of cleaner maintained contracts during this implementation sequence.
- **PR Sequence**:
  - [x] **PR-1** `feat/oa04-contract-adrs` — ADR acceptance (docs only)
    - Commit new OA04.2, OA04.3, OA04.4, OA04.5 files; later implementation has since moved those decimal ADRs to `implemented`
    - Carry in already-modified OA03.1/OA03.3 addendums + OA04 update + index.md
  - [x] **PR-2** `feat/oa04.3-run-artifact-contract` — Run-artifact domain contract + store (medium)
    - Expand `run_artifacts/models.py`: `RunMetadata`, `RunEventRecord`, `ArtifactRole` enum, `StepArtifactEntry`, `StepManifest`
    - Add manifest-level `evidence_summary` with compact canonical evidence references
    - Add canonical `policy_summary` artifact role for detailed requested/effective policy records
    - Expand `run_artifacts/protocols.py`: `write_step_manifest`, `artifact_step_dir`, canonical artifact persistence APIs
    - Update `run_artifacts/filesystem_store.py` to implement both
    - Keep filesystem concerns behind the store; no evaluator-facing filename dependencies
    - Tests for manifest writing, event stream fields, and canonical artifact-role lookup
  - [x] **PR-3** `feat/oa04.3-kernel-provenance-integration` — Kernel provenance integration (medium)
    - Update kernel/runtime services to write enriched run metadata, canonical events, and per-step manifests
    - Persist compact manifest summaries and canonical artifact references only; no adapter-local evidence lookup in evaluator assembly
    - Capture workspace diff/status and policy summary references through canonical artifact roles
    - Tests for manifest/event creation across `RUN_AGENT`, `RUN_VALIDATION`, `EVALUATE`, and `GATE`
    - *Depends on PR-2*
  - [x] **PR-4** `feat/oa04.4-policy-contract` — Execution policy package (medium)
    - New `agent_orchestration/execution_policy/` package
    - `models.py`: `ExecutionPolicySettings`, `RequestedExecutionPolicy`, `EffectiveExecutionPolicy`, `PolicyViolationClass`, `PolicyViolation`, `PolicySummary`
    - `assembly.py`: `ExecutionPolicyAssembler` for system settings → workflow → step requested policy → runtime override/effective policy derivation
    - `protocols.py`: `ExecutionPolicyAssemblerProtocol`
    - Update `runners/models.py`: retire `PromptInteractionPolicy` stub; link `RunnerTaskRequest` to `RequestedExecutionPolicy`
    - Persist detailed `policy_summary.json` via canonical `policy_summary` artifact role; keep only compact summary data in manifests
    - Tests for assembly precedence, requested/effective policy derivation, and hard-fail behavior
    - *Can run in parallel with PR-3*
  - [x] **PR-5** `feat/oa04.2-runner-adapters` — Runner adapters (largest PR)
    - Expand `runners/models.py`: `AdapterCapabilities` (capability declaration per OA04.2 §3a)
    - Add explicit mapper/normalizer classes for native CLI output → maintained runner-domain models
    - Add `runners/adapters/claude_cli.py`: `claude --print --output-format stream-json --permission-mode dontAsk`, stream-json parsing, normalization, termination mapping
    - Add `runners/adapters/codex_cli.py`: `codex exec --json --output-last-message`, JSONL capture, normalization, termination mapping
    - Adapters return typed normalized artifact payloads; canonical persistence is owned by `run_artifacts`
    - Evaluators consume manifests and canonical artifact roles only, never runner-local raw capture files
    - Tests for both adapters (subprocess mocking, normalization, mapper behavior, termination paths)
    - *Depends on PR-2, PR-3, and PR-4*
  - [x] **PR-6** `feat/oa04.5-harness-backend` — Script harness backend (medium)
    - Build out `agent_orchestration/validation/`: `BackendFamily` enum, `HarnessBackendRequest`, `HarnessBackendResult`, `HarnessBackendProtocol`
    - `backends/script.py`: migrate from `conductor_mvp/providers/validation_runner.py`; normalize to `validation_report`/`validation_stdout`/`validation_stderr` artifact roles
    - Add backend resolver seam, but defer `cli` and `web` implementation until a concrete maintained consumer exists
    - Tests for script backend, resolver seam, and artifact role normalization
    - *Depends on PR-2; independent of PR-4 and PR-5*

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

#### 🔮 Full-Coverage yt-dlp Test Suite + Monthly Ops Trigger

- **Status**: IN PROGRESS
- **Priority**: HIGH (external dependency instability)
- **Goal**: Add full coverage for all yt-dlp usage modules (transcript, audio, metadata, video download), then run a scheduled monthly ops test to surface breakage early.
- **Scope (Code)**:
  - `src/tnh_scholar/video_processing/video_processing.py`
  - `src/tnh_scholar/cli_tools/ytt_fetch/ytt_fetch.py`
  - `src/tnh_scholar/cli_tools/audio_transcribe/audio_transcribe.py`
  - `src/tnh_scholar/cli_tools/audio_transcribe/version_check.py`
- **Testing Strategy**:
  - [x] Add integration tests that exercise live yt-dlp behavior (guarded, opt-in)
  - [x] Add unit tests for runtime env inspection + yt-dlp option injection
  - [ ] Add offline unit tests with recorded fixtures for metadata + transcript parsing
  - [ ] Add failure-mode tests (missing captions, private video, geo-blocked)
- **Monthly Ops Trigger**:
  - [x] Add cron-ready ops check script + validation URL list
  - [x] Document monthly cron usage and log locations
  - [ ] Add failure notification workflow (issue creation or alerting)
- **Acceptance Criteria**:
  - [ ] Coverage for all yt-dlp entry points + error paths
  - [ ] Monthly ops check runs without manual intervention (cron)
  - [ ] Clear failure report includes test URL, date, yt-dlp version

#### 🔮 Patch ytt-fetch Robustness

- **Status**: IN PROGRESS
- **Priority**: HIGH (frequent breakage path)
- **Goal**: Make ytt-fetch resilient to upstream changes and failures.
- **Test URL**: `https://youtu.be/iqNzfK4_meQ`
- **Deliverables**:
  - [x] Add runtime preflight + yt-dlp runtime option injection
  - [ ] Verify transcript fetch on test URL (manual + test)
  - [ ] Add retries / improved error reporting
  - [ ] Ensure metadata embed + output path handling remain stable
  - [x] Update docs and CLI reference if flags or behaviors change

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

#### 🚧 Audio-Transcribe Service-Layer Refactor (P2)

- **Status**: NOT STARTED
- **Goal**: Align audio-transcribe with object-service pattern and ytt-fetch robustness.
- **Tasks**:
  - [ ] Introduce typed service orchestrator + protocols (CLI becomes thin wrapper)
  - [ ] Extract audio source resolution into a typed resolver (yt_url/CSV/local file)
  - [ ] Replace dict options with Pydantic models (transcription + diarization params)
  - [ ] Move logging bootstrap out of module import path so `audio-transcribe` modules are import-safe in tests and sandboxed environments
  - [ ] Add runtime preflight (yt-dlp inspector + ffmpeg availability); keep version checks ops-only
  - [ ] Migrate CLI to Typer with minimal surface (smoke tests only)
  - [ ] Add service-layer tests for all audio-transcribe use cases

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

#### 🚧 Configuration Tech Debt — Migrate to ADR-CF01/CF02 Three-Layer Model

- **Status**: PHASES 1-3 COMPLETE, Phase 4-5 NOT STARTED
- **Priority**: MEDIUM (foundational, not blocking current work)
- **ADRs**:
  - [ADR-CF01: Runtime Context & Configuration Strategy](/architecture/configuration/adr/adr-cf01-runtime-context-strategy.md)
  - [ADR-CF02: Prompt Catalog Discovery Strategy](/architecture/configuration/adr/adr-cf02-prompt-catalog-discovery.md) (status: accepted)
- **Related**: [ADR-A08: Config/Params/Policy Taxonomy](/architecture/gen-ai-service/adr/adr-a08-config-params-policy-taxonomy.md)

**Migration Phases**:

1. **Phase 1: Extend TNHContext for Prompts** ✅ COMPLETE
   - [x] Add `PromptPathBuilder` analogous to `RegistryPathBuilder` — `src/tnh_scholar/configuration/context.py:165-191`
   - [x] Define three-layer prompt discovery: workspace → user → built-in
   - [x] Create `runtime_assets/prompts/` with minimal built-in set (3 prompts + `_catalog.yaml`)
   - [x] Unit tests for prompt path resolution — `tests/configuration/test_prompt_discovery.py`

2. **Phase 2: Migrate GenAISettings** ✅ COMPLETE
   - [x] Update `GenAISettings.prompt_dir` to use lazy TNHContext resolution — `settings.py:89-102`
   - [x] Legacy `TNH_DEFAULT_PROMPT_DIR` constant removed from `__init__.py`
   - [x] tnh-gen config_loader works with new resolution

3. **Phase 3: Eliminate Module-Level Constants** ✅ COMPLETE
   - [x] `TNH_CONFIG_DIR`, `TNH_LOG_DIR`, `TNH_DEFAULT_PROMPT_DIR` removed from `__init__.py`
   - [x] Only structural constants remain (`TNH_ROOT_SRC_DIR`, `TNH_PROJECT_ROOT_DIR`, `TNH_CLI_TOOLS_DIR`)
   - [x] No `FileNotFoundError` raises at import time for config paths

4. **Phase 4: Unify Subsystem Settings** (Medium Priority) — NOT STARTED
   - [ ] Audit all `BaseSettings` classes across subsystems
   - [ ] Deprecate `PromptSystemSettings.tnh_prompt_dir` in favor of unified approach
   - [ ] Standardize env var prefixes (e.g., `TNH_GENAI_*`, `TNH_AUDIO_*`)

5. **Phase 5: Propagate tnh-gen Config Pattern** (Low Priority) — NOT STARTED
   - [ ] Create shared `CLIConfigLoader` base for all CLI tools
   - [ ] Add `config show/get/set` subcommands to major CLI tools
   - [ ] Standardize workspace config file format

**Success Criteria**:
- [x] No module-level config `Path` constants in `__init__.py`
- [x] Prompt path discovery flows through `TNHContext`
- [x] Prompt directories follow three-layer precedence (workspace → user → built-in)
- [ ] At least tnh-gen and audio-transcribe share config loader pattern

#### 🚧 Clean Up CLI Tool Versions

- **Status**: PARTIAL (old versions removed, utilities pending)
- **Location**: [cli_tools/audio_transcribe/](src/tnh_scholar/cli_tools/audio_transcribe/)
- **Tasks**:
  - [x] Remove legacy `audio_transcribe0.py`
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

#### 🔮 Shared CLI UI Module (tnh_cli_ui)

- **Status**: NOT STARTED (Research/Exploration)
- **Priority**: MEDIUM (UX consistency across CLI tools)
- **ADR**: [ADR-ST01.1: tnh-setup UI Design](/architecture/setup-tnh/adr/adr-st01.1-tnh-setup-ui-design.md)
- **Context**: The tnh-setup UI redesign (Rich library) could be extracted into a shared module for consistent styling across all tnh-scholar CLI tools.
- **Research Questions**:
  - [ ] Survey CLI tools for shared UI patterns (headers, status indicators, progress, tables)
  - [ ] Evaluate Rich vs alternatives (click-extra, questionary, etc.)
  - [ ] Design minimal API surface for common operations
  - [ ] Consider Typer + Rich integration patterns
- **Potential Scope**:
  - Styled section headers with step progress
  - Standardized status indicators (✓/⚠/✗/○/•) with color vocabulary
  - Spinner wrappers for async operations
  - Summary table generators
  - Banner/header utilities
- **Affected Tools**: tnh-setup, tnh-gen, ytt-fetch, audio-transcribe, nfmt, token-count, tnh-tree

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

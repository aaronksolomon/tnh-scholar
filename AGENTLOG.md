# AGENTLOG

This file captures AI agent interactions, decisions, discoveries, and work performed on the TNH Scholar project. It provides historical context for continuity across sessions and helps human collaborators understand the evolution of the codebase.

See [AGENTLOG_TEMPLATE.md](AGENTLOG_TEMPLATE.md) for structure and format.

**Archive**: Older sessions are archived in [`archive/agentlogs/`](archive/agentlogs/) with a summary index at [`archive/agentlogs/archive-index.md`](archive/agentlogs/archive-index.md).
Archived previous active log: [`archive/agentlogs/AGENTLOG-03-28-26.md`](archive/agentlogs/AGENTLOG-03-28-26.md).

**Ordering**: Append new records at the end (chronological order from least to most recent).

---

## [2026-03-31 10:42 PDT] OA04.4 Policy Contract

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: oa04-pr-series-build-sequence
**Human Collaborator**: phapman

### Context
Started the next TODO-ordered OA04 implementation slice from clean `main` on branch `feat/oa04.4-policy-contract`. The accepted target for this PR was ADR-OA04.4: add the maintained execution-policy package, replace the runner stub policy type, persist canonical `policy_summary` artifacts, and close the policy-contract gap before the runner-adapter PRs.

### Key Decisions
- **Keep PR-4 at the maintained policy boundary**: define typed settings/requested/effective/summary models plus an assembler and keep native flag mapping for adapter-local work in PR-5.
- **Persist policy evidence for every executed step**: write `policy_summary.json` before dispatch so failure paths retain policy evidence instead of only happy-path manifests carrying it.
- **Treat hard-fail behavior as part of PR-4, not a later follow-up**: kernel enforcement now raises on maintained hard violations instead of only persisting passive violation data.
- **Represent inheritance explicitly**: `RequestedExecutionPolicy.allowed_paths=None` means inherit, while `allowed_paths=()` means intentionally empty scope.
- **Keep shared runner enums below package initializers**: move `AgentFamily` and `RunnerTermination` into `shared_enums.py` so `runners/`, `run_artifacts/`, and `kernel/` can share them without package-init cycles.

### Work Completed
- [x] Added the maintained `execution_policy/` package with typed models, assembler logic, and protocol surface (files: `src/tnh_scholar/agent_orchestration/execution_policy/models.py`, `src/tnh_scholar/agent_orchestration/execution_policy/assembly.py`, `src/tnh_scholar/agent_orchestration/execution_policy/protocols.py`, `src/tnh_scholar/agent_orchestration/execution_policy/__init__.py`)
- [x] Replaced `PromptInteractionPolicy` with `RequestedExecutionPolicy` on `RunnerTaskRequest` and updated maintained runner exports accordingly (files: `src/tnh_scholar/agent_orchestration/runners/models.py`, `src/tnh_scholar/agent_orchestration/runners/__init__.py`)
- [x] Added `shared_enums.py` and rewired maintained imports so runner-facing enums no longer depend on package initializers (files: `src/tnh_scholar/agent_orchestration/shared_enums.py`, `src/tnh_scholar/agent_orchestration/kernel/enums.py`, `src/tnh_scholar/agent_orchestration/run_artifacts/models.py`)
- [x] Extended workflow/kernel policy references across executable step types and added workflow default policy support (file: `src/tnh_scholar/agent_orchestration/kernel/models.py`)
- [x] Wired kernel policy assembly and canonical persistence so every executed step emits `policy_summary.json` and compact policy notes in manifest evidence (files: `src/tnh_scholar/agent_orchestration/kernel/service.py`, `src/tnh_scholar/agent_orchestration/kernel/provenance.py`)
- [x] Implemented maintained hard-fail enforcement for protected-branch workspace-write violations and impossible empty write-scope violations before step dispatch (file: `src/tnh_scholar/agent_orchestration/kernel/service.py`)
- [x] Added focused contract and integration tests for precedence, explicit-empty path semantics, approval tightening, non-agent step policy refs, protected-branch enforcement, and hard-fail behavior (files: `tests/agent_orchestration/test_execution_policy_contract.py`, `tests/agent_orchestration/test_oa07_execution_validation_kernel.py`)

### Discoveries & Insights
- **Hard-fail behavior belonged in PR-4 scope**: simply persisting violations without kernel action left the policy contract incomplete relative to TODO and ADR-OA04.4.
- **Policy precedence needed a real inherit sentinel**: tuple truthiness was insufficient for `allowed_paths`; explicit empty scope is semantically different from “no override.”
- **Kernel policy evidence should survive failure**: persisting policy artifacts before dispatch keeps failure-path provenance inspectable and evaluator-safe.
- **Package initializers remain a practical import-cycle hazard**: shared enums are cleaner in a thin module than behind a package `__init__` that eagerly imports services.

### Files Modified/Created
- `src/tnh_scholar/agent_orchestration/execution_policy/models.py`: Added maintained execution-policy contract models.
- `src/tnh_scholar/agent_orchestration/execution_policy/assembly.py`: Implemented precedence, tightening, violation derivation, and unknown-reference failure.
- `src/tnh_scholar/agent_orchestration/execution_policy/protocols.py`: Added execution-policy assembler protocol.
- `src/tnh_scholar/agent_orchestration/execution_policy/__init__.py`: Exported maintained policy package surface.
- `src/tnh_scholar/agent_orchestration/shared_enums.py`: New low-level shared runner enums module.
- `src/tnh_scholar/agent_orchestration/kernel/models.py`: Added workflow default policy and step-level policy refs across executable step types.
- `src/tnh_scholar/agent_orchestration/kernel/service.py`: Added policy assembly, persistence, hard-fail enforcement, and runner request propagation.
- `src/tnh_scholar/agent_orchestration/kernel/provenance.py`: Preserved policy artifacts on failure-path manifests.
- `src/tnh_scholar/agent_orchestration/kernel/enums.py`: Re-exported shared runner enums cleanly.
- `src/tnh_scholar/agent_orchestration/run_artifacts/models.py`: Switched runner-facing enum imports to the shared lower-level module.
- `src/tnh_scholar/agent_orchestration/runners/models.py`: Replaced runner prompt policy stub with requested execution policy.
- `src/tnh_scholar/agent_orchestration/runners/__init__.py`: Updated maintained runner exports.
- `tests/agent_orchestration/test_execution_policy_contract.py`: Added direct PR-4 contract coverage.
- `tests/agent_orchestration/test_oa07_execution_validation_kernel.py`: Expanded kernel integration coverage for policy persistence and hard-fail enforcement.

### Validation Performed
- `poetry run pytest tests/agent_orchestration/test_execution_policy_contract.py tests/agent_orchestration/test_oa07_execution_validation_kernel.py tests/agent_orchestration/test_run_artifacts_contract.py -q`
- `poetry run ruff check src/tnh_scholar/agent_orchestration/execution_policy src/tnh_scholar/agent_orchestration/shared_enums.py src/tnh_scholar/agent_orchestration/kernel/service.py src/tnh_scholar/agent_orchestration/kernel/provenance.py src/tnh_scholar/agent_orchestration/kernel/models.py src/tnh_scholar/agent_orchestration/kernel/enums.py src/tnh_scholar/agent_orchestration/runners src/tnh_scholar/agent_orchestration/run_artifacts/models.py tests/agent_orchestration/test_execution_policy_contract.py tests/agent_orchestration/test_oa07_execution_validation_kernel.py`
- `poetry run mypy src/tnh_scholar/agent_orchestration/execution_policy src/tnh_scholar/agent_orchestration/shared_enums.py src/tnh_scholar/agent_orchestration/kernel/service.py src/tnh_scholar/agent_orchestration/kernel/provenance.py src/tnh_scholar/agent_orchestration/kernel/models.py src/tnh_scholar/agent_orchestration/kernel/enums.py src/tnh_scholar/agent_orchestration/runners src/tnh_scholar/agent_orchestration/run_artifacts/models.py tests/agent_orchestration/test_execution_policy_contract.py tests/agent_orchestration/test_oa07_execution_validation_kernel.py`

### Next Steps
- [ ] Refresh generated tree files and run repo PR readiness checks for the PR-4 slice.
- [ ] Commit `feat/oa04.4-policy-contract` with changelog/TODO/AGENTLOG updates.
- [ ] Push the branch and open the PR for review.

### Open Questions
- None in the maintained PR-4 slice after the hard-fail, step-policy, and explicit-empty override fixes.

### References
- [docs/architecture/agent-orchestration/adr/adr-oa04.4-policy-enforcement-contract.md](docs/architecture/agent-orchestration/adr/adr-oa04.4-policy-enforcement-contract.md)
- [docs/architecture/agent-orchestration/adr/adr-oa04.2-runner-contract.md](docs/architecture/agent-orchestration/adr/adr-oa04.2-runner-contract.md)
- [docs/architecture/agent-orchestration/adr/adr-oa04.3-provenance-run-artifact-contract.md](docs/architecture/agent-orchestration/adr/adr-oa04.3-provenance-run-artifact-contract.md)
- [TODO.md](TODO.md)

## [2026-03-28 22:34 PDT] OA04.3 Kernel Provenance Integration

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: oa04-pr-series-build-sequence
**Human Collaborator**: phapman

### Context
Started the next TODO-ordered OA04 implementation slice after PR-2 merged to `main`. The branch for this work is `feat/oa04.3-kernel-provenance-integration`, scoped to PR-3: wiring the maintained kernel to emit the richer OA04.3 provenance contract through canonical run-artifact events, manifests, metadata, and evidence artifacts without pulling PR-4 policy-contract work forward.

### Key Decisions
- **Keep PR-3 focused on kernel provenance assembly**: use the maintained `run_artifacts/` layer from PR-2 and avoid inventing policy-summary persistence before PR-4 defines that contract.
- **Record failure-path provenance as a first-class outcome**: a `step_started` event without a corresponding failure terminal record is not acceptable for this repo’s canonical evidence boundary, so each step now writes failure metadata, manifests, and `step_failed` events before re-raising.
- **Persist typed artifact payloads, not ad hoc dicts**: introduce maintained Pydantic artifact models for runner metadata and gate request/outcome payloads to stay aligned with OS01 and the repo’s “no dict/literal sprawl” rule.
- **Keep `run_artifacts/` lower-level than runners**: move `AgentFamily` and `RunnerTermination` into `kernel/enums.py` so canonical artifact models do not depend upward on `runners/`.

### Work Completed
- [x] Created and wired a new provenance collaborator for the kernel to record canonical step lifecycle events, gate events, rollback events, step manifests, and workspace evidence artifacts (files: `src/tnh_scholar/agent_orchestration/kernel/provenance.py`, `src/tnh_scholar/agent_orchestration/kernel/service.py`)
- [x] Added maintained typed artifact payloads for canonical JSON evidence written by the kernel during agent and gate steps (files: `src/tnh_scholar/agent_orchestration/run_artifacts/models.py`)
- [x] Updated the kernel run path to write final metadata fields on success and failure, including `ended_at`, `last_step_id`, and terminal `termination`, alongside canonical final-state persistence (file: `src/tnh_scholar/agent_orchestration/kernel/service.py`)
- [x] Removed app-layer dict payload assembly for canonical runner/gate artifacts and replaced it with typed models (files: `src/tnh_scholar/agent_orchestration/kernel/service.py`, `src/tnh_scholar/agent_orchestration/run_artifacts/models.py`)
- [x] Removed the `run_artifacts -> runners` layering violation by relocating shared runner-facing enums into the lower-level kernel enum module (files: `src/tnh_scholar/agent_orchestration/kernel/enums.py`, `src/tnh_scholar/agent_orchestration/runners/models.py`, `src/tnh_scholar/agent_orchestration/run_artifacts/models.py`)
- [x] Expanded maintained OA07 kernel tests to cover manifest contents, canonical event streams, timestamp shape, failure-path provenance, and the absence of raw runner-local file paths in canonical metadata artifacts (files: `tests/agent_orchestration/test_oa07_execution_validation_kernel.py`)
- [x] Tightened `KernelProvenanceRecorder` structure by extracting helper methods so the main manifest-recording path stays within repo function-size expectations (file: `src/tnh_scholar/agent_orchestration/kernel/provenance.py`)

### Discoveries & Insights
- **Failure-path provenance was a real contract gap**: without a step-level exception boundary, any runner/validator/planner/gate exception left behind only `step_started`, which is insufficient for evaluators and inconsistent with the OA04.3 event model.
- **Canonical evidence should not expose adapter-local capture filenames**: removing raw `transcript_path` and `final_response_path` from `runner_metadata.json` keeps the maintained evidence boundary compact and discourages downstream coupling to runner-internal file layout.
- **Typed persistence can still violate layering if the shared types live too high**: using runner enums directly from `run_artifacts/` looked clean locally but created the wrong dependency direction for upcoming adapter work.

### Files Modified/Created
- `src/tnh_scholar/agent_orchestration/kernel/provenance.py`: New kernel provenance recorder for canonical event, manifest, and artifact emission.
- `src/tnh_scholar/agent_orchestration/kernel/service.py`: Wired provenance recording into the main execution path, success/failure metadata persistence, and typed canonical artifact writes.
- `src/tnh_scholar/agent_orchestration/kernel/enums.py`: Added shared runner-facing enums to preserve lower-level dependency direction.
- `src/tnh_scholar/agent_orchestration/run_artifacts/models.py`: Added typed canonical artifact payload models and updated imports to shared enums.
- `src/tnh_scholar/agent_orchestration/runners/models.py`: Switched runner models to import shared enums from `kernel/enums.py`.
- `tests/agent_orchestration/test_oa07_execution_validation_kernel.py`: Expanded provenance integration coverage for happy-path and failure-path kernel behavior.

### Validation Performed
- `poetry run pytest tests/agent_orchestration/test_oa07_execution_validation_kernel.py tests/agent_orchestration/test_run_artifacts_contract.py -q`
- `poetry run ruff check src/tnh_scholar/agent_orchestration/kernel/enums.py src/tnh_scholar/agent_orchestration/kernel/provenance.py src/tnh_scholar/agent_orchestration/run_artifacts/models.py src/tnh_scholar/agent_orchestration/runners/models.py tests/agent_orchestration/test_oa07_execution_validation_kernel.py tests/agent_orchestration/test_run_artifacts_contract.py`
- `poetry run mypy src/tnh_scholar/agent_orchestration/kernel/enums.py src/tnh_scholar/agent_orchestration/kernel/provenance.py src/tnh_scholar/agent_orchestration/run_artifacts/models.py src/tnh_scholar/agent_orchestration/runners/models.py tests/agent_orchestration/test_oa07_execution_validation_kernel.py tests/agent_orchestration/test_run_artifacts_contract.py`

### Next Steps
- [ ] Review the PR-3 diff one more time for scope discipline and TODO alignment.
- [ ] Commit the kernel provenance integration slice on `feat/oa04.3-kernel-provenance-integration`.
- [ ] Push the branch and open the PR once the diff and branch note are clean.

### Open Questions
- None in the current PR-3 slice after the failure-path and layering fixes.

### References
- [docs/architecture/agent-orchestration/adr/adr-oa04.3-provenance-run-artifact-contract.md](docs/architecture/agent-orchestration/adr/adr-oa04.3-provenance-run-artifact-contract.md)
- [docs/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md](docs/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md)
- [docs/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md](docs/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)
- [TODO.md](TODO.md)

## [2026-03-28 20:53 PDT] OA04.3 Run-Artifact Contract First Coding Pass

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: oa04-pr-series-build-sequence
**Human Collaborator**: phapman

### Context
Started the OA04 contract-family implementation sequence from `main` after the OA04 ADR set was locked down and the TODO plan was updated. The first coding slice targeted PR-2, `feat/oa04.3-run-artifact-contract`, with scope limited to the maintained run-artifact contract/store layer and only the minimum kernel compatibility updates required by that contract.

### Key Decisions
- **Start with PR-2, not PR-1**: PR-1 was already effectively represented by the docs-only OA04 acceptance commit on `main`, so coding began with the first implementation slice in TODO order.
- **Keep PR-2 scoped to contract/store work**: expand `run_artifacts/` and add only the minimum kernel compatibility needed for richer metadata/event persistence, while deferring manifest-writing and fuller provenance assembly to PR-3.
- **Treat ADR-OA04.3 as authoritative for `artifacts_root`**: persist the configured parent run-artifact directory, not the per-run `artifacts/` subtree.
- **Preserve typed schema tokens**: keep uppercase `Opcode` values because they are the canonical OA04 workflow DSL tokens, while runtime status enums remain lowercase.
- **Narrow the persistence boundary**: remove arbitrary write methods from the maintained run-artifact protocol and keep canonical persistence role-based.

### Work Completed
- [x] Reviewed repo-local agent instructions, OS01 architecture guidance, design principles, style guide, OA04 ADR set, TODO implementation plan, system-design context, and recent AGENTLOG continuity before coding (files: `AGENTS.md`, `docs/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md`, `docs/development/design-principles.md`, `docs/development/style-guide.md`, `docs/architecture/agent-orchestration/adr/adr-oa04*.md`, `TODO.md`, `docs/architecture/agent-orchestration/system-design.md`, `AGENTLOG.md`)
- [x] Created the implementation branch for the first OA04.3 code slice (branch: `feat/oa04.3-run-artifact-contract`)
- [x] Expanded maintained run-artifact domain models for OA04.3, including canonical artifact roles, event types, evidence summaries, step artifact entries, manifests, and richer run metadata (files: `src/tnh_scholar/agent_orchestration/run_artifacts/models.py`)
- [x] Expanded the maintained run-artifact protocol and filesystem store for step directories, final-state persistence, manifest persistence, and role-based text/JSON artifact writing (files: `src/tnh_scholar/agent_orchestration/run_artifacts/protocols.py`, `src/tnh_scholar/agent_orchestration/run_artifacts/filesystem_store.py`, `src/tnh_scholar/agent_orchestration/run_artifacts/__init__.py`)
- [x] Updated the maintained kernel only where required for the new contract, including richer run metadata, canonical event records, typed `Opcode.stop` usage, and removal of the prior `STOP_STEP_ID` module constant (files: `src/tnh_scholar/agent_orchestration/kernel/enums.py`, `src/tnh_scholar/agent_orchestration/kernel/models.py`, `src/tnh_scholar/agent_orchestration/kernel/service.py`, `src/tnh_scholar/agent_orchestration/kernel/catalog.py`, `src/tnh_scholar/agent_orchestration/kernel/validator.py`, `src/tnh_scholar/agent_orchestration/kernel/__init__.py`)
- [x] Added focused OA04.3 run-artifact contract tests and updated maintained OA07 kernel tests for the new event shape and role-based artifact writing (files: `tests/agent_orchestration/test_run_artifacts_contract.py`, `tests/agent_orchestration/test_oa07_execution_validation_kernel.py`)
- [x] Performed a review/fix pass after independent feedback, tightening `artifacts_root`, typed contract fields, and the run-artifact persistence boundary without expanding into PR-3 scope.

### Discoveries & Insights
- **PR-1 is effectively landed already**: the accepted OA04 ADR family and TODO sequencing are already on `main`, so the first meaningful implementation branch is the OA04.3 contract/store slice.
- **`artifacts_root` semantics are easy to misread**: the ADR defines it as the configured parent root (for example `.tnh/run/`), while step artifacts still belong under the per-run `artifacts/` subtree.
- **Typed enum reuse across subsystems can create import cycles**: sharing kernel enums with run-artifact models required extracting them into a small dedicated `kernel/enums.py` module to preserve strong typing cleanly.
- **Uppercase opcode values are intentional schema tokens**: they mirror the OA04 workflow document syntax and should not be normalized to match lowercase runtime status enums.

### Files Modified/Created
- `src/tnh_scholar/agent_orchestration/run_artifacts/models.py`: Expanded OA04.3 run metadata, event, artifact, evidence, and manifest models.
- `src/tnh_scholar/agent_orchestration/run_artifacts/protocols.py`: Reworked maintained artifact-store protocol toward canonical role-based persistence.
- `src/tnh_scholar/agent_orchestration/run_artifacts/filesystem_store.py`: Implemented run root/artifact directory separation, final-state persistence, manifest writing, and canonical artifact writes.
- `src/tnh_scholar/agent_orchestration/run_artifacts/__init__.py`: Exported maintained run-artifact surface including the store protocol.
- `src/tnh_scholar/agent_orchestration/kernel/enums.py`: New shared enum module for kernel schema/runtime enums.
- `src/tnh_scholar/agent_orchestration/kernel/models.py`: Removed local enum definitions and `STOP_STEP_ID`; retained typed workflow models against shared enums.
- `src/tnh_scholar/agent_orchestration/kernel/service.py`: Updated run metadata/event persistence and final-state writing for the maintained OA04.3 contract.
- `src/tnh_scholar/agent_orchestration/kernel/catalog.py`: Updated STOP handling to use typed opcode value and tightened route typing.
- `src/tnh_scholar/agent_orchestration/kernel/validator.py`: Updated STOP handling to use typed opcode value.
- `src/tnh_scholar/agent_orchestration/kernel/__init__.py`: Re-exported shared kernel enums cleanly after enum extraction.
- `tests/agent_orchestration/test_run_artifacts_contract.py`: Added direct OA04.3 contract coverage including final-state persistence and BaseModel JSON artifact handling.
- `tests/agent_orchestration/test_oa07_execution_validation_kernel.py`: Updated maintained kernel tests for richer event records and role-based artifact writes.

### Validation Performed
- `poetry run pytest tests/agent_orchestration/test_run_artifacts_contract.py tests/agent_orchestration/test_oa07_execution_validation_kernel.py -q`
- `poetry run ruff check src/tnh_scholar/agent_orchestration/kernel src/tnh_scholar/agent_orchestration/run_artifacts tests/agent_orchestration/test_run_artifacts_contract.py tests/agent_orchestration/test_oa07_execution_validation_kernel.py`
- `poetry run mypy src/tnh_scholar/agent_orchestration/kernel src/tnh_scholar/agent_orchestration/run_artifacts tests/agent_orchestration/test_run_artifacts_contract.py`

### Next Steps
- [ ] Review the current OA04.3 branch diff for any remaining PR-2 scope cleanup before commit.
- [ ] Commit the OA04.3 run-artifact contract slice on `feat/oa04.3-run-artifact-contract`.
- [ ] Begin PR-3 kernel provenance integration only after the PR-2 contract/store slice is considered stable.

### Open Questions
- None in the current OA04.3 contract/store slice after the `artifacts_root` and opcode-style clarifications.

### References
- [docs/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md](docs/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)
- [docs/architecture/agent-orchestration/adr/adr-oa04.3-provenance-run-artifact-contract.md](docs/architecture/agent-orchestration/adr/adr-oa04.3-provenance-run-artifact-contract.md)
- [docs/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md](docs/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md)
- [TODO.md](TODO.md)

---

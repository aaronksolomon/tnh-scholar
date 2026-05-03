# AGENTLOG

This file captures AI agent interactions, decisions, discoveries, and work performed on the TNH Scholar project. It provides historical context for continuity across sessions and helps human collaborators understand the evolution of the codebase.

See [AGENTLOG_TEMPLATE.md](AGENTLOG_TEMPLATE.md) for structure and format.

**Archive**: Older sessions are archived in [`archive/agentlogs/`](archive/agentlogs/) with a summary index at [`archive/agentlogs/archive-index.md`](archive/agentlogs/archive-index.md).
Archived previous active log: [`archive/agentlogs/AGENTLOG-03-28-26.md`](archive/agentlogs/AGENTLOG-03-28-26.md).

**Ordering**: Append new records at the end (chronological order from least to most recent).

---

## [2026-04-09 00:05 PDT] OA07.1 Worktree Runtime Boundary Merge Wrap-Up

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: PR #45 follow-up / merge wrap-up
**Human Collaborator**: phapman

### Context
PR #45 (`feat/oa07.1-worktree-workspace-service`) was merged to `main`, but one local docs-only follow-up commit still needed to be carried over. This wrap-up synced that strict-docs fix onto clean `main`, checked the affected OA07.1 planning and OA03.3 historical-reference docs, and captured the merged slice in the agent log per repo policy.

### Key Decisions
- **Land the missing docs fix directly on clean `main`**: cherry-pick the local strict-docs cleanup instead of reopening a feature branch, since the substantive PR was already merged.
- **Keep the docs follow-up narrow**: preserve the OA07.1 plan-note wording fix and replace the OA03.3 archive hyperlink with repository-path text rather than touching generated docs indexes again.
- **Use a temporary clean main worktree**: avoid mixing post-merge cleanup with the dirty local feature worktree that still contains generated docs drift.

### Work Completed
- [x] Fetched/pruned remote refs, confirmed PR #45 merged on `origin/main`, and identified the one unmerged local follow-up commit `66623da4` (files: local git history, `CHANGELOG.md`, `docs/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-runner.md`, `docs/architecture/agent-orchestration/notes/oa07.1-pr7-worktree-workspace-plan.md`)
- [x] Created a temporary clean `main` worktree, fast-forwarded it to `origin/main`, and cherry-picked the strict-docs warning cleanup as `ce1ed92b` (files: temporary `/tmp/tnh-scholar-main-sync` worktree)
- [x] Rechecked the OA07.1 plan note and the OA03.3 archived-reference section to confirm the intended post-merge docs state (files: `docs/architecture/agent-orchestration/notes/oa07.1-pr7-worktree-workspace-plan.md`, `docs/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-runner.md`)
- [x] Appended the required merged-PR continuity record to `AGENTLOG.md` (files: `AGENTLOG.md`)

### Discoveries & Insights
- **PR #45 merged without the final docs-only cleanup**: the merged branch head on `origin/main` stopped at the workflow/code follow-ups, while the strict-docs fix existed only in the local feature branch.
- **The OA07.1 TODO-link warning fix is simple and correct**: replacing the repo-root docs link with plain `TODO.md` text is the cleanest published-docs-safe choice.
- **The remaining OA03.3 docs warning was just an excluded archive link**: converting it to plain repository-path text preserves the historical pointer without tripping MkDocs strict mode.

### Files Modified/Created
- `CHANGELOG.md`: Carries the docs strict-build warning cleanup entry now applied on `main`.
- `docs/architecture/agent-orchestration/notes/oa07.1-pr7-worktree-workspace-plan.md`: Uses plain `TODO.md` text instead of a published-docs-broken repo-root link.
- `docs/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-runner.md`: Replaces the excluded archive hyperlink with repository-path text for historical reference.
- `AGENTLOG.md`: Added this merge wrap-up entry for PR #45 continuity.

### Next Steps
- [ ] Run `poetry run mkdocs build --strict` from clean `main` and confirm the two known warnings are gone.
- [ ] Push the clean-main wrap-up commit(s) to `origin/main`.
- [ ] Delete the no-longer-needed local `feat/oa07.1-worktree-workspace-service` branch once the wrap-up is fully landed.

### Open Questions
- None for the merged OA07.1 slice if strict docs pass after the final cherry-picked cleanup.

### References
- [docs/architecture/agent-orchestration/adr/adr-oa07.1-worktree-lifecycle-and-rollback.md](docs/architecture/agent-orchestration/adr/adr-oa07.1-worktree-lifecycle-and-rollback.md)
- [docs/architecture/agent-orchestration/notes/oa07.1-pr7-worktree-workspace-plan.md](docs/architecture/agent-orchestration/notes/oa07.1-pr7-worktree-workspace-plan.md)
- [docs/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-runner.md](docs/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-runner.md)
- [CHANGELOG.md](CHANGELOG.md)

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

## [2026-04-03 12:20 PDT] OA04.2 Runner Adapters

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: oa04-pr-series-build-sequence
**Human Collaborator**: phapman

### Context
Started the next TODO-ordered OA04 implementation slice from clean `main` on branch `feat/oa04.2-runner-adapters`. The accepted target for this PR was ADR-OA04.2: replace thin runner scaffolding with maintained Claude/Codex CLI adapters, typed normalization at the adapter boundary, and canonical runner evidence flowing through the existing kernel/run-artifact layers.

### Key Decisions
- **Build adapters above the maintained execution subsystem**: use `execution/` as the only subprocess boundary instead of adding new raw subprocess logic inside `runners/`.
- **Keep canonical persistence in the kernel/run-artifact boundary**: adapters return typed normalized transcript/final-response payloads and invocation metadata; the kernel persists canonical artifact roles and manifests.
- **Fail fast on unsupported guarantees**: if a requested policy shape cannot be enforced natively by an adapter, raise instead of silently degrading.
- **Clarify OA04.2 by addendum rather than bending code to stale wording**: the maintained boundary now prefers typed payload returns over adapter-owned artifact-path semantics.

### Work Completed
- [x] Expanded maintained runner-domain models with adapter capabilities, normalized text artifacts, and typed invocation metadata (file: `src/tnh_scholar/agent_orchestration/runners/models.py`)
- [x] Added adapter and delegating-service seams for maintained runners (files: `src/tnh_scholar/agent_orchestration/runners/protocols.py`, `src/tnh_scholar/agent_orchestration/runners/service.py`, `src/tnh_scholar/agent_orchestration/runners/__init__.py`)
- [x] Implemented execution-backed maintained adapters for Claude CLI and Codex CLI with explicit invocation mappers and output normalizers (files: `src/tnh_scholar/agent_orchestration/runners/adapters/claude_cli.py`, `src/tnh_scholar/agent_orchestration/runners/adapters/codex_cli.py`, `src/tnh_scholar/agent_orchestration/runners/adapters/_shared.py`, `src/tnh_scholar/agent_orchestration/runners/adapters/__init__.py`)
- [x] Updated kernel runner handling so normalized runner outputs are persisted as canonical `runner_transcript`, `runner_final_response`, and richer `runner_metadata` artifacts (files: `src/tnh_scholar/agent_orchestration/kernel/service.py`, `src/tnh_scholar/agent_orchestration/run_artifacts/models.py`)
- [x] Added ADR-OA04.2 addendum clarifying the maintained payload-return shape and persistence ownership (file: `docs/architecture/agent-orchestration/adr/adr-oa04.2-runner-contract.md`)
- [x] Added focused adapter tests plus kernel integration coverage for canonical runner artifact persistence and failure paths (files: `tests/agent_orchestration/test_runner_adapters.py`, `tests/agent_orchestration/test_oa07_execution_validation_kernel.py`)

### Discoveries & Insights
- **OA04.2’s earlier path-shaped wording needed a maintained-runtime clarification**: once PR-3 and PR-4 landed, adapter-returned payloads plus kernel-owned persistence were the cleaner contract.
- **Capability declarations need real enforcement behind them**: approval and network posture handling could not be left as inert fields once adapters started advertising supported native controls.
- **Kernel runner persistence was cleaner after extraction**: splitting transcript/final-response/metadata writes kept the service aligned with the repo’s function-size target while preserving the canonical artifact flow.

### Files Modified/Created
- `src/tnh_scholar/agent_orchestration/runners/models.py`: Added maintained runner capability, artifact, and metadata models.
- `src/tnh_scholar/agent_orchestration/runners/protocols.py`: Added concrete runner-adapter protocol surface.
- `src/tnh_scholar/agent_orchestration/runners/service.py`: Added delegating maintained runner service.
- `src/tnh_scholar/agent_orchestration/runners/adapters/_shared.py`: Added shared executable resolution and termination mapping helpers.
- `src/tnh_scholar/agent_orchestration/runners/adapters/claude_cli.py`: Added maintained Claude CLI invocation mapping and output normalization.
- `src/tnh_scholar/agent_orchestration/runners/adapters/codex_cli.py`: Added maintained Codex CLI invocation mapping and output normalization.
- `src/tnh_scholar/agent_orchestration/runners/adapters/__init__.py`: Exported maintained runner adapters.
- `src/tnh_scholar/agent_orchestration/runners/__init__.py`: Exported the maintained runner subsystem surface.
- `src/tnh_scholar/agent_orchestration/kernel/service.py`: Persisted normalized runner artifacts through canonical artifact roles.
- `src/tnh_scholar/agent_orchestration/run_artifacts/models.py`: Expanded canonical runner metadata artifact fields.
- `docs/architecture/agent-orchestration/adr/adr-oa04.2-runner-contract.md`: Added maintained-runtime clarification addendum.
- `tests/agent_orchestration/test_runner_adapters.py`: Added adapter contract coverage for normalization, unsupported policy handling, and delegating service routing.
- `tests/agent_orchestration/test_oa07_execution_validation_kernel.py`: Added kernel coverage for canonical runner transcript/final-response persistence.

### Validation Performed
- `poetry run pytest tests/agent_orchestration/test_runner_adapters.py tests/agent_orchestration/test_oa07_execution_validation_kernel.py -q`
- `poetry run ruff check src/tnh_scholar/agent_orchestration/runners src/tnh_scholar/agent_orchestration/kernel/service.py tests/agent_orchestration/test_runner_adapters.py tests/agent_orchestration/test_oa07_execution_validation_kernel.py`
- `poetry run mypy src/tnh_scholar/agent_orchestration/runners src/tnh_scholar/agent_orchestration/kernel/service.py tests/agent_orchestration/test_runner_adapters.py tests/agent_orchestration/test_oa07_execution_validation_kernel.py`

### Next Steps
- [x] Run `make pr-check` for the PR-5 slice.
- [x] Run `make ci-check`; remaining failures were unrelated repo-wide lint/type debt outside the PR-5 slice.
- [x] Commit `feat/oa04.2-runner-adapters` with changelog/TODO/AGENTLOG updates.
- [x] Push the branch and open PR [#43](https://github.com/aaronksolomon/tnh-scholar/pull/43).
- [x] Merge PR #43 to `main`.

### Open Questions
- None in the maintained PR-5 slice after the adapter-boundary, policy-enforcement, and kernel-artifact cleanup passes.

### References
- [docs/architecture/agent-orchestration/adr/adr-oa04.2-runner-contract.md](docs/architecture/agent-orchestration/adr/adr-oa04.2-runner-contract.md)
- [docs/architecture/agent-orchestration/adr/adr-oa03.1-claude-code-runner.md](docs/architecture/agent-orchestration/adr/adr-oa03.1-claude-code-runner.md)
- [docs/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-runner.md](docs/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-runner.md)
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

## [2026-04-10 21:08 PDT] OA07.1 Maintained Headless Bootstrap Entry Merge Follow-Through

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: oa07.1 bootstrap merge wrap-up / next-slice planning
**Human Collaborator**: phapman

### Context
PR #46 (`feat/oa07-bootstrap-headless-entry`) was merged to `main`, completing the maintained headless bootstrap entry slice. Follow-on work then cleaned local branch state, restored and published the agent-orchestration orientation notes on `main`, and clarified the roadmap position after PR-8: the next blocker is not more runtime substrate or PR automation, but proving one useful repo-native task through the maintained path.

### Key Decisions
- **Treat PR-8 as operational substrate, not final bootstrap proof**: the maintained headless path now exists, but bootstrap should only be considered reached after one useful repository task runs through it end to end.
- **Keep rollback minimal and last-resort**: the expected normal path is validate, correct, and revalidate; `ROLLBACK(pre_run)` remains a fallback reset rather than a routine loop mechanism.
- **Do not promote this to a new strategy ADR yet**: record the correction-first / rollback-last posture in the direction memo instead of adding an OA01.x follow-on and creating design bloat.
- **Move the next slice ahead of PR-9 review automation**: a bootstrap-proof workflow is more important than commit/push/PR automation until the maintained loop demonstrates useful work.

### Work Completed
- [x] Confirmed PR #46 merged to `origin/main` and reconciled local branch cleanup around the recovered non-force push path used during review-fix follow-up (branches involved: `feat/oa07-bootstrap-headless-entry`, `backup/oa07-bootstrap-amended`)
- [x] Restored the parked design memo into agent-orchestration notes, normalized it with front matter, shortened the filename, and promoted it from draft framing to current directional guidance (file: `docs/architecture/agent-orchestration/notes/bootstrap-direction-design-memo.md`)
- [x] Added a new architecture blueprint note that summarizes maintained subsystems, current flow of control, and maintained-versus-reference package boundaries for new designers/engineers (file: `docs/architecture/agent-orchestration/notes/architecture-blueprint.md`)
- [x] Updated the direction memo with an explicit correction-first / rollback-last section to guide future OA07 design work (file: `docs/architecture/agent-orchestration/notes/bootstrap-direction-design-memo.md`)
- [x] Updated the agent-orchestration notes index to include the new design-orientation notes (file: `docs/architecture/agent-orchestration/notes/index.md`)
- [x] Committed and pushed the note set directly on `main` as `fbae2824` (`docs(agent-orch): add design orientation notes`)
- [x] Updated `TODO.md` so OA07.1 now reflects PR-7 and PR-8 merged on `main`, with a bootstrap-proof repo-task workflow slice explicitly ahead of optional PR-9 review automation (file: `TODO.md`)
- [x] Appended this continuity record as required after the merged substantive PR (file: `AGENTLOG.md`)

### Discoveries & Insights
- **The maintained bootstrap path is real but intentionally narrow**: `tnh-conductor` now exercises the maintained worktree-backed kernel end to end, but the entry path still fails closed on maintained `EVALUATE` and `GATE`.
- **The real next question is usefulness, not more substrate**: the system has enough maintained boundary work to attempt a genuine repo-native task, and that test should happen before more review automation or rollback elaboration.
- **Rollback already has the right shape for bootstrap**: `ROLLBACK(pre_run)` is a whole-run worktree reset and should stay minimal unless empirical use proves otherwise.
- **Direction notes materially help continuity now**: the architecture blueprint plus direction memo reduce re-orientation cost for both agents and humans entering OA07 follow-on design work.

### Files Modified/Created
- `docs/architecture/agent-orchestration/notes/bootstrap-direction-design-memo.md`: Published directional memo and added correction-first / rollback-last guidance.
- `docs/architecture/agent-orchestration/notes/architecture-blueprint.md`: New high-level maintained architecture blueprint.
- `docs/architecture/agent-orchestration/notes/index.md`: Added entries for the new notes.
- `TODO.md`: Updated OA07.1 status and next-slice sequencing after PR-8 merge.
- `AGENTLOG.md`: Added this merged-PR continuity entry.

### Validation Performed
- `make pr-check`
- `git fetch --prune origin`
- local branch ancestry and merge-state checks for the recovered OA07.1 branch state

### Next Steps
- [ ] Choose one narrow repo-native task that fits the current maintained subset (`RUN_AGENT`, `RUN_VALIDATION`, `STOP`) and define it as the bootstrap-proof slice.
- [ ] Prefer a task with deterministic validation and a clearly reviewable diff over anything requiring immediate evaluator/gate expansion.
- [ ] Keep PR-9 review automation deferred unless the bootstrap-proof attempt reveals that commit/push/PR handling is the real blocking seam.

### Open Questions
- Which first repo-native task best balances usefulness, deterministic validation, and low need for semantic control: a small `tnh-gen` CLI enhancement, a contained typing/refactor task, or a docs/ops-quality task with strong local checks?

### References
- [docs/architecture/agent-orchestration/notes/bootstrap-direction-design-memo.md](docs/architecture/agent-orchestration/notes/bootstrap-direction-design-memo.md)
- [docs/architecture/agent-orchestration/notes/architecture-blueprint.md](docs/architecture/agent-orchestration/notes/architecture-blueprint.md)
- [docs/architecture/agent-orchestration/adr/adr-oa07-diff-policy-safety-rails.md](docs/architecture/agent-orchestration/adr/adr-oa07-diff-policy-safety-rails.md)
- [docs/architecture/agent-orchestration/adr/adr-oa07.1-worktree-lifecycle-and-rollback.md](docs/architecture/agent-orchestration/adr/adr-oa07.1-worktree-lifecycle-and-rollback.md)
- [CHANGELOG.md](CHANGELOG.md)
- [TODO.md](TODO.md)

## [2026-04-20 15:55 PDT] tnh-gen Robustness and GPT-5 Compatibility Merge Wrap-Up

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: tnh-gen robustness and GPT-5 follow-up
**Human Collaborator**: phapman

### Context
PRs #58, #59, and #60 were merged to `main` to harden `tnh-gen` for orchestration use. The series covered typed completion outcomes, frontmatter-safe run behavior, prompt catalog health reporting, and GPT-5 / GPT-5.4 request-response compatibility. This wrap-up records the merged state plus the remaining architectural follow-up around registry-driven OpenAI request profiles.

### Key Decisions
- **Land the compatibility fix as a narrow provider bugfix**: restore GPT-5-family and GPT-5.4 behavior in the OpenAI adapter/client now, without blocking on a broader registry capability refactor.
- **Keep the next hardening step explicit**: track registry-driven request profiles as follow-up work rather than letting adapter-local model-prefix logic silently become permanent architecture.
- **Leave partially addressed registry freshness concerns open**: current-model support is fixed, but broader registry/pricing freshness still needs separate follow-up.

### Work Completed
- [x] Merged PR #58 to add typed completion outcomes, adapter diagnostics, robust failed/incomplete run handling, and frontmatter-preserving provenance writes.
- [x] Merged PR #59 to add prompt catalog health aggregation plus `tnh-gen list` / `tnh-gen config show --catalog-health` reporting.
- [x] Merged PR #60 to add `gpt-5.4` registry support and GPT-5-family request shaping compatible with current OpenAI behavior.
- [x] Added a TODO follow-up for registry-driven OpenAI request profiles and documented the same architectural follow-up at the top of the OpenAI adapter.
- [x] Appended this merged-series continuity record as required after the substantive PR sequence.

### Discoveries & Insights
- **The tnh-gen robustness failures were a coherent series, not isolated bugs**: completion contract, catalog health, CLI ergonomics, and provider compatibility all mattered to delegated-worker viability.
- **GPT-5 compatibility is fixed but still adapter-local**: the current behavior is correct for now, but future model-family controls should come from typed registry/request-profile metadata rather than string matching in the adapter.
- **Catalog-health aggregation materially improved operator signal**: moving away from ambient warning spam made both human and agent-facing execution paths clearer.

### Files Modified/Created
- `src/tnh_scholar/gen_ai_service/`: Completion-envelope, mapper, service, and OpenAI provider hardening merged through PRs #58 and #60.
- `src/tnh_scholar/cli_tools/tnh_gen/`: Run-path and catalog-health CLI updates merged through PRs #58 and #59.
- `src/tnh_scholar/prompt_system/`: Catalog-health accumulation and reporting support merged through PR #59.
- `TODO.md`: Added the registry-driven OpenAI request-profile follow-up.
- `AGENTLOG.md`: Added this merged-series continuity entry.

### Validation Performed
- Focused pytest / ruff / readiness checks were run and passed in the PR worktrees before merge for PRs #58, #59, and #60.
- Live golden validation on `gpt-5.4` succeeded for an exact `ACK` prompt and an ADR-review prompt before PR #60 merged.

### Next Steps
- [ ] Move OpenAI model-specific request shaping into registry-driven request-profile metadata.
- [ ] Decide which resolved `tnh-gen` robustness issues can be closed now and which should stay open for remaining follow-up.
- [ ] Remove obsolete local feature branches and worktrees only after explicit approval and non-loss checks.

### Open Questions
- What typed registry shape best expresses provider/model request constraints without turning the registry into an ad hoc adapter policy blob?

### References
- [CHANGELOG.md](CHANGELOG.md)
- [TODO.md](TODO.md)
- [src/tnh_scholar/gen_ai_service/providers/openai_adapter.py](src/tnh_scholar/gen_ai_service/providers/openai_adapter.py)

## [2026-04-21 12:08 PDT] SPIKE-10 Status Watch Merge and Cleanup

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: spike-10 recovery / PR #61 merge wrap-up
**Human Collaborator**: phapman

### Context
Recovered the final SPIKE-10 state after a lost thread, compared the direct and maintained conductor implementations for `tnh-conductor status --watch`, landed the direct-arm variant through PR #61, and then cleaned the local SPIKE-10 worktrees and run artifacts. This follow-up docs pass records the bootstrap milestone and the workflow rules exercised during cleanup and PR handling.

### Key Decisions
- **Treat the maintained conductor run as the milestone proof**: even though the direct arm produced the slightly cleaner merge candidate, the important result is that the maintained worktree-backed path produced viable code for the same bounded task.
- **Attribute the small quality gap to framing, not runtime family**: both runs read `AGENTS.md` and used the same Codex CLI execution family, so the main difference is prompt and entrypoint context rather than the underlying runner.
- **Shift from experimentation to release prep**: after the bootstrap-proof merge, clean the SPIKE-10 artifacts and move toward `0.4.0` prototype-alpha packaging and documentation rather than more comparison churn first.

### Work Completed
- [x] Recovered SPIKE-10 state from commits, worktrees, and conductor run artifacts; identified the maintained conductor implementation and the direct-arm merge candidate (files: `.tnh-conductor/runs/20260420T215817Z/`, `.tnh-conductor/worktrees/20260420T215817Z/`, `tmp/spike-10/20260420T215652Z/`)
- [x] Added a short SPIKE-10 result-note follow-up capturing the shared Codex CLI execution surface and the prompt-framing explanation for the small quality gap (files: `docs/architecture/agent-orchestration/notes/experiments/spike-10-agent-coordination-comparison-result.md`)
- [x] Landed `tnh-conductor status --watch`, addressed review feedback, handled transient watch-read retry behavior, and merged PR #61 (files: `src/tnh_scholar/cli_tools/tnh_conductor/tnh_conductor.py`, `tests/cli_tools/test_tnh_conductor.py`, `CHANGELOG.md`, `TODO.md`, `project_directory_tree.txt`, `src_directory_tree.txt`)
- [x] Removed merged local SPIKE-10 branches, worktrees, and run artifacts after non-loss verification (files: `tmp/spike-10/`, `.tnh-conductor/runs/20260420T203210Z/`, `.tnh-conductor/runs/20260420T215817Z/`)
- [x] Updated workflow and release-prep docs after the merge and cleanup pass (files: `AGENTS.md`, `TODO.md`, `CHANGELOG.md`, `AGENTLOG.md`)

### Discoveries & Insights
- **Bootstrap viability is now demonstrated**: the maintained `tnh-conductor` path produced a usable bounded implementation that was good enough to inform and validate the final merged feature.
- **External delegation paths remain fragile**: native subagent and external assistant paths were confounded by fork/runtime/auth issues, which makes them useful experimental seams but poor defaults.
- **Cleanup discipline matters for orchestration work**: explicit non-loss checks before branch and worktree deletion are necessary because conductor-managed runs leave behind both git refs and durable artifact directories.

### Files Modified/Created
- `docs/architecture/agent-orchestration/notes/experiments/spike-10-agent-coordination-comparison-result.md`: Added the terse shared-runtime follow-up note.
- `src/tnh_scholar/cli_tools/tnh_conductor/tnh_conductor.py`: Added `status --watch` polling and transient read retry behavior.
- `tests/cli_tools/test_tnh_conductor.py`: Added regression coverage for watch-mode polling, terminal states, and transient read races.
- `AGENTS.md`: Clarified default PR handling and `git branch -D` rules.
- `TODO.md`: Reframed top-level status around the bootstrap milestone and `0.4.0` release prep.
- `CHANGELOG.md`: Recorded the docs and workflow clarification follow-up.
- `AGENTLOG.md`: Added this merge-wrap and cleanup entry.

### Next Steps
- [ ] Decide the exact `0.4.0` scope and release-note framing for `tnh-conductor` as a prototype-alpha bootstrap tool.
- [ ] Prune or archive any remaining non-SPIKE temporary worktrees and directories that are no longer needed for active work.
- [ ] Package the remaining cleanup work into one or more docs-only or release-prep slices before changing the version number.

### Open Questions
- Should `0.4.0` ship with `tnh-conductor` positioned only as a local prototype-alpha CLI, or should the release also include packaging and entrypoint cleanup beyond the current bootstrap proof?

### References
- [docs/architecture/agent-orchestration/notes/experiments/spike-10-agent-coordination-comparison-result.md](docs/architecture/agent-orchestration/notes/experiments/spike-10-agent-coordination-comparison-result.md)
- [CHANGELOG.md](CHANGELOG.md)
- [TODO.md](TODO.md)
- [PR #61](https://github.com/aaronksolomon/tnh-scholar/pull/61)

## [2026-05-02 21:35 PDT] TG04 Structured JSON Contract Merge And Golden-Test Reset

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: tnh-gen structured JSON contract merge wrap-up
**Human Collaborator**: phapman

### Context
PR #73 (`feat/tnh-gen-json-contract-impl`) merged to `main` and established the first maintained `tnh-gen` structured JSON contract slice, including schema resolution, runtime validation, OpenAI structured-output wiring, and JSON provenance sidecars. Local work had been split across multiple worktrees, so the follow-up task was to preserve the open golden-test scaffold while resetting onto merged `main`.

### Key Decisions
- **Resume golden testing from fresh `main` rather than rebasing old exploratory branches**: avoid rebasing dirty worktrees and instead create a clean main-based worktree that already contains the merged JSON-contract code.
- **Carry forward only the golden scaffold commit**: cherry-pick the unmerged golden pipeline scaffold onto fresh `main` so live-golden work resumes without dragging older exploratory branch state along.
- **Preserve JSON purity and provenance together**: the merged slice now treats JSON output artifacts as pure JSON and writes adjacent provenance sidecars, which is the contract future golden tests should assume.

### Work Completed
- [x] Verified PR #73 merge commit was reachable from `origin/main` and that the local implementation branch could be safely retired (files: local git history, `origin/main`)
- [x] Created fresh worktree `feat/tnh-gen-golden-main` from updated `origin/main` and cherry-picked the golden pipeline scaffold commit `3130588d` onto it as `ff0ed7cd` (files: `/Users/phapman/Desktop/Projects/tnh-scholar-golden-main`, `tests/golden/journal-pipeline/`, user-guide/docs scaffold files)
- [x] Appended the required merged-PR continuity note to `AGENTLOG.md` in the new golden-testing worktree (files: `AGENTLOG.md`)

### Discoveries & Insights
- **The merged JSON-contract slice is now the right substrate for live golden tests**: there is no reason to continue testing structured JSON behavior from the older exploratory branches.
- **The older golden-runtime branch still held unique scaffold work**: because the scaffold commit was not merged, it needed to be retained explicitly before any cleanup.
- **The original docs-only main worktree is not clean**: it contains generated doc-index modifications, so it should not be removed blindly as part of routine cleanup.

### Files Modified/Created
- `AGENTLOG.md`: Added this merged-PR and golden-reset continuity entry.

### Next Steps
- [ ] Remove the now-redundant clean implementation worktree/branch for `feat/tnh-gen-json-contract-impl`.
- [ ] Remove the old clean `feat/tnh-gen-golden-runtime` worktree/branch now that its scaffold commit is retained on `feat/tnh-gen-golden-main`.
- [ ] Resume live golden-path testing from `feat/tnh-gen-golden-main` against merged `main` code.

### Open Questions
- Whether the old docs-only worktree `docs/tg04-adr-main` should be cleaned separately after deciding how to handle its generated index drift.

### References
- [PR #73](https://github.com/aaronksolomon/tnh-scholar/pull/73)
- [docs/architecture/tnh-gen/adr/adr-tg04-structured-json-contract-and-scope.md](docs/architecture/tnh-gen/adr/adr-tg04-structured-json-contract-and-scope.md)
- [docs/architecture/tnh-gen/adr/adr-tg04.1-json-contract-runtime-validation.md](docs/architecture/tnh-gen/adr/adr-tg04.1-json-contract-runtime-validation.md)
- [docs/architecture/tnh-gen/adr/adr-tg04.2-structured-json-provenance-sidecars.md](docs/architecture/tnh-gen/adr/adr-tg04.2-structured-json-provenance-sidecars.md)

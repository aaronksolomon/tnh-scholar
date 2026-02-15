# AGENTLOG

This file captures AI agent interactions, decisions, discoveries, and work performed on the TNH Scholar project. It provides historical context for continuity across sessions and helps human collaborators understand the evolution of the codebase.

See AGENTLOG_TEMPLATE.md for structure and format.

**Archive**: Older sessions are archived in [`archive/agentlogs/`](archive/agentlogs/) with a summary index at [`archive/agentlogs/archive-index.md`](archive/agentlogs/archive-index.md).

**Ordering**: Append new records at the end (chronological order from least to most recent).

---

## [2026-02-07 22:22 PST] Agent Orchestration ADR Refresh + Codex CLI Strategy

**Agent**: Claude Opus 4.5
**Chat Reference**: agent-orchestration-resume
**Human Collaborator**: Aaron

### Context

Resumed agent orchestration work after discovering Codex CLI availability. The CLI approach unblocks the API constraints that led to OA03.2 suspension. Incorporated Mario Zechner's "CLI tools over MCP" principle into conductor strategy.

### Key Decisions

- **Conductor Strategy v2 (ADR-OA01.1)**: stdout/stderr as primary capture mechanism, PTY demoted to fallback. CLI tools preferred over MCP for orchestration.
- **Codex CLI Runner (ADR-OA03.3)**: Use `codex exec` with `--json`, `--output-last-message`, `--full-auto` flags. Matches Claude Code runner pattern from OA03.1.
- **ADR Status Updates**: Superseded OA01 with OA01.1, superseded OA03.2 with OA03.3, resumed OA02 as WIP.

### Work Completed

- [x] Created ADR-OA01.1: Conductor Strategy v2 superseding OA01 (files: `docs/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md`)
- [x] Created ADR-OA03.3: Codex CLI Runner superseding OA03.2 API approach (files: `docs/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-runner.md`)
- [x] Updated ADR statuses: OA01 → superseded, OA02 → wip, OA03/OA03.1 → accepted, OA03.2 → superseded
- [x] Archived earlier OA03.3 draft from branch for reference (files: `docs/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-spike-2026-01-29.md`)
- [x] Updated ADR roadmap in OA01 addendum

### Discoveries & Insights

- **CLI over API**: Codex CLI provides the same capabilities as the VS Code extension without the proprietary app server dependency.
- **Capture parity**: Both Claude Code and Codex CLI support stdout/stderr capture, enabling unified runner architecture.

### Files Modified/Created

- `docs/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md`: New conductor strategy with CLI-first approach
- `docs/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-runner.md`: Codex CLI runner specification
- `docs/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-spike-2026-01-29.md`: Archived earlier draft
- `docs/architecture/agent-orchestration/adr/adr-oa01-agent-orchestration-strategy.md`: Status → superseded
- `docs/architecture/agent-orchestration/adr/adr-oa02-phase-0-protocol-spike.md`: Status → wip
- `docs/architecture/agent-orchestration/adr/adr-oa03-agent-runner-architecture.md`: Status → accepted
- `docs/architecture/agent-orchestration/adr/adr-oa03.1-claude-code-runner.md`: Status → accepted
- `docs/architecture/agent-orchestration/adr/adr-oa03.2-codex-runner.md`: Status → superseded

### Next Steps

- [ ] Implement Codex CLI command builder in spike harness
- [ ] Run spike test in sandbox worktree

### Open Questions

- None.
### References

- Commit 4f05b2c: "docs(agent-orch): Resume orchestration work with Codex CLI spike"
- `/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md`
- `/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-runner.md`

---

## 2026-02-08 06:45 UTC Agent Orchestration Codex CLI Spike

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: codex-cli-spike-followthrough
**Human Collaborator**: phapman

### Context
Resumed agent orchestration work to validate a Codex CLI execution path and align the spike harness with the Claude runner pattern. Needed a verified sandbox worktree testing sequence and a recorded spike run.

### Key Decisions
- **CLI parity for spike**: Use headless CLI capture and align Codex artifacts with Claude runner patterns.
- **Sandbox-first testing**: Use sync-sandbox workflow and run from a dedicated worktree to avoid dirty workspace failures.

### Work Completed
- [x] Updated Codex CLI ADR with model pinning, MCP exclusion, and Claude parity guidance (`docs/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-runner.md`)
- [x] Implemented Codex CLI command builder, response artifact pathing, and subprocess runner (`src/tnh_scholar/agent_orchestration/spike/providers/command_builder.py`, `src/tnh_scholar/agent_orchestration/spike/providers/subprocess_agent_runner.py`, `src/tnh_scholar/agent_orchestration/spike/service.py`, `src/tnh_scholar/agent_orchestration/spike/models.py`)
- [x] Switched spike CLI to subprocess runner and added response path output (`src/tnh_scholar/cli_tools/tnh_conductor_spike/tnh_conductor_spike.py`)
- [x] Added command builder tests (`tests/agent_orchestration/test_spike_command_builder.py`)
- [x] Documented spike testing sequence in orchestration notes (`docs/architecture/agent-orchestration/notes/spike-testing-sequence.md`)
- [x] Ran Codex CLI spike in sandbox worktree and captured run artifacts (run id `20260208-063754`)
- [x] Updated spike report with Codex run details (`SPIKE_REPORT.md`)

### Discoveries & Insights
- **Poetry sandbox setup required**: Running from the sandbox requires `poetry install` so the package is importable.
- **Sync script behavior**: `scripts/sync-sandbox.sh` resets/cleans the worktree and applies a patch; uncommitted changes must be re-synced before each run.

### Files Modified/Created
- `docs/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-runner.md`: Tightened spike scope and parity constraints.
- `src/tnh_scholar/agent_orchestration/spike/models.py`: Added response_path fields.
- `src/tnh_scholar/agent_orchestration/spike/service.py`: Wired response artifact into command builder.
- `src/tnh_scholar/agent_orchestration/spike/providers/command_builder.py`: Added Codex CLI command builder.
- `src/tnh_scholar/agent_orchestration/spike/providers/subprocess_agent_runner.py`: New non-PTY runner.
- `src/tnh_scholar/cli_tools/tnh_conductor_spike/tnh_conductor_spike.py`: Use subprocess runner, print response path.
- `tests/agent_orchestration/test_spike_command_builder.py`: New unit tests.
- `docs/architecture/agent-orchestration/notes/spike-testing-sequence.md`: Created concise sandbox test steps.
- `SPIKE_REPORT.md`: Added Codex CLI run notes.

### Next Steps
- [ ] Decide whether to wire dependency reinstall into `scripts/sync-sandbox.sh` or keep manual.
- [ ] Run `pytest tests/agent_orchestration/test_spike_command_builder.py` in sandbox for verification.

### Open Questions
- Should the sandbox sync script manage Poetry install when `poetry.lock` changes?

### References
- `/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-runner.md`
- `/architecture/agent-orchestration/notes/spike-testing-sequence.md`
- `SPIKE_REPORT.md`

---

## [2026-02-09 22:47 PST] Agent Orchestration MVP Kernel Round 1 + Active-Code Dedup

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: oa04-mvp-kernel-implementation-round1
**Human Collaborator**: phapman

### Context
Implemented the first code draft of OA04/OA04.1 MVP workflow execution in a new non-spike package, then performed a follow-up dedup pass across active agent-orchestration code (excluding spike modules).

### Key Decisions
- **Object-service alignment**: New conductor MVP code follows typed models/protocols/service/providers/adapters layering.
- **Golden safety enforcement split**:
  - Weak pre-run requirement in workflow validation (presence/reachability of `GATE` when goldens may be proposed).
  - Strong runtime enforcement in kernel transitions (no success-to-stop path while golden gate is pending).
- **Dedup scope**: Reuse moved to `agent_orchestration/common` (not global `utils`) to keep shared behavior domain-local.

### Work Completed
- [x] Added `conductor_mvp` package with typed workflow/opcode models, kernel service, protocols, providers, and workflow loader adapter.
- [x] Implemented static workflow validation constraints:
  - unique/valid step graph
  - evaluate route/allowed-next-step constraints
  - reachability checks
  - weak generative-golden gate requirement.
- [x] Implemented deterministic kernel opcode execution for:
  - `RUN_AGENT`
  - `RUN_VALIDATION`
  - `EVALUATE`
  - `GATE`
  - `ROLLBACK`
  - `STOP`
- [x] Implemented runtime golden gate enforcement (pending golden proposals must pass approved gate before success stop).
- [x] Added local validation runner support for builtin and script validators with harness report parsing/artifact capture hooks.
- [x] Added targeted tests for MVP kernel behavior (`tests/agent_orchestration/test_conductor_mvp_kernel.py`).
- [x] Performed active-code dedup for clock/run-id logic between `codex_harness` and `conductor_mvp` via new shared `agent_orchestration/common` helpers.

### Discoveries & Insights
- Mypy in this repo reports imported modules in new packages as `Any` until broader package/type-check coverage is in place; provider wrappers were kept explicit and validated in focused checks.
- Duplicate low-level providers existed only in active `codex_harness` + `conductor_mvp`; spike duplicates were intentionally left unchanged.

### Files Modified/Created
- `src/tnh_scholar/agent_orchestration/conductor_mvp/__init__.py`: New MVP package exports.
- `src/tnh_scholar/agent_orchestration/conductor_mvp/models.py`: Typed workflow, route, step, and result models.
- `src/tnh_scholar/agent_orchestration/conductor_mvp/protocols.py`: Kernel collaborator protocols.
- `src/tnh_scholar/agent_orchestration/conductor_mvp/service.py`: Workflow validator + deterministic kernel executor.
- `src/tnh_scholar/agent_orchestration/conductor_mvp/adapters/workflow_loader.py`: YAML-to-typed workflow loader.
- `src/tnh_scholar/agent_orchestration/conductor_mvp/providers/artifact_store.py`: Run artifact storage provider.
- `src/tnh_scholar/agent_orchestration/conductor_mvp/providers/validation_runner.py`: Local validator runner.
- `src/tnh_scholar/agent_orchestration/conductor_mvp/providers/clock.py`: Uses shared time helper.
- `src/tnh_scholar/agent_orchestration/conductor_mvp/providers/run_id.py`: Uses shared run-id helper.
- `tests/agent_orchestration/test_conductor_mvp_kernel.py`: New kernel tests.
- `src/tnh_scholar/agent_orchestration/common/__init__.py`: Shared helper exports.
- `src/tnh_scholar/agent_orchestration/common/time.py`: Shared local/UTC time helpers.
- `src/tnh_scholar/agent_orchestration/common/run_id.py`: Shared run-id formatter helper.
- `src/tnh_scholar/agent_orchestration/codex_harness/providers/clock.py`: Rewired to shared time helper.
- `src/tnh_scholar/agent_orchestration/codex_harness/providers/run_id.py`: Rewired to shared run-id helper.

### Validation Performed
- `poetry run ruff check src/tnh_scholar/agent_orchestration/conductor_mvp tests/agent_orchestration/test_conductor_mvp_kernel.py`
- `poetry run pytest tests/agent_orchestration/test_conductor_mvp_kernel.py -q`
- `poetry run mypy src/tnh_scholar/agent_orchestration/conductor_mvp tests/agent_orchestration/test_conductor_mvp_kernel.py`
- `poetry run ruff check src/tnh_scholar/agent_orchestration/common src/tnh_scholar/agent_orchestration/codex_harness/providers/clock.py src/tnh_scholar/agent_orchestration/codex_harness/providers/run_id.py src/tnh_scholar/agent_orchestration/conductor_mvp/providers/clock.py src/tnh_scholar/agent_orchestration/conductor_mvp/providers/run_id.py`
- `poetry run mypy src/tnh_scholar/agent_orchestration/common src/tnh_scholar/agent_orchestration/codex_harness/providers/clock.py src/tnh_scholar/agent_orchestration/codex_harness/providers/run_id.py src/tnh_scholar/agent_orchestration/conductor_mvp/providers/clock.py src/tnh_scholar/agent_orchestration/conductor_mvp/providers/run_id.py`
- `poetry run pytest tests/agent_orchestration/test_codex_harness_tools.py tests/agent_orchestration/test_conductor_mvp_kernel.py -q`

### Next Steps
- [ ] Begin OA04.1 MVP sequence step for concrete workflow definitions and kernel wiring into CLI surface.
- [ ] Add tests for workflow loader edge cases and planner/gate routing invariants.

### Open Questions
- None in this implementation round.

---

## [2026-02-14 20:04 PST] PT05 Prompt Platform Round 1 Implementation + Hardening

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: pt05-e2e-implementation-round1
**Human Collaborator**: phapman

### Context
Implemented PT05 prompt platform strategy end-to-end in the active prompt system codebase, with compatibility support for legacy metadata, namespace-first keying, deterministic validation rules, and expanded test coverage. Follow-up hardening focused on reviewer feedback for object-service clarity and safety.

### Key Decisions
- **Compatibility-first envelope adoption**: Keep legacy frontmatter loading paths operational while normalizing to PT05 envelope semantics (`prompt_id`, `role`, `output_contract`, namespaced keys).
- **Uniform validator enforcement**: Enforce platform-level output mode and strict-input rules in `PromptValidator`, independent of client semantics.
- **Catalog resilience**: Filesystem and git catalogs both use fallback metadata/warnings for invalid prompt artifacts (instead of failing hard at load time).
- **Legacy mode containment**: Legacy `output_mode: structured` is accepted only as input and normalized to `json`; new model field typing is enum-based.
- **Validation result invariants**: Keep `valid` for API ergonomics but derive it from `errors` as single source of truth.

### Work Completed
- [x] Added PT05-oriented prompt domain models and compatibility normalizers (`PromptOutputMode`, `PromptInputSpec`, `PromptOutputContract`, key/role/output sync behavior).
- [x] Implemented immutable key reference support (`<canonical_key>.v<version>`) and namespace-aware path/key mapping in prompt mapper.
- [x] Updated filesystem and git catalog adapters to:
  - use namespace keys and immutable refs
  - validate on load with warning-based fallback paths
  - emit typed fallback metadata for invalid prompt artifacts.
- [x] Implemented validator rules for:
  - required envelope fields
  - numeric versions
  - strict input declarations
  - `json` mode requiring `schema_ref`
  - `artifacts` mode requiring artifact declarations.
- [x] Refactored `PromptMetadata` sync logic into focused collaborators:
  - `_sync_key_fields()`
  - `_sync_role_fields()`
  - `_sync_output_fields()`.
- [x] Narrowed broad exception catches in catalog adapters to `(ValueError, pydantic.ValidationError)`.
- [x] Updated `PromptValidationResult` to enforce `valid == (len(errors) == 0)` via model validator.
- [x] Expanded and added tests across prompt system and dependent CLI/gen-ai flows, including new mapper-focused coverage.

### Discoveries & Insights
- Using path-relative canonical keys in adapters/mappers removed stem-collision risk and aligned catalog behavior with PT05 namespace goals.
- Warning-based fallback behavior in both catalog adapters preserves usability during migration while still surfacing schema issues to callers.
- Prompt system coverage is now strong on core PT05 logic, while transport/protocol modules remain lightly covered and can be expanded separately.

### Files Modified/Created
- `src/tnh_scholar/prompt_system/domain/models.py`: PT05 envelope/output/input models, compatibility sync helpers, validation-result invariant.
- `src/tnh_scholar/prompt_system/mappers/prompt_mapper.py`: Immutable ref parsing, namespace key mapping, metadata normalization.
- `src/tnh_scholar/prompt_system/service/validator.py`: PT05 structural/contract enforcement.
- `src/tnh_scholar/prompt_system/adapters/filesystem_catalog_adapter.py`: Typed fallback metadata, narrowed exception handling, module-level Frontmatter import.
- `src/tnh_scholar/prompt_system/adapters/git_catalog_adapter.py`: Filesystem-parity fallback behavior + narrowed exception handling.
- `tests/prompt_system/test_mapper.py`: New mapper test suite.
- `tests/prompt_system/test_models.py`: Expanded model compatibility/invariant coverage.
- `tests/prompt_system/test_validator.py`: Expanded PT05 validator rule coverage.
- `tests/prompt_system/test_catalog_adapters.py`: Expanded filesystem fallback coverage.
- `tests/prompt_system/test_git_catalog.py`: Expanded git adapter behavior coverage.
- `tests/cli_tools/test_tnh_gen.py`: Updated warning assertion for envelope-era message semantics.

### Validation Performed
- `poetry run ruff check` on all changed prompt-system and test files.
- `poetry run mypy` on changed prompt-system source modules.
- `poetry run pytest tests/prompt_system -q`
- `poetry run pytest tests/prompt_system --cov=tnh_scholar.prompt_system --cov-report=term-missing -q`
- `poetry run pytest tests/cli_tools/test_tnh_gen.py tests/cli_tools/test_tnh_gen_coverage.py -q`
- `poetry run pytest tests/gen_ai_service/test_policy_routing_safety.py tests/configuration/test_prompt_discovery.py -q`

### Next Steps
- [ ] Add PT05 follow-on implementation tasks for prompt namespace governance and schema reference resolution tooling.
- [ ] Start OA05/OA06 integration pass against the new PT05 prompt contract surfaces.

### Open Questions
- None blocking this round.

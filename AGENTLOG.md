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

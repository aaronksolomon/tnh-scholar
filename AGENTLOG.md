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

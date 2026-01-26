# AGENTLOG

This file captures AI agent interactions, decisions, discoveries, and work performed on the TNH Scholar project. It provides historical context for continuity across sessions and helps human collaborators understand the evolution of the codebase.

See AGENTLOG_TEMPLATE.md for structure and format.

**Archive**: Older sessions are archived in [`archive/agentlogs/`](archive/agentlogs/) with a summary index at [`archive/agentlogs/archive-index.md`](archive/agentlogs/archive-index.md).

**Ordering**: Append new records at the end (chronological order from least to most recent).

---
## [2026-01-20 06:40 UTC] Phase 0 Spike Implementation + Safeguards

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: agent-orchestration spike round
**Human Collaborator**: Aaron

### Context
Implement Phase 0 protocol spike per ADR-OA02, add safety gates, and validate with a smoke run. Follow-up fixes for command filters, event emission, and sandbox isolation.

### Key Decisions
- **Sandbox Root Guard**: Enforce `<repo>-sandbox` (override via `SPIKE_SANDBOX_ROOT`) and fail fast when outside sandbox.
- **Command Filter Regex**: Block destructive commands via regex on confirmation prompts; Codex CLI remains unimplemented.
- **Heartbeat + Output Events**: Emit `HEARTBEAT` and `AGENT_OUTPUT` to meet Phase 0 event requirements.

### Work Completed
- [x] Implemented spike service, protocols, PTY runner, git capture, and CLI entrypoint (files: `src/tnh_scholar/agent_orchestration/spike/service.py`, `src/tnh_scholar/agent_orchestration/spike/providers/pty_agent_runner.py`, `src/tnh_scholar/cli_tools/tnh_conductor_spike/tnh_conductor_spike.py`)
- [x] Added safety policy defaults and command filter (files: `src/tnh_scholar/agent_orchestration/spike/policy.py`, `src/tnh_scholar/agent_orchestration/spike/adapters/command_filter.py`)
- [x] Added heartbeat/output emission and preflight guards for clean worktree + sandbox root (files: `src/tnh_scholar/agent_orchestration/spike/service.py`, `src/tnh_scholar/agent_orchestration/spike/models.py`, `src/tnh_scholar/agent_orchestration/spike/providers/git_workspace.py`)
- [x] Added tests for command filter and preflight guards (files: `tests/agent_orchestration/test_spike_command_filter.py`)
- [x] Documented spike findings and sandbox strategy (files: `SPIKE_REPORT.md`, `docs/architecture/agent-orchestration/adr/adr-oa02-phase-0-protocol-spike.md`)
- [x] Added sandbox sync automation and Makefile target (files: `scripts/sync-sandbox.sh`, `Makefile`, `SPIKE_REPORT.md`)
- [x] Extended sandbox sync to auto-detect the active dev branch (files: `scripts/sync-sandbox.sh`, `Makefile`, `SPIKE_REPORT.md`)
- [x] Added patch-based sandbox sync option for uncommitted changes (files: `scripts/sync-sandbox.sh`, `Makefile`, `SPIKE_REPORT.md`)
- [x] Updated preflight tests for sandbox-only dirty allowance (files: `tests/agent_orchestration/test_spike_command_filter.py`)
- [x] Set sandbox sync defaults to patch + force for fast spike testing (files: `Makefile`, `SPIKE_REPORT.md`)
- [x] Simplified sandbox sync to a single patch-based flow (files: `scripts/sync-sandbox.sh`, `Makefile`, `SPIKE_REPORT.md`)

### Discoveries & Insights
- **Worktree Isolation Needed**: Spike branches can collide with active dev branches unless run in a dedicated worktree.
- **Worktree Environments Are Clean**: New worktrees require separate Poetry environment setup.

### Files Modified/Created
- `src/tnh_scholar/agent_orchestration/spike/models.py`: Added settings, policies, and preflight error.
- `src/tnh_scholar/agent_orchestration/spike/service.py`: Orchestration, events, preflight guards.
- `src/tnh_scholar/agent_orchestration/spike/providers/pty_agent_runner.py`: PTY capture with heartbeat/output callbacks.
- `src/tnh_scholar/agent_orchestration/spike/providers/git_workspace.py`: Repo root capture for sandbox guard.
- `src/tnh_scholar/agent_orchestration/spike/policy.py`: Regex blocklist defaults.
- `src/tnh_scholar/agent_orchestration/spike/providers/command_builder.py`: Codex not implemented guard.
- `src/tnh_scholar/cli_tools/tnh_conductor_spike/tnh_conductor_spike.py`: CLI wiring + preflight handling.
- `tests/agent_orchestration/test_spike_command_filter.py`: Added command filter + preflight tests.
- `SPIKE_REPORT.md`: Findings and sandbox strategy updates.
- `docs/architecture/agent-orchestration/adr/adr-oa02-phase-0-protocol-spike.md`: Addendum for sandbox preflight.
- `scripts/sync-sandbox.sh`: New sync script for sandbox resets and dependency refresh.
- `Makefile`: Added `sync-sandbox` target with `SANDBOX_PATH` and `SANDBOX_BRANCH`.
- `scripts/sync-sandbox.sh`: Added auto-branch detection from source repo.
- `Makefile`: Added `SANDBOX_SOURCE_REPO` and auto-branch toggle.
- `scripts/sync-sandbox.sh`: Added apply-patch mode for uncommitted work.
- `Makefile`: Added `SANDBOX_APPLY_PATCH` toggle.
- `tests/agent_orchestration/test_spike_command_filter.py`: Updated preflight tests for sandbox-only dirty allowance.
- `Makefile`: Defaulted sandbox sync to patch + force.
- `SPIKE_REPORT.md`: Documented default sandbox sync behavior.
- `scripts/sync-sandbox.sh`: Simplified to always reset + apply patch from source repo.
- `Makefile`: Removed sandbox sync flags in favor of a single flow.

### Next Steps
- [ ] Re-run spike in `tnh-scholar-sandbox` after Poetry env setup.

### Open Questions
- None.

### References
- `/architecture/agent-orchestration/adr/adr-oa02-phase-0-protocol-spike.md`
- `SPIKE_REPORT.md`

---
## [2026-01-23 23:45 UTC] Codex Harness Standup + Sandbox Sync Iteration

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: codex harness spike follow-up
**Human Collaborator**: Aaron

### Context
Stand up a minimal Codex harness inside agent_orchestration to test end-to-end tool-calling and code edits. Stabilize sandbox sync, add CLI entry, and capture learnings from initial runs.

### Key Decisions
- **Responses API + JSON-only prompt**: Use Responses API with a JSON-only system prompt and tool calls, no `response_format` until schema support confirmed.
- **Minimal toolset**: Provide `read_file`, `list_files`, `search_repo`, `apply_patch`, `run_tests` with strict schemas and error-returning tool outputs.
- **Sandbox sync flow**: Patch-based sync from source repo; skip branch checkout conflicts and allow empty patches; require `.env` copy into sandbox.

### Work Completed
- [x] Built Codex harness modules (models, protocols, service, providers, adapters) under `src/tnh_scholar/agent_orchestration/codex_harness/`
- [x] Added Codex harness CLI entrypoint (`src/tnh_scholar/cli_tools/tnh_codex_harness/tnh_codex_harness.py`) and `tnh-codex-harness` console script in `pyproject.toml`
- [x] Implemented tool schemas/execution and artifact capture (files: `src/tnh_scholar/agent_orchestration/codex_harness/tools.py`, `src/tnh_scholar/agent_orchestration/codex_harness/providers/tool_executor.py`, `src/tnh_scholar/agent_orchestration/codex_harness/providers/artifact_writer.py`)
- [x] Added initial tool tests (files: `tests/agent_orchestration/test_codex_harness_tools.py`)
- [x] Simplified sandbox sync script to avoid branch checkout conflicts + empty patch failures (files: `scripts/sync-sandbox.sh`, `Makefile`)
- [x] Added OpenAI SDK bump note and adapter TODO (files: `TODO.md`, `src/tnh_scholar/gen_ai_service/providers/openai_adapter.py`)

### Discoveries & Insights
- **Responses API quirks**: `response_format` is unsupported and `temperature` is rejected; JSON-only output needs schema enforcement via `text` config.
- **Tool loop stalls**: Model often returns tool calls without final text output, causing parse failure and blocked runs.
- **Sandbox hygiene**: Sync resets remove `.env`; sandbox runs require re-copying credentials.

### Files Modified/Created
- `src/tnh_scholar/agent_orchestration/codex_harness/__init__.py`: New package init.
- `src/tnh_scholar/agent_orchestration/codex_harness/models.py`: Pydantic models for requests, runs, and artifacts.
- `src/tnh_scholar/agent_orchestration/codex_harness/protocols.py`: Protocols for client/tooling/writer.
- `src/tnh_scholar/agent_orchestration/codex_harness/service.py`: Orchestrator for run lifecycle + tool loop.
- `src/tnh_scholar/agent_orchestration/codex_harness/tools.py`: Tool schemas + JSON schema config.
- `src/tnh_scholar/agent_orchestration/codex_harness/providers/openai_responses_client.py`: Responses API client + tool round handling.
- `src/tnh_scholar/agent_orchestration/codex_harness/providers/tool_executor.py`: Tool execution + safe error outputs.
- `src/tnh_scholar/agent_orchestration/codex_harness/providers/artifact_writer.py`: Artifact persistence + JSON serialization.
- `src/tnh_scholar/agent_orchestration/codex_harness/providers/patch_applier.py`: Patch apply helper.
- `src/tnh_scholar/agent_orchestration/codex_harness/providers/searcher.py`: Repo search via `rg -F`.
- `src/tnh_scholar/agent_orchestration/codex_harness/providers/tool_registry.py`: Tool registration.
- `src/tnh_scholar/agent_orchestration/codex_harness/providers/workspace_locator.py`: Repo root detection.
- `src/tnh_scholar/cli_tools/tnh_codex_harness/tnh_codex_harness.py`: CLI wiring.
- `pyproject.toml`: Added `tnh-codex-harness` console script.
- `tests/agent_orchestration/test_codex_harness_tools.py`: Tool unit tests.
- `scripts/sync-sandbox.sh`: Skip branch checkout; allow empty patch; avoid recursive deletion issues.
- `Makefile`: Updated `sync-sandbox` target defaults.
- `TODO.md`: Added OpenAI SDK validation task.
- `src/tnh_scholar/gen_ai_service/providers/openai_adapter.py`: SDK version note + TODO.
- `docs/architecture/agent-orchestration/notes/codex-harness-e2e-report.md`: Added end-to-end test report for other agents.

### Next Steps
- [ ] Add JSON schema enforcement using Responses `text` config and validate structured output.
- [ ] Capture tool results in artifacts for debugging tool-loop stalls.
- [ ] Verify OpenAI SDK 2.15.0 compatibility for existing adapter paths.

### Open Questions
- Should we hard-fail runs without final structured JSON, or allow partial output?
- Which minimal toolset is required for a reliable MVP coding task?

### References
- `/architecture/agent-orchestration/adr/adr-oa03-agent-runner-architecture.md`
- `/architecture/agent-orchestration/adr/adr-oa03.1-claude-code-runner.md`
- `/architecture/agent-orchestration/notes/codex-harness-e2e-report.md`

---
## [2026-01-25 ~19:00 UTC] Codex Harness Spike Evaluation + Suspension

**Agent**: Claude Opus 4.5
**Chat Reference**: codex harness evaluation session
**Human Collaborator**: Aaron

### Context
Evaluate Codex harness test runs, analyze API behavior constraints, and make go/no-go recommendation for continued development.

### Key Decisions
- **Suspend Codex harness development**: Core ADR assumption (model produces structured output after tool calls) is invalid. API behavior doesn't support the design.
- **Preserve work for future resumption**: All code, tests, and documentation retained. Can resume if API constraints change.
- **Prioritize Claude Code runner**: OA03.1 has tractable capture model (CLI stdout). Should be the near-term focus.

### Work Completed
- [x] Reviewed 15+ test runs in sandbox `.tnh-codex/runs/` directory
- [x] Analyzed API response patterns — confirmed model stops after tool calls without text output
- [x] Identified VS Code extension architecture difference (client-side orchestration vs model summary)
- [x] Wrote comprehensive spike findings report (`docs/architecture/agent-orchestration/notes/codex-harness-spike-findings.md`)
- [x] Added suspension addendum to ADR-OA03.2 with findings and conditions for resumption
- [x] Updated AGENTLOG with session record

### Discoveries & Insights
- **VS Code Codex is an orchestrator**: It tracks tool calls client-side and synthesizes summaries. The model doesn't self-summarize.
- **Responses API limitations**: No `response_format`, temperature rejected, no `tool_choice: none` to force text output.
- **Tool calls ARE the output**: From the model's perspective, calling `apply_patch` completes the task. No post-tool JSON summary.
- **Cost without feedback**: Without VS Code's interactive loop, API costs accumulate without proportional productivity gain.

### Files Modified/Created
- `docs/architecture/agent-orchestration/notes/codex-harness-spike-findings.md`: Comprehensive spike findings document
- `docs/architecture/agent-orchestration/adr/adr-oa03.2-codex-runner.md`: Added suspension addendum
- `AGENTLOG.md`: This session record

### Next Steps
- [ ] Update CHANGELOG and TODO to reflect suspension
- [ ] Commit all work on feat/agent-orchestration branch
- [ ] Consider Claude Code runner (OA03.1) as next implementation priority when resuming agent orchestration work

### Open Questions
- When/if to revisit: depends on OpenAI API improvements or business need for client-side orchestration
- Should Chat Completions API be tested as alternative to Responses API?

### References
- `/architecture/agent-orchestration/adr/adr-oa03.2-codex-runner.md` (updated with suspension addendum)
- `/architecture/agent-orchestration/notes/codex-harness-spike-findings.md` (new)
- `/architecture/agent-orchestration/notes/codex-harness-e2e-report.md`

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

---

## [2026-01-26 15:50 UTC] Chat Completions Probe + Sandbox Cleanup

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: codex harness chat-completions probe
**Human Collaborator**: Aaron

### Context

Test an alternate Chat Completions pathway for the Codex harness and confirm compatibility. Sync changes to sandbox, run a minimal test, and then remove the sandbox worktree when pausing agent-orchestration work.

### Key Decisions

- **Chat Completions client**: Added a separate client implementing `ResponsesClientProtocol` with JSON schema response_format for compatibility testing.
- **CLI toggle**: Added `--use-chat-completions` to switch clients without changing service wiring.
- **Sandbox decommission**: Removed the sandbox worktree to avoid uncommitted state and accidental commits during pause.

### Work Completed

- [x] Added Chat Completions client with tool loop (files: `src/tnh_scholar/agent_orchestration/codex_harness/providers/chat_completions_client.py`)
- [x] Added CLI flag to select chat completions (files: `src/tnh_scholar/cli_tools/tnh_codex_harness/tnh_codex_harness.py`)
- [x] Synced changes to sandbox and attempted run using chat completions (sandbox path: `/Users/phapman/Desktop/Projects/tnh-scholar-sandbox`)
- [x] Removed the sandbox worktree after confirmation (`git worktree remove --force`)

### Discoveries & Insights

- **Model compatibility**: `gpt-5.2-codex` is not a chat model; Chat Completions endpoint returns 404.
- **Sandbox permissions**: Worktree removal required escalation due to file permissions.

### Files Modified/Created

- `src/tnh_scholar/agent_orchestration/codex_harness/providers/chat_completions_client.py`: Created Chat Completions client.
- `src/tnh_scholar/cli_tools/tnh_codex_harness/tnh_codex_harness.py`: Added `--use-chat-completions` flag and client selection.

### Next Steps

- [ ] If revisiting Chat Completions path, use a chat-capable model override.
- [ ] Recreate sandbox worktree when resuming agent-orchestration testing.

### Open Questions

- Which chat-capable model should be the default for chat-completions experiments?

### References

- `/architecture/agent-orchestration/notes/codex-harness-e2e-report.md`

---

## [2026-01-26 ~19:30 UTC] Spike Findings Finalization + Commit

**Agent**: Claude Opus 4.5
**Chat Reference**: codex harness evaluation continuation
**Human Collaborator**: Aaron

### Context

Finalize spike findings based on Chat Completions test results and VS Code output channel analysis. Commit all agent orchestration work to branch.

### Work Completed

- [x] Analyzed Chat Completions test failure — GPT-Codex models are Responses API only
- [x] Updated Option D in spike findings as TESTED (failed)
- [x] Added Finding 4: VS Code Extension uses external app server (from output channel logs)
- [x] Updated CHANGELOG with agent orchestration work summary
- [x] Updated TODO with suspended Codex runner task
- [x] Committed all work to feat/agent-orchestration branch (commit: 1a0e759)

### Discoveries & Insights

- **GPT-Codex is Responses-only**: Chat Completions API returns 404 for gpt-5.2-codex — eliminates Option D
- **VS Code uses proprietary app server**: Output channel shows `codex/event/*` notifications from external orchestrator, not direct API calls
- **Public API provides raw capabilities only**: The orchestrated VS Code experience is not replicable via public API

### Files Modified

- `docs/architecture/agent-orchestration/notes/codex-harness-spike-findings.md`: Added Finding 4, updated Option D
- `CHANGELOG.md`: Added agent orchestration summary to Unreleased
- `TODO.md`: Added suspended Codex runner task, updated status

### References

- Commit 1a0e759: "feat: Add Codex harness with suspension findings"

---

## [2026-02-07 14:49 PST] yt-dlp Runtime Hardening + Ops Checks

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: yt-dlp reliability + tnh-setup hardening
**Human Collaborator**: Aaron

### Context

Stabilize yt-dlp usage across CLI tools with runtime setup, preflight checks, and regular ops testing. Improve tnh-setup UX to guide users through runtime readiness and document the operational strategy.

### Key Decisions

- **Python runtime setup**: Replace shell script with a Python setup script for yt-dlp runtime to improve error handling and testability.
- **Ops checks via cron**: Provide a cron-ready Python ops check + URL list, avoiding monthly GitHub noise.
- **Service-layer testing**: Keep CLI tests as smoke and focus robustness on service and environment layers.

### Work Completed

- [x] Added yt-dlp runtime setup + verification script with clear diagnostics (files: `scripts/setup_ytdlp_runtime.py`)
- [x] Hardened tnh-setup Typer UI and runtime workflow (files: `src/tnh_scholar/cli_tools/tnh_setup/tnh_setup_typer.py`, `src/tnh_scholar/cli_tools/tnh_setup/ui.py`)
- [x] Implemented yt-dlp environment inspection + ops check services (files: `src/tnh_scholar/video_processing/yt_environment.py`, `src/tnh_scholar/video_processing/ops_check.py`)
- [x] Injected runtime options in yt-dlp downloader for JS runtime and remote components (files: `src/tnh_scholar/video_processing/video_processing.py`)
- [x] Added ops check runner + validation URL list (files: `scripts/yt_dlp_ops_check.py`, `tests/fixtures/yt_dlp/validation_urls.txt`)
- [x] Added tests for runtime setup, env inspection, ops checks, and runtime options (files: `tests/scripts/test_setup_ytdlp_runtime_py.py`, `tests/video_processing/test_ops_check.py`, `tests/video_processing/test_yt_environment.py`, `tests/video_processing/test_video_processing_runtime_options.py`, `tests/video_processing/test_yt_environment_remote_components.py`, `tests/cli_tools/test_yt_dlp_live.py`)
- [x] Updated docs and ADRs for runtime hardening and ops strategy (files: `docs/architecture/video-processing/adr/adr-vp02-ytdlp-operational-strategy.md`, `docs/architecture/setup-tnh/adr/adr-st01-tnh-setup-runtime-hardening.md`, `docs/development/yt-dlp-ops-check.md`, `docs/cli-reference/tnh-setup.md`, `docs/cli-reference/ytt-fetch.md`)
- [x] Updated Makefile targets for runtime setup (files: `Makefile`, `pyproject.toml`, `poetry.lock`)

### Discoveries & Insights

- **Pipx env detection matters**: yt-dlp runtime checks must account for pipx-installed `curl_cffi` to avoid false warnings.
- **Remote components are required**: yt-dlp JS challenge solver must be enabled (`remote_components`) to avoid missing formats.

### Files Modified/Created

- `scripts/setup_ytdlp_runtime.py`: New Python runtime setup with diagnostics and install flow.
- `scripts/yt_dlp_ops_check.py`: Cron-friendly ops check runner.
- `src/tnh_scholar/cli_tools/tnh_setup/tnh_setup_typer.py`: UI flow updates + runtime integration.
- `src/tnh_scholar/cli_tools/tnh_setup/ui.py`: Rich UI helper for consistent setup output.
- `src/tnh_scholar/video_processing/yt_environment.py`: Runtime inspection for JS runtime, curl_cffi, remote components.
- `src/tnh_scholar/video_processing/ops_check.py`: Ops check domain service.
- `src/tnh_scholar/video_processing/video_processing.py`: Runtime options injection for yt-dlp.
- `tests/scripts/test_setup_ytdlp_runtime_py.py`: Unit tests for runtime setup script.
- `tests/video_processing/test_ops_check.py`: Ops check unit tests.
- `tests/video_processing/test_yt_environment.py`: Runtime inspection tests.
- `tests/video_processing/test_video_processing_runtime_options.py`: yt-dlp options tests.
- `tests/video_processing/test_yt_environment_remote_components.py`: Remote components tests.
- `tests/cli_tools/test_yt_dlp_live.py`: Live smoke tests for yt-dlp (opt-in).
- `tests/fixtures/yt_dlp/validation_urls.txt`: Live validation URL list.
- `docs/architecture/video-processing/adr/adr-vp02-ytdlp-operational-strategy.md`: Operational strategy ADR.
- `docs/architecture/setup-tnh/adr/adr-st01-tnh-setup-runtime-hardening.md`: Runtime hardening ADR updates.
- `docs/development/yt-dlp-ops-check.md`: Cron-based ops check documentation.
- `docs/cli-reference/tnh-setup.md`: Updated setup CLI documentation.
- `docs/cli-reference/ytt-fetch.md`: Updated runtime notes and warnings.
- `Makefile`: Added `ytdlp-runtime` target and build integration.
- `pyproject.toml`: Dependencies updated for setup UI.
- `poetry.lock`: Dependency lock updates.
- `scripts/setup_ytdlp_runtime.sh`: Removed legacy shell setup.
- `TODO.md`: Updated yt-dlp reliability tracking (P1) and audio-transcribe refactor (P2).

### Next Steps

- [ ] Add offline fixture-based yt-dlp tests and failure-mode coverage.
- [ ] Decide on cron failure notification path (issue creation or alerting).
- [ ] Complete ytt-fetch robustness (retries, error reporting, output stability).
- [ ] Plan audio-transcribe service-layer refactor to match object-service pattern.

### Open Questions

- What alerting mechanism should the monthly cron use when ops checks fail?

### References

- `/architecture/video-processing/adr/adr-vp02-ytdlp-operational-strategy.md`
- `/architecture/setup-tnh/adr/adr-st01-tnh-setup-runtime-hardening.md`
- `/development/yt-dlp-ops-check.md`

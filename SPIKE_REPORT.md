---
title: "Phase 0 Spike Report"
description: "Findings and gotchas from the protocol layer spike run"
status: complete
created: "2026-01-20"
updated: "2026-02-08"
---
# Phase 0 Spike Report

## Summary

The Phase 0 spike ran successfully against both Claude Code CLI (earlier) and Codex CLI (2026-02-08), producing full transcripts, git snapshots, and an NDJSON event stream. The protocol-layer capture chain works end-to-end in a real headless run.

## What Worked

- Headless Claude invocation with PTY capture completed successfully.
- Raw and normalized transcripts were written.
- Git pre/post snapshots and diff patch were emitted.
- Events stream recorded run start, workspace capture, agent start, diff, and completion.
- Heartbeat and agent output events are now emitted during execution.
- Headless Codex CLI invocation (`codex exec --json --output-last-message ... --full-auto -m gpt-5.2-codex`) completed successfully.

## Failure Modes Observed

- Missing `claude` binary caused a hard failure when not installed.
- Running in a dirty workspace produced diffs unrelated to the agent run.

## Gotchas

- `poetry run` warns when entrypoints are not installed; running `poetry install` removes the warning.
- The spike enforces a sandbox root preflight; dirty worktrees are allowed only inside the sandbox root.
- Sandbox sync resets and cleans the worktree; uncommitted changes must be re-applied via the sync patch.

## Recommendations

- Keep heartbeat and output event emission enabled to satisfy Phase 0 success criteria.
- Use a dedicated sandbox worktree (default: `<repo>-sandbox`) for spike runs.
- Define a follow-up ADR for Codex integration and agent binary discovery.

## Sandbox Strategy

Phase 0 runs should execute from a dedicated worktree named `<repo>-sandbox` (or set via `SPIKE_SANDBOX_ROOT`). The runner fails fast if the repo root does not match the expected sandbox path, but allows dirty worktrees inside the sandbox.

### Sandbox Sync

Use `scripts/sync-sandbox.sh` (or `make sync-sandbox`) to update the sandbox. The script now always resets the sandbox to the source repo branch and applies a patch of uncommitted changes, then runs in-place from that snapshot.

## Codex CLI Run (2026-02-08)

- **Worktree**: `/Users/phapman/Desktop/Projects/tnh-scholar-sandbox`
- **Branch**: `feat/agent-orchestration-v2`
- **Sync**: `scripts/sync-sandbox.sh --sandbox ... --source-repo ... --branch feat/agent-orchestration-v2`
- **Deps**: `poetry env use python`, `poetry install`
- **Command**:

```bash
poetry run python -m tnh_scholar.cli_tools.tnh_conductor_spike.tnh_conductor_spike \
  --agent codex \
  --task "List files in src/"
```

- **Run ID**: `20260208-063754`
- **Artifacts**: `.tnh-gen/runs/20260208-063754/` (transcripts, diff, response, run.json, events.ndjson)

## Codex CLI Implementation Run (2026-02-08)

A full implementation run validated the spike harness with a real coding task.

### Run Details

- **Run ID**: `20260208-155213`
- **Duration**: 6m 47s (15:52:13 → 15:59:00 UTC)
- **Task**: Implement ADR-CF02 (Prompt Catalog Discovery)
- **Exit Code**: 0 (completed)
- **Work Branch**: `work/20260208-155213`

### Artifact Capture

| Artifact | Size | Description |
|----------|------|-------------|
| `run.json` | 3KB | Run metadata, timing, git summaries |
| `events.ndjson` | 260KB | 272 events in NDJSON stream |
| `stdout.log` | 294KB | Raw CLI output |
| `transcript.md` | 294KB | Formatted transcript |
| `response.txt` | 2KB | Structured final report |
| `diff.patch` | 13KB | Unified diff (10 files) |
| `git_pre.json` | 105B | Pre-run clean state |
| `git_post.json` | 649B | Post-run dirty state |

### Forensic Note (2026-02-08)

Post-run analysis found two separate conditions:

1. **Artifact capture gap for untracked files**: `git_post.json` records untracked additions (`?? tests/configuration/`), but `diff.patch` only includes tracked-file edits. This explains why the reported implementation scope is larger than the patch alone.
2. **Later sandbox drift/corruption**: a subsequent sandbox state showed ~557 docs deletions that were not present in the run's recorded `git_post.json`. This indicates post-run workspace drift, not run-time divergence.

Result: the spike run itself is still considered valid; future salvage workflows should collect both tracked patch data and explicit untracked file manifests.

### Event Stream Analysis

**Orchestration Events:**

| Event Type | Count |
|------------|-------|
| AGENT_OUTPUT | 226 |
| HEARTBEAT | 40 |
| RUN_STARTED/COMPLETED | 2 |
| WORKSPACE_CAPTURED | 2 |
| DIFF_EMITTED | 1 |

**Codex Item Types:**

| Item Type | Count |
|-----------|-------|
| item.completed | 137 |
| command_execution | 108 |
| reasoning | 70 |
| item.started | 55 |
| file_change | 11 |
| todo_list | 4 |
| agent_message | 1 |

### Token Usage

```
Input tokens:        4,239,965  (4.2M)
Cached input:        4,089,472  (96% cache hit)
Output tokens:          17,936
```

### Implementation Quality

The agent produced commit-worthy code:

- Added `PromptPathBuilder` class with workspace → user → built-in precedence
- Lazy resolution via `@model_validator` in Pydantic settings
- Removed import-time constants, updated 4 CLI tools
- Created 4 new tests (all passing)
- Self-verified cleanup with `rg` for deprecated constants

### Conclusion

**Phase 0 Spike: PASSED**

All success criteria met. The harness provides full observability into autonomous agent runs. Proceed to Phase 1 implementation.

## Artifacts

- `.tnh-gen/runs/<run_id>/transcript.raw.log`
- `.tnh-gen/runs/<run_id>/transcript.md`
- `.tnh-gen/runs/<run_id>/diff.patch`
- `.tnh-gen/runs/<run_id>/run.json`
- `.tnh-gen/runs/<run_id>/events.ndjson`

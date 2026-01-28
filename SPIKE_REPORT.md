---
title: "Phase 0 Spike Report"
description: "Findings and gotchas from the protocol layer spike run"
status: draft
created: "2026-01-20"
---
# Phase 0 Spike Report

## Summary

The Phase 0 spike ran successfully against the Claude Code CLI, producing full transcripts, git snapshots, and an NDJSON event stream. The protocol-layer capture chain works end-to-end in a real headless run.

## What Worked

- Headless Claude invocation with PTY capture completed successfully.
- Raw and normalized transcripts were written.
- Git pre/post snapshots and diff patch were emitted.
- Events stream recorded run start, workspace capture, agent start, diff, and completion.
- Heartbeat and agent output events are now emitted during execution.

## Failure Modes Observed

- Missing `claude` binary caused a hard failure when not installed.
- Running in a dirty workspace produced diffs unrelated to the agent run.

## Gotchas

- `poetry run` warns when entrypoints are not installed; running `poetry install` removes the warning.
- The spike enforces a sandbox root preflight; dirty worktrees are allowed only inside the sandbox root.
- `codex` agent is declared but not implemented; it currently raises a `NotImplementedError`.

## Recommendations

- Keep heartbeat and output event emission enabled to satisfy Phase 0 success criteria.
- Use a dedicated sandbox worktree (default: `<repo>-sandbox`) for spike runs.
- Define a follow-up ADR for Codex integration and agent binary discovery.

## Sandbox Strategy

Phase 0 runs should execute from a dedicated worktree named `<repo>-sandbox` (or set via `SPIKE_SANDBOX_ROOT`). The runner fails fast if the repo root does not match the expected sandbox path, but allows dirty worktrees inside the sandbox.

### Sandbox Sync

Use `scripts/sync-sandbox.sh` (or `make sync-sandbox`) to update the sandbox. The script now always resets the sandbox to the source repo branch and applies a patch of uncommitted changes, then runs in-place from that snapshot.

## Artifacts

- `.tnh-gen/runs/<run_id>/transcript.raw.log`
- `.tnh-gen/runs/<run_id>/transcript.md`
- `.tnh-gen/runs/<run_id>/diff.patch`
- `.tnh-gen/runs/<run_id>/run.json`
- `.tnh-gen/runs/<run_id>/events.ndjson`

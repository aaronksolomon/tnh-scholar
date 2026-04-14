---
title: "Codex Harness End-to-End Test Report"
description: "Operational notes and blockers for the Codex harness test flow"
owner: "aaronksolomon"
author: "GPT-5 (Codex CLI)"
status: "draft"
created: "2026-01-23"
updated: "2026-01-23"
---

# Codex Harness End-to-End Test Report

## Context

We stood up a minimal Codex harness to validate a full tool-calling loop (read/search/apply/run tests) against the repo. This report captures what worked, what blocked, and the practical gotchas to help other agents reproduce and extend the test.

## Current State

- Harness runs via `tnh-codex-harness` (Typer CLI) and writes artifacts under `.tnh-codex/runs/<timestamp>/`.
- Tool calls are executed successfully (read/search), but final structured output is often missing.
- The run ends "blocked" when no final JSON response is produced after tool rounds.

## What Worked

- Tools executed with real outputs and filesystem access.
- Sandbox patch sync updates code without committing or switching branches.
- Codex runs can be executed from the sandbox with a copied `.env`.

## Key Blockers

1. **No final output text**: The model often emits tool calls only. Without a final JSON response, parsing fails.
2. **Responses API limitations**: `response_format` and `temperature` are rejected, so schema enforcement must use the `text` config.
3. **Sandbox hygiene**: Sync resets remove `.env`, so credentials must be copied after sync.

## Operational Gotchas

- Run `make sync-sandbox` from the source repo root, not inside the sandbox.
- After sync, copy `.env` to sandbox before running the harness.
- CLI is `tnh-codex-harness` with `--task`; there is no `run` subcommand.

## Recommended Next Steps

1. Enforce structured output with `text` JSON schema in the Responses API.
2. Persist tool results into artifacts for easier debugging.
3. Add a termination rule when tool calls repeat without final output.

## References

- `/architecture/agent-orchestration/adr/adr-oa03-agent-runner-architecture.md`
- `/architecture/agent-orchestration/adr/adr-oa03.1-claude-code-runner.md`
- `SPIKE_REPORT.md`

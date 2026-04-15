---
title: "SPIKE-03 Native Subagent Smoke Test"
description: "Lightweight result note on whether native headless subagent behavior can be observed and captured clearly enough for the OA01.x spike."
owner: ""
author: "Codex"
status: current
created: "2026-04-15"
updated: "2026-04-15"
---

# SPIKE-03 Native Subagent Smoke Test

SPIKE-03 records the retained evidence for native subagent behavior in headless Codex runs.

## Experiment ID

`SPIKE-03`

## Question

Can native subagent behavior be invoked, observed, and captured clearly enough in headless mode to support the spike?

## Setup

Primary artifacts:

- `tmp/codex-subagent-smoke-stdout.jsonl`
- `tmp/codex-wrapper-subagent-best-stdout.jsonl`
- `tmp/codex-subagent-smoke-stderr.log`
- `tmp/codex-wrapper-subagent-best-stderr.log`
- `tmp/supervisory-shell-trial-stdout.jsonl`
- `tmp/supervisory-shell-trial-stderr.log`

The retained evidence spans:

- one minimal subagent smoke test
- one wrapper-based low-noise subagent run
- one higher-level supervisory shell trial

## Result

Native subagent behavior is real and observable in headless mode.

Strongest retained evidence:

- `spawn_agent` appears as a `collab_tool_call`
- `wait` appears as a `collab_tool_call`
- the waited-on agent returns a concrete completion message
- the parent agent emits a final top-level message after the wait completes

Minimal proof path:

- `tmp/codex-wrapper-subagent-best-stdout.jsonl`

That artifact shows:

- one `spawn_agent`
- one `wait`
- one completed subordinate result with message `AVAILABLE`
- one final parent response `SUBAGENT_OK`

Important limitation:

- the minimal smoke test proves availability, not usefulness
- the supervisory-shell trial proves some usefulness, but also exposed a parent-rollout fork-context failure on the first spawn strategy

## Useful Artifacts

- `tmp/codex-wrapper-subagent-best-stdout.jsonl` is the clearest compact proof artifact
- `tmp/codex-subagent-smoke-stdout.jsonl` is the smallest proof that `spawn_agent` appears in headless JSONL output
- `tmp/supervisory-shell-trial-stdout.jsonl` is the best evidence that native subagent use can contribute to a broader supervisory task, even though the first inherited-context strategy failed

## Next Action

Treat native subagent behavior as observed capability, not just documented capability.

Do not assume inherited forked context is dependable.

The next useful experiment is the narrow supervisory comparison:

- same task
- same files
- same time budget
- direct single-agent pass versus tightly bounded supervisor with at most two subagent calls

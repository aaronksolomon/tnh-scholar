---
title: "Run Supervisory Shell Trial"
description: "Operator note for launching the first shell-based Codex supervisory team experiment."
owner: ""
author: "Codex"
status: current
created: "2026-04-13"
updated: "2026-04-13"
---
# Run Supervisory Shell Trial

Operator note for the first shell-launched supervisory Codex experiment.

## Files

- Workflow contract: `docs/architecture/agent-orchestration/supervisory-shell-trial/supervisory-team-workflow-contract.md`
- Current task brief: `docs/architecture/agent-orchestration/supervisory-shell-trial/current-supervisory-task-brief.md`

## Prompt Shape

The supervisor prompt should stay simple:

1. read the workflow contract
2. read the current task brief
3. act as a supervisor using native subagents
4. do not do substantive task work directly
5. use no more than 5 subagent calls
6. stop when the brief is sufficiently addressed or clearly blocked

## Suggested Command

Run from the repo root in your shell:

```bash
'/Users/phapman/.vscode/extensions/openai.chatgpt-26.406.31014-darwin-arm64/bin/macos-aarch64/codex' exec \
  --json \
  --ephemeral \
  -p collab \
  "Read docs/architecture/agent-orchestration/supervisory-shell-trial/supervisory-team-workflow-contract.md and docs/architecture/agent-orchestration/supervisory-shell-trial/current-supervisory-task-brief.md. Follow them precisely. Use native subagents for the substantive work. Do not do the substantive evaluation directly yourself. Use no more than 5 subagent calls." \
  2> >(tee tmp/supervisory-shell-trial-stderr.log >&2) \
  | tee tmp/supervisory-shell-trial-stdout.jsonl
```

## Lower-Noise Variant

If the goal is a cleaner machine-readable channel rather than maximum native surface exposure:

```bash
'/Users/phapman/.vscode/extensions/openai.chatgpt-26.406.31014-darwin-arm64/bin/macos-aarch64/codex' exec \
  --json \
  --ephemeral \
  -p collab \
  --disable plugins \
  --disable shell_snapshot \
  "Read docs/architecture/agent-orchestration/supervisory-shell-trial/supervisory-team-workflow-contract.md and docs/architecture/agent-orchestration/supervisory-shell-trial/current-supervisory-task-brief.md. Follow them precisely. Use native subagents for the substantive work. Do not do the substantive evaluation directly yourself. Use no more than 5 subagent calls." \
  2> >(tee tmp/supervisory-shell-trial-stderr.log >&2) \
  | tee tmp/supervisory-shell-trial-stdout.jsonl
```

This form preserves real-time terminal output while still capturing both streams to files.

## What To Inspect

- whether native subagents were actually used
- whether the supervisor kept to the supervisory role
- the quality of the final synthesis
- whether the result appears stronger than a plausible direct single-agent pass
- the number and shape of `collab_tool_call` events in `stdout`
- whether `stderr` noise materially interfered with understanding the run

## Success Criteria

The trial counts as useful if:

- the supervisor clearly delegates substantive work,
- at least one native subagent workstream completes,
- the final synthesis is more useful than a single direct critique pass would likely have been,
- and the run leaves enough observable evidence to guide the next experiment.

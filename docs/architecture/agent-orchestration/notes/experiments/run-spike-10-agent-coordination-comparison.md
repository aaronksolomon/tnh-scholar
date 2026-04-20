---
title: "Run SPIKE-10 Agent Coordination Comparison"
description: "Operator note for the five-arm SPIKE-10 comparison using direct Codex, native subagents, explicit Codex and Claude assistant CLIs, and the existing tnh-conductor path."
owner: ""
author: "Codex"
status: current
created: "2026-04-20"
updated: "2026-04-20"
---

# Run SPIKE-10 Agent Coordination Comparison

SPIKE-10 compares five execution shapes on the same bounded repo task.

## Task

Use this task brief:

- `docs/architecture/agent-orchestration/notes/experiments/spike-10-conductor-watch-task-brief.md`

The current maintained workflow for the agent-orch arm is:

- `docs/architecture/agent-orchestration/notes/experiments/spike-10-conductor-watch.workflow.yaml`

## Arms

### Arm A: Direct Codex

- one Codex run
- no native subagents
- no external worker CLIs

### Arm B: Native Codex Subagents

- one Codex supervisor run
- native `spawn_agent` delegation only

### Arm C: Explicit External Codex Worker

- one Codex supervisor run
- substantive delegation should go through the `codex-assistant` CLI entry point

### Arm D: Explicit External Claude Worker

- one Codex supervisor run
- substantive delegation should go through the `claude-assistant` CLI entry point

### Arm E: Existing Agent-Orch

- one maintained `tnh-conductor` run
- current repo-owned orchestration surface

## Comparison Intent

The point of SPIKE-10 is not only to compare outputs. It is also to compare:

- control-surface depth
- artifact clarity
- worker isolation
- coordination overhead
- and practical fit for TNH Scholar’s forward path

## Notes

- Keep all arms on the same committed base ref.
- Do not conflate the current `tnh-conductor` arm with a future `tnh-gen` evaluator path.
- The external-worker arms should prefer the assistant CLI entry points over ad hoc shell invocations so the comparison reflects the repo-native wrapper direction.

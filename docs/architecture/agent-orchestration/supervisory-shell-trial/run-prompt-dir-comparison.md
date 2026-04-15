---
title: "Run Prompt Dir Comparison"
description: "Operator commands for the three-arm prompt-dir implementation comparison: direct Codex, supervisory Codex, and kernel-mediated orchestration."
owner: ""
author: "Codex"
status: current
created: "2026-04-15"
updated: "2026-04-15"
---

# Run Prompt Dir Comparison

Use the same task brief for all arms:

- `docs/architecture/agent-orchestration/supervisory-shell-trial/prompt-dir-task-brief.md`

## Prerequisite

Before running the kernel-mediated arm, commit the Codex runner invocation update so the managed worktree includes the corrected `codex exec` invocation.

## Arm A: Direct Codex

```bash
codex exec \
  --json \
  --ephemeral \
  -p collab \
  "Read docs/architecture/agent-orchestration/supervisory-shell-trial/prompt-dir-task-brief.md. Implement the task directly as a single engineer. Do not use subagents. Do not commit, push, or open a pull request." \
  > tmp/prompt-dir-direct-stdout.jsonl \
  2> tmp/prompt-dir-direct-stderr.log
```

## Arm B: Supervisory Codex

```bash
codex exec \
  --json \
  --ephemeral \
  -p collab \
  "Read docs/architecture/agent-orchestration/supervisory-shell-trial/supervisory-team-workflow-contract-v2.md and docs/architecture/agent-orchestration/supervisory-shell-trial/prompt-dir-task-brief.md. Follow the supervisory contract. You are the engineering supervisor only. Delegate substantive work to subagent engineers. Do not commit, push, or open a pull request." \
  > tmp/prompt-dir-supervisory-stdout.jsonl \
  2> tmp/prompt-dir-supervisory-stderr.log
```

## Arm C: Kernel-Mediated Agent Orchestration

```bash
poetry run tnh-conductor run \
  --workflow docs/architecture/agent-orchestration/supervisory-shell-trial/prompt-dir-comparison.workflow.yaml \
  --repo-root . \
  --codex-executable "$(command -v codex)" \
  > tmp/prompt-dir-kernel-summary.json \
  2> tmp/prompt-dir-kernel-stderr.log
```

## Minimal Review Bundle

Capture:

- task brief
- stdout JSONL or conductor summary
- stderr log
- final diff
- targeted test result
- short human judgment note

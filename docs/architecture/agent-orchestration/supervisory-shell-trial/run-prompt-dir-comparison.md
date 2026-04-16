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

Run from the repository root.

## Prerequisites

Use the standalone native Codex CLI, not the VS Code extension-bundled binary.

Check:

```bash
CODEX=/opt/homebrew/bin/codex
"$CODEX" --version
```

Before running the kernel-mediated arm, the Codex runner invocation update must be committed so the managed worktree includes the corrected `codex exec` invocation.

Create the capture directory if needed:

```bash
mkdir -p tmp
```

## Arm A: Direct Codex

Single direct Codex call. This is the baseline for normal direct-agent workflow.

```bash
"$CODEX" exec \
  --json \
  --ephemeral \
  -p collab \
  "Read docs/architecture/agent-orchestration/supervisory-shell-trial/prompt-dir-task-brief.md. Implement the task directly as a single engineer. Do not use subagents. Do not commit, push, or open a pull request." \
  > tmp/prompt-dir-direct-stdout.jsonl \
  2> tmp/prompt-dir-direct-stderr.log
```

Suggested validation after the direct run:

```bash
poetry run pytest tests/cli_tools/test_tnh_gen.py tests/cli_tools/test_tnh_gen_coverage.py \
  > tmp/prompt-dir-direct-tests.log \
  2>&1
```

Capture the resulting diff:

```bash
git diff > tmp/prompt-dir-direct.diff
```

## Arm B: Supervisory Codex

Supervisor delegates substantive work to subagent engineers according to the v2 contract.

```bash
"$CODEX" exec \
  --json \
  --ephemeral \
  -p collab \
  "Read docs/architecture/agent-orchestration/supervisory-shell-trial/supervisory-team-workflow-contract-v2.md and docs/architecture/agent-orchestration/supervisory-shell-trial/prompt-dir-task-brief.md. Follow the supervisory contract. You are the engineering supervisor only. Delegate substantive work to subagent engineers. Do not commit, push, or open a pull request." \
  > tmp/prompt-dir-supervisory-stdout.jsonl \
  2> tmp/prompt-dir-supervisory-stderr.log
```

Suggested validation after the supervisory run:

```bash
poetry run pytest tests/cli_tools/test_tnh_gen.py tests/cli_tools/test_tnh_gen_coverage.py \
  > tmp/prompt-dir-supervisory-tests.log \
  2>&1
```

Capture the resulting diff:

```bash
git diff > tmp/prompt-dir-supervisory.diff
```

## Arm C: Kernel-Mediated Agent Orchestration

Run the existing agent-orchestration kernel through `tnh-conductor`.

The conductor creates its own managed worktree from committed `HEAD`.

```bash
poetry run tnh-conductor run \
  --workflow docs/architecture/agent-orchestration/supervisory-shell-trial/prompt-dir-comparison.workflow.yaml \
  --repo-root . \
  --codex-executable "$CODEX" \
  > tmp/prompt-dir-kernel-summary.json \
  2> tmp/prompt-dir-kernel-stderr.log
```

Inspect the conductor summary:

```bash
cat tmp/prompt-dir-kernel-summary.json
```

The summary includes the managed worktree path and run directory. Inspect those artifacts before comparing the kernel arm to the direct and supervisory arms.

## Minimal Review Bundle

Capture:

- task brief
- stdout JSONL or conductor summary JSON
- stderr log
- final diff
- targeted test result
- short human judgment note

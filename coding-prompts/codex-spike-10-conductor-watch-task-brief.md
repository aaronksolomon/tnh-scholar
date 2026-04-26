---
title: "Codex Spike 10 Conductor Watch Task Brief"
description: "Prompt for implementing watch-mode monitoring in tnh-conductor status."
owner: ""
author: "OpenAI GPT-5 Codex"
status: current
created: "2026-04-20"
updated: "2026-04-25"
model_family: "codex"
source: "docs/architecture/agent-orchestration/notes/experiments/spike-10-conductor-watch-task-brief.md"
copied: "2026-04-24"
---
# SPIKE-10 Conductor Watch Task Brief

Objective: add watch-mode monitoring to `tnh-conductor status`.

Target shape:

```bash
tnh-conductor status run-123 --watch
```

Requirements:

- Add `--watch` to `tnh-conductor status`.
- Add a configurable polling interval flag.
- When `--watch` is enabled, print status snapshots repeatedly until the run reaches a terminal state.
- Terminal states should include at least `completed`, `failed`, and `blocked`.
- Preserve the current one-shot status behavior when `--watch` is not supplied.
- Keep output machine-readable JSON, one snapshot per line.

Scope:
- in: `src/tnh_scholar/cli_tools/tnh_conductor/`, targeted tests, and optional CLI docs if they naturally change
- out: broader conductor architecture work

Validation:

- run the targeted `tnh-conductor` CLI tests

```bash
poetry run pytest tests/cli_tools/test_tnh_conductor.py
```

Deliverable:
- changed files
- short summary
- any follow-up gaps left out intentionally

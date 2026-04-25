---
title: "Codex Bootstrap Proof Current Task Brief"
description: "Prompt for the current bootstrap-proof implementation task."
owner: ""
author: "OpenAI GPT-5 Codex"
status: current
created: "2026-04-10"
updated: "2026-04-25"
model_family: "codex"
source: "docs/architecture/agent-orchestration/bootstrap-proof/current-task-brief.md"
copied: "2026-04-24"
---
# Current Bootstrap Proof Task Brief

Objective: implement `tnh-gen --prompt-dir` as a one-off prompt catalog override.

Context:
- keep the change small and aligned with existing `tnh-gen` CLI and config-loader patterns
- preserve clear precedence: CLI override above env, user config, workspace config, and explicit config file defaults where applicable

The intended user-facing shape is:

```bash
tnh-gen --prompt-dir ./test-prompts list
```

Scope:
- in: `src/tnh_scholar/cli_tools/tnh_gen/`, relevant tests, and `docs/cli-reference/tnh-gen.md`
- out: prompt-system redesign, unrelated CLI cleanup

Requirements:

- add a global `--prompt-dir` option
- route it through the existing config loading path
- preserve current behavior when the flag is absent
- keep invalid or missing prompt-dir failures clear

Validation:

- run the targeted CLI tests for `tnh-gen`
- cover precedence and at least one command path using the override

Deliverable:
- changed files
- short summary
- any follow-up gaps left out intentionally

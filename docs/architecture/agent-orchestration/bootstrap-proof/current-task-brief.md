---
title: "Current Bootstrap Proof Task Brief"
description: "Task brief consumed by the generic bootstrap-proof workflow."
owner: ""
author: "OpenAI GPT-5 Codex"
status: current
created: "2026-04-10"
updated: "2026-04-10"
---
# Current Bootstrap Proof Task Brief

## Repo Orientation

Read the repo-local instructions and standards before coding:

- `AGENTS.md`
- `docs/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md`
- `docs/development/design-principles.md`
- `docs/development/style-guide.md`
- `docs/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md`
- the `TODO.md` section `Add --prompt-dir Global Flag to tnh-gen`

Follow existing `tnh-gen` CLI patterns and keep the change small, typed, and reviewable.

## Task

Implement the `--prompt-dir` global flag for `tnh-gen` so one-off prompt catalog overrides can be supplied directly at the CLI without requiring environment variables or a temporary config file.

The intended user-facing shape is:

```bash
tnh-gen --prompt-dir ./test-prompts list
```

This task matters because it improves one-off CLI use for testing, CI, and development workflows without widening into prompt-system redesign or unrelated CLI cleanup. Preserve config precedence clarity, with the CLI flag overriding the other prompt directory sources.

Likely files in scope:

- `src/tnh_scholar/cli_tools/tnh_gen/tnh_gen.py`
- `src/tnh_scholar/cli_tools/tnh_gen/config_loader.py`
- `src/tnh_scholar/cli_tools/tnh_gen/types.py`
- `tests/cli_tools/test_tnh_gen.py`
- `docs/cli-reference/tnh-gen.md`

## Validation

Develop and run appropriate tests for the change, especially precedence and at least one command path using the override. Check code quality with the relevant local tooling and keep the resulting diff small and reviewable.

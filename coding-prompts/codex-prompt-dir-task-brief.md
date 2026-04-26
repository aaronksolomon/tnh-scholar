---
title: "Codex Prompt Dir Task Brief"
description: "Prompt for implementing the tnh-gen prompt-dir CLI override."
owner: ""
author: "OpenAI GPT-5 Codex"
status: current
created: "2026-04-15"
updated: "2026-04-25"
model_family: "codex"
source: "docs/architecture/agent-orchestration/supervisory-shell-trial/prompt-dir-task-brief.md"
copied: "2026-04-24"
---
# Prompt Dir Task Brief

Objective: implement `tnh-gen --prompt-dir` as a CLI-level prompt catalog override.

Example:

```bash
tnh-gen --prompt-dir ./test-prompts list
```

Requirements:

- Add a global `--prompt-dir` option to `tnh-gen`.
- The flag should override all lower-precedence prompt directory sources.
- The override should flow through the existing `tnh-gen` config loading path.
- Existing config behavior should remain unchanged when `--prompt-dir` is not supplied.

Precedence:

Effective precedence should be:

1. defaults and environment
2. user config
3. workspace config
4. explicit `--config`
5. CLI overrides, including `--prompt-dir`

Scope:
- in: `src/tnh_scholar/cli_tools/tnh_gen/`, targeted tests, and `docs/cli-reference/tnh-gen.md`
- out: broader config cleanup or prompt-system redesign

Validation:

- run the targeted `tnh-gen` CLI tests

```bash
poetry run pytest tests/cli_tools/test_tnh_gen.py tests/cli_tools/test_tnh_gen_coverage.py
```

If broader config behavior changes, add or run the relevant config tests too.

Deliverable:
- changed files
- short summary
- any follow-up gaps left out intentionally

---
title: "Prompt Dir Task Brief"
description: "Bounded implementation task brief for comparing direct Codex, supervisory Codex, and kernel-mediated agent orchestration on the tnh-gen --prompt-dir feature."
owner: ""
author: "Codex"
status: current
created: "2026-04-15"
updated: "2026-04-15"
---

# Prompt Dir Task Brief

Implement the `tnh-gen --prompt-dir` global flag.

## Goal

Allow one-off `tnh-gen` calls to override the prompt catalog directory from the command line.

Example:

```bash
tnh-gen --prompt-dir ./test-prompts list
```

## Expected Behavior

- Add a global `--prompt-dir` option to `tnh-gen`.
- The flag should override all lower-precedence prompt directory sources.
- The override should flow through the existing `tnh-gen` config loading path.
- Existing config behavior should remain unchanged when `--prompt-dir` is not supplied.

## Precedence To Preserve

Effective precedence should be:

1. defaults and environment
2. user config
3. workspace config
4. explicit `--config`
5. CLI overrides, including `--prompt-dir`

## Likely Files

- `src/tnh_scholar/cli_tools/tnh_gen/tnh_gen.py`
- `src/tnh_scholar/cli_tools/tnh_gen/config_loader.py`
- `tests/cli_tools/test_tnh_gen.py`
- `tests/cli_tools/test_tnh_gen_coverage.py`
- `docs/cli-reference/tnh-gen.md`

## Validation

At minimum, run targeted tests covering:

```bash
poetry run pytest tests/cli_tools/test_tnh_gen.py tests/cli_tools/test_tnh_gen_coverage.py
```

If the implementation changes broader config behavior, add or run the relevant config tests too.

## Success Criteria

- `tnh-gen --prompt-dir <dir> list` uses the supplied prompt directory.
- `--prompt-dir` wins over env, user config, workspace config, and explicit config file values.
- Missing or invalid prompt directory errors remain clear.
- CLI reference docs mention the new global flag.
- Targeted tests pass.

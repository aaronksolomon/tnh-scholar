---
title: "SPIKE-06 Native Codex CLI Baseline"
description: "Baseline validation of the standalone native Codex CLI before running the prompt-dir orchestration comparison."
owner: ""
author: "Codex"
status: current
created: "2026-04-15"
updated: "2026-04-15"
---

# SPIKE-06 Native Codex CLI Baseline

## Experiment ID

`SPIKE-06`

## Question

Does the standalone native Codex CLI at `/opt/homebrew/bin/codex` support the baseline headless and kernel-mediated flows cleanly enough to proceed to the larger prompt-dir comparison?

## Setup

Native CLI:

- executable: `/opt/homebrew/bin/codex`
- version: `codex-cli 0.120.0`

Baseline checks:

- `codex --version`
- `codex --help`
- `codex exec --help`
- direct `codex exec --json --ephemeral -p collab` ACK prompt
- `tnh-conductor --help`
- `tnh-conductor run --help`
- focused runner/conductor test set
- no-edit `tnh-conductor` ACK workflow using the native Codex executable

Primary artifacts:

- `tmp/codex-native-version.txt`
- `tmp/codex-native-help.txt`
- `tmp/codex-native-exec-help.txt`
- `tmp/codex-native-ack-stdout.jsonl`
- `tmp/codex-native-ack-stderr.log`
- `tmp/tnh-conductor-help.txt`
- `tmp/tnh-conductor-run-help.txt`
- `tmp/codex-native-runner-tests-after-response-path-fix.log`
- `tmp/codex-native-kernel-summary-after-response-path-fix.json`
- `.tnh-conductor/runs/20260415T210728Z/`

## Result

The standalone native Codex CLI is usable for the next prompt-dir comparison after two runner fixes.

Confirmed behavior:

- `codex --version`, `codex --help`, and `codex exec --help` exited cleanly with empty stderr.
- direct headless `codex exec` returned valid JSONL and the expected final message `ACK_NATIVE_CODEX_BASELINE`.
- direct headless `codex exec` still emitted plugin-manifest warnings to stderr from the user Codex home, so stdout/stderr split remains required.
- `poetry run tnh-conductor --help` and `poetry run tnh-conductor run --help` work cleanly.
- `poetry run python -m tnh_scholar.cli_tools.tnh_conductor.tnh_conductor --help` is not a useful help path in this environment; it exits with only a runpy warning.
- the focused runner/conductor tests passed after fixes: `22 passed in 5.72s`.
- the no-edit kernel run completed through `tnh-conductor` using `/opt/homebrew/bin/codex`.
- the final kernel ACK run returned `ACK_NATIVE_CODEX_KERNEL_BASELINE`.
- the final kernel ACK run left the managed worktree clean.

## Issues Found And Fixed

### Forced Model Was Too Specific

The maintained Codex runner forced `-m gpt-5.2-codex`.

That failed under the native CLI with ChatGPT account auth:

```text
The 'gpt-5.2-codex' model is not supported when using Codex with a ChatGPT account.
```

The runner now omits `-m` by default so Codex uses repo-local CLI configuration. Explicit model override remains supported for configured callers.

### Final Response Capture Dirtied Worktrees

The maintained runner previously wrote `codex-last-message.txt` inside the managed worktree.

That made a no-edit run appear dirty:

```text
?? codex-last-message.txt
```

The runner now captures `--output-last-message` in a temporary path outside the worktree and persists the final response through the normal run-artifact path.

## Useful Artifacts

Most useful artifacts:

- `.tnh-conductor/runs/20260415T210728Z/artifacts/ack/runner_metadata.json`
- `.tnh-conductor/runs/20260415T210728Z/artifacts/ack/transcript.ndjson`
- `.tnh-conductor/runs/20260415T210728Z/artifacts/ack/final_response.txt`
- `.tnh-conductor/runs/20260415T210728Z/artifacts/ack/workspace_status.json`

The final workspace status shows:

```json
{
  "is_dirty": false,
  "staged_count": 0,
  "unstaged_count": 0,
  "diff_summary": null
}
```

## Next Action

Proceed to the prompt-dir comparison with these constraints:

- use `/opt/homebrew/bin/codex` or `$(command -v codex)` after confirming it resolves to the native CLI
- use `poetry run tnh-conductor`, not the module form
- keep stdout/stderr split for all direct Codex calls
- inspect managed worktree cleanliness as part of the kernel arm review

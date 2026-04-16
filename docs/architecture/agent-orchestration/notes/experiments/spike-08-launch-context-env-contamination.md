---
title: "SPIKE-08 Launch Context Environment Contamination"
description: "Differential experiment on whether Codex-on-Codex launch noise comes from PTY shape or from inherited execution environment contamination."
owner: ""
author: "Codex"
status: current
created: "2026-04-15"
updated: "2026-04-15"
---

# SPIKE-08 Launch Context Environment Contamination

## Experiment ID

`SPIKE-08`

## Question

When Codex launches another Codex process, is the noisy startup behavior caused mainly by PTY shape, or by inherited execution environment contamination?

## Setup

Constant command shape:

- executable: `/opt/homebrew/bin/codex`
- working directory: repo root
- command: `codex exec --json --ephemeral -p collab "<ACK prompt>"`

Compared launch contexts:

- fresh `zsh -lic` without PTY, inheriting the current agent environment
- fresh `zsh -lic` with PTY, inheriting the current agent environment
- real user Terminal.app shell, same command run manually by the operator
- stripped environment launch modeled on the real Terminal.app shell

Primary artifacts:

- `tmp/spike-08-pty-vs-shell/nonpty-*.stdout.jsonl`
- `tmp/spike-08-pty-vs-shell/nonpty-*.stderr.log`
- `tmp/spike-08-pty-vs-shell/pty-*.stdout.jsonl`
- `tmp/spike-08-pty-vs-shell/pty-*.stderr.log`
- `tmp/spike-08-pty-vs-shell/nonpty-login-env.txt`
- `tmp/spike-08-pty-vs-shell/pty-login-env.txt`
- `tmp/user-json-*.stdout.jsonl`
- `tmp/user-json-*.stderr.log`
- `tmp/user-shell-env.txt`
- `tmp/spike-08-pty-vs-shell/stripped.stdout.jsonl`
- `tmp/spike-08-pty-vs-shell/stripped.stderr.log`
- `tmp/spike-08-pty-vs-shell/stripped-env.txt`

## Result

The main cause of noisy Codex-on-Codex startup behavior is inherited environment contamination, not PTY shape.

Observed behavior:

- 5/5 non-PTY inherited-env runs succeeded and emitted repeated plugin and shell-snapshot warnings
- 5/5 PTY inherited-env runs succeeded and emitted essentially the same warnings
- 5/5 real Terminal.app user-shell runs succeeded and emitted zero warning lines on stderr
- 1/1 stripped-env run modeled on the real user shell succeeded and emitted no plugin or shell-snapshot warnings

This rules out PTY as the main explanation for the warning difference.

## Key Comparison

Inherited-env launched shells contained agent-host contamination not present in the clean user shell, including:

- `CODEX_CI=1`
- `CODEX_INTERNAL_ORIGINATOR_OVERRIDE=codex_vscode`
- `CODEX_THREAD_ID=...`
- multiple `VSCODE_*` variables
- `TERM=dumb` in the inherited PTY login shell path
- mutated `PATH` entries including Codex temp/wrapper locations

The real Terminal.app shell did not contain those variables and used a normal user-facing terminal setup such as:

- `TERM=xterm-256color`
- `TERM_PROGRAM=Apple_Terminal`
- no `CODEX_*`
- no `VSCODE_*`

The stripped-env run did not perfectly match the real user shell, but it removed the contaminated inherited variables and was sufficient to restore clean stderr.

## Practical Conclusion

Codex can be launched from Codex without interference if the child process is started with a curated user-like environment instead of the inherited parent agent environment.

For the current spike, the meaningful launch policy is:

- do not blindly inherit parent env
- build an explicit allowlist environment
- exclude `CODEX_*`, `VSCODE_*`, and other host-runtime control variables by default

## Useful Artifacts

Most useful artifacts:

- `tmp/spike-08-pty-vs-shell/nonpty-summary.txt`
- `tmp/spike-08-pty-vs-shell/pty-summary.txt`
- `tmp/user-shell-env.txt`
- `tmp/spike-08-pty-vs-shell/stripped-env.txt`
- `tmp/spike-08-pty-vs-shell/stripped.stderr.log`
- `tmp/spike-08-pty-vs-shell/stripped.stdout.jsonl`

Representative warning-bearing stderr:

- `tmp/spike-08-pty-vs-shell/nonpty-1.stderr.log`
- `tmp/spike-08-pty-vs-shell/pty-1.stderr.log`

Representative clean stderr:

- `tmp/user-json-1.stderr.log`
- `tmp/spike-08-pty-vs-shell/stripped.stderr.log`

## Next Action

Use the curated environment launch policy in the maintained Codex runner path for larger orchestration comparisons.

That launch policy has now been validated through the maintained `tnh-conductor` ACK workflow as a clean end-to-end path.

The next practical work is:

- keep the allowlist environment contract explicit and narrow
- preserve only variables shown to matter for local toolchain use
- run the prompt-dir comparison on the sanitized launch surface

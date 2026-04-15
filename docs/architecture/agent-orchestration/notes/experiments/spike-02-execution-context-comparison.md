---
title: "SPIKE-02 Execution Context Comparison"
description: "Lightweight result note comparing headless Codex execution contexts for noise, reliability, and practical usability."
owner: ""
author: "Codex"
status: current
created: "2026-04-15"
updated: "2026-04-15"
---

# SPIKE-02 Execution Context Comparison

SPIKE-02 compares the practical headless execution contexts already exercised during the OA01.x communication experiments.

## Experiment ID

`SPIKE-02`

## Question

Which execution context is the most reliable and least noisy for headless Codex use?

## Setup

Contexts compared:

- direct user shell
- agent-launched shell from repo root
- agent-launched shell from repo subdirectory
- agent-launched shell outside the repo
- repo-local wrapper path

Primary artifacts:

- `tmp/codex-user-stdout.jsonl`
- `tmp/codex-user-stderr.log`
- `tmp/codex-matrix-root-stdout.jsonl`
- `tmp/codex-matrix-root-stderr.log`
- `tmp/codex-matrix-subdir-stdout.jsonl`
- `tmp/codex-matrix-subdir-stderr.log`
- `tmp/codex-matrix-outside-stdout.jsonl`
- `tmp/codex-matrix-outside-stderr.log`
- `tmp/codex-script-stdout.jsonl`
- `tmp/codex-script-stderr.log`

## Result

Best practical context:

- direct user shell

Best machine-oriented context available from the live agent environment:

- wrapper or direct agent-launched path with `stdout`/`stderr` separation

Observed ranking:

1. direct user shell
2. wrapper-assisted agent launch
3. direct agent-launched shell from repo root
4. direct agent-launched shell from repo subdirectory
5. direct agent-launched shell outside repo

Key observations:

- the direct user shell produced clean JSON on `stdout` and empty `stderr`
- the agent-launched contexts all remained workable, but they carried noisy state-db and plugin warnings
- repo-root versus subdirectory versus outside-repo changed details, but not the main conclusion
- the wrapper improved normalization and capture, but it did not recreate user-shell cleanliness

## Useful Artifacts

- `tmp/codex-user-stderr.log` is the clearest evidence that user-shell launch is materially cleaner
- `tmp/codex-matrix-root-stderr.log`, `tmp/codex-matrix-subdir-stderr.log`, and `tmp/codex-matrix-outside-stderr.log` show the recurring warning pattern in tool-launched contexts
- `tmp/codex-script-stdout.jsonl` and `tmp/codex-script-stderr.log` show the wrapper's value as a stable capture surface

## Next Action

Treat direct user-shell launch as the best high-value comparison path when testing supervisory behavior.

For automation from the live agent environment, continue using:

- explicit `stdout`/`stderr` separation
- the small wrapper when capture normalization helps
- narrow tasks rather than broad autonomy experiments

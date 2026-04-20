---
title: "SPIKE-10 Conductor Watch Task Brief"
description: "Medium bounded implementation task for comparing agent-coordination arms on live operator visibility in tnh-conductor."
owner: ""
author: "Codex"
status: current
created: "2026-04-20"
updated: "2026-04-20"
---

# SPIKE-10 Conductor Watch Task Brief

Implement live operator monitoring for `tnh-conductor status`.

## Goal

Add a watch mode so operators can monitor one run until it reaches a terminal lifecycle state without manually rerunning the command.

Example target shape:

```bash
tnh-conductor status run-123 --watch
```

## Expected Behavior

- Add `--watch` to `tnh-conductor status`.
- Add a configurable polling interval flag.
- When `--watch` is enabled, print status snapshots repeatedly until the run reaches a terminal state.
- Terminal states should include at least `completed`, `failed`, and `blocked`.
- Preserve the current one-shot status behavior when `--watch` is not supplied.
- Keep output machine-readable JSON, one snapshot per line.

## Likely Files

- `src/tnh_scholar/cli_tools/tnh_conductor/tnh_conductor.py`
- `tests/cli_tools/test_tnh_conductor.py`
- optional CLI docs if the implementation naturally reaches them

## Validation

At minimum, run:

```bash
poetry run pytest tests/cli_tools/test_tnh_conductor.py
```

## Success Criteria

- one-shot `status` still works unchanged
- `status --watch` exits once the run reaches a terminal state
- repeated snapshots are emitted while the run is still active
- invalid or missing runs still fail clearly
- tests cover both one-shot and watch behavior

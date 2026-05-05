---
title: "TNH Prompts Workspace"
description: "Tracked repo-local prompt workspace used for tnh-scholar testing, walkthroughs, and release validation."
status: current
created: "2026-05-02"
---

# TNH Prompts Workspace

This directory is the tracked repo-local prompt workspace for `tnh-scholar`.

## Purpose

`tnh-prompts/` exists to make prompt-driven workflows in this repository reproducible:

- golden tests
- walkthrough commands
- release validation
- prompt/schema integration checks

It is a workspace for testing and exploration during the current rapid-prototype phase.

## Relationship to Other Prompt Locations

- `prompts/`
  - Separate fast-moving external prompt repo used for active authoring.
- `tnh-prompts/`
  - Tracked repo-local mirror used by `tnh-scholar` docs and tests.
- `src/tnh_scholar/runtime_assets/prompts/`
  - Minimal bundled shipped subset for installed-package behavior.

For this phase, repo-local reproducibility takes priority over prompt-repo separation. As prompts stabilize, verified prompts from this workspace may later be promoted into runtime assets.

## Usage

For walkthroughs and golden tests, prefer:

```bash
tnh-gen --prompt-dir ./tnh-prompts ...
```

This avoids dependence on an external local prompt checkout.

Golden-run outputs generated from this workspace should stay local to the
operator's environment; this directory tracks the prompt mirror itself, not run
artifacts.

## Scope

- Prompt quality is still under active iteration.
- Backward compatibility is not guaranteed during the current `0.x` prototype phase.
- Structural JSON contract compliance is enforced through the schema files in `src/tnh_scholar/runtime_assets/schemas/`.

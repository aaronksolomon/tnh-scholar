---
title: "tnh-conductor Operator Guide"
description: "Practical operator guidance for running the maintained tnh-conductor bootstrap path."
owner: ""
author: ""
status: current
created: "2026-04-24"
---
# tnh-conductor Operator Guide

This guide is the practical companion to the [tnh-conductor CLI Reference](/cli-reference/tnh-conductor.md).

It is for maintainers and contributors using the current bootstrap-oriented `tnh-conductor` path, not for historical spike code.

## What To Expect

The maintained path is intentionally narrow:

- you start from a committed base ref
- `tnh-conductor` creates a managed worktree
- one workflow runs against that worktree
- canonical artifacts are written under the conductor runs root
- status is read back through `tnh-conductor status`

This is a bootstrap runner, not a general orchestration shell.

## Typical Flow

1. Choose a workflow YAML file.
2. Run it from the repository root or pass `--repo-root`.
3. Capture the returned run id from stdout.
4. Inspect progress with `tnh-conductor status <run_id>`.
5. Use `tnh-conductor status <run_id> --watch` when you want stable live polling.
6. Review the resulting worktree diff and canonical artifacts before taking any follow-on action.

Example:

```bash
# Example illustrative workflow path
tnh-conductor run \
  --workflow workflows/bootstrap/docs-review.yaml \
  --repo-root /path/to/tnh-scholar

tnh-conductor status 20260424T143022Z --watch
```

## Operator Defaults

- Prefer running from a clean, committed base state.
- Treat the managed worktree as the mutable execution boundary.
- Treat the canonical run-artifact directory as the evidence boundary.
- Prefer the CLI status command over ad hoc file inspection when checking live progress.

## Current Maintained Subset

The current maintained operator surface is:

- `run`
- `status`
- `status --watch`

Do not assume older spike or MVP packages reflect the preferred workflow for current release use.

## Related Docs

- [tnh-conductor CLI Reference](/cli-reference/tnh-conductor.md)
- [Architecture Blueprint](/architecture/agent-orchestration/notes/design/architecture-blueprint.md)
- [System Design](/development/system-design.md)
- [Release Workflow](/development/release-workflow.md)

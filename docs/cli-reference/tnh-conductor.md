---
title: "tnh-conductor"
description: "Maintained local/headless workflow bootstrap runner for agent orchestration."
owner: ""
author: ""
status: current
created: "2026-04-24"
---
# tnh-conductor

`tnh-conductor` is the maintained local/headless workflow bootstrap runner for TNH Scholar agent orchestration.

It is the current operator-facing CLI for running a bounded workflow against managed worktrees and reading canonical run status artifacts.

## Maintained Scope

The maintained CLI surface is intentionally small:

- `tnh-conductor run` executes one workflow
- `tnh-conductor status` reads one run status snapshot
- `tnh-conductor status --watch` polls until a run reaches a terminal lifecycle state

This command should be treated as distinct from older orchestration lines:

| Surface | Status | Purpose |
| --- | --- | --- |
| `tnh-conductor` | Maintained | Current headless/bootstrap entry point |
| `tnh-conductor-spike` | Experimental | Earlier spike CLI for protocol exploration |
| `conductor_mvp/` | Migration source | Internal implementation lineage, not the preferred operator entry |

## Usage

```bash
tnh-conductor [OPTIONS] COMMAND [ARGS]...
```

## Commands

### `run`

Execute one maintained local/headless bootstrap run.

```bash
tnh-conductor run --workflow WORKFLOW_FILE [OPTIONS]
```

| Option | Description |
| --- | --- |
| `--workflow FILE` | Workflow YAML file to execute. Required. |
| `--repo-root DIRECTORY` | Repository root for the managed worktree run. Defaults to the current directory. |
| `--runs-root DIRECTORY` | Optional override for the canonical runs root. |
| `--workspace-root DIRECTORY` | Optional override for the managed worktree root. |
| `--base-ref TEXT` | Committed git base ref for the run. Defaults to `HEAD`. |
| `--codex-executable FILE` | Optional explicit path to the Codex executable. |
| `--claude-executable FILE` | Optional explicit path to the Claude executable. |

Successful runs emit a JSON summary to stdout. Failures emit a user-facing error to stderr and exit with code `1`.

Example:

```bash
# Example illustrative workflow path
tnh-conductor run \
  --workflow workflows/bootstrap/docs-review.yaml \
  --repo-root /path/to/tnh-scholar
```

### `status`

Read the maintained live status artifact for one run.

```bash
tnh-conductor status [OPTIONS] RUN_ID
```

| Option | Description |
| --- | --- |
| `RUN_ID` | Run id to inspect. Required. |
| `--repo-root DIRECTORY` | Repository root used to resolve default storage roots. Defaults to the current directory. |
| `--runs-root DIRECTORY` | Optional override for the canonical runs root. |
| `--watch` | Poll and print status snapshots until the run reaches a terminal state. |
| `--poll-interval-seconds FLOAT` | Polling interval in seconds when `--watch` is enabled. Defaults to `1.0`. |

Examples:

```bash
# One-shot status read
tnh-conductor status 20260424T143022Z

# Watch mode
tnh-conductor status 20260424T143022Z --watch
```

## Output and Artifacts

The CLI emits machine-readable JSON to stdout.

For a completed run, canonical artifacts live under the conductor runs root in a structure like:

```text
.tnh-conductor/runs/<run_id>/
  metadata.json
  final-state.txt
  events.ndjson
  artifacts/
    <step_id>/
      manifest.json
```

Use `tnh-conductor status --watch` when you want a stable polling interface instead of tailing files directly.

## Current Limitations

- The maintained CLI is bootstrap-focused, not a full orchestration control plane.
- More advanced semantic-control depth is still under active development.
- The architecture docs describe broader direction than the currently exposed CLI surface.

## Related Docs

- [tnh-conductor Operator Guide](/development/tnh-conductor-operator-guide.md)
- [Architecture Blueprint](/architecture/agent-orchestration/notes/design/architecture-blueprint.md)
- [ADR-OA01.1: TNH-Conductor Strategy v2](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md)
- [ADR-OA04: Workflow Execution Contracts](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)

---
title: "Run Bootstrap Proof"
description: "Operator note for running the first maintained bootstrap-proof workflow."
owner: ""
author: "OpenAI GPT-5 Codex"
status: current
created: "2026-04-10"
updated: "2026-04-10"
---
# Run Bootstrap Proof

## Files

- Workflow: `docs/architecture/agent-orchestration/bootstrap-proof/generic-bootstrap-proof.workflow.yaml`
- Task brief: `docs/architecture/agent-orchestration/bootstrap-proof/current-task-brief.md`

## Command

Use the module form, since the uninstalled `poetry run tnh-conductor` entry point is not resolving correctly in this repo environment:

```bash
poetry run python -m tnh_scholar.cli_tools.tnh_conductor.tnh_conductor run \
  --workflow docs/architecture/agent-orchestration/bootstrap-proof/generic-bootstrap-proof.workflow.yaml \
  --repo-root . \
  --base-ref main
```

## What To Inspect After The Run

- stdout JSON summary from `tnh-conductor`
- the reported `run_directory`
- the reported `workspace_context.worktree_path`
- artifacts under the run directory:
  - `metadata.json`
  - `events.ndjson`
  - `artifacts/<step_id>/manifest.json`
  - `final-state.txt`

## Success Criteria

The run counts as a useful bootstrap proof if:

- the managed worktree contains a small reviewable diff for the task brief
- validation reaches a clean terminal outcome
- canonical run artifacts are present and intelligible
- a human could plausibly continue the result through the normal review flow

---
title: "Agent Orchestration Spike Testing Sequence"
description: "Concise, unambiguous steps to run the Codex CLI spike in a sandbox worktree."
owner: ""
author: ""
status: current
created: "2026-02-08"
updated: "2026-02-08"
---
# Agent Orchestration Spike Testing Sequence

Purpose: run the Codex CLI spike from a clean sandbox worktree that mirrors the
source repo, using Poetry for dependencies.

## Preconditions

- Python 3.12.4 available
- Poetry installed
- Codex CLI installed + authenticated (for `--agent codex`)
- Source repo path: `.../tnh-scholar`

## 1) Create sandbox worktree (one-time)

```bash
git -C /path/to/tnh-scholar worktree add ../tnh-scholar-sandbox <branch>
```

## 2) Sync sandbox to source repo (every run)

Run from the **source repo root**:

```bash
./scripts/sync-sandbox.sh \
  --sandbox /path/to/tnh-scholar-sandbox \
  --source-repo /path/to/tnh-scholar \
  --branch <branch>
```

Notes:

- This resets/cleans the sandbox worktree and applies the source repo diff.
- The branch must exist in the sandbox worktree.

## 3) Install deps in sandbox (when lockfile changes)

```bash
cd /path/to/tnh-scholar-sandbox
poetry env use python
poetry install
```

## 4) Run the spike (Codex CLI)

```bash
poetry run python -m tnh_scholar.cli_tools.tnh_conductor_spike.tnh_conductor_spike \
  --agent codex \
  --task "List files in src/"
```

Artifacts are written to `.tnh-gen/runs/<run_id>/` in the sandbox worktree:

- `transcript.md`
- `transcript.raw.log`
- `diff.patch`
- `response.txt`
- `run.json`
- `events.ndjson`

## 5) Optional: run the focused test

```bash
poetry run pytest tests/agent_orchestration/test_spike_command_builder.py
```

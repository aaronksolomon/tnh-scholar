---
title: "SPIKE-10 Agent Coordination Comparison Result"
description: "Five-arm comparison of direct Codex, native subagents, explicit Codex and Claude assistant CLIs, and the existing tnh-conductor orchestration path on the same bounded implementation task."
owner: ""
author: "Codex"
status: current
created: "2026-04-20"
updated: "2026-04-20"
---

# SPIKE-10 Agent Coordination Comparison Result

This note records the observed outcomes, artifact evidence, and practical recommendation from the five-arm SPIKE-10 coordination run.

## Experiment ID

`SPIKE-10`

## Question

On the same bounded implementation task, which coordination shape currently looks most viable for TNH Scholar?

Compared arms:

- direct single-agent Codex
- Codex with native subagents
- explicit external Codex workers through `codex-assistant`
- explicit external Claude workers through `claude-assistant`
- existing agent-orch through `tnh-conductor`

This result intentionally excludes a live `tnh-gen` evaluator arm because maintained agent-orch code does not currently wire `tnh-gen` into supervisory interpretation or workflow routing.

## Setup

Task brief:

- `/docs/architecture/agent-orchestration/notes/experiments/spike-10-conductor-watch-task-brief.md`

Maintained workflow:

- `/docs/architecture/agent-orchestration/notes/experiments/spike-10-conductor-watch.workflow.yaml`

Committed base for all arms:

- `6909fcca` on `main`

Manual-arm experiment root:

- `tmp/spike-10/20260420T215652Z`

Conductor run:

- run id `20260420T215817Z`
- run directory `.tnh-conductor/runs/20260420T215817Z`
- managed worktree `.tnh-conductor/worktrees/20260420T215817Z`

Task:

- implement `tnh-conductor status --watch`
- add a configurable polling interval
- emit machine-readable JSON snapshots until a terminal lifecycle state
- preserve existing one-shot behavior

## Result

All five arms produced viable implementation work on the same feature.

The strongest practical result is not that one arm alone dominated. It is that the comparison now cleanly separates three different kinds of value:

- direct Codex is still the cleanest baseline for bounded coding work
- existing agent-orch has the strongest control surface and artifact model
- explicit external worker CLIs are promising as a repo-native interface, but current environment and auth friction make them less reliable than the other two paths

Native subagents remain credible, but this run did not show a clean native-subagent win because the intended forked-collaboration path failed and the supervisor had to recover locally.

So the current recommendation is:

- keep direct Codex as the baseline for simple bounded work
- keep `tnh-conductor` as the main path to invest in for controlled orchestration
- keep the external assistant CLIs as experimental worker interfaces, not primary coordination defaults
- treat future `tnh-gen` work as a separate review or evaluator layer rather than conflating it with the current orchestrator

## Arm A: Direct Codex

Outcome:

- completed cleanly
- changed 2 files
- targeted validation passed

Worktree:

- `tmp/spike-10/20260420T215652Z/worktrees/direct`

Artifacts:

- `tmp/spike-10/20260420T215652Z/captures/direct/supervisor.stdout.jsonl`
- `tmp/spike-10/20260420T215652Z/captures/direct/supervisor.stderr.log`

Validation:

- `poetry install --with local`
- `poetry run pytest tests/cli_tools/test_tnh_conductor.py`
- result observed in run trace: `6 passed in 2.37s`

Practical read:

- this was the lowest-overhead path
- failures were ordinary local implementation/test issues rather than orchestration issues
- it remains the right baseline any coordination layer needs to justify beating

## Arm B: Native Codex Subagents

Outcome:

- completed with a useful implementation
- changed 2 files
- targeted validation passed

Worktree:

- `tmp/spike-10/20260420T215652Z/worktrees/native-subagent`

Artifacts:

- `tmp/spike-10/20260420T215652Z/captures/native-subagent/supervisor.stdout.jsonl`
- `tmp/spike-10/20260420T215652Z/captures/native-subagent/supervisor.stderr.log`

Validation:

- `poetry install --with local`
- `poetry run pytest tests/cli_tools/test_tnh_conductor.py`
- result observed in run trace: `6 passed in 2.02s`

Observed weakness:

- intended native collaboration failed twice with `parent thread rollout unavailable for fork`

Practical read:

- this arm still supports the view that native subagents are viable
- but this run does not support treating them as the default coordination path yet
- the biggest issue was not output quality, it was delegation reliability

## Arm C: Explicit External Codex Worker

Outcome:

- completed with a useful implementation
- changed 2 files
- targeted validation passed
- explicit `codex-assistant` path was exercised, but the worker did not complete successfully

Worktree:

- `tmp/spike-10/20260420T215652Z/worktrees/external-codex`

Artifacts:

- `tmp/spike-10/20260420T215652Z/captures/external-codex/supervisor.stdout.jsonl`
- `tmp/spike-10/20260420T215652Z/captures/external-codex/supervisor.stderr.log`
- `tmp/codex-assistant/worker-status-watch.stdout.jsonl`
- `tmp/codex-assistant/worker-status-watch.stderr.log`

Validation:

- `poetry install --with local`
- `poetry run pytest tests/cli_tools/test_tnh_conductor.py`
- final worktree validation result: `7 passed`

Observed weaknesses:

- worker startup depended on local package install
- Codex worker then hit `~/.codex` session-write restrictions
- the supervisor still had to recover locally to finish the task

Practical read:

- the checked-in `codex-assistant` wrapper is useful as an explicit delegation seam
- the process boundary did improve failure visibility
- but right now the external Codex path is operationally more fragile than direct execution or `tnh-conductor`

## Arm D: Explicit External Claude Worker

Outcome:

- completed with a useful implementation
- changed 2 files
- targeted validation passed
- explicit `claude-assistant` path was exercised, but the worker did not complete successfully

Worktree:

- `tmp/spike-10/20260420T215652Z/worktrees/external-claude`

Artifacts:

- `tmp/spike-10/20260420T215652Z/captures/external-claude/supervisor.stdout.jsonl`
- `tmp/spike-10/20260420T215652Z/captures/external-claude/supervisor.stderr.log`
- `tmp/spike-10/20260420T215652Z/worktrees/external-claude/tmp/claude-assistant/20260420T220039Z.stdout.jsonl`
- `tmp/spike-10/20260420T215652Z/worktrees/external-claude/tmp/claude-assistant/20260420T220039Z.stderr.log`

Validation:

- `poetry install --with local`
- `poetry run pytest tests/cli_tools/test_tnh_conductor.py`
- result observed in run trace: `6 passed in 2.24s`

Observed weaknesses:

- first launch failed before the worktree environment was installed
- launch shape needed clarification because `claude-assistant` is effectively a single-command CLI
- worker then hit `~/.claude` write restrictions
- after redirecting `HOME`, the worker still failed on local Claude authentication

Practical read:

- this arm was valuable mainly because it exposed real wrapper and auth constraints
- the CLI is a valid repo-native seam
- but external Claude is not yet a dependable unattended worker path in this environment

## Arm E: Existing Agent-Orch

Outcome:

- completed successfully through the maintained workflow
- changed 2 files
- implementation and validation artifacts were persisted canonically

Managed worktree:

- `.tnh-conductor/worktrees/20260420T215817Z`

Run artifacts:

- `.tnh-conductor/runs/20260420T215817Z/status.json`
- `.tnh-conductor/runs/20260420T215817Z/metadata.json`
- `.tnh-conductor/runs/20260420T215817Z/events.ndjson`
- `.tnh-conductor/runs/20260420T215817Z/artifacts/implement/final_response.txt`
- `.tnh-conductor/runs/20260420T215817Z/artifacts/validate/validation_stdout.txt`

Validation:

- implementation step reported `poetry run pytest tests/cli_tools/test_tnh_conductor.py`
- observed result in final response: `6 passed`
- maintained validation step then ran the bootstrap `tests` validator
- observed result in validation artifact: `535 passed, 2 skipped, 10 warnings`

Practical read:

- this arm had the best control surface and the clearest artifact model
- status, events, route transitions, workspace diff, final response, and validation output all landed in predictable canonical locations
- the main weakness was coarser live visibility and higher operator inspection cost than the direct arm

Most important distinction:

- unlike the other arms, this path already gives TNH Scholar a repo-owned orchestration boundary with managed worktree, workflow routing, validation, and canonical artifacts
- that is why it still looks like the strongest long-term coordination substrate

## Comparison Summary

Direct Codex was best on simplicity.

- least overhead
- cleanest path to a passing result
- easiest to reason about during execution

Native subagents were best on potential upside, but not on demonstrated reliability.

- real delegation intent was present
- the supervisor recovered sensibly
- native fork reliability is still not good enough to lean on without caveats

Explicit external worker CLIs were best on process-boundary clarity, but weakest on operational readiness.

- failures were easier to capture and inspect
- `codex-assistant` and `claude-assistant` now give us stable repo-native seams
- both paths were blocked by real environment or auth issues before the delegated worker could carry the task end to end

Existing agent-orch was best on control surface.

- canonical run directory
- managed worktree
- event stream
- artifact persistence
- validation routing

That is the main reason to keep investing in it even though the direct arm remains cleaner on a small task.

### Follow-up code comparison:

- the direct arm and the `tnh-conductor` implementation arm both used the same Codex CLI execution family (`codex exec --ephemeral`)
- the code quality of the direct arm had minor but noticeable quality edges in implementation. 
- the small code-quality edge for the direct arm therefore looks more like a prompt and entrypoint-context difference than a runner-surface difference
- in practice, that points to workflow prompt packaging and worker context as the next hardening opportunity for `tnh-conductor`

## What This Says About `tnh-gen`

This comparison should not be read as evidence against using `tnh-gen`.

It says something narrower:

- current maintained orchestrator value comes from workflow, artifacts, and controlled execution
- `tnh-gen` is still untested in the live evaluator role because that seam is not yet wired
- when `tnh-gen` is introduced, it should be compared as a reviewer or process evaluator, not as a synonym for the current conductor arm

## Practical Conclusion

If TNH Scholar needs one primary forward path for agent coordination right now, keep the existing agent-orch code and continue hardening `tnh-conductor`.

That path already owns the most important surfaces:

- workflow definition
- managed workspace lifecycle
- route control
- validation execution
- canonical artifacts

Direct Codex should remain the baseline and fallback for bounded work because it is still the cleanest way to get code written quickly.

Native subagents are worth continuing to test, but as an augmentation inside the Codex baseline rather than as a replacement for the orchestrator.

Explicit external `codex-assistant` and `claude-assistant` workers are worth keeping because they create a useful explicit worker interface. But they should still be treated as experimental until environment bootstrapping, home-state isolation, and model authentication are made dependable.

## Next Actions

1. Keep `tnh-conductor` as the main coordination path under active development.
2. Add a targeted maintained validator route for conductor comparison tasks so the validation scope matches the task brief instead of defaulting to the whole test suite.
3. Harden native subagent launch reliability before treating native delegation as a dependable default.
4. Harden assistant-worker runtime setup so `codex-assistant` and `claude-assistant` can run in fresh worktrees without manual environment or auth recovery.
5. Add a separate follow-on spike for `tnh-gen` as a review or evaluator artifact producer rather than folding it into the current orchestrator comparison.

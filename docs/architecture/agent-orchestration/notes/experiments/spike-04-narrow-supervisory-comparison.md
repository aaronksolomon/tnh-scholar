---
title: "SPIKE-04 Narrow Supervisory Comparison"
description: "Lightweight comparison note between a direct single-agent pass and the existing supervisory shell run on the same bounded OA01.x design-review task."
owner: ""
author: "Codex"
status: current
created: "2026-04-15"
updated: "2026-04-15"
---

# SPIKE-04 Narrow Supervisory Comparison

SPIKE-04 compares a direct single-agent pass against the existing supervisory shell run on the same bounded OA01.x design-review task.

## Experiment ID

`SPIKE-04`

## Question

Does a tightly bounded supervisor using native subagents produce a meaningfully better result than a direct single-agent pass on the same task?

## Setup

Task basis:

- `docs/architecture/agent-orchestration/supervisory-shell-trial/current-supervisory-task-brief.md`

Arm A:

- direct single-agent run
- artifact: `tmp/spike-04-direct-stdout.jsonl`
- stderr: `tmp/spike-04-direct-stderr.log`

Arm B:

- existing shell-launched supervisory run
- artifact: `tmp/supervisory-shell-trial-stdout.jsonl`
- stderr: `tmp/supervisory-shell-trial-stderr.log`

Comparison lens:

- usefulness of findings
- distinctness of decomposition
- added value versus overhead
- operational reliability

## Result

The supervisory arm produced the more useful result, but not cleanly enough yet to count as an endorsed default workflow.

Why the supervisory arm was stronger:

- it produced three distinct critique workstreams
- the workstreams converged on a tighter set of structural issues
- the final synthesis was sharper about pruning and next experiment shape
- it surfaced one important capability constraint directly: inherited fork-context spawning was not dependable in that launch mode

Why the direct arm still matters:

- it was simpler
- it completed cleanly
- it produced a competent high-level critique without coordination overhead
- it did not depend on any subagent behavior

Practical judgment:

- direct single-agent use is the cleaner baseline
- supervisory use has higher upside
- current supervisory value depends on explicit-context delegation rather than trusting inherited context

## Useful Artifacts

- `tmp/spike-04-direct-stdout.jsonl` shows a clean direct critique with no `collab_tool_call` events
- `tmp/supervisory-shell-trial-stdout.jsonl` shows real delegated workstreams and a stronger synthesis
- `tmp/supervisory-shell-trial-stderr.log` captures the main supervisory reliability issue: parent-rollout fork-context failure during the first spawn strategy

## Comparison Summary

Direct arm strengths:

- simpler and more reliable
- no subagent failure mode
- adequate output quality for a bounded design review

Direct arm weaknesses:

- less evidence of differentiated exploration
- less pressure-testing from multiple angles
- weaker signal about whether supervision itself adds value

Supervisory arm strengths:

- better decomposition
- stronger convergence on pruning moves
- more informative next-experiment recommendation
- direct evidence about native subagent constraints

Supervisory arm weaknesses:

- higher overhead
- failed initial spawn strategy
- dependence on explicit repo/task context in delegated prompts

## Conclusion

The current evidence favors continuing supervisory experimentation, but only in a very bounded form.

The supervisory path has enough upside to keep testing because it produced a better result than the direct pass on this task. But it is not yet clean or robust enough to replace direct-agent workflow as the default.

## Next Action

Proceed to `SPIKE-05` and formalize the minimum artifact bundle needed for a useful comparison run.

For future supervisory runs:

- use the direct path as baseline
- keep the supervisor to at most two subagent calls
- prefer explicit-context subagent prompts
- and judge value against one narrow task rather than broad exploratory work

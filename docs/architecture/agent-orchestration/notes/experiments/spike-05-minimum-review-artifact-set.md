---
title: "SPIKE-05 Minimum Review Artifact Set"
description: "Lightweight result note defining the smallest artifact bundle that still made the OA01.x spike runs understandable and reviewable."
owner: ""
author: "Codex"
status: current
created: "2026-04-15"
updated: "2026-04-15"
---

# SPIKE-05 Minimum Review Artifact Set

SPIKE-05 defines the smallest artifact bundle that still let the completed OA01.x spike runs be understood and judged.

## Experiment ID

`SPIKE-05`

## Question

What is the smallest artifact bundle that still lets a human understand what happened and judge whether the run was useful?

## Setup

Evaluated against the artifact sets used in:

- `SPIKE-02`
- `SPIKE-03`
- `SPIKE-04`

Primary evidence files:

- `tmp/spike-04-direct-stdout.jsonl`
- `tmp/spike-04-direct-stderr.log`
- `tmp/supervisory-shell-trial-stdout.jsonl`
- `tmp/supervisory-shell-trial-stderr.log`
- `tmp/codex-wrapper-subagent-best-stdout.jsonl`

## Result

The minimum useful review bundle is:

1. input brief or task prompt
2. `stdout` JSONL event stream
3. `stderr` log
4. one short operator note
5. final extracted result or final agent message

This was enough to answer the practical questions that mattered:

- did the run complete
- were subagents actually used
- what failed
- what was the final outcome
- and was the run more useful than a simpler baseline

Artifacts that were helpful but not required for the current spike:

- richer manifests
- step-by-step summaries beyond the raw JSONL
- expanded provenance bundles
- broad scorecards

## Useful Artifacts

- the prompt or task brief was necessary to judge whether the result actually addressed the intended task
- `stdout` JSONL was necessary to confirm `spawn_agent`, `wait`, and final response behavior
- `stderr` was necessary to confirm the supervisory fork-context failure
- one short experiment note was necessary to turn raw artifacts into a usable human judgment record

## Recommended Minimal Bundle

For the current spike, keep:

- task brief or exact prompt text
- `stdout.jsonl`
- `stderr.log`
- one extracted final response
- one short result note in the six-field spike format

Do not add more structure unless a concrete comparison run fails because this bundle is insufficient.

## Next Action

Keep future spike runs on this minimal artifact contract unless a missing artifact prevents useful review.

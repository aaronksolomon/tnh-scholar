---
title: "OA01.x Spike Experiment Register"
description: "Minimal maintained experiment register for the current OA01.x spike, limited to headless execution patterns, native subagent viability, and low-overhead operator-facing artifacts."
owner: ""
author: "Codex"
status: current
created: "2026-04-14"
updated: "2026-04-14"
related_adrs:
  - "/docs/architecture/agent-orchestration/adr/adr-oa01.2-conceptual-spike-orientation-based-supervisory-orchestration.md"
  - "/docs/architecture/agent-orchestration/adr/adr-oa01.3-conceptual-spike-practical-approach.md"
  - "/docs/architecture/agent-orchestration/adr/adr-oa01.4-headless-agent-communication-functional-spike.md"
---

# OA01.x Spike Experiment Register

## Purpose

This is the maintained experiment register for the current `OA01.x` spike.

Scope is intentionally narrow:

- headless execution patterns,
- native subagent invocation viability,
- simple supervisory comparisons,
- and the minimum artifacts needed to run and review those experiments.

Out of scope for now:

- economics,
- broad topology programs,
- large benchmark programs,
- cross-provider portfolio planning,
- and long-horizon overnight scale architecture.

Cloud-generated strategy docs are preserved separately as experimental artifacts. They are not workflow authority.

## Lightweight Experiment Card

Each experiment note should record only:

1. experiment ID,
2. question,
3. setup,
4. result,
5. useful artifacts,
6. next action.

## Maintained Experiments

### `SPIKE-01` Headless Baseline

Question:

Can `codex exec` be used headlessly in a repeatable enough way to support simple collaborator-style exchanges?

Status:

- completed

Primary references:

- [Codex Headless Communication Report](/architecture/agent-orchestration/notes/experiments/codex-headless-communication-report.md)

### `SPIKE-02` Execution Context Comparison

Question:

Which execution context is the most reliable and least noisy for headless use?

Focus:

- direct user shell,
- agent-launched shell,
- wrapper path,
- repo-local config effects.

Status:

- in progress

### `SPIKE-03` Native Subagent Smoke Test

Question:

Can native subagent behavior be invoked, observed, and captured clearly enough in headless mode to support the spike?

Focus:

- spawn evidence,
- wait evidence,
- retained artifacts,
- explicit distinction between documented capability and observed behavior.

Status:

- partially completed

### `SPIKE-04` Narrow Supervisory Comparison

Question:

Does a tightly bounded supervisor plus at most two subagent calls produce a meaningfully better result than a direct single-agent pass on the same task?

Focus:

- same task,
- same files,
- same time budget,
- same output scorecard.

Status:

- next

### `SPIKE-05` Minimum Review Artifact Set

Question:

What is the smallest artifact bundle that still lets a human understand what happened and judge whether the run was useful?

Focus:

- final response,
- concise event evidence,
- prompt or task brief,
- stderr or failure evidence when relevant,
- one short operator summary.

Status:

- next

## Current Recommendation

Run these experiments sequentially and keep the documentation light.

The immediate goal is not to design a mature orchestration program. The immediate goal is to decide whether:

- headless agent communication is easy enough,
- native subagent use is viable enough,
- and a simple supervisory pattern is actually better than working directly within existing agent bounds.

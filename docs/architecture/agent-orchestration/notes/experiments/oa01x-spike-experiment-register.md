---
title: "OA01.x Spike Experiment Register"
description: "Minimal maintained experiment register for the current OA01.x spike, limited to headless execution patterns, native subagent viability, and low-overhead operator-facing artifacts."
owner: ""
author: "Codex"
status: current
created: "2026-04-14"
updated: "2026-04-16"
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

- completed

Primary references:

- [SPIKE-02 Execution Context Comparison](/architecture/agent-orchestration/notes/experiments/spike-02-execution-context-comparison.md)

### `SPIKE-03` Native Subagent Smoke Test

Question:

Can native subagent behavior be invoked, observed, and captured clearly enough in headless mode to support the spike?

Focus:

- spawn evidence,
- wait evidence,
- retained artifacts,
- explicit distinction between documented capability and observed behavior.

Status:

- completed

Primary references:

- [SPIKE-03 Native Subagent Smoke Test](/architecture/agent-orchestration/notes/experiments/spike-03-native-subagent-smoke-test.md)

### `SPIKE-04` Narrow Supervisory Comparison

Question:

Does a tightly bounded supervisor plus at most two subagent calls produce a meaningfully better result than a direct single-agent pass on the same task?

Focus:

- same task,
- same files,
- same time budget,
- same output scorecard.

Status:

- completed

Primary references:

- [SPIKE-04 Narrow Supervisory Comparison](/architecture/agent-orchestration/notes/experiments/spike-04-narrow-supervisory-comparison.md)

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

- completed

Primary references:

- [SPIKE-05 Minimum Review Artifact Set](/architecture/agent-orchestration/notes/experiments/spike-05-minimum-review-artifact-set.md)

### `SPIKE-06` Native Codex CLI Baseline

Question:

Does the standalone native Codex CLI support the baseline headless and kernel-mediated flows cleanly enough to proceed to the larger prompt-dir comparison?

Focus:

- native CLI version and help surface
- direct `codex exec` JSONL smoke test
- maintained runner/conductor tests
- no-edit `tnh-conductor` ACK workflow
- managed worktree cleanliness

Status:

- completed

Primary references:

- [SPIKE-06 Native Codex CLI Baseline](/architecture/agent-orchestration/notes/experiments/spike-06-native-codex-cli-baseline.md)

### `SPIKE-07` Codex Home State Dependency

Question:

What `HOME`-scoped Codex state is required for a successful scripted headless invocation, and which state only affects startup noise?

Focus:

- minimum viable `~/.codex` content
- config profile dependency
- auth dependency
- plugin cache dependency
- distinction between success-critical state and noise-inducing state

Status:

- completed

Primary references:

- [SPIKE-07 Codex Home State Dependency](/architecture/agent-orchestration/notes/experiments/spike-07-codex-home-state-dependency.md)

### `SPIKE-08` Launch Context Environment Contamination

Question:

When Codex launches another Codex process, is noisy startup behavior caused mainly by PTY shape or by inherited execution environment contamination?

Focus:

- PTY versus non-PTY launch comparison
- inherited environment versus curated user-like environment
- real Terminal.app user-shell baseline
- practical clean-launch policy for Codex-on-Codex runs

Status:

- completed

Primary references:

- [SPIKE-08 Launch Context Environment Contamination](/architecture/agent-orchestration/notes/experiments/spike-08-launch-context-env-contamination.md)

### `SPIKE-09` Prompt Dir Three-Arm Comparison

Question:

On the same bounded implementation task, how do direct Codex, supervisory Codex, and kernel-mediated orchestration compare in practical usefulness and behavior?

Focus:

- same task brief across all three arms
- same sanitized launch surface for shell-based Codex runs
- direct versus supervisor-with-subagents versus conductor-managed execution
- overlap, uniqueness, validation quality, and coordination overhead

Status:

- completed

Primary references:

- [SPIKE-09 Prompt Dir Three-Arm Comparison](/architecture/agent-orchestration/notes/experiments/spike-09-prompt-dir-three-arm-comparison.md)

## Current Recommendation

Run these experiments sequentially and keep the documentation light.

The immediate goal is not to design a mature orchestration program. The immediate goal is to decide whether:

- headless agent communication is easy enough,
- native subagent use is viable enough,
- a simple supervisory pattern is actually better than working directly within existing agent bounds,
- the scripted Codex launch surface is understood well enough to avoid chasing false shell-state explanations,
- and launched Codex runs should use a curated user-like environment rather than inherited parent agent environment.

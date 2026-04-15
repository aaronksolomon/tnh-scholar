---
title: "Codex Headless Communication Experiment Plan"
description: "Practical next-step experiment plan for Codex headless communication, incorporating research findings while explicitly bracketing premature directions."
owner: ""
author: "Codex"
status: current
created: "2026-04-12"
updated: "2026-04-14"
---

# Codex Headless Communication Experiment Plan

## Purpose

Define the next rounds of Codex headless communication experiments in a way that is practical, narrow, sequential, and grounded in the results already observed.

This plan takes useful inputs from:

- [Codex Headless Communication Report](/architecture/agent-orchestration/notes/experiments/codex-headless-communication-report.md)
- [Codex Headless Research Memo for Engineer Agents](/architecture/agent-orchestration/notes/research/codex-headless-research-memo-for-engineer-agents.md)
- [OA01.x Spike Experiment Register](/architecture/agent-orchestration/notes/experiments/oa01x-spike-experiment-register.md)

The research memo is treated as an input, not as a decision document.

The cloud-generated direction docs are preserved as experimental artifacts only. They are not maintained planning authority for the current spike.

## Current Baseline

The current best machine-oriented baseline is:

- use `codex exec` as the headless surface,
- use the authenticated default `~/.codex` home,
- use repo-local profile `collab`,
- use `--ephemeral`,
- separate `stdout` from `stderr`,
- and disable `plugins` plus `shell_snapshot` when the goal is a cleaner event channel.

This path is viable enough for further experiments, but it is not yet endorsed as the long-term operating mode.

## Current Scope

The current spike scope is narrower than a general orchestration program.

Active focus:

- headless execution patterns,
- native subagent invocation and evidence capture,
- simple supervisor vs direct-agent comparison,
- and minimal operator-facing artifacts.

Explicitly not active right now:

- economics,
- broad topology exploration,
- large benchmark programs,
- cross-provider portfolio design,
- and broad overnight scale architecture.

## Adopted Directions

### 1. Build a Documented-vs-Observed Matrix

Adopt the memo's suggestion to explicitly track:

- officially documented behavior,
- locally observed behavior,
- confidence,
- and follow-up experiments.

Reason:

This is useful discipline and keeps research from collapsing into opinion.

### 2. Continue User-Shell Mimic Experiments

Adopt direct comparison across execution contexts such as:

- direct user shell,
- agent-launched `zsh -lc`,
- repo-local wrapper script,
- and targeted working-directory or config changes.

Reason:

This is now clearly one of the highest-signal questions.

### 3. Keep Capability Checking in Any Automation Path

Adopt lightweight capability verification before assuming CLI flags or behavior.

Reason:

This is ordinary hygiene for an actively changing CLI surface.

### 4. Keep Experiments Narrow and Collaboration-Focused

Adopt the memo's bias toward narrow collaboration patterns and away from early broad autonomy experiments.

Reason:

This aligns with `OA01.4` and with the current stage of uncertainty.

### 5. Keep the Spike Decisive Rather Than Expansive

Adopt a narrow success question:

- is headless subagent work viable enough for TNH Scholar,
- or are existing direct agent workflows the better practical path for now?

Reason:

This is the real decision boundary for the current spike.

### 6. Prefer More Meaningful User-Shell Experiments Over More Noise Tuning

Adopt a bias toward user-shell supervisory experiments before doing much more local wrapper optimization.

Reason:

The main unknown is no longer whether Codex can be called. The main unknown is whether native collaborative behavior is genuinely useful for the direction now being explored.

## On Hold

### 1. Isolated-but-Authenticated Execution

This remains interesting, but it is on hold rather than the immediate next move.

Reason:

- it may matter later for reproducibility,
- but the current path is already viable,
- and the project does not yet need a cleaner isolated home badly enough to make this the top priority.

### 2. Broader Collaboration-Mode Taxonomy

The memo's breakdown of guidance-layer, process-layer, and supervisory collaboration is useful conceptually, but it is on hold for planning purposes.

Reason:

It adds conceptual structure faster than current experiments require.

### 3. Safety-Model Redesign

Questions about dangerous mode, custom safety gating, or stronger external permission models are on hold.

Reason:

The project still needs better understanding of the normal execution path before reasoning about stronger or more permissive modes.

## Rejected for Now

### 1. Broad New Orchestration or Collaboration Infrastructure

Rejected for this phase.

Reason:

The communication path is already viable enough to support further learning without more system buildout.

### 2. Treating the Research Memo's Recommendations as Directional Decisions

Rejected.

Reason:

The memo contains useful research, but its recommendations are not sufficiently grounded in the repo's full context to serve as planning authority.

### 3. Requiring Clean Isolated State Before Continuing

Rejected.

Reason:

This would block useful experimentation unnecessarily. The current authenticated path is noisy but workable.

## Next Experiments

The next rounds should stay sequential and small.

### Experiment 1. Baseline Establishment

Status:

- completed

What it covered:

- headless reachability
- stream separation
- real review usefulness
- user-shell cleanliness
- wrapper usefulness
- repo-local config viability
- native subagent availability
- first noise-reduction levers

Primary output:

- [Codex Headless Communication Report](/architecture/agent-orchestration/notes/experiments/codex-headless-communication-report.md)

### Experiment 2. Surface-Cost Comparison

Goal:

Understand the likely cost of suppressing noisy surfaces before treating the lower-noise path as a design win.

Sub-experiments:

#### 2.1 Plugins Cost

Compare one small but meaningful task under:

- baseline path
- `--disable plugins`

Question:

- what useful behavior, if any, disappears when plugins are disabled?

#### 2.2 Shell Snapshot Cost

Compare one small but meaningful task under:

- baseline path
- `--disable shell_snapshot`

Question:

- does disabling shell snapshots reduce useful environment/context behavior, or only suppress noise?

#### 2.3 Persistence / State Cost

Observe whether the persistent state warning appears correlated with any degraded useful behavior during a slightly longer task.

Question:

- is the state DB issue merely noisy, or operationally relevant?

### Experiment 3. User-Shell Supervisory Trial

Goal:

Run a more meaningful Codex session from the user's shell, with explicit permission to use native subagents, and see how far the native collaboration surface goes before custom orchestration is introduced.

Shape:

- launch from the user's shell
- provide a clear supervisory objective
- allow native subagent use
- include stop conditions and output expectations

Questions:

- does the supervisory mode feel meaningfully stronger than thin wrapper-led task execution?
- what native coordination behavior appears without additional structure?
- what artifacts are actually useful for human review afterward?

Status:

- first round completed

What was learned:

- the supervisor did produce useful delegated work and a stronger synthesis than a likely straight-line pass
- the initial inherited subagent spawn mode failed with a parent-rollout fork error
- explicit-context retry worked
- the result suggests promise, but not a clean workflow yet

Immediate implication:

- the next comparison should not assume inherited subagent context is dependable
- and the next design-review comparison should be narrower and more controlled

### Experiment 4. Paired Design-Review Comparison

Goal:

Test the real question more cleanly: does supervised native collaboration beat a direct single-agent pass on the same review task?

Shape:

- same day
- same file set
- same brief
- same time budget
- same output scorecard

Arms:

- Arm A: one direct `codex exec` design-review pass
- Arm B: one shell-launched supervisor with at most 2 subagent calls

Constraint:

- use one orientation only: `Design Review`
- do not widen into broader runner or architecture work during the trial
- use explicit subagent context if inherited context remains unreliable
### Experiment 5. Thin Launcher Refinement

Goal:

Only after the paired comparison, decide whether the wrapper should become a slightly more intentional launcher surface for future orchestration agents.

Possible additions:

- `--prompt-file`
- stable output-path conventions
- optional event filtering

Constraint:

- keep this thin
- do not build a larger orchestration substrate yet

## Working Principle

The project should continue to optimize for rapid learning through small experiments, not for premature system design.

The next meaningful question is not "can Codex be launched?" That has already been answered. The next meaningful question is whether a user-launched supervisory Codex session, using native collaboration features, is good enough to inform the emerging collaboration-oriented direction before more local tooling is built.

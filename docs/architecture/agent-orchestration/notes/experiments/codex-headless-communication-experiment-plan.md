---
title: "Codex Headless Communication Experiment Plan"
description: "Practical next-step experiment plan for Codex headless communication, incorporating research findings while explicitly bracketing premature directions."
owner: ""
author: "Codex"
status: current
created: "2026-04-12"
updated: "2026-04-12"
---

# Codex Headless Communication Experiment Plan

## Purpose

Define the next round of Codex headless communication experiments in a way that is practical, narrow, and grounded in the results already observed.

This plan takes useful inputs from:

- [Codex Headless Communication Report](/architecture/agent-orchestration/notes/experiments/codex-headless-communication-report.md)
- [Codex Headless Research Memo for Engineer Agents](/architecture/agent-orchestration/notes/research/codex-headless-research-memo-for-engineer-agents.md)

The research memo is treated as an input, not as a decision document.

## Current Baseline

The current working baseline is:

- use `codex exec` as the headless surface,
- use the authenticated default `~/.codex` home,
- use `--ephemeral`,
- and separate `stdout` from `stderr`.

This path is already viable enough for further experiments.

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

The next round should stay small.

### A. Context Comparison

Run the same simple prompt through:

- direct user shell,
- repo-local wrapper script from live agent execution,
- and any close user-shell variant available here.

Goal:

Identify which context differences actually matter for cleanliness and reliability.

### B. Real Task Small Review

Run one or two tiny real review or critique prompts with the established baseline path.

Goal:

Confirm that the viable path remains useful beyond `ACK`.

### C. Minimal Matrix Draft

Start a small documented-vs-observed matrix with only the most important rows:

- auth,
- persistence,
- config,
- working directory,
- `AGENTS.md`,
- and shell context.

Goal:

Create a disciplined reference without turning it into a large artifact.

## Working Principle

The project should continue to optimize for rapid learning through small experiments, not for premature system design.

The immediate task is to understand the real communication path well enough to keep collaborating with Codex headlessly in a controlled and repeatable way.

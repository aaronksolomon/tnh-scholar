---
title: "SPIKE-10 Agent Coordination Comparison Plan"
description: "Next comparison plan covering native Codex delegation, explicit external workers, Claude worker invocation, and tnh-gen review/process roles."
owner: ""
author: "Codex"
status: current
created: "2026-04-20"
updated: "2026-04-20"
---

# SPIKE-10 Agent Coordination Comparison Plan

## Experiment ID

`SPIKE-10`

## Question

For agent coordination inside TNH Scholar, which execution shape looks like the most viable forward path once we compare:

- direct single-agent Codex
- Codex with native subagents
- existing agent-orch through `tnh-conductor`
- Codex supervising explicit external Codex workers
- Codex supervising explicit external Claude workers
- a future `tnh-gen`-backed review/process evaluator

## Why This Is Next

SPIKE-09 already showed that:

- direct Codex is the cleanest baseline on small bounded tasks
- native Codex subagents are real and usable
- the maintained kernel path is viable enough to keep

What remains unclear is where the best coordination seam lives:

- native Codex delegation inside one runtime
- the existing explicit workflow/runtime boundary in agent-orch
- explicit worker-to-worker subprocess delegation
- or a mixed model where reviewer/process agents stay outside the coding runtime

## Comparison Arms

### Arm A: Direct Codex Baseline

Purpose:

- preserve the low-overhead baseline
- measure what any coordination layer must beat or justify

### Arm B: Native Codex Subagents

Purpose:

- measure the best-case native in-process delegation path
- focus on spawn reliability, return-path clarity, and synthesis quality

### Arm C: Explicit External Codex Workers

Mechanism:

- parent Codex invokes `codex-assistant`

Purpose:

- compare explicit process boundaries against native subagents
- test whether artifact capture and failure isolation improve enough to justify the extra overhead

### Arm D: Existing Agent-Orch

Mechanism:

- maintained `tnh-conductor` / current agent-orchestration runtime

Purpose:

- compare the existing repo-controlled orchestration surface against both native subagents and ad hoc explicit worker delegation
- measure whether the current kernel, worktree management, and canonical artifact model already justify keeping agent-orch as the main coordination substrate

Important current limitation:

- this arm currently exercises `RUN_AGENT`, `RUN_VALIDATION`, rollback, and artifact capture
- it does not yet exercise a live semantic evaluator through `tnh-gen`

### Arm E: Explicit External Claude Workers

Mechanism:

- parent Codex invokes `claude-assistant`

Purpose:

- test whether cross-model delegated execution adds useful perspective
- compare Claude as a bounded external worker against Codex-as-worker on the same task

### Arm F: Future `tnh-gen` Review Or Process Evaluator

Purpose:

- keep `tnh-gen` out of the coder role
- test it as a structured reviewer, evaluator, or process-step agent

Recommended use:

- review a proposed diff
- classify failure modes
- generate a structured process recommendation
- emit a compact judgment artifact for human or supervisor use

Current status:

- planned only
- this is not currently wired into maintained agent-orch code
- comparison notes must keep this separate from the existing `tnh-conductor` arm

## Task Shape

Use one task that is:

- real repo work
- moderately decomposable
- larger than the prompt-dir flag task
- small enough to inspect without a multi-day run

Good candidate shapes:

- bounded refactor plus tests
- implementation plus docs plus validation split
- bug fix plus regression test plus review memo

Avoid:

- tiny one-file tasks that unfairly favor the direct arm
- huge ambiguous tasks where failure analysis becomes noisy

## Measurements

For every arm, capture:

- elapsed wall time
- changed file set
- targeted validation result
- stop behavior
- artifact clarity
- supervisor effort required to understand the run
- final synthesis usefulness

Specific coordination metrics:

- delegation success rate
- number of retries or restarts
- worker failure isolation quality
- merge or handoff friction
- review signal quality from non-coder agents
- current maintained control-surface depth versus operational friction

## Working Hypotheses

Current best hypotheses:

- native Codex subagents may stay best when the task is tightly coupled and the parent needs fast iteration
- the existing agent-orch runtime may remain the best long-term control surface because it owns workflow, workspace, rollback, and canonical artifacts in repo-native code
- explicit external workers may be better when artifact capture, fault isolation, or role separation matters more than speed
- Claude is more likely to add value as an alternate implementation or review worker than as the primary supervisor
- `tnh-gen` is more likely to be valuable as a structured reviewer/process evaluator than as another general-purpose coder

## Immediate Follow-Through

1. Add and validate a minimal `claude-assistant` CLI so Codex can launch Claude workers through the same explicit-worker pattern already available for Codex.
2. Run a five-arm comparison on one moderately decomposable repo task: direct Codex, native Codex subagents, existing agent-orch, explicit external Codex workers, and explicit external Claude workers.
3. Record the `tnh-conductor` arm separately from any future `tnh-gen` evaluator work so current control-surface value is judged on what actually exists.
4. Treat future `tnh-gen` output as a review artifact, not just conversational prose, so it can later be compared cleanly with the other arms.
5. Use the result to decide whether the next OA01.x effort should emphasize the existing agent-orch runtime, native subagents, explicit worker wrappers, or reviewer-process layering.

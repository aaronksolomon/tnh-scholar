---
title: "Agent Orchestration Recursive Bootstrap Proposal"
description: "Working draft for release framing of tnh-conductor and the post-bootstrap build sequence toward long-horizon multi-agent engineering."
owner: ""
author: "Codex"
status: draft
created: "2026-04-24"
updated: "2026-04-24"
---
# Agent Orchestration Recursive Bootstrap Proposal

This proposal frames the bootstrap release and sketches the next recursive build sequence toward longer-horizon multi-agent engineering work.

## Purpose

This working note has two jobs:

1. clarify how the current `tnh-conductor` release should be described to users, and
2. sketch the next recursive build sequence after the bootstrap release milestone.

This is intentionally high level. It is a sequencing memo, not an ADR.

## Current Read Of The System

The current maintained path is real, but narrow.

What exists now:

- a maintained headless entry point via `/docs/cli-reference/tnh-conductor.md`
- a managed worktree execution boundary
- canonical run artifacts, manifests, and status polling
- maintained Codex and Claude runner paths
- deterministic validation support
- bootstrap-proof workflow and operator notes

What does not yet exist in the maintained path:

- a real maintained `EVALUATE` capability
- a maintained `GATE` capability
- a bounded revision loop that is actually live in the bootstrap entry
- task parameterization and prompt-library execution at the maintained operator surface
- commit, push, PR, and merge progression as a maintained end-to-end path
- multi-agent mutable collaboration inside one run

That means the next release should be presented as a **bootstrap orchestration release**, not as an autonomous coding system and not yet as a full prompt-program runtime.

## Recommended Release Framing For `tnh-conductor`

The release docs should present `tnh-conductor` as:

- the maintained experimental entry point for bounded repository workflows
- the first operational bootstrap path for headless agent orchestration
- a worktree-isolated, artifact-first execution runner
- a platform for proving useful end-to-end repo tasks under supervision

The release docs should explicitly avoid implying:

- open-ended autonomy
- unattended long-horizon engineering
- self-directed planning across arbitrary tasks
- safe merge-to-main automation
- stable multi-agent collaboration

Recommended operator claim:

> `tnh-conductor` is the maintained experimental bootstrap runner for bounded, reviewable, worktree-isolated agent workflows in TNH Scholar.

Recommended current-state promise:

- one workflow
- one managed worktree
- one reviewable result
- canonical evidence
- human-governed promotion afterward

## Why The Next Phase Should Be Recursive

Bootstrap is only valuable if it becomes a tool for building the next version of the system.

The immediate post-release direction should therefore be:

- use `tnh-conductor` to work on agent-orchestration tasks first
- strengthen the orchestration system in the order that most increases autonomous useful work
- keep each new capability usable by the system itself as soon as it lands

The practical standard is:

Each new orchestration feature should either:

- increase the amount of useful work one run can complete,
- increase the reliability of that work,
- or increase the system's ability to improve its own prompts, workflows, evaluators, tooling, and runtime.

## North Star

The long-term target is not just “run agents longer.”

The target is a supervised system that can carry a repository task through:

- design
- planning
- implementation
- refinement
- testing
- check-in
- PR creation
- review response
- merge-ready completion

while producing artifacts, evidence, and branch state that a human maintainer can trust and continue.

The key qualifier is that this should become possible for **long-sequence collaborative work**, not only for single-pass implementation.

## Sequencing Principles

The next build sequence should follow these rules:

### 1. Strengthen the loop before widening the surface

The first priority is not more commands. It is a stronger end-to-end correction loop.

### 2. Prefer maintained vertical slices over abstract completeness

A thin real path is more valuable than a broader unexercised contract surface.

### 3. Put semantic control into maintained `EVALUATE`

The system will not become self-improving until review, validation, and revision can drive the next step through a maintained evaluator contract.

### 4. Treat tools as first-class runtime dependencies

Codex, Claude, and `tnh-gen` are not incidental integrations. Their invocation reliability, artifact capture, and behavioral contracts are core product scope.

### 5. Build self-use quickly

As soon as a capability is good enough, use the system to improve that same capability.

### 6. Keep merge authority human-only until the evidence says otherwise

Commit/push/PR automation can arrive before merge automation. Human merge authority should remain the stable safety line for now.

## Capability Ladder

The most useful high-level sequence looks like this.

### Phase 0: Release The Bootstrap Runner Cleanly

Objective:
Ship the current `0.4.0` milestone with honest docs and a clear experimental boundary.

Primary tasks:

- tighten `/docs/cli-reference/tnh-conductor.md` so “experimental bootstrap runner” is explicit
- expand `/docs/development/tnh-conductor-operator-guide.md` with current limitations, operator expectations, and review obligations
- document the maintained supported subset versus the architectural target
- publish one or two canonical example workflows that demonstrate the real supported path
- define what counts as a successful bootstrap run in release notes

Release outcome:
Users understand what the tool is for now, what it is not for yet, and how to interpret results.

### Phase 1: Turn Review Into A Real Control Signal

Objective:
Move from one-pass execution to one bounded refinement loop.

Primary tasks:

- implement a maintained evaluator path aligned with `/docs/architecture/agent-orchestration/adr/adr-oa06-planner-evaluator-contract.md`
- land the first maintained review-to-revision loop described in `/docs/architecture/agent-orchestration/adr/adr-oa06.1-evaluator-directed-revision-loop.md`
- normalize evaluator inputs from canonical artifacts rather than ad hoc transcript parsing
- persist evaluator decisions, fix instructions, blockers, and risk flags as first-class artifacts
- expose loop state in `status` output so operators can see whether refinement budget has been spent

Why this comes first:
Without evaluator-directed correction, the system is still mostly a bounded launcher.

### Phase 2: Make Tasking Generic Enough To Reuse

Objective:
Stop hardcoding task specificity into workflow bodies.

Primary tasks:

- introduce a maintained task-brief and task-parameter contract
- add prompt rendering and prompt reference resolution for maintained workflows
- move from static inline prompt text toward the OA05 prompt-library direction
- define a stable handoff package for implementation, review, and refinement steps
- make workflow reuse practical across multiple orchestration improvement tasks

Why this matters:
Recursive self-improvement requires reusable workflow templates, not one-off bootstrap proofs.

### Phase 3: Harden The Tool Substrate

Objective:
Make agent runs and generated validation trustworthy enough for repeated unattended segments.

Primary tasks:

- improve Codex and Claude adapter reliability around permissions, stalled writes, timeouts, transcript capture, and termination mapping
- strengthen `tnh-gen` generic execution as a first-class fallback or specialized worker path
- formalize capability profiles for each executor: implementation, review, synthesis, evaluator, harness generation
- add runner-level regression suites using canonical artifact assertions
- add smoke workflows that continuously verify the maintained orchestration stack itself

Why this matters:
A recursive system must trust its own execution substrate before it can safely lean on it for self-modification.

### Phase 4: Add Commit And PR Progression

Objective:
Let successful runs advance work into normal repository review flow.

Primary tasks:

- create a maintained commit step or bounded post-run promotion path
- add branch publication and PR creation/update support within the OA07 authority envelope
- capture PR metadata and review feedback as canonical run artifacts
- preserve protected-branch human-only merge
- support “run produced a reviewable branch and PR” as a first-class successful terminal outcome

Why this matters:
This is the point where the system stops producing isolated worktree artifacts and starts producing review-ready engineering work products.

### Phase 5: Close The Review Feedback Loop

Objective:
Make PR review and requested changes part of the maintained recursive cycle.

Primary tasks:

- ingest review comments and requested changes into typed evidence packages
- route review findings through maintained evaluation and refinement
- distinguish between mechanical failures, reviewer requests, and design disagreements
- support bounded “respond to review and revalidate” workflows
- build artifact summaries that let a human quickly inspect what changed between revision rounds

Why this matters:
The system starts becoming genuinely collaborative when external critique can drive another structured pass.

### Phase 6: Support Multi-Agent Collaboration Inside One Run

Objective:
Move from single-worker runs to supervised multi-role collaboration.

Primary tasks:

- define role-specialized worker patterns: planner, implementer, reviewer, synthesizer, harness generator
- add typed handoff contracts between agent steps
- decide whether collaboration is sequential first, parallel first, or mixed by workflow policy
- keep mutable write boundaries explicit to avoid workspace contention
- add artifact views that make agent-to-agent causality intelligible

Initial bias:
Start with sequential or lightly parallel collaboration. Avoid shared-write concurrency before evidence says it is worth the complexity.

### Phase 7: Move Toward Long-Horizon Runs

Objective:
Increase endurance from bounded bootstrap tasks to multi-hour engineering sequences.

Primary tasks:

- improve resumability and recovery around partial failure
- add stronger run monitoring and intervention hooks
- support richer evaluator memory windows and progress accounting
- define “net forward progress” metrics so the system can detect spinning
- add budgets for time, refinement count, and branch complexity

Why this matters:
Long-horizon autonomy is mostly a control-loop and recovery problem, not only an agent-quality problem.

## Recursive Self-Improvement Track

The orchestration system should begin working on itself in a disciplined order.

Recommended self-work sequence:

1. use bootstrap workflows to improve user docs and operator docs
2. use those workflows to improve workflow definitions and task-brief conventions
3. use the improved workflow system to build evaluator inputs and outputs
4. use the evaluator loop to improve runner reliability and validation harnesses
5. use the stronger loop to automate commit/PR progression
6. use PR-based runs to refine review-response workflows
7. only then push harder into multi-agent collaboration and longer unattended sequences

This creates a compounding ladder:

- better docs improve operator correctness
- better workflows improve repeatability
- better evaluators improve correction
- better runners improve reliability
- better PR handling improves integration with real development flow
- better review-response loops improve real-world usefulness

## Highest-Leverage Near-Term Design And Build Tasks

If the goal is “add the most needed functionality first,” the near-term queue should probably be:

1. Maintained `EVALUATE` implementation with deterministic fixtures and artifact contracts.
2. One bounded evaluator-directed refinement workflow in the maintained entry path.
3. Maintained prompt/task rendering contract so workflows become reusable.
4. Runner hardening for Codex and Claude permission and transcript edge cases.
5. Generic validation profile strategy for narrow orchestration tasks.
6. Commit plus PR creation/update path with canonical evidence capture.
7. Review-ingestion and requested-change refinement loop.

That order improves the system's actual working loop before expanding the ambition of the workflow surface.

## Tooling Priorities

The current tool stack is:

- Codex assistant
- Claude assistant
- `tnh-gen` generic model executor

The next tooling work should focus on:

- making each tool legible to the orchestrator through typed capability descriptions
- giving each tool a clear preferred role in workflows
- making fallback routing explicit rather than ad hoc
- ensuring artifact capture is equally strong across tools
- validating that tools behave well under repo-local, headless, policy-constrained execution

One useful medium-term outcome would be a simple capability matrix such as:

- Codex: implementation-heavy edits, repo-native coding, bounded review
- Claude: synthesis, critique, longer-form review, evaluator support
- `tnh-gen`: generic planner/evaluator/harness worker where a direct assistant binding is not required

## What To Defer

The following items should remain deferred until the stronger loop exists:

- merge automation to protected branches
- open-ended autonomous task discovery
- stacked PR orchestration as a default path
- rich rollback semantics beyond the current worktree reset model
- shared-write multi-agent concurrency in one mutable workspace
- broad control-plane expansion without a maintained use case

## Suggested Follow-On Docs

After this working note, the most useful follow-on documents would be:

- a short release-framing addendum for `/docs/cli-reference/tnh-conductor.md`
- a current-limitations section for `/docs/development/tnh-conductor-operator-guide.md`
- a focused design note for “maintained evaluator bootstrap sequence”
- a focused design note for “task brief and prompt rendering contract”
- a focused design note for “commit/push/PR progression boundary”

## Decision Heuristic

When choosing the next orchestration task, prefer work that answers:

Does this make the maintained system better at improving itself through a bounded, reviewable, evidence-backed workflow?

If yes, it is probably on-sequence.

If it mostly adds control surface without improving the loop, it is probably early.

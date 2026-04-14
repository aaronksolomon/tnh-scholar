---
title: "Bootstrap Direction Design Memo"
description: "Directional memo for agent orchestration design after the bootstrap threshold."
owner: ""
author: "aaronksolomon"
status: current
created: "2026-04-09"
updated: "2026-04-10"
---
# Design Memo: Re-centering Agent Orchestration on Bootstrap and Long-Horizon Useful Work

## Purpose

This memo clarifies the intended direction of the TNH Scholar agent orchestration platform. It is not an ADR. It does not lock a low-level implementation decision. Its purpose is to realign design and implementation work around the actual capability the system is meant to deliver.

The current platform has accumulated substantial execution substrate: typed contracts, workspace isolation, validation pathways, artifact recording, rollback primitives, and runtime boundary definitions. That work is useful. However, there is a meaningful risk that the platform drifts toward being primarily a control and safety layer around already-powerful agents rather than a system that materially increases what those agents can accomplish over time.

This memo states the directional correction.

## Core Direction

The orchestration platform must be judged by whether it enables agents to produce more useful, more coherent, and more durable engineering work than direct one-shot or short-session use of tools such as Codex CLI and Claude Code.

The immediate design priority is therefore:

**Achieve bootstrap.**

Bootstrap means the system can run a maintained end-to-end workflow through the real execution path and produce a useful engineering result in the repository using the maintained runtime, not a prototype path.

Once bootstrap exists, the system can begin to work on itself under direction. Before bootstrap, further architectural elaboration should be treated with skepticism unless it is directly required to make the bootstrap path real.

## Immediate Objective

The near-term objective is not full autonomy, multi-agent sophistication, or broad policy completeness.

The near-term objective is a thin, operational, maintained headless path that can:

1. start from a known repository state,
2. create an isolated managed work context,
3. invoke one or more real agents for planning and implementation,
4. run deterministic validation and test harnesses,
5. capture artifacts and evidence,
6. either stop with a reviewable result or roll back cleanly.

This is the threshold where the platform becomes testable as a product rather than only as infrastructure.

## Why Bootstrap Matters

Without bootstrap, the platform cannot demonstrate that it adds leverage.

Without bootstrap, additional work on orchestration architecture tends to improve boundaries, safety, and structure around a capability that does not yet exist in maintained form.

With bootstrap, the system can begin iterative self-improvement in a disciplined way:

- tightening prompts,
- refining workflow structure,
- improving evaluator behavior,
- strengthening validation harnesses,
- expanding agent collaboration patterns,
- and eventually helping build its own next version.

Bootstrap is therefore the hinge point between architecture preparation and operational usefulness.

## Long-Term Target Capability

The long-term goal is much more ambitious than a single-task runner or guarded wrapper around a frontier coding agent.

The target capability is:

A system that can sustain **multiple hours** of collaborative design, build, test, review, repair, and refinement in order to produce **large, connected, repository-native deliverables** of significant scope.

More concretely, the target is the ability to carry out work such as:

- designing a functional component of nontrivial architectural scope,
- generating and revising multiple connected modules,
- building subcomponents in coordination rather than as isolated files,
- producing integrated code on the order of **10k+ lines** when appropriate,
- using tests, harnesses, and structured evaluation throughout development rather than only at the end,
- invoking sub-agent review and critique during the process,
- iterating on both design and implementation as failures and insights arise,
- and leaving behind a coherent branch-ready deliverable suitable for human review and eventual merge.

This target should remain visible during present design decisions even though the immediate milestone is much smaller.

## Important Clarification

The long-term target is not merely “let an agent code for a long time.”

The target is a sustained engineering process with the following qualities:

### 1. Iterative, not one-pass

The system should repeatedly revisit design, implementation, and validation rather than performing a single generation pass followed by a static test step.

### 2. Collaborative, not monolithic

Different agent roles may contribute planning, coding, review, evaluation, repair, or synthesis. The purpose of orchestration is to structure collaboration when that collaboration yields better outcomes.

### 3. Harness-driven

Validation, test harnesses, CI checks, and review signals are not peripheral. They are part of the refinement loop.

### 4. Repository-native

Useful work must land as coherent repository changes: modules, tests, docs, artifacts, and branch history that a human team can actually inspect and continue from.

### 5. Directional persistence

The system should be capable of pursuing a goal through partial failure, redesign, test breakage, and local dead ends over an extended runtime.

### 6. Human-governed, machine-executed

Protected branch policy, merge decisions, and final acceptance remain human-governed. The system’s job is to carry work farther before human intervention is required.

## Diagnosis of Current Drift

The present concern is that design emphasis has drifted toward runtime safety and control substrate in a way that risks reducing marginal value.

Examples of this drift include overemphasis on:

- rollback completeness before bootstrap,
- protective boundaries beyond immediate need,
- infrastructure polish ahead of maintained workflow usefulness,
- and constraints that may mostly regulate agents rather than compound their capabilities.

This does **not** mean the substrate work was wasted. Much of it is necessary and valuable. The issue is one of sequencing and proportionality.

The concern is that the platform may become excellent at supervising work it does not yet reliably cause to happen.

## Directional Rule for Near-Term Design Work

Until bootstrap is achieved and tested, new design work should follow this rule:

**No new orchestration complexity unless it is required to make the maintained end-to-end bootstrap path real and testable.**

This implies:

- prefer thin vertical completion over broader architecture,
- prefer one real maintained path over multiple abstract future-capable paths,
- prefer operational leverage over formal completeness,
- prefer proving value in repo tasks over refining theoretical control surfaces.

## Practical Near-Term Focus

Near-term implementation should concentrate on a minimal useful loop.

That loop should prove that the maintained system can:

- load a real workflow,
- execute real agent steps through the maintained runtime,
- invoke validators and harnesses,
- persist canonical evidence,
- and leave either a usable result or a clean rollback state.

The system does not yet need, in maintained form, all of the following:

- rich autonomous PR lifecycle automation,
- complex multi-agent concurrency,
- elaborate rollback taxonomies,
- stacked branch strategies,
- advanced planner hierarchies,
- or broad surface-area policy systems.

Those may become important later. They should not displace bootstrap.

## Correction First, Rollback Last

The expected normal operating path for bootstrap and near-follow-on orchestration should be:

- validate,
- evaluate,
- repair,
- revalidate,
- and only then escalate or stop if progress is not being made.

In other words, the system should usually respond to ordinary implementation mistakes, missed requirements, weak tests, or incomplete outputs by correcting and iterating rather than by rolling back.

`ROLLBACK` should remain a minimal last-resort mechanism for invalid or unusable run state, not a routine part of the refinement loop.

This implies a near-term design posture of:

- keep maintained rollback limited and simple,
- prefer whole-run reset over elaborate undo semantics,
- keep safety mechanisms functional enough to prevent bad state from propagating,
- and invest design energy primarily in evaluator-guided correction and evidence-based gating rather than in richer rollback machinery.

If future empirical use shows that rollback is commonly needed during normal development, that should be treated as a sign that the refinement loop is too weak, not as evidence that rollback should become the primary control mechanism.

## Design Standard After Bootstrap

Once bootstrap exists, future design work should be judged by a stricter standard:

Does this addition materially improve the system’s ability to perform long-horizon useful engineering work?

That means additions should be favored when they improve one or more of:

- endurance over multi-hour runs,
- collaboration between specialized agent roles,
- design quality under iteration,
- code coherence across many modules,
- validation-guided repair,
- review quality,
- artifact traceability that helps iteration,
- and the probability of reaching a merge-worthy state.

Additions should be disfavored when they mostly:

- constrain already-capable agents without increasing outcome quality,
- add ceremony to execution,
- or formalize boundaries whose practical benefit has not yet been demonstrated.

## Evaluation Standard

The platform should be evaluated against a real comparison baseline:

Can it outperform direct short-session use of powerful agents on meaningful repository tasks?

Bootstrap gives the first point at which that question can be tested honestly.

The longer-term system succeeds only if, over time, it can do things such as:

- carry a task farther without human intervention,
- recover from local failure better than a one-shot session,
- integrate work across more files and modules coherently,
- and produce stronger validated deliverables than ad hoc direct agent use.

## Implications for Current Work

PR-8 should be treated as strategically important because it is close to the bootstrap threshold.

The value of PR-8 is not merely that it implements another runtime layer. Its value is that it may create the first real opportunity to test whether the platform can produce maintained end-to-end useful work.

Once PR-8 lands and bootstrap testing is possible, the project should quickly shift from architectural speculation to empirical evaluation:

- what useful work can it complete,
- where does it stall,
- what kinds of evaluator signals help,
- what failures are common,
- what loop structure produces real improvement,
- and where orchestration genuinely beats direct agent use.

## Two Directional Anchors

The following points should remain explicit in future design discussions.

### 1. Bootstrap is the first strategic threshold

Bootstrap is the point at which the system begins to become operationally self-improving under direction. Once the maintained path can complete real work end to end, the platform can start helping refine its own prompts, workflows, evaluators, harnesses, runtime structure, and surrounding tooling.

Before bootstrap, the system is still primarily preparation.

After bootstrap, the system can begin contributing to its own advancement.

### 2. The real target is long-horizon collaborative engineering

The long-term target is not a constrained wrapper around frontier coding agents, and not a system optimized only for small task execution.

The real target is a platform that can sustain hours of collaborative engineering work across a significant design and implementation surface, including:

- architectural reasoning,
- decomposition into subproblems,
- multi-module code generation,
- repeated testing and harness-driven refinement,
- review by sub-agents,
- iterative redesign when the initial approach proves weak,
- and production of a coherent functional component of meaningful scope.

That functional scope may reasonably involve **10k+ lines** of connected implementation across multiple modules and subcomponents, with tests, review artifacts, and validation evidence integrated into the process rather than appended afterward.

This target should shape present choices even when the immediate milestone is only a minimal bootstrap loop.

## Summary

The platform’s immediate mission is to achieve bootstrap.

Bootstrap is the turning point that allows the system to begin useful work through the maintained orchestration path and eventually to contribute to its own improvement.

The long-term mission is not a safer wrapper around coding agents. It is a system capable of hours-long collaborative engineering: design, build, test, critique, repair, and refinement across many connected modules, producing repository-native deliverables of significant scope.

Until bootstrap is real, the design bias should be toward thin vertical usefulness and against new complexity.

After bootstrap, the design bias should be toward whatever most increases long-horizon useful engineering output.

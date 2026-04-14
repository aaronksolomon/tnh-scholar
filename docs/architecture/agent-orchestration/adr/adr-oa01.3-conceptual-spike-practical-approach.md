---
title: "ADR-OA01.3: Practical Approach for the Orientation-Based Conceptual Spike"
description: "Practical approach for testing the OA01.2 orientation-based collaboration hypothesis with minimal new code and explicit prerequisite spike work."
type: "implementation-guide"
owner: "aaronksolomon"
author: "Aaron Solomon, Codex"
status: proposed
created: "2026-04-11"
parent_adr: "adr-oa01.2-conceptual-spike-orientation-based-supervisory-orchestration.md"
related_adrs: ["adr-oa03-agent-runner-architecture.md", "adr-oa07.1-worktree-lifecycle-and-rollback.md"]
---

# ADR-OA01.3: Practical Approach for the Orientation-Based Conceptual Spike

Practical guide for how to test the `OA01.2` orientation-based collaboration hypothesis without prematurely rebuilding the orchestration stack.

- **Status**: Proposed
- **Type**: Implementation Guide ADR
- **Date**: 2026-04-11
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, Codex
- **Parent**: [ADR-OA01.2](/architecture/agent-orchestration/adr/adr-oa01.2-conceptual-spike-orientation-based-supervisory-orchestration.md)

---

## Context

`OA01.2` establishes a strategic reset: test whether orientation-based supervisory collaboration is a more viable control model than the prior engine-first direction.

The immediate need is not a new permanent orchestration architecture. The immediate need is a practical way to run the conceptual spike cleanly enough that the project can learn from it.

That means:

- keeping the first implementation thin,
- avoiding broad new framework work,
- reusing substrate only where it clearly helps,
- and recognizing that some narrower functional spike work must happen first to make the conceptual spike executable at all.

The most immediate prerequisite is headless worker communication. If the project cannot reliably send a structured collaborator brief to a worker agent and inspect what comes back, the supervisory orientation model cannot be meaningfully tested.

## Problem

Without a practical approach, the project risks falling into one of two failure modes:

- returning to broad infrastructure-first implementation before the conceptual model is tested,
- or keeping the idea so abstract that it never reaches a meaningful repo task comparison.

The conceptual spike therefore needs a small practical frame that names:

- what must exist first,
- what the first spike materials might be,
- what parts of the current codebase may be reused,
- and what should remain out of scope until evidence justifies more buildout.

## Decision

The `OA01.2` conceptual spike will be approached in three layers, with the smallest viable footprint.

### 1. Prerequisite Functional Spike Layer

Before the supervisory concept is evaluated, the project should prove a minimal ability to:

- launch a worker agent from the local environment,
- pass a bounded task brief,
- capture enough output and diagnostics to understand what happened,
- and preserve workspace and evidence state for review.

This layer is not the point of the new architecture. It is a prerequisite spike that makes the conceptual spike runnable.

The first prerequisite focus should be headless agent communication compatibility and diagnosability:

- executable discovery,
- capability or contract probing,
- minimal communication invocation,
- returned-text capture,
- and legible failure reporting.

### 2. Conceptual Spike Layer

Once bounded worker execution is good enough to support real testing, the project should evaluate whether a supervisor choosing orientations produces better engineering progress than simpler direct-agent use.

The first conceptual spike should use a very small practical orientation set:

- implementation,
- repair,
- design review,
- evaluation.

These orientations should be expressed in English documents or playbook-style guidance, not in a new workflow language.

### 3. Comparative Review Layer

The spike should be judged by running a small number of real repo tasks through two comparison modes:

- a simpler direct-agent baseline,
- and an orientation-supervised approach.

The goal is not formal measurement. The goal is to produce enough evidence for an expert judgment about whether the orientation model creates better task framing, decomposition, follow-through, and adaptation.

## Artifact Guidance

The first practical spike should prefer the smallest artifact set that still makes learning possible.

At minimum, the project likely needs:

- some form of supervisory guidance,
- some form of orientation definition,
- at least one real repo task brief,
- and a lightweight way to capture what happened.

The exact shape of those artifacts should remain open during the spike. They do not need to begin as a polished or stable system. If a looser document, prompt, or operator note is sufficient to run a useful comparison, that is acceptable.

## Minimal Operation Set Beneath the Supervisor

The conceptual spike should assume a very small bounded operation set beneath the supervisor.

The initial operation set should be limited to actions close to:

- inspect context,
- run worker agent,
- run validation,
- summarize evidence,
- and stop or hand back to human review.

This list is intentionally small. It is guidance, not a final contract. If the spike needs richer or differently shaped operations, that should be discovered through use rather than assumed up front.

## Reuse Guidance

The conceptual spike may reuse clearly separable substrate from the current codebase when that reduces spike cost without pulling prior architecture assumptions back in through the side door.

Reasonable reuse candidates include:

- worktree and workspace helpers,
- lightweight validation execution,
- artifact writing utilities,
- and repo inspection helpers.

Reuse should remain opportunistic, not mandatory. The spike should not be forced to route itself through the current workflow kernel just because that code exists.

## Codebase Approach

The spike should continue within the existing documentation and architecture space for now.

The project should **not** create a parallel long-lived “v2” doc universe or a broad replacement package before the conceptual direction is tested.

If code is written for the spike, it should stay visibly experimental, narrow in scope, and easy to discard or condense later.

That means:

- prefer new spike-local documents before new framework modules,
- prefer thin helper code before new orchestration subsystems,
- and prefer explicit temporary seams over speculative abstractions.

The project should optimize for trying multiple plausible supervisory shapes quickly. The value of the spike comes partly from learning through several approaches, mostly expressed in English and mostly executed through strong external coding agents, rather than from selecting one architecture too early.

## Out of Scope

This practical approach intentionally does not authorize:

- a new workflow DSL,
- a general supervisor runtime,
- a new persistent state machine,
- broad prompt-library infrastructure,
- a final runner-abstraction platform,
- or a replacement of the current orchestration codebase.

Those may become appropriate later, but only if the conceptual spike produces evidence that they are worth building.

## Evaluation Standard

The practical spike is successful if it produces credible evidence for the `OA01.2` question while keeping code investment small, reversible, and exploratory.

The main evaluation questions are:

- did the prerequisite communication spike make bounded worker collaboration legible and usable,
- did the orientation framing improve real repo-task progress compared with simpler direct-agent use,
- and did the spike reveal what thinner substrate is actually necessary?

Evaluation remains primarily qualitative and based on expert engineering judgment.

## Consequences

### Positive

- keeps the project moving without another infrastructure-first detour,
- makes headless agent communication a prerequisite rather than the architectural center,
- creates a practical bridge from `OA01.2` to executable spike work,
- and protects the project from premature parallel architecture buildout.

### Negative

- leaves some implementation ambiguity in place by design,
- may reuse current substrate unevenly,
- and may require discarding some spike-local code or documents later if the direction changes.

## Open Questions

- What is the smallest headless communication layer that is good enough for the spike?
- Should the first comparison case be an implementation task, a repair task, or both?
- How much of the current maintained conductor path is worth reusing before it starts shaping the spike too strongly?
- What is the cleanest place to keep any spike-local helper code if the project writes some?

## Rationale

The practical danger after `OA01.2` is to mistake strategic clarity for implementation readiness.

This ADR avoids that mistake by defining a narrow path from concept to test:

- first make headless worker communication usable enough to support the spike,
- then test orientation-based supervision on real tasks through fast iteration,
- then decide what architecture, if any, has earned deeper implementation.

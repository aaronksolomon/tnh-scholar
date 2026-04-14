---
title: "ADR-OA01.2: Conceptual Spike for Orientation-Based Supervisory Orchestration"
description: "Strategy-level spike direction for testing orientation-based supervisory orchestration as an alternative to engine-first workflow control."
type: "strategy"
owner: "aaronksolomon"
author: "Aaron Solomon, Codex"
status: proposed
created: "2026-04-11"
parent_adr: "adr-oa01.1-tnh-conductor-provenance-driven-ai-workflow-coordination-v2.md"
related_adrs: ["adr-oa01-agent-orchestration-strategy.md"]
---

# ADR-OA01.2: Conceptual Spike for Orientation-Based Supervisory Orchestration

Strategy-level conceptual spike to test whether orientation-based supervisory orchestration is more viable than engine-first workflow control for strong coding agents.

- **Status**: Proposed
- **Type**: Strategy ADR
- **Date**: 2026-04-11
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, Codex
- **Supersedes**: [ADR-OA01.1](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md) at the strategic direction level

---

## Context

Recent execution attempts exposed a deeper architectural issue than a local implementation failure.

A concrete trigger was runtime failure caused by CLI flag drift in headless Codex execution. The immediate defect was operational, but the broader lesson was conceptual: the system had been designed too much as though strong frontier coding agents were low-level executors inside a deterministic orchestration engine.

That framing now appears misaligned with the actual capabilities and volatility of modern coding agents and their command-line surfaces.

The project also incurred a second kind of failure: too much robust code had to be written before the central orchestration idea itself had been tested at concept level. A large amount of engineering effort went into substrate and control machinery without first proving that the underlying control paradigm was viable.

This ADR responds to both lessons.

## Problem

The prior strategy direction overemphasized engine-first orchestration:

- strong agents were treated too much like bounded executors inside a predefined runtime model,
- deterministic sequencing assumptions were encoded too early,
- substantial structure was built before concept-level viability was demonstrated,
- and the cost of testing the central orchestration idea became too high.

This created a risk that the system would become highly robust at supervising work without materially improving the amount or quality of useful engineering work that frontier agents could perform.

## Decision

For the next phase, the project will run a conceptual spike based on the following architectural hypothesis:

**Orientations are a more appropriate unit of system architecture than rigid workflow state machinery for advanced coding agents coordinated by a supervisory agent.**

Under this hypothesis:

- a supervisory agent determines the next high-level task orientation,
- the orientation is expressed primarily in English,
- worker-agent runs are delegated according to that orientation,
- bounded operations and evidence capture remain available beneath that layer,
- and the system is evaluated by whether this structure produces more useful iterative engineering work than the previous orchestration model.

This ADR does **not** define a full implementation architecture.

It defines the hypothesis to test.

## Hypothesis

A viable orchestration model for strong coding agents is a hybrid system in which a supervisory agent selects among a small set of high-level task orientations, expressed in English, and coordinates worker-agent execution through bounded operations and evidence-producing runtime services.

Stated differently:

- the system should not primarily encode intelligence in deterministic workflow structure,
- the system should instead encode high-level intent, mode, and evaluation expectations in orientation documents and supervisory guidance,
- while retaining a thinner deterministic substrate for execution, validation, artifact capture, and workspace isolation.

This shift reduces how much the overall architecture depends on runner-specific control assumptions, but it does not eliminate the volatility of external worker invocation surfaces. The spike will still need to navigate that constraint explicitly.

## Initial Orientation Set for the Spike

The spike should begin with a small set of mid-level work orientations.

These should be substantial enough that a supervisory choice matters, but not so broad that they collapse into generic open-ended prompting.

### 1. Implementation

Used when the goal is to make bounded forward progress on a concrete repository task.

Typical questions include:
- what should be built next,
- what repo context and constraints matter for the change,
- what validation should accompany the work,
- and whether the result appears ready for human review or follow-on repair.

### 2. Repair

Used when an attempted implementation or existing code path is failing, incomplete, or directionally wrong and needs targeted correction.

Typical questions include:
- what appears to be broken,
- what evidence best explains the failure,
- whether the problem is local or structural,
- and whether the correct next step is direct repair, deeper inspection, or escalation back to design review.

### 3. Design Review

Used when the system needs higher-level critique, structural evaluation, or a narrowed architectural next step before more implementation proceeds.

Typical questions include:
- what the most important design tensions are,
- whether the current direction is coherent,
- what should be preserved or abandoned,
- and what narrower follow-on work should come next.

### 4. Evaluation

Used when the project needs a clearer judgment about progress, comparative quality, or readiness based on available evidence.

Typical questions include:
- whether a result is actually good enough,
- whether one approach appears stronger than another,
- what evidence is still missing,
- and whether the next step should be implementation, repair, review, or stop.

These are starting categories, not a closed taxonomy.

The spike framing remains at the project level. Functional spike work, conceptual spike work, and UX spike work are still important evaluation contexts, but they should not be the first orientation taxonomy if the goal is to test whether orientations improve real engineering progress.

## Illustrative Broader Orientation Scope

The broader architectural direction may eventually include additional orientations or collapse some of the initial ones above.

Illustrative examples include:

- synthesis,
- release-readiness,
- improvement,
- repo audit,
- environment diagnosis,
- and human-review preparation.

These examples are included to show possible scope, not to define a committed taxonomy.

This ADR does not decide which of these should exist, how they should be represented, or whether some should later collapse into others. The point is only to make clear that the orientation concept is intended to organize meaningful work modes rather than only experimental labels.

## What “Orientation” Means

An orientation is a high-level mode of work.

It describes what kind of progress is being sought, what kind of question is being answered, what evidence matters, and what success or failure means for the current effort.

An orientation is not the same as a low-level executable operation.

The supervisor may choose concrete operations within an orientation, but the architecture being tested here treats the orientation as the higher-order organizing unit.

The orientation concept also does not eliminate bounded execution surfaces. It assumes a thinner operational layer still exists beneath the supervisor for concrete actions such as worker invocation, validation, evidence capture, and workspace control.

## Example Orientation Document Shape

The conceptual spike may benefit from lightweight orientation documents that give a supervisory agent a stable English target without prematurely forcing the project into a rigid workflow language.

An orientation document might take a form such as:

```md
# Orientation: Design Review

## Purpose
Review the current design at conceptual and structural levels and identify the most important weaknesses, omissions, tensions, and opportunities for improvement.

## Use When
Use when the project needs higher-level architectural critique, internal consistency checking, or a clearer next-step design direction before implementation proceeds.

## Do Not Use When
Do not use when the main uncertainty is runtime behavior, integration correctness, or low-level implementation breakage that would be better addressed by functional or repair-oriented work.

## Supervisor Responsibilities
Determine what level of review is needed, what artifacts or source documents should be examined, what standard of critique is expected, and whether the outcome should be analysis, revision proposals, or a narrowed follow-on task.

## Allowed Operations
Inspect design documents, inspect code structure, compare competing approaches, request critique from a worker agent, request a revision proposal, synthesize findings, and propose next orientations.

## Required Evidence
A written critique, identified design tensions, concrete recommendations, and a clear statement of what should happen next.

## Success Criteria
The review produces actionable insight that improves design quality, clarifies tradeoffs, or reduces uncertainty in a meaningful way.

## Failure / Pivot Criteria
Stop or pivot when the review becomes repetitive, too abstract to guide action, or blocked on missing implementation evidence.

## Typical Next Orientations
Conceptual spike, implementation, repair, evaluation, or improvement.
```

This example is illustrative only. It is included to make the concept more concrete for future design and coding agents evaluating this ADR. Early spike work should nevertheless treat the presence of clear allowed operations, required evidence, success criteria, and failure or pivot criteria as orientation-document discipline rather than optional embellishment.

## What This ADR Intentionally Does Not Do

This ADR intentionally avoids over-encoding structure.

It does **not** define:

- a full workflow DSL,
- a new opcode system,
- a comprehensive state machine,
- a complete taxonomy of agent roles,
- a final supervisor architecture,
- a final persistence model,
- or a final implementation plan for the orchestration platform.

Those may emerge later, or may be rejected.

The purpose here is to keep the conceptual spike small enough to learn from.

## Reuse Policy

Existing orchestration code is not the starting constraint for this spike.

Reuse is allowed where it reduces spike effort without importing prior control assumptions.

In practice, this means that clearly separable substrate pieces may be reused opportunistically, such as:

- workspace and worktree utilities,
- validation and harness execution helpers,
- artifact capture utilities,
- repo inspection helpers,
- or other leaf-level infrastructure.

By contrast, architecture-shaped components that strongly encode the prior control model should not be treated as mandatory foundations for the spike.

## Evaluation Standard

The spike should be evaluated by whether it helps answer the following question:

**Does orientation-based supervisory orchestration materially improve useful engineering progress over simpler direct use of frontier coding agents?**

Useful engineering progress may include:

- better iterative task completion,
- more effective decomposition and follow-through,
- stronger adaptation to runtime surprises,
- better use of testing and validation during development,
- clearer evidence and human inspectability,
- and greater ability to continue through redesign, repair, and refinement.

Comparison should be grounded in a small number of real repo tasks rather than narrative impressions alone. At minimum, the project should compare orientation-based supervision against a simpler direct-agent baseline on equivalent task classes.

Evaluation at this stage should remain primarily qualitative and guided by expert engineering judgment, human and agentic. Comparison cases should inform that judgment, not replace it with premature formal metrics.

## Success Criteria for the Conceptual Spike

The spike is successful if it demonstrates, at minimum, that:

1. a supervisory agent can select among a small number of orientations in a meaningful way,
2. orientation documents in English are sufficient to guide next-step behavior at useful resolution,
3. worker-agent runs can be coordinated within that model,
4. runtime volatility such as CLI drift can be handled more naturally than in the prior deterministic framing,
5. and the resulting process appears directionally more viable than the superseded strategy model.

Success does not require production readiness.

Success requires learning that the control idea is plausible and worth deeper implementation.

## Consequences

### Positive

- lowers the cost of conceptual learning,
- re-centers design around current frontier-agent realities,
- encourages spike-first validation before robustness-first implementation,
- preserves room for English-defined supervisory logic,
- and allows reuse of existing substrate without forcing inheritance of the previous architecture.

### Negative

- reduces determinism at the supervisory layer,
- may make behavior harder to reproduce exactly,
- may produce vague or overly prompt-driven designs if not kept disciplined,
- may still depend on a volatile external runner surface beneath the supervisor,
- and may create a new form of drift if “orientation” becomes a loose label rather than a useful architectural unit.

## Alternatives Considered

### Continue the Prior Engine-First Direction With Incremental Fixes

Rejected for the conceptual spike because it keeps the project anchored to a control model that now appears to be the primary uncertainty.

### Discard All Existing Orchestration Work Entirely

Rejected because the project already has useful reusable substrate and a valuable design record. The need is conceptual reset, not historical erasure.

## Open Questions

- What is the smallest stable operation set required beneath the supervisor?
- How much runner capability probing is necessary before worker invocation is considered trustworthy?
- Which orientations are actually distinct enough to justify separate documents during the spike?
- What real repo tasks are best suited for comparison against a simpler direct-agent baseline?

## Follow-On Guidance

The next design work should remain close to the spike question and resist broad architectural expansion until the conceptual direction has clearer evidence behind it.

## Rationale

This decision reflects a specific lesson:

When the core uncertainty is about the control paradigm itself, robust implementation of that paradigm is premature until the paradigm has been tested at concept level.

The project is therefore shifting from robustness-first orchestration design toward concept-first spike work, while preserving the value of earlier exploration and reusable substrate.

This ADR is itself an example of the broader flexibility the orientation idea is meant to support. The first practical orientation set for implementation should use mid-level work modes such as implementation, repair, design review, and evaluation, because those better test whether supervisory selection improves real engineering progress.

At the same time, the orientation concept is intentionally broader than that first practical set. The project should be free to define higher-order spike-oriented orientations when useful, including conceptual spike, functional spike, UX spike, and other future spike forms that help frame a class of inquiry or development effort. The important point is that orientations are intended to be an adaptable organizing unit expressed in English. If the project can clearly conceive and draft an orientation that improves supervision, framing, evidence expectations, or inter-agent coordination, that orientation is in scope for the model.

In that sense, this ADR is both a strategy reset and a conceptual demonstration of the proposed flexibility: orientations are not limited to one fixed taxonomy, but they also should not be made so abstract that they stop helping real work move forward.

## Notes on Process Evolution

This ADR should be read as part of an evolving design record, not as a repudiation of previous work.

The earlier strategy work remains useful as a picture of the blackboard before erasure: it records the path by which the project arrived at the current insight.

If the new direction later proves viable, the project may condense older superseded strategy and code into a clearer narrative of process evolution and retained substrate.

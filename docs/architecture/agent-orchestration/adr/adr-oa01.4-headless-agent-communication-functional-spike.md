---
title: "ADR-OA01.4: Headless Agent Communication Functional Spike"
description: "Prerequisite functional spike for proving that structured headless communication between supervising and worker agents can happen simply and repeatably enough to support the OA01.2 conceptual spike."
type: "testing-strategy"
owner: "aaronksolomon"
author: "Aaron Solomon, Codex"
status: proposed
created: "2026-04-11"
parent_adr: "adr-oa01.3-conceptual-spike-practical-approach.md"
related_adrs: ["adr-oa03-agent-runner-architecture.md", "adr-oa03.3-codex-cli-runner.md"]
---

# ADR-OA01.4: Headless Agent Communication Functional Spike

Prerequisite functional spike for proving that structured headless communication between supervising and worker agents can happen simply and repeatably enough to support the `OA01.2` conceptual spike.

- **Status**: Proposed
- **Type**: Testing Strategy ADR
- **Date**: 2026-04-11
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, Codex
- **Parent**: [ADR-OA01.3](/architecture/agent-orchestration/adr/adr-oa01.3-conceptual-spike-practical-approach.md)

---

## Context

`OA01.2` and `OA01.3` shift the project toward a new question: can a supervisor coordinate useful work by giving strong coding agents structured English collaboration frames rather than treating them as low-level executors inside a rigid engine?

That question cannot be tested unless a minimal headless communication path exists at all.

The immediate need is not a runner platform. The immediate need is much smaller:

- one agent or human can give another agent a structured collaborator brief,
- the brief can be delivered through a simple headless interface,
- and the response can be captured clearly enough to support the next iteration.

Recent bootstrap testing showed that this path is not yet dependable enough. The failure was not mainly about the quality of the agent. It was about the thin communication interface between the project and the agent CLI.

## Problem

The conceptual spike will stall if the project cannot establish a minimal, legible, repeatable communication path with at least one strong external coding agent.

The key uncertainty is not yet broader orchestration behavior. The key uncertainty is whether structured collaborator-to-collaborator communication can be made to happen simply enough to support rapid experimentation.

At present, the project does not yet have a sufficiently clear answer to questions such as:

- how does the project find a usable headless agent executable,
- how does it determine a minimal valid invocation shape,
- how does it pass a structured English collaborator brief,
- how does it capture what came back,
- and how does it make failures legible without building a larger system first?

## Decision

The project will run a narrow functional spike focused on headless agent communication.

The purpose of this spike is to prove a minimal collaboration path, not to build a general runner substrate.

The spike should stay centered on the following practical question:

**Can the project send a structured natural-language collaboration brief to a strong external coding agent and get back a usable response through a very small amount of code?**

## What the Spike Should Test

The spike should test only a few things.

### 1. Agent Reachability

The project should be able to determine whether a target worker agent is locally reachable in headless form and which executable path is actually being used.

### 2. Minimal Invocation Shape

The project should be able to discover or probe a minimal valid way to invoke that agent headlessly.

This does not require a durable abstraction. It only requires a practical invocation shape that is good enough to support experimentation.

### 3. Structured English Collaboration Brief

The project should be able to send a collaboration brief that is mostly English and that clearly frames:

- who the worker is in relation to the supervisor,
- what the worker is being asked to do,
- what context should be read,
- and what kind of response is expected.

This brief is the real center of the spike. The code exists only to make that exchange happen.

### 4. Returned Response Capture

The project should capture what the worker returned in a form that a supervisor or human can inspect and use for the next step.

This can be extremely lightweight. It does not need to begin as a comprehensive artifact system.

### 5. Legible Failure

If the communication path fails, the project should be able to see that clearly enough to continue iterating.

The spike does not need a full failure taxonomy. It only needs enough visibility to distinguish:

- communication happened,
- communication failed at startup or invocation,
- or communication returned something unusable.

## What “Good Enough” Means

This spike should be considered successful when the project can do the following with at least one strong worker agent:

- locate and invoke the headless agent,
- deliver a structured English collaborator brief,
- capture a returned response,
- and understand, at a simple practical level, whether the exchange succeeded or failed.

If that path exists, the conceptual spike can begin.

Good enough does not mean robust, elegant, or generalized. It means the communication loop exists and can be iterated on quickly.

## Code Posture

This spike should assume that very little code may be necessary.

The likely correct default is a tiny experimental communication layer, potentially on the order of a small script or helper module, whose job is only to:

- find the executable,
- form the minimal invocation,
- pass the brief,
- and capture what comes back.

If the spike starts attracting significantly more structure than that, the project should pause and ask whether it is rebuilding assumptions before the collaboration path itself has been proven.

## Reuse Guidance

Existing code may be reused where it helps the spike happen faster and more clearly.

Possible reuse candidates include:

- simple subprocess helpers,
- existing executable-resolution logic,
- small pieces of artifact writing,
- and prior runner experiments as reference material.

Reuse is optional. If starting thinner is clearer, the spike should prefer the thinner path.

## Out of Scope

This spike does not attempt to deliver:

- a final runner abstraction,
- a stable multi-agent protocol,
- a general supervisor architecture,
- a workflow engine,
- a complete event or artifact system,
- or a full theory of task bounding, evaluation, or failure handling.

Those questions belong later, if the communication path proves worthwhile.

## Evaluation Standard

This spike should be judged primarily by simple practical questions:

- can the project make headless communication happen at all,
- can the exchanged brief and response support the next iteration of collaborative work,
- and does the communication layer stay thin enough to avoid rebuilding the old architecture prematurely?

Evaluation should remain qualitative and based on expert judgment.

## Consequences

### Positive

- keeps the prerequisite spike aligned with the collaboration-centered paradigm,
- lowers the amount of code assumed necessary up front,
- focuses effort on English collaboration structure rather than subsystem design,
- and creates a clearer entry point into the conceptual spike.

### Negative

- leaves many later engineering questions intentionally unresolved,
- may produce very temporary code or scripts,
- and may reveal that some additional structure is still needed sooner than hoped.

## Open Questions

- Should the first headless communication spike target Codex, Claude, or whichever agent proves easiest to reach?
- What is the smallest useful structure for a collaborator brief?
- What is the minimum response shape that is useful for supervision or human review?
- How much visibility is necessary before the communication loop becomes meaningfully iterable?

## Rationale

The project is no longer primarily asking how to build a stronger orchestration engine.

It is asking whether structured collaboration between strong agents can be facilitated simply enough to produce useful engineering progress.

This ADR keeps the first prerequisite spike faithful to that question.

---
title: "ADR-OA07.2: Runner Subsystem Design"
description: "Defines the maintained runner subsystem for tnh-conductor MVP, including typed runner contracts, CLI runner boundaries, and shared execution substrate usage."
type: "design-detail"
owner: "aaronksolomon"
author: "Aaron Solomon, GPT-5 Codex"
status: accepted
created: "2026-03-06"
parent_adr: "adr-oa07-mvp-runtime-architecture-strategy.md"
related_adrs:
  - "adr-oa03-agent-runner-architecture.md"
  - "adr-oa03.1-claude-code-runner.md"
  - "adr-oa03.3-codex-cli-runner.md"
  - "adr-oa07.1-kernel-runtime-design.md"
  - "adr-oa05-prompt-library-specification.md"
  - "adr-os01-object-service-architecture-v3.md"
---

# ADR-OA07.2: Runner Subsystem Design

Defines the maintained runner subsystem for tnh-conductor MVP, including typed runner contracts, CLI runner boundaries, and shared execution substrate usage.

- **Status**: Accepted
- **Type**: Design Detail
- **Date**: 2026-03-06
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, GPT-5 Codex
- **Parent ADR**: [ADR-OA07](/architecture/agent-orchestration/adr/adr-oa07-mvp-runtime-architecture-strategy.md)
- **Related ADRs**:
  - [ADR-OA03](/architecture/agent-orchestration/adr/adr-oa03-agent-runner-architecture.md)
  - [ADR-OA03.1](/architecture/agent-orchestration/adr/adr-oa03.1-claude-code-runner.md)
  - [ADR-OA03.3](/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-runner.md)
  - [ADR-OA07.1](/architecture/agent-orchestration/adr/adr-oa07.1-kernel-runtime-design.md)
  - [ADR-OA05](/architecture/agent-orchestration/adr/adr-oa05-prompt-library-specification.md)
  - [ADR-OS01](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

ADR-OA03 established the runner architecture conceptually: a shared kernel with per-agent adapters. ADR-OA03.1 and ADR-OA03.3 selected the active CLI surfaces:

- Claude Code via headless CLI mode
- Codex via `codex exec`

The prototype implementation under `spike/` demonstrated useful behavior, but its design is still below TNH standards:

- runner protocols still exchange raw command vectors
- prompt handling, process execution, artifact/event coordination, and workspace concerns are too intertwined
- PTY and subprocess paths duplicate control-loop mechanics
- the maintained path is obscured by spike-era naming and structure

ADR-OA07 states that the maintained MVP runtime needs a dedicated `runners/` subsystem. This ADR defines that subsystem.

### Implementation Guidance

The runner subsystem touches unstable external surfaces, so stronger boundaries are justified here than in purely internal kernel decomposition.

However:

- keep the maintained runner contracts as small as possible
- avoid introducing adapters or mappers that only rename data without reducing coupling
- share low-level execution mechanics only where the behavior is truly common

---

## Decision

### 1. The maintained runner package is `agent_orchestration/runners/`

The maintained runtime path for `RUN_AGENT` execution will live in `agent_orchestration/runners/`.

This package owns:

- typed runner request/result contracts
- agent-family identifiers
- maintained CLI runner adapters
- prompt/approval interaction handling needed for maintained runners
- runner-specific artifact normalization

It does not own:

- workflow semantics
- validator execution
- git workspace lifecycle
- generic run metadata persistence

### 2. Runner contracts are typed objects, not argv vectors

The runner subsystem will define typed request/result models.

Minimum runner request model:

- agent identity
- rendered task text
- response artifact policy
- timeouts / heartbeat policy
- working directory context
- approval/prompt-handling policy
- prompt reference for provenance only, if needed

Minimum runner result model:

- mechanical outcome
- transcript references or normalized transcript payload
- stdout/stderr text where applicable
- final response location/content reference
- command/prompt decision metadata where applicable

The runner protocol must not expose:

- `list[str]`
- `tuple[str, ...]`
- raw subprocess configuration

### 3. Separate maintained runner request/result models from validator models

`RUN_AGENT` is not the same domain concept as `RUN_VALIDATION`.

Therefore:

- runners get their own typed request/result models
- validation gets its own typed request/result models in `validation/`
- the two subsystems may share low-level process execution helpers from `execution/`
- they must not share one generic “execute anything” domain contract

### 4. Use explicit agent-family identifiers

The maintained runner subsystem will use typed agent identifiers instead of free-form strings for supported maintained runners.

At MVP, the maintained set is:

- Claude CLI runner
- Codex CLI runner

Prototype or deprecated surfaces do not belong in the maintained identifier set.

### 5. Split runner concerns into explicit collaborators

The current spike service and runner providers should be decomposed into smaller maintained collaborators.

Minimum collaborator set:

#### A. `RunnerRequestBuilder`

Builds a typed runner request from kernel-facing inputs and runner policy.

Prompt ownership rule:

- prompt catalog lookup and prompt rendering remain with the control plane / kernel-side prompt assembly flow defined by [ADR-OA05](/architecture/agent-orchestration/adr/adr-oa05-prompt-library-specification.md)
- runners receive rendered task text plus typed runner policy
- runners may carry prompt references only for provenance, not for prompt-system resolution

#### B. `CliInvocationRenderer`

Renders a typed runner request into the execution-layer process request.

This is the final translation point before subprocess execution.

#### C. `RunnerOutputCollector`

Normalizes execution-layer output into runner-domain results.

Responsibilities:

- transcript normalization
- stdout/stderr mapping
- final response mapping
- prompt-decision capture

#### D. `PromptInteractionHandler`

Owns application of prompt/approval handling policy for maintained CLI runners.

The maintained direction is:

- a shared typed `PromptInteractionPolicy` model
- agent-specific handlers that interpret that policy for each CLI surface

It should not be embedded into the low-level process collector itself.

#### E. Agent-specific adapters

Examples:

- `ClaudeCliRunner`
- `CodexCliRunner`

These adapters map maintained runner requests to the surface-specific CLI semantics documented in OA03.1 and OA03.3.

### 6. PTY is not part of the maintained MVP runner path

PTY support remains in `reference/spike/` for design history and fallback reference.

The maintained runner subsystem will assume:

- headless CLI surfaces first
- structured stdout/stderr or file-based outputs where supported
- no PTY dependency in the maintained MVP path unless a new requirement emerges

### 7. The shared execution substrate lives in `execution/`

The runner subsystem may use `execution/` for shared process mechanics:

- process launch
- timeout enforcement
- output capture primitives
- termination handling
- low-level result capture

But `execution/` must remain infrastructure-only.

Runner-domain concerns such as:

- agent family
- prompt handling semantics
- transcript interpretation
- final response semantics

must remain inside `runners/`.

### 8. Maintained runner results visible to the kernel should stay minimal

The kernel should only see what it needs for deterministic orchestration.

That means the kernel-facing runner result contract should expose:

- `MechanicalOutcome`
- runner-owned artifact references or structured references needed by later evaluation

The kernel does not need low-level subprocess internals.

These kernel-facing contracts should live in `runners/protocols.py` and be imported by the kernel rather than duplicated in `kernel/`.

### 9. `reference/spike/` remains the historical comparison point during migration

The maintained runner subsystem is not an in-place cleanup of `spike/`.

Migration rule:

- no new forward-path runner work lands in `reference/spike/`
- new runner design and implementation work lands under `runners/`
- historical spike artifacts remain available until the maintained subsystem is stable

---

## Suggested Package Shape

```text
agent_orchestration/runners/
  __init__.py
  models.py                 # typed runner requests/results/policies
  protocols.py              # kernel-facing runner contracts
  service.py                # runner orchestration facade if needed
  prompt_handling.py        # maintained prompt interaction policy
  providers/
    __init__.py
    claude_cli_runner.py
    codex_cli_runner.py
```

Notes:

- a single `service.py` is optional; do not introduce it unless it provides real coordination value
- agent-specific adapters belong under `providers/`
- if prompt handling becomes agent-specific, split it further under `providers/` or `policies/`
- add dedicated renderers or mappers only if testing pressure or real reuse justifies them
- do not create `renderers/` or `mappers/` packages merely to preserve symmetry

---

## Consequences

### Positive

- gives `RUN_AGENT` a maintained subsystem boundary instead of continuing to depend on spike-era structure
- removes raw argv vectors from runner-facing contracts
- clarifies what the kernel should and should not know about agent execution
- preserves OA03 runner decisions while finally expressing them in a TNH-compliant module design

### Negative

- adds a new maintained package before prototype code is retired
- requires import and test churn during migration
- may initially duplicate logic that still exists under `reference/spike/`

---

## Alternatives Considered

### 1. Keep using `reference/spike/` as the maintained runner path

Rejected. The package purpose and structure are wrong for long-term maintained use.

### 2. Share one generic execution request/result model with validators

Rejected. Runner and validator semantics differ enough that a shared domain contract would become too generic and weakly modeled.

### 3. Keep PTY as a first-class maintained runner option

Rejected for MVP. No maintained requirement justifies that complexity today.

---

## Open Questions

1. What is the minimal maintained runner request model the kernel should construct directly, versus a richer runner-internal request model built inside `runners/`?
2. How minimal can the shared `PromptInteractionPolicy` remain before agent-specific divergence becomes clearer?
3. Which runner outputs should be captured by `runners/` as raw runner artifacts, and which should be handed off to `run_artifacts/` for structured metadata ownership and formatting?

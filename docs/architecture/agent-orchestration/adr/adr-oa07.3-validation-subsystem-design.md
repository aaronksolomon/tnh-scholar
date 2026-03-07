---
title: "ADR-OA07.3: Validation Subsystem Design"
description: "Defines the maintained validation subsystem for tnh-conductor MVP, including typed validator contracts, harness/report ownership, and the boundary to shared process execution."
type: "design-detail"
owner: "aaronksolomon"
author: "Aaron Solomon, GPT-5 Codex"
status: accepted
created: "2026-03-06"
parent_adr: "adr-oa07-mvp-runtime-architecture-strategy.md"
related_adrs:
  - "adr-oa04-workflow-schema-opcode-semantics.md"
  - "adr-oa04.1-implementation-notes-mvp-buildout.md"
  - "adr-oa04.2-mvp-hardening-compliance-plan.md"
  - "adr-oa07.1-kernel-runtime-design.md"
  - "adr-os01-object-service-architecture-v3.md"
---

# ADR-OA07.3: Validation Subsystem Design

Defines the maintained validation subsystem for tnh-conductor MVP, including typed validator contracts, harness/report ownership, and the boundary to shared process execution.

- **Status**: Accepted
- **Type**: Design Detail
- **Date**: 2026-03-06
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, GPT-5 Codex
- **Parent ADR**: [ADR-OA07](/architecture/agent-orchestration/adr/adr-oa07-mvp-runtime-architecture-strategy.md)
- **Related ADRs**:
  - [ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)
  - [ADR-OA04.1](/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md)
  - [ADR-OA04.2](/architecture/agent-orchestration/adr/adr-oa04.2-mvp-hardening-compliance-plan.md)
  - [ADR-OA07.1](/architecture/agent-orchestration/adr/adr-oa07.1-kernel-runtime-design.md)
  - [ADR-OS01](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

ADR-OA04 defines `RUN_VALIDATION` semantically: deterministic validators run, mechanical outcomes are produced, artifacts may be captured, and generated harness reports may affect later `EVALUATE` and `GATE` behavior. ADR-OA07 establishes that validation is a maintained subsystem of the MVP runtime, separate from both the kernel and the runner subsystem.

The current prototype implementation under `conductor_mvp/providers/validation_runner.py` proved the control flow, but it still has prototype-shaped boundaries:

- trusted validator resolution and subprocess execution are too tightly coupled
- builtin validators and generated harnesses share low-level execution paths but not clearly separated domain models
- artifact capture and harness report loading are embedded in the same provider that launches the process
- typed kernel contracts still sit too close to argv-shaped infrastructure details

The goal of this ADR is not to over-design validation into a large framework. The goal is to define a small maintained subsystem with clear ownership:

- the kernel decides **when** validation runs and how outcomes route
- the validation subsystem decides **how** validators are resolved, executed, and normalized
- the execution subsystem owns only the final process-launch mechanics

Compatibility rule with OA04:

- this ADR does not redefine the external workflow YAML shape for `RUN_VALIDATION`
- the OA04 source-document contract remains the normative workflow shape unless OA04 is explicitly amended
- maintained validation code should normalize OA04 source entries such as string validator ids and inline script/harness objects into typed validation-domain models as quickly as possible after loading

### Validation Definition

For agent-orchestration MVP, validation means:

> deterministic execution of trusted validator families, producing normalized validation outcomes and validation-owned artifacts/reports for kernel and planner consumption.

Validation is not:

- a generic command execution interface
- an alternate runner subsystem
- a planner subsystem
- a general artifact persistence layer

### Implementation Guidance

Validation touches an external process boundary, so typed contracts matter here. But the maintained subsystem should still stay small.

Guidance for implementers:

- keep validation-domain models focused on validator semantics, not subprocess mechanics
- use stronger boundary objects where validation crosses into execution or file/report loading
- avoid introducing extra service layers unless they clarify ownership
- prefer one clear typed model over several pass-through wrappers

Goal:

> deterministic validation semantics with the smallest durable contract surface

---

## Decision

### 1. The maintained validation package is `agent_orchestration/validation/`

The maintained runtime path for `RUN_VALIDATION` execution will live in `agent_orchestration/validation/`.

This package owns:

- typed validation request/result contracts
- trusted validator identifiers and validator-family models
- validator resolution from kernel-facing workflow specs to maintained validation requests
- validation result normalization
- harness report loading and normalization
- validation-specific artifact collection policy

It does not own:

- workflow route semantics
- agent execution
- generic subprocess launch primitives
- generic run-directory creation

### 2. Validation contracts are typed objects, not commands

The validation subsystem will define typed request/result models.

Minimum validation request model:

- validator identity
- validator family
- run directory / working directory context
- validation timeout policy
- validation artifact capture policy

Minimum validation result model:

- mechanical outcome
- normalized harness report reference or payload when present
- validation-owned artifact references needed by later steps

Validation protocols must not expose:

- `list[str]`
- `tuple[str, ...]`
- raw subprocess configuration objects

### 3. Validation families are explicit and typed

The maintained MVP validation subsystem will support at least two validator families:

- builtin validators
- generated harness validators

These are different validation concepts and should remain explicit in the maintained model.

At MVP:

- builtin validators are selected by typed validator identifiers
- generated harness validators are selected by typed harness identifiers plus typed harness policy fields
- OA04 source-document entries may still arrive as strings or inline script-style objects, but those are loader/input shapes rather than maintained kernel-facing validation-domain contracts
- neither family should be described as an arbitrary script command in maintained kernel-facing models

### 4. Resolution and execution are separate collaborators

Validation needs a clear split between trusted resolution and process execution.

Minimum collaborator set:

#### A. `ValidatorResolver`

Owns trusted resolution from kernel-facing validation specs into validation-domain execution requests.

Responsibilities:

- resolve builtin validator identifiers
- resolve harness validator identifiers
- apply validation-family defaults and policy

This collaborator should prefer typed init-time config and typed policy objects over hard-coded registries where validator behavior is expected to evolve across repos or deployments. It should not invoke subprocesses directly.

#### B. `ValidationExecutor`

Owns orchestration of one or more validation requests.

Responsibilities:

- invoke the execution subsystem with typed execution input
- aggregate multiple validation results
- merge mechanical outcomes deterministically

#### C. `HarnessReportLoader`

Owns loading and normalization of harness reports.

Responsibilities:

- locate expected report files
- parse report payloads into typed validation models
- handle malformed or missing reports deterministically

#### D. `ValidationArtifactCollector`

Owns validation-specific artifact collection policy.

Responsibilities:

- apply allowed artifact patterns
- copy or register validation-owned artifact outputs
- return validation artifact references for downstream use

These collaborators may be composed into a small facade service, but their responsibilities should remain explicit.

### 5. The kernel sees only minimal validation results

The kernel should depend only on the smallest validation result contract it needs for deterministic orchestration.

That kernel-facing contract should expose:

- `MechanicalOutcome`
- whether a harness report exists
- normalized harness report content needed for OA04 runtime rules
- validation artifact references needed by later evaluation or gating

The kernel should not depend on:

- validator-family-specific process details
- raw stdout/stderr capture
- command shapes
- file-loading/parsing internals

This narrows the remaining open question in [ADR-OA07.1](/architecture/agent-orchestration/adr/adr-oa07.1-kernel-runtime-design.md): the stable contract should be the semantic validation result, not the execution-layer detail behind it.

### 6. Harness report ownership belongs to validation, not kernel

Generated harness reports are part of validation-domain output.

Therefore:

- parsing and normalization of harness reports belongs in `validation/`
- the kernel consumes only the normalized result
- the kernel may enforce OA04 runtime rules based on normalized harness semantics, such as proposed goldens requiring `GATE`

This keeps file-format details out of the kernel.

### 7. Artifact collection policy belongs to validation, but run-directory ownership does not

Validation is responsible for deciding which validation outputs count as validation artifacts.

That includes:

- validator-specific artifact glob/pattern policy
- mapping collected files into validation-owned artifact references

But validation does not own:

- creation of the run directory itself
- generic run metadata layout
- non-validation artifact persistence conventions

Those remain with the run-artifact subsystem.

MVP guidance:

- validation artifact references should remain paths-only unless a concrete metadata need appears during implementation

### 8. The shared execution substrate lives in `execution/`

Validation may use `execution/` for:

- final process request rendering
- subprocess launch
- timeout enforcement
- low-level result capture

But validation-domain contracts must stop above that layer.

Critical boundary rule:

> argv rendering is permitted only at the final execution edge, never in kernel-facing or validation-domain contracts.

This is the direct maintained replacement for the prototype pattern that surfaced review and security concerns in PR #35.

Migration direction:

- current prototype: `ValidatorExecutionSpec.command: tuple[str, ...]` -> `subprocess.run(...)`
- maintained path: typed validator ref + typed validator policy -> `ValidatorResolver` -> typed execution request -> `execution/` -> subprocess edge

MVP guidance:

- harness report normalization should support only the current minimal report contract
- if schema evolution becomes necessary later, add an explicit schema version field rather than speculative multi-schema support

### 9. Validation remains distinct from runners even where infrastructure overlaps

The validation subsystem and runner subsystem may share `execution/`, but they remain distinct domains.

Do not merge them into one generic command-execution subsystem.

Rationale:

- `RUN_AGENT` is performer-oriented and interactive/provenance-heavy
- `RUN_VALIDATION` is deterministic and evidence-oriented
- conflating them would create a vague “execute process” domain contract rather than clear subsystem ownership

### 10. Validation policy should lean config-first where tuning is likely

Builtin validator identity may remain code-owned where the semantic meaning is fixed.

However, validation policy should prefer typed config objects passed at init where repo-specific or deployment-specific tuning is likely.

This is the preferred maintained direction for:

- validator family defaults
- harness execution policy
- timeout and artifact behavior likely to vary across environments

Rationale:

- the orchestrator is expected to evolve beyond TNH Scholar
- validation behavior is likely to change faster than core subsystem identity
- config-first policy keeps the subsystem adaptable without pushing low-level command structure back into workflow or kernel models

---

## Suggested Package Shape

```text
agent_orchestration/validation/
  __init__.py
  models.py                  # validator refs, requests, results, report models
  protocols.py               # kernel-facing validation contracts
  service.py                 # validation orchestration facade if needed
  resolver.py                # trusted validation resolution
  providers/
    __init__.py
    validation_executor.py
    harness_report_loader.py
    artifact_collector.py
```

Notes:

- keep the package flat until a second resolver implementation actually appears
- do not introduce extra subpackages only for symmetry with other subsystems

---

## Consequences

### Positive

- Removes arbitrary-command thinking from the maintained validation domain.
- Gives the kernel a smaller and more stable validation contract.
- Keeps harness-report parsing and artifact capture out of the kernel.
- Makes the subprocess trust boundary explicit at `execution/`.
- Preserves flexibility to support both builtin validators and generated harnesses without over-generalizing.

### Negative

- Introduces more explicit validation-domain models than the prototype used.
- Requires migration work out of `conductor_mvp/providers/validation_runner.py`.
- May reveal that some current prototype model fields belong in validation-specific models rather than kernel models.

### Neutral

- Validation may still use subprocesses in MVP; the architectural correction is about where those details live, not about avoiding subprocesses entirely.
- Exact builtin validator inventory can remain small at MVP as long as the model boundary is correct.

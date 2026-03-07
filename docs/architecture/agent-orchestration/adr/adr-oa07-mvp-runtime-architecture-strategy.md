---
title: "ADR-OA07: MVP Runtime Architecture Strategy"
description: "Defines the maintained modular runtime architecture strategy for the tnh-conductor walking skeleton, replacing prototype-era structure with TNH-compliant subsystem boundaries."
owner: "aaronksolomon"
author: "Aaron Solomon, GPT-5 Codex"
type: "strategy"
status: accepted
created: "2026-03-06"
related_adrs:
  - "adr-oa04-workflow-schema-opcode-semantics.md"
  - "adr-oa04.1-implementation-notes-mvp-buildout.md"
  - "adr-oa04.2-mvp-hardening-compliance-plan.md"
  - "adr-os01-object-service-architecture-v3.md"
---

# ADR-OA07: MVP Runtime Architecture Strategy

Defines the maintained modular runtime architecture for the tnh-conductor walking skeleton, replacing prototype-era structure with TNH-compliant subsystem boundaries.

- **Status**: Accepted
- **Type**: Strategy ADR
- **Date**: 2026-03-06
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, GPT-5 Codex
- **Related ADRs**:
  - [ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)
  - [ADR-OA04.1](/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md)
  - [ADR-OA04.2](/architecture/agent-orchestration/adr/adr-oa04.2-mvp-hardening-compliance-plan.md)
  - [ADR-OA05](/architecture/agent-orchestration/adr/adr-oa05-prompt-library-specification.md)
  - [ADR-OA06](/architecture/agent-orchestration/adr/adr-oa06-planner-evaluator-contract.md)
  - [ADR-OS01](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

ADR-OA04 and ADR-OA04.1 define the workflow bytecode, opcode semantics, and intended MVP operating loop for tnh-conductor. The first implementation pass proved valuable, but it also exposed that the current code organization is still prototype-shaped rather than foundation-shaped.

The problem is not lack of functionality. We now know a great deal about what the system needs to do:

- validate and execute declarative workflows
- invoke external agents through stable CLI surfaces
- run deterministic validators and generated harnesses
- manage isolated workspaces and durable run artifacts
- support planner-driven routing with bounded transitions

What is missing is the correct **maintained runtime architecture**.

The current implementation spreads these responsibilities across:

- `conductor_mvp/`
- `spike/`
- `codex_harness/`
- CLI entrypoints and supporting providers

This prototype structure was acceptable for exploration, but it does not yet satisfy TNH Scholar design requirements for:

- object-service boundaries
- high cohesion and loose coupling
- typed contracts instead of low-level transport shapes
- clear separation between maintained runtime code and historical spike/reference code

ADR-OA04.2 documents the audit findings. This ADR answers the next question:

> What should the maintained MVP runtime architecture be, if we are treating the walking skeleton as the foundation for future work?

### Design Principle for This Phase

> The MVP is not disposable. It is the first maintained runtime. Therefore it must be designed as a modular TNH subsystem, not merely cleaned up after prototyping.

### Architectural Constraints

The redesign must satisfy the following constraints:

1. Preserve the OA04/OA04.1 kernel semantics and workflow contracts.
2. Stay compatible with the existing OA05 prompt-library contract and OA06 planner-evaluator contract.
3. Comply with [ADR-OS01](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md).
4. Preserve spike and deprecated artifacts long enough to remain useful historical references.
5. Avoid “compliance by patching”; redesign module boundaries where the prototype shape is wrong.
6. Keep the resulting MVP small enough to remain reviewable and evolvable.

### Implementation Guidance

TNH modular standards apply here as design principles, not as a requirement to maximize abstraction count.

Guidance for implementers:

- use strong object-service boundaries at unstable or externally-coupled surfaces:
  - subprocess/CLI execution
  - workflow YAML loading
  - planner outputs
  - git/workspace side effects
- use lighter internal collaborators where the concern is purely TNH-internal decomposition
- prefer the smallest typed boundary that makes ownership and information flow clear
- do not introduce service/provider/mapper layers unless they reduce real coupling or clarify responsibility

Goal:

> durable simplicity, not ceremonial architecture

---

## Decision

We will build a **maintained MVP runtime architecture** beside the current prototype-era packages, then migrate forward-path code onto that architecture in phases.

### 1. Distinguish maintained runtime from reference prototype code

The codebase will explicitly separate:

- **Maintained runtime modules**: the forward implementation path for conductor MVP
- **Reference prototype modules**: spike or deprecated packages preserved for design history and comparison

This means:

- `reference/spike/` remains as a reference artifact during transition
- `reference/codex_harness/` is treated as deprecated/reference because the API-first Codex path was superseded by OA03.3
- new maintained runtime code will not be added under spike/reference packages

### 2. Organize the MVP by subsystem responsibility, not by history

The maintained architecture will be organized into explicit runtime subsystems.

#### A. Kernel subsystem

Owns deterministic workflow execution and workflow-state semantics.

Responsibilities:

- workflow models and typed step definitions
- workflow loading and normalization
- workflow validation
- route resolution
- runtime kernel state and trace
- opcode dispatch

This subsystem will use the package name `kernel/`.

Rationale:

- `tnh-conductor` is the overall system name
- "kernel" precisely describes the deterministic execution core
- OA04 already uses kernel terminology consistently
- resolving this name early reduces migration ambiguity

#### B. Runner subsystem

Owns `RUN_AGENT` execution through maintained CLI runner implementations.

Responsibilities:

- typed agent execution requests/results
- maintained CLI runner adapters
- command rendering at the final subprocess boundary
- output capture and normalization
- prompt/approval handling where applicable
- shared runner execution substrate

This subsystem replaces the forward-looking role currently played by `spike/`.

#### C. Validation subsystem

Owns `RUN_VALIDATION` execution.

Responsibilities:

- typed validator execution requests/results
- builtin validator resolution
- generated harness execution
- report loading and normalization
- artifact collection rules for validation outputs

This remains distinct from the runner subsystem even if both share low-level process execution helpers.

#### D. Workspace subsystem

Owns git/worktree lifecycle and deterministic workspace operations.

Responsibilities:

- repo-root discovery
- branch/worktree setup and cleanup
- status/diff capture
- rollback/checkpoint primitives
- workspace safety constraints

#### E. Run-artifact subsystem

Owns run-scoped persistence.

Responsibilities:

- run directory creation
- event writing
- metadata writing
- artifact path resolution
- persisted transcript/log/report conventions

#### F. Shared process execution substrate

Owns the lowest-level trusted process execution mechanics shared by runner and validation subsystems.

Responsibilities:

- typed process-launch policy objects
- final argv rendering from typed execution requests
- subprocess launch and result capture
- timeout enforcement
- shared output/result normalization primitives

This substrate should live in a dedicated `execution/` package rather than in `common/`.

Rationale:

- it is shared infrastructure, but not general-purpose enough to belong in `common/`
- it should remain narrower than either the runner or validation domains
- a dedicated package makes the trust boundary around subprocess execution explicit

### 3. Share the execution engine, not the domain contracts

Agent runs and validator runs are both process-execution concerns, but they are not the same domain concept.

Therefore:

- `RUN_AGENT` and `RUN_VALIDATION` will have **separate typed execution request models**
- both may share a lower-level execution substrate for process launch, timeout handling, and result capture
- neither should exchange naked argv vectors across service/protocol boundaries

The only place argv rendering is permitted is the final infrastructure edge that invokes the process.

### 4. Keep prototype artifacts available during migration

We will not immediately delete or rewrite the prototype packages.

Instead:

- `reference/spike/` remains as a historical and comparative artifact
- PTY support remains in reference code unless a maintained requirement emerges
- `reference/codex_harness/` remains available as deprecated/reference code until later cleanup

This allows documentation and design history to remain intelligible while the maintained runtime is built.

### 5. Treat `codex_harness/` as deprecated, not active runner architecture

The API-first Codex path in `codex_harness/` is no longer the active runner direction. It should not shape the maintained MVP runner design.

It may still be useful:

- as reference for typed tool-call modeling
- as a future experimental path if API surfaces become relevant again

But for the current MVP runtime architecture, it is not the forward execution surface.

### 6. Prefer redesign over patch-hardening where prototype structure is wrong

If a subsystem’s current package shape is fundamentally misaligned with TNH standards, we redesign it rather than “clean it up in place.”

This applies especially to:

- `spike/service.py`
- `conductor_mvp/service.py`
- runner and validator subprocess boundaries

### 7. Migration will be phased and subsystem-driven

Implementation will proceed by migrating one maintained subsystem at a time.

Suggested order:

1. Kernel runtime design (`OA07.1`) and initial package boundary
2. Runner subsystem (`OA07.2`)
3. Validation subsystem (`OA07.3`)
4. Workspace + run-artifact subsystems (`OA07.4`)
5. Reference package policy (`OA07.5`)
6. Execution subsystem (`OA07.6`)
7. Kernel decomposition and runtime rewiring
8. Deprecation labeling and eventual cleanup of prototype/reference packages

---

## Target Runtime Shape

The exact package names may still evolve, but the maintained architecture should converge on a shape like:

```text
agent_orchestration/
  common/                # narrow shared primitives only
  kernel/                # maintained workflow runtime
  runners/               # maintained CLI runner subsystem
  validation/            # maintained validator subsystem
  workspace/             # git/worktree lifecycle + capture
  run_artifacts/         # events, metadata, artifact persistence
  execution/             # shared process execution substrate
  reference/
    spike/               # reference prototype code (temporary/historical)
    codex_harness/       # deprecated/reference API path
```

Notes:

- `kernel/` replaces the maintained role currently played by `conductor_mvp/`
- `conductor_mvp/` is a temporary migration-source package during OA07 implementation; it is not part of the maintained end-state and should be deleted after its responsibilities are migrated
- `runners/` is a strong candidate for the maintained replacement of forward-path code currently living in `spike/`
- not every helper currently in `reference/spike/` belongs in `runners/`; several belong in `workspace/` or `run_artifacts/`
- `execution/` is the shared subprocess/process-launch substrate for runner and validation domains
- `reference/` keeps historical and deprecated code discoverable without presenting it as a peer maintained subsystem

---

## Planned Follow-On ADR Map

OA07 defines the top-level runtime strategy. Detailed subsystem design should be captured as decimal ADRs beneath it so the redesign remains modular and avoids re-deciding work already covered by OA04, OA05, and OA06.

Planned follow-on ADRs:

- **ADR-OA07.1: Kernel Runtime Design**
  - scope: maintained kernel package boundary, workflow catalog/validator/runtime split, state model, route resolution ownership
  - should reuse OA04 and OA04.1 decisions rather than redefining opcode semantics
  - should be written before runner/validation migration begins
- **ADR-OA07.2: Runner Subsystem Design**
  - scope: maintained CLI runner package, typed agent execution models, shared execution substrate, prompt/approval handling boundary
  - should absorb lessons from OA03.1, OA03.3, and the `reference/spike/` prototype
- **ADR-OA07.3: Validation Subsystem Design**
  - scope: typed validator execution models, builtin vs generated harness resolution, artifact/report contract, subprocess rendering boundary
  - should reuse OA04 validation semantics rather than redefining them
- **ADR-OA07.4: Workspace and Run Artifact Subsystems**
  - scope: git worktree lifecycle, rollback/checkpoint support, run directory ownership, event/log/metadata persistence
  - should reuse OA01/OA04 provenance and workspace requirements
- **ADR-OA07.5: Reference Package Policy**
  - scope: how `reference/spike` and `reference/codex_harness` are labeled, documented, imported, and eventually retired

- **ADR-OA07.6: Execution Subsystem Design**
  - scope: typed execution request/result models, cwd/env policy, timeout/termination taxonomy, stdout/stderr contract, final argv rendering boundary
  - should define the shared subprocess trust boundary before implementation begins

This map is intentionally narrow. It focuses on subsystem boundaries that remain under-specified by the prototype implementation rather than duplicating decisions already accepted in the OA03/OA04 ADR families.

---

## Consequences

### Positive

- Gives the walking skeleton a real maintained architecture rather than a prototype-shaped one.
- Aligns the MVP with TNH modular and object-service standards before the subsystem grows further.
- Preserves useful spike and deprecated artifacts without letting them dictate the maintained package structure.
- Makes later security, compliance, and review work substantially easier because subsystem ownership becomes clear.

### Negative

- Requires redesign and migration work before further feature build-out.
- Increases short-term duplication while maintained modules coexist beside reference modules.
- Will create naming and import churn as forward-path code moves off prototype packages.

---

## Alternatives Considered

### 1. Harden the current prototype packages in place

Rejected. This would preserve historical/package naming accidents and push structural problems forward.

### 2. Delete spike and deprecated code immediately

Rejected. That would erase useful design reference points and create unnecessary documentation churn during an active MVP design phase.

### 3. Treat runner architecture as a separate ADR family concern from the MVP redesign

Rejected. The runner subsystem is now a necessary modular component of the integrated MVP runtime and should be redesigned in that context.

---

## Open Questions

1. What is the smallest viable maintained runner package that lets us stop adding forward-path code under `reference/spike/`?
2. Which parts of the current event-writing and artifact-writing surface belong in `run_artifacts/` versus runner/validation subsystems?
3. At what point should `reference/codex_harness/` be labeled in-code as deprecated/reference rather than merely inferred from the ADR set?

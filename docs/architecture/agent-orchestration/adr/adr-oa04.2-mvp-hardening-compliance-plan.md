---
title: "ADR-OA04.2: Agent-Orch MVP Hardening and Compliance Plan"
description: "Audit findings and remediation plan for bringing the agent-orchestration walking skeleton up to TNH Scholar code standards."
type: "implementation-guide"
owner: "aaronksolomon"
author: "Aaron Solomon, GPT-5 Codex"
status: proposed
created: "2026-03-06"
parent_adr: "adr-oa04-workflow-schema-opcode-semantics.md"
related_adrs:
  - "adr-oa04.1-implementation-notes-mvp-buildout.md"
  - "adr-oa03.3-codex-cli-runner.md"
  - "adr-oa07-mvp-runtime-architecture-strategy.md"
  - "adr-os01-object-service-architecture-v3.md"
---

# ADR-OA04.2: Agent-Orch MVP Hardening and Compliance Plan

Audit findings and remediation plan for bringing the agent-orchestration walking skeleton up to TNH Scholar code standards.

- **Status**: Proposed
- **Type**: Implementation Guide
- **Date**: 2026-03-06
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, GPT-5 Codex
- **Parent ADR**: [ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)
- **Related ADRs**:
  - [ADR-OA04.1](/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md)
  - [ADR-OA03.3](/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-runner.md)
  - [ADR-OS01](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

ADR-OA04 and ADR-OA04.1 intentionally define a **walking skeleton** for tnh-conductor. The walking skeleton is not throwaway code. It is the implementation base we intend to extend, harden, and depend on for future agent-orchestration work.

That design intent changes the quality bar:

1. Code on the MVP path must meet TNH Scholar design standards, not merely spike sufficiency.
2. CLI runner code originally created under de-risking ADR-OA03.3 can no longer be treated as isolated spike code if the MVP kernel depends on its concepts, contracts, or execution patterns.
3. Security review findings on subprocess boundaries exposed a deeper issue: several agent-orchestration modules still use low-level command vectors and stringly typed control surfaces where the repo standard requires typed models, protocol boundaries, and provider-owned translations.

This ADR records the current audit findings that motivated the redesign work now captured in ADR-OA07, and defines the core compliance gaps the prototype implementation exposed:

- [Design principles](/development/design-principles.md)
- [Style guide](/development/style-guide.md)
- [ADR-OS01 object-service architecture](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md)
- [ADR-OA07 MVP Runtime Architecture Strategy](/architecture/agent-orchestration/adr/adr-oa07-mvp-runtime-architecture-strategy.md)

### Audit Scope

This audit covers the current agent-orchestration implementation surface:

- `src/tnh_scholar/agent_orchestration/conductor_mvp/`
- `src/tnh_scholar/agent_orchestration/spike/`
- `src/tnh_scholar/agent_orchestration/common/`
- `src/tnh_scholar/agent_orchestration/codex_harness/`
- `src/tnh_scholar/cli_tools/tnh_conductor_spike/`
- `tests/agent_orchestration/`

### Audit Findings

#### 1. Raw command vectors remain in critical infrastructure boundaries

The most serious issue is the continued use of naked argv shapes (`list[str]`, `tuple[str, ...]`) as provider or protocol payloads for agent and validator execution.

Examples:

- `src/tnh_scholar/agent_orchestration/conductor_mvp/models.py:209`
- `src/tnh_scholar/agent_orchestration/conductor_mvp/providers/validation_runner.py:134`
- `src/tnh_scholar/agent_orchestration/spike/protocols.py:62`
- `src/tnh_scholar/agent_orchestration/spike/protocols.py:134`
- `src/tnh_scholar/agent_orchestration/spike/providers/command_builder.py:15`
- `src/tnh_scholar/agent_orchestration/spike/providers/subprocess_agent_runner.py:48`
- `src/tnh_scholar/agent_orchestration/spike/providers/pty_agent_runner.py:45`

This is below repo standards even when command authorship is restricted to trusted provider code. The problem is architectural, not just operational. Execution should be represented as typed command objects, with argv rendering deferred to the final subprocess edge.

#### 2. Spike code has crossed the promotion boundary

The `spike/` package is no longer purely disposable experimentation. Parts of it now serve as the effective model for CLI runner behavior in the MVP path.

That means the current naming is misleading:

- it suggests throwaway code
- it lowers review expectations
- it obscures which modules are now operational dependencies

If code remains on the forward path, it must either:

- be preserved as reference-only spike code, while a new maintained replacement is built, or
- be replaced directly by a standards-compliant runtime package

#### 3. Oversized orchestration services and mixed responsibilities

Two files are well beyond the cohesion and responsibility limits described in the design principles:

- `src/tnh_scholar/agent_orchestration/conductor_mvp/service.py`
- `src/tnh_scholar/agent_orchestration/spike/service.py`

These modules combine:

- graph/catalog traversal
- validation logic
- runtime execution
- event emission
- artifact persistence coordination
- state transitions
- workspace lifecycle behavior

The result is a walking skeleton that works, but is too difficult to reason about, validate, and safely evolve.

#### 4. Duplicate runner control loops and process-management logic

`PtyAgentRunner` and `SubprocessAgentRunner` share substantial output-collection, timeout, prompt-handling, heartbeat, and termination logic, but currently implement these concerns separately.

Examples:

- `src/tnh_scholar/agent_orchestration/spike/providers/pty_agent_runner.py`
- `src/tnh_scholar/agent_orchestration/spike/providers/subprocess_agent_runner.py`

This duplication increases the chance of safety fixes landing in one runner path but not the other.

#### 5. Domain models still rely heavily on raw strings for control semantics

Several important orchestration concepts remain stringly typed where explicit enums or typed identifiers should exist.

Examples:

- `SpikeParams.agent: str`
- `RunAgentStep.agent: str`
- `WorkflowDefaults.component_kind: str | None`
- `WorkflowDefaults.eval_profile: str | None`
- `RouteRule.target: str`

Some string use is unavoidable for human-authored workflow identifiers, but several current surfaces are underspecified compared with repo standards.

#### 6. YAML loading still uses ad hoc dict normalization at the adapter boundary

`YamlWorkflowLoader` still normalizes YAML through `dict[str, Any]` structures and manual shape branching:

- `src/tnh_scholar/agent_orchestration/conductor_mvp/adapters/workflow_loader.py`

This is acceptable as an adapter concern in principle, but the current implementation is still too unstructured and too aware of low-level shape details. It should be tightened so the adapter is only responsible for external representation normalization, not workflow semantics.

#### 7. Codex harness is closer to standards, but not fully aligned

`codex_harness/` is generally stronger than the `spike/` surface because it uses typed tool-call models and clearer object boundaries. However, it still contains:

- low-level `dict[str, object]` and `dict[str, Any]` shapes for OpenAI transport payloads
- subprocess providers that should be reviewed with the same rigor as the runner path
- some stringly request fields that should be audited before further expansion

This area is lower-risk than the conductor/spike boundary, but it belongs in the same hardening program.

---

## Decision

### 1. Treat the agent-orchestration walking skeleton as promotable code

The OA04 walking skeleton is the base for future implementation. It must therefore be hardened to repo standards rather than tolerated as provisional spike code.

### 2. Run one unified hardening effort under OA04

We will handle MVP hardening as a single OA04 follow-up effort, not as disconnected cleanup items.

The hardening scope includes:

- conductor MVP kernel
- CLI runner path currently under `spike/`
- shared agent-orchestration primitives
- CLI entrypoints that expose these paths
- codex harness review where it intersects the same standards

### 3. Preserve `spike/` as reference and build a maintained replacement beside it

We will not continue promoting the current `agent_orchestration/spike/` package in place.

Instead:

- `spike/` remains as a documented historical/reference artifact for OA02 and OA03.3
- a new maintained module will be created for the forward MVP runtime path
- imports, CLI entrypoints, and future implementation work will shift to the maintained module
- spike cleanup, archival, and documentation simplification can happen later once the maintained path is stable

This preserves historical traceability without forcing the MVP path to inherit spike naming or structure indefinitely.

### 4. Replace raw command vectors with typed execution command models

This is the first required architectural correction.

We will:

- remove naked argv tuples/lists from conductor and runner protocol surfaces
- introduce **separate typed execution command models** for validator and agent invocation
- move argv rendering to the final subprocess edge only
- ensure protocol contracts exchange typed objects, not low-level shell/process representations

The agent and validator domains should not be collapsed into one generic command object. They have different semantics and should keep distinct typed contracts.

### 5. Split oversized orchestration services into smaller collaborators

We will decompose large coordination modules into explicit collaborators.

#### Conductor target split

`conductor_mvp/service.py` should be split into typed units such as:

- workflow catalog / graph traversal helper
- workflow validator
- runtime step executor
- kernel state / trace management
- route resolution policy

#### Runner target split

`spike/service.py` should be split into collaborators such as:

- preflight policy service
- workspace preparation/finalization service
- artifact persistence coordinator
- event emission coordinator
- runner invocation coordinator

### 6. Consolidate duplicate runner mechanics

We will extract shared process-management logic into a shared execution substrate where appropriate.

That shared substrate may cover:

- timeout enforcement
- heartbeat scheduling
- output capture emission
- subprocess result normalization
- working-directory and process policy enforcement

However, PTY support does not need to be promoted into the maintained MVP path at this time. The existing PTY runner can remain in `spike/` as a reference implementation unless a maintained requirement emerges later.

### 7. Raise typing strictness for orchestration domain semantics

We will incrementally replace ambiguous string fields with typed alternatives where the values represent fixed semantics rather than free-form content.

Priority candidates:

- agent identifiers
- component/eval profile hints
- runner mode or execution family identifiers
- validator identifiers

### 8. Record hardening work as phased remediation, not one massive rewrite

The remediation will proceed in bounded phases so we keep momentum and reviewability.

---

## Remediation Plan

### Phase 1: Security and contract hardening

Required first:

1. Replace conductor validator argv tuples with typed execution command objects.
2. Replace runner command builder/runner protocol exchange of `list[str]` with typed agent command models.
3. Add explicit typed agent identifiers for runner selection.
4. Introduce typed validator command models for `RUN_VALIDATION`.
5. Ensure subprocess providers are only fed trusted typed execution objects rendered only at the executor edge.

### Phase 2: Service decomposition

Required next:

1. Split conductor runtime responsibilities out of `service.py`.
2. Split spike orchestration responsibilities out of `service.py`.
3. Consolidate route lookup / traversal helpers where duplicated.
4. Extract shared runner control-loop mechanics.

### Phase 3: Maintained-module build-out and naming cleanup

Required before concluding the hardening sequence:

1. Build the maintained replacement module beside `spike/`.
2. Move forward-path imports and runtime wiring onto the maintained module.
3. Rename `tnh_conductor_spike` CLI if it remains the forward execution surface.
4. Update ADR references to distinguish archived spike findings from maintained runtime code.
5. Leave `spike/` in place as historical/reference code until later cleanup.

### Phase 4: Secondary compliance pass

Follow-on review after the primary corrections:

1. Review `codex_harness/` against the same standards.
2. Tighten remaining transport-layer `dict` payloads where practical.
3. Re-run Sourcery and code review on all touched modules.

---

## Consequences

### Positive

- Aligns the agent-orchestration codebase with the declared intent of OA04 as a walking skeleton.
- Reduces security-review friction caused by low-level command-vector contracts.
- Makes future extension of runner and kernel behavior safer and more reviewable.
- Clarifies which code is experimental history versus maintained runtime surface.

### Negative

- Introduces near-term refactoring work before new feature expansion.
- Some merged code will need structural change soon after landing.
- Renaming `spike/` modules will cause churn across imports, docs, and CLI references.

---

## Alternatives Considered

### 1. Leave spike code as-is until later feature pressure forces cleanup

Rejected. This would normalize weak boundaries in code we already intend to build upon.

### 2. Treat the subprocess findings as lint/tooling noise and patch locally around them

Rejected. The review findings exposed a real architectural mismatch with repo standards.

### 3. Write a separate ADR for spike hardening

Rejected. The spike runner path is now part of the same MVP hardening problem. Splitting the decision record would obscure that promotion boundary.

---

## Open Questions

1. Should the maintained replacement for `spike/` live under `agent_orchestration/runners/` or a more explicit package name?
2. How much of `codex_harness/` should be included in the first hardening pass versus a second pass?

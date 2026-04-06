---
title: "ADR-OA04.5: Harness Backend Contract"
description: "Defines the maintained backend contract for executing generated and predefined validation harnesses under RUN_VALIDATION."
type: "design-detail"
owner: "aaronksolomon"
author: "Aaron Solomon, GPT-5 Codex"
status: implemented
created: "2026-03-27"
parent_adr: "adr-oa04-workflow-schema-opcode-semantics.md"
related_adrs:
  - "adr-oa04.3-provenance-run-artifact-contract.md"
  - "adr-oa04.4-policy-enforcement-contract.md"
  - "adr-oa04.1-implementation-notes-mvp-buildout.md"
  - "adr-oa06-planner-evaluator-contract.md"
---

# ADR-OA04.5: Harness Backend Contract

Defines the maintained backend contract for executing generated and predefined validation harnesses under `RUN_VALIDATION`.

- **Status**: Implemented
- **Type**: Design Detail
- **Date**: 2026-03-27
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, GPT-5 Codex
- **Parent ADR**: [ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)
- **Related ADRs**:
  - [ADR-OA04.3](/architecture/agent-orchestration/adr/adr-oa04.3-provenance-run-artifact-contract.md)
  - [ADR-OA04.4](/architecture/agent-orchestration/adr/adr-oa04.4-policy-enforcement-contract.md)
  - [ADR-OA04.1](/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md)
  - [ADR-OA06](/architecture/agent-orchestration/adr/adr-oa06-planner-evaluator-contract.md)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

[ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md) deliberately keeps generative evaluation inside `RUN_VALIDATION` rather than introducing new opcodes. [ADR-OA04.1](/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md) then calls for CLI and web harness backends later in the build-out sequence.

What remains under-specified is the maintained contract for harness backends themselves:

- how generated harnesses are invoked,
- how different backend families normalize results,
- how artifact capture relates to backends,
- where backend-specific logic stops and validation service logic resumes.

Without OA04.5, "script validator with artifacts" is enough for MVP shell code, but too weak for a maintained multi-backend validation design.

---

## Decision

### 1. Harnesses Remain Validators, Not Opcodes

Harness execution stays inside `RUN_VALIDATION`.

"Harness backend" is an execution detail of validation, not a new workflow primitive.

This preserves OA04's opcode discipline while allowing richer validation surfaces.

### 2. Backend Family Contract

The maintained validation subsystem recognizes backend families for harness execution:

- `script`
- `cli`
- `web`

`script` is the MVP baseline.

`cli` and `web` are planned maintained backend families, not separate opcode semantics.

For implementation sequencing, only the `script` backend family is in scope for the first maintained backend PR. `cli` and `web` should remain protocol-level planned families until a concrete maintained consumer requires them.

### 3. Backend Request Boundary

Every harness backend execution request MUST provide:

- backend family,
- entrypoint or executable reference,
- arguments or scenario input,
- working directory,
- declared artifact capture patterns,
- timeout and environment constraints.

This boundary is backend-neutral at the validation service layer.

For maintained implementation handoff, only the `script` backend family is frozen as workflow-addressable today. `cli` and `web` remain planned backend families whose workflow/schema exposure is deferred until a later OA04 addendum or OA04 revision explicitly extends validator selection semantics.

### 4. Backend Result Boundary

Every harness backend execution result MUST normalize to:

- termination,
- captured artifact paths,
- optional structured report path,
- stdout/stderr captures where relevant.

Backends may produce additional native outputs, but they must normalize into the maintained validation artifact contract.

### 5. Structured Report Requirement

When a harness is intended for planner consumption, it MUST emit a structured report artifact compatible with OA04 Section 9 harness report expectations and OA06 evaluator consumption expectations.

Backends are responsible for execution; report semantics remain shared across backend families.

### 6. Backend Family Responsibilities

#### Script Backend

- Executes a local script entrypoint.
- Best fit for generated harness code and deterministic test wrappers.
- MVP baseline and required maintained backend.

#### CLI Backend

- Executes a CLI tool or scenario runner against the repo artifact under test.
- Best fit for command-line products and interaction scripts.
- Normalizes console output and generated logs into maintained artifact roles.
- Deferred from the first maintained implementation slice.

#### Web Backend

- Executes headless browser or browser-driven harnesses.
- Best fit for UI validation, screenshots, and visual regression flows.
- Normalizes screenshots, traces, and structured reports into maintained artifact roles.
- Deferred from the first maintained implementation slice.

### 7. Artifact Role Conventions

OA04.5 uses the canonical manifest role vocabulary from [ADR-OA04.3](/architecture/agent-orchestration/adr/adr-oa04.3-provenance-run-artifact-contract.md).

Required mappings:

- harness report artifacts map to `validation_report`
- harness stdout artifacts map to `validation_stdout`
- harness stderr artifacts map to `validation_stderr`

Additional backend-local artifacts may be recorded using additional roles when needed, including:

- `harness_screenshot`
- `harness_trace`
- `harness_fixture`

`harness_fixture` refers to supporting files required to run or interpret a harness, such as generated input cases, seeded data, snapshots, or scenario descriptors.

### 8. Environment and Safety

Harness backends execute under the same broad workflow safety posture:

- worktree isolation,
- sanitized environment,
- explicit timeout controls,
- no special bypass around policy enforcement.

Backend-specific sandboxing may vary, but backends must surface their execution constraints clearly in metadata.

### 9. Backend Selection

Workflow authors do not select backend families through new opcodes.

Backend selection is derived from validator specification and validation service configuration.

Generated harness prompts may target a preferred backend using workflow hints like `component_kind`, defined in [ADR-OA04.1](/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md) Section 5b, but these hints have no direct kernel semantics.

### 10. Deferred Surfaces

The following remain deferred:

- VS Code UI automation backend,
- mobile or desktop GUI harness backends,
- flake-detection orchestration,
- performance-budget-specific backend semantics.

---

## Consequences

### Positive

- Gives `RUN_VALIDATION` a scalable multi-backend path without opcode growth.
- Preserves a clean split between workflow semantics and backend execution detail.
- Makes future Playwright-style and CLI harnesses fit into one maintained family.

### Negative

- Introduces another normalization layer inside validation.
- Requires discipline to keep backend differences out of kernel semantics.

---

## Alternatives Considered

### A. Introduce a dedicated HARNESS opcode

Rejected: unnecessary opcode growth and semantic duplication.

### B. Keep all harnesses as opaque scripts forever

Rejected: workable for MVP, but too weak for maintained CLI and web backend design.

### C. Encode backend details directly in prompts

Rejected: backend execution is runtime contract, not prompt-only behavior.

---

## Open Questions

- Should `cli` and `web` backend families be frozen now even if only `script` is implemented first?
- Should screenshot and trace artifact metadata be standardized further in this ADR family, or left to backend-local schemas initially?

## Future Considerations

- Once real CLI and web harnesses exist in maintained code, a later addendum can freeze how validator declarations select backend family without forcing that schema surface prematurely.

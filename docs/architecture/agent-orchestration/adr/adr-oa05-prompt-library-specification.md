---
title: "ADR-OA05: Prompt Library Specification"
description: "Defines prompt artifact schema, versioning, rendering, and catalog validation contracts for tnh-conductor prompt-program behavior."
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Code, GPT-5 Codex"
status: proposed
created: "2026-02-09"
updated: "2026-02-11"
parent_adr: "adr-oa01.1-conductor-strategy-v2.md"
related_adrs:
  - "adr-oa04-workflow-schema-opcode-semantics.md"
  - "adr-oa04.1-implementation-notes-mvp-buildout.md"
  - "adr-oa06-planner-evaluator-contract.md"
---

# ADR-OA05: Prompt Library Specification

Defines prompt artifact schema, versioning, rendering, and catalog validation contracts for tnh-conductor prompt-program behavior.

- **Status**: Proposed
- **Type**: Component ADR
- **Date**: 2026-02-11
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, Claude Code, GPT-5 Codex
- **Parent ADR**: [ADR-OA01.1](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md)
- **Related ADRs**:
  - [ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)
  - [ADR-OA04.1](/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md)
  - [ADR-OA06](/architecture/agent-orchestration/adr/adr-oa06-planner-evaluator-contract.md)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

[ADR-OA01.1](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md) establishes the prompt library as the behavioral "standard library" of conductor workflows. [ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md) defines opcode and routing mechanics, but defers prompt artifact definition and catalog validation to OA05.

[ADR-OA06](/architecture/agent-orchestration/adr/adr-oa06-planner-evaluator-contract.md) now defines planner evaluator I/O, which requires prompt artifacts to declare compatible input and output contracts.

Without OA05, workflows can reference prompts but cannot be compile-validated for:

- prompt existence,
- version compatibility,
- input contract correctness,
- output contract correctness for `EVALUATE`.

---

## Decision

### 1. Prompt Role Taxonomy

OA05 standardizes prompt roles. Canonical role set:

- `task`
- `planner`
- `policy`
- `triage`
- `risk`
- `journal`

Decision on harness prompts:

- Harness synthesis remains `role: task`.
- No new top-level `harness` role is introduced in MVP.
- Harness behavior is expressed via `capabilities`, for example `capabilities: [harness_synthesis]`.

This avoids taxonomy sprawl while preserving explicit intent.

### 2. Prompt Reference and Versioning Contract

Prompt references in workflows MUST be immutable version references:

- `prompt_id`: dotted identifier without version (example: `planner.evaluate_harness_report`)
- `version`: positive integer
- canonical reference string: `<prompt_id>.v<version>`

Rules:

- Workflows MUST reference canonical versioned refs.
- Prompt content for a given `prompt_id + version` is immutable once accepted.
- Breaking behavior change requires new version.
- Backward-incompatible changes are allowed in project version `0.x`, but must fail fast at workflow compile/validation time if refs are invalid.

### 3. Prompt Artifact Schema (Normative)

Prompt artifacts are Markdown files with YAML frontmatter + template body.

Required frontmatter fields:

| Field | Type | Description |
|-------|------|-------------|
| `prompt_id` | string | Stable unversioned prompt identifier |
| `version` | int | Prompt version |
| `role` | enum | One of OA05 canonical roles |
| `summary` | string | Short behavior description |
| `inputs` | list[object] | Input contract declarations |
| `output_contract` | object | Structured output expectations |
| `owner` | string | Prompt owner |
| `status` | enum | `draft`, `current`, `deprecated`, `archived` |

Optional frontmatter fields:

- `capabilities` (list strings)
- `model_hints` (object)
- `safety_notes` (list strings)
- `deprecates` (prompt ref)

Example (planner prompt):

```yaml
---
prompt_id: "planner.evaluate_harness_report"
version: 1
role: "planner"
summary: "Classify validation evidence into bounded conductor status."
owner: "tnh-scholar"
status: "current"
inputs:
  - name: "allowed_next_steps"
    type: "list[string]"
    required: true
  - name: "evidence"
    type: "planner_evidence.v1"
    required: true
output_contract:
  schema_ref: "planner_decision.v1"
  required_fields: ["status", "next_step", "fix_instructions", "blockers", "risk_flags"]
---
```

### 4. Input Contract Rules

Each prompt input declaration requires:

- `name`
- `type`
- `required`

Optional:

- `description`
- `source` (`workflow_input`, `artifact`, `provenance`, `system`)

Compile-time validation rules:

- Every required prompt input must be satisfiable from workflow/context assembly.
- Unknown required input sources fail validation.
- For `EVALUATE`, required inputs must include OA06 contract-critical fields (`allowed_next_steps`, `evidence`).

### 5. Output Contract Rules

`output_contract` is mandatory for all prompts.

Rules by role:

- `planner` prompts MUST target `schema_ref: planner_decision.v1` (or future OA06-compatible schema).
- `task` prompts MAY specify artifact expectations instead of structured JSON schema.
- `policy`, `triage`, `risk`, `journal` prompts MUST specify declared output shape for consuming component.

Task prompt artifact contract example:

```yaml
output_contract:
  artifacts:
    - path: ".tnh/run/${run_id}/harness/harness.py"
      required: true
    - path: ".tnh/run/${run_id}/harness/suite.yaml"
      required: true
```

### 6. Template Rendering Rules

Rendering engine contract (MVP):

- Engine: Jinja2.
- Undefined behavior: strict failure on missing required variables.
- Input context is explicitly assembled by control plane (`tnh-gen`) from declared sources.
- Rendering must be deterministic for identical inputs.

Safety constraints:

- No arbitrary filesystem includes/imports from templates.
- No dynamic execution hooks beyond allowlisted filters/helpers.
- Prompt rendering failure is a hard workflow error.

### 7. Prompt Catalog Resolution and Precedence

Prompt resolution follows runtime context precedence:

1. Workspace prompt catalog
2. User prompt catalog
3. Built-in prompt catalog

This aligns with TNH context layering from [ADR-CF01](/architecture/configuration/adr/adr-cf01-runtime-context-strategy.md).

Catalog protocol responsibilities:

- Resolve canonical prompt ref to artifact.
- Return parsed metadata + body.
- Validate role/input/output contract integrity.
- Support listing by role and capability.

### 8. Workflow-to-Prompt Compile Validation

Before run execution, workflow compile/validation MUST check:

1. Every referenced prompt ref exists.
2. `RUN_AGENT.prompt` references role `task` (or other explicitly allowed role by policy).
3. `EVALUATE.prompt` references role `planner` with OA06-compatible output contract.
4. `policy` fields reference role `policy` prompts.
5. Required prompt inputs are satisfiable from workflow context.

Invalid prompt references are hard failures before opcode execution.

### 9. Testing and Fixture Requirements

OA05 requires fixture coverage for prompt contracts:

- valid planner prompt fixture (`planner_decision.v1` output contract)
- invalid planner prompt fixture (missing required output fields)
- valid harness synthesis task prompt fixture
- invalid input-source fixture (unresolvable required input)
- deprecated version resolution fixture

These fixtures should back compile-time prompt validation tests.

---

## Consequences

### Positive

- Enables compile-time validation of workflow-to-prompt wiring.
- Reduces runtime ambiguity in planner and task prompt behavior.
- Supports safe prompt evolution via explicit versioning and role contracts.
- Keeps harness prompts integrated without introducing a new top-level role taxonomy.

### Negative

- Increases prompt authoring overhead (metadata and contract declarations).
- Requires catalog tooling to parse and validate richer frontmatter schema.
- Introduces stricter failure modes for missing or invalid prompt metadata.

---

## Alternatives Considered

### A. Introduce `role: harness` as a new top-level role

Rejected for MVP: adds taxonomy complexity without kernel/runtime benefit.

### B. Unversioned prompt references (`prompt_id` only)

Rejected: breaks auditability and deterministic replay guarantees.

### C. Runtime-only prompt validation

Rejected: allows invalid prompt wiring to fail late during execution.

---

## Open Questions

1. Should OA05 formalize profile-specific prompt selection (`smoke`, `overnight`, `release_candidate`) as catalog policy now, or defer to OA05.1?
2. Should prompt deprecation policy include automatic replacement hints for workflow compilation errors?

---

## Implementation Notes

- Add typed prompt artifact models in the prompt system domain layer.
- Add catalog validator that enforces OA05 role/input/output rules.
- Add workflow compile hook that validates all prompt refs before kernel start.

---

## Related ADRs

- [ADR-OA01.1: TNH-Conductor Strategy v2](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md)
- [ADR-OA04: Workflow Schema + Opcode Semantics](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)
- [ADR-OA04.1: Implementation Notes - MVP Build-Out Sequence](/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md)
- [ADR-OA06: Planner Evaluator Contract](/architecture/agent-orchestration/adr/adr-oa06-planner-evaluator-contract.md)

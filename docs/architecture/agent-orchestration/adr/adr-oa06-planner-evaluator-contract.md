---
title: "ADR-OA06: Planner Evaluator Contract"
description: "Defines planner evaluator I/O schemas, status derivation, contradiction rules, and deterministic decision vectors for EVALUATE steps."
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Code, GPT-5 Codex"
status: proposed
created: "2026-02-09"
updated: "2026-02-11"
parent_adr: "adr-oa01.1-conductor-strategy-v2.md"
related_adrs:
  - "adr-oa04-workflow-schema-opcode-semantics.md"
  - "adr-oa04.1-implementation-notes-mvp-buildout.md"
  - "adr-oa05-prompt-library-specification.md"
---

# ADR-OA06: Planner Evaluator Contract

Defines planner evaluator I/O schemas, status derivation, contradiction rules, and deterministic decision vectors for `EVALUATE` steps.

- **Status**: Proposed
- **Type**: Component ADR
- **Date**: 2026-02-11
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, Claude Code, GPT-5 Codex
- **Parent ADR**: [ADR-OA01.1](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md)
- **Related ADRs**:
  - [ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)
  - [ADR-OA04.1](/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md)
  - [ADR-OA05](/architecture/agent-orchestration/adr/adr-oa05-prompt-library-specification.md)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

[ADR-OA01.1](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md) defines the planner evaluator as the only semantic decision locus. [ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md) defines kernel opcodes and deterministic routing constraints, but intentionally leaves semantic interpretation rules to a dedicated planner contract.

This separation is critical:

- Kernel stays small, deterministic, and mechanically testable.
- Planner absorbs semantic interpretation of transcripts, diffs, validator artifacts, and harness reports.
- Workflow authors get stable routing semantics (`status` values + legal transitions) without embedding decision trees in code.

Open design work from OA04/OA04.1 now requires OA06 to lock:

1. A canonical planner input envelope for `EVALUATE`.
2. A canonical planner output schema.
3. Status derivation precedence, including golden handling.
4. Contradiction detection rules.
5. Deterministic test vectors for implementation validation.

---

## Decision

### 1. Contract Layering and Ownership

The planner contract is layered across ADRs as follows:

| ADR | Role |
|-----|------|
| OA01.1 | Conceptual full planner role and future-facing behavior |
| OA04 | Kernel routing constraints and deterministic opcode semantics |
| OA04.1 | MVP minimum fields needed for routing correctness |
| OA06 | Normative planner I/O schema and semantic derivation rules |

Kernel responsibilities remain unchanged from OA04:

- Validate workflow graph and legal routes.
- Execute opcodes deterministically.
- Enforce legal transition invariants.
- Never interpret free-form text.

Planner responsibilities in OA06:

- Interpret semantic evidence.
- Emit structured decision object.
- Emit escalation/fix metadata for subsequent steps.

### 2. Planner Input Envelope (Normative)

`EVALUATE` receives a structured input envelope. Required top-level fields:

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | Current conductor run id |
| `workflow_id` | string | Workflow identifier |
| `step_id` | string | Current evaluate step id |
| `evaluate_prompt` | string | Prompt reference (`id.vN`) |
| `allowed_next_steps` | array[string] | Bounded legal next steps from workflow |
| `provenance_window` | array[object] | Last `K` step summaries (default `K=3`) |
| `evidence` | object | Current step evidence package |

`evidence` fields (required unless marked optional):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transcript_summary` | string | yes | Structured summary of agent/validator output |
| `workspace_diff_summary` | string | yes | Structured diff summary |
| `validation` | object | yes | Deterministic validation summary |
| `harness_report` | object/null | no | Parsed harness report payload |
| `artifacts` | array[string] | yes | Referenced artifact paths |
| `policy_events` | array[string] | yes | Policy/safety signals from kernel |

`validation` minimum fields:

- `mechanical_outcome`
- `exit_codes` (map by validator id)
- `timeouts` (array validator ids)

### 3. Planner Output Contract (Normative)

Planner MUST return a structured object with this shape:

```yaml
status: success | partial | blocked | unsafe | needs_human
next_step: string | null
fix_instructions: object | null
blockers: list[object]
risk_flags: list[string]
```

`fix_instructions` object (if provided):

```yaml
objective: string
constraints: list[string]
edits:
  - target: string
    action: string
    rationale: string
verification:
  - command: string
    expected_signal: string
```

`blockers` entry shape:

```yaml
code: string
summary: string
evidence_ref: string | null
severity: low | medium | high
```

MVP routing dependency remains OA04.1-compliant:

- Kernel only depends on `status` and bounded `next_step` legality.
- `fix_instructions`, `blockers`, and `risk_flags` are consumed by downstream prompts and gate context.

### 4. Status Derivation Precedence

Planner MUST classify status using this precedence (top to bottom):

1. `unsafe`
2. `needs_human`
3. `blocked`
4. `partial`
5. `success`

Derivation rules:

| Condition | Status |
|-----------|--------|
| Policy violation, forbidden operation, or contradiction indicating untrusted state | `unsafe` |
| `proposed_goldens` non-empty, required human approval, or escalation threshold exceeded | `needs_human` |
| No safe forward action (missing critical artifacts, non-recoverable failure, repeated hard failure) | `blocked` |
| Recoverable failures with clear fix path | `partial` |
| All required checks satisfied and no escalation conditions | `success` |

Golden rule alignment:

- If `harness_report.proposed_goldens` is non-empty, planner MUST emit `needs_human`.
- This aligns with OA04 static+runtime gate constraints and avoids direct success-to-stop routing.

### 5. Contradiction Detection Rules

Planner MUST detect transcript/workspace contradictions and emit risk flags.

Required contradiction checks:

| Claim/Evidence Mismatch | Required Action |
|-------------------------|-----------------|
| Agent claims "implemented" but diff is empty for implementation intent | Emit `risk_flags += ["transcript_workspace_mismatch"]`; classify `partial` or `unsafe` |
| Validation claims pass but required artifact is missing | Emit `risk_flags += ["missing_artifact"]`; classify `blocked` or `unsafe` |
| Harness report indicates pass while deterministic validator failed | Emit `risk_flags += ["report_execution_mismatch"]`; classify `unsafe` |
| Repeated contradictory output across loop iterations | Emit `risk_flags += ["repeated_contradiction"]`; classify `needs_human` or `unsafe` |

### 6. `next_step` Semantics and Constraints

`next_step` is planner intent, bounded by workflow legality.

Rules:

- If present, `next_step` MUST be in `allowed_next_steps`.
- Planner MAY return `next_step: null` when status implies terminal routing by policy.
- For `partial`, planner SHOULD provide `next_step` pointing to fix/adjust path.
- For `needs_human`, planner SHOULD provide `next_step` pointing to gate path.
- For `unsafe`, planner SHOULD provide `next_step` pointing to rollback or gate path.

Kernel remains source of truth for legal routing via OA04 route maps.

### 7. Provenance Window and Escalation Policy

Default provenance window:

- Include last `K=3` completed steps before current `EVALUATE`.
- Each window entry includes: `step_id`, `opcode`, `status/outcome`, `diff_summary`, `risk_flags`, `blocker_codes`.

Escalation thresholds:

| Pattern | Required Escalation |
|---------|---------------------|
| 3 consecutive `partial` statuses | Escalate to `needs_human` |
| Same blocker code repeated twice with no net diff improvement | Escalate to `needs_human` |
| Any contradiction after previous contradiction flag | Escalate to `unsafe` |

### 8. Deterministic Decision Vectors (Required)

OA06 defines a required fixture set for implementation validation.

| Vector ID | Input Summary | Expected Status |
|-----------|---------------|-----------------|
| `vector_success_clean` | Validators pass, no risk flags, no goldens | `success` |
| `vector_partial_fixable` | One failed case with clear repro and fix path | `partial` |
| `vector_blocked_missing_artifact` | Required artifact missing, no safe fallback | `blocked` |
| `vector_unsafe_policy_violation` | Forbidden path edit detected | `unsafe` |
| `vector_needs_human_goldens` | `proposed_goldens` non-empty | `needs_human` |
| `vector_needs_human_repeat_partial` | 3 consecutive partial loops | `needs_human` |
| `vector_unsafe_report_mismatch` | Harness says pass, validator exit non-zero | `unsafe` |
| `vector_partial_transcript_mismatch` | Claimed completion with empty diff | `partial` |

Required assertions per vector:

- `status` exact match.
- If `next_step` present, it is legal.
- `risk_flags` includes expected canonical flag where applicable.

### 9. Canonical Risk Flag Set (MVP)

Reserved OA06 risk flags for consistent downstream handling:

- `transcript_workspace_mismatch`
- `missing_artifact`
- `report_execution_mismatch`
- `policy_violation`
- `proposed_goldens_present`
- `repeated_partial_loop`
- `repeated_contradiction`

Additional flags are allowed, but these names are stable for MVP.

---

## Consequences

### Positive

- Locks a deterministic planner contract while preserving prompt-program flexibility.
- Makes planner behavior testable via fixture vectors before full orchestration UI/CLI wiring.
- Clarifies kernel/planner boundaries and prevents semantic drift into opcode execution code.
- Improves loop safety with explicit contradiction and escalation rules.

### Negative

- Adds stricter schema expectations for prompt authors and adapters.
- Requires additional fixture maintenance as planner prompts evolve.
- May force early normalization work for legacy free-form planner outputs.

---

## Alternatives Considered

### A. Free-form planner output + heuristic parsing

Rejected: brittle, non-deterministic, and incompatible with OA04 mechanical routing guarantees.

### B. Move status derivation into kernel code

Rejected: violates OA01.1 architecture (decision intelligence should stay prompt-defined and planner-owned).

### C. Omit contradiction detection in MVP

Rejected: unsafe for unattended loops and weakens provenance trust model.

---

## Open Questions

1. Should OA06 define severity mapping for `ux_flags` directly, or leave to prompt-level profile policies?
2. Should confidence scoring (`0.0-1.0`) be added to planner output in OA06 now, or deferred to OA06.1?

---

## Implementation Notes

- OA06 output schema should map to typed domain model(s) in conductor MVP and control-plane adapters.
- Add fixture files under `tests/agent_orchestration/fixtures/planner_vectors/` for the required vector set.
- Keep `status` enum names aligned with OA04 route outcomes.

---

## Related ADRs

- [ADR-OA01.1: TNH-Conductor Strategy v2](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md)
- [ADR-OA04: Workflow Schema + Opcode Semantics](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)
- [ADR-OA04.1: Implementation Notes - MVP Build-Out Sequence](/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md)
- [ADR-OA05: Prompt Library Specification](/architecture/agent-orchestration/adr/adr-oa05-prompt-library-specification.md)

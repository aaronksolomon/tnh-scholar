---
title: "ADR-OA04.3: Provenance and Run-Artifact Contract"
description: "Defines the maintained run directory, artifact manifest, and event/provenance handoff contract for workflow execution."
type: "design-detail"
owner: "aaronksolomon"
author: "Aaron Solomon, GPT-5 Codex"
status: implemented
created: "2026-03-27"
parent_adr: "adr-oa04-workflow-schema-opcode-semantics.md"
related_adrs:
  - "adr-oa04.2-runner-contract.md"
  - "adr-oa04.4-policy-enforcement-contract.md"
  - "adr-oa04.1-implementation-notes-mvp-buildout.md"
  - "adr-oa06-planner-evaluator-contract.md"
---

# ADR-OA04.3: Provenance and Run-Artifact Contract

Defines the maintained run directory, artifact manifest, and event/provenance handoff contract for workflow execution.

- **Status**: Implemented
- **Type**: Design Detail
- **Date**: 2026-03-27
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, GPT-5 Codex
- **Parent ADR**: [ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)
- **Related ADRs**:
  - [ADR-OA04.2](/architecture/agent-orchestration/adr/adr-oa04.2-runner-contract.md)
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

[ADR-OA01.1](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md) makes provenance and durable artifacts central to the orchestration design. [ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md) defines artifact conventions and step execution semantics, while [ADR-OA04.2](/architecture/agent-orchestration/adr/adr-oa04.2-runner-contract.md) freezes the runner-facing normalized artifacts.

What remains under-specified is the maintained contract for:

- run directory shape,
- step artifact indexing,
- event stream structure,
- provenance handoff into `tnh-gen`,
- how later evaluator assembly resolves artifacts reliably.

Without OA04.3, the runtime can write files, but the system still lacks a stable maintained answer to:

- which files are canonical versus adapter-local,
- how a later component resolves "the transcript for step X",
- how event and artifact identity remain stable across replay, review, and evaluation.

---

## Decision

### 1. Scope

OA04.3 defines the maintained **execution artifact contract** for one workflow run.

It covers:

- run directory structure,
- required run-level files,
- required step-level artifact indexing,
- normalized event stream expectations,
- the minimum handoff contract from runtime artifacts to provenance systems.

It does **not** freeze the full `tnh-gen` ledger schema or retention implementation details.

### 2. Canonical Run Directory

Every workflow run MUST materialize a canonical run directory under the configured artifacts root:

```text
.tnh/run/<run_id>/
  metadata.json
  final-state.txt
  events.ndjson
  artifacts/
    <step_id>/
      manifest.json
      ...
```

Required run-level files:

| File | Purpose |
|------|---------|
| `metadata.json` | Run metadata and workflow identity |
| `final-state.txt` | Terminal workflow state summary |
| `events.ndjson` | Ordered execution event stream |

### 3. Required Run Metadata

`metadata.json` MUST include:

- `run_id`
- `workflow_id`
- `workflow_version`
- `started_at`
- `artifacts_root`
- `entry_step`

`artifacts_root` refers to the configured parent run-artifact directory, for example `.tnh/run/`, not the per-run directory at `.tnh/run/<run_id>/`.

It SHOULD also include:

- `ended_at`
- `last_step_id`
- `termination`
- `schema_versions` for major cross-boundary contracts in play

### 4. Step Artifact Partitioning

All step-produced artifacts MUST be partitioned by `step_id` under `artifacts/<step_id>/`.

Examples:

- `artifacts/implement/transcript.md`
- `artifacts/validate/harness_report.json`
- `artifacts/evaluate/planner_decision.json`
- `artifacts/gate/gate_request.json`

This partitioning is the primary maintained lookup boundary. Consumers should resolve artifacts by step and artifact role, not by ad hoc globbing across the run root.

### 5. Step Manifest Contract

Each executed step MUST have a manifest at:

```text
artifacts/<step_id>/manifest.json
```

The manifest MUST include:

- `step_id`
- `opcode`
- `started_at`
- `ended_at`
- `termination`
- `evidence_summary`
- `artifacts`

`evidence_summary` is a compact, evaluator-facing summary of the canonical evidence for the step. It is intentionally thin and SHOULD include only stable references and summaries needed for cross-step assembly.

Each artifact entry MUST include:

| Field | Purpose |
|-------|---------|
| `role` | Canonical artifact role identifier |
| `path` | Relative path from run root |
| `media_type` | Coarse type hint (`text/plain`, `application/json`, etc.) |
| `required` | Whether the artifact is contract-critical |

Canonical artifact roles include:

- `runner_transcript`
- `runner_final_response`
- `runner_metadata`
- `policy_summary`
- `validation_report`
- `validation_stdout`
- `validation_stderr`
- `planner_decision`
- `gate_request`
- `gate_outcome`
- `workspace_diff`
- `workspace_status`

Additional roles are allowed, but these names are reserved for maintained consumers.

The `policy_summary` artifact is the canonical detailed record for requested policy, effective policy, adapter capability contribution, and any policy violations or enforcement notes relevant to the step.

### 6. Event Stream Contract

`events.ndjson` is the canonical ordered event stream for one run.

Each event MUST include:

- `timestamp`
- `run_id`
- `step_id`
- `event_type`

Recommended core event types:

- `step_started`
- `step_completed`
- `step_failed`
- `artifact_recorded`
- `gate_requested`
- `gate_resolved`
- `rollback_completed`

Event records SHOULD remain thin. Large payloads belong in artifact files, with events pointing to artifact roles or paths.

### 7. Provenance Handoff Boundary

OA04.3 defines the handoff from runtime to provenance as:

- stable run metadata,
- stable event stream,
- stable step manifests,
- stable artifact paths and roles.

`tnh-gen` or other provenance consumers may ingest, transform, or enrich these records, but must treat the run directory as the canonical execution-source artifact set.

### 8. Evaluator-Facing Resolution

Later components assembling OA06 evaluator inputs MUST resolve evidence through:

1. run metadata,
2. step manifests,
3. canonical artifact roles.

They MUST NOT depend on adapter-specific filenames when a canonical role exists.

They SHOULD use `evidence_summary` in each step manifest for lightweight assembly and open canonical artifacts only when the summary points to them. Raw adapter-local captures are non-canonical debug artifacts unless promoted into a canonical role.

### 9. Retention and Importance Tags

Retention remains system-level, consistent with [ADR-OA04.1](/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md).

Step manifests MAY mark artifacts as `important` when the producing runtime component believes they are especially relevant for human review, summarization, or retention heuristics.

This flag is advisory metadata only. It does not change runtime semantics.

### 10. Non-Goals

This ADR does not:

- define the full provenance database schema,
- require a specific event transport beyond `events.ndjson`,
- standardize all future artifact roles,
- define journal or human-summary document formats.

---

## Consequences

### Positive

- Gives the maintained runtime a stable artifact lookup contract.
- Prevents evaluator and review tooling from depending on incidental filenames.
- Makes replay, inspection, and provenance ingestion cleaner.

### Negative

- Adds manifest-writing overhead to each step.
- Forces a stricter distinction between canonical and adapter-local artifacts.

---

## Alternatives Considered

### A. Keep artifact layout implicit in code

Rejected: too brittle for provenance, evaluation, and future tooling.

### B. Put all artifacts flat at run root

Rejected: breaks step identity and makes evidence resolution ambiguous.

### C. Freeze full provenance ledger schema here

Rejected: too broad. OA04.3 only freezes the runtime-side handoff boundary.

---

## Open Questions

- Should planner and gate artifacts get reserved JSON schemas in this ADR family, or remain role-only until their implementation slices land?
- Should `events.ndjson` include a stable event `id`, or is ordered append-only sequencing sufficient for MVP?

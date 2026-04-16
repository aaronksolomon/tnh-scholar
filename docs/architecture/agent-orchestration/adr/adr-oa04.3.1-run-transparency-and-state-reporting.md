---
title: "ADR-OA04.3.1: Run Transparency and State Reporting"
description: "Adds a maintained operator-facing status contract on top of the OA04.3 run-artifact model for live monitoring of headless workflow runs."
type: "design-detail"
owner: "aaronksolomon"
author: "Codex"
status: accepted
created: "2026-04-16"
parent_adr: "adr-oa04.3-provenance-run-artifact-contract.md"
related_adrs:
  - "adr-oa04.2-runner-contract.md"
  - "adr-oa06-planner-evaluator-contract.md"
  - "adr-oa07.1-worktree-lifecycle-and-rollback.md"
---

# ADR-OA04.3.1: Run Transparency and State Reporting

Adds a maintained operator-facing status contract on top of the OA04.3 run-artifact model for live monitoring of headless workflow runs.

- **Status**: Accepted
- **Type**: Design Detail
- **Date**: 2026-04-16
- **Owner**: Aaron Solomon
- **Author**: Codex
- **Parent ADR**: [ADR-OA04.3](/architecture/agent-orchestration/adr/adr-oa04.3-provenance-run-artifact-contract.md)
- **Related ADRs**:
  - [ADR-OA04.2](/architecture/agent-orchestration/adr/adr-oa04.2-runner-contract.md)
  - [ADR-OA06](/architecture/agent-orchestration/adr/adr-oa06-planner-evaluator-contract.md)
  - [ADR-OA07.1](/architecture/agent-orchestration/adr/adr-oa07.1-worktree-lifecycle-and-rollback.md)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

[ADR-OA04.3](/architecture/agent-orchestration/adr/adr-oa04.3-provenance-run-artifact-contract.md) defines the canonical run directory, step manifests, event stream, and artifact-role contract for maintained workflow execution. That contract is sufficient for durable provenance and later evaluator assembly, but it is not yet sufficient for practical monitoring of long-running headless runs.

Recent spike work on prompt-dir comparison runs showed a recurring operational gap:

- the run directory is durable, but not easy to monitor live,
- run-level metadata does not always make current state obvious during execution,
- event emission is too sparse for quick operator understanding,
- long-running runs are harder to supervise because route decisions and active runner state are not surfaced clearly enough.

This is now a product requirement rather than a convenience. If `tnh-conductor` is intended to support longer headless runs with iterative review and feedback loops, operators need a stable way to answer basic questions during execution:

- what step is currently active,
- what step completed most recently,
- which runner or agent family is active,
- what the runtime decided most recently,
- whether the run appears healthy, blocked, or terminal.

OA04.3 should remain the provenance and artifact source of truth. This ADR adds a thin operator-facing status layer on top of it.

## Decision

### 1. Add a Maintained Live Status Surface

Each workflow run MUST expose a lightweight live status artifact alongside the existing OA04.3 run directory artifacts.

The maintained default file is:

```text
.tnh/run/<run_id>/status.json
```

This file is operator-facing and monitoring-oriented. It does not replace `metadata.json`, `events.ndjson`, or step manifests.

The kernel runtime owns `status.json` writes.

Runner adapters and other step executors may contribute typed state inputs to the kernel, but they MUST NOT write `status.json` directly. This avoids concurrent-write races and keeps run-level status ownership aligned with OA04.3 run-artifact ownership.

### 2. Required Status Fields

`status.json` MUST be updated during execution and MUST include:

- `run_id`
- `workflow_id`
- `started_at`
- `updated_at`
- `lifecycle_state`
- `current_step_id`
- `last_completed_step_id`
- `active_opcode`
- `active_runner_family`
- `worktree_path`
- `last_route_target`
- `termination`

`lifecycle_state` is a bounded maintained enum with the following values:

- `running`
- `waiting`
- `blocked`
- `failed`
- `completed`

`active_opcode` MUST use the canonical opcode vocabulary defined by [ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md).

Recommended optional fields:

- `active_attempt`
- `elapsed_seconds`
- `last_artifact_write`
- `blocking_reason`
- `operator_note`

When a field is not yet known, it SHOULD be present with a null value rather than omitted.

### 3. Metadata Remains Canonical Run Summary

`metadata.json` remains the canonical run summary artifact defined by OA04.3.

During execution, the runtime SHOULD also keep `metadata.json` reasonably current for:

- `ended_at`
- `last_step_id`
- `termination`

`status.json` is the primary live-monitoring surface. `metadata.json` remains the canonical run-level provenance summary.

### 4. Event Coverage Must Be Expanded

The maintained event stream MUST include enough event coverage for a human or monitoring tool to reconstruct meaningful progress without opening step-local artifacts immediately.

In addition to OA04.3 core events, the runtime SHOULD emit:

- `runner_started`
- `runner_completed`
- `route_selected`
- `step_waiting`
- `step_blocked`
- `status_updated`

Event payloads should remain thin. Large details still belong in artifact files.

`status_updated` SHOULD be emitted for meaningful run-state transitions, not for every file write or heartbeat-like refresh. Examples include:

- a change to `lifecycle_state`,
- a change to `current_step_id`,
- a change to `last_completed_step_id`,
- a change to `last_route_target`,
- a transition into or out of a blocked or waiting condition.

### 5. Step Artifacts Must Surface Active Runner State

For `RUN_AGENT` steps, the runtime SHOULD record step-local state that makes active runner behavior easier to inspect while the step is still in progress.

That surface may be satisfied by:

- incremental `runner_metadata.json` updates,
- a step-local status file,
- or another maintained artifact with equivalent semantics.

The maintained requirement is the behavior, not a second fixed filename at this stage.

### 6. Route and Evaluation Decisions Must Be Visible

For workflows that use `EVALUATE`, `GATE`, or future review/refinement routing, the current run state MUST surface the most recent route decision in a stable machine-readable form.

At minimum this means:

- most recent decision status,
- selected next step,
- whether retry/refinement was requested,
- whether the run is awaiting a human or policy gate.

### 7. CLI Status Readout Is a Follow-On, Not a Prerequisite

This ADR does not require a new CLI command immediately.

A future `tnh-conductor status <run_id>` command should consume the maintained live status surface defined here rather than inventing a parallel contract.

## Consequences

- **Positive**: Long-running runs become materially easier to monitor, supervise, and debug.
- **Positive**: Review/refinement workflows gain a clearer operator feedback loop.
- **Positive**: Monitoring tools and CLI status views can build on one stable contract.
- **Negative**: The runtime must write more frequently to run-level artifacts.
- **Negative**: The system takes on a stronger compatibility obligation for operator-facing state fields.

## Alternatives Considered

### Rely Only on `events.ndjson`

Rejected because event replay is useful but too indirect for quick operator checks. A single live status artifact is a better monitoring surface.

### Keep Status Implicit in Step Manifests Only

Rejected because step manifests are terminal or step-scoped artifacts, not a clear run-level answer to "what is happening right now?"

### Expand `metadata.json` Only

Partially acceptable, but rejected as the sole approach because `metadata.json` is better kept as the canonical run summary while `status.json` carries the higher-churn live view.

## Open Questions

- Should `status.json` include runner process identifiers when available?
- Should step-local live status be normalized under OA04.2 or remain an OA04.3 artifact concern?
- What is the minimum acceptable update cadence for long-running steps?

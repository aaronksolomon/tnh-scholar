---
title: "ADR-OA07.4: Workspace and Run Artifact Subsystems"
description: "Defines the maintained workspace and run-artifact subsystems for tnh-conductor MVP, including ownership boundaries for git/worktree operations, rollback primitives, run directories, events, metadata, and persisted artifact records."
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
  - "adr-oa07.2-runner-subsystem-design.md"
  - "adr-oa07.3-validation-subsystem-design.md"
  - "adr-oa06-planner-evaluator-contract.md"
---

# ADR-OA07.4: Workspace and Run Artifact Subsystems

Defines the maintained workspace and run-artifact subsystems for tnh-conductor MVP, including ownership boundaries for git/worktree operations, rollback primitives, run directories, events, metadata, and persisted artifact records.

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
  - [ADR-OA07.2](/architecture/agent-orchestration/adr/adr-oa07.2-runner-subsystem-design.md)
  - [ADR-OA07.3](/architecture/agent-orchestration/adr/adr-oa07.3-validation-subsystem-design.md)
  - [ADR-OA06](/architecture/agent-orchestration/adr/adr-oa06-planner-evaluator-contract.md)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

ADR-OA04.1 requires the MVP to support `ROLLBACK(pre_run)`, run-scoped artifact directories under `.tnh/run/<run_id>/...`, and durable provenance outputs such as logs, reports, and artifact references. ADR-OA07 establishes two maintained subsystems for those concerns:

- `workspace/`
- `run_artifacts/`

The current prototype spreads these responsibilities across multiple places:

- `reference/spike/providers/git_workspace.py`
- `conductor_mvp/providers/artifact_store.py`
- kernel service methods that still implicitly shape run directory and artifact outputs

That prototype proved the flow, but ownership is not yet explicit:

- git/worktree safety, branch changes, rollback, and repo-state capture are mixed together
- run directory creation and artifact writing are underspecified as a subsystem
- raw artifact capture performed by runners/validation is not yet cleanly separated from durable run-artifact ownership

This ADR defines the maintained boundary.

### Workspace Definition

For agent-orchestration MVP, workspace means:

> deterministic management of repo/worktree state needed to run the workflow safely, including pre-run capture and rollback primitives.

Workspace is not:

- the runner subsystem
- the validation subsystem
- a generic git automation surface
- the owner of run metadata, logs, or artifact files

### Run Artifact Definition

For agent-orchestration MVP, run artifacts mean:

> run-scoped persisted records owned by the orchestration runtime: directories, event logs, metadata, normalized artifact references, and other durable outputs needed for provenance and review.

Run-artifacts are not:

- the place where runner or validation policy decides what to capture
- the place where subprocess output is interpreted
- the owner of git state or rollback operations

### Implementation Guidance

These subsystems touch filesystem and git side effects, so their boundaries should be explicit. But they should remain small and concrete.

Guidance for implementers:

- keep workspace focused on repo/worktree semantics and safety
- keep run-artifacts focused on persisted run records and path ownership
- let runners and validation decide what raw outputs they emit, but not how the orchestration runtime organizes durable records
- do not create generic “storage” abstractions if filesystem-backed implementations are the only maintained need in MVP
- take limited inspiration from TNH Scholar's existing metadata persistence pattern: small inspectable metadata files are useful, but flexible dict-like metadata containers are not the right maintained model here

Goal:

> explicit ownership of side effects without turning filesystem and git behavior into a framework

---

## Decision

### 1. The maintained workspace package is `agent_orchestration/workspace/`

The maintained runtime path for repo/worktree operations will live in `agent_orchestration/workspace/`.

This package owns:

- repo-root discovery
- current branch/worktree inspection
- pre-run capture
- rollback primitives required by OA04
- deterministic workspace status/diff capture
- workspace safety checks around branch/worktree state

It does not own:

- kernel route semantics
- run directory layout
- event writing
- transcript or report persistence

### 2. The maintained run-artifact package is `agent_orchestration/run_artifacts/`

The maintained runtime path for durable run-scoped records will live in `agent_orchestration/run_artifacts/`.

This package owns:

- run directory creation and path layout
- event log writing
- metadata writing
- final-state persistence
- normalized artifact reference persistence
- conventions for persisted transcripts, reports, and summaries once they are already captured by their owning subsystem

It does not own:

- deciding which raw runner outputs are worth capturing
- deciding which validation outputs count as validation artifacts
- git operations
- workflow route semantics

### 3. Workspace and run-artifacts are separate subsystems

Do not merge workspace and run-artifacts into one generic “runtime IO” subsystem.

Rationale:

- workspace semantics are about repo state, safety, and rollback
- run-artifact semantics are about provenance, persistence, and reviewable outputs
- the two overlap operationally, but they are different domains with different failure modes

### 4. Workspace owns rollback and checkpoint primitives

The workspace subsystem owns runtime rollback mechanics required by OA04.

At MVP this includes:

- `capture_pre_run(run_id)`
- rollback to `pre_run`

The subsystem may also define checkpoint-oriented typed models for later expansion, but named checkpoints remain future scope until OA04 requires them.

The kernel may request rollback through workspace protocols, but it must not implement git logic itself.

### 5. Workspace capture is semantic, not just command output

The workspace subsystem should return typed workspace snapshots rather than raw command output strings.

Minimum maintained workspace snapshot content:

- repo root
- current branch or detached-head status
- clean/dirty state
- staged/unstaged counts
- optionally normalized diff/status references when required for review or rollback decisions

The workspace subsystem may use git subprocesses internally in MVP, but those mechanics must not leak across the workspace boundary.

MVP guidance:

- workspace does not need to preemptively persist diffs for every step
- however, because [ADR-OA06](/architecture/agent-orchestration/adr/adr-oa06-planner-evaluator-contract.md) requires `workspace_diff_summary` in planner evidence, workspace must support on-demand normalized diff summary generation when `EVALUATE` evidence is assembled
- if pre-rollback diff capture becomes an audit requirement, workspace should capture it and `run_artifacts/` should persist the resulting record

### 6. Run directory ownership belongs to `run_artifacts/`

The run-artifact subsystem owns creation of the run directory and its maintained path layout.

This includes:

- `.tnh/run/<run_id>/...` path resolution
- stable locations for:
  - event log(s)
  - metadata
  - kernel final state
  - persisted runner/validation artifact references

Other subsystems receive run-artifact paths or path helpers through typed contracts rather than inventing their own layout rules.

MVP guidance:

- prefer a small fixed set of inspectable files
- use a single structured metadata file for run-level facts
- follow the spirit of TNH Scholar's existing metadata persistence pattern, but with typed agent-orch models rather than generic dict-like metadata containers

### 7. Raw capture and durable ownership are different concerns

Runners and validation own raw output capture policy for their domain outputs.

Examples:

- runners decide what raw transcript/stdout/final-response outputs are captured
- validation decides what reports or files count as validation artifacts

`run_artifacts/` owns the durable orchestration record of those outputs:

- canonical persisted locations
- metadata and event records pointing to them
- normalized artifact reference files if needed for later review

This keeps subsystem-specific capture logic out of the general provenance layer.

### 8. Event and metadata writing belong to `run_artifacts/`

The maintained run-artifact subsystem owns structured runtime records such as:

- run metadata
- step events
- final kernel state
- summary records needed for later review or planner consumption

The kernel may produce kernel-owned event payloads, but it should not own file-writing policy or path layout.

Similarly:

- runners should not own orchestration event formatting
- validation should not own orchestration metadata formatting

MVP guidance:

- prefer a small fixed set of run-artifact files over a single broad ledger or a prematurely typed multi-file schema
- keep the persisted layout simple and inspectable before introducing richer event-taxonomy machinery
- event records may use an append-friendly text format such as NDJSON if that proves simplest during implementation
- run metadata should remain a single structured file per run in MVP

### 9. Workspace safety policy belongs to workspace, not kernel

The kernel may require certain workspace guarantees before execution begins, but the workspace subsystem owns the logic that determines whether those guarantees are met.

Examples:

- whether the repo is in a clean enough state to begin
- whether a rollback target exists
- whether the current branch/worktree state permits the requested operation

This keeps git-specific safety reasoning out of the kernel.

### 10. Migration path from prototype code should follow ownership, not file names

Current prototype surfaces should migrate by concern:

- `reference/spike/providers/git_workspace.py` -> `workspace/`
- `conductor_mvp/providers/artifact_store.py` -> `run_artifacts/`
- any kernel-side file/path shaping -> `run_artifacts/`
- runner/validation-local capture code stays with those subsystems unless it is actually general provenance writing

Do not preserve prototype file groupings if the responsibilities belong to different maintained subsystems.

### 11. `run_artifacts/` should preserve availability, not force cross-subsystem normalization

The purpose of `run_artifacts/` is to make outputs durable and easy to access, not to coerce runner and validation outputs into one shared content schema.

Therefore:

- `run_artifacts/` should persist and reference outputs in the forms their owning subsystems already produce
- humans and AI reviewers are expected to consume varied but accessible output formats
- normalization should be limited to path/layout/reference conventions, not content-level unification across subsystems

---

## Suggested Package Shape

```text
agent_orchestration/workspace/
  __init__.py
  models.py                # workspace snapshots, rollback targets, policies
  protocols.py             # kernel-facing workspace contracts
  service.py               # orchestration facade if needed
  git_workspace.py

agent_orchestration/run_artifacts/
  __init__.py
  models.py                # run metadata, event records, artifact references
  protocols.py             # kernel-facing artifact persistence contracts
  service.py               # path/layout + write coordination if needed
  filesystem_store.py
```

Notes:

- `service.py` is optional in both subsystems; add it only if coordination logic becomes real
- filesystem-backed persistence is the maintained MVP assumption unless a second backend appears
- typed path/layout helpers are preferred over scattered string concatenation
- keep the package roots flat until a second provider implementation actually appears

---

## Consequences

### Positive

- Makes git/worktree ownership explicit and keeps it out of the kernel.
- Makes provenance and persisted run records a maintained subsystem rather than incidental file writes.
- Clarifies the split between raw capture policy and durable orchestration ownership.
- Creates a clear migration target for current spike workspace code and conductor artifact writing.

### Negative

- Introduces two more maintained packages during migration.
- Requires some current file-writing code to move again even though the prototype already works.
- May expose hidden coupling between kernel, runner, validation, and file layout assumptions.

### Neutral

- MVP may still use filesystem and git subprocesses internally; the architectural correction is about ownership and contract boundaries, not about avoiding those tools.
- Named checkpoints remain deferred even though workspace models may leave room for them later.

---

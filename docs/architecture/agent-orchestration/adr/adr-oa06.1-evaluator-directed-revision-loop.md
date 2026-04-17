---
title: "ADR-OA06.1: Evaluator-Directed Revision Loop"
description: "Defines a bounded maintained review-to-revision loop for conductor workflows so review and validation artifacts can drive one deterministic refinement pass."
type: "design-detail"
owner: "aaronksolomon"
author: "Codex"
status: proposed
created: "2026-04-16"
parent_adr: "adr-oa06-planner-evaluator-contract.md"
related_adrs:
  - "adr-oa04-workflow-schema-opcode-semantics.md"
  - "adr-oa04.3.1-run-transparency-and-state-reporting.md"
  - "adr-oa07.1-worktree-lifecycle-and-rollback.md"
---

# ADR-OA06.1: Evaluator-Directed Revision Loop

Defines a bounded maintained review-to-revision loop for conductor workflows so review and validation artifacts can drive one deterministic refinement pass.

- **Status**: Proposed
- **Type**: Design Detail
- **Date**: 2026-04-16
- **Owner**: Aaron Solomon
- **Author**: Codex
- **Parent ADR**: [ADR-OA06](/architecture/agent-orchestration/adr/adr-oa06-planner-evaluator-contract.md)
- **Related ADRs**:
  - [ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)
  - [ADR-OA04.3.1](/architecture/agent-orchestration/adr/adr-oa04.3.1-run-transparency-and-state-reporting.md)
  - [ADR-OA07.1](/architecture/agent-orchestration/adr/adr-oa07.1-worktree-lifecycle-and-rollback.md)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

[ADR-OA06](/architecture/agent-orchestration/adr/adr-oa06-planner-evaluator-contract.md) establishes that `EVALUATE` is the only semantic decision locus in maintained conductor workflows. [ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md) already defines legal routing and bounded `allowed_next_steps`, but the maintained bootstrap path still lacks a concrete loop that turns review and validation evidence into a deterministic refinement attempt.

Recent conductor work established three prerequisites:

- live `status.json` and richer event coverage now make long-running runs monitorable,
- native Codex and Claude runners both work in maintained headless execution,
- bootstrap validation now runs through `poetry` and emits readable stdout/stderr artifacts.

That means the remaining gap is no longer basic execution. The gap is control flow: review is currently observational only. A review step can identify issues, but the maintained runtime does not yet use those findings to request a bounded fix pass and then resume validation.

The next maintained capability should stay narrow:

- no open-ended planning loop,
- no unconstrained retries,
- no semantic routing outside `EVALUATE`,
- one clear revision opportunity driven by typed evidence and bounded legal routes.

## Decision

### 1. Add a Bounded Maintained Revision Loop

Maintained conductor workflows may implement a review-to-revision loop with this shape:

1. `RUN_AGENT` implementation step
2. `RUN_AGENT` review step
3. `EVALUATE` review-and-validation synthesis step
4. route to either:
   - validation or stop when outcome is acceptable,
   - one refinement step when outcome is fixable,
   - gate/rollback/stop when outcome is blocked or unsafe
5. optional single refinement pass followed by validation

This loop is bounded to at most one evaluator-directed refinement attempt in the maintained bootstrap path.

### 2. `EVALUATE` Owns the Revision Decision

The kernel MUST NOT inspect free-form review text directly.

The evaluator remains the only semantic decision maker. It consumes structured evidence from:

- latest review artifacts,
- latest validation artifacts,
- current workspace diff summary,
- most recent provenance window,
- policy or blocking signals captured in run artifacts.

The evaluator emits the OA06 decision object:

- `status`
- `next_step`
- `fix_instructions`
- `blockers`
- `risk_flags`

For this loop, `fix_instructions` becomes a first-class downstream input to the refinement `RUN_AGENT` step.

### 3. First Maintained Policy Is Narrow and Deterministic

The first maintained evaluator policy for review-driven refinement MUST follow these rules:

- `success` means the review and validation evidence supports forward progress without another coding step
- `partial` means there is a fixable issue with a concrete edit path; the evaluator may route to one refinement step
- `blocked` means a required artifact or execution result is missing or unusable; the workflow must not pretend a refinement path is known
- `unsafe` means policy contradiction, untrusted state, or other evidence that should route away from normal refinement
- `needs_human` means the evaluator cannot safely continue without external judgment

For maintained bootstrap workflows:

- at most one refinement step may be requested after a review-driven `partial`
- a second `partial` after refinement MUST escalate to `needs_human` or `blocked`
- the evaluator MUST select a `next_step` from the workflow's bounded `allowed_next_steps`

### 4. Refinement Inputs Must Be Stable and Typed

The refinement step MUST receive a stable typed instruction package derived from evaluator output rather than raw pasted review prose.

The maintained refinement package SHOULD include:

- objective summary,
- concrete issues to fix,
- constraints to preserve,
- artifact references backing each requested change,
- verification expectations for the subsequent validation step.

Raw review transcripts may be preserved as evidence, but they are not the maintained control contract.

### 5. Review and Validation Must Stay Distinct

The maintained loop separates review from validation:

- review may be model-driven and comparative,
- validation remains mechanical and command-backed,
- `EVALUATE` synthesizes both rather than replacing either one.

This separation prevents the loop from collapsing into "the reviewing model decides correctness by opinion alone."

### 6. Transparency Requirements Apply to the Loop

Any maintained evaluator-directed refinement workflow MUST surface the loop state through the OA04.3.1 transparency contract.

At minimum the run status and event stream must make visible:

- that review completed,
- that `EVALUATE` selected refinement or not,
- whether the refinement attempt has already been spent,
- why the run escalated to `blocked`, `unsafe`, or `needs_human`.

## Consequences

- **Positive**: Review becomes an actionable control signal rather than passive commentary.
- **Positive**: Maintained conductor gains a genuinely more capable workflow shape than a single-agent one-shot run.
- **Positive**: Cross-model review can improve outcomes without giving the kernel semantic authority.
- **Negative**: The evaluator contract takes on stronger obligations around evidence packaging and refinement instruction quality.
- **Negative**: Workflow authors must think explicitly about bounded retry structure and escalation paths.

## Alternatives Considered

### Let Review Steps Route Directly

Rejected because it would let free-form model output steer the workflow outside the OA06 contract and would weaken deterministic kernel behavior.

### Allow Unlimited Evaluate-Refine Iteration

Rejected for the maintained bootstrap path because it would make debugging, monitoring, and failure containment much harder before the basic loop is proven.

### Collapse Review into Validation

Rejected because review and validation provide different evidence. Mechanical validation cannot replace design/code critique, and critique should not replace deterministic execution checks.

## Open Questions

- Should the first maintained evaluator operate entirely on artifact summaries, or may it also consume selected transcript excerpts?
- Should the single refinement cap be encoded in workflow schema, evaluator policy, or both?
- Should a review-only workflow be allowed to skip validation when the task is documentation-only, or should validation remain mandatory whenever commands are available?

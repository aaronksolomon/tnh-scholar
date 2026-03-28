---
title: "ADR-OA04.4: Policy Enforcement Contract"
description: "Defines the shared permissibility model, native-control mapping boundary, and violation handling contract for workflow execution."
type: "design-detail"
owner: "aaronksolomon"
author: "Aaron Solomon, GPT-5 Codex"
status: accepted
created: "2026-03-27"
parent_adr: "adr-oa04-workflow-schema-opcode-semantics.md"
related_adrs:
  - "adr-oa04.2-runner-contract.md"
  - "adr-oa04.3-provenance-run-artifact-contract.md"
  - "adr-oa01.1-conductor-strategy-v2.md"
  - "adr-oa05-prompt-library-specification.md"
---

# ADR-OA04.4: Policy Enforcement Contract

Defines the shared permissibility model, native-control mapping boundary, and violation handling contract for workflow execution.

- **Status**: Accepted
- **Type**: Design Detail
- **Date**: 2026-03-27
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, GPT-5 Codex
- **Parent ADR**: [ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)
- **Related ADRs**:
  - [ADR-OA04.2](/architecture/agent-orchestration/adr/adr-oa04.2-runner-contract.md)
  - [ADR-OA04.3](/architecture/agent-orchestration/adr/adr-oa04.3-provenance-run-artifact-contract.md)
  - [ADR-OA01.1](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md)
  - [ADR-OA05](/architecture/agent-orchestration/adr/adr-oa05-prompt-library-specification.md)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

[ADR-OA01.1](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md) establishes policy prompts and kernel-side diff enforcement as core guardrails. [ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md) allows workflow defaults and step-level policy references, and [ADR-OA04.2](/architecture/agent-orchestration/adr/adr-oa04.2-runner-contract.md) introduces agent-neutral execution intent plus requested-versus-effective policy provenance.

What remains missing is the maintained contract for:

- the shared permissibility model,
- how that model maps to native agent controls,
- where kernel enforcement begins when native controls are incomplete,
- how policy violations are classified and surfaced to workflow execution.

Without OA04.4, policy remains conceptually important but operationally fuzzy.

---

## Decision

### 1. Shared Policy Model

Workflow execution uses a shared, agent-neutral **execution policy** model.

This model expresses intent such as:

- writable workspace posture,
- allowed path scope,
- forbidden path scope,
- forbidden operations,
- interactive prompt posture,
- network posture,
- approval posture.

The shared model is the maintained contract. Native runner flags are adapter-local implementation details.

### 2. Requested vs Effective Policy

Execution policy is tracked in two forms:

| Form | Meaning |
|------|---------|
| `requested_policy` | What the workflow/control plane asks to be enforced |
| `effective_policy` | What is actually enforced via native controls plus kernel safeguards |

Both forms are provenance-relevant.

If a workflow requires guarantees an adapter cannot satisfy, the adapter MUST fail fast rather than silently weakening policy.

For maintained implementation, the policy boundary SHOULD follow the repository taxonomy from OS01:

- `ExecutionPolicySettings`: long-lived system defaults and deployment-level controls
- `RequestedExecutionPolicy`: per-step requested intent assembled by the control plane
- `EffectiveExecutionPolicy`: the enforced outcome after capability mapping and runtime safety overrides
- `PolicySummary`: canonical persisted policy evidence for one executed step

Adapter capability declarations participate in effective-policy derivation, but they belong to the runner layer rather than the policy model layer.

These forms MUST remain distinct in typed models. The maintained runtime should not collapse them into one mutable policy blob.

### 3. Policy Sources and Precedence

The effective policy is assembled from:

1. system defaults,
2. workflow defaults,
3. step-level policy reference,
4. runtime safety overrides.

Runtime safety overrides can only tighten policy, never loosen it. When present, they always win if they are more restrictive.

The assembly boundary SHOULD therefore be:

1. settings/config at init time,
2. requested policy per workflow step,
3. effective policy derived at execution time.

### 4. Native Control Mapping Boundary

Runner adapters translate shared policy intent into native control surfaces when available.

Examples:

- approval mode flags,
- sandbox mode flags,
- native tool allow/deny controls,
- settings-file-based restrictions.

This translation is adapter-specific. The kernel does not reason in native flag vocabulary.

### 5. Kernel Enforcement Boundary

Kernel enforcement remains mandatory even when native controls exist.

Kernel-side policy enforcement includes:

- workspace isolation,
- protected-branch safeguards,
- post-step diff and status inspection,
- forbidden path and operation checks,
- rollback or halt on severe violations.

The kernel is the final authority on workflow safety outcomes.

### 6. Canonical Policy Dimensions

The shared policy model MUST support, at minimum:

| Dimension | Examples |
|-----------|----------|
| filesystem scope | allowed paths, forbidden paths |
| operation scope | no commit, no push, no delete, no force operations |
| approval posture | fail on prompt, deny interactive approval, allow bounded auto-approval |
| network posture | deny, allow |
| execution posture | read-only, workspace-write |

Additional dimensions are allowed, but these form the MVP contract.

### 7. Violation Classes

Policy violations MUST be classified using a small stable set:

- `native_policy_block`
- `forbidden_path`
- `forbidden_operation`
- `interactive_prompt_violation`
- `network_violation`
- `protected_branch_violation`

Additional internal detail may exist, but maintained runtime and provenance should preserve these stable classes.

### 8. Violation Outcomes

Violation handling follows this pattern:

| Severity | Runtime Effect |
|----------|----------------|
| hard violation | mechanical failure and no forward progress |
| recoverable policy block | `killed_policy` or `error`, then workflow routes via existing OA04 transition semantics for non-`EVALUATE` mechanical outcomes |

The kernel may mark a step unsafe or force rollback at the workflow level, but OA04.4 itself remains in the mechanical enforcement domain.

### 8a. Policy Provenance Shape

Each executed step MUST persist policy evidence in two layers:

1. a compact requested/effective policy summary in the step manifest `evidence_summary`
2. a detailed canonical `policy_summary` artifact

The detailed `policy_summary` artifact SHOULD contain:

- `requested_policy`
- `effective_policy`
- adapter capability declaration used for derivation
- applied runtime overrides
- violation records, if any
- enforcement notes relevant to later review

Evaluators and other downstream consumers SHOULD use manifest summary data first and open `policy_summary` only when detailed inspection is required.

### 9. Policy Prompts and Structured Parsing

Policy prompts remain prompt artifacts, but the maintained runtime only depends on their structured policy payload, not free-form prose.

OA04.4 therefore requires that policy prompts ultimately resolve to a typed policy object before execution.

Ownership boundary:

- OA05 owns prompt artifact structure and validation.
- The control plane owns resolving a referenced policy prompt into the typed execution-policy object consumed by runtime components.

### 10. Capability Declaration Requirement

Each runner adapter MUST declare which policy dimensions it can honor natively.

Capability examples:

- native sandbox support,
- native approval control,
- native tool allowlist support,
- native network restriction support.

The declaration mechanism is defined in [ADR-OA04.2](/architecture/agent-orchestration/adr/adr-oa04.2-runner-contract.md) Section 3a. OA04.4 requires that declaration to be used when deriving `effective_policy`.

### 11. Non-Goals

This ADR does not:

- define all policy prompt authoring conventions,
- encode native flags from every agent surface,
- replace kernel safeguards with native controls,
- define semantic planner handling of risk flags.

---

## Consequences

### Positive

- Makes permissibility explicit and portable across agents.
- Prevents silent weakening of policy when adding new runners.
- Clarifies the split between adapter-native controls and kernel enforcement.

### Negative

- Requires another typed object boundary before execution.
- Adds policy-assembly complexity to the control plane.

---

## Alternatives Considered

### A. Keep policy entirely in prompt prose

Rejected: too ambiguous for deterministic enforcement.

### B. Standardize one universal set of native flags across agents

Rejected: unrealistic and brittle as control surfaces evolve.

### C. Rely only on kernel post-hoc diff checks

Rejected: too weak as a sole safety mechanism once native controls are available.

---

## Open Questions

- Which policy dimensions must be first-class in maintained Pydantic models in the first implementation slice?
- Should policy violation severity be part of the stable contract here, or inferred later from violation class plus workflow context?

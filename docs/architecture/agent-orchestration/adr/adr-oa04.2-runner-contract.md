---
title: "ADR-OA04.2: Runner Contract"
description: "Defines the maintained RUN_AGENT request/result, artifact, and normalization contract for Claude CLI and Codex CLI adapters."
type: "design-detail"
owner: "aaronksolomon"
author: "Aaron Solomon, GPT-5 Codex"
status: implemented
created: "2026-03-26"
parent_adr: "adr-oa04-workflow-schema-opcode-semantics.md"
related_adrs:
  - "adr-oa03-agent-runner-architecture.md"
  - "adr-oa03.1-claude-code-runner.md"
  - "adr-oa03.3-codex-cli-runner.md"
  - "adr-oa04.1-implementation-notes-mvp-buildout.md"
  - "adr-oa06-planner-evaluator-contract.md"
---

# ADR-OA04.2: Runner Contract

Defines the maintained `RUN_AGENT` request/result, artifact, and normalization contract for Claude CLI and Codex CLI adapters.

- **Status**: Implemented
- **Type**: Design Detail
- **Date**: 2026-03-26
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, GPT-5 Codex
- **Parent ADR**: [ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)
- **Related ADRs**:
  - [ADR-OA03](/architecture/agent-orchestration/adr/adr-oa03-agent-runner-architecture.md)
  - [ADR-OA03.1](/architecture/agent-orchestration/adr/adr-oa03.1-claude-code-runner.md)
  - [ADR-OA03.3](/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-runner.md)
  - [ADR-OA04.1](/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md)
  - [ADR-OA06](/architecture/agent-orchestration/adr/adr-oa06-planner-evaluator-contract.md)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

[ADR-OA01.1](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md) and [ADR-OA03](/architecture/agent-orchestration/adr/adr-oa03-agent-runner-architecture.md) establish that:

- `RUN_AGENT` invokes bounded CLI sub-agents,
- the kernel owns capture, enforcement, and provenance,
- per-agent adapters own control-surface specifics,
- durable artifacts are the stable handoff for evaluation and review.

[ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md) defines the workflow step shape for `RUN_AGENT`, but does not yet freeze the maintained contract between:

- kernel and runner adapter,
- runner adapter and run artifact store,
- runner outputs and future evaluator inputs.

[ADR-OA03.1](/architecture/agent-orchestration/adr/adr-oa03.1-claude-code-runner.md) and [ADR-OA03.3](/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-runner.md) describe Claude and Codex control surfaces, but they are partly spike-oriented and do not by themselves define the maintained OA07 subsystem contract.

This gap now matters because the maintained runtime already has:

- a kernel that routes `RUN_AGENT`,
- typed runner request/result shell models,
- run artifact and workspace boundaries,

but no accepted runner normalization contract for implementation.

Without OA04.2, runner implementation risks drift in:

- artifact naming and retention,
- transcript and final-response capture expectations,
- termination mapping,
- Claude/Codex surface differences,
- evaluator-facing evidence availability.

---

## Decision

### 1. Scope and Ownership

OA04.2 defines the **maintained `RUN_AGENT` boundary contract**.

It covers:

- kernel-facing runner request and result models,
- required per-step artifacts,
- normalization rules across Claude CLI and Codex CLI,
- mechanical termination mapping,
- minimum provenance payload expected from runner execution.

It does **not** redefine:

- workflow step syntax owned by OA04,
- agent-specific CLI flags owned by OA03.1/OA03.3,
- planner semantics owned by OA06,
- policy prompt content owned by OA05/OA01.1.

Detailed permissibility modeling, native-control mapping, and policy violation classification are deferred to planned `ADR-OA04.4`.

### 2. Contract Layering

The runner contract is layered as follows:

| ADR | Responsibility |
|-----|----------------|
| OA03 | Kernel/adapter architectural split |
| OA03.1 | Claude CLI supported surface and capture posture |
| OA03.3 | Codex CLI supported surface and capture posture |
| OA04 | `RUN_AGENT` workflow step schema and runtime semantics |
| OA04.2 | Maintained request/result/artifact normalization contract |

### 3. Maintained Runner Request Contract

The maintained runner request for one `RUN_AGENT` step MUST include:

| Field | Type | Purpose |
|-------|------|---------|
| `agent_family` | enum | Adapter selection (`claude_cli`, `codex_cli`) |
| `rendered_task_text` | string | Fully rendered task text presented to the agent |
| `working_directory` | path | Isolated run/worktree directory for execution |
| `prompt_reference` | string/null | Versioned prompt reference for provenance |
| `requested_policy` | object | Typed agent-neutral execution intent assembled upstream per `ADR-OA04.4` |

This request is intentionally narrow. Workflow parsing, prompt rendering, policy assembly, and workspace preparation remain upstream responsibilities.

The request carries **agent-neutral execution intent**, not raw agent-specific flags. Adapters are responsible for translating this intent into native control surfaces.

### 3a. Capability Declaration

Each maintained runner adapter MUST declare the execution capabilities it can honor natively.

Representative capability dimensions include:

- writable workspace support,
- read-only or sandboxed execution support,
- native approval/permission controls,
- native tool allow/deny controls,
- structured event stream support,
- interactive prompt suppression.

The shared runner contract does not require identical native controls across agents. It requires adapters to:

1. declare what they can enforce,
2. map shared intent into native controls where possible,
3. fail fast when required guarantees cannot be satisfied.

### 4. Maintained Runner Result Contract

The maintained runner result MUST provide:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `termination` | enum | yes | Kernel-facing mechanical outcome |
| `transcript_path` | path/null | yes | Canonical runner transcript artifact if produced |
| `final_response_path` | path/null | yes | Final agent summary/message artifact if produced |

Runner metadata is still part of the required normalized artifact contract, but it is resolved through the step manifest and canonical artifact roles defined by [ADR-OA04.3](/architecture/agent-orchestration/adr/adr-oa04.3-provenance-run-artifact-contract.md), not through a dedicated result field in the initial maintained model.

The maintained runner result intentionally describes **normalized execution output**, not persistence details. Writing canonical artifacts, manifests, and event records is owned by the run-artifact subsystem and coordinated by the kernel/runtime services.

### 5. Required Runner Artifacts

Each `RUN_AGENT` step MUST produce the following normalized artifacts, recorded in the step manifest defined by [ADR-OA04.3](/architecture/agent-orchestration/adr/adr-oa04.3-provenance-run-artifact-contract.md):

| Artifact | Required | Description |
|----------|----------|-------------|
| `runner_transcript` | yes | Captured event stream or normalized transcript |
| `runner_final_response` | yes | Final human-readable agent completion text, if available |
| `runner_metadata` | yes | Structured invocation and capture metadata |

Runner adapters may also emit typed optional artifact payloads for persistence by the run-artifact service, including adapter-local raw captures and debug outputs. Those optional payloads are non-canonical unless assigned a canonical role by OA04.3.

Recommended metadata fields:

- `agent_family`
- `invocation_mode`
- `command`
- `working_directory`
- `prompt_reference`
- `started_at`
- `ended_at`
- `exit_code`
- `termination`
- `capture_format`

Optional artifacts are allowed:

- raw stderr/stdout logs,
- native JSONL event streams,
- native response files,
- adapter-specific debug captures.

Optional artifacts MUST NOT replace the normalized artifact set.

Filesystem layout is owned by [ADR-OA04.3](/architecture/agent-orchestration/adr/adr-oa04.3-provenance-run-artifact-contract.md). OA04.2 freezes required artifact roles and meanings, not concrete file paths.

The maintained runtime SHOULD model this as:

1. adapter parses native output into typed maintained runner models,
2. adapter returns normalized result plus artifact payloads,
3. run-artifact service persists canonical artifacts and step manifest entries.

### 6. Normalization Rules by Adapter

#### Claude CLI

Supported maintained surface is headless `claude --print`, consistent with OA03.1.

Normalization rules:

- stdout structured output or text output is recorded under the canonical `runner_transcript` artifact role.
- Final result content is recorded under the canonical `runner_final_response` artifact role.
- Interactive output or prompt-for-input behavior is a hard mechanical failure, not a supported branch.
- PTY is not part of the maintained Claude adapter contract.

#### Codex CLI

Supported maintained surface is headless `codex exec`, consistent with OA03.3.

Normalization rules:

- JSONL event output is recorded under the canonical `runner_transcript` artifact role.
- `--output-last-message` content is recorded under the canonical `runner_final_response` artifact role.
- Native Codex CLI capture files may be preserved, but the adapter must normalize them into the maintained artifact roles.

### 7. Mechanical Termination Mapping

Runner adapters MUST map native execution outcomes into the shared runner termination enum:

| Shared Termination | Meaning |
|--------------------|---------|
| `completed` | Process exited successfully and no runner-level hard failure occurred |
| `error` | Non-zero exit, malformed required capture, or unsupported output mode |
| `killed_timeout` | Wall-clock timeout exceeded |
| `killed_idle` | Idle timeout exceeded |
| `killed_policy` | Native permission/policy posture or kernel enforcement terminated the run |

Important rules:

- Missing or unparseable optional native artifacts do not by themselves require failure if normalized required artifacts are still produced.
- Missing normalized transcript or metadata artifacts is `error`.
- Unsupported interactive/prompting behavior in a headless-only adapter is `error` or `killed_policy`; it is never silently downgraded to success.

### 8. Evaluator-Facing Evidence Boundary

OA04.2 freezes the minimum evidence that `RUN_AGENT` must make available for later evaluation:

- transcript artifact path,
- final response artifact path,
- invocation metadata,
- workspace diff captured outside the runner by the kernel/workspace layer,
- policy summary captured outside the runner by the policy/run-artifact layer.

Evaluators MUST resolve this evidence through step manifests and canonical artifact roles only. They MUST NOT open adapter-specific raw capture files or depend on incidental runner filenames.

The runner does not classify semantic success. It only ensures the normalized evidence exists for OA06 evaluation.

### 9. Provenance Expectations

The kernel MUST be able to record, per `RUN_AGENT` step:

- agent family used,
- prompt reference,
- artifact paths produced,
- mechanical termination,
- execution timestamps,
- any adapter-reported native exit code.

OA04.2 does not freeze the full provenance ledger schema. It freezes the minimum runner-produced data required for provenance integration.

Where older runner ADRs discuss agent-surface-specific capture details, OA04.x governs maintained runtime contract details for request/result models, artifact lookup, and execution semantics.

Where execution policy is involved, provenance SHOULD distinguish:

- **requested policy**: the agent-neutral execution and permissibility intent passed into the runner,
- **effective policy**: the subset enforced through native runner controls plus kernel-side enforcement.

The canonical policy model and violation taxonomy are deferred to planned `ADR-OA04.4`.

### 10. Non-Goals

This ADR explicitly does not:

- preserve spike module structures as maintained contracts,
- standardize native CLI flag sets beyond what is necessary for supported surfaces,
- require identical native output formats across agents,
- define the full shared permissibility model,
- define native-control mapping taxonomy beyond the runner boundary,
- define planner contradiction logic,
- define web or Playwright harness backend contracts.

---

## Consequences

### Positive

- Gives the maintained OA07 runtime a concrete target for runner implementation.
- Separates runner normalization from spike evidence and agent-specific experimentation.
- Preserves OA03 control-surface decisions while making OA04 execution boundaries implementable.
- Creates a stable handoff for future OA06 evaluator evidence assembly.

### Negative

- Introduces one more contract layer in an already dense ADR family.
- Forces a decision on normalized artifacts before provenance/event schema is fully frozen.
- May require small follow-on model changes in maintained `runners/` and `run_artifacts/`.

---

## Alternatives Considered

### A. Implement runners directly from OA03.1 and OA03.3 without a new decimal ADR

Rejected: too much of the maintained contract would remain implied, especially artifact normalization and evaluator-facing evidence boundaries.

### B. Put runner contract under OA03 as another runner-specific decimal ADR

Rejected: the missing detail is not a new agent surface. It is the maintained execution contract for `RUN_AGENT` within the OA04 runtime family.

### C. Defer runner normalization until after first maintained adapter implementation

Rejected: likely to encode accidental contracts in code and make later provenance/evaluator alignment harder.

---

## Open Questions

- Should normalized runner transcript format be Markdown text, NDJSON, or "native + normalized sidecar" by default?
- Should native exit-code and approval-mode details live in runner metadata only, or also in first-class maintained models?

## Future Considerations

- A future maintained result model may replace per-field artifact paths with a richer artifact-reference structure keyed by canonical role.
- Native transcript preservation versus normalized sidecar generation may warrant a later addendum once real Claude/Codex runtime evidence accumulates.

## Addendum 2026-04-03: Maintained Runner Payload Return Shape

**Context**: The maintained OA04.3/OA04.4 runtime now owns canonical artifact persistence and manifest writing inside `run_artifacts/` and the kernel provenance layer. That made the earlier "result carries transcript/final-response paths" wording too filesystem-shaped for the maintained boundary.

**Decision**: Maintained runner adapters now return:

- mechanical termination,
- typed normalized transcript/final-response payloads,
- typed invocation metadata sufficient for canonical `runner_metadata.json`,
- optional path fields only as transitional or native-capture hints.

The kernel persists canonical `runner_transcript`, `runner_final_response`, and `runner_metadata` artifacts through the run-artifact store. Adapters do not own final manifest registration or canonical artifact layout.

**Rationale**: This keeps persistence ownership aligned with OA04.3, preserves OS01 typing at the runner boundary, and avoids making evaluators depend on adapter-local filenames.

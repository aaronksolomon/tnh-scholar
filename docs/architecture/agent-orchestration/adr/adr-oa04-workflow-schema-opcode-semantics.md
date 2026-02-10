---
title: "ADR-OA04: Workflow Schema + Opcode Semantics"
description: "Defines the canonical workflow document format and execution semantics for tnh-conductor kernel opcodes."
owner: "aaronksolomon"
author: "Aaron Solomon, GPT-5 Codex"
status: wip
created: "2026-02-09"
parent_adr: "adr-oa01.1-conductor-strategy-v2.md"
related_adrs:
  - "adr-oa03-agent-runner-architecture.md"
  - "adr-oa04.1-implementation-notes-mvp-buildout.md"
  - "adr-oa05-prompt-library-specification.md"
  - "adr-oa06-planner-evaluator-contract.md"
---

# ADR-OA04: Workflow Schema + Opcode Semantics

Defines the canonical workflow document format and execution semantics for tnh-conductor kernel opcodes.

- **Status**: WIP
- **Type**: Component ADR
- **Date**: 2026-02-09
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, GPT-5 Codex, Claude Code
- **Parent ADR**: [ADR-OA01.1](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md)
- **Related ADRs**:
  - [ADR-OA03](/architecture/agent-orchestration/adr/adr-oa03-agent-runner-architecture.md)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

ADR-OA01.1 establishes that workflows are "bytecode": declarative step sequences executed by a minimal kernel. It intentionally defers concrete schema and transition semantics to OA04.

Current gaps:

1. There is no canonical workflow document schema with stable versioning.
2. Opcode arguments and required fields are described conceptually but not normalized.
3. Transition behavior (`routes`, planner-selected `next_step`) is not specified as a deterministic contract.
4. Gate and rollback behavior needs explicit machine-level rules so different workflow authors cannot create incompatible semantics.
5. Validation is limited to static validators—no support for **generative evaluation** where agents synthesize test harnesses on-the-fly and the kernel executes them.

Without OA04, conductor behavior remains prompt-defined but runtime mechanics are under-specified, making validation and testing brittle.

### Generative Evaluation Motivation

Some validation scenarios cannot be pre-defined: UI components need visual regression tests, CLI tools need interaction scripts, documentation needs link/example verification. In these cases, an agent synthesizes a test harness tailored to the current diff, the kernel executes it, and the planner evaluates structured results.

This capability MUST be achieved **without expanding the opcode set**. Instead, we stretch `RUN_VALIDATION` to support script-based validators with artifact capture, and define a standard harness report format for planner consumption.

---

## Decision

We define a **versioned workflow schema** and **fixed opcode execution contract** for the kernel runtime.

### 1. Canonical Workflow Document

Every workflow document MUST include:

- `workflow_id` (stable identifier)
- `version` (integer schema + behavior version)
- `description`
- `defaults` (optional shared config: policy, limits, validation profile, artifacts directory)
- `steps` (ordered, unique `id`)
- `entry_step` (initial step id)

#### Defaults Block

The optional `defaults` block provides workflow-wide configuration:

| Field | Type | Description |
|-------|------|-------------|
| `policy` | string | Default policy prompt id for all steps |
| `limits` | object | Default resource limits (timeout, token budget) |
| `artifacts_dir` | string | Base directory for run artifacts (default: `.tnh/run/<run_id>/`) |
| `component_kind` | enum | Hint for harness synthesis: `docs`, `cli`, `web`, `vscode_ui`, `library` |
| `eval_profile` | enum | Validation depth: `smoke`, `overnight`, `release_candidate` |

Minimal shape:

```yaml
workflow_id: "implement_adr"
version: 1
description: "Implement ADR-scoped code changes with validation and review gates."
entry_step: "implement"
defaults:
  artifacts_dir: ".tnh/run/"
  component_kind: "library"
  eval_profile: "smoke"
steps:
  - id: "implement"
    opcode: "RUN_AGENT"
    ...
```

### 2. Supported Kernel Opcodes

OA04 standardizes the opcode set defined in OA01.1:

- `RUN_AGENT`
- `RUN_VALIDATION`
- `EVALUATE`
- `GATE`
- `ROLLBACK`
- `STOP`

Unknown opcodes MUST fail schema validation pre-execution.

### 3. Step Contract by Opcode

Common required fields for executable steps:

- `id`: unique string
- `opcode`: enum
- `routes`: explicit transition map from outcome to next step id or `STOP`

`STOP` is terminal and does not require `routes`.

Opcode-specific required fields:

- `RUN_AGENT`: `agent`, `prompt`, `routes` (required), optional `inputs`, optional `policy`, optional `limits`
- `RUN_VALIDATION`: `run` (list of validator entries—see below), `routes` (required)
- `EVALUATE`: `prompt`, `allowed_next_steps` (required), `routes` (required)—see below
- `GATE`: `gate` (gate type), `routes` (required), optional `approvers`, optional `timeout`
- `ROLLBACK`: `target` (`pre_run` | `pre_step` | `checkpoint:<id>`), `routes` (required)
- `STOP`: optional `reason`

#### EVALUATE Step Contract

`EVALUATE` is the **only decision-making opcode**. To ensure determinism and static validation:

- `allowed_next_steps` is **REQUIRED** (list of valid step ids the planner may select)
- `routes` is **REQUIRED** (explicit mapping from planner status to next step)

**Required shape:**

```yaml
- id: "evaluate_results"
  opcode: "EVALUATE"
  prompt: "planner.evaluate_results.v1"
  allowed_next_steps: ["fix", "gate_final", "rollback", "stop_failed"]
  routes:
    success: "gate_final"
    partial: "fix"
    blocked: "stop_failed"
    unsafe: "rollback"
    needs_human: "gate_final"
```

**Kernel validation rules:**

1. Planner status MUST exist in `routes`
2. Route target MUST be in `allowed_next_steps` or `STOP`
3. `unsafe` MUST route to `ROLLBACK` or `STOP`
4. `needs_human` MUST route to `GATE` or `STOP`
5. Violation of any rule → workflow error (hard fail)

#### RUN_VALIDATION Entry Format

Each entry in `run` can be either:

1. **String** (validator id): References a named, pre-registered validator (e.g., `"tests"`, `"lint"`, `"typecheck"`).

2. **Object** (validator spec): Inline specification for script-based or generative validators.

Object validator spec fields:

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | Unique identifier for this validator |
| `kind` | yes | Validator type: `"builtin"` or `"script"` |
| `entrypoint` | for script | Command or script path to execute |
| `args` | no | Arguments passed to entrypoint |
| `cwd` | no | Working directory (default: repo root) |
| `artifacts` | no | Glob patterns for outputs to capture (e.g., `["*.json", "screenshots/*.png"]`) |
| `timeout` | no | Override default timeout for this validator |

**Note:** "Harness" is a **convention**, not a kernel semantic. Generated test harnesses use `kind: "script"` with appropriate artifact declarations. The kernel executes all script validators identically.

Example with mixed entries:

```yaml
- id: "validate"
  opcode: "RUN_VALIDATION"
  run:
    - "tests"                          # string: builtin validator
    - "lint"                           # string: builtin validator
    - id: "generated_harness"          # object: script validator (harness convention)
      kind: "script"
      entrypoint: ".tnh/run/${run_id}/harness.py"
      args: ["--report", "harness_report.json"]
      artifacts: ["harness_report.json", "screenshots/**/*.png"]
  routes:
    completed: "evaluate"
    error: "STOP"
    killed_timeout: "STOP"
    killed_idle: "STOP"
    killed_policy: "STOP"
```

**Kernel behavior for script/harness validators:**

1. Execute `entrypoint` with `args` in `cwd` (or repo root).
2. Capture stdout/stderr as validator transcript.
3. Collect files matching `artifacts` globs into run artifact directory.
4. Validator passes if exit code is 0; fails otherwise.

### 4. Transition Semantics

The kernel transition algorithm is deterministic:

1. Execute current step.
2. Record artifacts/events.
3. Compute mechanical result (`completed`, `error`, timeout states, policy kill states from OA03).
4. Resolve transition:
   - For non-`EVALUATE` steps: use mechanical outcome key in `routes`.
   - For `EVALUATE`: planner emits semantic status; kernel maps status via `routes`.
5. If next step is invalid, halt with workflow error.

`EVALUATE` mapping rules:

- `success` -> configured success target
- `partial` -> configured partial target
- `blocked` -> configured blocked target (default `STOP`)
- `unsafe` -> MUST route to `ROLLBACK` or `STOP`
- `needs_human` -> MUST route to `GATE` or `STOP`

### 5. Gate Semantics

`GATE` is a first-class blocking opcode. Kernel behavior:

- Persist gate request artifact (step id, reason, required decision).
- Mark run state as waiting.
- Resume only via explicit human action.
- Apply timeout behavior if configured (`timeout` → route via `routes.killed_timeout`).

**Gate outcomes are provenance events, not opcodes:**

| Event | Trigger | Description |
|-------|---------|-------------|
| `gate_requested` | GATE step begins | Records gate type, step id, reason |
| `gate_approved` | Human approves | Workflow continues via `routes.gate_approved` |
| `gate_rejected` | Human rejects | Workflow continues via `routes.gate_rejected` |
| `gate_timed_out` | Timeout expires | Workflow continues via `routes.gate_timed_out` |

**Rationale:** Keeping gate outcomes as events (not opcodes) preserves opcode stability and enables replay/debug without inventing new execution semantics.

### 6. Rollback Semantics

`ROLLBACK` implements deterministic git-state cleanup (aligned with OA01.1):

- Scope is limited to conductor work branch/worktree.
- Rollback never touches protected branches.
- Every rollback emits provenance events and post-rollback workspace diff/status.

**Target hierarchy:**

| Target | Availability | Description |
|--------|--------------|-------------|
| `pre_run` | **Required** (always available) | Snapshot at workflow start; primary escape hatch |
| `pre_step` | Optional | Snapshot before the triggering step; finer granularity |
| `checkpoint:<id>` | Reserved (future) | Named checkpoint; not implemented in MVP |

**Kernel behavior:**

1. Resolve target to a git commit SHA.
2. Reset worktree to target state (`git checkout` or equivalent).
3. Emit `rollback_completed` provenance event with before/after diff.
4. Continue to next step via `routes` (rollback itself succeeds or fails mechanically).

### 7. Workflow Validation Rules

Pre-run validation MUST enforce:

1. `entry_step` exists.
2. Step ids are unique.
3. Every transition target exists or is `STOP`.
4. No unreachable steps unless explicitly marked `allow_unreachable: true`.
5. `unsafe`/`needs_human` planner statuses have legal routing targets.
6. Opcode-specific required fields exist.

### 8. Artifact Conventions

All run artifacts are written to a structured directory:

```
.tnh/run/<run_id>/
├── transcript.md           # Agent session transcript
├── diff.patch              # Git diff for this run
├── harness/                # Generated harness code (if any)
│   ├── harness.py
│   └── fixtures/
├── harness_report.json     # Structured validation results
├── screenshots/            # Visual artifacts (if captured)
└── logs/                   # Additional logs from validators
```

**Conventions:**

- `<run_id>` is a unique identifier for each workflow execution (e.g., timestamp + short hash).
- Agents and harness writers MUST write generated code/specs to `.tnh/run/<run_id>/harness/`.
- The kernel captures artifacts declared in `RUN_VALIDATION` entries and copies them to the run directory.
- Artifact paths in reports should be relative to the run directory.

### 9. Harness Report Schema

For generative evaluation, validators emit a structured **Harness Report** (JSON) that the planner consumes via `EVALUATE`.

**Minimum required fields:**

```json
{
  "suite_id": "cli_smoke_tests",
  "version": "1.0.0",
  "generated_at": "2026-02-09T14:30:00Z",
  "cases": [
    {
      "id": "test_help_command",
      "kind": "cli",
      "status": "passed",
      "repro": "tnh-gen --help",
      "observations": [],
      "artifacts": []
    },
    {
      "id": "test_invalid_flag",
      "kind": "cli",
      "status": "failed",
      "repro": "tnh-gen --invalid",
      "observations": ["Expected exit code 1, got 0"],
      "artifacts": ["logs/invalid_flag.log"]
    }
  ],
  "summary": {
    "passed": 1,
    "failed": 1,
    "flaky": 0,
    "duration_ms": 1250
  }
}
```

**Optional but recommended: `ux_flags`**

For UI/UX validation, harnesses can emit flags for human review:

```json
{
  "ux_flags": [
    {
      "severity": "warning",
      "area": "accessibility",
      "description": "Button lacks aria-label",
      "evidence_ref": "screenshots/button_missing_aria.png"
    }
  ]
}
```

**Harness Report field definitions:**

| Field | Type | Description |
|-------|------|-------------|
| `suite_id` | string | Identifier for this test suite |
| `version` | string | Schema version of the report |
| `generated_at` | ISO 8601 | When the harness was executed |
| `cases[]` | array | Individual test case results |
| `cases[].id` | string | Unique test case identifier |
| `cases[].kind` | enum | Test type: `cli`, `web`, `docs`, `vscode_ui`, `unit` |
| `cases[].status` | enum | `passed`, `failed`, `skipped`, `flaky` |
| `cases[].repro` | string | Command or steps to reproduce |
| `cases[].observations` | array | Human-readable notes or failure messages |
| `cases[].artifacts` | array | Paths to supporting files (relative to run dir) |
| `ux_flags[]` | array | Optional UX/accessibility concerns |
| `summary` | object | Aggregate counts and timing |

**Validation boundary (kernel vs planner):**

| Layer | Responsibility |
|-------|----------------|
| **Kernel** | Validates minimal structure only |
| **Planner (OA06)** | Owns semantic interpretation |

**Kernel MUST enforce:**

- Artifact exists (if declared in `RUN_VALIDATION`)
- JSON parses without error
- Required top-level keys present: `suite_id`, `cases`, `summary`

**Planner handles (OA06 territory):**

- Schema version compatibility
- Status derivation from test results
- UX flag severity interpretation
- Fix instruction generation

**Rationale:** Kernel stays small and stable; planner absorbs schema evolution.

### 10. Golden Snapshot Safety Rule

When a harness proposes updated golden snapshots (visual regression baselines, expected outputs), the workflow MUST route through a `GATE` before acceptance.

**Rationale:** Automatic golden updates can mask regressions. Human approval prevents silent drift.

**Workflow authoring-time requirement (static / pre-run):**

- If a workflow includes generative harness execution that could produce `proposed_goldens`, it MUST include a `GATE` step reachable from the evaluation path.
- Pre-run validation checks this in weak form (presence + reachability only).

**Runtime enforcement (strong):**

- When the kernel observes a non-empty `proposed_goldens` field in a harness report artifact, the next transition MUST pass through a `GATE` before the run can reach success `STOP` (or before any accept-goldens action).

### 11. Opcode Non-Negotiables

The following invariants define the semantic boundaries of each opcode. Violations indicate architectural misuse.

| Opcode | Semantic Boundary |
|--------|-------------------|
| `RUN_AGENT` | Heavy edits only (CLI runners: Claude, Codex). Never used for structured decisions. |
| `EVALUATE` | Structured decision only (via tnh-gen / GenAIService). Planner emits status from bounded set. |
| `RUN_VALIDATION` | Deterministic execution + artifact capture. Exit code determines pass/fail. |
| `GATE` | Human decision point. Outcomes are events, not opcodes. |
| `ROLLBACK` | Deterministic git-state cleanup. Never touches protected branches. |
| `STOP` | Terminal state. No further steps execute. |

**Critical invariant:** The kernel never interprets free-form text. All semantic interpretation happens in the planner (via `EVALUATE`), which emits structured outputs that the kernel routes mechanically.

---

## Appendix: Canonical Workflow Patterns

### Pattern A: Generative Evaluation Micro-Sequence

This pattern shows how existing opcodes compose for generative testing:

```yaml
workflow_id: "generative_eval"
version: 1
description: "Synthesize and execute a test harness for changed components."
entry_step: "synthesize"
defaults:
  artifacts_dir: ".tnh/run/"
  component_kind: "cli"
  eval_profile: "smoke"

steps:
  # Step 1: Agent synthesizes harness based on diff + component_kind
  - id: "synthesize"
    opcode: "RUN_AGENT"
    agent: "claude-code"
    prompt: "task.synthesize_harness.v1"
    inputs: ["diff", "component_kind"]
    routes:
      completed: "execute_harness"
      error: "STOP"
      killed_timeout: "STOP"
      killed_idle: "STOP"
      killed_policy: "STOP"

  # Step 2: Kernel executes harness; captures report + artifacts
  - id: "execute_harness"
    opcode: "RUN_VALIDATION"
    run:
      - id: "generated_harness"
        kind: "script"  # harness is a convention, not a kernel semantic
        entrypoint: ".tnh/run/${run_id}/harness/harness.py"
        args: ["--report", "harness_report.json"]
        artifacts: ["harness_report.json", "screenshots/**/*.png", "logs/**"]
    routes:
      completed: "evaluate"
      error: "evaluate"           # Still evaluate on failure to capture structured report
      killed_timeout: "evaluate"
      killed_idle: "evaluate"
      killed_policy: "evaluate"

  # Step 3: Planner evaluates structured report
  - id: "evaluate"
    opcode: "EVALUATE"
    prompt: "planner.evaluate_harness_report.v1"
    allowed_next_steps: ["fix", "golden_gate", "STOP"]
    routes:
      success: "STOP"
      partial: "fix"
      blocked: "STOP"
      unsafe: "STOP"
      needs_human: "golden_gate"

  # Step 4 (optional): Agent fixes issues based on planner instructions
  - id: "fix"
    opcode: "RUN_AGENT"
    agent: "claude-code"
    prompt: "task.fix_from_harness_report.v1"
    inputs: ["harness_report", "fix_instructions"]
    routes:
      completed: "execute_harness"
      error: "STOP"
      killed_timeout: "STOP"
      killed_idle: "STOP"
      killed_policy: "STOP"

  # Step 5: Gate for golden snapshot approval
  - id: "golden_gate"
    opcode: "GATE"
    gate: "requires_approval"
    routes:
      gate_approved: "STOP"
      gate_rejected: "STOP"
      gate_timed_out: "STOP"
```

**Key points:**

- `RUN_AGENT` synthesizes the harness—prompt defines how (OA05 territory).
- `RUN_VALIDATION` executes it—kernel captures artifacts mechanically.
- `EVALUATE` interprets the report—planner prompt defines criteria (OA06 territory).
- Optional fix loop allows iteration without human intervention for minor issues.
- `GATE` ensures human approval for golden updates.

---

## Consequences

### Positive

- Enables typed workflow compilation and static validation before execution.
- Makes conductor runtime deterministic and testable across workflow authors.
- Reduces ambiguity around planner-vs-kernel responsibilities.
- Establishes a clear integration surface for OA06 (planner evaluator contract).
- **Generative evaluation without opcode expansion**: Script validators + artifact capture + harness report schema enable agents to synthesize test harnesses while keeping the kernel minimal.
- **Structured validation artifacts**: Harness reports provide a machine-readable contract between validators and planner, enabling sophisticated evaluation prompts.
- **Golden snapshot safety**: Mandatory GATE for proposed goldens prevents silent regression drift.

### Negative

- Adds upfront authoring friction (more explicit transition fields).
- Requires migration for any ad-hoc workflow definitions created during spikes.
- May require schema evolution machinery sooner (version 2+) as new opcodes appear.
- **Harness synthesis complexity**: Agents must produce valid harnesses that emit conformant reports—prompt engineering burden shifts to OA05.

---

## Alternatives Considered

### A. Prompt-only control flow (no explicit transitions)

Rejected: too implicit; prevents static validation and deterministic replay.

### B. Hardcoded Python workflow classes instead of YAML schema

Rejected: conflicts with OA01.1 prompt-program runtime valuation and slows iteration.

### C. DAG-first model in OA04

Deferred: OA04 keeps step sequencing explicit and bounded. DAG expansion remains future work once linear semantics are proven in production.

---

## Open Questions

*All original open questions have been resolved. Decisions documented in this ADR and ADR-OA04.1.*

| Original Question | Resolution | Location |
|-------------------|------------|----------|
| `allowed_next_steps` required? | Yes, required for all EVALUATE steps | Section 3: EVALUATE Step Contract |
| Formal `checkpoint` opcode? | No; `pre_run` required, `pre_step` optional, `checkpoint:<id>` reserved | Section 6: Rollback Semantics |
| Gate resume actions as opcodes? | No; gate outcomes are provenance events | Section 5: Gate Semantics |
| Harness report versioning? | Kernel validates structure; planner owns semantics | Section 9: Validation boundary |
| Artifact retention policy? | System-level, not workflow-authored | ADR-OA04.1 |
| Harness sandboxing? | Worktree isolation + sanitized env + entrypoint allowlist | ADR-OA04.1 |

---

## Implementation Plan

### Phase 1: Schema and Models

- Define workflow schema models in `tnh_conductor` domain layer.
- Add parser/validator with deterministic error reporting.
- **Support `RUN_VALIDATION` object entries** with `kind: script` and basic artifact capture.

### Phase 2: Kernel Transition Engine

- Implement transition resolver with status mapping rules.
- Enforce opcode contracts and legal targets at runtime.
- **Add harness report schema** (`harness_report.json`) and planner prompt contract stub for consuming it.

### Phase 3: Fixtures and Golden Tests

- Add workflow fixtures covering success, partial, blocked, unsafe, needs_human.
- Add regression tests for validation failures and rollback/gate invariants.
- **Add generative evaluation workflow fixture** demonstrating the Pattern A micro-sequence.

### Phase 4: Harness Backends (Deferred)

- VS Code UI automation backend (deferred—start with CLI + headless web via Playwright).
- Visual regression tooling integration.
- Accessibility scanner integration.

---

## Related ADRs

- [ADR-OA01.1: TNH-Conductor Strategy v2](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md) — Parent strategy; defines opcode set and kernel/prompt-program split
- [ADR-OA03: Agent Runner Architecture](/architecture/agent-orchestration/adr/adr-oa03-agent-runner-architecture.md) — Runner contracts referenced by `RUN_AGENT` semantics
- [ADR-OA04.1: Implementation Notes](/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md) — MVP build-out sequence and operational decisions
- [ADR-OA05: Prompt Library Specification](/architecture/agent-orchestration/adr/adr-oa05-prompt-library-specification.md) — Defines prompt artifact format; harness synthesis prompts are OA05 territory
- [ADR-OA06: Planner Evaluator Contract](/architecture/agent-orchestration/adr/adr-oa06-planner-evaluator-contract.md) — Defines how planner interprets `harness_report.json`; OA04 only specifies artifact format
- **ADR-OA07: Diff-Policy + Safety Rails** (planned) — Golden snapshot approval rules may be further detailed there

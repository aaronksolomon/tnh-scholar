---
title: "ADR-OA07.6: Execution Subsystem Design"
description: "Defines the shared execution subsystem for tnh-conductor MVP, including typed process request/result contracts, cwd/env policy, timeout taxonomy, and the final argv rendering boundary."
type: "design-detail"
owner: "aaronksolomon"
author: "Aaron Solomon, GPT-5 Codex"
status: accepted
created: "2026-03-06"
parent_adr: "adr-oa07-mvp-runtime-architecture-strategy.md"
related_adrs:
  - "adr-oa07.2-runner-subsystem-design.md"
  - "adr-oa07.3-validation-subsystem-design.md"
  - "adr-oa04.2-mvp-hardening-compliance-plan.md"
  - "adr-os01-object-service-architecture-v3.md"
---

# ADR-OA07.6: Execution Subsystem Design

Defines the shared execution subsystem for tnh-conductor MVP, including typed process request/result contracts, cwd/env policy, timeout taxonomy, and the final argv rendering boundary.

- **Status**: Accepted
- **Type**: Design Detail
- **Date**: 2026-03-06
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, GPT-5 Codex
- **Parent ADR**: [ADR-OA07](/architecture/agent-orchestration/adr/adr-oa07-mvp-runtime-architecture-strategy.md)
- **Related ADRs**:
  - [ADR-OA07.2](/architecture/agent-orchestration/adr/adr-oa07.2-runner-subsystem-design.md)
  - [ADR-OA07.3](/architecture/agent-orchestration/adr/adr-oa07.3-validation-subsystem-design.md)
  - [ADR-OA04.2](/architecture/agent-orchestration/adr/adr-oa04.2-mvp-hardening-compliance-plan.md)
  - [ADR-OS01](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

`runners/` and `validation/` both rely on a shared low-level process-execution boundary. Earlier ADRs established that naked argv vectors must not cross runner, validation, or kernel-facing domain contracts, and that final argv rendering is permitted only at the last infrastructure edge.

That makes `execution/` the most security-sensitive shared subsystem in the maintained MVP runtime.

Without a normative execution design, implementers would still be forced to improvise:

- process request/result models
- cwd and environment policy
- timeout and termination behavior
- stdout/stderr handling
- subprocess error taxonomy

This ADR defines the smallest acceptable maintained contract for that shared substrate.

### Execution Definition

For agent-orchestration MVP, execution means:

> trusted low-level process launch and result capture for typed runner and validation execution requests.

Execution is not:

- a runner-domain contract
- a validation-domain contract
- a generic workflow or planner API
- the owner of prompt semantics, transcript semantics, or harness semantics

### Implementation Guidance

Execution touches the most sensitive external boundary in the current design. This is where object-service rigor should be strongest.

Guidance for implementers:

- accept only typed execution requests
- render argv only at the final subprocess edge
- keep cwd/env policy explicit and narrow
- make timeout and termination outcomes part of the typed result contract
- do not let domain-specific semantics from runners or validation leak into execution models

Goal:

> one narrow, trusted subprocess boundary shared by maintained subsystems

---

## Decision

### 1. The maintained execution package is `agent_orchestration/execution/`

This package owns:

- typed execution request/result models
- final argv rendering from typed execution requests
- cwd and environment policy application
- subprocess launch
- timeout enforcement
- low-level stdout/stderr capture
- termination classification

It does not own:

- runner-domain prompt semantics
- validator-domain harness/report semantics
- kernel route semantics

### 2. Execution contracts are typed request/result objects

The execution subsystem will define typed process request/result models.

Minimum execution request model:

- explicit invocation family
- typed invocation payload for that family
- working directory
- environment policy
- timeout policy
- output capture policy

MVP guidance:

- the request shape should be a small discriminated union of invocation families, not one catch-all payload object
- preferred maintained families are:
  - CLI executable invocation
  - Python script or module invocation
- each family should carry its own typed argument model rather than generic string lists hidden inside a wrapper

Minimum execution result model:

- termination outcome
- exit code or null if unavailable
- stdout bytes/text capture
- stderr bytes/text capture
- timeout or kill metadata when relevant

`execution/` must not accept:

- `list[str]` or `tuple[str, ...]` from kernel-facing contracts
- free-form dict subprocess payloads
- workflow-authored command structures

MVP guidance:

- the maintained execution interface should be sync-only in MVP
- if concurrency becomes necessary later, add it as a higher-level coordination concern or a new execution implementation rather than forcing async contracts through the whole subsystem stack early

### 3. Environment and cwd policy must be explicit

Execution requests must carry typed cwd and environment policy rather than ad hoc path/string decisions.

MVP rules:

- cwd must be an explicit `Path`
- environment behavior should be one of:
  - inherit minimal parent environment
  - inherit with explicit overrides
  - isolated allowlisted environment

The default maintained bias should be narrow inheritance plus explicit overrides.

### 4. Timeout and termination taxonomy are shared and typed

The execution result contract should normalize mechanical process outcomes into a shared typed taxonomy.

At MVP this taxonomy should distinguish at least:

- completed
- non-zero exit
- wall-clock timeout
- idle timeout
- policy kill
- startup failure

Runner and validation subsystems may map these execution outcomes into their own domain results, but the low-level taxonomy should be shared here.

MVP guidance:

- idle timeout detection should be based on observed stdout/stderr activity only
- heartbeat files or other auxiliary liveness signals should not be introduced unless a maintained runner later proves output-based idle detection is insufficient

### 5. Stdout/stderr are execution outputs, not domain semantics

`execution/` may capture stdout and stderr, but it does not interpret them.

That means:

- `execution/` returns captured output
- `runners/` interpret runner output into transcripts/final responses
- `validation/` interprets output into validation evidence only where needed

### 6. Final argv rendering happens only here

The final transformation from typed execution request to subprocess argv happens only inside `execution/`.

This is the critical trust-boundary rule for the maintained MVP.

Callers may prepare structured invocation data, but they may not bypass the execution request contract and hand raw argv into the subsystem interface.

### 7. Execution remains shared infrastructure, not a generic domain API

Both `runners/` and `validation/` may use `execution/`, but the subsystem should remain small and infrastructure-oriented.

Do not turn it into a generic “command platform” or let it absorb runner/validation semantics.

---

## Suggested Package Shape

```text
agent_orchestration/execution/
  __init__.py
  models.py                # execution requests, results, timeout/env policies
  protocols.py             # execution-facing contracts if needed
  service.py               # trusted subprocess orchestration
  renderer.py              # final typed request -> argv translation
```

Notes:

- keep the package flat until multiple execution backends exist
- a single filesystem/OS subprocess backend is the MVP assumption

---

## Consequences

### Positive

- Makes the riskiest shared boundary explicit before implementation.
- Gives runner and validation ADRs a concrete shared substrate instead of a placeholder.
- Prevents raw argv from reappearing in higher-level contracts.
- Centralizes timeout and termination behavior.

### Negative

- Adds one more subsystem ADR before implementation starts.
- Forces early discipline around execution policy instead of allowing ad hoc subprocess calls.

### Neutral

- MVP may still use standard subprocess primitives under the hood; the architectural change is about contract shape and trust boundaries, not tool choice.

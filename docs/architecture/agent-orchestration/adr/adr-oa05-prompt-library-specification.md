---
title: "ADR-OA05: Prompt Library Specification"
description: "Defines prompt artifact format, versioning, template rendering, and harness synthesis contracts for tnh-conductor."
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Code"
status: proposed
created: "2026-02-09"
parent_adr: "adr-oa01.1-conductor-strategy-v2.md"
related_adrs:
  - "adr-oa04-workflow-schema-opcode-semantics.md"
  - "adr-oa06-planner-evaluator-contract.md"
---

# ADR-OA05: Prompt Library Specification

Defines prompt artifact format, versioning, template rendering, and harness synthesis contracts for tnh-conductor.

- **Status**: Proposed
- **Type**: Component ADR
- **Date**: 2026-02-09
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, Claude Code
- **Parent ADR**: [ADR-OA01.1](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md)
- **Related ADRs**:
  - [ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)
  - [ADR-OA06](/architecture/agent-orchestration/adr/adr-oa06-planner-evaluator-contract.md)

---

> **STUB ADR**: This ADR captures scope and boundary points deferred from OA04. Full design pending.

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

ADR-OA01.1 establishes that "behavior lives in prompts" — the prompt library is the "standard library" of system behavior. OA04 defines workflow schema and opcode semantics but defers prompt artifact format to OA05.

With the generative evaluation stretch in OA04, specific prompt contracts have emerged that require formal specification.

---

## Scope

OA05 will address:

- **Prompt artifact format**: YAML structure for task, policy, evaluation, triage, risk, journal, and agent prompts
- **Versioning scheme**: How prompts are versioned (`id.version` references in workflows)
- **Template rendering**: Jinja2 or similar for input interpolation
- **Input/output contracts**: Typed schemas for prompt inputs and expected outputs
- **Prompt catalog protocol**: How the kernel discovers and loads prompts

---

## Boundary Points from OA04

The following integration points were identified during OA04 design:

### Harness Synthesis Prompts

OA04 Pattern A references `task.synthesize_harness.v1`:

- **Inputs**: `diff`, `component_kind` (from workflow defaults)
- **Output contract**: Must write valid harness code to `.tnh/run/<run_id>/harness/`
- **Harness requirements**: Must emit `harness_report.json` conforming to OA04 Section 9 schema

### Fix Prompts

OA04 Pattern A references `task.fix_from_harness_report.v1`:

- **Inputs**: `harness_report`, `fix_instructions` (from planner)
- **Output contract**: Code changes addressing failed test cases

### Prompt Type: `harness`

Consider adding a new prompt type specifically for harness synthesis:

```yaml
prompt: task.synthesize_harness
version: 1
type: harness  # New type?

inputs:
  - name: diff
    type: unified_diff
  - name: component_kind
    type: enum[docs, cli, web, vscode_ui, library]

output_contract:
  artifacts:
    - path: "harness/harness.py"
      required: true
    - path: "harness_report.json"
      schema: "harness_report.v1"
      required: true
```

---

## Open Questions

1. Should harness prompts have a distinct `type: harness` or remain under `type: task`?
2. How do prompt output contracts relate to OA04 artifact capture globs?
3. Should prompt schemas be validated at workflow compile time or runtime?
4. How do we handle prompt library evolution without breaking existing workflows?

---

## Decision

*To be designed.*

---

## Consequences

*To be designed.*

---

## Related ADRs

- [ADR-OA01.1: TNH-Conductor Strategy v2](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md) — Establishes prompt library as "standard library"
- [ADR-OA04: Workflow Schema + Opcode Semantics](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md) — Defines artifact format; references prompt IDs
- [ADR-OA06: Planner Evaluator Contract](/architecture/agent-orchestration/adr/adr-oa06-planner-evaluator-contract.md) — Evaluation prompts are OA05 artifacts consumed per OA06 contract

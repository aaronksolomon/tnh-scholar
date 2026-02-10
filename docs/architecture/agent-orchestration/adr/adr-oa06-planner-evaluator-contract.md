---
title: "ADR-OA06: Planner Evaluator Contract"
description: "Defines input/output schemas, status derivation rules, and harness report interpretation for the tnh-conductor planner."
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Code"
status: proposed
created: "2026-02-09"
parent_adr: "adr-oa01.1-conductor-strategy-v2.md"
related_adrs:
  - "adr-oa04-workflow-schema-opcode-semantics.md"
  - "adr-oa05-prompt-library-specification.md"
---

# ADR-OA06: Planner Evaluator Contract

Defines input/output schemas, status derivation rules, and harness report interpretation for the tnh-conductor planner.

- **Status**: Proposed
- **Type**: Component ADR
- **Date**: 2026-02-09
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, Claude Code
- **Parent ADR**: [ADR-OA01.1](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md)
- **Related ADRs**:
  - [ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)
  - [ADR-OA05](/architecture/agent-orchestration/adr/adr-oa05-prompt-library-specification.md)

---

> **STUB ADR**: This ADR captures scope and boundary points deferred from OA04. Full design pending.

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

ADR-OA01.1 establishes the Planner Evaluator as "the only decision-making locus in the system." OA04 defines the `EVALUATE` opcode and transition semantics but defers planner input/output contracts to OA06.

With the generative evaluation stretch in OA04, the planner must now interpret structured `harness_report.json` artifacts in addition to transcripts and diffs.

---

## Scope

OA06 will address:

- **Planner input schema**: Structured inputs for `EVALUATE` steps
- **Planner output schema**: Status, blockers, side_paths, risk_flags, next_step, review_entries
- **Harness report interpretation**: How test results map to planner status
- **Contradiction detection**: Rules for detecting transcript/workspace inconsistencies (per OA01.1)
- **Provenance window**: How historical context (last K steps) is provided to the planner
- **Fix instruction generation**: Output format for `fix_instructions` passed to fix agents

---

## Boundary Points from OA04

The following integration points were identified during OA04 design:

### Harness Report Consumption

OA04 Section 9 defines `harness_report.json` schema. OA06 must specify:

- **Status derivation from test results**:

  | Test Summary | Planner Status |
  |--------------|----------------|
  | All passed, no ux_flags | `success` |
  | All passed, ux_flags present | `partial` or `needs_human` |
  | Some failed, fixable | `partial` with `fix_instructions` |
  | Critical failures | `blocked` or `unsafe` |
  | `proposed_goldens` present | `needs_human` → route to GATE |

- **Fix instruction format**: What structure does `fix_instructions` take for the fix agent?

### Evaluation Prompt Contract

OA04 references `planner.evaluate_harness_report.v1`. OA06 defines:

- Required inputs: `harness_report`, `step_intent`, `transcript`, `diff_summary`, `validation_results`
- Required outputs: `status`, `next_step`, optional `fix_instructions`, `blockers`, `risk_flags`

### Planner Statelessness

Per OA01.1, the planner is stateless but receives a "provenance window." OA06 must specify:

- Window size (default: last 2-3 steps)
- What fields from prior steps are included
- How repeated failures trigger escalation (e.g., 3 consecutive `partial` → `needs_human`)

---

## Open Questions

1. Should `fix_instructions` be structured (JSON) or natural language for the fix agent?
2. What is the maximum provenance window size before context becomes unwieldy?
3. Should planner status derivation rules be prompt-defined or kernel-enforced?
4. How do `ux_flags` severity levels map to planner status? (e.g., `severity: error` → `blocked`?)

---

## Decision

*To be designed.*

---

## Consequences

*To be designed.*

---

## Related ADRs

- [ADR-OA01.1: TNH-Conductor Strategy v2](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md) — Defines planner as decision-making locus; specifies dual-channel evaluation
- [ADR-OA04: Workflow Schema + Opcode Semantics](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md) — Defines `harness_report.json` schema; OA06 specifies interpretation
- [ADR-OA05: Prompt Library Specification](/architecture/agent-orchestration/adr/adr-oa05-prompt-library-specification.md) — Evaluation prompts are OA05 artifacts; OA06 defines their contract

---
title: "ADR Template"
description: "Reusable template for TNH Scholar architecture decision records."
owner: ""
author: ""
status: processing
created: "2025-02-27"
---
# ADR-XXX: Concise Decision Title

One-sentence or short paragraph summarizing the decision.

- **Filename**: `adr-<modulecode><number>-<descriptor>.md` (e.g., `adr-dd01-docs-reorg.md`). Append `-strategy` for strategy ADRs.
- **Heading**: `# ADR-<MODULECODE><NUMBER>: Title` (uppercase module code for readability).
- **Status**: Proposed
- **Date**: YYYY-MM-DD
- **Authors**: Initial creator of ADR (typically an AI agent or system, plus human initiator/reviewer)
- **Owner**: Person or group responsible (typically aaronksolomon (git name), current repo maintainer/builder)

## Context

Describe the background, forces, and problems that make the decision necessary. Provide enough detail for future readers to understand the environment without reading code.

## Decision

State the decision clearly. Use bullet points or sub-headings if the decision has multiple parts (e.g., architecture, tooling, processes).

## Consequences

- **Positive**: List the benefits or opportunities created by this decision.
- **Negative**: Call out trade-offs, risks, or work created.

## Alternatives Considered

Summarize other options that were evaluated and why they were rejected (optional but encouraged).

## Open Questions

Document any follow-up work, unresolved issues, or validation steps to revisit later.

---

## As-Built Notes & Addendums

*Optional section for post-decision updates. Never edit the original Context/Decision/Consequences sections - always append addendums here to preserve historical decision-making context.*

### Addendum YYYY-MM-DD: Brief Title

**Context**: Describe what changed or was discovered during implementation.

**Decision**: Document the actual implementation decision or deviation from the original plan.

**Rationale**: Explain why the change was necessary.

**Implementation Changes**: List specific code/config changes.

**References**: Link to related TODOs, issues, or ADRs.

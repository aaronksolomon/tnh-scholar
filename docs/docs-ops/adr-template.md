---
title: "ADR Template"
description: "Reusable template for TNH Scholar architecture decision records."
owner: ""
author: ""
status: current
created: "2025-02-27"
updated: "2025-12-12"
---

# ADR Template

Template for ADRs in TNH scholar system

## Frontmatter Patterns

### Standard ADR Frontmatter

```yaml
---
title: "ADR-XXX: Decision Title"
description: "Brief summary of decision"
owner: "aaronksolomon"
author: "Author Name, Claude Sonnet 4.5"
status: proposed
created: "YYYY-MM-DD"
---
```

### Decimal ADR Frontmatter (added 2025-12-12)

For supporting/related ADRs (e.g., `adr-at03.1-transition-plan.md`):

```yaml
---
title: "ADR-XXX.N: Supporting Decision Title"
description: "Brief summary of supporting decision"
type: "transition-strategy"  # or: "implementation-guide", "testing-strategy", etc.
owner: "aaronksolomon"
author: "Author Name, Claude Sonnet 4.5"
status: proposed
created: "YYYY-MM-DD"
parent_adr: "adr-xxx-main-decision.md"  # Required for decimal ADRs
related_adrs: ["adr-yyy-related.md", "adr-zzz-related.md"]  # Optional
---
```

**Required fields for decimal ADRs**:

- `parent_adr`: Filename of the parent/main ADR
- `type`: ADR type (e.g., "transition-strategy", "implementation-guide", "testing-strategy")

**Optional fields**:

- `related_adrs`: List of related ADR filenames

### ADR Types (Canonical List)

**Main ADR types** (no decimal):

- (default/unspecified): Standard architectural decision
- `strategy`: High-level directional decision (use `-strat` suffix in filename)

**Decimal ADR types** (supporting/related):

- `transition-strategy`: Migration or phased implementation plan
- `implementation-guide`: Detailed implementation instructions
- `testing-strategy`: Test approach and validation plan
- `design-detail`: Detailed design decisions for specific components
- `evaluation-report`: Analysis or comparison of alternatives

**Usage notes**:

- Main ADRs typically don't specify `type` (it's implied as architectural decision)
- Decimal ADRs **must** specify `type` for clarity
- Feel free to propose new types if existing ones don't fit—update this list when accepted

## Template

```markdown
# ADR-XXX: Concise Decision Title

One-sentence or short paragraph summarizing the decision.

- **Filename**: `adr-<modulecode><number>-<descriptor>.md` (e.g., `adr-dd01-docs-reorg.md`). Append `-strategy` for strategy ADRs.
- **Decimal Naming** (added 2025-12-12): For related/supporting ADRs, use decimal notation:
  - Main ADR: `adr-at03-object-service-refactor.md`
  - Supporting: `adr-at03.1-transition-plan.md`, `adr-at03.2-implementation-guide.md`
  - Decimal ADRs should include `parent_adr` and `type` fields in frontmatter (see below)
- **Heading**: `# ADR-<MODULECODE><NUMBER>: Title` (uppercase module code for readability).
- **Status**: Proposed
- **Date**: YYYY-MM-DD
- **Authors**: Initial creator of ADR (typically an AI agent or system, plus human initiator/reviewer)
- **Owner**: Person or group responsible (typically aaronksolomon (git name), current repo maintainer/builder)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status (note that the adr status is not the same as the markdown frontmatter status -> see markdown standards for frontmatter status codes.)

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`,  status**: Coding has begun. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums (see below).
- **Status transitions**: If we need to make significant changes to an ADR in `accepted` or `wip` status, and an addendum is insufficient, we should supersede the ADR with a new one. General rule: no edits accept addendums after moving out of proposed.

**Rationale**: Once implementation begins, the original decision must be preserved for historical context. Changes during/after implementation are tracked as addendums to show the evolution of thinking.

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

---

## Historical References

*Optional section for linking to superseded ADRs or archived design documents. Use this pattern to provide progressive disclosure of historical context for maintainers and contributors.*

<details>
<summary>📚 View superseded design documents (maintainers/contributors)</summary>

**Note**: These documents are archived and excluded from the published documentation. They provide historical context for the current design.

### Superseded ADRs

- **[ADR-XX: Title](<docs-absolute-path>/archive/adr/adr-xx-title.md)** (YYYY-MM-DD)
  *Status*: Superseded by this ADR

### Earlier Design Explorations

- **[Design Doc Title](<docs-absolute-path>/archive/design-doc.md)** (YYYY-MM-DD)
  *Status*: Replaced by this ADR

</details>
```

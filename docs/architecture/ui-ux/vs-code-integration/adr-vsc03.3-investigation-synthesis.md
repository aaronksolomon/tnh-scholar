---
title: "ADR-VSC03.3: Investigation Synthesis - Validation of Design Choices"
description: "Synthesis of real-world survey findings validating TNH Scholar's VS Code integration strategy and design decisions"
owner: "phapman"
author: "Claude Sonnet 4"
type: "investigation-synthesis"
parent_adr: "adr-vsc03-python-javascript-impedance-investigation.md"
status: "draft"
created: "2025-12-12"
---

# ADR-VSC03.3: Investigation Synthesis - Validation of Design Choices

This synthesis analyzes findings from **ADR-VSC03.2** (Real-World Survey Addendum) to validate design choices made in earlier ADRs and propose minor refinements based on ecosystem precedents.

## Executive Summary

The real-world survey (VSC03.2) confirms that TNH Scholar's VS Code integration strategy is **well-founded and aligned with proven patterns** from the VS Code ecosystem. Key findings:

1. **Protocol-first boundaries** are the canonical pattern (LSP, DAP, MCP, Jupyter)
2. **Monaco alignment** (ADR-AT03.2) follows the "zero-translation" approach used by successful systems
3. **CLI-first integration** (ADR-VSC01) matches the "thin extension host" pattern
4. **Object-service conformance** aligns with LSP's separation of domain logic from UI
5. **Type safety approach** is validated by DAP's versioned schema + change history discipline

**Conclusion**: Proceed with current design direction. Minor refinements suggested below.

---

## Validation of Key Design Decisions

### 1. Monaco Editor Alignment (ADR-AT03.2)

**Decision**: Align Python `SectionRange` with Monaco's 1-based inclusive line semantics.

**Validation from VSC03.2**:
- **LSP precedent**: "Treat domain actions as request/response tools with explicit schemas" - Monaco alignment is a schema-first decision
- **DAP precedent**: "Versioned protocol + schema + interoperability" - inclusive ranges are Monaco's published schema
- **Pattern**: "Thin extension host" - zero-translation reduces extension complexity

**Status**: ✅ **Validated**. Real-world systems prioritize protocol/schema compatibility over internal implementation preferences.

**Refinement**: Consider documenting Monaco's `IRange` interface explicitly in ADR-AT03.2 as the "authoritative schema" we align to (similar to how DAP publishes its JSON schema).

---

### 2. CLI-First Integration (ADR-VSC01)

**Decision**: Start with CLI invocation, evolve to HTTP/LSP/MCP as needed.

**Validation from VSC03.2**:
- **LSP pattern**: "Non-UI components living outside the extension host"
- **Jupyter precedent**: "VS Code acts as the 'shell' UI; Python remains authoritative for execution"
- **Thin client**: "Keep the extension host 'thin': orchestration + UX, not heavy computation"

**Status**: ✅ **Validated**. The transport evolution path (CLI → HTTP → LSP → MCP) matches how Jupyter and LSP evolved.

**Refinement**: Add explicit "transport agnostic" design principle - ensure Python models/services can work with *any* transport without modification (already implicit in object-service conformance).

---

### 3. Object-Service Conformance (ADR-AT03.2, ADR-AT03.3)

**Decision**: Position NumberedText as pure domain model, TextObject as hybrid → future service orchestrator.

**Validation from VSC03.2**:
- **LSP architecture**: "Strongly typed messages at the boundary (schema-first mindset)"
- **DAP pattern**: "Separation between VS Code UI and external runtime implementations"
- **Extractable pattern**: "Treat 'domain actions' as request/response tools with explicit schemas"

**Status**: ✅ **Validated**. Object-service separation mirrors LSP's client/server split and DAP's debugger/UI separation.

**Refinement**: Consider adopting **explicit capability negotiation** (like LSP's feature negotiation) for TextObject services - aligns with "progressive capability growth" pattern from VSC03.2.

---

### 4. Python-First Data Model Ownership (ADR-VSC03)

**Decision**: Python models are source of truth, generate TypeScript types from Pydantic.

**Validation from VSC03.2**:
- **DAP precedent**: "Machine-readable JSON schema and publishes change history"
- **Pattern**: "Versioned message protocol with forward/backward compatibility rules"
- **Jupyter**: "Python remains authoritative for execution"

**Status**: ✅ **Validated**. Python-first ownership is consistent with how Jupyter maintains kernel authority.

**Refinement**: Adopt **DAP-style change history** - track schema evolution in a dedicated changelog (e.g., `SCHEMA_CHANGELOG.md`) to support forward/backward compatibility analysis.

---

### 5. Webview Security Posture (Future - ADR-VSC01)

**Current**: Not yet formalized in TNH Scholar ADRs.

**Recommendation from VSC03.2**:
- "Treat Webview ↔ Extension messages as **untrusted inputs**"
- "Validate against schemas, reject unknown fields/versions, require explicit capability negotiation"
- "Apply strict CSP (content security policy) defaults"

**Status**: ⚠️ **Missing**. Should be formalized before implementing webview-based viewers.

**Action**: Create **ADR-VSC04: Webview Security Posture** when viewer implementation begins, incorporating Trail of Bits' security guidance from VSC03.2.

---

## Proposed Refinements to Existing ADRs

### Minor Update: ADR-AT03.2 (NumberedText)

**Add**: "Authoritative Schema Reference" section

```markdown
## Authoritative Schema Reference

NumberedText's `SectionRange` is designed for zero-translation compatibility with Monaco Editor's `IRange` interface, which serves as the authoritative schema:

**Monaco IRange** (TypeScript):
```typescript
interface IRange {
  startLineNumber: number;  // 1-based, inclusive
  endLineNumber: number;    // 1-based, inclusive
  startColumn: number;
  endColumn: number;
}
```

**TNH Scholar SectionRange** (Python):
```python
@dataclass(frozen=True)
class SectionRange:
    start_line: int  # 1-based, inclusive (maps to startLineNumber)
    end_line: int    # 1-based, inclusive (maps to endLineNumber)
```

This alignment follows the **schema-first discipline** used by DAP and LSP: external protocols define the canonical schema, internal implementations conform.
```

**Rationale**: Makes Monaco's schema authority explicit (DAP-style documentation).

---

### Minor Update: ADR-VSC03 (Impedance Investigation)

**Add**: "Validation from Real-World Survey" section (before "Timeline")

```markdown
## Validation from Real-World Survey

Initial findings from ADR-VSC03.2 (Real-World Survey) indicate the investigation direction is well-aligned with ecosystem precedents:

- **LSP/DAP**: Validate protocol-first boundaries and versioned schemas
- **Jupyter**: Validates Python-as-authority, thin TypeScript client
- **MCP**: Validates tool-based architecture with schema discovery
- **Webview security**: Identifies schema validation as security feature (not just DX)

These precedents reduce risk for the proposed investigation and suggest focusing research efforts on:
1. **DAP-style change history** for schema evolution tracking
2. **LSP-style capability negotiation** for progressive feature growth
3. **Webview security posture** formalization (separate ADR needed)
```

**Rationale**: Connects investigation to validated patterns, refines research focus.

---

### New ADR Recommended: ADR-VSC04 (Future Work)

**Title**: "ADR-VSC04: Webview Security Posture"

**Scope**: Formalize security discipline for webview-based viewers (when implemented)

**Key Requirements** (from VSC03.2):
- Treat webview messages as untrusted inputs
- Schema validation with version rejection
- Strict CSP defaults
- Capability negotiation

**Trigger**: Before implementing first webview-based viewer (e.g., parallel text viewer)

---

## Transport Evolution Path (Refined)

Based on VSC03.2 findings, refine the transport evolution strategy:

### Phase 1: CLI (Current - v0.1.0-v0.2.0)
- **Pattern**: Thin client, domain logic in Python
- **Precedent**: Jupyter kernel invocation
- **Trade-off**: Startup latency acceptable for batch workflows

### Phase 2: HTTP (v0.2.0+)
- **Pattern**: Long-running service, session management
- **Precedent**: Language servers (many use HTTP/WebSocket)
- **Trade-off**: Adds deployment complexity, improves interactivity

### Phase 3: LSP (Future - Text-Centric Features)
- **Pattern**: Standardized protocol for editor features
- **Precedent**: LSP itself (definitions, references, diagnostics)
- **Use case**: Text navigation, cross-references in TNH corpus
- **Trade-off**: LSP protocol overhead vs standardization benefits

### Phase 4: MCP (v2.0+ - AI Workflows)
- **Pattern**: Tool-based architecture with schema discovery
- **Precedent**: VS Code MCP client support
- **Use case**: AI-assisted research, provenance inspection, annotation workflows
- **Trade-off**: Requires MCP ecosystem adoption

**Key Insight from VSC03.2**: "Multiple execution modes" (desktop vs web) require transport flexibility. Design Python services to be **transport-agnostic** from the start.

---

## Schema Evolution Discipline (New Recommendation)

Adopt **DAP-style change history** for schema versioning:

### Proposed: `SCHEMA_CHANGELOG.md`

Track breaking/non-breaking changes to Python models exposed to TypeScript:

```markdown
# TNH Scholar Schema Changelog

## Version 0.2.0 (2025-01-15)

### Breaking Changes
- `SectionRange.end_line`: Changed from exclusive to **inclusive** (Monaco alignment)
  - **Migration**: TypeScript clients: no change needed (already expected inclusive)
  - **Python**: Internal `range()` calls must use `end_line + 1`

### Non-Breaking Changes
- `TextObject.merge_metadata()`: Added `source` parameter (optional, for provenance)
  - **Backward compatible**: Existing calls work without `source`

## Version 0.1.0 (2025-01-01)
- Initial schema release
```

**Rationale**: DAP's change history (VSC03.2) enables forward/backward compatibility analysis. Supports multi-version clients (web vs desktop).

---

## Web vs Desktop Constraints (Future-Proofing)

VSC03.2 identifies **web extension host constraints** as a future consideration:

**Current Design**: Desktop-first (CLI invocation, local Python)

**Future Web Considerations** (from VSC03.2):
- "If TNH Scholar wants 'web-first' access later, the boundary discipline (schema + strict messaging + capability detection) becomes *more* important, not less"
- "A Python backend may need to be remote (Codespaces, server, local companion)"

**Recommendation**: No immediate changes needed. Current schema-first + transport-agnostic design already prepares for web deployment (Python backend becomes remote HTTP service).

**Action**: When web support is prioritized, create **ADR-VSC05: Web Extension Host Strategy**.

---

## Synthesis: Patterns That Reinforce TNH Scholar Design

From VSC03.2, five patterns recur across LSP, DAP, Jupyter, MCP:

| Pattern | VSC03.2 Precedent | TNH Scholar Alignment | Status |
|---------|-------------------|----------------------|--------|
| **Protocol-first boundaries** | LSP, DAP, MCP | Monaco alignment (AT03.2), CLI-first (VSC01) | ✅ Aligned |
| **Strict versioning + change history** | DAP publishes schema changelog | *Missing* - should add `SCHEMA_CHANGELOG.md` | ⚠️ Refinement needed |
| **Thin extension host** | LSP, Jupyter | Object-service conformance (AT03.2/3.3) | ✅ Aligned |
| **Schema validation as security** | Webview messaging, DAP | *Missing* - need ADR-VSC04 for webviews | ⚠️ Future work |
| **Multiple execution modes** | Desktop vs web | Transport-agnostic design (implicit) | ✅ Aligned |

**Overall**: 3/5 patterns fully aligned, 2/5 need refinement or future formalization.

---

## Recommended Actions

### Immediate (This Sprint)
1. ✅ **No changes required** - current design is validated
2. 📝 **Optional**: Add "Authoritative Schema Reference" section to ADR-AT03.2 (minor enhancement)
3. 📝 **Optional**: Add "Validation from Real-World Survey" section to ADR-VSC03 (connects investigation to findings)

### Short-Term (v0.2.0 - v0.3.0)
1. 📋 **Create `SCHEMA_CHANGELOG.md`** - track breaking/non-breaking changes (DAP-style discipline)
2. 🔍 **Formalize capability negotiation** - add to TextObject service design (LSP-style progressive features)

### Future (When Implementing Webviews)
1. 📝 **Create ADR-VSC04: Webview Security Posture** - formalize security discipline before first webview
2. 📝 **Create ADR-VSC05: Web Extension Host Strategy** - when web support is prioritized

---

## Conclusion

The real-world survey (ADR-VSC03.2) provides strong validation for TNH Scholar's VS Code integration strategy. Key design decisions - Monaco alignment, CLI-first integration, object-service conformance, and Python-first data ownership - are **consistent with proven patterns** from LSP, DAP, Jupyter, and MCP.

**Minor refinements** (schema changelog, capability negotiation) would strengthen alignment with ecosystem best practices, but **no fundamental changes are needed**.

**Status**: Investigation (ADR-VSC03) can proceed with high confidence in the current direction.

---

## Related ADRs

- **[ADR-VSC01: VS Code Integration Strategy](/architecture/ui-ux/vs-code-integration/adr-vsc01-vscode-integration-strategy.md)** - CLI-first integration (validated)
- **[ADR-VSC03: Python-JavaScript Impedance Investigation](/architecture/ui-ux/vs-code-integration/adr-vsc03-python-javascript-impedance-investigation.md)** - Parent investigation
- **[ADR-VSC03.2: Real-World Survey Addendum](/architecture/ui-ux/vs-code-integration/adr-vsc03.2-real-world-survey-addendum.md)** - Survey findings
- **[ADR-AT03.2: NumberedText Monaco Alignment](/architecture/ai-text-processing/adr/adr-at03.2-numberedtext-validation.md)** - Monaco alignment decision (validated)
- **[ADR-AT03.3: TextObject Robustness](/architecture/ai-text-processing/adr/adr-at03.3-textobject-robustness.md)** - Object-service conformance (validated)

---

**Next Steps**: Review synthesis with stakeholders, optionally implement short-term refinements (schema changelog, capability negotiation).

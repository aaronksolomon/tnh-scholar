---
title: "ADR-VSC03: Python-JavaScript Impedance Mismatch Investigation"
description: "Decision to investigate architectural strategies for mitigating Python-JavaScript platform mismatch in VS Code integration"
type: "investigation"
owner: "UI/UX Working Group"
author: "Aaron Solomon, Claude Sonnet 4.5"
status: proposed
created: "2025-12-12"
parent_adr: "adr-vsc01-vscode-integration-strategy.md"
---

# ADR-VSC03: Python-JavaScript Impedance Mismatch Investigation

Decision to investigate architectural strategies for mitigating the Python (TNH Scholar) ↔ JavaScript (VS Code) platform mismatch in our VS Code integration strategy.

- **Status**: Proposed (Investigation)
- **Type**: Investigation ADR
- **Date**: 2025-12-12
- **Owner**: UI/UX Working Group
- **Author**: Aaron Solomon, Claude Sonnet 4.5
- **Parent ADR**: [ADR-VSC01: VS Code Integration Strategy](/architecture/ui-ux/vs-code-integration/adr-vsc01-vscode-integration-strategy.md)

---

## Context

### The Fundamental Platform Mismatch

TNH Scholar's adoption of VS Code as its UI/UX platform (per ADR-VSC01) creates a **fundamental architectural boundary**:

```text
Python Ecosystem (TNH Scholar)          JavaScript Ecosystem (VS Code)
├─ Core Logic                          ├─ Monaco Editor
├─ Data Models (Pydantic)              ├─ Extension API
├─ GenAI Service                       ├─ Webview API
├─ TextObject / NumberedText           └─ Language Server Protocol
└─ AI Text Processing
         │
         └──────── Impedance Mismatch ─────────┘
                   ↕
            How do these communicate?
```

**The Problem**: While we've designed NumberedText for Monaco compatibility (ADR-AT03.2) and planned CLI-first integration (ADR-VSC01), the **long-term sustainability** of Python ↔ JavaScript communication patterns needs investigation.

---

## Decision

**We decide to investigate** architectural strategies for mitigating the Python-JavaScript impedance mismatch, focusing on:

1. **Data Model Alignment**: How to maintain type safety across Python ↔ TypeScript boundaries
2. **Transport Evolution**: CLI → HTTP → LSP → MCP progression and trade-offs
3. **Code Generation**: Auto-generating TypeScript types from Python models (Pydantic → TS)
4. **Runtime Boundaries**: Where to draw the line between Python and JavaScript responsibilities

**This is an investigation ADR** - we're committing to research, not to a specific solution.

---

## Investigation Scope

### Key Questions

1. **Type Safety Across Boundaries**
   - Can we auto-generate TypeScript interfaces from Pydantic models?
   - Tools: `pydantic-to-typescript`, `datamodel-code-generator`, custom generators?
   - How to maintain schema versioning and compatibility?

2. **Transport Layer Evolution**
   - CLI (v0.1.0): JSON serialization, subprocess invocation
   - HTTP (v0.2.0): FastAPI service, streaming, sessions
   - LSP (future?): Language Server Protocol for text-centric features
   - MCP (v2.0+): Model Context Protocol for agent workflows
   - Which transport patterns minimize impedance for which use cases?

3. **Data Model Ownership**
   - **Python-first**: Generate TS from Pydantic (current approach per ADR-AT03.2)
   - **Schema-first**: Shared JSON Schema → generate both Python + TS
   - **Dual-native**: Maintain parallel implementations with manual sync
   - Trade-offs of each approach?

4. **Runtime Responsibility Boundaries**
   - What logic stays in Python? (AI processing, validation, business rules)
   - What logic moves to JavaScript? (UI state, Monaco integration, interactivity)
   - Where do we draw the line for performance vs maintainability?

5. **Monaco Editor Integration Depth**
   - Current approach: Align Python models with Monaco (ADR-AT03.2)
   - Alternative: Python exports raw data, JS layer handles all Monaco mapping
   - Trade-off: Coupling vs translation complexity?

### Out of Scope (For Now)

- Embedding Python in browser (Pyodide) - rejected in ADR-VSC01
- Rewriting TNH Scholar in TypeScript - not viable
- Abandoning VS Code platform - committed per ADR-VSC01

---

## Investigation Deliverables

### Phase 1: Research & Analysis (1-2 weeks)

1. **Type Generation Survey**
   - Evaluate `pydantic-to-typescript` with real TNH Scholar models
   - Test roundtrip: Python → JSON → TS deserialization
   - Assess schema evolution and versioning strategies

2. **Transport Pattern Analysis**
   - Benchmark CLI vs HTTP for realistic workloads (file size, latency)
   - Prototype LSP integration for text-centric features (definitions, references)
   - Explore MCP spec alignment with TNH Scholar's GenAI service

3. **Case Study: NumberedText / TextObject**
   - Document current approach (Monaco alignment in ADR-AT03.2)
   - Prototype alternative: Python exports generic JSON, JS maps to Monaco
   - Compare maintainability, type safety, performance

### Phase 2: Prototype & Validate (2-3 weeks)

1. **Build Walking Skeleton**
   - Python: TextObject with Pydantic model
   - Auto-generate TypeScript interface
   - VS Code extension: Deserialize + map to Monaco editor
   - Measure roundtrip reliability and developer experience

2. **Schema Evolution Test**
   - Add field to Python model (e.g., `TextObject.metadata`)
   - Re-generate TypeScript
   - Test backward compatibility in extension

### Phase 3: Recommendation (1 week)

**Write ADR-VSC04 (or update VSC03)** with findings and recommendations:

- Recommended type generation approach
- Transport layer progression path
- Data model ownership strategy
- Implementation guidelines for future integrations

---

## Known Mitigation Strategies

### Strategy 1: Pydantic → TypeScript Code Generation

**Tools**: `pydantic-to-typescript`, `datamodel-code-generator`

**Example**:
```python
# Python: text_object.py
class SectionRange(BaseModel):
    start_line: int = Field(..., description="1-based, inclusive")
    end_line: int   = Field(..., description="1-based, inclusive")

# Generated TypeScript: text_object.ts
export interface SectionRange {
  /** 1-based, inclusive */
  start_line: number;
  /** 1-based, inclusive */
  end_line: number;
}
```

**Pros**: Automatic, type-safe, single source of truth (Python)
**Cons**: Build-time dependency, schema evolution complexity

### Strategy 2: JSON Schema Intermediate

**Approach**: Python exports JSON Schema, both Python and TS validate against it

**Pros**: Language-agnostic, versioning support
**Cons**: Extra abstraction layer, schema-first development required

### Strategy 3: Monaco Alignment (Current - ADR-AT03.2)

**Approach**: Design Python models to match TypeScript interfaces (Monaco)

**Pros**: Zero translation in UI, clear mental model
**Cons**: Couples Python to UI framework (mitigated by domain model purity)

---

## Success Criteria

This investigation succeeds if we can answer:

1. **Type Safety**: Can we maintain type safety across Python → JSON → TypeScript with <5% manual intervention?
2. **Performance**: Is the chosen transport layer acceptable for realistic workloads (e.g., 100KB text file sectioning in <500ms)?
3. **Maintainability**: Can a Python developer add a field to a model without manually updating TypeScript?
4. **Future-Proof**: Does the approach support transport evolution (CLI → HTTP → MCP)?

---

## Timeline

- **Week 1-2**: Research & analysis (type generation, transport patterns)
- **Week 3-4**: Prototype & validation (walking skeleton)
- **Week 5**: Recommendation ADR (VSC04 or updated VSC03)

**Target Completion**: 2025-01-30

---

## Related Context

### Related ADRs

- **[ADR-VSC01: VS Code Integration Strategy](/architecture/ui-ux/vs-code-integration/adr-vsc01-vscode-integration-strategy.md)** - Parent decision (CLI-first integration)
- **[ADR-AT03.2: NumberedText Monaco Alignment](/architecture/ai-text-processing/adr/adr-at03.2-numberedtext-validation.md)** - Example of Python → Monaco alignment
- **[ADR-OS01: Object-Service Architecture](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md)** - Domain model principles

### Surfaced During

- ADR-AT03.2 design discussion (Monaco Editor alignment for NumberedText)
- Concern: Long-term sustainability of Python ↔ JavaScript type mapping
- Question: Should we investigate deeper integration strategies?

---

## Open Questions

1. **Should Python models directly mirror Monaco interfaces**, or should we insert a translation layer?
2. **What's the cost of maintaining dual implementations** (Python + TypeScript) for core types?
3. **Can we leverage Language Server Protocol** for richer editor features beyond basic text?
4. **How do other polyglot projects** (Jupyter, VS Code Python extension) handle this boundary?

---

## Approval Path

1. Review and approve investigation scope
2. Allocate 5 weeks for research + prototyping
3. Produce recommendation ADR (VSC04) with findings

---

**Status**: Proposed (awaiting approval to proceed with investigation)

*This investigation ensures TNH Scholar's Python-JavaScript boundary is sustainable for long-term VS Code platform adoption.*

---
title: "ADR-AT03.1: AT03→AT04 Transition Plan"
description: "Phased transition strategy: minimal refactor (AT03) for tnh-gen release, followed by comprehensive platform (AT04)"
type: "transition-strategy"
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Sonnet 4.5"
status: proposed
created: "2025-12-12"
parent_adr: "adr-at03-object-service-refactor.md"
related_adrs: ["adr-at04-ai-text-processing-platform-strat.md", "adr-tg01-cli-architecture.md"]
---

# ADR-AT03.1: AT03→AT04 Transition Plan

**Transition strategy ADR defining the phased approach from minimal refactor (AT03) to comprehensive platform (AT04)**

- **Status**: Proposed
- **Type**: Transition Strategy
- **Date**: 2025-12-12
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, Claude Sonnet 4.5
- **Parent ADR**: [ADR-AT03](/architecture/ai-text-processing/adr/adr-at03-object-service-refactor.md)
- **Related ADRs**: [ADR-AT04](/architecture/ai-text-processing/adr/adr-at04-ai-text-processing-platform-strat.md), [ADR-TG01](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md)

---

## Context

### The Problem

**tnh-gen CLI** (ADR-TG01) requires robust ai_text_processing to function, but we face a timing dilemma:

- **ADR-AT04** proposes comprehensive AI text processing platform (13-17 weeks implementation)
- **tnh-gen** is ready except for ai_text_processing dependency
- **Blocking Issue**: Making tnh-gen dependent on full AT04 creates 3-4 month release delay

### The Question

How do we unblock tnh-gen without:

1. Shipping with current brittle ai_text_processing (section boundary bugs, direct OpenAI calls)?
2. Abandoning AT04's strategic vision (context propagation, strategy catalog, validation loops)?
3. Creating throwaway work that must be rewritten for AT04?

---

## Decision

### Two-Phase Transition Strategy

Implement a **phased approach** that delivers incremental value:

**Phase 1: AT03 Minimal Refactor** → Unblock tnh-gen (1-2 weeks)
**Phase 2: AT04 Full Platform** → Comprehensive capabilities (13-17 weeks, later)

### Phase 1: ADR-AT03 - Minimal Viable Refactor (1-2 weeks)

**Document**: [ADR-AT03](/architecture/ai-text-processing/adr/adr-at03-object-service-refactor.md)

**Scope** (what we WILL implement):

- ✅ **Tier 0**: TextObject/NumberedText robustness
  - `validate_section_boundaries()` - catches gaps/overlaps/out-of-bounds
  - `get_coverage_report()` - debugging coverage statistics
  - Fixed `merge_metadata()` - correct metadata propagation

- ✅ **Tier 1**: Minimal object-service patterns
  - Simple error hierarchy (SectionBoundaryError, ProcessingError, PromptRenderError)
  - `GenAIWrapper` class to isolate GenAI Service dependency

- ✅ **Tier 2**: GenAI Service integration
  - Remove all direct OpenAI SDK calls
  - Route through GenAI Service for budget/rate limiting policies
  - Response fingerprinting for provenance tracking

- ✅ **Tier 3**: Basic prompt system adoption
  - Migrate 3-5 key prompts to catalog (translation, sectioning, summarization)
  - Use PromptsAdapter for rendering
  - Add deprecation warning to `prompts.py`

**Scope Constraint** (what we will NOT implement):

- ❌ Task Orchestration Layer (AT04 Phase 1)
- ❌ Context Propagation Graph (AT04 Phase 1)
- ❌ Strategy Catalog & Polymorphism (AT04 Phase 2)
- ❌ Validation Loops (AT04 Phase 3)
- ❌ Experimentation Harness (AT04 Phase 4)
- ❌ Cross-Document Coherence (AT04 Phase 5)

**Timeline**: 10-12 working days (4 phases × 3 days)

**Success Criteria**:

1. tnh-gen CLI functional with prompt execution
2. Section validation catches boundary errors
3. No direct OpenAI SDK calls
4. Structured errors map to tnh-gen CLI exit codes
5. Unit tests pass for validation and GenAIWrapper
6. Foundation ready for AT04

### Phase 2: ADR-AT04 - Full Platform (13-17 weeks) - LATER

**Document**: [ADR-AT04](/architecture/ai-text-processing/adr/adr-at04-ai-text-processing-platform-strat.md)

**Scope**: Comprehensive platform for:

- Context-aware processing with propagation graph
- Strategy experimentation with catalog and polymorphism
- Evaluation-driven development with experimentation harness
- Cross-document coherence with shared terminology

**Relationship to AT03**: Builds on AT03's foundation (TextObject, GenAI, Prompts)

**Timeline**: Deferred pending tnh-gen release and validation spike

---

## Why This Works

### Strategic Advantages

1. **Unblocks tnh-gen**: Release in 2 weeks instead of 4+ months
2. **No wasted work**: AT03 establishes foundation AT04 requires
3. **De-risks AT04**: Validate platform approach with working CLI first
4. **Incremental value**: Users get tnh-gen sooner, platform capabilities later
5. **Clear migration path**: AT04 proceeds without disrupting tnh-gen

### Key Insight: AT03 as Phase 0.5 of AT04

AT03 is **not a detour**—it's the prerequisite foundation:

```text
ADR-AT03 (Phase 0.5)          →  ADR-AT04 Full Platform
──────────────────────────────────────────────────────────
✅ TextObject robustness      →  Context Propagation Graph
✅ GenAI Service integration  →  Task Orchestration Layer
✅ Basic prompt adoption      →  Strategy Catalog & Polymorphism
✅ Error handling             →  Validation Loops
                              →  Experimentation Harness
                              →  Cross-Document Coherence
```

**What AT03 Provides for AT04**:

1. **TextObject Robustness** → Context Propagation can track section lineage accurately
2. **GenAI Service Integration** → Task Orchestrator calls GenAI Service (no direct OpenAI)
3. **Prompt System Adoption** → Strategy Catalog extends prompt catalog with strategy templates
4. **Error Handling** → Validation Loops use same exception hierarchy

---

## Implementation Plan

### Week 1-2: AT03 Implementation

#### Phase 1: TextObject Robustness (Days 1-3)

1. Add `validate_section_boundaries()` to `NumberedText`
2. Add `get_coverage_report()` for debugging
3. Fix `merge_metadata()` bugs in `TextObject`
4. Unit tests for validation methods
5. **Deliverable**: TextObject tests pass, section validation working

#### Phase 2: GenAI Service Integration (Days 4-6)

1. Create `GenAIWrapper` class with `render_and_execute()`
2. Add `exceptions.py` with error hierarchy
3. Create `factory.py` with `create_genai_wrapper()`
4. Update `line_translator.py` to use wrapper
5. Remove direct OpenAI imports
6. **Deliverable**: No direct OpenAI SDK calls, provenance metadata captured

#### Phase 3: Prompt Migration (Days 7-9)

1. Migrate 3-5 key prompts to catalog
2. Update processors to use prompt keys
3. Add deprecation warning to `prompts.py`
4. Test prompt rendering with PromptsAdapter
5. **Deliverable**: Key prompts loaded from catalog

#### Phase 4: Integration & Testing (Days 10-12)

1. Integration tests for full workflows (sectioning → translation)
2. Test tnh-gen CLI with refactored module
3. Verify error handling maps to CLI exit codes
4. Documentation updates (migration guide)
5. **Deliverable**: tnh-gen CLI functional with robust ai_text_processing

### Week 3+: tnh-gen Release

1. Ship tnh-gen with robust ai_text_processing
2. Gather user feedback on CLI experience
3. Plan AT04 validation spike (Phase 0 from AT04 §4)

### Months 2-6: AT04 Implementation (Optional)

**Decision Point**: After tnh-gen release, evaluate need for AT04 investment

If proceeding:

- **Phase 0**: Validation spike (1 week) - quantify cost/quality trade-offs
- **Phase 1**: Task Orchestration, Context Propagation (3-4 weeks)
- **Phase 2**: Strategy Catalog (2-3 weeks)
- **Phase 3**: Validation Loops (2 weeks)
- **Phase 4**: Experimentation Harness (2-3 weeks)
- **Phase 5**: Cross-Document Extensions (3-4 weeks)

---

## Migration Timeline

```text
NOW          +2 weeks       +3 weeks        +6 months
│               │              │               │
├─ AT03 Impl ──┤              │               │
│               ├─ tnh-gen    │               │
│               │   Release   │               │
│               │              ├─ Phase 0     │
│               │              │   Validation │
│               │              ├─ Phase 1-5  ─┤
│               │              │   (AT04)     │
│               │              │              ├─ Full Platform
                                                  Ready
```

**Key Milestones**:

- **Week 2**: AT03 complete, tnh-gen functional
- **Week 3**: tnh-gen released to users
- **Week 4**: AT04 validation spike (optional)
- **Month 6**: Full platform ready (if AT04 approved)

---

## Decision Points

### Immediate (Now)

1. ✅ **Approve AT03 refactor** as minimal viable approach
2. ⏳ **Begin implementation** (10-12 days sprint)
3. ✅ **Update AT04** with Phase 0.5 reference

### After AT03 Complete (Week 2)

1. **Release tnh-gen**: Ship CLI with robust ai_text_processing
2. **Gather feedback**: User experience with CLI
3. **Document learnings**: What worked, what needs improvement

### After tnh-gen Release (Week 3+)

1. **Evaluate AT04 need**: Is platform investment justified by usage?
2. **Run validation spike**: Quantify cost/quality trade-offs for context strategies
3. **Decide on timeline**: Proceed with full platform or defer to later

---

## Consequences

### Positive

- **Fast tnh-gen release**: 2 weeks vs 4+ months
- **Foundation for AT04**: No throwaway work—everything feeds into platform
- **Risk mitigation**: Validate approach with real CLI before large platform investment
- **User value**: tnh-gen users get functionality sooner
- **Clear path forward**: AT04 can proceed when ready without disrupting CLI

### Negative

- **Minimal abstractions**: AT03 avoids full object-service patterns (technical debt)
- **Limited capabilities**: No context propagation, strategy catalog, validation loops initially
- **Future refactor**: Some AT03 code will be enhanced (not replaced) for AT04
- **Coordination overhead**: Must track two parallel ADRs (AT03, AT04)

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **AT03 scope creep** | Delays tnh-gen release | Strict 10-12 day timeline; defer anything non-essential to AT04 |
| **AT04 never happens** | Platform vision unrealized | AT03 still provides value (robust TextObject, GenAI integration, prompts) |
| **AT03→AT04 migration pain** | Complex refactor later | AT03 builds foundation AT04 assumes; minimize breaking changes |
| **User confusion** | Two ai_text_processing "versions" | Clear documentation on AT03 as Phase 0.5; AT04 extends, not replaces |

---

## Success Criteria

This transition plan succeeds if:

1. **AT03 ships on time**: 10-12 working days
2. **tnh-gen releases**: CLI functional with robust ai_text_processing
3. **No rework needed**: AT03 foundation remains valid for AT04
4. **User satisfaction**: tnh-gen users report positive CLI experience
5. **AT04 path clear**: Validation spike runs successfully; platform approach validated
6. **Team alignment**: Clear understanding of phased approach; no confusion about goals

---

## Files Updated

This transition plan coordinates:

- ✅ [ADR-AT03](/architecture/ai-text-processing/adr/adr-at03-object-service-refactor.md) - Refactored as minimal viable implementation
- ✅ [ADR-AT04](/architecture/ai-text-processing/adr/adr-at04-ai-text-processing-platform-strat.md) - Updated "Migration from AT03" section
- ✅ This transition plan (ADR-AT03.1)

---

## Next Steps

### Immediate Actions

1. **Review & approve** ADR-AT03.1 (this doc)
2. **Plan sprint**: 10-12 day implementation schedule
3. **Assign work**: Tiers 0-3 to team members
4. **Set up tracking**: Deliverables checklist for each phase
5. **Begin Tier 0**: TextObject robustness implementation

### Follow-Up Actions (After AT03)

1. **Release tnh-gen**: Announce CLI availability
2. **Gather feedback**: User testing, bug reports
3. **Evaluate AT04**: Decision on platform investment
4. **Plan validation spike**: If proceeding with AT04

---

**Approval Path**: Architecture review → Sprint planning → Implementation → tnh-gen Release

*This transition strategy enables pragmatic tnh-gen release while preserving AT04's strategic platform vision.*

---
title: "ADR-AT04: AI Text Processing Platform Strategy"
description: "Platform architecture for extensible, evaluation-driven text processing with strategy polymorphism and context fidelity"
type: "strategy"
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Sonnet 4.5"
status: proposed
created: "2025-12-11"
updated: "2025-12-12"
---

# ADR-AT04: AI Text Processing Platform Strategy

Extensible platform architecture for evaluation-driven text processing with strategy polymorphism and context fidelity.

- **Status**: Proposed
- **Type**: Strategy ADR
- **Date**: 2025-12-11
- **Updated**: 2025-12-12
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, Claude Sonnet 4.5

## Executive Summary

This ADR establishes both the **strategic direction** and **platform architecture** for TNH Scholar's text processing capabilities. It supersedes ADR-AT03's incremental refactor approach with a platform designed for **strategy experimentation**, **context fidelity**, and **evaluation-driven development**.

### Core Thesis

*"We've proven sectioning + context translation works (JVB journals PoC). Now we need a platform that makes strategy experimentation cheap, supports multiple approaches in production, and centers prompt engineering as the primary extension mechanism."*

### Scope

**This ADR defines**:

- Strategic principles guiding platform design
- Core architectural components and their relationships
- Extension mechanisms (prompt-driven strategies)
- Integration points with existing systems (GenAI Service, Prompt System, TextObject)
- Migration path from current prototype
- Implementation phases and validation approach

**This ADR does NOT define** (deferred to decimal spin-off ADRs):

- Detailed task orchestration implementation → **ADR-AT04.1** (Task Orchestration Model)
- Context propagation algorithms and lineage tracking → **ADR-AT04.2** (Context Propagation Design)
- Strategy catalog internals and versioning → **ADR-AT04.3** (Strategy Catalog Design)
- Specific validation loop patterns → **ADR-AT04.4** (Validation Loops Design)
- Experimentation harness design → **ADR-AT04.5** (Experimentation Harness)
- Cross-document coherence implementation → **ADR-AT04.6** (Cross-Document Coherence)

---

## Context

### What We've Learned from the PoC

The current `ai_text_processing` implementation was used successfully to translate Thích Nhất Hạnh's 1950s journals (JVB project). This PoC validated core concepts but revealed critical limitations:

#### ✅ **What Worked**

1. **Sectioning for context preservation**: Breaking documents into logical sections maintained translation quality
2. **AI-driven boundary detection**: Token-based target section counts with AI-identified boundaries produced coherent sections
3. **Context windows**: Neighbor-line context (3 lines before/after) improved translation coherence
4. **Metadata propagation**: Document-level context (summaries, key concepts) proved valuable when used
5. **Prompt-driven approach**: Flexibility to adjust prompts without code changes enabled rapid iteration

#### ❌ **Pain Points Discovered**

1. **Sectioning brittleness**: AI-generated section boundaries produced off-by-one errors, missing lines, non-contiguous coverage
2. **Context fragmentation**: Document-level context (summaries, key concepts, narrative) generated but not effectively propagated to downstream tasks
3. **No validation loops**: No mechanism to verify section quality or catch translation errors before final output
4. **Limited strategy options**: Single hard-coded approach (token-based sectioning + 3-line context) - no way to try alternatives
5. **No cross-document coherence**: Multi-volume journals processed in isolation - no shared terminology or concept tracking
6. **No experimentation harness**: Cannot quantitatively compare sectioning strategies or context enrichment approaches
7. **Tight coupling**: Direct OpenAI SDK dependencies make testing and provider-switching difficult (inherited from AT03 analysis)

### Strategic Shift

**From**: Prototype with hard-coded sectioning strategy and incremental cleanup
**To**: Platform supporting multiple strategies with experimentation harness and evaluation-driven evolution

### The Hard Problems We're Solving

1. **Tight-context tasks over sectioned documents**: How do we maintain translation fidelity when processing large documents in chunks?
2. **Strategy polymorphism**: How do we support multiple sectioning/context strategies and let users/automation choose per document?
3. **Brittleness mitigation**: How do we add validation loops to catch and fix errors (section boundaries, translation quality)?
4. **Context propagation**: How do we ensure document-level context flows through entire pipeline?
5. **Cross-document coherence**: How do we maintain terminology consistency across multi-volume works?
6. **Evaluation-driven development**: How do we quantitatively compare strategies to make informed decisions?
7. **Prompt engineering as primary extension**: How do we make new strategies cheap to add (prompts, not code)?

### Why AT03's Refactor Approach Is Insufficient

ADR-AT03 proposed a three-tier refactor (object-service compliance + GenAI integration + prompt system adoption). While valuable for architectural hygiene, it:

- ✅ Addresses testability and dependency management
- ✅ Integrates modern prompt system and GenAI service
- ❌ **Doesn't address context fragmentation** - still processes segments in isolation
- ❌ **Doesn't enable strategy polymorphism** - single approach remains hard-coded
- ❌ **Doesn't provide validation loops** - brittleness persists
- ❌ **Doesn't support experimentation** - no framework for comparing strategies
- ❌ **Doesn't solve cross-document coherence** - documents still processed independently

**Conclusion**: We need a **platform architecture** that makes AT03's patterns (ports/adapters, prompt catalog, DI) serve strategy experimentation and context fidelity, not just cleaner code.

---

## Decision

### Key Definitions

To ensure clarity across follow-on ADRs (AT05-AT10), we define core terms:

- **Document**: Complete source text with metadata (e.g., journal entry, dharma talk transcript)
- **Section**: Logical subdivision of document with boundaries (start_line, implicit end_line)
- **Chunk/Span**: Portion of text processed in single operation (may be section, subsection, or fixed-token window)
- **Strategy**: Combination of (1) prompt template (from PromptCatalog), (2) configuration schema (YAML), and (3) mechanical kernel (Python code for chunking/stitching)
- **Mechanical Kernel**: Code-based operations for segmentation, indexing, overlap handling, merge logic (not LLM-driven)
- **Task**: Stateful orchestrator managing one processing stage (e.g., TranslationTask handles all section translations with retries/caching)
- **Pipeline**: Configured sequence of tasks with dependencies (e.g., Section → Validate → Translate → Assemble)
- **Context**: Accumulated information (document summaries, terminology, entity maps, lineage) flowing through pipeline

### Non-Goals & Guardrails

To prevent "architecture for architecture's sake" and scope creep:

**Non-Goals**:

- **No persistent workflow engine in Phase 1**: Tasks manage in-memory state; checkpointing deferred to Phase 2+
- **No general plugin system**: Extensions via PromptCatalog + typed schemas, not arbitrary plugin loading
- **No cross-document graph persistence in Phase 1-2**: Terminology store is simple dict + provenance, not graph database
- **No duplication of GenAIService responsibilities**: AI Text Processing focuses on document-level orchestration; provider selection, caching policies, rate limiting remain GenAIService concerns

**Guardrails**:

- **Phase 1 minimal baseline**: Tasks are pure functions with in-memory state; only two stateful features allowed: retry policy and small in-run cache
- **ContextGraph v1 is simple**: Append-only DAG stored as JSONL or in-memory object; full persistence deferred
- **Strategy components have clear homes**: Prompt template → PromptCatalog, schema → YAML config, mechanical kernel → Python module
- **Walking skeleton requirement**: By end of Phase 1, must run section → translate → assemble with deterministic chunking, one validation pass, and QA artifact output

### Architectural Principles

These seven principles guide all platform design decisions:

#### 1. **Context-First Processing**

**Principle**: Plan the context window before invoking models; avoid "fire-and-forget" per-chunk calls.

**Implication**:

- Context Planner component builds neighbor windows, pulls doc/global glossaries, sets per-chunk variables **before** task execution
- Tasks receive pre-planned context, not reactive/ad-hoc context gathering
- Context decisions are explicit, logged, and reproducible
- Example: "Section 3 translation will use: 2 neighbor sections, document glossary (15 terms), entity map (3 people)"

**Benefit**: Makes context decisions auditable and tunable. Prevents inconsistent context across chunks.

#### 2. **Strategies are Prompt-Driven with Code Kernels**

**Principle**: Strategies combine (1) prompt templates for semantic decisions, (2) configuration schemas for parameters, and (3) mechanical kernels (code) for chunking/indexing/stitching operations.

**Implication**:

- **Prompt-swappable**: Semantic logic lives in PromptCatalog templates (e.g., "identify section boundaries based on topic shifts")
- **Config-driven**: Parameters in YAML (e.g., `min_section_lines: 5`, `overlap_tokens: 50`)
- **Code kernels**: Deterministic operations remain Python (e.g., heading extraction via regex, token window splitting, overlap policy, gap detection)
- New strategy = drop in new prompt + config + (optionally) new mechanical kernel module
- Example: `heading-based` strategy uses heading extractor kernel (code) + prompt to refine boundaries (LLM)

**Rationale**: Avoids pushing brittle "string surgery" into LLM prompts. Semantic decisions are prompt-driven; mechanical operations stay in code for reliability and performance.

**Benefit**: Enables rapid semantic experimentation while maintaining deterministic mechanical foundations.

#### 3. **Task as Stateful Orchestrator Unit**

**Principle**: Tasks orchestrate multi-step operations with retries and in-run caching, maintaining state internally rather than as pure functions.

**Implication**:

- Pipeline = sequence of tasks: `Section → Validate → Translate → Validate → Assemble`
- Each task manages: chunk queueing, retry logic, result stitching
- Tasks maintain **in-memory state** during execution (e.g., TranslationTask accumulates terminology across 10 sections)
- **Phase 1 constraint**: State is ephemeral (no persistence); only retry policy and small in-run cache allowed
- **Phase 2+**: Add checkpointing for recovery, persistent state for cross-run optimization
- Users can insert validation loops, adjust context windows, swap strategies mid-pipeline

**Benefit**: Complex operations (translate 50-section document with validation) become single task invocation. State management is encapsulated, avoiding workflow engine complexity in v1.

#### 4. **Context as a Propagation Graph**

**Principle**: Every task contributes to an accumulating context graph that downstream tasks can query.

**Implication**:

- Context includes: section summaries, terminology maps, entity references, cross-document glossaries
- Tasks explicitly declare what context they consume (e.g., "I need document-level key concepts")
- Full traceability: response fingerprints + lineage tracking through entire graph
- Context persists across documents in multi-document pipelines

**Benefit**: Solves context fragmentation - downstream tasks have rich context for quality decisions.

#### 5. **Deterministic Lineage to Source**

**Principle**: Every output ties to prompt key/version, fingerprint, source section IDs, and original line ranges with diff-view support.

**Implication**:

- All outputs include: `source_section_id`, `source_line_range` (e.g., "lines 42-67"), `prompt_fingerprint`, `model_metadata`
- Assembly stage produces alignment maps: translated section → source section + line numbers
- QA workflows: side-by-side view (source lines | translated lines) with anchors
- Reproducibility: "Re-translate section 3 with same prompt version" → deterministic

**Benefit**: Enables QA workflows, debugging, reproducibility, and auditing. Translations are always traceable to source.

#### 6. **Object-Service for Strategy Polymorphism**

**Principle**: Hexagonal architecture (ports/adapters) serves strategy interchangeability, not just dependency abstraction.

**Implication**:

- `SectioningPort` protocol with multiple adapters: `HeadingBasedAdapter`, `TokenWindowAdapter`, `SemanticChunkAdapter`
- `ContextEnrichmentPort` protocol with adapters: `NeighborLinesAdapter`, `TerminologyEnrichedAdapter`
- Test harness exercises same pipeline with different adapter wiring to compare strategies
- Production code swaps adapters based on document type or user preference

**Benefit**: Strategy experimentation becomes architectural, not ad-hoc. AT03's patterns serve this higher purpose.

#### 7. **Evaluation as Built-In**

**Principle**: Every processing run captures strategy metadata and enables quantitative comparison.

**Implication**:

- Every run records: strategy used, context consumed, response fingerprints, quality metrics, cost/latency
- Comparison framework: "Run corpus through 3 sectioning strategies, generate quality report"
- Support human spot-checks, automated metrics (BLEU/COMET for translation), hallucination detection
- Evaluation harness is first-class platform component, not afterthought tooling

**Benefit**: Data-driven strategy selection replaces intuition. Platform learns what works.

#### 8. **Validation Loops for Brittleness**

**Principle**: Known failure modes (section boundary errors, translation drift) get dedicated validation prompts inserted into pipelines with explicit failure semantics.

**Implication**:

- Section validator prompt: "Check boundaries, fix off-by-one errors, ensure contiguous coverage"
- Translation spot-checker prompt: "Sample 3 passages, verify accuracy against source, flag concerns"
- Validation as optional pipeline stages configured per workflow
- **Validation Results**: `PASS | WARN | FAIL`
  - `FAIL`: Stops pipeline unless `allow_fail=true`; emits error artifact with source span references
  - `WARN`: Continues but emits QA artifact for human review
  - `PASS`: Proceeds to next task
- Each validation outputs: standardized report + references to exact source span (line ranges)

**Benefit**: Addresses PoC brittleness systematically with clear failure contracts. Quality gates prevent bad outputs while enabling human-in-loop workflows.

---

### Platform Architecture Impact

This strategy affects TNH Scholar's overall platform architecture and requires clarification of component positioning:

#### Relationship to Existing Architecture

**AT01 Pipeline Architecture**: This ADR **extends** (not replaces) AT01's pipeline model:

- **AT01 provides**: `Pipeline → ProcessState → ProcessResult` abstraction for text transformations
- **AT04 specializes**: Multi-step AI operations requiring context planning, chunking, and validation
- **Relationship**: Task Orchestrator is a specialized implementation of AT01's pipeline pattern for AI workloads

**GenAI Service Boundary** (from ADR-A13):

- **GenAI Service scope**: Single-completion execution, provider abstraction, response fingerprinting
- **Task Orchestrator scope**: Multi-call orchestration with state, context planning, result assembly
- **Integration**: Task Orchestrator is **expected client** of GenAI service for complex AI workflows

**Object-Service Patterns** (from ADR-OS01):

- **Conformance**: Task follows Service pattern (protocol + adapters), Context Planner follows Service pattern
- **Extension**: Orchestration responsibilities are new, but built on existing ports/adapters foundation
- **Blueprint alignment**: Task = Service, Strategies = Adapters, Pipeline = Processor

#### Architectural Layer Positioning

```text
┌─────────────────────────────────────────────────┐
│         Application Layer (CLI, API)            │
│             (tnh-gen, tnh-fab)                  │
└────────────────┬────────────────────────────────┘
                 │
        ┌────────▼─────────────────────────────────┐
        │    Processor Layer (Orchestration)       │
        │                                          │
        │  • Task Orchestrator (AI workflows)      │  ← NEW (AT04)
        │  • Pipeline (general transformations)   │   ← Existing (AT01)
        └────────┬─────────────────────────────────┘
                 │
        ┌────────▼─────────────────────────────────┐
        │       Service Layer                      │
        │                                          │
        │  • GenAI Service (AI execution)          │  ← Existing (A13)
        │  • Context Planner (context prep)        │  ← NEW (AT04)
        │  • Prompt Catalog (template mgmt)        │  ← Existing (PT04)
        │  • TextObject (state container)          │  ← Existing (AT01/02)
        └──────────────────────────────────────────┘
```

**Answer to Key Questions**:

1. **Orchestration Scope**: Task Orchestrator is **domain-specific** for AI text processing (translation, summarization). It is **not** a platform-wide pattern for all processing.

2. **Context Planning Scope**: Context Planner is **general capability** for AI workloads but **initially implemented** for translation. Could serve summarization, extraction in Phase 2+.

3. **Assembly/Validation Position**: Assembly/Validation is **peer component** to Task Orchestrator, operates on Task results (not inside Task execution).

4. **Evaluation Harness Nature**: Evaluation is **development tooling** (offline experimentation) that can optionally integrate as **runtime capability** (continuous quality monitoring) in Phase 4+.

#### Generalization Strategy

**Phase 1 (Current - Translation Focus)**:

- Optimize for translation: chunking, terminology, alignment
- Context Planning specialized for sectioned document translation
- Validation focused on translation accuracy/completeness

**Phase 2 (Abstraction Extraction)**:

- Identify common patterns across translation, summarization, extraction
- Extract reusable Task Orchestrator patterns (chunk → process → merge)
- Generalize Context Planning for any multi-chunk AI workflow

**Phase 3 (Platform Capability)**:

- Task Orchestrator becomes platform pattern for all multi-step AI work
- Context Planning serves all AI services
- Evaluation harness supports any AI workflow metrics

**Design Principle**: "Build concrete, extract abstractions" - no premature generalization. Translation is the proving ground; patterns emerge through use.

---

### Platform Architecture

#### Component Overview

```text
┌─────────────────────────────────────────────────────────────────────┐
│                      Processing Pipeline                            │
│   (Configurable sequence of Tasks with Strategy Selection)          │
│                                                                     │
│   Ingestion → Sectioning → Context Planner → Task Orchestrator →    │
│   GenAI + PT04 → Assembly/Validation → Outputs                      │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ orchestrates
                         ↓
         ┌───────────────┼────────────────────────────────┐
         │               │                                │
    ┌────▼─────┐   ┌────▼─────┐   ┌──────▼────────┐  ┌────▼─────────┐
    │ Section  │   │Context   │   │   Translate   │  │  Assembly/   │
    │   Task   │   │ Planner  │   │     Task      │  │  Validation  │
    └────┬─────┘   └────┬─────┘   └──────┬────────┘  └──────┬───────┘
         │              │                │                  │
         │ Uses Strategy Ports (polymorphic adapters)       │
         │              │                │                  │
         │              │ Plans context  │                  │ Stitches/aligns
         │              │ windows        │                  │ to source
         ↓              ↓                ↓                  ↓
    ┌────────────────────────────────────────────────────────┐
    │              Strategy Catalog                          │
    │      (Prompt-driven, versioned strategies)             │
    │                                                        │
    │  Sectioning:                                           │
    │    • heading-based.md (extract markdown headings)      │
    │    • token-windows.md (fixed-size chunks)              │
    │    • semantic-chunks.md (paragraph boundaries)         │
    │    • ai-identified.md (current PoC approach)           │
    │                                                        │
    │  Context Enrichment:                                   │
    │    • neighbor-lines.md (N lines before/after)          │
    │    • section-summary.md (full section + summary)       │
    │    • terminology-enriched.md (+ glossary)              │
    │    • cross-section.md (adjacent section context)       │
    │                                                        │
    │  Validation:                                           │
    │    • section-boundary-check.md (fix off-by-one)        │
    │    • translation-spot-check.md (sample passages)       │
    │    • metadata-completeness.md (required fields)        │
    └────┬───────────────────────────────────────────────────┘
         │
         │ reads from
         ↓
    ┌────────────────────────────────────────────────────┐
    │         Context Propagation Layer                  │
    │  (Accumulates metadata, tracks lineage)            │
    │                                                    │
    │  Graph nodes:                                      │
    │    • Section boundaries + metadata                 │
    │    • Document summaries + key concepts             │
    │    • Terminology maps (term → translation)         │
    │    • Entity references (people, places, concepts)  │
    │    • Response fingerprints (prompt versions)       │
    │    • Task lineage (section → translate → validate) │
    │                                                    │
    │  Cross-document extensions:                        │
    │    • Shared terminology service                    │
    │    • Multi-document concept tracking               │
    └────┬───────────────────────────────────────────────┘
         │
         │ integrates with
         ↓
    ┌────────────────────────────────────────────────────┐
    │     Integration Layer (from AT03)                  │
    │                                                    │
    │  • GenAI Service (ADR-A13): Prompt execution       │
    │  • Prompt System (ADR-PT04): Template rendering    │
    │  • TextObject (ADR-AT01/02): State container       │
    │  • Object-Service (ADR-OS01): Ports/adapters       │
    └────────────────────────────────────────────────────┘
```

#### Core Components

##### 1. Context Planner

**Purpose**: Pre-plans context windows for tasks before execution; builds neighbor windows, pulls glossaries, sets per-chunk variables.

**Responsibilities**:

- Analyze document structure and task requirements
- Determine context scope per section (e.g., "2 neighbor sections + document glossary")
- Build context packages: neighbor text, terminology maps, entity references
- Log context decisions for auditability and tuning
- Output: `ContextPlan` objects consumed by tasks

**Context Planning Strategies**:

- **Neighbor-based**: N sections before/after current section
- **Glossary-enriched**: Document or cross-document terminology injection
- **Entity-aware**: Reference resolution (people, places, concepts)
- **Adaptive**: Adjust context window based on section complexity

**Example Context Plan**:

```python
@dataclass
class ContextPlan:
    """Pre-planned context for a task."""
    section_id: str
    neighbor_sections: list[str]  # IDs of adjacent sections
    glossary_terms: dict[str, str]  # term → translation
    entity_map: dict[str, str]  # entity → description
    context_window_tokens: int  # Estimated token usage
    rationale: str  # Why this context was selected
```

**Integration**:

- Sits between Sectioning and Task Execution
- Queries Context Propagation Layer for document/global context
- Produces explicit context packages logged for reproducibility

##### 2. Task Abstraction

**Purpose**: Unit of work in processing pipeline with clear inputs, outputs, and strategy selection.

**Interface** (conceptual):

```python
class Task(Protocol):
    """Unit of work in processing pipeline."""

    def execute(
        self,
        input: TaskInput,
        strategy: Strategy,
        context: ContextGraph
    ) -> TaskResult:
        """Execute task with selected strategy and context."""
        ...

    def required_context(self) -> list[str]:
        """Declare what context this task consumes."""
        ...

    def contributed_context(self) -> list[str]:
        """Declare what context this task produces."""
        ...

@dataclass
class TaskInput:
    """Input to a task."""
    text_object: TextObject
    config: TaskConfig
    metadata: Metadata

@dataclass
class TaskResult:
    """Result from task execution."""
    text_object: TextObject  # Transformed state
    metadata: Metadata  # Metadata contributions
    fingerprint: Fingerprint  # Response provenance
    metrics: Metrics  # Quality/cost/latency
```

**Task Types** (initial set):

- `SectioningTask`: Divide text into logical sections
- `TranslationTask`: Translate text with context
- `ValidationTask`: Verify quality and fix errors
- `AssemblyTask`: Combine processed sections with alignment mapping
- `EnrichmentTask`: Add context (summaries, glossaries)

**Key Design Choices**:

- Tasks manage state internally (chunk queues, retries, accumulated terminology) but present clean interfaces
- Tasks declare context dependencies explicitly (enables validation and optimization)
- Tasks contribute to context graph (enables lineage tracking)
- Tasks are units of retry and caching

##### 3. Assembly & Validation Stage

**Purpose**: Merge processed chunks with deterministic alignment to source; verify quality and completeness.

**Responsibilities**:

- **Stitching**: Combine translated sections into final document
- **Alignment mapping**: Produce `translated_section_id → source_section_id + source_line_range` maps
- **Verification**: Check for omissions, hallucinations, boundary errors
- **QA outputs**: Generate side-by-side views (source | translation) with line anchors

**Alignment Map Structure**:

```python
@dataclass
class AlignmentMap:
    """Maps translated output to source."""
    translated_section_id: str
    source_section_id: str
    source_line_range: tuple[int, int]  # (start_line, end_line)
    prompt_fingerprint: str
    model_metadata: dict[str, Any]
    quality_metrics: dict[str, float]  # BLEU, confidence, etc.
```

**QA Workflow Support**:

- **Side-by-side view**: Source lines | Translated lines with anchors
- **Diff view**: Highlight additions, omissions, structural changes
- **Spot-check interface**: Sample passages with quality ratings
- **Reproducibility**: "Re-translate section 3 with prompt v1.2" → deterministic re-run

**Validation Strategies**:

- **Heuristic checks**: Line count variance, character ratio, structural markers
- **LLM-based checks**: Secondary prompt asking "Are there omissions or hallucinations?"
- **Human-in-loop**: Flag suspicious sections for manual review

**Integration**:

- Final stage before outputs
- Consumes all task results + context graph
- Produces final `TextObject` + alignment metadata + QA artifacts

##### 4. Strategy Catalog

**Purpose**: Registry of prompt-driven strategies with versioning and discovery.

**Structure**:

```
prompts/
  strategies/
    sectioning/
      heading-based.md          # Extract markdown/HTML headings
      token-windows.md          # Fixed-size token chunks
      semantic-chunks.md        # Paragraph/thought boundaries
      ai-identified.md          # Current PoC approach
    context/
      neighbor-lines.md         # N lines before/after
      section-summary.md        # Full section + AI summary
      terminology-enriched.md   # + accumulated glossary
      cross-section.md          # Adjacent section context
    validation/
      section-boundary-check.md # Fix off-by-one errors
      translation-spot-check.md # Sample passages for quality
      metadata-completeness.md  # Ensure required fields
```

**Strategy Prompt Format**:

```markdown
---
name: heading-based
version: 1.0
strategy_type: sectioning
description: Extract document headings and use as section boundaries
required_variables: [input_text]
optional_variables: [heading_pattern]
default_model: gpt-4
output_mode: json
response_format: section_boundaries
tags: [sectioning, structured-documents]
---

Extract all headings from the following text and identify section boundaries:

{{input_text}}

Return a JSON list of sections with start_line and title for each heading.
```

**Strategy Configuration Schema**:

```yaml
# config/strategies/heading-based.yaml
strategy: heading-based
parameters:
  heading_pattern: "^#{1,6}\\s"  # Markdown headings
  min_section_lines: 5
  max_sections: 50
```

**Strategy Component Locations** (single source of truth):

- **Prompt Template**: Lives in PromptCatalog (PT04) at `prompts/strategies/{type}/{name}.md`
- **Configuration Schema**: YAML file at `config/strategies/{name}.yaml` OR embedded in prompt frontmatter
- **Mechanical Kernel**: Python module at `src/tnh_scholar/ai_text_processing/kernels/{name}.py` (if strategy needs custom chunking/merge logic)
- **Strategy Registration**: Auto-discovery via catalog scan + explicit type annotation in prompt frontmatter

**Discovery Mechanism**:

- Strategy catalog scans `prompts/strategies/` directory
- Strategies registered by type (sectioning, context, validation) via frontmatter `strategy_type` field
- Runtime selection via configuration or heuristics

##### 3. Context Propagation Layer

**Purpose**: Accumulate and propagate context through pipeline with lineage tracking.

**Context Graph Model** (v1 - Simple):

**Phase 1 Constraint**: ContextGraph is an append-only DAG stored as in-memory object or JSONL. No graph database; no complex query engine. Cross-document context starts as single TerminologyStore (dict + provenance).

```python
@dataclass
class ContextNode:
    """Node in context propagation graph."""
    node_id: str
    node_type: str  # 'document', 'section', 'task_result'
    content: dict[str, Any]  # Flexible key-value store
    fingerprint: Fingerprint  # Response provenance
    parent_nodes: list[str]  # Lineage tracking

class ContextGraph:
    """Graph of accumulated context."""

    def add_node(self, node: ContextNode) -> None:
        """Add context node with lineage."""
        ...

    def query(self, node_type: str, **filters) -> list[ContextNode]:
        """Query context by type and filters."""
        ...

    def get_lineage(self, node_id: str) -> list[ContextNode]:
        """Get full lineage for a node."""
        ...

    def merge(self, other: ContextGraph) -> ContextGraph:
        """Merge graphs (for cross-document)."""
        ...
```

**Context Types**:

- **Document-level**: Summary, key concepts, narrative context, language
- **Section-level**: Boundaries, titles, summaries, complexity estimates
- **Terminology**: Term → translation mappings, entity references
- **Task lineage**: Which tasks produced which outputs, with fingerprints
- **Quality metrics**: Translation scores, validation results, cost/latency

**Propagation Rules**:

- Document-level context flows to all sections and tasks
- Section context flows to tasks operating on that section
- Task results contribute back to graph for downstream tasks
- Cross-document: terminology merges across document boundaries

##### 4. Pipeline Orchestration

**Purpose**: Compose tasks into workflows with dependency management and failure handling.

**Pipeline Configuration** (YAML example):

```yaml
pipeline:
  name: journal-translation
  description: Translate journal with validation

  tasks:
    - id: section
      type: SectioningTask
      strategy: ai-identified
      config:
        target_tokens: 650
        section_range: [3, 7]

    - id: validate_sections
      type: ValidationTask
      strategy: section-boundary-check
      depends_on: [section]
      config:
        fix_errors: true
        max_retries: 2

    - id: translate
      type: TranslationTask
      strategy: section-aware
      depends_on: [validate_sections]
      config:
        context_strategy: terminology-enriched
        target_language: en
        context_lines: 3

    - id: spot_check
      type: ValidationTask
      strategy: translation-spot-check
      depends_on: [translate]
      config:
        sample_size: 3
        threshold: 0.8

    - id: assemble
      type: AssemblyTask
      depends_on: [spot_check]
```

**Orchestration Features**:

- Dependency resolution (topological sort)
- Parallel execution where possible (independent tasks)
- Retry logic per task (configurable max retries)
- Failure isolation (continue or abort on task failure)
- Context propagation between tasks
- Checkpointing for recovery

##### 5. Experimentation Harness

**Purpose**: Quantitative comparison of strategies on standard corpus.

**Comparison Framework**:

```python
class Experiment:
    """Compare strategies on corpus."""

    def __init__(
        self,
        corpus: list[TextObject],
        baseline_strategy: Strategy,
        candidate_strategies: list[Strategy]
    ):
        ...

    def run(self) -> ComparisonReport:
        """Run all strategies on corpus, collect metrics."""
        ...

@dataclass
class ComparisonReport:
    """Results from strategy comparison."""
    strategies: list[str]
    metrics: dict[str, dict[str, float]]  # strategy → metric → value
    human_evaluations: dict[str, list[Rating]]
    cost_analysis: dict[str, CostBreakdown]
    recommendations: str
```

**Metrics Collected**:

- **Quality**: BLEU/COMET scores (translation), section coverage (sectioning), error rates (validation)
- **Cost**: Token usage, API calls, total cost
- **Latency**: Processing time per document, per task
- **Human evaluations**: Spot-check ratings, error annotations

**Usage**:

```python
# Compare sectioning strategies
experiment = Experiment(
    corpus=load_corpus("JVB-journals"),
    baseline_strategy="ai-identified",
    candidate_strategies=["heading-based", "semantic-chunks"]
)
report = experiment.run()
report.display()  # Show comparison table
```

##### 6. Integration Points (from AT03)

**Boundary with GenAI Service (ADR-A13)**:

AI Text Processing focuses on **document-level orchestration**; GenAIService owns **provider/execution concerns**:

- **AI Text Processing responsibilities**: Strategy selection, context planning, chunk queueing, validation orchestration
- **GenAIService responsibilities**: Provider selection (OpenAI, Anthropic, etc.), rate limiting, retry/backpressure, response caching, cost tracking, model routing
- **Integration**: All AI calls go through `GenAIService.execute()`; no direct OpenAI SDK usage
- Strategy prompts rendered via `PromptsAdapter` from PromptCatalog
- Response fingerprinting for provenance tracking handled by GenAIService

**Prompt System Integration (ADR-PT04)**:

- Strategy prompts stored in PromptCatalog (PT04)
- Template rendering with variable substitution via PromptsAdapter
- Prompt versioning and rollback support from PT04
- Introspection for strategy discovery (scan `prompts/strategies/` with PT04 catalog APIs)

**TextObject Integration (ADR-AT01/AT02)**:

- `TextObject` remains state container
- Section boundaries via implicit end_line model
- Metadata propagation via `merge_metadata()`
- Transform tracking via process history

**Object-Service Patterns (ADR-OS01)**:

- Ports: `SectioningPort`, `ContextEnrichmentPort`, `ValidationPort`
- Adapters: Strategy-specific implementations
- Dependency injection for testability
- Protocol-based contracts for flexibility

---

### Initial Strategy Set

#### Sectioning Strategies

1. **AI-Identified** (current PoC approach)
   - Token-based target section count
   - AI determines logical boundaries
   - Returns: sections with start_line + title
   - **Use case**: Unstructured documents, narrative text
   - **Known issues**: Brittleness (off-by-one errors)

2. **Heading-Based**
   - Extract markdown/HTML headings
   - Use headings as section boundaries
   - Returns: sections aligned to document structure
   - **Use case**: Structured documents with clear headings
   - **Advantage**: Deterministic, no AI errors

3. **Token-Windows**
   - Fixed-size token chunks (e.g., 500 tokens/section)
   - Ignore semantic boundaries
   - Returns: uniform sections
   - **Use case**: Cost-controlled processing, batch jobs
   - **Advantage**: Predictable cost/latency

4. **Semantic-Chunks**
   - Detect paragraph/thought boundaries
   - Section at natural break points
   - Returns: semantically coherent sections
   - **Use case**: Translation where breaking mid-thought degrades quality
   - **Advantage**: Preserves meaning units

#### Context Enrichment Strategies

1. **Neighbor-Lines** (current PoC approach)
   - N lines before/after segment (default: 3)
   - Context for AI understanding, not translation
   - **Use case**: Baseline context for all tasks
   - **Known issues**: May not capture enough context for complex passages

2. **Section-Summary**
   - Full section as context + AI-generated summary
   - Richer context than neighbor lines
   - **Use case**: Long sections where neighbor lines insufficient
   - **Tradeoff**: Higher token cost

3. **Terminology-Enriched**
   - Accumulated glossary of term → translation mappings
   - Injected as preamble: "Use these translations consistently"
   - **Use case**: Multi-document works, technical terminology
   - **Advantage**: Cross-document consistency

4. **Cross-Section**
   - Include adjacent section's final/opening paragraphs
   - Preserve narrative flow across section boundaries
   - **Use case**: Continuous narratives where sections are artificial divisions
   - **Advantage**: Reduces context loss at boundaries

#### Validation Strategies

1. **Section-Boundary-Check**
   - Verify: contiguous coverage, no overlaps, no gaps
   - Fix: off-by-one errors, missing lines
   - **Use case**: After AI-identified sectioning
   - **Fixes known PoC brittleness**

2. **Translation-Spot-Check**
   - Sample N passages (default: 3)
   - Verify accuracy against source
   - Flag: hallucinations, omissions, mistranslations
   - **Use case**: Quality gate before final output
   - **Human-in-loop**: Can request human review on flags

3. **Metadata-Completeness**
   - Ensure required fields present (title, language, date, etc.)
   - Validate format (ISO language codes, date formats)
   - **Use case**: Before archival or publication
   - **Advantage**: Catch metadata issues early

---

## Implementation Plan

### Phase 0: Early Validation Spike (1 week)

**Objective**: Validate core assumptions about chunking strategies and context policies with real data before committing to full platform implementation.

**Approach**: Time-boxed experiment on representative documents to inform architecture decisions.

**Test Corpus Selection**:

- 3-5 representative documents from TNH corpus
- Varied characteristics:
  - **Short** (< 2000 tokens): Quick validation, minimal context needed
  - **Medium** (2000-5000 tokens): Typical section-based processing
  - **Long** (5000-10000 tokens): Tests context propagation at scale
  - **Mixed structure**: Narrative text, structured documents with headings
  - **Multilingual**: Vietnamese → English (primary use case)

**Experiment Matrix**:

| Dimension | Options to Test |
|-----------|----------------|
| **Chunking Strategy** | (1) Token-windows (300 tokens), (2) Heading-aware, (3) AI-identified sections |
| **Context Policy** | (1) ±1 neighbor section, (2) ±2 neighbor sections, (3) + document glossary |
| **Prompt Variants** | (1) Current prompt, (2) Context-enriched prompt (via PT04) |

**Metrics to Collect**:

- **Quality**:
  - Human spot-checks (5 passages per document): Accuracy, fluency, terminology consistency
  - Automated (if feasible): BLEU/COMET scores against reference translations
  - Omission/hallucination detection: Heuristic checks (line count, structure)

- **Cost**: Token usage per document, API call count, total cost

- **Latency**: Processing time per document (wall-clock), per-section average

- **Brittleness**: Section boundary errors, retry counts, validation failures

**Deliverables**:

1. **Comparison Report**: Strategy performance matrix with recommendations
2. **Default Configuration**: Chunking + context policy based on quality/cost tradeoff
3. **Identified Issues**: Edge cases, failure modes requiring architectural support
4. **Go/No-Go Decision**: Does platform approach address real needs, or pivot required?

**Success Criteria**:

- ✅ At least one strategy combination shows measurable improvement over current baseline
- ✅ Human evaluations prefer context-enriched over minimal context
- ✅ Cost increase (if any) is justified by quality improvement
- ✅ Platform architecture can support winning strategies

**Timeline**: 1 week (Day 1-2: Setup, Day 3-4: Run experiments, Day 5: Analysis + report)

**Experiment Harness v0 Specification**:

To ensure reproducibility and clear comparison:

**Run Manifest** (JSON per experiment run):

```json
{
  "run_id": "heading-based-v1-2025-12-11",
  "corpus": "JVB-journals-sample",
  "strategy": "heading-based",
  "prompt_fingerprints": {
    "sectioning": "sha256:abc123...",
    "translation": "sha256:def456..."
  },
  "model": "gpt-4",
  "chunk_policy": {"min_section_lines": 5, "max_sections": 20},
  "cost_usd": 2.47,
  "latency_seconds": 145,
  "timestamp": "2025-12-11T10:30:00Z"
}
```

**Outputs Folder Layout**:

```
experiments/
  run_id/
    manifest.json           # Run configuration + metadata
    outputs/
      doc1_translated.txt   # Translated documents
      doc1_alignment.json   # Source → translation alignment
    qa/
      doc1_spot_checks.csv  # Human evaluation template
    metrics/
      quality.json          # BLEU/COMET scores
      cost.json             # Token usage breakdown
```

**Human Scoring Template** (CSV format):

```csv
document_id,passage_id,source_lines,translated_lines,accuracy_1-5,fluency_1-5,terminology_consistent_y/n,notes
doc1,passage1,"42-45","38-41",4,5,y,"Minor terminology drift in line 44"
```

**Phase 0 Outcome Gates Phase 1**: Only proceed with full platform implementation if validation spike confirms value.

---

### Phase 1: Core Platform (3-4 weeks)

**Objective**: Build foundational components without full strategy catalog.

**Deliverables**:

1. **Task Abstraction**
   - `Task` protocol and base implementation
   - `TaskInput`, `TaskResult`, `TaskConfig` models
   - `SectioningTask`, `TranslationTask`, `ValidationTask` skeletons

2. **Context Propagation Layer**
   - `ContextGraph` and `ContextNode` implementation
   - Query interface for context retrieval
   - Lineage tracking with fingerprints

3. **Pipeline Orchestration**
   - YAML pipeline configuration parser
   - Dependency resolution (topological sort)
   - Task execution engine with retry logic

4. **Object-Service Patterns** (from AT03)
   - `SectioningPort`, `ContextEnrichmentPort`, `ValidationPort` protocols
   - Adapter base classes
   - Dependency injection container

**Testing**:

- Unit tests for all components (80%+ coverage)
- Integration test: Simple pipeline (section → translate → assemble)
- Use existing PoC approach as first adapter implementation

**Success Criteria**:

- Can run existing PoC workflow through new platform
- Context propagates correctly through pipeline
- Lineage tracking captures all transformations

**Walking Skeleton Requirement** (must demo by end of Phase 1):

Run `section → translate → assemble` pipeline on 1 document with:

- Deterministic chunking policy (one strategy fully implemented)
- One validation pass (coverage/gap detection)
- QA artifact output: alignment map (section_id → source_lines) + validation report

This "vertical slice" proves the platform architecture works end-to-end before expanding strategy catalog.

### Phase 2: Strategy Catalog & Migration (2-3 weeks)

**Objective**: Migrate existing approach to prompt-driven strategy, add alternatives.

**Deliverables**:

1. **Strategy Catalog Structure**
   - Directory layout: `prompts/strategies/{type}/{name}.md`
   - Strategy prompt format (frontmatter + template)
   - Configuration schema (YAML per strategy)

2. **Strategy Migration**
   - Convert current sectioning to `ai-identified.md` strategy
   - Convert current translation to `neighbor-lines.md` context strategy
   - Implement `section-boundary-check.md` validation strategy

3. **New Strategies**
   - `heading-based.md` sectioning (deterministic extraction)
   - `token-windows.md` sectioning (fixed-size chunks)
   - `terminology-enriched.md` context (accumulated glossary)

4. **Strategy Selection**
   - Runtime strategy loading from catalog
   - Configuration-based selection (YAML pipeline config)
   - Adapter factory (strategy name → adapter instance)

**Testing**:

- Test each strategy independently on sample documents
- Verify catalog discovery and loading
- Validate strategy swapping without code changes

**Success Criteria**:

- Can run JVB corpus through 3 sectioning strategies
- Strategies load from catalog, not hard-coded
- Configuration-driven strategy selection works

### Phase 3: Validation Loops & Brittleness Fixes (2 weeks)

**Objective**: Address known PoC brittleness with validation tasks.

**Deliverables**:

1. **Section Boundary Validator**
   - Prompt: `section-boundary-check.md`
   - Logic: Detect gaps, overlaps, off-by-one errors
   - Repair: Automatically fix common errors or flag for review

2. **Translation Spot-Checker**
   - Prompt: `translation-spot-check.md`
   - Logic: Sample passages, verify against source
   - Reporting: Confidence scores, flagged concerns

3. **Pipeline Integration**
   - Insert validators into existing pipelines
   - Retry logic: Re-run sectioning on boundary errors
   - Human-in-loop: Flag for review on quality concerns

**Testing**:

- Run validators on known-bad PoC outputs (off-by-one errors)
- Verify automated fixes resolve common issues
- Test retry logic with intentionally bad sectioning

**Success Criteria**:

- Section boundary errors reduced by 90%+
- Translation spot-checker catches known hallucinations
- Pipelines with validation produce higher quality outputs

### Phase 4: Experimentation Harness (2-3 weeks)

**Objective**: Enable quantitative strategy comparison.

**Deliverables**:

1. **Experiment Framework**
   - `Experiment` class for strategy comparison
   - `ComparisonReport` with metrics, costs, recommendations
   - Corpus management (load, partition, sample)

2. **Metrics Collection**
   - Quality: BLEU/COMET for translation, coverage for sectioning
   - Cost: Token counts, API call counts, total spend
   - Latency: Processing time per document, per task

3. **Reporting**
   - Comparison tables (strategy → metric → value)
   - Visualization (charts for quality vs. cost tradeoffs)
   - Recommendations (best strategy per document type)

4. **Initial Comparison Study**
   - Run JVB corpus through 3 sectioning strategies
   - Collect metrics, human evaluations (spot-checks)
   - Document findings in comparison report

**Testing**:

- Verify metrics collection accuracy
- Test experiment runner on small corpus
- Validate report generation and visualization

**Success Criteria**:

- Can compare strategies on 50+ document corpus
- Metrics match manual calculations (spot-check)
- Report clearly identifies best strategy per use case

### Phase 5: Cross-Document Extensions (3-4 weeks)

**Objective**: Enable multi-document processing with shared context.

**Deliverables**:

1. **Terminology Service**
   - Accumulate term → translation mappings across documents
   - Query interface: "Get translation for term in context"
   - Persistence: Save/load terminology databases

2. **Document Relationship Model**
   - Represent document collections (multi-volume works, series)
   - Ordering: Sequential processing for narrative continuity
   - Shared context: Collections share terminology, style constraints

3. **Multi-Document Pipelines**
   - Process documents sequentially, accumulating context
   - Context merging: Combine terminology from volumes 1-N
   - Lineage: Track cross-document dependencies

4. **JVB Multi-Volume Test**
   - Process all journal volumes with shared terminology
   - Measure terminology consistency across volumes
   - Compare to single-document processing (baseline)

**Testing**:

- Unit tests for terminology service
- Integration test: 3-volume series with shared terms
- Verify cross-document lineage tracking

**Success Criteria**:

- Terminology consistent across multi-volume works
- Processing N volumes accumulates context correctly
- Cross-document lineage tracks dependencies

---

## Strategic Trade-offs

This architecture makes explicit trade-offs that favor accuracy and maintainability over simplicity:

### 1. **Complexity vs. Accuracy**

**Trade-off**: Adds architectural layers (Context Planner, Task Orchestrator, Assembly/Validation) increasing surface area.

**Justification**: Accuracy bottlenecks (drift, coherence gaps, brittleness) require structured orchestration. PoC demonstrated that single-pass processing cannot maintain quality at scale.

**Mitigation**: Guardrails constrain Phase 1 complexity (in-memory state, simple Context Graph). Walking skeleton proves value before expansion.

### 2. **Flexibility vs. Performance**

**Trade-off**: Context enrichment (neighbor windows, glossaries) increases token usage → higher latency and cost. Evaluation-driven development means more experimental runs → slower initial feature delivery.

**Justification**: TNH Scholar's mission prioritizes translation fidelity over speed. Evaluation data guides optimization (e.g., "2-section context sufficient, not 3").

**Mitigation**: Phase 0 spike quantifies cost/quality trade-offs before committing. Caching and adaptive context policies reduce steady-state overhead.

### 3. **Domain Specificity vs. Generality**

**Trade-off**: Components (Context Planner, Assembly) initially optimized for translation, not general AI workflows.

**Justification**: "Build concrete, extract abstractions" - translation is complex enough to prove patterns. Premature generalization risks over-engineering.

**Mitigation**: Abstraction points identified (Task protocol, Strategy ports) enable future generalization. Phase 2+ extracts patterns for summarization, extraction.

### 4. **Evaluation Cost vs. Confidence**

**Trade-off**: Experiment harness, metrics collection, human evaluations require upfront investment before feature delivery.

**Justification**: Without evaluation, cannot distinguish effective strategies from ineffective ones. Risk of building wrong thing is higher cost than validation delay.

**Mitigation**: Phase 0 spike time-boxed to 1 week. Reusable harness amortizes cost across all future strategy experiments.

## Reliability Philosophy

TNH Scholar favors **best-effort with traceability** for long-running multi-chunk tasks:

- **Partial failures**: Tasks continue processing remaining chunks; emit warning artifacts for failed chunks
- **Validation failures**: `WARN` allows pipeline to continue with flagged output; `FAIL` stops pipeline but preserves intermediate state
- **Recovery model**: Checkpoint after each major stage (sectioning, translation, assembly); failed tasks can resume from last checkpoint (Phase 2+)
- **Partial results**: Acceptable for delivery **with clear provenance** (which chunks succeeded, which failed, why)

**Rationale**: For scholarly work, transparency about limitations is more valuable than failing silently or hiding partial outputs.

## Consequences

### Positive

1. **Strategy Experimentation is Cheap**
   - New strategy = prompt + config, no code changes
   - A/B testing built-in via experimentation harness
   - User-driven customization (select strategy per document)

2. **Brittleness Addressed Systematically**
   - Validation loops catch known errors (section boundaries, translation drift)
   - Automated fixes for common issues
   - Quality gates prevent bad outputs

3. **Context Fidelity Guaranteed**
   - Context graph ensures document-level context flows through pipeline
   - Terminology enrichment enables cross-document consistency
   - Lineage tracking provides full provenance

4. **Evaluation-Driven Development**
   - Quantitative metrics inform strategy selection
   - Comparison framework enables data-driven decisions
   - Human evaluations complement automated metrics

5. **Extensible via Prompt Engineering**
   - Prompt system is primary extension mechanism
   - Non-engineers can contribute strategies
   - Rapid iteration on new approaches

6. **Object-Service Patterns Serve Higher Purpose**
   - Ports/adapters enable strategy polymorphism, not just testability
   - Dependency injection supports experimentation harness
   - Protocol contracts enable comparison framework

7. **Cross-Document Coherence Enabled**
   - Shared terminology across multi-volume works
   - Document relationship model for collections
   - Context accumulation across processing runs

### Negative

1. **Increased Abstraction Complexity**
   - More layers (tasks, strategies, context graph, pipeline orchestration)
   - Steeper learning curve for new contributors
   - Debugging harder (more indirection)

2. **Strategy Catalog Requires Governance**
   - Need versioning strategy for prompts
   - Deprecation policy for obsolete strategies
   - Quality control (not all contributed strategies may work)

3. **Orchestration Overhead**
   - Pipeline configuration adds conceptual complexity
   - Runtime overhead (task scheduling, context propagation)
   - May need profiling and optimization

4. **Experimentation Harness Maintenance**
   - Metrics calculation requires ongoing validation
   - Corpus management (storage, versioning, partitioning)
   - Comparison reports need maintenance as metrics evolve

5. **Cross-Document State Management**
   - Terminology service needs persistence strategy
   - Multi-document processing increases memory footprint
   - Concurrency challenges (parallel document processing)

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Over-engineering**: Too much abstraction for unclear benefit | High | Start with 3 strategies, prove value before expanding. Phase 1-2 validate core concepts. |
| **Performance degradation**: Orchestration overhead slows processing | Medium | Profile each phase, optimize hot paths. Context propagation uses lazy evaluation. |
| **Prompt catalog sprawl**: Too many strategies, unclear which to use | Medium | Strategy versioning, deprecation policy. Experimentation harness recommends best strategy. |
| **Strategy quality variance**: User-contributed strategies may not work | Medium | Validation suite for new strategies. Peer review process. Mark strategies as experimental. |
| **Metrics accuracy**: Automated quality metrics may not correlate with human judgment | High | Combine automated metrics with human evaluations. Calibrate metrics against human ratings. |
| **Cross-document complexity**: Multi-document processing introduces hard-to-debug issues | Medium | Strong lineage tracking. Checkpoint between documents. Incremental rollout (single-doc first). |

---

## Open Questions

### 1. Strategy Selection Heuristics

**Question**: Should strategy selection be auto-detected, user-specified, or heuristic-based?

**Options**:

- **Auto-detect**: Analyze document structure, choose best strategy (e.g., headings present → use heading-based)
- **User-specified**: User picks strategy via configuration
- **Heuristics**: Rules like "use heading-based for Markdown, ai-identified for plain text"

**Implications**: Auto-detect requires reliable document analysis. Heuristics may miss edge cases. User-specified requires user knowledge.

**Decision needed by**: Phase 2 (strategy catalog)

### 2. Validation Loop Behavior

**Question**: Should validation loops always run, opt-in per pipeline, or triggered by confidence scores?

**Options**:

- **Always run**: Every pipeline includes validation (higher quality, higher cost)
- **Opt-in**: User configures validation tasks in pipeline (flexibility)
- **Confidence-triggered**: Run validation only if AI response has low confidence (adaptive)

**Implications**: Always-run increases cost. Opt-in may lead to skipped validation. Confidence-triggered requires reliable confidence scoring.

**Decision needed by**: Phase 3 (validation loops)

### 3. Context Propagation Strategy

**Question**: Should context be eagerly accumulated (all context to all tasks) or lazily queried (tasks request what they need)?

**Options**:

- **Eager**: Every task gets full context graph (simple, high memory)
- **Lazy**: Tasks query context graph for specific nodes (complex, low memory)

**Implications**: Eager is simpler but may overwhelm token limits. Lazy requires explicit context declarations.

**Decision needed by**: Phase 1 (context propagation layer)

### 4. Cross-Document Terminology Service

**Question**: Single terminology service for all documents or per-collection?

**Options**:

- **Single service**: Global terminology database (may have conflicts across domains)
- **Per-collection**: Each document collection has own terminology (isolation, duplication)

**Implications**: Single service simpler but may conflate terms across unrelated works. Per-collection isolates but duplicates common terms.

**Decision needed by**: Phase 5 (cross-document extensions)

### 5. Quality Metrics

**Question**: Which quality metrics are practical to compute automatically, and how do they correlate with human judgment?

**Options**:

- **Translation**: BLEU, COMET, chrF (established but imperfect)
- **Sectioning**: Coverage %, boundary accuracy (easy to compute)
- **Human evaluations**: Spot-checks, ratings (accurate but expensive)

**Implications**: Need to calibrate automated metrics against human ratings. May need to develop domain-specific metrics.

**Decision needed by**: Phase 4 (experimentation harness)

### 6. Pipeline Composition Limits

**Question**: Should pipelines have structure constraints (e.g., "validation must follow sectioning") or allow arbitrary composition?

**Options**:

- **Constrained**: Enforce sensible orderings (e.g., can't translate before sectioning)
- **Free-form**: Allow any task sequence, fail at runtime if invalid

**Implications**: Constraints prevent errors but limit flexibility. Free-form enables experimentation but may produce confusing failures.

**Decision needed by**: Phase 1 (pipeline orchestration)

### 7. Minimum Context Window Requirements

**Question**: What minimum context window is required per task (translation vs. summarization) before latency/cost becomes prohibitive?

**Options**:

- **Translation**: Test ±1, ±2, ±3 neighbor sections + document glossary
- **Summarization**: Full section vs. section + neighbors
- **Adaptive**: Adjust based on section complexity scoring

**Implications**: Larger context improves quality but increases cost and latency. Need empirical data from Phase 0 validation spike.

**Decision needed by**: Phase 0 (validation spike will inform)

### 8. Response Validation Methods

**Question**: Which response validation methods are sufficient (heuristic vs. secondary LLM check) for omissions/hallucinations on long texts?

**Options**:

- **Heuristic only**: Line count, character ratio, structural markers (fast, cheap, limited accuracy)
- **Secondary LLM**: "Review this translation for omissions/hallucinations" (slower, expensive, higher accuracy)
- **Hybrid**: Heuristics for filtering, LLM for flagged cases

**Implications**: Secondary LLM doubles cost but may catch critical errors. Heuristics may have false positives/negatives.

**Decision needed by**: Phase 3 (validation loops)

### 9. QA Output Formats as Product Surface

**Question**: Do we need document-level alignment outputs (e.g., bilingual side-by-side with anchors) as a first-class product surface, or is this internal tooling?

**Options**:

- **Product feature**: Bilingual outputs with line anchors, diff views, spot-check interfaces for end users
- **Internal tooling**: QA artifacts for developers/editors only
- **Phased approach**: Internal first, productize if valuable

**Implications**: Product feature requires UX design, persistence, API endpoints. Internal tooling is faster to build but limits user workflows.

**Decision needed by**: Phase 3 (Assembly/Validation implementation) - Informs interface design

### 10. Caching Strategy Granularity

**Question**: How aggressively should we cache per-section vs. per-task, given prompt fingerprint changes?

**Options**:

- **Section-level**: Cache section translation with fingerprint key (fine-grained invalidation)
- **Task-level**: Cache entire task output (coarse-grained, less reusable)
- **Prompt-aware**: Cache invalidates only when prompt version changes

**Implications**: Section-level caching maximizes reuse but complex cache management. Task-level simpler but less efficient.

**Caching Tier Clarification**:

- **Phase 1**: Task-level ephemeral cache (in-memory, cleared after pipeline completes)
- **Phase 2+**: Infrastructure-level persistent cache (Redis/similar, shared across runs)
- **Responsibility split**: GenAI Service handles response caching (provider-level); Task Orchestrator handles result caching (section-level)

**Decision needed by**: Phase 2 (GenAI integration with caching)

### 11. Cross-Document Coordination Scope

**Question**: What are the temporal and scope boundaries of cross-document coordination?

**Options**:

- **Per-batch**: Shared glossary within single Task execution (batch of docs processed together)
- **Per-session**: Glossary persists across user's processing session (multiple task runs)
- **Project-level**: Persistent terminology database shared across all users/sessions

**Implications**: Each scope requires different architectural support (in-memory, file system, database).

**Phase 1 Decision**: Per-batch coordination (in-memory TerminologyStore cleared after Task completes)

**Phase 5 Evolution**: Project-level persistent glossary (database-backed) for scholarly collections

**Decision needed by**: Phase 5 (cross-document extensions)

---

## Migration from AT03

### Phased Approach: AT03 → AT04

**UPDATE 2025-12-12**: AT03 has been refactored as a **minimal viable implementation** to unblock tnh-gen CLI release (1-2 weeks). AT04 will build on this foundation.

### Phase 0.5: AT03 Minimal Refactor (1-2 weeks) - **CURRENT**

**Scope** (see [ADR-AT03](/architecture/ai-text-processing/adr/adr-at03-object-service-refactor.md)):

- ✅ **TextObject Robustness**: Section boundary validation, metadata merging fixes
- ✅ **GenAI Service Integration**: Remove direct OpenAI calls, add provenance tracking
- ✅ **Basic Prompt Adoption**: Migrate key prompts to catalog, use PromptsAdapter
- ✅ **Error Handling**: Structured exceptions for tnh-gen CLI exit codes

**Deliverable**: tnh-gen CLI functional with robust ai_text_processing

**NOT Included** (deferred to AT04):

- ❌ Task Orchestration Layer
- ❌ Context Propagation Graph
- ❌ Strategy Catalog & Polymorphism
- ❌ Validation Loops
- ❌ Experimentation Harness

### Phase 0: Early Validation Spike (1 week) - AFTER AT03

Run Phase 0 validation spike (from AT04 §4) to quantify cost/quality trade-offs for context strategies before committing to full platform.

### Phase 1-5: Full AT04 Platform (11-16 weeks) - AFTER VALIDATION

Implement full platform architecture as described in this ADR:

1. **Phase 1**: Task Orchestration, Context Propagation (3-4 weeks)
2. **Phase 2**: Strategy Catalog (2-3 weeks)
3. **Phase 3**: Validation Loops (2 weeks)
4. **Phase 4**: Experimentation Harness (2-3 weeks)
5. **Phase 5**: Cross-Document Extensions (3-4 weeks)

### What AT03 Provides for AT04

AT03 establishes the **foundation** AT04 builds upon:

1. **TextObject Robustness** → Enables Context Propagation to track section lineage accurately
2. **GenAI Service Integration** → Task Orchestrator calls GenAI Service (no direct OpenAI)
3. **Prompt System Adoption** → Strategy Catalog extends prompt catalog with strategy templates
4. **Error Handling** → Validation Loops use same exception hierarchy

**Key Insight**: AT03's work is **not throwaway**—it's the prerequisite infrastructure AT04 assumes exists.

### Migration Timeline

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

**Result**: tnh-gen releases quickly (2 weeks), AT04 platform proceeds without blocking the CLI.

---

## Decimal Spin-Off ADRs (Design Details)

This strategy ADR establishes direction and platform architecture. Detailed design decisions will be captured in decimal spin-off ADRs using the naming convention **ADR-AT04.N**:

### ADR-AT04.1: Task Orchestration Model

**Type**: `design-detail`

**Purpose**: Detailed task interface, pipeline composition rules, configuration schema, dependency resolution, retry logic, failure handling.

**Dependencies**: AT04 accepted

**Timeline**: Week 1-2 of Phase 1

**File**: `adr-at04.1-task-orchestration.md`

### ADR-AT04.2: Context Propagation Design

**Type**: `design-detail`

**Purpose**: Context graph model, query interface, lineage tracking, fingerprinting, metadata merging, cross-document context.

**Dependencies**: AT04 accepted, Phase 1 complete

**Timeline**: Week 2-3 of Phase 1

**File**: `adr-at04.2-context-propagation.md`

### ADR-AT04.3: Strategy Catalog Design

**Type**: `design-detail`

**Purpose**: Prompt structure, versioning, discovery mechanism, selection heuristics, deprecation policy, contribution process.

**Dependencies**: AT04 accepted, Phase 1 complete

**Timeline**: Week 1 of Phase 2

**File**: `adr-at04.3-strategy-catalog.md`

### ADR-AT04.4: Validation Loops Design

**Type**: `design-detail`

**Purpose**: Where to insert validation, configuration schema, failure modes, retry strategies, human-in-loop integration.

**Dependencies**: AT04 accepted, Phase 2 complete

**Timeline**: Phase 3

**File**: `adr-at04.4-validation-loops.md`

### ADR-AT04.5: Experimentation Harness

**Type**: `design-detail`

**Purpose**: Comparison framework design, metrics collection, corpus management, reporting, visualization.

**Dependencies**: AT04 accepted, Phase 3 complete

**Timeline**: Phase 4

**File**: `adr-at04.5-experimentation-harness.md`

### ADR-AT04.6: Cross-Document Coherence

**Type**: `design-detail`

**Purpose**: Terminology service design, document relationship model, multi-document pipelines, context merging, lineage across documents.

**Dependencies**: AT04 accepted, Phase 4 complete

**Timeline**: Phase 5

**File**: `adr-at04.6-cross-document-coherence.md`

**Note**: Each decimal ADR will include `parent_adr: "adr-at04-ai-text-processing-platform-strat.md"` and `type: "design-detail"` in its frontmatter.

---

## References

### Related ADRs

- **[ADR-AT03: Minimal AI Text Processing Refactor](/architecture/ai-text-processing/adr/adr-at03-object-service-refactor.md)** - Minimal refactor for tnh-gen (Phase 0.5)
- **[ADR-AT03.1: AT03→AT04 Transition Plan](/architecture/ai-text-processing/adr/adr-at03.1-transition-plan.md)** - Phased transition strategy
- **[ADR-AT01: AI Text Processing Pipeline](/architecture/ai-text-processing/adr/adr-at01-ai-text-processing.md)** - Original pipeline design, metadata strategy
- **[ADR-AT02: TextObject Architecture](/architecture/ai-text-processing/adr/adr-at02-sectioning-textobject.md)** - TextObject design evolution, section boundaries
- **[ADR-A13: GenAI Service](/architecture/gen-ai-service/adr/adr-a13-migrate-openai-to-genaiservice.md)** - GenAI service integration
- **[ADR-PT04: Prompt System Refactor](/architecture/prompt-system/adr/adr-pt04-prompt-system-refactor.md)** - Prompt system architecture
- **[ADR-OS01: Object-Service Architecture V3](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md)** - Object-service patterns foundation

### External Resources

- [Hexagonal Architecture (Ports & Adapters)](https://alistair.cockburn.us/hexagonal-architecture/) - Foundation for strategy polymorphism
- [Strategy Pattern](https://refactoring.guru/design-patterns/strategy) - Behavioral pattern for algorithm interchangeability
- [Pipeline Pattern](https://java-design-patterns.com/patterns/pipeline/) - Compositional processing flows
- [BLEU Metric](https://en.wikipedia.org/wiki/BLEU) - Automatic translation quality evaluation
- [COMET Metric](https://github.com/Unbabel/COMET) - Neural translation quality estimation

### TNH Scholar Context

This ADR serves TNH Scholar's mission to preserve and translate Thích Nhất Hạnh's teachings with fidelity and accessibility. The platform architecture enables:

1. **High-fidelity translation** via context-aware processing
2. **Multi-volume works** (journals, lecture series) with terminology consistency
3. **Evaluation-driven quality** ensuring translations honor original meaning
4. **Extensibility** for future document types and languages
5. **Experimentation** to continuously improve processing strategies

---

## Approval & Next Steps

### Approval Process

1. **Review Period**: 1 week for stakeholder feedback
2. **Concerns**: Document open questions and risks
3. **Acceptance**: Move status from `proposed` → `accepted`

### Immediate Next Steps (on acceptance)

1. **Begin Phase 1**: Core platform implementation (3-4 weeks)
2. **Draft ADR-AT04.1**: Task orchestration model (parallel with Phase 1 implementation)
3. **Draft ADR-AT04.2**: Context propagation design (Week 2-3 of Phase 1)

### Success Criteria for AT04

This strategy ADR is successful if it achieves:

#### **1. Accuracy Improvement** (measurable)

- Translation quality improves on evaluation corpus (Phase 0 validates)
- Human evaluations prefer context-enriched strategies over baseline
- Section boundary errors reduced by 90%+ (validation loops)
- Cross-document terminology consistency demonstrable in multi-volume works

#### **2. Maintainability** (qualitative)

- Can swap providers (OpenAI → Anthropic) without changing orchestration logic
- Can experiment with new prompts (PT04 catalog) without code changes
- Can add new chunking strategies (heading-based, semantic) in days, not weeks
- Validation loops can be inserted/removed via configuration

#### **3. Traceability** (verifiable)

- Every output includes: source_section_id, source_line_range, prompt_fingerprint, model_metadata
- Alignment maps enable side-by-side QA views (source | translation)
- "Re-translate section 3 with prompt v1.2" produces deterministic results
- Lineage tracking answers: "Which prompt version produced this translation?"

#### **4. Extensibility** (demonstrated)

- Architecture supports summarization, extraction tasks with minimal refactoring (Phase 2+ proves this)
- Context Planning generalizes to non-translation AI workflows
- Task Orchestrator patterns apply beyond text processing
- Evaluation harness supports new metrics/strategies without core changes

#### **5. Performance** (acceptable bounds)

- Latency per document: < 2x baseline for context-enriched processing
- Cost per document: < 1.5x baseline (context overhead justified by quality improvement)
- Phase 0 spike quantifies exact trade-offs before committing

#### **6. Team Alignment** (organizational)

- Team aligns on platform approach over incremental refactor
- Implementation phases are clear and achievable
- Follow-on design ADRs (AT05-AT10) have clear scope boundaries
- Risks and open questions are understood and acceptable

---

*This ADR establishes the strategic foundation for TNH Scholar's text processing platform, enabling extensible, evaluation-driven development of high-fidelity translation and document processing capabilities.*

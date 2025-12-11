---
title: "Conceptual Architecture of TNH-Scholar"
description: "High-level, implementation-agnostic view of TNH-Scholar’s layers, abstractions, and how they interact."
owner: "Architecture"
author: "Aaron Solomon"
status: draft
created: "2025-12-11"
updated: "2025-12-11"
---
# Conceptual Architecture of TNH-Scholar

High-level, implementation-agnostic overview of TNH-Scholar’s conceptual layers, core entities, and how the system’s abstractions relate.

## 1. Conceptual Layers

At a high level, TNH-Scholar can be seen as four interacting layers:

1. **Corpus Layer**
   - Raw scans, OCR output, EPUBs, text files.
   - Cleaned and structured texts with metadata.
   - Versioned, annotated, multi-lingual corpora.

2. **Processing & Enrichment Layer**
   - Text parsing, cleaning, sectioning.
   - Metadata extraction and tagging.
   - Alignment (cross-language, cross-version, cross-corpus).

3. **GenAI & Automation Layer**
   - GenAIService:
     - Prompt/Pattern catalog,
     - Model routing and configuration,
     - Provenance and fingerprinting.
   - Pipelines that:
     - Translate,
     - Summarize,
     - Tag and classify,
     - Evaluate and compare outputs.

4. **UX & Integration Layer**
   - Command line tools and batch jobs.
   - VS Code extensions and developer tooling.
   - Web-based viewers (e.g., JVB viewer).
   - Future interactive agents and dashboards.

Conceptually:

> Corpus → Process & Enrich → GenAI & Automation → UX & Tools → Back to Corpus (via new annotations, translations, and metadata).

## 2. Core Conceptual Entities

Some central conceptual entities:

- **TextObject / Document Unit**
  - A structured representation of text plus metadata.
  - May correspond to:
    - A page,
    - A section,
    - A chapter,
    - A sutra, poem, or exercise.

- **Metadata Record**
  - Information about:
    - Source document,
    - Page and line references,
    - Language,
    - Section type (heading, paragraph, quote, exercise, etc.),
    - Historical and bibliographic context.

- **Prompt / Pattern**
  - A structured instruction template for GenAI systems.
  - Lives in a **Prompt/Pattern Catalog** with:
    - Keys, labels, descriptions,
    - Versioning and provenance.

- **GenAIService Request & Result**
  - Request:
    - Prompt key,
    - Input text and context,
    - Model configuration.
  - Result:
    - Output text,
    - Usage statistics,
    - Provenance and fingerprint metadata.

- **Provenance & Fingerprint**
  - Provenance: “What happened, when, using which inputs and models?”
  - Fingerprint: A compact identifier for (request, config, model, input) tuples used in transformations.

## 3. Conceptual Data Flow

A typical high-level flow might be:

1. **Ingest**
   - OCR or parse an input source (PDF, EPUB, images).
   - Create an initial TextObject or document representation.

2. **Clean & Structure**
   - Apply rules, regex, and structural heuristics.
   - Tag headings, paragraphs, quotes, footnotes, exercises.
   - Attach metadata (page numbers, section types, document IDs).

3. **Enrich via GenAIService**
   - Use patterns to:
     - Refine section boundaries,
     - Suggest headings,
     - Propose translations,
     - Generate queries and test pairs,
     - Identify entities or concepts.
   - All GenAI calls run through GenAIService with provenance.

4. **Store & Index**
   - Persist structured text and metadata.
   - Build indices for:
     - Search and retrieval,
     - Cross-language alignment,
     - Topic and concept exploration.

5. **Expose via UX & Tools**
   - JVB viewer for bilingual page-level exploration.
   - VS Code tools for developers and text engineers.
   - CLIs and batch jobs for large-scale processing.

6. **Evaluate & Iterate**
   - Use patterns and tools to:
     - Evaluate translation quality,
     - Assess sectioning and metadata quality,
     - Identify gaps or errors.
   - Feed these insights back into:
     - Data cleaning rules,
     - Prompt/pattern design,
     - Future ADRs and design refinements.

## 4. Conceptual Integration Points

Some key conceptual seams:

- **GenAIService CLI / API**
  - A boundary between:
    - The core project,
    - External tooling (VS Code, scripts, other agents).

- **Prompt/Pattern Catalog**
  - A boundary between:
    - Stable, named operations (“translate this page”),
    - The evolving internals of prompts and model selection.

- **Corpus Store**
  - A boundary between:
    - Data and metadata,
    - The tools that operate on them.

These seams are critical for:

- Testing,
- Refactoring,
- Building agentic workflows,
- Integrating with external systems without coupling everything together.

## 5. Relationship to Architecture Docs and ADRs

This conceptual architecture is intentionally:

- Higher-level than any single ADR.
- More stable than implementation details.
- A reference point for:
  - Evaluating new features,
  - Deciding where new components “live”,
  - Keeping the system mentally manageable.

Detailed architecture docs (under `docs/architecture`) and ADRs should:

- Be *consistent* with this conceptual view,
- Refine and specialize parts of it,
- Update it when fundamental assumptions or seams change.

This document should be updated when:

- New layers are added (e.g., a new data store or major subsystem),
- The conceptual flow between layers significantly changes,
- New categories of tools (e.g., agent orchestrators) become central, rather than experimental.

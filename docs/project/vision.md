# TNH-Scholar Project Vision

This document defines the long-term north star of the TNH-Scholar project — its purpose, scope, aspirations, and the future directions it aims toward.

## 1. Purpose

TNH-Scholar exists to serve the living Plum Village tradition by:

- Making Thích Nhất Hạnh’s teachings more accessible, discoverable, and navigable.
- Supporting deep, careful study by monastics, lay students, researchers, and practitioners.
- Providing trustworthy, transparent AI-assisted tools that respect the Dharma, the lineage, and the humans who work with them.

The project is not “just” a software system. It is a long-term scholarly and technical infrastructure for interacting with a body of teachings.

## 2. Core Vision

At a high level, TNH-Scholar aims to become:

- **A canonical, clean, multi-lingual corpus** of Thích Nhất Hạnh’s work and related sources, with:
  - High-fidelity text,
  - Rich metadata,
  - Sentence-level alignment across languages,
  - Footnotes, references, and contextual markers.
- **A flexible AI-assisted research environment** that:
  - Helps users search, explore, compare, and understand teachings.
  - Provides transparent reasoning and provenance for all AI outputs.
- **A foundation for future interactive tools**:
  - Conversational exploration agents,
  - Guided study companions,
  - Practice-support tools,
  - Visual and audio interfaces (e.g., JVB viewer, audio transcription pipelines).

## 3. Long-Horizon Aspirations

Over the long term, TNH-Scholar is envisioned to support:

- **Cross-lingual, cross-corpus research**:
  - Aligning Vietnamese, English, French, Chinese, Pāli, Sanskrit, Tibetan sources.
  - Surfacing conceptual parallels across canons and modern commentaries.
- **Rich interactive experiences**:
  - Bilingual reading environments,
  - Side-by-side views of scanned pages, cleaned text, translations, and annotations,
  - Audio + transcript + translation aligned at sentence/segment level.
- **Agentic workflows** (human-supervised automations):
  - Corpus cleaning and enrichment loops,
  - Translation and evaluation pipelines,
  - Semi-automated test and data-generation loops for models,
  - Eventually: code-aware agents that help maintain the TNH-Scholar system itself.

The long-term vision is *not* to replace human scholars or practitioners, but to:

> Extend human capacity for understanding, cross-referencing, and preserving the teachings — while always keeping human judgment and responsibility at the center.

## 4. Scope and Non-Scope

**In scope:**

- Tools to structure, clean, annotate, translate, and search the corpus.
- Infrastructure to support reliable AI-assisted workflows (GenAIService, patterns, provenance).
- Developer and research tooling (CLI, VS Code integration, batch jobs, evaluation tools).

**Out of scope (for TNH-Scholar itself):**

- Becoming a generic LLM platform unrelated to Plum Village or Buddhist studies.
- Building closed or opaque systems where the source texts, transformations, and models cannot be inspected or critiqued.
- Automation that removes humans from the loop in any way that would obscure responsibility, ethical judgment, or interpretive nuance.

## 5. Relationship to Spin-Offs and Descendants

TNH-Scholar may eventually give rise to:

- Separate tools focused on:
  - Software engineering assistance,
  - General AI infrastructure,
  - Generic prompt/pattern frameworks.
- Specialized research platforms built on its data and abstractions.

The guiding principle is:

> TNH-Scholar remains the reference home for Dharma-focused, Plum Village–centric work.  
> Spin-offs may reuse its design patterns and components, but do not dilute this core identity.

## 6. Time Scale

This project is intended as a **multi-year, possibly multi-decade effort**.  
Design choices should:

- Favor composability and clarity over short-term hacks.
- Respect that future maintainers (human and AI) will need to understand the intent behind the system.
- Support gradual refinement rather than one-off prototypes that cannot grow.

This vision document is living. It should be revisited when major architectural shifts occur or when the project’s role in the broader ecosystem meaningfully changes.

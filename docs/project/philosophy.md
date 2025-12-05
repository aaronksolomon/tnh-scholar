# TNH-Scholar Project Philosophy

> This document captures the project’s foundational philosophy — the conceptual, ethical, and methodological lens through which TNH-Scholar is designed and understood.

## 1. Human–AI Collaboration, Not Replacement

TNH-Scholar assumes that:

- Human practitioners, monastics, and scholars are the primary interpreters of the teachings.
- AI systems are tools that:
  - Surface patterns,
  - Accelerate mechanical tasks,
  - Support navigation and cross-referencing,
  - Help maintain a complex technical and textual ecosystem.

Philosophically:

> AI should amplify human care, attention, and discernment — not bypass them.

## 2. Fidelity and Clarity Over Novelty

The project values:

- **Faithful representation of source texts** over creative reinterpretation.
- **Clarity of structure and provenance** over opaque “smart” behavior.
- **Plain explanations and transparent pipelines** over magic.

This applies equally to:

- Corpus cleaning and transformation,
- Translation,
- Search and retrieval,
- UX design.

## 3. One Cohesive System, Many Facets

TNH-Scholar keeps related work in a single repository because:

- The same conceptual and technical foundations (TextObject models, metadata, GenAIService, provenance) underlie:
  - Corpus preparation,
  - Translation pipelines,
  - Knowledge base construction,
  - UX layers (JVB viewer, VS Code integrations),
  - Agentic workflows.
- Having one cohesive system:
  - Preserves cross-cutting consistency,
  - Makes it easier to reason about long-term evolution,
  - Reduces fragmentation of design philosophy.

The repo is large by necessity, but its *coherence* is a feature, not a bug.

## 4. Narrative and Structure as Teaching Supports

The project treats:

- Structure (chapters, sections, exercises, poems, plays, sutras),
- Metadata (time, place, audience, language),
- Narrative flow (how a teaching unfolds in context),

as **part of the teaching itself**, not incidental.  

Therefore:

- Tools are designed to preserve and highlight structure and narrative, not flatten them.
- Visualizations (e.g., JVB viewer) should respect page layout and historical context while making them navigable and searchable.

## 5. Agents as Careful Assistants

In future, more agentic patterns may emerge:

- Agents that:
  - Read design docs and ADRs,
  - Propose changes,
  - Refactor code,
  - Run evaluation patterns,
  - Suggest next steps.

The philosophical stance is:

- Agents are **careful assistants**, operating within:
  - Clear scopes,
  - Strong provenance,
  - Human-specified constraints,
  - Oversight and review.

They should help maintain alignment with the project’s purpose, not drift away from it.

## 6. Embracing Iteration and Walking Skeletons

TNH-Scholar accepts that:

- The system will grow in fits and starts.
- Walking skeletons (minimal, end-to-end prototypes) are favored:
  - Over big, untested designs.
  - Over premature generalization.

The philosophy is:

> Make something small, real, and testable.  
> Learn from it. Then refine.

This aligns with both mindful practice (step-by-step, attentive) and good engineering.

## 7. Documentation as Shared Mind

The project treats documentation as:

- A shared “mind” for:
  - Human contributors,
  - AI coding agents,
  - Future maintainers.
- A medium to:
  - Capture philosophy and intent,
  - Record decisions,
  - Guide automated tools.

This is why project philosophy and vision are documented explicitly, not just held in one person’s head or scattered across conversations.

This document should evolve as the project’s understanding deepens. When the philosophy shifts, that shift should be visible and explainable here.

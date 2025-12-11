---
title: "TNH-Scholar Project Principles"
description: "Guiding principles, values, and constraints for design and engineering decisions in TNH-Scholar."
owner: "Project Leadership"
author: "Aaron Solomon"
status: current
created: "2025-12-11"
updated: "2025-12-11"
---
# TNH-Scholar Project Principles

Defines the guiding principles, values, and constraints that shape design and engineering decisions in the TNH-Scholar project.

## 1. Dharma-Respecting Design

- **Faithfulness before cleverness**: When in doubt, preserve and accurately represent the source text rather than “improving” it.
- **Lineage awareness**: Tools should make it easy to find and verify original sources and context, not hide them.
- **Transparency about AI**: Any AI-generated or AI-transformed content must be clearly identifiable as such.

## 2. Provenance and Traceability

- **Provenance is first-class**: Every non-trivial transformation (cleaning, translation, tagging, summarization) should have:
  - Source reference(s),
  - Transformation description,
  - Model/config snapshot,
  - Timestamp and unique fingerprint where practical.
- **No silent mutations**: Avoid transformations that overwrite data without leaving a trace (log, provenance marker, or version history).
- **Inspectable by design**: It should be possible for a motivated user to trace “where did this output come from?” at a reasonable level of detail.

## 3. Structured Text as Canonical

- **Text + metadata > opaque blobs**:
  - Use structured representations (XML/HTML-like, JSON, TextObject models) instead of free-floating strings whenever feasible.
- **Preserve structure, then enhance it**:
  - Start from accurate transcription and basic structure,
  - Then add layers: headings, sections, footnotes, semantic tags.
- **Metadata is not an afterthought**:
  - Section types, page numbers, document IDs, language tags, etc. are essential; treat them as core data, not optional extras.

## 4. Human-in-the-Loop Automation

- **Automation serves humans, not the other way around**:
  - Automated pipelines should be reviewable, interruptible, and correctable by humans.
- **Gradual autonomy**:
  - Start with simple, inspectable, human-supervised loops,
  - Only move toward more autonomous agents when evaluation and guardrails are strong.
- **Explainable workflows**:
  - Pipelines should be describable in plain language (“what happens to the text at each step?”).

## 5. Simplicity, Composability, and Testability

- **Walking skeletons first**:
  - Prefer minimal, end-to-end vertical slices over large, half-finished subsystems.
- **Small, composable tools**:
  - Favor small utilities that can be combined in flexible ways (CLIs, services, pattern-based prompts) over monolithic pipelines.
- **Type safety and explicit interfaces**:
  - Use strong typing and clearly defined models to reduce ambiguity.
- **Documented seams**:
  - Integration points (e.g., GenAIService CLI, PromptCatalog APIs, data processing interfaces) should be documented and tested.

## 6. Documentation as Architecture

- **Docs are part of the system**:
  - ADRs, design docs, and philosophy documents are not optional; they are a key part of the project’s architecture.
- **Decision-first thinking**:
  - Significant design changes should be accompanied by ADRs or design notes.
- **AI-readable documentation**:
  - Documents should be written so that both humans and AI coding agents can use them to generate or maintain code.

## 7. Ethical AI Use

- **No misleading authority**:
  - AI outputs should not be presented as if they were canonically “Thích Nhất Hạnh speaking,” even if styled after him.
- **Context, not replacement**:
  - AI is used to point toward teachings, summarize, and support understanding — not to replace original texts or human teachers.
- **Respect for privacy and copyrights**:
  - Handle sensitive data, unpublished materials, and copyright constraints with care, explicit agreements, and clear boundaries.

## 8. Engineering Discipline for a Long-Lived System

- **Refactor as you go**:
  - Regularly clean interfaces and internal structure as the system evolves.
- **Keep the repo integrable**:
  - Maintain a coherent structure that can be understood by new contributors after a reasonable onboarding period.
- **Prefer boring infrastructure**:
  - Choose stable, well-understood technologies when possible (e.g., Postgres, standard Python tooling), especially for core components.

These principles are meant to be *referenced* when making choices. If a change conflicts with them, that conflict should be explicit and justified.

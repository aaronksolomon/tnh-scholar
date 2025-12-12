---
title: "User Guide Overview"
description: "Practical guide for using TNH Scholar as a tool user or workflow designer, covering main workflows and how the pieces fit together."
owner: ""
author: ""
status: current
created: "2025-12-02"
---
# User Guide Overview

This User Guide describes how to use TNH Scholar as a **tool user** or **workflow designer**. It focuses on practical flows, concrete decisions, and how the pieces fit together, without requiring you to understand every internal design document.

If you are new to the project, you may want to read the [TNH Scholar index](/index.md) first, then return here when you are ready to dive into concrete workflows.

---

## Roles and Typical Usage

Most people who interact with TNH Scholar do so in one of these roles:

- **Tool user**  
  Runs the CLI commands to process specific audio, text, or video inputs, and reviews the outputs.

- **Workflow designer**  
  Chains together multiple tools (and sometimes GenAIService calls) into repeatable flows for a community or project.

- **Developer or maintainer**  
  Extends the codebase, adds new tools, or modifies existing ones.

This guide is aimed primarily at **tool users** and **workflow designers**. Developers should also see the [development](/development/contributing-prototype-phase.md) docs.

---

## The Main Workflows

The current CLI and service layer support three broad types of workflows.

### 1. Audio and Video to Clean Text

**Goal:** Start from a recorded Dharma talk or teaching session and end with a clean, reviewable transcript.

Typical steps:

1. **Transcribe audio** with `audio-transcribe`  
   - Input: audio or video file (for example, `.wav`, `.mp3`, `.mp4`).  
   - Output: timestamped transcript (often JSON and/or text).

2. **Normalize formatting** with `nfmt`  
   - Input: transcript text.  
   - Output: normalized plain text, with consistent line wrapping, spacing, and punctuation.

3. **Optional: apply structure or tagging** with `tnh-fab` (deprecated; migrating to `tnh-gen`) or GenAIService-based flows
   - Add markers for paragraphs, headings, quotes, or exercises.
   - Prepare the text for metadata or translation workflows.

Relevant documentation:

- [CLI Overview](/cli-reference/overview.md)
- [audio-transcribe](/cli-reference/audio-transcribe.md) and [nfmt](/cli-reference/nfmt.md) CLI guides

---

### 2. Existing Text to Structured, Metadata-Rich Text

**Goal:** Take texts that already exist (OCR, EPUB, PDF-derived, or plain text) and make them **structured, tagged, and ready** for search, translation, or archival use.

Typical steps:

1. **Normalize and clean**  
   - Use `nfmt` or equivalent preprocessing to remove obvious noise and enforce consistent formatting.

2. **Apply patterns and prompts** with `tnh-fab` (deprecated; migrating to `tnh-gen`)
   - Use domain-specific patterns or prompts to:
     - Identify headings and sections,
     - Tag poems, plays, quotes, exercises, or notes,
     - Insert metadata or footnote markers.

3. **Review and refine**
   - Humans review the output, correct tagging, and adjust patterns as needed.
   - The corrected text becomes a better training or reference dataset for future workflows.

Relevant documentation:

- [Prompt System Architecture](/architecture/prompt-system/prompt-system-architecture.md)
- Additional prompt design docs: [ADR-PT03](/architecture/prompt-system/adr/adr-pt03-prompt-system-status-roadmap.md)
- [tnh-fab](/cli-reference/tnh-fab.md) CLI guide (deprecated; see [TNH-Gen](/architecture/tnh-gen/index.md) for migration)

---

### 3. Prepared Text to Model-Ready Chunks

**Goal:** Convert cleaned and structured text into units suitable for:

- Vector embedding and semantic search,
- Translation via GenAIService or other models,
- Evaluation and QA workflows.

Typical steps:

1. **Segment text into chunks**  
   - Apply rules based on token length, semantic boundaries, or structural markers (for example, sections, paragraphs, stanzas).

2. **Estimate token usage** with `token-count`  
   - Check that individual chunks fit model limits.  
   - Plan batch sizes and costs for large-scale processing.

3. **Run AI workflows** via GenAIService or other orchestration tools  
   - For example, translation, query-text pair generation, or similarity search indexing.

Relevant documentation:

- Chunking and diarization design docs: [Diarization System Design](/architecture/transcription/design/diarization-system-design.md)
- [GenAI Service design documents](/architecture/gen-ai-service/design/genai-service-design-strategy.md)
- [token-count](/cli-reference/token-count.md) CLI guide

---

## Choosing the Right Tool

When deciding which tool or workflow to use, consider:

- **Type of input**  
  - Audio or video → start with `audio-transcribe`.  
  - Text or OCR output → start with `nfmt` and/or `tnh-fab`.

- **Target output**  
  - Human-readable transcript → focus on `audio-transcribe` + `nfmt`.  
  - Machine-usable chunks for search or translation → include chunking logic and `token-count`.  
  - Rich, tagged editions → lean on `tnh-fab` and relevant prompt patterns.

- **Review requirements**  
  - For archival or publication-ready materials, assume **human review is mandatory**.  
  - For internal experimentation, you may tolerate more automation, but provenance still matters.

The [CLI Overview](/cli-reference/overview.md) includes a quick decision table for common scenarios.

---

## Provenance and Human Oversight

A central principle of TNH Scholar is that **all AI-assisted outputs must be traceable and reviewable**. In practice this means:

- Keeping original sources (audio, scans, raw text) accessible and referenced.  
- Recording which tools, prompts, and models were used to generate any derived artifact.  
- Encouraging review workflows where humans accept, modify, or reject AI-suggested changes.

The internal GenAIService and prompt system are designed to support these requirements. See:

- [Prompt System Architecture](/architecture/prompt-system/prompt-system-architecture.md)
- [Prompt Fingerprints and Provenance](/architecture/gen-ai-service/adr/adr-a12-prompt-system-fingerprinting-v1.md)

---

## Where to Go Next

Suggested next readings:

- For **concrete commands and options**:
  - [CLI Overview](/cli-reference/overview.md)
  - CLI guides under [cli](/cli-reference/overview.md)

- For **design and architecture background**:
  - [Architecture Overview](/architecture/overview.md)
  - GenAIService ADRs such as [ADR-A12](/architecture/gen-ai-service/adr/adr-a12-prompt-system-fingerprinting-v1.md)

- For **contributing and development**:  
  - [Contributing to TNH Scholar (Prototype Phase)](/development/contributing-prototype-phase.md)  
  - [Human–AI Software Engineering Principles](/development/human-ai-software-engineering-principles.md)

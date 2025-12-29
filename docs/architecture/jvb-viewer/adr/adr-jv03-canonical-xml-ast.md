---
title: "ADR-JV03: Canonical XML AST for English Parsing"
description: "Establishes canonical XML AST structure for JVB viewer English text parsing and rendering"
owner: "phapman"
author: "Aaron Solomon"
status: "accepted"
created: "2025-09-07"
---

# ADR-JV03: Canonical XML AST for English Parsing

Establishes canonical XML AST structure for JVB viewer English text parsing and rendering.

**Status:** Accepted
**Date:** 2025-09-07
**Authors:** Aaron Solomon

---

## Context
... [existing content unchanged] ...

## Consequences
- Mixed inline styling and nesting are preserved exactly.
- Viewer, search, and downstream NLP can derive their specific projections from one canonical model.
- Future transformations (HTML/Markdown/round-trip) are enabled without revisiting raw XML.
- Slightly higher upfront complexity in parse step; reduced complexity overall by avoiding parallel structures (no EnBlock).

---

# As-Built Addendum (json_builder3.py, 2025-09-14)

## Scope
Documents the implemented behavior of `json_builder3.py` where it narrows, clarifies, or extends ADR-003.

## Confirmed decisions
- **Dual AID model**: Logical **sAID** (`s:{doc_id}:{i:02d}`) and physical **pAID** (`p:{doc_id}:{page}`) with a published `aid_index {section_to_pages, page_to_section}`.
- **EN AST as first-class**: Section-scoped English AST serialized to JSON, including `Paragraph`, `Heading`, `Author`, `ListBlock/ListItemBlock`, `Toc`, `Raw`, and explicit `PageBreak`.
- **Notes isolation**: `<notes>` and `<translation-notes>` stored in an **annotations sidecar** keyed by sAID. Notes do not affect pagination or linearized EN text.
- **Section blocks**: `section_blocks[]` carry `en`, `vi`, `en_ast`, and `pagination {target_pages, status, breaks, method}`. Status is `exact|incomplete|pending`.

## Clarifications and simplifications vs prior intent
- **VI pagination policy (simplified)**  
  - Vietnamese OCR is parsed **sequentially** starting at page 1. `<pagebreak page="N">` attributes are **ignored** (`keep_pagebreaks=False`).  
  - Consequence: VI page numbers reflect file order, not embedded attributes. This removes drift caused by bad OCR tags.
- **VI section text with hard page separators**  
  - Section-level VI is consolidated with **U+000C form feed (`\f`)** between pages. Newlines remain available for future paragraphing.  
  - Rationale: unambiguous page boundaries inside section text while allowing later paragraph insertion.
- **EN pagination threading (explicit, side-effect free)**  
  - Page context (`cur`) is threaded through AST emission. Only an explicit `PageBreak(page=N)` advances context to `N+1`. Other blocks do not mutate context.
- **Top-level structure repair (strict)**  
  - A repair pass moves any top-level `pagebreak/notes/translation-notes/other` **between sections** into the **preceding section**.  
  - Any content before the first `<section>` raises `ValueError`. Multiple consecutive pagebreaks are warned, not fatal.
- **Images → pages policy**  
  - Page numbers are extracted from filenames; when absent, **deterministic fallback numbering** is assigned with a warning. Duplicate numbers are an error. URLs are normalized to `/images/{doc_id}/{filename}`.
- **Alignment intent signaling**  
  - If a page belongs to a section (by metadata) and EN is empty, a `Span.align = {"status":"pending","source":"section"}` is emitted to flag later reconciliation.
- **TOC handling**  
  - TOC is parsed into a nested AST and linearizes to indented lines for page text. This preserves structure without inventing semantics.
- **Raw passthrough**  
  - Unknown tags are preserved as `Raw{tag, attrs, text}` in AST and contribute text to linearized EN if present.

## Derived behaviors
- **Section ordering** follows metadata order; titles come only from metadata.  
- **Bundle title** is derived from `doc_id` pattern `…YYYY…Vol` when possible.  
- **Validation** reports: duplicate AIDs, missing images, empty VI/EN, EN pending, missing EN pagebreaks inside targeted ranges, and expected pages not present in spans.

## Reasons
- Reduce fragility from noisy OCR page markers.  
- Make pagination deterministic and auditable.  
- Keep notes non-intrusive to alignment.  
- Prepare for human-in-the-loop pagination repair by emitting clear signals (`pending`, `breaks` placeholder, `edits` log scaffold).

## Operational consequences
- Rebuilding with the same inputs yields stable page indices even if OCR page attributes change.  
- Any future tool that re-numbers VI pages must run **before** this builder or supply corrected images/metadata.  
- UI can rely on `\f` within `SectionBlock.vi` to segment pages in section view.

## Migration notes
- Existing consumers should switch to **`section_blocks[].vi`** for section-scoped VI with page splits and prefer **`section_blocks[].en_ast`** for rich rendering.  
- Tools that previously read EN notes from linearized text must read **`annotations[sAID]`** instead.  
- If prior workflows assumed VI page numbers from OCR attributes, update them to the **sequential policy** or pre-normalize the XML.

## Open questions / future work
- Populate `pagination.breaks` from observed EN pagebreaks to mark in-section splits.  
- Optional mode to honor VI `<pagebreak page="N">` when verified metadata exists.  
- Emit per-node source spans to enable diff-based reconciliation.  
- Define minimal edit ops in `edits[]` and wire a reviewer UI.
---
title: "JVB Viewer — Version 2 Strategy & High‑Level Design"
description: "Strategy for a projection-first VS Code-based viewer/editor that reconciles OCR outputs into a canonical JSON artifact."
owner: ""
author: ""
status: current
created: "2025-11-15"
---
# JVB Viewer — Version 2 Strategy & High‑Level Design

Strategy for a projection-first VS Code-based viewer/editor that reconciles OCR outputs into a canonical JSON artifact.

**ID (proposed):** JVB-STRAT-001 · **Status:** Draft · **Owner:** Aaron + TNH‑Scholar team · **Last updated:** 2025-09-19

## 0) Summary

We will build a **projection‑first** JVB viewer/editor anchored in **VS Code**.
The canonical artifact per page is a **minimal JSON** capturing: (a) page image reference, (b) word bboxes + text, (c) sentence groupings, (d) dual text sources (Google OCR vs. AI Chat-GPT vision) with provenance/confidence, (e) chosen text, and (f) optional structural cues (columns, heading level, emphasis).

Editing happens in a **VS Code webview overlay** on the scanned page with a bottom **edit/annotate panel** for quick human reconciliation and translation touch‑ups. Exports (HTML/EPUB/TEI/DOCX/Markdown) remain optional projections built later. This avoids the fragile, error‑prone XML of v1 while aligning tightly with the program’s UI/UX platform strategy.

---

## 1) Context & Motivation

- **V1 recap:** custom browser viewer + AI‑generated XML. Two blocking issues:
  1. **UI lift:** bespoke navigation/controls were heavy; goal is *clean viewing & editing* → VS Code is a better host.
  2. **Data fragility:** XML contained structural & page‑alignment errors (off‑by‑1 section spans). Fixing was tedious.
- **V2 direction:** regenerate translation + structure **from images** with a small, typed **layout DSL** (JSON), edited via overlay in VS Code. Document‑level metadata (section titles and page spans) will be corrected **upfront** and used as guidance.

**Why now:** Modern AI vision gives reliable sentence/fragment pairs. We can capture *just enough* structure on the first pass (columns, heading levels, bold/italic/underline) while the GPU is “hot,” minimizing re‑runs.

---

## 2) Goals & Non‑Goals

### Goals

- Beautiful, faithful **facsimile overlay** on the scanned page.
- **Fast human reconciliation** between dual sources (Google OCR vs AI vision) per sentence.
- **Sentence/fragment‑level translations** with roles (title/heading/body/poem_line/caption…).
- **Compute-aware capture** of structural cues on first pass: columns, heading levels (1–4), bold/italic/underline, quote/poem/caption detection.
- Fit naturally in **VS Code** (desktop + vscode.dev) with Git‑native collaboration (small JSON per page).

### Non‑Goals (for V2)**

- Print‑perfect typesetting or full kerning fidelity (good enough overlay is sufficient).
- Immediate TEI/DOCX round‑trip perfection (exports are later projections).
- One single monolithic file; we prefer **per‑page JSON** to reduce PR conflicts.

---

## 3) Strategic Approach

**Projection‑first architecture.** Canonical source = **minimal per‑page JSON**. Views:

- **Overlay View (primary):** HTML/SVG/Canvas over the page image. Hover/select sentence → highlight bbox union.
- **Edit Panel (bottom):** shows VI (GOCR vs AI) diff/chooser and editable EN translation; one‑click “adopt AI/GOCR,” mark reviewed.
- **Modes:** overlay VI / overlay EN / overlay with subscript EN / overlay both (VI+EN) / side‑by‑side (original vs overlay).

**Document metadata** (journal summary, section titles, page ranges) is tracked separately and used to label sentences and power navigation.

---

## 4) Minimal Data Model (v0)

Per **page JSON** (one file per page, Git‑friendly). Keep it small; add fields only when a feature needs them.

```jsonc
{
  "schema_version": "v0.1",
  "page": {
    "id": "p045",
    "image_uri": "images/1956-05/p045.png",
    "size": { "w": 2480, "h": 3508 },
    "words": [
      { "id": "w1", "bbox": [210,220,340,280], "text": "PHẬT" },
      { "id": "w2", "bbox": [360,220,470,280], "text": "-GIÁO" }
    ],
    "sentences": [
      {
        "id": "s1",
        "word_ids": ["w1","w2"],
        "role": "title",
        "section_id": "sec-0004",
        "sources": [
          { "kind": "gocr", "lang": "vi", "text": "Câu chuyện thống nhất", "confidence": 0.87 },
          { "kind": "ai",   "lang": "vi", "text": "Câu chuyện thống nhất", "confidence": 0.96 },
          { "kind": "ai",   "lang": "en", "text": "The Story of Unification", "confidence": 0.95 }
        ],
        "chosen": { "lang": "vi", "source_kind": "ai", "text": "Câu chuyện thống nhất" },
        "style": { "heading_level": 1, "bold": true, "italic": false, "underline": false }
      }
    ],
    "translations": [
      { "sentence_id": "s1", "lang": "en", "text": "The Story of Unification", "status": "draft" }
    ]
  }
}
```

**Document metadata JSON** (one per issue):

```jsonc
{
  "doc_meta": {
    "doc_id": "pgvn-1956-05",
    "journal_summary": "…",
    "sections": [
      { "section_id": "sec-0001", "title_vi": "Trang tiêu đề", "title_en": "Title Page", "start_page": 1, "end_page": 1 },
      { "section_id": "sec-0002", "title_vi": "Mục lục", "title_en": "Table of Contents", "start_page": 2, "end_page": 2 },
      { "section_id": "sec-0004", "title_vi": "Câu chuyện thống nhất", "title_en": "The Story of Unification", "start_page": 4, "end_page": 5 }
    ]
  }
}
```

---

## 5) Processing Pipeline (walking skeleton)

1. **Ingest**  
   - Load `doc_meta.json`.  
   - For each page image: load Google OCR (if available) and run AI vision to produce VI sentences + EN drafts and style cues.
2. **Assemble per‑page JSON**  
   - Words (bbox,text), sentence groupings (list of word_ids), `sources[]` with `{kind, lang, text, confidence}`.  
   - Choose initial VI source (simple heuristic: higher confidence if edit distance ≤ τ). Attach `section_id` using page ranges.  
   - Capture first‑pass **structure**: `columns` (1,2), `heading_level` (0–4), `bold/italic/underline`, and coarse roles (`title/heading/body/poem_line/caption`).
3. **Render**  
   - VS Code webview overlay (Canvas/SVG), hit‑testing on sentence bbox unions.  
   - Bottom panel shows VI (GOCR vs AI) diff + EN editor; mark reviewed.
4. **Persist**  
   - `Cmd+S`: write updated per‑page JSON. Git tracks small diffs; PR review is the editorial checkpoint.
5. **(Later) Exporters**  
   - HTML/EPUB reading edition; TEI/DOCX optional once semantics stabilize.

---

## 6) UI/UX Plan (VS Code native; web‑capable)

- **Overlay panel** (primary):  
  - Hover: highlight sentence bbox; tooltip shows role, source, confidence.  
  - Click: select; bottom panel opens.  
  - Drag or Shift‑click: multi‑select for batch actions.  
- **Bottom edit/annotate panel**:  
  - VI (GOCR vs AI) side‑by‑side diff + radio‑choose + “Merge” button.  
  - EN translation textarea with status (draft/reviewed/final).  
- **Modes**: overlay VI/EN/subscript EN/subscript both/side‑by‑side.  
- **Hotkeys**: `C` (cycle VI source), `T` (toggle modes), `↑/↓` (prev/next sentence), `R` (reviewed).  
- **Section breadcrumb** from `doc_meta`: e.g., `The Story of Unification · p4`.

**Performance**: batch draw to Canvas; spatial index for hit‑testing; lazy render for large pages.

---

## 7) Alignment, Structure & Compute Notes

- **Sentence alignment**: start without char spans; sentence bbox = union of its `word_ids`. If VI source changes, recompute union.  
- **Columns**: detect via x‑band clustering of `word`/`line` centroids; store as `page.columns = 1|2` hint.  
- **Heading levels**: simple features (font size proxy = bbox height, y‑position bands, centeredness, leading whitespace) → classify into 0–4.  
- **Emphasis**: bold/italic/underline from AI vision; optional later refinement via glyph thickness heuristics.  
- **Compute economy**: capture all first‑pass cues while the model is warm; persist; later passes use cached JSON and avoid re‑visioning pages.

---

## 8) Integration of Dual Sources (GOCR vs AI)

- Store both under `sentence.sources[]`; keep `confidence` + `trace_id`.  
- Auto‑choose high‑confidence agreement; flag disagreements (`needs_review: true`).  
- UI exposes a **one‑click chooser** and a **merge** helper; commit choice into `sentence.chosen`.  
- Batch adoption tool per section: “Adopt AI when `confidence >= 0.95` and edit‑distance ≤ 2”.

---

## 9) Risks & Mitigations

- **Schema creep** → Keep v0 minimal; add fields behind explicit features.  
- **Round‑trip loss** → Defer TEI/DOCX until semantics stabilize; treat JSON as canonical.  
- **Human ergonomics** → No raw JSON editing; all edits via overlay/panel; provide small PR diffs per page.  
- **OCR noise & drift** → Provide “re‑snap sentence” to neighbor words; keep an `audits[]` log for revertibility.  
- **GPU cost** → Batch pages; cache all first‑pass cues; only re‑run AI on truly changed pages.

---

## 10) Alternatives Considered

- **Re‑commit to XML (ALTO/TEI) as canonical**: higher barrier to edit; brittle early on.  
- **Browser‑only custom app**: higher UI lift; diverges from the VS Code platform strategy.  
- **DOCX/ODF as canonical**: painful diffing/merges; poor fit for sentence‑level overlays.

---

## 11) Milestones (walking skeleton → v2 beta)

- **M0 (Prototype overlay)**: static HTML showing page image, word bboxes, selectable sentences; bottom panel with VI/EN.  
- **M1 (VS Code extension)**: load/save per‑page JSON; overlay modes; section breadcrumb.  
- **M2 (Dual‑source UI)**: GOCR vs AI diff chooser; batch adoption; “reviewed” status.  
- **M3 (Structure cues)**: columns, heading levels, emphasis flags captured and rendered.  
- **M4 (v2 beta)**: section‑level navigation; export HTML; light theming/typography.

---

## 12) Alignment with Human‑Agent Coding Principles

- **Single responsibility & small helpers**: separation of ingest, assemble, render, persist.  
- **State explicit & local**: page‑scoped JSON; no global hidden state.  
- **Validation before mutation**: preview diffs, PR reviews.  
- **Walking skeleton first**: ship overlay + editor with minimal model before exporters.  
- **Type safety**: Pydantic models mirror JSON; enums for roles/modes.  
- **No premature optimization**: only add spans/blocks/char‑level detail if a UI feature demands it.

---

## 13) Open Questions

- What is the minimum **role set** that covers the journal? (title, heading, subtitle, body, poem_line, quote, caption, aside?)  
- Do we need **paragraph grouping** in v2, or can we stay sentence‑centric and infer paragraphs visually?  
- Should **glossary/terminology** support land in v2 (suggestions in EN panel), or v3?  
- What is the desired **export target** priority (HTML reading edition vs TEI vs DOCX)?  
- Will public editors use **vscode.dev** (PR‑based), and do we need contributor onboarding tooling?

---


## 14) Appendix — Suggested Repo Layout (per issue)

```plaintext
/JVB-1956-05/
  doc_meta.json
  /pages/
    p001.json
    p002.json
    ...
  /images/
    p001.png
    p002.png
    ...
  /exports/   (generated)
    html/
    epub/
    tei/
```

---

**Decision to record (provisional):** Adopt **JVB-STRAT-001** as the working strategy for Version 2. Treat this document as a **Strategy Note** (pre‑ADR). As details solidify (e.g., sentence alignment specifics, exporter contracts), split into focused ADRs (e.g., *ADR‑006 Overlay Rendering Contract*, *ADR‑007 Dual‑Source Reconciliation*).

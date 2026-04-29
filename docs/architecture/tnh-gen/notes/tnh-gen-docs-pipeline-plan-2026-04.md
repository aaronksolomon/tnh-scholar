---
title: "tnh-gen Docs Consistency + OCR Pipeline Walkthrough Plan"
description: "Work plan for v0.4.0 docs consistency pass on tnh-gen user-guide and CLI reference, and development of a golden OCR pipeline example with two-track clean→punctuate→section→translate walkthrough."
owner: ""
author: ""
status: active
created: "2026-04-27"
---

# tnh-gen Docs Consistency + OCR Pipeline Walkthrough

Work plan for the v0.4.0 docs consistency pass and golden pipeline example development.

---

## Context

Two interrelated goals:

1. **Docs consistency pass** — `docs/user-guide/` and `docs/cli-reference/tnh-gen.md` need to sit tightly together, share a canonical pipeline example, and reflect the current tnh-gen API (not the legacy tnh-fab / patterns terminology).

2. **Golden pipeline example** — a fully worked, real-world pipeline using 4 pages of OCR journal text, exercising both the simple (`clean→punctuate→translate`) and line-tracked (`clean_numbered→section→line_translate`) paths. This doubles as a live regression test.

---

## Source Material

**Journal:** *Phật Giáo Việt Nam*, issue 17–18, December 1957  
**Article:** *"Vũ-trụ-quan Phật học"* (Buddhist Cosmological View) by Thạc-Đức  
**Pages:** 7–10 of the scan (indices 6–9 in `text_pages.json`)  
**Source file:** `tests/golden/journal-pipeline/source.txt`  
**Scan images:** `tests/golden/journal-pipeline/images/page7–10.jpg`  
**PDF source:** Thư Viện Huệ Quang (HCMC, 2014 reprint series)  
Collection page: https://thuvienhoasen.org/a21829/tap-chi-phat-giao-viet-nam-nam-1956  
Local copy (untracked): `data/PDF/Phat_Giao_journals/phat-giao-viet-nam-1956-17-18.pdf`

**Known OCR artifacts in source.txt (intentional — what the clean stage must fix):**
- Running footer "PHẬT GIÁO VIỆT NAM" at bottom of page 7
- Running footer fragment "THẢI CHO MỌT NẤU" at bottom of page 10
- Duplicate section marker (`1.―` / `1-`) on page 7
- Stray mid-paragraph OCR artifact `KO` on page 8
- Broken sentence continuations at page boundaries

**Pipeline variables for this source:**
```
--var source_language=Vietnamese
--var publication_name="Phật Giáo Việt Nam"
--var publisher_mark="Tư Viện Huệ Quang"
```

---

## Pipeline Design

### Recommended Pipeline (demonstrates sectioning capacity)

```
source.txt (combined OCR)
  → awk number lines          (preprocessing)
  → section_by_break          (tnh-gen: identify page sections → sections.json)
  → [per section]
      default_clean_numbered  (tnh-gen: remove artifacts, N:LINE output)
      default_line_translate  (tnh-gen: translate with section context)
  → combine
```

Key design decisions:
- `section_by_break` performs the document split using structural breaks (page headers, blank lines, article titles). This is the tnh-gen split step — it demonstrates the sectioning capability.
- Cleaning happens **per section** (~30 lines), not on the full combined document. This keeps model context focused and contains errors locally.
- `sections.json` carries document metadata (section titles, key concepts, Dublin Core, summary) that gives the translator full context for every section.
- The numbering step (awk) is a trivial preprocessing step before any AI call.

### Simple Alternative (no line tracking)

```
[per page source file]
  → default_clean             (free-form plain text output)
  → default_punctuate
  → [translate]
```

Pre-extracted per-page files (`source_page_7.txt` etc.) in `tests/golden/journal-pipeline/` support this simpler path without the sectioning step.

---

## Prompts Created

Both new prompts derived from the original cleaning system message in
`notebooks/journal_processing/journal_cleaning1.ipynb` and `journal_cleaning2.ipynb`.

| File | Key | Purpose |
|------|-----|---------|
| `prompts/default_clean.md` | `default_clean` | Free-form OCR cleaning to plain text (Track A) |
| `prompts/default_clean_numbered.md` | `default_clean_numbered` | OCR cleaning to `N:LINE` numbered transcript (Track B) |

**Variables (both prompts):**
- `source_language` — required
- `publication_name` — optional; removes footer lines matching this name
- `publisher_mark` — optional; removes watermark lines matching this text
- Default model: `gpt-4o`, temperature: 0

---

## Work Items

### ✅ Done

- [x] `prompts/default_clean.md` — created
- [x] `prompts/default_clean_numbered.md` — created
- [x] `tests/golden/journal-pipeline/source.txt` — extracted (pages 6–9 from `text_pages.json`)
- [x] `tests/golden/journal-pipeline/images/page7–10.jpg` — copied
- [x] `tests/golden/journal-pipeline/README.md` — source attribution, known artifacts, PDF provenance

### 🚧 Pending: Run the Pipeline

Run both tracks against `source.txt` and commit golden outputs.

**Track A commands:**
```bash
tnh-gen run --prompt default_clean \
  --input-file tests/golden/journal-pipeline/source.txt \
  --var source_language=Vietnamese \
  --var publication_name="Phật Giáo Việt Nam" \
  --var publisher_mark="Tư Viện Huệ Quang" \
  --output-file tests/golden/journal-pipeline/01_cleaned.txt

tnh-gen run --prompt default_punctuate \
  --input-file tests/golden/journal-pipeline/01_cleaned.txt \
  --var source_language=Vietnamese \
  --output-file tests/golden/journal-pipeline/02_punctuated.txt
```

**Track B commands:**
```bash
tnh-gen run --prompt default_clean_numbered \
  --input-file tests/golden/journal-pipeline/source.txt \
  --var source_language=Vietnamese \
  --var publication_name="Phật Giáo Việt Nam" \
  --var publisher_mark="Tư Viện Huệ Quang" \
  --output-file tests/golden/journal-pipeline/01_cleaned_numbered.txt

# Count lines in output, then run section:
tnh-gen run --prompt default_section \
  --input-file tests/golden/journal-pipeline/01_cleaned_numbered.txt \
  --var source_language=Vietnamese \
  --var section_count=4 \
  --var line_count=<lines/4> \
  --var metadata="{\"title\": \"Vũ-trụ-quan Phật học\", \"author\": \"Thạc-Đức\", \"journal\": \"Phật Giáo Việt Nam\", \"issue\": \"17-18\", \"year\": \"1957\"}" \
  --output-file tests/golden/journal-pipeline/03_sections.json

tnh-gen run --prompt default_line_translate \
  --input-file tests/golden/journal-pipeline/01_cleaned_numbered.txt \
  --vars tests/golden/journal-pipeline/03_sections.json \
  --var source_language=Vietnamese \
  --var target_language=English \
  --var style="scholarly" \
  --output-file tests/golden/journal-pipeline/04_translated.txt
```

### ✅ Docs Updates Complete

- [x] `docs/user-guide/best-practices.md` — replaced stale pipeline example with two-track commands; added link to walkthrough
- [x] `docs/user-guide/pipeline-walkthrough.md` — new file; full annotated two-track walkthrough with OCR artifact examples, all commands, section JSON shape, golden output table
- [x] `docs/cli-reference/tnh-gen.md` — added "Pipeline Examples" section with both tracks, before/after OCR snippet, track comparison note
- [x] `docs/user-guide/overview.md` — Workflow 2 updated with concrete CLI commands and link to walkthrough
- [x] `docs/user-guide/prompt-system.md` — rewritten: Pattern/PatternManager removed, PromptCatalog API, updated default prompts table including `default_clean` and `default_clean_numbered`

---

## Key Decisions Recorded

- **Two-track design**: show simple (plain text) and line-tracked pipelines side by side; the contrast is the teaching value.
- **Source selection**: pages 7–10 of issue 17–18 chosen because they are a coherent philosophical article with real, diverse OCR artifacts — not a manufactured example.
- **`default_clean` scope**: includes character-substitution fixing (e.g. `f`→`t` OCR errors) and optional publication/watermark artifact removal via template variables, not just structural cleanup.
- **Numbered clean preserves scan-line boundaries**: do not merge lines; omitted artifact lines don't consume a line number so downstream `N:LINE` indexing stays clean.
- **Section count for 4 pages**: use `section_count=4` (one section per page as a starting point, model may prefer natural topic breaks).
- **PDF not committed**: 12 MB; stays in untracked `data/PDF/`; README documents the thuvienhoasen.org collection page as the public source.
- **Golden outputs location**: `tests/golden/journal-pipeline/` — consistent with existing test directory structure.

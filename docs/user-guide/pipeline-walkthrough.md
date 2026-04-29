---
title: "Pipeline Walkthrough: OCR Journal Text"
description: "A fully worked pipeline example — section, clean, and translate four pages of OCR-scanned Vietnamese Buddhist journal text using tnh-gen for every stage."
owner: ""
author: ""
status: current
created: "2026-04-28"
---

# Pipeline Walkthrough: OCR Journal Text

This walkthrough processes four pages of scanned Vietnamese Buddhist text through a complete pipeline that demonstrates all the major tnh-gen processing stages. Every stage uses `tnh-gen run` — including the split step.

```
source (combined OCR)
  → number lines          (preprocessing)
  → section_by_break      (tnh-gen: identify page sections → sections.json)
  → [per section]
      default_clean_numbered   (tnh-gen: remove artifacts, output N:LINE)
      default_line_translate   (tnh-gen: translate with section context)
  → combine
```

Processing section-by-section rather than as one large batch keeps each model call focused on a single page's worth of content (~30–40 lines), which gives the model appropriate context and contains any errors to a single page.

---

## Source Material

**Text:** *"Vũ-trụ-quan Phật học"* (Buddhist Cosmological View) by Thạc-Đức
**Source:** *Phật Giáo Việt Nam*, issue 17–18, December 1957
**Pages:** 7–10 of the journal scan
**Combined source file:** `tests/golden/journal-pipeline/source.txt`
**Scan images:** `tests/golden/journal-pipeline/images/page7–10.jpg`
**Journal collection:** https://thuvienhoasen.org/a21829/tap-chi-phat-giao-viet-nam-nam-1956

The article presents the Buddhist doctrine of dependent origination (*paticca-samuppāda*) against three competing Indian philosophical schools from the time of the Buddha — representative of the dense, formally structured academic Vietnamese that this pipeline is designed for.

### What the Raw OCR Looks Like

The four pages contain several categories of artifact that the clean stage must fix:

```
VŨ-TRỤ-QUAN
PHAT-HOC                          ← diacritics dropped on article title
THẠC - ĐỨC
...
1.―
1-                                ← duplicate section marker
Khuynh hướng Túc mệnh-luận (Pubba kata hetu)
...
họa phúc đều
PHẬT GIÁO VIỆT NAM                ← running journal footer mid-paragraph
...
thấu suốt quá khứ vị lai hiện-
THẢI CHO MỌT NẤU                  ← page footer artifact (page 10)
```

**Pipeline variables for this source** (used throughout):

```bash
SOURCE_LANG=Vietnamese
PUB_NAME="Phật Giáo Việt Nam"
PUB_MARK="Tư Viện Huệ Quang"
METADATA='{"title":"Vũ-trụ-quan Phật học","author":"Thạc-Đức","journal":"Phật Giáo Việt Nam","issue":"17-18","year":"1957"}'
```

---

## Stage 1: Number Lines (Preprocessing)

The sectioning prompt requires `N:LINE` numbered input. Add line numbers to the combined raw source before any AI processing:

```bash
awk '{print NR":"$0}' \
  tests/golden/journal-pipeline/source.txt \
  > tests/golden/journal-pipeline/source_numbered.txt
```

This is a plain shell step — no model call. The numbered file retains all OCR artifacts; the AI sectioning step works from raw numbered text.

---

## Stage 2: Section (Split)

`section_by_break` divides the numbered transcript into sections, preferring existing structural breaks — page headers, blank lines, article title lines — over thematic interpretation. With `section_count=4` it naturally identifies the four journal pages.

```bash
tnh-gen run --prompt section_by_break \
  --input-file tests/golden/journal-pipeline/source_numbered.txt \
  --var source_language=Vietnamese \
  --var section_count=4 \
  --var metadata="${METADATA}" \
  --output-file tests/golden/journal-pipeline/sections.json
```

The output JSON identifies section boundaries, carries document-level metadata, and will serve as translation context later:

```json
{
  "sections": [
    { "start_line": 1,   "title": "Ba Khuynh Hướng Triết Học" },
    { "start_line": 29,  "title": "Thế Giới Quan Nhân Duyên" },
    { "start_line": 68,  "title": "Đồng Thời và Dị Thời Nhân Quả" },
    { "start_line": 106, "title": "Quan Niệm Nhân Quả Phật Giáo" }
  ],
  "document_summary": "...",
  "key_concepts": ["nhân duyên", "paticca-samuppāda", "vô thường"],
  "dublin_core": { "title": "Vũ-trụ-quan Phật học", "creator": "Thạc-Đức", ... }
}
```

---

## Stage 3: Extract Section Lines

Use the `start_line` values from `sections.json` to extract each section's lines from the numbered source. A small helper script handles this:

```python
import json, sys

with open("tests/golden/journal-pipeline/source_numbered.txt") as f:
    lines = f.readlines()

with open("tests/golden/journal-pipeline/sections.json") as f:
    sections = json.load(f)["sections"]

for i, sec in enumerate(sections):
    start = sec["start_line"]
    end = sections[i + 1]["start_line"] - 1 if i + 1 < len(sections) else len(lines)
    section_lines = [l for l in lines if start <= int(l.split(":")[0]) <= end]
    outfile = f"tests/golden/journal-pipeline/section_{i+1}_raw.txt"
    with open(outfile, "w") as f:
        f.writelines(section_lines)
    print(f"Section {i+1}: lines {start}–{end} → {outfile}")
```

This produces `section_1_raw.txt` through `section_4_raw.txt`, each containing only that page's numbered raw lines.

---

## Stage 4: Clean Each Section

Run `default_clean_numbered` on each section file individually. Each call receives a single page's worth of content (~25–40 lines), giving the model a focused context for OCR correction.

```bash
for i in 1 2 3 4; do
  tnh-gen run --prompt default_clean_numbered \
    --input-file tests/golden/journal-pipeline/section_${i}_raw.txt \
    --var source_language="${SOURCE_LANG}" \
    --var publication_name="${PUB_NAME}" \
    --var publisher_mark="${PUB_MARK}" \
    --output-file tests/golden/journal-pipeline/section_${i}_clean.txt
done
```

After cleaning, footer lines (`PHẬT GIÁO VIỆT NAM`, `THẢI CHO MỌT NẤU`) are gone. The duplicate `1.―` / `1-` on page 1 is resolved to `1.`. Line numbering remains contiguous — artifact lines are omitted without occupying a line number.

---

## Stage 5: Translate Each Section

Translate each clean section with `default_line_translate`, passing `sections.json` as the context source. The model receives the full document summary, key concepts, and section titles to inform its translation choices.

```bash
for i in 1 2 3 4; do
  tnh-gen run --prompt default_line_translate \
    --input-file tests/golden/journal-pipeline/section_${i}_clean.txt \
    --vars tests/golden/journal-pipeline/sections.json \
    --var source_language="${SOURCE_LANG}" \
    --var target_language=English \
    --var style=scholarly \
    --output-file tests/golden/journal-pipeline/section_${i}_translated.txt
done
```

Output preserves `N:LINE` numbering so translated lines align back to source lines.

---

## Stage 6: Combine

```bash
cat tests/golden/journal-pipeline/section_{1,2,3,4}_translated.txt \
  > tests/golden/journal-pipeline/final_translated.txt
```

---

## Golden Output Structure

After running the full pipeline, commit these files as the golden reference:

```
tests/golden/journal-pipeline/
├── source.txt                    ← combined raw OCR (all 4 pages)
├── source_numbered.txt           ← line-numbered raw OCR
├── source_page_7.txt             ← individual page sources (also available)
├── source_page_8.txt
├── source_page_9.txt
├── source_page_10.txt
├── images/
│   └── page7–10.jpg             ← scan images
├── sections.json                 ← section boundaries + document metadata
├── section_1_raw.txt             ← extracted raw section lines
├── section_2_raw.txt
├── section_3_raw.txt
├── section_4_raw.txt
├── section_1_clean.txt           ← cleaned N:LINE per section
├── section_2_clean.txt
├── section_3_clean.txt
├── section_4_clean.txt
├── section_1_translated.txt      ← translated N:LINE per section
├── section_2_translated.txt
├── section_3_translated.txt
├── section_4_translated.txt
└── final_translated.txt          ← combined output
```

Re-running the pipeline on the same source and diffing against these files confirms that prompt changes have not introduced regressions.

---

## A Simpler Alternative (Track A)

If you do not need line-level provenance, you can use the per-page source files directly and process each page through plain-text cleaning and translation without sectioning:

```bash
for page in 7 8 9 10; do
  tnh-gen run --prompt default_clean \
    --input-file tests/golden/journal-pipeline/source_page_${page}.txt \
    --var source_language=Vietnamese \
    --var publication_name="${PUB_NAME}" \
    --var publisher_mark="${PUB_MARK}" \
    --output-file page_${page}_clean.txt

  tnh-gen run --prompt default_punctuate \
    --input-file page_${page}_clean.txt \
    --var source_language=Vietnamese \
    --output-file page_${page}_punctuated.txt
done
```

This requires no sectioning step and no line-number handling, at the cost of losing per-section translation context and line references.

---

## See Also

- [Prompt System](/user-guide/prompt-system.md)
- [Best Practices](/user-guide/best-practices.md)
- [tnh-gen CLI Reference](/cli-reference/tnh-gen.md)

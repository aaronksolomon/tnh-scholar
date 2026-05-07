---
title: "Journal Pipeline Golden Test"
description: "Source material and reference assets for the clean→punctuate→section→translate pipeline walkthrough"
status: current
created: "2026-04-27"
---

# Journal Pipeline — Golden Test Assets

Source material for the four-stage OCR journal pipeline:

```
clean → punctuate → section → translate
```

## Source Text

**`source.txt`** — Raw OCR output for four pages of the article *"Vũ-trụ-quan Phật học"*
(Buddhist Cosmological View) by Thạc-Đức, from *Phật Giáo Việt Nam* journal, issue 17–18, 1957.

Corresponds to pages 7–10 of the journal scan (1-indexed), i.e. indices 6–9 in
`processed_data/processed_journal_data/phat-giao-viet-nam-1956-17-18/ocr_data/text_pages.json`.

Known OCR artifacts in this text (intentional — they are what the `clean` stage should fix):
- Running footer "PHẬT GIÁO VIỆT NAM" intruding at the bottom of page 7
- Running footer fragment "THẢI CHO MỌT NẤU" at the bottom of page 10
- Duplicate section marker (`1.―` / `1-`) on page 7
- Stray mid-paragraph artifact `KO` on page 8
- Broken sentence continuations across page boundaries

## Scan Images

**`images/page7.jpg` – `images/page10.jpg`** — Source scan images for visual verification of OCR output and cleaning decisions.

## Full Journal PDF

The local copy is at (untracked, not in version control):

```
data/PDF/Phat_Giao_journals/phat-giao-viet-nam-1956-17-18.pdf
```

**Public source:** The journal is digitised and hosted by Thư Viện Huệ Quang (Hue Quang Library, Ho Chi Minh City, 2014 reprint series). The collection page is:

> https://thuvienhoasen.org/a21829/tap-chi-phat-giao-viet-nam-nam-1956

Individual issue PDFs follow the pattern `phat-giao-viet-nam-1956-{issue}.pdf` but require a session-based file ID from the collection page — visit the page in a browser to obtain the direct download link for issue 17-18.

Note: the watermark text `TU VIEN HUE QUANG` in the scans is the stamp of this same library.

## Pipeline Variables

Run the walkthrough from the repo root. `tnh-gen` will discover the canonical
repo-local prompt workspace from `./tnh-prompts/` by default.

When running this example, use:

```bash
--var source_language=Vietnamese
--var publication_name="Phật Giáo Việt Nam"
--var publisher_mark="Tư Viện Huệ Quang"
```

## Local Output Conventions

After running the pipeline, local outputs are typically written here:

| File | Stage | Prompt |
|------|-------|--------|
| `01_cleaned.txt` | clean (plain text) | `default_clean` |
| `01_cleaned_numbered.txt` | clean (numbered) | `default_clean_numbered` |
| `02_punctuated.txt` | punctuate | `default_punctuate` |
| `sections.json` | section | `default_section` |
| `04_translated.txt` | translate (simple) | `default_line_translate` or `simple_translate_paragraph_thay` |

Scratch variants such as `02_sections.json`, `03_sections.json`, or
`sections.strict.json` may also appear during prompt iteration. These are
generated local artifacts as well.

The checked-in walkthrough artifacts live under
`tests/golden/journal-pipeline/walkthrough/clean_translate/`, including
`sections_gpt54.json`, its provenance sidecar, numbered section slices, cleaned
section outputs, vars files, and translated section outputs. Treat those as the
artifact set of record for the current journal case study walkthrough. Ad hoc
reruns and scratch variants may still be left untracked.

## Handoff State

Before rerunning this larger journal golden:

- Run from the repo root so the default `./tnh-prompts/` workspace is discovered.
- Confirm the five small JSON prompt live checks in `tests/golden/json-prompts/` first.
- Confirm budget configuration is high enough for live runs. Earlier preliminary attempts in this workstream were blocked under the old `$0.10` default; the current runtime default is now `$0.30`.
- If running from this worktree source, export env vars from the root repo `.env` with `set -a` before invoking `tnh-gen`.

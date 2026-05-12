---
title: "Journal Pipeline Golden Test"
description: "Source material and reference assets for the clean→punctuate→section→translate pipeline walkthrough"
status: current
created: "2026-04-27"
---

# Journal Pipeline — Golden Test Assets

Source material for the OCR journal pipeline case study.

```
clean → punctuate → section → translate
```

## Source Text

The current canonical source for the case study is the rebuilt five-page article under:

- `5page/source.txt`
- `5page/source_numbered.txt`
- `5page/source_page_7.txt` through `5page/source_page_11.txt`

That rebuilt source corresponds to pages 7–11 of the journal scan (1-indexed).

Earlier four-page workflow artifacts are preserved separately under
`walkthrough/clean_translate/` as historical testing/reference material. The current
case-study workflow uses `walkthrough/clean_translate_5page/`.

Known OCR artifacts in the rebuilt source text (intentional — they are what the `clean`
stage should fix):
- Running footer "PHẬT GIÁO VIỆT NAM" intruding at the bottom of page 7
- Running footer fragment near the end of page 10
- Duplicate section marker (`1.―` / `1-`) on page 7
- Stray mid-paragraph artifact `KO` on page 8
- Broken sentence continuations across page boundaries

## Scan Images

User-facing scan assets for the case study are tracked under
`docs/user-guide/assets/journal-pipeline/`, including pages 7 and 11 with clean and
annotated variants for review.

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
| `04_translated.txt` | translate (simple) | `translate_journal_section_en` or `translate_journal_section_tnh_voice_en` |

Scratch variants such as `02_sections.json`, `03_sections.json`, or
`sections.strict.json` may also appear during prompt iteration. These are
generated local artifacts as well.

The checked-in current walkthrough artifacts live under
`tests/golden/journal-pipeline/walkthrough/clean_translate_5page/`, including
`sections_gpt54.json`, its provenance sidecar, numbered section slices, cleaned
section outputs, vars files, and translated section outputs. Treat those as the
artifact set of record for the current journal case study walkthrough.

The earlier four-page artifact set remains under
`tests/golden/journal-pipeline/walkthrough/clean_translate/` as historical
comparison material.

## Handoff State

Before rerunning this larger journal golden:

- Run from the repo root so the default `./tnh-prompts/` workspace is discovered.
- Confirm the five small JSON prompt live checks in `tests/golden/json-prompts/` first.
- Confirm budget configuration is high enough for live runs. Earlier preliminary attempts in this workstream were blocked under the old `$0.10` default; the current runtime default is now `$0.30`.
- If running from this worktree source, export env vars from the root repo `.env` with `set -a` before invoking `tnh-gen`.

## Artifact Preservation Rules

This journal golden exposed an important workflow rule: preserve raw `tnh-gen` outputs,
especially structured JSON artifacts, before any reviewed edits or reruns.

Practical rules for this directory:

- Keep raw model outputs unchanged when they are used as golden evidence.
- If a human review step changes a model artifact, write a new file with a suffix such as
  `_corrected` or `_edited`; do not patch the raw output in place.
- When a rerun changes the underlying source dataset materially, preserve the prior artifact
  set and write the new run under a distinct name or directory rather than clobbering the
  earlier reference set.
- Preserve section maps and vars files as tracked JSON where they are part of the workflow.
  They are necessary for later historical comparison, provenance review, and regression
  analysis.

This matters because later prompt, model, or source changes can otherwise erase the exact
boundary decisions and structured handoff state that made a prior run reviewable.

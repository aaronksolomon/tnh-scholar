---
title: "Pipeline Walkthrough Draft"
description: "User-facing draft walkthrough for processing OCR-scanned journal text with tnh-gen and related TNH Scholar CLI tools."
owner: ""
author: "OpenAI Codex"
status: draft
created: "2026-05-04"
updated: "2026-05-04"
---
# Pipeline Walkthrough Draft

This walkthrough shows a complete, bounded `tnh-gen` workflow on a real OCR-scanned Buddhist journal article. It is written as a user-facing guide: what the task is, which tools are used, what each stage produces, and what the current workflow still makes harder than it should be.

The example article is:

- *Vũ-trụ-quan Phật học*
- author: Thạc-Đức
- journal: *Phật Giáo Việt Nam*
- issue: 17–18
- year: 1957

Repo source files:

- `tests/golden/journal-pipeline/source.txt`
- `tests/golden/journal-pipeline/images/`

The goal is to turn one raw OCR article into:

- a section map
- cleaned section text
- readable English translation per section
- reviewable artifacts at every stage

## What This Workflow Demonstrates

This pipeline is a good fit for `tnh-gen` because it shows three distinct kinds of work:

1. structure discovery
2. OCR cleanup
3. context-aware translation

It also shows the current working model of the system:

- use deterministic CLI tools for file preparation
- use `tnh-gen` for bounded prompt execution
- keep every stage explicit and inspectable
- pass artifacts forward rather than hiding steps inside one large automation loop

## Tools Used

This walkthrough uses two CLI tools from the repo:

- `tnh-lines`
  Creates numbered text for sectioning, or removes numbering again.
- `tnh-gen`
  Runs a prompt against a file and writes a result artifact.

All prompt runs in this walkthrough assume the repository prompt workspace:

```bash
--prompt-dir ./tnh-prompts
```

## The Processing Stages

The article moves through six stages:

```text
plain OCR source
  -> numbered source
  -> section JSON
  -> numbered section slice
  -> cleaned plain-text section
  -> translated English section
```

This is intentionally explicit. The section JSON does not automatically trigger later runs. A person can inspect the section map first, then choose the next step.

## Stage 1: Number the Source

Sectioning prompts expect numbered input in `N:LINE` form.

```bash
poetry run tnh-lines number \
  tests/golden/journal-pipeline/source.txt \
  tests/golden/journal-pipeline/walkthrough/clean_translate/source_numbered_walkthrough.txt
```

Output:

- `tests/golden/journal-pipeline/walkthrough/clean_translate/source_numbered_walkthrough.txt`

Sample:

```text
1:VŨ-TRỤ-QUAN
2:PHAT-HOC
3:THẠC - ĐỨC
4:Vào thời đại của đức Phật, vấn đề nguyên lý của vạn vật là một vấn-
5:đề rất được chú trọng trong tư tưởng-giới Ấn Độ. Kinh Phạm-Động có
```

## Stage 2: Section the Article

`default_section` identifies contiguous sections and produces document-level context.

```bash
tnh-gen run \
  --prompt-dir ./tnh-prompts \
  --prompt default_section \
  --input-file tests/golden/journal-pipeline/walkthrough/clean_translate/source_numbered_walkthrough.txt \
  --var source_language=Vietnamese \
  --var target_section_count=4 \
  --var target_lines_per_section=36 \
  --var document_metadata='title: Vũ-trụ-quan Phật học\nauthor: Thạc-Đức\njournal: Phật Giáo Việt Nam\nissue: 17-18\nyear: 1957' \
  --output-file tests/golden/journal-pipeline/walkthrough/clean_translate/sections_gpt54.json
```

Output:

- `tests/golden/journal-pipeline/walkthrough/clean_translate/sections_gpt54.json`
- `tests/golden/journal-pipeline/walkthrough/clean_translate/sections_gpt54.json.provenance.yaml`

Sample:

```json
{
  "sections": [
    {
      "start_line": 1,
      "end_line": 48,
      "title": "Bối cảnh tư tưởng Ấn Độ và lập trường phê bình của Phật giáo"
    },
    {
      "start_line": 49,
      "end_line": 93,
      "title": "Thế giới nhân duyên và nguyên lý duyên khởi"
    }
  ],
  "document_summary": "..."
}
```

In the current walkthrough run, the full source was split into four contiguous sections covering the entire article.

## Stage 3: Extract a Section Slice

Read the section boundaries from the JSON and extract the range you want to work on next. For the first section:

```bash
sed -n '1,48p' \
  tests/golden/journal-pipeline/walkthrough/clean_translate/source_numbered_walkthrough.txt \
  > tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_numbered.txt
```

Output:

- `tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_numbered.txt`

Sample:

```text
1:VŨ-TRỤ-QUAN
2:PHAT-HOC
3:THẠC - ĐỨC
4:Vào thời đại của đức Phật, vấn đề nguyên lý của vạn vật là một vấn-
```

This is the current manual handoff point in the workflow. It keeps the section choice visible and reviewable.

## Stage 4: Convert Back to Plain Text

Cleaning and section-level translation work better on plain text than on numbered lines.

```bash
poetry run tnh-lines unnumber \
  tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_numbered.txt \
  tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_raw.txt
```

Output:

- `tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_raw.txt`

## Stage 5: Clean the OCR Text

`default_clean` corrects OCR damage while keeping the text faithful.

```bash
tnh-gen run \
  --prompt-dir ./tnh-prompts \
  --prompt default_clean \
  --input-file tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_raw.txt \
  --vars tests/golden/journal-pipeline/walkthrough/clean_translate/clean_vars.json \
  --output-file tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_cleaned.txt
```

Output:

- `tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_cleaned.txt`

Sample:

```text
VŨ-TRỤ-QUAN
PHẬT-HỌC
THẠC-ĐỨC

Vào thời đại của đức Phật, vấn đề nguyên lý của vạn vật là một vấn đề rất được chú trọng trong tư tưởng giới Ấn Độ.
```

At this stage the output is plain readable Vietnamese prose, with OCR noise reduced and page artifacts removed.

## Stage 6: Translate the Cleaned Section

`translate_journal_section_en` uses the cleaned section together with context taken from the sectioning JSON.

```bash
tnh-gen run \
  --prompt-dir ./tnh-prompts \
  --prompt translate_journal_section_en \
  --input-file tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_cleaned.txt \
  --vars tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_journal_translate_vars.json \
  --output-file tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_translated_journal_en.txt
```

Output:

- `tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_translated_journal_en.txt`

Sample:

```text
The Indian Intellectual Context and the Critical Stance of Buddhism

In the time of the Buddha, the question of the underlying principle of all things was one to which Indian thinkers gave great attention.
```

The same pattern can then be repeated for the remaining sections.

## What Appears in the Terminal

During a run, the terminal is usually quiet while the model call is in flight.

On success:

- the result content prints to `stdout`
- if `--output-file` is used, `stderr` prints: `Wrote output to <path>`

On failure:

- an error message is shown
- a trace ID is emitted for debugging

This means the output file is the primary artifact, while terminal output confirms what happened and where the result was written.

## Expected Artifact Layout

This walkthrough produces a clear local artifact chain:

```text
tests/golden/journal-pipeline/walkthrough/clean_translate/
├── source_numbered_walkthrough.txt
├── sections_gpt54.json
├── sections_gpt54.json.provenance.yaml
├── section_01_numbered.txt
├── section_01_raw.txt
├── section_01_cleaned.txt
├── section_01_journal_translate_vars.json
├── section_01_translated_journal_en.txt
├── section_04_numbered.txt
├── section_04_raw.txt
├── section_04_cleaned.txt
├── section_04_journal_translate_vars.json
└── section_04_translated_journal_en.txt
```

These files are useful for review, regression checking, and future prompt refinement.

## Scope of This Walkthrough

This guide is intentionally limited to a human-operated workflow.

It does not attempt to:

- automatically turn section JSON into later runs
- hide file preparation inside one command
- build a full orchestration loop

Instead, it shows the current strong use case:

- a person can run the steps
- inspect the outputs
- adjust prompts or variables
- continue section by section

## Planned Improvements

The current workflow is usable, but there are still clear improvements to make:

- `--vars` is still JSON-only, which is awkward for metadata-heavy runs
- section extraction from JSON is still a manual step
- long-running `tnh-gen` calls do not yet show progress feedback
- `target_lines_per_section` is a useful heuristic, but it is still a manual input
- the new `tnh-lines` entry point should be installed into the virtual environment so `poetry run` no longer warns about an uninstalled script entry

## Summary

This pipeline shows `tnh-gen` doing real work on a real document:

- discover structure
- produce reusable section metadata
- clean OCR text
- translate bounded sections into readable English

The result is not a black-box one-command pipeline. It is a clear, staged workflow with reviewable artifacts, which makes it a strong teaching example and a practical prototype for further refinement.

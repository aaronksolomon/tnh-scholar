---
title: "tnh-gen Walkthrough"
description: "A walkthrough of tnh-gen using small examples first, then a real journal workflow with actual commands, artifacts, and sample output."
owner: ""
author: "OpenAI Codex"
status: current
created: "2026-05-03"
updated: "2026-05-04"
---
# tnh-gen Walkthrough

`tnh-gen` runs a prompt against a file and writes the result to an output file. This walkthrough shows how that works — starting with the smallest useful examples, then moving to a real multi-step journal workflow.

For the older pipeline-oriented reference, keep [Pipeline Walkthrough](/user-guide/pipeline-walkthrough.md) open beside this one.

## The Basic Command Shape

Most runs look like this:

```bash
tnh-gen run \
  --prompt-dir ./tnh-prompts \
  --prompt <prompt-key> \
  --input-file <input-file> \
  [--vars <vars.json>] \
  [--var key=value] \
  --output-file <result-path>
```

`--output-file` is where the result lands. That file is what you inspect, keep, diff, or feed into the next step.

## What You See in the Terminal

While `tnh-gen` is waiting for the model, the terminal is silent — no progress bar, no spinning cursor. For short inputs this is usually fine. For longer documents, expect 10–30 seconds of nothing.

When the run finishes:

- the result text (or JSON) prints to stdout
- a confirmation prints to stderr: `Wrote output to <path>`

If the run fails, you get an error message and a trace ID instead.

!!! note "Progress feedback"
    A progress indicator for long-running calls is planned. For now, if it feels like the run has hung, it probably hasn't — it's just waiting on the model.

## Sample 1: Small Vietnamese Sectioning Run

The smallest maintained example in the repo. Runs a JSON sectioning prompt on a short numbered Vietnamese input.

**Input**: `tests/golden/json-prompts/numbered-short-vi.txt`

```bash
tnh-gen run \
  --prompt-dir ./tnh-prompts \
  --prompt default_section \
  --input-file tests/golden/json-prompts/numbered-short-vi.txt \
  --var source_language=Vietnamese \
  --var target_section_count=3 \
  --var target_lines_per_section=4 \
  --var document_metadata='title: Ví dụ ngắn\nauthor: Demo' \
  --output-file tests/golden/json-prompts/default-section.default-current.output.json
```

The input is plain numbered text in `N:LINE` format. The model returns a JSON file with section boundaries, titles, a document summary, and key concepts.

**Sample output** (`tests/golden/json-prompts/default-section.default-current.output.json`):

```json
{
  "language": "vi",
  "sections": [
    {
      "start_line": 1,
      "end_line": 3,
      "title": "Mở đầu an trú thân tâm",
      "title_en": "Opening: Returning to Body and Mind"
    }
  ],
  "document_summary": "...",
  "key_concepts": ["hơi thở chánh niệm", "tương tức", "từ bi"]
}
```

Alongside the output file, `tnh-gen` writes a provenance sidecar (`*.provenance.yaml`) recording the model used, token counts, prompt fingerprint, and timestamp.

## Sample 2: Small English Sectioning Run

The same prompt on a short English input.

**Input**: `tests/golden/json-prompts/numbered-short-en.txt`

```bash
tnh-gen run \
  --prompt-dir ./tnh-prompts \
  --prompt generate_sections_en \
  --input-file tests/golden/json-prompts/numbered-short-en.txt \
  --var target_section_count=3 \
  --output-file tests/golden/json-prompts/generate-sections-en.default-current.output.json
```

**Sample output**: `tests/golden/json-prompts/generate-sections-en.default-current.output.json`

## What the JSON Output Is For

The sectioning output gives you a structured map of the document: line ranges, titles in the source language and English, a summary, key concepts. You can read it directly, diff it across runs, or use the line ranges to pull sections out for follow-on prompts.

`tnh-gen` does not read this JSON and automatically continue to the next step. Each run is its own explicit command. That keeps every step visible and easy to review.

## Full Workflow Demo: A Journal Article

The repo includes a real OCR scan — *Vũ-trụ-quan Phật học* by Thạc-Đức, from *Phật Giáo Việt Nam* (1957). Source files are in `tests/golden/journal-pipeline/`.

### Step 1: Prepare a Numbered Source File

`default_section` expects `N:LINE` input. For a normal plain-text source file, use the repo's `tnh-lines` helper first:

```bash
poetry run tnh-lines number \
  tests/golden/journal-pipeline/source.txt \
  tests/golden/journal-pipeline/walkthrough/clean_translate/source_numbered_walkthrough.txt
```

**Output**: `tests/golden/journal-pipeline/walkthrough/clean_translate/source_numbered_walkthrough.txt`

```text
1:VŨ-TRỤ-QUAN
2:PHAT-HOC
3:THẠC - ĐỨC
4:Vào thời đại của đức Phật, vấn đề nguyên lý của vạn vật là một vấn-
5:đề rất được chú trọng trong tư tưởng-giới Ấn Độ. Kinh Phạm-Động có
```

This is a better real-world input path than hand-maintaining numbered fixtures. The model sees stable line references; the human still works from ordinary text files.

### Step 2: Section the Document

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

**Output**: `tests/golden/journal-pipeline/walkthrough/clean_translate/sections_gpt54.json`

```json
{
  "sections": [
    {
      "start_line": 1,
      "end_line": 48,
      "title": "Bối cảnh tư tưởng Ấn Độ và lập trường phê bình của Phật giáo",
      "title_en": "Indian Intellectual Context and the Buddhist Critical Position"
    },
    {
      "start_line": 49,
      "end_line": 93,
      "title": "Thế giới nhân duyên và nguyên lý duyên khởi",
      "title_en": "The Conditioned World and the Principle of Dependent Origination"
    }
  ],
  "document_summary": "..."
}
```

Even without doing anything else, this output is useful. A human reviewer can read the section titles, summaries, and ranges, then decide which parts to work with next.

### Step 3: Extract the Numbered Section Slice

The JSON does not trigger the next prompts. Today, you read the section ranges and extract the segment you want explicitly. For the first section:

```bash
sed -n '1,48p' \
  tests/golden/journal-pipeline/walkthrough/clean_translate/source_numbered_walkthrough.txt \
  > tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_numbered.txt
```

**Output**: `tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_numbered.txt`

```text
1:VŨ-TRỤ-QUAN
2:PHAT-HOC
3:THẠC - ĐỨC
4:Vào thời đại của đức Phật, vấn đề nguyên lý của vạn vật là một vấn-
```

This is the current manual handoff. It is intentionally visible. You can see exactly which section range is being moved into the next step.

### Step 4: Convert the Slice Back to Plain Text

Cleaning and translation prompts work better on normal prose, not numbered line references. Strip the numbering before the clean step:

```bash
poetry run tnh-lines unnumber \
  tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_numbered.txt \
  tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_raw.txt
```

**Output**: `tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_raw.txt`

```text
VŨ-TRỤ-QUAN
PHAT-HOC
THẠC - ĐỨC
Vào thời đại của đức Phật, vấn đề nguyên lý của vạn vật là một vấn-
```

The flow is now cleaner:

- plain source text
- numbered working copy for sectioning
- numbered section slice for explicit handoff
- plain section text for cleaning and translation

### Step 4.5: Carry Forward Metadata and Summary from the Sectioning Output

The sectioning artifact is not only a split map. It also gives you context you can reuse later:

- `document_summary`
- `key_concepts`
- per-section `title`
- per-section `summary`
- document metadata fields

For this walkthrough, those values were pulled out of `sections_gpt54.json` and written into explicit vars files for follow-on translation runs:

- `tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_journal_translate_vars.json`
- `tests/golden/journal-pipeline/walkthrough/clean_translate/section_04_journal_translate_vars.json`

**Sample vars file** (`section_01_journal_translate_vars.json`):

```json
{
  "source_language": "Vietnamese",
  "target_language": "English",
  "section_title": "Bối cảnh tư tưởng Ấn Độ và lập trường phê bình của Phật giáo",
  "document_summary": "...",
  "section_summary": "...",
  "document_key_concepts": "Vũ-trụ-quan Phật học; Nhân duyên; Duyên khởi; Nhân quả; ...",
  "document_metadata": "title: Vũ-trụ-quan Phật học\nauthor: Thạc-Đức\njournal: Phật Giáo Việt Nam\nissue: 17-18\nyear: 1957"
}
```

This is the current handoff pattern:

- JSON sectioning output is generated once
- a human or deterministic helper pulls out the needed context
- the next prompt receives that context explicitly through `--vars`

That is more manual than a hidden automation loop, but it is clearer for teaching and review.

One simple inspection command is:

```bash
jq '.sections[] | {start_line, end_line, title, summary}' \
  tests/golden/journal-pipeline/walkthrough/clean_translate/sections_gpt54.json
```

That does not automate the next step. It makes the handoff visible. Today, that visibility is a feature.

### Step 5: Clean a Section

```bash
tnh-gen run \
  --prompt-dir ./tnh-prompts \
  --prompt default_clean \
  --input-file tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_raw.txt \
  --vars tests/golden/journal-pipeline/walkthrough/clean_translate/clean_vars.json \
  --output-file tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_cleaned.txt
```

**Output**: `tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_cleaned.txt`

```
VŨ-TRỤ-QUAN
PHẬT-HỌC
THẠC-ĐỨC

Vào thời đại của đức Phật, vấn đề nguyên lý của vạn vật là một vấn đề rất được
chú trọng trong tư tưởng giới Ấn Độ.
```

Plain readable Vietnamese with OCR errors corrected. No JSON — you can read it directly.

### Step 6: Translate the Cleaned Section

For this journal workflow, a dedicated prompt is clearer than reusing a narrower or badly named surface. The walkthrough now uses:

- `tnh-prompts/translate_journal_section_en.md`

This prompt is written for cleaned journal prose and expects the document and section context assembled from the earlier sectioning JSON.

```bash
tnh-gen run \
  --prompt-dir ./tnh-prompts \
  --prompt translate_journal_section_en \
  --input-file tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_cleaned.txt \
  --vars tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_journal_translate_vars.json \
  --output-file tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_translated_journal_en.txt
```

**Output**: `tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_translated_journal_en.txt`

```
The Indian Intellectual Context and the Critical Stance of Buddhism

In the time of the Buddha, the question of the underlying principle of all things
was one to which Indian thinkers gave great attention. The Brahmajāla Sutta
records as many as sixty-two different explanations advanced by the Indian
philosophical schools of that age.
```

Each step — sectioning, cleaning, translating — is a separate run with a visible input, a visible output, and a provenance sidecar. Nothing is hidden between steps.

## What Works Well Today

`tnh-gen` is ready to use for:

- sectioning a document into a reviewable JSON map
- OCR cleanup of raw scanned text
- section-by-section translation
- any workflow where each step is a separate, inspectable run

## Known Friction Points

These rough edges are real and documented honestly:

- multiline metadata is cumbersome to pass inline; use `--vars` with a JSON file for multi-field metadata
- `target_section_count` must still be chosen explicitly, and `target_lines_per_section` is still a manual heuristic when used
- extracting line ranges from the sections JSON into individual text files is currently a manual step
- turning the sectioning JSON into follow-on vars is still a visible assembly step
- the terminal is silent while the model is working — there is no progress indicator for long runs

## What to Read Next

1. `tests/golden/json-prompts/README.md` — the maintained JSON prompt examples and golden outputs
2. [Journal Walkthrough Review](/user-guide/journal-walkthrough-review.md)
3. [Pipeline Walkthrough](/user-guide/pipeline-walkthrough.md)
4. [Prompt System](/user-guide/prompt-system.md)

## Related Docs

- [Journal Walkthrough Review](/user-guide/journal-walkthrough-review.md)
- [Pipeline Walkthrough](/user-guide/pipeline-walkthrough.md)
- [Prompt System](/user-guide/prompt-system.md)
- [Best Practices](/user-guide/best-practices.md)
- [tnh-gen CLI Reference](/cli-reference/tnh-gen.md)

---
title: "tnh-gen GPT-5 Structured Output Eval — May 2026"
description: "Concise findings from live golden evaluation of maintained tnh-gen prompts for walkthrough viability, human usability, artifact-backed real journal runs, and GPT-5-family prompt tuning."
owner: "aaronksolomon"
author: "OpenAI Codex"
status: current
created: "2026-05-03"
---
# tnh-gen GPT-5 Structured Output Eval — May 2026

Short report from live golden evaluation of the maintained `tnh-gen` prompt slice against GPT-5-family models, focused on walkthrough viability, bounded human use, artifact-backed journal runs, and whether `tnh-gen` can actually do maintained tasks cleanly enough to support examples and follow-on design.

## Scope

Prompts evaluated in this loop:

- `default_section`
- `section_by_break`
- `generate_sections_en`
- `generate_sections_multi_lang`
- `default_clean`
- `translate_section_dt_en`
- `translate_json`

Models evaluated:

- `gpt-5-mini`
- `gpt-5.4`
- `gpt-5` (translation spot check only)

Primary evaluation goals:

- verify that maintained JSON prompts can complete small real runs successfully
- check whether the prompt outputs are usable for walkthrough examples
- compare GPT-5-family behavior where prompt/model/schema changes might improve real outcomes
- note operator friction when a human would realistically try to run these commands

## Findings

### 1. Sectioning is viable on `gpt-5.4`

The maintained sectioning prompts were structurally successful on GPT-5-family models, but `gpt-5-mini` still allowed semantic misses on line coverage for some cases.

`gpt-5.4` materially improved the sectioning path:

- `generate_sections_en` produced contiguous full-line coverage
- `section_by_break` produced contiguous full-line coverage
- `default_section` and `generate_sections_multi_lang` were also usable

Resulting decision:

- keep the maintained sectioning prompt family on `gpt-5.4` by default for now

### 2. Prompt wording still matters even with structured output

Line coverage was previously expressed mainly as prompt instruction rather than enforced strongly enough by the acceptance surface.

Tightening the sectioning prompts to require:

- first section starts at line 1
- each next section starts exactly one line after the previous section ends
- final section ends at the final input line

helped make the successful default-model path more legible and robust.

### 3. `translate_json` is not a good maintained `tnh-gen` walkthrough or prompt-catalog example in its current form

`translate_json` remained semantically unsuccessful across:

- `gpt-5-mini`
- `gpt-5.4`
- `gpt-5`

Observed failure mode:

- the run succeeds structurally
- the model returns the original English JSON payload unchanged

This persisted even after tightening prompt wording.

Interpretation:

- this is not just a model-capacity issue
- this is a poor fit between the prompt goal and the current `tnh-gen` artifact-contract surface
- broad "any JSON" structural acceptance is too weak to prove translation happened

Resulting decision:

- remove `translate_json` from the maintained prompt workspace
- if JSON translation is needed later, design a different pathway rather than treating this prompt as a healthy maintained contract

### 4. Real journal clean and section-translation runs are now credible enough to serve as walkthrough sample artifacts

A real-world sectioning pass was run against `tests/golden/journal-pipeline/source_numbered.txt`, with the result written as an artifact:

- `tests/golden/journal-pipeline/walkthrough/clean_translate/sections_gpt54.json`

That run produced four usable sections spanning the full 146-line source. Two representative sections were then processed through a file-based clean then translate loop, again writing artifacts at each stage:

- raw extracted section text
- cleaned section text via `default_clean`
- translated section text via `translate_section_dt_en`

Representative outputs:

- `tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_cleaned.txt`
- `tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_translated_dt_en.txt`
- `tests/golden/journal-pipeline/walkthrough/clean_translate/section_04_cleaned.txt`
- `tests/golden/journal-pipeline/walkthrough/clean_translate/section_04_translated_dt_en.txt`

Observed result:

- the clean stage is doing useful real work on journal prose, not just cosmetic rewriting
- the section translation surface is more plausible for walkthrough use than `default_line_translate`
- the artifact chain is reviewable and reusable for follow-on prompt iteration

Interpretation:

- for this class of journal text, a section-first handoff followed by plain-text clean and plain-text section translation is a more believable human workflow than line-level translation
- `default_line_translate` should be viewed as a narrower control-loop surface, not the main journal walkthrough surface

## UI/UX Notes

The human operator path is still awkward for richer sectioning prompts.

Main friction observed:

- multiline structured metadata passed inline through `--var metadata=...`
- repeated flags and long commands for otherwise small live checks
- vars files are much more believable than large inline payloads, but JSON-only `--vars` is still less friendly than it should be for common metadata-heavy workflows

This is usable for bounded engineering evaluation, but it is not an especially friendly human CLI surface for routine operators.

The sectioning prompts and the journal clean→translate slice are now viable enough for walkthrough-oriented use; the remaining UX issue is mostly variable-entry ergonomics rather than core runtime instability.

## Resulting Actions

- Keep maintained sectioning prompts on `gpt-5.4` defaults.
- Keep `default_clean` and the section translation surface on `gpt-5.4` defaults for now.
- Remove `translate_json` from maintained prompts.
- Treat future JSON-translation support as separate design work, likely involving deterministic JSON traversal plus targeted string translation rather than a broad "translate arbitrary JSON" prompt contract.
- Treat file-driven vars and saved output artifacts as the realistic operator path for richer multi-step walkthroughs; revisit broader YAML vars / metadata ergonomics later as separate UX work.

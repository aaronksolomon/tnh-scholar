---
title: "JSON Prompt Golden Scaffolds"
description: "Small live-golden inputs for maintained JSON prompts exercised through tnh-gen."
status: current
created: "2026-05-02"
---

# JSON Prompt Golden Scaffolds

This directory holds small live-golden inputs for the maintained JSON prompts:

- `default_section`
- `section_by_break`
- `generate_sections_en`
- `generate_sections_multi_lang`
- `translate_json`

These are intentionally small and cheap. They are meant to validate:

- prompt discovery through `--prompt-dir`
- schema resolution and runtime JSON validation
- basic prompt-shape viability before running the larger journal pipeline

## Inputs

- `numbered-short-en.txt`
  - English numbered text for `generate_sections_en`
- `numbered-short-vi.txt`
  - Vietnamese numbered text for `default_section`, `section_by_break`, and `generate_sections_multi_lang`
- `translate-json-input.json`
  - Small nested JSON document for `translate_json`

## Expected Outputs

Generated golden outputs should be written alongside these inputs once the live runs are captured. Typical filenames:

- `default-section.output.json`
- `section-by-break.output.json`
- `generate-sections-en.output.json`
- `generate-sections-multi-lang.output.json`
- `translate-json.output.json`

Each JSON output should also produce a provenance sidecar:

- `<output>.provenance.yaml`

These generated outputs are intentionally local-only and ignored by git. The
tracked fixture in this directory is the input scaffold, including
`translate-json-input.json`.

## Prompt Source

These goldens are intended to run against the tracked repo-local prompt workspace:

```bash
--prompt-dir ./tnh-prompts
```

## Notes

- This scaffold is for structural and live-contract validation, not semantic prompt-quality review.
- Broader prompt simplification and quality cleanup remain deferred under `TODO.md` in the `Prompt Catalog Safety` area.

## Handoff State

Current branch setup for the next agent:

- The repo-local prompt mirror now lives at `./tnh-prompts`.
- The built-in JSON schemas for this prompt family are now present under `src/tnh_scholar/runtime_assets/schemas/prompt-contracts/tnh/`.
- Prompt catalog health is expected to be checked against the current branch source, for example:

```bash
set -a
source /Users/phapman/Desktop/Projects/tnh-scholar/.env >/dev/null 2>&1
set +a

PYTHONPATH=./src \
  /Users/phapman/Desktop/Projects/tnh-scholar/.venv/bin/tnh-gen \
  --prompt-dir ./tnh-prompts \
  config show --catalog-health
```

- The next intended live runs are the five small JSON prompt checks in this directory.
- The first preliminary live attempts were blocked by the active budget config still resolving to `$0.10`, so the next agent should address budget configuration before retrying.

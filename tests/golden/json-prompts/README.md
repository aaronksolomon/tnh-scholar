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

These are intentionally small and cheap. They are meant to validate:

- prompt discovery through the default repo-local workspace
- schema resolution and runtime JSON validation
- basic prompt-shape viability before running the larger journal pipeline

## Inputs

- `numbered-short-en.txt`
  - English numbered text for `generate_sections_en`
- `numbered-short-vi.txt`
  - Vietnamese numbered text for `default_section`, `section_by_break`, and `generate_sections_multi_lang`
- `translate-json-input.json`
  - Retained as a possible future design fixture for JSON-translation work, not as a maintained `tnh-gen` golden prompt

## Local Output Conventions

Generated golden outputs may be written alongside these inputs during live runs.
Typical filenames:

- `default-section.output.json`
- `section-by-break.output.json`
- `generate-sections-en.output.json`
- `generate-sections-multi-lang.output.json`

Each JSON output should also produce a provenance sidecar:

- `<output>.provenance.yaml`

The current maintained live-golden outputs in this directory are tracked in git
as comparison artifacts, including model-suffixed variants produced during the
GPT-5-family evaluation loop. Additional local reruns may still create
untracked scratch outputs alongside them.

## Prompt Source

These goldens are intended to run from the repo root against the default
repo-local `./tnh-prompts/` workspace.

## Notes

- This scaffold is for structural and live-contract validation, not semantic prompt-quality review.
- Broader prompt simplification and quality cleanup remain deferred under `TODO.md` in the `Prompt Catalog Safety` area.
- `translate_json` was removed from the maintained prompt workspace after GPT-5-family evaluation showed repeated semantic no-op behavior despite structural success.

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
  config show --catalog-health
```

- The next intended live runs are the four maintained sectioning checks in this directory.
- The first preliminary live attempts in this workstream were blocked under the earlier `$0.10` default. The current runtime default is now `$0.30`, but operators can still raise it explicitly when a specific run needs more headroom.

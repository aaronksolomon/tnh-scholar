---
title: "tnh-gen UX Directions and Issues — May 2026"
description: "Observed UX friction and improvement directions from the journal pipeline walkthrough, for a careful human operator running tnh-gen at the CLI."
owner: "aaronksolomon"
author: ""
status: current
created: "2026-05-04"
---

# tnh-gen UX Directions and Issues — May 2026

These notes come from walking a human operator through the full journal pipeline — section, clean, translate — against a real OCR article. The audience is a careful, non-developer user working at the command line: someone who knows their domain, is comfortable with a terminal, but should not need to write scripts or inspect JSON by hand to do normal work.

Each item is grounded in a specific friction point from the walkthrough. They are ordered roughly from most disruptive to most minor.

---

## 1. Section extraction requires manual line lookup

**What happens now:** After `default_section` produces `sections.json`, the user
reads out `start_line` and `end_line` values by eye, then runs:

```bash
sed -n '1,48p' source_numbered.txt > section_01_numbered.txt
```

This is a shell-scripting step embedded in what should be a single-tool workflow.
The user has to know `sed`, read JSON, and not mistype the line numbers.

**Direction:** A `tnh-lines slice` command (or `tnh-gen extract-section`) that takes
the sections file and an index and produces the slice directly:

```bash
tnh-lines slice sections.json 1 source_numbered.txt section_01_numbered.txt
```

The sections JSON is already structured for this — every entry has `start_line` and
`end_line`. The extraction logic is trivial; it just needs a home in the toolchain.

---

## 2. Translation vars file must be constructed by hand

**What happens now:** `translate_journal_section_en` needs a vars file carrying
document summary, section title, section summary, key concepts, and metadata — all
of which already exist in `sections.json`. The user has to manually copy and reformat
these fields into `section_01_journal_translate_vars.json`.

This is the most invisible step in the pipeline: the sections JSON already contains
everything the translate call needs, but there is no command that bridges them.

**Direction:** A `tnh-gen build-vars` command that produces a ready-to-use vars file
from a sections JSON entry:

```bash
tnh-gen build-vars sections.json --section 1 > section_01_translate_vars.json
```

Alternatively, a `--section-context sections.json:1` flag on `tnh-gen run` that
injects the relevant context directly without a separate file.

This gap currently makes the translate stage look more complex than it is and will
be a real barrier for users who are not comfortable with JSON.

---

## 3. No progress feedback during model calls

**What happens now:** The terminal is completely silent while a model call is in
flight — typically 10–30 seconds for a clean or translate call, longer for sectioning.
There is no indication that anything is happening.

This is disorienting. Users try pressing Enter to see if the call is still live,
or abort and retry unnecessarily.

**Direction:** At minimum, a spinner and elapsed time on `stderr`. Optionally a
brief status line showing which prompt is running and what file it is reading.
This does not need to be rich; it just needs to confirm that the process is alive.

---

## 4. Two translation prompts, no clear guidance on which to use

**What happens now:** Two translation paths exist:

- `default_line_translate` — works on numbered `N:LINE` output, produces numbered output
- `translate_journal_section_en` — works on plain-text cleaned sections

The `tnh-gen list` output does not distinguish them. A user who picks the wrong one
gets confusing output without a helpful error.

**Direction:** `tnh-gen list` output should include a one-line description for each
prompt that indicates expected input format (numbered vs. plain text) and the
primary use case. Until that exists, the walkthrough documentation needs to
explicitly name the translation path for each workflow.

Longer term, consider consolidating these under a single `translate` prompt with
an `--input-format` switch, or deprecating the numbered-line path in favor of the
section-based one.

---

## 5. `--vars` is JSON-only; metadata entry is awkward

**What happens now:** Simple variable sets — three strings for a clean call — must
be expressed as a JSON file:

```json
{
  "source_language": "Vietnamese",
  "publication_name": "Phật Giáo Việt Nam",
  "publisher_mark": "Tư Viện Huệ Quang"
}
```

Writing a JSON file to pass three strings is disproportionate effort and a source
of quoting and encoding errors (especially with Vietnamese diacritics on some
systems).

**Direction:** Support YAML vars files as an alternative (lower quoting friction
for text with special characters). Alternatively, accept multiple `--var` flags
for common cases and reserve `--vars` for the richer context objects that
translation actually needs.

---

## 6. Budget cap is not surfaced before a run

**What happens now:** The current default budget is `$0.30` per run. Earlier pipeline
attempts were silently cut short at `$0.10`. A full four-section journal pipeline
can approach or exceed the default cap depending on model and prompt verbosity. The
user discovers this at failure, not before the run starts.

**Direction:** Display the active budget limit in the `tnh-gen run` startup output
(even a single line: `Budget: $0.30`). Consider a `--dry-run` or `--estimate` flag
that calls the tokenizer and reports approximate cost before committing to a live
call. For multi-section workflows, a warning when the estimated total across planned
calls would exceed budget would be especially useful.

---

## 7. `tnh-lines --force` required to overwrite existing files

**What happens now:** `tnh-lines number` and `tnh-lines unnumber` require a `--force`
flag when the output file already exists. This is non-obvious on first encounter and
breaks re-running a pipeline without modification.

**Direction:** Default to overwriting, consistent with standard Unix tool behavior.
If a safer default is preferred, prompt interactively when a terminal is attached
rather than requiring a flag.

---

## 8. No batch mode for multi-section runs

**What happens now:** Processing four sections requires four separate invocations or
a shell `for` loop. Neither is ergonomic for a non-developer operator. The pipeline
pattern (iterate sections.json, apply prompt, write output) is repetitive and
mechanical.

**Direction:** A `--batch-from sections.json` mode on `tnh-gen run` that iterates
the section list and runs the prompt for each entry, writing named output files.
The key design question is how to pass per-section context (titles, summaries) as
vars within a batch — probably resolved by combining with the `build-vars` direction
above.

This is a medium-term direction; the single-call workflow is reasonable for now and
keeps each step visible and reviewable.

---

## 9. Provenance sidecars appear unexpectedly in working directories

**What happens now:** Every structured output produces a `.provenance.yaml` sidecar
alongside the output file:

```
sections.json
sections.json.provenance.yaml   ← appears automatically
```

This is the right behavior for auditability, but it surprises users who are watching
the directory. In a working directory with four sections, eight additional files
appear.

**Direction:** A `.provenance/` subdirectory would keep the working tree readable
without losing the provenance trail. Alternatively, a `--provenance-dir` flag to
redirect sidecars. No change is urgent, but this becomes more noticeable as
pipeline depth increases.

---

## Summary

The pipeline works. A careful human operator can run it end to end and produce
good output. The friction points above are real, but none of them are blockers for
current use.

Priority order for improvement:

| # | Item | Impact | Effort |
|---|------|--------|--------|
| 1 | Section extraction command | High | Low |
| 2 | Vars file from sections JSON | High | Low |
| 3 | Progress feedback | High | Low |
| 4 | Prompt list descriptions | Medium | Low |
| 5 | Budget surfacing | Medium | Low |
| 6 | Two translation prompts | Medium | Medium |
| 7 | YAML vars support | Medium | Medium |
| 8 | `--force` default | Low | Low |
| 9 | Batch mode | Medium | High |
| 10 | Provenance sidecar location | Low | Medium |

Items 1–3 are the clearest quick wins: they remove real barriers for a non-developer
operator without requiring any prompt or model changes.

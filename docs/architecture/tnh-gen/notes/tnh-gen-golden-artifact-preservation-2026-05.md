---
title: "tnh-gen Golden Artifact Preservation Note — May 2026"
description: "Short operations note from the journal pipeline rerun on preserving structured artifacts, separating reviewed edits from raw outputs, and avoiding rerun clobber."
owner: "aaronksolomon"
author: "OpenAI Codex"
status: current
created: "2026-05-07"
---
# tnh-gen Golden Artifact Preservation Note — May 2026

Short operations note from the real-world journal case-study rerun.

## Context

The journal pipeline golden was first run on an incomplete four-page source. Later review
showed the article actually continued onto a fifth page. Rebuilding the source and rerunning
the workflow exposed an important weakness in the current testing posture: some of the most
useful workflow artifacts were local JSON files that had not been tracked cleanly enough to
support later historical comparison.

## Main Lesson

For `tnh-gen` golden work, structured outputs are not just transient helper files. They are
part of the evidence trail.

In particular:

- section maps
- reviewed section-map corrections
- vars files that carry section/document context
- preserved comparison runs with different split targets

need to survive later reruns if we want to compare prompt behavior, model behavior, and
human review interventions honestly.

## Resulting Working Rules

- Keep raw model outputs unchanged when they serve as golden evidence.
- Put human-reviewed changes in separately named artifacts such as `_corrected` or `_edited`.
- If the underlying source dataset changes materially, preserve the old artifact set and
  write the new run under a clearly distinct path such as a dated or source-scope-specific
  directory.
- Track the JSON artifacts that are operationally important to the workflow rather than
  relying on git history to reconstruct them later.
- Treat assembled user-facing `.md` documents differently from `tnh-gen` workflow artifacts:
  keep only the current canonical refined assembly, and rely on preserved source, section,
  clean, and translation artifacts to reconstruct earlier or alternate assemblies when
  needed.

## Why This Matters

Without these rules, later prompt or source improvements can erase the exact structured
handoff state of earlier runs. That makes it harder to answer questions like:

- Did the model improve, or did the source change?
- Did the section boundary move because of a better prompt, a different target count, or a
  human review correction?
- What context was actually passed into downstream translation runs?

For real-world golden evaluation, preserving that structure is part of the provenance story,
not an optional convenience.

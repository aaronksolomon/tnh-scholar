---
title: "ADR-K03: Concept Extraction and Evidence Contract"
description: "Proposes an optional passage-extraction probe with inspectable evidence and measured review effort."
owner: "aaronksolomon"
author: "Codex"
status: proposed
created: "2026-09-18"
---
# ADR-K03: Concept Extraction and Evidence Contract

Proposes a small, optional extraction probe with inspectable evidence rather than a production extraction pipeline.

## Context and Status

Proposed, narrowed 2026-09-19. First test the value of a hand-checked conceptual map through [K02](/architecture/knowledge-base/adr/adr-k02-concept-grounded-knowledge-base.md). Automatic extraction is a separate question: can the system suggest useful concept associations without routine cleanup by a second coding agent?

The [journal live test](/architecture/knowledge-base/notes/concept-extraction-live-review-2026-09-17.md) produced useful candidates but also altered quotations and reversed relations. These findings justify a small evidence check, not a complete repair/publication architecture before we know what works.

## Proposed Probe

After the initial search comparison, optionally process two or three representative passages with one prompt and one model configuration. Reuse `tnh-gen` and its structured-output/provenance facilities. Save the untouched response and a short assessment; do not build a new agent workflow.

A candidate needs only a concept key or proposed label, source/passage reference, exact supporting quote, explicit-versus-inferred marker, and brief explanation. Novel concepts remain suggestions outside the hand-checked search map. An exact quote must match stored text; if it occurs more than once, require a disambiguating location. A reviewer checks sense, negation, attribution, and relation direction. Matching text alone cannot establish support for an interpretation.

Use a small typed schema at the generation boundary when implementing the probe. Record source hash, prompt/model/settings, actual output, available usage, and validation findings. Missing fields or evidence are flagged; never silently repair the saved response.

## What We Measure

Count candidates accepted unchanged, incorrect or unsupported candidates, omitted important concepts noticed by the reviewer, and review/correction time. Include rejected candidates in the denominator. Distinguish mechanical validity from semantic correctness. A human assessment sheet is sufficient; no reviewer service or publication queue is required.

Default to one extraction attempt. If a specific repeatable defect warrants it, test one explicit repair prompt as a separate experimental condition with its cost and effect recorded. Do not implement automatic retry/repair policy in this exploration. Provider failures are reported through the existing service; uncertain paid outcomes are not blindly replayed.

The reviewer may correct entries for a later experiment, but original and corrected data must be separate and results must disclose which was used. A required Codex cleanup pass is a negative finding about extraction readiness, not a hidden successful step.

## Deferred Decisions

Automatic concept publication, confidence thresholds, review state machines, general relation schemas, canonical offset/revision frameworks, resumable jobs, and bounded repair orchestration. If extraction becomes a repeated ingestion need, design only the contracts supported by the observed failure patterns and measured review load.

## Exit

A short report with raw outputs, examples of errors, acceptance counts, cost, and reviewer effort. Decide whether to use assisted extraction, keep hand-curated concepts, or run one targeted follow-up. No production-readiness claim follows from this sample.

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


## Addendum 2026-09-29: Smoke Test and Bounded Follow-Up

The initial two or three passages are a smoke test for obvious failures, not an estimate of extraction acceptance or readiness. Report raw counts and correction effort; a severe quotation, negation, attribution, or relation-direction defect warrants stopping to investigate. A clean smoke test alone does not justify adopting assisted extraction.

If retrieval findings warrant extraction work and the smoke test is promising, optionally test 10–20 additional heterogeneous passages selected before generation. Include differing source traditions, terminology, explicit and inferred associations, negation, and ambiguous or sparse-concept passages; use multiple languages only where qualified review is available. Freeze the prompt, schema, model/configuration, and source snapshots after smoke-test adjustments. Record any subsequent revision as a separate experiment, rather than pooling it with the frozen batch.

Report candidates accepted unchanged over all candidates (including rejected ones), passage-level failures, reviewer-noticed omissions, and generation/validation failures separately. Record review minutes for every passage, correction minutes separately, available model cost, and retained usable entries. A comparable hand-curation timing sample is needed before claiming labor savings. Even this follow-up supports only a provisional decision for the sampled material, not a general acceptance rate or production readiness. Keep raw and corrected outputs separate and retain the existing prohibition on hidden repair.

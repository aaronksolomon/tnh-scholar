---
title: "ADR-K02: Concept-Grounded Knowledge Base"
description: "Proposes a source-first KB with reviewed Buddhist and Plum Village vocabularies and measurable retrieval."
owner: "aaronksolomon"
author: "Codex"
status: proposed
created: "2026-09-18"
---
# ADR-K02: Concept-Grounded Knowledge Base

Proposes a small search experiment using Buddhist and Plum Village concepts, before committing to a KB platform.

## Context and Status

Proposed, revised 2026-09-19 to narrow the exploration. This draft replaces the earlier expansive K02 proposal; it does not approve implementation. [K01](/architecture/knowledge-base/adr/adr-k01-kb-architecture-strategy.md) remains the historical direction pending acceptance. The bounded conductor loop is deferred and is not a dependency.

We want to learn whether a modest conceptual map helps people find useful passages beyond ordinary search. The adjacent `bsearch` project already provides local corpus parsing and separate keyword/semantic search. Start from its strengths, documented in the [implementation review](/architecture/knowledge-base/notes/bsearch-review-2026-09-19.md), rather than designing another complete search platform.

## Proposed Experiment

Use one fixed collection of roughly 10–15 texts or talks, 8–12 concept entries, and 12–15 real questions. Include existing Buddhist material and a small PV/TNH subset. These are caps to guide selection, not prerequisites to meet by inventing data. Start smaller if the first useful comparison needs fewer sources.

Build a hand-checked table with concept key, label/aliases, Buddhist or PV scope, brief sense note, supporting source, and optional related entry plus explanation. Preserve distinctions between traditions and periods. Similar labels do not imply equivalence; a later PV connection to an earlier text is an interpretation, not the earlier author's terminology. No exhaustive ontology or fixed predicate taxonomy is needed.

Compare the same base search with expansion off and on. Expansion means a few explicitly listed terms from the small table, not an autonomous graph traversal or LLM research loop. Keep the original query, results, and added terms visible. Search uncatalogued passages normally. If the map does not help, retain direct search and report that result.

## Minimum Records

Keep a source manifest with identifier, title, language, origin/locator, captured text hash, and available translation information. Keep exact passage text and a source-relative location. Store the concept table and a run manifest with the corpus snapshot, search/index settings, queries, and raw ranked results. A spreadsheet or versioned JSON/CSV files are sufficient for review; no review database is required.

Source identity must remain separate from generated commentary. Unsupported interpretation is labeled as such. Broken references, missing source text, and search errors are visible failures, not empty-result evidence. These are requirements for a meaningful experiment, not a full editorial governance system.

## Implementation Boundary

Prefer an isolated experiment driver around existing `bsearch` search interfaces, using a frozen corpus export and temporary indexes. Confirm a narrow integration path before committing to importing its package into TNH. SQLite FTS5 and the existing vector backend are candidates for experiment reuse, not permanent infrastructure choices. Rebuild small indexes from scratch; do not rely on the current resume path without fixing its consistency risks.

Any new TNH GenAI calls still follow [ADR-OS01](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md) and use the existing service. Apply the repository's typing rules to the few boundary records actually needed. This ADR does not require generating repositories, services, adapters, or a complete family of domain classes in advance.

## Deferred

Publication/approval state machines, immutable revision graphs, automatic invalidation, distributed execution, general graph traversal, hybrid ranking frameworks, reviewer UI, and answer synthesis. Cross-language retrieval is one optional probe if trustworthy paired material is already available, not a bilingual coverage commitment. Storage and embedding choices remain replaceable experiment settings.

## Consequences and Next Decision

Manual curation of a tiny map is deliberate: it tests the value of concepts separately from extraction quality. It cannot establish whole-corpus coverage or production reliability. The [exploration plan](/architecture/knowledge-base/design/kb-pilot-roadmap.md) defines the smallest deliverables and a stop point before further engineering. [K03](/architecture/knowledge-base/adr/adr-k03-concept-extraction-evidence-contract.md) scopes an optional extraction probe after the first search comparison.

The [Bayer case study](https://martinfowler.com/articles/reliable-llm-bayer.html) motivates traceable evidence and evaluation; it is not a requirement to reproduce its orchestration or infrastructure.

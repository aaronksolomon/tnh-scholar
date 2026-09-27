---
title: "KB Pilot Roadmap and Review Map"
description: "Review order, bounded implementation slices, and evaluation gates for the concept-grounded KB pilot."
owner: "aaronksolomon"
author: "Codex"
status: proposed
created: "2026-09-18"
---
# KB Pilot Roadmap and Review Map

A bounded exploration to decide whether conceptual guidance improves Buddhist/PV passage discovery.

## Scope Reset — 2026-09-19

The initial draft specified too much policy and infrastructure before learning from search. This revision replaces its larger corpus targets, mandatory extraction pipeline, and numeric production-style gates with one small comparison. Runtime status is complete; conductor work is deferred. No application code is requested by these drafts.

Read [K02](/architecture/knowledge-base/adr/adr-k02-concept-grounded-knowledge-base.md), the [bsearch review](/architecture/knowledge-base/notes/bsearch-review-2026-09-19.md), and then the optional [K03 probe](/architecture/knowledge-base/adr/adr-k03-concept-extraction-evidence-contract.md). K01 and the older research document are background, not implementation checklists.

## Smallest Useful Experiment

1. **Select material and questions.** Roughly 10–15 texts/talks, 8–12 concepts, and 12–15 real questions. Include both Buddhist source material and PV/TNH teachings; do not require a large or representative corpus. Record source permissions and whether any provider may process the selected text.
2. **Establish the baseline.** Reuse a frozen `bsearch` corpus export or narrowly adapt its parsers. Run keyword search and, where an existing model/index is usable, semantic search. Check source locations and errors. No hosted service, new UI, broad dependency import, or live corpus download is required just to start.
3. **Try a hand-checked concept table.** Run the same queries with a small explicit set of expansions. Hold corpus, passage boundaries, filters, result limits, and base ranking fixed. Keep the original results alongside expanded results. If combining multiple query lists, use one documented fixed rank-fusion rule; do not tune a ranking framework.
4. **Review the difference and stop.** Produce a query-by-query table of useful top-five passages, losses/noise, citation correctness, added terms, latency, and available cost. Decide whether concepts help enough to justify another slice. Only then consider automatic extraction on two or three passages.

If the semantic setup requires substantial environment repair or new paid indexing, run the lexical comparison first and record the limitation. Do not let infrastructure preparation consume the exploration. Any paid run gets a small explicit budget before execution.

## Meaningful Evaluation Without a Benchmark Project

Choose questions before adjusting expansion terms: exact terminology, paraphrase, a PV practice connection, a historical distinction, an ambiguous term, and a question the corpus cannot answer. Include one cross-language case only if suitable source pairs already exist. Reserve a few questions for a final untouched comparison; group paraphrases together.

The maintainer or another knowledgeable reader grades shuffled top-five results as useful, partly useful, or not useful and checks source references. Record counts, examples, and reviewer time. Report how many questions gained or lost a useful passage and how many had any useful result. Do not equate no results with doctrinal absence, and do not claim exhaustive recall from this small corpus.

There is no advance requirement for a particular nDCG improvement or automated-acceptance percentage. Continue only if concrete gains matter to the reviewer and the losses/cost are understood; otherwise keep simple search. Unresolvable citations and incorrect attribution are defects to fix before interpreting the comparison.

## Deliverables and Stop Point

- Source snapshot/manifest and the exact concept table.
- Query list, search settings, raw results with expansion off/on, and a short assessment table.
- One recommendation: keep direct search, test a specific mapping change, or proceed to a small extraction probe.

No graph database, formal review workflow, synthesis engine, version-management platform, or generated service scaffolding is needed. Reuse existing code where it reduces work; build only a thin experiment driver and necessary boundary validation. Save artifacts in a dedicated experiment directory with enough hashes/settings to rerun the comparison.

## Local Task Map

- [x] Review bsearch's implemented strengths and reuse risks.
- [x] Reduce K02/K03 to a bounded exploration.
- [ ] Maintainer reviews scope and picks initial texts/questions.
- [ ] Verify baseline on the selected snapshot, isolating indexes from existing bsearch data.
- [ ] Curate the small map and run the off/on comparison.
- [ ] Review findings before choosing further implementation.

Storage, formal semantic predicates, publication policy, automation, and wider multilingual evaluation remain later decisions. The point of this prototype is to discover which of them are needed.

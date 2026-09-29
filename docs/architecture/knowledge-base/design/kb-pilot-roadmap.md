---
title: "KB Pilot Roadmap and Review Map"
description: "Review order, bounded implementation slices, and evaluation gates for the concept-grounded KB pilot."
owner: "aaronksolomon"
author: "Codex"
status: proposed
created: "2026-09-18"
updated: "2026-09-29"
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
4. **Run the held-out control, review, and stop.** Compare direct search, generic expansion, and curated expansion under the procedure below. Produce a query-by-query table of useful top-five passages, losses/noise, citation correctness, added terms, latency, and available cost. Decide whether concepts help enough to justify another slice. Only then consider the optional extraction smoke test.

If the semantic setup requires substantial environment repair or new paid indexing, run the lexical comparison first and record the limitation. Do not let infrastructure preparation consume the exploration. Any paid run gets a small explicit budget before execution.

## Meaningful Evaluation Without a Benchmark Project

Choose questions before adjusting expansion terms: exact terminology, paraphrase, a PV practice connection, a historical distinction, an ambiguous term, and a question the corpus cannot answer. Include one cross-language case only if suitable source pairs already exist. Reserve a few questions for a final untouched comparison; group paraphrases together. Record intended sense, tradition/period scope, and whether the question asks for connections before running search. Freeze the concept table, expansion prompt/configuration, and retrieval settings before revealing held-out results. Report development and held-out findings separately; changes prompted by held-out results require new questions for a fresh held-out claim.

### Three Retrieval Conditions

| Condition | Input to the same base search | Interpretation |
| --- | --- | --- |
| A: Direct | Original query | Existing-search baseline |
| B: Generic expansion | Original query plus model-generated paraphrases/terms; no concept table, corpus passages, or relevance judgments | Practical alternative to manual curation |
| C: Curated expansion | Original query plus terms selected from the frozen reviewed map, with mapping provenance | Incremental value of this curated knowledge |

Run A/C on development questions first if useful; include B on at least the held-out subset before claiming a curated advantage. Generate B once with a frozen prompt/model/configuration and save its untouched output and actual search terms. Do not selectively regenerate poor rewrites. If a rewrite fails, report it as a condition failure, not a legitimate zero-result search. Use existing TNH GenAI facilities and the explicit experiment budget. If B cannot be run within that budget, report A/C as preliminary and defer the stronger conclusion.

Predeclare the same maximum added terms and subqueries, literal-query handling, and fixed fusion rule for B/C. Preserve the original query in both; record actual term/subquery counts. Hold corpus, boundaries, filters, retrieval depth, and ranking fixed; report keyword and semantic backends separately. Measure expansion cost/latency as well as search cost, and record manual map-curation effort. B may contain learned domain knowledge, so this is not a pure test of conceptual versus non-conceptual reasoning. C winning supports this map's value; a tie weakens the case for paying its curation cost for retrieval, without ruling out other scholarly uses.

Ordinary C expansion uses only reviewed aliases/equivalents within the intended sense and scope. Related concepts, historical connections, and later PV interpretations require an explicit connection-seeking question or a separately labeled secondary run. Never silently merge secondary results into the primary top five. Retain relation explanations and sources for review. Apply the same recorded query intent and filters to all conditions; do not silently repair scope drift in B after seeing results.

### Origin-Hidden Pooled Judgments

For each query/backend comparison, take the union of the top ten passages from every participating condition (or all returned passages if fewer). Deduplicate by frozen source/passage identity, retain condition/rank membership separately, and randomize presentation with a saved seed. Distinct translations or source occurrences remain distinct evidence. Hide condition labels, ranks, scores, and expansion terms while showing the original question, declared scope, passage, and source context needed to judge it.

The maintainer or another knowledgeable reader grades each pooled passage once: 0 = not useful or wrong sense/scope; 1 = partly useful; 2 = directly useful. Record citation defects separately. Lock judgments before revealing condition membership. Disclose if the reviewer curated the map or recognizes results: this reduces origin bias but cannot guarantee full blindness. Record reviewer time and brief reasons for disagreements or borderline cases; no reviewer platform is needed.

Keep the query-by-query gains/losses table primary. Derive these descriptive measurements from the saved rankings and shared judgments:

- Useful@5: count grade-2 passages; P@5 is that count divided by five, treating unfilled ranks as zero.
- nDCG@5: use graded gain `2^grade - 1` divided by `log2(rank + 1)` for ranks starting at one and an ideal ranking from the same judged pool. Report N/A where the pool has no positive grades, and disclose that count in aggregates.
- MRR@5: reciprocal rank of the first grade-2 passage within five, or zero if none; average over the declared query set. The cutoff avoids implying a judgment of the entire ranking.
- Counts of queries improved, tied, or regressed on Useful@5 for C versus A and C versus B, with grade-1 counts and examples alongside them.

A technical failure invalidates that query/condition comparison; report failures and any excluded comparisons explicitly rather than scoring them as retrieval misses. Fix unresolvable citations or incorrect attribution before interpreting the affected comparison. Report zero-positive-pool questions separately, especially unanswerable cases. Pooled judgments do not establish exhaustive recall, and no results do not establish doctrinal absence. New conditions that retrieve unjudged passages require additional judgments before comparing metrics.

There is no advance requirement for a particular nDCG improvement or automated-acceptance percentage. These small samples provide descriptive evidence, not statistical or production claims. Continue only if concrete gains matter to the reviewer and the losses/cost are understood; otherwise keep simple search.

### Optional Extraction Follow-Up

K03 starts with two or three passages as a failure-finding smoke test. If warranted by retrieval value and promising smoke-test findings, freeze the revised prompt/schema/model and run 10–20 additional heterogeneous passages. Track passage failures, unchanged acceptance counts, omissions, review/correction minutes, and cost; compare a small hand-curation timing sample before claiming labor savings. Neither batch establishes general readiness. See the [K03 addendum](/architecture/knowledge-base/adr/adr-k03-concept-extraction-evidence-contract.md#addendum-2026-09-29-smoke-test-and-bounded-follow-up).

## Deliverables and Stop Point

- Source snapshot/manifest and the exact concept table.
- Query list and split, scope/intent, frozen settings, A/B/C terms and raw rankings, pooled judgments with saved shuffle seed and condition membership, and the assessment table/metric definitions.
- One recommendation: keep direct search, prefer generic expansion, test a specific mapping change, or proceed to the extraction smoke test. Record limits of preliminary A/C-only findings.

No graph database, formal review workflow, synthesis engine, version-management platform, or generated service scaffolding is needed. Reuse existing code where it reduces work; build only a thin experiment driver and necessary boundary validation. Save artifacts in a dedicated experiment directory with enough hashes/settings to rerun the comparison.

## Local Task Map

- [x] Review bsearch's implemented strengths and reuse risks.
- [x] Reduce K02/K03 to a bounded exploration.
- [ ] Maintainer reviews scope and picks initial texts/questions.
- [ ] Verify baseline on the selected snapshot, isolating indexes from existing bsearch data.
- [ ] Curate the small map, freeze the query split and expansion rules, and run A/C plus the held-out A/B/C comparison.
- [ ] Pool and grade results with origin hidden; report descriptive metrics, failures, regressions, and effort.
- [ ] Review findings before choosing further implementation.

Storage, formal semantic predicates, publication policy, automation, and wider multilingual evaluation remain later decisions. The point of this prototype is to discover which of them are needed.

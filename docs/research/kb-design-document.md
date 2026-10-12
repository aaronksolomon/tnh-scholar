---
title: "TNH Scholar Knowledge Base: Design Document"
description: "Current concept-aware KB design, beginning with a controlled bsearch retrieval pilot and evidence-led extensions."
owner: "aaronksolomon"
author: "Codex"
status: current
created: "2025-06-10"
updated: "2026-10-03"
---
# TNH Scholar Knowledge Base: Design Document

The TNH Scholar Knowledge Base supports scholarly discovery of source passages across Thích Nhất Hạnh’s teachings and classical Buddhist texts. Its immediate design is a controlled retrieval study, followed by extensions justified by measured usefulness and review effort.

## Design status and scope

This document consolidates the earlier semantic-search design with the September 30 [pilot study proposal](/research/kb-pilot-proposal.md) and the [concept-extraction review](/architecture/knowledge-base/notes/concept-extraction-live-review-2026-09-17.md). The proposal describes researcher participation and the experiment; this document describes the supporting design and subsequent decision gates. Both describe proposed work, not an implemented KB.

The first study uses **bsearch**, a small reviewed concept table, one shared language, and passage-first results. It compares direct search, general AI query expansion, and reviewed concept expansion on the same collection. The starting targets are **8–12 concepts, 10–15 source units, and 12–15 authentic questions**. The earlier roadmap’s 20–30 concepts, 30–50 sources, and 30 questions are possible expansion sizes after the first study, not initial requirements.

[ADR-K01](/architecture/knowledge-base/adr/adr-k01-kb-architecture-strategy.md) remains proposed. Its original managed/vector-first and English-first assumptions are historical proposals; its October 3 addendum points to this revised pilot direction. Embedding providers, storage, multilingual strategy, and production architecture remain open.

## Objectives and research questions

The primary users are monastics, researchers, and senior community members. The first output is a useful passage with an accurate citation and a path back to its source. Generated answers are a later experiment.

The study asks whether reviewed terminology and relationships discover useful passages missed by direct search or general AI expansion, and whether the improvement justifies curation and operational effort. It also tests whether expansion creates misleading connections across traditions, translations, or historical contexts.

Select questions across these use cases, scaled to the small collection:

| Query type | Example or test purpose |
| --- | --- |
| Factual or practice lookup | Find a description of touching the earth practice. |
| Thematic exploration | Find passages connecting environmental responsibility and non-separate self. |
| Perspective analysis | Find teachings concerning nonviolence and public service. |
| Qualitative inquiry | Find passages a researcher considers especially difficult or compassionate; record the researcher’s criteria. |
| Cross-domain inquiry | Find connections between physics and Dharma teachings where the collection supports them. |
| Ambiguity and historical distinction | Distinguish shared terminology with different meanings or later interpretations. |
| Insufficient evidence | Include at least one question the selected collection cannot answer. |

These examples guide question selection; the study does not claim every topic is represented. Speculative attribution such as “What would Thay say about a present-day conflict?” is outside the pilot.

## Collection preparation and provenance

### Source selection

The proposed TNH books are *Chanting from the Heart*, *Fragrant Palm Leaves*, *The Miracle of Mindfulness*, and *The Heart of the Buddha’s Teaching*. Selected talks may supplement them. Compare selected sections with a small classical collection already supported by bsearch, initially SuttaCentral or CBETA as appropriate to the questions and shared language. Confirm available files, permissions, editions, translations, and bsearch ingestion capabilities before freezing the collection.

A source unit is a selected book section, talk, or discourse; it is distinct from a retrieval passage. Include potentially misleading material so improved recall can be assessed alongside false matches. Preserve canonical identifiers for classical texts. EPUB is preferred, PDF acceptable, and talks may use UTF-8 text with paragraphs and available timestamps.

### Processing and metadata

Retain original files alongside extracted text. Normalize encoding and formatting while keeping a traceable mapping back to source locations. Review OCR or transcription errors that could alter meaning. Existing processing tools may assist preparation, but complete audio/video ingestion is not required for the study.

Reuse the [journal pipeline’s provenance approach](/user-guide/journal-pipeline-case-study.md). Distinguish source metadata from processing metadata and derived interpretations.

| Record | Minimum information |
| --- | --- |
| Source | Stable ID, title, author/speaker, language, known date, edition, translator, canonical identifier where applicable, source location, and use restrictions. |
| Passage | Stable ID, source ID and version, section position, page/canonical locator/timestamp as available, boundaries, and original text location. |
| Processing | Extraction or transcription method/version, processing time, normalization steps, and review status. |
| Translation | Original/translation links and attribution when available; explicitly record missing links. |
| Concept annotation | Concept ID, evidence span or locator, relationship type and direction, rationale, provenance, and review status. |
| Experiment | Collection and concept-table versions, passage policy, retrieval settings, expansion limits, actual queries, ranked passage IDs, and judgments. |

Do not invent missing dates, translators, or page numbers. Use the available locator and identify its limitations. Generated annotations and model confidence must not be presented as verified bibliographic facts or expert judgments.

### Passage boundaries

Start with a documented paragraph or logical-section policy, retaining parent-section context and reliable source navigation. Record how long passages, boundary splits, and any overlap are handled. Use **identical boundaries across all three study conditions**.

If preparation shows that boundaries regularly remove necessary context, compare paragraph-based and section-based passage policies on development questions before freezing the main experiment. Keep this comparison separate from the query-expansion comparison. Sliding windows and hierarchical retrieval remain options if observed boundary failures justify them.

## Reviewed conceptual model

Use a small reviewed table rather than requiring a graph database or automated concept extraction. Each concept has a stable ID, preferred label, alternative names, scoped meaning, tradition or historical context, source evidence, and review status. Preserve the distinction between general Buddhist concepts and Plum Village teachings/practices.

Relationships must identify their type, direction, scope, evidence, and rationale. Distinguish equivalents and translation variants from broader/narrower concepts, related teachings, and practice expressions. Related concepts must not automatically become synonyms. A later Plum Village interpretation must not be projected onto a classical source as though it were the source’s own terminology.

Reviewed equivalent terms may expand ordinary queries within their documented scope. Related ideas or interpretive connections require an explicit request for connections or a separately labeled search. Retain original-query retrieval for uncatalogued material. Record which concept and relationship caused each added term so gains and errors can be explained.

The first study uses one shared language. The data model should accommodate multilingual labels and original/translation links, but multilingual retrieval is a separately evaluated extension.

## Retrieval design

### Controlled comparison

All conditions use the same frozen collection, passage boundaries, metadata filters, ranking settings, and result limit.

| Condition | Input | Purpose |
| --- | --- | --- |
| Direct search | Original question. | Baseline without expansion. |
| General AI expansion | Original question plus AI-suggested terms; no access to the reviewed table or study collection. | Measure general reformulation. |
| Concept-based expansion | Original question plus terms from the reviewed table. | Measure the added value of curated knowledge. |

Use matching limits on added terms and search calls for both expansion conditions. Document how searches are combined, duplicate passages removed, and results ordered; use the same combination policy for both expansion conditions. Log actual expansions and results. General AI expansion may already contain Buddhist knowledge, so the comparison measures the table’s added value rather than knowledge versus no knowledge.

Keyword search is the initial baseline. If semantic retrieval is already available, evaluate it as a separate comparison while keeping the query-expansion conditions comparable. Do not introduce new ranking stages or model choices in only one expansion condition.

### Evolution toward hybrid retrieval

The older design’s distinction remains useful: keyword retrieval tests exact terminology, semantic retrieval tests paraphrases and conceptual similarity, and hybrid retrieval combines their candidates. Metadata filtering and source context apply across these approaches.

Introduce semantic or hybrid retrieval only when the baseline reveals missed relevant passages that justify another experiment. Reranking, query rewriting, intent routing, and hierarchical retrieval are possible later interventions; each should address an observed failure and be compared against the established baseline.

### Results and evidence sufficiency

Return passages, source citations, surrounding context, and clearly labeled expansion reasons. Provide a basic path to original text or file during the study; an integrated scan/translation/concept viewer can follow later.

Evaluate whether returned passages actually support the researcher’s question. Empty results and top-ranked weak matches must remain visible in the report. Retrieval scores alone do not establish sufficient evidence, and no match in this small collection does not establish absence from TNH’s complete works.

## Evaluation and decision gates

Reserve several questions from tuning. Before held-out evaluation, freeze the collection, concept table, boundaries, prompts/models, retrieval settings, and budgets. Agree with researchers on what constitutes a worthwhile gain and unacceptable regressions before seeing held-out results.

Pool the top ten passages from each condition for each question, remove duplicates, and grade each passage once with retrieval origin hidden: **not useful, partly useful, or directly useful**. Define the rubric with researchers, record disagreements, and distinguish interpretive usefulness from explicit source support. Review existing query-response pairs as possible question/evidence candidates; do not treat generated pairs as ground truth without source checks.

| Measure | Pilot use |
| --- | --- |
| Top-five usefulness | Report partly and directly useful passages separately, using the same rubric across conditions. |
| First useful result | Report first-useful rank or reciprocal rank, including failures to retrieve a useful passage. |
| Gains and regressions | Show discoveries, false matches, and losses by question and query type. |
| Citation and context accuracy | Check source identity, locator resolution, quotation fidelity, and whether surrounding context changes the interpretation. |
| Insufficient evidence | Assess behavior on unanswerable questions and misleading matches; record collection limitations. |
| Operational effort | Report latency, API cost, preparation/curation effort, and researcher review effort. |

The pooled judgments support comparisons within the study, not absolute corpus-wide recall. More comprehensive recall measurement or graded nDCG can follow if the question set and judgments justify them. Report results per question alongside aggregates; a small pilot cannot establish broad statistical or production claims.

Proceed with concept expansion only if its discoveries justify effort without unacceptable misleading associations or citation errors. If general AI expansion performs similarly, simplify the design or identify where curation provides a defensible contextual benefit. If expansion harms retrieval, narrow relations or retain direct search. Treat citation defects and misleading equivalences as failures to repair and re-evaluate, not gains masked by an aggregate relevance score.

## Implementation sequence

1. **Prepare and review.** Confirm bsearch capabilities and source availability; select units, concepts, and questions; define provenance and passage policies; agree on judgments and decision criteria.
2. **Run the controlled study.** Establish direct retrieval, implement bounded expansion conditions, freeze inputs, collect blinded judgments, and publish a reproducible comparative report with representative discoveries and errors.
3. **Choose the next experiment.** Based on failures and researcher needs, consider a larger collection, semantic/hybrid retrieval, a bilingual subset, or improved source navigation. Keep experiment variables separable.
4. **Develop assistance after retrieval evidence.** Consider automated extraction, evidence-linked answers, and a fuller viewer only when their prerequisites and evaluation are defined.

No fixed production schedule, monthly infrastructure budget, corpus-coverage percentage, availability target, or adoption target is established by this pilot. Measure actual effort and cost before committing to them.

## Subsequent experiments and architectural boundaries

### Automated concept extraction

The [September 17 live test](/architecture/knowledge-base/notes/concept-extraction-live-review-2026-09-17.md) found reversed relationships and altered quotations, including loss of a crucial negation. It motivates validation work; it does not establish an accepted production concept map.

A later extraction pipeline should use typed outputs against reviewed vocabularies, preserve evidence spans and negation, validate IDs and predicates, evaluate relationship direction, and propose novel terms separately. Detectable failures should trigger bounded repair or an explicit review queue. Measure unassisted acceptance and correction rates before scaling. Expert review curates vocabularies and assesses sampled/flagged results; schema validity alone cannot establish doctrinal correctness. Per-document ad hoc agent cleanup must not become a required processing stage.

### Multilingual retrieval and answer generation

Use a small Vietnamese–English subset to compare cross-language discovery and translation effects after the shared-language study. Preserve language, translation attribution, scoped equivalents, and direct access to originals. Unified multilingual embeddings, separate indexes, and translation-based expansion are options to evaluate rather than settled choices.

Evidence-linked answers require demonstrated passage retrieval, source-linked claims, explicit insufficient-evidence behavior, and evaluation against passages and originals. Speculative attribution, fine-tuning, temporal analytics, visualization, and collaborative annotation remain future research rather than pilot deliverables.

### Infrastructure and service boundaries

Reuse bsearch and existing preparation tools wherever feasible. Select storage and embedding infrastructure from measured needs: integration effort, metadata filtering, reproducible indexing, exportability, source restrictions, latency, and total operational cost. Managed and open-source approaches remain alternatives; neither managed-to-open migration nor Supabase is predetermined. Detailed provider comparisons and pricing should be refreshed when selecting a stack.

New GenAI services must follow [ADR-OS01](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md): typed Pydantic domain models, Protocol boundaries, service orchestration, and provider adapters with bidirectional mappers and isolated transports. Use Settings → Config → Params → Policy, config at initialization, and params per call. Keep provider selection independent of concept semantics and scholarly judgments.

## Open decisions

- Which source editions, classical corpus, shared language, and authentic questions are available?
- Which bsearch ingestion, filtering, ranking, and export capabilities can be reused without new infrastructure?
- Which passage policy preserves necessary context while keeping the comparison manageable?
- Which scoped equivalences and relationship types are reviewed strongly enough for expansion?
- What gain and regression criteria do researchers accept relative to curation effort?
- Which observed limitation warrants the next experiment, and what evidence would justify a larger KB?

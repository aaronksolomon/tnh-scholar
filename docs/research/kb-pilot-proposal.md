---
title: "Proposed Pilot Study: Concept-Based Search and Retrieval for TNH Scholar"
description: "A controlled comparison of direct search, AI query expansion, and reviewed concept-based retrieval across Thích Nhất Hạnh’s teachings and classical Buddhist sources."
owner: "aaronksolomon"
author: "Codex"
status: proposed
created: "2026-09-30"
updated: "2026-10-03"
---
# Proposed Pilot Study: Concept-Based Search and Retrieval for TNH Scholar

This proposal defines the first controlled retrieval study and the materials and researcher input it needs. The [Knowledge Base Design Document](/research/kb-design-document.md) describes the supporting provenance, passage preparation, conceptual model, and evidence-led extensions. Automated extraction, multilingual retrieval, and generated answers are subsequent experiments.

**Research context:** Sarang Kulkarni’s Bayer/Thoughtworks case study, [*Building Reliable Agentic AI Systems*](https://martinfowler.com/articles/reliable-llm-bayer.html), published on Martin Fowler’s website, describes a progression from search to evidence-based assistance. It informs this pilot’s emphasis on source traceability and evaluation before extending the system to generated answers.

## Objective and hypothesis

Determine whether a reviewed conceptual model improves passage retrieval across Thích Nhất Hạnh’s teachings and classical Buddhist texts. The hypothesis is that explicit knowledge of terminology, context, and conceptual relationships can uncover relevant passages missed by direct search or general AI-generated query expansion—adding related wording to a search request.

The pilot builds on **bsearch**. Its conceptual model is a small table of concepts, alternative names, meanings, tradition or historical context, and supported relationships. Each connection records its source and rationale. Equivalent terms can expand a query directly; related ideas or later Plum Village interpretations require an explicit request for connections or a separately labeled search.

## Required materials to begin pilot

The proposed TNH collection comprises:

- *Chanting from the Heart*
- *Fragrant Palm Leaves*
- *The Miracle of Mindfulness*
- *The Heart of the Buddha’s Teaching*

**Source files:** EPUB preferred; PDF acceptable. Selected talks can be supplied as UTF-8 plain text, preserving paragraphs and available timestamps. Include title, author or speaker, language, date, edition, translator, source location, and any restrictions on use. Original files are retained alongside extracted text; conversion is part of pilot preparation.

**Classical comparison material:** A small selection of discourses from a corpus already supported by bsearch, initially SuttaCentral or CBETA as appropriate to the research questions and language. Preserve canonical identifiers and translation attribution. Selected book sections, talks, and discourses should form roughly 10–15 manageable source units, including material that could produce misleading matches. Start in one shared language; multilingual retrieval is a later extension.

**Research input:** Approximately 12–15 authentic questions and 8–12 initial concepts, with researcher review of meanings and relationships. Questions should include exact terms, paraphrases, historical distinctions, ambiguous terminology, and at least one question the collection cannot answer. Cover factual/practice lookup, thematic exploration, perspective analysis, and cross-domain inquiry where the selected material permits. For qualitative questions, record what the researcher considers useful rather than assuming a single objective answer.

**Passage preparation:** Give sources and passages stable identifiers and resolvable locators; preserve edition/translation attribution and processing history. Select a paragraph or logical-section policy that retains enough context to interpret the passage. If boundaries need comparison, use development questions before the main experiment and keep the same final boundaries across conditions. Detailed requirements are in the [collection preparation and provenance design](/research/kb-design-document.md#collection-preparation-and-provenance).

## Experimental design

All conditions search the same frozen collection, with identical passage boundaries, filters, and ranking settings:

| Condition | Search input | Purpose |
| --- | --- | --- |
| Direct search | Original question | Establish baseline performance |
| General AI expansion | Original question plus AI-suggested terms, without access to the concept table or source collection | Measure the benefit of general reformulation |
| Concept-based expansion | Original question plus terms from the reviewed conceptual model | Measure the additional value of curated knowledge |

The two expansion conditions use matching limits on added terms and searches, with the same result-combination and deduplication policy. Keyword search provides the initial baseline; semantic search, which retrieves by similarity of meaning, can be evaluated separately if already available. General AI expansion may itself contain Buddhist knowledge: the comparison tests the added value of the reviewed model.

Reserve several questions from tuning. Freeze the concept map and settings before evaluating those questions. Preserve source versions, passage identifiers, actual queries, and ranked results so the comparison can be reproduced.

## Evaluation and decision

Pool the top ten passages from each condition, remove duplicates, and grade each passage once with retrieval origin hidden: not useful, partly useful, or directly useful. Report partly and directly useful passages separately in the top five, the rank of the first useful passage, gains and regressions by question, citation accuracy, latency, cost, and preparation/curation/researcher review effort. Check locators and quotation fidelity against sources, assess weak matches on unanswerable questions, and record collection limitations. Pooled judgments do not establish absolute corpus-wide recall.

The deliverable is a comparative results table with representative discoveries and errors. Agree on worthwhile gains and unacceptable regressions before held-out evaluation. Expansion should justify its curation effort through meaningful retrieval gains without misleading equivalences or citation failures; otherwise narrow it or retain direct search. Existing query-response pairs may supply candidate examples after source review, not automatic ground truth. The [evaluation and decision gates](/research/kb-design-document.md#evaluation-and-decision-gates) describe reporting and follow-up choices. Automated concept extraction and answer generation remain subsequent experiments; neither is required to establish the value of the conceptual model.

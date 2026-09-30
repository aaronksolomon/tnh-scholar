---
title: "Proposed Pilot Study: Concept-Based Search and Retrieval for TNH Scholar"
description: "A controlled comparison of direct search, AI query expansion, and reviewed concept-based retrieval across Thích Nhất Hạnh’s teachings and classical Buddhist sources."
owner: "aaronksolomon"
author: "Codex"
status: proposed
created: "2026-09-30"
updated: "2026-09-30"
---
# Proposed Pilot Study: Concept-Based Search and Retrieval for TNH Scholar

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

**Research input:** Approximately 12–15 authentic questions and 8–12 initial concepts, with researcher review of meanings and relationships. Questions should include exact terms, paraphrases, historical distinctions, ambiguous terminology, and at least one question the collection cannot answer.

## Experimental design

All conditions search the same frozen collection, with identical passage boundaries, filters, and ranking settings:

| Condition | Search input | Purpose |
| --- | --- | --- |
| Direct search | Original question | Establish baseline performance |
| General AI expansion | Original question plus AI-suggested terms, without access to the concept table or source collection | Measure the benefit of general reformulation |
| Concept-based expansion | Original question plus terms from the reviewed conceptual model | Measure the additional value of curated knowledge |

The two expansion conditions use matching limits on added terms and searches. Keyword search provides the initial baseline; semantic search, which retrieves by similarity of meaning, can be evaluated separately if already available. General AI expansion may itself contain Buddhist knowledge: the comparison tests the added value of the reviewed model.

Reserve several questions from tuning. Freeze the concept map and settings before evaluating those questions. Preserve source versions, passage identifiers, actual queries, and ranked results so the comparison can be reproduced.

## Evaluation and decision

Pool the top ten passages from each condition, remove duplicates, and grade each passage once with retrieval origin hidden: not useful, partly useful, or directly useful. Report useful passages in the top five, the rank of the first useful passage, gains and regressions by question, citation accuracy, latency, cost, and researcher review effort.

The deliverable is a comparative results table with representative discoveries and errors. Expansion should justify its curation effort through meaningful retrieval gains. Automated concept extraction and answer generation remain subsequent experiments; neither is required to establish the value of the conceptual model.

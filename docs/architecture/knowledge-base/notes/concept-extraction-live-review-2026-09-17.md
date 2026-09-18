---
owner: "Engineering"
title: "Concept extraction live-test review"
description: "Brief KB implications of a tnh-gen processing test; extraction must not depend on ad hoc agent cleanup."
author: "Codex"
status: draft
created: "2026-09-17"
---

# Concept extraction live-test review

A live `tnh-gen` test transformed the case study's [baseline journal translation](/user-guide/assets/journal-pipeline/vu-tru-quan-phat-hoc-en.md) using GPT-5.4. Its primary purpose was processing-system validation. The [raw result](/architecture/knowledge-base/notes/assets/concept-extraction-2026-09-17/raw-concept-map.md.txt), [exact prompt](/architecture/knowledge-base/notes/assets/concept-extraction-2026-09-17/extraction-prompt.md.txt), and [runtime events](/architecture/knowledge-base/notes/assets/concept-extraction-2026-09-17/runtime-events.jsonl) preserve evidence from the pre-repair run. Raw result frontmatter also preserves the source-metadata/timezone defects discovered in that run.

The model proposed 39 concepts and five Plum Village connections. Several relation predicates reversed the intended meaning; two quotations changed punctuation and another dropped a crucial negation. The assistant-reviewed derivative required manual corrections. Such cleanup must **not become a required Codex/agent execution step** for each document. Full local review and derivative: `tmp/tg06-live-concepts-20260917/review-notes.md` and `concept-map-reviewed.md` in that directory (local, untracked).

For the KB pilot, define a reviewed general Buddhist vocabulary and a distinct Plum Village vocabulary grounded in representative primary sources. Extract article concepts against these vocabularies, propose novel terms separately, and keep later PV mappings explicitly inferred until supported. Names, aliases, and multilingual equivalents need stable IDs and source evidence; related concepts must not automatically become equivalents.

Build extraction and validation into the processing pipeline: typed outputs, evidence spans retaining negation, ID/predicate checks, and evaluated relation direction. Detectable failures should trigger bounded repair or an explicit review queue. Expert review should curate vocabularies and assess sampled/flagged cases; schema validation alone cannot establish doctrinal correctness. Measure unassisted acceptance and correction rates before scaling. This test motivates that design work; it does not establish a production concept map.

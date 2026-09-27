---
title: "bsearch Review for the KB Exploration"
description: "Implemented search strengths, reproduced limitations, and narrow reuse recommendations."
owner: "aaronksolomon"
author: "Codex"
status: draft
created: "2026-09-19"
---
# bsearch Review for the KB Exploration

The sibling project offers a useful local search baseline; reuse its working pieces before building a new KB platform.

## Scope and Evidence

Reviewed the local `../bsearch` checkout at `3849925` (2026-01-09), including parsers, named-index builder, keyword/vector backends, cache, search engine, CLI routing, and focused tests. An existing untracked `scripts/run_bsearch_scenario.sh` was left untouched. Source references below are relative to the bsearch root, not TNH Scholar.

Using bsearch's existing environment with its source directory on PYTHONPATH, 48 search-engine, vector-index, and corpus-parser tests passed. Initial collection without PYTHONPATH failed because the package was not importable from that environment. Three additional temporary synthetic probes reproduced the issues below without downloading data, loading an embedding model, calling a provider, or touching existing corpus/index data. This is implementation review and fixture testing, not an assessment of live corpus search quality.

## Strengths Worth Reusing

| Strength | Evidence and relevance |
| --- | --- |
| Local keyword baseline | `src/buddha_search/index/sqlite_index.py:59`: SQLite FTS5 with corpus/language filters and ranked passage results. A small experiment needs no search server. |
| Separate semantic path | `src/buddha_search/search/engine.py:68`: query embedding and vector retrieval can be compared independently of keyword search. CLI named-index routing selects the relevant backend/model. |
| Passage-aware parsing | `src/buddha_search/corpus/parsers.py:110` and `:555`: SuttaCentral segment aggregation and CBETA paragraph processing retain source segment/paragraph metadata. These are useful locator patterns, though not a complete immutable citation system. |
| Named experiment indexes | `src/buddha_search/indexes/builder.py:380`: model/index configurations permit isolated comparisons instead of one global index. |
| Content-aware cache | `src/buddha_search/embeddings/cache.py:15`: cache identity includes document, model, and text hash. Reuse this idea to avoid repeated embedding expense. |
| Small corpus record | `src/buddha_search/corpus/models.py:8`: ID, corpus, language, title, text, metadata are sufficient to start. Add only the source snapshot/locator information the experiment needs. |

The project provides separate keyword and semantic modes, not an implemented hybrid/concept engine. `search/ranking.py` and all four non-init files in `lexicon/` are empty. Do not count filename scaffolding as working expansion, language detection, transliteration, or lexicon lookup.

## Limitations Relevant to Reuse

1. **Filtered vector search can miss eligible results.** `src/buddha_search/index/vector_index.py:179` fetches only `limit * 3` neighbors before metadata filtering. A synthetic index with four closer excluded passages and one eligible passage returned zero results at limit one. For the tiny experiment, search the entire small vector index before filtering or use indexes partitioned by the selected corpus; correct the behavior before judging filtered semantic quality.
2. **SQLite/vector persistence is not atomic.** `src/buddha_search/index/vector_index.py:117` commits metadata per insertion, while vector saving is separate (`:249`). A simulated interruption before save reopened with five metadata records and zero vectors. Do not use these artifacts as a reliable resumable store. Build disposable indexes afresh for this exploration and check metadata/vector counts before use.
3. **Resume ignores changed content.** `src/buddha_search/indexes/builder.py:403` drops documents whose IDs already exist before consulting the content-aware embedding cache. A text edit under the same ID can therefore retain stale indexed content. This is a code-path finding, not a separate crash test. Freeze the source snapshot and rebuild rather than designing a general migration engine now.
4. **Query error and no match are conflated.** `src/buddha_search/index/sqlite_index.py:123` prints an OperationalError and returns an empty list. A malformed quote query reproduced this behavior. An experiment driver must distinguish invalid queries from legitimate absence and escape ordinary text before passing it as FTS syntax.
5. **Multilingual corpus support is not multilingual quality evidence.** Parsers cover SuttaCentral/CBETA, but that does not establish Vietnamese/PV coverage, cross-language embedding quality, or Chinese lexical segmentation quality. Test selected examples rather than inheriting a broad claim from the README.

Other integration costs: the project uses dictionary/dataclass interfaces and relative imports, unlike TNH's typed object-service conventions. Its dependency graph includes torch, sentence-transformers, Faiss, API and TUI packages; importing the whole application could expand TNH's environment unnecessarily. README reports 0.4.0 while pyproject declares 0.3.0. README points to LICENSE, but no LICENSE file was found in the inspected checkout; establish code licensing before copying/distributing code, separately from source-text permissions.

## Recommendation

Use bsearch as a baseline and source of parser/index/cache designs. First run a fixed small snapshot through its existing interfaces in an isolated experiment environment. Add PV/TNH passages through a narrow corpus export/import boundary, rather than extending every downloader. Add a small hand-checked concept table outside the search engine and compare expansion off/on with the same base search.

Prefer reuse through a thin driver over immediate package adoption or code copying. Reuse does not require adopting bsearch's UI, cloud backend, dependency set, or architectural style. No bsearch files were changed in this review. If its baseline needs repairs, scope those independently; the first KB comparison can use lexical search while semantic integration remains unresolved.

Proceed according to the reduced [exploration map](/architecture/knowledge-base/design/kb-pilot-roadmap.md). The first deliverable is comparative search evidence, not a production framework.

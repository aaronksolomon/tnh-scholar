# ADR-K01: Preliminary Architectural Strategy for TNH Scholar Knowledge Base

- **Status**: Proposed
- **Date**: 2025-02-14
- **Stakeholders**: Research tooling team, GenAI service maintainers, metadata working group

## Context

The research note in `docs/research/tnh-scholar-knowledge-vector-search.md` captures objectives, content scope, architectural options, and open questions for the TNH Scholar Knowledge Base. The document establishes the target user base, outlines the ingestion pipeline, compares embedding/search/storage technologies, and lists evaluation metrics. However, several foundational choices remain unresolved (chunking strategy, multilingual plan, metadata schema, and the commercial vs. open-source stack). An initial Architectural Decision Record is needed to align stakeholders on a phased approach while these investigations continue.

## Decision

Adopt a two-phase strategy:

1. **Phase 1 – Learning Prototype**
   - Use managed services for speed: OpenAI text-embedding-3-large, a lightweight vector store (Pinecone or Chroma), and a simple ingestion pipeline leveraging existing transcription tools.
   - Focus on English content first, using paragraph-level chunks with conservative overlap to validate retrieval quality.
   - Capture user feedback from monastics/senior researchers to refine query patterns and metadata expectations.

2. **Phase 2 – Production Architecture**
   - Based on Phase 1 metrics, evaluate migration to an open-source or hybrid stack (e.g., BGE/E5 embeddings + Weaviate/Qdrant/Elasticsearch with BM25).
   - Finalize a bilingual metadata schema and chunking policy, incorporating cross-lingual retrieval requirements.
   - Introduce advanced ranking (re-rankers or intent-aware routing) only after core precision/recall targets are met.

## Rationale

- The research document identifies rapid prototyping as the recommended path (`docs/research/tnh-scholar-knowledge-vector-search.md:200-209`). Managed embeddings and hosted vector DBs minimize infrastructure drag while user needs crystallize.
- Paragraph-level chunks provide good context/precision balance (`docs/research/tnh-scholar-knowledge-vector-search.md:76-85`). We can adjust chunking once evaluation data indicates better boundaries.
- Focusing on English first limits scope while the multilingual strategy (separate indices vs. cross-lingual embeddings) is still under investigation (`docs/research/tnh-scholar-knowledge-vector-search.md:210-248`).
- A phased migration plan keeps the door open for cost/control optimization once we have empirical data on query mix, cost-per-query, and operational complexity.

## Consequences

- **Positive**: Enables a demonstrable prototype in weeks, surfaces real user queries, and produces concrete metrics needed for later ADRs.
- **Neutral/Deferred**: Multilingual retrieval, sophisticated reranking, and hybrid search remain research tracks tied to Phase 1 learnings.
- **Negative**: Short-term vendor lock-in (OpenAI + Pinecone) and recurring API costs until the open-source evaluation completes.

## Next Steps & Open Questions

1. **Chunking Experiments**: Run A/B tests across paragraph, sliding-window, and hierarchical strategies to inform ADR-K02.
2. **Metadata Schema Draft**: Collaborate with the metadata working group to prototype the bibliographic/content/structural fields listed in the research doc (`docs/research/tnh-scholar-knowledge-vector-search.md:48-75`).
3. **Multilingual Plan**: Prototype cross-language retrieval on a bilingual subset to assess whether cross-lingual embeddings or dual indices perform better.
4. **Cost & Privacy Analysis**: Document the operational cost envelope for the managed stack and the data-handling implications before onboarding sensitive transcripts.
5. **Evaluation Harness**: Build the test query set, gold judgments, and logging needed to compute precision, recall, MAP, and nDCG as outlined (`docs/research/tnh-scholar-knowledge-vector-search.md:214-273`).

Approval of this ADR should be revisited once Phase 1 metrics and user feedback reports are available.

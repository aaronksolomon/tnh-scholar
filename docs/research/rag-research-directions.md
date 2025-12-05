---
title: "RAG Research Directions for TNH Scholar"
description: "Exploratory roadmap for retrieval-augmented generation (RAG) within the TNH Scholar project, with emphasis on multilingual Buddhist corpora and Plum Village practice contexts."
owner: ""
author: "Aaron Solomon (with GPT-5.1 Thinking as research assistant)"
status: draft
created: "2025-12-05"
---
# RAG Research Directions for TNH Scholar

This document sketches medium–term research directions for **retrieval-augmented generation (RAG)** inside the TNH Scholar project. It assumes:

- A growing corpus of text from *Thich Nhat Hanh* (TNH), Plum Village, and related Buddhist canons (e.g., CBETA, Taishō).
- A layered architecture in which **LLMs act as reasoning and explanation engines**, while **retrievers and indexes act as external memory**.
- A long-term goal of **grounded, citation-rich Dharma assistance**, not purely conversational or speculative answers.

The aim here is not to specify implementation details, but to identify **research themes**, **walking-skeleton experiments**, and **relevant external work** that can inform TNH Scholar’s roadmap.

## 1. Background: Why RAG for TNH Scholar?

TNH Scholar’s domain is:

- **Knowledge-intensive**: thousands of pages of canonical and commentarial material; fine-grained doctrinal distinctions; multiple schools and historical layers.
- **Multilingual and multi-era**: classical Chinese, Vietnamese, Pāli/Sanskrit, French, English, and modern commentary across decades.
- **High-stakes conceptually**: misquoting or hallucinating scriptures, mis-attributing teachings, or collapsing doctrinal nuance is not acceptable.

Vanilla LLMs are powerful but limited for this domain:

- Their **internal “parametric” memory** is opaque and not easily updated; it may or may not contain accurate Buddhist sources.
- They may **hallucinate sutra passages, attributions, and historical details** without clear references.
- They struggle to provide **verifiable links back** into a specific TNH / CBETA / PV corpus under version control.

RAG directly addresses this by combining:

- A **retriever + index** over the curated Buddhist corpora (TNH books, CBETA, etc.), and
- A **generator (LLM)** that uses retrieved passages as grounding context, with explicit citations and provenance.

In this framing, RAG is not an add-on; it is the **primary way TNH Scholar connects “intelligence” (LLM) with “memory” (canon + metadata)**.

## 2. RAG Building Blocks in the TNH Scholar Context

At a high level, most RAG systems have three components. TNH Scholar can use the same decomposition but with domain-specific constraints.

### 2.1 Retrieval layer

Core responsibilities:

- Encode text (sentences, paragraphs, sections) into **dense vectors**, ideally with **domain-tuned multilingual embeddings**.
- Support **semantic search** across multiple corpora and languages.
- Respect **rich metadata filters**:
  - Canon / collection (e.g., CBETA X, Taishō, TNH books, PV talks).
  - Language and translation alignment.
  - Genre (sutra, commentary, letter, Dharma talk, journal, etc.).
  - Time period and location when available.

Medium-term research leverages bi-encoders and domain fine-tuning, but the PoC can rely on **pre-trained multilingual models** (e.g., MPNet, E5) plus careful chunking and metadata design.

### 2.2 Generation layer

Core responsibilities:

- Take **user queries + retrieved passages** and produce:
  - Clear, accessible explanations.
  - Short comparisons (e.g., “Lotus Sutra vs TNH on compassion”).
  - Citations into the TNH Scholar corpus.
- Respect **stylistic and ethical constraints**:
  - No fabricated citations or sutra names.
  - Clear separation between “what the texts say” and “interpretive framing.”
  - Capacity to answer at multiple levels (beginner, experienced practitioner, academic).

This layer will increasingly be **instruction-tuned and/or fine-tuned** to TNH Scholar’s norms, but early prototypes can use off-the-shelf high-quality LLMs with strong prompt design.

### 2.3 Orchestration and reasoning layer

Core responsibilities:

- Decide **when** to retrieve (not every question needs a heavy RAG pipeline).
- Decide **what** to retrieve:
  - Which corpus? Which language? What level of detail?
  - Should we prefer TNH’s own explanations, classical sources, or both?
- Support **multi-step tasks**:
  - First retrieve background on “mindfulness of breathing,”
  - then retrieve TNH’s own commentary,
  - then synthesize and compare.

Research here connects to **agentic patterns** (e.g., ReAct) and **self-reflective RAG** (e.g., Self-RAG).

## 3. Priority Research Directions

This section outlines concrete directions that are both **scientifically interesting** and **directly applicable** to TNH Scholar.

### 3.1 Multilingual, Canon-Aware Embeddings

**Goal:** Build embedding spaces that respect both **semantic content** and **canonical structure** across languages.

Key questions:

- How well do off-the-shelf multilingual models (e.g., MPNet, E5) capture:
  - Buddhist terms of art (e.g., śūnyatā, interbeing, bodhicitta),
  - doctrinal categories (Four Noble Truths, dependent origination, etc.),
  - cross-lingual parity between Chinese / Vietnamese / English?
- What is the benefit of **fine-tuning bi-encoders** on:
  - Manually curated query–passage pairs (e.g., TNH Scholar training data).
  - Parallel corpora (Chinese ↔ Vietnamese ↔ English sutra translations).
  - TNH-specific writings with aligned translations.

Possible experiments:

- Start with **generic multilingual embeddings** and measure retrieval quality on hand-crafted evaluation sets (e.g., “mindfulness of breathing passages across languages”).
- Introduce **contrastive fine-tuning** using query–passage pairs and evaluate improvement in:
  - Top-k recall for doctrinal questions.
  - Cross-lingual retrieval accuracy (e.g., English query → Chinese or Vietnamese source).

### 3.2 Self-Querying and Metadata-Aware Retrieval

**Goal:** Allow the LLM to **co-design the retrieval query**, including semantic intent and metadata filters.

External work on **self-query retrievers** shows that LLMs can:

- Parse a natural-language query into:
  - A semantic search vector.
  - A structured metadata filter (e.g., `author = TNH`, `language = EN`, `year > 1990`). 
- Improve retrieval quality when document metadata is rich.

TNH Scholar is a natural fit because its documents have (or will have):

- Per-text and per-section metadata: author, era, collection, language, genre.
- Cross-references between canonical sources and TNH commentary.

Possible experiments:

- Build a **minimal self-querying retriever** that:
  - Uses an LLM to propose a metadata filter from the user question.
  - Combines this with vector search in the TNH / CBETA index.
- Evaluate whether self-querying improves:
  - Precision of citations for targeted questions (“Where does Thay discuss climate and interbeing?”).
  - User satisfaction for queries that implicitly assume a particular corpus or timeframe.

### 3.3 Agentic RAG: ReAct-Style Reasoning and Tool Use

**Goal:** Equip TNH Scholar with a light-weight **reason–act loop**, so that it can break down complex queries and call tools (retrievers, databases) step by step.

The **ReAct** pattern (Reason + Act) prompts an LLM to:

- Interleave **“thought” steps** (natural-language reasoning) with
- **“action” steps** (tool calls, e.g., search, metadata lookup).

For TNH Scholar, this could look like:

1. User asks: “Compare how the Lotus Sutra and Thich Nhat Hanh describe compassionate action.”
2. Agent reasoning:
   - Identify: need passages from **Lotus Sutra** and **TNH’s writings** on compassion in action.
   - Issue two searches: one over CBETA/Taishō, one over TNH books.
   - Retrieve top passages, maybe in different languages.
3. Agent then synthesizes similarities and differences, with citations.

Possible experiments:

- Implement a **walking-skeleton ReAct agent** with a small set of tools:
  - `search_cbeta`, `search_tnh`, `fetch_metadata`.
- Constrain its output to **always include citations** and a short explanation of its reasoning steps (for internal debugging and evaluation).
- Compare ReAct-style answers with single-shot RAG answers on multi-hop questions (e.g., “compare,” “trace evolution of an idea,” “relate canonical verse to modern commentary”).

### 3.4 Self-Reflective RAG and Faithfulness

**Goal:** Reduce hallucinations and ensure that generated answers are **faithful to retrieved sources**.

**Self-RAG** proposes training a model that can:

- Decide **when to retrieve**, and when parametric knowledge is enough.
- Insert **special reflection tokens** to:
  - Check whether retrieved passages are relevant.
  - Critique its own draft answer against the evidence. 

TNH Scholar can adapt these ideas without necessarily re-training large models from scratch:

- Define a prompt schema where the LLM:
  - First writes a draft answer.
  - Then explicitly **checks each key claim** against retrieved passages.
  - Marks claims as “directly supported,” “interpretive but consistent,” or “not supported.”
- Optionally, enforce a **“no unsupported claim” mode** where the assistant must either:
  - Provide a citation, or
  - Clearly label content as opinion or extrapolation.

Possible experiments:

- Develop a small suite of “gotcha” questions (e.g., tempt the model to fabricate a sutra name or misattribute a quote), and see how a self-reflective RAG prompt mitigates these errors.
- Explore whether **lightweight fine-tuning** on TNH Scholar reflection tasks improves faithfulness metrics.

### 3.5 Evaluation Frameworks for Dharma-Oriented RAG

**Goal:** Move beyond generic QA metrics and evaluate TNH Scholar along **Dharma-appropriate dimensions**.

Inspired by RAG evaluation work in knowledge-intensive domains (e.g., scientific QA, healthcare), TNH Scholar can define:

- **Faithfulness:** Are claims supported by cited passages? Are citations correct and non-fabricated?
- **Coverage:** Does the system surface a reasonable sample of relevant sources (not just one favorite passage)?
- **Doctrinal accuracy:** For monastic/teacher evaluators, does the answer respect traditional interpretations and avoid serious doctrinal mistakes?
- **Pedagogical suitability:** Is the explanation appropriate for the requested audience (beginner / practitioner / researcher)?

Possible components:

- A **small gold-standard evaluation set** curated by practitioners:
  - Questions, ideal answer sketches, and illustrative source passages.
- A **citation correctness checker**:
  - Human-in-the-loop at first; later possibly supported by automated overlap metrics (e.g., answer-text vs evidence-text similarity).
- Periodic **“Dharma review” sessions** where monastics or senior practitioners score system outputs and feed back into model alignment and retrieval tuning.

### 3.6 Data and Annotation Programs

**Goal:** Create reusable supervision signals to improve retrieval and generation over time.

Key data types:

- **Query–passage pairs** for retriever fine-tuning:
  - Human-generated queries for important passages.
  - GPT-assisted synthetic queries filtered and curated by humans.
- **Parallel corpora** for multilingual alignment:
  - Sutra passages across Chinese/Vietnamese/English.
  - TNH works where multiple translations exist.
- **Explanatory pairs** for generation tuning:
  - Short explanations or commentaries linked to source text.
  - Structured responses (e.g., “context,” “key teaching,” “application to daily life”).

Possible experiments:

- Integrate existing TNH Scholar pipelines (e.g., GPT-based query generation) into a **formal dataset** for retriever training.
- Explore **curriculum-style training**:
  - Start with simple factual questions.
  - Progress to conceptual and comparative questions.
  - Eventually move to multi-hop questions involving multiple sources and eras.

## 4. Walking Skeleton Plan (High-Level)

This section sketches a phased approach that stays faithful to the “walking skeleton” philosophy: minimal viable functionality first, with clear anchors for future complexity.

### Phase 0: PoC Search (Current)

- **Status:** In progress.
- Components:
  - Basic vector index over a small CBETA subset and/or TNH texts.
  - Off-the-shelf multilingual model (e.g., MPNet) for embeddings.
  - Simple similarity search and ranking.
- Goal:
  - Verify that cross-lingual search already surfaces meaningful passages for queries like “compassionate action,” “interbeing,” or “mindfulness of breathing.”

### Phase 1: Baseline RAG

- Add a **generation step** on top of retrieval:
  - Retrieve top-k passages.
  - Feed them into an LLM with a structured prompt to produce:
    - A short explanation.
    - A list of citations.
- Keep the orchestration logic simple:
  - Always retrieve for now.
  - Single corpus (e.g., TNH English texts or a curated CBETA subset).

### Phase 2: Metadata & Self-Querying

- Introduce **metadata-rich indexing**:
  - Author, language, genre, canonical collection.
- Implement a **self-querying retriever**:
  - LLM proposes semantic query + metadata filters.
  - Use this to improve retrieval for focused questions (e.g., “TNH on climate and interbeing,” “Lotus Sutra references only”).

### Phase 3: Agentic RAG (ReAct-Style Walking Skeleton)

- Add a lightweight **ReAct-style agent** with 2–3 tools:
  - `search_cbeta`, `search_tnh`, `lookup_metadata`.
- Teach the agent (via prompting) to:
  - Break down complex questions.
  - Call tools in a small number of steps.
  - Produce answers with explicit citations and a short “reasoning summary” (for debugging and evaluation).

### Phase 4: Self-Reflective & Evaluated RAG

- Experiment with **self-reflective prompts** inspired by Self-RAG:
  - Draft answer → retrieve/reflect → revise answer with evidence labels.
- Define and implement an **evaluation harness**:
  - Faithfulness and citation correctness metrics.
  - Human evaluation protocol with monastics / experienced practitioners.
- Consider **small-scale fine-tuning** on TNH Scholar-specific reflection tasks if early experiments are promising.

## 5. Bibliography and External Resources

This section lists selected external work that is especially relevant to TNH Scholar’s RAG roadmap. It is intentionally opinionated and incomplete; the goal is to anchor future deep dives, not to be exhaustive.

### 5.1 Primary RAG Research

1. **Lewis et al., 2020 – Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks**  
   The original RAG paper, introducing a framework that combines a dense retriever with a sequence-to-sequence generator over a Wikipedia index. Useful as a conceptual baseline and for understanding early design trade-offs.  
   - [ArXiv abstract](https://arxiv.org/abs/2005.11401) 
2. **Gao et al., 2023/2024 – Retrieval-Augmented Generation for Large Language Models: A Survey**  
   A comprehensive survey of RAG for LLMs, organizing the field into Naive, Advanced, and Modular RAG, and discussing retrieval, generation, and augmentation techniques as separate modules. Highly relevant for TNH Scholar’s architectural planning and evaluation design.  
   - [ArXiv survey](https://arxiv.org/abs/2312.10997)  
   - [PDF](https://arxiv.org/pdf/2312.10997) 

### 5.2 Self-Reflective and Faithfulness-Oriented RAG

3. **Asai et al., 2023 – Self-RAG: Learning to Retrieve, Generate, and Critique**  
   Proposes a framework where a single LM learns to decide when to retrieve, how to use retrieved passages, and how to critique its own generations using reflection tokens. Important for TNH Scholar’s goals around reducing hallucinations and explicitly grounding answers in Dharma sources.  
   - [Project page](https://selfrag.github.io/)  
   - [ArXiv / OpenReview entry](https://arxiv.org/abs/2310.11511)  
   - [OpenReview page](https://openreview.net/forum?id=hSyW5go0v8) 

### 5.3 Agentic Patterns and Tool Use

4. **Yao et al., 2022/2023 – ReAct: Synergizing Reasoning and Acting in Language Models**  
   Introduces the ReAct pattern, where LLMs interleave natural-language reasoning with tool calls. Provides a template for TNH Scholar to build agents that can search multiple corpora, inspect metadata, and iteratively refine their answers.  
   - [ArXiv paper](https://arxiv.org/abs/2210.03629)  
   - [PDF](https://arxiv.org/pdf/2210.03629)  
   - [Project page](https://react-lm.github.io/)  
   - [Google AI blog summary](https://research.google/blog/react-synergizing-reasoning-and-acting-in-language-models/) 

### 5.4 Metadata-Aware and Self-Querying Retrieval

5. **Self-Query Retriever (various implementations and guides)**  
   Practical articles describing how to use LLMs to generate structured queries (including metadata filters) for vector stores. While implementation details vary (LangChain, custom frameworks, etc.), the core idea—LLM-driven metadata-aware retrieval—is directly applicable to TNH Scholar’s canonical corpora.  
   - [Enhancing RAG Performance with Metadata: The Power of Self-Query Retrievers](https://medium.com/%40lorevanoudenhove/enhancing-rag-performance-with-metadata-the-power-of-self-query-retrievers-e29d4eecdb73)  
   - [RAG X — Self Query Retriever](https://ai.plainenglish.io/rag-x-self-query-retriever-952dd55c68ed)  
   - [Advanced RAG Techniques: What They Are & How to Use Them](https://falkordb.com/blog/advanced-rag/) 

### 5.5 Practitioner Overviews and Emerging Tooling

6. **Advanced RAG Engineering Guides and Blogs**  
   A growing ecosystem of practitioner-focused articles and frameworks (e.g., Haystack, LlamaIndex, LangChain, vendor-specific stacks) is exploring: multi-hop RAG, hybrid dense+sparse retrieval, re-ranking, and evaluation tooling. These are not Dharma-specific, but they provide implementation patterns and pitfalls that can inform TNH Scholar’s engineering phase.  
   - Example: [Advanced RAG Techniques: What They Are & How to Use Them](https://falkordb.com/blog/advanced-rag/) (already listed above).

---

This document is intentionally high-level and research-oriented. As TNH Scholar matures, each subsection can be expanded into:

- A design document (for a specific RAG component or experiment).
- An ADR (capturing specific architectural and tooling decisions).
- A set of notebooks or scripts in the `research/` or `experiments/` tree, linked back here for provenance.

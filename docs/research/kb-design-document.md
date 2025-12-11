---
title: "TNH Scholar Knowledge Base: Design Document"
description: "Design document for the TNH Scholar knowledge base and semantic search stack."
owner: ""
author: ""
status: current
created: "2025-06-10"
---
# TNH Scholar Knowledge Base: Design Document

Design document for the TNH Scholar knowledge base and semantic search stack.

## Project Overview

The TNH Scholar Knowledge Base project aims to create an AI-driven searchable knowledge base for the works of Thich Nhat Hanh, enabling researchers to perform semantic searches across a comprehensive corpus of teachings. The system will support complex queries ranging from thematic exploration to perspective synthesis while maintaining scholarly accuracy and source attribution.

### Core Objectives

- **Primary Goal**: Enable semantic search across Thich Nhat Hanh's complete works with accurate source attribution
- **Target Users**: Monastics and senior community members for research purposes (internal use only)
- **Output Focus**: Concrete passage references rather than synthesized responses (initially)
- **Technical Approach**: Leverage off-the-shelf systems and technologies where possible

### Query Types to Support

The system must handle diverse query patterns:

1. **Factual Retrieval**: "Where is the best description of touching the earth practice?"
2. **Thematic Exploration**: "Find all works referencing climate change and transcending separate self"
3. **Perspective Analysis**: "What does Thay say about soldiers, police officers, and nonviolence?"
4. **Qualitative Assessment**: "What were some of Thay's most difficult/profound/loving moments?"
5. **Cross-Domain Inquiry**: "Does Thay ever talk about physics and dharma teachings?"
6. **Synthetic Analysis** (future): "What would Thay say about the Israel Palestine conflict today?"

## Content Scope and Processing

### Source Materials

- **Text Sources**: Hundreds of texts in Vietnamese and English (predominant languages)
- **Audio/Video Sources**: Potentially thousands of sources requiring transcription
- **Processing Approach**: All sources converted to digital text with unified metadata structure
- **Transcription Capability**: Robust transcription tools already available in the project

### Content Processing Pipeline

#### 1. Text Normalization

- Consistent formatting, punctuation, and character handling
- Language-specific processing for Vietnamese and English
- Special character and encoding standardization

#### 2. Transcription Integration

- Audio/video content processed through existing transcription tools
- Quality assurance for transcribed content
- Timestamping preservation for multimedia sources

#### 3. Metadata Enrichment

Development of consistent metadata schema including:

**Bibliographic Information**:

- Source identification and publication details
- Date, author/speaker, and publication context
- Original format and processing information

**Content Classification**:

- Topics, themes, and spiritual practices
- Target audiences and contexts
- Relationship to other works in corpus

**Structural Metadata**:

- Position within larger works
- Section and subsection organization
- Cross-references and citations

**Technical Metadata**:

- Processing timestamps and methods
- Language identification and translation links
- Quality scores and confidence measures

#### 4. Text Segmentation Strategy

**Key Decision Point**: Determining optimal chunk size for retrieval

Options for consideration:

- **Paragraph-level chunks**: Balance between context and precision
- **Section-based chunks**: Preserving logical content boundaries  
- **Sliding window approaches**: Overlapping chunks to prevent context loss
- **Hierarchical chunking**: Multiple granularities (section → paragraph → sentence)

## Search and Retrieval Architecture

### Vector Embeddings: Technical Foundation

Vector embeddings convert text into high-dimensional numerical representations where semantically similar content occupies nearby positions in vector space. This enables semantic search beyond keyword matching.

**Key Concepts**:

- Text converted to vectors (lists of numbers) representing meaning
- Similar concepts have mathematically similar vectors
- Search performed by finding nearest neighbors in vector space
- Typical dimensions: 768-3072 numbers per text segment

**Example Flow**:

```plaintext
Text: "The practice of mindful breathing"
→ Embedding Model → [0.016, -0.028, 0.044, ..., 0.037]
```

### Embedding Model Options

#### Commercial Solutions

- **OpenAI text-embedding-3-large**: 3,072 dimensions, high quality, API-based
- **Cohere Embed**: Multilingual support, commercial API
- **Azure AI Embeddings**: Enterprise integration capabilities

#### Open Source Solutions

- **Sentence-BERT (SBERT)**: Wide model variety, multilingual options available
- **E5 Models**: Microsoft's efficient embeddings with strong performance
- **BGE Models**: Multilingual embeddings with strong cross-language capabilities
- **Multilingual Models**: Specialized for Vietnamese-English bilingual corpus

**Key Decision Point**: Commercial vs. Open Source Embedding Strategy

- Commercial: Higher quality, faster development, ongoing costs
- Open Source: Full control, customization potential, infrastructure overhead

### Search Paradigms

#### 1. Vector-Based Semantic Search

- **Approach**: Dense vector embeddings with nearest neighbor search
- **Strengths**: Captures conceptual relationships, handles paraphrasing
- **Limitations**: Computationally expensive, may lose precision on technical terms
- **Best For**: Thematic queries, conceptual exploration

#### 2. Keyword-Based Search  

- **Approach**: Traditional BM25/TF-IDF algorithms with boolean operators
- **Strengths**: Precise terminology matching, computationally efficient
- **Limitations**: Misses semantic relationships, language-dependent
- **Best For**: Exact phrase matching, specific terminology

#### 3. Hybrid Search Systems

- **Approach**: Combining vector and keyword search with result fusion
- **Strengths**: Balances precision and recall, handles diverse query types
- **Limitations**: Complex implementation, requires careful tuning
- **Best For**: Production systems serving varied query patterns

**Recommended Approach**: Start with pure vector search, evolve to hybrid system based on user feedback and query patterns.

### Storage and Infrastructure Options

#### Vector Database Solutions

**Specialized Vector Databases**:

- **Pinecone**: Fully managed, simple API, commercial service
- **Weaviate**: Open-source, schema support, self-hosted or cloud
- **Milvus**: High-performance, enterprise features, complex setup
- **Qdrant**: Fast performance, good filtering, moderate complexity
- **Chroma**: Simple open-source, ideal for prototypes
- **PGVector**: PostgreSQL extension, leverages existing database skills

**Traditional Search with Vector Extensions**:

- **Elasticsearch**: Mature ecosystem, hybrid search capabilities, complex configuration
- **Solr**: Similar to Elasticsearch, vector plugins available

#### Infrastructure Decision Matrix

| Solution | Setup Complexity | Performance | Cost Model | Best For |
|----------|------------------|-------------|------------|----------|
| Pinecone | Low | High | Usage-based | Rapid prototyping |
| Elasticsearch | Medium | High | Infrastructure | Hybrid search needs |
| Chroma | Low | Medium | Self-hosted | Initial development |
| Weaviate | Medium | High | Flexible | Production deployment |

### Advanced Retrieval Techniques

#### Passage Ranking and Re-ranking

Methods to improve relevance of returned results:

- **Cross-Encoders**: Direct query-passage relevance scoring
- **LLM-based Reranking**: Large language models for relevance judgment  
- **Learning to Rank**: Machine learning approaches using multiple features
- **Multi-stage Retrieval**: Initial retrieval followed by sophisticated ranking

#### Query Processing Enhancement

- **Query Expansion**: Adding related terms to improve recall
- **Query Rewriting**: Reformulating queries for better matching
- **Retrieval Augmented Generation for Queries**: LLM-generated query improvements
- **Intent Classification**: Understanding query type to optimize search strategy

## Implementation Pathways

### Fully Commercial Pathway

**Components**:

- Embedding: OpenAI text-embedding-3-large API
- Storage: Pinecone or Azure Cognitive Search
- Query Processing: OpenAI API for query understanding
- Infrastructure: Cloud providers (AWS, Azure, GCP)

**Cost Estimate**: $500-2000/month depending on usage
**Timeline**: 2-4 weeks for initial prototype
**Advantages**: Rapid development, managed infrastructure, high-quality embeddings
**Disadvantages**: Recurring costs, vendor dependency, data privacy considerations

### Fully Open Source Pathway

**Components**:

- Embedding: SBERT, E5, or BGE models (self-hosted)
- Storage: Elasticsearch, Qdrant, or Milvus (self-hosted)
- Query Processing: Open source rerankers, self-hosted LLMs
- Infrastructure: Self-managed servers

**Cost Estimate**: Primarily hardware and operational overhead
**Timeline**: 6-12 weeks for initial prototype  
**Advantages**: No recurring API costs, full control, complete customization
**Disadvantages**: Higher development effort, infrastructure management, technical expertise required

### Hybrid Approach (Recommended for Prototyping)

**Phase 1 - Rapid Prototype**:

- Commercial embedding API + simple vector database
- Focus on core functionality validation
- Minimal infrastructure overhead

**Phase 2 - Production System**:

- Evaluate commercial vs. open source based on Phase 1 learnings
- Implement sophisticated ranking and query processing
- Scale infrastructure based on usage patterns

## Evaluation Framework

### Technical Metrics

**Relevance Metrics**:

- **Precision/Recall**: Classical search performance measures
- **Mean Average Precision (MAP)**: Standard information retrieval metric
- **Normalized Discounted Cumulative Gain (nDCG)**: Ranking quality assessment
- **Mean Reciprocal Rank (MRR)**: Position of first relevant result

**System Performance**:

- Query response time and throughput
- Index size and memory requirements
- Computational resource utilization
- System availability and reliability

### User-Centered Evaluation

**Relevance Assessment**:

- Human judgment of search result quality
- Task completion rates for researchers
- Side-by-side comparison of different approaches
- Feedback collection and analysis systems

**Usage Analytics**:

- Query patterns and frequency analysis
- Result click-through and usage patterns
- User satisfaction surveys and interviews
- Feature usage and adoption metrics

### Evaluation Data Requirements

**Test Query Development**:

- Representative query sets across all supported types
- Ground truth relevance judgments
- Edge cases and challenging queries
- Multilingual query examples

**Benchmark Creation**:

- Gold standard query-document pairs
- Cross-validation datasets for model training
- Hold-out test sets for final evaluation
- Adversarial examples for robustness testing

## Open Decision Points and Areas for Exploration

### 1. Chunking Strategy Selection

**Decision Required**: Optimal text segment size and boundaries
**Options**:

- Paragraph-level with context preservation
- Section-based following logical boundaries
- Sliding window with overlap
- Hierarchical multi-granularity approach

**Exploration Needed**:

- Performance testing with different chunk sizes
- User feedback on result granularity preferences
- Context preservation vs. precision trade-offs

### 2. Multilingual Handling Approach

**Decision Required**: Strategy for Vietnamese-English bilingual corpus
**Options**:

- Separate indices for each language
- Cross-lingual embeddings for unified search
- Translation-based query expansion
- Language-specific optimization

**Exploration Needed**:

- Cross-language retrieval effectiveness
- Translation quality impact on search results
- User preference for language-specific vs. unified results

### 3. Metadata Schema Design

**Decision Required**: Comprehensive metadata structure for all content types
**Critical Elements**:

- Standardization across diverse source materials
- Balance between detail and usability
- Automatic vs. manual metadata generation
- Evolution and versioning strategy

**Exploration Needed**:

- Analysis of existing source material organization
- User requirements for filtering and faceting
- Automated metadata extraction capabilities

### 4. Commercial vs. Open Source Technology Mix

**Decision Required**: Optimal balance of commercial and open source components
**Considerations**:

- Budget constraints and cost predictability
- Data privacy and control requirements
- Development timeline and resource availability
- Long-term maintenance and scaling needs

**Exploration Needed**:

- Pilot testing of different technology combinations
- Total cost of ownership analysis
- Performance and quality comparisons
- Risk assessment for vendor dependencies

### 5. Advanced Feature Development Priority

**Decision Required**: Roadmap for sophisticated features beyond basic retrieval
**Potential Features**:

- Synthetic query answering ("What would Thay say about...")
- Cross-reference and citation analysis
- Temporal analysis of teaching evolution
- Thematic clustering and visualization
- Collaborative annotation and correction systems

**Exploration Needed**:

- User interviews to prioritize feature importance
- Technical feasibility assessment for advanced features
- Resource requirements for feature development
- Integration complexity with core search functionality

### 6. Query-Response Pair Integration Strategy

**Decision Required**: Optimal use of existing query-response pair prototype
**Options**:

- Training data for custom embedding fine-tuning
- Evaluation benchmarks for system performance
- Re-ranking model training data
- Query expansion and reformulation examples

**Exploration Needed**:

- Quality assessment of existing query-response pairs
- Expansion strategies for broader coverage
- Integration methods with chosen search architecture
- Contribution to overall system performance

## Implementation Phases

### Phase 1: Foundation Development (4-6 weeks)

**Objectives**:

- Establish core document processing pipeline
- Implement basic vector search functionality
- Create initial metadata schema
- Develop evaluation framework

**Deliverables**:

- Document ingestion and processing system
- Basic search interface for internal testing
- Initial performance benchmarks
- Technology stack validation

### Phase 2: Enhanced Retrieval (6-8 weeks)

**Objectives**:

- Implement sophisticated ranking and filtering
- Optimize query processing and understanding
- Expand metadata richness and utility
- Integrate user feedback mechanisms

**Deliverables**:

- Production-quality search system
- Comprehensive evaluation results
- User training materials and documentation
- Performance optimization and scaling plan

### Phase 3: Advanced Features (8-12 weeks)

**Objectives**:

- Develop synthetic query capabilities
- Implement collaborative features
- Create analytical and visualization tools
- Establish long-term maintenance procedures

**Deliverables**:

- Feature-complete knowledge base system
- Advanced query processing capabilities
- Analytics dashboard and reporting tools
- Comprehensive system documentation

## Success Criteria

### Technical Success Metrics

- Query response time under 2 seconds for 95% of searches
- Relevance scores above 0.8 for top-3 results on benchmark queries
- System availability above 99% during operating hours
- Support for concurrent users without performance degradation

### User Success Metrics  

- User satisfaction scores above 4.0/5.0 in system evaluation
- Task completion rates above 85% for research queries
- Adoption rate above 90% among target user community
- Positive feedback on system utility and accuracy

### Content Success Metrics

- Coverage of 95% of available source materials
- Metadata completeness above 90% for all indexed content
- Cross-language retrieval accuracy comparable to single-language performance
- Successful handling of all defined query types

This design document provides a comprehensive framework for developing the TNH Scholar Knowledge Base while highlighting critical decision points that require further investigation and stakeholder input. The modular approach allows for iterative development and refinement based on user feedback and technical validation.
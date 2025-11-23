---
title: "TNH Scholar Documentation"
description: "Comprehensive documentation for TNH Scholar, an AI-driven project exploring the teachings of Thich Nhat Hanh."
auto_generated: true
---
# TNH Scholar Documentation

Welcome to the TNH Scholar documentation. This page maps all available documentation organized by topic.

TNH Scholar is an AI-driven project exploring, processing, and translating the teachings of Thich Nhat Hanh and the Plum Village community through natural language processing and machine learning.

## Documentation Map


### Architecture

- [ADR-AT01: AI Text Processing Pipeline Redesign](architecture/ai-text-processing/adr/adr-at01-ai-text-processing.md)
- [ADR-AT02: TextObject Architecture Decision Records](architecture/ai-text-processing/adr/adr-at02-sectioning-textobject.md)
- [TextObject System Design Document](architecture/ai-text-processing/design/textobject-new-design.md)
- [TextObject Original Design](architecture/ai-text-processing/design/textobject-original-design.md)
- [TNH Configuration Management](architecture/configuration/tnh-configuration.md)
- [ADR-DD01: Documentation System Reorganization Strategy](architecture/docs-design/adr/adr-dd01-docs-reorg-strat.md)
- [Documentation Design](architecture/docs-design/design/documentation.md)
- [ADR-A01: Adopt Object-Service for GenAI Interactions](architecture/gen-ai-service/adr/adr-a01-domain-service.md)
- [ADR-A02: PatternCatalog Integration (V1)](architecture/gen-ai-service/adr/adr-a02-pattern-catalog-v1.md)
- [ADR-A08: Configuration / Parameters / Policy Taxonomy](architecture/gen-ai-service/adr/adr-a08-config-params-policy.md)
- [ADR-A09: V1 Simplified Implementation Pathway](architecture/gen-ai-service/adr/adr-a09-v1-simplified.md)
- [ADR-A11: Model Parameters and Strong Typing Fix](architecture/gen-ai-service/adr/adr-a11-model-parameters-fix.md)
- [ADR-A12: Prompt System & Fingerprinting Architecture (V1)](architecture/gen-ai-service/adr/adr-a12-prompt-system-fingerprinting-v1.md)
- [ADR-A13: Migrate All OpenAI Interactions to GenAIService](architecture/gen-ai-service/adr/adr-a13-legacy-client-migration.md)
- [GenAI Service — Design Strategy](architecture/gen-ai-service/design/genai-service-strategy.md)
- [OpenAI Interface Migration Plan](architecture/gen-ai-service/design/migration-plan.md)
- [Generate Markdown Translation JSON Pairs](architecture/jvb-viewer/design/instruction-test0.md)
- [Generate Markdown Vietnamese](architecture/jvb-viewer/design/instruction-test1.md)
- [JVB Viewer — Version 2 Strategy & High‑Level Design](architecture/jvb-viewer/design/jvb-strat-001.md)
- [LUÂN-HỒI](architecture/jvb-viewer/design/output1.md)
- [ADR-K01: Preliminary Architectural Strategy for TNH Scholar Knowledge Base](architecture/knowledge-base/adr/adr-k01-preliminary-architectural-design.md)
- [ADR-MD01: Adoption of JSON-LD for Metadata Management](architecture/metadata/adr/adr-md01-metadata-strategy.md)
- [ADR-PT01: Pattern Access Strategy](architecture/pattern-system/adr/adr-pt01-pattern-access-strategy.md)
- [ADR-PT02: Adopt Pattern and PatternCatalog as Core Concepts](architecture/pattern-system/adr/adr-pt02-pattern-catalog.md)
- [minimal but extensible setup tool for the prototyping phase](architecture/setup-tnh/design/setup-design.md)
- [TNH FAB Design Document](architecture/tnh-fab/design/text-processing-cli-design-v1.md)
- [TNH-FAB Command Line Tool Specification](architecture/tnh-fab/design/text-processing-cli-design-v2.md)
- [ADR-TR01: AssemblyAI Integration for Transcription Service](architecture/transcription/adr/adr-tr01-assemblyai-integration.md)
- [ADR-TR02: Optimized SRT Generation Design](architecture/transcription/adr/adr-tr02-optimize-srt.md)
- [ADR-TR03: Standardizing Timestamps to Milliseconds](architecture/transcription/adr/adr-tr03-standard-timestamp.md)
- [ADR-TR04: AssemblyAI Service Implementation Improvements](architecture/transcription/adr/adr-tr04-assemblyai-improvements.md)
- [Diarization Chunker Module Design Strategy](architecture/transcription/design/additional-design.md)
- [Audio Chunking Algorithm Design Document](architecture/transcription/design/audio-chunk-splitting.md)
- [Simplified Language-Aware Chunking Design](architecture/transcription/design/chunking-strategies.md)
- [Language-Aware Chunking Orchestrator Notes](architecture/transcription/design/chunking-strategies0.md)
- [Diarization Algorithms](architecture/transcription/design/diarization-algorithms.md)
- [Speaker Diarization Algorithm Design](architecture/transcription/design/diarization-algorithms0.md)
- [Speaker Diarization and Time-Mapped Transcription System Design](architecture/transcription/design/diarization-system0.md)
- [Diarization System Design](architecture/transcription/design/diarization-system1.md)
- [Modular Pipeline Design: Best Practices for Audio Transcription and Diarization](architecture/transcription/design/gpt-modular-pipeline.md)
- [Practical Language-Aware Chunking Design](architecture/transcription/design/language-chunking-algorithm.md)
- [Interval-to-Segment Mapping Algorithm](architecture/transcription/design/segment-match-algorithm.md)
- [TimelineMapper Design Document](architecture/transcription/design/timeline-mapping.md)
- [Design Strategy: VS Code as UI/UX Platform for TNH Scholar](architecture/ui-ux/design/ui-ux-strategy.md)
- [TNH‑Scholar Utilities Catalog](architecture/utilities/design/utilities-catalog.md)
- [Package Version Checker Design Document](architecture/utilities/design/version-checking-design.md)
- [ADR-VP01: Video Processing Return Types and Configuration](architecture/video-processing/adr/adr-vp01-video-processing.md)
- [ADR-YF00: Early yt-fetch Transcript Decisions (Historical)](architecture/ytt-fetch/adr/adr-yf00-overview.md)
- [ADR-YF01: YouTube Transcript Source Handling](architecture/ytt-fetch/adr/adr-yf01-transcript-source-handling.md)
- [ADR-YF02: YouTube Transcript Format Selection](architecture/ytt-fetch/adr/adr-yf02-yt-dlp-transcripts.md)
- [YouTube API vs yt-dlp Evaluation](architecture/ytt-fetch/design/yt-dlp-vs-youtube-api.md)

### Cli

- [audio-transcribe](cli/audio-transcribe.md)
- [nfmt](cli/nfmt.md)
- [Command Line Tools Overview](cli/overview.md)
- [tnh-fab](cli/tnh-fab.md)
- [tnh-setup](cli/tnh-setup.md)
- [token-count](cli/token-count.md)
- [ytt-fetch](cli/ytt-fetch.md)

### Cli Reference

- [audio-transcribe](cli-reference/audio-transcribe.md)
- [json-to-srt](cli-reference/json-to-srt.md)
- [nfmt](cli-reference/nfmt.md)
- [sent-split](cli-reference/sent-split.md)
- [srt-translate](cli-reference/srt-translate.md)
- [tnh-fab](cli-reference/tnh-fab.md)
- [tnh-setup](cli-reference/tnh-setup.md)
- [token-count](cli-reference/token-count.md)
- [ytt-fetch](cli-reference/ytt-fetch.md)

### Development

- [API Integration Blueprint (Generic)](development/architecture/api-integration-blueprint_(old).md)
- [Object–Service Design Blueprint (Integrated)](development/architecture/object-service-design-blueprint-v2.md)
- [TNH Scholar Object & Service Design Blueprint](development/architecture/object-service-design-blueprint.md)
- [Object-Service Design Blueprint: Critical Gaps & Clarifications](development/architecture/object-service-gaps.md)
- [Contributing to TNH Scholar (Prototype Phase)](development/contributing.md)
- [TNH Scholar Design Guide](development/design-guide.md)
- [Fine Tuning Strategy](development/fine-tuning-strategy.md)
- [Human-AI Software Engineering Principles](development/human-agent-coding-principles.md)
- [Improvements / Initial structure](development/initial-improvements.md)
- [Core Pattern Architecture: Meta-patterns, Textual Expansion Processing](development/pattern-core-design.md)
- [TNH Scholar System Design](development/system-design.md)
- [yt-dlp Format Selection Guide](development/yt-dlp_docs/ytdlp-formats.md)
- [yt-dlp Comprehensive Guide](development/yt-dlp_docs/ytdlp-guide.md)

### Docs Ops

- [ADR Template](docs-ops/adr-template.md)
- [Markdown Standards](docs-ops/markdown-standards.md)

### Getting Started

- [Configuration](getting-started/configuration.md)
- [Installation](getting-started/installation.md)
- [Quick Start Guide](getting-started/quick-start.md)

### Research

- [1-3 Word Queries](research/gpt_4o_search_query_text_pair_testing/testing_input_output.md)
- [Passage Test](research/gpt_4o_translations_experiments/passage_test.md)
- [GPT Development Convos](research/gpt_development_convos.md)
- [**Summary Report on Metadata Extraction, Source Parsing, and Model Training for TNH-Scholar**](research/metadata_report.md)
- [Preliminary Feasibility Study](research/preliminary_feasibility_study.md)
- [Structural-Informed Adaptive Processing (SIAP) Methodology](research/strategic-information-processing.md)
- [TNH Scholar Knowledge Base: Design Document](research/tnh-scholar-knowledge-vector-search.md)

### User Guide

- [Best Practices](user-guide/best-practices.md)
- [User Guide Overview](user-guide/overview.md)
- [TNH Scholar Pattern System](user-guide/patterns.md)

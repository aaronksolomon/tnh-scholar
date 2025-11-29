---
title: TNH Scholar Documentation
description: Comprehensive documentation for TNH Scholar, an AI-driven project exploring,
  processing, and translating the teachings of Thich Nhat Hanh.
---

# TNH Scholar Documentation

TNH Scholar is an AI-driven project designed to explore, process, and translate the teachings of Thich Nhat Hanh and the Plum Village community. For a more concise intro to the project, see the [README](project/repo-root/repo-readme.md). This document contains deeper onboarding and architectural context.

## Vision & Goals

- **Make Plum Village teachings accessible, discoverable, and navigable** through modern AI workflows, multimodal interfaces, and structured corpora.  
- **Translate teachings across languages with precision and cultural sensitivity**, while maintaining robust **provenance**, **version history**, and **source transparency**.  
- **Convert audio, video, and archival transcripts into structured, searchable formats**, enabling deep research on dharma talks and historical materials.  
- **Organize, index, and search key concepts, themes, and doctrinal insights** across Thich Nhat Hanh’s written works, talks, poems, letters, and journal materials.  
- **Provide reliable, high-fidelity tools for practitioners, developers, historians, and researchers**, spanning everything from simple lookups to advanced analysis.  
- **Support scholarly research for monastic and lay students** in the Plum Village tradition, encouraging rigorous engagement with texts, commentary, and historical context.  
- **Discover subtle connections between teachings, topics, and practices** through embeddings, cross-lingual alignment, metadata, and semantic search.  
- **Engage with the tradition through interactive and programmatic tools**, including APIs, conversational agents, structured datasets, translation assistants, and learning modules.  
- **Build a canonical, clean, multi-lingual corpus** (Vietnamese, English, French, Chinese, Tibetan, etc.) with sentence-level alignment, footnotes, metadata, and context markers.  
- **Preserve historical materials** (e.g., 1950s Vietnamese Buddhist journals, manuscripts, early Plum Village publications) with accurate OCR, restoration, and annotation.  
- **Ensure long-term reproducibility, integrity, and openness** through consistent provenance tracking, fingerprinting, and transparent model-training workflows.  
- **Enable deep comparative Buddhist studies** through cross-text indexing (Pali, Sanskrit, Chinese, Tibetan canons) and alignments of terminology, concepts, and doctrinal parallels.  
- **Provide tools for teaching and learning**, including guided exploration, topic overviews, glossaries, bilingual reading tools, and structured learning pathways.
- **Serve as a foundation for future embodied or dialogical systems**, including guided practice companions, study assistants, and advanced interactive Dharma tools.

> **Note on Terminology**: Earlier versions of TNH Scholar referred to engineered AI prompts as "Patterns" to emphasize their engineering pattern nature. Current documentation uses "Prompt" to align with industry standards. References to "Pattern" in legacy documentation should be read as "Prompt".

## Features

- **Audio and transcript processing**: `audio-transcribe` with diarization and YouTube support
- **Text formatting and translation**: `tnh-fab` for punctuation, translation, sectioning, and prompt-driven processing
- **Acquisition utilities**: `ytt-fetch` for transcripts; `token-count` and `nfmt` for prep and planning
- **Setup and configuration**: `tnh-setup` plus guided config in Getting Started
- **Prompt system**: See [Prompt System Architecture](architecture/prompt-system/prompt-architecture.md) and [ADR-PT03](architecture/prompt-system/adr/adr-pt03-current-status-roadmap.md) for current status and roadmap

## Quick Start

- Install from PyPI and run the setup helper:

  ```bash
  pip install tnh-scholar
  tnh-setup
  ```

- Configure credentials (OpenAI, optional Google Vision) per [Configuration](getting-started/configuration.md)
- Run your first workflow via the [Quick Start Guide](getting-started/quick-start.md)

## Getting Started (persona-based)

- **Practitioners**: Follow [Installation](getting-started/installation.md), then the [Quick Start Guide](getting-started/quick-start.md); explore workflows in the [User Guide](user-guide/overview.md)
- **Developers**: Set up via [DEV_SETUP.md](https://github.com/aaronksolomon/tnh-scholar/blob/main/DEV_SETUP.md) and [Contributing](https://github.com/aaronksolomon/tnh-scholar/blob/main/CONTRIBUTING.md); review [System Design](development/system-design.md), [Style Guide](development/style-guide.md), and [Design Principles](development/design-principles.md); see the [CLI Overview](cli/overview.md)
- **Researchers**: Start with [Research](research/) for experiments and notes; for knowledge-base direction see [ADR-K01](architecture/knowledge-base/adr/adr-k01-preliminary-architectural-design.md); review [Architecture](architecture/) for transcription/translation pipelines

## Architecture Overview

- **Docs strategy**: [ADR-DD01](architecture/docs-system/adr/adr-dd01-docs-reorg-strat.md) and [ADR-DD02](architecture/docs-system/adr/adr-dd02-docs-content-nav.md)
- **GenAI service layer**: See [GenAI Service Strategy](architecture/gen-ai-service/design/genai-service-strategy.md) and the ADR-A series.
- **Transcription pipeline**: See [ADR-TR01](architecture/transcription/adr/adr-tr01-assemblyai-integration.md) and related ADR-TR docs (diarization, chunking, timing).
- **Prompt design**: See [Prompt Architecture](architecture/prompt-system/prompt-architecture.md) and [ADR-PT03](architecture/prompt-system/adr/adr-pt03-current-status-roadmap.md) for current status; archived ADRs in [archive/adr/](architecture/prompt-system/archive/adr/)
- **System design references**: [Object-Service Design](architecture/object-service/design-overview.md) and [System Design](development/system-design.md)

## Development

- Common commands: `make test`, `make lint`, `make format`, `make docs`, `poetry run mypy src/`
- Optional dependency groups (development only): `tnh-scholar[ocr]`, `tnh-scholar[gui]`, `tnh-scholar[query]`, `tnh-scholar[dev]`
- Troubleshooting and workflows: [DEV_SETUP.md](https://github.com/aaronksolomon/tnh-scholar/blob/main/DEV_SETUP.md)

## Contributing

See [CONTRIBUTING.md](https://github.com/aaronksolomon/tnh-scholar/blob/main/CONTRIBUTING.md) for coding standards, testing expectations, and PR workflow. We welcome contributions from practitioners, developers, and scholars.

## Documentation Overview

- **Getting Started**: Installation, configuration, first-run guidance
- **User Guide**: Task-oriented workflows and practical how-tos
- **CLI Reference**: Auto-generated command documentation for every CLI entry point
- **API**: Python API reference (mkdocstrings)
- **Architecture**: ADRs, design docs, system diagrams by component
- **Development**: Contributor guides, design principles, engineering practices
- **Docs Ops**: Style guides, ADR template, documentation maintenance
- **Research**: Experiments, evaluations, exploratory notes

## Project Status

TNH Scholar is currently in **alpha stage**. Expect ongoing API and workflow changes during active development.

## Support & Community

- Bug reports & feature requests: [GitHub Issues](https://github.com/aaronksolomon/tnh-scholar/issues)
- Questions & discussions: [GitHub Discussions](https://github.com/aaronksolomon/tnh-scholar/discussions)

## License

This project is licensed under the [GPL-3.0 License](https://github.com/aaronksolomon/tnh-scholar/blob/main/LICENSE).

## Documentation Map

### Architecture

- [ADR-AT01: AI Text Processing Pipeline Redesign](architecture/ai-text-processing/adr/adr-at01-ai-text-processing.md)
- [ADR-AT02: TextObject Architecture Decision Records](architecture/ai-text-processing/adr/adr-at02-sectioning-textobject.md)
- [TextObject System Design Document](architecture/ai-text-processing/design/textobject-new-design.md)
- [TextObject Original Design](architecture/ai-text-processing/design/textobject-original-design.md)
- [TNH Configuration Management](architecture/configuration/tnh-configuration.md)
- [ADR-DD01: Documentation System Reorganization Strategy](architecture/docs-system/adr/adr-dd01-docs-reorg-strat.md)
- [ADR-DD02: Documentation Main Content and Navigation Strategy](architecture/docs-system/adr/adr-dd02-docs-content-nav.md)
- [Documentation Design](architecture/docs-system/design/documentation.md)
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
- [ADR-PT03: Prompt System Current Status & Roadmap](architecture/prompt-system/adr/adr-pt03-current-status-roadmap.md)
- [Prompt System Architecture](architecture/prompt-system/prompt-architecture.md)
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

- [ADR-OS01: Object-Service Design Architecture V3](architecture/object-service/adr/adr-os01-design-v3.md)
- [Object-Service Design Overview](architecture/object-service/design-overview.md)
- [Object-Service Implementation Status](architecture/object-service/implementation-status.md)
- [Contributing to TNH Scholar (Prototype Phase)](development/contributing.md)
- [TNH Scholar Style Guide](development/style-guide.md)
- [TNH Scholar Design Principles](development/design-principles.md)
- [Fine Tuning Strategy](development/fine-tuning-strategy.md)
- [Human-AI Software Engineering Principles](development/human-agent-coding-principles.md)
- [Improvements / Initial structure](development/initial-improvements.md)
- [TNH Scholar System Design](development/system-design.md)

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
- [TNH Scholar Prompt System](user-guide/prompts.md)

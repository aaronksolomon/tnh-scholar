---
title: TNH Scholar
description: Comprehensive documentation for TNH Scholar, an AI-driven project exploring,
  processing, and translating the teachings of Thich Nhat Hanh.
---


# TNH Scholar

TNH Scholar is an AI-driven project designed to explore, process, and translate the teachings of Thich Nhat Hanh and the Plum Village community. For a more concise intro to the project, see the [README](project/repo-root/repo-readme.md). This document contains deeper onboarding and architectural context.

## Vision & Aspirations

TNH Scholar is a long-term effort to support the **living Plum Village tradition** with trustworthy, transparent digital tools. This work is intended, both in development and usage, to deeply respect the tradition and practice of Thay Nhất Hạnh and the Plum Village community.

- Build a **canonical, multilingual corpus** of Thích Nhất Hạnh's teachings with high-fidelity text, rich metadata, and sentence-level alignment across languages.
- Provide **AI-assisted research tools** that expose their reasoning and keep human judgment central, serving monastics, practitioners, teachers, and researchers.
- Support **cross-lingual research** across Vietnamese, English, French, Chinese, Pāli, Sanskrit, Tibetan, and other sources.
- Enable **rich interactive environments** like bilingual readers combining scans, text, translations, and audio.
- Enable **human-supervised AI workflows** for corpus processing, translation, and evaluation.

This work is envisioned on a **multi-year to multi-decade timescale**. The CLI tools and GenAI Service in this repository are the **early infrastructure** for that larger arc.

For the full description, including scope, non-scope, relationship to spin-offs, and time horizon, see:

- [TNH Scholar Project Vision (in project/vision)](project/vision.md)

---

> **Note on Terminology**: Earlier versions of TNH Scholar referred to engineered AI prompts as "Patterns" to emphasize their engineering pattern nature. Current documentation uses "Prompt" to align with industry standards. References to "Pattern" in legacy documentation should be read as "Prompt".

---

## Features

- **Audio and transcript processing**: `audio-transcribe` with diarization and YouTube support
- **Text formatting and translation**: `tnh-fab` for punctuation, translation, sectioning, and prompt-driven processing
- **Acquisition utilities**: `ytt-fetch` for transcripts; `token-count` and `nfmt` for prep and planning
- **Setup and configuration**: `tnh-setup` plus guided config in Getting Started
- **Prompt system**: See [Prompt System Architecture](architecture/prompt-system/prompt-system-architecture.md) and [ADR-PT03](architecture/prompt-system/adr/adr-pt03-prompt-system-status-roadmap.md) for current status and roadmap

## Quick Start (for those wishing to use the tools)

- Install from PyPI and run the setup helper:

  ```bash
  pip install tnh-scholar
  tnh-setup
  ```

- Configure credentials (OpenAI, optional Google Vision) per [Configuration](getting-started/configuration.md)
- Run your first workflow via the [Quick Start Guide](getting-started/quick-start-guide.md)

## Getting Started (persona-based)

- **Practitioners**: Follow [Installation](getting-started/installation.md), then the [Quick Start Guide](getting-started/quick-start-guide.md); explore workflows in the [User Guide](user-guide/overview.md)
- **Developers**: Set up via [DEV_SETUP.md](https://github.com/aaronksolomon/tnh-scholar/blob/main/DEV_SETUP.md) and [Contributing](https://github.com/aaronksolomon/tnh-scholar/blob/main/CONTRIBUTING.md); review [System Design](development/system-design.md), [Style Guide](development/style-guide.md), and [Design Principles](development/design-principles.md); see the [CLI Overview](cli-reference/overview.md)
- **Researchers**: Start with [Research](research/index.md) for experiments and notes; for knowledge-base direction see [ADR-K01](architecture/knowledge-base/adr/adr-k01-kb-architecture-strategy.md); review [Architecture](architecture/overview.md) for transcription/translation pipelines

## Architecture Overview

- **Docs strategy**: [ADR-DD01](architecture/docs-system/adr/adr-dd01-docs-reorg-strategy.md) and [ADR-DD02](architecture/docs-system/adr/adr-dd02-main-content-nav.md)
- **GenAI service layer**: See [GenAI Service Strategy](architecture/gen-ai-service/design/genai-service-design-strategy.md) and the ADR-A series.
- **Transcription pipeline**: See [ADR-TR01](architecture/transcription/adr/adr-tr01-assemblyai-integration.md) and related ADR-TR docs (diarization, chunking, timing).
- **Prompt design**: See [Prompt Architecture](architecture/prompt-system/prompt-system-architecture.md) and [ADR-PT03](architecture/prompt-system/adr/adr-pt03-prompt-system-status-roadmap.md) for current status.
- **System design references**: [Object-Service Design](architecture/object-service/object-service-design-overview.md) and [System Design](development/system-design.md)

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
- [TextObject Original Design](architecture/ai-text-processing/design/textobject-original-design.md)
- [TextObject System Design Document](architecture/ai-text-processing/design/textobject-system-design.md)
- [TNH Configuration Management](architecture/configuration/tnh-configuration-management.md)
- [ADR-DD01: Documentation System Reorganization Strategy](architecture/docs-system/adr/adr-dd01-docs-reorg-strategy.md)
- [ADR-DD02: Documentation Main Content and Navigation Strategy](architecture/docs-system/adr/adr-dd02-main-content-nav.md)
- [ADR-DD03: Pattern to Prompt Terminology Standardization](architecture/docs-system/adr/adr-dd03-pattern-to-prompt.md)
- [Adr Dd03 Phase1 Punchlist](architecture/docs-system/adr/adr-dd03-phase1-punchlist.md)
- [Documentation Design](architecture/docs-system/design/documentation-design.md)
- [ADR-A01: Adopt Object-Service for GenAI Interactions](architecture/gen-ai-service/adr/adr-a01-object-service-genai.md)
- [ADR-A02: PatternCatalog Integration (V1)](architecture/gen-ai-service/adr/adr-a02-patterncatalog-integration-v1.md)
- [ADR-A08: Configuration / Parameters / Policy Taxonomy](architecture/gen-ai-service/adr/adr-a08-config-params-policy-taxonomy.md)
- [ADR-A09: V1 Simplified Implementation Pathway](architecture/gen-ai-service/adr/adr-a09-v1-simplified.md)
- [ADR-A11: Model Parameters and Strong Typing Fix](architecture/gen-ai-service/adr/adr-a11-model-parameters-fix.md)
- [ADR-A12: Prompt System & Fingerprinting Architecture (V1)](architecture/gen-ai-service/adr/adr-a12-prompt-system-fingerprinting-v1.md)
- [ADR-A13: Migrate All OpenAI Interactions to GenAIService](architecture/gen-ai-service/adr/adr-a13-migrate-openai-to-genaiservice.md)
- [GenAI Service — Design Strategy](architecture/gen-ai-service/design/genai-service-design-strategy.md)
- [OpenAI Interface Migration Plan](architecture/gen-ai-service/design/openai-interface-migration-plan.md)
- [Generate Markdown Translation JSON Pairs](architecture/jvb-viewer/design/generate-md-translation-json-pairs.md)
- [Generate Markdown Vietnamese](architecture/jvb-viewer/design/generate-md-vietnamese.md)
- [JVB Viewer — Version 2 Strategy & High‑Level Design](architecture/jvb-viewer/design/jvb-viewer-v2-strategy.md)
- [LUÂN-HỒI](architecture/jvb-viewer/design/luan-hoi.md)
- [ADR-K01: Preliminary Architectural Strategy for TNH Scholar Knowledge Base](architecture/knowledge-base/adr/adr-k01-kb-architecture-strategy.md)
- [ADR-MD01: Adoption of JSON-LD for Metadata Management](architecture/metadata/adr/adr-md01-json-ld-metadata.md)
- [ADR-OS01: Object-Service Design Architecture V3](architecture/object-service/adr/adr-os01-object-service-architecture-v3.md)
- [Object-Service Design Overview](architecture/object-service/object-service-design-overview.md)
- [Object-Service Implementation Status](architecture/object-service/object-service-implementation-status.md)
- [Architecture Overview](architecture/overview.md)
- [ADR-PT03: Prompt System Current Status & Roadmap](architecture/prompt-system/adr/adr-pt03-prompt-system-status-roadmap.md)
- [ADR-PT01: Pattern Access Strategy](architecture/prompt-system/archive/adr/adr-pt01-pattern-access-strategy.md)
- [ADR-PT02: Adopt Pattern and PatternCatalog as Core Concepts](architecture/prompt-system/archive/adr/adr-pt02-adopt-pattern-and-patterncatalog.md)
- [Core Pattern Architecture: Meta-patterns, Textual Expansion Processing](architecture/prompt-system/archive/core-pattern-architecture.md)
- [Prompt System Architecture](architecture/prompt-system/prompt-system-architecture.md)
- [minimal but extensible setup tool for the prototyping phase](architecture/setup-tnh/design/setup-tnh-minimal-extensible-tool.md)
- [TNH-FAB Command Line Tool Specification](architecture/tnh-fab/design/tnh-fab-cli-spec.md)
- [TNH FAB Design Document](architecture/tnh-fab/design/tnh-fab-design-document.md)
- [ADR-TR01: AssemblyAI Integration for Transcription Service](architecture/transcription/adr/adr-tr01-assemblyai-integration.md)
- [ADR-TR02: Optimized SRT Generation Design](architecture/transcription/adr/adr-tr02-optimized-srt-design.md)
- [ADR-TR03: Standardizing Timestamps to Milliseconds](architecture/transcription/adr/adr-tr03-ms-timestamps.md)
- [ADR-TR04: AssemblyAI Service Implementation Improvements](architecture/transcription/adr/adr-tr04-assemblyai-improvements.md)
- [Audio Chunking Algorithm Design Document](architecture/transcription/design/audio-chunking-design.md)
- [Diarization Algorithms](architecture/transcription/design/diarization-algorithms.md)
- [Diarization Chunker Module Design Strategy](architecture/transcription/design/diarization-chunker-design.md)
- [Diarization System Design](architecture/transcription/design/diarization-system-design.md)
- [Interval-to-Segment Mapping Algorithm](architecture/transcription/design/interval-to-segment-mapping.md)
- [Simplified Language-Aware Chunking Design](architecture/transcription/design/language-aware-chunking-design.md)
- [Language-Aware Chunking Orchestrator Notes](architecture/transcription/design/language-aware-chunking-orchestrator-notes.md)
- [Modular Pipeline Design: Best Practices for Audio Transcription and Diarization](architecture/transcription/design/modular-pipeline-best-practices.md)
- [Practical Language-Aware Chunking Design](architecture/transcription/design/practical-language-aware-chunking.md)
- [Speaker Diarization Algorithm Design](architecture/transcription/design/speaker-diarization-algorithm-design.md)
- [Speaker Diarization and Time-Mapped Transcription System Design](architecture/transcription/design/speaker-diarization-time-mapped-design.md)
- [TimelineMapper Design Document](architecture/transcription/design/timelinemapper-design.md)
- [Design Strategy: VS Code as UI/UX Platform for TNH Scholar](architecture/ui-ux/design/vs-code-as-ui-platform.md)
- [Adr Vsc01 Vscode Integration Strategy](architecture/ui-ux/vs-code-integration/adr-vsc01-vscode-integration-strategy.md)
- [Adr Vsc02 Tnh Gen Cli Implementation](architecture/ui-ux/vs-code-integration/adr-vsc02-tnh-gen-cli-implementation.md)
- [Package Version Checker Design Document](architecture/utilities/design/package-version-checker-design.md)
- [TNH‑Scholar Utilities Catalog](architecture/utilities/design/utilities-catalog.md)
- [ADR-VP01: Video Processing Return Types and Configuration](architecture/video-processing/adr/adr-vp01-video-processing.md)
- [ADR-YF00: Early yt-fetch Transcript Decisions (Historical)](architecture/ytt-fetch/adr/adr-yf00-early-decisions.md)
- [ADR-YF01: YouTube Transcript Source Handling](architecture/ytt-fetch/adr/adr-yf01-yt-transcript-source-handling.md)
- [ADR-YF02: YouTube Transcript Format Selection](architecture/ytt-fetch/adr/adr-yf02-yt-transcript-format-selection.md)
- [YouTube API vs yt-dlp Evaluation](architecture/ytt-fetch/design/youtube-api-vs-yt-dlp-eval.md)

### Cli

- [audio-transcribe](cli-reference/audio-transcribe.md)
- [nfmt](cli-reference/nfmt.md)
- [Command Line Tools Overview](cli-reference/overview.md)
- [tnh-fab](cli-reference/tnh-fab.md)
- [tnh-setup](cli-reference/tnh-setup.md)
- [token-count](cli-reference/token-count.md)
- [ytt-fetch](cli-reference/ytt-fetch.md)

### Community

- [Parallax Overview](community/parallax-overview.md)

### Development

- [Contributing to TNH Scholar (Prototype Phase)](development/contributing-prototype-phase.md)
- [TNH Scholar Design Principles](development/design-principles.md)
- [Fine Tuning Strategy](development/fine-tuning-strategy.md)
- [Human-AI Software Engineering Principles](development/human-ai-software-engineering-principles.md)
- [Improvements / Initial structure](development/improvements-initial-structure.md)
- [Development Documentation](development/overview.md)
- [TNH Scholar Style Guide](development/style-guide.md)
- [TNH Scholar System Design](development/system-design.md)

### Docs Ops

- [ADR Template](docs-ops/adr-template.md)
- [Markdown Standards](docs-ops/markdown-standards.md)
- [MkDocs Strict Warning Backlog](docs-ops/mkdocs-strict-warning-backlog.md)
- [Preview TNH Scholar Theme](docs-ops/preview-theme.md)
- [TNH Scholar Theme Design](docs-ops/theme-design.md)

### Getting Started

- [Configuration](getting-started/configuration.md)
- [Installation](getting-started/installation.md)
- [Quick Start Guide](getting-started/quick-start-guide.md)

### Project

- [Conceptual Architecture](project/conceptual-architecture.md)
- [Future Directions](project/future-directions.md)
- [Philosophy](project/philosophy.md)
- [Principles](project/principles.md)
- [TNH Scholar CHANGELOG](project/repo-root/changelog.md)
- [TNH Scholar CONTRIBUTING](project/repo-root/contributing-root.md)
- [TNH-Scholar DEV_SETUP](project/repo-root/dev-setup-guide.md)
- [TNH Scholar Release Checklist](project/repo-root/release_checklist.md)
- [TNH Scholar README](project/repo-root/repo-readme.md)
- [TNH Scholar TODO List](project/repo-root/todo-list.md)
- [Vision](project/vision.md)

### Research

- [1-3 Word Queries](research/gpt4o-search-query-testing/queries-1-3-words.md)
- [Passage Test](research/gpt4o-translation-experiments/passage_test.md)
- [GPT Development Convos](research/gpt_development_convos.md)
- [TNH Scholar Knowledge Base: Design Document](research/kb-design-document.md)
- [Summary Report on Metadata Extraction, Source Parsing, and Model Training for TNH-Scholar](research/metadata-summary-report.md)
- [Preliminary Feasibility Study](research/preliminary-feasibility-study.md)
- [Structural-Informed Adaptive Processing (SIAP) Methodology](research/siap-methodology.md)

### User Guide

- [Best Practices](user-guide/best-practices.md)
- [User Guide Overview](user-guide/overview.md)
- [TNH Scholar Prompt System](user-guide/prompt-system.md)

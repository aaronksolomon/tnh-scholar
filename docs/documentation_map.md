---
title: "Documentation Map"
description: "Hierarchical navigation of TNH Scholar documentation"
owner: "Documentation Working Group"
author: "Docs Automation"
status: "current"
created: "2026-02-07"
auto_generated: true
---

# Documentation Map

Auto-generated map of the documentation hierarchy. Regenerated during docs builds; edit source content instead of this file.

## Getting Started

- [Configuration](/getting-started/configuration.md)
- [Installation](/getting-started/installation.md)
- [Quick Start Guide](/getting-started/quick-start-guide.md)

## User Guide

- [Best Practices](/user-guide/best-practices.md)
- [TNH Scholar Prompt System](/user-guide/prompt-system.md)
- [User Guide Overview](/user-guide/overview.md)

## Project

- [Conceptual Architecture of TNH-Scholar](/project/conceptual-architecture.md)
- [Future Directions of TNH-Scholar](/project/future-directions.md)
- [TNH Scholar CHANGELOG](/project/repo-root/changelog.md)
- [TNH Scholar CONTRIBUTING](/project/repo-root/contributing-root.md)
- [TNH Scholar README](/project/repo-root/repo-readme.md)
- [TNH Scholar Release Checklist](/project/repo-root/release_checklist.md)
- [TNH Scholar TODO List](/project/repo-root/todo-list.md)
- [TNH Scholar Versioning Policy](/project/repo-root/versioning.md)
- [TNH-Scholar DEV_SETUP](/project/repo-root/dev-setup-guide.md)
- [TNH-Scholar Project Philosophy](/project/philosophy.md)
- [TNH-Scholar Project Principles](/project/principles.md)
- [TNH-Scholar Project Vision](/project/vision.md)

## Community

- [TNH-Scholar: Project Overview for Parallax Press & Plum Village Editorial Community](/community/parallax-overview.md)

## CLI Reference

- [audio-transcribe](/cli-reference/audio-transcribe.md)
- [Command Line Tools Overview](/cli-reference/overview.md)
- [json-to-srt](/cli-reference/json-to-srt.md)
- [nfmt](/cli-reference/nfmt.md)
- [sent-split](/cli-reference/sent-split.md)
- [srt-translate](/cli-reference/srt-translate.md)
- [tnh-gen](/cli-reference/tnh-gen.md)
- [tnh-setup](/cli-reference/tnh-setup.md)
- [token-count](/cli-reference/token-count.md)
- [ytt-fetch](/cli-reference/ytt-fetch.md)

## Architecture

- [ADR-A01: Adopt Object-Service for GenAI Interactions](/architecture/gen-ai-service/adr/adr-a01-object-service-genai.md)
- [ADR-A02: PatternCatalog Integration (V1)](/architecture/gen-ai-service/adr/adr-a02-patterncatalog-integration-v1.md)
- [ADR-A08: Configuration / Parameters / Policy Taxonomy](/architecture/gen-ai-service/adr/adr-a08-config-params-policy-taxonomy.md)
- [ADR-A09: V1 Simplified Implementation Pathway](/architecture/gen-ai-service/adr/adr-a09-v1-simplified.md)
- [ADR-A11: Model Parameters and Strong Typing Fix](/architecture/gen-ai-service/adr/adr-a11-model-parameters-fix.md)
- [ADR-A12: Prompt System & Fingerprinting Architecture (V1)](/architecture/gen-ai-service/adr/adr-a12-prompt-system-fingerprinting-v1.md)
- [ADR-A13: Migrate All OpenAI Interactions to GenAIService](/architecture/gen-ai-service/adr/adr-a13-migrate-openai-to-genaiservice.md)
- [ADR-A14.1: Registry Staleness Detection and User Warnings](/architecture/gen-ai-service/adr/adr-a14.1-registry-staleness-detection.md)
- [ADR-A14: File-Based Registry System for Provider Metadata](/architecture/gen-ai-service/adr/adr-a14-file-based-registry-system.md)
- [ADR-A15: Thread Safety and Rate Limiting](/architecture/gen-ai-service/adr/adr-a15-thread-safety-rate-limiting.md)
- [ADR-AT01: AI Text Processing Pipeline Redesign](/architecture/ai-text-processing/adr/adr-at01-ai-text-processing.md)
- [ADR-AT02: TextObject Architecture Decision Records](/architecture/ai-text-processing/adr/adr-at02-sectioning-textobject.md)
- [ADR-AT03.1: AT03→AT04 Transition Plan](/architecture/ai-text-processing/adr/adr-at03.1-transition-plan.md)
- [ADR-AT03.2: NumberedText Section Boundary Validation](/architecture/ai-text-processing/adr/adr-at03.2-numberedtext-validation.md)
- [ADR-AT03.3: TextObject Robustness and Metadata Management](/architecture/ai-text-processing/adr/adr-at03.3-textobject-robustness.md)
- [ADR-AT03: Minimal AI Text Processing Refactor for tnh-gen](/architecture/ai-text-processing/adr/adr-at03-object-service-refactor.md)
- [ADR-AT04: AI Text Processing Platform Strategy](/architecture/ai-text-processing/adr/adr-at04-ai-text-processing-platform-strat.md)
- [ADR-CF01: Runtime Context & Configuration Strategy](/architecture/configuration/adr/adr-cf01-runtime-context-strategy.md)
- [ADR-CF02: Prompt Catalog Discovery Strategy](/architecture/configuration/adr/adr-cf02-prompt-catalog-discovery.md)
- [ADR-DD01: Documentation System Reorganization Strategy](/architecture/docs-system/adr/adr-dd01-docs-reorg-strategy.md)
- [ADR-DD02: Documentation Main Content and Navigation Strategy](/architecture/docs-system/adr/adr-dd02-main-content-nav.md)
- [ADR-DD03: Pattern to Prompt Terminology Standardization](/architecture/docs-system/adr/adr-dd03-pattern-to-prompt.md)
- [ADR-DD03: Phase 1 Execution Punch List](/architecture/docs-system/adr/adr-dd03-phase1-punchlist.md)
- [ADR-JV03: Canonical XML AST for English Parsing](/architecture/jvb-viewer/adr/adr-jv03-canonical-xml-ast.md)
- [ADR-JVB01: JVB Parallel Viewer v1 As-Built](/architecture/jvb-viewer/adr/adr-jvb01_as-built_jvb_viewer_v1.md)
- [ADR-K01: Preliminary Architectural Strategy for TNH Scholar Knowledge Base](/architecture/knowledge-base/adr/adr-k01-kb-architecture-strategy.md)
- [ADR-MD01: Adoption of JSON-LD for Metadata Management](/architecture/metadata/adr/adr-md01-json-ld-metadata.md)
- [ADR-MD02: Metadata Infrastructure Object-Service Integration](/architecture/metadata/adr/adr-md02-metadata-object-service-integration.md)
- [ADR-OA01: TNH-Conductor — Provenance-Driven AI Workflow Coordination](/architecture/agent-orchestration/adr/adr-oa01-agent-orchestration-strategy.md)
- [ADR-OA02: Phase 0 Protocol Layer Spike](/architecture/agent-orchestration/adr/adr-oa02-phase-0-protocol-spike.md)
- [ADR-OA03.1: Claude Code Runner](/architecture/agent-orchestration/adr/adr-oa03.1-claude-code-runner.md)
- [ADR-OA03.2: Codex Runner](/architecture/agent-orchestration/adr/adr-oa03.2-codex-runner.md)
- [ADR-OA03: Agent Runner Architecture](/architecture/agent-orchestration/adr/adr-oa03-agent-runner-architecture.md)
- [ADR-OS01: Object-Service Design Architecture V3](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md)
- [ADR-PP01: Rapid Prototype Versioning Policy](/architecture/project-policies/adr/adr-pp01-rapid-prototype-versioning.md)
- [ADR-PT03: Prompt System Current Status & Roadmap](/architecture/prompt-system/adr/adr-pt03-prompt-system-status-roadmap.md)
- [ADR-PT04: Prompt System Refactor Plan (Revised)](/architecture/prompt-system/adr/adr-pt04-prompt-system-refactor.md)
- [ADR-PV01: Provenance & Tracing Infrastructure Strategy](/architecture/provenance/adr/adr-pv01-provenance-tracing-strat.md)
- [ADR-ST01.1: tnh-setup UI Design](/architecture/setup-tnh/adr/adr-st01.1-tnh-setup-ui-design.md)
- [ADR-ST01: tnh-setup Runtime Hardening](/architecture/setup-tnh/adr/adr-st01-tnh-setup-runtime-hardening.md)
- [ADR-TG01.1: Human-Friendly CLI Defaults with --api Flag](/architecture/tnh-gen/adr/adr-tg01.1-human-friendly-defaults.md)
- [ADR-TG01: tnh-gen CLI Architecture](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md)
- [ADR-TG02: TNH-Gen CLI Prompt System Integration](/architecture/tnh-gen/adr/adr-tg02-prompt-integration.md)
- [ADR-TR01: AssemblyAI Integration for Transcription Service](/architecture/transcription/adr/adr-tr01-assemblyai-integration.md)
- [ADR-TR02: Optimized SRT Generation Design](/architecture/transcription/adr/adr-tr02-optimized-srt-design.md)
- [ADR-TR03: Standardizing Timestamps to Milliseconds](/architecture/transcription/adr/adr-tr03-ms-timestamps.md)
- [ADR-TR04: AssemblyAI Service Implementation Improvements](/architecture/transcription/adr/adr-tr04-assemblyai-improvements.md)
- [ADR-VP01: Video Processing Return Types and Configuration](/architecture/video-processing/adr/adr-vp01-video-processing.md)
- [ADR-VSC01: VS Code Integration Strategy (TNH-Scholar Extension v0.1.0)](/architecture/ui-ux/vs-code-integration/adr-vsc01-vscode-integration-strategy.md)
- [ADR-VSC02: VS Code Extension Architecture](/architecture/ui-ux/vs-code-integration/adr-vsc02-tnh-gen-cli-implementation.md)
- [ADR-VSC03.2: Real-World Survey Addendum (VS Code as a UI/UX Platform)](/architecture/ui-ux/vs-code-integration/adr-vsc03.2-real-world-survey-addendum.md)
- [ADR-VSC03.3: Investigation Synthesis - Validation of Design Choices](/architecture/ui-ux/vs-code-integration/adr-vsc03.3-investigation-synthesis.md)
- [ADR-VSC03: Preliminary Investigation Findings](/architecture/ui-ux/vs-code-integration/adr-vsc03.1-findings.md)
- [ADR-VSC03: Python-JavaScript Impedance Mismatch Investigation](/architecture/ui-ux/vs-code-integration/adr-vsc03-python-javascript-impedance-investigation.md)
- [ADR-YF00: Early yt-fetch Transcript Decisions (Historical)](/architecture/ytt-fetch/adr/adr-yf00-early-decisions.md)
- [ADR-YF01: YouTube Transcript Source Handling](/architecture/ytt-fetch/adr/adr-yf01-yt-transcript-source-handling.md)
- [ADR-YF02: YouTube Transcript Format Selection](/architecture/ytt-fetch/adr/adr-yf02-yt-transcript-format-selection.md)
- [Architecture Overview](/architecture/overview.md)
- [Audio Chunking Algorithm Design Document](/architecture/transcription/design/audio-chunking-design.md)
- [Codex Harness End-to-End Test Report](/architecture/agent-orchestration/notes/codex-harness-e2e-report.md)
- [Codex Harness Spike Findings](/architecture/agent-orchestration/notes/codex-harness-spike-findings.md)
- [Design Strategy: VS Code as UI/UX Platform for TNH Scholar](/architecture/ui-ux/design/vs-code-as-ui-platform.md)
- [Diarization Algorithms](/architecture/transcription/design/diarization-algorithms.md)
- [Diarization Chunker Module Design Strategy](/architecture/transcription/design/diarization-chunker-design.md)
- [Diarization System Design](/architecture/transcription/design/diarization-system-design.md)
- [Documentation Design](/architecture/docs-system/design/documentation-design.md)
- [GenAI Service — Design Strategy](/architecture/gen-ai-service/design/genai-service-design-strategy.md)
- [Generate Markdown Translation JSON Pairs](/architecture/jvb-viewer/design/generate-md-translation-json-pairs.md)
- [Generate Markdown Vietnamese](/architecture/jvb-viewer/design/generate-md-vietnamese.md)
- [Interval-to-Segment Mapping Algorithm](/architecture/transcription/design/interval-to-segment-mapping.md)
- [JVB Viewer — Version 2 Strategy & High‑Level Design](/architecture/jvb-viewer/design/jvb-viewer-v2-strategy.md)
- [Language-Aware Chunking Orchestrator Notes](/architecture/transcription/design/language-aware-chunking-orchestrator-notes.md)
- [LUÂN-HỒI](/architecture/jvb-viewer/design/luan-hoi.md)
- [minimal but extensible setup tool for the prototyping phase](/architecture/setup-tnh/design/setup-tnh-minimal-extensible-tool.md)
- [Modular Pipeline Design: Best Practices for Audio Transcription and Diarization](/architecture/transcription/design/modular-pipeline-best-practices.md)
- [Object-Service Design Gaps](/architecture/object-service/object-service-design-gaps.md)
- [Object-Service Design Overview](/architecture/object-service/object-service-design-overview.md)
- [Object-Service Implementation Status](/architecture/object-service/object-service-implementation-status.md)
- [OpenAI Interface Migration Plan](/architecture/gen-ai-service/design/openai-interface-migration-plan.md)
- [Package Version Checker Design Document](/architecture/utilities/design/package-version-checker-design.md)
- [Practical Language-Aware Chunking Design](/architecture/transcription/design/practical-language-aware-chunking.md)
- [Prompt System Architecture](/architecture/prompt-system/prompt-system-architecture.md)
- [Simplified Language-Aware Chunking Design](/architecture/transcription/design/language-aware-chunking-design.md)
- [Speaker Diarization Algorithm Design](/architecture/transcription/design/speaker-diarization-algorithm-design.md)
- [Speaker Diarization and Time-Mapped Transcription System Design](/architecture/transcription/design/speaker-diarization-time-mapped-design.md)
- [TextObject Original Design](/architecture/ai-text-processing/design/textobject-original-design.md)
- [TextObject System Design Document](/architecture/ai-text-processing/design/textobject-system-design.md)
- [TimelineMapper Design Document](/architecture/transcription/design/timelinemapper-design.md)
- [TNH Configuration Management](/architecture/configuration/tnh-configuration-management.md)
- [TNH-Scholar Agent Orchestration System](/architecture/agent-orchestration/system-design.md)
- [TNH‑Scholar Utilities Catalog](/architecture/utilities/design/utilities-catalog.md)
- [Versioning Policy Documentation Additions](/architecture/project-policies/versioning-policy-implementation-summary.md)
- [YouTube API vs yt-dlp Evaluation](/architecture/ytt-fetch/design/youtube-api-vs-yt-dlp-eval.md)

## Development

- [Contributing to TNH Scholar (Prototype Phase)](/development/contributing-prototype-phase.md)
- [Development Documentation](/development/overview.md)
- [Fine Tuning Strategy](/development/fine-tuning-strategy.md)
- [Forensic Analysis: December 7, 2025 Git Data Loss Incident](/development/incident-reports/2025-12-07-reference/forensic-analysis.md)
- [Git Workflow & Safety Guide](/development/git-workflow.md)
- [Human-AI Software Engineering Principles](/development/human-ai-software-engineering-principles.md)
- [Implementation Summary: Git Safety Improvements](/development/incident-reports/2025-12-07-reference/implementation-summary.md)
- [Improvements / Initial structure](/development/improvements-initial-structure.md)
- [Incident Report: Git Recovery - December 7, 2025](/development/incident-reports/2025-12-07-git-recovery.md)
- [Proposed Updates to Incident Report](/development/incident-reports/2025-12-07-reference/incident-report-updates.md)
- [Release Workflow](/development/release-workflow.md)
- [TNH Scholar Design Principles](/development/design-principles.md)
- [TNH Scholar Style Guide](/development/style-guide.md)
- [TNH Scholar System Design](/development/system-design.md)
- [v0.2.0 Tag Correction Plan](/development/incident-reports/tag-v0.2.0-correction-plan.md)
- [yt-dlp Ops Check](/development/yt-dlp-ops-check.md)

## Docs Ops

- [ADR Template](/docs-ops/adr-template.md)
- [Markdown Standards](/docs-ops/markdown-standards.md)
- [MkDocs Strict Warning Backlog](/docs-ops/mkdocs-strict-warning-backlog.md)
- [Preview TNH Scholar Theme](/docs-ops/preview-theme.md)
- [TNH Scholar Theme Design](/docs-ops/theme-design.md)

## Research

- [1-3 Word Queries](/research/gpt4o-search-query-testing/queries-1-3-words.md)
- [GPT Development Convos](/research/gpt_development_convos.md)
- [Passage Test](/research/gpt4o-translation-experiments/passage_test.md)
- [Preliminary Feasibility Study](/research/preliminary-feasibility-study.md)
- [RAG Research Directions for TNH Scholar](/research/rag-research-directions.md)
- [Structural-Informed Adaptive Processing (SIAP) Methodology](/research/siap-methodology.md)
- [Summary Report on Metadata Extraction, Source Parsing, and Model Training for TNH-Scholar](/research/metadata-summary-report.md)
- [TNH Scholar Knowledge Base: Design Document](/research/kb-design-document.md)

---
title: "Design"
description: "Table of contents for architecture/transcription/design"
owner: ""
author: ""
status: current
created: "2025-12-11"
auto_generated: true
---

# Design

**Table of Contents**:

<!-- To manually edit this file, update the front matter and keep `auto_generated: true` to allow regeneration. -->

**[Audio Chunking Algorithm Design Document](audio-chunking-design.md)** - Design for splitting diarization segments into five-minute audio chunks using greedy accumulation and speaker-aware boundaries.

**[Diarization Algorithms](diarization-algorithms.md)** - This document details the key algorithms in the diarization system, focusing on high-level design without implementation details. Each algorithm is presented with its inputs, outputs, and process flow.

**[Diarization Chunker Module Design Strategy](diarization-chunker-design.md)** - I've analyzed the current system and PoC code to propose a modular, extensible design for integrating the diarization chunking functionality into your tnh-scholar project.

**[Diarization System Design](diarization-system-design.md)** - Detailed architecture for the diarization pipeline, covering segmentation, track extraction, and transcript remapping.

**[Interval-to-Segment Mapping Algorithm](interval-to-segment-mapping.md)** - Algorithm for mapping chunk-relative transcription intervals back to diarization segments using overlap and proximity.

**[Simplified Language-Aware Chunking Design](language-aware-chunking-design.md)** - Language-aware chunking strategy that augments diarization splits with practical language detection heuristics.

**[Language-Aware Chunking Orchestrator Notes](language-aware-chunking-orchestrator-notes.md)** - Working notes for extending the DiarizationChunker orchestrator with language-aware strategies.

**[Modular Pipeline Design: Best Practices for Audio Transcription and Diarization](modular-pipeline-best-practices.md)** - This document summarizes a detailed design and refactoring discussion on building a clean, modular, and production-ready audio transcription pipeline, with a focus on diarization chunking and robust system structure. It includes architectural patterns, file organization, and code hygiene practices.

**[Practical Language-Aware Chunking Design](practical-language-aware-chunking.md)** - Practical heuristics for detecting language changes during chunking when diarization output is noisy.

**[Speaker Diarization Algorithm Design](speaker-diarization-algorithm-design.md)** - This document details the key algorithms referenced in the main diarization system design. Each algorithm is presented with a clear breakdown of its inputs, outputs, and processing steps.

**[Speaker Diarization and Time-Mapped Transcription System Design](speaker-diarization-time-mapped-design.md)** - System design for mapping diarization outputs to speaker-specific transcriptions with accurate global timelines.

**[TimelineMapper Design Document](timelinemapper-design.md)** - Design for the TimelineMapper component that reprojects chunk-level transcripts into the original audio timeline.

---

*This file auto-generated.*

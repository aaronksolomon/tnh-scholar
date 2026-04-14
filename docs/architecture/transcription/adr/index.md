---
title: "Adr"
description: "Table of contents for architecture/transcription/adr"
owner: ""
author: ""
status: processing
created: "2026-04-13"
auto_generated: true
---

# Adr

**Table of Contents**:

<!-- To manually edit this file, update the front matter and keep `auto_generated: true` to allow regeneration. -->

**[ADR-TR01: AssemblyAI Integration for Transcription Service](adr-tr01-assemblyai-integration.md)** - Introduces a pluggable transcription interface with AssemblyAI and Whisper providers.

**[ADR-TR02: Optimized SRT Generation Design](adr-tr02-optimized-srt-design.md)** - Uses provider-native SRT generation to simplify the transcription pipeline.

**[ADR-TR03: Standardizing Timestamps to Milliseconds](adr-tr03-ms-timestamps.md)** - Aligns all transcription providers on millisecond timestamps to avoid float drift.

**[ADR-TR04: AssemblyAI Service Implementation Improvements](adr-tr04-assemblyai-improvements.md)** - Refactors the AssemblyAI adapter to use the official SDK, richer options, and better error handling.

**[ADR-TR05: Language-Aware Multilingual Transcription Engine](adr-tr05-language-aware-multilingual-transcription-engine.md)** - Adopts language-aware segmentation and merge-first orchestration for multilingual audio transcription and English subtitle generation.

**[ADR-TR05.1: Speaker-Block Language Lock Default Strategy](adr-tr05.1-speaker-block-language-lock-default.md)** - Defines the default multilingual segmentation strategy as contiguous-speaker language locking with selective translation.

**[ADR-TR05.2: MVP Service Scaffold for Multilingual Transcription](adr-tr05.2-mvp-service-scaffold.md)** - Defines an in-place refactor of the existing audio_processing stack for the multilingual transcription MVP.

---

*This file auto-generated.*

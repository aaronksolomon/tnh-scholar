---
title: "ADR-TR05.1: Speaker-Block Language Lock Default Strategy"
description: "Defines the default multilingual segmentation strategy as contiguous-speaker language locking with selective translation."
type: "design-detail"
owner: "aaronksolomon"
author: "Codex"
status: wip
created: "2026-03-01"
parent_adr: "adr-tr05-language-aware-multilingual-transcription-engine.md"
related_adrs: ["adr-tr02-optimized-srt-design.md"]
---
# ADR-TR05.1: Speaker-Block Language Lock Default Strategy

Define the default multilingual segmentation strategy as contiguous-speaker language locking, with English segments bypassing translation.

- **Status**: Proposed
- **Date**: 2026-03-01

## Context

`ADR-TR05` establishes that the primary engine should be language-aware and segment-first. That leaves one important implementation-level architectural choice open: what language segmentation strategy should be the default.

The repository already contains the core ingredients for a speaker-contiguous strategy:

- speaker-run grouping in `src/tnh_scholar/audio_processing/diarization/strategies/speaker_blocker.py`
- language probing in `src/tnh_scholar/audio_processing/diarization/strategies/language_probe.py`

At the same time, existing language-aware chunking code is exploratory and does not yet define a stable production contract. We need an explicit default strategy so the future CLI and service orchestration expose a predictable behavior.

## Decision

The default multilingual segmentation strategy will be:

- `speaker-block-language-lock`

### Contract

1. Build contiguous speaker blocks
   - Group adjacent segments when the speaker label remains the same and the inter-segment gap is within the configured same-speaker threshold.

2. Probe language once per block by default
   - Probe the block using a representative sample, normally from the middle of the contiguous span.
   - Record a language code plus confidence where the detector supports it.

3. Lock language for that block
   - Assume the block remains in one language unless an optional re-probe policy overrides the assumption.

4. Transcribe with language-aware routing
   - If the block language is English, transcribe and preserve the English output directly.
   - If the block language is non-English, transcribe in that detected language and route the result to translation.
   - If language is unknown or low-confidence, use fallback policy rather than forcing a hard split.
   - The v1 implementation must support both Whisper and AssemblyAI through the same segment-level orchestration contract.

5. Merge all blocks into a single final English timeline
   - English blocks pass through untranslated.
   - Non-English blocks are translated before merge.

### Required Fallback Behavior

The default strategy must define deterministic fallback behavior for uncertain inputs:

- If language detection returns unknown, prefer inheriting the prior block language only when that inference is locally defensible.
- Otherwise, allow provider auto-detect at transcription time and mark the block as uncertain in debug artifacts.
- Do not silently coerce unknown segments into a configured default language without recording that decision.

### Relationship to Provider-Native SRT Generation

This strategy does not replace `ADR-TR02`. It changes where that design is applied.

- `ADR-TR02` remains valid for segment-level transcription.
- Provider-native SRT generation should occur after segmentation, not before it.
- Merged final subtitles remain a higher-level orchestration concern.

The default strategy is provider-neutral. It should operate identically at the orchestration level whether the selected transcription backend is Whisper or AssemblyAI.

## Consequences

- **Positive**: Creates a stable default behavior for the multilingual engine and future CLI options.
- **Positive**: Minimizes unnecessary translation work by bypassing translation for English blocks.
- **Positive**: Matches common real-world conversational and interpreted media better than naive fixed-window probing.
- **Positive**: Reuses existing diarization and language-probe primitives already present in the codebase.

- **Negative**: The strategy depends on speaker diarization quality when diarization is enabled.
- **Negative**: A bilingual speaker can still switch languages mid-turn, which this default may miss unless optional re-probe policies are enabled.
- **Negative**: Poor or noisy speaker segmentation can produce over-fragmented blocks and unstable language decisions.

## Alternatives Considered

### 1. Fixed-window probing as the default

Rejected because it is simpler but more likely to cut across natural turn boundaries and create avoidable misclassification in dialog-heavy media.

### 2. Force translation for all segments regardless of detected language

Rejected because it wastes cost, adds latency, and can degrade already-English transcript quality.

### 3. Require repeated probing inside every block

Rejected as the default because it increases cost and complexity. It may still be offered as an opt-in strategy for difficult audio.

### 4. Include provider comparison mode in the default strategy contract

Rejected for v1 scope. The default strategy governs segmentation and routing decisions. Provider comparison may be added later, but it should not be part of the initial MVP contract.

## Open Questions

- Block-level language probing should expose confidence as a first-class typed model in the engine contract; this is resolved in `/architecture/transcription/adr/adr-tr05.2-mvp-service-scaffold.md` via `LanguageDetectionResult`.
- At what duration should a long contiguous block qualify for optional mid-block re-probing?
- Should re-probing be a threshold-based flag, a separate strategy, or both?

## Future Directions

- Add an optional provider comparison mode that reuses the same `speaker-block-language-lock` segmentation manifest across multiple transcription backends.

## References

- `/architecture/transcription/adr/adr-tr05-language-aware-multilingual-transcription-engine.md`
- `/architecture/transcription/adr/adr-tr02-optimized-srt-design.md`
- `/architecture/transcription/design/practical-language-aware-chunking.md`

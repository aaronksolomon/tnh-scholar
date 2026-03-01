---
title: "ADR-TR05: Language-Aware Multilingual Transcription Engine"
description: "Adopts language-aware segmentation and merge-first orchestration for multilingual audio transcription and English subtitle generation."
owner: "aaronksolomon"
author: "Codex"
status: wip
created: "2026-03-01"
related_adrs: ["adr-tr02-optimized-srt-design.md"]
---
# ADR-TR05: Language-Aware Multilingual Transcription Engine

Adopt a language-aware transcription pipeline for real-world multilingual audio so mixed-language source media can produce a complete English SRT instead of a dominant-language partial transcript.

- **Status**: Proposed
- **Date**: 2026-03-01

## Context

The current working prototype uses provider-native SRT generation on the full audio file, then translates the resulting SRT to English. This works for short single-language audio, but it fails on realistic video-sourced audio where:

- speakers switch languages mid-file
- one speaker may be mostly uniform in language while another is not
- short translated asides are embedded inside longer source-language turns
- the transcription provider tends to lock onto the dominant language and ignore or normalize brief language changes

This behavior was reproduced in a local test: the whole-file Whisper path produced a clean Vietnamese transcript but omitted expected non-Vietnamese segments. That is not primarily a translation problem. The failure occurs earlier because whole-file transcription does not preserve multilingual boundaries well enough for downstream translation.

The repository already contains relevant building blocks and design exploration:

- `/architecture/transcription/adr/adr-tr02-optimized-srt-design.md`
- `/architecture/transcription/design/practical-language-aware-chunking.md`
- `/architecture/transcription/design/language-aware-chunking-design.md`
- `/architecture/transcription/design/diarization-system-design.md`

However, the currently usable CLI path does not yet compose these pieces into a single production-usable workflow for multilingual audio.

## Decision

We will build the next transcription engine around language-aware segmentation, not whole-file transcription.

The pipeline will be organized as these orchestration stages:

1. **Media normalization**
   - Normalize input audio to a stable local working file.
   - Preserve a single timeline reference in milliseconds for all later remapping.

2. **Optional speaker segmentation**
   - Use speaker diarization only as a boundary source, not as the primary output goal.
   - Treat speaker turns as hints for language stability and chunk boundaries.
   - Allow the engine to run without diarization when cost, latency, or reliability make diarization undesirable.

3. **Language probing and contiguous segment formation**
   - Probe short windows or speaker-contiguous spans for likely language.
   - Merge adjacent spans when language is stable enough.
   - Split when language changes with sufficient confidence.
   - Maintain an explicit fallback language state for low-confidence spans rather than forcing a false hard split.

4. **Per-segment transcription**
   - Transcribe each language-contiguous segment independently.
   - Pass the detected or locked language into the transcription provider for that segment.
   - Support both Whisper and AssemblyAI as first-class v1 pathways using the existing transcription service foundation.
   - Prefer provider-native SRT generation where possible, but only after segmentation.

5. **Per-segment English translation**
   - Translate each segment transcript or SRT into English independently when the detected language is not English.
   - Skip translation for English segments and preserve the provider transcript directly.
   - Keep timing scoped to the segment during translation.

6. **Timeline remapping and merge**
   - Remap segment-local timestamps back to the original full-audio timeline.
   - Merge all translated segments into one final English SRT ordered by original timestamps.
   - Preserve source-language intermediate artifacts when requested for debugging and QA.

### Architectural Shape

This should be implemented as a composed service pipeline, not a monolithic script.

The engine should center on a new orchestrator, conceptually:

- `MultilingualTranscriptionOrchestrator`

With typed collaborators such as:

- `AudioPreparationService`
- `SpeakerBoundaryService`
- `LanguageSegmentationService`
- `SegmentTranscriptionService`
- `SegmentTranslationService`
- `SubtitleMergeService`

This keeps the system aligned with the project’s design standards:

- encapsulated responsibilities
- composition over procedural sprawl
- typed models instead of loose dict passing in application logic

The `SegmentTranscriptionService` contract should be provider-agnostic even in the first implementation. The MVP should ship with:

- a Whisper-backed path
- an AssemblyAI-backed path

These should reuse the existing provider service layer rather than introducing a provider-specific orchestration branch for each engine.

### Default Segmentation Strategy

The default strategy for the first production implementation will be:

- `speaker-block-language-lock`

This strategy means:

- contiguous same-speaker spans are grouped into `SpeakerBlock`-like units
- the engine assumes language remains stable while the active speaker does not change
- one language probe is taken per contiguous speaker block by default
- very long blocks may optionally be re-probed internally, but that is an enhancement, not the baseline contract

This default is chosen because it matches common multilingual source material better than fixed-window probing:

- interpreted talks
- Q&A recordings
- conversational or instructional video audio

In these cases, language changes often align with turn-taking more reliably than with arbitrary time windows.

The engine must still support alternative strategies for more difficult audio, but the default path should optimize for this speaker-contiguous heuristic.

### Primary Output Contract

The engine’s primary user-facing output will be:

- one merged English SRT spanning the full original timeline

Optional artifacts:

- source-language segment SRTs
- translated per-segment SRTs
- language segmentation manifest
- diarization manifest
- debug trace of language decisions

## Consequences

- **Positive**: Handles multilingual and code-switched audio more reliably than whole-file transcription.
- **Positive**: Preserves short translated asides that are commonly lost when the provider commits to a dominant language.
- **Positive**: Produces a single full English SRT suitable for downstream editing, subtitle review, and transcript generation.
- **Positive**: Makes speaker diarization optional instead of mandatory, reducing cost and operational fragility for simpler files.
- **Positive**: Reuses existing provider-native SRT generation while moving the intelligence to the segmentation layer.
- **Positive**: Avoids unnecessary translation cost and potential quality loss for segments already detected as English.
- **Positive**: Preserves an immediate path to professional workflows that require choosing between Whisper and AssemblyAI on a per-job basis.

- **Negative**: The orchestration becomes materially more complex than the current prototype.
- **Negative**: Language detection errors can introduce bad splits or wrong-language forced transcription if thresholds are tuned poorly.
- **Negative**: More segments means more provider calls, which can increase cost and latency.
- **Negative**: Timestamp remapping and merge logic must be tested carefully to avoid subtle subtitle drift or ordering errors.

## Alternatives Considered

### 1. Keep whole-file transcription, then translate

Rejected because it performs acceptably only for mostly single-language files and is not reliable for the target class of real-world multilingual audio.

### 2. Always require speaker diarization first

Rejected because speaker boundaries are useful but not sufficient. Speaker changes do not always align with language changes, and diarization adds cost, latency, and another operational dependency.

### 3. Manual post-editing after whole-file transcription

Rejected as the primary strategy because it does not scale and defeats the goal of a reusable engine for video-sourced audio.

### 4. Build provider comparison into the v1 MVP

Rejected for the MVP scope. Comparative provider review is a valid future direction, but it is not required for the first usable multilingual engine. The initial milestone should support both providers as selectable pathways without also building a comparison workflow.

## Open Questions

- The default heuristic is `speaker-block-language-lock`; remaining work is to validate whether pyannote output quality is sufficient for this to remain the default in noisy real-world inputs.
- What confidence threshold should trigger a hard language split versus a soft fallback to the prior segment language?
- Should translation operate on SRT entries directly, or on a richer timed text model before final SRT generation?
- What artifact bundle should be retained by default to support debugging without creating excessive clutter?

## Future Directions

- Add a provider comparison mode that runs the same segmented timeline through both Whisper and AssemblyAI for human review and QA.
- Add richer timed-text intermediates if segment-level SRT proves too limiting for subtitle quality control.

## Implementation Notes

The current prototype script in `scripts/transcribe_translate_srt.py` is useful as a minimal baseline, but it should be treated as a temporary whole-file mode. The next implementation should preserve that mode as a fallback while adding a new multilingual mode built around language-aware segmentation.

The first production-oriented build should prioritize:

1. Local audio input only
2. Optional diarization
3. Language segmentation manifest
4. Merged English SRT output
5. Retained intermediate artifacts for debugging

## References

- `/architecture/transcription/adr/adr-tr02-optimized-srt-design.md`
- `/architecture/transcription/design/practical-language-aware-chunking.md`
- `/architecture/transcription/design/language-aware-chunking-design.md`
- `/architecture/transcription/design/timelinemapper-design.md`
- `/architecture/transcription/design/diarization-system-design.md`

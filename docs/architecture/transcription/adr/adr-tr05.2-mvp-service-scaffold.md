---
title: "ADR-TR05.2: MVP Service Scaffold for Multilingual Transcription"
description: "Defines an in-place refactor of the existing audio_processing stack for the multilingual transcription MVP."
type: "implementation-guide"
owner: "aaronksolomon"
author: "Codex"
status: wip
created: "2026-03-01"
parent_adr: "adr-tr05-language-aware-multilingual-transcription-engine.md"
related_adrs: ["adr-tr05.1-speaker-block-language-lock-default.md", "adr-tr02-optimized-srt-design.md"]
---
# ADR-TR05.2: MVP Service Scaffold for Multilingual Transcription

Define an in-place refactor plan for implementing the multilingual transcription MVP by improving the existing `audio_processing` stack rather than introducing a parallel subsystem.

- **Status**: Proposed
- **Date**: 2026-03-01

## Context

`ADR-TR05` and `ADR-TR05.1` establish the architecture and default segmentation strategy, but they intentionally stop short of prescribing the concrete service layout for implementation.

The current repository has useful primitives:

- provider transcription services in `src/tnh_scholar/audio_processing/transcription/`
- diarization and speaker block primitives in `src/tnh_scholar/audio_processing/diarization/`
- a temporary whole-file prototype in `scripts/transcribe_translate_srt.py`

What it does not yet have is a clean, cohesive multilingual path through those existing modules that satisfies the project’s design constraints:

- strong typing
- composition over procedural scripts
- provider-agnostic orchestration
- minimal coupling between domain and provider-specific infrastructure

Without an explicit implementation guide, there is a high risk of either:

- extending the current prototype script into production logic, or
- creating a second orchestration stack that duplicates concepts already present in `audio_processing`

Both outcomes would create avoidable technical debt.

## Decision

The MVP implementation will be built as an in-place refactor of the existing `src/tnh_scholar/audio_processing/` package, not as expanded script logic and not as a separate parallel subsystem.

### Refactor Boundary

This ADR defines a targeted refactor for multilingual transcription goals only.

In scope:

- making the existing diarization and transcription abstractions work together for multilingual segmentation and English SRT generation
- repairing stale interfaces in language-aware strategy code
- introducing missing typed models and provider-neutral orchestration where required

Out of scope:

- a full general hardening pass of the entire `audio_processing` subsystem
- unrelated cleanup of all legacy modules
- a complete redesign of every transcription and diarization API surface

The broader audio processing pipeline likely does need a larger audit and modernization pass, but that should be tracked as future work rather than folded into this MVP.

### Proposed Structural Shape

The MVP should improve the existing package structure in place.

```text
src/tnh_scholar/audio_processing/
  transcription/
    ...
  diarization/
    ...
  timed_object/
    ...
  # add only the minimal shared models/protocols/services needed
```

The preferred shape is:

- keep provider implementations in `audio_processing/transcription/`
- keep speaker segmentation primitives in `audio_processing/diarization/`
- add only the minimum new shared models, protocols, and orchestration service needed inside `audio_processing/`

The existing script may remain as a thin application-layer caller during the transition, but it must delegate to the refactored `audio_processing` service layer instead of accumulating orchestration logic.

### Required Domain Models

The MVP should define the missing typed models before implementing orchestration behavior.

At minimum:

- `LanguageDetectionResult`
  - detected language code
  - confidence
  - detector source
  - reliability or fallback indicator

- `SpeakerLanguageBlock`
  - source speaker label
  - original start and end times
  - detected or inferred language
  - confidence metadata
  - uncertainty marker

- `SegmentTranscriptionRequest`
  - block reference
  - selected provider
  - transcription language policy
  - output format policy

- `SegmentTranscriptionResult`
  - block reference
  - provider name
  - source-language subtitle content
  - optional translated subtitle content
  - status and error metadata

- `MergedSubtitleArtifact`
  - final English SRT
  - manifest references for optional intermediate artifacts

These models should be placed inside the existing `audio_processing` domain, use Pydantic where validation or serialization matters, and avoid untyped dictionaries in app or service logic.

### Required Protocols

The MVP should define only the provider-neutral interfaces that are currently missing for orchestration.

At minimum:

- `LanguageSegmentationServiceProtocol`
  - turns diarization segments or fallback spans into `SpeakerLanguageBlock` results

- `SegmentTranscriptionServiceProtocol`
  - accepts `SegmentTranscriptionRequest`
  - returns `SegmentTranscriptionResult`
  - routes to Whisper or AssemblyAI via existing provider services

- `SegmentTranslationServiceProtocol`
  - accepts source-language segment subtitle or transcript artifacts
  - applies translation only when the segment language is not English
  - returns translated segment subtitle content plus status metadata

- `SubtitleMergeServiceProtocol`
  - remaps segment-local timings
  - merges segment outputs into one final timeline

### Orchestrator Responsibility

The main orchestrator should be added within the existing `audio_processing` package as a focused service, conceptually:

- `MultilingualTranscriptionService`

Its job is to coordinate existing and refactored collaborators, not to embed provider-specific logic.

It should:

1. prepare normalized input state
2. obtain optional speaker boundaries
3. invoke language segmentation
4. invoke per-segment transcription
5. invoke selective translation for non-English segments
6. merge outputs into final English SRT

It should not:

- perform direct provider SDK calls itself
- manipulate raw dictionaries as internal state
- own file-system formatting logic beyond orchestrating typed artifact writers

### Provider Integration Rule

The MVP must support both Whisper and AssemblyAI using existing provider foundations in `src/tnh_scholar/audio_processing/transcription/`.

This means:

- the multilingual orchestrator remains provider-agnostic
- provider-specific parameter mapping stays in adapter or provider-facing collaborators
- the service contract is identical regardless of backend selection

### Existing Code Upgrade Rule

The MVP should prefer upgrading and reusing existing modules before adding new ones.

This means:

- repair stale language-aware strategy code where the current interfaces have drifted
- strengthen existing diarization strategy boundaries instead of replacing them wholesale
- add new files only where the current package lacks a clean place for the missing abstraction

New files are acceptable when they clarify responsibility, but they should extend the current package structure rather than create an adjacent subsystem.

### Transition Rule for Existing Script

The script `scripts/transcribe_translate_srt.py` may remain temporarily for testing and operational convenience, but only as:

- input parsing
- service invocation
- output path selection

All segmentation, routing, and merge logic should move into the new module cluster.

## Consequences

- **Positive**: Keeps the implementation aligned with AGENTS.md and design-principles requirements before code complexity grows.
- **Positive**: Creates a clear place for multilingual orchestration that does not overload the existing provider service modules.
- **Positive**: Makes future CLI integration straightforward because the application layer can call a stable service.
- **Positive**: Reduces the risk of building production behavior into a prototype script.

- **Negative**: Adds upfront structure before visible feature expansion.
- **Negative**: Requires writing typed models and protocols before the end-to-end feature feels complete.

## Alternatives Considered

### 1. Extend the prototype script directly

Rejected because it would concentrate domain orchestration in a procedural application-layer script and conflict with the project’s design standards.

### 2. Add multilingual orchestration directly into existing provider modules

Rejected because it would blur the boundary between provider implementation and cross-provider orchestration.

### 3. Put the feature into a new CLI first, then refactor later

Rejected because it creates avoidable churn and encourages the wrong layering.

### 4. Build a separate multilingual subsystem beside audio_processing

Rejected because it would duplicate concepts that already exist in the current transcription, diarization, and timing layers. The MVP goal is to make the current abstraction set robust and usable for multilingual work, not to create a competing stack.

## Open Questions

- Should artifact writing be handled by a dedicated result writer in the first MVP, or can the initial service return typed in-memory artifacts only?
- Should provider selection be represented by an enum in the multilingual module or reuse an existing provider identifier type?
- Should optional diarization be abstracted behind a new protocol immediately, or can the first MVP call the existing diarization façade through a thin adapter?

## Future Work Boundary

This ADR intentionally does not attempt to fully modernize all of `audio_processing`.

Future work outside this MVP likely includes:

- a broader architecture review of the full audio processing pipeline
- hardening and simplification of legacy modules unrelated to multilingual routing
- consistency passes across older transcription and diarization surfaces

Those needs are real, but they should be scoped and documented separately from this feature-driven refactor.

## References

- `/architecture/transcription/adr/adr-tr05-language-aware-multilingual-transcription-engine.md`
- `/architecture/transcription/adr/adr-tr05.1-speaker-block-language-lock-default.md`
- `/architecture/transcription/adr/adr-tr02-optimized-srt-design.md`
- `/architecture/transcription/design/diarization-system-design.md`

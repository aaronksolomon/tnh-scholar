---
title: "Language-Aware Chunking Orchestrator Notes"
description: "Working notes for extending the DiarizationChunker orchestrator with language-aware strategies."
owner: ""
author: ""
status: processing
created: "2025-06-24"
---
# Language-Aware Chunking Orchestrator Notes
Working notes for extending the DiarizationChunker orchestrator with language-aware strategies.

Design Proposal: Language-Aware Chunking Extension for diarization_chunker

1. Background

DiarizationChunker currently supports two implicit strategies
	1.	Contiguous-Time (no speaker split)
	2.	Speaker-Aware (split at speaker change)

Both rely exclusively on timing / speaker labels and treat language as uniform.

⸻

2. Objectives

Goal	Why it matters
Language-Purity per Chunk	Whisper (and most ASR models) transcribe best when each input clip is single-language.
Pluggable Strategies	Future research (e.g., energy-based chunking, silence detection) should drop in without core refactors.
Compact, Single-Purpose Methods	Improves testability & maintenance.
Config-Driven	Users should tune via settings rather than editing code.


⸻

3. High-Level Architecture

             +--------------------+
 audio ----> | DiarizationChunker |  (orchestrator, owns config)
             +---------+----------+
                       |
                       v
             +--------------------+                       +----------------+
             | IChunkingStrategy  |<--- dependency delve --| LanguageProbe |
             +---------+----------+                       +----------------+
                       ^                                           ^
         (Strategy 1)  |                                           |
                       | (Strategy N)                              |
           +--------------------+                         +-------------------+
           | DefaultStrategy    |                         | LanguageAwareStrategy |
           +--------------------+                         +-------------------+

	•	IChunkingStrategy (Protocol / ABC)

class IChunkingStrategy(Protocol):
    def extract(self, segments: list[DiarizationSegment]) -> list[DiarizationChunk]: ...


	•	DiarizationChunker becomes a light façade
	•	Accepts strategy: IChunkingStrategy via constructor or config name.
	•	Delegates all chunk creation to that strategy—no branching inside.
	•	LanguageProbe helper
	•	Stateless (or memoized) service:
	•	probe(audio: AudioChunk, *, sample_ms: int, tries: int, randomize: bool) -> str
	•	Wraps Whisper‐tiny / faster language ID.

⸻

4. New Strategy: LanguageAwareStrategy

Step	Action	Notes
1	Group contiguous segments by speaker	Reuse existing _gap_time, _speaker_change.
2	Compute speaker-block duration	Skip probing if block < min_probe_block_ms.
3	Sample audio from each block	Either deterministic (mid-segment) or random.sample.
4	Detect language via LanguageProbe	Early-exit if all blocks agree on language.
5	Split chunk if mixed languages	Options:• Hard split at first language boundary• Greedy accumulate until mismatch• Recursively bisect noisy blocks
6	Return list[DiarizationChunk]	Each chunk carries a language attribute (extend DiarizationChunk).

Config Additions (suggested):

Field	Type	Default	Description
lang_probe_sample_ms	int	2000	Milliseconds per sample.
lang_probe_tries	int	3	Number of probes per block.
lang_split_enabled	bool	True	Gate for runtime enable/disable.
max_speakers_for_probe	int	2	Skip whole strategy if count greater.
min_probe_block_ms	int	15 000	Don’t probe very short blocks.


⸻

5. Modifications to Existing Models

Class	Change
DiarizationChunk	Add language: Optional[str] = None
ChunkerConfig	Extend with new language-probe fields.
AudioChunk (if available)	Provide lightweight .slice(start_ms, end_ms) for probe sampling.


⸻

6. Example (Illustrative Only)

# orchestrator
chunker = DiarizationChunker(
    strategy=LanguageAwareStrategy(config=ChunkerConfig(lang_split_enabled=True))
)

chunks = chunker.chunk(diarization_segments)
for ch in chunks:
    print(ch.language, ch.total_duration_sec)


⸻

7. Open Questions & Options

Topic	Choices & Trade-offs
Language detector	Whisper-tiny vs. fasttext vs. pycld3. Whisper is heavier but aligned with final ASR.
Granularity of split	Split at block boundary vs. mid-block split when detection disagrees?
Parallelism	Probe calls can run concurrently; decide between concurrent.futures or asyncio.
Caching	Same speaker ID across chunks might reuse earlier language result.
Testing	Need synthetic mixed-language audio fixtures.
Fallback	If detector returns "unknown" above threshold, skip splitting to avoid over-fragmentation.


⸻

8. Migration Plan
	1.	Introduce interfaces.py with IChunkingStrategy, LanguageDetector.
	2.	Refactor existing logic out of DiarizationChunker into DefaultStrategy.
	3.	Add unit tests ensuring parity with current outputs for default strategy.
	4.	Implement LanguageProbe (start with Whisper CLI call wrapper).
	5.	Develop LanguageAwareStrategy iteratively:
	•	Phase-0: Probe once per speaker, no splitting—just annotate language.
	•	Phase-1: Enable optional split on mismatch.
	6.	Benchmark transcription WER before & after on bilingual test set.
	7.	Update docs & example notebooks.

⸻

9. Future Extensions
	•	Energy-AwareStrategy (split on low RMS zones).
	•	Topic-AwareStrategy (use embedding similarity between segments).
	•	Dynamic-Target-Duration (adjust chunk length based on compute budget).

⸻

10. Summary

By extracting chunking logic into interchangeable strategies and adding a LanguageAwareStrategy that probes speaker blocks for language shifts, we achieve:
	•	Cleaner separation of concerns
	•	Config-driven experimentation
	•	Improved ASR accuracy on mixed-language recordings
	•	Foundation for future chunking heuristics

⸻

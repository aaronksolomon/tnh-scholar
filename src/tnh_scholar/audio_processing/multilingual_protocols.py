from __future__ import annotations

from typing import Protocol

from tnh_scholar.audio_processing.multilingual_models import (
    MergedSubtitleArtifact,
    MultilingualTranscriptionRequest,
    SegmentTranscriptionRequest,
    SegmentTranscriptionResult,
    SpeakerLanguageBlock,
)


class LanguageSegmentationServiceProtocol(Protocol):
    """Build language-tagged speaker blocks for downstream routing."""

    def build_blocks(
        self,
        request: MultilingualTranscriptionRequest,
    ) -> list[SpeakerLanguageBlock]:
        """Return speaker blocks for multilingual processing."""


class SegmentTranscriptionServiceProtocol(Protocol):
    """Provider-neutral segment transcription contract."""

    def transcribe_segment(
        self,
        request: SegmentTranscriptionRequest,
    ) -> SegmentTranscriptionResult:
        """Generate source-language subtitles for a segment."""


class SegmentTranslationServiceProtocol(Protocol):
    """Selective translation contract for non-English segments."""

    def translate_segment(
        self,
        result: SegmentTranscriptionResult,
    ) -> SegmentTranscriptionResult:
        """Return a transcription result with translated subtitles when needed."""


class SubtitleMergeServiceProtocol(Protocol):
    """Merge segment results into a final user-facing subtitle artifact."""

    def merge(
        self,
        results: list[SegmentTranscriptionResult],
    ) -> MergedSubtitleArtifact:
        """Merge segment subtitle results into one artifact."""

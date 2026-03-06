from __future__ import annotations

from enum import Enum
from io import BytesIO
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from tnh_scholar.audio_processing.diarization.models import DiarizedSegment


class TranscriptionProvider(str, Enum):
    """Supported transcription providers for the multilingual workflow."""

    WHISPER = "whisper"
    ASSEMBLYAI = "assemblyai"


class ArtifactRetention(str, Enum):
    """Artifact retention policy for generated subtitles."""

    MINIMAL = "minimal"
    DEBUG = "debug"


class LanguageDetectionResult(BaseModel):
    """Language detection metadata for a routed segment or block."""

    language_code: str | None = Field(default=None)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    detector_source: str
    is_reliable: bool = True


class SpeakerLanguageBlock(BaseModel):
    """A speaker-contiguous block with language metadata."""

    speaker_label: str
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    detection: LanguageDetectionResult
    is_uncertain: bool = False


class SegmentTranscriptionRequest(BaseModel):
    """Segment-level transcription request for provider-neutral orchestration."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    audio_file: Path | BytesIO
    audio_file_extension: str | None = None
    provider: TranscriptionProvider
    source_language: str | None = None
    target_language: str = "en"
    transcription_model: str | None = None
    chars_per_caption: int = Field(default=42, ge=1)


class SegmentTranscriptionResult(BaseModel):
    """Segment-level subtitle generation result."""

    provider: TranscriptionProvider
    segment_start_ms: int = Field(default=0, ge=0)
    source_language: str | None = None
    target_language: str = "en"
    source_srt: str
    translated_srt: str | None = None
    translation_skipped: bool = False
    error_message: str | None = None


class MergedSubtitleArtifact(BaseModel):
    """Final user-facing subtitle artifact for the current MVP path."""

    provider: TranscriptionProvider
    source_language: str | None = None
    target_language: str = "en"
    source_srt: str
    final_english_srt: str
    artifact_retention: ArtifactRetention = ArtifactRetention.MINIMAL


class MultilingualTranscriptionRequest(BaseModel):
    """Top-level request for the multilingual transcription service."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    audio_file: Path
    provider: TranscriptionProvider = TranscriptionProvider.WHISPER
    source_language: str | None = None
    target_language: str = "en"
    transcription_model: str | None = None
    translation_model: str | None = None
    translation_pattern: str | None = None
    metadata_file: Path | None = None
    chars_per_caption: int = Field(default=42, ge=1)
    artifact_retention: ArtifactRetention = ArtifactRetention.MINIMAL
    skip_translation: bool = False
    use_speaker_blocks: bool = False
    diarization_segments: list[DiarizedSegment] | None = None

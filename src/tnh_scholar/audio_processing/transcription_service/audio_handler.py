"""
Audio handler utilities for slicing and assembling audio around diarization
chunks.  Designed for pipeline-friendly, single-responsibility methods so
that higher-level services can remain agnostic of the underlying audio
library.

This implementation purposely keeps logic minimal for testing.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError

from tnh_scholar.logging_config import get_child_logger

from .audio_models import AudioChunk

# TODO: Evaluate whether runtime type import isolation (using TYPE_CHECKING) is needed 
# across the codebase. E.g.:
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from .diarization_chunker import Chunk, ChunkerConfig, Segment
from .diarization_chunker import DiarizationChunk, DiarizationSegment

logger = get_child_logger(__name__)

class AudioHandlerConfig(BaseSettings):
    """
    Configuration settings for the AudioHandler.
    All audio time units are milliseconds (int)
    """

    output_format: str = Field(
        default="wav",
        description=
        "Audio output format used when exporting segments (e.g., 'wav', 'mp3')."
    )
    silence_between_segments: int = Field(
        default=1000,
        description="Duration of silence (in milliseconds) inserted between segments"
    )
    temp_storage_dir: Optional[Path] = Field(
        default=None,
        description=
        "Optional directory path for storing temporary audio files (currently unused)."
    )
    max_segment_length: Optional[int] = Field(
        default=None,
        description="Maximum allowed segment length (in milliseconds)."
    )
    gap_threshold: int = Field(
        default=4000,
        description="If gap between segments exceeds this, "
        "insert silence instead of using original audio."
    )
    silent_space_duration: int = Field(
        default=1000,
        description="Duration of silence inserted between separated segments."
    )
    class Config:
        env_prefix = "AUDIO_HANDLER_"  # Optional: allow env vars like AUDIO_HANDLER_OUTPUT_FORMAT
        
class AudioHandler:
    """Isolates audio operations and external dependencies (pydub, ffmpeg)."""

    def __init__(self, config: AudioHandlerConfig):
        self.config = config
        # Sensible fall‑backs for optional config values
        self.base_audio: AudioSegment
        self.input_format: str
        self.output_format: str = getattr(config, "output_format", "wav")
        self.min_silence_gap: int = getattr(config, "min_silence_gap", 300)

    def build_audio_chunk(self, chunk: DiarizationChunk, audio_file: Path) -> AudioChunk:
        """builds and sets the internal chunk.audio to be the new AudioChunk"""
        self.base_audio = self._load_audio(audio_file)
        processor = self._SegmentProcessor(self, chunk, self.base_audio)
        audio_segment = processor.process()
        audio_chunk = AudioChunk(
            data=self._export_audio(audio_segment),
            start_ms=chunk.start_time,
            end_ms=chunk.end_time,
            format=self.output_format,
        )
        chunk.audio = audio_chunk
        return audio_chunk

    class _SegmentProcessor:
        def __init__(self, handler: AudioHandler, chunk: DiarizationChunk, base_audio: AudioSegment):
            self.handler = handler
            self.chunk = chunk
            self.offset: int = 0
            self.base_audio: AudioSegment = base_audio
            self.previous_segment: Optional[DiarizationSegment] = None
            self.assembled_audio: AudioSegment = AudioSegment.empty()
            self.silent_spacing = self.handler.config.silent_space_duration
            self.gap_threshold = self.handler.config.gap_threshold
            
        @property
        def previous_end(self) -> int:
            return self.previous_segment.end if self.previous_segment else 0
        
        def gap_audio(self, segment: DiarizationSegment) -> AudioSegment:
            """
            Returns the audio gap between the previous segment and the current segment.
            If segments overlap (allowed in diarization), returns an empty AudioSegment.
            Raises an error if segments are out of order.
            """
            if self.previous_segment:
                if segment.start < self.previous_segment.start:
                    raise ValueError(
                        f"Segment start times out of order: {segment}, {self.previous_segment}"
                    )
                if segment.start < self.previous_end:
                    # Overlap: no gap audio
                    return AudioSegment.empty()
                result = self.base_audio[self.previous_end:segment.start]
                if isinstance(result, AudioSegment) and len(result) > 0:
                    return result
            return AudioSegment.empty()
            
        def process(self) -> AudioSegment:
            if len(self.base_audio) == 0:
                return AudioSegment.empty()
            for idx, d_segment in enumerate(self.chunk.segments):
                is_last = idx == len(self.chunk.segments) - 1
                self._process_segment(d_segment, is_last)
            return self._finalize()
        
        def _process_segment(self, segment: DiarizationSegment, is_last: bool) -> None:
            # Only include non-overlapping audio
            start = max(segment.start, self.offset)
            end = segment.end
            if start >= end:
                segment_audio = AudioSegment.empty()
            else:
                segment_audio = self.base_audio[start:end]

            if self.previous_segment is not None:
                gap = self._gap(segment)
                if gap < self.gap_threshold:
                    # keep this audio together as there is only a small gap
                    self._add_segment(self.gap_audio(segment))
                else:
                    # replace a larger gap with a smaller silent space for efficiency
                    # and removal of potential intervening noise
                    self._add_segment(AudioSegment.silent(duration=self.silent_spacing))

            self._add_segment(AudioSegment(segment_audio), segment)  # Forced to AudioSegment. Pylance issue
            self.previous_segment = segment

        def _gap(self, current: DiarizationSegment) -> int:
            return current.start - self.previous_end

        def _add_segment(
            self, 
            audio: AudioSegment, 
            segment: Optional[DiarizationSegment] = None
            ) -> None:
            self.assembled_audio += audio
            duration = len(audio)
            if segment is not None:
                segment.audio_map_time = self.offset
            self.offset += duration
        
        def _finalize(self) -> AudioSegment:
            return self.assembled_audio

    def _load_audio(self, audio_file: Path) -> AudioSegment:
        """Load the audio file and validate format."""
        self.input_format = audio_file.suffix.lstrip(".").lower()
        self.output_format = self.input_format # default
        return AudioSegment.from_file(audio_file, format=self.input_format)

    def _export_audio(
        self, 
        audio_segment: AudioSegment,  
        format: Optional[str] = None
        ) -> BytesIO:
        """Export *audio segment* in the configured format and return raw bytes."""
        buffer = BytesIO()
        try:
            audio_segment.export(buffer, format=format or self.output_format)
        except Exception as e:
            # You may want to use a logger here instead of print, depending on your codebase
            logger.error(f"Failed to export audio segment: {e}")
            raise RuntimeError(f"Audio export failed: {e}") from e
        return buffer
    
    def _validate_audio_format(self, audio_file: Path, expected_format: str) -> bool:
        """Check if the actual audio format matches the expected (extension) format."""
        try:
            audio = AudioSegment.from_file(audio_file)
            detected_format = audio.format_description.lower()
            return expected_format.lower() in detected_format
        except (CouldntDecodeError, OSError) as e:
            logger.error(f"Audio format validation failed for {audio_file}: {e}", exc_info=True)
            return False
        
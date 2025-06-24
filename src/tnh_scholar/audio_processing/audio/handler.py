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

from pydub import AudioSegment

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.pattern_share.app import ConfigurationError

# TODO: Evaluate whether runtime type import isolation (using TYPE_CHECKING) is needed 
# across the codebase. E.g.:
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from .diarization_chunker import Chunk, ChunkerConfig, Segment
from ..diarization.chunker import DiarizationChunk
from .config import AudioHandlerConfig
from .models import AudioChunk

logger = get_child_logger(__name__)


class AudioHandler:
    """Isolates audio operations and external dependencies (pydub, ffmpeg)."""

    def __init__(
        self, 
        config: AudioHandlerConfig = AudioHandlerConfig()
        ):
        self.config = config
        # Sensible fall‑backs for optional config values
        self.base_audio: AudioSegment
        self.output_format: Optional[str] = config.output_format
        self.input_format: Optional[str] = None

    def build_audio_chunk(self, chunk: DiarizationChunk, audio_file: Path) -> AudioChunk:
        """builds and sets the internal chunk.audio to be the new AudioChunk"""
        
        self._set_io_format(audio_file)
        base_audio = self._load_audio(audio_file)
        self._validate_segments(chunk)
        
        audio_segment = self._assemble_segments(chunk, base_audio)
        audio_chunk = AudioChunk(
            data=self._export_audio(audio_segment),
            start_ms=chunk.start_time,
            end_ms=chunk.end_time,
            format=self.output_format,
        )
        chunk.audio = audio_chunk
        return audio_chunk

    def _set_io_format(self, audio_file: Path):
        formats = self.config.SUPPORTED_FORMATS
        suffix = audio_file.suffix.lstrip(".").lower()
        if not suffix or suffix not in formats:
            raise ValueError(
                f"Unsupported or missing audio file format: '{audio_file.suffix}'. "
                f"Supported formats are: {', '.join(sorted(formats))}"
            )
        self.input_format = suffix

        # Use input format if output format not specified
        self.output_format = self.output_format or self.input_format
        
    def _load_audio(self, audio_file: Path) -> AudioSegment:
        """Load the audio file and validate format."""
        return AudioSegment.from_file(audio_file, format=self.input_format)

    def _validate_segments(self, chunk: DiarizationChunk):
        """Ensure all segments have gap_before and spacing_time attributes set."""
        for i, segment in enumerate(chunk.segments):
            if not hasattr(segment, "gap_before") or not hasattr(segment, "spacing_time"):
                raise ValueError(
                    f"Segment at index {i} missing required gap annotations: "
                    f"gap_before={getattr(segment, 'gap_before', None)}, "
                    f"spacing_time={getattr(segment, 'spacing_time', None)}"
                )

    def _assemble_segments(self, chunk: DiarizationChunk, base_audio: AudioSegment) -> AudioSegment:
        """Assemble audio for the given diarization chunk using gap information."""
        assembled = AudioSegment.empty()
        offset = 0
        prev_end: Optional[int] = None

        for segment in chunk.segments:
            
            if prev_end is not None:
                if self.config.silence_all_intervals or segment.gap_before:
                    assert segment.spacing_time is not None
                    if segment.spacing_time > 0:
                        assembled += AudioSegment.silent(duration=segment.spacing_time)
                        offset += segment.spacing_time
                elif segment.start > prev_end:
                    interval_audio = base_audio[prev_end:segment.start]
                    assembled += interval_audio
                    offset += len(interval_audio) # type: ignore

            # Append current segment audio
            seg_audio = base_audio[segment.start:segment.end]
            segment.audio_map_start = offset
            assembled += seg_audio
            offset += len(seg_audio) # type: ignore

            prev_end = segment.end

        return assembled
        
    def _export_audio(
        self, 
        audio_segment: AudioSegment,  
        format_str: Optional[str] = None
        ) -> BytesIO:
        """Export *audio segment* in the configured format and return raw bytes."""

        export_format = format_str or self.output_format
        supported_formats = self.config.SUPPORTED_FORMATS

        if not export_format:
            raise ConfigurationError("Cannot export. Output format not specified.")

        if export_format not in supported_formats:
            raise ValueError(
                f"Unsupported export format: '{export_format}'. "
                f"Supported formats are: {', '.join(sorted(supported_formats))}"
            )

        file_obj = BytesIO()
        try:
            audio_segment.export(file_obj, format=export_format)
        except Exception as e:
            logger.error(f"Failed to export audio segment: {e}")
            raise RuntimeError(f"Audio export failed: {e}") from e
        return file_obj
    
    def _add_filename_ext(self, file_obj: BytesIO, export_format: str):
        """"
        Some downstream APIs (e.g., OpenAI Whisper) require a file-like object with a .name attribute
        that includes a valid extension. We add this as a patch to avoid unnecessary disk I/O.
        """
        file_obj.name = f"audio_chunk_for_transcription.{export_format}"
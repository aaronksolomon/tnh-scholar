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

from tnh_scholar.exceptions import ConfigurationError
from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils import TNHAudioSegment as AudioSegment

# TODO: Evaluate whether runtime type import isolation (using TYPE_CHECKING) is needed 
# across the codebase. E.g.:
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from .diarization_chunker import Chunk, ChunkerConfig, Segment
from ..chunker import DiarizationChunk
from ..models import AudioChunk
from .config import AudioHandlerConfig

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
    
    def export_audio_bytes(self, audio_segment: AudioSegment, format_str: Optional[str] = None) -> BytesIO:
        """Export AudioSegment to BytesIO for services/modules that require file-like objects."""
        return self._export_audio(audio_segment, format_str)

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
        assembled: AudioSegment = AudioSegment.empty()
        offset = 0
        prev_end: Optional[int] = None
        audio_length = len(base_audio)

        def _clamp(val, min_val, max_val):
            return max(min_val, min(val, max_val))

        def _add_silence(duration):
            nonlocal assembled, offset
            if duration > 0:
                assembled += AudioSegment.silent(duration=duration)
                offset += duration

        def _add_interval_audio(start, end):
            nonlocal assembled, offset
            start = _clamp(start, 0, audio_length)
            end = _clamp(end, 0, audio_length)
            if end > start:
                interval_audio = base_audio[start:end]
                assembled += interval_audio
                offset += len(interval_audio)

        def _add_segment_audio(start, end):
            nonlocal assembled, offset
            start = _clamp(start, 0, audio_length)
            end = _clamp(end, 0, audio_length)
            if end > start:
                seg_audio: AudioSegment = base_audio[start:end]
                assembled += seg_audio
                offset += len(seg_audio)
                return len(seg_audio)
            return 0

        for segment in chunk.segments:
            seg_start = int(segment.start)
            seg_end = int(segment.end)

            # Handle gap before segment
            if prev_end is not None:
                if self.config.silence_all_intervals or getattr(segment, "gap_before", False):
                    spacing_time = getattr(segment, "spacing_time", 0)
                    _add_silence(spacing_time)
                elif seg_start > prev_end:
                    _add_interval_audio(prev_end, seg_start)

            # Append current segment audio (clamped)
            segment.audio_map_start = offset
            _add_segment_audio(seg_start, seg_end)

            prev_end = seg_end

        return assembled

    # TODO: in _export_audio:
    # handle needed parameters for various export formats (can use kwargs for options)    
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
            file_obj.seek(0)
        except Exception as e:
            logger.error(f"Failed to export audio segment: {e}")
            raise RuntimeError(f"Audio export failed: {e}") from e
        return file_obj

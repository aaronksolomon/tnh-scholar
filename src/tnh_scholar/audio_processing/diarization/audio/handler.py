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

    def _clamp_bounds(self, start: int, end: int, audio_length: int) -> tuple[int, int]:
        """Clamp audio slice bounds to the available audio length."""
        return max(0, min(start, audio_length)), max(0, min(end, audio_length))

    def _append_audio_slice(
        self,
        assembled: AudioSegment,
        base_audio: AudioSegment,
        start: int,
        end: int,
        audio_length: int,
    ) -> tuple[AudioSegment, int]:
        """Append a clamped audio slice and return updated audio plus appended length."""
        start, end = self._clamp_bounds(start, end, audio_length)
        if end <= start:
            return assembled, 0
        interval_audio: AudioSegment = base_audio[start:end]
        return assembled + interval_audio, len(interval_audio)

    def _append_gap_content(
        self,
        assembled: AudioSegment,
        segment: DiarizationChunk | object,
        prev_end: int,
        seg_start: int,
        base_audio: AudioSegment,
        audio_length: int,
    ) -> tuple[AudioSegment, int]:
        """Append either silence or the real audio between two diarized segments."""
        if self.config.silence_all_intervals or getattr(segment, "gap_before", False):
            spacing_time = getattr(segment, "spacing_time", 0)
            if spacing_time <= 0:
                return assembled, 0
            return assembled + AudioSegment.silent(duration=spacing_time), spacing_time
        if seg_start <= prev_end:
            return assembled, 0
        return self._append_audio_slice(
            assembled,
            base_audio,
            prev_end,
            seg_start,
            audio_length,
        )

    def _assemble_segments(self, chunk: DiarizationChunk, base_audio: AudioSegment) -> AudioSegment:
        """Assemble audio for the given diarization chunk using gap information."""
        assembled: AudioSegment = AudioSegment.empty()
        offset = 0
        prev_end: Optional[int] = None
        audio_length = len(base_audio)

        for segment in chunk.segments:
            seg_start = int(segment.start)
            seg_end = int(segment.end)

            if prev_end is not None:
                assembled, added_gap = self._append_gap_content(
                    assembled,
                    segment,
                    prev_end,
                    seg_start,
                    base_audio,
                    audio_length,
                )
                offset += added_gap

            segment.audio_map_start = offset
            assembled, added_segment = self._append_audio_slice(
                assembled,
                base_audio,
                seg_start,
                seg_end,
                audio_length,
            )
            offset += added_segment

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

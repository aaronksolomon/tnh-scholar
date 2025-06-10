# tnh_scholar.audio_processing.transcription_service.diarization_chunker.py

from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from pydantic_settings import BaseSettings

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils import convert_ms_to_sec, convert_sec_to_ms

from .audio_models import AudioChunk

logger = get_child_logger(__name__)


# TODO Create protocols and interfaces for the diarization-transcription pipeline modules:
# DiarizationChunker, AudioHandler, TimelineMapper, TranscriptionService

# TODO Deprecate or remove speaker change logic

# TODO Consider using a ChunkingStrategy class for chunking strategies (?)

class ChunkerConfig(BaseSettings):
    """Simple configuration for audio chunking algorithm."""
    
    # Target duration for each chunk in milliseconds (default: 5 minutes = 300,000ms)
    target_time: int = 300_000

    # Minimum duration for final chunk (in ms); shorter chunks are merged
    min_chunk_time: int = 30_000 # 30 seconds
    
    # If set to true, all speakers are set to default speaker label
    single_speaker: bool = False
    
    # Maximum allowed gap between segments for audio processing
    gap_threshold: int = 4000
    
    # Spacing used between segments that are greater than gap threshold ms apart
    gap_spacing_time: int = 1000 
    
    default_speaker_label: str = "SPEAKER_00"
    

class DiarizationSegment(BaseModel):
    """Represents a speaker segment from diarization."""
    speaker: str
    start: int  # Start time in milliseconds
    end: int    # End time in milliseconds
    audio_map_start: Optional[int] # location in the audio output file
    gap_before: Optional[bool] # indicates a gap > gap_threshold before this segment
    spacing_time: Optional[int] # spacing between this and previous segment; adjusted spacing if gap before
    
    @property
    def duration(self) -> int:
        """Get segment duration in milliseconds."""
        return self.end - self.start

    @property
    def duration_sec(self) -> float:
        return convert_ms_to_sec(self.duration)
    
    @property
    def mapped_start(self):
        """Downstream registry field set by the audio handler"""
        return self.start if self.audio_map_start is None else self.audio_map_start
    
    @property
    def mapped_end(self):
        if self.audio_map_start is None:
            return self.end 
        else:
            return self.audio_map_start + self.duration 
    
    def normalize(self) -> None:
        """Normalize the duration of the segment to be nonzero and validate start/end values."""
        # Validate that start and end are non-negative integers
        if not isinstance(self.start, int) or not isinstance(self.end, int):
            raise ValueError("Segment start and end must be integers, "
                             f"got start={self.start}, end={self.end}")
        if self.start < 0 or self.end < 0:
            raise ValueError(f"Segment start and end must be non-negative, "
                             f"got start={self.start}, end={self.end}")

        # Explicitly handle negative durations
        if self.end < self.start:
            logger.warning(
                f"Invalid segment duration detected: start ({self.start}) > end ({self.end}). "
                "Adjusting end to ensure minimum duration of 1."
            )
            self.end = self.start + 1  # set minimum nonzero duration

        # Ensure minimum nonzero duration
        if self.start == self.end:
            logger.warning(
                f"Zero segment duration detected: start ({self.start}) == end ({self.end}). "
                "Adjusting end to ensure minimum duration of 1."
            )
            self.end = self.start + 1  # set minimum nonzero duration

            
class DiarizationChunk(BaseModel):
    """Represents a chunk of segments to be processed together."""
    start_time: int  # Start time in milliseconds
    end_time: int    # End time in milliseconds
    audio: Optional[AudioChunk] = None
    segments: List[DiarizationSegment]
    accumulated_time: int = 0
    class Config:
        arbitrary_types_allowed = True
    
    @property
    def total_duration(self) -> int:
        """Get chunk duration in milliseconds."""
        return self.end_time - self.start_time
    
    @property
    def total_duration_sec(self) -> float:
        return convert_ms_to_sec(self.total_duration)


class DiarizationChunker:
    """
    Class for chunking diarization results into processing units
    based on configurable duration targets.
    """
    
    def __init__(self, **config_options):
        """Initialize chunker with additional config_options."""
        self.config = ChunkerConfig()
        
        self._handle_config_options(config_options)
        
    def to_segments(self, pyannote_data: Dict[str, Any]) -> List[DiarizationSegment]:
        """
        Convert a pyannoteai diarization result dict to list of DiarizationSegment objects.
        
        Args:
            diarization_data: Dictionary containing diarization results
            
        Returns:
            List of Segment objects with times converted to milliseconds
        """

        speaker_label = self.config.default_speaker_label
        single_speaker = self.config.single_speaker
        
        segments = []
        for entry in pyannote_data.get('diarization', []):
            segment = DiarizationSegment(
                speaker=speaker_label if single_speaker else entry['speaker'],
                start=convert_sec_to_ms(entry['start']),
                end=convert_sec_to_ms(entry['end']),
                audio_map_start=None,
                gap_before=None,
                spacing_time=None,
            )
            segments.append(segment)
            
        return self.sort_and_normalize_segments(segments)
        
    def sort_and_normalize_segments(
        self, segments: List[DiarizationSegment]
        ) -> List[DiarizationSegment]:
        """
        Validate and normalize segments by sorting and ensuring nonzero duration.
        
        Args:
            segments: List of diarization segments
            
        Returns:
            List of sorted and normalized segments
        """
        self.sort_by_start(segments)
        for segment in segments:
            segment.normalize()
        return segments
    
    def sort_by_start(self, segments: List[DiarizationSegment]) -> None:
        """Sort segments by start time."""
        segments.sort(key=lambda segment: segment.start)
    
    def extract_chunks_by_speaker(
        self, segments: List[DiarizationSegment]
        ) -> Dict[str, List[DiarizationChunk]]:
        """
        Split diarization segments into chunks of approximately target_duration,
        splitting at speaker changes.

        Args:
            segments: List of speaker segments from diarization

        Returns:
            Dict[str, List[Chunk]]: Mapping from speaker label to list of chunks
        """
        if not segments:
            return {}

        extractor = self._ChunkExtractor(self.config, split_on_speaker_change=True)
        chunks = extractor.extract(segments)
        return self._group_chunks_by_speaker(chunks)

    def extract_contiguous_chunks(self, segments: List[DiarizationSegment]) -> List[DiarizationChunk]:
        """
        Split diarization segments into contiguous chunks of
        approximately target_duration, without splitting on speaker changes.

        Args:
            segments: List of speaker segments from diarization

        Returns:
            List[Chunk]: Flat list of contiguous chunks
        """
        if not segments:
            return []

        extractor = self._ChunkExtractor(self.config, split_on_speaker_change=False)
        return extractor.extract(segments)

    class _ChunkExtractor:
        def __init__(self, config: ChunkerConfig, split_on_speaker_change: bool = True):
            self.config = config
            self.split_on_speaker_change = split_on_speaker_change
            self.gap_threshold = self.config.gap_threshold
            self.spacing = self.config.gap_spacing_time
            self.chunks: List[DiarizationChunk] = []
            self.current_chunk_segments: List[DiarizationSegment] = []
            self.chunk_start: int = 0
            self.current_speaker = ""
            self.accumulated_time: int = 0
            
        @property
        def last_segment(self):
            return self.current_chunk_segments[-1] if self.current_chunk_segments else None

        def extract(self, segments: List[DiarizationSegment]) -> List[DiarizationChunk]:
            if not segments:
                return []

            self.chunk_start = segments[0].start
            self.current_speaker = segments[0].speaker
            for segment in segments:
                self._check_segment_duration(segment)  
                self._process_segment(segment)

            self._finalize_last_chunk()
            return self.chunks

        def _process_segment(self, segment: DiarizationSegment):
            if self._should_split(segment):
                self._finalize_current_chunk(segment)
                self.chunk_start = segment.start                
            self._add_segment(segment)
    
        def _add_segment(self, segment: DiarizationSegment):
            gap_time =  self._gap_time(segment)
            if gap_time > self.gap_threshold:
                segment.gap_before = True
                segment.spacing_time = self.spacing
                self.accumulated_time += segment.duration + self.spacing
            else:
                segment.gap_before = False
                segment.spacing_time = max(gap_time, 0)
                self.accumulated_time += segment.duration + gap_time
            self.current_chunk_segments.append(segment)
            self.current_speaker = segment.speaker
            
        def _gap_time(self, segment) -> int:
            if self.last_segment is None:
                # If no last_segment, this is first segment, so no gap.
                return 0 
            else:
                return segment.start - self.last_segment.end
            
        def _speaker_change(self, segment):
            return segment.speaker != self.current_speaker

        def _should_split(self, segment: DiarizationSegment) -> bool:
            gap_time = self._gap_time(segment)
            interval_time = gap_time if gap_time < self.gap_threshold else self.spacing
            accumulated_time = self.accumulated_time + interval_time + segment.duration
            split_on_time = accumulated_time >= self.config.target_time
            split_on_speaker = self._speaker_change(segment) \
                if self.split_on_speaker_change else False
            return split_on_time or split_on_speaker
         
        def _finalize_current_chunk(self, next_segment: Optional[DiarizationSegment]):
            if self.current_chunk_segments:
                assert self.last_segment is not None
                self.chunks.append(
                    DiarizationChunk(
                        start_time=self.chunk_start,
                        end_time=self.last_segment.end, 
                        segments=self.current_chunk_segments.copy(),
                        audio=None,
                        accumulated_time=self.accumulated_time
                    )
                )
                self._reset_chunk_state(next_segment)             
                    
        def _reset_chunk_state(self, next_segment):
            self.current_chunk_segments = []
            self.accumulated_time = 0
            if self.split_on_speaker_change and next_segment:
                    self.current_speaker = next_segment.speaker

        def _finalize_last_chunk(self):
            if self.current_chunk_segments:
                self._handle_final_segments()
        
        def _check_segment_duration(self, segment: DiarizationSegment) -> None:
            """Check if segment exceeds target duration and issue warning if needed."""
            if segment.duration > self.config.target_time:
                logger.warning(f"Found segment longer than "
                            f"target duration: {segment.duration_sec:.0f}s")
                
        def _handle_final_segments(self) -> None:
            """Append final segments to last chunk if below min duration."""
            approx_remaining_time = sum(segment.duration for segment in self.current_chunk_segments)
            final_time = self.accumulated_time + approx_remaining_time
            min_time = self.config.min_chunk_time

            if final_time < min_time and self.chunks:
               self._merge_to_last_chunk()
            else:
                # Create standalone chunk
                self._finalize_current_chunk(next_segment=None)
                
        def _merge_to_last_chunk(self):
            """Merge segments to the last chunk processed. self.chunks cannot be empty."""
            assert self.chunks
            self.chunks[-1].segments.extend(self.current_chunk_segments)
            self.chunks[-1].end_time = self.current_chunk_segments[-1].end
            self.chunks[-1].accumulated_time += self.accumulated_time
                    
    def _group_chunks_by_speaker(self, chunks: List[DiarizationChunk]) -> Dict[str, List[DiarizationChunk]]:
        chunks_by_speaker: Dict[str, List[DiarizationChunk]] = {}
        for chunk in chunks:
            speaker = chunk.segments[0].speaker \
                if chunk.segments else self.config.default_speaker_label
            chunks_by_speaker.setdefault(speaker, []).append(chunk)
        return chunks_by_speaker
    
    def _handle_config_options(self, config_options: Dict[str, Any]) -> None:
        """
        Handles additional configuration options, 
        logging a warning for unrecognized keys.
        """
        for key, value in config_options.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                logger.warning(f"Unrecognized configuration option: {key}")

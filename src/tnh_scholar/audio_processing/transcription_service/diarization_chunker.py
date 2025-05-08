# tnh_scholar.audio_processing.transcription_service.diarization_chunker.py

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils import convert_ms_to_sec, convert_sec_to_ms

from .audio_models import AudioChunk

logger = get_child_logger(__name__)

class ChunkerConfig:
    """Simple configuration for audio chunking algorithm."""
    
    # Target duration for each chunk in milliseconds (default: 5 minutes = 300,000ms)
    target_duration: int = 300_000

    # Minimum duration for final chunk (in ms); shorter chunks are merged
    min_chunk_duration: int = 30_000
    
    # If set to true, all speakers are set to default speaker label
    single_speaker: bool = False
    
    default_speaker_label = "SPEAKER_00"
    
    # Potential future parameters:
    # - gap_threshold_ms: int - Consider silence gaps as natural boundaries

class DiarizationSegment(BaseModel):
    """Represents a speaker segment from diarization."""
    speaker: str
    start: int  # Start time in milliseconds
    end: int    # End time in milliseconds
    audio_map_time: Optional[int] # location in the audio output file
    
    @property
    def duration(self) -> int:
        """Get segment duration in milliseconds."""
        return self.end - self.start

    @property
    def duration_sec(self) -> float:
        return convert_ms_to_sec(self.duration)
    
    @property
    def mapped_start(self):
        return self.audio_map_time or self.start
    
    @property
    def mapped_end(self):
        return self.audio_map_time + self.duration if self.audio_map_time else self.end
    
    def normalize(self) -> None:
        """Normalize the duration of the segment to be nonzero"""
        if self.start == self.end:
            self.end = self.start + 1 # minimum duration 
            
    


class DiarizationChunk(BaseModel):
    """Represents a chunk of segments to be processed together."""
    start_time: int  # Start time in milliseconds
    end_time: int    # End time in milliseconds
    audio: Optional[AudioChunk] = None
    segments: List[DiarizationSegment]
    
    @property
    def duration(self) -> int:
        """Get chunk duration in milliseconds."""
        return self.end_time - self.start_time
    
    @property
    def duration_sec(self) -> float:
        return convert_ms_to_sec(self.duration) 

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
        Convert a pyannoteai diarization result dict to list of Segment objects.
        
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
                audio_map_time=None
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
        segments.sort(key=lambda s: s.start)
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
            self.chunks: List[DiarizationChunk] = []
            self.current_chunk_segments: List[DiarizationSegment] = []
            self.chunk_start = 0
            self.current_speaker = ""

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
            self.current_chunk_segments.append(segment)
            
        def _speaker_change(self, segment):
            return segment.speaker != self.current_speaker

        def _should_split(self, segment: DiarizationSegment) -> bool:
            current_end = segment.end
            duration = current_end - self.chunk_start
            split_on_time = duration >= self.config.target_duration
            split_on_speaker = self._speaker_change(segment) \
                if self.split_on_speaker_change else False
            return split_on_time or split_on_speaker

        def _finalize_current_chunk(self, next_segment: DiarizationSegment):
            if self.current_chunk_segments:
                self.chunks.append(
                    DiarizationChunk(
                        start_time=self.chunk_start,
                        end_time=self.current_chunk_segments[-1].end,
                        segments=self.current_chunk_segments.copy(),
                        audio=None,
                    )
                )
                self.current_chunk_segments = []
                if self.split_on_speaker_change:
                    self.current_speaker = next_segment.speaker

        def _finalize_last_chunk(self):
            if self.current_chunk_segments:
                self._handle_final_segments()
        
        def _check_segment_duration(self, segment: DiarizationSegment) -> None:
            """Check if segment exceeds target duration and issue warning if needed."""
            if segment.duration > self.config.target_duration:
                logger.warning(f"Found segment longer than "
                            f"target duration: {segment.duration_sec:.0f}s")
                
        def _handle_final_segments(self) -> None:
            """Append final segments to last chunk if below min duration."""
            final_end = self.current_chunk_segments[-1].end
            final_duration = final_end - self.chunk_start
            min_duration = getattr(self.config, "min_chunk_duration")

            if final_duration < min_duration and self.chunks:
                # Merge into previous chunk
                self.chunks[-1].segments.extend(self.current_chunk_segments)
                self.chunks[-1].end_time = final_end
            else:
                # Create standalone chunk
                self.chunks.append(
                    DiarizationChunk(start_time=self.chunk_start, 
                          end_time=self.current_chunk_segments[-1].end, 
                          segments=self.current_chunk_segments.copy(),
                          audio=None,
                          )
                )
                    
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

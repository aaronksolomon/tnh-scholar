# tnh_scholar.audio_processing.transcription_service.diarization_chunker.py

from typing import Any, Dict, List, Optional

from tnh_scholar.logging_config import get_child_logger

from .config import ChunkConfig
from .models import DiarizationChunk, DiarizedSegment

logger = get_child_logger(__name__)

# TODO Implement a ChunkingStrategy class for chunking strategies

class DiarizationChunker:
    """
    Class for chunking diarization results into processing units
    based on configurable duration targets.
    """
    
    def __init__(self, **config_options):
        """Initialize chunker with additional config_options."""
        self.config = ChunkConfig()
        
        self._handle_config_options(config_options)
                    

    def extract_contiguous_chunks(self, segments: List[DiarizedSegment]) -> List[DiarizationChunk]:
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
        def __init__(self, config: ChunkConfig, split_on_speaker_change: bool = True):
            self.config = config
            self.split_on_speaker_change = split_on_speaker_change
            self.gap_threshold = self.config.gap_threshold
            self.spacing = self.config.gap_spacing_time
            self.chunks: List[DiarizationChunk] = []
            self.current_chunk_segments: List[DiarizedSegment] = []
            self.chunk_start: int = 0
            self.current_speaker = ""
            self.accumulated_time: int = 0
            
        @property
        def last_segment(self):
            return self.current_chunk_segments[-1] if self.current_chunk_segments else None

        def extract(self, segments: List[DiarizedSegment]) -> List[DiarizationChunk]:
            if not segments:
                return []

            self.chunk_start = int(segments[0].start)
            self.current_speaker = segments[0].speaker
            for segment in segments:
                self._check_segment_duration(segment)  
                self._process_segment(segment)

            self._finalize_last_chunk()
            return self.chunks

        def _process_segment(self, segment: DiarizedSegment):
            if self._should_split(segment):
                self._finalize_current_chunk(segment)
                self.chunk_start = int(segment.start)                
            self._add_segment(segment)
    
        def _add_segment(self, segment: DiarizedSegment):
            gap_time =  self._gap_time(segment)
            if gap_time > self.gap_threshold:
                segment.gap_before = True
                segment.spacing_time = self.spacing
                self.accumulated_time += int(segment.duration) + self.spacing
            else:
                segment.gap_before = False
                segment.spacing_time = max(gap_time, 0)
                self.accumulated_time += int(segment.duration) + gap_time
            self.current_chunk_segments.append(segment)
            self.current_speaker = segment.speaker
            
        def _gap_time(self, segment) -> int:
            if self.last_segment is None:
                # If no last_segment, this is first segment, so no gap.
                return 0 
            else:
                return segment.start - self.last_segment.end
            

        def _should_split(self, segment: DiarizedSegment) -> bool:
            gap_time = self._gap_time(segment)
            interval_time = gap_time if gap_time < self.gap_threshold else self.spacing
            accumulated_time = self.accumulated_time + interval_time + segment.duration
            return accumulated_time >= self.config.target_duration 
         
        def _finalize_current_chunk(self, next_segment: Optional[DiarizedSegment]):
            if self.current_chunk_segments:
                assert self.last_segment is not None
                self.chunks.append(
                    DiarizationChunk(
                        start_time=int(self.chunk_start),
                        end_time=int(self.last_segment.end), 
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
        
        def _check_segment_duration(self, segment: DiarizedSegment) -> None:
            """Check if segment exceeds target duration and issue warning if needed."""
            if segment.duration > self.config.target_duration:
                logger.warning(f"Found segment longer than "
                            f"target duration: {segment.duration_sec:.0f}s")
                
        def _handle_final_segments(self) -> None:
            """Append final segments to last chunk if below min duration."""
            approx_remaining_time = sum(segment.duration for segment in self.current_chunk_segments)
            final_time = self.accumulated_time + approx_remaining_time
            min_time = self.config.min_duration

            if final_time < min_time and self.chunks:
               self._merge_to_last_chunk()
            else:
                # Create standalone chunk
                self._finalize_current_chunk(next_segment=None)
                
        def _merge_to_last_chunk(self):
            """Merge segments to the last chunk processed. self.chunks cannot be empty."""
            assert self.chunks
            self.chunks[-1].segments.extend(self.current_chunk_segments)
            self.chunks[-1].end_time = int(self.current_chunk_segments[-1].end)
            self.chunks[-1].accumulated_time += self.accumulated_time
                    

    
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

# tnh_scholar.audio_processing.diarization.strategies.time_gap.py
"""
TimeGapChunker – baseline strategy: split purely on accumulated time.
"""

from __future__ import annotations

from typing import List

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils import TimeMs

from .._diarization_utils import ChunkAccumulator, SegmentWalker
from ..config import DiarizationConfig
from ..models import DiarizationChunk, DiarizedSegment
from ..protocols import ChunkingStrategy

logger = get_child_logger(__name__)


class TimeGapChunker(ChunkingStrategy):
    """Chunker that ignores speaker/language and uses only time-gap logic."""

    def __init__(self, config: DiarizationConfig = DiarizationConfig()):
        self.cfg = config

    def extract(self, segments: List[DiarizedSegment]) -> List[DiarizationChunk]:
        """Extract time-based chunks from diarization segments."""
        if not segments:
            return []

        walker = SegmentWalker(segments)
        accumulator = ChunkAccumulator(self.cfg)

        for context in walker.walk():
            if self._should_finalize_chunk(context, accumulator):
                accumulator.finalize_chunk()
            
            gap_time, gap_before = self._calculate_gap_info(context)
            accumulator.add_segment(context.segment, gap_time, gap_before)

        return accumulator.finalize_and_get_chunks()

    def _should_finalize_chunk(self, context, accumulator: ChunkAccumulator) -> bool:
        """Determine if current chunk should be finalized before adding segment."""
        if not accumulator.current_segments:
            return False
        
        gap_time, _ = self._calculate_gap_info(context)
        projected_time = accumulator.accumulated_time + context.segment.duration + gap_time
        
        # Don't split if remaining time would create small final chunk
        if context.remaining_time < self.cfg.chunk.min_duration:
            return False
            
        return projected_time >= self.cfg.chunk.target_duration

    def _calculate_gap_info(self, context) -> tuple[TimeMs, bool]:
        """Calculate gap time and gap_before flag for current segment."""
        if context.is_first:
            return TimeMs(0), False
        
        gap_time = context.time_interval_prev or TimeMs(0)
        gap_before = gap_time > self.cfg.chunk.gap_threshold
        
        # Use configured spacing for large gaps, actual gap time for small gaps
        spacing_time = TimeMs(self.cfg.chunk.gap_spacing_time) if gap_before else gap_time
        
        return spacing_time, gap_before
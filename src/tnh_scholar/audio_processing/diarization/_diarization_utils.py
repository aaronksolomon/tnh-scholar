# tnh_scholar.audio_processing.diarization._utils.py
"""
Shared utilities for diarization strategies using context-based traversal.
"""

from __future__ import annotations

from typing import Iterator, List, Optional

from tnh_scholar.utils import TimeMs

from .models import DiarizationChunk, DiarizedSegment


class SegmentContext:
    """Rich context for current segment during traversal."""
    
    def __init__(
        self, 
        segment: DiarizedSegment,
        prev_segment: Optional[DiarizedSegment],
        next_segment: Optional[DiarizedSegment], 
        consumed_time: TimeMs,
        remaining_time: TimeMs,
        index: int,
        total_segments: int,
    ):
        self.segment = segment
        self.prev = prev_segment
        self.next = next_segment
        self.consumed_time = consumed_time
        self.remaining_time = remaining_time
        self.index = index
        self.total_segments = total_segments
    
    @property
    def time_interval_next(self) -> Optional[TimeMs]:
        """
        Time interval between current segment end and next segment start. 
        Can be negative if segments overlap.
        """
        return TimeMs(self.next.start - self.segment.end) if self.next else None
    
    @property
    def time_interval_prev(self) -> Optional[TimeMs]:
        """
        Time interval between current segment start and previous segment end. 
        Can be negative if segments overlap.
        """
        return TimeMs(self.segment.start - self.prev.end) if self.prev else None
    
    @property
    def speaker_changed_from_prev(self) -> bool:
        """True if speaker changed from previous segment."""
        return self.prev is not None and self.prev.speaker != self.segment.speaker
    
    @property
    def speaker_changes_to_next(self) -> bool:
        """True if speaker changes to next segment."""
        return self.next is not None and self.next.speaker != self.segment.speaker
    
    @property
    def is_first(self) -> bool:
        """True if this is the first segment."""
        return self.index == 0
    
    @property
    def is_last(self) -> bool:
        """True if this is the last segment."""
        return self.index == self.total_segments - 1
    
    def __repr__(self) -> str:
        return (f"SegmentContext(index={self.index}, speaker='{self.segment.speaker}', "
                f"elapsed={self.consumed_time}, remaining={self.remaining_time})")


class SegmentWalker:
    """Manages segment collection and provides rich context during iteration."""
    
    def __init__(self, segments: List[DiarizedSegment]):
        if not segments:
            raise ValueError("Cannot create walker with empty segment list.")
        
        self.segments = segments
        self.total_segments = len(segments)
        self.total_time = TimeMs(sum(seg.duration for seg in segments))
    
    def walk(self) -> Iterator[SegmentContext]:
        """
        Iterate through segments yielding rich context for each.
        
        Yields:
            SegmentContext: Rich context for each segment including timing and neighbors
        """
        consumed = TimeMs(0)

        for i, segment in enumerate(self.segments):
            remaining = self.total_time - consumed
            prev_segment = self.segments[i-1] if i > 0 else None
            next_segment = self.segments[i+1] if i < self.total_segments-1 else None

            yield SegmentContext(
                segment=segment,
                prev_segment=prev_segment,
                next_segment=next_segment,
                consumed_time=TimeMs(consumed),
                remaining_time=TimeMs(remaining),
                index=i,
                total_segments=self.total_segments,
            )
            consumed += segment.duration


class ChunkAccumulator:
    """Handles chunk building logic with configurable finalization rules."""
    
    def __init__(self, config):
        self.config = config
        self.current_segments: List[DiarizedSegment] = []
        self.chunks: List[DiarizationChunk] = []
        self.chunk_start_time: Optional[TimeMs] = None
        self.accumulated_time: TimeMs = TimeMs(0)
    
    def add_segment(self, segment: DiarizedSegment, segment_spacing: TimeMs, gap_before: bool) -> None:
        """
        Add segment to current chunk with specified gap handling.

        This is the ONLY place where `segment.gap_before` and `segment.spacing_time` are set.
        If either is already set, a ValueError is raised to enforce this contract.

        Args:
            segment: Segment to add
            segment_spacing: the time between this and previous segment
            gap_before: True if the previous segment is far enough away in time 
            that a smaller silent gap is added, and interval is condensed.
        """
        if not self.current_segments:
            self.chunk_start_time = segment.start
            self.accumulated_time = TimeMs(0)

        # Enforce that these fields are only set here
        if getattr(segment, "gap_before", None) is not None:
            raise ValueError("segment.gap_before is already set. This should only be set in add_segment().")
        if getattr(segment, "spacing_time", None) is not None:
            raise ValueError("segment.spacing_time is already set. This should only be set in add_segment().")

        self.current_segments.append(segment)
        segment.gap_before = gap_before
        segment.spacing_time = segment_spacing
        self.accumulated_time += segment.duration + segment_spacing

    def finalize_chunk(self) -> DiarizationChunk:
        """Create chunk from current segments and reset state."""
        if not self.current_segments:
            raise ValueError("Cannot finalize empty chunk")
        
        if self.chunk_start_time is None:
            raise ValueError("Chunk start time not set. "
                             "Possibly no segments have been added to the accumulator."
                             )
        chunk = DiarizationChunk(
            start_time=self.chunk_start_time,
            end_time=int(self.current_segments[-1].end),
            segments=self.current_segments.copy(),
            audio=None,
            accumulated_time=self.accumulated_time
        )
        
        self.chunks.append(chunk)
        self._reset_state()
        return chunk
    
    def finalize_and_get_chunks(self) -> List[DiarizationChunk]:
        """Finalize any remaining chunk and return all chunks."""
        if self.current_segments:
            self.finalize_chunk()
        return self.chunks.copy()
    
    
    def _reset_state(self) -> None:
        """Reset accumulator state for next chunk."""
        self.current_segments = []
        self.chunk_start_time = None
        self.accumulated_time = TimeMs(0)


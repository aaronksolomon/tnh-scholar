"""
Timeline mapping utilities for transforming timestamps from chunk-relative
coordinates to original audio coordinates.

This module enables mapping transcript segments back to their original positions
in the source audio after processing chunked audio.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

from tnh_scholar.logging_config import get_child_logger

from ..timed_object.timed_text import TimedText, TimedTextUnit
from .models import DiarizationChunk, DiarizedSegment

logger = get_child_logger(__name__)

class TimelineMapperConfig(BaseModel):
    """Configuration options for timeline mapping."""
    
    debug_logging: bool = Field(
        default=False,
        description="Enable detailed logging of mapping decisions"
    )
    map_speakers: bool = Field(
        default=True,
        description="Assign speaker to mapped timings using diarization segment speaker."
    )
    

class TimelineMapper:
    """Maps timestamps from chunk-relative coordinates to original audio coordinates."""
    
    def __init__(self, config: Optional[TimelineMapperConfig] = None):
        """Initialize with optional configuration."""
        self.config = config or TimelineMapperConfig()
    
    def remap(self, timed_text: TimedText, chunk: DiarizationChunk) -> TimedText:
        """
        Remap all timestamps in a TimedText object from chunk-relative to original audio coordinates.
        
        Args:
            timed_text: TimedText with chunk-relative timestamps
            chunk: DiarizationChunk containing mapping information
            
        Returns:
            New TimedText object with remapped timestamps
        """
        
        self._validate_diarize_segments(chunk)
        mapper = self._TimeUnitMapper(chunk.segments, self.config)
        self._validate_timed_text(timed_text)    
        
        if timed_text.segments:    
            timed_text = mapper.map_timed_text(timed_text)
        
        if timed_text.words:
            timed_text = mapper.map_timed_text(timed_text)
            
        return timed_text
    
    def _validate_diarize_segments(self, chunk: DiarizationChunk):
        if not (segments:=chunk.segments):
            logger.error("Empty segments.")
            raise ValueError("Cannot remap with empty chunk segments.")
        
        # Validate segments
        for segment in segments:
            if segment.audio_map_start is None:
                raise ValueError(f"Remap not possible. Segment {segment} is missing audio_map_time.")
            segment.normalize() 
            
    def _validate_timed_text(self, timed_text: TimedText):
        timed_text.sort_by_start()
        for timed_unit in timed_text.iter():
            timed_unit.normalize()
        
    class _TimeUnitMapper:
        """Internal helper class for time-unit mapping."""
        
        def __init__(self, map_segments: List[DiarizedSegment], config: TimelineMapperConfig):
            self.map_segments = map_segments
            self.config = config            
        
        def map_timed_text(self, tt: TimedText) -> TimedText:
            """Map timestamps in all TimedTextUnit collections contained in the TimedText object."""
            new_tt = tt.model_copy(deep=True)

            sources: List[Tuple[str, List[TimedTextUnit]]] = []
            if tt.is_segment_granularity():
                sources.append(("segments", tt.segments))
            if tt.is_word_granularity():
                sources.append(("words", tt.words))

            for attr, units in sources:
                mapped_units = [self._map_text_unit(u) for u in units]
                setattr(new_tt, attr, mapped_units)

            return new_tt
        
        def _map_text_unit(self, unit: TimedTextUnit) -> TimedTextUnit:
            """Map a single TimedTextUnit's timestamps."""
            # Find the best matching segment
            best_segment = self._find_best_segment(unit)

            # Debug logging for mapping decision
            if self.config.debug_logging:
                self._log_mapping_choice(unit, best_segment)

            # Apply mapping transformation and return new unit
            return self._apply_mapping(
                unit,
                best_segment
            )
            
        
        def _log_mapping_choice(self, unit, segment):
            logger.info(
                    f"Mapping unit (start: {unit.start_ms}, end: {unit.end_ms}) "
                    f"to segment (start: {segment.start}, end: {segment.end}, "
                    f"mapped_start: {segment.mapped_start}, mapped_end: {segment.mapped_end})"
                )
            
        def _find_best_segment(self, unit: TimedTextUnit) -> DiarizedSegment:
            """
            Find the best segment to use for mapping a TimedTextUnit.
            
            First tries to find segments with direct overlap.
            If none, finds proximal segments and chooses the closest.
            """
            if overlapping := self._find_overlapping_segments(unit):
                return self._choose_best_overlap(unit, overlapping)

            # If no overlaps, find proximal segments
            before, after = self._find_proximal_segments(unit)

            if before is None and after is None:
                raise ValueError("A before or after segment was not found.")
            
            if before is None:
                return after # type: ignore
            if after is None:
                return before

            # Choose closest proximal segment
            return self._choose_closest_proximal(unit, before, after)
            
        def _find_overlapping_segments(self, unit: TimedTextUnit) -> List[DiarizedSegment]:
            """Find all segments that overlap with the given unit."""
            return [
                segment for segment in self.map_segments
                if (segment.mapped_start <= unit.end_ms and
                    segment.mapped_end >= unit.start_ms)
            ]
            
        def _choose_best_overlap(
            self, 
            unit: TimedTextUnit, 
            candidates: List[DiarizedSegment]
        ) -> DiarizedSegment:
            """Choose the segment with the largest overlap with the unit."""
            best_segment = candidates[0]
            best_overlap = self._calculate_overlap(unit, best_segment)
            
            for segment in candidates[1:]:
                overlap = self._calculate_overlap(unit, segment)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_segment = segment
            
            return best_segment
            
        def _calculate_overlap(
            self, 
            unit: TimedTextUnit, 
            segment: DiarizedSegment
        ) -> int:
            """Calculate the amount of overlap between a unit and a segment in milliseconds."""     
            overlap_start = max(unit.start_ms, segment.mapped_start)
            overlap_end = min(unit.end_ms, segment.mapped_end)
            
            return max(0, overlap_end - overlap_start)
        
        def _find_proximal_segments(
            self, 
            unit: TimedTextUnit
        ) -> Tuple[Optional[DiarizedSegment], Optional[DiarizedSegment]]:
            """Find the nearest segments before and after the unit."""
            before = None
            before_end = float('-inf')
            after = None
            after_start = float('inf')
            
            for segment in self.map_segments:
                # Check if segment ends before unit starts
                if segment.mapped_end <= unit.start_ms and segment.mapped_end > before_end:
                    before = segment
                    before_end = segment.mapped_end
                
                # Check if segment starts after unit ends
                if segment.mapped_start >= unit.end_ms and segment.mapped_start < after_start:
                    after = segment
                    after_start = segment.mapped_start
                    
            if not (before or after):
                raise ValueError("Before or after segments not found.")
            
            return before, after
        
        def _choose_closest_proximal(
            self,
            unit: TimedTextUnit,
            before: DiarizedSegment,
            after: DiarizedSegment
        ) -> DiarizedSegment:
            """
            Choose the closest proximal segment based on gap distance.
            Requires both before and after segments (cannot be None)
            """
            before_gap = unit.start_ms - before.mapped_end
            after_gap = after.mapped_start - unit.end_ms

            # Choose segment with smaller gap
            return before if before_gap <= after_gap else after
        
        def _apply_mapping(
            self, 
            unit: TimedTextUnit,
            segment: DiarizedSegment
        ) -> TimedTextUnit:
            """
            Apply the timeline mapping transformation.
            
            Maps unit timestamps from chunk-relative to original timeline.
            Returns the mapped (start_ms, end_ms) tuple.
            """
            # Calculate offset from segment's local start
            offset = unit.start_ms - segment.mapped_start
            
            # Apply offset to original timeline
            new_unit_start = segment.start + offset
            
            # Preserve duration
            duration = unit.duration_ms
            new_unit_end = new_unit_start + duration
            
            unit = unit.model_copy(
                update={"start_ms": new_unit_start, "end_ms": new_unit_end}
            )
            
            if self.config.map_speakers:
                unit.set_speaker(segment.speaker)
                
            return unit

"""
Module for handling timed text objects. For example, can be used  subtitles like VTT and SRT.

This module provides classes and utilities for parsing, manipulating, and generating
timed text objects useful in subtitle and transcript processing. It uses
Pydantic for robust data validation and type safety.
"""

from enum import Enum
from typing import Iterator, List, Optional

from pydantic import BaseModel, Field, field_validator

# TODO convert this module to work not just on text but any object. 
# Create a super class, TimedObject and TimedUnit.
# Would allow segments in DiarizationChunker to be TimedObjects,
# with unified interface.

class Granularity(str, Enum):
    SEGMENT = "segment"
    WORD = "word"
    
class TimedTextUnit(BaseModel):
    """
    Represents a timed unit with timestamps.

    A fundamental building block for subtitle and transcript processing that
    associates text content with start/end times and optional metadata.
    Can represent either a segment (phrase/sentence) or a word.
    """
    text: str = Field(..., description="The text content")
    start_ms: int = Field(..., description="Start time in milliseconds")
    end_ms: int = Field(..., description="End time in milliseconds")
    speaker: Optional[str] = Field(None, description="Speaker identifier if available")
    index: Optional[int] = Field(None, description="Entry index or sequence number")
    granularity: Granularity
    confidence: Optional[float] = Field(None, description="Optional confidence score")

    @property
    def duration_ms(self) -> int:
        """Get duration in milliseconds."""
        return self.end_ms - self.start_ms

    @property
    def start_sec(self) -> float:
        """Get start time in seconds."""
        return self.start_ms / 1000

    @property
    def end_sec(self) -> float:
        """Get end time in seconds."""
        return self.end_ms / 1000

    @property
    def duration_sec(self) -> float:
        """Get duration in seconds."""
        return self.duration_ms / 1000

    def shift_time(self, offset_ms: int) -> "TimedTextUnit":
        """Create a new TimedUnit with timestamps shifted by offset."""
        return self.model_copy(
            update={
                "start_ms": self.start_ms + offset_ms,
                "end_ms": self.end_ms + offset_ms
            }
        )

    def overlaps_with(self, other: "TimedTextUnit") -> bool:
        """Check if this unit overlaps with another."""
        return (self.start_ms <= other.end_ms and 
                other.start_ms <= self.end_ms)

    def set_speaker(self, speaker: str) -> None:
        """Set the speaker label."""
        self.speaker = speaker
        
    def normalize(self) -> None:
        """Normalize the duration of the segment to be nonzero"""
        if self.start_ms == self.end_ms:
            self.end_ms = self.start_ms + 1 # minimum duration 

    @field_validator("start_ms", "end_ms")
    @classmethod
    def _validate_time_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("start_ms and end_ms must be non-negative.")
        return v

    @field_validator("end_ms")
    @classmethod
    def _validate_positive_duration(cls, end_ms: int, info) -> int:
        """Ensure each TimedTextUnit has non-negative duration."""
        start_ms = info.data.get("start_ms")
        if start_ms is not None and end_ms < start_ms:
            raise ValueError(
                f"end_ms ({end_ms}) must be greater than start_ms ({start_ms})."
                )
        return end_ms

    @field_validator("text")
    @classmethod
    def _validate_word_text(cls, v: str, info):
        granularity = info.data.get("granularity", "segment")
        if granularity == "word" and (" " in v.strip()):
            raise ValueError(
                "Text for a word-level TimedUnit cannot contain whitespace.")
        return v


class TimedText(BaseModel):
    """
    Represents a collection of timed text units.

    Notes:
        - Start times must be non-decreasing 
            overlaps allowed, e.g., for multiple speakers).
            Use internal sort as post-init.
        - Mixed granularity (WORD, SEGMENT) is allowed for now.
        - Negative start_ms or end_ms values are not allowed.
        - Durations must be strictly positive (>0 ms).
    """

    segments: List[TimedTextUnit] = Field(
        default=[],
        description="Phrase-level timed units"
    )
    words: List[TimedTextUnit] = Field(
        default=[],
        description="Optional list of word-level timed units"
    )

    @field_validator("segments")
    @classmethod
    def _validate_segments_granularity(cls, v):
        for unit in v:
            if unit.granularity != Granularity.SEGMENT:
                raise ValueError("All segment units must have granularity SEGMENT.")
        return v

    @field_validator("words")
    @classmethod
    def _validate_words_granularity(cls, v):
        for unit in v:
            if unit.granularity != Granularity.WORD:
                raise ValueError("All word units must have granularity WORD.")
        return v

    def model_post_init(self, __context) -> None:
        """
        After initialization, sort segments by start time, 
        and normalize so that durations are positive.
        """
        self.sort_by_start()
        for segment in self.iter_segments():
            segment.normalize()
            

    @property
    def start_ms(self) -> int:
        """Get the start time of the earliest segment."""
        return min(segment.start_ms for segment in self.segments) \
            if self.segments else 0

    @property
    def end_ms(self) -> int:
        """Get the end time of the latest segment."""
        return max(segment.end_ms for segment in self.segments) \
            if self.segments else 0

    @property
    def duration(self) -> int:
        """Get the total duration in milliseconds."""
        return self.end_ms - self.start_ms

    def iter_segments(self) -> Iterator[TimedTextUnit]:
        """Iterate over the segments of the TT"""
        return iter(self.segments)
    
    def iter_words(self) -> Iterator[TimedTextUnit]:
        """Iterate over the words of the TT"""
        return iter(self.words)
    
    def __len__(self) -> int:
        """Return the number of segments."""
        return len(self.segments)

    def append(self, segment: TimedTextUnit):
        """Add a segment to the end."""
        self.segments.append(segment)

    def extend(self, segments: List[TimedTextUnit]):
        """Add multiple segments to the end."""
        self.segments.extend(segments)

    def clear(self):
        """Remove all segments."""
        self.segments.clear()

    def set_speaker(self, index: int, speaker: str) -> None:
        """Set speaker for a specific segment by index."""
        if not (0 <= index < len(self.segments)):
            raise IndexError(f"Index {index} out of range for segments.")
        self.segments[index].set_speaker(speaker)

    def set_all_speakers(self, speaker: str) -> None:
        """Set the same speaker for all segments."""
        for segment in self.segments:
            segment.set_speaker(speaker)
            
    def shift(self, offset_ms: int) -> None:
        """Shift all segments by a given offset in milliseconds."""
        self.segments = [segment.shift_time(offset_ms) for segment in self.segments]

    def sort_by_start(self) -> None:
        """Sort segments and words by start time."""
        self.segments.sort(key=lambda segment: segment.start_ms)
        self.words.sort(key=lambda word: word.start_ms)

    def slice(self, start_ms: int, end_ms: int) -> "TimedText":
        """
        Return a new TimedText object containing only segments within 
        [start_ms, end_ms].
        
        Segments must overlap with the interval to be included.
        """
        sliced_segments = [
            segment for segment in self.segments
            if segment.end_ms > start_ms and segment.start_ms < end_ms
        ]
        return TimedText(segments=sliced_segments)

    def filter_by_min_duration(self, min_duration_ms: int) -> "TimedText":
        """
        Return a new TimedText object containing only segments with a minimum duration.
        """
        filtered_segments = [
            segment for segment in self.segments
            if segment.duration_ms >= min_duration_ms
        ]
        return TimedText(segments=filtered_segments)

    @classmethod
    def merge(cls, items: List["TimedText"]) -> "TimedText":
        """
        Merge a list of TimedText objects into a single TimedText object.
        """
        all_segments: List[TimedTextUnit] = []
        all_words: List[TimedTextUnit] = []

        for item in items:
            all_segments.extend(item.segments)
            all_words.extend(item.words)

        return cls(segments=all_segments, words=all_words)
    
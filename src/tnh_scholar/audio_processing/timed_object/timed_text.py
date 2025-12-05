"""
Module for handling timed text objects. For example, can be used  subtitles like VTT and SRT.

This module provides classes and utilities for parsing, manipulating, and generating
timed text objects useful in subtitle and transcript processing. It uses
Pydantic for robust data validation and type safety.
"""

from enum import Enum
from typing import Iterator, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

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
                "Text for a word-level TimedUnit cannot contain whitespace."
            )
        return v


class TimedText(BaseModel):
    """
    Represents a collection of timed text units of a single granularity.

    Only one of `segments` or `words` is populated, determined by `granularity`.
    All units must match the declared granularity.

    Notes:
        - Start times must be non-decreasing (overlaps allowed for multiple speakers).
        - Negative start_ms or end_ms values are not allowed.
        - Durations must be strictly positive (>0 ms).
        - Mixed granularity is strictly prohibited.
    """

    granularity: Granularity = Field(..., description="Granularity type for all units.")
    segments: List[TimedTextUnit] = Field(default_factory=list, description="Phrase-level timed units")
    words: List[TimedTextUnit] = Field(default_factory=list, description="Word-level timed units")

    def __init__(
        self,
        *,
        granularity: Optional[Granularity] = None,
        segments: Optional[List[TimedTextUnit]] = None,
        words: Optional[List[TimedTextUnit]] = None,
        units: Optional[List[TimedTextUnit]] = None,
        **kwargs
    ):
        """
        Custom initializer for TimedText.
        If `units` is provided, granularity is inferred from the first unit unless explicitly set.
        If only `segments` or `words` is provided, granularity is set accordingly.
        If all are empty, granularity must be provided.
        """
        segments = segments or []
        words = words or []
        if units is not None:
            if units:
                inferred_granularity = units[0].granularity
                granularity = granularity or inferred_granularity
                if granularity == Granularity.SEGMENT:
                    segments = units
                    words = []
                elif granularity == Granularity.WORD:
                    words = units
                    segments = []
                else:
                    raise ValueError("Invalid granularity inferred from units.")
            else:
                if granularity is None:
                    raise ValueError("Must provide granularity for empty TimedText.")
        elif segments:
            granularity = granularity or Granularity.SEGMENT
            words = []
        elif words:
            granularity = granularity or Granularity.WORD
            segments = []
        elif granularity is None:
            raise ValueError("Must provide granularity for empty TimedText.")

        super().__init__(granularity=granularity, segments=segments, words=words, **kwargs)
        
    @model_validator(mode="after")
    def _validate_exclusive_granularity(self):
        """
        Validate that TimedText contains only units matching its granularity.
        Allows empty TimedText objects for prototyping and construction.
        Modular logic for segments and words.
        """
        granularity = self.granularity
        segments = self.segments
        words = self.words

        if granularity == Granularity.SEGMENT:
            if words:
                raise ValueError("TimedText with SEGMENT granularity must not have word units.")
            for unit in segments:
                if unit.granularity != Granularity.SEGMENT:
                    raise ValueError("All segment units must have granularity SEGMENT.")
        elif granularity == Granularity.WORD:
            if segments:
                raise ValueError("TimedText with WORD granularity must not have segment units.")
            for unit in words:
                if unit.granularity != Granularity.WORD:
                    raise ValueError("All word units must have granularity WORD.")
        else:
            raise ValueError("Invalid granularity type.")
        return self

    def model_post_init(self, __context) -> None:
        """
        After initialization, sort units by start time and normalize durations.
        """
        self.sort_by_start()
        for unit in self.units:
            unit.normalize()

    @property
    def units(self) -> List[TimedTextUnit]:
        """Return the list of units matching the granularity."""
        return self.segments if self.granularity == Granularity.SEGMENT else self.words

    def is_segment_granularity(self) -> bool:
        """Return True if granularity is SEGMENT."""
        return self.granularity == Granularity.SEGMENT

    def is_word_granularity(self) -> bool:
        """Return True if granularity is WORD."""
        return self.granularity == Granularity.WORD

    @property
    def start_ms(self) -> int:
        """Get the start time of the earliest unit."""
        return min(unit.start_ms for unit in self.units) if self.units else 0

    @property
    def end_ms(self) -> int:
        """Get the end time of the latest unit."""
        return max(unit.end_ms for unit in self.units) if self.units else 0

    @property
    def duration(self) -> int:
        """Get the total duration in milliseconds."""
        return self.end_ms - self.start_ms

    def __len__(self) -> int:
        """Return the number of units."""
        return len(self.units)

    def append(self, unit: TimedTextUnit):
        """Add a unit to the end."""
        if unit.granularity != self.granularity:
            raise ValueError(f"Cannot append unit with granularity {unit.granularity} "
                             "to TimedText of granularity {self.granularity}.")
        self.units.append(unit)

    def extend(self, units: List[TimedTextUnit]):
        """Add multiple units to the end."""
        for unit in units:
            self.append(unit)

    def clear(self):
        """Remove all units."""
        self.units.clear()

    def set_speaker(self, index: int, speaker: str) -> None:
        """Set speaker for a specific unit by index."""
        if not (0 <= index < len(self.units)):
            raise IndexError(f"Index {index} out of range for units.")
        self.units[index].set_speaker(speaker)

    def set_all_speakers(self, speaker: str) -> None:
        """Set the same speaker for all units."""
        for unit in self.units:
            unit.set_speaker(speaker)

    def shift(self, offset_ms: int) -> None:
        """Shift all units by a given offset in milliseconds."""
        for i, unit in enumerate(self.units):
            self.units[i] = unit.shift_time(offset_ms)

    def sort_by_start(self) -> None:
        """Sort units by start time."""
        self.units.sort(key=lambda unit: unit.start_ms)

            
    @classmethod
    def _new_with_units(
        cls, units: List[TimedTextUnit], granularity: Optional[Granularity] = None
    ) -> "TimedText":
        """
        Helper to create a new TimedText object with the given granularity and units.
        If granularity is not provided, it is inferred from the first unit.
        """
        if units:
            inferred_granularity = units[0].granularity
            granularity = granularity or inferred_granularity
            if granularity == Granularity.SEGMENT:
                return cls(granularity=granularity, segments=units, words=[])
            elif granularity == Granularity.WORD:
                return cls(granularity=granularity, segments=[], words=units)
            else:
                raise ValueError("Invalid granularity inferred from units.")
        else:
            if granularity is None:
                raise ValueError("Must provide granularity for empty TimedText.")
            if granularity in [Granularity.SEGMENT, Granularity.WORD]:
                return cls(granularity=granularity, segments=[], words=[])
            else:
                raise ValueError("Invalid granularity provided.")

    def slice(self, start_ms: int, end_ms: int) -> "TimedText":
        """
        Return a new TimedText object containing only units within [start_ms, end_ms].
        Units must overlap with the interval to be included.
        """
        sliced_units = [
            unit for unit in self.units
            if unit.end_ms > start_ms and unit.start_ms < end_ms
        ]
        return self._new_with_units(sliced_units, self.granularity)

    def filter_by_min_duration(self, min_duration_ms: int) -> "TimedText":
        """
        Return a new TimedText object containing only units with a minimum duration.
        """
        filtered_units = [
            unit for unit in self.units
            if unit.duration_ms >= min_duration_ms
        ]
        return self._new_with_units(filtered_units, self.granularity)

    @classmethod
    def merge(cls, items: List["TimedText"]) -> "TimedText":
        """
        Merge a list of TimedText objects of the same granularity into a single TimedText object.
        """
        if not items:
            raise ValueError("No TimedText objects to merge.")
        granularity = items[0].granularity
        for item in items:
            if item.granularity != granularity:
                raise ValueError("Cannot merge TimedText objects of different granularities.")
        all_units: List[TimedTextUnit] = []
        for item in items:
            all_units.extend(item.units)
            
        # Use the classmethod to generate with units
        return cls._new_with_units(all_units, granularity)
    
    def iter(self) -> Iterator[TimedTextUnit]:
        """
        Unified iterator over the units of the correct granularity.
        """
        return iter(self.units)

    def iter_segments(self) -> Iterator[TimedTextUnit]:
        """
        Iterate over segment-level units.

        Raises:
            ValueError: If granularity is not SEGMENT.
        """
        if not self.is_segment_granularity():
            raise ValueError("Cannot call iter_segments() on TimedText with WORD granularity.")
        return iter(self.segments)

    def iter_words(self) -> Iterator[TimedTextUnit]:
        """
        Iterate over word-level units.

        Raises:
            ValueError: If granularity is not WORD.
        """
        if not self.is_word_granularity():
            raise ValueError("Cannot call iter_words() on TimedText with SEGMENT granularity.")
        return iter(self.words)
    
    def export_text(self, separator: str = "\n", skip_empty: bool = True, show_speaker: bool = True) -> str:
        """
        Export the text content of all units as a single string.

        Args:
            separator: String used to separate units (default: newline).
            skip_empty: If True, skip units with empty or whitespace-only text.
            show_speaker: If True, add speaker info.

        Returns:
            Concatenated text of all units, separated by `separator`.
        """
        def _text_line(unit: TimedTextUnit) -> str:
            if show_speaker and unit.speaker:
                return f"[{unit.speaker}] {unit.text}"
            return unit.text

        texts = [
            _text_line(unit) for unit in self.units
            if not skip_empty or unit.text.strip()
        ]
        return separator.join(texts)

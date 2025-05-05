"""
Module for handling timed text formats such as SRT and VTT subtitles.

This module provides classes and utilities for parsing, manipulating, and generating
timed text formats commonly used in subtitle and transcript processing. It uses
Pydantic for robust data validation and type safety.
"""

from enum import Enum
from typing import Iterator, List, Optional

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("start_ms", "end_ms")
    @classmethod
    def _validate_time_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("start_ms and end_ms must be non-negative.")
        return v

    @field_validator("end_ms")
    @classmethod
    def _validate_positive_duration(cls, end_ms: int, info) -> int:
        """Ensure each TimedTextUnit has strictly positive duration."""
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
        ..., description="Phrase-level timed units"
    )
    words: Optional[List[TimedTextUnit]] = Field(
        default=None,
        description="Optional list of word-level timed units"
    )

    def model_post_init(self, __context) -> None:
        """After initialization, sort segments by start time."""
        self.sort_by_start()

    @field_validator('segments')
    @classmethod
    def validate_segments(cls, segments: List[TimedTextUnit]) -> List[TimedTextUnit]:
        """Validate basic timing sanity (non-negative, positive durations)."""
        if not segments:
            return segments

        for idx, seg in enumerate(segments):
            if seg.start_ms < 0:
                raise ValueError(
                    f"Segment at index {idx} has negative start_ms: {seg.start_ms}"
                    )
            if seg.end_ms < 0:
                raise ValueError(
                    f"Segment at index {idx} has negative end_ms: {seg.end_ms}"
                    )
            if seg.end_ms < seg.start_ms:
                raise ValueError(
                    f"Segment at index {idx} has negative duration: "
                    f"start={seg.start_ms}, end={seg.end_ms}"
                )
        return segments

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
        """Iterate over the segments."""
        return iter(self.segments)

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
        """Sort segments by start time."""
        self.segments.sort(key=lambda segment: segment.start_ms)

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

    def build_segments(
        self,
        *,
        target_duration: Optional[int] = None,
        target_characters: Optional[int] = None,
        avoid_orphans: Optional[bool] = True,
        max_gap_duration: Optional[int] = None,
        ignore_speaker: bool = False,
    ) -> None:
        """
        Build or rebuild `segments` from the contents of `words`.

        Args:
            target_duration: Maximum desired segment duration in milliseconds.
            target_characters: Maximum desired character length of a segment.
            speaker_split: Whether to start a new segment when the speaker changes.

        Note:
            This is a stub.  Concrete algorithms will be implemented later.

        Raises:
            NotImplementedError: Always, until implemented.
        """
        raise NotImplementedError("build_segments is not yet implemented.")
    
    
"""
SegmentBuilder for creating phrase-level segments from word-level TimedText.

This module builds higher-level segments from a TimedText object containing 
word-level units, based on configurable criteria like duration, character count, 
punctuation, pauses, and speaker changes.
"""

COMMON_ABBREVIATIONS = frozenset({
    "adj.", "adm.", "adv.", "al.", "anon.", "apr.", "arc.", "aug.", "ave.",
    "brig.", "bros.", "capt.", "cmdr.", "col.", "comdr.", "con.", "corp.",
    "cpl.", "dr.", "drs.", "ed.", "enc.", "etc.", "ex.", "feb.", "gen.",
    "gov.", "hon.", "hosp.", "hr.", "inc.", "jan.", "jr.", "maj.", "mar.",
    "messrs.", "mlle.", "mm.", "mme.", "mr.", "mrs.", "ms.", "msgr.", "nov.",
    "oct.", "op.", "ord.", "ph.d.", "prof.", "pvt.", "rep.", "reps.", "res.",
    "rev.", "rt.", "sen.", "sens.", "sep.", "sfc.", "sgt.", "sr.", "st.", "supt.",
    "surg.", "u.s.", "v.p.", "vs."
})

class SegmentBuilder:
    def __init__(
        self,
        *,
        max_duration: Optional[int] = None, # milliseconds
        target_characters: Optional[int] = None,
        avoid_orphans: bool = True,
        max_gap_duration: Optional[int] = None, # milliseconds
        ignore_speaker: bool = True,
    ):
        self.max_duration = max_duration
        self.target_characters = target_characters
        self.avoid_orphans = avoid_orphans
        self.max_gap_duration = max_gap_duration
        self.ignore_speaker = ignore_speaker

        self.segments: List[TimedTextUnit] = []
        self.current_words: List[TimedTextUnit] = []
        self.current_characters = 0

    def create_segments(self, timed_text: TimedText) -> TimedText:
        # Validate
        if not timed_text.words:
            raise ValueError(
                "TimedText object must have word-level units to build segments."
                )

        for unit in timed_text.words:
            if unit.granularity != Granularity.WORD:
                raise ValueError(f"Expected WORD units, got {unit.granularity}")

        # Process
        for word in timed_text.words:
            if self._should_start_new_segment(word):
                self._flush_current_words()
            self._add_word(word)

        self._flush_current_words()  # Final flush
        return TimedText(segments=self.segments)
    
    def _add_word(self, word: TimedTextUnit):
        if self.current_words:
            self.current_characters += 1  # space before the new word
        self.current_characters += len(word.text)
        self.current_words.append(word)
        

    def _should_start_new_segment(self, word: TimedTextUnit) -> bool:
        if not self.current_words:
            return False

        # Speaker change
        last_word = self.current_words[-1]
        if not self.ignore_speaker and (word.speaker != last_word.speaker):
            return True

        # Significant pause
        if self.max_gap_duration is not None:
            pause = word.start_ms - last_word.end_ms
            if pause > self.max_gap_duration:
                return True

        # End punctuation
        if last_word.text and self._is_punctuation_word(last_word.text):
            return True

        # Max duration
        if self.max_duration is not None:
            duration = word.end_ms - self.current_words[0].start_ms
            if duration > self.max_duration:
                return True

        # Target character count
        if self.target_characters is not None:
            total_chars = self.current_characters + len(word.text) + 1
            if total_chars > self.target_characters:
                return True

        return False

    def _flush_current_words(self):
        if not self.current_words:
            return

        segment_text = " ".join(word.text for word in self.current_words)
        segment = TimedTextUnit(
            text=segment_text,
            start_ms=self.current_words[0].start_ms,
            end_ms=self.current_words[-1].end_ms,
            granularity=Granularity.SEGMENT,
            speaker=None if self.ignore_speaker else self._find_speaker(),
            confidence=None,
            index=None,
        )
        self.segments.append(segment)
        self.current_words = []
        self.current_characters = 0
        
    def _find_speaker(self) -> Optional[str]:
        """
        Only called when ignore_speakers is False; 
        in this case we always split on speaker. 
        So only one speaker is expected. 
        """
        speakers = {word.speaker for word in self.current_words}
        assert len(speakers) == 1, "Inconsistent speakers in segment"
        return speakers.pop()

    def _is_punctuation_word(self, word_text: str) -> bool:
        """
        Check if a word ending in punctuation should trigger a new segment,
        excluding common abbreviations.
        """
        if not word_text:
            return False
        return word_text[-1] in ".!?" and word_text.lower() not in COMMON_ABBREVIATIONS
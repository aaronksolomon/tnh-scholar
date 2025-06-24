
from typing import List, Optional

from pydantic import BaseModel

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils import TimeMs, convert_ms_to_sec

from ..audio.models import AudioChunk

logger = get_child_logger(__name__)

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
    
    # ------------------------------------------------------------------- #
    # IMPLEMENTATION NOTE
    # Convenience wrappers returning the new Time abstraction so can
    # start migrating call‑sites incrementally without touching the int‑ms
    # fields just yet.
    # ------------------------------------------------------------------- #
    @property
    def start_time(self) -> "TimeMs":
        return TimeMs(self.start)

    @property
    def end_time(self) -> "TimeMs":
        return TimeMs(self.end)

    @property
    def duration_time(self) -> "TimeMs":
        return TimeMs(self.duration)
    
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

    @property
    def total_duration_time(self) -> "TimeMs":
        return TimeMs(self.total_duration)
    
class SpeakerBlock(BaseModel):
    """A block of contiguous or near-contiguous segments spoken by the same speaker.

    Used as a higher-level abstraction over diarization segments to simplify
    chunking strategies (e.g., language-aware sampling, re-segmentation).
    """

    speaker: str
    segments: list["DiarizationSegment"]

    class Config:
        arbitrary_types_allowed = True

    @property
    def start(self) -> TimeMs:
        """Start time of the first segment (in ms)."""
        return TimeMs(self.segments[0].start)

    @property
    def end(self) -> TimeMs:
        """End time of the last segment (in ms)."""
        return TimeMs(self.segments[-1].end)

    @property
    def duration(self) -> TimeMs:
        """Total duration of the speaker block (in ms)."""
        return self.end - self.start

    @property
    def duration_sec(self) -> float:
        return self.duration.to_seconds()

    @property
    def segment_count(self) -> int:
        return len(self.segments)

    def __str__(self) -> str:
        return (
            f"SpeakerBlock(speaker={self.speaker}, "
            "segments={self.segment_count}, "
            "duration={self.duration}ms)"
        )
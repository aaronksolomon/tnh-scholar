from io import BytesIO
from typing import List, Optional

from pydantic import BaseModel

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils import TimeMs, convert_ms_to_sec
from tnh_scholar.utils import TNHAudioSegment as AudioSegment

logger = get_child_logger(__name__)

# TODO use TimeMS everywhere in timing logic throughout codebase 

class DiarizedSegment(BaseModel):
    """
    Represents a diarized audio segment for a single speaker.
    
    Attributes:
        speaker (str): The speaker label for this segment.
        start (TimeMs): Start time in milliseconds.
        end (TimeMs): End time in milliseconds.
        audio_map_start (Optional[int]): Location in the audio output file, if mapped.
        gap_before (Optional[bool]): Indicates if there is a gap greater than the configured threshold
            before this segment. This attribute is set exclusively by `ChunkAccumulator.add_segment()`
            and should be None until that point.
        spacing_time (Optional[int]): The spacing (in ms) between this and the previous segment,
            possibly adjusted if there is a gap before. This attribute is also set exclusively by
            `ChunkAccumulator.add_segment()` and should be None until that point.

    Notes:
        - `gap_before` and `spacing_time` are not set during initial diarization, but are assigned
          only when the segment is accumulated into a chunk for downstream audio handling.
        - These fields should be considered write-once and must not be mutated elsewhere.
    """
    speaker: str
    start: TimeMs  # Start time in milliseconds
    end: TimeMs    # End time in milliseconds
    audio_map_start: Optional[int] # location in the audio output file
    gap_before: Optional[bool] # indicates a gap > gap_threshold before this segment
    spacing_time: Optional[int] # spacing between this and previous segment; adjusted spacing if gap before
    
    @property
    def duration(self) -> "TimeMs":
        """Get segment duration in milliseconds."""
        return TimeMs(self.end - self.start)

    @property
    def duration_sec(self) -> float:
        return self.duration.to_seconds()
    
    # ------------------------------------------------------------------- #
    # IMPLEMENTATION NOTE
    # Convenience wrappers returning the new Time abstraction so can
    # start migrating call‑sites incrementally without touching the int‑ms
    # fields just yet.
    # ------------------------------------------------------------------- #
    @property
    def start_time(self) -> "TimeMs":
        return self.start

    @property
    def end_time(self) -> "TimeMs":
        return self.end
    
    @property
    def mapped_start(self):
        """Downstream registry field set by the audio handler"""
        return self.start if self.audio_map_start is None else self.audio_map_start
    
    @property
    def mapped_end(self):
        if self.audio_map_start is None:
            return self.end 
        else:
            return self.audio_map_start + int(self.duration) 
    
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
            self.end = TimeMs(self.start + 1)  # set minimum nonzero duration

        # Ensure minimum nonzero duration
        if self.start == self.end:
            logger.warning(
                f"Zero segment duration detected: start ({self.start}) == end ({self.end}). "
                "Adjusting end to ensure minimum duration of 1."
            )
            self.end = TimeMs(self.start + 1)  # set minimum nonzero duration

class AugDiarizedSegment(DiarizedSegment):
    """
    DiarizedSegment with additional chunking/processing metadata.

    This class extends `DiarizationSegment` and adds fields that are only set during
    chunk accumulation or downstream processing.

    Attributes:
        gap_before (bool): Indicates if there is a gap greater than the configured threshold
            before this segment. Set only during chunk accumulation.
        spacing_time (TimeMs): The spacing (in ms) between this and the previous segment,
            possibly adjusted if there is a gap before. Set only during chunk accumulation.
        audio (AudioSegment): The audio data for this segment, sliced from the original audio.

    Notes:
        - The `audio` field is a slice of the original audio corresponding to this segment.
        - All time values (start, end, duration) are relative to the original audio.
        - When slicing or probing the `audio` field, use times relative to 0 (i.e., 0 to duration).
        - For language probing or any operation on `audio`, 
          always use 0 as the start and `duration` as the end.
    """

    @property
    def relative_start(self) -> TimeMs:
        """Start time relative to the segment audio (always 0)."""
        return TimeMs(0)

    @property
    def relative_end(self) -> TimeMs:
        """End time relative to the segment audio (duration of segment)."""
        return self.duration

    gap_before_new: bool  # rename when ready to move over to using this class 
    spacing_time_new: TimeMs  # rename when ready to move over to using this class 
    audio: Optional[AudioSegment]

    @classmethod
    def from_segment(
        cls,
        segment: DiarizedSegment,
        gap_before: Optional[bool] = None,
        spacing_time_new: Optional[TimeMs] = None,
        audio: Optional[AudioSegment] = None,
        **kwargs
    ) -> "AugDiarizedSegment":
        """
        Create an AugDiarizedSegment from a DiarizedSegment, with optional new fields.
        Args:
            segment (DiarizedSegment): The base segment to copy fields from.
            gap_before_new (bool, optional): Value for gap_before_new. Defaults to False.
            spacing_time_new (TimeMs, optional): Value for spacing_time_new. Defaults to None.
            audio (AudioSegment, optional): Audio data for this segment. Defaults to None.
            **kwargs: Any additional fields to override.
        Returns:
            AugDiarizedSegment: The new augmented segment.
        """
        return cls(
            speaker=segment.speaker,
            start=segment.start,
            end=segment.end,
            audio_map_start=segment.audio_map_start,
            gap_before=segment.gap_before,
            spacing_time=segment.spacing_time,
            gap_before_new=segment.gap_before if segment.gap_before is not None else False,
            spacing_time_new=spacing_time_new if spacing_time_new is not None else TimeMs(0),
            audio=audio,
            **kwargs
        )

    class Config:
        arbitrary_types_allowed = True


class AudioChunk(BaseModel):
    data: BytesIO
    start_ms: int
    end_ms: int
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    format: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
        

class DiarizationChunk(BaseModel):
    """Represents a chunk of segments to be processed together."""
    start_time: int  # Start time in milliseconds
    end_time: int    # End time in milliseconds
    audio: Optional[AudioChunk] = None
    segments: List[DiarizedSegment]
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
    segments: list["DiarizedSegment"]

    class Config:
        arbitrary_types_allowed = True

    @property
    def start(self) -> "TimeMs":
        return TimeMs(self.segments[0].start)

    @property
    def end(self) -> "TimeMs":
        return TimeMs(self.segments[-1].end)

    @property
    def duration(self) -> "TimeMs":
        return TimeMs(self.end - self.start)

    @property
    def duration_sec(self) -> float:
        return self.duration.to_seconds()

    @property
    def segment_count(self) -> int:
        return len(self.segments)

    def to_dict(self) -> dict:
        """custom serializer for SpeakerBlock with validation."""
        # Validate speaker
        if not isinstance(self.speaker, str) or not self.speaker:
            logger.error("SpeakerBlock.to_dict: 'speaker' must be a non-empty string.")
            raise ValueError("'speaker' must be a non-empty string.")

        # Validate segments
        if not isinstance(self.segments, list) or not self.segments:
            logger.error("SpeakerBlock.to_dict: 'segments' must be a non-empty list.")
            raise ValueError("'segments' must be a non-empty list of DiarizedSegment.")

        for idx, segment in enumerate(self.segments):
            if not isinstance(segment, DiarizedSegment):
                logger.error(f"SpeakerBlock.to_dict: Segment at index {idx} is not a DiarizedSegment.")
                raise TypeError(f"Segment at index {idx} is not a DiarizedSegment.")

        # Validate start/end/duration
        try:
            start = int(self.start)
            end = int(self.end)
            duration = int(self.duration)
            duration_sec = float(self.duration_sec)
            segment_count = int(self.segment_count)
        except Exception as e:
            logger.error(f"SpeakerBlock.to_dict: Error computing time fields: {e}")
            raise

        return {
            "speaker": self.speaker,
            "segments": [segment.model_dump() for segment in self.segments],
            "start": start,
            "end": end,
            "duration": duration,
            "duration_sec": duration_sec,
            "segment_count": segment_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SpeakerBlock":
        """
        Create a SpeakerBlock from a dictionary (output of to_dict).
        Args:
            data (dict): Dictionary with keys matching SpeakerBlock fields.
        Returns:
            SpeakerBlock: Deserialized SpeakerBlock instance.
        Raises:
            ValueError, TypeError: If validation fails.
        """
        if not isinstance(data, dict):
            logger.error("SpeakerBlock.from_dict: Input data must be a dictionary.")
            raise TypeError("Input data must be a dictionary.")

        if "speaker" not in data or not isinstance(data["speaker"], str) or not data["speaker"]:
            logger.error("SpeakerBlock.from_dict: 'speaker' must be a non-empty string.")
            raise ValueError("'speaker' must be a non-empty string.")

        if "segments" not in data or not isinstance(data["segments"], list) or not data["segments"]:
            logger.error("SpeakerBlock.from_dict: 'segments' must be a non-empty list.")
            raise ValueError("'segments' must be a non-empty list.")

        segments = []
        for idx, seg in enumerate(data["segments"]):
            if not isinstance(seg, dict):
                logger.error(f"SpeakerBlock.from_dict: Segment at index {idx} is not a dict.")
                raise TypeError(f"Segment at index {idx} is not a dict.")
            try:
                segment = DiarizedSegment(**seg)
            except Exception as e:
                logger.error(
                    f"SpeakerBlock.from_dict: Failed to construct DiarizedSegment at index {idx}: {e}"
                    )
                raise
            segments.append(segment)

        return cls(speaker=data["speaker"], segments=segments)
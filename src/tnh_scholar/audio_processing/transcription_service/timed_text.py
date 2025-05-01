"""
Module for handling timed text formats such as SRT and VTT subtitles.

This module provides classes and utilities for parsing, manipulating, and generating
timed text formats commonly used in subtitle and transcript processing. It uses
Pydantic for robust data validation and type safety.
"""

import re
from enum import Enum
from typing import Iterator, List, Optional, Tuple, Union

from pydantic import BaseModel, Field


class TimedTextSegment(BaseModel):
    """
    Represents text segment with timestamps.
    
    A fundamental building block for subtitle and transcript processing that
    associates text content with start/end times and optional metadata.
    """
    text: str = Field(..., description="The text content")
    start_ms: int = Field(..., description="Start time in milliseconds")
    end_ms: int = Field(..., description="End time in milliseconds")
    speaker: Optional[str] = Field(None, description="Speaker identifier if available")
    index: Optional[int] = Field(None, description="Entry index or sequence number")
    
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
    
    def shift_time(self, offset_ms: int) -> "TimedTextSegment":
        """Create a new TimedText with timestamps shifted by offset."""
        return self.model_copy(
            update={
                "start_ms": self.start_ms + offset_ms,
                "end_ms": self.end_ms + offset_ms
            }
        )
    
    def overlaps_with(self, other: "TimedTextSegment") -> bool:
        """Check if this segment overlaps with another."""
        return (self.start_ms <= other.end_ms and 
                other.start_ms <= self.end_ms)


class TimedText(BaseModel):
    """Represents a collection of timed text segments."""

    segments: List[TimedTextSegment] = Field(
        ..., description="List of TimedTextSegment objects"
        )

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

    def __iter__(self) -> Iterator[TimedTextSegment]:
        """Iterate over the segments."""
        return iter(self.segments)

    def __len__(self) -> int:
        """Return the number of segments."""
        return len(self.segments)

    def append(self, segment: TimedTextSegment):
        """Add a segment to the end."""
        self.segments.append(segment)

    def extend(self, segments: List[TimedTextSegment]):
        """Add multiple segments to the end."""
        self.segments.extend(segments)

    def clear(self):
        """Remove all segments."""
        self.segments.clear()

    
class SubtitleFormat(str, Enum):
    """Supported subtitle formats."""
    SRT = "srt"
    VTT = "vtt"
    TEXT = "text"


class SRTConfig:
    """Configuration options for SRT processing."""
    
    def __init__(
        self,
        include_speaker=False,
        speaker_format="[{speaker}] {text}",
        reindex_entries=True,
        timestamp_format="{:02d}:{:02d}:{:02d},{:03d}",
        max_chars_per_line=42
    ):
        """
        Initialize with default settings.
        
        Args:
            include_speaker: Whether to include speaker labels in output
            speaker_format: Format string for speaker attribution
            reindex_entries: Whether to reindex entries sequentially
            timestamp_format: Format string for timestamp formatting
            max_chars_per_line: Maximum characters per line before splitting
        """
        self.include_speaker = include_speaker
        self.speaker_format = speaker_format
        self.reindex_entries = reindex_entries
        self.timestamp_format = timestamp_format
        self.max_chars_per_line = max_chars_per_line


class VTTConfig:
    """Configuration options for WebVTT processing."""
    
    def __init__(
        self,
        include_speaker=False,
        speaker_format="<v {speaker}>{text}",
        reindex_entries=False,
        timestamp_format="{:02d}:{:02d}:{:02d}.{:03d}",
        max_chars_per_line=42
    ):
        """
        Initialize with default settings.
        
        Args:
            include_speaker: Whether to include speaker labels in output
            speaker_format: Format string for speaker attribution
            reindex_entries: Whether to reindex entries sequentially
            timestamp_format: Format string for timestamp formatting
            max_chars_per_line: Maximum characters per line before splitting
        """
        self.include_speaker = include_speaker
        self.speaker_format = speaker_format
        self.reindex_entries = reindex_entries
        self.timestamp_format = timestamp_format
        self.max_chars_per_line = max_chars_per_line


class SRTProcessor:
    """
    Handles parsing and generating SRT format.
    
    Provides functionality to convert between SRT text format and
    TimedText objects, with various formatting options.
    """
    
    def __init__(self, config: Optional[SRTConfig] = None):
        """
        Initialize with optional configuration overrides.
        
        Args:
            config: Configuration options for SRT processing
        """
        self.config = config or SRTConfig()
        
    def merge_srts(self, srt_list: List[str]) -> str:
        """Merge multiple SRT files into a single SRT string."""
        timed_text_list = [self.parse(srt) for srt in srt_list]
        combined_timed_text = self.combine(timed_text_list)
        return self.generate(combined_timed_text)
    
    def generate(self, timed_text: TimedText) -> str:
        """Generate SRT content from a TimedText object."""

        srt_parts = []
        srt_parts.extend(
            self._generate_entry(
                entry, index=i if self.config.reindex_entries else entry.index
            )
            for i, entry in enumerate(timed_text, start=1)
        )
        return "\n".join(srt_parts)
        
    def parse(self, srt_content: str) ->TimedText:
            """
            Parse SRT content into a list of TimedText objects using a stateful parser.
            """
            parser = self._SRTParser(srt_content)
            return parser.parse()
        
    def shift_timestamps(self, timed_text: TimedText, offset_ms: int) -> TimedText:
            """
            Shift all timestamps by the given offset.
            
            Args:
                timed_texts: List of TimedText objects
                offset_ms: Offset in milliseconds to apply
                
            Returns:
                New list of TimedText objects with adjusted timestamps
            """
            new_segments = [segment.shift_time(offset_ms) for segment in timed_text]
            return TimedText(segments=new_segments)
    
    def combine(self, timed_texts: List[TimedText]) -> TimedText:
        """
        Combine multiple lists of TimedText into one, with proper indexing.
        
        Args:
            timed_text_lists: List of TimedText lists to combine
            
        Returns:
            Combined list of TimedText objects
        """
        combined_segments = []
        for timed_text in timed_texts:
            combined_segments.extend(timed_text.segments)

        # Sort by start time
        combined_segments.sort(key=lambda x: x.start_ms)

        return TimedText(segments=combined_segments)

    class _SRTParser:
        """Inner class to manage the state of the SRT parsing."""

        def __init__(self, srt_content: str):
            self.lines = srt_content.splitlines()
            self.current_index = 0
            self.timed_segments = []

        def parse(self) -> TimedText:
            while self.current_index < len(self.lines):
                if self.lines[self.current_index].strip():
                    try:
                        timed_segment = self._parse_entry()
                        self.timed_segments.append(timed_segment)
                    except (IndexError, ValueError) as e:
                        raise ValueError(
                            f"Invalid SRT format at line {self.current_index}: {e}"
                        ) from e
                self.current_index += 1  # Always increment to avoid infinite loops

            return TimedText(segments=self.timed_segments)
        
        def _parse_entry(self) -> TimedTextSegment:
            index = self._parse_index()
            start_time, end_time = self._parse_timestamps()
            text = self._parse_text()
            start_ms = self._timestamp_to_ms(start_time)
            end_ms = self._timestamp_to_ms(end_time)
            speaker, text = self._extract_speaker(text)

            return TimedTextSegment(
                text=text,
                start_ms=start_ms,
                end_ms=end_ms,
                speaker=speaker,
                index=index,
            )

        def _parse_index(self) -> int:
            try:
                index = int(self.lines[self.current_index])
                self.current_index += 1
                return index
            except ValueError as ve:
                raise ValueError(
                    f"Invalid SRT entry index at line {self.current_index + 1}:"
                    f" '{self.lines[self.current_index]}' is not an integer."
                ) from ve

        def _parse_timestamps(self) -> Tuple[str, str]:
            timestamps_line = self.lines[self.current_index]
            start_time, end_time = timestamps_line.split("-->")
            self.current_index += 1
            return start_time.strip(), end_time.strip()

        def _parse_text(self) -> str:
            text_lines = []
            while self.current_index < len(self.lines) \
                and self.lines[self.current_index].strip():
                text_lines.append(self.lines[self.current_index])
                self.current_index += 1
            return "\n".join(text_lines).strip()


        def _extract_speaker(self, text: str) -> Tuple[Optional[str], str]:
            """Extract speaker information from text if present, 
            using the format "[speaker] text"."""
            if match := re.match(r"^\[([^\]]+)\]\s*(.*)", text):
                speaker = match[1].strip()
                text = match[2].strip()
                return speaker, text
            return None, text
        
        def _timestamp_to_ms(self, timestamp: str) -> int:
            """
            Convert SRT timestamp (HH:MM:SS,mmm) to milliseconds.
            
            Args:
                timestamp: SRT format timestamp
                
            Returns:
                Timestamp in milliseconds
            """
            pattern = r"(\d{2}):(\d{2}):(\d{2}),(\d{3})"
            match = re.match(pattern, timestamp)
            if not match:
                raise ValueError(f"Invalid timestamp format: {timestamp}")

            hours, minutes, seconds, milliseconds = map(int, match.groups())
            return hours * 3600000 + minutes * 60000 + seconds * 1000 + milliseconds

    def _generate_entry(
        self, entry: TimedTextSegment, index: Optional[int] = None
        ) -> str:
        """Generate a single SRT entry."""
        start_timestamp = self._ms_to_timestamp(entry.start_ms)
        end_timestamp = self._ms_to_timestamp(entry.end_ms)

        text = entry.text
        if self.config.include_speaker and entry.speaker:
            text = self.config.speaker_format.format(speaker=entry.speaker, text=text)

        srt_entry = [
            str(index or 0),
            f"{start_timestamp} --> {end_timestamp}",
            text,
            "",  # Empty line between entries
        ]
        return "\n".join(srt_entry)
    
    def _ms_to_timestamp(self, milliseconds: int) -> str:
        """
        Convert milliseconds to SRT timestamp format (HH:MM:SS,mmm).
        
        Args:
            milliseconds: Time in milliseconds
            
        Returns:
            Formatted timestamp string
        """
        total_seconds, ms = divmod(milliseconds, 1000)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return self.config.timestamp_format.format(hours, minutes, seconds, ms)
    
class VTTProcessor:
    """Handles parsing and generating WebVTT format."""
    
    def __init__(self, config: Optional[VTTConfig] = None):
        """
        Initialize with optional configuration.
        
        Args:
            config: Configuration options for VTT processing
        """
        self.config = config or VTTConfig()
    
    def parse(self, vtt_content: str) -> List[TimedTextSegment]:
        """
        Parse VTT content into a list of TimedText objects.
        
        Args:
            vtt_content: String containing VTT formatted content
            
        Returns:
            List of TimedText objects
        """
        # Implementation will go here
        raise NotImplementedError("Not implemented.")
    
    def generate(self, timed_texts: List[TimedTextSegment]) -> str:
        """
        Generate VTT content from a list of TimedText objects.
        
        Args:
            timed_texts: List of TimedText objects
            
        Returns:
            String containing VTT formatted content
        """
        # Implementation will go here
        raise NotImplementedError("Not implemented.")


def create_processor(
    format_type: Union[str, SubtitleFormat], 
    **options
) -> Union[SRTProcessor, VTTProcessor]:
    """
    Create the appropriate processor for the given format.
    
    Args:
        format_type: Format type ("srt" or "vtt")
        **options: Configuration options for the processor
    
    Returns:
        Appropriate processor instance
    
    Raises:
        ValueError: If format is not supported
    """
    format_str = format_type.value \
        if isinstance(format_type, SubtitleFormat) \
            else format_type
    format_str = format_str.lower()
    
    if format_str == SubtitleFormat.SRT:
        config = SRTConfig(**options)
        return SRTProcessor(config)
    elif format_str == SubtitleFormat.VTT:
        config = VTTConfig(**options)
        return VTTProcessor(config)
    else:
        raise ValueError(f"Unsupported format: {format_type}")
    

    
    

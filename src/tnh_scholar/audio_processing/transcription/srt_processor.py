import re
from enum import Enum
from typing import List, Optional, Tuple

import pysrt

from tnh_scholar.audio_processing.transcription import (
    Granularity,
    TimedText,
    TimedTextUnit,
)


class SubtitleFormat(str, Enum):
    """Supported subtitle formats."""
    SRT = "srt"
    VTT = "vtt"
    TEXT = "text"


class SRTConfig:
    """Configuration options for SRT processing."""
    
    def __init__(
        self,
        include_speaker: bool = False,
        speaker_format: str = "[{speaker}] {text}",
        reindex_entries: bool = True,
        timestamp_format: str = "{:02d}:{:02d}:{:02d},{:03d}",
        max_chars_per_line: int = 42,
        use_pysrt: bool = False,
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
        self.use_pysrt = use_pysrt


def _extract_speaker_from_text(text: str) -> Tuple[Optional[str], str]:
            """Utility to extract speaker information from text if present, 
            using the format "[speaker] text"."""
            if match := re.match(r"^\[([^\]]+)\]\s*(.*)", text):
                speaker = match[1].strip()
                text = match[2].strip()
                return speaker, text
            return None, text
        
class SRTProcessor:
    """
    Handles parsing and generating SRT format.
    
    Provides functionality to convert between SRT text format and
    TimedText objects, with various formatting options.
    Supports both native parsing/generation and pysrt backend.
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
        return self.generate(combined_timed_text, self.config.include_speaker)
    
    def generate(
        self, 
        timed_text: TimedText, 
        include_speaker: Optional[bool] = None
    ) -> str:
        """
        Generate SRT content from a TimedText object.
        Uses internal generator or pysrt depending on configuration.
        """
        if not include_speaker:
            include_speaker = self.config.include_speaker
        if self.config.use_pysrt:
            return self._generate_with_pysrt(timed_text)
        
        srt_parts = []
        srt_parts.extend(
            self._generate_entry(
                entry, 
                index=i if self.config.reindex_entries else entry.index,
                include_speaker=include_speaker
            )
            for i, entry in enumerate(timed_text.iter_segments(), start=1)
        )
        return "\n".join(srt_parts)
        
    def parse(self, srt_content: str) -> TimedText:
        """
        Parse SRT content into a new TimedText object.
        Uses internal parser or pysrt depending on configuration.
        """
        if self.config.use_pysrt:
            return self._parse_with_pysrt(srt_content)
        parser = self._SRTParser(srt_content)
        return parser.parse()
        
    def shift_timestamps(self, timed_text: TimedText, offset_ms: int) -> TimedText:
            """
            Shift all timestamps by the given offset.
            
            Args:
                timed_text: TimedText to shift
                offset_ms: Offset in milliseconds to apply
                
            Returns:
                New TimedText object with adjusted timestamps
            """
            new_segments = [
                segment.shift_time(offset_ms) 
                for segment in timed_text.iter_segments()
                ]
            return TimedText(segments=new_segments)
    
    def combine(self, timed_texts: List[TimedText]) -> TimedText:
        """
        Combine multiple lists of TimedText into one, with proper indexing.
        
        Args:
            timed_texts: List of TimedText to combine
            
        Returns:
            Combined TimedText object
        """
        combined_segments = []
        for timed_text in timed_texts:
            combined_segments.extend(timed_text.segments)

        # Sort by start time
        combined_segments.sort(key=lambda x: x.start_ms)

        return TimedText(segments=combined_segments)
    
    def assign_single_speaker(self, srt_content: str, speaker: str) -> str:
        """
        Assign the same speaker to all segments in the SRT content.
        """
        timed_text = self.parse(srt_content)
        timed_text.set_all_speakers(speaker)
        return self.generate(timed_text, include_speaker=True)

    def assign_speaker_by_mapping(
        self, srt_content: str, speaker_labels: dict[str, list[int]]
        ) -> str:
        """
        Assign speakers to segments based on a mapping of speaker to segment indices.
        (Not implemented yet.)
        """
        raise NotImplementedError("assign_speaker_by_mapping is not implemented yet.")

    def add_speaker_labels(
        self, 
        srt_content: str, 
        *, 
        speaker: Optional[str] = None, 
        speaker_labels: Optional[dict[str, list[int]]] = None
        ) -> str:
        """
        Unified entry point for adding speaker labels. 
        (Not implemented yet.)
        """
        raise NotImplementedError("add_speaker_labels is not implemented yet.")

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
        
        def _parse_entry(self) -> TimedTextUnit:
            index = self._parse_index()
            start_time, end_time = self._parse_timestamps()
            text = self._parse_text()
            start_ms = self._timestamp_to_ms(start_time)
            end_ms = self._timestamp_to_ms(end_time)
            speaker, text = _extract_speaker_from_text(text)

            return TimedTextUnit(
                text=text,
                start_ms=start_ms,
                end_ms=end_ms,
                speaker=speaker,
                index=index,
                granularity=Granularity.SEGMENT,
                confidence=None,
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
        self, 
        entry: TimedTextUnit, 
        index: Optional[int] = None,
        include_speaker: bool = False,
        ) -> str:
        """Generate a single SRT entry from a TimedUnit."""
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

    def _parse_with_pysrt(self, srt_content: str) -> TimedText:
        """Internal: Parse using pysrt, extracting speaker information."""
        subs = pysrt.from_string(srt_content)
        segments = []
        for item in subs:
            speaker, text = _extract_speaker_from_text(item.text)
            segments.append(
                TimedTextUnit(
                    text=text,
                    speaker=speaker,
                    start_ms=item.start.ordinal,
                    end_ms=item.end.ordinal,
                    index=item.index,
                    granularity=Granularity.SEGMENT,
                    confidence=None,
                )
            )
        return TimedText(segments=segments)

    def _generate_with_pysrt(self, timed_text: TimedText) -> str:
        """Internal: Generate SRT using pysrt."""
        subs = pysrt.SubRipFile()
        for i, segment in enumerate(timed_text.iter_segments(), start=1):
            start = pysrt.SubRipTime(milliseconds=segment.start_ms)
            end = pysrt.SubRipTime(milliseconds=segment.end_ms)
            text = segment.text
            if self.config.include_speaker and segment.speaker:
                text = self.config.speaker_format.format(
                    speaker=segment.speaker, text=text)
            subs.append(pysrt.SubRipItem(index=i, start=start, end=end, text=text))
        return subs.to_string()

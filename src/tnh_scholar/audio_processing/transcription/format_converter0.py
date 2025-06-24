from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field, computed_field


def convert_sec_to_ms(data: Dict[str, Any]) -> None:
    """
    Convert 'start' and 'end' fields in seconds to 'start_ms' 
    and 'end_ms' in milliseconds.
    Only does conversion if the millisecond keys are absent.
    """
    if "start" in data and "start_ms" not in data:
        data["start_ms"] = int(data["start"] * 1000)
    if "end" in data and "end_ms" not in data:
        data["end_ms"] = int(data["end"] * 1000)
        convert_sec_to_ms(data)
        
class SegmenterConfig(BaseModel):
    """Configuration for word-based segmentation."""
    max_words_per_segment: int = 20
    max_segment_duration_sec: float = 7.0
    min_pause_secs: float = 2.0
    sentence_end_chars: Set[str] = {'.', '!', '?'}

class FormatConverterConfig(BaseModel):
    """Configuration for TranscriptionFormatConverter."""
    default_audio_duration: float = 60.0
    segmenter_config: SegmenterConfig = Field(default_factory=SegmenterConfig)
    include_segment_index: bool = True

class TranscriptionWord(BaseModel):
    """Represents a single word with timing information."""
    text: str = ""
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    confidence: float = 0.0
    
    model_config = {
    "populate_by_name": True,
    "extra": "ignore",
    "arbitrary_types_allowed": True  # Allow float
    }
    
    def has_timing(self) -> bool:
        """Check if word has valid timing information."""
        return self.start_ms is not None and self.end_ms is not None
    
    @computed_field(return_type=float)
    def start_sec(self) -> float:
        """
        Get start time in seconds.
        
        Raises:
            ValueError: If start_ms is None
        """
        if self.start_ms is None:
            raise ValueError("Word has no start timing information")
        return self.start_ms / 1000
    
    @computed_field(return_type=float)
    def end_sec(self) -> float:
        """
        Get end time in seconds.
        
        Raises:
            ValueError: If end_ms is None
        """
        if self.end_ms is None:
            raise ValueError("Word has no end timing information")
        return self.end_ms / 1000
    
    def ends_punctuation(self, end_chars: Set[str]) -> bool:
        """Check if word ends with sentence-ending punctuation."""
        stripped = self.text.rstrip()
        return bool(stripped and stripped[-1] in end_chars)
    
    @classmethod
    def from_dict(cls, word_dict: Dict[str, Any]) -> "TranscriptionWord":
        """
        Create from dict with special handling for time formats.
        Converts seconds to milliseconds if needed.
        """
        # Copy to avoid modifying original
        data = word_dict.copy()
        
        # Handle different field names for the word text
        if "word" in data and "text" not in data:
            data["text"] = data.pop("word")
            
        # Convert seconds to milliseconds if needed
        data = convert_sec_to_ms(data)
            
        return cls.model_validate(data)
    

class TranscriptionSegment(BaseModel):
    """Represents a segment of transcribed speech."""
    text: str = ""
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    speaker: Optional[str] = None
    words: List[TranscriptionWord] = Field(default_factory=list)
    
    model_config = {
        "populate_by_name": True,
        "extra": "ignore",
        "arbitrary_types_allowed": True  # Allow float
    }
    
    def has_timing(self) -> bool:
        """Check if segment has valid timing information."""
        return self.start_ms is not None and self.end_ms is not None
    
    @computed_field(return_type=float)
    def start_sec(self) -> float:
        """
        Get start time in seconds.
        
        Raises:
            ValueError: If start_ms is None
        """
        if self.start_ms is None:
            raise ValueError("Segment has no start timing information")
        return self.start_ms / 1000
    
    @computed_field(return_type=float)
    def end_sec(self) -> float:
        """
        Get end time in seconds.
        
        Raises:
            ValueError: If end_ms is None
        """
        if self.end_ms is None:
            raise ValueError("Segment has no end timing information")
        return self.end_ms / 1000
    
    @computed_field(return_type=float)
    def duration_sec(self) -> float:
        """
        Get duration in seconds.
        
        Raises:
            ValueError: If timing information is incomplete
        """
        if not self.has_timing():
            raise ValueError(
                "Cannot calculate duration without complete timing information"
                )
        return (self.end_ms - self.start_ms) / 1000 # type: ignore
        
    def is_empty(self) -> bool:
        """Check if segment has any text content."""
        return not bool(self.text)
    
    def add_word(self, word: TranscriptionWord) -> None:
        """Add a word to the segment."""
        # Handle timing updates
        if self.start_ms is None:
            self.start_ms = word.start_ms
        
        if word.end_ms is not None:
            self.end_ms = word.end_ms
            
        # Update text with proper spacing
        if self.text:
            self.text += f" {word.text}"
        else:
            self.text = word.text
            
        # Add to words list
        self.words.append(word)
        
    @classmethod
    def from_dict(cls, segment_dict: Dict[str, Any]) -> "TranscriptionSegment":
        """
        Create from dict with special handling for time formats.
        Converts seconds to milliseconds if needed.
        """
        # Copy to avoid modifying original
        data = segment_dict.copy()
        
        data = convert_sec_to_ms(data)
            
        return cls.model_validate(data)


class WordSegmenter:
    """
    Creates logical segments from word-level transcript data.
    
    Segments are created based on several criteria:
    1. Natural language boundaries (punctuation)
    2. Maximum word count
    3. Maximum segment duration
    4. Significant pauses in speech
    """
    
    # Constants
    MS_PER_SECOND = 1000
    
    def __init__(self, config: Optional[SegmenterConfig] = None):
        self.config = config or SegmenterConfig()

    def create_segments(
        self,
        words: List[TranscriptionWord]
        ) -> List[TranscriptionSegment]:
        
        segments: List[TranscriptionSegment] = []
        current_segment = TranscriptionSegment()
        word_count = 0
        prev_word_end: Optional[float] = None

        for word in words:
            word_start = word.start_sec or 0.0
            word_end = word.end_sec or word_start

            if self._has_pause(prev_word_end, word_start) and not current_segment.is_empty(): # type: ignore  # noqa: E501
                
                segments.append(current_segment)
                current_segment = TranscriptionSegment()
                word_count = 0

            current_segment.add_word(word)
            word_count += 1

            if self._should_complete_segment(current_segment, word, word_count) and \
                not current_segment.is_empty():
                segments.append(current_segment)
                current_segment = TranscriptionSegment()
                word_count = 0

            prev_word_end = word_end  # type: ignore

        if not current_segment.is_empty():
            segments.append(current_segment)

        return segments

    def _has_pause(
        self, prev_end: Optional[float], current_start: float) -> bool:
        if prev_end is None:
            return False
        return (current_start - prev_end) >= self.config.min_pause_secs

    def _should_complete_segment(
        self, 
        segment: TranscriptionSegment, 
        word: TranscriptionWord, 
        word_count: int
    ) -> bool:
        if word.ends_punctuation(self.config.sentence_end_chars):
            return True
        if word_count >= self.config.max_words_per_segment:
            return True
        return segment.duration_sec >= self.config.max_segment_duration_sec  # type: ignore


class TranscriptionFormatConverter:
    """
    Converts transcription results into various output formats.
    
    This class provides a standardized way to convert transcription results
    into different output formats (e.g., SRT, VTT, text) when the native
    API capabilities of the transcription service aren't available.
    """
    
    def __init__(self, config: Optional[FormatConverterConfig] = None):
        """
        Initialize format converter with optional configuration.
        
        Args:
            config: Configuration options for format conversion
        """
        self.config = config or FormatConverterConfig()
        self.word_segmenter = WordSegmenter(self.config.segmenter_config)
    
    @staticmethod
    def _ms_to_seconds(milliseconds: int) -> float:
        """Convert milliseconds to seconds."""
        return milliseconds / 1000
    
    @staticmethod
    def _seconds_to_ms(seconds: float) -> int:
        """Convert seconds to milliseconds."""
        return int(seconds * 1000)
    
    def _get_segments(self, result: Dict[str, Any]) -> List[TranscriptionSegment]:
        """
        Extract segments from result using best available strategy.
        
        Tries different segmentation methods in order of preference:
        1. Speaker utterances (with speaker information)
        2. Word-level segmentation (grouped into sentences)
        3. Single segment with entire text
        
        Args:
            result: Standardized transcription result
            
        Returns:
            List of segment dictionaries with at least "text", "start", and "end" keys
        """
        # Try utterances (has speaker info)
        if utterances := result.get("utterances", []):
            return [TranscriptionSegment.from_dict(u) for u in utterances]

        # Try word-level segmentation
        if words := result.get("words", []):
            return self.word_segmenter.create_segments(words)

        # Fallback to single segment
        if text := result.get("text", ""):
            # Get duration in milliseconds, using default if not available
            duration_ms = result.get("audio_duration_ms", 
                                    int(self.config.default_audio_duration * 1000))
            
            return [TranscriptionSegment(
                text=text,
                start_ms=0,
                end_ms=duration_ms
            )]
            
        return []
    
    def _normalize_segment_timestamps(
        self, 
        segments: List[TranscriptionSegment]
        ) -> List[TranscriptionSegment]:
        """Normalize segment timestamps to ensure consistency."""
        normalized = []

        for segment in segments:
            start_ms = segment.start_ms if segment.start_ms is not None else 0
            end_ms = segment.end_ms if segment.end_ms is not None else start_ms + 1000

            normalized_segment = segment.model_copy(update={
                "start_ms": start_ms,
                "end_ms": end_ms
            })

            normalized.append(normalized_segment)

        return normalized
    
    def _format_srt_timestamp(self, seconds: float) -> str:
        """Format timestamp for SRT format (HH:MM:SS,mmm)."""
        return self._format_timestamp(seconds, ',')
    
    def _format_vtt_timestamp(self, seconds: float) -> str:
        """Format timestamp for VTT format (HH:MM:SS.mmm)."""
        return self._format_timestamp(seconds, '.')
    
    def _format_timestamp(self, seconds: float, separator: str) -> str:
        """
        Format timestamp in HH:MM:SS[separator]mmm format.
        
        Args:
            seconds: Time in seconds
            separator: Separator character between seconds and milliseconds
            
        Returns:
            Formatted timestamp string
        """            
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds_int = divmod(remainder, 60)
        
        # Get milliseconds with configurable precision
        milliseconds = int((seconds - int(seconds)) * 1000)
        
        return \
            f"{hours:02d}:{minutes:02d}:{seconds_int:02d}{separator}{milliseconds:03d}"
            
    def convert(
        self,
        result: Dict[str, Any],
        format_type: str = "srt",
        format_options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Convert transcription result to specified format.
        
        Args:
            result: Standardized transcription result dictionary
            format_type: Output format type ("srt", "vtt", "text")
            format_options: Format-specific options
                - max_length: Maximum characters per caption (default: 42)
                - include_speaker: Whether to include speaker labels (default: True)
        
        Returns:
            String representation in requested format
            
        Raises:
            ValueError: If format_type is not supported
        """
        format_options = format_options or {}
        format_type = format_type.lower()
        
        # Get segments from result
        segments = self._get_segments(result)
        
        # Normalize timestamps
        segments = self._normalize_segment_timestamps(segments)
        
        # Check format type
        if format_type == "text":
            return self._convert_to_text(segments)
        elif format_type == "srt":
            return self._convert_to_srt(segments, format_options)
        elif format_type == "vtt":
            return self._convert_to_vtt(segments, format_options)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    def _convert_to_text(self, segments: List[TranscriptionSegment]) -> str:
        """Convert segments to plain text."""
        return "\n".join(segment.text for segment in segments if segment.text)

    def _convert_to_srt(
        self,
        segments: List[TranscriptionSegment],
        options: Dict[str, Any]
    ) -> str:
        """
        Convert segments to SRT format.
        
        SRT format:
        1
        00:00:00,000 --> 00:00:05,000
        This is the first subtitle.
        
        2
        00:00:05,100 --> 00:00:10,000
        This is the second subtitle.
        """
        include_speaker = options.get("include_speaker", True)
        lines = []

        for i, segment in enumerate(segments, 1):
            if segment.is_empty():
                continue

            # Format index
            if self.config.include_segment_index:
                lines.append(f"{i}")

            # Format time range - Use default values if timing is missing
            if segment.has_timing():
                start_time = self._format_srt_timestamp(segment.start_sec)
                end_time = self._format_srt_timestamp(segment.end_sec)
            else:
                # Default timing if not available
                start_time = self._format_srt_timestamp(0.0)
                end_time = self._format_srt_timestamp(1.0)  # Default 1-second duration
                
            lines.append(f"{start_time} --> {end_time}")
            

            # Format text with optional speaker
            text = segment.text
            if include_speaker and segment.speaker:
                text = f"[{segment.speaker}] {text}"

            lines.extend((text, ""))
        return "\n".join(lines).strip()

    def _convert_to_vtt(
        self,
        segments: List[TranscriptionSegment],
        options: Dict[str, Any]
    ) -> str:
        """
        Convert segments to VTT format.
        
        VTT format:
        WEBVTT
        
        00:00:00.000 --> 00:00:05.000
        This is the first subtitle.
        
        00:00:05.100 --> 00:00:10.000
        This is the second subtitle.
        """
        include_speaker = options.get("include_speaker", True)
        lines = ["WEBVTT", ""]  # Header and blank line

        for segment in segments:
            if segment.is_empty():
                continue

            # Format time range
            start_time = self._format_vtt_timestamp(segment.start_sec or 0.0)
            end_time = self._format_vtt_timestamp(segment.end_sec or 0.0)
            lines.append(f"{start_time} --> {end_time}")

            # Format text with optional speaker
            text = segment.text
            if include_speaker and segment.speaker:
                text = f"[{segment.speaker}] {text}"

            lines.extend((text, ""))
        return "\n".join(lines).strip()
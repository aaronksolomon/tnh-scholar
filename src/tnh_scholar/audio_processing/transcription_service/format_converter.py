from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field, field_validator

from tnh_scholar.audio_processing.transcription_service.timed_text import (
    SRTConfig,
    SRTProcessor,
    TimedText,
    TimedTextSegment,
)
from tnh_scholar.logging_config import get_child_logger

logger = get_child_logger(__name__)


def convert_sec_to_ms(
    data: Dict[str, Any], source_field: str, target_field: str, label="Word"
    )-> Dict[str, Any]:
    """
    Helper function to convert a timing field in seconds to milliseconds.
    Raises ValueError if the required timing is missing (None).
    Modifies the data dictionary in place.

    Args:
        data (dict): The dictionary containing timing fields.
        source_field (str): The key for the timing value in seconds.
        target_field (str): The key to set the converted timing in milliseconds.
        label (str): A label used in error messages.
    Returns:
        dict: The updated dictionary.
    """
    if source_field in data and target_field not in data:
        if data[source_field] is None:
            raise ValueError(f"{label} missing {source_field} timing: {data}")
        data[target_field] = int(data[source_field] * 1000)
    return data


class SegmenterConfig(BaseModel):
    """Configuration for word-based segmentation."""
    max_words_per_segment: int = 20
    max_characters_per_segment: int = 42
    max_seg_duration: int = 5000  # in ms
    min_pause: int = 1700  # in ms
    sentence_end_chars: Set[str] = {'.', '!', '?'}


class FormatConverterConfig(BaseModel):
    """Configuration for TranscriptionFormatConverter."""
    default_audio_duration_ms: int = 60000  # 60 seconds in ms
    segmenter_config: SegmenterConfig = Field(default_factory=SegmenterConfig)
    include_segment_index: bool = True


class TranscriptionWord(BaseModel):
    """Represents a single word with timing information."""
    text: str = ""
    start_ms: int  # Required field, no default
    end_ms: int    # Required field, no default
    confidence: float = 0.0
    
    model_config = {
        "populate_by_name": True,
        "extra": "ignore",
        "arbitrary_types_allowed": True  
    }
    
    def __len__(self) -> int:
        return len(self.text)
    
    @field_validator('start_ms', 'end_ms')
    @classmethod
    def validate_timing(cls, v: int) -> int:
        if v < 0:
            raise ValueError(f"Timing value must be non-negative: {v}")
        return v
    
    def ends_with_punctuation(self, end_chars: Set[str]) -> bool:
        """Check if word ends with sentence-ending punctuation."""
        stripped = self.text.rstrip()
        return bool(stripped and stripped[-1] in end_chars)
    
    @classmethod
    def from_dict(cls, word_dict: Dict[str, Any]) -> "TranscriptionWord":
        """
        Create from dict with normalization of fields.
        Ensures all time values are in milliseconds.
        
        Raises:
            ValueError: If required timing information is missing or invalid
        """
        # Copy to avoid modifying original
        data = word_dict.copy()
        
        # Handle different field names for the word text
        if "word" in data and "text" not in data:
            data["text"] = data.pop("word")
        
        # Convert seconds to milliseconds if provided that way    
        convert_sec_to_ms(data, "start", "start_ms", label="Word")
        convert_sec_to_ms(data, "end", "end_ms", label="Word")
        
        # Check that required timing fields are present
        if "start_ms" not in data:
            raise ValueError(f"Word missing timing: {data}")
        if "end_ms" not in data:
            raise ValueError(f"Word missing timing: {data}")
            
        return cls.model_validate(data)


class TranscriptionSegment(BaseModel):
    """Represents a segment of transcribed speech."""
    text: str = ""
    start_ms: int  # Required field, no default
    end_ms: int    # Required field, no default
    speaker: Optional[str] = None
    words: List[TranscriptionWord] = Field(default_factory=list)
    
    model_config = {
        "populate_by_name": True,
        "extra": "ignore",
        "arbitrary_types_allowed": True  
    }
    
    @field_validator('start_ms', 'end_ms')
    @classmethod
    def validate_timing(cls, v: int) -> int:
        if v < 0:
            raise ValueError(f"Timing value must be non-negative: {v}")
        return v
    
    @field_validator('words')
    @classmethod
    def validate_words_order(
        cls, words: List[TranscriptionWord]
        ) -> List[TranscriptionWord]:
        """Validate that words are in chronological order."""
        if not words:
            return words
            
        prev_end = words[0].start_ms
        for i, word in enumerate(words):
            if word.start_ms <= prev_end:
                raise ValueError(f"Word at index {i} starts before previous word ends")
            prev_end = word.end_ms
        return words
    
    def duration_ms(self) -> int:
        """Get duration in milliseconds."""
        return self.end_ms - self.start_ms
        
    def is_empty(self) -> bool:
        """Check if segment has any text content."""
        return not bool(self.text)
    
    def add_word(self, word: TranscriptionWord) -> None:
        """Add a word to the segment."""
        # Update timing when adding first word
        if not self.words:
            self.start_ms = word.start_ms
        
        # Always update end time with the latest word
        self.end_ms = word.end_ms
            
        # Update text with proper spacing
        if self.text:
            self.text += f" {word.text}"
        else:
            self.text = word.text
            
        # Add to words list
        self.words.append(word)
        
    def _to_timed_text_segment(self):
        """convert to TimedText object for output formatting using SRTProcessor"""
        return TimedTextSegment(
            text=self.text, 
            start_ms=self.start_ms, 
            end_ms=self.end_ms, 
            speaker=self.speaker,
            index=None
            )
        
    @classmethod
    def from_dict(cls, segment_dict: Dict[str, Any]) -> "TranscriptionSegment":
        """
        Create from dict with normalization of fields.
        Ensures all time values are in milliseconds.
        
        Raises:
            ValueError: If required timing information is missing or invalid
        """
        # Copy to avoid modifying original
        data = segment_dict.copy()
        
        # Convert seconds to milliseconds if provided that way
        convert_sec_to_ms(data, "start", "start_ms", label="Segment")
        convert_sec_to_ms(data, "end", "end_ms", label="Segment")
        
        # Check that required timing fields are present
        if "start_ms" not in data:
            raise ValueError(f"Segment missing start_ms: {data}")
        if "end_ms" not in data:
            raise ValueError(f"Segment missing end_ms: {data}")
            
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
    
    def __init__(self, config: Optional[SegmenterConfig] = None):
        self.config = config or SegmenterConfig()
        self.segments: List[TranscriptionSegment] = []
        self.current_segment: TranscriptionSegment
        self.word_count: int = 0
        self.char_count: int = 0
        self.prev_word_end: int = 0

    def create_segments(
        self, words: List[TranscriptionWord]
        ) -> List[TranscriptionSegment]:
        if not words:
            raise ValueError("Cannot create segments from empty words list")

        self._init_segment_creation(words)
    
        for word in words:
            self._add_to_segments(word)
            
        self._finalize_segments()
        
        return self.segments

    def _init_segment_creation(self, words):
        self.segments = []
        self.word_count = 0
        self.char_count = 0
        self.prev_word_end = 0
        self.current_segment = TranscriptionSegment(
            start_ms=words[0].start_ms, end_ms=words[0].end_ms
        )
        
    def _finalize_segments(self):
        if not self.current_segment.is_empty():
            self.segments.append(self.current_segment)
    
    def _add_to_segments(self, word):
        # Check for pause between words
        if self._significant_pause_before(word):
            self._start_new_segment(word)

        self.current_segment.add_word(word)
        self.char_count += len(word)
        self.word_count += 1

        # Check if we should complete this segment
        if self._segment_complete(word):
            self._start_new_segment(word)

        self.prev_word_end = word.end_ms

    def _start_new_segment(self, word: TranscriptionWord):
        """Finalize current segment and start another with given word."""
        self.segments.append(self.current_segment)
        self.current_segment = TranscriptionSegment(
            start_ms=word.start_ms, end_ms=word.end_ms
        )
        self._reset_segment_state()
    
        
    def _reset_segment_state(self) -> None:
        """Reset the segment data for a new segment."""
        self.word_count = 0
        self.char_count = 0
        
        
    def _segment_complete(self, word: TranscriptionWord) -> bool:
        """Check if the current segment should be completed."""
        return (
            not self.current_segment.is_empty()
            and (
                word.ends_with_punctuation(self.config.sentence_end_chars)
                or self.char_count >= self.config.max_characters_per_segment
                or self.word_count >= self.config.max_words_per_segment
                or self.current_segment.duration_ms() >= self.config.max_seg_duration
            )
        )

    def _significant_pause_before(self, word: TranscriptionWord) -> bool:
        """Check if there's a significant pause before the current word."""
        return (
            self.prev_word_end > 0
            and not self.current_segment.is_empty()
            and (word.start_ms - self.prev_word_end) >= self.config.min_pause
        )


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
        
    def _to_timed_text(self, ts_segments: List[TranscriptionSegment]):
        timed_segments = [ts_seg._to_timed_text_segment() for ts_seg in ts_segments]
        return TimedText(segments=timed_segments)
    
    def _format_timestamp(self, ms: int, separator: str) -> str:
        """
        Format timestamp in HH:MM:SS[separator]mmm format from milliseconds.
        
        Args:
            ms: Time in milliseconds
            separator: Separator character between seconds and milliseconds
            
        Returns:
            Formatted timestamp string
        """
        # Calculate hours, minutes, seconds and remaining milliseconds
        hours, remainder_ms = divmod(ms, 3600000)  # ms in an hour
        minutes, remainder_ms = divmod(remainder_ms, 60000)  # ms in a minute
        seconds, milliseconds = divmod(remainder_ms, 1000)  # ms in a second
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}{separator}{milliseconds:03d}"
    
    def _format_srt_timestamp(self, ms: int) -> str:
        """Format timestamp for SRT format (HH:MM:SS,mmm)."""
        return self._format_timestamp(ms, ',')
    
    def _format_vtt_timestamp(self, ms: int) -> str:
        """Format timestamp for VTT format (HH:MM:SS.mmm)."""
        return self._format_timestamp(ms, '.')
            
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
            List of segment dictionaries with at 
            least "text", "start_ms", and "end_ms" keys
            
        Raises:
            ValueError: If segments cannot be created due to missing or invalid data
        """
        # Try utterances (has speaker info)
        if utterances := result.get("utterances", []):
            return [TranscriptionSegment.from_dict(u) for u in utterances]

        # Try word-level segmentation
        if words := result.get("words", []):
            word_objects = [TranscriptionWord.from_dict(w) for w in words]
            return self.word_segmenter.create_segments(word_objects)

        # Fallback to single segment
        if text := result.get("text", ""):
            # Get duration in milliseconds, using default if not available
            duration_ms = result.get("audio_duration_ms", 
                                    self.config.default_audio_duration_ms)
            
            return [TranscriptionSegment(
                text=text,
                start_ms=0,
                end_ms=duration_ms
            )]
            
        raise ValueError(
            "Cannot create segments: no utterances, words, or text found in result"
            )
    
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
        
        Returns:
            String representation in requested format
            
        Raises:
            ValueError: If format_type is not supported or segments cannot be created
        """
        format_options = format_options or {}
        format_type = format_type.lower()
        
        # Get segments from result
        segments = self._get_segments(result)
        
        logger.info(f"segments collected: {segments}")
        
        # Check format type and convert accordingly
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
        """
        include_speaker = options.get("include_speaker", True)
        
        timed_text = self._to_timed_text(segments)
        
        config = SRTConfig(include_speaker=include_speaker)
        processor = SRTProcessor(config=config)
        
        return processor.generate(timed_text)

        # for i, segment in enumerate(segments, 1):
        #     if segment.is_empty():
        #         continue

        #     # Format index
        #     if self.config.include_segment_index:
        #         lines.append(f"{i}")

        #     # Format time range
        #     start_time = self._format_srt_timestamp(segment.start_ms)
        #     end_time = self._format_srt_timestamp(segment.end_ms)
        #     lines.append(f"{start_time} --> {end_time}")

        #     # Format text with optional speaker
        #     text = segment.text
        #     if include_speaker and segment.speaker:
        #         text = f"[{segment.speaker}] {text}"

        #     lines.extend((text, ""))
        # return "\n".join(lines).strip()

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

            # Format time range using milliseconds directly
            start_time = self._format_vtt_timestamp(segment.start_ms)
            end_time = self._format_vtt_timestamp(segment.end_ms)
            lines.append(f"{start_time} --> {end_time}")

            # Format text with optional speaker
            text = segment.text
            if include_speaker and segment.speaker:
                text = f"[{segment.speaker}] {text}"

            lines.extend((text, ""))
        return "\n".join(lines).strip()
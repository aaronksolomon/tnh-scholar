from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field


class SegmenterConfig(BaseModel):
    """Configuration for word-based segmentation."""
    max_words_per_segment: int = 20
    max_segment_duration_ms: int = 7000  # 7 seconds in ms
    min_pause_ms: int = 2000  # 2 seconds in ms
    sentence_end_chars: Set[str] = {'.', '!', '?'}


class FormatConverterConfig(BaseModel):
    """Configuration for TranscriptionFormatConverter."""
    default_audio_duration_ms: int = 60000  # 60 seconds in ms
    segmenter_config: SegmenterConfig = Field(default_factory=SegmenterConfig)
    include_segment_index: bool = True


class TranscriptionWord(BaseModel):
    """Represents a single word with timing information."""
    text: str = ""
    start_ms: int
    end_ms: int 
    confidence: float = 0.0
    
    model_config = {
        "populate_by_name": True,
        "extra": "ignore",
    }
    
    def has_timing(self) -> bool:
        """Check if word has valid timing information."""
        return self.start_ms is not None and self.end_ms is not None
    
    def ends_punctuation(self, end_chars: Set[str]) -> bool:
        """Check if word ends with sentence-ending punctuation."""
        stripped = self.text.rstrip()
        return bool(stripped and stripped[-1] in end_chars)
    
    @classmethod
    def from_dict(cls, word_dict: Dict[str, Any]) -> "TranscriptionWord":
        """
        Create from dict with normalization of fields.
        Ensures all time values are in milliseconds.
        """
        # Copy to avoid modifying original
        data = word_dict.copy()
        
        # Handle different field names for the word text
        if "word" in data and "text" not in data:
            data["text"] = data.pop("word")
            
        # Handle seconds to milliseconds conversion if needed
        if "start" in data and "start_ms" not in data:
            data["start_ms"] = int(data["start"] * 1000)
        if "end" in data and "end_ms" not in data:
            data["end_ms"] = int(data["end"] * 1000)
            
        return cls.model_validate(data)
    
    @classmethod
    def _validate_words(cls, words: List[Dict[str, Any]]) -> None:
        """
        Validate that all words have required timing information.
        
        Args:
            words: List of word dictionaries
            
        Raises:
            ValueError: If any word is missing start_ms or end_ms
        """
        for i, word in enumerate(words):
            if "start_ms" not in word or word["start_ms"] is None:
                raise ValueError(f"Word at index {i} is missing start_ms: {word}")
            if "end_ms" not in word or word["end_ms"] is None:
                raise ValueError(f"Word at index {i} is missing end_ms: {word}")


class TranscriptionSegment(BaseModel):
    """Represents a segment of transcribed speech."""
    text: str = ""
    start_ms: int = None
    end_ms: int = None
    speaker: Optional[str] = None
    words: List[TranscriptionWord] = Field(default_factory=list)
    
    model_config = {
        "populate_by_name": True,
        "extra": "ignore",
    }
    
    def has_timing(self) -> bool:
        """Check if segment has valid timing information."""
        return self.start_ms is not None and self.end_ms is not None
    
    def duration_ms(self) -> int:
        """
        Get duration in milliseconds.
        
        Raises:
            ValueError: If timing information is incomplete
        """
        if not self.has_timing():
            raise ValueError(
                "Cannot calculate duration without complete timing information"
                )
        return self.end_ms - self.start_ms  # type: ignore
        
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
        Create from dict with normalization of fields.
        Ensures all time values are in milliseconds.
        """
        # Copy to avoid modifying original
        data = segment_dict.copy()
        
        # Handle seconds to milliseconds conversion if needed
        if "start" in data and "start_ms" not in data:
            data["start_ms"] = int(data["start"] * 1000)
        if "end" in data and "end_ms" not in data:
            data["end_ms"] = int(data["end"] * 1000)
            
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

    def create_segments(
        self,
        words: List[TranscriptionWord]
        ) -> List[TranscriptionSegment]:
        
        segments: List[TranscriptionSegment] = []
        current_segment = TranscriptionSegment()
        word_count = 0
        prev_word_end: Optional[int] = None

        for word in words:
            # Default to 0 if start_ms is None
            word_start_ms = word.start_ms or 0
            # Default to start_ms if end_ms is None
            word_end_ms = word.end_ms or word_start_ms

            # Check for pause between words
            if self._has_pause(prev_word_end, word_start_ms) and \
                not current_segment.is_empty():
                segments.append(current_segment)
                current_segment = TranscriptionSegment()
                word_count = 0

            current_segment.add_word(word)
            word_count += 1

            # Check if we should complete this segment
            if self._should_complete_segment(current_segment, word, word_count) and \
                not current_segment.is_empty():
                segments.append(current_segment)
                current_segment = TranscriptionSegment()
                word_count = 0

            prev_word_end = word_end_ms

        # Add remaining segment if not empty
        if not current_segment.is_empty():
            segments.append(current_segment)

        return segments

    def _has_pause(
        self, prev_end_ms: Optional[int], current_start_ms: int) -> bool:
        """Check if there's a significant pause between words."""
        if prev_end_ms is None:
            return False
        return (current_start_ms - prev_end_ms) >= self.config.min_pause_ms

    def _should_complete_segment(
        self, 
        segment: TranscriptionSegment, 
        word: TranscriptionWord, 
        word_count: int
    ) -> bool:
        """Determine if the current segment should be completed."""
        # Complete segment if word ends with sentence-ending punctuation
        if word.ends_punctuation(self.config.sentence_end_chars):
            return True
            
        # Complete segment if we've reached max word count
        if word_count >= self.config.max_words_per_segment:
            return True
            
        # Complete segment if we've reached max duration
        try:
            return segment.duration_ms() >= self.config.max_segment_duration_ms
        except ValueError:
            # If we can't calculate duration, don't complete segment
            return False


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
            List of segment dictionaries with 
            at least "text", "start_ms", and "end_ms" keys
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
            start_ms = segment.start_ms or 0
            end_ms = segment.end_ms or start_ms + 1000
                
            start_time = self._format_srt_timestamp(start_ms)
            end_time = self._format_srt_timestamp(end_ms)
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

            # Format time range using milliseconds directly
            start_ms = segment.start_ms or 0
            end_ms = segment.end_ms or start_ms + 1000
            
            start_time = self._format_vtt_timestamp(start_ms)
            end_time = self._format_vtt_timestamp(end_ms)
            lines.append(f"{start_time} --> {end_time}")

            # Format text with optional speaker
            text = segment.text
            if include_speaker and segment.speaker:
                text = f"[{segment.speaker}] {text}"

            lines.extend((text, ""))
        return "\n".join(lines).strip()
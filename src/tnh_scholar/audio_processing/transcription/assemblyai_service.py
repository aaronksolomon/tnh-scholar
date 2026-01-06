"""
AssemblyAI implementation of the TranscriptionService interface.

This module provides a complete implementation of the TranscriptionService interface
using the AssemblyAI Python SDK, with support for all major features including:

- Transcription with configurable options
- Speaker diarization
- Automatic language detection
- Audio intelligence features
- Subtitle generation
- Regional endpoint support
- Webhook callbacks

The implementation follows a modular design with single-action methods and
supports both synchronous and asynchronous usage patterns.
"""

import inspect
import os
from concurrent.futures import Future
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

import assemblyai as aai
from dotenv import load_dotenv

from tnh_scholar.logging_config import get_child_logger

from ..timed_object.timed_text import Granularity, TimedText, TimedTextUnit
from .format_converter import FormatConverter
from .transcription_service import TranscriptionResult, TranscriptionService

# Load environment variables
load_dotenv()

logger = get_child_logger(__name__)


class SpeechModel(str, Enum):
    """Supported AssemblyAI speech models."""
    BEST = "best"
    NANO = "nano"


@dataclass
class AAIConfig:
    """
    Comprehensive configuration for AssemblyAI transcription service.
    
    This class contains all configurable options for the AssemblyAI API,
    organized by feature category.
    """
    
    # Base configuration
    api_key: Optional[str] = None
    use_eu_endpoint: bool = False
    
    # Connection configuration
    polling_interval: int = 4
    
    # Core transcription configuration
    speech_model: SpeechModel = SpeechModel.BEST
    language_code: Optional[str] = None
    language_detection: bool = True
    dual_channel: bool = False
    
    # Text formatting options
    format_text: bool = True
    punctuate: bool = True
    disfluencies: bool = False
    filter_profanity: bool = False
    
    # subtitle options
    chars_per_caption: int = 60
    
    # Speaker options
    speaker_labels: bool = True
    speakers_expected: Optional[int] = None
    
    # Audio channel options
    custom_spelling: Dict[str, str] = field(default_factory=dict)
    word_boost: List[str] = field(default_factory=list)
    
    # Audio intelligence configuration
    auto_chapters: bool = False
    auto_highlights: bool = False
    entity_detection: bool = False
    iab_categories: bool = False
    sentiment_analysis: bool = False
    summarization: bool = False
    content_safety: bool = False
    
    # Callback options (Webhook functionality currently not implemented)
    # The transcribe_asynch method provides asynchronous processing
    webhook_url: Optional[str] = None
    webhook_auth_header_name: Optional[str] = None
    webhook_auth_header_value: Optional[str] = None


class AAITranscriptionService(TranscriptionService):
    """
    AssemblyAI implementation of the TranscriptionService interface.
    
    Provides comprehensive access to AssemblyAI's transcription services
    with support for all major features through the official Python SDK.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        options: Optional[Dict[str, Any]] = None,
        ):
        """
        Initialize the AssemblyAI transcription service.
        
        Args:
            api_key: AssemblyAI API key (defaults to ASSEMBLYAI_API_KEY env var)
            options: Additional transcription configuration overrides
        """
        # Initialize format converter for fallback cases
        self.format_converter = FormatConverter()
        
        # Set and validate configuration
        self.config = AAIConfig()
        
        # Configure SDK
        self._configure_sdk(api_key)
        
        # Create transcriber instance
        self.transcriber = aai.Transcriber(
            config=self._create_transcription_config(options)
            )
        
        logger.debug("Initialized AssemblyAI service with SDK")
    
    def _configure_sdk(self, api_key: Optional[str] = None) -> None:
        """
        Configure the AssemblyAI SDK with API key and regional settings.
        
        Args:
            api_key: AssemblyAI API key
            
        Raises:
            ValueError: If no API key is provided or found in environment
        """
        # Set API key - priority: parameter > config > env var
        api_key = api_key or self.config.api_key or os.getenv("ASSEMBLYAI_API_KEY")
        if not api_key:
            raise ValueError(
                "AssemblyAI API key is required. Set ASSEMBLYAI_API_KEY environment "
                "variable, pass as api_key parameter, or include in config."
            )
        
        # Configure SDK settings
        aai.settings.api_key = api_key
        aai.settings.polling_interval = self.config.polling_interval


        
        # Configure regional settings
        if self.config.use_eu_endpoint:
            aai.settings.base_url = "https://api.eu.assemblyai.com/v2"
            logger.debug("Using EU endpoint for AssemblyAI API")
    
    def _create_transcription_config(
        self, 
        options: Optional[Dict[str, Any]] = None
    ) -> aai.TranscriptionConfig:
        """
        Create a TranscriptionConfig object from configuration and options.
        
        Args:
            options: Additional options to override configuration
            
        Returns:
            Configured TranscriptionConfig object
        """
        # Start with empty config
        config_params = {}

        # Add core settings
        if self.config.speech_model == SpeechModel.NANO:
            config_params["speech_model"] = "nano"

        if self.config.language_code:
            config_params["language_code"] = self.config.language_code

        config_params["language_detection"] = self.config.language_detection
        config_params["dual_channel"] = self.config.dual_channel

        # Add text formatting options
        config_params["format_text"] = self.config.format_text
        config_params["punctuate"] = self.config.punctuate
        config_params["disfluencies"] = self.config.disfluencies
        config_params["filter_profanity"] = self.config.filter_profanity

        # Add speaker options
        config_params["speaker_labels"] = self.config.speaker_labels
        if self.config.speakers_expected is not None:
            config_params["speakers_expected"] = self.config.speakers_expected

        # Add audio intelligence options
        config_params["auto_chapters"] = self.config.auto_chapters
        config_params["auto_highlights"] = self.config.auto_highlights
        config_params["entity_detection"] = self.config.entity_detection
        config_params["iab_categories"] = self.config.iab_categories
        config_params["sentiment_analysis"] = self.config.sentiment_analysis
        config_params["summarization"] = self.config.summarization
        config_params["content_safety"] = self.config.content_safety

        # Add custom vocabulary options
        if self.config.word_boost:
            config_params["word_boost"] = self.config.word_boost

        # Add custom spelling
        if self.config.custom_spelling:
            config_params["custom_spelling"] = self.config.custom_spelling

        # Add webhook config
        if self.config.webhook_url:
            config_params["webhook_url"] = self.config.webhook_url
            if self.config.webhook_auth_header_name and \
                self.config.webhook_auth_header_value:
                config_params["webhook_auth_header_name"] = \
                    self.config.webhook_auth_header_name
                config_params["webhook_auth_header_value"] = \
                    self.config.webhook_auth_header_value

        # Override with any provided options (filtered to SDK-supported keys)
        if options:
            config_params |= self._normalize_options(options)

        # Create config object
        return aai.TranscriptionConfig(**config_params)

    def _normalize_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter/translate CLI options into supported AssemblyAI config keys.
        """
        normalized: Dict[str, Any] = {}
        allowed_keys = self._get_transcription_config_keys()

        for key, value in options.items():
            if key == "language" and "language_code" in allowed_keys:
                if value is not None:
                    normalized["language_code"] = value
                continue
            if key in allowed_keys:
                normalized[key] = value
        if "language_code" in normalized and "language_detection" in allowed_keys:
            normalized["language_detection"] = False
        return normalized

    def _get_transcription_config_keys(self) -> set[str]:
        """
        Return supported keyword names for AssemblyAI TranscriptionConfig.
        """
        params = inspect.signature(aai.TranscriptionConfig).parameters
        return set(params.keys())
    
    def _get_file_path(
        self, 
        audio_file: Union[Path, BinaryIO, str]
        ) -> Union[BinaryIO, str]:
        """
        Get appropriate file path for different input types.
        
        Args:
            audio_file: Path, file-like object, or URL of audio file
            
        Returns:
            Path or string for SDK
            
        Raises:
            TypeError: If input type is not supported
        """
        # Handle Path objects
        if isinstance(audio_file, Path):
            return str(audio_file)
            
        # Handle URLs
        if isinstance(audio_file, str) and (
            audio_file.startswith("http://") or 
            audio_file.startswith("https://")
        ):
            return audio_file
            
        # Handle file-like objects
        if hasattr(audio_file, "read"):
            # SDK handles file-like objects directly
            return audio_file
            
        raise TypeError(f"Unsupported audio file type: {type(audio_file)}")
    
    def _extract_words(self, transcript: aai.Transcript) -> TimedText:
        """
        Extract words with timestamps from transcript and return a TimedText object.

        Args:
            transcript: AssemblyAI transcript object

        Returns:
            TimedText object containing word-level units
        """
        if not transcript.words:
            raise ValueError(f"Transcript object has no words: {transcript}")

        units = [
            TimedTextUnit(
                index=None,
                granularity=Granularity.WORD,
                speaker=word.speaker,
                text=word.text,
                start_ms=word.start,
                end_ms=word.end,
                confidence=word.confidence,
            )
            for word in transcript.words
        ]

        # TimedText performs its own internal validation
        return TimedText(words=units, granularity=Granularity.WORD)
    
    def _extract_utterances(self, transcript: aai.Transcript) -> TimedText:
        """
        Extract utterances (speaker segments) from transcript and return a TimedText object.

        Args:
            transcript: AssemblyAI transcript object

        Returns:
            TimedText object containing utterance-level units
        """
        if not (utterances := getattr(transcript, "utterances", None)):
            # Return an empty TimedText if diarization wasn't requested
            return TimedText(segments=[], granularity=Granularity.SEGMENT)

        units = [
            TimedTextUnit(
                index=None,
                granularity=Granularity.SEGMENT,
                text=utterance.text,
                start_ms=utterance.start,
                end_ms=utterance.end,
                speaker=utterance.speaker,
                confidence=utterance.confidence,
            )
            for utterance in utterances
        ]

        return TimedText(segments=units, granularity=Granularity.SEGMENT)
    
    def _extract_audio_intelligence(self, transcript: aai.Transcript) -> Dict[str, Any]:
        """
        Extract audio intelligence features from transcript.
        
        Args:
            transcript: AssemblyAI transcript object
            
        Returns:
            Dictionary of audio intelligence features
        """
        intelligence = {}

        # Extract auto chapters
        if hasattr(transcript, "chapters") and transcript.chapters:
            chapters_data = []
            chapters_data.extend(
                {
                    "summary": chapter.summary,
                    "headline": chapter.headline,
                    "start_ms": chapter.start,
                    "end_ms": chapter.end,
                }
                for chapter in transcript.chapters
            )
            intelligence["chapters"] = chapters_data

        # Extract sentiment analysis
        if hasattr(transcript, "sentiment_analysis") and transcript.sentiment_analysis:
            sentiment_data = []
            sentiment_data.extend(
                {
                    "text": sentiment.text,
                    "sentiment": sentiment.sentiment,
                    "confidence": sentiment.confidence,
                    "start_ms": sentiment.start,
                    "end_ms": sentiment.end,
                }
                for sentiment in transcript.sentiment_analysis
            )
            intelligence["sentiment_analysis"] = sentiment_data

        # Extract entity detection
        if hasattr(transcript, "entities") and transcript.entities:
            entities_data = []
            entities_data.extend(
                {
                    "text": entity.text,
                    "entity_type": entity.entity_type,
                    "start_ms": entity.start,
                    "end_ms": entity.end,
                }
                for entity in transcript.entities
            )
            intelligence["entities"] = entities_data

        # Extract topics (IAB categories)
        if hasattr(transcript, "iab_categories") and transcript.iab_categories:
            topics_data = {
                "results": [],
                "summary": transcript.iab_categories.summary
            }

            if not transcript.iab_categories.results:
                return topics_data
            
            for result in transcript.iab_categories.results:
                topics_data["results"].append({
                    "text": result.text,
                    "labels": [
                        {"label": label.label, "relevance": label.relevance}
                        for label in result.labels
                    ],
                    "timestamp": {
                        "start": result.timestamp.start,
                        "end": result.timestamp.end
                    }
                })

            intelligence["topics"] = topics_data

        # Extract auto highlights
        if hasattr(transcript, "auto_highlights") and transcript.auto_highlights:
            intelligence["highlights"] = {
                "results": transcript.auto_highlights.results,
                "status": transcript.auto_highlights.status
            }

        return intelligence
    
    def standardize_result(self, transcript: aai.Transcript) -> TranscriptionResult:
        """
        Standardize AssemblyAI transcript to match common format.

        Args:
            transcript: AssemblyAI transcript object

        Returns:
            Standardized result dictionary
        """
        # Extract words and utterances as TimedText
        words = self._extract_words(transcript)
        utterances = self._extract_utterances(transcript)

        language = self.config.language_code or \
                ("auto" if self.config.language_detection else "unknown")

        return TranscriptionResult(
            text=transcript.text or "",
            language=language,
            word_timing=words,
            utterance_timing=utterances,
            confidence=getattr(transcript, "confidence", 0.0),
            audio_duration_ms=getattr(transcript, "audio_duration", 0),
            transcript_id=transcript.id,
            status=transcript.status,
            raw_result=transcript.json_response,
        )
    
    def transcribe(
        self,
        audio_file: Union[Path, BinaryIO, str],
        options: Optional[Dict[str, Any]] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio file to text using AssemblyAI's synchronous SDK approach.
        
        This method handles:
        - File paths
        - File-like objects
        - URLs
        
        Args:
            audio_file: Path, file-like object, or URL of audio file
            options: Provider-specific options for transcription
            
        Returns:
            Dictionary containing standardized transcription results
        """
        try:
            transcript = self._gen_transcript(options, audio_file)
            
            # Standardize the result format
            return self.standardize_result(transcript)
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise RuntimeError(f"AssemblyAI transcription failed: {e}") from e
    
    def transcribe_async(
        self,
        audio_file: Union[Path, BinaryIO, str],
        options: Optional[Dict[str, Any]] = None
    ) ->  Future:
        """
        Submit an asynchronous transcription job using AssemblyAI's SDK.
        
        This method submits a transcription job and returns immediately with
        a transcript ID that can be used to retrieve results later.
        
        Args:
            audio_file: Path, file-like object, or URL of audio file
            options: Provider-specific options for transcription
            
        Returns:
            String containing the transcript ID for later retrieval
            
        Notes:
            The SDK's submit method returns a Future object, but this method
            extracts just the transcript ID for simpler handling.
        """
        try:
            # Create configuration with options
            tx_config = self._create_transcription_config(options)
            
            # Get file path/object in the right format
            file_path = self._get_file_path(audio_file)
            
            logger.info("Submitting asynchronous transcription with AssemblyAI SDK")
            
            # Use the SDK's asynchronous submit method
            # This returns a Future object containing a Transcript
            return self.transcriber.transcribe_async(file_path, config=tx_config)
                        
        except Exception as e:
            logger.error(f"Transcription submission failed: {e}")
            raise RuntimeError(f"AssemblyAI transcription submission failed: {e}") \
                from e
    
    def get_result(self, job_id: str) -> TranscriptionResult:
        """
        Get results for an existing transcription job.
        
        This method blocks until the transcript is retrieved.
        
        Args:
            job_id: ID of the transcription job
            
        Returns:
            Dictionary containing transcription results
        """
        try:
            # Use the SDK's get_by_id method to retrieve the transcript
            # This blocks until the transcript is retrieved
            transcript = aai.Transcript.get_by_id(job_id)
            
            # Standardize the result format
            return self.standardize_result(transcript)
            
        except Exception as e:
            logger.error(f"Failed to retrieve transcript {job_id}: {e}")
            raise RuntimeError(f"Failed to retrieve transcript: {e}") from e
    
    def get_subtitles(
        self, 
        transcript_id: str, 
        format_type: str = "srt",
    ) -> str:
        """
        Get subtitles directly from AssemblyAI.
        
        Args:
            transcript_id: ID of the transcription job
            format_type: Format type ("srt" or "vtt")
            
        Returns:
            String representation in the requested format
            
        Raises:
            ValueError: If the format type is not supported
        """
        chars_per_caption = self.config.chars_per_caption
        
        format_type = format_type.lower()
        
        if format_type not in ["srt", "vtt"]:
            raise ValueError(
                f"Unsupported subtitle format: {format_type}. "
                "Supported formats: srt, vtt"
                )
        # Create transcript object from ID
        transcript = aai.Transcript(transcript_id=transcript_id)
        
        # Get subtitles in requested format
        if format_type == "srt":
            return transcript.export_subtitles_srt(chars_per_caption=chars_per_caption)
        else:  # format_type == "vtt"
            return transcript.export_subtitles_vtt(chars_per_caption=chars_per_caption)
    
    def transcribe_to_format(
        self,
        audio_file: Union[Path, BinaryIO, str],
        format_type: str = "srt",
        transcription_options: Optional[Dict[str, Any]] = None,
        format_options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Transcribe audio and return result in specified format.
        
        Takes advantage of the direct subtitle generation
        functionality when requesting SRT or VTT formats.
        
        Args:
            audio_file: Path, file-like object, or URL of audio file
            format_type: Format type (e.g., "srt", "vtt", "text")
            transcription_options: Options for transcription
            format_options: Format-specific options
            
        Returns:
            String representation in the requested format
        """
        format_type = format_type.lower()
        chars_per_caption = format_options.get(
            'chars_per_caption', self.config.chars_per_caption) \
            if format_options else self.config.chars_per_caption

        transcript = self._gen_transcript(
                transcription_options, audio_file
            )

        # Check if we need direct subtitle generation
        if format_type == "srt":  
            return transcript.export_subtitles_srt(chars_per_caption=chars_per_caption)
        elif format_type == "vtt":
            return transcript.export_subtitles_vtt(chars_per_caption=chars_per_caption)

        # For other formats, use the format converter
        # First get a normal transcription result
        result = self.transcribe(audio_file, transcription_options)

        # Then convert to the requested format
        return self.format_converter.convert(
            result, format_type, format_options or {}
        )

    def _gen_transcript(self, transcription_options, audio_file):
        # Create configuration with options
        tx_config = self._create_transcription_config(transcription_options)
        
        # Get file path/object in the right format
        file_path = self._get_file_path(audio_file)
        
        logger.info("Starting synchronous transcription with AssemblyAI SDK")
        
        # Use the SDK's synchronous transcribe method
        # This will block until transcription is complete
        return self.transcriber.transcribe(file_path, config=tx_config)

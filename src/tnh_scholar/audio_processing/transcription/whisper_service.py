"""
TODO: MAJOR REFACTOR PLANNED
-----------------------------------
This module currently mixes persistent service configuration (WhisperConfig) with per-call runtime options,
leading to complex validation and logic. Plan is to:

  - Refactor so each WhisperTranscriptionService instance is configured once at construction, with all
    relevant settings (including file-like/path-like mode, file extension, etc).
  - Use Pydantic BaseSettings for configuration to normalize configuration and validation according to 
        TNH Scholar style.
  - Remove ad-hoc runtime options from the transcribe() entrypoint; all config should be set at init.
  - If a different configuration is needed, instantiate a new service object.
  - This will simplify validation, error handling, and code logic, and make the contract clear and robust.
  - NOTE: This will change the TranscriptionService contract and will require similar changes in other
    transcription system implementations.
  - Update all dependent code and tests accordingly.
-----------------------------------
"""

import json
import os
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, TypedDict, Union

from dotenv import load_dotenv

from tnh_scholar.logging_config import get_child_logger

from ..timed_object.timed_text import Granularity, TimedText, TimedTextUnit
from .format_converter import FormatConverter
from .patches import patch_file_with_name
from .transcription_service import (
    TranscriptionResult,
    TranscriptionService,
)

load_dotenv()

logger = get_child_logger(__name__)


def _logprob_to_confidence(avg_logprob: Optional[float]) -> float:
    """
    Map avg_logprob to confidence [0,1] linearly.
    
    avg_logprob = 0 -> confidence = 1
    avg_logprob = -1 -> confidence = 0
    """
    if avg_logprob is None:
        return 0.0

    confidence = avg_logprob + 1.0

    # Clamp to [0,1]
    confidence = max(0.0, min(1.0, confidence))
    return confidence

class WordEntry(TypedDict, total=False):
    word: str
    start: Optional[float]
    end: Optional[float]


class WhisperSegment(TypedDict, total=False):
    id: int
    start: float
    end: float
    text: str
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float


class WhisperBase(TypedDict):
    text: str
    language: str
    duration: float


class WhisperResponse(WhisperBase, total=False):
    words: Optional[List[WordEntry]]
    segments: Optional[List[WhisperSegment]]


@dataclass
class WhisperConfig:
    """Configuration for the Whisper transcription service."""
    model: str = "whisper-1"
    response_format: str = "verbose_json"
    timestamp_granularities: Optional[List[str]] = field(
        default_factory=lambda: ["word"]
        )
    chunking_strategy: str = "auto" # currently not usable
    language: Optional[str] = None # language code
    temperature: Optional[float] = None
    prompt: Optional[str] = None

    # Supported response formats
    SUPPORTED_FORMATS = ["json", "text", "srt", "vtt", "verbose_json"]
    
    # Parameters allowed for each format
    FORMAT_PARAMS = {
        "verbose_json": ["timestamp_granularities"],
        "json": [],
        "text": [],
        "srt": [],
        "vtt": []
    }
    
    # Basic parameters: always allowed
    BASE_PARAMS = [
            "model", "language", "temperature", "prompt", "response_format",
        ]
    

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for API call."""
        # Filter out None values to avoid sending unnecessary parameters
        return {k: v for k, v in self.__dict__.items() 
                if v is not None and not k.startswith("_") and k != "SUPPORTED_FORMATS"}
    
    def validate(self) -> None:
        """Validate configuration values."""
        if self.response_format not in self.SUPPORTED_FORMATS:
            logger.warning(
                f"Unsupported response format: {self.response_format}, "
                f"defaulting to 'verbose_json'"
            )
            self.response_format = "verbose_json"


class WhisperTranscriptionService(TranscriptionService):
    """
    OpenAI Whisper implementation of the TranscriptionService interface.
    
    Provides transcription services using the OpenAI Whisper API.
    """
    
    def __init__(self, api_key: Optional[str] = None, **config_options: Any):
        """
        Initialize the Whisper transcription service.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            **config_options: Additional configuration options
        """
        # Create configuration base
        self.config = WhisperConfig()
        
        # Set any configuration options provided
        for key, value in config_options.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        # Validate configuration
        self.config.validate()
        
        # Initialize format converter
        self.format_converter = FormatConverter()
        
        # Set API key
        self.set_api_key(api_key)
    
    def _create_jsonl_writer(self):
        """
        Create a file-like object that captures JSONL output.
        
        Returns:
            A file-like object that captures writes
        """
        class JsonlCapture:
            def __init__(self):
                self.data = []
            
            def write(self, content):
                try:
                    # Try to parse as JSON
                    json_obj = json.loads(content)
                    self.data.append(json_obj)
                except json.JSONDecodeError:
                    # If not valid JSON, just append as string
                    self.data.append(content)
            
            def flush(self):
                pass
            
            def close(self):
                pass
        
        return JsonlCapture()
    
    def _prepare_file_object(
        self,
        audio_file: Union[Path, BytesIO],
        options: Optional[Dict[str, Any]] = None
    ) -> tuple[BinaryIO, bool]:
        """
        Prepare file object for API call. PATCH: file-like objects require 'file_extension' in options.

        Args:
            audio_file: Path to audio file or file-like object
            options: Dict containing 'file_extension' if audio_file is file-like

        Returns:
            Tuple of (file_object, should_close_file)

        Raises:
            ValueError: If file-like object is provided without 'file_extension' in options
        """
        if isinstance(audio_file, Path):
            try:
                file_obj = open(audio_file, "rb")
                should_close = True
            except (IOError, OSError) as e:
                raise RuntimeError(f"Failed to open audio file '{audio_file}': {e}") from e
        else:
            file_extension = options.get("file_extension", None) if options else None
            if not file_extension:
                logger.error(f"No file extension provided in options for file-like object: {audio_file}")
                raise ValueError(
                    "For file-like objects, options['file_extension'] "
                    "must be provided. (PATCH for OpenAI API which requires)."
                )
            file_obj = patch_file_with_name(audio_file, file_extension)
            should_close = False

        return file_obj, should_close
    
    def _prepare_api_params(
        self, options: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
        """
        Prepare parameters for the Whisper API call.

        Args:
            options: Additional options for this specific transcription

        Returns:
            Dictionary of parameters for the API call
        """
        base_params = self.config.to_dict()

        # Defensive: ensure options is a dict
        options = options or {}

        # Determine which response format we're using
        response_format = options.get(
            "response_format", self.config.response_format
        )

        # Compute allowed parameters for the chosen format
        allowed_params = (
            set(self.config.FORMAT_PARAMS.get(response_format, []))
            | 
            set(self.config.BASE_PARAMS)
        )

        # Start with base params, filtered to allowed
        api_params = {k: v for k, v in base_params.items() if k in allowed_params}

        # Overlay with options, but only allowed keys
        for k, v in options.items():
            if k in allowed_params:
                api_params[k] = v

        # Validate response format
        if api_params.get("response_format") not in self.config.SUPPORTED_FORMATS:
            logger.warning(
                f"Unsupported response format: {api_params.get('response_format')}, "
                f"defaulting to 'verbose_json'"
            )
            api_params["response_format"] = "verbose_json"

        return api_params
    
    def _to_whisper_response(self, response: Any) -> WhisperResponse:
        """
        Convert an OpenAI Whisper API response (JSON or Verbose JSON) into a clean,
        type-safe WhisperResponse structure.

        Args:
            response: API response (should have .model_dump())

        Returns:
            A WhisperVerboseJson dictionary
        """
            
        if hasattr(response, "model_dump"):
            data = response.model_dump(exclude_unset=True)
        elif hasattr(response, "to_dict"):
            data = response.to_dict()
        elif isinstance(response, dict):
            data = response
        elif isinstance(response, str):
            data = {"text": response} # mimic minimal data response format.
        else:
            raise ValueError(f"OpenAI response does not have a method to extract data "
                             f"(missing 'model_dump' or 'to_dict'): {repr(response)}")
        
        # Required field: duration
        duration = float(data.get("duration", 0.0))
        
        # Required field: text 
        text = data.get("text")
        if not isinstance(text, str):
            raise ValueError(f"Invalid response: 'text' must be a string, "
                             f"got {type(text)}")

        # Optional fields with normalization 
        language = data.get("language") or self.config.language or "unknown"
        if not isinstance(language, str):
            raise ValueError(f"Unexpected OpenAI response: 'language' is not a string."
                             f"got {type(language)}")

        # Optional: words and segments (only present in verbose_json)
        words = data.get("words")
        if words is not None and not isinstance(words, list):
            raise ValueError(f"Invalid 'words': expected list, got {type(words)}")

        segments = data.get("segments")
        if segments is not None and not isinstance(segments, list):
            raise ValueError(f"Invalid 'segments': expected list, got {type(segments)}")

        return WhisperResponse(
            text=text,
            language=language,
            duration=duration,
            words=words,
            segments=segments,
        )
    
    def set_api_key(self, api_key: Optional[str] = None) -> None:
        """
        Set or update the API key.
        
        This method allows refreshing the API key without re-instantiating the class.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            
        Raises:
            ValueError: If no API key is provided or found in environment
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment "
                "variable or pass as api_key parameter."
            )
        
        # Configure OpenAI client
        openai.api_key = self.api_key
        logger.debug("API key updated")
    
    def _seconds_to_ms(self, seconds: Optional[float]) -> Optional[int]:
        """
        Convert seconds to milliseconds.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Time in milliseconds or None if seconds is None
        """
        return None if seconds is None else int(seconds * 1000)
    
    def _export_response(self, response: WhisperResponse) -> TranscriptionResult:
        """Process and validate WhisperResponse into TranscriptionResult."""       
        return TranscriptionResult(
            text=response["text"],
            language=response["language"],
            word_timing=self._extract_and_validate_words(response),
            utterance_timing=self._extract_and_validate_utterances(response),
            confidence=0.0,  # Whisper doesn't provide overall confidence
            audio_duration_ms=self._seconds_to_ms(response.get("duration")),
            transcript_id=None,  # No ID from Whisper
            status="completed",  # You can set a static "completed" status
            raw_result=dict(response),  # Store the original response for debugging
        )
        
    def _extract_and_validate_words(
        self, response: WhisperResponse
        ) -> TimedText:
        """Extract, validate, and convert word data into WordTiming objects."""
        words_data = response.get("words")
        units: list[TimedTextUnit] = []

        if words_data:
            for i, word_entry in enumerate(words_data, start=1):
                word = word_entry.get("word")
                start_ms = self._seconds_to_ms(word_entry.get("start"))
                end_ms = self._seconds_to_ms(word_entry.get("end"))

                if not isinstance(word, str) or not word:
                    logger.warning(f"Invalid or missing word: {word_entry}")
                    continue

                if not isinstance(start_ms, int) or not isinstance(end_ms, int):
                    logger.warning(f"Invalid timestamps for word: {word_entry}")
                    continue

                if start_ms > end_ms:
                    logger.warning(
                        f"Invalid timestamps: start ({start_ms}) > end ({end_ms}) "
                        f"for word: {word}. Setting end = start + 1."
                    )
                    end_ms = start_ms + 1

                if start_ms == end_ms:
                    # Workaround for OpenAI Whisper API bug:
                    # Sometimes start == end for word timestamps, which is invalid for downstream consumers.
                    logger.debug(
                        f"Whisper API returned identical start and end times "
                        f"({start_ms} ms) for word '{word}'. "
                        "Adjusting end_ms to start_ms + 1."
                    )
                    end_ms += 1

                units.append(
                    TimedTextUnit(
                        index=i,
                        text=word,
                        start_ms=start_ms,
                        end_ms=end_ms,
                        speaker=None,
                        granularity=Granularity.WORD,
                        confidence=0.0,
                    )
                )
        
        return TimedText(words=units, granularity=Granularity.WORD)

    def _extract_and_validate_utterances(
        self, response: WhisperResponse
        ) -> TimedText:
        """Extract and validate utterance segments into Utterance objects."""
        segments = response.get("segments")
        units: list[TimedTextUnit] = []
        
        if segments:
            for i, segment in enumerate(segments, start=1):
                start_ms = self._seconds_to_ms(segment.get("start"))
                end_ms = self._seconds_to_ms(segment.get("end"))
                text = segment.get("text", "")

                if not isinstance(start_ms, int) or not isinstance(end_ms, int):
                    logger.warning(f"Invalid segment timestamps: {segment}")
                    continue

                if not isinstance(text, str) or not text.strip():
                    logger.warning(f"Empty or invalid text for segment: {segment}")
                    continue

                units.append(
                    TimedTextUnit(
                        index=i,
                        text=text,
                        start_ms=start_ms,
                        end_ms=end_ms,
                        speaker=None,
                        granularity=Granularity.SEGMENT,
                        confidence=_logprob_to_confidence(segment.get("avg_logprob", 0.0)),
                    )
                )
        
        return TimedText(segments=units, granularity=Granularity.SEGMENT)

    def transcribe(
        self,
        audio_file: Union[Path, BytesIO],
        options: Optional[Dict[str, Any]] = None,
    ) -> TranscriptionResult:
        """
        Transcribe audio file to text using OpenAI Whisper API.

        PATCH: If audio_file is a file-like object, options['file_extension'] must be provided 
        (OpenAI API quirk).

        Args:
            audio_file: Path to audio file or file-like object
            options: Provider-specific options for transcription. 
                     If audio_file is file-like, must include 'file_extension'.

        Returns:
            Dictionary containing transcription results with standardized keys

        Raises:
            ValueError: If file-like object is provided without 'file_extension' in options
        """
        # Prepare file object
        file_obj, should_close = self._prepare_file_object(audio_file, options)
        try:
            return self._transcribe_execute(options, file_obj)
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise
        finally:
            # Clean up file object if we opened it
            if should_close:
                file_obj.close()

    def _transcribe_execute(self, options, file_obj):
        # Prepare API parameters
        api_params = self._prepare_api_params(options)
        api_params["file"] = file_obj

        # Call OpenAI API
        logger.info(f"Transcribing audio with Whisper API "
                    f"using model: {api_params['model']}")
        raw_response = openai.audio.transcriptions.create(**api_params)
        response = self._to_whisper_response(raw_response)

        result = self._export_response(response)
            
        logger.info("Transcription completed successfully")
        return result

    def get_result(self, job_id: str) -> TranscriptionResult:
        """
        Get results for an existing transcription job.
        
        Whisper API operates synchronously and doesn't use job IDs,
        so this method is not implemented.
        
        Args:
            job_id: ID of the transcription job
                
        Returns:
            Dictionary containing transcription results
            
        Raises:
            NotImplementedError: This method is not supported for Whisper
        """
        raise NotImplementedError(
            "Whisper API operates synchronously.\n"
            "Does not support retrieving results by job ID.\n"
            "Use the transcribe() method for direct transcription."
        )
        
    def transcribe_to_format(
        self,
        audio_file: Union[Path, BytesIO],
        format_type: str = "srt",
        transcription_options: Optional[Dict[str, Any]] = None,
        format_options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Transcribe audio and return result in specified format.

        PATCH: If audio_file is a file-like object, transcription_options['file_extension'] must be provided 
        (OpenAI API quirk).

        Takes advantage of the direct subtitle generation functionality when requesting SRT or VTT formats.

        Args:
            audio_file: Path, file-like object, or URL of audio file
            format_type: Format type (e.g., "srt", "vtt", "text")
            transcription_options: Options for transcription. If audio_file is file-like, must include 
                                   'file_extension'.
            format_options: Format-specific options

        Returns:
            String representation in the requested format

        Raises:
            ValueError: If file-like object is provided without 'file_extension' in transcription_options
        """
        format_type = format_type.lower()

        # If requesting SRT or VTT directly, use native OpenAI capabilities
        if format_type in {"srt", "vtt"}:
            # Create options with format set to SRT or VTT
            options = transcription_options.copy() if transcription_options else {}
            options["response_format"] = format_type

            # Prepare file object
            file_obj, should_close = self._prepare_file_object(audio_file, options)

            try:
                # Prepare API parameters
                api_params = self._prepare_api_params(options)
                api_params["file"] = file_obj

                # Call OpenAI API
                logger.info(f"Transcribing directly to {format_type} with Whisper API")
                return openai.audio.transcriptions.create(**api_params)
            finally:
                # Clean up file object if we opened it
                if should_close:
                    file_obj.close()

        # For other formats, use the format converter
        # First get a normal transcription result
        result = self.transcribe(audio_file, transcription_options)

        # Then convert to the requested format
        return self.format_converter.convert(
            result, format_type, format_options or {}
        )

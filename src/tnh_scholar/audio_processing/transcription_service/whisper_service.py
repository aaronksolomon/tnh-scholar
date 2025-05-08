import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, TypedDict, Union

import openai
from dotenv import load_dotenv

from tnh_scholar.logging_config import get_child_logger

from .format_converter import FormatConverter
from .transcription_service import (
    TranscriptionResult,
    TranscriptionService,
    Utterance,
    WordTiming,
)

# Load environment variables
load_dotenv()

logger = get_child_logger(__name__)


def logprob_to_confidence(avg_logprob: Optional[float]) -> float:
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
    
    def __init__(self, api_key: Optional[str] = None, **config_options):
        """
        Initialize the Whisper transcription service.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            **config_options: Additional configuration options
        """
        # Create configuration from provided options
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
        audio_file: Union[Path, BinaryIO]
        ) -> tuple[BinaryIO, bool]:
        """
        Prepare file object for API call.
        
        Args:
            audio_file: Path to audio file or file-like object
            
        Returns:
            Tuple of (file_object, should_close_file)
        """
        if isinstance(audio_file, Path):
            file_obj = open(audio_file, "rb")
            should_close = True
        else:
            file_obj = audio_file
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
    
        # Determine which response format we're using
        if options:
            response_format = options.get(
                "response_format", self.config.response_format
                )
        else:
            response_format = self.config.response_format
        
        # Remove parameters not allowed for the chosen format
        allowed_params = self.config.FORMAT_PARAMS.get(response_format, []) + [
            "model", "language", "temperature", "prompt", "response_format"
        ]
        
        api_params = {k: v for k, v in base_params.items() if k in allowed_params}
        
        # Override with provided options   
        if options:
            api_params |= options
        
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
        
        # --- PATCH for OpenAI Whisper API inconsistency ---
        # The OpenAI API incorrectly sends 'duration' as float, 
        # but the OpenAPI schema defines it as str.
        # Here it is patched to str temporarily for model_dump(), 
        # then normalized back to float after.
        # see API definition of Pydantic model: TranscriptionVerbose 
        if hasattr(response, "duration") and isinstance(response.duration, float):
            response.duration = str(response.duration)
            
        if hasattr(response, "model_dump"):
            logger.debug("model_dumping...")
            data = response.model_dump(exclude_unset=True)
            logger.debug("Dumped.")
        elif hasattr(response, "to_dict"):
            data = response.to_dict()
        elif isinstance(response, dict):
            data = response
        else:
            raise ValueError(f"OpenAI response does not have a method to extract data "
                             f"(missing 'model_dump' or 'to_dict'): {repr(response)}")

        # Required field: text 
        text = data.get("text")
        if not isinstance(text, str):
            raise ValueError(f"Invalid response: 'text' must be a string, "
                             f"got {type(text)}")

        # Optional fields with normalization 
        language = data.get("language") or self.config.language or "unknown"
        if not isinstance(language, str):
            raise ValueError(f"Invalid response: 'language' must be a string, "
                             f"got {type(language)}")

        duration_raw = data.get("duration", "0.0")
        try:
            logger.debug("converting duration...")
            duration = float(duration_raw)
            logger.debug("converted.")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid 'duration': expected number-like value, "
                             f"got {repr(duration_raw)}") from e

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
            words=self._extract_and_validate_words(response),
            utterances=self._extract_and_validate_utterances(response),
            confidence=0.0,  # Whisper doesn't provide overall confidence
            audio_duration_ms=self._seconds_to_ms(response.get("duration")),
            transcript_id=None,  # No ID from Whisper
            status="completed",  # You can set a static "completed" status
            raw_result=dict(response),  # Store the original response for debugging
        )
        
    def _extract_and_validate_words(
        self, response: WhisperResponse
        ) -> List[WordTiming]:
        """Extract, validate, and convert word data into WordTiming objects."""
        words_data = response.get("words")
        words = []
        if words_data:
            for word_entry in words_data:
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
                    # Silent handling for identical timestamps
                    end_ms += 1

                words.append(
                    WordTiming(
                        word=word, 
                        start_ms=start_ms, 
                        end_ms=end_ms,
                        confidence=0.0,
                        )
                    )
        
        return words

    def _extract_and_validate_utterances(
        self, response: WhisperResponse
        ) -> List[Utterance]:
        """Extract and validate utterance segments into Utterance objects."""
        segments = response.get("segments")
        utterances = []
        
        if segments:
            for segment in segments:
                start_ms = self._seconds_to_ms(segment.get("start"))
                end_ms = self._seconds_to_ms(segment.get("end"))
                text = segment.get("text", "")

                if not isinstance(start_ms, int) or not isinstance(end_ms, int):
                    logger.warning(f"Invalid segment timestamps: {segment}")
                    continue

                if not isinstance(text, str) or not text.strip():
                    logger.warning(f"Empty or invalid text for segment: {segment}")
                    continue

                utterances.append(
                    Utterance(
                        speaker=None,  # Whisper doesn't provide speaker ID
                        start_ms=start_ms,
                        end_ms=end_ms,
                        text=text.strip(),
                        confidence=logprob_to_confidence(
                            segment.get('avg_logprob', 0.0)
                            ),
                    )
                )
        
        return utterances

    def transcribe(
        self,
        audio_file: Union[Path, BinaryIO],
        options: Optional[Dict[str, Any]] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio file to text using OpenAI Whisper API.
        
        Args:
            audio_file: Path to audio file or file-like object
            options: Provider-specific options for transcription
                
        Returns:
            Dictionary containing transcription results with standardized keys
        """
        # Prepare file object
        file_obj, should_close = self._prepare_file_object(audio_file)

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
        
        if isinstance(audio_file, str):
                audio_file = Path(audio_file)

        # If requesting SRT or VTT directly, use native OpenAI capabilities
        if format_type in {"srt", "vtt"}:
            # Create options with format set to SRT or VTT
            options = transcription_options.copy() if transcription_options else {}
            options["response_format"] = format_type

            # Prepare file object
            file_obj, should_close = self._prepare_file_object(audio_file)

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


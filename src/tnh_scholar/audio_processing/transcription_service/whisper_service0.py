import json
import os
from pathlib import Path
from typing import Any, BinaryIO, Dict, Optional, Union

import openai
from dotenv import load_dotenv

from tnh_scholar.logging_config import get_child_logger

from .format_converter import TranscriptionFormatConverter
from .transcription_service import TranscriptionService

# Load environment variables
load_dotenv()

logger = get_child_logger(__name__)

class WhisperTranscriptionService(TranscriptionService):
    """
    OpenAI Whisper implementation of the TranscriptionService interface.
    
    Provides transcription services using the OpenAI Whisper API.
    """
    
    # Default configuration
    DEFAULT_CONFIG = {
        "model": "whisper-1",
        "response_format": "verbose_json",
        "timestamp_granularities": ["word"],
    }
    
    # Supported response formats
    SUPPORTED_FORMATS = ["json", "text", "srt", "vtt", "verbose_json"]
    
    def __init__(self, api_key: Optional[str] = None, **config):
        """
        Initialize the Whisper transcription service.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            **config: Additional configuration options
        """
        # Merge default config with provided config
        self.config = {**self.DEFAULT_CONFIG, **config}
        
        # Initialize format converter
        self.format_converter = TranscriptionFormatConverter()
        
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
    
    def _prepare_api_params(self, effective_options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare parameters for the Whisper API call.
        
        Args:
            effective_options: Combined configuration and options
            
        Returns:
            Dictionary of parameters for the API call
        """
        # Get model from options
        model = effective_options.get("model", self.DEFAULT_CONFIG["model"])
        
        # Format parameters for the API
        api_params = {
            "model": model,
        }

        # Add prompt if specified
        if "prompt" in effective_options:
            api_params["prompt"] = effective_options["prompt"]

        # Add language if specified
        if "language" in effective_options:
            api_params["language"] = effective_options["language"]

        # Add temperature if specified
        if "temperature" in effective_options:
            api_params["temperature"] = effective_options["temperature"]

        # Add response format if specified
        response_format = effective_options.get(
            "response_format", self.DEFAULT_CONFIG["response_format"])
        if response_format not in self.SUPPORTED_FORMATS:
            logger.warning(
                f"Unsupported response format: "
                f"{response_format}, defaulting to 'verbose_json'")
            response_format = "verbose_json"
        api_params["response_format"] = response_format
        
        return api_params
    
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
    
    def _seconds_to_milliseconds(self, seconds: Optional[float]) -> Optional[int]:
        """
        Convert seconds to milliseconds.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Time in milliseconds or None if seconds is None
        """
        return None if seconds is None else int(seconds * 1000)
    
    def _process_json_response(
        self, 
        response: Any, 
        effective_options: Dict[str, Any]
        ) -> Dict[str, Any]:
        """
        Process JSON response from Whisper API.
        
        Args:
            response: Response from the API
            effective_options: Combined configuration and options
            
        Returns:
            Standardized result dictionary
        """
        text = response.text if hasattr(response, "text") else response.get("text", "")
        # Create standardized result
        return {
            "text": text,
            "language": effective_options.get("language", "en"),
            "words": [],  # Whisper doesn't provide word-level timing by default
            "utterances": [],  # Whisper doesn't provide speaker diarization
            "confidence": 0.0,  # Whisper doesn't provide confidence scores
            "audio_duration_ms": 0,  # Not available from Whisper API
            "raw_result": response,
        }
    
    def _process_verbose_json_response(
        self, 
        response: Any, 
        effective_options: Dict[str, Any]
        ) -> Dict[str, Any]:
        """
        Process verbose JSON response from Whisper API.
        
        Args:
            response: Response from the API
            effective_options: Combined configuration and options
            
        Returns:
            Standardized result dictionary
        """
        # For verbose_json, we get detailed information
        if isinstance(response, dict):
            data = response
        else:
            data = response.model_dump() if hasattr(response, "model_dump") \
                else response.__dict__

        # Extract text
        text = data.get("text", "")

        # Extract words if available and convert timestamps to milliseconds
        words = []
        segments = data.get("segments", [])
        for segment in segments:
            if "words" in segment:
                words.extend(
                    {
                        "word": word.get("word", ""),
                        "start_ms": self._seconds_to_milliseconds(word.get("start")),
                        "end_ms": self._seconds_to_milliseconds(word.get("end")),
                        "confidence": word.get("confidence", 0.0),
                    }
                    for word in segment["words"]
                    if word.get("start") is not None and word.get("end") is not None
                )
        
        # Convert audio duration to milliseconds
        audio_duration_ms = self._seconds_to_milliseconds(data.get("duration", 0.0))
        
        # Create standardized result
        return {
            "text": text,
            "language": data.get(
                "language", effective_options.get("language", "en")
            ),
            "words": words,
            "utterances": [],  # Whisper doesn't provide speaker diarization
            "confidence": 0.0,  # Not directly provided
            "audio_duration_ms": audio_duration_ms,
            "raw_result": data,
        }

    def transcribe(
        self,
        audio_file: Union[Path, BinaryIO],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text using OpenAI Whisper API.
        
        Args:
            audio_file: Path to audio file or file-like object
            options: Provider-specific options for transcription
                
        Returns:
            Dictionary containing transcription results with standardized keys
        """
        # Combine default options with provided options
        effective_options = {**self.config, **(options or {})}

        # Prepare file object
        file_obj, should_close = self._prepare_file_object(audio_file)

        try:
            return self._openai_create_transcript(effective_options, file_obj)
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise

        finally:
            # Clean up file object if we opened it
            if should_close:
                file_obj.close()

    def _openai_create_transcript(self, effective_options, file_obj):
        # Prepare API parameters
        api_params = self._prepare_api_params(effective_options)
        api_params["file"] = file_obj

        # Call OpenAI API
        logger.info(
            f"Transcribing audio with Whisper API using model: {api_params['model']}")
        response = openai.audio.transcriptions.create(**api_params)

            # Process response based on format
        result = (
            self._process_verbose_json_response(response, effective_options)
            if api_params.get("response_format") == "verbose_json"
            else self._process_json_response(response, effective_options)
        )
        logger.info("Transcription completed successfully")
        return result

    def get_result(self, job_id: str) -> Dict[str, Any]:
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
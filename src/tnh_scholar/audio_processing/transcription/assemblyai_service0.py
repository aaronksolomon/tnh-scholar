# src/tnh_scholar/audio_processing/transcription_service/assemblyai_service.py

import os
import time
from pathlib import Path
from typing import Any, BinaryIO, Dict, Optional, Tuple, Union

import requests
from dotenv import load_dotenv

from tnh_scholar.logging_config import get_child_logger

from .format_converter import TranscriptionFormatConverter
from .transcription_service import TranscriptionService

# Load environment variables
load_dotenv()

logger = get_child_logger(__name__)

class AssemblyAITranscriptionService(TranscriptionService):
    """
    AssemblyAI implementation of the TranscriptionService interface.
    
    Provides transcription services using the AssemblyAI API.
    """
    
    # API endpoints
    BASE_URL = "https://api.assemblyai.com/v2"
    UPLOAD_ENDPOINT = f"{BASE_URL}/upload"
    TRANSCRIPT_ENDPOINT = f"{BASE_URL}/transcript"
    
    # Default configuration
    DEFAULT_CONFIG = {
        "polling_interval": 3,  # seconds
        "max_polling_time": 300,  # seconds (5 minutes)
        "language_code": "en",
        "speaker_labels": True,
        "format_text": True
    }
    
    # Subtitle output format mapping
    SUBTITLE_FORMATS = {
        "srt": "srt",
        "vtt": "vtt"
    }
    
    def __init__(self, api_key: Optional[str] = None, **config):
        """
        Initialize the AssemblyAI transcription service.
        
        Args:
            api_key: AssemblyAI API key (defaults to ASSEMBLYAI_API_KEY env var)
            **config: Additional configuration options
        """
        # Initialize format converter
        self.format_converter = TranscriptionFormatConverter()
        
        # Set API key
        self.set_api_key(api_key)
        
        # Merge default config with provided config
        self.config = {**self.DEFAULT_CONFIG, **config}
        
    def set_api_key(self, api_key: Optional[str] = None) -> None:
        """
        Set or update the API key.
        
        This method allows refreshing the API key without re-instantiating the class.
        
        Args:
            api_key: AssemblyAI API key (defaults to ASSEMBLYAI_API_KEY env var)
            
        Raises:
            ValueError: If no API key is provided or found in environment
        """
        self.api_key = api_key or os.getenv("ASSEMBLYAI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "AssemblyAI API key is required. Set ASSEMBLYAI_API_KEY environment "
                "variable or pass as api_key parameter."
            )
        
        # Set up API headers
        self.headers = {
            "authorization": self.api_key,
            "content-type": "application/json"
        }
        logger.debug("API key updated")
    
    def _prepare_file_object(self, audio_file: Union[Path, BinaryIO]) -> BinaryIO:
        """
        Prepare file object for API upload.
        
        Args:
            audio_file: Path to audio file or file-like object
            
        Returns:
            File-like object ready for upload
        """
        return open(audio_file, "rb") if isinstance(audio_file, Path) else audio_file
    
    def _handle_api_response(
        self, 
        response: requests.Response, 
        field_name: str, 
        log_message: str
        ) -> str:
        """
        Handle API response and extract field.
        
        Args:
            response: API response
            field_name: Name of field to extract
            log_message: Log message prefix
            
        Returns:
            Value from specified field
            
        Raises:
            requests.HTTPError: If request failed
        """
        response.raise_for_status()
        value = response.json()[field_name]
        logger.debug(f"{log_message}{value}")
        return value
    
    def upload_file(self, audio_file: Union[Path, BinaryIO]) -> str:
        """
        Upload an audio file to AssemblyAI.
        
        Args:
            audio_file: Path to audio file or file-like object
            
        Returns:
            String URL of the uploaded file
        """
        logger.info(f"Uploading file to AssemblyAI: {audio_file}")

        # Handle file path or file-like object
        file_obj = self._prepare_file_object(audio_file)
        
        # If file was opened by us, ensure it's closed after upload
        should_close = isinstance(audio_file, Path)
        
        try:
            response = requests.post(
                self.UPLOAD_ENDPOINT,
                headers=self.headers,
                data=file_obj
            )
            return self._handle_api_response(
                response, "upload_url", "File uploaded successfully: "
            )
        finally:
            if should_close and file_obj:
                file_obj.close()
    
    def _prepare_transcription_options(
        self, 
        audio_url: str, 
        options: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
        """
        Prepare transcription options.
        
        Args:
            audio_url: URL of the uploaded audio file
            options: Additional transcription options
            
        Returns:
            Combined transcription options
        """
        # Combine default options with provided options
        transcription_options = {
            "audio_url": audio_url,
            "language_code": self.config["language_code"],
            "speaker_labels": self.config["speaker_labels"]
        }

        # Add any additional options
        if options:
            transcription_options |= options

        return transcription_options
    
    def start_transcription(
        self, 
        audio_url: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a transcription job.
        
        Args:
            audio_url: URL of the uploaded audio file
            options: Additional transcription options
            
        Returns:
            String ID of the transcription job
        """
        transcription_options = self._prepare_transcription_options(audio_url, options)
        logger.info(f"Starting transcription with options: {transcription_options}")

        response = requests.post(
            self.TRANSCRIPT_ENDPOINT,
            json=transcription_options,
            headers=self.headers
        )

        return self._handle_api_response(
            response, "id", "Transcription job started: "
        )
    
    def _check_status(self, transcript_id: str) -> Dict[str, Any]:
        """
        Check status of a transcription job.
        
        Args:
            transcript_id: ID of the transcription job
            
        Returns:
            Response JSON
            
        Raises:
            requests.HTTPError: If request failed
        """
        endpoint = f"{self.TRANSCRIPT_ENDPOINT}/{transcript_id}"
        response = requests.get(endpoint, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def _handle_polling_status(
        self, 
        status: str, 
        transcript_id: str, 
        elapsed_time: float, 
        max_polling_time: float
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Handle status during polling.
        
        Args:
            status: Current status
            transcript_id: ID of the transcription job
            elapsed_time: Time elapsed since polling started
            max_polling_time: Maximum polling time
            
        Returns:
            Tuple of (continue_polling, result, error_message)
        """
        if status == "completed":
            logger.info(f"Transcription completed: {transcript_id}")
            return False, self._check_status(transcript_id), None
        
        if status == "error":
            error = self._check_status(transcript_id).get("error", "Unknown error")
            logger.error(f"Transcription failed: {error}")
            return False, None, f"Transcription failed: {error}"
        
        # Check timeout
        if elapsed_time > max_polling_time:
            logger.error(f"Polling timeout for transcript {transcript_id}")
            return False, None, f"Polling timeout for transcript {transcript_id}"
        
        # Continue polling
        remaining_time = max_polling_time - elapsed_time
        logger.debug(
            f"Transcription status: {status}. "
            f"Elapsed time: {elapsed_time:.2f}s, "
            f"remaining timeout: {remaining_time:.2f}s. "
            f"Polling again..."
        )
        return True, None, None
    
    def poll_for_completion(self, transcript_id: str) -> Dict[str, Any]:
        """
        Poll for transcription completion.
        
        Args:
            transcript_id: ID of the transcription job
            
        Returns:
            Dictionary containing transcription results
            
        Raises:
            TimeoutError: If polling exceeds max_polling_time
            RuntimeError: If transcription fails
        """
        polling_interval = self.config["polling_interval"]
        max_polling_time = self.config["max_polling_time"]
        
        logger.info(f"Polling for completion of job {transcript_id}")
        
        start_time = time.time()
        while True:
            status_data = self._check_status(transcript_id)
            status = status_data["status"]
            
            elapsed_time = time.time() - start_time
            continue_polling, result, error = self._handle_polling_status(
                status, transcript_id, elapsed_time, max_polling_time
            )
            
            if not continue_polling:
                if error:
                    if "timeout" in error.lower():
                        raise TimeoutError(error)
                    raise RuntimeError(error)
                return result or status_data
            
            # Wait before checking again
            time.sleep(polling_interval)
    
    def _extract_words(self, result: Dict[str, Any]) -> list:
        """
        Extract words with timestamps from result.
        
        Args:
            result: Raw AssemblyAI transcription result
            
        Returns:
            List of word objects with timing info
        """
        words = []
        words.extend(
            {
                "word": w["text"],
                "start_ms": w["start"],  # Already in milliseconds
                "end_ms": w["end"],      # Already in milliseconds
                "confidence": w["confidence"],
            }
            for w in result.get("words", [])
            if w["start"] is not None and w["end"] is not None
        )
        return words
    
    def _extract_utterances(self, result: Dict[str, Any]) -> list:
        """
        Extract utterances by speaker from result.
        
        Args:
            result: Raw AssemblyAI transcription result
            
        Returns:
            List of utterance objects
        """
        utterances = []
        if result.get("utterances"):
            utterances.extend(
                {
                    "speaker": u["speaker"],
                    "text": u["text"],
                    "start_ms": u["start"],  # Already in milliseconds
                    "end_ms": u["end"],      # Already in milliseconds
                }
                for u in result["utterances"]
                if u["start"] is not None and u["end"] is not None
            )
        return utterances
    
    def standardize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardize AssemblyAI result to match common format.
        
        Args:
            result: Raw AssemblyAI transcription result
            
        Returns:
            Standardized result dictionary
        """
        # Extract words with timestamps
        words = self._extract_words(result)

        # Extract utterances by speaker
        utterances = self._extract_utterances(result)

        return {
            "text": result.get("text", ""),
            "language": result.get("language_code", "en"),
            "words": words,
            "utterances": utterances,
            "confidence": result.get("confidence", 0.0),
            "audio_duration_ms": result.get("audio_duration", 0),  # Already in milliseconds
            "raw_result": result,  # Include the original result for advanced usage
        }
    
    def transcribe(
        self,
        audio_file: Union[Path, BinaryIO],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text.
        
        Args:
            audio_file: Path to audio file or file-like object
            options: Provider-specific options for transcription
            
        Returns:
            Dictionary containing transcription results
        """
        # Upload the file
        audio_url = self.upload_file(audio_file)
        
        # Start transcription
        transcript_id = self.start_transcription(audio_url, options)
        
        # Poll for completion
        result = self.poll_for_completion(transcript_id)
        
        # Return standardized result
        return self.standardize_result(result)
    
    def get_result(self, job_id: str) -> Dict[str, Any]:
        """
        Get results for an existing transcription job.
        
        Args:
            job_id: ID of the transcription job
            
        Returns:
            Dictionary containing transcription results
        """
        result = self._check_status(job_id)
        
        if result["status"] != "completed":
            raise ValueError(f"Transcription not completed. Status: {result['status']}")
        
        return self.standardize_result(result)
    
    def _prepare_subtitle_params(self, format_options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Prepare parameters for subtitle request.
        
        Args:
            format_options: Format-specific options
            
        Returns:
            Dictionary of parameters
        """
        params = {
            "chars_per_caption": (
                format_options.get("max_length", 42) if format_options else 42
            )
        }

        # Handle speaker labels if available
        if format_options and "include_speaker" in format_options:
            params["speaker_labels"] = format_options["include_speaker"]

        return params
    
    def get_subtitles(
        self, 
        transcript_id: str, 
        format_type: str = "srt",
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get subtitles directly from AssemblyAI.
        
        This method is more efficient than converting from the transcript
        as it uses AssemblyAI's dedicated subtitles endpoint.
        
        Args:
            transcript_id: ID of the transcription job
            format_type: Format type ("srt" or "vtt")
            options: Format-specific options (passed as query parameters)
            
        Returns:
            String representation in the requested format
            
        Raises:
            ValueError: If the format type is not supported
        """
        format_type = format_type.lower()
        if format_type not in self.SUBTITLE_FORMATS:
            raise ValueError(f"Unsupported subtitle format: {format_type}")
        
        # Get the AssemblyAI format name
        asm_format = self.SUBTITLE_FORMATS[format_type]
        
        # Prepare query parameters
        params = self._prepare_subtitle_params(options)
        params["format"] = asm_format
        
        # Get the subtitles
        endpoint = f"{self.TRANSCRIPT_ENDPOINT}/{transcript_id}/subtitles"
        response = requests.get(
            endpoint,
            params=params,
            headers=self.headers
        )
        
        response.raise_for_status()
        
        # Response is plain text, not JSON
        return response.text
    
    def transcribe_to_format(
        self,
        audio_file: Union[Path, BinaryIO],
        format_type: str = "srt",
        transcription_options: Optional[Dict[str, Any]] = None,
        format_options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Transcribe audio and return result in specified format.
        
        For AssemblyAI, we take advantage of the direct subtitle generation
        functionality when requesting SRT or VTT formats.
        
        Args:
            audio_file: Path to audio file or file-like object
            format_type: Format type (e.g., "srt", "vtt", "text")
            transcription_options: Options for transcription
            format_options: Format-specific options
            
        Returns:
            String representation in the requested format
        """
        format_type = format_type.lower()
        
        # Check if we can use direct subtitle generation
        if format_type in self.SUBTITLE_FORMATS:
            # We need to upload and transcribe first
            audio_url = self.upload_file(audio_file)
            transcript_id = self.start_transcription(audio_url, transcription_options)
            
            # Wait for completion (but don't retrieve full results)
            self.poll_for_completion(transcript_id)
            
            # Get subtitles directly in the requested format
            return self.get_subtitles(transcript_id, format_type, format_options)
        
        # For other formats, use the format converter
        # First get a normal transcription result
        result = self.transcribe(audio_file, transcription_options)
        
        # Then convert to the requested format
        return self.format_converter.convert(
            result, format_type, format_options or {}
        )
# src/tnh_scholar/audio_processing/transcription_service/transcription_service.py

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, BinaryIO, Callable, Dict, Optional, Union


class TranscriptionService(ABC):
    """
    Abstract base class defining the interface for transcription services.
    
    This interface provides a standard way to interact with different
    transcription service providers (e.g., OpenAI Whisper, AssemblyAI).
    """
    
    @abstractmethod
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
            Dictionary containing transcription results with standardized keys:
                - text: Complete transcription text
                - language: Detected or specified language code
                - words: List of words with timing information 
                   (timestamps in milliseconds)
                - utterances: List of utterances by speaker 
                   (timestamps in milliseconds)
                - confidence: Overall confidence score (0.0-1.0)
                - audio_duration_ms: Duration of audio in milliseconds
                - transcript_id: id of the transcript
                - status: status of transcription
                - raw_result: Original provider-specific result
        """
        pass
    
    @abstractmethod
    def get_result(self, job_id: str) -> Dict[str, Any]:
        """
        Get results for an existing transcription job.
        
        Args:
            job_id: ID of the transcription job
            
        Returns:
            Dictionary containing transcription results in the same
            standardized format as transcribe()
        """
        pass
    
    @abstractmethod
    def transcribe_to_format(
        self,
        audio_file: Union[Path, BinaryIO, str],
        format_type: str = "srt",
        transcription_options: Optional[Dict[str, Any]] = None,
        format_options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Transcribe audio and return result in specified format.

        Args:
            audio_file: Path, file-like object, or URL of audio file
            format_type: Format type (e.g., "srt", "vtt", "text")
            transcription_options: Options for transcription
            format_options: Format-specific options

        Returns:
            String representation in the requested format
        """
        pass


class TranscriptionServiceFactory:
    """
    Factory for creating transcription service instances.
    
    This factory provides a standard way to create transcription service
    instances based on the provider name and configuration.
    """
    
    # Mapping provider names to implementation classes
    # Classes will be imported lazily when needed
    _PROVIDER_MAP: Dict[str, Callable[..., TranscriptionService]] = {}
    
    @classmethod
    def register_provider(
        cls, 
        name: str, 
        provider_class: Callable[..., TranscriptionService]
    ) -> None:
        """
        Register a provider implementation with the factory.
        
        Args:
            name: Provider name (lowercase)
            provider_class: Provider implementation class or factory function
            
        Example:
            >>> from my_module import MyTranscriptionService
            >>> TranscriptionServiceFactory.register_provider("my_provider", MyTranscriptionService)
        """  # noqa: E501
        cls._PROVIDER_MAP[name.lower()] = provider_class
    
    @classmethod
    def create_service(
        cls,
        provider: str = "assemblyai",
        api_key: Optional[str] = None,
        **kwargs
    ) -> TranscriptionService:
        """
        Create a transcription service instance.
        
        Args:
            provider: Service provider name (e.g., "whisper", "assemblyai")
            api_key: API key for the service
            **kwargs: Additional provider-specific configuration
            
        Returns:
            TranscriptionService instance
            
        Raises:
            ValueError: If the provider is not supported
            ImportError: If the provider module cannot be imported
        """
        provider = provider.lower()
        
        # Initialize provider map if empty
        if not cls._PROVIDER_MAP:
            # Import lazily to avoid circular imports
            from .assemblyai_service import AAITranscriptionService
            from .whisper_service import WhisperTranscriptionService
            
            cls._PROVIDER_MAP = {
                "whisper": WhisperTranscriptionService,
                "assemblyai": AAITranscriptionService,
            }
        
        # Get the provider implementation
        provider_class = cls._PROVIDER_MAP.get(provider)
        
        if provider_class is None:
            raise ValueError(f"Unsupported transcription provider: {provider}")
        
        # Create and return the service instance
        return provider_class(api_key=api_key, **kwargs)
# src/tnh_scholar/audio_processing/transcription_service/transcription_service.py

from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

from pydantic import BaseModel

from ..timed_object.timed_text import TimedText


class WordTiming(BaseModel):
    word: str
    start_ms: int
    end_ms: int
    confidence: float

class Utterance(BaseModel):
    speaker: Optional[str]
    start_ms: int
    end_ms: int
    text: str
    confidence: float

class TranscriptionResult(BaseModel):
    text: str
    language: str
    word_timing: Optional[TimedText] = None
    utterance_timing: Optional[TimedText] = None
    confidence: Optional[float] = None
    audio_duration_ms: Optional[int] = None
    transcript_id: Optional[str] = None
    status: Optional[str] = None
    raw_result: Optional[Dict[str, Any]] = None
    
class TranscriptionService(ABC):
    """
    Abstract base class defining the interface for transcription services.
    
    This interface provides a standard way to interact with different
    transcription service providers (e.g., OpenAI Whisper, AssemblyAI).
    """
    
    @abstractmethod
    def transcribe(
        self,
        audio_file: Union[Path, BytesIO],
        options: Optional[Dict[str, Any]] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio file to text.
        
        Args:
            audio_file: Path to audio file or file-like object
            options: Provider-specific options for transcription
            
        Returns:
            TranscriptionResult
            
        """
        pass
    
    @abstractmethod
    def get_result(self, job_id: str) -> TranscriptionResult:
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
        audio_file: Union[Path, BytesIO],
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

    @staticmethod
    def _create_whisper_service(api_key: Optional[str] = None, **kwargs: Any) -> TranscriptionService:
        from .whisper_service import WhisperTranscriptionService

        return WhisperTranscriptionService(api_key=api_key, **kwargs)

    @staticmethod
    def _create_assemblyai_service(api_key: Optional[str] = None, **kwargs: Any) -> TranscriptionService:
        try:
            from .assemblyai_service import AAITranscriptionService
        except ModuleNotFoundError as exc:
            raise ImportError(
                "assemblyai package is not installed. Install it or use --service whisper."
            ) from exc

        return AAITranscriptionService(api_key=api_key, **kwargs)
    
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
        """  
        cls._PROVIDER_MAP[name.lower()] = provider_class
    
    @classmethod
    def create_service(
        cls,
        provider: str = "assemblyai",
        api_key: Optional[str] = None,
        **kwargs: Any
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
            cls._PROVIDER_MAP = {
                "whisper": cls._create_whisper_service,
                "assemblyai": cls._create_assemblyai_service,
            }
        
        # Get the provider implementation
        provider_class = cls._PROVIDER_MAP.get(provider)
        
        if provider_class is None:
            raise ValueError(f"Unsupported transcription provider: {provider}")
        
        # Create and return the service instance
        return provider_class(api_key=api_key, **kwargs)

from pydantic_settings import BaseSettings, SettingsConfigDict

from tnh_scholar.utils import TimeMs


class PyannoteConfig(BaseSettings):
    """Configuration constants for Pyannote API."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive = False,
        env_prefix = "PYANNOTE_",
        extra="ignore",
    )
    
    # API Endpoints
    base_url: str = "https://api.pyannote.ai/v1"

    @property
    def media_input_endpoint(self) -> str:
        return f"{self.base_url}/media/input"

    @property
    def diarize_endpoint(self) -> str:
        return f"{self.base_url}/diarize"

    @property
    def job_status_endpoint(self) -> str:
        return f"{self.base_url}/jobs"

    # Parameters
    polling_interval: int = 15  # Polling interval in seconds
    polling_timeout: int = 180  # Polling timeout in seconds
    initial_poll_time: int = 7 # First polling time in seconds (for short files)

    # Media
    media_prefix: str = "media://diarization-"
    media_content_type: str = "audio/mpeg"
    
    # Upload-specific settings
    upload_timeout: int = 300  # 5 minutes for large files
    upload_max_retries: int = 3
    
    # Network specific settings
    network_timeout: int = 3 # seconds

class SpeakerConfig(BaseSettings):
    """Configuration settings for speaker block generation."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive = False,
        env_prefix = "SPEAKER_",
        extra="ignore",
    )
    
    # Set the default gap allowed between segments that will allow grouping of
    # consecutive same-speaker segments
    same_speaker_gap_threshold: TimeMs = TimeMs.from_seconds(2)
    
    default_speaker_label: str = "SPEAKER_00"
    
    # If set to true, all speakers are set to default speaker label
    single_speaker: bool = False

        
class ChunkConfig(BaseSettings):
    """Configuration for chunking"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive = False,
        env_prefix = "CHUNK_",
        extra="ignore",
    )
    
    # Target duration for each chunk in milliseconds (default: 5 minutes = 300,000ms)
    target_duration: int = 300_000

    # Minimum duration for final chunk (in ms); shorter chunks are merged
    min_duration: int = 30_000 # 30 seconds
    
    # Maximum allowed gap between segments for audio processing
    gap_threshold: int = 4000
    
    # Spacing used between segments that are greater than gap threshold ms apart
    gap_spacing_time: int = 1000 


class LanguageConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive = False,
        env_prefix = "LANGUAGE_",
        extra="ignore",
    )
    # Duration for language probe sampling in milliseconds (default: 2 seconds)
    probe_time: int = 10_000
    
    # The file format used for language probe file-like objects
    export_format: str = "wav"
    
    # Default language
    default_language: str = "en"


class DiarizationConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive = False,
        env_prefix = "DIARIZATION_",
        extra="ignore",
    )
    speaker: SpeakerConfig = SpeakerConfig()
    chunk: ChunkConfig = ChunkConfig()
    language: LanguageConfig = LanguageConfig()
    
    


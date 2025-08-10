from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class AudioHandlerConfig(BaseSettings):
    """
    Configuration settings for the AudioHandler.
    All audio time units are milliseconds (int)
    """

    output_format: Optional[str] = Field(
        default=None,
        description=
        "Audio output format used when exporting segments (e.g., 'wav', 'mp3')."
    )
    temp_storage_dir: Optional[Path] = Field(
        default=None,
        description=
        "Optional directory path for storing temporary audio files (currently unused)."
    )
    max_segment_length: Optional[int] = Field(
        default=None,
        description="Maximum allowed segment length (in milliseconds)."
    )
    silence_all_intervals: bool = Field(
        default=False,
        description="If True, replace every non-zero interval between consecutive diarization segments " 
        "with silence of length spacing_time."
    )
    SUPPORTED_FORMATS: frozenset = frozenset({"mp3", "wav", "flac", "ogg", "m4a", "mp4"})
    class Config:
        env_prefix = "AUDIO_HANDLER_"  # Optional: allow env vars like AUDIO_HANDLER_OUTPUT_FORMAT
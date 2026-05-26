from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class NoAudioSourceError(ValueError):
    """Raised when no audio source is provided."""


class MultipleAudioSourceError(ValueError):
    """Raised when audio source selection has multiple sources)."""


DEFAULT_OUTPUT_PATH = "./audio_transcriptions/transcript.txt"
DEFAULT_TEMP_DIR = "./audio_transcriptions/tmp"
DEFAULT_SERVICE = "whisper"


class AudioTranscribeConfig(BaseSettings):
    """Validated runtime configuration for the audio-transcribe CLI."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    yt_url: str | None = Field(default=None, description="YouTube URL")
    yt_url_csv: str | None = Field(default=None, description="CSV file with YouTube URLs")
    file_: str | None = Field(default=None, description="Path to local audio file")
    output: str = Field(default=DEFAULT_OUTPUT_PATH, description="Path to output transcript file")
    temp_dir: str | None = Field(default=None, description="Directory for temporary processing files")
    service: str = Field(
        default=DEFAULT_SERVICE,
        pattern="^(whisper|assemblyai)$",
        description="Transcription service",
    )
    model: str = Field(default="whisper-1", description="Transcription model name")
    language: str = Field(default="en", description="Language code")
    response_format: str = Field(default="text", description="Response format")
    chunk_duration: int = Field(default=120, description="Target chunk duration in seconds")
    min_chunk: int = Field(default=10, ge=10, description="Minimum chunk duration in seconds")
    start_time: str | None = Field(default=None, description="Start time offset")
    end_time: str | None = Field(default=None, description="End time offset")
    prompt: str = Field(default="", description="Prompt or keywords")

    no_transcribe: bool = Field(
        default=False,
        description="If True, only download YouTube audio to mp3, no transcription.",
    )
    keep_artifacts: bool = Field(
        default=False,
        description=(
            "Keep all intermediate artifacts in the output directory "
            "instead of using a system temp directory."
        ),
    )

    @model_validator(mode="after")
    def validate_sources(self) -> "AudioTranscribeConfig":
        """Enforce coherent source selection for CLI execution."""
        sources = [self.yt_url, self.yt_url_csv, self.file_]
        num_sources = sum(bool(s) for s in sources)
        if self.no_transcribe:
            if not (self.yt_url or self.yt_url_csv):
                raise ValueError("--no_transcribe requires a YouTube URL or CSV (--yt_url or --yt_url_csv).")
            if self.file_:
                raise ValueError(
                    "--no_transcribe does not support local file input. Use --yt_url or --yt_url_csv only."
                )
            return self

        if num_sources == 0:
            raise NoAudioSourceError("No audio source provided: yt_url, yt_url_csv, or file_ input.")
        if num_sources > 1:
            raise MultipleAudioSourceError(
                "Only one audio source may be provided at a time: yt_url, yt_url_csv, or file_ input."
            )
        return self

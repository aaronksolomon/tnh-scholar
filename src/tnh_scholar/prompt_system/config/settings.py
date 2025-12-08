"""Environment-backed settings for the prompt system."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class PromptSystemSettings(BaseSettings):
    """Application-wide prompt system settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    tnh_prompt_dir: Path = Path("prompts/")
    default_validation_mode: str = "strict"
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    enable_safety_validation: bool = True

    @classmethod
    def from_env(cls) -> "PromptSystemSettings":
        """Factory for consistency with other settings objects."""
        return cls()


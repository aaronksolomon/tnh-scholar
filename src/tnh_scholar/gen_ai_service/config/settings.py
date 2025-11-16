"""Runtime Configuration for GenAIService.

Uses Pydantic BaseSettings to load environment variables, API keys,
and model defaults. Provides globally accessible configuration to orchestrators
and adapters.

Connected modules:
  - service.GenAIService
  - infra.rate_limit, infra.retry_policy
  - providers.base.ProviderClient
"""

from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# We use the default pattern directory for TNH Scholar.
# Later this will move to 'Prompt' dir.  
from tnh_scholar import TNH_DEFAULT_PATTERN_DIR


class Settings(BaseSettings):
    """Application-level settings loaded from environment or .env.

    Pydantic v2 note:
    - Use class-level `model_config` with `SettingsConfigDict` for env behavior.
    - Per-field `env=` is discouraged; rely on the default mapping from field
      name -> UPPER_SNAKE_CASE env var (e.g. `openai_api_key` -> `OPENAI_API_KEY`).
    - Avoid the legacy inner `Config` class.
    """

    # Pydantic v2 settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignore unknown env vars rather than erroring
    )

    # Provider credentials / org metadata
    openai_api_key: str | None = None
    openai_org: str | None = None

    # Service-wide defaults (no hardcoded literals elsewhere)
    default_provider: str = "openai"
    default_model: str = "gpt-5-mini"
    default_temperature: float = 1
    default_max_output_tokens: int = 10_000
    default_seed: int | None = None
    
    # Prompt Catalog
    # Env → field mapping:
    # - TNH_PATTERN_DIR (project-wide)
    # - PROMPT_DIR (future, more generic)
    prompt_dir: Path = Field(
        default=TNH_DEFAULT_PATTERN_DIR,
        validation_alias=AliasChoices("TNH_PATTERN_DIR", "PROMPT_DIR", "TNH_PROMPT_DIR"),
    )
    @property
    def default_prompt_dir(self) -> Path | None:
        return self.prompt_dir if self.prompt_dir is not None else None
      
    

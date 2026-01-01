"""Runtime Configuration for GenAIService.

Uses Pydantic BaseSettings to load environment variables, API keys,
and model defaults. Provides globally accessible configuration to orchestrators
and adapters.

# TODO: externalize provider/model capability constants into a shared registry
# module and/or data file so Settings validation, routing, and safety checks
# reuse a single source of truth (see ADR-A08/A09/OS01).
# TODO: move provider pricing table into a registry/asset file and load here.

Connected modules:
  - service.GenAIService
  - infra.rate_limit, infra.retry_policy
  - providers.base.ProviderClient
"""

from dataclasses import dataclass
from os import getenv
from pathlib import Path

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# We use the default pattern directory for TNH Scholar.
# Later this will move to 'Prompt' dir.
from tnh_scholar import TNH_DEFAULT_PATTERN_DIR
from tnh_scholar.exceptions import ConfigurationError


class GenAISettings(BaseSettings):
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
    # NOTE: default_max_output_tokens must not exceed provider/model limits.
    # For OpenAI GPT-4/5, max tokens is typically 4096-8192 (sometimes higher for newer models).
    # See: https://platform.openai.com/docs/models/overview
    default_provider: str = "openai"
    default_model: str = "gpt-5-mini"
    default_temperature: float = 1
    default_max_output_tokens: int = 10_000
    default_seed: int | None = None
    max_input_chars: int = 120_000
    max_dollars: float = 0.10
    registry_staleness_warn: bool = True
    registry_staleness_threshold_days: int = 90

    @model_validator(mode="after")
    def validate_max_output_tokens(cls, values):
        """
        Ensure configured max_output_tokens stays within known context limits
        for the selected default model.
        """

        model = getattr(values, "default_model", "gpt-5-mini")
        provider = getattr(values, "default_provider", "openai")
        max_tokens = getattr(values, "default_max_output_tokens", 10_000)
        try:
            from tnh_scholar.gen_ai_service.config.registry import get_model_info
            limit = get_model_info(provider, model).context_window
        except ConfigurationError:
            return values
        if max_tokens > limit:
            raise ValueError(
                f"default_max_output_tokens={max_tokens} exceeds context limit for {model} ({limit}). "
                "Lower the value or choose a model with a larger context window."
            )
        return values

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


@dataclass(frozen=True)
class RegistryStalenessConfig:
    """Configuration for registry staleness warnings."""

    warn: bool
    threshold_days: int


def get_registry_staleness_config() -> RegistryStalenessConfig:
    """Load registry staleness configuration from environment."""
    warn_raw = getenv("REGISTRY_STALENESS_WARN", "true").strip().lower()
    warn = warn_raw not in {"0", "false", "no", "off"}
    try:
        threshold_days = int(getenv("REGISTRY_STALENESS_THRESHOLD_DAYS", "90"))
    except ValueError:
        threshold_days = 90
    return RegistryStalenessConfig(warn=warn, threshold_days=threshold_days)

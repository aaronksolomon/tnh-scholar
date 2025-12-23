"""Parameter Policy Management.

Defines structured defaults and precedence rules for runtime parameters
(model, temperature, max_tokens, provider, etc.). Ensures consistent behavior
across all GenAIService calls.

Connected modules:
  - config.settings.Settings
  - service.GenAIService
  - pattern_catalog.catalog.PatternCatalog
"""

from functools import lru_cache
from typing import Optional

from pydantic import BaseModel

from tnh_scholar.gen_ai_service.config.settings import GenAISettings
from tnh_scholar.prompt_system.domain.models import PromptMetadata


class ResolvedParams(BaseModel):
    provider: str
    model: str
    temperature: float
    max_output_tokens: int
    output_mode: str = "text"
    seed: Optional[int] = None
    routing_reason: Optional[str] = None


@lru_cache(maxsize=1)
def _cached_settings() -> GenAISettings:
    """Cache Settings so policy resolution doesn't re-read env on every call."""
    return GenAISettings()


def apply_policy(
    intent: str | None,
    call_hint: str | None,
    *,
    prompt_metadata: PromptMetadata | None = None,
    settings: GenAISettings | None = None,
) -> ResolvedParams:
    """
    Merge defaults to choose effective params for a completion request.

    Precedence:
      1. `call_hint` (explicit caller override)
      2. Prompt metadata defaults (`default_model`, `output_mode`)
      3. Service settings defaults

    V1 uses Settings as the policy source; later versions can replace the
    settings lookup with a policy registry while keeping the same contract.

    Args:
        intent: Optional intent tag for routing diagnostics.
        call_hint: Explicit model hint from the request.
        prompt_metadata: Metadata from the prompt catalog entry.
        settings: Optional Settings instance (defaults to cached Settings()).

    Returns:
        ResolvedParams: Fully-resolved provider/model/parameter set with routing reason.
    """
    current_settings = settings or _cached_settings()

    metadata_model = prompt_metadata.default_model if prompt_metadata else None
    metadata_output_mode = prompt_metadata.output_mode if prompt_metadata else None

    model = (
        call_hint
        if call_hint is not None
        else metadata_model
        if metadata_model is not None
        else current_settings.default_model
    )
    output_mode = metadata_output_mode if metadata_output_mode is not None else "text"

    return ResolvedParams(
        provider=current_settings.default_provider,
        model=model,
        temperature=current_settings.default_temperature,
        max_output_tokens=current_settings.default_max_output_tokens,
        output_mode=output_mode,
        seed=current_settings.default_seed,
        routing_reason=f"policy: intent={intent or 'unspecified'},"
        f" call_hint={'yes' if call_hint else 'no'},"
        f" prompt_default={'yes' if metadata_model else 'no'}",
    )

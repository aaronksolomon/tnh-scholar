"""Parameter Policy Management.

Defines structured defaults and precedence rules for runtime parameters
(model, temperature, max_tokens, provider, etc.). Ensures consistent behavior
across all GenAIService calls.

Connected modules:
  - config.settings.Settings
  - service.GenAIService
  - pattern_catalog.catalog.PatternCatalog
"""

from typing import Optional

from pydantic import BaseModel


class ResolvedParams(BaseModel):
    provider: str
    model: str
    temperature: float
    max_output_tokens: int
    seed: Optional[int] = None

# TODO V1 requires more simple policy management. For now in prototype walking skeleton we use a stub.

def apply_policy(
    intent: str | None, 
    call_hint: str | None
    ) -> ResolvedParams:
    """
    Merge in order: call_hint / pattern_defaults / global policy / settings.
    This function reads ADR-A08 policy (yaml/env) via Settings accessor(s).
    For V1, read from Settings directly; later, load from policies/params file.
    """
    # sketch only; implement with real merges:
    # - get defaults from settings (no literals)
    from .settings import Settings
    settings = Settings()
    model = call_hint or settings.default_model
    return ResolvedParams(
        provider=settings.default_provider,
        model=model,
        temperature=settings.default_temperature,
        max_output_tokens=settings.default_max_output_tokens,
        seed=settings.default_seed,
    )
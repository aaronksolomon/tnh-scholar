"""Model Router.

Selects appropriate model/provider configuration based on intent,
task type, and system policies.  Uses declarative routing tables.

Connected modules:
  - routing.intents
  - config.params_policy
  - providers.base.ProviderClient
"""

from dataclasses import dataclass
from typing import Mapping, Optional

from tnh_scholar.gen_ai_service.config.params_policy import ResolvedParams
from tnh_scholar.gen_ai_service.config.settings import Settings
from tnh_scholar.prompt_system.domain.models import PromptMetadata


@dataclass(frozen=True)
class _Capability:
    vision: bool
    structured: bool


_MODEL_CAPABILITIES: Mapping[str, _Capability] = {
    # Text + JSON capable defaults
    "gpt-5o-mini": _Capability(vision=True, structured=True),
    "gpt-5o": _Capability(vision=True, structured=True),
    "gpt-5-mini": _Capability(vision=True, structured=True),
    "gpt-4o-mini": _Capability(vision=True, structured=True),
    "gpt-4o": _Capability(vision=True, structured=True),
    # Text-focused fallback
    "gpt-3.5-turbo": _Capability(vision=False, structured=False),
}


def _lookup_capability(model: str) -> Optional[_Capability]:
    normalized = model.lower()
    if normalized in _MODEL_CAPABILITIES:
        return _MODEL_CAPABILITIES[normalized]
    return next(
        (entry for key, entry in _MODEL_CAPABILITIES.items() if normalized.startswith(key)),
        None,
    )


def _pick_structured_fallback(preferred: str) -> str:
    """
    Return a structured-capable model; prefer the configured default if it
    supports structured outputs, otherwise pick the first structured-capable
    option in the capability table.
    """
    preferred_caps = _lookup_capability(preferred)
    if preferred_caps and preferred_caps.structured:
        return preferred

    return next(
        (model for model, caps in _MODEL_CAPABILITIES.items() if caps.structured),
        preferred,
    )


def select_provider_and_model(
    intent: str | None,
    params: ResolvedParams,
    settings: Settings,
    *,
    prompt_metadata: PromptMetadata | None = None,
) -> ResolvedParams:
    """
    Intent-aware routing with lightweight capability checks.

    Behavior:
      - Preserve provider from policy resolution.
      - If JSON mode requested and model lacks structured support, switch to a
        structured-capable default for that provider.
      - Attach routing reason diagnostics for observability.
      - Leave room for future intent tables and latency/budget heuristics.

    Args:
        intent: Optional intent string from caller or prompt metadata.
        params: ResolvedParams from policy resolution.
        settings: Service settings (used for default/fallback model).
        prompt_metadata: Prompt metadata (for intent tagging).

    Returns:
        ResolvedParams: Updated with selected model and routing reason.
    """
    capability = _lookup_capability(params.model)
    structured_needed = params.output_mode == "json"

    model = params.model
    routing_reason = params.routing_reason or "policy-preselection"

    if structured_needed and (capability is None or not capability.structured):
        fallback = _pick_structured_fallback(settings.default_model)
        routing_reason = f"{routing_reason} → router: switched to structured-capable model {fallback}"
        model = fallback

    # Placeholder for future intent-based overrides
    intent_tag = intent or (prompt_metadata.task_type if prompt_metadata else None)
    if intent_tag:
        routing_reason = f"{routing_reason}; intent={intent_tag}"

    return params.model_copy(
        update={
            "model": model,
            "routing_reason": routing_reason,
        }
    )

"""Model Router.

Selects appropriate model/provider configuration based on intent,
task type, and system policies.  Uses declarative routing tables.

Connected modules:
  - routing.intents
  - config.params_policy
  - providers.base.ProviderClient
"""

from tnh_scholar.gen_ai_service.config.params_policy import ResolvedParams
from tnh_scholar.gen_ai_service.config.registry import (
    get_model_info,
    get_registry_loader,
)
from tnh_scholar.gen_ai_service.config.settings import GenAISettings
from tnh_scholar.prompt_system.domain.models import PromptMetadata


class StructuredFallbackSelector:
    """Selects a structured-capable fallback model."""

    def __init__(self, provider: str) -> None:
        self._provider = provider

    def supports_structured(self, model: str) -> bool:
        model_info = get_model_info(self._provider, model)
        return bool(model_info.capabilities.structured_output)

    def select(self, preferred: str) -> str:
        if self.supports_structured(preferred):
            return preferred
        return self._first_structured() or preferred

    def _first_structured(self) -> str | None:
        registry = get_registry_loader().get_provider(self._provider)
        return next(
            (
                model_name
                for model_name, model_info in registry.models.items()
                if model_info.capabilities.structured_output
            ),
            None,
        )


def select_provider_and_model(
    intent: str | None,
    params: ResolvedParams,
    settings: GenAISettings,
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
    structured_needed = params.output_mode == "json"

    model = params.model
    routing_reason = params.routing_reason or "policy-preselection"

    if structured_needed:
        selector = StructuredFallbackSelector(params.provider)
        if not selector.supports_structured(params.model):
            fallback = selector.select(settings.default_model)
            routing_reason = (
                f"{routing_reason} → router: switched to structured-capable model {fallback}"
            )
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

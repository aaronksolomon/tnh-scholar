"""Model Router.

Selects appropriate model/provider configuration based on intent,
task type, and system policies.  Uses declarative routing tables.

Connected modules:
  - routing.intents
  - config.params_policy
  - providers.base.ProviderClient
"""

from tnh_scholar.gen_ai_service.config.params_policy import ResolvedParams


def select_provider_and_model(intent: str | None, params: ResolvedParams, settings) -> ResolvedParams:
    # V1 pass-through (later: intent-specific model maps)
    return params
"""service.py: GenAIService Orchestrator.

Implements the primary coordination layer between the domain (PromptCatalog, ParamsPolicy)
and infrastructure (ProviderClient adapters).  Responsible for assembling provider requests,
applying policies, invoking adapters, and returning typed domain results.

Connected modules:
  - config.settings.Settings
  - config.params_policy.ParamsPolicy
  - pattern_catalog.catalog.PatternCatalog
  - providers.openai_adapter.OpenAIAdapter
  - infra.issue_handler.IssueHandler (runtime validation & error hints)
"""

from datetime import datetime

from tnh_scholar.gen_ai_service.config.params_policy import apply_policy
from tnh_scholar.gen_ai_service.config.settings import Settings
from tnh_scholar.gen_ai_service.infra.issue_handler import IssueHandler
from tnh_scholar.gen_ai_service.infra.tracking.provenance import build_provenance
from tnh_scholar.gen_ai_service.mappers.completion_mapper import provider_to_completion
from tnh_scholar.gen_ai_service.models.domain import (
    CompletionEnvelope,
    RenderRequest,
)
from tnh_scholar.gen_ai_service.models.transport import ProviderRequest, ProviderResponse
from tnh_scholar.gen_ai_service.pattern_catalog.adapters.prompts_adapter import PromptsAdapter
from tnh_scholar.gen_ai_service.providers.openai_adapter import OpenAIAdapter
from tnh_scholar.gen_ai_service.providers.openai_client import OpenAIClient
from tnh_scholar.gen_ai_service.routing.model_router import select_provider_and_model
from tnh_scholar.gen_ai_service.safety import safety_gate


class GenAIService:
    # Note for V1 we are defaulting to limited provenance info.

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        prompts_base = self.settings.default_prompt_dir
        api_key = self.settings.openai_api_key
        self.openai_client: OpenAIClient
        if api_key is None:
            # library usage should fail fast; IssueHandler raises ConfigurationError
            IssueHandler.no_api_key("OPENAI_API_KEY")
        self.openai_client = OpenAIClient(api_key, None)
        if prompts_base is None:
            prompts_base = IssueHandler.no_prompt_catalog()
        if prompts_base is None:
            raise RuntimeError("GenAIService could not determine a prompt catalog directory")
        self.catalog = PromptsAdapter(prompts_base=prompts_base)
        self.openai_adapter = OpenAIAdapter()

    def generate(self, request: RenderRequest) -> CompletionEnvelope:
        prompt_metadata = self.catalog.introspect(request.instruction_key)
        # Adapter / catalog returns a RenderedPrompt and a Fingerprint (per ADR-A12)
        rendered, fingerprint = self.catalog.render(request)

        # Resolve params strictly via policy → router (no literals)
        base_params = apply_policy(
            intent=request.intent,
            call_hint=request.model,
            prompt_metadata=prompt_metadata,
            settings=self.settings,
        )
        selection = select_provider_and_model(
            intent=request.intent,
            params=base_params,
            settings=self.settings,
            prompt_metadata=prompt_metadata,
        )
        # selection contains: provider, model, temperature, max_output_tokens, seed

        safety_report = safety_gate.pre_check(
            rendered,
            selection,
            self.settings,
            prompt_metadata=prompt_metadata,
        )

        provider_request = ProviderRequest(
            provider=selection.provider,
            model=selection.model,
            system=rendered.system,
            messages=rendered.messages,
            temperature=selection.temperature,
            max_output_tokens=selection.max_output_tokens,
            seed=selection.seed,
        )

        started = datetime.now()
        if selection.provider == "openai":
            response: ProviderResponse = self.openai_client.generate(provider_request)
        else:
            # (Anthropic skeleton later)
            raise NotImplementedError(selection.provider)
        finished = datetime.now()

        provenance = build_provenance(
            fingerprint=fingerprint,
            provider=selection.provider,
            model=selection.model,
            sdk_version=getattr(self.openai_client, "sdk_version", None),
            started_at=started,
            finished_at=finished,
            attempt_count=response.attempts,
        )

        envelope = provider_to_completion(
            response,
            provenance=provenance,
            policy_applied={
                "routing_reason": selection.routing_reason,
                "prompt_tokens": safety_report.prompt_tokens,
                "context_limit": safety_report.context_limit,
                "estimated_cost": safety_report.estimated_cost,
            },
            warnings=list(safety_report.warnings),
        )

        post_warnings = safety_gate.post_check(envelope.result)
        envelope.warnings.extend(post_warnings)
        return envelope

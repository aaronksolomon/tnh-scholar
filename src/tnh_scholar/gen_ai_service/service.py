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

import copy
import json
from datetime import datetime
from pathlib import Path

from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

from tnh_scholar.exceptions import ConfigurationError
from tnh_scholar.gen_ai_service.config.params_policy import apply_policy
from tnh_scholar.gen_ai_service.config.settings import GenAISettings
from tnh_scholar.gen_ai_service.infra.issue_handler import IssueHandler
from tnh_scholar.gen_ai_service.infra.tracking.provenance import build_provenance
from tnh_scholar.gen_ai_service.mappers.completion_mapper import (
    PolicyApplied,
    provider_to_completion,
)
from tnh_scholar.gen_ai_service.models.domain import (
    CompletionFailure,
    CompletionEnvelope,
    CompletionOutcomeStatus,
    CompletionResult,
    FailureReason,
    RenderRequest,
)
from tnh_scholar.gen_ai_service.models.transport import ProviderRequest, ProviderResponse
from tnh_scholar.gen_ai_service.pattern_catalog.adapters.prompts_adapter import PromptsAdapter
from tnh_scholar.gen_ai_service.protocols import PromptCatalogProtocol
from tnh_scholar.gen_ai_service.providers.openai_adapter import OpenAIAdapter
from tnh_scholar.gen_ai_service.providers.openai_client import OpenAIClient
from tnh_scholar.gen_ai_service.routing.model_router import select_provider_and_model
from tnh_scholar.gen_ai_service.safety import safety_gate
from tnh_scholar.prompt_system.domain.models import PromptMetadata, PromptOutputMode
from tnh_scholar.prompt_system.service.contract_schema import (
    PromptContractSchemaResolver,
    ResolvedPromptContractSchema,
    format_contract_validation_error,
)


class GenAIService:
    # Note for V1 we are defaulting to limited provenance info.

    def __init__(self, settings: GenAISettings | None = None):
        self.settings: GenAISettings = settings or GenAISettings()
        prompts_base: Path | None = self.settings.default_prompt_dir
        api_key = self.settings.openai_api_key
        if api_key is None:
            # library usage should fail fast; IssueHandler raises ConfigurationError
            IssueHandler.no_api_key("OPENAI_API_KEY")
        self.openai_client: OpenAIClient = OpenAIClient(api_key, None)
        if prompts_base is None:
            prompts_base = IssueHandler.no_prompt_catalog()
        if prompts_base is None:
            raise RuntimeError("GenAIService could not determine a prompt catalog directory")
        self.catalog: PromptCatalogProtocol = PromptsAdapter(prompts_base=prompts_base)
        self.openai_adapter = OpenAIAdapter()
        self._schema_resolver = PromptContractSchemaResolver.for_prompt_directory(prompts_base)

    def generate(self, request: RenderRequest) -> CompletionEnvelope:
        prompt_metadata = self.catalog.introspect(request.instruction_key)
        resolved_schema = self._resolve_json_schema(prompt_metadata)
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
            response_format=_response_format_for_schema(
                resolved_schema=resolved_schema,
                provider=selection.provider,
            ),
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
            policy_applied=_build_policy_applied(selection.routing_reason, safety_report),
            warnings=list(safety_report.warnings),
        )
        return self._apply_json_contract(envelope, resolved_schema)

    def _resolve_json_schema(
        self,
        prompt_metadata: PromptMetadata,
    ) -> ResolvedPromptContractSchema | None:
        contract = prompt_metadata.output_contract
        if contract is None or contract.mode != PromptOutputMode.json:
            return None
        if not contract.schema_ref:
            raise ConfigurationError("JSON prompt output_contract.schema_ref is required.")
        return self._schema_resolver.resolve_validated(contract.schema_ref)

    def _apply_json_contract(
        self,
        envelope: CompletionEnvelope,
        resolved_schema: ResolvedPromptContractSchema | None,
    ) -> CompletionEnvelope:
        if resolved_schema is None or envelope.result is None:
            return envelope
        if envelope.outcome is CompletionOutcomeStatus.FAILED:
            return envelope
        try:
            json_value = json.loads(envelope.result.text)
            self._schema_resolver.validate_instance(resolved_schema, json_value)
        except (json.JSONDecodeError, JsonSchemaValidationError) as exc:
            return _contract_validation_failure(envelope, resolved_schema.schema_ref, exc)
        return _with_validated_json(
            envelope,
            resolved_schema.schema_ref,
            json_value,
        )


def _build_policy_applied(
    routing_reason: str | None,
    safety_report: safety_gate.SafetyReport,
) -> PolicyApplied:
    """Construct a PolicyApplied dict while filtering out None values."""
    policy: PolicyApplied = {
        "prompt_tokens": safety_report.prompt_tokens,
        "context_limit": safety_report.context_limit,
        "estimated_cost": safety_report.estimated_cost,
    }
    if routing_reason is not None:
        policy["routing_reason"] = routing_reason
    return policy


def _response_format_for_schema(
    *,
    resolved_schema: ResolvedPromptContractSchema | None,
    provider: str,
) -> dict[str, object] | None:
    if resolved_schema is None:
        return None
    if provider != "openai":
        return None
    if not _supports_openai_json_schema(resolved_schema.document):
        return None
    return {
        "type": "json_schema",
        "json_schema": {
            "name": _response_format_name(resolved_schema.schema_ref),
            # Use schema-guided output without forcing OpenAI's strict subset gate.
            # Local JSON Schema validation remains the authoritative contract check.
            "strict": False,
            "schema": _openai_compatible_json_schema(resolved_schema.document),
        },
    }


def _supports_openai_json_schema(schema_document: object) -> bool:
    if not isinstance(schema_document, dict):
        return False
    return bool(schema_document.get("type") == "object")


def _openai_compatible_json_schema(schema_document: object) -> dict[str, object]:
    if not isinstance(schema_document, dict):
        raise TypeError("OpenAI JSON schema compatibility requires an object schema document.")
    compatible_schema = copy.deepcopy(schema_document)
    for keyword in ("oneOf", "anyOf", "allOf", "enum", "not"):
        compatible_schema.pop(keyword, None)
    return compatible_schema


def _response_format_name(schema_ref: str) -> str:
    normalized = "".join(
        char if char.isalnum() or char in {"_", "-"} else "_"
        for char in schema_ref
    )
    return normalized[:64] or "structured_output"


def _contract_validation_failure(
    envelope: CompletionEnvelope,
    schema_ref: str,
    error: json.JSONDecodeError | JsonSchemaValidationError,
) -> CompletionEnvelope:
    return CompletionEnvelope(
        outcome=CompletionOutcomeStatus.FAILED,
        failure=CompletionFailure(
            reason=FailureReason.CONTRACT_VALIDATION_FAILED,
            message=format_contract_validation_error(schema_ref=schema_ref, error=error),
            retryable=False,
        ),
        provenance=envelope.provenance,
        policy_applied=dict(envelope.policy_applied),
        warnings=list(envelope.warnings),
    )


def _with_validated_json(
    envelope: CompletionEnvelope,
    schema_ref: str,
    json_value: object,
) -> CompletionEnvelope:
    result = envelope.result
    if result is None:
        return envelope
    canonical_text = json.dumps(json_value, ensure_ascii=False, separators=(",", ":"))
    updated_result = CompletionResult(
        text=canonical_text,
        usage=result.usage,
        model=result.model,
        provider=result.provider,
        parsed=result.parsed,
        json_value=json_value,
        schema_ref=schema_ref,
        finish_reason=result.finish_reason,
    )
    return envelope.model_copy(update={"result": updated_result})

# mappers/completion_mapper.py
from typing import Dict, List, Optional, Union

from tnh_scholar.gen_ai_service.models.domain import CompletionEnvelope, CompletionResult, Provenance, Usage
from tnh_scholar.gen_ai_service.models.transport import (
    ErrorInfo,
    ProviderResponse,
    ProviderStatus,
    TextPayload,
)

PolicyApplied = Dict[str, Union[str, int, float]]


def _usage_from_provider(usage) -> Optional[Usage]:
    if usage is None:
        return None
    return Usage(
        prompt_tokens=usage.tokens_in or 0,
        completion_tokens=usage.tokens_out or 0,
        total_tokens=usage.tokens_total or 0,
    )


def _policy_from_error(error: ErrorInfo | None) -> Dict[str, str]:
    if error is None:
        return {}
    message = error.message or ""
    return {
        "provider_error_kind": error.kind.value if hasattr(error.kind, "value") else str(error.kind),
        "provider_error_code": error.code or "",
        "provider_error_message": message,
    }


def provider_to_completion(
    resp: ProviderResponse,
    *,
    provenance: Provenance,
    policy_applied: Optional[PolicyApplied] = None,
    warnings: Optional[List[str]] = None,
) -> CompletionEnvelope:
    """
    Map a ProviderResponse into a domain CompletionEnvelope without dropping error details.

    Args:
        resp: Normalized provider response payload.
        provenance: Provenance metadata assembled by the service.
        policy_applied: Optional diagnostics (routing reason, usage, provider errors).
        warnings: Optional warnings propagated from earlier phases.

    Returns:
        CompletionEnvelope with result (if available), provenance, policy diagnostics, and warnings.
    """
    warnings_out: list[str] = list(warnings) if warnings else []
    policy_out: PolicyApplied = dict(policy_applied) if policy_applied else {}

    result: CompletionResult | None = None
    payload = resp.payload if isinstance(resp.payload, TextPayload) else None

    if payload is None:
        warnings_out.append("provider-missing-payload")
    else:
        result = CompletionResult(
            text=payload.text,
            usage=_usage_from_provider(resp.usage),
            model=resp.model,
            provider=resp.provider,
            parsed=payload.parsed,
            finish_reason=payload.finish_reason,
        )

    if resp.status != ProviderStatus.OK:
        warnings_out.append(f"provider-status:{resp.status}")
        if resp.incomplete_reason:
            warnings_out.append(f"incomplete:{resp.incomplete_reason}")
        policy_out.update(_policy_from_error(resp.error))

    return CompletionEnvelope(
        result=result,
        provenance=provenance,
        policy_applied=policy_out,
        warnings=warnings_out,
    )

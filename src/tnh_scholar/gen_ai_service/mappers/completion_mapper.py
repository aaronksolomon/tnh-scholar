# mappers/completion_mapper.py
from typing import Any, Dict, List, Optional, Union

from tnh_scholar.gen_ai_service.models.domain import (
    CompletionEnvelope,
    CompletionFailure,
    CompletionOutcomeStatus,
    CompletionResult,
    FailureReason,
    Provenance,
    Usage,
)
from tnh_scholar.gen_ai_service.models.transport import ErrorInfo, ProviderResponse, ProviderStatus, TextPayload

PolicyApplied = Dict[str, Union[str, int, float]]


def _usage_from_provider(usage: Any) -> Optional[Usage]:
    if usage is None:
        return None
    return Usage(
        prompt_tokens=usage.tokens_in or 0,
        completion_tokens=usage.tokens_out or 0,
        total_tokens=usage.tokens_total or 0,
    )


def _outcome_from_response(
    resp: ProviderResponse,
    payload: TextPayload | None,
) -> CompletionOutcomeStatus:
    match resp.status:
        case ProviderStatus.OK:
            return (
                CompletionOutcomeStatus.SUCCEEDED
                if payload is not None
                else CompletionOutcomeStatus.FAILED
            )
        case ProviderStatus.INCOMPLETE:
            return (
                CompletionOutcomeStatus.INCOMPLETE
                if payload is not None
                else CompletionOutcomeStatus.FAILED
            )
        case ProviderStatus.FAILED | ProviderStatus.FILTERED | ProviderStatus.RATE_LIMITED:
            return CompletionOutcomeStatus.FAILED
    return CompletionOutcomeStatus.FAILED


def _retryable_for_failure(reason: FailureReason) -> bool:
    match reason:
        case FailureReason.EMPTY_CONTENT_WITH_TOKENS:
            return False
        case FailureReason.CONTENT_FIELD_MISSING:
            return False
        case FailureReason.UNSUPPORTED_RESPONSE_SHAPE:
            return False
        case FailureReason.CONTENT_EXTRACTION_ERROR:
            return False
    return False


def _failure_message(resp: ProviderResponse, reason: FailureReason) -> str:
    if resp.error is not None and resp.error.message:
        return resp.error.message

    match reason:
        case FailureReason.EMPTY_CONTENT_WITH_TOKENS:
            return "Provider returned no extractable text after consuming completion tokens."
        case FailureReason.CONTENT_FIELD_MISSING:
            return "Provider response did not include extractable content."
        case FailureReason.UNSUPPORTED_RESPONSE_SHAPE:
            return "Provider response shape was not recognized by the adapter."
        case FailureReason.CONTENT_EXTRACTION_ERROR:
            return "Adapter failed while extracting content from the provider response."
    return "Provider response could not be converted into a completion result."


def _default_failure_reason(resp: ProviderResponse) -> FailureReason:
    if resp.error is not None:
        return FailureReason.CONTENT_EXTRACTION_ERROR
    if resp.incomplete_reason:
        return FailureReason.CONTENT_FIELD_MISSING
    return FailureReason.UNSUPPORTED_RESPONSE_SHAPE


def _failure_from_response(
    resp: ProviderResponse,
    outcome: CompletionOutcomeStatus,
) -> CompletionFailure | None:
    if outcome is not CompletionOutcomeStatus.FAILED:
        return None

    reason = resp.failure_reason
    if reason is None:
        reason = _default_failure_reason(resp)

    return CompletionFailure(
        reason=reason,
        message=_failure_message(resp, reason),
        retryable=_retryable_for_failure(reason),
        adapter_diagnostics=resp.adapter_diagnostics,
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


def _build_warnings_and_policy(
    resp: ProviderResponse,
    outcome: CompletionOutcomeStatus,
    warnings: Optional[List[str]],
    policy_applied: Optional[PolicyApplied],
    payload: TextPayload | None,
) -> tuple[list[str], PolicyApplied]:
    warnings_out = list(warnings) if warnings else []
    policy_out: PolicyApplied = dict(policy_applied) if policy_applied else {}

    if outcome is CompletionOutcomeStatus.FAILED:
        warnings_out.append(f"provider-status:{resp.status}")
        if resp.incomplete_reason:
            warnings_out.append(f"incomplete:{resp.incomplete_reason}")
        if payload is None:
            warnings_out.append("provider-missing-payload")
        policy_out.update(_policy_from_error(resp.error))
        return warnings_out, policy_out

    if payload is None:
        warnings_out.append("provider-missing-payload")

    if resp.status != ProviderStatus.OK:
        warnings_out.append(f"provider-status:{resp.status}")
        if resp.incomplete_reason:
            warnings_out.append(f"incomplete:{resp.incomplete_reason}")
        policy_out.update(_policy_from_error(resp.error))
    return warnings_out, policy_out


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
    result: CompletionResult | None = None
    payload = resp.payload if isinstance(resp.payload, TextPayload) else None
    outcome = _outcome_from_response(resp, payload)
    failure = _failure_from_response(resp, outcome)
    warnings_out, policy_out = _build_warnings_and_policy(
        resp,
        outcome,
        warnings,
        policy_applied,
        payload,
    )

    if payload is not None and outcome is not CompletionOutcomeStatus.FAILED:
        result = CompletionResult(
            text=payload.text,
            usage=_usage_from_provider(resp.usage),
            model=resp.model,
            provider=resp.provider,
            parsed=payload.parsed,
            finish_reason=payload.finish_reason,
        )

    return CompletionEnvelope(
        outcome=outcome,
        result=result,
        failure=failure,
        provenance=provenance,
        policy_applied=policy_out,
        warnings=warnings_out,
    )

from __future__ import annotations

from datetime import UTC, datetime

from tnh_scholar.gen_ai_service.mappers.completion_mapper import provider_to_completion
from tnh_scholar.gen_ai_service.models.domain import CompletionResult, Fingerprint, Provenance, Usage
from tnh_scholar.gen_ai_service.models.transport import (
    ErrorInfo,
    ErrorKind,
    FinishReason,
    ProviderResponse,
    ProviderStatus,
    ProviderUsage,
    TextPayload,
)


def _provenance() -> Provenance:
    return Provenance(
        provider="openai",
        model="gpt-test",
        sdk_version="2.5.0",
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
        attempt_count=1,
        fingerprint=Fingerprint(
            prompt_key="k",
            prompt_name="name",
            prompt_base_path="/tmp",
            prompt_content_hash="abc",
            variables_hash="def",
            user_string_hash="ghi",
        ),
    )


def test_provider_error_is_mapped_to_envelope():
    resp = ProviderResponse(
        provider="openai",
        model="gpt-test",
        status=ProviderStatus.FAILED,
        attempts=1,
        payload=None,
        usage=None,
        error=ErrorInfo(kind=ErrorKind.PROVIDER, message="backend failure", code="500"),
    )

    envelope = provider_to_completion(resp, provenance=_provenance())

    assert envelope.result is None
    assert any("provider-status" in w for w in envelope.warnings)
    assert envelope.policy_applied["provider_error_message"] == "backend failure"


def test_provider_response_maps_usage_and_finish_reason():
    resp = ProviderResponse(
        provider="openai",
        model="gpt-test",
        status=ProviderStatus.OK,
        attempts=1,
        payload=TextPayload(text="ok", finish_reason=FinishReason.STOP),
        usage=ProviderUsage(tokens_in=10, tokens_out=5, tokens_total=15),
    )

    envelope = provider_to_completion(resp, provenance=_provenance())

    assert isinstance(envelope.result, CompletionResult)
    assert isinstance(envelope.result.usage, Usage)
    assert envelope.result.finish_reason == FinishReason.STOP
    assert envelope.result.usage.total_tokens == 15

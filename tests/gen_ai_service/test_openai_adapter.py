from __future__ import annotations

from types import SimpleNamespace

from pydantic import BaseModel

from tnh_scholar.gen_ai_service.models.domain import AdapterDiagnostics, FailureReason
from tnh_scholar.gen_ai_service.models.transport import ProviderStatus
from tnh_scholar.gen_ai_service.providers.openai_adapter import OpenAIAdapter


class _UsageStub:
    def __init__(self, *, prompt_tokens: int | None, completion_tokens: int | None, total_tokens: int | None):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens

    def dict(self) -> dict[str, int | None]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


def _response(*, content, finish_reason: str | None = "stop", parsed=None, usage=None, choices=None):
    if choices is None:
        message = SimpleNamespace(content=content, parsed=parsed)
        choices = [SimpleNamespace(message=message, finish_reason=finish_reason)]
    return SimpleNamespace(choices=choices, usage=usage)


class _ParsedStub(BaseModel):
    value: str


def test_openai_adapter_marks_empty_content_with_tokens_as_failed():
    adapter = OpenAIAdapter()
    response = _response(
        content="",
        usage=_UsageStub(prompt_tokens=5, completion_tokens=9, total_tokens=14),
    )

    provider_response = adapter.from_openai_response(
        response,
        model="gpt-test",
        provider="openai",
        attempts=2,
    )

    assert provider_response.status == ProviderStatus.FAILED
    assert provider_response.failure_reason == FailureReason.EMPTY_CONTENT_WITH_TOKENS
    assert provider_response.payload is None
    assert isinstance(provider_response.adapter_diagnostics, AdapterDiagnostics)
    assert provider_response.adapter_diagnostics.extraction_notes == "message.content was empty; completion_tokens=9"


def test_openai_adapter_marks_missing_content_without_tokens_as_failed():
    adapter = OpenAIAdapter()
    response = _response(
        content=None,
        usage=_UsageStub(prompt_tokens=5, completion_tokens=0, total_tokens=5),
    )

    provider_response = adapter.from_openai_response(
        response,
        model="gpt-test",
        provider="openai",
        attempts=1,
    )

    assert provider_response.status == ProviderStatus.FAILED
    assert provider_response.failure_reason == FailureReason.CONTENT_FIELD_MISSING
    assert provider_response.payload is None
    assert provider_response.adapter_diagnostics is not None


def test_openai_adapter_marks_empty_choices_as_failed():
    adapter = OpenAIAdapter()
    response = _response(
        content="unused",
        choices=[],
        usage=_UsageStub(prompt_tokens=1, completion_tokens=1, total_tokens=2),
    )

    provider_response = adapter.from_openai_response(
        response,
        model="gpt-test",
        provider="openai",
        attempts=1,
    )

    assert provider_response.status == ProviderStatus.FAILED
    assert provider_response.failure_reason == FailureReason.UNSUPPORTED_RESPONSE_SHAPE
    assert provider_response.adapter_diagnostics is not None


def test_openai_adapter_keeps_parsed_structured_output_successful():
    adapter = OpenAIAdapter()
    response = _response(
        content=None,
        parsed=_ParsedStub(value="ok"),
        usage=_UsageStub(prompt_tokens=2, completion_tokens=0, total_tokens=2),
    )

    provider_response = adapter.from_openai_response(
        response,
        model="gpt-test",
        provider="openai",
        attempts=1,
    )

    assert provider_response.status == ProviderStatus.OK
    assert provider_response.failure_reason is None
    assert provider_response.payload is not None
    assert provider_response.payload.parsed == _ParsedStub(value="ok")

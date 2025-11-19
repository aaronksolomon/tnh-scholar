from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from tnh_scholar.gen_ai_service.adapters.simple_completion import simple_completion
from tnh_scholar.gen_ai_service.models.transport import (
    FinishReason,
    ProviderResponse,
    ProviderStatus,
    TextPayload,
)

simple_completion_module = importlib.import_module(
    "tnh_scholar.gen_ai_service.adapters.simple_completion"
)

class DummyClient:
    def __init__(self, response: ProviderResponse):
        self.response = response
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return self.response


class StructuredOutput(BaseModel):
    value: str


def _setup_stub(monkeypatch: pytest.MonkeyPatch, response: ProviderResponse) -> DummyClient:
    dummy_client = DummyClient(response)
    dummy_service = SimpleNamespace(openai_client=dummy_client)
    monkeypatch.setattr(simple_completion_module, "_get_service", lambda: dummy_service)
    return dummy_client


def test_simple_completion_returns_text(monkeypatch: pytest.MonkeyPatch):
    payload = TextPayload(text="Rendered completion", finish_reason=FinishReason.STOP)
    response = ProviderResponse(
        provider="openai",
        model="gpt-test",
        status=ProviderStatus.OK,
        payload=payload,
        attempts=1,
    )
    dummy_client = _setup_stub(monkeypatch, response)

    result = simple_completion(
        system_message="System",
        user_message="User",
        model="gpt-custom",
        max_tokens=123,
        temperature=0.55,
    )

    assert result == "Rendered completion"
    assert dummy_client.requests
    request = dummy_client.requests[0]
    assert request.model == "gpt-custom"
    assert request.max_output_tokens == 123
    assert pytest.approx(request.temperature) == 0.55
    assert request.response_format is None


def test_simple_completion_returns_structured_object(monkeypatch: pytest.MonkeyPatch):
    structured = StructuredOutput(value="ok")
    payload = TextPayload(
        text="ignored",
        finish_reason=FinishReason.STOP,
        parsed=structured,
    )
    response = ProviderResponse(
        provider="openai",
        model="gpt-test",
        status=ProviderStatus.OK,
        payload=payload,
        attempts=1,
    )
    dummy_client = _setup_stub(monkeypatch, response)

    result = simple_completion(
        system_message="System",
        user_message="User",
        response_model=StructuredOutput,
    )

    assert isinstance(result, StructuredOutput)
    assert result.value == "ok"
    assert dummy_client.requests[0].response_format is StructuredOutput


def test_simple_completion_requires_parsed_payload(monkeypatch: pytest.MonkeyPatch):
    payload = TextPayload(
        text="{}",
        finish_reason=FinishReason.STOP,
        parsed=None,
    )
    response = ProviderResponse(
        provider="openai",
        model="gpt-test",
        status=ProviderStatus.OK,
        payload=payload,
        attempts=1,
    )
    _setup_stub(monkeypatch, response)

    with pytest.raises(ValueError, match="structured payload"):
        simple_completion(
            system_message="System",
            user_message="User",
            response_model=StructuredOutput,
        )

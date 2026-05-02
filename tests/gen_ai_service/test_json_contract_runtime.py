from __future__ import annotations

from textwrap import dedent

import pytest

from tnh_scholar.gen_ai_service import service as service_module
from tnh_scholar.gen_ai_service.config.params_policy import ResolvedParams
from tnh_scholar.gen_ai_service.config.settings import GenAISettings
from tnh_scholar.gen_ai_service.models.domain import FailureReason, RenderRequest
from tnh_scholar.gen_ai_service.models.transport import (
    FinishReason,
    ProviderRequest,
    ProviderResponse,
    ProviderStatus,
    ProviderUsage,
    TextPayload,
)
from tnh_scholar.gen_ai_service.service import GenAIService


class DummyOpenAIClient:
    def __init__(self, api_key: str | None, organization: str | None):
        self.requests: list[ProviderRequest] = []
        self.response: ProviderResponse | None = None
        self.sdk_version = "openai-sdk-test"

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        self.requests.append(request)
        if self.response is None:
            raise AssertionError("test must set DummyOpenAIClient.response")
        return self.response


def _write_json_prompt(tmp_path):
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    prompt_dir.joinpath("json-echo.md").write_text(
        dedent(
            """\
            ---
            key: json-echo
            name: json-echo
            version: 1.0.0
            description: JSON contract prompt for testing.
            task_type: test
            role: task
            required_variables: []
            output_contract:
              mode: json
              schema_ref: tnh.testing.echo.v1
            ---
            Return a JSON object.
            """
        ),
        encoding="utf-8",
    )
    return prompt_dir


def _provider_response(text: str) -> ProviderResponse:
    return ProviderResponse(
        provider="openai",
        model="gpt-5-mini",
        status=ProviderStatus.OK,
        attempts=1,
        payload=TextPayload(text=text, finish_reason=FinishReason.STOP),
        usage=ProviderUsage(tokens_in=5, tokens_out=4, tokens_total=9),
    )


def _fake_apply_policy(intent, call_hint, **_):
    return ResolvedParams(
        provider="openai",
        model="gpt-5-mini",
        temperature=0.2,
        max_output_tokens=256,
        output_mode="json",
        seed=1,
        routing_reason="test-policy",
    )


def _fake_select(intent, params, settings, **_):
    return params


def test_gen_ai_service_validates_json_contract_and_canonicalizes_text(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
):
    prompt_dir = _write_json_prompt(tmp_path)
    monkeypatch.setattr(service_module, "apply_policy", _fake_apply_policy)
    monkeypatch.setattr(service_module, "select_provider_and_model", _fake_select)
    monkeypatch.setattr(service_module, "OpenAIClient", DummyOpenAIClient)
    monkeypatch.setenv("TNH_PROMPT_DIR", str(prompt_dir))
    monkeypatch.setenv("OPENAI_API_KEY", "unit-test-key")

    settings = GenAISettings(_env_file=None)
    service = GenAIService(settings=settings)
    dummy_client: DummyOpenAIClient = service.openai_client  # type: ignore[assignment]
    dummy_client.response = _provider_response('{\n  "message": "hello"\n}')

    envelope = service.generate(
        RenderRequest(
            instruction_key="json-echo",
            user_input="ignored",
            variables={},
        )
    )

    assert envelope.outcome.value == "succeeded"
    response_format = dummy_client.requests[0].response_format
    assert response_format is not None
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["name"] == "tnh_testing_echo_v1"
    assert response_format["json_schema"]["strict"] is True
    assert response_format["json_schema"]["schema"]["type"] == "object"
    assert envelope.result is not None
    assert envelope.result.json_value == {"message": "hello"}
    assert envelope.result.schema_ref == "tnh.testing.echo.v1"
    assert envelope.result.text == '{"message":"hello"}'


def test_gen_ai_service_maps_schema_validation_failures_to_failed_outcome(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
):
    prompt_dir = _write_json_prompt(tmp_path)
    monkeypatch.setattr(service_module, "apply_policy", _fake_apply_policy)
    monkeypatch.setattr(service_module, "select_provider_and_model", _fake_select)
    monkeypatch.setattr(service_module, "OpenAIClient", DummyOpenAIClient)
    monkeypatch.setenv("TNH_PROMPT_DIR", str(prompt_dir))
    monkeypatch.setenv("OPENAI_API_KEY", "unit-test-key")

    settings = GenAISettings(_env_file=None)
    service = GenAIService(settings=settings)
    dummy_client: DummyOpenAIClient = service.openai_client  # type: ignore[assignment]
    dummy_client.response = _provider_response('{"message": 1}')

    envelope = service.generate(
        RenderRequest(
            instruction_key="json-echo",
            user_input="ignored",
            variables={},
        )
    )

    assert envelope.outcome.value == "failed"
    assert envelope.result is None
    assert envelope.failure is not None
    assert envelope.failure.reason == FailureReason.CONTRACT_VALIDATION_FAILED
    assert "schema 'tnh.testing.echo.v1'" in envelope.failure.message
